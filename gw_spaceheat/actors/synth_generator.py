import time
import json
import pytz
import asyncio
import aiohttp
import numpy as np
from typing import Optional, Sequence, List
from result import Ok, Result
from datetime import datetime, timedelta
from actors.scada_data import ScadaData
from gwproto import Message

from gwproto.named_types import SingleReading, PowerWatts
from gwproactor import MonitoredName, ServicesInterface
from gwproactor.message import PatInternalWatchdogMessage

from actors.scada_actor import ScadaActor
from data_classes.house_0_names import H0CN
from named_types import EnergyInstruction, Ha1Params

# -------------- TODO: move to named_types -------------
from typing import Literal
from pydantic import BaseModel
from gwproto.property_format import LeftRightDotStr

class RemainingElec(BaseModel):
    FromGNodeAlias: LeftRightDotStr
    RemainingWattHours: int
    TypeName: Literal["remaining.elec"] = "remaining.elec"
    Version: Literal["000"] = "000"

class WeatherForecast(BaseModel):
    Time: List[datetime]
    OatForecast: List[float]
    WsForecast: List[float]
    AvgPowerForecast: List[float]
    RswtForecast: List[float]
    RswtDeltaTForecast: List[float]
    TypeName: Literal["weather.forecast"] = "weather.forecast"
    Version: Literal["000"] = "000"

class PriceForecast(BaseModel):
    DpForecast: List[float]
    LmpForecsat: List[float]
    TypeName: Literal["price.forecast"] = "price.forecast"
    Version: Literal["000"] = "000"
# -------------- TODO: move to named_types -------------


class SynthGenerator(ScadaActor):
    MAIN_LOOP_SLEEP_SECONDS = 60

    def __init__(self, name: str, services: ServicesInterface):
        super().__init__(name, services)
        self.cn: H0CN = self.layout.channel_names
        self._stop_requested: bool = False
        self.hardware_layout = self._services.hardware_layout
        self.temperature_channel_names = [
            H0CN.buffer.depth1, H0CN.buffer.depth2, H0CN.buffer.depth3, H0CN.buffer.depth4,
            H0CN.hp_ewt, H0CN.hp_lwt, H0CN.dist_swt, H0CN.dist_rwt, 
            H0CN.buffer_cold_pipe, H0CN.buffer_hot_pipe, H0CN.store_cold_pipe, H0CN.store_hot_pipe,
            *(depth for tank in self.cn.tank.values() for depth in [tank.depth1, tank.depth2, tank.depth3, tank.depth4])
        ]
        self.elec_assigned_amount = None
        self.previous_time = None
        self.temperatures_available = False

        # House parameters in the .env file
        self.is_simulated = self.settings.is_simulated
        self.timezone = pytz.timezone(self.settings.timezone_str)
        self.latitude = self.settings.latitude
        self.longitude = self.settings.longitude

        # used by the rswt quad params calculator
        self._cached_params: Optional[Ha1Params] = None 
        self._rswt_quadratic_params: Optional[np.ndarray] = None 
    
        self.log(f"self.timezone: {self.timezone}")
        self.log(f"self.latitude: {self.latitude}")
        self.log(f"self.longitude: {self.longitude}")
        self.log(f"Params: {self.params}")
        self.log(f"self.is_simulated: {self.is_simulated}")

        # For the weather forecast
        self.weather = None
        self.coldest_oat_by_month = [-3, -7, 1, 21, 30, 31, 46, 47, 28, 24, 16, 0]
    
    @property
    def data(self) -> ScadaData:
        return self._services.data
    
    @property
    def params(self) -> Ha1Params:
        return self.data.ha1_params
    
    @property
    def no_power_rswt(self) -> float:
        alpha = self.params.AlphaTimes10 / 10
        beta = self.params.BetaTimes100 / 100
        return -alpha/beta

    @property
    def rswt_quadratic_params(self) -> np.ndarray:
        """Property to get quadratic parameters for calculating heating power 
        from required source water temp, recalculating if necessary
        """
        if self.params != self._cached_params:
            intermediate_rswt = self.params.IntermediateRswtF
            dd_rswt = self.params.DdRswtF
            intermediate_power = self.params.IntermediatePowerKw
            dd_power = self.params.DdPowerKw
            x_rswt = np.array([self.no_power_rswt, intermediate_rswt, dd_rswt])
            y_hpower = np.array([0, intermediate_power, dd_power])
            A = np.vstack([x_rswt**2, x_rswt, np.ones_like(x_rswt)]).T
            self._rswt_quadratic_params = np.linalg.solve(A, y_hpower)
            self._cached_params = self.params
            self.log(f"Calculating rswt_quadratic_params: {self._rswt_quadratic_params}")
        
        if self._rswt_quadratic_params is None:
            raise Exception("_rswt_quadratic_params should have been set here!!")
        return self._rswt_quadratic_params

    def start(self) -> None:
        self.services.add_task(
            asyncio.create_task(self.main(), name="Synth Generator keepalive")
        )

    @property
    def monitored_names(self) -> Sequence[MonitoredName]:
        return [MonitoredName(self.name, self.MAIN_LOOP_SLEEP_SECONDS * 2.1)]
    
    async def main(self):
        async with aiohttp.ClientSession() as session:
            await self.main_loop(session)

    async def main_loop(self, session: aiohttp.ClientSession) -> None:
        await self.get_weather(session)
        await asyncio.sleep(2)
        while not self._stop_requested:
            self._send(PatInternalWatchdogMessage(src=self.name))

            if datetime.now(self.timezone)>self.weather['time'][0]:
                await self.get_weather(session)

            self.get_latest_temperatures()
            if self.temperatures_available:
                self.update_energy()

            self.update_remaining_elec()

            await asyncio.sleep(self.MAIN_LOOP_SLEEP_SECONDS)

    def stop(self) -> None:
        self._stop_requested = True
        
    async def join(self):
        ...

    def process_message(self, message: Message) -> Result[bool, BaseException]:
        match message.Payload:
            case EnergyInstruction():
                self.process_energy_instruction(message.Payload)
            case PowerWatts():
                self.update_remaining_elec()
                self.previous_watts = message.Payload.Watts
        return Ok(True)
    
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
    
    # Receive latest temperatures
    def get_latest_temperatures(self):
        if not self.is_simulated:
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

    def process_energy_instruction(self, payload: EnergyInstruction) -> None:
        self.elec_assigned_amount = payload.AvgPowerWatts * payload.SlotDurationMinutes/60
        self.elec_used_since_assigned_time = 0
        self.log(f"Received an EnergyInstruction for {self.elec_assigned_amount} Watts average power")
        if self.is_simulated:
            self.previous_watts = 1000
        else:
            self.previous_watts = self.data.latest_channel_values[H0CN.hp_idu_pwr] + self.data.latest_channel_values[H0CN.hp_odu_pwr]
        self.previous_time = payload.SendTimeMs

    def update_remaining_elec(self) -> None:
        if self.elec_assigned_amount is None or self.previous_time is None:
            return
        time_now = time.time() * 1000
        self.log(f"The HP power was {round(self.previous_watts,1)} Watts {round((time_now-self.previous_time)/1000,1)} seconds ago")
        elec_watthours = self.previous_watts * (time_now - self.previous_time)/1000/3600
        self.log(f"This corresponds to an additional {round(elec_watthours,1)} Wh of electricity used")
        self.elec_used_since_assigned_time += elec_watthours
        self.log(f"Electricity used since EnergyInstruction: {round(self.elec_used_since_assigned_time,1)} Wh")
        remaining_wh = int(self.elec_assigned_amount - self.elec_used_since_assigned_time)
        self.log(f"Remaining electricity to be used from EnergyInstruction: {remaining_wh} Wh")
        remaining = RemainingElec(
            FromGNodeAlias=self.layout.atn_g_node_alias,
            RemainingWattHours=remaining_wh
        )
        self._send_to(self.atomic_ally, remaining)
        self.previous_time = time_now

    # Compute usable and required energy
    def update_energy(self) -> None:
        time_now = datetime.now(self.timezone)
        latest_temperatures = self.latest_temperatures.copy()
        storage_temperatures = {k:v for k,v in latest_temperatures.items() if 'tank' in k}
        simulated_layers = [self.to_fahrenheit(v/1000) for k,v in storage_temperatures.items()]        
        self.usable_kwh = 0
        while True:
            if round(self.rwt(simulated_layers[0])) == round(simulated_layers[0]):
                simulated_layers = [sum(simulated_layers)/len(simulated_layers) for x in simulated_layers]
                if round(self.rwt(simulated_layers[0])) == round(simulated_layers[0]):
                    break
            self.usable_kwh += 360/12*3.78541 * 4.187/3600 * (simulated_layers[0]-self.rwt(simulated_layers[0]))*5/9
            simulated_layers = simulated_layers[1:] + [self.rwt(simulated_layers[0])]          
        self.required_kwh = self.get_required_storage(time_now) # TODO
        self.log(f"Usable energy: {round(self.usable_kwh,1)} kWh")
        self.log(f"Required energy: {round(self.required_kwh,1)} kWh")

        # Post usable and required energy
        t_ms = int(time.time() * 1000)
        self._send_to(
                self.primary_scada,
                SingleReading(
                    ChannelName="usable-energy",
                    Value=int(self.usable_kwh*1000),
                    ScadaReadTimeUnixMs=t_ms,
                ),
            )
        self._send_to(
                self.primary_scada,
                SingleReading(
                    ChannelName="required-energy",
                    Value=int(self.required_kwh*1000),
                    ScadaReadTimeUnixMs=t_ms,
                ),
            )
        
    def get_required_storage(self, time_now: datetime) -> float:
        morning_kWh = sum(
            [kwh for t, kwh in zip(list(self.weather['time']), list(self.weather['avg_power'])) 
             if 7<=t.hour<=11]
            )
        midday_kWh = sum(
            [kwh for t, kwh in zip(list(self.weather['time']), list(self.weather['avg_power'])) 
             if 12<=t.hour<=15]
            )
        afternoon_kWh = sum(
            [kwh for t, kwh in zip(list(self.weather['time']), list(self.weather['avg_power'])) 
             if 16<=t.hour<=19]
            )
        # if (((time_now.weekday()<4 or time_now.weekday()==6) and time_now.hour>=20)
        #     or (time_now.weekday()<5 and time_now.hour<=6)):
        if (time_now.hour>=20 or time_now.hour<=6):
            self.log('Preparing for a morning onpeak + afternoon onpeak')
            afternoon_missing_kWh = afternoon_kWh - (4*self.params.HpMaxKwTh - midday_kWh) # TODO make the kW_th a function of COP and kW_el
            return morning_kWh if afternoon_missing_kWh<0 else morning_kWh + afternoon_missing_kWh
        # elif (time_now.weekday()<5 and time_now.hour>=12 and time_now.hour<16):
        elif (time_now.hour>=12 and time_now.hour<16):
            self.log('Preparing for an afternoon onpeak')
            return afternoon_kWh
        else:
            self.log('Currently in on-peak or no on-peak period coming up soon')
            return 0

    def to_celcius(self, t: float) -> float:
        return (t-32)*5/9

    def to_fahrenheit(self, t:float) -> float:
        return t*9/5+32

    def delta_T(self, swt: float) -> float:
        a, b, c = self.rswt_quadratic_params
        delivered_heat_power = a*swt**2 + b*swt + c
        dd_delta_t = self.params.DdDeltaTF
        dd_power = self.params.DdPowerKw
        d = dd_delta_t/dd_power * delivered_heat_power
        return d if d>0 else 0
        
    def required_heating_power(self, oat: float, wind_speed_mph: float) -> float:
        ws = wind_speed_mph
        alpha = self.params.AlphaTimes10 / 10
        beta = self.params.BetaTimes100 / 100
        gamma = self.params.GammaEx6 / 1e6
        r = alpha + beta*oat + gamma*ws
        return round(r,2) if r>0 else 0

    def required_swt(self, required_kw_thermal: float) -> float:
        a, b, c = self.rswt_quadratic_params
        c2 = c - required_kw_thermal
        return round((-b + (b**2-4*a*c2)**0.5)/(2*a), 2)
    
    def get_price_forecast(self) -> None:
        daily_dp = [50.13]*7 + [487.63]*5 + [54.98]*4 + [487.63]*4 + [50.13]*4
        dp_forecast_usd_per_mwh = (daily_dp[datetime.now(tz=self.timezone).hour+1:] + daily_dp[:datetime.now(tz=self.timezone).hour+1])*2
        lmp_forecast_usd_per_mwh = [102]*48
        pf = PriceForecast(
            Time = [datetime.now(tz=self.timezone)+timedelta(hours=1+x) for x in range(48)],
            DpForecast = dp_forecast_usd_per_mwh,
            LmpForecsat = lmp_forecast_usd_per_mwh,
        )
        self._send_to(self.atomic_ally, pf)

    async def get_weather(self, session: aiohttp.ClientSession) -> None:
        config_dir = self.settings.paths.config_dir
        weather_file = config_dir / "weather.json"
        try:
            url = f"https://api.weather.gov/points/{self.latitude},{self.longitude}"
            response = await session.get(url)
            if response.status != 200:
                self.log(f"Error fetching weather data: {response.status}")
                return None
            data = await response.json()
            forecast_hourly_url = data['properties']['forecastHourly']
            forecast_response = await session.get(forecast_hourly_url)
            if forecast_response.status != 200:
                self.log(f"Error fetching hourly weather forecast: {forecast_response.status}")
                return None
            forecast_data = await forecast_response.json()
            forecasts = {}
            periods = forecast_data['properties']['periods']
            for period in periods:
                if ('temperature' in period and 'startTime' in period 
                    and datetime.fromisoformat(period['startTime'])>datetime.now(tz=self.timezone)):
                    forecasts[datetime.fromisoformat(period['startTime'])] = period['temperature']
            forecasts = dict(list(forecasts.items())[:96])
            cropped_forecast = dict(list(forecasts.items())[:48])
            self.weather = {
                'time': list(cropped_forecast.keys()),
                'oat': list(cropped_forecast.values()),
                'ws': [0]*len(cropped_forecast)
                }
            self.log(f"Obtained a {len(forecasts)}-hour weather forecast starting at {self.weather['time'][0]}")
            weather_long = {
                'time': [x.timestamp() for x in list(forecasts.keys())],
                'oat': list(forecasts.values()),
                'ws': [0]*len(forecasts)
                }
            with open(weather_file, 'w') as f:
                json.dump(weather_long, f, indent=4) 
        
        except Exception as e:
            self.log(f"[!] Unable to get weather forecast from API: {e}")
            try:
                with open(weather_file, 'r') as f:
                    weather_long = json.load(f)
                    weather_long['time'] = [datetime.fromtimestamp(x, tz=self.timezone) for x in weather_long['time']]
                if weather_long['time'][-1] >= datetime.fromtimestamp(time.time(), tz=self.timezone)+timedelta(hours=48):
                    self.log("A valid weather forecast is available locally.")
                    time_late = weather_long['time'][0] - datetime.now(self.timezone)
                    hours_late = int(time_late.total_seconds()/3600)
                    self.weather = weather_long
                    for key in self.weather:
                        self.weather[key] = self.weather[key][hours_late:hours_late+48]
                else:
                    self.log("No valid weather forecasts available locally. Using coldest of the current month.")
                    current_month = datetime.now().month-1
                    self.weather = {
                        'time': [datetime.now(tz=self.timezone)+timedelta(hours=1+x) for x in range(48)],
                        'oat': [self.coldest_oat_by_month[current_month]]*48,
                        'ws': [0]*48,
                        }
            except Exception as e:
                self.log("No valid weather forecasts available locally. Using coldest of the current month.")
                current_month = datetime.now().month-1
                self.weather = {
                    'time': [datetime.now(tz=self.timezone)+timedelta(hours=1+x) for x in range(48)],
                    'oat': [self.coldest_oat_by_month[current_month]]*48,
                    'ws': [0]*48,
                    }

        self.weather['avg_power'] = [
            self.required_heating_power(oat, ws) 
            for oat, ws in zip(self.weather['oat'], self.weather['ws'])
            ]
        self.weather['required_swt'] = [
            self.required_swt(x) 
            for x in self.weather['avg_power']
            ]
        # Send weather forecast to relevant scada actors
        wf = WeatherForecast(
            Time = self.weather['time'],
            OatForecast = self.weather['oat'],
            WsForecast = self.weather['ws'],
            AvgPowerForecast = self.weather['avg_power'],
            RswtForecast = self.weather['required_swt'],
            RswtDeltaTForecast = [round(self.delta_T(x),2) for x in self.weather['required_swt']]
        )
        self._send_to(self.home_alone, wf)
        # Todo: broadcast weather forecast for ability to analyze HomeAlone actions
        # Crop to use only 24 hours of forecast in this code
        for key in self.weather:
            self.weather[key] = self.weather[key][:24]
        self.log(f"OAT = {self.weather['oat']}")
        self.log(f"Average Power = {self.weather['avg_power']}")
        self.log(f"RSWT = {self.weather['required_swt']}")
        self.log(f"DeltaT at RSWT = {[round(self.delta_T(x),2) for x in self.weather['required_swt']]}")

    def rwt(self, swt: float, return_rswt_onpeak=False) -> float:
        timenow = datetime.now(self.timezone)
        if timenow.hour > 19 or timenow.hour < 12:
            required_swt = max(
                [rswt for t, rswt in zip(self.weather['time'], self.weather['required_swt'])
                if t.hour in [7,8,9,10,11,16,17,18,19]]
                )
        else:
            required_swt = max(
                [rswt for t, rswt in zip(self.weather['time'], self.weather['required_swt'])
                if t.hour in [16,17,18,19]]
                )
        if return_rswt_onpeak:
            return required_swt
        if swt < required_swt - 10:
            delta_t = 0
        elif swt < required_swt:
            delta_t = self.delta_T(required_swt) * (swt-(required_swt-10))/10
        else:
            delta_t = self.delta_T(swt)
        return round(swt - delta_t,2)