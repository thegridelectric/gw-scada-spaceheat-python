from gwproactor import ServicesInterface
from actors.config import ScadaSettings
from typing import Optional
import asyncio
import time
import numpy as np
import requests
import json
from gwproto import Message
from actors.scada_data import ScadaData
from result import Ok, Result
from datetime import datetime, timedelta
import pytz
from gwproto.named_types import GoDormant, Ha1Params, SingleReading, WakeUp

from actors.scada_actor import ScadaActor
class SynthGenerator(ScadaActor):
    MAIN_LOOP_SLEEP_SECONDS = 60

    def __init__(self, name: str, services: ServicesInterface):
        super().__init__(name, services)
        self._stop_requested = False
        self.timezone = pytz.timezone(self.settings.timezone_str)

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

        # Get the weather forecast
        self.weather = None
        self.coldest_oat_by_month = [-3, -7, 1, 21, 30, 31, 46, 47, 28, 24, 16, 0]
        self.get_weather()

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

    async def main(self):
        await asyncio.sleep(2)
        self.log("In synth gen main loop")
        while not self._stop_requested:

            if datetime.now(self.timezone)>self.weather['time'][0]:
                self.get_weather()

            self.get_latest_temperatures()
            self.update_energy()

            await asyncio.sleep(self.MAIN_LOOP_SLEEP_SECONDS)

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
    
    @property
    def data(self) -> ScadaData:
        return self._services.data
    
    @property
    def params(self) -> Ha1Params:
        return self.data.ha1_params
    
    # Receive latest temperatures
    def get_latest_temperatures(self):
        temp = {
            x: self.data.latest_channel_values[x] 
            for x in self.temperature_channel_names
            if x in self.data.latest_channel_values
            and self.data.latest_channel_values[x] is not None
            }
        self.latest_temperatures = temp.copy()
        if list(self.latest_temperatures.keys()) == self.temperature_channel_names:
            self.temperatures_available = True
        else:
            self.temperatures_available = False
            all_buffer = [x for x in self.temperature_channel_names if 'buffer-depth' in x]
            available_buffer = [x for x in list(self.latest_temperatures.keys()) if 'buffer-depth' in x]
            if all_buffer == available_buffer:
                self.fill_missing_store_temps()
                self.temperatures_available = True

    # Compute usable and required energy
    def update_energy(self) -> bool:
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
            self.log('No onpeak period coming up soon')
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
        rhp = required_kw_thermal
        a, b, c = self.rswt_quadratic_params
        return round(-b/(2*a) + ((rhp-b**2/(4*a)+b**2/(2*a)-c)/a)**0.5,2)

    def get_weather(self) -> None:
        config_dir = self.settings.paths.config_dir
        weather_file = config_dir / "weather.json"
        try:
            url = f"https://api.weather.gov/points/{self.latitude},{self.longitude}"
            response = requests.get(url)
            if response.status_code != 200:
                self.log(f"Error fetching weather data: {response.status_code}")
                return None
            data = response.json()
            forecast_hourly_url = data['properties']['forecastHourly']
            forecast_response = requests.get(forecast_hourly_url)
            if forecast_response.status_code != 200:
                self.log(f"Error fetching hourly weather forecast: {forecast_response.status_code}")
                return None
            forecast_data = forecast_response.json()
            forecasts = {}
            periods = forecast_data['properties']['periods']
            for period in periods:
                if ('temperature' in period and 'startTime' in period 
                    and datetime.fromisoformat(period['startTime'])>datetime.now(tz=self.timezone)):
                    forecasts[datetime.fromisoformat(period['startTime'])] = period['temperature']
            forecasts = dict(list(forecasts.items())[:96])
            cropped_forecast = dict(list(forecasts.items())[:24])
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
                if weather_long['time'][-1] >= datetime.fromtimestamp(time.time(), tz=self.timezone)+timedelta(hours=24):
                    self.log("A valid weather forecast is available locally.")
                    time_late = weather_long['time'][0] - datetime.now(self.timezone)
                    hours_late = int(time_late.total_seconds()/3600)
                    self.weather = weather_long
                    for key in self.weather:
                        self.weather[key] = self.weather[key][hours_late:hours_late+24]
                else:
                    self.log("No valid weather forecasts available locally. Using coldest of the current month.")
                    current_month = datetime.now().month-1
                    self.weather = {
                        'time': [datetime.now(tz=self.timezone)+timedelta(hours=1+x) for x in range(24)],
                        'oat': [self.coldest_oat_by_month[current_month]]*24,
                        'ws': [0]*24,
                        }
            except Exception as e:
                self.log("No valid weather forecasts available locally. Using coldest of the current month.")
                current_month = datetime.now().month-1
                self.weather = {
                    'time': [datetime.now(tz=self.timezone)+timedelta(hours=1+x) for x in range(24)],
                    'oat': [self.coldest_oat_by_month[current_month]]*24,
                    'ws': [0]*24,
                    }

        self.weather['avg_power'] = [
            self.required_heating_power(oat, ws) 
            for oat, ws in zip(self.weather['oat'], self.weather['ws'])
            ]
        self.weather['required_swt'] = [
            self.required_swt(x) 
            for x in self.weather['avg_power']
            ]
        self.log(f"OAT = {self.weather['oat']}")
        self.log(f"Average Power = {self.weather['avg_power']}")
        self.log(f"RSWT = {self.weather['required_swt']}")
        self.log(f"DeltaT at RSWT = {[round(self.delta_T(x),2) for x in self.weather['required_swt']]}")