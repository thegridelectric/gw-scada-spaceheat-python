import time
from typing import Optional

from aiohttp import ClientResponse
from aiohttp import ClientSession
from gwproactor import ServicesInterface
from gwproactor.actors.rest import RESTPoller
from gwproto import Message
from gwproto.enums import TelemetryName
from pydantic import BaseModel
from pydantic import Extra

from actors.message import GtTelemetryMessage

class FibaroAttribute(BaseModel, extra=Extra.allow):
    name: str = ""
    currentValue: Optional[str | int | float] = None
    dataType: str = ""

class FibaroRefreshResponse(BaseModel, extra=Extra.allow):
    id: int
    name: str = ""
    label: str = ""
    type: str = ""
    attributes: list[FibaroAttribute]

    def get_attribute_by_name(self, name: str) -> Optional[FibaroAttribute]:
        return next((attr for attr in self.attributes if attr.name == name), None)

    def get_voltage(self) -> Optional[float]:
        attribute = self.get_attribute_by_name("voltage")
        if attribute is not None:
            try:
                return float(attribute.currentValue)
            except: # noqa
                pass
        return None

class FibaroTankTempSensor(RESTPoller):

    _read_time: float
    _telemetry_name: TelemetryName
    _exponent: int

    def __init__(self, name: str, services: ServicesInterface):
        super().__init__(name, services)
        telemetry_name = getattr(self._component, "telemetry_name", None)
        exponent = getattr(self._component, "exponent", None)
        if not isinstance(telemetry_name, TelemetryName):
            raise ValueError(
                f"ERROR. Component.telemetry_name has type {type(telemetry_name)}. Expected TelemetryName."
            )
        if not isinstance(exponent, int):
            raise ValueError(
                f"ERROR. Cac.exponent has type {type(telemetry_name)}. Expected int."
            )
        self._telemetry_name = telemetry_name
        self._exponent = exponent

    async def _make_request(self, session: ClientSession) -> ClientResponse:
        """"A refresh sent to hubitate for fibaro returns the value of the *last* refresh,
        so we just send two refreshes.
        """
        with await session.request(**self._request_args()):
            self._read_time = time.time()
        return await session.request(**self._request_args())

    async def _convert(self, response: ClientResponse) -> Optional[Message]:
        return GtTelemetryMessage(
            src=self.name,
            dst=self.services.name,
            telemetry_name=self._telemetry_name,
            value=int(FibaroRefreshResponse(**await response.json()).get_voltage()),
            exponent=self._exponent,
            scada_read_time_unix_ms=int(self._read_time * 1000),
        )
