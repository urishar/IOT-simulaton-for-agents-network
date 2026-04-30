"""Asynchronous simulator with Lamport clocks."""

import heapq
import random
from dataclasses import dataclass, field


@dataclass
class Message:
    sender_id: int
    receiver_id: int
    table: dict
    lamport_time: int


@dataclass(order=True)
class ScheduledMessage:
    delivery_time: float
    order: int
    message: Message = field(compare=False)


class AsynchronousSimulator:
    """Runs message delivery in random order and records Lamport behavior."""

    def __init__(self, network, seed=1):
        self._network = network
        self._rng = random.Random(seed + 1000)
        self._message_count = 0
        self._processed_message_count = 0
        self._activation_count = 0
        self._max_lamport_timestamp = 0
        self._events = []
        self._queue = []
        self._order = 0

    def run(self, max_events=600):
        self._message_count = 0
        self._processed_message_count = 0
        self._activation_count = 0
        self._max_lamport_timestamp = 0
        self._events = []
        self._queue = []
        self._order = 0

        for agent in self._network.get_agents():
            agent.reset_lamport_clock()

        self._send_initial_messages()

        while self._queue and self._processed_message_count < max_events:
            scheduled = heapq.heappop(self._queue)
            self._deliver_message(scheduled)

    def _send_initial_messages(self):
        for agent in self._network.get_agents():
            self._send_table_to_neighbors(agent, now=0)

    def _send_table_to_neighbors(self, sender, now):
        shared_table = sender.create_shared_table_view()
        for neighbor in sender.get_neighbors():
            self._schedule_message(sender, neighbor, shared_table, now)

    def _schedule_message(self, sender, receiver, shared_table, now):
        lamport_time = sender.increment_lamport_clock()
        self._max_lamport_timestamp = max(self._max_lamport_timestamp, lamport_time)
        delay = self._rng.uniform(0.35, 1.8)

        self._order += 1
        self._message_count += 1
        heapq.heappush(
            self._queue,
            ScheduledMessage(
                round(now + delay, 3),
                self._order,
                Message(sender.get_id(), receiver.get_id(), dict(shared_table), lamport_time),
            ),
        )

    def _deliver_message(self, scheduled):
        message = scheduled.message
        sender = self._network.get_agent_by_id(message.sender_id)
        receiver = self._network.get_agent_by_id(message.receiver_id)

        self._processed_message_count += 1
        self._activation_count += 1

        before = receiver.lamport_clock
        after = receiver.update_lamport_clock_on_receive(message.lamport_time)
        self._max_lamport_timestamp = max(self._max_lamport_timestamp, after)

        updates = receiver.compute_message_effect(message.sender_id, message.table)
        changed = receiver.apply_updates(updates)
        if changed:
            self._send_table_to_neighbors(receiver, scheduled.delivery_time)

        self._events.append(
            {
                "mode": "async",
                "time": scheduled.delivery_time,
                "sender": sender.get_id(),
                "receiver": receiver.get_id(),
                "sentLamport": message.lamport_time,
                "receiverBefore": before,
                "receiverAfter": after,
                "lamport": self._lamport_snapshot(),
                "changed": self._updates_to_rows(updates),
                "label": (
                    f"t={scheduled.delivery_time:.2f}: A{receiver.get_id()} receives from "
                    f"A{sender.get_id()}, LC {before}->{after}"
                ),
                "tables": self.snapshot_tables(),
            }
        )

    def snapshot_tables(self):
        return {str(agent.get_id()): agent.table_rows() for agent in self._network.get_agents()}

    def _lamport_snapshot(self):
        return {agent.get_id(): agent.lamport_clock for agent in self._network.get_agents()}

    def _updates_to_rows(self, updates):
        return [
            {"target": target, "distance": distance, "via": via}
            for target, (distance, via) in sorted(updates.items())
        ]

    def to_visual_result(self):
        return {
            "events": self._events,
            "tables": self.snapshot_tables(),
            "lamport": self._lamport_snapshot(),
            "metrics": {
                "deliveries": self._processed_message_count,
                "messages": self._message_count,
                "maxLamport": self._max_lamport_timestamp,
                "knownRows": sum(len(agent.get_table()) for agent in self._network.get_agents()),
            },
        }

    def print_agent_tables(self):
        print("\nFinal update tables:")
        for agent in self._network.get_agents():
            print(agent.table_as_string())
            print()

    def get_message_count(self):
        return self._message_count

    def get_processed_message_count(self):
        return self._processed_message_count

    def get_activation_count(self):
        return self._activation_count

    def get_max_lamport_timestamp(self):
        return self._max_lamport_timestamp
