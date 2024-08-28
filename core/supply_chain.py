import numpy as np
from scipy import interpolate
import math
import random

time = 0


class Edge:
    def __init__(self, unit_price, min_cost, max_cost):
        self.unit_price = unit_price
        self.in_transit = [0, 0, 0]  # 3 cycles of transit
        self.quantity = 0  # Current cycle's quantity
        self.min_cost = min_cost
        self.max_cost = max_cost
        self.current_cost = 0

    def update(self, new_quantity):
        delivered = self.in_transit.pop(0)
        self.in_transit.append(new_quantity)
        self.quantity = delivered
        return delivered

    def initialize(self, initial_quantity):
        self.in_transit = [initial_quantity] * 3
        self.quantity = initial_quantity

    def calculate_cost(self, source_node):
        if source_node.cost_type == "fixed":
            self.current_cost = (self.min_cost + self.max_cost) / 2
        elif source_node.cost_type == "positive_dynamic":
            cost_range = self.max_cost - self.min_cost
            inventory_ratio = source_node.inventory / source_node.max_inventory
            self.current_cost = self.min_cost + (cost_range * inventory_ratio)
        elif source_node.cost_type == "negative_dynamic":
            cost_range = self.max_cost - self.min_cost
            inventory_ratio = 1 - (source_node.inventory / source_node.max_inventory)
            self.current_cost = self.min_cost + (cost_range * inventory_ratio)
        return self.current_cost * self.quantity


class Node:
    def __init__(self, max_inventory, node_class, cost_type):
        self.max_inventory = max_inventory
        self.inventory = 0
        self.node_class = node_class
        self.incoming_edges = []
        self.outgoing_edges = []
        self.last_production = 0
        self.cost_type = cost_type

    def add_incoming_edge(self, edge, source_node):
        self.incoming_edges.append((edge, source_node))

    def add_outgoing_edge(self, edge, target_node):
        self.outgoing_edges.append((edge, target_node))

    def update(self):
        self.receive()
        self.produce()
        self.distribute()

    def receive(self):
        for edge, _ in self.incoming_edges:
            self.inventory = min(self.max_inventory, self.inventory + edge.update(0))

    def produce(self):
        production = min(
            self.calculate_production(), self.max_inventory - self.inventory
        )
        self.inventory = min(self.max_inventory, self.inventory + production)
        self.last_production = production

    def distribute(self):
        if not self.outgoing_edges:
            return
        total_demand = sum(edge.quantity for edge, _ in self.outgoing_edges)
        if total_demand == 0:
            total_demand = len(self.outgoing_edges)  # Distribute evenly if no demand
        available = max(
            self.inventory, self.last_production
        )  # Always distribute something
        ratio = available / total_demand
        for edge, target_node in self.outgoing_edges:
            amount = max(1, int(edge.quantity * ratio))  # Always send at least 1
            self.inventory = max(0, self.inventory - amount)
            edge.update(amount)
            edge.calculate_cost(self)

    def calculate_production(self):
        raise NotImplementedError(
            "Subclasses must implement calculate_production method"
        )


class LeafNode(Node):
    def __init__(self, max_inventory, node_class, spline_points, cost_type):
        super().__init__(max_inventory, node_class, cost_type)
        x, y = zip(*spline_points)
        self.spline = interpolate.interp1d(
            x, y, kind="linear", fill_value="extrapolate"
        )

    def calculate_production(self):
        return max(0, int(self.spline(time)))


class CombinerNode(Node):
    def __init__(self, max_inventory, node_class, a_coeffs, b_powers, cost_type):
        super().__init__(max_inventory, node_class, cost_type)
        self.a_coeffs = a_coeffs
        self.b_powers = b_powers

    def calculate_production(self):
        production = 0
        for (edge, _), a, b in zip(self.incoming_edges, self.a_coeffs, self.b_powers):
            production += a * (max(1, edge.quantity) ** b)  # Always use at least 1
        return max(1, int(production))  # Always produce at least 1


class SinkNode(Node):
    def __init__(self, consumption_rate, cost_type):
        super().__init__(math.inf, "sink", cost_type)
        self.consumption_rate = consumption_rate
        self.total_consumed = 0

    def update(self):
        self.receive()
        self.consume()

    def consume(self):
        consumed = min(self.inventory, self.consumption_rate)
        self.inventory -= consumed
        self.total_consumed += consumed
        self.last_production = consumed  # For consistency in reporting

    def calculate_production(self):
        return 0  # Sink nodes don't produce


class SupplyChain:
    def __init__(self):
        self.nodes = []
        self.edges = []

    def add_node(self, node):
        self.nodes.append(node)

    def add_edge(
        self, source, target, unit_price, initial_quantity, min_cost, max_cost
    ):
        edge = Edge(unit_price, min_cost, max_cost)
        edge.initialize(initial_quantity)
        self.edges.append(edge)
        source.add_outgoing_edge(edge, target)
        target.add_incoming_edge(edge, source)

    def update(self):
        for node in self.nodes:
            node.update()
