from gwproactor import ServicesInterface
import asyncio
import time
from gwproto import Message
from result import Ok, Result
from gw.enums import MarketTypeName
from gwproto.enums import MarketPriceUnit, MarketQuantityUnit
from actors.scada_actor import ScadaActor
from named_types import AtnBid, EnergyInstruction, GoDormant, PriceQuantityUnitless, WakeUp

class FakeAtn(ScadaActor):
    MAIN_LOOP_SLEEP_SECONDS = 61
    P_NODE = "hw1.isone.ver.keene"
    def __init__(self, name: str, services: ServicesInterface):
        super().__init__(name, services)
        self._stop_requested: bool = False

    def start(self) -> None:
        self.services.add_task(
            asyncio.create_task(self.main(), name="FakeAtn keepalive")
        )

    def stop(self) -> None:
        self._stop_requested = True
        
    async def join(self):
        ...

    def process_message(self, message: Message) -> Result[bool, BaseException]:
        match message.Payload:
            case GoDormant():
                ...
            case WakeUp():
                ...
        return Ok(True)
    
    async def main(self):
        await asyncio.sleep(2)
        self.log("In fake atn main loop")
        # SendTimeMs should be no more than 10 seconds after SlotStartS
        # slot start has to fall on top of 5 minutes
        t = time.time()
        slot_start_s = int(t -(t % 3600))
        if t - slot_start_s < 9:
            sample_dispatch = EnergyInstruction(
                FromGNodeAlias=self.layout.atn_g_node_alias,
                SlotStartS=slot_start_s,
                SlotDurationMinutes=60,
                SendTimeMs=int(t * 1000),
                AvgPowerWatts=9500
            )
            self.log(f"Sample dispatch: {sample_dispatch}")
        MarketPriceUnit.USDPerMWh
        # at or below $35.432/MWh buy 7 kWh
        mtn = MarketTypeName.rt60gate5.value
        market_slot_name = f"e.{mtn}.{FakeAtn.P_NODE}.{slot_start_s}"
        bid = AtnBid(
            BidderAlias=self.layout.atn_g_node_alias,
            MarketSlotName=market_slot_name,
            PqPairs=[PriceQuantityUnitless(PriceTimes1000=35432, QuantityTimes1000=7000)],
            InjectionIsPositive=False, # withdrawing energy since load not generation
            PriceUnit=MarketPriceUnit.USDPerMWh,
            QuantityUnit=MarketQuantityUnit.AvgkW,
            SignedMarketFeeTxn="BogusAlgoSignature"
        )
        self.log(f"Sample bid: {bid}")

        while not self._stop_requested:
            await asyncio.sleep(self.MAIN_LOOP_SLEEP_SECONDS)