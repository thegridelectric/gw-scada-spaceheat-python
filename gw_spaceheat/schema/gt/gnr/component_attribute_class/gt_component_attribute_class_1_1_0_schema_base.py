"""SchemaBase for gt.component.attribute.class.1_1_0"""
from typing import List, Dict, Tuple, Optional, NamedTuple
import schema.property_format


class SchemaBase(NamedTuple):
    ComponentAttributeClassId: str     #
    ComponentTypeValue: str     #
    ComponentManufacturerValue: str     #
    NormalizedEquivInertia: Optional[float] = None
    StartupSeconds: Optional[int] = None
    MaxBoostPowerKw: Optional[float] = None
    MaxRampUpFractionPerSecond: Optional[float] = None
    RatedPowerInjectedVa: Optional[int] = None
    ShutdownSeconds: Optional[int] = None
    ShuntReactanceDefaultOhms: Optional[float] = None
    MaxHeatpumpPowerKw: Optional[float] = None
    SeriesReactanceOhms: Optional[float] = None
    ResistanceOhms: Optional[float] = None
    MinStoreTempF: Optional[int] = None
    RatedAmpacityRmsAmps: Optional[float] = None
    MaxWChangeIn100Milliseconds: Optional[int] = None
    StoreSizeGallons: Optional[int] = None
    DesignDayTempF: Optional[int] = None
    RatedMaxInverterEfficiency: Optional[float] = None
    PvTotalAreaM2: Optional[float] = None
    AmbientTempStoreF: Optional[int] = None
    Cop4TempF: Optional[int] = None
    VolatilityPercent: Optional[int] = None
    Cop1TempF: Optional[int] = None
    ExcitationSystemPowerFactorLimit: Optional[float] = None
    ColdStartSeconds: Optional[float] = None
    StorePassiveLossRatio: Optional[float] = None
    RatedPowerWithdrawnVa: Optional[int] = None
    HeatCapacityWhperDegC: Optional[float] = None
    ModelNumber: Optional[str] = None
    MaxStoreTempF: Optional[int] = None
    MaxRampDownFractionPerSecond: Optional[float] = None
    RatedVoltageVrms: Optional[int] = None
    MpAlias: str = 'gt.component.attribute.class.1_1_0'

    def asdict(self):
        d = self._asdict()
        if d["NormalizedEquivInertia"] is None:
            del d["NormalizedEquivInertia"]
        if d["StartupSeconds"] is None:
            del d["StartupSeconds"]
        if d["MaxBoostPowerKw"] is None:
            del d["MaxBoostPowerKw"]
        if d["MaxRampUpFractionPerSecond"] is None:
            del d["MaxRampUpFractionPerSecond"]
        if d["RatedPowerInjectedVa"] is None:
            del d["RatedPowerInjectedVa"]
        if d["ShutdownSeconds"] is None:
            del d["ShutdownSeconds"]
        if d["ShuntReactanceDefaultOhms"] is None:
            del d["ShuntReactanceDefaultOhms"]
        if d["MaxHeatpumpPowerKw"] is None:
            del d["MaxHeatpumpPowerKw"]
        if d["SeriesReactanceOhms"] is None:
            del d["SeriesReactanceOhms"]
        if d["ResistanceOhms"] is None:
            del d["ResistanceOhms"]
        if d["MinStoreTempF"] is None:
            del d["MinStoreTempF"]
        if d["RatedAmpacityRmsAmps"] is None:
            del d["RatedAmpacityRmsAmps"]
        if d["MaxWChangeIn100Milliseconds"] is None:
            del d["MaxWChangeIn100Milliseconds"]
        if d["StoreSizeGallons"] is None:
            del d["StoreSizeGallons"]
        if d["DesignDayTempF"] is None:
            del d["DesignDayTempF"]
        if d["RatedMaxInverterEfficiency"] is None:
            del d["RatedMaxInverterEfficiency"]
        if d["PvTotalAreaM2"] is None:
            del d["PvTotalAreaM2"]
        if d["AmbientTempStoreF"] is None:
            del d["AmbientTempStoreF"]
        if d["Cop4TempF"] is None:
            del d["Cop4TempF"]
        if d["VolatilityPercent"] is None:
            del d["VolatilityPercent"]
        if d["Cop1TempF"] is None:
            del d["Cop1TempF"]
        if d["ExcitationSystemPowerFactorLimit"] is None:
            del d["ExcitationSystemPowerFactorLimit"]
        if d["ColdStartSeconds"] is None:
            del d["ColdStartSeconds"]
        if d["StorePassiveLossRatio"] is None:
            del d["StorePassiveLossRatio"]
        if d["RatedPowerWithdrawnVa"] is None:
            del d["RatedPowerWithdrawnVa"]
        if d["HeatCapacityWhperDegC"] is None:
            del d["HeatCapacityWhperDegC"]
        if d["ModelNumber"] is None:
            del d["ModelNumber"]
        if d["MaxStoreTempF"] is None:
            del d["MaxStoreTempF"]
        if d["MaxRampDownFractionPerSecond"] is None:
            del d["MaxRampDownFractionPerSecond"]
        if d["RatedVoltageVrms"] is None:
            del d["RatedVoltageVrms"]
        return d

    def passes_derived_validations(self) -> Tuple[bool, Optional[List[str]]]:
        is_valid = True
        errors = []
        if self.MpAlias != 'gt.component.attribute.class.1_1_0':
            is_valid = False
            errors.append(f"Payload requires MpAlias of gt.component.attribute.class.1_1_0, not {self.MpAlias}.")
        if not isinstance(self.ComponentAttributeClassId, str):
            is_valid = False
            errors.append(f"ComponentAttributeClassId {self.ComponentAttributeClassId} must have type str.")
        if not schema.property_format.is_uuid_canonical_textual(self.ComponentAttributeClassId):
            is_valid = False
            errors.append(f"ComponentAttributeClassId {self.ComponentAttributeClassId} must have format UuidCanonicalTextual.")
        if not isinstance(self.ComponentTypeValue, str):
            is_valid = False
            errors.append(f"ComponentTypeValue {self.ComponentTypeValue} must have type str.")
        if not schema.property_format.is_recognized_component_type(self.ComponentTypeValue):
            is_valid = False
            errors.append(f"ComponentTypeValue {self.ComponentTypeValue} must have format RecognizedComponentType.")
        if not isinstance(self.ComponentManufacturerValue, str):
            is_valid = False
            errors.append(f"ComponentManufacturerValue {self.ComponentManufacturerValue} must have type str.")
        if not schema.property_format.is_recognized_component_manufacturer(self.ComponentManufacturerValue):
            is_valid = False
            errors.append(f"ComponentManufacturerValue {self.ComponentManufacturerValue} must have format RecognizedComponentManufacturer.")
        if self.NormalizedEquivInertia:
            if not isinstance(self.NormalizedEquivInertia, float):
                is_valid = False
                errors.append(f"NormalizedEquivInertia {self.NormalizedEquivInertia} must have type float.")
        if self.StartupSeconds:
            if not isinstance(self.StartupSeconds, int):
                is_valid = False
                errors.append(f"StartupSeconds {self.StartupSeconds} must have type int.")
        if self.MaxBoostPowerKw:
            if not isinstance(self.MaxBoostPowerKw, float):
                is_valid = False
                errors.append(f"MaxBoostPowerKw {self.MaxBoostPowerKw} must have type float.")
        if self.MaxRampUpFractionPerSecond:
            if not isinstance(self.MaxRampUpFractionPerSecond, float):
                is_valid = False
                errors.append(f"MaxRampUpFractionPerSecond {self.MaxRampUpFractionPerSecond} must have type float.")
        if self.RatedPowerInjectedVa:
            if not isinstance(self.RatedPowerInjectedVa, int):
                is_valid = False
                errors.append(f"RatedPowerInjectedVa {self.RatedPowerInjectedVa} must have type int.")
        if self.ShutdownSeconds:
            if not isinstance(self.ShutdownSeconds, int):
                is_valid = False
                errors.append(f"ShutdownSeconds {self.ShutdownSeconds} must have type int.")
        if self.ShuntReactanceDefaultOhms:
            if not isinstance(self.ShuntReactanceDefaultOhms, float):
                is_valid = False
                errors.append(f"ShuntReactanceDefaultOhms {self.ShuntReactanceDefaultOhms} must have type float.")
        if self.MaxHeatpumpPowerKw:
            if not isinstance(self.MaxHeatpumpPowerKw, float):
                is_valid = False
                errors.append(f"MaxHeatpumpPowerKw {self.MaxHeatpumpPowerKw} must have type float.")
        if self.SeriesReactanceOhms:
            if not isinstance(self.SeriesReactanceOhms, float):
                is_valid = False
                errors.append(f"SeriesReactanceOhms {self.SeriesReactanceOhms} must have type float.")
        if self.ResistanceOhms:
            if not isinstance(self.ResistanceOhms, float):
                is_valid = False
                errors.append(f"ResistanceOhms {self.ResistanceOhms} must have type float.")
        if self.MinStoreTempF:
            if not isinstance(self.MinStoreTempF, int):
                is_valid = False
                errors.append(f"MinStoreTempF {self.MinStoreTempF} must have type int.")
        if self.RatedAmpacityRmsAmps:
            if not isinstance(self.RatedAmpacityRmsAmps, float):
                is_valid = False
                errors.append(f"RatedAmpacityRmsAmps {self.RatedAmpacityRmsAmps} must have type float.")
        if self.MaxWChangeIn100Milliseconds:
            if not isinstance(self.MaxWChangeIn100Milliseconds, int):
                is_valid = False
                errors.append(f"MaxWChangeIn100Milliseconds {self.MaxWChangeIn100Milliseconds} must have type int.")
        if self.StoreSizeGallons:
            if not isinstance(self.StoreSizeGallons, int):
                is_valid = False
                errors.append(f"StoreSizeGallons {self.StoreSizeGallons} must have type int.")
        if self.DesignDayTempF:
            if not isinstance(self.DesignDayTempF, int):
                is_valid = False
                errors.append(f"DesignDayTempF {self.DesignDayTempF} must have type int.")
        if self.RatedMaxInverterEfficiency:
            if not isinstance(self.RatedMaxInverterEfficiency, float):
                is_valid = False
                errors.append(f"RatedMaxInverterEfficiency {self.RatedMaxInverterEfficiency} must have type float.")
        if self.PvTotalAreaM2:
            if not isinstance(self.PvTotalAreaM2, float):
                is_valid = False
                errors.append(f"PvTotalAreaM2 {self.PvTotalAreaM2} must have type float.")
        if self.AmbientTempStoreF:
            if not isinstance(self.AmbientTempStoreF, int):
                is_valid = False
                errors.append(f"AmbientTempStoreF {self.AmbientTempStoreF} must have type int.")
        if self.Cop4TempF:
            if not isinstance(self.Cop4TempF, int):
                is_valid = False
                errors.append(f"Cop4TempF {self.Cop4TempF} must have type int.")
        if self.VolatilityPercent:
            if not isinstance(self.VolatilityPercent, int):
                is_valid = False
                errors.append(f"VolatilityPercent {self.VolatilityPercent} must have type int.")
        if self.Cop1TempF:
            if not isinstance(self.Cop1TempF, int):
                is_valid = False
                errors.append(f"Cop1TempF {self.Cop1TempF} must have type int.")
        if self.ExcitationSystemPowerFactorLimit:
            if not isinstance(self.ExcitationSystemPowerFactorLimit, float):
                is_valid = False
                errors.append(f"ExcitationSystemPowerFactorLimit {self.ExcitationSystemPowerFactorLimit} must have type float.")
        if self.ColdStartSeconds:
            if not isinstance(self.ColdStartSeconds, float):
                is_valid = False
                errors.append(f"ColdStartSeconds {self.ColdStartSeconds} must have type float.")
        if self.StorePassiveLossRatio:
            if not isinstance(self.StorePassiveLossRatio, float):
                is_valid = False
                errors.append(f"StorePassiveLossRatio {self.StorePassiveLossRatio} must have type float.")
        if self.RatedPowerWithdrawnVa:
            if not isinstance(self.RatedPowerWithdrawnVa, int):
                is_valid = False
                errors.append(f"RatedPowerWithdrawnVa {self.RatedPowerWithdrawnVa} must have type int.")
        if self.HeatCapacityWhperDegC:
            if not isinstance(self.HeatCapacityWhperDegC, float):
                is_valid = False
                errors.append(f"HeatCapacityWhperDegC {self.HeatCapacityWhperDegC} must have type float.")
        if self.ModelNumber:
            if not isinstance(self.ModelNumber, str):
                is_valid = False
                errors.append(f"ModelNumber {self.ModelNumber} must have type str.")
        if self.MaxStoreTempF:
            if not isinstance(self.MaxStoreTempF, int):
                is_valid = False
                errors.append(f"MaxStoreTempF {self.MaxStoreTempF} must have type int.")
        if self.MaxRampDownFractionPerSecond:
            if not isinstance(self.MaxRampDownFractionPerSecond, float):
                is_valid = False
                errors.append(f"MaxRampDownFractionPerSecond {self.MaxRampDownFractionPerSecond} must have type float.")
        if self.RatedVoltageVrms:
            if not isinstance(self.RatedVoltageVrms, int):
                is_valid = False
                errors.append(f"RatedVoltageVrms {self.RatedVoltageVrms} must have type int.")
        return is_valid, errors

