from gwproactor import ServicesInterface
import asyncio
import time
import numpy as np
from datetime import datetime
from gwproto import Message
from result import Ok, Result
from typing import List, Tuple
from actors.scada_actor import ScadaActor
from gw.enums import MarketTypeName
from enums import MarketPriceUnit, MarketQuantityUnit
from named_types import AtnBid, EnergyInstruction, LatestPrice, Ha1Params
from named_types.price_quantity_unitless import PriceQuantityUnitless
from actors.scada_data import ScadaData
from actors.flo import DGraph, DConfig
from actors.synth_generator import WeatherForecast, PriceForecast
from data_classes.house_0_names import H0CN
from gwproto.named_types import SingleReading

def kmeans(data, k=2, max_iters=100, tol=1e-4):
    data = np.array(data).reshape(-1, 1)
    # Initialize centroids randomly
    centroids = data[np.random.choice(len(data), k, replace=False)]
    for _ in range(max_iters):
        # Assign labels by finding the closest centroid for each data point
        labels = np.argmin(np.abs(data - centroids.T), axis=1)
        new_centroids = np.zeros_like(centroids)
        for i in range(k):
            cluster_points = data[labels == i]
            if len(cluster_points) > 0:
                new_centroids[i] = cluster_points.mean()
            else:
                # Reinitialize the centroid randomly if no points are assigned to it
                new_centroids[i] = data[np.random.choice(len(data))]
        if np.all(np.abs(new_centroids - centroids) < tol):
            break
        centroids = new_centroids
    return labels


class FakeAtn(ScadaActor):
    MAIN_LOOP_SLEEP_SECONDS = 61
    P_NODE = "hw1.isone.ver.keene"
    def __init__(self, name: str, services: ServicesInterface):
        super().__init__(name, services)
        self._stop_requested: bool = False
        self.weather_forecast = None
        self.price_forecast = None

        self.cn: H0CN = self.layout.channel_names
        self._stop_requested: bool = False
        self.hardware_layout = self._services.hardware_layout
        self.temperature_channel_names = [
            H0CN.buffer.depth1, H0CN.buffer.depth2, H0CN.buffer.depth3, H0CN.buffer.depth4,
            H0CN.hp_ewt, H0CN.hp_lwt, H0CN.dist_swt, H0CN.dist_rwt, 
            H0CN.buffer_cold_pipe, H0CN.buffer_hot_pipe, H0CN.store_cold_pipe, H0CN.store_hot_pipe,
            *(depth for tank in self.cn.tank.values() for depth in [tank.depth1, tank.depth2, tank.depth3, tank.depth4])
        ]

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
                self.log("Recieved price forecast")
                self.price_forecast = {
                    'dp': message.Payload.DpForecast,
                    'lmp': message.Payload.LmpForecsat
                    }
            case LatestPrice():
                ...
        return Ok(True)
    
    def run_d(self)-> None:
        # In the last 5 minutes of the hour: make a bid for the next hour
        if (datetime.now().minute >= 1
                and self.weather_forecast is not None 
                and self.price_forecast is not None):
                        
            self.log("Finding thermocline position and top temperature")
            initial_toptemp, initial_thermocline = self.get_thermocline_and_centroids()
            if (initial_toptemp, initial_thermocline) == (0,0):
                self.log("Can not run Dijkstra!")
                return

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
            st = time.time()
            g = DGraph(configuration)
            self.log(f"Done in {round(time.time()-st,2)} seconds")
            self.log("Solving Dijkstra")
            g.solve_dijkstra()
            self.log("Solved!")
            self.log("Finding PQ pairs")
            st = time.time()
            pq_pairs: List[PriceQuantityUnitless] = g.generate_bid()
            self.log(f"Found in {round(time.time()-st,2)} seconds")

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

    def to_fahrenheit(self, t:float) -> float:
        return t*9/5+32
    
    def fill_missing_store_temps(self):
        all_store_layers = sorted([x for x in self.temperature_channel_names if 'tank' in x])
        for layer in all_store_layers:
            if (layer not in self.latest_temperatures 
            or self.to_fahrenheit(self.latest_temperatures[layer]/1000) < 70
            or self.to_fahrenheit(self.latest_temperatures[layer]/1000) > 200):
                self.latest_temperatures[layer] = None
        if H0CN.store_cold_pipe in self.latest_temperatures:
            value_below = self.latest_temperatures[H0CN.store_cold_pipe]
        else:
            value_below = 0
        for layer in sorted(all_store_layers, reverse=True):
            if self.latest_temperatures[layer] is None:
                self.latest_temperatures[layer] = value_below
            value_below = self.latest_temperatures[layer]  
        self.latest_temperatures = {k:self.latest_temperatures[k] for k in sorted(self.latest_temperatures)}

    def get_latest_temperatures(self):
        if not self.settings.is_simulated:
            temp = {
                x: self.data.latest_channel_values[x] 
                for x in self.temperature_channel_names
                if x in self.data.latest_channel_values
                and self.data.latest_channel_values[x] is not None
                }
            self.latest_temperatures = temp.copy()
        else:
            self.log("IN SIMULATION - set all temperatures to 60 degC")
            self.latest_temperatures = {}
            for channel_name in self.temperature_channel_names:
                self.latest_temperatures[channel_name] = 60 * 1000
        if list(self.latest_temperatures.keys()) == self.temperature_channel_names:
            self.temperatures_available = True
        else:
            self.temperatures_available = False
            all_buffer = [x for x in self.temperature_channel_names if 'buffer-depth' in x]
            available_buffer = [x for x in list(self.latest_temperatures.keys()) if 'buffer-depth' in x]
            if all_buffer == available_buffer:
                self.fill_missing_store_temps()
                self.temperatures_available = True

    def get_thermocline_and_centroids(self) -> Tuple[float, int]:
        # Get all tank temperatures in a dict, if you can't abort
        # TODO: what do we return when there are not enough temperatures available?
        self.get_latest_temperatures()
        if not self.temperatures_available:
            self.log("Not enough tank temperatures available to compute top temperature and thermocline!")
            return 0, 0
        all_store_layers = sorted([x for x in self.temperature_channel_names if 'tank' in x])
        try:
            tank_temps = {key: self.to_fahrenheit(self.latest_temperatures[key]/1000) for key in all_store_layers}
        except KeyError as e:
            self.log(f"Failed to get all the tank temps in get_thermocline_and_centroids! Bailing on process {e}")
            return 0, 0
        # Process the temperatures before clustering
        processed_temps = []
        for key in tank_temps:
            processed_temps.append(tank_temps[key])
        iter_count = 0
        while sorted(processed_temps, reverse=True) != processed_temps and iter_count<20:
            iter_count+=1
            processed_temps = []
            for key in tank_temps:
                if processed_temps:
                    if tank_temps[key] > processed_temps[-1]:
                        mean = round((processed_temps[-1] + tank_temps[key])/2)
                        processed_temps[-1] = mean
                        processed_temps.append(mean)
                    else:
                        processed_temps.append(tank_temps[key])
                else:
                    processed_temps.append(tank_temps[key])
            i = 0
            for key in tank_temps:
                tank_temps[key] = processed_temps[i]
                i+=1
            if iter_count == 20:
                processed_temps = sorted(processed_temps, reverse=True)
        # Cluster
        data = processed_temps.copy()
        labels = kmeans(data, k=2)
        cluster_top = sorted([data[i] for i in range(len(data)) if labels[i] == 0])
        cluster_bottom = sorted([data[i] for i in range(len(data)) if labels[i] == 1])
        if not cluster_top:
            cluster_top = cluster_bottom.copy()
            cluster_bottom = []
        if cluster_bottom:
            if max(cluster_bottom) > max(cluster_top):
                cluster_top_copy = cluster_top.copy()
                cluster_top = cluster_bottom.copy()
                cluster_bottom = cluster_top_copy
        thermocline = len(cluster_top)
        top_centroid_f = round(sum(cluster_top)/len(cluster_top),3)
        if cluster_bottom:
            bottom_centroid_f = round(sum(cluster_bottom)/len(cluster_bottom),3)
        else:
            bottom_centroid_f = min(cluster_top)
        self.log(f"Thermocline {thermocline}, top: {top_centroid_f} F, bottom: {bottom_centroid_f} F")
        # Post values
        t_ms = int(time.time() * 1000)
        self._send_to(
                self.primary_scada,
                SingleReading(
                    ChannelName="thermocline-position",
                    Value=thermocline,
                    ScadaReadTimeUnixMs=t_ms,
                ),
            )
        self._send_to(
                self.primary_scada,
                SingleReading(
                    ChannelName="top-centroid",
                    Value=int(top_centroid_f*1000),
                    ScadaReadTimeUnixMs=t_ms,
                ),
            )
        self._send_to(
                self.primary_scada,
                SingleReading(
                    ChannelName="bottom-centroid",
                    Value=int(bottom_centroid_f*1000),
                    ScadaReadTimeUnixMs=t_ms,
                ),
            )
        return top_centroid_f, thermocline

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