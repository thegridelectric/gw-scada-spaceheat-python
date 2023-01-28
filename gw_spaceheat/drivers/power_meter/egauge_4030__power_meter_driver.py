import socket
import time
from typing import Any

from pyModbusTCP.client import ModbusClient
from result import Err
from result import Ok
from result import Result

from actors2.config import ScadaSettings
from data_classes.components.electric_meter_component import ElectricMeterComponent
from drivers.driver_result import DriverResult
from drivers.exceptions import DriverWarning
from drivers.power_meter.egauge import ModbusClientSettings
from drivers.power_meter.egauge import RegisterType
from drivers.power_meter.egauge.registers import readF32
from drivers.power_meter.egauge.registers import readT16
from drivers.power_meter.power_meter_driver import PowerMeterDriver

class EGaugeReadFailed(DriverWarning):
    offset: int
    num_registers: int
    register_type: RegisterType
    value: Any

    def __init__(
            self,
            offset: int,
            num_registers: int,
            register_type: RegisterType,
            value: Any,
            msg: str = "",
    ):
        super().__init__(msg)
        self.offset = offset
        self.num_registers = num_registers
        self.register_type = register_type
        self.value = value

    def __str__(self):
        s = self.__class__.__name__
        super_str = super().__str__()
        if super_str:
            s += f" <{super_str}>"
        s += (
            f"  offset: {self.offset}  num_registers: {self.num_registers}  "
            f"  {self.register_type.value}  received: <{self.value}>"
        )
        return s

class EGaugeCommWarning(DriverWarning):
    ...

class EGaugeHadDisconnect(EGaugeCommWarning):
    ...

class EGaugeConnectFailed(EGaugeCommWarning):
    ...



class EGuage4030_PowerMeterDriver(PowerMeterDriver):
    MAX_RECONNECT_DELAY_SECONDS: float = 10
    CLIENT_TIMEOUT: float = 3.0

    _modbus_client: ModbusClient
    _client_settings: ModbusClientSettings
    _curr_connect_delay = 0.5
    _last_connect_time: float = 0.0

    def __init__(self, component: ElectricMeterComponent, settings: ScadaSettings):
        super().__init__(component, settings)
        self._client_settings = ModbusClientSettings(
            host=socket.gethostbyname(self.component.modbus_host),
            port=self.component.modbus_port,
            timeout=self.CLIENT_TIMEOUT
        )
        self._modbus_client = ModbusClient(**self._client_settings.dict())

    def try_connect(self) -> Result[DriverResult, Exception]:
        now = time.time()
        comm_warnings = []
        if not self._modbus_client.is_open:
            comm_warnings.append(EGaugeHadDisconnect())
            if now - self._last_connect_time > self._curr_connect_delay:
                self._curr_connect_delay = min(
                    self._curr_connect_delay * 2,
                    self.MAX_RECONNECT_DELAY_SECONDS
                )
                self._modbus_client.open()
        if self._modbus_client.is_open:
            self._last_connect_time = now
            self._curr_connect_delay = 0.0
            return Ok(DriverResult(True, comm_warnings))
        else:
            return Err(EGaugeConnectFailed())

    def start(self) -> Result[DriverResult[bool], Exception]:
        return self.try_connect()

    def read_current_rms_micro_amps(self) -> Result[DriverResult[int], Exception]:
        raise NotImplementedError

    def read_hw_uid(self) -> Result[DriverResult[str], Exception]:
        connect_result = self.try_connect()
        if connect_result.is_ok():
            _, _, bytes_ = readT16(self._modbus_client, self.component.modbus_hw_uid_register)
            if bytes_ is not None:
                return Ok(DriverResult(bytes_.decode("utf-8"), connect_result.value.warnings))
            else:
                return Err(
                    EGaugeReadFailed(
                        offset=self.component.modbus_hw_uid_register,
                        num_registers=8,
                        register_type=RegisterType.t16,
                        value=None,
                    )
                )
        else:
            return connect_result

    def read_power_w(self) -> Result[DriverResult[int], Exception]:
        connect_result = self.try_connect()
        if connect_result.is_ok():
            _, _, power = readF32(self._modbus_client, self.component.modbus_power_register)
            if power is not None:
                power = int(power)
                return Ok(DriverResult(int(power), connect_result.value.warnings))
            else:
                return Err(
                    EGaugeReadFailed(
                        offset=self.component.modbus_power_register,
                        num_registers=2,
                        register_type=RegisterType.f32,
                        value=None,
                    )
                )
        else:
            return connect_result
