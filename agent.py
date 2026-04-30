"""Agent model used by both simulators."""


class Agent:
    """One network node with neighbors, an update table, and a Lamport clock."""

    def __init__(self, agent_id):
        self._agent_id = agent_id
        self._neighbors = []
        self._table = {}
        self.lamport_clock = 0
        self.initialize_table()

    def get_id(self):
        return self._agent_id

    def add_neighbor(self, agent):
        if agent is self or self.has_neighbor(agent):
            return
        self._neighbors.append(agent)
        self._neighbors.sort(key=lambda item: item.get_id())

    def has_neighbor(self, agent):
        return any(neighbor.get_id() == agent.get_id() for neighbor in self._neighbors)

    def get_neighbors(self):
        return list(self._neighbors)

    def initialize_table(self):
        self._table = {self._agent_id: (0, self._agent_id)}

    def get_table(self):
        return dict(self._table)

    def create_shared_table_view(self):
        return {target: distance for target, (distance, _via) in self._table.items()}

    def compute_message_effect(self, sender_id, received_table, base_table=None):
        """Return table improvements caused by one received distance table."""
        if base_table is None:
            base_table = self.get_table()

        updates = {}
        for target_id, received_distance in received_table.items():
            new_distance = received_distance + 1
            current = updates.get(target_id, base_table.get(target_id))
            if current is None or new_distance < current[0]:
                updates[target_id] = (new_distance, sender_id)
        return updates

    def apply_updates(self, updates):
        changed = False
        for target_id, row in updates.items():
            current = self._table.get(target_id)
            if current is None or row[0] < current[0]:
                self._table[target_id] = row
                changed = True
        return changed

    def update_algorithm(self, sender_id, received_table):
        updates = self.compute_message_effect(sender_id, received_table)
        return self.apply_updates(updates)

    def reset_lamport_clock(self):
        self.lamport_clock = 0

    def increment_lamport_clock(self):
        self.lamport_clock += 1
        return self.lamport_clock

    def update_lamport_clock_on_receive(self, message_lamport_time):
        self.lamport_clock = max(self.lamport_clock, message_lamport_time) + 1
        return self.lamport_clock

    def table_rows(self):
        return [
            {"target": target, "distance": distance, "via": via}
            for target, (distance, via) in sorted(self._table.items())
        ]

    def table_as_string(self):
        lines = [f"Agent {self._agent_id} table:", "  target | distance | via"]
        for row in self.table_rows():
            lines.append(f"  {row['target']:>6} | {row['distance']:>8} | {row['via']}")
        return "\n".join(lines)

    def __str__(self):
        neighbor_ids = [neighbor.get_id() for neighbor in self._neighbors]
        return f"Agent {self._agent_id} -> {neighbor_ids}"
