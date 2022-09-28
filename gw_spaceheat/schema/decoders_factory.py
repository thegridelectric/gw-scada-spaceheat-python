import inspect
import json
import sys
from typing import Any, Sequence, Callable, Optional, Tuple, Mapping, NamedTuple

from schema.decoders import Decoders

def get_type_field_value_from_pydantic_model(potential_decoder: Any, type_name_field: str) -> str:
    type_name = ""
    decoder_fields = getattr(potential_decoder, "__fields__", None)
    if decoder_fields:
        model_field = decoder_fields.get(type_name_field, None)
        if model_field:
            type_name = getattr(model_field, "default", "")
    return type_name

def get_type_field_value(potential_decoder: Any, type_name_field: str) -> str:
    return getattr(
        potential_decoder,
        type_name_field,
        get_type_field_value_from_pydantic_model(potential_decoder, type_name_field)
    )

DEFAULT_TYPE_NAME_FIELD = "type_name"

def str_to_json_adapter(f: Callable, **json_kwargs) -> Callable:
    def str_to_json(content: str) -> Any:
        return f(**json.loads(content, **json_kwargs))
    return str_to_json

def from_objects(
        objs: list,
        type_name_field: str = DEFAULT_TYPE_NAME_FIELD,
        decoder_func_name: str = "",
        adapter_func: Optional[Callable[[Callable], Callable]] = None
) -> Decoders:
    decoder_dict: dict[str, Callable] = dict()
    for obj in objs:
        if type_field_value := get_type_field_value(obj, type_name_field):
            if decoder_func_name:
                if not hasattr(obj, decoder_func_name):
                    raise ValueError(f"ERROR. object {obj} has no attribute named {decoder_func_name}")
                decoder_func = getattr(obj, decoder_func_name)
                if not isinstance(decoder_func, Callable):
                    raise ValueError(f"ERROR. object {obj} attribute {decoder_func_name} is not Callable")
                decoder_func = getattr(obj, decoder_func_name, None)
            else:
                decoder_func = obj
            if adapter_func is not None:
                decoder_func = adapter_func(decoder_func)
            decoder_dict[type_field_value] = decoder_func
    return Decoders(decoder_dict)

def from_module(module_name: str, type_name_field: str = DEFAULT_TYPE_NAME_FIELD) -> Decoders:
    return from_objects(
        [entry[1] for entry in inspect.getmembers(sys.modules[module_name], inspect.isclass)],
        type_name_field=type_name_field
    )

def from_modules(module_names: Sequence[str], type_name_field: str = DEFAULT_TYPE_NAME_FIELD) -> Decoders:
    decoders = Decoders()
    for module_name in module_names:
        decoders.merge(from_module(module_name, type_name_field=type_name_field))
    return decoders

