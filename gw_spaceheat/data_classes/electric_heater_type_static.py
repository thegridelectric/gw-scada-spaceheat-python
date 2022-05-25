from typing import Dict

from .electric_heater_type import ElectricHeaterType

PlatformElectricHeaterType: Dict[str,ElectricHeaterType] = {}


""" WATER_HEATER_BOOST"""
WATER_HEATER_BOOST = ElectricHeaterType(value = "WaterHeaterBoost",
            display_name = "Water Heater Boost Resistive Element",
            is_resistive_load=True,
            expected_startup_seconds=0.1,
            expected_shutdown_seconds=0.1)

PlatformElectricHeaterType[WATER_HEATER_BOOST.value] = WATER_HEATER_BOOST

""" AIR_TO_WATER_HEAT_PUMP"""
AIR_TO_WATER_HEAT_PUMP = ElectricHeaterType(value = "AirToWaterHeatPump",
            display_name = "Air to Water Heat Pump",
            is_resistive_load=False,
            expected_startup_seconds=60,
            expected_shutdown_seconds=60)

PlatformElectricHeaterType[AIR_TO_WATER_HEAT_PUMP.value] = AIR_TO_WATER_HEAT_PUMP