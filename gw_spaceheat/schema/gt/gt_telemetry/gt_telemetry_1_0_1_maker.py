"""Makes gt.telemetry.101 type"""

from typing import List, Dict, Tuple, Optional, Any

from schema.errors import MpSchemaError
from schema.gt.gt_telemetry.gt_telemetry_1_0_1 import GtTelemetry101


class GtTelemetry101_Maker():
    mp_alias = 'gt.telemetry.101'
    
    @classmethod
    def camel_dict_to_type(cls, d:dict) -> GtTelemetry101:
        if 'MpAlias' not in d.keys():
            d['MpAlias'] = 'gt.telemetry.101'
        p = GtTelemetry101(Name=d["Name"],
                        Value=d["Value"],
                        ScadaReadTimeUnixMs=d["ScadaReadTimeUnixMs"])
        is_valid, errors = p.is_valid()
        if not is_valid:
            raise MpSchemaError(errors)
        return p 

    @classmethod
    def type_is_valid(cls, payload_as_dict: Dict[str, Any]) -> Tuple[bool, Optional[List[str]]]:
        try:
            t = cls.camel_dict_to_type(payload_as_dict)
        except MpSchemaError as e:
            errors = [e]
            return False, errors
        return t.is_valid()

    def __init__(self,name,
                value,
                scada_read_time_unix_ms):

        t = GtTelemetry101(Name=name,
                    Value=value,
                    ScadaReadTimeUnixMs=scada_read_time_unix_ms)

        is_valid, errors = t.is_valid()
        if is_valid is False:
            raise MpSchemaError(f"Failed to create type due to these errors: {errors}")
        self.type = t

