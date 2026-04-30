"""Small command-line entry point for the simulation classes."""

from asynchronous_simulator import AsynchronousSimulator
from network import Network
from synchronous_simulator import SynchronousSimulator


def build_demo(agent_count=8, edge_probability=0.28, seed=7):
    """Build one graph, run both simulators, and return web-friendly data."""
    sync_network = Network(agent_count, edge_probability, seed)
    sync_network.build_network()

    sync = SynchronousSimulator(sync_network)
    sync.run()

    async_network = Network(agent_count, edge_probability, seed)
    async_network.build_network()

    async_simulator = AsynchronousSimulator(async_network, seed)
    async_simulator.run()

    sync_result = sync.to_visual_result()
    async_result = async_simulator.to_visual_result()
    graph = sync_network.to_visual_graph()

    return {
        "graph": graph,
        "sync": sync_result,
        "async": async_result,
        "comparison": {
            "sameFinalKnowledge": (
                sync_result["metrics"]["knownRows"] == async_result["metrics"]["knownRows"]
            ),
            "agentCount": agent_count,
            "edgeCount": len(graph["edges"]),
        },
    }


def main():
    network = Network(8, 0.28, seed=7)
    network.build_network()
    network.print_network()

    print("\nSynchronous simulation")
    sync = SynchronousSimulator(network)
    sync.run()
    print(f"Rounds: {sync.get_iteration_count()}")
    print(f"Messages: {sync.get_message_count()}")
    sync.print_agent_tables()

    async_network = Network(8, 0.28, seed=7)
    async_network.build_network()
    print("\nAsynchronous simulation")
    async_simulator = AsynchronousSimulator(async_network, seed=7)
    async_simulator.run()
    print(f"Deliveries: {async_simulator.get_processed_message_count()}")
    print(f"Messages: {async_simulator.get_message_count()}")
    print(f"Max Lamport clock: {async_simulator.get_max_lamport_timestamp()}")
    async_simulator.print_agent_tables()


if __name__ == "__main__":
    main()
