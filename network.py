"""Random undirected network of agents."""

import math
import random

from agent import Agent


class Network:
    """Creates agents and connects them in a random connected graph."""

    def __init__(self, number_of_agents, edge_probability, seed=None):
        self._number_of_agents = number_of_agents
        self._edge_probability = edge_probability
        self._rng = random.Random(seed)
        self._agents = {agent_id: Agent(agent_id) for agent_id in range(number_of_agents)}

    def build_network(self):
        """Build a connected graph with extra random edges."""
        for agent_id in range(self._number_of_agents - 1):
            self._connect(agent_id, agent_id + 1)

        for first_id in range(self._number_of_agents):
            for second_id in range(first_id + 2, self._number_of_agents):
                if self._rng.random() < self._edge_probability:
                    self._connect(first_id, second_id)

    def _connect(self, first_id, second_id):
        first = self._agents[first_id]
        second = self._agents[second_id]
        first.add_neighbor(second)
        second.add_neighbor(first)

    def get_agents(self):
        return [self._agents[agent_id] for agent_id in sorted(self._agents)]

    def get_all_agents(self):
        return self.get_agents()

    def get_agent_by_id(self, agent_id):
        return self._agents.get(agent_id)

    def initialize_agent_tables(self):
        for agent in self.get_agents():
            agent.initialize_table()
            agent.reset_lamport_clock()

    def get_edges(self):
        edges = []
        for agent in self.get_agents():
            source = agent.get_id()
            for neighbor in agent.get_neighbors():
                target = neighbor.get_id()
                if source < target:
                    edges.append({"source": source, "target": target})
        return edges

    def get_neighbors_by_id(self):
        return {
            agent.get_id(): [neighbor.get_id() for neighbor in agent.get_neighbors()]
            for agent in self.get_agents()
        }

    def to_visual_graph(self):
        center_x, center_y = 420, 260
        radius = 170
        nodes = []

        for agent in self.get_agents():
            agent_id = agent.get_id()
            angle = (2 * math.pi * agent_id / self._number_of_agents) - math.pi / 2
            nodes.append(
                {
                    "id": agent_id,
                    "x": round(center_x + radius * math.cos(angle), 2),
                    "y": round(center_y + radius * math.sin(angle), 2),
                }
            )

        return {"nodes": nodes, "edges": self.get_edges()}

    def print_network(self):
        print("\nGenerated network:")
        for agent in self.get_agents():
            print(agent)
