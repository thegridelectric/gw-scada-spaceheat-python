"""Makes gt.time.step.100 type."""

from typing import List, Dict, Tuple, Optional, Any
from schema.errors import MpSchemaError
from data_classes.errors import DcError, DataClassLoadingError
from schema.gt.enum.mp_status import MpStatus
from data_classes.time_step import TimeStep
from schema.gt.gnr.time_step.gt_time_step_1_0_0 import GtTimeStep100
    
    
class GtTimeStep100_Maker():
    mp_alias = 'gt.time.step.100'
    mp_status = MpStatus.ACTIVE.value

    @classmethod
    def camel_dict_to_schema_type(cls, d:dict) -> GtTimeStep100:
        if 'MpAlias' not in d.keys():
            d['MpAlias'] = 'gt.time.step.100'
        if "PreviousTimeStepId" not in d.keys():
            d["PreviousTimeStepId"] = None
        if "WorldInstanceAlias" not in d.keys():
            d["WorldInstanceAlias"] = None
        p = GtTimeStep100(MpAlias=d["MpAlias"],
                        TimeStepId=d["TimeStepId"],
                        IrlCreatedAtUtc=float(d["IrlCreatedAtUtc"]),
                        PreviousTimeStepId=d["PreviousTimeStepId"],
                        EraIndex=d["EraIndex"],
                        EraId=d["EraId"],
                        TsIndex=d["TsIndex"])
        is_valid, errors = p.is_valid()
        if not is_valid:
            raise MpSchemaError(errors)
        return p 

    @classmethod
    def data_class_to_schema_type(cls,dc:TimeStep) -> GtTimeStep100:
        if dc is None:
            return None
        candidate = GtTimeStep100(MpAlias='gt.time.step.100',
                        TimeStepId=dc.time_step_id,
                        IrlCreatedAtUtc=float(dc.irl_created_at_utc),
                        PreviousTimeStepId=dc.previous_time_step_id,
                        EraIndex=dc.era_index,
                        EraId=dc.era_id,
                        TsIndex=dc.ts_index)
        is_valid, errors = candidate.is_valid()
        if not is_valid:
            raise MpSchemaError(errors)
        else:
            return candidate
    
    @classmethod
    def schema_type_to_data_class(cls,p:GtTimeStep100) -> TimeStep:
        if p is None:
            return None
        snake_dict = {}
        snake_dict['time_step_id']=p.TimeStepId
        snake_dict['irl_created_at_utc']=p.IrlCreatedAtUtc
        snake_dict['previous_time_step_id']=p.PreviousTimeStepId
        snake_dict['era_index']=p.EraIndex
        snake_dict['era_id']=p.EraId
        snake_dict['ts_index']=p.TsIndex
        if snake_dict['time_step_id'] in TimeStep.by_id.keys():
            time_step = TimeStep.by_id[snake_dict['time_step_id']]
            try:
                time_step.check_update_consistency(snake_dict)
            except DcError or DataClassLoadingError as err:
                print(f'Not updating or returning TimeStep: {err}')
                return None
            except KeyError as err:
                print(f'Not updating or returning TimeStep: {err}')
                return None

            for key, value in snake_dict.items():
                if hasattr(time_step, key):
                    setattr(time_step, key, value)
        else:
            time_step = TimeStep(**snake_dict)

        return time_step

    @classmethod
    def type_is_valid(cls, object_as_dict: Dict[str, Any]) -> Tuple[bool, Optional[List[str]]]:
        try:
            p = cls.camel_dict_to_schema_type(object_as_dict)
        except MpSchemaError as e:
            errors = [e]
            return False, errors
        return p.is_valid()

    def __init__(self,
                 time_step_id: str,
                 irl_created_at_utc: float,
                 era_index: int,
                 era_id: str,
                 ts_index: int,
                 previous_time_step_id: Optional[str] = None ):
        self.errors = []
        try:
            irl_created_at_utc = float(irl_created_at_utc)
        except ValueError:
            pass # This will get caught in is_valid() check below

        t = GtTimeStep100(MpAlias=GtTimeStep100_Maker.mp_alias,
                    TimeStepId=time_step_id,
                    IrlCreatedAtUtc=irl_created_at_utc,
                    PreviousTimeStepId=previous_time_step_id,
                    EraIndex=era_index,
                    EraId=era_id,
                    TsIndex=ts_index)

        is_valid, errors = t.is_valid()
        if is_valid is False:
            raise MpSchemaError(f"Failed to create payload due to these errors: {errors}")
        self.type = t

