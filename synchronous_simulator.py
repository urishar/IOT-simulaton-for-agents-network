"""Synchronous simulator for the distance-table update algorithm."""


class SynchronousSimulator:
    """Runs all sends first, then commits all table updates per round."""

    def __init__(self, network):
        self._network = network
        self._iteration_count = 0
        self._message_count = 0
        self._events = []

    def run(self, max_rounds=30):
        self._iteration_count = 0
        self._message_count = 0
        self._events = []

        for round_number in range(1, max_rounds + 1):
            messages = self._collect_round_messages()
            round_changed, round_changes = self._deliver_round_messages(messages, round_number)
            self._iteration_count = round_number

            self._events.append(
                {
                    "mode": "sync",
                    "round": round_number,
                    "sender": None,
                    "receiver": None,
                    "changed": [],
                    "label": f"round {round_number} committed: {round_changes} improvements",
                    "tables": self.snapshot_tables(),
                }
            )

            if not round_changed:
                break

    def _collect_round_messages(self):
        messages = []
        for sender in self._network.get_agents():
            shared_table = sender.create_shared_table_view()
            for neighbor in sender.get_neighbors():
                messages.append(
                    {
                        "sender_id": sender.get_id(),
                        "receiver_id": neighbor.get_id(),
                        "table": dict(shared_table),
                    }
                )
        return messages

    def _deliver_round_messages(self, messages, round_number):
        agents = self._network.get_agents()
        snapshots = {agent.get_id(): agent.get_table() for agent in agents}
        pending_updates = {agent.get_id(): {} for agent in agents}
        round_changes = 0

        for message in messages:
            self._message_count += 1
            receiver_id = message["receiver_id"]
            receiver = self._network.get_agent_by_id(receiver_id)
            combined_base = dict(snapshots[receiver_id])
            combined_base.update(pending_updates[receiver_id])
            updates = receiver.compute_message_effect(
                message["sender_id"],
                message["table"],
                base_table=combined_base,
            )
            pending_updates[receiver_id].update(updates)
            changed_rows = self._updates_to_rows(updates)
            round_changes += len(changed_rows)

            self._events.append(
                {
                    "mode": "sync",
                    "round": round_number,
                    "sender": message["sender_id"],
                    "receiver": receiver_id,
                    "changed": changed_rows,
                    "label": f"round {round_number}",
                }
            )

        round_changed = False
        for agent in agents:
            if agent.apply_updates(pending_updates[agent.get_id()]):
                round_changed = True

        return round_changed, round_changes

    def snapshot_tables(self):
        return {str(agent.get_id()): agent.table_rows() for agent in self._network.get_agents()}

    def _updates_to_rows(self, updates):
        return [
            {"target": target, "distance": distance, "via": via}
            for target, (distance, via) in sorted(updates.items())
        ]

    def to_visual_result(self):
        return {
            "events": self._events,
            "tables": self.snapshot_tables(),
            "metrics": {
                "rounds": self._iteration_count,
                "messages": self._message_count,
                "knownRows": sum(len(agent.get_table()) for agent in self._network.get_agents()),
            },
        }

    def print_agent_tables(self):
        print("\nFinal update tables:")
        for agent in self._network.get_agents():
            print(agent.table_as_string())
            print()

    def get_iteration_count(self):
        return self._iteration_count

    def get_message_count(self):
        return self._message_count
