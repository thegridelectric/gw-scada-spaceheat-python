from typing import Dict

from data_classes.component_type import ComponentType

PlatformComponentType: Dict[str, ComponentType] = {}


"""CABLE
"""
CABLE = ComponentType(value="Cable",
                      display_name="Cable",
                      is_resistive_load=False,
                      component_sub_category_value="GenericInterconnector")

PlatformComponentType[CABLE.value] = CABLE


"""BATTERY
"""
BATTERY = ComponentType(value="Battery",
                        display_name="Chemical Battery",
                        is_resistive_load=False,
                        component_sub_category_value="GenericBattery")

PlatformComponentType[BATTERY.value] = BATTERY


"""PUMPED_HYDRO
"""
PUMPED_HYDRO = ComponentType(value="PumpedHydro",
                             display_name="Pumped Hydro",
                             is_resistive_load=False,
                             component_sub_category_value="PumpedHydro")

PlatformComponentType[PUMPED_HYDRO.value] = PUMPED_HYDRO


"""HYDRO
"""
HYDRO = ComponentType(value="Hydro",
                      display_name="Hydro",
                      is_resistive_load=False,
                      expected_startup_seconds=300,
                      expected_shutdown_seconds=300,
                      component_sub_category_value="GenericGenerator")

PlatformComponentType[HYDRO.value] = HYDRO


"""SPACE_HEAT_AIR_TO_WATER_HEAT_PUMP_AND_BOOST_WATER_HEAT_BATTERY
"""
SPACE_HEAT_AIR_TO_WATER_HEAT_PUMP_AND_BOOST_WATER_HEAT_BATTERY = ComponentType(value="SpaceHeatAirToWaterHeatPumpAndBoostWaterHeatBattery",
                                                                               display_name="Air to Water HeatPump with boost element and water heat battery",
                                                                               is_resistive_load=False,
                                                                               component_sub_category_value="SpaceHeat")

PlatformComponentType[SPACE_HEAT_AIR_TO_WATER_HEAT_PUMP_AND_BOOST_WATER_HEAT_BATTERY.value] = SPACE_HEAT_AIR_TO_WATER_HEAT_PUMP_AND_BOOST_WATER_HEAT_BATTERY


"""STORAGE_HEATER: An electric thermal storage heater. Ceramic bricks with resistive elements 
        stuck through them, surrounded with insulation. The better ones also have 
        a fan that can control the heat output.
"""
STORAGE_HEATER = ComponentType(value="StorageHeater",
                               display_name="Storage Heater",
                               is_resistive_load=True,
                               expected_startup_seconds=0.05,
                               expected_shutdown_seconds=0.05,
                               component_sub_category_value="SpaceHeat")

PlatformComponentType[STORAGE_HEATER.value] = STORAGE_HEATER


"""DIESEL: A diesel generator.
"""
DIESEL = ComponentType(value="Diesel",
                       display_name="Diesel",
                       is_resistive_load=False,
                       expected_startup_seconds=45,
                       expected_shutdown_seconds=15,
                       component_sub_category_value="GenericGenerator")

PlatformComponentType[DIESEL.value] = DIESEL


"""TRANSFORMER
"""
TRANSFORMER = ComponentType(value="Transformer",
                            display_name="Transformer",
                            is_resistive_load=False,
                            component_sub_category_value="GenericLoad")

PlatformComponentType[TRANSFORMER.value] = TRANSFORMER


"""SINGLE_ZONE_VERTICAL_AIR_HANDLER
"""
SINGLE_ZONE_VERTICAL_AIR_HANDLER = ComponentType(value="SingleZoneVerticalAirHandler",
                                                 display_name="Single Zone Vertical Air Handler",
                                                 is_resistive_load=False,
                                                 expected_startup_seconds=10,
                                                 expected_shutdown_seconds=10,
                                                 component_sub_category_value="GenericLoad")

PlatformComponentType[SINGLE_ZONE_VERTICAL_AIR_HANDLER.value] = SINGLE_ZONE_VERTICAL_AIR_HANDLER


"""SINGLE_FAMILY_DETACHED
"""
SINGLE_FAMILY_DETACHED = ComponentType(value="SingleFamilyDetached",
                                       display_name="Single Family Detached",
                                       is_resistive_load=False,
                                       component_sub_category_value="GenericBuilding")

PlatformComponentType[SINGLE_FAMILY_DETACHED.value] = SINGLE_FAMILY_DETACHED


"""VARIABLE_SPEED_MOTOR
"""
VARIABLE_SPEED_MOTOR = ComponentType(value="VariableSpeedMotor",
                                     display_name="Generic Variable Speed Motor",
                                     is_resistive_load=False,
                                     expected_startup_seconds=5,
                                     expected_shutdown_seconds=5,
                                     component_sub_category_value="GenericLoad")

PlatformComponentType[VARIABLE_SPEED_MOTOR.value] = VARIABLE_SPEED_MOTOR


"""FAN
"""
FAN = ComponentType(value="Fan",
                    display_name="Fan",
                    is_resistive_load=False,
                    component_sub_category_value="GenericLoad")

PlatformComponentType[FAN.value] = FAN


"""BLOWER
"""
BLOWER = ComponentType(value="Blower",
                       display_name="Generic Blower",
                       is_resistive_load=False,
                       component_sub_category_value="GenericLoad")

PlatformComponentType[BLOWER.value] = BLOWER


"""WIND
"""
WIND = ComponentType(value="Wind",
                     display_name="Wind",
                     is_resistive_load=False,
                     expected_startup_seconds=2.5,
                     expected_shutdown_seconds=2.5,
                     component_sub_category_value="GenericGenerator")

PlatformComponentType[WIND.value] = WIND


"""OVERHEAD_LINE
"""
OVERHEAD_LINE = ComponentType(value="OverheadLine",
                              display_name="Overhead Line",
                              is_resistive_load=False,
                              component_sub_category_value="GenericInterconnector")

PlatformComponentType[OVERHEAD_LINE.value] = OVERHEAD_LINE


"""INFINITESIMAL_CONNECTOR
"""
INFINITESIMAL_CONNECTOR = ComponentType(value="InfinitesimalConnector",
                                        display_name="Infinitesimal Connector",
                                        is_resistive_load=False,
                                        component_sub_category_value="GenericInterconnector")

PlatformComponentType[INFINITESIMAL_CONNECTOR.value] = INFINITESIMAL_CONNECTOR


"""TRANSPORT_CHILLER: A chilling device used inside trucks that can run on fuel or on electricity. 
        They arrive at a facility and plug in.
"""
TRANSPORT_CHILLER = ComponentType(value="TransportChiller",
                                  display_name="Transport Chiller",
                                  is_resistive_load=False,
                                  component_sub_category_value="GenericLoad")

PlatformComponentType[TRANSPORT_CHILLER.value] = TRANSPORT_CHILLER


"""SPACE_HEAT_AIR_TO_WATER_HEAT_PUMP_AND_BOOST
"""
SPACE_HEAT_AIR_TO_WATER_HEAT_PUMP_AND_BOOST = ComponentType(value="SpaceHeatAirToWaterHeatPumpAndBoost",
                                                            display_name="Air to Water HeatPump with boost element and water heat battery",
                                                            is_resistive_load=False,
                                                            component_sub_category_value="SpaceHeat")

PlatformComponentType[SPACE_HEAT_AIR_TO_WATER_HEAT_PUMP_AND_BOOST.value] = SPACE_HEAT_AIR_TO_WATER_HEAT_PUMP_AND_BOOST


"""SOLAR: Photo Voltaic generator.
"""
SOLAR = ComponentType(value="Solar",
                      display_name="Solar",
                      is_resistive_load=False,
                      expected_startup_seconds=7,
                      expected_shutdown_seconds=0,
                      component_sub_category_value="GenericGenerator")

PlatformComponentType[SOLAR.value] = SOLAR
