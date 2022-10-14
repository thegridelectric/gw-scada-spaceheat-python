import json
from pathlib import Path
from typing import Callable, Any, Optional, NamedTuple

Decoder = Callable[[Any], Any]

class DecoderItem(NamedTuple):
    type_name: str
    decoder: Decoder

class Decoders:
    _decoders: dict[str, Decoder]

    def __init__(self, decoders: Optional[dict[str, Decoder]] = None):
        self._decoders = dict()
        if decoders is not None:
            self._decoders.update(decoders)

    def decoder(self, type_name: str) -> Decoder:
        return self._decoders[type_name]

    def decode(self, type_name: str, *args, **kwargs) -> Any:
        return self.decoder(type_name)(*args, **kwargs)

    def decode_str(
        self,
        type_name: str,
        content: str | bytes,
        encoding: str = "utf-8",
    ) -> Any:
        if isinstance(content, bytes):
            content = content.decode(encoding)
        return self.decode(type_name, content)

    def decode_json(
        self,
        type_name: str,
        content: str | bytes,
        encoding: str = "utf-8",
        json_args: Optional[dict[str, Any]] = None
    ) -> Any:
        if isinstance(content, bytes):
            content = content.decode(encoding)
        return self.decode(type_name, json.loads(content, **(json_args or dict())))

    def decode_path(
        self,
        type_name: str,
        path: str | Path,
        encoding: str = "utf-8",
        json_args: Optional[dict[str, Any]] = None
    ):
        return self.decode_json(type_name, Path(path).read_bytes(), encoding=encoding, json_args=json_args)

    def add_decoder(self, type_name: str, decoder: Decoder) -> "Decoders":
        self._validate(type_name, decoder)
        self._decoders[type_name] = decoder
        return self

    def add_decoders(self, decoders: dict[str, Decoder]) -> "Decoders":
        for type_name, decoder in decoders.items():
            self._validate(type_name, decoder)
        self._decoders.update(decoders)
        for type_name, decoder in decoders.items():
            self._validate(type_name, decoder)
        return self

    def merge(self, other: "Decoders") -> "Decoders":
        self.add_decoders(other._decoders)
        return self

    def __contains__(self, type_name: str) -> bool:
        return type_name in self._decoders

    def types(self) -> list[str]:
        return list(self._decoders.keys())

    def _validate(self, type_name: str, decoder: Callable) -> None:
        if type_name in self._decoders:
            if self._decoders[type_name] is not decoder:
                raise ValueError(
                    f"ERROR. decoder for [{type_name}] is already present as [{self._decoders[type_name]}]")

