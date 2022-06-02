from typing import Dict

from data_classes.sh_node_role import ShNodeRole

PlatformShNodeRole: Dict[str, ShNodeRole] = {}

ELECTRIC_HEATER = ShNodeRole(alias="ElectricHeater",
                             has_heat_flow=True,
                             has_voltage=True,
                             has_stored_thermal_energy=False,
                             is_actuated=True)

PlatformShNodeRole[ELECTRIC_HEATER.alias] = ELECTRIC_HEATER

DEDICATED_THERMAL_STORE = ShNodeRole(alias="DedicatedThermalStore",
                                     has_heat_flow=False,
                                     has_voltage=False,
                                     has_stored_thermal_energy=True,
                                     is_actuated=False)

PlatformShNodeRole[DEDICATED_THERMAL_STORE.alias] = DEDICATED_THERMAL_STORE

CIRCULATOR_PUMP = ShNodeRole(alias="CirculatorPump",
                             has_heat_flow=False,
                             has_voltage=False,
                             has_stored_thermal_energy=False,
                             is_actuated=True)

PlatformShNodeRole[CIRCULATOR_PUMP.alias] = CIRCULATOR_PUMP

PASSIVE_ROOM_HEATER = ShNodeRole(alias="PassiveRoomHeater",
                                 has_heat_flow=True,
                                 has_voltage=False,
                                 has_stored_thermal_energy=False,
                                 is_actuated=False)

PlatformShNodeRole[PASSIVE_ROOM_HEATER.alias] = PASSIVE_ROOM_HEATER

HEATED_SPACE = ShNodeRole(alias="HeatedSpace",
                          has_heat_flow=False,
                          has_voltage=False,
                          has_stored_thermal_energy=True,
                          is_actuated=False)

PlatformShNodeRole[HEATED_SPACE.alias] = HEATED_SPACE


SENSOR = ShNodeRole(alias="Sensor",
                    has_heat_flow=False,
                    has_voltage=False,
                    has_stored_thermal_energy=False,
                    is_actuated=False)

PlatformShNodeRole[SENSOR.alias] = SENSOR

ACTUATOR = ShNodeRole(alias="Actuator",
                      has_heat_flow=False,
                      has_voltage=False,
                      has_stored_thermal_energy=False,
                      is_actuated=False)

PlatformShNodeRole[ACTUATOR.alias] = ACTUATOR

HYDRONIC_PIPE = ShNodeRole(alias="HydronicPipe",
                           has_heat_flow=True,
                           has_voltage=False,
                           has_stored_thermal_energy=False,
                           is_actuated=False)

PlatformShNodeRole[HYDRONIC_PIPE.alias] = HYDRONIC_PIPE

ATOMIC_T_NODE = ShNodeRole(alias="AtomicTNode",
                           has_heat_flow=False,
                           has_voltage=False,
                           has_stored_thermal_energy=False,
                           is_actuated=False)

PlatformShNodeRole[ATOMIC_T_NODE.alias] = ATOMIC_T_NODE

PRIMARY_SCADA = ShNodeRole(alias="PrimaryScada",
                           has_heat_flow=False,
                           has_voltage=False,
                           has_stored_thermal_energy=False,
                           is_actuated=True)

PlatformShNodeRole[PRIMARY_SCADA.alias] = PRIMARY_SCADA

OUTDOORS = ShNodeRole(alias="Outdoors",
                      has_heat_flow=False,
                      has_voltage=False,
                      has_stored_thermal_energy=True,
                      is_actuated=False)

PlatformShNodeRole[OUTDOORS.alias] = OUTDOORS


POWER_METER = ShNodeRole(alias="PowerMeter",
                         has_heat_flow=False,
                         has_voltage=False,
                         has_stored_thermal_energy=False,
                         is_actuated=False)

PlatformShNodeRole[POWER_METER.alias] = POWER_METER
