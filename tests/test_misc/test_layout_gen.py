from typing import Optional
from typing import Tuple

import rich
from gwproto.data_classes.components.hubitat_tank_component import HubitatTankComponent
from gwproto.data_classes.hardware_layout import HardwareLayout
from gwproto.enums import ActorClass
from gwproto.types.hubitat_gt import HubitatGt
from pydantic import BaseModel

from layout_gen import add_hubitat
from layout_gen import add_hubitat_thermostat
from layout_gen import add_tank
from layout_gen import FibaroGenCfg
from layout_gen import HubitatThermostatGenCfg
from layout_gen import LayoutDb
from layout_gen import StubConfig
from layout_gen import TankGenCfg

_sn = 0

def _dummy_sn() -> str:
    global _sn
    _sn += 1
    return str(_sn)

def _dummy_fib() -> FibaroGenCfg:
    return FibaroGenCfg(SN=_dummy_sn(), ZWaveDSK="NA")

_DEFAULT_POLL_PERIODS = (
    60.0,
    60.0,
    60.0,
    60.0,
    60.0,
)

class _TankDeviceTestConfig(BaseModel):
    Name: str
    DisplayName: str = ""
    DefaultPollPeriodSeconds: Optional[float] = None
    DevicePollPeriodSeconds: Tuple[float|None, float|None, float|None, float|None] = None, None, None, None
    RestExp: Tuple[float, float, float, float] = _DEFAULT_POLL_PERIODS

def test_tank_device_poll_period(tmp_path):

    db = LayoutDb(
        # existing_layout=LayoutIDMap.from_path(Path(__file__).parent.parent.joinpath("config/hardware-layout.json")),
        add_stubs=True,
        stub_config=StubConfig(),
    )

    hubitat = HubitatGt(
        Host="hubitat-dummy.local",
        MakerApiId=4,
        AccessToken="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        MacAddress="00:00:00:00:00:00",
    )

    cfgs = [
        _TankDeviceTestConfig(
            Name="a.unset",
        ),
        _TankDeviceTestConfig(
            Name="a.default",
            DefaultPollPeriodSeconds=1.0,
            RestExp=(1.0, 1.0, 1.0, 1.0),
        ),
        _TankDeviceTestConfig(
            Name="a.one.explicit",
            DevicePollPeriodSeconds=(1.0, None, None, None),
            RestExp=(1.0, 60.0, 60.0, 60.0),
        ),
        _TankDeviceTestConfig(
            Name="a.mixed",
            DefaultPollPeriodSeconds=1.0,
            DevicePollPeriodSeconds=(2.0, None, None, None),
            RestExp=(2.0, 1.0, 1.0, 1.0),
        ),
    ]

    for cfg in cfgs:
        tank_gen_cfg = TankGenCfg(
            NodeAlias=cfg.Name,
            InHomeName=cfg.Name,
            SN=_dummy_sn(),
            DeviceIds=(1, 2, 3, 4),
            DefaultPollPeriodSeconds=cfg.DefaultPollPeriodSeconds,
            DevicePollPeriodSeconds=cfg.DevicePollPeriodSeconds,
        )
        cfg.DisplayName = tank_gen_cfg.component_alias()
        add_tank(
            db,
            fibaro_a=_dummy_fib(),
            fibaro_b=_dummy_fib(),
            hubitat=hubitat,
            tank=tank_gen_cfg,
        )

    d = db.dict()
    errors = []
    def _err_str(name: str, field: str, exp: float, got: float) -> str:
        return (
            f"ERROR with cfg {name}  {field}. "
            f"Exp: {exp}  "
            f"Got: {got}"
        )
    tanks = []
    for cfg in cfgs:
        found = False
        for tankcj in d["OtherComponents"]:
            if "Tank" in tankcj:
                found = True
                tanks.append(tankcj)
                if tankcj["DisplayName"] == cfg.DisplayName:
                    tankj = tankcj["Tank"]
                    if cfg.DefaultPollPeriodSeconds is None:
                        if  "DefaultPollPeriodSeconds" in tankj:
                            errors.append(
                                _err_str(
                                    cfg.Name, "DefaultPollPeriodSeconds",
                                    cfg.DefaultPollPeriodSeconds,
                                    "DefaultPollPeriodSeconds",
                                )
                            )
                    elif cfg.DefaultPollPeriodSeconds != tankj["DefaultPollPeriodSeconds"]:
                        errors.append(
                            _err_str(
                                cfg.Name, "DefaultPollPeriodSeconds",
                                cfg.DefaultPollPeriodSeconds,
                                tankj["DefaultPollPeriodSeconds"],
                            )
                        )
                    for i, devicej in enumerate(tankj["Devices"]):
                        if cfg.DevicePollPeriodSeconds[i] is None:
                            if "PollPeriodSeconds" in devicej:
                                errors.append(
                                _err_str(
                                    f"{cfg.Name} layout device {i}", "PollPeriodSeconds",
                                    cfg.DefaultPollPeriodSeconds[i],
                                    "PollPeriodSeconds",
                                )
                            )
                        elif str(cfg.DevicePollPeriodSeconds[i])!= str(devicej["PollPeriodSeconds"]):
                            errors.append(
                                _err_str(
                                    f"{cfg.Name} layout device {i}", "PollPeriodSeconds",
                                    cfg.DevicePollPeriodSeconds[i],
                                    devicej["PollPeriodSeconds"],
                                )
                            )
        if not found:
            errors.append(f"<{cfg.DisplayName}> not found")

    layout_path = tmp_path / "hardware-layout.json"
    db.write(layout_path)

    load_errors = []
    layout = HardwareLayout.load(
        layout_path,
        raise_errors=True,
        errors=load_errors,
    )

    if load_errors:
        for error in load_errors:
            rich.print(error)
        raise ValueError(str(load_errors))

    for cfg in cfgs:
        component = layout.component(cfg.Name)
        assert isinstance(component, HubitatTankComponent)

        # rich.print(component.devices)
        for i, device in enumerate(component.devices):
            if str(cfg.RestExp[i]) != str(device.rest.poll_period_seconds):
                errors.append(
                    _err_str(
                        f"{cfg.Name} rest device {i}", "poll_period_seconds",
                        cfg.RestExp[i],
                        device.rest.poll_period_seconds,
                    )
                )
    s = ""
    if errors:
        s = f"Found {len(errors)} errors\n"
        for error in errors:
            s += f"\t{error}\n"
        print(s)
        rich.print(tanks)
    assert not s

def test_hubitat():
    db = LayoutDb(
        add_stubs=True,
        stub_config=StubConfig(),
    )
    hubitat_mac_address = "00:00:00:0A:BB:cc"
    hubitat_component_id = db.component_id_by_alias(
        add_hubitat(
            db,
            HubitatGt(
                Host="hubitat-dummy.local",
                MakerApiId=4,
                AccessToken="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                MacAddress=hubitat_mac_address,
            )
        )
    )
    layout = HardwareLayout.load_dict(db.dict(), raise_errors=True)
    node = layout.node_from_component(
        hubitat_component_id
    )
    assert node is not None
    assert node.alias == f"a.hubitat.{hubitat_mac_address[-8:].replace(':', '')}".lower()
    assert node.component_id == hubitat_component_id
    assert node.actor_class == ActorClass.Hubitat

def test_honeywell_thermostat():
    db = LayoutDb(
        add_stubs=True,
        stub_config=StubConfig(),
    )

    thermostat_node_name = "garage"
    add_hubitat_thermostat(
        db,
        HubitatThermostatGenCfg(
            node_name=thermostat_node_name,
            display_name=f"{thermostat_node_name.capitalize()} Component",
            hubitat=HubitatGt(
                Host="hubitat-dummy.local",
                MakerApiId=4,
                AccessToken="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                MacAddress="00:00:00:00:00:00",
            ),
            device_id=1
        ),
    )
    layout = HardwareLayout.load_dict(db.dict(), raise_errors=True)
    assert layout.node(thermostat_node_name).actor_class == ActorClass.HoneywellThermostat
    assert layout.node(f"{thermostat_node_name}.temp").actor_class == ActorClass.NoActor
    assert layout.node(f"{thermostat_node_name}.set").actor_class == ActorClass.NoActor
    assert layout.node(f"{thermostat_node_name}.state").actor_class == ActorClass.NoActor
