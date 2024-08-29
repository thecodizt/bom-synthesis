import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import random
import io

# Assuming you have these classes defined
from core.supply_chain import SupplyChain, LeafNode, CombinerNode, SinkNode
from core.simulate import simulate_and_collect_data


def create_supply_chain():
    supply_chain = SupplyChain()

    # Create leaf nodes with random cost types
    leaf1 = LeafNode(
        200,
        "raw_material_1",
        [(0, 10), (5, 15), (10, 20)],
        random.choice(["fixed", "positive_dynamic", "negative_dynamic"]),
    )
    leaf2 = LeafNode(
        250,
        "raw_material_2",
        [(0, 15), (5, 20), (10, 25)],
        random.choice(["fixed", "positive_dynamic", "negative_dynamic"]),
    )
    leaf3 = LeafNode(
        220,
        "raw_material_3",
        [(0, 12), (5, 18), (10, 22)],
        random.choice(["fixed", "positive_dynamic", "negative_dynamic"]),
    )
    supply_chain.add_node(leaf1)
    supply_chain.add_node(leaf2)
    supply_chain.add_node(leaf3)

    # Create intermediate nodes with random cost types
    intermediate_a1 = CombinerNode(
        300,
        "intermediate_a1",
        [0.8, 1.0],
        [1, 1.2],
        random.choice(["fixed", "positive_dynamic", "negative_dynamic"]),
    )
    intermediate_a2 = CombinerNode(
        280,
        "intermediate_a2",
        [0.9, 1.1],
        [1.1, 1.3],
        random.choice(["fixed", "positive_dynamic", "negative_dynamic"]),
    )
    supply_chain.add_node(intermediate_a1)
    supply_chain.add_node(intermediate_a2)

    intermediate_b1 = CombinerNode(
        300,
        "intermediate_b1",
        [0.8, 1.0],
        [1, 1.2],
        random.choice(["fixed", "positive_dynamic", "negative_dynamic"]),
    )
    intermediate_b2 = CombinerNode(
        280,
        "intermediate_b2",
        [0.9, 1.1],
        [1.1, 1.3],
        random.choice(["fixed", "positive_dynamic", "negative_dynamic"]),
    )
    supply_chain.add_node(intermediate_b1)
    supply_chain.add_node(intermediate_b2)

    # Create final combiner node with random cost type
    final_combiner = CombinerNode(
        350,
        "final_product",
        [0.7, 0.8, 0.9],
        [1, 1.1, 1.2],
        random.choice(["fixed", "positive_dynamic", "negative_dynamic"]),
    )
    supply_chain.add_node(final_combiner)

    # Create sink node with random cost type
    sink = SinkNode(
        consumption_rate=250,
        cost_type=random.choice(["fixed", "positive_dynamic", "negative_dynamic"]),
    )
    supply_chain.add_node(sink)

    # Add edges with cost ranges
    supply_chain.add_edge(leaf1, intermediate_a1, 10, 30, 5, 15)
    supply_chain.add_edge(leaf2, intermediate_a1, 15, 35, 8, 20)
    supply_chain.add_edge(leaf2, intermediate_a2, 12, 30, 6, 18)
    supply_chain.add_edge(leaf3, intermediate_a2, 14, 32, 7, 19)
    supply_chain.add_edge(intermediate_a1, intermediate_b1, 20, 40, 10, 25)
    supply_chain.add_edge(intermediate_a2, intermediate_b1, 22, 42, 11, 27)
    supply_chain.add_edge(intermediate_b1, final_combiner, 20, 40, 10, 25)
    supply_chain.add_edge(intermediate_b2, final_combiner, 22, 42, 11, 27)
    supply_chain.add_edge(leaf3, final_combiner, 18, 35, 9, 23)
    supply_chain.add_edge(final_combiner, sink, 25, 50, 13, 30)

    return supply_chain


def convert_to_graph(metadata, node, edge):
    graphs = []
    unique_cycles = node["cycle"].unique()

    for cycle in unique_cycles:
        G = nx.DiGraph()

        # Add nodes
        cycle_nodes = node[node["cycle"] == cycle]
        for _, row in cycle_nodes.iterrows():
            node_id = row["node_id"]
            node_data = (
                metadata[metadata["node_id"] == node_id].iloc[0].to_dict()
                if not metadata[metadata["node_id"] == node_id].empty
                else {}
            )
            node_data.update(row.to_dict())
            G.add_node(node_id, **node_data)

        # Add edges
        cycle_edges = edge[edge["cycle"] == cycle]
        for _, row in cycle_edges.iterrows():
            edge_id = row["edge_id"]
            edge_data = (
                metadata[metadata["edge_id"] == edge_id].iloc[0].to_dict()
                if not metadata[metadata["edge_id"] == edge_id].empty
                else {}
            )
            edge_data.update(row.to_dict())
            source = edge_data.get("source_node_id")
            target = edge_data.get("target_node_id")
            if source and target:
                G.add_edge(source, target, **edge_data)

        graphs.append(G)

    return graphs


def visualize_graph(G, cycle):
    plt.figure(figsize=(15, 10))
    pos = nx.spring_layout(G, k=0.9, iterations=50)

    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_size=3000, node_color="lightblue", alpha=0.8)
    node_labels = {
        node: f"{node}\n{G.nodes[node].get('node_class', 'N/A')}\nInv: {G.nodes[node].get('inventory', 'N/A')}\nProd: {G.nodes[node].get('last_production', 'N/A')}"
        for node in G.nodes()
    }
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=8)

    # Draw edges
    nx.draw_networkx_edges(G, pos, edge_color="gray", arrows=True, arrowsize=20)
    edge_labels = {
        (
            u,
            v,
        ): f"Edge: {d.get('edge_id', 'N/A')}\nQ: {d.get('quantity', 'N/A'):.2f}\nC: {d.get('current_cost', 'N/A'):.2f}"
        for u, v, d in G.edges(data=True)
    }
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=6)

    plt.title(f"Supply Chain Network - Cycle {cycle}")
    plt.axis("off")
    plt.tight_layout()
    return plt


def main():
    st.title("BoM Synthesis with Supply Chain Simulation")

    # Create supply chain and simulate data
    supply_chain = create_supply_chain()
    n_cycles = st.slider(
        "Number of cycles to simulate", min_value=1, max_value=50, value=20
    )

    if st.button("Generate Data"):
        metadata_df, node_data_df, edge_data_df = simulate_and_collect_data(
            supply_chain, n_cycles
        )
        st.session_state.metadata_df = metadata_df
        st.session_state.node_data_df = node_data_df
        st.session_state.edge_data_df = edge_data_df
        st.success("Data generated successfully!")

    if "metadata_df" in st.session_state:
        # Visualize the graph
        graphs = convert_to_graph(
            st.session_state.metadata_df,
            st.session_state.node_data_df,
            st.session_state.edge_data_df,
        )
        cycle_to_view = st.slider(
            "Select cycle to visualize", min_value=0, max_value=len(graphs) - 1, value=0
        )
        fig = visualize_graph(graphs[cycle_to_view], cycle_to_view)
        st.pyplot(fig)

        # Download options
        st.subheader("Download Data")

        def to_excel(df):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Sheet1")
            processed_data = output.getvalue()
            return processed_data

        metadata_excel = to_excel(st.session_state.metadata_df)
        node_data_excel = to_excel(st.session_state.node_data_df)
        edge_data_excel = to_excel(st.session_state.edge_data_df)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                label="Download Metadata",
                data=metadata_excel,
                file_name="metadata.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        with col2:
            st.download_button(
                label="Download Node Data",
                data=node_data_excel,
                file_name="node_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        with col3:
            st.download_button(
                label="Download Edge Data",
                data=edge_data_excel,
                file_name="edge_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )


if __name__ == "__main__":
    main()
