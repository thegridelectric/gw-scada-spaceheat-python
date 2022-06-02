from typing import Dict

from data_classes.component_sub_category import ComponentSubCategory

PlatformComponentSubCategory: Dict[str, ComponentSubCategory] = {}


"""GENERIC_BATTERY
"""
GENERIC_BATTERY = ComponentSubCategory(value="GenericBattery",
                                       component_category_value="Battery")

PlatformComponentSubCategory[GENERIC_BATTERY.value] = GENERIC_BATTERY


"""GENERIC_GENERATOR
"""
GENERIC_GENERATOR = ComponentSubCategory(value="GenericGenerator",
                                         component_category_value="Generator")

PlatformComponentSubCategory[GENERIC_GENERATOR.value] = GENERIC_GENERATOR


"""GENERIC_LOAD
"""
GENERIC_LOAD = ComponentSubCategory(value="GenericLoad",
                                    component_category_value="Load")

PlatformComponentSubCategory[GENERIC_LOAD.value] = GENERIC_LOAD


"""SPACE_HEAT: Device responsible for heating a commercial or industrial space
"""
SPACE_HEAT = ComponentSubCategory(value="SpaceHeat",
                                  component_category_value="Load")

PlatformComponentSubCategory[SPACE_HEAT.value] = SPACE_HEAT


"""GENERIC_INTERCONNECTOR
"""
GENERIC_INTERCONNECTOR = ComponentSubCategory(value="GenericInterconnector",
                                              component_category_value="Interconnector")

PlatformComponentSubCategory[GENERIC_INTERCONNECTOR.value] = GENERIC_INTERCONNECTOR


"""PUMPED_HYDRO
"""
PUMPED_HYDRO = ComponentSubCategory(value="PumpedHydro",
                                    component_category_value="Battery")

PlatformComponentSubCategory[PUMPED_HYDRO.value] = PUMPED_HYDRO


"""GENERIC_BUILDING
"""
GENERIC_BUILDING = ComponentSubCategory(value="GenericBuilding",
                                        component_category_value="Building")

PlatformComponentSubCategory[GENERIC_BUILDING.value] = GENERIC_BUILDING
