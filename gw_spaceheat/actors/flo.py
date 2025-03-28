import time
import json
import sys
import gc
import numpy as np
from typing import Dict, List, Tuple
from .dijkstra_types import DParams, DNode, DEdge
from named_types import FloParamsHouse0, PriceQuantityUnitless
from gwproactor.logger import LoggerOrAdapter

class DGraph():
    LOGGER_NAME="Flo"
    def __init__(self, 
                 flo_params: FloParamsHouse0,
                 logger: LoggerOrAdapter):
        self.logger = logger
        self.params = DParams(flo_params)
        start_time = time.time()
        self.load_super_graph()
        try:
            self.create_nodes()
        except Exception as e:
            self.logger.info(f"Error with create_nodes! {e}")
            raise e
        self.create_edges()
        self.logger.info(f"Created graph in {round(time.time()-start_time,1)} seconds")
        # Force garbage collection after heavy operations
        gc.collect()

    # def load_super_graph(self):
    #     with open("super_graph.json", 'r') as f:
    #         self.super_graph: Dict = json.load(f)
    #     print("Sucessfully loaded super graph from JSON file.")
    #     self.discretized_store_heat_in = [float(x) for x in list(self.super_graph.keys())]
    #     self.discretized_store_heat_in_array = np.array(self.discretized_store_heat_in)
        
    def load_super_graph(self):
        # Use a memory-efficient approach: load only keys first
        with open("super_graph.json", 'r') as f:
            # Read the first level of keys without loading entire structure
            first_char = f.read(1)
            f.seek(0)
            if first_char != '{':
                raise ValueError("Expected JSON object")

            # Read keys only first
            self.super_graph_keys = []
            depth = 0
            in_key = False
            current_key = ""

            while True:
                char = f.read(1)
                if not char:
                    break
                    
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                elif depth == 1 and char == '"' and not in_key:
                    in_key = True
                    current_key = ""
                elif depth == 1 and char == '"' and in_key:
                    in_key = False
                    self.super_graph_keys.append(current_key)
                elif in_key:
                    current_key += char

        # Now load the actual structure, with memory management
        self.super_graph = {}
        with open("super_graph.json", 'r') as f:
            data = json.load(f)
            self.super_graph = data

        self.logger.info("Sucessfully loaded super graph from JSON file.")
        self.discretized_store_heat_in = [float(x) for x in list(self.super_graph.keys())]
        self.discretized_store_heat_in_array = np.array(self.discretized_store_heat_in)

    def create_nodes(self):
        self.nodes: Dict[int, List[DNode]] = {h: [] for h in range(self.params.horizon+1)}
        self.nodes_by: Dict[int, Dict[Tuple, Dict[Tuple, DNode]]] = {h: {} for h in range(self.params.horizon+1)}

        current_state = DNode(
            top_temp=self.params.initial_top_temp,
            middle_temp=self.params.initial_bottom_temp,
            bottom_temp=self.params.initial_bottom_temp,
            thermocline1=self.params.initial_thermocline,
            thermocline2=self.params.initial_thermocline,
            parameters=self.params
        )

        super_graph_nodes: Dict[str, str] = self.super_graph['0.0']

        # Original approach: process all nodes at once
        # for node_no_time_slice in super_graph_nodes:
        #   Process node..

        # New approach: process in batches. Gives Python a chance
        # to release memory between batches
        batch_size = 100
        keys = list(super_graph_nodes.keys())
        total_keys = len(keys)

        gc.disable()  # Disable automatic garbage collection during processing

        try:
            for batch_start in range(0, total_keys, batch_size):
                # Track memory before batch processing
                mem_before = sys.getsizeof(self.nodes)
                batch_keys = keys[batch_start:batch_start + batch_size]
                for node_no_time_slice in batch_keys:
                    # process nodes
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

                        if self.params.initial_top_temp > 170 and node.energy>=current_state.energy:
                            continue

                        self.nodes[h].append(node)
                        if h==0 and (t,m,b) not in self.nodes_by[h]:
                            for hour in range(self.params.horizon+1):
                                self.nodes_by[hour][(t,m,b)] = {}
                        self.nodes_by[h][(t,m,b)][(th1,th2)] = node

                    # Clean up between batches
                    if batch_start % (batch_size * 5) == 0:
                        gc.collect()
                        mem_after = sys.getsizeof(self.nodes)
                        if mem_after > mem_before * 1.5:
                            self.logger.info(f"Memory usage increased from {mem_before} to {mem_after}")
        finally:
            gc.enable()
                
        self.logger.info(f"Built a graph with {self.params.horizon} layers of {len(self.nodes[0])} nodes each")
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

            # Process nodes in batches for this time slice
            batch_size = 50
            nodes_for_hour = self.nodes[h]

            for i in range(0, len(nodes_for_hour), batch_size):
                batch_nodes = nodes_for_hour[i:i+batch_size]

                for node_now in batch_nodes:
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

                # Force garbage collection between batches
                if i % (batch_size * 5) == 0:
                    gc.collect()

            self.logger.info(f"Built edges for hour {h}")
    
    def solve_dijkstra(self):
        """Memory-efficient implementation of Dijkstra's algorithm"""
        # Process one time slice at a time to reduce memory pressure
        for time_slice in range(self.params.horizon-1, -1, -1):
            # Process in batches
            batch_size = 100
            nodes_for_time = self.nodes[time_slice]

            for i in range(0, len(nodes_for_time), batch_size):
                batch_nodes = nodes_for_time[i:i+batch_size]

                for node in batch_nodes:
                    if node not in self.edges:
                        continue

                    best_edge = min(self.edges[node], key=lambda e: e.head.pathcost + e.cost)
                    node.pathcost = best_edge.head.pathcost + best_edge.cost
                    node.next_node = best_edge.head

                # Force garbage collection between batches
                if i % (batch_size * 5) == 0:
                    gc.collect()

            # Force garbage collection after each time slice
            gc.collect()

    def read_node_str(self, node_str: str):
        parts = node_str.replace(')', '(').split('(')
        top, thermocline1, middle, thermocline2, bottom = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
        return top, thermocline1, middle, thermocline2, bottom

    def find_initial_node(self, updated_flo_params: FloParamsHouse0=None):
        if updated_flo_params:
            self.params = DParams(updated_flo_params)
        
        self.initial_state = DNode(
            top_temp = self.params.initial_top_temp,
            middle_temp=self.params.initial_bottom_temp,
            bottom_temp=self.params.initial_bottom_temp,
            thermocline1=self.params.initial_thermocline,
            thermocline2=self.params.initial_thermocline,
            parameters=self.params
        )

        top_temps = set([n.top_temp for n in self.nodes[0]])
        closest_top_temp = min(top_temps, key=lambda x: abs(x-self.initial_state.top_temp))

        middle_temps = set([n.middle_temp for n in self.nodes[0] if n.top_temp==closest_top_temp])
        closest_middle_temp = min(middle_temps, key=lambda x: abs(x-self.initial_state.bottom_temp))

        thermoclines1 = set([n.thermocline1 for n in self.nodes[0] if n.top_temp==closest_top_temp and n.middle_temp==closest_middle_temp])
        closest_thermocline1 = min(thermoclines1, key=lambda x: abs(x-self.initial_state.thermocline1))

        nodes_with_initial_top_and_middle = [
            n for n in self.nodes[0]
            if n.top_temp == closest_top_temp
            and n.middle_temp == closest_middle_temp
            and n.thermocline1 == closest_thermocline1
        ]

        self.initial_node = min(
            nodes_with_initial_top_and_middle, 
            key=lambda x: abs(x.energy-self.initial_state.energy)
        )
        self.logger.info(f"Initial state: {self.initial_state}")
        self.logger.info(f"Initial node: {self.initial_node}")

        for e in self.edges[self.initial_node]:
            if self.initial_state.top_temp > 170 and e.head.energy > self.initial_node.energy:
                self.edges[self.initial_node].remove(e)
                self.logger.info(f"Removed edge {e} because the storage is already close to full.")

        # Force garbage collection
        gc.collect()

    def generate_bid(self, updated_flo_params: FloParamsHouse0=None):
        self.logger.info("\nGenerating bid...")
        self.pq_pairs: List[PriceQuantityUnitless] = []
        self.find_initial_node(updated_flo_params)
        
        forecasted_cop = self.params.COP(oat=self.params.oat_forecast[0])
        forecasted_price_usd_mwh = self.params.elec_price_forecast[0]*10

        price_range_usd_mwh = sorted(list(range(-100, 2000)) + [forecasted_price_usd_mwh])

        # Pre-allocate memory for edge costs
        edge_cost = {}

        # Process prices in batches
        batch_size = 200
        for i in range(0, len(price_range_usd_mwh), batch_size):
            batch_prices = price_range_usd_mwh[i:i+batch_size]
            for price_usd_mwh in batch_prices:
                for edge in self.edges[self.initial_node]:
                    edge_cost[edge] = edge.cost if edge.cost >= 1e4 else edge.hp_heat_out/forecasted_cop * price_usd_mwh/1000

                best_edge: DEdge = min(self.edges[self.initial_node], key=lambda e: e.head.pathcost + edge_cost[e])
                best_quantity_kwh = max(0, best_edge.hp_heat_out/forecasted_cop)

                # Only add if significantly different from previous point
                if not self.pq_pairs or (self.pq_pairs[-1].QuantityTimes1000-int(best_quantity_kwh*1000)>10):
                    self.pq_pairs.append(
                        PriceQuantityUnitless(
                            PriceTimes1000 = int(price_usd_mwh * 1000),
                            QuantityTimes1000 = int(best_quantity_kwh * 1000))
                    )

            # Force garbage collection between batches
            if i % batch_size == 0:
                gc.collect()

        self.logger.info(f"Done ({len(self.pq_pairs)} PQ pairs found).")

        # Clean up
        del edge_cost
        gc.collect()