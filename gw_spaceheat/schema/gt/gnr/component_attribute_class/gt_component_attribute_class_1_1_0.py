"""TypeMaker for gt.component.attribute.class.1_1_0"""

from typing import List, Dict, Tuple, Optional, Any
from schema.errors import MpSchemaError
from data_classes.errors import DcError, DataClassLoadingError
from schema.gt.enum.mp_status import MpStatus
from data_classes.component_attribute_class import ComponentAttributeClass
from schema.gt.gnr.component_attribute_class.gt_component_attribute_class_1_1_0_schema import GtComponentAttributeClass110
    
    
class Gt_Component_Attribute_Class_1_1_0():
    mp_alias = 'gt.component.attribute.class.1_1_0'
    mp_status = MpStatus.ACTIVE.value

    @classmethod
    def camel_dict_to_schema_type(cls, d:dict) -> GtComponentAttributeClass110:
        if 'MpAlias' not in d.keys():
            d['MpAlias'] = 'gt.component.attribute.class.1_1_0'
        if "NormalizedEquivInertia" not in d.keys():
            d["NormalizedEquivInertia"] = None 
        elif not d["NormalizedEquivInertia"] is None:
            d["NormalizedEquivInertia"] = float(d["NormalizedEquivInertia"])
        if "StartupSeconds" not in d.keys():
            d["StartupSeconds"] = None
        if "MaxBoostPowerKw" not in d.keys():
            d["MaxBoostPowerKw"] = None 
        elif not d["MaxBoostPowerKw"] is None:
            d["MaxBoostPowerKw"] = float(d["MaxBoostPowerKw"])
        if "MaxRampUpFractionPerSecond" not in d.keys():
            d["MaxRampUpFractionPerSecond"] = None 
        elif not d["MaxRampUpFractionPerSecond"] is None:
            d["MaxRampUpFractionPerSecond"] = float(d["MaxRampUpFractionPerSecond"])
        if "RatedPowerInjectedVa" not in d.keys():
            d["RatedPowerInjectedVa"] = None
        if "ShutdownSeconds" not in d.keys():
            d["ShutdownSeconds"] = None
        if "ShuntReactanceDefaultOhms" not in d.keys():
            d["ShuntReactanceDefaultOhms"] = None 
        elif not d["ShuntReactanceDefaultOhms"] is None:
            d["ShuntReactanceDefaultOhms"] = float(d["ShuntReactanceDefaultOhms"])
        if "MaxHeatpumpPowerKw" not in d.keys():
            d["MaxHeatpumpPowerKw"] = None 
        elif not d["MaxHeatpumpPowerKw"] is None:
            d["MaxHeatpumpPowerKw"] = float(d["MaxHeatpumpPowerKw"])
        if "SeriesReactanceOhms" not in d.keys():
            d["SeriesReactanceOhms"] = None 
        elif not d["SeriesReactanceOhms"] is None:
            d["SeriesReactanceOhms"] = float(d["SeriesReactanceOhms"])
        if "ResistanceOhms" not in d.keys():
            d["ResistanceOhms"] = None 
        elif not d["ResistanceOhms"] is None:
            d["ResistanceOhms"] = float(d["ResistanceOhms"])
        if "MinStoreTempF" not in d.keys():
            d["MinStoreTempF"] = None
        if "RatedAmpacityRmsAmps" not in d.keys():
            d["RatedAmpacityRmsAmps"] = None 
        elif not d["RatedAmpacityRmsAmps"] is None:
            d["RatedAmpacityRmsAmps"] = float(d["RatedAmpacityRmsAmps"])
        if "MaxWChangeIn100Milliseconds" not in d.keys():
            d["MaxWChangeIn100Milliseconds"] = None
        if "StoreSizeGallons" not in d.keys():
            d["StoreSizeGallons"] = None
        if "DesignDayTempF" not in d.keys():
            d["DesignDayTempF"] = None
        if "RatedMaxInverterEfficiency" not in d.keys():
            d["RatedMaxInverterEfficiency"] = None 
        elif not d["RatedMaxInverterEfficiency"] is None:
            d["RatedMaxInverterEfficiency"] = float(d["RatedMaxInverterEfficiency"])
        if "PvTotalAreaM2" not in d.keys():
            d["PvTotalAreaM2"] = None 
        elif not d["PvTotalAreaM2"] is None:
            d["PvTotalAreaM2"] = float(d["PvTotalAreaM2"])
        if "AmbientTempStoreF" not in d.keys():
            d["AmbientTempStoreF"] = None
        if "Cop4TempF" not in d.keys():
            d["Cop4TempF"] = None
        if "VolatilityPercent" not in d.keys():
            d["VolatilityPercent"] = None
        if "Cop1TempF" not in d.keys():
            d["Cop1TempF"] = None
        if "ExcitationSystemPowerFactorLimit" not in d.keys():
            d["ExcitationSystemPowerFactorLimit"] = None 
        elif not d["ExcitationSystemPowerFactorLimit"] is None:
            d["ExcitationSystemPowerFactorLimit"] = float(d["ExcitationSystemPowerFactorLimit"])
        if "ColdStartSeconds" not in d.keys():
            d["ColdStartSeconds"] = None 
        elif not d["ColdStartSeconds"] is None:
            d["ColdStartSeconds"] = float(d["ColdStartSeconds"])
        if "StorePassiveLossRatio" not in d.keys():
            d["StorePassiveLossRatio"] = None 
        elif not d["StorePassiveLossRatio"] is None:
            d["StorePassiveLossRatio"] = float(d["StorePassiveLossRatio"])
        if "RatedPowerWithdrawnVa" not in d.keys():
            d["RatedPowerWithdrawnVa"] = None
        if "HeatCapacityWhperDegC" not in d.keys():
            d["HeatCapacityWhperDegC"] = None 
        elif not d["HeatCapacityWhperDegC"] is None:
            d["HeatCapacityWhperDegC"] = float(d["HeatCapacityWhperDegC"])
        if "ModelNumber" not in d.keys():
            d["ModelNumber"] = None
        if "MaxStoreTempF" not in d.keys():
            d["MaxStoreTempF"] = None
        if "MaxRampDownFractionPerSecond" not in d.keys():
            d["MaxRampDownFractionPerSecond"] = None 
        elif not d["MaxRampDownFractionPerSecond"] is None:
            d["MaxRampDownFractionPerSecond"] = float(d["MaxRampDownFractionPerSecond"])
        if "RatedVoltageVrms" not in d.keys():
            d["RatedVoltageVrms"] = None
        if "WorldInstanceAlias" not in d.keys():
            d["WorldInstanceAlias"] = None
        p = GtComponentAttributeClass110(MpAlias=d["MpAlias"],
                        NormalizedEquivInertia=d["NormalizedEquivInertia"],
                        StartupSeconds=d["StartupSeconds"],
                        MaxBoostPowerKw=d["MaxBoostPowerKw"],
                        MaxRampUpFractionPerSecond=d["MaxRampUpFractionPerSecond"],
                        RatedPowerInjectedVa=d["RatedPowerInjectedVa"],
                        ShutdownSeconds=d["ShutdownSeconds"],
                        ShuntReactanceDefaultOhms=d["ShuntReactanceDefaultOhms"],
                        MaxHeatpumpPowerKw=d["MaxHeatpumpPowerKw"],
                        SeriesReactanceOhms=d["SeriesReactanceOhms"],
                        ResistanceOhms=d["ResistanceOhms"],
                        MinStoreTempF=d["MinStoreTempF"],
                        RatedAmpacityRmsAmps=d["RatedAmpacityRmsAmps"],
                        ComponentAttributeClassId=d["ComponentAttributeClassId"],
                        MaxWChangeIn100Milliseconds=d["MaxWChangeIn100Milliseconds"],
                        StoreSizeGallons=d["StoreSizeGallons"],
                        DesignDayTempF=d["DesignDayTempF"],
                        RatedMaxInverterEfficiency=d["RatedMaxInverterEfficiency"],
                        PvTotalAreaM2=d["PvTotalAreaM2"],
                        AmbientTempStoreF=d["AmbientTempStoreF"],
                        ComponentTypeValue=d["ComponentTypeValue"],
                        Cop4TempF=d["Cop4TempF"],
                        VolatilityPercent=d["VolatilityPercent"],
                        Cop1TempF=d["Cop1TempF"],
                        ExcitationSystemPowerFactorLimit=d["ExcitationSystemPowerFactorLimit"],
                        ColdStartSeconds=d["ColdStartSeconds"],
                        StorePassiveLossRatio=d["StorePassiveLossRatio"],
                        RatedPowerWithdrawnVa=d["RatedPowerWithdrawnVa"],
                        HeatCapacityWhperDegC=d["HeatCapacityWhperDegC"],
                        ModelNumber=d["ModelNumber"],
                        MaxStoreTempF=d["MaxStoreTempF"],
                        MaxRampDownFractionPerSecond=d["MaxRampDownFractionPerSecond"],
                        RatedVoltageVrms=d["RatedVoltageVrms"],
                        ComponentManufacturerValue=d["ComponentManufacturerValue"])
        is_valid, errors = p.is_valid()
        if not is_valid:
            raise MpSchemaError(errors)
        return p 

    @classmethod
    def data_class_to_schema_type(cls,dc:ComponentAttributeClass) -> GtComponentAttributeClass110:
        if dc is None:
            return None
        candidate = GtComponentAttributeClass110(MpAlias='gt.component.attribute.class.1_1_0',
                        NormalizedEquivInertia=dc.normalized_equiv_inertia,
                        StartupSeconds=dc.startup_seconds,
                        MaxBoostPowerKw=dc.max_boost_power_kw,
                        MaxRampUpFractionPerSecond=dc.max_ramp_up_fraction_per_second,
                        RatedPowerInjectedVa=dc.rated_power_injected_va,
                        ShutdownSeconds=dc.shutdown_seconds,
                        ShuntReactanceDefaultOhms=dc.shunt_reactance_default_ohms,
                        MaxHeatpumpPowerKw=dc.max_heatpump_power_kw,
                        SeriesReactanceOhms=dc.series_reactance_ohms,
                        ResistanceOhms=dc.resistance_ohms,
                        MinStoreTempF=dc.min_store_temp_f,
                        RatedAmpacityRmsAmps=dc.rated_ampacity_rms_amps,
                        ComponentAttributeClassId=dc.component_attribute_class_id,
                        MaxWChangeIn100Milliseconds=dc.max_w_change_in100_milliseconds,
                        StoreSizeGallons=dc.store_size_gallons,
                        DesignDayTempF=dc.design_day_temp_f,
                        RatedMaxInverterEfficiency=dc.rated_max_inverter_efficiency,
                        PvTotalAreaM2=dc.pv_total_area_m2,
                        AmbientTempStoreF=dc.ambient_temp_store_f,
                        ComponentTypeValue=dc.component_type_value,
                        Cop4TempF=dc.cop4_temp_f,
                        VolatilityPercent=dc.volatility_percent,
                        Cop1TempF=dc.cop1_temp_f,
                        ExcitationSystemPowerFactorLimit=dc.excitation_system_power_factor_limit,
                        ColdStartSeconds=dc.cold_start_seconds,
                        StorePassiveLossRatio=dc.store_passive_loss_ratio,
                        RatedPowerWithdrawnVa=dc.rated_power_withdrawn_va,
                        HeatCapacityWhperDegC=dc.heat_capacity_whper_deg_c,
                        ModelNumber=dc.model_number,
                        MaxStoreTempF=dc.max_store_temp_f,
                        MaxRampDownFractionPerSecond=dc.max_ramp_down_fraction_per_second,
                        RatedVoltageVrms=dc.rated_voltage_vrms,
                        ComponentManufacturerValue=dc.component_manufacturer_value)
        is_valid, errors = candidate.is_valid()
        if not is_valid:
            raise MpSchemaError(errors)
        else:
            return candidate
    
    @classmethod
    def schema_type_to_data_class(cls,p:GtComponentAttributeClass110) -> ComponentAttributeClass:
        if p is None:
            return None
        snake_dict = {}
        snake_dict['normalized_equiv_inertia']=p.NormalizedEquivInertia
        snake_dict['startup_seconds']=p.StartupSeconds
        snake_dict['max_boost_power_kw']=p.MaxBoostPowerKw
        snake_dict['max_ramp_up_fraction_per_second']=p.MaxRampUpFractionPerSecond
        snake_dict['rated_power_injected_va']=p.RatedPowerInjectedVa
        snake_dict['shutdown_seconds']=p.ShutdownSeconds
        snake_dict['shunt_reactance_default_ohms']=p.ShuntReactanceDefaultOhms
        snake_dict['max_heatpump_power_kw']=p.MaxHeatpumpPowerKw
        snake_dict['series_reactance_ohms']=p.SeriesReactanceOhms
        snake_dict['resistance_ohms']=p.ResistanceOhms
        snake_dict['min_store_temp_f']=p.MinStoreTempF
        snake_dict['rated_ampacity_rms_amps']=p.RatedAmpacityRmsAmps
        snake_dict['component_attribute_class_id']=p.ComponentAttributeClassId
        snake_dict['max_w_change_in100_milliseconds']=p.MaxWChangeIn100Milliseconds
        snake_dict['store_size_gallons']=p.StoreSizeGallons
        snake_dict['design_day_temp_f']=p.DesignDayTempF
        snake_dict['rated_max_inverter_efficiency']=p.RatedMaxInverterEfficiency
        snake_dict['pv_total_area_m2']=p.PvTotalAreaM2
        snake_dict['ambient_temp_store_f']=p.AmbientTempStoreF
        snake_dict['component_type_value']=p.ComponentTypeValue
        snake_dict['cop4_temp_f']=p.Cop4TempF
        snake_dict['volatility_percent']=p.VolatilityPercent
        snake_dict['cop1_temp_f']=p.Cop1TempF
        snake_dict['excitation_system_power_factor_limit']=p.ExcitationSystemPowerFactorLimit
        snake_dict['cold_start_seconds']=p.ColdStartSeconds
        snake_dict['store_passive_loss_ratio']=p.StorePassiveLossRatio
        snake_dict['rated_power_withdrawn_va']=p.RatedPowerWithdrawnVa
        snake_dict['heat_capacity_whper_deg_c']=p.HeatCapacityWhperDegC
        snake_dict['model_number']=p.ModelNumber
        snake_dict['max_store_temp_f']=p.MaxStoreTempF
        snake_dict['max_ramp_down_fraction_per_second']=p.MaxRampDownFractionPerSecond
        snake_dict['rated_voltage_vrms']=p.RatedVoltageVrms
        snake_dict['component_manufacturer_value']=p.ComponentManufacturerValue
        if snake_dict['component_attribute_class_id'] in ComponentAttributeClass.by_id.keys():
            component_attribute_class = ComponentAttributeClass.by_id[snake_dict['component_attribute_class_id']]
            try:
                component_attribute_class.check_update_consistency(snake_dict)
            except DcError or DataClassLoadingError as err:
                print(f'Not updating or returning ComponentAttributeClass: {err}')
                return None
            except KeyError as err:
                print(f'Not updating or returning ComponentAttributeClass: {err}')
                return None

            for key, value in snake_dict.items():
                if hasattr(component_attribute_class, key):
                    setattr(component_attribute_class, key, value)
        else:
            component_attribute_class = ComponentAttributeClass(**snake_dict)

        return component_attribute_class

    @classmethod
    def type_is_valid(cls, payload_as_dict: Dict[str, Any]) -> Tuple[bool, Optional[List[str]]]:
        try:
            p = cls.camel_dict_to_schema_type(payload_as_dict)
        except MpSchemaError as e:
            errors = [e]
            return False, errors
        return p.is_valid()

    def __init__(self,
                 component_attribute_class_id: str,
                 component_type_value: str,
                 component_manufacturer_value: str,
                 normalized_equiv_inertia: Optional[float] = None ,
                 startup_seconds: Optional[int] = None ,
                 max_boost_power_kw: Optional[float] = None ,
                 max_ramp_up_fraction_per_second: Optional[float] = None ,
                 rated_power_injected_va: Optional[int] = None ,
                 shutdown_seconds: Optional[int] = None ,
                 shunt_reactance_default_ohms: Optional[float] = None ,
                 max_heatpump_power_kw: Optional[float] = None ,
                 series_reactance_ohms: Optional[float] = None ,
                 resistance_ohms: Optional[float] = None ,
                 min_store_temp_f: Optional[int] = None ,
                 rated_ampacity_rms_amps: Optional[float] = None ,
                 max_w_change_in100_milliseconds: Optional[int] = None ,
                 store_size_gallons: Optional[int] = None ,
                 design_day_temp_f: Optional[int] = None ,
                 rated_max_inverter_efficiency: Optional[float] = None ,
                 pv_total_area_m2: Optional[float] = None ,
                 ambient_temp_store_f: Optional[int] = None ,
                 cop4_temp_f: Optional[int] = None ,
                 volatility_percent: Optional[int] = None ,
                 cop1_temp_f: Optional[int] = None ,
                 excitation_system_power_factor_limit: Optional[float] = None ,
                 cold_start_seconds: Optional[float] = None ,
                 store_passive_loss_ratio: Optional[float] = None ,
                 rated_power_withdrawn_va: Optional[int] = None ,
                 heat_capacity_whper_deg_c: Optional[float] = None ,
                 model_number: Optional[str] = None ,
                 max_store_temp_f: Optional[int] = None ,
                 max_ramp_down_fraction_per_second: Optional[float] = None ,
                 rated_voltage_vrms: Optional[int] = None ):
        self.errors = []
        try:
            normalized_equiv_inertia = float(normalized_equiv_inertia)
        except ValueError:
            pass # This will get caught in is_valid() check below
        try:
            max_boost_power_kw = float(max_boost_power_kw)
        except ValueError:
            pass # This will get caught in is_valid() check below
        try:
            max_ramp_up_fraction_per_second = float(max_ramp_up_fraction_per_second)
        except ValueError:
            pass # This will get caught in is_valid() check below
        try:
            shunt_reactance_default_ohms = float(shunt_reactance_default_ohms)
        except ValueError:
            pass # This will get caught in is_valid() check below
        try:
            max_heatpump_power_kw = float(max_heatpump_power_kw)
        except ValueError:
            pass # This will get caught in is_valid() check below
        try:
            series_reactance_ohms = float(series_reactance_ohms)
        except ValueError:
            pass # This will get caught in is_valid() check below
        try:
            resistance_ohms = float(resistance_ohms)
        except ValueError:
            pass # This will get caught in is_valid() check below
        try:
            rated_ampacity_rms_amps = float(rated_ampacity_rms_amps)
        except ValueError:
            pass # This will get caught in is_valid() check below
        try:
            rated_max_inverter_efficiency = float(rated_max_inverter_efficiency)
        except ValueError:
            pass # This will get caught in is_valid() check below
        try:
            pv_total_area_m2 = float(pv_total_area_m2)
        except ValueError:
            pass # This will get caught in is_valid() check below
        try:
            excitation_system_power_factor_limit = float(excitation_system_power_factor_limit)
        except ValueError:
            pass # This will get caught in is_valid() check below
        try:
            cold_start_seconds = float(cold_start_seconds)
        except ValueError:
            pass # This will get caught in is_valid() check below
        try:
            store_passive_loss_ratio = float(store_passive_loss_ratio)
        except ValueError:
            pass # This will get caught in is_valid() check below
        try:
            heat_capacity_whper_deg_c = float(heat_capacity_whper_deg_c)
        except ValueError:
            pass # This will get caught in is_valid() check below
        try:
            max_ramp_down_fraction_per_second = float(max_ramp_down_fraction_per_second)
        except ValueError:
            pass # This will get caught in is_valid() check below

        t = GtComponentAttributeClass110(MpAlias=Gt_Component_Attribute_Class_1_1_0.mp_alias,
                    NormalizedEquivInertia=normalized_equiv_inertia,
                    StartupSeconds=startup_seconds,
                    MaxBoostPowerKw=max_boost_power_kw,
                    MaxRampUpFractionPerSecond=max_ramp_up_fraction_per_second,
                    RatedPowerInjectedVa=rated_power_injected_va,
                    ShutdownSeconds=shutdown_seconds,
                    ShuntReactanceDefaultOhms=shunt_reactance_default_ohms,
                    MaxHeatpumpPowerKw=max_heatpump_power_kw,
                    SeriesReactanceOhms=series_reactance_ohms,
                    ResistanceOhms=resistance_ohms,
                    MinStoreTempF=min_store_temp_f,
                    RatedAmpacityRmsAmps=rated_ampacity_rms_amps,
                    ComponentAttributeClassId=component_attribute_class_id,
                    MaxWChangeIn100Milliseconds=max_w_change_in100_milliseconds,
                    StoreSizeGallons=store_size_gallons,
                    DesignDayTempF=design_day_temp_f,
                    RatedMaxInverterEfficiency=rated_max_inverter_efficiency,
                    PvTotalAreaM2=pv_total_area_m2,
                    AmbientTempStoreF=ambient_temp_store_f,
                    ComponentTypeValue=component_type_value,
                    Cop4TempF=cop4_temp_f,
                    VolatilityPercent=volatility_percent,
                    Cop1TempF=cop1_temp_f,
                    ExcitationSystemPowerFactorLimit=excitation_system_power_factor_limit,
                    ColdStartSeconds=cold_start_seconds,
                    StorePassiveLossRatio=store_passive_loss_ratio,
                    RatedPowerWithdrawnVa=rated_power_withdrawn_va,
                    HeatCapacityWhperDegC=heat_capacity_whper_deg_c,
                    ModelNumber=model_number,
                    MaxStoreTempF=max_store_temp_f,
                    MaxRampDownFractionPerSecond=max_ramp_down_fraction_per_second,
                    RatedVoltageVrms=rated_voltage_vrms,
                    ComponentManufacturerValue=component_manufacturer_value)

        is_valid, errors = t.is_valid()
        if is_valid is False:
            raise MpSchemaError(f"Failed to create payload due to these errors: {errors}")
        self.type = t

