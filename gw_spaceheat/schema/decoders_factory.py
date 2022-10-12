import json
import sys
from typing import (
    Any,
    Sequence,
    Optional,
    Callable,
    Union,
    Type,
    TypeVar,
)
import typing
import functools
import inspect
from dataclasses import dataclass

from pydantic import create_model, Field

from proactor import Message, Header
from schema.decoders import Decoders, Decoder, DecoderItem

DEFAULT_TYPE_NAME_FIELD = "type_name"

def has_pydantic_literal_type_name(o, type_name_field: str = DEFAULT_TYPE_NAME_FIELD) -> bool:
    if hasattr(o, "__fields__"):
        if type_name_field in o.__fields__:
            return typing.get_origin(o.__fields__[type_name_field].annotation) == typing.Literal
    return False

def pydantic_named_types(module_names: str | Sequence[str], type_name_field: str = DEFAULT_TYPE_NAME_FIELD) -> list:
    if isinstance(module_names, str):
        module_names = [module_names]
    if unimported := [module_name for module_name in module_names if not module_name in sys.modules]:
        raise ValueError(f"ERROR. modules {unimported} have not been imported.")
    types = []
    for module_name in module_names:
        types.extend(
            [
                entry[1] for entry in inspect.getmembers(sys.modules[module_name], inspect.isclass)
                if has_pydantic_literal_type_name(entry[1], type_name_field=type_name_field)
            ]
        )
    return types

MessageDiscriminator = TypeVar("MessageDiscriminator", bound=Message)

def create_message_payload_discriminator(model_name: str, modules_names: str | Sequence[str]) -> Type["MessageDiscriminator"]:
    return create_model(
        model_name,
        __base__=Message,
        payload=(
            Union[tuple(pydantic_named_types(modules_names, type_name_field=DEFAULT_TYPE_NAME_FIELD))],
            Field(..., discriminator=DEFAULT_TYPE_NAME_FIELD)
        )
    )

# TODO: type of content should be better thought out (or maybe never dict?); decode needs encoding
def gridworks_message_decoder(
        content: str | bytes | dict,
        decoders: Decoders,
        message_payload_discriminator: Optional[Type["MessageDiscriminator"]] = None
) -> Message:
    if isinstance(content, bytes):
        content = content.decode("utf-8")
    if isinstance(content, str):
        content = json.loads(content)
    message_dict = dict(content)
    message_dict["header"] = Header.parse_obj(content.get("header", dict()))
    if message_dict["header"].message_type in decoders:
        message_dict["payload"] = decoders.decode(
            message_dict["header"].message_type,
            json.dumps(message_dict.get("payload", dict()))
        )
        message = Message(**message_dict)
    else:
        if message_payload_discriminator is None:
            raise ValueError(f"ERROR. No decoder present for payload type {message_dict['header'].message_type}")
        else:
            message = message_payload_discriminator.parse_obj(content)
    return message

@dataclass
class OneDecoderExtractor:
    type_name_field: str = "type_alias"
    decoder_function_name: str = "dict_to_tuple"

    def get_type_name_value(self, obj: Any) -> str:
        return getattr(obj, self.type_name_field, "")

    def extract(self, obj: Any) -> Optional[DecoderItem]:
        if type_field_value := self.get_type_name_value(obj):
            if self.decoder_function_name:
                if not hasattr(obj, self.decoder_function_name):
                    raise ValueError(f"ERROR. object {obj} has no attribute named {self.decoder_function_name}")
                decoder_function = getattr(obj, self.decoder_function_name)
            else:
                decoder_function = obj
            if not isinstance(decoder_function, Callable):
                raise ValueError(f"ERROR. object {obj} attribute {self.decoder_function_name} is not Callable")
            item = DecoderItem(type_field_value, decoder_function)
        else:
            item = None
        return item

@dataclass
class PydanticExtractor(OneDecoderExtractor):
    type_name_field: str = DEFAULT_TYPE_NAME_FIELD
    decoder_function_name: str = "parse_obj"

    def get_type_name_value(self, obj: Any) -> str:
        type_name = ""
        decoder_fields = getattr(obj, "__fields__", None)
        if decoder_fields:
            model_field = decoder_fields.get(self.type_name_field, None)
            if model_field:
                type_name = getattr(model_field, "default", "")
        return type_name

class DecoderExtractor:
    _extractors: list

    def __init__(self, extractors: Optional[Sequence[OneDecoderExtractor]] = None):
        if extractors is None:
            self._extractors = [
                OneDecoderExtractor(),
                PydanticExtractor(),
            ]
        else:
            self._extractors = list(extractors)

    def decoder_item_from_object(self, obj: Any) -> Optional[DecoderItem]:
        item = None
        for extractor in self._extractors:
            item = extractor.extract(obj)
            if item is not None:
                break
        return item

    def decoder_items_from_objects(self, objs: list) -> dict[str, Decoder]:
        return dict(filter(lambda item: item is not None, [self.decoder_item_from_object(obj) for obj in objs]))

    def from_objects(self, objs: list, message_payload_discriminator: Optional[Type["MessageDiscriminator"]] = None) -> Decoders:
        d = Decoders(self.decoder_items_from_objects(objs))
        d.add_decoder(
            Message.__fields__[DEFAULT_TYPE_NAME_FIELD].default,
            functools.partial(gridworks_message_decoder, decoders=d, message_payload_discriminator=message_payload_discriminator)
        )
        return d


