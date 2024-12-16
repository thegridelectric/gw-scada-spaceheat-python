from gwproactor import ServicesInterface
import asyncio
import time
from datetime import datetime
from gwproto import Message
from result import Ok, Result
from typing import List
from actors.scada_actor import ScadaActor
from gw.enums import MarketTypeName
from enums import MarketPriceUnit, MarketQuantityUnit
from named_types import AtnBid, EnergyInstruction, LatestPrice, Ha1Params
from named_types.price_quantity_unitless import PriceQuantityUnitless
from actors.scada_data import ScadaData
from actors.flo import DGraph, DConfig
from actors.synth_generator import WeatherForecast, PriceForecast

class FakeAtn(ScadaActor):
    MAIN_LOOP_SLEEP_SECONDS = 61
    P_NODE = "hw1.isone.ver.keene"
    def __init__(self, name: str, services: ServicesInterface):
        super().__init__(name, services)
        self._stop_requested: bool = False
        self.weather_forecast = None
        self.price_forecast = None

    @property
    def data(self) -> ScadaData:
        return self._services.data
    
    @property
    def params(self) -> Ha1Params:
        return self.data.ha1_params

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
            case WeatherForecast():
                self.log("Recieved weather forecast")
                self.weather_forecast = {
                    'oat': message.Payload.OatForecast, 
                    'ws': message.Payload.WsForecast,
                    }
            case PriceForecast():
                self.log("Recieved price forecast:")
                self.price_forecast = {
                    'dp': message.Payload.DpForecast,
                    'lmp': message.Payload.LmpForecsat
                    }
                self.log(f"{[x+y for x,y in zip(self.price_forecast['dp'], self.price_forecast['lmp'])]}")
            case LatestPrice():
                ...
        return Ok(True)
    
    def run_d(self)-> None:
        # In the last 5 minutes of the hour: make a bid for the next hour
        if (datetime.now().minute >= 1
                and self.weather_forecast is not None 
                and self.price_forecast is not None):
            
            self.log("Preparing to run Dijkstra")
            if ('top-centroid' not in self.data.latest_channel_values
                or 'therrmocline-position' not in self.data.latest_channel_values):
                self.log("Need thermocline and top centroid")
                # return
            else:
                if (self.data.latest_channel_values['top-centroid'] is None or
                    self.data.latest_channel_values['thermocline-position'] is None):
                    self.log("Need thermocline and top centroid")
                    # return
                
            initial_toptemp = 140
            initial_thermocline = 8

            # TODO: uncomment
            # initial_toptemp = self.data.latest_channel_values['top-centroid'] / 1000,
            # initial_thermocline = self.data.latest_channel_values['thermocline-position'],

            # Find PQ pairs using Dijkstra
            self.log("Building configuration for Dijkstra")
            configuration = DConfig(
                InitialTopTemp = initial_toptemp,
                InitialThermocline = initial_thermocline,
                DpForecastUsdMwh = self.price_forecast['dp'],
                LmpForecastUsdMwh = self.price_forecast['lmp'],
                OatForecastF = self.weather_forecast['oat'],
                WindSpeedForecastMph = self.weather_forecast['ws'],
                AlphaTimes10 = self.params.AlphaTimes10,
                BetaTimes100 = self.params.BetaTimes100,
                GammaEx6 = self.params.GammaEx6,
                IntermediatePowerKw = self.params.IntermediatePowerKw,
                IntermediateRswtF = self.params.IntermediateRswtF,
                DdPowerKw = self.params.DdPowerKw,
                DdRswtF = self.params.DdRswtF,
                DdDeltaTF = self.params.DdDeltaTF,
                MaxEwtF = self.params.MaxEwtF
            )
            self.log("Creating graph")
            g = DGraph(configuration)
            self.log("Solving Dijkstra")
            g.solve_dijkstra()
            self.log("Done!")
            self.log("Getting PQ pairs...")
            pq_pairs: List[PriceQuantityUnitless] = g.generate_bid()
            self.log(f"Obtained Price-Quantity pairs")

            # Generate bid
            t = time.time()
            slot_start_s = int(t-(t%3600))
            mtn = MarketTypeName.rt60gate5.value
            market_slot_name = f"e.{mtn}.{FakeAtn.P_NODE}.{slot_start_s}"
            bid = AtnBid(
                BidderAlias=self.layout.atn_g_node_alias,
                MarketSlotName=market_slot_name,
                PqPairs=pq_pairs,
                InjectionIsPositive=False, # withdrawing energy since load not generation
                PriceUnit=MarketPriceUnit.USDPerMWh,
                QuantityUnit=MarketQuantityUnit.AvgkW,
                SignedMarketFeeTxn="BogusAlgoSignature"
            )
            self.log(f"Bid: {bid}")

        else:
            self.log(f"Minute {datetime.now().minute}")
     
    async def main(self):

        await asyncio.sleep(10)

        while not self._stop_requested:
            # try:
            #     self.run_d()
            # except Exception as e:
            #     self.log(f"Exception running d: {e}")    
            await asyncio.sleep(self.MAIN_LOOP_SLEEP_SECONDS)


            # # SendTimeMs should be no more than 10 seconds after SlotStartS
            # # slot start has to fall on top of 5 minutes
            # t = time.time()
            # slot_start_s = int(t -(t % 3600))
            # # if t - slot_start_s < 9:
            # #     sample_dispatch = EnergyInstruction(
            # #         FromGNodeAlias=self.layout.atn_g_node_alias,
            # #         SlotStartS=slot_start_s,
            # #         SlotDurationMinutes=60,
            # #         SendTimeMs=int(t * 1000),
            # #         AvgPowerWatts=9500
            # #     )
            # #     self.log(f"Sample dispatch: {sample_dispatch}")
            # sample_dispatch = EnergyInstruction(
            #         FromGNodeAlias=self.layout.atn_g_node_alias,
            #         SlotStartS=slot_start_s,
            #         SlotDurationMinutes=60,
            #         SendTimeMs=int(slot_start_s*1000+5000),
            #         AvgPowerWatts=9500
            #     )
            # self._send_to(self.synth_generator, sample_dispatch)
            # sample_power = PowerWatts(Watts=1000)
            # self._send_to(self.synth_generator, sample_power)

            # MarketPriceUnit.USDPerMWh
            # # at or below $35.432/MWh buy 7 kWh
            # mtn = MarketTypeName.rt60gate5.value
            # market_slot_name = f"e.{mtn}.{FakeAtn.P_NODE}.{slot_start_s}"
            # bid = AtnBid(
            #     BidderAlias=self.layout.atn_g_node_alias,
            #     MarketSlotName=market_slot_name,
            #     PqPairs=[PriceQuantityUnitless(PriceTimes1000=35432, QuantityTimes1000=7000)],
            #     InjectionIsPositive=False, # withdrawing energy since load not generation
            #     PriceUnit=MarketPriceUnit.USDPerMWh,
            #     QuantityUnit=MarketQuantityUnit.AvgkW,
            #     SignedMarketFeeTxn="BogusAlgoSignature"
            # )
            # self.log(f"Sample bid: {bid}")

    def send_energy_instr(self, watthours:int):
        t = time.time()
        wait_s = 300 - t%300
        time.sleep(wait_s)
        t = time.time()
        slot_start_s = int(t - (t % 300))
        if t - slot_start_s < 10:
            sample_dispatch = EnergyInstruction(
                    FromGNodeAlias=self.layout.atn_g_node_alias,
                    SlotStartS=slot_start_s,
                    SlotDurationMinutes=60,
                    SendTimeMs=int(time.time()*1000),
                    AvgPowerWatts=int(watthours)
                )
            self.log(f"Sent EnergyInstruction: {sample_dispatch}")
            self._send_to(self.synth_generator, sample_dispatch)