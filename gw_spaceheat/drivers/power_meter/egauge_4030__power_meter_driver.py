import socket
import time
from typing import Any

from gwproto import property_format
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
    client_error: int
    client_error_text: str
    client_except: int
    client_except_summary: str
    client_except_details: str


    def __init__(
            self,
            offset: int,
            num_registers: int,
            register_type: RegisterType,
            value: Any,
            client: ModbusClient,
            msg: str = "",
    ):
        super().__init__(msg)
        self.offset = offset
        self.num_registers = num_registers
        self.register_type = register_type
        self.value = value
        self.client_error = client.last_error
        self.client_error_text = client.last_error_as_txt
        self.client_except = client.last_except
        self.client_except_summary = client.last_except_as_txt
        self.client_except_details = client.last_except_as_full_txt

    def __str__(self):
        s = self.__class__.__name__
        super_str = super().__str__()
        if super_str:
            s += f" <{super_str}>"
        s += (
            f"  offset: {self.offset}  num_registers: {self.num_registers}  "
            f"  {self.register_type.value}  received: <{self.value}>\n"
            f"  PyModubsTCP client info:\n"
            f"    error:{self.client_error}  <{self.client_error_text}>\n"
            f"    except:{self.client_error}  <{self.client_except_summary}>\n"
            f"    except:<{self.client_except_details}>"
        )
        return s

class EGaugeReadOutOfRange(EGaugeReadFailed):
    ...

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

    def try_connect(self, first_time: bool = False) -> Result[DriverResult, Exception]:

        now = time.time()
        comm_warnings = []
        if not self._modbus_client.is_open:
            if not first_time:
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
        return self.try_connect(first_time=True)

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
                        client=self._modbus_client
                    )
                )
        else:
            return connect_result

    def read_power_w(self) -> Result[DriverResult[int | None], Exception]:
        connect_result = self.try_connect()
        if connect_result.is_ok():
            _, _, power = readF32(self._modbus_client, self.component.modbus_power_register)
            returned_power: int | None
            driver_result: DriverResult[int | None] = DriverResult(None, connect_result.value.warnings)
            if power is None:
                driver_result.warnings.append(
                    EGaugeReadFailed(
                        offset=self.component.modbus_power_register,
                        num_registers=2,
                        register_type=RegisterType.f32,
                        value=None,
                        client=self._modbus_client,
                    )
                )
            else:
                driver_result.value = int(power)
                if not property_format.is_short_integer(driver_result.value):
                    unclipped_int_power = driver_result.value
                    MIN_POWER = -2**15
                    MAX_POWER = 2**15 - 1
                    driver_result.value = max(MIN_POWER, min(int(driver_result.value), MAX_POWER))
                    driver_result.warnings.append(
                        EGaugeReadOutOfRange(
                            offset=self.component.modbus_power_register,
                            num_registers=2,
                            register_type=RegisterType.f32,
                            value=unclipped_int_power,
                            client=self._modbus_client,
                            msg=rf"Power value {unclipped_int_power} clipped to \[{MIN_POWER}, {MAX_POWER}] result: {driver_result.value}",
                        )
                    )
            return Ok(driver_result)
        else:
            return connect_result
