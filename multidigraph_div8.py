import networkx 
import random
import math
import matplotlib.pyplot as plt
import numpy
from itertools import combinations
import csv
import json
import pandas as pd
from fractions import Fraction
from math import isclose


def create_ring_of_cliques(cliquenumbers: int, cliquesize: int = 5):
    Graph = networkx.MultiDiGraph()
    cliques = []

    for i in range(cliquenumbers):
        clique = networkx.complete_graph(
            cliquesize,
            create_using=networkx.MultiDiGraph
        )

        rename_nodes = {}
        for node in clique.nodes():
            rename_nodes[node] = node + i * cliquesize

        clique = networkx.relabel_nodes(clique, rename_nodes)
        Graph = networkx.compose(Graph, clique)
        cliques.append(list(clique.nodes()))

    for i in range(cliquenumbers):
        first_node = cliques[i][0]
        last_node = cliques[i][-1]
        next_first_node = cliques[(i+1) % cliquenumbers][0]

        Graph.remove_edge(last_node, first_node)
        Graph.add_edge(last_node, next_first_node)

    S = set(range(math.floor(cliquenumbers / 2) * cliquesize))
    T = set(Graph.nodes()) - S

    return Graph, S, T


def random_sets(Graph:networkx.MultiDiGraph):
    S = []
    T = []
    for node in Graph:
        if random.random() < 0.5:
            S.append(node)
        else:
            T.append(node)
    return S,T


def flip_edge(Graph: networkx.MultiDiGraph):

    # Startknoten zufällig auswählen
    node1 = random.choice(list(Graph.nodes()))

    # Erste Kante auswählen
    edge1 = random.choice(
        list(Graph.out_edges(node1, keys=True))
    )

    node2 = edge1[1]

    # Zweite Kante auswählen
    edge2_candidates = [
        edge for edge in Graph.out_edges(node2, keys=True)
        if edge != edge1
    ]

    edge2 = random.choice(edge2_candidates)
    node3 = edge2[1]

    # Dritte Kante auswählen
    edge3_candidates = [
        edge for edge in Graph.out_edges(node3, keys=True)
        if edge != edge1 and edge != edge2
    ]

    edge3 = random.choice(edge3_candidates)
    node4 = edge3[1]

    old_edges = [edge1, edge2, edge3]

    new_Graph = Graph.copy()

    # Genau die ausgewählten Kanten entfernen
    new_Graph.remove_edges_from(old_edges)

    # Neue Kanten hinzufügen
    key1 = new_Graph.add_edge(node1, node3)
    key2 = new_Graph.add_edge(node3, node2)
    key3 = new_Graph.add_edge(node2, node4)

    new_edges = [
        (node1, node3, key1),
        (node3, node2, key2),
        (node2, node4, key3)
    ]

    # Kontrolle der Graderhaltung
    assert dict(Graph.in_degree()) == dict(new_Graph.in_degree())
    assert dict(Graph.out_degree()) == dict(new_Graph.out_degree())

    return new_Graph, old_edges, new_edges


def degree_changes(edges):
    in_changes = {}
    out_changes = {}

    for u, v, k in edges:
        out_changes[u] = out_changes.get(u, 0) + 1
        in_changes[v] = in_changes.get(v, 0) + 1

    return in_changes, out_changes


def cut_size(S:set, T:set, Graph: networkx.MultiDiGraph)-> int:
    outgoing = []
    for u, v, k in Graph.edges(keys=True):
        if u in S and v in T:
            outgoing.append((u, v, k))
    return len(outgoing)



def cut_strain_div8(
    S: set, T: set, Graph: networkx.MultiDiGraph
) -> tuple[float, dict, dict]:

    S, T = set(S), set(T)
    cut_strain = 0
    neighbours_S = {}
    neighbours_T = {}

    for node in Graph.nodes:

        outgoing_S = sum(
            1 for u, v, k in Graph.out_edges(node, keys=True)
            if v in S
        )

        outgoing_T = sum(
            1 for u, v, k in Graph.out_edges(node, keys=True)
            if v in T
        )

        incoming_S = sum(
            1 for u, v, k in Graph.in_edges(node, keys=True)
            if u in S
        )

        incoming_T = sum(
            1 for u, v, k in Graph.in_edges(node, keys=True)
            if u in T
        )

        neighbours_S[node] = outgoing_S + incoming_S
        neighbours_T[node] = outgoing_T + incoming_T

        degree = Graph.in_degree(node) + Graph.out_degree(node)

        cut_strain += ((neighbours_S[node] / degree)* (neighbours_T[node] / degree)
)
    return cut_strain, neighbours_S, neighbours_T


def flip_chain_simulation_for_changes(Graph, S, T, rounds, samples=1000):

    cut_strain_mean = []
    expected_changes = []

    current_Graph = Graph

    for i in range(rounds + 1):

        
        print(i)
            # Tatsächlicher Cut Strain
        strain, _, _ = cut_strain_div8(S, T, current_Graph)

        cut_strain_mean.append(strain)

            # Erwartete Veränderung durch den nächsten Flip
        expected_change = expected_cut_strain_change(
            current_Graph, S, T, samples
            )

        expected_changes.append(expected_change)

        # Nächsten tatsächlichen Flip durchführen
        if i < rounds:
            current_Graph, _, _ = flip_edge(current_Graph)

    return cut_strain_mean, expected_changes


def expected_cut_strain_change(Graph, S, T, samples=1000):

    # Cut Strain vor dem Flip
    current_strain, _, _ = cut_strain_div8(S, T, Graph)

    changes = []

    for i in range(samples):

        # Ein zufälliger Flip vom gleichen Ausgangsgraphen
        next_Graph, _, _ = flip_edge(Graph)

        # Cut Strain nach dem Flip
        next_strain, _, _ = cut_strain_div8(S, T, next_Graph)

        changes.append(next_strain - current_strain)

    # Durchschnittliche Veränderung
    return numpy.mean(changes)


def expected_cut_strain_change_in_and_out(
        Graph, S, T, samples=10000):

    current_strain, current_S, current_T = (
        cut_strain_div8(S, T, Graph)
    )

    changes_S = []
    changes_T = []
    changes_interaction = []
    changes_strain = []

    for i in range(samples):

        next_Graph, _, _ = flip_edge(Graph)

        strain, next_S, next_T = cut_strain_div8(
            S, T, next_Graph
        )

        contribution_S = 0
        contribution_T = 0
        contribution_interaction = 0

        for node in Graph.nodes:

            delta_S = (
                next_S[node] - current_S[node]
            )

            delta_T = (
                next_T[node] - current_T[node]
            )

            degree = Graph.in_degree(node) + Graph.out_degree(node)

            contribution_S += (current_T[node] * delta_S) / degree**2

            contribution_T += (current_S[node] * delta_T) / degree**2

            contribution_interaction += (delta_S * delta_T) / degree**2

        actual_change = strain - current_strain

        # Kontrolle der mathematischen Zerlegung
        assert math.isclose(
            actual_change,
            contribution_S
            + contribution_T
            + contribution_interaction,
            abs_tol=1e-12
        )

        changes_S.append(contribution_S)
        changes_T.append(contribution_T)
        changes_interaction.append(
            contribution_interaction
        )
        changes_strain.append(actual_change)

    expected_S = numpy.mean(changes_S)
    expected_T = numpy.mean(changes_T)

    expected_interaction = numpy.mean(
        changes_interaction
    )

    expected_directed = numpy.mean(changes_strain)

    return (expected_directed, expected_S, expected_T, expected_interaction)


def generate_all_cuts(Graph: networkx.MultiDiGraph):
    nodes = list(Graph.nodes())
    n = len(nodes)

    fixed_node = nodes[0]
    remaining_nodes = nodes[1:]

    for size in range(n):
        for combination in combinations(remaining_nodes, size):

            S = {fixed_node, *combination}
            T = set(nodes) - S

            if T:
                yield S, T


def search_easteregg(
    Graph: networkx.MultiDiGraph,
    rounds=90,
    samples=1000,
    max_positive=15,
    max_cuts=None
):
    original_Graph = Graph.copy()
    tested_cuts = 0
    max_number_neg_averages = 0

    for S, T in generate_all_cuts(original_Graph):
        if len(S) < 3 or len(T) < 3:
            continue
        # Only consider cuts with initially low cut strain
        initial_strain, _, _ = cut_strain_div8(S, T, original_Graph)

        initial_cut_size = cut_size(S, T, original_Graph)

        if initial_cut_size < 7.5 * min(len(S), len(T)):
            continue

        tested_cuts += 1

        current_Graph = original_Graph.copy()
        positive_count = 0
        neg_rounds = 0
        
        expected_changes = []
        actual_strains = [initial_strain]
        flip_history = []

        print(f"Testing cut {tested_cuts}: initial strain = {initial_strain:.4f}")

        for step in range(rounds):

            if tested_cuts == 1000:
                print("Maximum negatives:", max_number_neg_averages)
                return 0
            # Estimate expected one-step change from current graph
            average = expected_cut_strain_change(
                current_Graph, S, T, samples
            )

            expected_changes.append(float(average))

            # Allow up to 15 nonnegative estimates
            if average >= 0:
                positive_count += 1
            neg_rounds += 1
            if positive_count > max_positive:
                if neg_rounds > max_number_neg_averages:
                    max_number_neg_averages = neg_rounds
                break
            
            # Perform one actual flip
            current_Graph, old_edges, new_edges = flip_edge(
                current_Graph
            )

            flip_history.append({
                "step": step + 1,
                "removed_edges": sorted(old_edges),
                "added_edges": sorted(new_edges)
            })

            # Record actual strain after the flip
            strain, _, _ = cut_strain_div8(S, T, current_Graph)
            actual_strains.append(float(strain))
        
        # Successful cut: all 200 steps completed
        if len(flip_history) == rounds:

            result = {
                "original_graph": original_Graph.copy(),
                "final_graph": current_Graph.copy(),
                "S": S.copy(),
                "T": T.copy(),
                "initial_strain": initial_strain,
                "expected_changes": expected_changes,
                "actual_strains": actual_strains,
                "flip_history": flip_history,
                "positive_count": positive_count,
                "negative_count": rounds - positive_count,
                "tested_cuts": tested_cuts
            }

            print("\nSUCCESS: Suitable cut found!")
            print("S:", S)
            print("T:", T)
            print("Initial strain:", initial_strain)
            print("Negative estimates:", rounds - positive_count)
            print("Nonnegative estimates:", positive_count)
            

            return result

        if max_cuts is not None and tested_cuts >= max_cuts:
            break

    print("No suitable cut found.")
    return None


def flip_specific_edges(Graph: networkx.MultiDiGraph, old_edges, new_edges):
    # Work on a copy so invalid histories cannot partially modify Graph.
    result = Graph.copy()
    for u, v, k in old_edges:
        if not result.has_edge(u, v, k):
            raise ValueError(f"Missing edge: {(u, v, k)}")
        result.remove_edge(u, v, k)
    for u, v, k in new_edges:
        if result.has_edge(u, v, k):
            raise ValueError(f"Duplicate edge key: {(u, v, k)}")
        result.add_edge(u, v, key=k)
    if dict(result.in_degree()) != dict(Graph.in_degree()) or dict(result.out_degree()) != dict(Graph.out_degree()):
        raise ValueError("Flip changes degrees")
    return result


def load_history(filename="found_cut_multi_div8.json"):
    with open(filename, encoding="utf-8") as file:
        data = json.load(file)
    Graph = networkx.MultiDiGraph()
    Graph.add_nodes_from(data["original_nodes"])
    for u, v, k in data["original_edges"]:
        if Graph.has_edge(u, v, k):
            raise ValueError("Duplicate initial edge key")
        Graph.add_edge(u, v, key=k)
    return Graph, set(data["S"]), set(data["T"]), data["flip_history"]


def replay_flip_history(Graph, S, T, flip_history, samples= 1000):

        current_Graph = Graph.copy()

        cut_strain_means = []
        expected_changes = []
        
    # Replay recorded flips
        for step in range(len(flip_history) + 1):
            

        # Actual mean cut strain
            strain, _, _ = cut_strain_div8(S, T, current_Graph)
            cut_strain_means.append(float(strain))
            
        # Expected change in mean cut strain
            expected_change = expected_cut_strain_change(
                current_Graph, S, T, samples
            )
            expected_changes.append(float(expected_change))

        # No further flip after the last state
            if step == len(flip_history):
                break

        # Replay the next recorded flip
            flip = flip_history[step]

            old_edges = [
                tuple(edge) for edge in flip["removed_edges"]
        ]

            new_edges = [
                tuple(edge) for edge in flip["added_edges"]
        ]

            current_Graph = flip_specific_edges(current_Graph, old_edges, new_edges)

        return current_Graph, cut_strain_means, expected_changes


def plot_expected_changes(
        Graph, S, T, flip_history,
        step=89, repetitions=20, samples=10000):

    if not 0 <= step <= len(flip_history):
        raise ValueError(
            "Step liegt außerhalb der Flip-History."
        )

    current_Graph = Graph.copy()

    for i in range(step):

        flip = flip_history[i]

        old_edges = [
            tuple(e) for e in flip["removed_edges"]
        ]

        new_edges = [
            tuple(e) for e in flip["added_edges"]
        ]

        current_Graph = flip_specific_edges(current_Graph, old_edges, new_edges)

    expected_S = []
    expected_T = []
    expected_interaction = []
    expected_directed = []

    for i in range(repetitions):

        strain, contribution_S, contribution_T, interaction = (
            expected_cut_strain_change_in_and_out(
                current_Graph, S, T, samples
            )
        )

        expected_S.append(contribution_S)
        expected_T.append(contribution_T)
        expected_interaction.append(interaction)
        expected_directed.append(strain)

        print(f"Durchlauf {i + 1}/{repetitions}")

    x = range(1, repetitions + 1)

    plt.figure(figsize=(12, 6))

    plt.plot(
        x, expected_S,
        color="blue",
        label="Expected S Contribution"
    )

    plt.plot(
        x, expected_T,
        color="orange",
        label="Expected T Contribution"
    )

    plt.plot(
        x, expected_interaction,
        color="purple",
        label="Expected Interaction"
    )

    plt.plot(
        x, expected_directed,
        color="green",
        label="Expected Total Strain Change"
    )

    plt.axhline(
        0, color="black",
        linestyle="--", linewidth=0.8
    )

    plt.xlabel("Durchlauf")
    plt.ylabel("Expected Contribution")
    plt.title(
        f"Expected Cut Strain Decomposition – Step {step}"
    )

    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()

    return (
        expected_directed,
        expected_S,
        expected_T,
        expected_interaction
    )


if __name__ == "__main__":
    search = False


    Graph, S, T = create_ring_of_cliques(5,16)


    if search == True:
        result = search_easteregg(Graph)

        strain, expected_changes = flip_chain_simulation_for_changes(Graph, S, T,rounds=300,samples=1000)
        if result is not None and result != 0:

            # Save initial graph, cut and flip sequence
            documentation = {
                "original_nodes": list(result["original_graph"].nodes()),
                "original_edges": [
                    list(edge)
                    for edge in result["original_graph"].edges(keys=True)
                ],
                "S": sorted(result["S"]),
                "T": sorted(result["T"]),
                "initial_strain": result["initial_strain"],
                "cut_strain_definition": "div8",
                "flip_history": result["flip_history"]
            }

            with open("found_cut_multi_div8.json", "w", encoding="utf-8") as file:
                json.dump(documentation, file, indent=2)

            # Save strain development
            with open("strain_development_multi_div8.csv", "w", newline="") as file:
                writer = csv.writer(file)

                writer.writerow([
                    "step",
                    "actual_strain_before_flip",
                    "estimated_expected_change",
                    "actual_strain_after_flip"
                ])

                for i in range(len(result["expected_changes"])):
                    writer.writerow([
                        i + 1,
                        result["actual_strains"][i],
                        result["expected_changes"][i],
                        result["actual_strains"][i + 1]
                    ])

            #Plot expected one-step changes
            plt.figure(figsize=(10, 5))
            plt.plot(
                range(1, len(result["expected_changes"]) + 1),
                result["expected_changes"],
                label="Estimated expected change"
            )
            plt.axhline(0, color="black", linestyle="--")
            plt.xlabel("Flip step")
            plt.ylabel("Expected change in cut strain")
            plt.title("Expected cut strain change over 90 flips")
            plt.legend()
            plt.tight_layout()
            plt.show()


    Replay = False


    if Replay == True:
        Graph, S, T, flip_history = load_history()
        new_Graph, replay_cut_strain, replay_expected_changes = replay_flip_history(Graph, S, T, flip_history)

        #print("Expected:" ,replay_expected_changes)
        #print("Actual:",replay_cut_strain)

        plt.figure(figsize=(10, 5))
        plt.plot(
                range(len(replay_cut_strain)),
                replay_cut_strain,
                label="Actual strain"
            )
        plt.axhline(0, color="black", linestyle="--")
        plt.xlabel("Flip step")
        plt.ylabel("Actual cut strain")
        plt.title("Actual cut strain change over 90 flips")
        plt.legend()
        plt.tight_layout()
        plt.show()


        plt.figure(figsize=(10, 5))
        plt.plot(
                range(len(replay_expected_changes)),
                replay_expected_changes,
                label="Estimated expected change"
            )
        plt.axhline(0, color="black", linestyle="--")
        plt.xlabel("Flip step")
        plt.ylabel("Expected change in cut strain")
        plt.title("Expected cut strain change over 90 flips")
        plt.legend()
        plt.tight_layout()
        plt.show()


    show_in_and_out = True


    if show_in_and_out == True:
        Graph, S, T, flip_history = load_history()
        strain, contribution_S45, contribution_T45, interaction45 = (
        plot_expected_changes(
            Graph, S, T, flip_history,
            step=70,
            repetitions=20,
            samples=10000
        )
    )

