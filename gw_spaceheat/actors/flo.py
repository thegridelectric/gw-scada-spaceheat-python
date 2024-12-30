import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple
from named_types import PriceQuantityUnitless, FloParamsHouse0

def to_kelvin(t):
    return (t-32)*5/9 + 273.15

def to_celcius(t):
    return (t-32)*5/9

class DParams():
    def __init__(self, config: FloParamsHouse0) -> None:
        self.config = config
        self.start_time = config.StartUnixS
        self.horizon = config.HorizonHours
        self.num_layers = config.NumLayers
        self.storage_volume = config.StorageVolumeGallons
        self.max_hp_elec_in = config.HpMaxElecKw
        self.min_hp_elec_in = config.HpMinElecKw
        self.initial_top_temp = config.InitialTopTempF
        self.initial_thermocline = config.InitialThermocline
        self.storage_losses_percent = config.StorageLossesPercent
        self.reg_forecast = [x/10 for x in config.RegPriceForecast[:self.horizon]]
        self.dist_forecast = [x/10 for x in config.DistPriceForecast[:self.horizon]]
        self.lmp_forecast = [x/10 for x in config.LmpForecast[:self.horizon]]
        self.elec_price_forecast = [rp+dp+lmp for rp,dp,lmp in zip(self.reg_forecast, self.dist_forecast, self.lmp_forecast)]
        self.oat_forecast = config.OatForecastF[:self.horizon]
        self.ws_forecast = config.WindSpeedForecastMph[:self.horizon]
        self.alpha = config.AlphaTimes10/10
        self.beta = config.BetaTimes100/100
        self.gamma = config.GammaEx6/1e6
        self.no_power_rswt = -self.alpha/self.beta
        self.intermediate_power = config.IntermediatePowerKw
        self.intermediate_rswt = config.IntermediateRswtF
        self.dd_power = config.DdPowerKw
        self.dd_rswt = config.DdRswtF
        self.dd_delta_t = config.DdDeltaTF
        self.quadratic_coefficients = self.get_quadratic_coeffs()
        self.available_top_temps, self.energy_between_nodes = self.get_available_top_temps()
        self.load_forecast = [self.required_heating_power(oat,ws) for oat,ws in zip(self.oat_forecast,self.ws_forecast)]
        self.rswt_forecast = [self.required_swt(x) for x in self.load_forecast]
        self.check_hp_sizing()
        # TODO: add to config
        self.min_cop = 1
        self.max_cop = 3
        self.soft_constraint: bool = True
        # First time step can be shorter than an hour
        if datetime.fromtimestamp(self.start_time).minute > 0:
            self.fraction_of_hour_remaining: float = datetime.fromtimestamp(self.start_time).minute / 60
        else:
            self.fraction_of_hour_remaining: float = 1
        self.load_forecast[0] = self.load_forecast[0]*self.fraction_of_hour_remaining
        
    def check_hp_sizing(self):
        max_load_elec = max(self.load_forecast) / self.COP(min(self.oat_forecast), max(self.rswt_forecast))
        if max_load_elec > self.max_hp_elec_in:
            error_text = f"\nThe current parameters indicate that on the coldest hour of the forecast ({min(self.oat_forecast)} F):"
            error_text += f"\n- The heating requirement is {round(max(self.load_forecast),2)} kW"
            error_text += f"\n- The COP is {round(self.COP(min(self.oat_forecast), max(self.rswt_forecast)),2)}"
            error_text += f"\n=> Need a HP that can reach {round(max_load_elec,2)} kW electrical power"
            error_text += f"\n=> The given HP is undersized ({self.max_hp_elec_in} kW electrical power)"
            print(error_text)
        
    def COP(self, oat, lwt):
        oat = to_celcius(oat)
        lwt = to_celcius(lwt)
        return self.config.CopIntercept + self.config.CopOatCoeff*oat + self.config.CopLwtCoeff*lwt      

    def required_heating_power(self, oat, ws):
        r = self.alpha + self.beta*oat + self.gamma*ws
        return r if r>0 else 0

    def delivered_heating_power(self, swt):
        a, b, c = self.quadratic_coefficients
        d = a*swt**2 + b*swt + c
        return d if d>0 else 0

    def required_swt(self, rhp):
        a, b, c = self.quadratic_coefficients
        c2 = c - rhp
        return (-b + (b**2-4*a*c2)**0.5)/(2*a)

    def delta_T(self, swt):
        d = self.dd_delta_t/self.dd_power * self.delivered_heating_power(swt)
        d = 0 if swt<self.no_power_rswt else d
        return d if d>0 else 0
    
    def delta_T_inverse(self, rwt: float) -> float:
        a, b, c = self.quadratic_coefficients
        aa = -self.dd_delta_t/self.dd_power * a
        bb = 1-self.dd_delta_t/self.dd_power * b
        cc = -self.dd_delta_t/self.dd_power * c - rwt
        if bb**2-4*aa*cc < 0 or (-bb + (bb**2-4*aa*cc)**0.5)/(2*aa) - rwt > 30:
            return 30
        return (-bb + (bb**2-4*aa*cc)**0.5)/(2*aa) - rwt
    
    def get_quadratic_coeffs(self):
        x_rswt = np.array([self.no_power_rswt, self.intermediate_rswt, self.dd_rswt])
        y_hpower = np.array([0, self.intermediate_power, self.dd_power])
        A = np.vstack([x_rswt**2, x_rswt, np.ones_like(x_rswt)]).T
        return [float(x) for x in np.linalg.solve(A, y_hpower)] 
    
    def get_available_top_temps(self) -> Tuple[Dict, Dict]:
        available_temps = [self.initial_top_temp]
        x = self.initial_top_temp
        while round(x + self.delta_T_inverse(x),2) <= 185:
            x = round(x + self.delta_T_inverse(x),2)
            available_temps.append(int(x))
        while x+10 <= 185:
            x += 10
            available_temps.append(int(x))
        x = self.initial_top_temp
        while self.delta_T(x) >= 3:
            x = round(x - self.delta_T(x))
            available_temps.append(int(x))
        while x >= 70:
            x += -10
            available_temps.append(int(x))
        available_temps = sorted(available_temps)
        if max(available_temps) < 176:
            available_temps = available_temps + [185]
        energy_between_nodes = {}
        m_layer = self.storage_volume*3.785 / self.num_layers
        for i in range(1,len(available_temps)):
            temp_drop_f = available_temps[i] - available_temps[i-1]
            energy_between_nodes[available_temps[i]] = round(m_layer * 4.187/3600 * temp_drop_f*5/9,3)
        return available_temps, energy_between_nodes
    

class DNode():
    def __init__(self, time_slice:int, top_temp:float, thermocline:float, parameters:DParams):
        self.params = parameters
        # Position in graph
        self.time_slice = time_slice
        self.top_temp = top_temp
        self.thermocline = thermocline
        # Dijkstra's algorithm
        self.pathcost = 0 if time_slice==parameters.horizon else 1e9
        self.next_node = None
        # Absolute energy level
        tt_idx = parameters.available_top_temps.index(top_temp)
        tt_idx = tt_idx-1 if tt_idx>0 else tt_idx
        self.bottom_temp = parameters.available_top_temps[tt_idx]
        self.energy = self.get_energy()
        self.index = None

    def __repr__(self):
        return f"Node[time_slice:{self.time_slice}, top_temp:{self.top_temp}, thermocline:{self.thermocline}]"

    def get_energy(self):
        m_layer_kg = self.params.storage_volume*3.785 / self.params.num_layers
        kWh_above_thermocline = (self.thermocline-0.5)*m_layer_kg * 4.187/3600 * to_kelvin(self.top_temp)
        kWh_below_thermocline = (self.params.num_layers-self.thermocline+0.5)*m_layer_kg * 4.187/3600 * to_kelvin(self.bottom_temp)
        return kWh_above_thermocline + kWh_below_thermocline


class DEdge():
    def __init__(self, tail:DNode, head:DNode, cost:float, hp_heat_out:float):
        self.tail: DNode = tail
        self.head: DNode = head
        self.cost = cost
        self.hp_heat_out = hp_heat_out

    def __repr__(self):
        return f"Edge: {self.tail} --cost:{round(self.cost,3)}--> {self.head}"


class DGraph():
    def __init__(self, config: FloParamsHouse0):
        self.params = DParams(config)
        self.nodes: Dict[int, List[DNode]] = {}
        self.edges: Dict[DNode, List[DEdge]] = {}
        self.create_nodes()
        self.create_edges()

    def create_nodes(self):
        self.initial_node = DNode(0, self.params.initial_top_temp, self.params.initial_thermocline, self.params)
        for time_slice in range(self.params.horizon+1):
            self.nodes[time_slice] = [self.initial_node] if time_slice==0 else []
            self.nodes[time_slice].extend(
                DNode(time_slice, top_temp, thermocline, self.params)
                for top_temp in self.params.available_top_temps[1:]
                for thermocline in range(1,self.params.num_layers+1)
                if (time_slice, top_temp, thermocline) != (0, self.params.initial_top_temp, self.params.initial_thermocline)
            )

    def create_edges(self):
        
        self.bottom_node = DNode(0, self.params.available_top_temps[1], 1, self.params)
        self.top_node = DNode(0, self.params.available_top_temps[-1], self.params.num_layers, self.params)
        
        for h in range(self.params.horizon):
            
            for node_now in self.nodes[h]:
                self.edges[node_now] = []
                
                for node_next in self.nodes[h+1]:

                    # The losses might be lower than energy between two nodes
                    losses = self.params.storage_losses_percent/100 * (node_now.energy-self.bottom_node.energy)
                    if h==0:
                        losses = losses * self.params.fraction_of_hour_remaining
                    if self.params.load_forecast[h]==0 and losses>0 and losses<self.params.energy_between_nodes[node_now.top_temp]:
                        losses = self.params.energy_between_nodes[node_now.top_temp] + 1/1e9

                    store_heat_in = node_next.energy - node_now.energy
                    hp_heat_out = store_heat_in + self.params.load_forecast[h] + losses

                    # The first time step is not necessarily a full hour
                    if h==0:
                        min_hp_elec_in = self.params.min_hp_elec_in * self.params.fraction_of_hour_remaining
                        max_hp_elec_in = self.params.max_hp_elec_in * self.params.fraction_of_hour_remaining
                    else:
                        min_hp_elec_in = self.params.min_hp_elec_in
                        max_hp_elec_in = self.params.max_hp_elec_in
                    
                    # This condition reduces the amount of times we need to compute the COP
                    if (hp_heat_out/self.params.max_cop <= max_hp_elec_in and
                        hp_heat_out/self.params.min_cop >= min_hp_elec_in):
                    
                        cop = self.params.COP(oat=self.params.oat_forecast[h], lwt=node_next.top_temp)

                        if (hp_heat_out/cop <= max_hp_elec_in and 
                            hp_heat_out/cop >= min_hp_elec_in):

                            cost = self.params.elec_price_forecast[h]/100 * hp_heat_out/cop

                            # If some of the load is satisfied by the storage
                            # Then it must satisfy the SWT requirement
                            if store_heat_in < 0:
                                if ((hp_heat_out < self.params.load_forecast[h] and 
                                     self.params.load_forecast[h] > 0)
                                     and
                                    (node_now.top_temp < self.params.rswt_forecast[h] or 
                                     node_next.top_temp < self.params.rswt_forecast[h])):
                                    if self.params.soft_constraint:
                                        # TODO: make cost punishment proportional to constraint violation
                                        cost += 1e5
                                    else:
                                        continue
                            
                            self.edges[node_now].append(DEdge(node_now, node_next, cost, hp_heat_out))

    def solve_dijkstra(self):
        for time_slice in range(self.params.horizon-1, -1, -1):
            for node in self.nodes[time_slice]:
                best_edge = min(self.edges[node], key=lambda e: e.head.pathcost + e.cost)
                if best_edge.hp_heat_out < 0: 
                    best_edge_neg = max([e for e in self.edges[node] if e.hp_heat_out<0], key=lambda e: e.hp_heat_out)
                    best_edge_pos = min([e for e in self.edges[node] if e.hp_heat_out>=0], key=lambda e: e.hp_heat_out)
                    best_edge = best_edge_pos if (-best_edge_neg.hp_heat_out >= best_edge_pos.hp_heat_out) else best_edge_neg
                node.pathcost = best_edge.head.pathcost + best_edge.cost
                node.next_node = best_edge.head
    
    def generate_bid(self):
        self.pq_pairs = []
        min_elec_ctskwh, max_elec_ctskwh = -10, 200
        for elec_price in range(min_elec_ctskwh*10, max_elec_ctskwh*10):
            elec_price = elec_price/10
            elec_to_nextnode = []
            pathcost_from_nextnode = []
            for e in self.edges[self.initial_node]:
                cop = self.params.COP(oat=self.params.oat_forecast[0], lwt=e.head.top_temp)
                elec_to_nextnode.append(e.hp_heat_out/cop if e.hp_heat_out/cop>0 else 0)
                pathcost_from_nextnode.append(e.head.pathcost)
            cost_to_nextnode = [x*elec_price/100 for x in elec_to_nextnode]
            pathcost_from_current_node = [x+y for x,y in zip(cost_to_nextnode, pathcost_from_nextnode)]
            min_pathcost_elec = elec_to_nextnode[pathcost_from_current_node.index(min(pathcost_from_current_node))]
            if self.pq_pairs:
                # Record a new pair if at least 0.01 kWh of difference in quantity with the previous one
                if self.pq_pairs[-1].QuantityTimes1000 - int(min_pathcost_elec * 1000) > 10:
                    self.pq_pairs.append(
                        PriceQuantityUnitless(
                            PriceTimes1000 = int(elec_price*10 * 1000),         # usd/mwh * 1000
                            QuantityTimes1000 = int(min_pathcost_elec * 1000))  # kWh * 1000 = Wh
                    )
            else:
                self.pq_pairs.append(
                    PriceQuantityUnitless(
                        PriceTimes1000 = int(elec_price*10 * 1000),         # usd/mwh * 1000
                        QuantityTimes1000 = int(min_pathcost_elec * 1000))  # kWh * 1000
                )
        return self.pq_pairs