import time
import json
import numpy as np
from typing import Dict, List, Tuple
from dijkstra_types import DParams, DNode, DEdge
from named_types import FloParamsHouse0, PriceQuantityUnitless

class DGraph():
    def __init__(self, flo_params: FloParamsHouse0):
        self.params = DParams(flo_params)
        start_time = time.time()
        self.load_super_graph()
        self.create_nodes()
        self.create_edges()
        print(f"Created graph in {round(time.time()-start_time,1)} seconds")
        
    def load_super_graph(self):
        with open("super_graph.json", 'r') as f:
            self.super_graph: Dict = json.load(f)
        print("Sucessfully loaded super graph from JSON file.")
        self.discretized_store_heat_in = [float(x) for x in list(self.super_graph.keys())]
        self.discretized_store_heat_in_array = np.array(self.discretized_store_heat_in)

    def create_nodes(self):
        self.nodes: Dict[int, List[DNode]] = {h: [] for h in range(self.params.horizon+1)}
        self.nodes_by: Dict[int, Dict[Tuple, Dict[Tuple, DNode]]] = {h: {} for h in range(self.params.horizon+1)}

        self.initial_state = DNode(
            top_temp=self.params.initial_top_temp,
            middle_temp=self.params.initial_bottom_temp,
            bottom_temp=self.params.initial_bottom_temp,
            thermocline1=self.params.initial_thermocline,
            thermocline2=self.params.initial_thermocline,
            parameters=self.params
        )

        super_graph_nodes: List[str] = self.super_graph['0.0']

        for node_no_time_slice in super_graph_nodes:
            t, th1, m, th2, b = self.read_node_str(node_no_time_slice)

            for h in range(self.params.horizon+1):
                node = DNode(
                    time_slice=h,
                    top_temp=t,
                    middle_temp=m,
                    bottom_temp=b,
                    thermocline1=th1,
                    thermocline2=th2,
                    parameters=self.params
                )

                if self.params.initial_top_temp > 170 and node.energy>=self.initial_state.energy:
                    continue

                self.nodes[h].append(node)
                if h==0 and (t,m,b) not in self.nodes_by[h]:
                    for hour in range(self.params.horizon+1):
                        self.nodes_by[hour][(t,m,b)] = {}
                self.nodes_by[h][(t,m,b)][(th1,th2)] = node
                
        print(f"Built a graph with {self.params.horizon} layers of {len(self.nodes[0])} nodes each")
        self.min_node_energy = min(self.nodes[0], key=lambda n: n.energy).energy
        self.max_node_energy = max(self.nodes[0], key=lambda n: n.energy).energy

    def create_edges(self):
        self.edges: Dict[DNode, List[DEdge]] = {}

        for h in range(self.params.horizon):

            load = self.params.load_forecast[h]
            rswt = self.params.rswt_forecast[h]
            cop = self.params.COP(oat=self.params.oat_forecast[h])

            turn_on_minutes = self.params.hp_turn_on_minutes if h==0 else self.params.hp_turn_on_minutes/2
            max_hp_elec_in = ((1-turn_on_minutes/60) if (h==0 and self.params.hp_is_off) else 1) * self.params.max_hp_elec_in
            max_hp_heat_out = max_hp_elec_in * cop
            
            for node_now in self.nodes[h]:
                self.edges[node_now] = []

                losses = self.params.storage_losses_percent/100 * (node_now.energy-self.min_node_energy)
                
                # Can not put out more heat than what would fill the storage
                store_heat_in_for_full = self.max_node_energy - node_now.energy
                hp_heat_out_for_full = store_heat_in_for_full + load + losses
                if hp_heat_out_for_full < max_hp_heat_out:
                    hp_heat_out_levels = [0, hp_heat_out_for_full] if hp_heat_out_for_full > 10 else [0]
                else:
                    hp_heat_out_levels = [0, max_hp_heat_out]
                
                for hp_heat_out in hp_heat_out_levels:
                    store_heat_in = hp_heat_out - load - losses
                    closest_store_heat_in = self.discretized_store_heat_in[abs(self.discretized_store_heat_in_array-store_heat_in).argmin()]
                    
                    node_next_str: str = self.super_graph[str(closest_store_heat_in)][node_now.to_string()]
                    t, th1, m, th2, b = self.read_node_str(node_next_str)
                    node_next = self.nodes_by[node_now.time_slice+1][(t,m,b)][(th1,th2)]

                    cost = self.params.elec_price_forecast[h]/100 * hp_heat_out/cop
                    if store_heat_in<0 and load>0 and (node_now.top_temp<rswt or node_next.top_temp<rswt):
                        cost += 1e5

                    self.edges[node_now].append(DEdge(node_now, node_next, cost, hp_heat_out))

            print(f"Built edges for hour {h}")
    
    def solve_dijkstra(self):
        for time_slice in range(self.params.horizon-1, -1, -1):
            for node in self.nodes[time_slice]:
                best_edge = min(self.edges[node], key=lambda e: e.head.pathcost + e.cost)
                node.pathcost = best_edge.head.pathcost + best_edge.cost
                node.next_node = best_edge.head

    def read_node_str(self, node_str: str):
        parts = node_str.replace(')', '(').split('(')
        top, thermocline1, middle, thermocline2, bottom = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
        return top, thermocline1, middle, thermocline2, bottom

    def find_initial_node(self):
        top_temps = set([n.top_temp for n in self.nodes[0]])
        initial_top_temp = min(top_temps, key=lambda x: abs(x-self.params.initial_top_temp))

        middle_temps = set([n.middle_temp for n in self.nodes[0] if n.top_temp==initial_top_temp])
        initial_middle_temp = min(middle_temps, key=lambda x: abs(x-self.params.initial_bottom_temp))

        nodes_with_initial_top_and_middle = [
            n for n in self.nodes[0]
            if n.top_temp == initial_top_temp
            and n.middle_temp == initial_middle_temp
        ]

        self.initial_node = min(
            nodes_with_initial_top_and_middle, 
            key=lambda x: abs(x.energy-self.initial_state.energy)
        )
        print(f"Initial state: {self.initial_state}")
        print(f"Initial node: {self.initial_node}")

    def generate_bid(self):
        print("\nGenerating bid...")
        self.pq_pairs: List[PriceQuantityUnitless] = []
        self.find_initial_node()
        
        forecasted_cop = self.params.COP(oat=self.params.oat_forecast[0])
        forecasted_price_usd_mwh = self.params.elec_price_forecast[0]*10
        price_range_usd_mwh = sorted(list(range(-100, 2000)) + [forecasted_price_usd_mwh])
        edge_cost = {}

        for price_usd_mwh in price_range_usd_mwh:
            for edge in self.edges[self.initial_node]:
                edge_cost[edge] = edge.cost if edge.cost >= 1e4 else edge.hp_heat_out/forecasted_cop * price_usd_mwh/1000
            best_edge: DEdge = min(self.edges[self.initial_node], key=lambda e: e.head.pathcost + edge_cost[e])
            best_quantity_kwh = max(0, best_edge.hp_heat_out/forecasted_cop)
            if not self.pq_pairs or (self.pq_pairs[-1].QuantityTimes1000-int(best_quantity_kwh*1000)>10):
                self.pq_pairs.append(
                    PriceQuantityUnitless(
                        PriceTimes1000 = int(price_usd_mwh * 1000),
                        QuantityTimes1000 = int(best_quantity_kwh * 1000))
                )
        print(f"Done ({len(self.pq_pairs)} PQ pairs found).")