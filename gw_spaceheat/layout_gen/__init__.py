"""Temporary package for assisting generation of hardware_layout.json files"""

from layout_gen.egauge import add_egauge
from layout_gen.egauge import EGaugeGenCfg
from layout_gen.egauge import EGaugeIOGenCfg
from layout_gen.flow import add_flow_meter
from layout_gen.flow import add_istec_flow_meter
from layout_gen.hubitat import add_hubitat
from layout_gen.layout_db import LayoutDb
from layout_gen.layout_db import LayoutIDMap
from layout_gen.layout_db import StubConfig
from layout_gen.multi import add_tsnap_multipurpose
from layout_gen.poller import add_hubitat_poller
from layout_gen.poller import add_hubitat_thermostat
from layout_gen.poller import HubitatPollerGenCfg
from layout_gen.poller import HubitatThermostatGenCfg
from layout_gen.tank import FibaroGenCfg
from layout_gen.tank import TankGenCfg
from layout_gen.tank import add_tank
from layout_gen.web_server import add_web_server

__all__ = [
    "add_egauge",
    "add_flow_meter",
    "add_istec_flow_meter",
    "add_hubitat",
    "add_hubitat_poller",
    "add_hubitat_thermostat",
    "add_tank",
    "add_tsnap_multipurpose",
    "add_web_server",
    "EGaugeGenCfg",
    "EGaugeIOGenCfg",
    "FibaroGenCfg",
    "LayoutDb",
    "LayoutIDMap",
    "HubitatPollerGenCfg",
    "HubitatThermostatGenCfg",
    "StubConfig",
    "TankGenCfg",
]


