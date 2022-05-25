from typing import Dict
from data_classes.component_category import ComponentCategory
PlatformComponentCategory: Dict[str,ComponentCategory] = {}


"""INTERCONNECTOR
"""
INTERCONNECTOR = ComponentCategory(value = "Interconnector") 

PlatformComponentCategory[INTERCONNECTOR.value] = INTERCONNECTOR


"""BATTERY
"""
BATTERY = ComponentCategory(value = "Battery") 

PlatformComponentCategory[BATTERY.value] = BATTERY


"""BUILDING
"""
BUILDING = ComponentCategory(value = "Building") 

PlatformComponentCategory[BUILDING.value] = BUILDING


"""LOAD
"""
LOAD = ComponentCategory(value = "Load") 

PlatformComponentCategory[LOAD.value] = LOAD


"""GENERATOR
"""
GENERATOR = ComponentCategory(value = "Generator") 

PlatformComponentCategory[GENERATOR.value] = GENERATOR