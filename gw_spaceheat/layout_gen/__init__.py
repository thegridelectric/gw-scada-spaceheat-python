"""Temporary package for assisting generation of hardware_layout.json files"""

from layout_gen.egauge import add_egauge
from layout_gen.egauge import PowerMeterGenConfig
from layout_gen.egauge import EgaugeChannelConfig
from layout_gen.hubitat import add_hubitat
from layout_gen.layout_db import LayoutDb
from layout_gen.layout_db import LayoutIDMap
from layout_gen.layout_db import StubConfig
from layout_gen.multi import add_tsnap_multipurpose, TSnapMultipurposeGenCfg, SensorNodeGenCfg
from layout_gen.poller import add_thermostat
from layout_gen.poller import HubitatThermostatGenCfg
from layout_gen.tank import FibaroGenCfg
from layout_gen.tank import TankGenCfg
from layout_gen.tank import add_tank
from layout_gen.tank2 import add_tank2
from layout_gen.tank2 import Tank2Cfg
from layout_gen.web_server import add_web_server

__all__ = [
    "add_egauge",
    "add_hubitat",
    "add_thermostat",
    "add_hubitat_thermostat",
    "add_tank",
    "add_tank2",
    "add_tsnap_multipurpose",
    "add_web_server",
    "PowerMeterGenConfig",
    "EgaugeChannelConfig",
    "FibaroGenCfg",
    "LayoutDb",
    "LayoutIDMap",
    "HubitatThermostatGenCfg",
    "StubConfig",
    "TankGenCfg",
    "Tank2Cfg",
    "TSnapMultipurposeGenCfg",
    "SensorNodeGenCfg",

]


