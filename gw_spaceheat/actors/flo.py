import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple
from named_types import PriceQuantityUnitless, FloParamsHouse0
from typing import Optional

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
        self.initial_bottom_temp = config.InitialBottomTempF
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
        self.hp_is_off = config.HpIsOff
        self.hp_turn_on_minutes = config.HpTurnOnMinutes
        self.quadratic_coefficients = self.get_quadratic_coeffs()
        self.temperature_stack = self.get_available_top_temps()
        self.load_forecast = [self.required_heating_power(oat,ws) for oat,ws in zip(self.oat_forecast,self.ws_forecast)]
        self.rswt_forecast = [self.required_swt(x) for x in self.load_forecast]
        # Modify load forecast to include energy available in the buffer
        available_buffer = config.BufferAvailableKwh
        i = 0
        while available_buffer > 0 and i < len(self.load_forecast):
            load_backup = self.load_forecast[i]
            self.load_forecast[i] = self.load_forecast[i] - min(available_buffer, self.load_forecast[i])
            available_buffer = available_buffer - min(available_buffer, load_backup)
            i += 1
        # Modify load forecast to include energy available in the house (zones above thermostat)
        available_house = config.HouseAvailableKwh
        i = 0
        if available_house < 0:
            self.load_forecast[0] += -available_house
        else:
            while available_house > 0 and i < len(self.load_forecast):
                load_backup = self.load_forecast[i]
                self.load_forecast[i] = self.load_forecast[i] - min(available_house, self.load_forecast[i])
                available_house = available_house - min(available_house, load_backup)
                i += 1
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
        # Find the first top temperature above RSWT for each hour
        self.rswt_plus = {}
        for rswt in self.rswt_forecast:
            self.rswt_plus[rswt] = self.first_top_temp_above_rswt(rswt)
        
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
        if oat < self.config.CopMinOatF: 
            return self.config.CopMin
        else:
            return self.config.CopIntercept + self.config.CopOatCoeff * oat

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
        MIN_BOTTOM_TEMP, MAX_TOP_TEMP = 100, 175

        if self.initial_bottom_temp < self.initial_top_temp - self.delta_T(self.initial_top_temp):
            self.initial_bottom_temp = round(self.initial_top_temp - self.delta_T(self.initial_top_temp))

        self.max_thermocline = self.num_layers
        if self.initial_top_temp > MAX_TOP_TEMP-5:
            self.max_thermocline = self.initial_thermocline

        available_temps = []
        height_top = self.initial_thermocline
        height_bottom = self.num_layers - self.initial_thermocline

        # Add temperatures above initial tank
        t = self.initial_top_temp
        b = self.initial_bottom_temp
        while t < MAX_TOP_TEMP or b < MAX_TOP_TEMP:
            if t > MAX_TOP_TEMP:
                available_temps.append((b, height_bottom))
                b = round(b + self.delta_T_inverse(b))
            else:
                available_temps.append((b, height_bottom))
                available_temps.append((t, height_top))
                t = round(t + self.delta_T_inverse(t))
                b = round(b + self.delta_T_inverse(b))

        # Add temperatures below initial tank
        t = round(self.initial_top_temp - self.delta_T(self.initial_top_temp))
        b = round(self.initial_bottom_temp - self.delta_T(self.initial_bottom_temp))
        while b > MIN_BOTTOM_TEMP or t > MIN_BOTTOM_TEMP:
            if b < MIN_BOTTOM_TEMP:
                available_temps = [(t, height_top)] + available_temps
                t = round(t - self.delta_T(t))
            else:
                available_temps = [(t, height_top)] + available_temps
                available_temps = [(b, height_bottom)] + available_temps
                t = round(t - self.delta_T(t))
                b = round(b - self.delta_T(b))

        self.available_top_temps = [x[0] for x in available_temps]
        if self.available_top_temps != sorted(self.available_top_temps):
            for i in range(1, len(available_temps)):
                available_temps[i] = (max(available_temps[i][0], available_temps[i-1][0]), available_temps[i][1])

        available_temps_no_duplicates = []
        skip_next_i = False
        for i in range(len(available_temps)):
            if i<len(available_temps)-1 and available_temps[i][0] == available_temps[i+1][0]:
                available_temps_no_duplicates.append((available_temps[i][0], available_temps[i][1]+available_temps[i+1][1]))
                skip_next_i = True
            elif not skip_next_i:
                available_temps_no_duplicates.append(available_temps[i])
            else:
                skip_next_i = False
        available_temps = available_temps_no_duplicates.copy()
            
        if max([x[0] for x in available_temps]) < MAX_TOP_TEMP-5:
            available_temps.append((MAX_TOP_TEMP-5, self.num_layers))

        if self.max_thermocline == self.num_layers and available_temps[-1][1] < self.num_layers:
            available_temps[-1] = (available_temps[-1][0], self.num_layers)

        self.available_top_temps = [x[0] for x in available_temps]
        if self.available_top_temps != sorted(self.available_top_temps):
            print("ERROR sorted is not the same")

        # heights = [x[1] for x in available_temps]
        # fig, ax = plt.subplots(figsize=(8, 6))
        # cmap = matplotlib.colormaps['Reds']
        # norm = plt.Normalize(min(self.available_top_temps)-20, max(self.available_top_temps)+20)
        # bottom = 0
        # for i in range(len(available_temps)):
        #     color = cmap(norm(self.available_top_temps[i]))
        #     ax.bar(0, heights[i], bottom=bottom, color=color, width=1)
        #     ax.text(0, bottom + heights[i]/2, str(self.available_top_temps[i]), ha='center', va='center', fontsize=10, color='white')
        #     if i < len(available_temps)-1:
        #         bottom += heights[i]
        # ax.set_xticks([])
        # ax.set_xlim([-2,2])
        # plt.title(self.initial_top_temp)
        # plt.tight_layout()
        # plt.show()

        self.energy_between_nodes = {}
        m_layer = self.storage_volume*3.785 / self.num_layers
        for i in range(1,len(self.available_top_temps)):
            temp_drop_f = self.available_top_temps[i] - self.available_top_temps[i-1]
            self.energy_between_nodes[self.available_top_temps[i]] = round(m_layer * 4.187/3600 * temp_drop_f*5/9,3)

        return available_temps

    def first_top_temp_above_rswt(self, rswt):
        for x in sorted(self.available_top_temps):
            if x > rswt:
                return x

class DNode():
    def __init__(self, time_slice:int, top_temp:float, thermocline1:float, parameters:DParams, hinge_node=None):
        self.params = parameters
        # Position in graph
        self.time_slice = time_slice
        self.top_temp = top_temp
        self.thermocline1 = thermocline1
        if not hinge_node:
            temperatures = [x[0] for x in self.params.temperature_stack]
            heights = [x[1] for x in self.params.temperature_stack]
            toptemp_idx = temperatures.index(top_temp)
            height_first_two_layers = thermocline1 + heights[toptemp_idx-1]
            if height_first_two_layers >= self.params.num_layers or toptemp_idx < 2:
                self.middle_temp = None
                self.bottom_temp = temperatures[toptemp_idx-1]
                self.thermocline2 = None
            else:
                self.middle_temp = temperatures[toptemp_idx-1]
                self.bottom_temp = temperatures[toptemp_idx-2]
                self.thermocline2 = height_first_two_layers
            # Dijkstra's algorithm
            self.pathcost = 0 if time_slice==parameters.horizon else 1e9
            self.next_node = None
            # Absolute energy level
            self.energy = self.get_energy()
            self.index = None
        else:
            self.middle_temp = hinge_node['middle_temp']
            self.thermocline2 = hinge_node['thermocline2']
            self.bottom_temp = hinge_node['bottom_temp']
            self.pathcost = hinge_node['pathcost']
            self.energy = self.get_energy()

    def __repr__(self):
        if self.thermocline2 is not None:
            return f"{self.top_temp}({self.thermocline1}){self.middle_temp}({self.thermocline2}){self.bottom_temp}"
            # return f"Node[top:{self.top_temp}, thermocline1:{self.thermocline1}, middle:{self.middle_temp}, thermocline2:{self.thermocline2}, bottom:{self.bottom_temp}]"
        else:
            return f"{self.top_temp}({self.thermocline1}){self.bottom_temp}"
            # return f"Node[top:{self.top_temp}, thermocline1:{self.thermocline1}, bottom:{self.bottom_temp}]"

    def get_energy(self):
        m_layer_kg = self.params.storage_volume*3.785 / self.params.num_layers
        if self.middle_temp is not None:
            kWh_top = (self.thermocline1-0.5)*m_layer_kg * 4.187/3600 * to_kelvin(self.top_temp)
            kWh_midlle = (self.thermocline2-self.thermocline1)*m_layer_kg * 4.187/3600 * to_kelvin(self.middle_temp)
            kWh_bottom = (self.params.num_layers-self.thermocline2+0.5)*m_layer_kg * 4.187/3600 * to_kelvin(self.bottom_temp)
        else:        
            kWh_top = (self.thermocline1-0.5)*m_layer_kg * 4.187/3600 * to_kelvin(self.top_temp)
            kWh_midlle = 0
            kWh_bottom = (self.params.num_layers-self.thermocline1+0.5)*m_layer_kg * 4.187/3600 * to_kelvin(self.bottom_temp)
        return kWh_top + kWh_midlle + kWh_bottom


class DEdge():
    def __init__(self, tail:DNode, head:DNode, cost:float, hp_heat_out:float, rswt_minus_edge_elec:Optional[float]=None):
        self.tail: DNode = tail
        self.head: DNode = head
        self.cost = cost
        self.hp_heat_out = hp_heat_out
        self.rswt_minus_edge_elec = rswt_minus_edge_elec
        self.fake_cost: Optional[float] = None

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
            if self.params.max_thermocline < self.params.num_layers:
                self.nodes[time_slice].extend(
                    DNode(time_slice, top_temp, thermocline, self.params)
                    for top_temp in self.params.available_top_temps[1:-1]
                    for thermocline in range(1,self.params.num_layers+1)
                    if thermocline <= self.params.temperature_stack[self.params.available_top_temps.index(top_temp)][1]
                    and (time_slice, top_temp, thermocline) != (0, self.params.initial_top_temp, self.params.initial_thermocline)
                )
                self.nodes[time_slice].extend(
                    DNode(time_slice, self.params.available_top_temps[-1], thermocline, self.params)
                    for thermocline in range(1,self.params.max_thermocline+1)
                    if thermocline <= self.params.temperature_stack[-1][1]
                    and (time_slice, self.params.available_top_temps[-1], thermocline) != (0, self.params.initial_top_temp, self.params.initial_thermocline)
                )
            else:
                self.nodes[time_slice].extend(
                    DNode(time_slice, top_temp, thermocline, self.params)
                    for top_temp in self.params.available_top_temps[1:]
                    for thermocline in range(1,self.params.num_layers+1)
                    if thermocline <= self.params.temperature_stack[self.params.available_top_temps.index(top_temp)][1]
                    and (time_slice, top_temp, thermocline) != (0, self.params.initial_top_temp, self.params.initial_thermocline)
                )

    def create_edges(self):
        
        self.bottom_node = DNode(0, 
                                 self.params.available_top_temps[1],
                                 self.params.num_layers - self.params.temperature_stack[self.params.available_top_temps.index(self.params.available_top_temps[0])][1],
                                 self.params)
        self.top_node = DNode(0, 
                              self.params.available_top_temps[-1], 
                              self.params.temperature_stack[self.params.available_top_temps.index(self.params.available_top_temps[-1])][1], 
                              self.params)
        
        for h in range(self.params.horizon):
            
            for node_now in self.nodes[h]:
                self.edges[node_now] = []

                # The losses might be lower than energy between two nodes
                losses = self.params.storage_losses_percent/100 * (node_now.energy-self.bottom_node.energy)
                if self.params.load_forecast[h]==0 and losses>0 and losses<self.params.energy_between_nodes[node_now.top_temp]:
                    losses = self.params.energy_between_nodes[node_now.top_temp] + 1/1e9

                # If the current top temperature is the first one available above RSWT
                # If it exists, add an edge from the current node that drains the storage further than RSWT
                RSWT_plus = self.params.rswt_plus[self.params.rswt_forecast[h]]
                if node_now.top_temp == RSWT_plus and h < self.params.horizon-1:
                    self.add_rswt_minus_edge(node_now, h, losses)
                
                for node_next in self.nodes[h+1]:

                    store_heat_in = node_next.energy - node_now.energy
                    hp_heat_out = store_heat_in + self.params.load_forecast[h] + losses
                    
                    # Adjust the max elec the HP can use in the first time step
                    # (Duration of time step + turn-on effects)
                    max_hp_elec_in = self.params.max_hp_elec_in
                    if h==0:
                        max_hp_elec_in = max_hp_elec_in * self.params.fraction_of_hour_remaining
                        max_hp_elec_in = (((1-self.params.hp_turn_on_minutes/60) if self.params.hp_is_off else 1) * max_hp_elec_in)
                    
                    # This condition reduces the amount of times we need to compute the COP
                    if (hp_heat_out/self.params.max_cop <= max_hp_elec_in and
                        hp_heat_out/self.params.min_cop >= self.params.min_hp_elec_in):
                    
                        cop = self.params.COP(oat=self.params.oat_forecast[h], lwt=node_next.top_temp)

                        if (hp_heat_out/cop <= max_hp_elec_in and 
                            hp_heat_out/cop >= self.params.min_hp_elec_in):

                            cost = self.params.elec_price_forecast[h]/100 * hp_heat_out/cop

                            # If some of the load is satisfied by the storage
                            # Then it must satisfy the SWT requirement
                            if store_heat_in < 0:
                                if ((hp_heat_out < self.params.load_forecast[h] and 
                                     self.params.load_forecast[h] > 0)
                                     and
                                    (node_now.top_temp < self.params.rswt_forecast[h] or 
                                     node_next.top_temp < self.params.rswt_forecast[h])):
                                    if self.params.soft_constraint and not [x for x in self.edges[node_now] if x.head==node_next]:
                                        cost += 1e5
                                    else:
                                        continue
                            
                            self.edges[node_now].append(DEdge(node_now, node_next, cost, hp_heat_out))
                    
                if not self.edges[node_now]:
                    print(f"No edge from node {node_now}, adding edge with penalty")
                    cop = self.params.COP(oat=self.params.oat_forecast[h], lwt=node_next.top_temp)
                    hp_heat_out = max_hp_elec_in * cop
                    node_next = [n for n in self.nodes[h+1] if n.top_temp==node_now.top_temp and n.thermocline1==node_now.thermocline1][0]
                    self.edges[node_now].append(DEdge(node_now, node_next, 1e5, hp_heat_out))
                    print(DEdge(node_now, node_next, 1e5, hp_heat_out))

    def add_rswt_minus_edge(self, node: DNode, time_slice, Q_losses):
        # In these calculations the load is both the heating requirement and the losses
        Q_load = self.params.load_forecast[time_slice] + Q_losses
        # Find the heat stored in the water that is hotter than RSWT
        Q_plus = 0
        m_layer_kg = self.params.storage_volume*3.785 / self.params.num_layers
        RSWT_minus = node.top_temp
        if node.top_temp > self.params.rswt_forecast[time_slice]:
            m_plus = (node.thermocline1-0.5) * m_layer_kg
            Q_plus = m_plus * 4.187/3600 * self.params.delta_T(node.top_temp)*5/9
            if node.middle_temp is not None:
                RSWT_minus = node.middle_temp
                RSWT_minus_minus = node.bottom_temp
            else:
                RSWT_minus = node.bottom_temp
                RSWT_minus_minus = None
        # The hot part of the storage alone can not provide the load and the losses
        if Q_plus <= Q_load:
            RSWT = self.params.rswt_forecast[time_slice]
            RSWT_min_DT = RSWT - self.params.delta_T(RSWT)
            m_chc = Q_load / (4.187/3600 * (to_kelvin(RSWT)-to_kelvin(RSWT_min_DT)))
            m_minus_max = (1 - Q_plus/Q_load) * m_chc
            if m_minus_max > self.params.storage_volume*3.785:
                print("m_minus_max > total storage mass!")
                m_minus_max = self.params.storage_volume*3.785
            if node.middle_temp is not None and RSWT_minus != node.top_temp:
                m_minus = m_layer_kg * (node.thermocline2 - node.thermocline1)
                if m_minus > m_minus_max:
                    m_minus = m_minus_max
                m_minus_minus = m_minus_max - m_minus
                Q_minus_max = (
                    m_minus * 4.187/3600 * (self.params.delta_T(RSWT_minus)*5/9)
                    + m_minus_minus * 4.187/3600 * (self.params.delta_T(RSWT_minus_minus)*5/9)
                    )
            else:
                Q_minus_max = m_minus_max * 4.187/3600 * (self.params.delta_T(RSWT_minus)*5/9)
            Q_missing = Q_load - Q_plus - Q_minus_max
            if Q_missing < 0:
                print(f"Isn't this impossible? Q_load - Q_plus - Q_minus_max = {round(Q_missing,2)} kWh")
            Q_missing = 0 if Q_missing < 0 else Q_missing
            if Q_missing > 0 and not self.params.soft_constraint:
                return
            # Find the next node that would be the closest to matching the energy
            next_node_energy = node.energy - (Q_plus + Q_minus_max)
            next_nodes = [x for x in self.nodes[time_slice+1] if x.energy <= node.energy and x.energy >= next_node_energy]
            next_node = sorted(next_nodes, key=lambda x: x.energy)[0]
            # Penalty is slightly more expensive than the cost of producing Q_missing in the next hour
            cop = self.params.COP(oat=self.params.oat_forecast[time_slice+1], lwt=next_node.top_temp)
            penalty = (Q_missing+1)/cop * self.params.elec_price_forecast[time_slice+1]/100
            self.edges[node].append(DEdge(node, next_node, penalty, 0, rswt_minus_edge_elec=(Q_missing+1)/cop))

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
        self.pq_pairs: List[PriceQuantityUnitless] = []
        forecasted_price_usd_mwh = self.params.elec_price_forecast[0] * 10
        # For every possible price
        min_elec_ctskwh, max_elec_ctskwh = -10, 200
        for elec_price_usd_mwh in sorted(list(range(min_elec_ctskwh*10, max_elec_ctskwh*10))+[forecasted_price_usd_mwh]):
            # Update the fake cost of initial node edges with the selected price
            for edge in self.edges[self.initial_node]:
                if edge.cost >= 1e4: # penalized node
                    edge.fake_cost = edge.cost
                elif edge.rswt_minus_edge_elec is not None: # penalized node
                    edge.fake_cost = edge.rswt_minus_edge_elec * elec_price_usd_mwh/1000
                else:
                    cop = self.params.COP(oat=self.params.oat_forecast[0], lwt=edge.head.top_temp)
                    edge.fake_cost = edge.hp_heat_out / cop * elec_price_usd_mwh/1000
            # Find the best edge with the given price
            best_edge: DEdge = min(self.edges[self.initial_node], key=lambda e: e.head.pathcost + e.fake_cost)
            if best_edge.hp_heat_out < 0: 
                best_edge_neg = max([e for e in self.edges[self.initial_node] if e.hp_heat_out<0], key=lambda e: e.hp_heat_out)
                best_edge_pos = min([e for e in self.edges[self.initial_node] if e.hp_heat_out>=0], key=lambda e: e.hp_heat_out)
                best_edge = best_edge_pos if (-best_edge_neg.hp_heat_out >= best_edge_pos.hp_heat_out) else best_edge_neg
            # Find the associated quantity
            cop = self.params.COP(oat=self.params.oat_forecast[0], lwt=best_edge.head.top_temp)
            best_quantity_kwh = best_edge.hp_heat_out / cop
            best_quantity_kwh = 0 if best_quantity_kwh<0 else best_quantity_kwh
            if not self.pq_pairs:
                self.pq_pairs.append(
                    PriceQuantityUnitless(
                        PriceTimes1000 = int(elec_price_usd_mwh * 1000),
                        QuantityTimes1000 = int(best_quantity_kwh * 1000))
                )
            else:
                # Record a new pair if at least 0.01 kWh of difference in quantity with the previous one
                if self.pq_pairs[-1].QuantityTimes1000 - int(best_quantity_kwh * 1000) > 10:
                    self.pq_pairs.append(
                        PriceQuantityUnitless(
                            PriceTimes1000 = int(elec_price_usd_mwh * 1000),
                            QuantityTimes1000 = int(best_quantity_kwh * 1000))
                    )
        return self.pq_pairs