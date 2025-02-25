from actors.flo import DGraph, DParams, DNode, DEdge, to_kelvin
from named_types import FloParamsHouse0, PriceQuantityUnitless
from typing import List, Union

PRINT = False


class HingeNode():
    def __init__(self, time_slice:int, params: DParams, top_temp:float, middle_temp:float, bottom_temp:float, 
                 thermocline1:float, thermocline2: float, pathcost: float=None):
        self.time_slice = time_slice
        self.top_temp = top_temp
        self.middle_temp = middle_temp
        self.bottom_temp = bottom_temp
        self.thermocline1 = thermocline1
        self.thermocline2 = thermocline2
        self.params = params
        self.pathcost = pathcost
        self.energy = self.get_energy()

    def __repr__(self):
        if self.thermocline2 is not None:
            return f"{self.top_temp}({self.thermocline1}){self.middle_temp}({self.thermocline2}){self.bottom_temp}"
        else:
            return f"{self.top_temp}({self.thermocline1}){self.bottom_temp}"

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


class FloHinge():

    def __init__(self, flo_params: FloParamsHouse0, hinge_hours: int, num_nodes: List[int]):
        self.flo_params = flo_params
        self.hinge_hours = hinge_hours
        self.num_nodes = num_nodes
        self.g = DGraph(flo_params)
        self.g.solve_dijkstra()
        flo_params.DdDeltaTF = flo_params.DischargingDdDeltaTF
        self.dg = DGraph(flo_params)
        self.num_layers = self.g.params.num_layers
        self.start()

    def start(self):
        self.initial_node = self.to_hingenode(self.dg.initial_node)
        self.hinge_steps: List[HingeNode] = [self.initial_node]
        print(f"Estimated storage at the start: {self.initial_node}")

        # Find the HP max thermal output for every hour in the hinge
        hp_max_kwh_th = [
            round(self.flo_params.HpMaxElecKw * self.g.params.COP(self.g.params.oat_forecast[x]),2)
            for x in range(self.hinge_hours)
            ]
        # Create a list of all available HP thermal outputs for every hour in the hinge
        step_size_kwh = [hp_max_kwh_th[x] / (self.num_nodes[x]-1) for x in range(self.hinge_hours)]
        available_paths_kwh = [[round(i * step_size_kwh[x],2) for i in range(self.num_nodes[x])] for x in range(self.hinge_hours)]   
        # Remove the non-zero element that is closest to the load and add the load
        for i in range(self.hinge_hours):
            if self.num_nodes[i] > 2:
                load = round(self.g.params.load_forecast[i],2)
                closest_to_load = min([x for x in available_paths_kwh[i] if x>0], key=lambda x: abs(x-load))
                available_paths_kwh[i].remove(closest_to_load)
                available_paths_kwh[i] = sorted(available_paths_kwh[i] + [load])
        self.available_paths_kwh = available_paths_kwh

        # Check the number of available possibilities
        num_combinations = 1
        for h in range(self.hinge_hours):
            num_combinations *= len(available_paths_kwh[h])
            print(f"Hour {h} options: {available_paths_kwh[h]} kWh_th")
        print(f"There are {num_combinations} possible combinations")

        # Explore all possibilities
        self.feasible_branches = {}
        from itertools import product
        for combination in product(*available_paths_kwh):
            self.create_branch(list(combination))
        self.knit_branches()

        if PRINT:
            for branch in self.feasible_branches:
                print(f"\nCombination: {branch}")
                print(f"- Ends at {self.feasible_branches[branch]['final_state']}")
                print(f"- Knitted to {self.feasible_branches[branch]['knitted_to']}")
                print(f"- Total pathcost: {self.feasible_branches[branch]['total_pathcost']}")

        # Best combination
        self.best_combination = min(self.feasible_branches, key=lambda k: self.feasible_branches[k]['total_pathcost'])
        print(f"\nThe best path forward is {self.best_combination}")
        self.hinge_steps = [self.initial_node]
        self.create_branch(self.best_combination, best_combination=True)
        self.hinge_steps.append(self.feasible_branches[self.best_combination]['knitted_to'])

    def create_branch(self, combination, best_combination=False):
        node = self.initial_node
        load = [round(x,2) for x in self.g.params.load_forecast]
        cop = [self.g.params.COP(self.g.params.oat_forecast[x]) for x in range(self.hinge_hours)]
        elec_price = [x/100 for x in self.g.params.elec_price_forecast]
        branch_cost = 0
        for h in range(self.hinge_hours):
            branch_cost += combination[h] / cop[h] * elec_price[h]
            heat_to_store = combination[h]-load[h]
            if heat_to_store > 0:
                node = self.charge(node, heat_to_store)
                if node.top_temp > 175:
                    return
            elif heat_to_store < 0:
                node_before = node
                node = self.discharge(node, -heat_to_store)
                rswt = self.g.params.rswt_forecast[h]
                if node_before.top_temp < rswt or node.top_temp < rswt - self.g.params.delta_T(rswt):
                    return
            else:
                node = self.to_hingenode(node, time_slice=node.time_slice+1)
            if best_combination:
                self.hinge_steps.append(node)
        if not best_combination:
            self.feasible_branches[tuple(combination)] = {
                'branch_cost': round(branch_cost,3), 
                'final_state': node
                }

    def discharge(self, n: HingeNode, discharge_kwh: float):
        next_node_energy = n.energy - discharge_kwh
        if n.top_temp - self.dg.params.delta_T(n.top_temp) < n.bottom_temp or n.middle_temp is not None:
            # Build a new discharging graph from current node and find the node that matches the next node energy
            flo_params_temporary: FloParamsHouse0 = self.dg.params.config.model_copy()
            flo_params_temporary.HorizonHours = 1
            flo_params_temporary.InitialTopTempF = n.top_temp if n.top_temp<=175 else 175
            flo_params_temporary.InitialBottomTempF = n.bottom_temp if n.middle_temp is None else n.middle_temp
            flo_params_temporary.InitialBottomTempF = flo_params_temporary.InitialBottomTempF if flo_params_temporary.InitialBottomTempF<=170 else 170
            flo_params_temporary.InitialThermocline = n.thermocline1 if n.thermocline2 is None else (self.dg.params.num_layers-n.thermocline2+n.thermocline1)
            temporary_g = DGraph(flo_params_temporary)
            node_after = min(temporary_g.nodes[0], key=lambda x: abs(x.energy-next_node_energy))
            return self.to_hingenode(node_after, time_slice=n.time_slice+1)
        else:
            # Starting with current top and bottom, find the thermocline position that matches the next node energy
            next_node_top_temp = n.top_temp
            next_node_bottom_temp = n.bottom_temp
            next_node_thermocline = self.find_thermocline(next_node_top_temp, next_node_bottom_temp, next_node_energy)
            while next_node_thermocline < 1:
                next_node_top_temp = next_node_bottom_temp
                next_node_bottom_temp = round(next_node_bottom_temp - self.g.params.delta_T(next_node_bottom_temp))
                next_node_thermocline = self.find_thermocline(next_node_top_temp, next_node_bottom_temp, next_node_energy)
            return HingeNode(
                time_slice = n.time_slice+1,
                top_temp = next_node_top_temp,
                middle_temp = None,
                bottom_temp = next_node_bottom_temp,
                thermocline1 = next_node_thermocline,
                thermocline2 = None,
                params = self.g.params
            )
    
    def charge(self, n: HingeNode, charge_kwh: float):
        next_node_energy = n.energy + charge_kwh
        if n.bottom_temp + self.g.params.delta_T(n.bottom_temp) < n.top_temp:
            # The next top temperature will be a mix of the current top and bottom+deltaT
            if n.middle_temp is not None:
                top_mixed = (n.top_temp*n.thermocline1 + n.middle_temp*(n.thermocline2-n.thermocline1))/n.thermocline2
                next_node_top_temp = round(
                    (top_mixed*n.thermocline2 
                     + (n.bottom_temp+self.g.params.delta_T(n.bottom_temp))*(self.num_layers-n.thermocline2))/self.num_layers
                    )
            else:
                next_node_top_temp = round(
                    (n.top_temp*n.thermocline1
                     + (n.bottom_temp+self.g.params.delta_T(n.bottom_temp))*(self.num_layers-n.thermocline1))/self.num_layers
                    )
        else:
            next_node_top_temp = n.top_temp
        # Starting with that top and current bottom, find the thermocline position that matches the next node energy
        next_node_bottom_temp = n.bottom_temp
        next_node_thermocline = self.find_thermocline(next_node_top_temp, next_node_bottom_temp, next_node_energy)
        while next_node_thermocline > self.num_layers:
            next_node_bottom_temp = next_node_top_temp
            next_node_top_temp = round(next_node_top_temp + self.g.params.delta_T(next_node_top_temp))
            next_node_thermocline = self.find_thermocline(next_node_top_temp, next_node_bottom_temp, next_node_energy)
        return HingeNode(
            time_slice = n.time_slice+1,
            top_temp = next_node_top_temp,
            middle_temp = None,
            bottom_temp = next_node_bottom_temp,
            thermocline1 = next_node_thermocline,
            thermocline2 = None,
            params = self.g.params
        )
        
    def find_thermocline(self, top_temp, bottom_temp, energy):
        top, bottom = to_kelvin(top_temp), to_kelvin(bottom_temp)
        m_layer_kg = self.g.params.storage_volume*3.785 / self.g.params.num_layers      
        return int(1/(top-bottom)*(energy/(m_layer_kg*4.187/3600)-(-0.5*top+(self.num_layers+0.5)*bottom)))

    def knit_branches(self):
        for branch in self.feasible_branches:
            n: HingeNode = self.feasible_branches[branch]['final_state']
            knitted_node = [min(self.g.nodes[n.time_slice], key= lambda x: abs(x.energy-n.energy))][0]            
            self.feasible_branches[branch]['knitted_to'] = knitted_node
            self.feasible_branches[branch]['total_pathcost'] = round(knitted_node.pathcost + self.feasible_branches[branch]['branch_cost'],2)

    def generate_bid(self):
        # Add new nodes and edges
        hinge_hour0_edges: List[DEdge] = []
        for hour0_kwh in self.available_paths_kwh[0]:
            load0_kwh = self.g.params.load_forecast[0]
            heat_to_store = hour0_kwh-load0_kwh
            if heat_to_store > 0:
                node = self.charge(self.initial_node, heat_to_store)
                if node.top_temp > 175:
                    continue
            elif heat_to_store < 0:
                node = self.discharge(self.initial_node, -heat_to_store)
                rswt = self.g.params.rswt_forecast[0]
                if self.initial_node.top_temp < rswt or node.top_temp < rswt - self.g.params.delta_T(rswt):
                    continue
            else:
                node = self.to_hingenode(node, time_slice=node.time_slice+1)
            hour0_cost = hour0_kwh / self.g.params.COP(self.g.params.oat_forecast[0]) * self.g.params.elec_price_forecast[0]/100
            if [x for x in self.feasible_branches if x[0]==hour0_kwh]:
                best_branch_from_hour1 = min(
                    [x for x in self.feasible_branches if x[0]==hour0_kwh],
                    key=lambda k: self.feasible_branches[k]['total_pathcost']
                    )
                pathcost = self.feasible_branches[best_branch_from_hour1]['total_pathcost'] - hour0_cost
                node.pathcost = pathcost
                hinge_hour0_edges.append(DEdge(self.g.initial_node, node, hour0_cost, hour0_kwh))
        # Find the PQ pairs
        self.pq_pairs: List[PriceQuantityUnitless] = []
        forecasted_price_usd_mwh = self.g.params.elec_price_forecast[0] * 10
        # For every possible price
        min_elec_ctskwh, max_elec_ctskwh = -10, 200
        for elec_price_usd_mwh in sorted(list(range(min_elec_ctskwh*10, max_elec_ctskwh*10))+[forecasted_price_usd_mwh]):
            # Update the fake cost of initial node edges with the selected price
            for edge in hinge_hour0_edges:
                if edge.cost >= 1e4: # penalized node
                    edge.fake_cost = edge.cost
                elif edge.rswt_minus_edge_elec is not None: # penalized node
                    edge.fake_cost = edge.rswt_minus_edge_elec * elec_price_usd_mwh/1000
                else:
                    cop = self.g.params.COP(oat=self.g.params.oat_forecast[0], lwt=edge.head.top_temp)
                    edge.fake_cost = edge.hp_heat_out / cop * elec_price_usd_mwh/1000
            # Find the best edge with the given price
            best_edge: DEdge = min(hinge_hour0_edges, key=lambda e: e.head.pathcost + e.fake_cost)
            if best_edge.hp_heat_out < 0: 
                best_edge_neg = max([e for e in hinge_hour0_edges if e.hp_heat_out<0], key=lambda e: e.hp_heat_out)
                best_edge_pos = min([e for e in hinge_hour0_edges if e.hp_heat_out>=0], key=lambda e: e.hp_heat_out)
                best_edge = best_edge_pos if (-best_edge_neg.hp_heat_out >= best_edge_pos.hp_heat_out) else best_edge_neg
            # Find the associated quantity
            cop = self.g.params.COP(oat=self.g.params.oat_forecast[0], lwt=best_edge.head.top_temp)
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
    
    def to_hingenode(self, node: Union[DNode, HingeNode], time_slice=None):
        return HingeNode(
            time_slice = node.time_slice if time_slice is None else time_slice,
            top_temp = node.top_temp,
            middle_temp = node.middle_temp,
            bottom_temp = node.bottom_temp,
            thermocline1 = node.thermocline1,
            thermocline2 = node.thermocline2,
            params = node.params
        )