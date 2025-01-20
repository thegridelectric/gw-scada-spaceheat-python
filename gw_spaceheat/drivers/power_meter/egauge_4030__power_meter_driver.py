import socket
import time
import struct
from typing import Any
from typing import Optional

from gwproactor.logger import LoggerOrAdapter
from gwproto.named_types import ElectricMeterChannelConfig
from pyModbusTCP.client import ModbusClient
from result import Err
from result import Ok
from result import Result

from actors.config import ScadaSettings
from gwproto.data_classes.data_channel import DataChannel
from gwproto.data_classes.components.electric_meter_component import ElectricMeterComponent
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

class ModbusClientStale(EGaugeCommWarning):
    """Connection appears open but cannot actually read data"""
    pass

class TryConnectResult(DriverResult[bool | None]):
    skipped_for_backoff: bool = False

    def __init__(
        self,
        connected: bool,
        warnings: Optional[list[Exception]] = None,
        skipped_for_backoff: bool = False,
    ):
        super().__init__(value=True if connected else None, warnings=warnings)
        self.skipped_for_backoff = skipped_for_backoff

    @property
    def connected(self) -> bool:
        return bool(self.value)

    def __bool__(self) -> bool:
        return self.connected

    @property
    def had_disconnect(self) -> bool:
        return any(type(warning) == EGaugeHadDisconnect for warning in self.warnings)

    def __str__(self) -> str:
        s = (
            f"TryConnectResult connected: {self.connected}  "
            f"had_disconnected: {self.had_disconnect}  "
            f"skipped: {self.skipped_for_backoff}  warnings: {len(self.warnings)}"
        )
        for warning in self.warnings:
            s += f"\n  type: <{type(warning)}>  warning: <{warning}>"
        return s

class EGuage4030_PowerMeterDriver(PowerMeterDriver):
    MAX_RECONNECT_DELAY_SECONDS: float = 10
    MODBUS_HW_UID_REGISTER: int = 100
    CLIENT_TIMEOUT: float = 3.0

    _modbus_client: Optional[ModbusClient] = None
    _client_settings: ModbusClientSettings
    _curr_connect_delay = 0.5
    _last_connect_time: float = 0.0


    def __init__(self, component: ElectricMeterComponent, settings: ScadaSettings, logger: LoggerOrAdapter):
        super().__init__(component, settings, logger=logger)
        self._client_settings = ModbusClientSettings(
            port=self.component.gt.ModbusPort,
            timeout=self.CLIENT_TIMEOUT
        )

    def try_connect(self) -> Result[TryConnectResult, Exception]:
        """Attempts to establish or verify Modbus connection to eGauge.
        Returns Ok(TryConnectResult) if connection attempt succeeds or is properly delayed,
        or Err(Exception) if there's an unrecoverable error.

        Detects and handles three main failure modes:
        1. ModbusClientStale: Connection appears open but can't read
        2. EGaugeHadDisconnect: Connection is explicitly closed
        3. EGaugeConnectFailed: Cannot establish new connection or read from it
        """
        
        now = time.time()
        comm_warnings = []
        skip_for_backoff = False

        def test_connection(client: ModbusClient) -> bool:
            """Tests if a connection can actually read data"""
            try:
                registers = client.read_input_registers(100, 8)
                return registers is not None
            except Exception:
                return False

        # Check existing connection
        if self._modbus_client is not None:
            if not self._modbus_client.is_open:
                comm_warnings.append(EGaugeHadDisconnect())
                self._modbus_client = None
            elif not test_connection(self._modbus_client):
                comm_warnings.append(ModbusClientStale(
                    "Connection appears open but cannot read registers"
                ))
                self._modbus_client = None

        # Handle connection creation
        if self._modbus_client is None:
            skip_for_backoff = (now - self._last_connect_time) <= self._curr_connect_delay
            if not skip_for_backoff:
                try:
                    self._client_settings.host = socket.gethostbyname(self.component.gt.ModbusHost)
                    new_client = ModbusClient(**self._client_settings.model_dump())
                    new_client.open()
                    self._last_connect_time = now

                    if new_client.is_open and test_connection(new_client):
                        self._modbus_client = new_client
                        self._curr_connect_delay = 0.0
                        self.logger.info("Successfully established new connection")
                    else:
                        comm_warnings.append(EGaugeConnectFailed())
                        self._curr_connect_delay = min(
                            self._curr_connect_delay * 2 if self._curr_connect_delay > 0 else 0.5,
                            self.MAX_RECONNECT_DELAY_SECONDS
                        )
                except socket.gaierror as e:
                    comm_warnings.append(e)
                except Exception as e:
                    return Err(e)

        # Log any warnings collected during connection attempt
        if comm_warnings:
            for warning in comm_warnings:
                self.logger.warning(f"Connection warning: {warning}")

            return Ok(
                TryConnectResult(
                    connected=self._modbus_client is not None and self._modbus_client.is_open,
                    warnings=comm_warnings,
                    skipped_for_backoff=skip_for_backoff
                )
            )

    def start(self) -> Result[DriverResult[TryConnectResult], Exception]:
        return self.try_connect(first_time=True)

    def read_hw_uid(self) -> Result[DriverResult[str | None], Exception]:
        connect_result = self.try_connect()
        if connect_result.is_ok() and connect_result.value.connected:
            _, _, bytes_ = readT16(self._modbus_client, self.MODBUS_HW_UID_REGISTER)
            if bytes_ is not None:
                return Ok(DriverResult(bytes_.decode("utf-8"), connect_result.value.warnings))
            else:
                return Ok(
                    DriverResult(
                        None,
                        connect_result.value.warnings + [
                            EGaugeReadFailed(
                                offset=self.MODBUS_HW_UID_REGISTER,
                                num_registers=8,
                                register_type=RegisterType.t16,
                                value=None,
                                client=self._modbus_client
                            )
                        ]
                    )
                )
        else:
            return connect_result

    def read_power_w(self, channel: DataChannel) -> Result[DriverResult[int | None], Exception]:
        egauge_config = next(
            (
                cfg for cfg in self.component.gt.ConfigList
                if cfg.ChannelName == channel.Name
            ),
            None
        ).EgaugeRegisterConfig
        connect_result = self.try_connect()
        if connect_result.is_ok() and connect_result.value.connected:
            _, _, power = readF32(self._modbus_client, egauge_config.Address)
            driver_result: DriverResult[int | None] = DriverResult(None, connect_result.value.warnings)
            if power is None:
                driver_result.warnings.append(
                    EGaugeReadFailed(
                        offset=egauge_config.Address,
                        num_registers=2,
                        register_type=RegisterType.f32,
                        value=None,
                        client=self._modbus_client,
                    )
                )
            else:
                driver_result.value = int(power)
                if not is_short_integer(driver_result.value):
                    unclipped_int_power = driver_result.value
                    MIN_POWER = -2**15
                    MAX_POWER = 2**15 - 1
                    driver_result.value = max(MIN_POWER, min(int(driver_result.value), MAX_POWER))
                    driver_result.warnings.append(
                        EGaugeReadOutOfRange(
                            offset=egauge_config.Address,
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

    def read_current_rms_micro_amps(self, channel: DataChannel) -> Result[DriverResult[int | None], Exception]:
        raise NotImplementedError

    def validate_config(self, config: ElectricMeterChannelConfig) -> None:
        egauge_config = config.EgaugeRegisterConfig
        if egauge_config is None:
            raise ValueError("Misconfigured eGaugeConfig for power. eGaugeConfig is None.")
        if egauge_config.Type != 'f32':
            raise ValueError(f"Misconfigured eGaugeConfig for power. Type must be f32: {egauge_config}")
        if egauge_config.Unit != 'W':
            raise ValueError(f"Misconfigured eGaugeConfig for power. Unit must be W: {egauge_config}")
        if egauge_config.Denominator != 1:
            raise ValueError(f"Misconfigured eGaugeConfig for power. Denominator must be 1: {egauge_config}")


def is_short_integer(candidate: int) -> bool:
    try:
        struct.pack("h", candidate)
    except:  # noqa
        return False
    return True