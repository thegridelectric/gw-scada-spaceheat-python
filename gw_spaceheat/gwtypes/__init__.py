
""" List of all the types used by SCADA """

# Types from gwproto
from gwproto.types.ads111x_based_cac_gt import Ads111xBasedCacGt
from gwproto.types.ads111x_based_cac_gt import Ads111xBasedCacGt_Maker
from gwproto.types.batched_readings import BatchedReadings
from gwproto.types.batched_readings import BatchedReadings_Maker
from gwproto.types.channel_config import ChannelConfig
from gwproto.types.channel_config import ChannelConfig_Maker
from gwproto.types.channel_readings import ChannelReadings
from gwproto.types.channel_readings import ChannelReadings_Maker
from gwproto.types.component_attribute_class_gt import ComponentAttributeClassGt
from gwproto.types.component_attribute_class_gt import ComponentAttributeClassGt_Maker
from gwproto.types.component_gt import ComponentGt
from gwproto.types.component_gt import ComponentGt_Maker
from gwproto.types.data_channel_gt import DataChannelGt
from gwproto.types.data_channel_gt import DataChannelGt_Maker
from gwproto.types.egauge_io import EgaugeIo
from gwproto.types.egauge_io import EgaugeIo_Maker
from gwproto.types.egauge_register_config import EgaugeRegisterConfig
from gwproto.types.egauge_register_config import EgaugeRegisterConfig_Maker
from gwproto.types.electric_meter_cac_gt import ElectricMeterCacGt
from gwproto.types.electric_meter_cac_gt import ElectricMeterCacGt_Maker
from gwproto.types.fsm_atomic_report import FsmAtomicReport
from gwproto.types.fsm_atomic_report import FsmAtomicReport_Maker
from gwproto.types.fsm_event import FsmEvent
from gwproto.types.fsm_event import FsmEvent_Maker
from gwproto.types.fsm_full_report import FsmFullReport
from gwproto.types.fsm_full_report import FsmFullReport_Maker
from gwproto.types.fsm_trigger_from_atn import FsmTriggerFromAtn
from gwproto.types.fsm_trigger_from_atn import FsmTriggerFromAtn_Maker
from gwproto.types.gt_sh_cli_atn_cmd import GtShCliAtnCmd
from gwproto.types.gt_sh_cli_atn_cmd import GtShCliAtnCmd_Maker
from gwproto.types.heartbeat_b import HeartbeatB
from gwproto.types.heartbeat_b import HeartbeatB_Maker
from gwproto.types.keyparam_change_log import KeyparamChangeLog
from gwproto.types.keyparam_change_log import KeyparamChangeLog_Maker
from gwproto.types.power_watts import PowerWatts
from gwproto.types.power_watts import PowerWatts_Maker
from gwproto.types.relay_actor_config import RelayActorConfig
from gwproto.types.relay_actor_config import RelayActorConfig_Maker
from gwproto.types.resistive_heater_cac_gt import ResistiveHeaterCacGt
from gwproto.types.resistive_heater_cac_gt import ResistiveHeaterCacGt_Maker
from gwproto.types.single_reading import SingleReading
from gwproto.types.single_reading import SingleReading_Maker
from gwproto.types.snapshot_spaceheat import Snapshot
from gwproto.types.snapshot_spaceheat import Snapshot_Maker
from gwproto.types.spaceheat_node_gt import SpaceheatNodeGt
from gwproto.types.spaceheat_node_gt import SpaceheatNodeGt_Maker
from gwproto.types.synced_readings import SyncedReadings
from gwproto.types.synced_readings import SyncedReadings_Maker
from gwproto.types.ta_data_channels import TaDataChannels
from gwproto.types.ta_data_channels import TaDataChannels_Maker
from gwproto.types.thermistor_data_processing_config import ThermistorDataProcessingConfig
from gwproto.types.thermistor_data_processing_config import ThermistorDataProcessingConfig_Maker


# Types from SCADA
from gwtypes.gt_powermeter_reporting_config import GtPowermeterReportingConfig
from gwtypes.gt_powermeter_reporting_config import GtPowermeterReportingConfig_Maker

__all__ = [
    "Ads111xBasedCacGt",
    "Ads111xBasedCacGt_Maker",
    # "Ads111xBasedComponentGt",
    # "Ads111xBasedComponentGt_Maker",
    "BatchedReadings",
    "BatchedReadings_Maker",
    "ChannelConfig",
    "ChannelConfig_Maker",
    "ChannelReadings",
    "ChannelReadings_Maker",
    "ComponentAttributeClassGt",
    "ComponentAttributeClassGt_Maker",
    "ComponentGt",
    "ComponentGt_Maker",
    "DataChannelGt",
    "DataChannelGt_Maker",
    "EgaugeIo",
    "EgaugeIo_Maker",
    "EgaugeRegisterConfig",
    "EgaugeRegisterConfig_Maker",
    "ElectricMeterCacGt",
    "ElectricMeterCacGt_Maker",
    # "ElectricMeterComponentGt",
    # "ElectricMeterComponentGt_Maker",
    # "FibaroSmartImplantComponentGt",
    # "FibaroSmartImplantComponentGt_Maker",
    "FsmAtomicReport",
    "FsmAtomicReport_Maker",
    "FsmEvent",
    "FsmEvent_Maker",
    "FsmFullReport",
    "FsmFullReport_Maker",
    "FsmTriggerFromAtn",
    "FsmTriggerFromAtn_Maker",
    "GtPowermeterReportingConfig",
    "GtPowermeterReportingConfig_Maker",
    "GtShCliAtnCmd",
    "GtShCliAtnCmd_Maker",
    "HeartbeatB",
    "HeartbeatB_Maker",
    # "HubitatComponentGt",
    # "HubitatComponentGt_Maker",
    # "HubitatPollerComponentGt",
    # "HubitatPollerComponentGt_Maker",
    # "HubitatTankComponentGt",
    # "HubitatTankComponentGt_Maker",
    # "I2cFlowTotalizerComponentGt",
    # "I2cFlowTotalizerComponentGt_Maker",
    # "I2cMultichannelDtRelayComponentGt",
    # "I2cMultichannelDtRelayComponentGt_Maker",
    "KeyparamChangeLog",
    "KeyparamChangeLog_Maker",
    "PowerWatts",
    "PowerWatts_Maker",
    "RelayActorConfig",
    "RelayActorConfig_Maker",
    "ResistiveHeaterCacGt",
    "ResistiveHeaterCacGt_Maker",
    # "ResistiveHeaterComponentGt",
    # "ResistiveHeaterComponentGt_Maker",
    # "RESTPollerComponentGt",
    # "RESTPollerComponentGt_Maker",
    "SingleReading",
    "SingleReading_Maker",
    "Snapshot",
    "Snapshot_Maker",
    "SpaceheatNodeGt",
    "SpaceheatNodeGt_Maker",
    "SyncedReadings",
    "SyncedReadings_Maker",
    "TaDataChannels",
    "TaDataChannels_Maker",
    "ThermistorDataProcessingConfig",
    "ThermistorDataProcessingConfig_Maker",
]