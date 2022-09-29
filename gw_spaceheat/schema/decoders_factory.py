from dataclasses import dataclass
from typing import Any, Sequence, Optional, Callable

from schema.decoders import Decoders, Decoder, DecoderItem

@dataclass
class OneDecoderExtractor:
    type_name_field: str = "type_alias"
    decoder_function_name: str = "type_to_tuple"

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


class PydanticExtractor(OneDecoderExtractor):
    type_name_field = "type_name"
    decoder_function_name = "parse_raw"

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
            self._extractors = list(*extractors)

    def decoder_item_from_object(self, obj: Any) -> Optional[DecoderItem]:
        item = None
        for extractor in self._extractors:
            item = extractor.extract(obj)
            if item is not None:
                break
        return item

    def decoder_items_from_objects(self, objs: list) -> dict[str, Decoder]:
        return dict(filter(lambda item: item is not None, [self.decoder_item_from_object(obj) for obj in objs]))

    def from_objects(self, objs: list) -> Decoders:
        return Decoders(self.decoder_items_from_objects(objs))

