import pandas as pd


def simulate_and_collect_data(supply_chain, n_cycles):
    # Initialize DataFrames
    metadata = []
    node_data = []
    edge_data = []

    node_id = 0

    # Create metadata and assign unique IDs
    for node in supply_chain.nodes:
        metadata.append(
            {
                "node_id": str(node_id),
                "node_class": node.node_class,
                "max_inventory": node.max_inventory,
                "cost_type": node.cost_type,
            }
        )
        node.id = node_id  # Assign ID to node object for reference
        node_id += 1

    edge_id = 0
    # Create edge metadata
    for edge in supply_chain.edges:
        source_node = None
        target_node = None

        for node in supply_chain.nodes:
            if edge in [e for e, _ in node.outgoing_edges]:
                source_node = node
            if edge in [e for e, _ in node.incoming_edges]:
                target_node = node
            if source_node and target_node:
                break

        if not source_node or not target_node:
            print(f"Warning: Edge {edge_id} is not properly connected.")
            print(f"Source node: {source_node.node_class if source_node else 'None'}")
            print(f"Target node: {target_node.node_class if target_node else 'None'}")
            continue

        metadata.append(
            {
                "edge_id": str(edge_id),
                "source_node_id": str(source_node.id),
                "target_node_id": str(target_node.id),
                "unit_price": edge.unit_price,
                "min_cost": edge.min_cost,
                "max_cost": edge.max_cost,
            }
        )
        edge.id = edge_id  # Assign ID to edge object for reference
        edge_id += 1

    # Simulate for n cycles
    for cycle in range(n_cycles):
        supply_chain.update()

        # Collect node data
        for node in supply_chain.nodes:
            node_data.append(
                {
                    "cycle": cycle,
                    "node_id": str(node.id),
                    "inventory": node.inventory,
                    "last_production": node.last_production,
                }
            )

        # Collect edge data
        for edge in supply_chain.edges:
            if hasattr(
                edge, "id"
            ):  # Only collect data for edges that were properly connected
                edge_data.append(
                    {
                        "cycle": cycle,
                        "edge_id": str(edge.id),
                        "quantity": edge.quantity,
                        "current_cost": edge.current_cost,
                    }
                )

    # Create DataFrames
    metadata_df = pd.DataFrame(metadata)
    node_data_df = pd.DataFrame(node_data)
    edge_data_df = pd.DataFrame(edge_data)

    return metadata_df, node_data_df, edge_data_df
