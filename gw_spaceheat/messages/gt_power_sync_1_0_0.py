"""MessageMaker for gt.power.sync.1_0_0"""

from typing import List, Dict, Tuple, Optional, Any
import time
import uuid
import datetime
from messages.utils import log_style_utc_date_w_millis
from messages.errors import MpSchemaError
from messages.gt_power_sync_1_0_0_payload import GtPowerSync100Payload


class Gt_Telemetry_1_0_0():
    mp_alias = 'gt.power.sync.1_0_0'
    
    @classmethod
    def create_payload_from_camel_dict(cls, d:dict) -> GtPowerSync100Payload:
        if 'MpAlias' not in d.keys():
            d['MpAlias'] = 'gt.power.sync.1_0_0'
        p = GtPowerSync100Payload(Name=d["Name"],
                        Value=d["Value"],
                        ScadaReadTimeUnixMs=d["ScadaReadTimeUnixMs"])
        is_valid, errors = p.is_valid()
        if not is_valid:
            raise MpSchemaError(errors)
        return p 

    @classmethod
    def payload_is_valid(cls, payload_as_dict: Dict[str, Any]) -> Tuple[bool, Optional[List[str]]]:
        try:
            p = cls.create_payload_from_camel_dict(payload_as_dict)
        except MpSchemaError as e:
            errors = [e]
            return False, errors
        return p.is_valid()

    def __init__(self,name,
                value,
                scada_read_time_unix_ms):

        p = GtPowerSync100Payload(Name=name,
                    Value=value,
                    ScadaReadTimeUnixMs=scada_read_time_unix_ms)

        is_valid, errors = p.is_valid()
        if is_valid is False:
            raise MpSchemaError(f"Failed to create payload due to these errors: {errors}")
        self.payload = p

