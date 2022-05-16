from typing import Dict
from .sensor_type import SensorType

PlatformSensorType: Dict[str,SensorType] = {}

""" ELECTRIC_POWER_METER """
ELECTRIC_POWER_METER= SensorType(value = "ElectricPowerMeter",
            display_name = "Electric Power Meter")

PlatformSensorType[ELECTRIC_POWER_METER.value] = ELECTRIC_POWER_METER

""" WATER_FLOW_METER """
WATER_FLOW_METER = SensorType(value = "WaterFlowMeter",
            display_name = "Water Flow Meter")

PlatformSensorType[WATER_FLOW_METER.value] = WATER_FLOW_METER

""" INDOOR_AIR_TEMP_SENSOR """
INDOOR_AIR_TEMP_SENSOR = SensorType(value = "IndoorAirTempSensor",
            display_name = "Indoor Air Temperature Sensor")

PlatformSensorType[INDOOR_AIR_TEMP_SENSOR.value] = INDOOR_AIR_TEMP_SENSOR

""" OUTDOOR_AIR_TEMP_SENSOR """
OUTDOOR_AIR_TEMP_SENSOR = SensorType(value = "OutdoorAirTempSensor",
            display_name = "Outdoor Air Temperature Sensor")

PlatformSensorType[OUTDOOR_AIR_TEMP_SENSOR.value] = OUTDOOR_AIR_TEMP_SENSOR

""" PIPE_CLAMP_WATER_TEMP_SENSOR """
PIPE_CLAMP_WATER_TEMP_SENSOR = SensorType(value = "PipeClampWaterTempSensor",
            display_name = "Pipe Clamp Water Temp Sensor")

PlatformSensorType[PIPE_CLAMP_WATER_TEMP_SENSOR.value] = PIPE_CLAMP_WATER_TEMP_SENSOR

""" WATER_STORE_TEMP_SENSOR """
WATER_STORE_TEMP_SENSOR = SensorType(value = "WaterStoreTempSensor",
            display_name = "Water Store Temp Sensor")

PlatformSensorType[WATER_STORE_TEMP_SENSOR.value] = WATER_STORE_TEMP_SENSOR