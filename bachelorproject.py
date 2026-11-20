import networkx 
import random
import math
import matplotlib.pyplot as plt
import numpy
from itertools import combinations
import csv
import json
import pandas as pd
from math import isclose

def create_ring_of_cliques(cliquenumbers:int):
    Graph = networkx.DiGraph()
    cliques = []
    for i in range(cliquenumbers):
        clique = networkx.complete_graph(5, create_using=networkx.DiGraph)
        rename_nodes = {}
        for node in clique.nodes():
            rename_nodes[node] = node + i * 5

        clique = networkx.relabel_nodes(clique, rename_nodes)
        Graph = networkx.compose(Graph, clique)
        cliques.append(list(clique.nodes()))

    for i in range(cliquenumbers):
        first_node = cliques[i][0]
        last_node = cliques[i][-1]
        next_first_node = cliques[(i+1)%cliquenumbers][0]
        Graph.remove_edge(last_node,first_node)
        Graph.add_edge(last_node,next_first_node)
        edges = Graph.add_edge(last_node,next_first_node)
    # divide the Graph in two sets that are only connected by 2 edges
    S = set(range(math.floor(cliquenumbers / 2) * 5))
    T = set(Graph.nodes())- S
    return Graph, S, T

def random_sets(Graph:networkx.Graph):
    S = []
    T = []
    for node in Graph:
        if random.random() < 0.5:
            S.append(node)
        else:
            T.append(node)
    return S,T

def flip_edge(Graph:networkx.Graph):

    while True:

        node1 = random.choice(list(Graph.nodes()))
        node2 = random.choice(list(Graph.successors(node1)))

        node3_candidates = list(Graph.successors(node2))
        node3_candidates = [
            node for node in node3_candidates
            if (node2, node) != (node1, node2)
        ]
        node3 = random.choice(node3_candidates)

        node4_candidates = list(Graph.successors(node3))

        node4_candidates = [
            node for node in node4_candidates
            if (node3, node) != (node1, node2)
            and (node3, node) != (node2, node3)
        ]
        node4 = random.choice(node4_candidates)

        old_edges = {
            (node1, node2),
            (node2, node3),
            (node3, node4)
        }

        new_edges = {
            (node1, node3),
            (node2, node4),
            (node3, node2)
        }

        
        if any(
            Graph.has_edge(*edge) and edge not in old_edges
            for edge in new_edges
        ):
            continue

        
        removed_edges = old_edges - new_edges
        added_edges = new_edges - old_edges

        
        if degree_changes(removed_edges) != degree_changes(added_edges):
            continue
        break

    new_Graph = Graph.copy()
    new_Graph.remove_edges_from(old_edges)
    new_Graph.add_edges_from(new_edges)

    return new_Graph, old_edges, new_edges

def degree_changes(edges):
    in_changes = {}
    out_changes = {}

    for u, v in edges:
        out_changes[u] = out_changes.get(u, 0) + 1
        in_changes[v] = in_changes.get(v, 0) + 1

    return in_changes, out_changes

def cut_size(S:set, T:set, Graph: networkx.Graph)-> int:
    outgoing = []
    for u, v in Graph.edges():
        if u in S and v in T:
            outgoing.append((u, v))
    return len(outgoing)




def cut_strain(S:set, T:set, Graph: networkx.Graph)-> tuple[float,float,float]:
    #returns 0 if a cut would be empty although 0 is not in the range of possible cut sizes
    cut_strain_out = 0
    cut_strain_in = 0
    for node in Graph.nodes:
        neighbours_out_in_S = 0
        neighbours_out_in_T = 0
        neighbours_in_in_S = 0
        neighbours_in_in_T = 0
        for u,v in Graph.edges:
            if u == node:
                if v in S:
                    neighbours_out_in_S += 1
                elif v in T:
                    neighbours_out_in_T += 1
            if v == node:
                if u in S:
                    neighbours_in_in_S += 1
                elif u in T:
                    neighbours_in_in_T += 1

        all_neighbours_out = neighbours_out_in_S + neighbours_out_in_T
    
        cut_strain_out += ((neighbours_out_in_S/all_neighbours_out)*(neighbours_out_in_T/all_neighbours_out))
        
        all_neighbours_in = neighbours_in_in_S + neighbours_in_in_T
       
        cut_strain_in += ((neighbours_in_in_S/all_neighbours_in)*(neighbours_in_in_T/all_neighbours_in))

    cut_strain_mean = (cut_strain_out + cut_strain_in)/2
    return cut_strain_out, cut_strain_in, cut_strain_mean



def flip_chain_simulation(Graph: networkx.Graph, S, T , rounds: int):
    # the lists of size and strain shall document the change over time during the rounds. they are equivilent to the data points
    # that i want to visualize in a graphic picture later
    cut_sizes = []
    cut_strain_out = []
    cut_strain_in = []
    cut_strain_mean = []
    current_Graph = Graph
    for i in range(1,rounds):
    
        current_Graph, _, _ = flip_edge(current_Graph)

        # for big roundnumbers, only every 10th average is added to the list to shorten the listlength and reduce the number of
        # datapoints 
        if rounds > 100:
            if i%10 == 0:
                cut_sizes.append(cut_size(S,T,current_Graph))
                u,v,w = cut_strain(S,T,current_Graph)
                cut_strain_out.append(u)
                cut_strain_in.append(v)
                cut_strain_mean.append(w)
        else:
            cut_sizes.append(cut_size(S,T,current_Graph))
            u,v,w = cut_strain(S,T,current_Graph)
            cut_strain_out.append(u)
            cut_strain_in.append(v)
            cut_strain_mean.append(w)
    
    return (cut_sizes,cut_strain_out,cut_strain_in,cut_strain_mean)


def flip_chain_simulation_for_changes(Graph, S, T, rounds, samples=1000):

    cut_strain_mean = []
    expected_changes = []

    current_Graph = Graph

    for i in range(rounds + 1):

        
        print(i)
            # Tatsächlicher Cut Strain
        _, _, strain = cut_strain(S, T, current_Graph)

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
    _, _, current_strain = cut_strain(S, T, Graph)

    changes = []

    for i in range(samples):

        # Ein zufälliger Flip vom gleichen Ausgangsgraphen
        next_Graph, _, _ = flip_edge(Graph)

        # Cut Strain nach dem Flip
        _, _, next_strain = cut_strain(S, T, next_Graph)

        changes.append(next_strain - current_strain)

    # Durchschnittliche Veränderung
    return numpy.mean(changes)

def expected_cut_strain_change_in_and_out(Graph, S, T, samples=10000):

    current_out, current_in, _ = cut_strain(S, T, Graph)

    changes_out = []
    changes_in = []

    for i in range(samples):
        next_Graph, _, _ = flip_edge(Graph)
        next_out, next_in, _ = cut_strain(S, T, next_Graph)

        changes_out.append(next_out - current_out)
        changes_in.append(next_in - current_in)

    expected_out = numpy.mean(changes_out)
    expected_in = numpy.mean(changes_in)
    expected_directed = (expected_out + expected_in) / 2

    return expected_out, expected_in, expected_directed

def generate_all_cuts(Graph: networkx):
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
    Graph: networkx.DiGraph,
    rounds=90,
    samples=1000,
    max_positive=15,
    max_cuts=None
):
    original_Graph = Graph.copy()
    tested_cuts = 0
    max_number_neg_averages = 0

    for S, T in generate_all_cuts(original_Graph):
        if len(S) < 6 or len(T) < 6:
            continue
        # Only consider cuts with initially low cut strain
        _, _, initial_strain = cut_strain(S, T, original_Graph)

        if initial_strain > 3.0:
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
            _, _, strain = cut_strain(S, T, current_Graph)
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
    


search= False

Graph, S, T = create_ring_of_cliques(5)

#V = {5*i + j for i in range(25) for j in (0, 1)}
#W = set(Graph.nodes()) - V
if search == True:
    result = search_easteregg(Graph)

    strain, expected_changes = flip_chain_simulation_for_changes(Graph, S, T,rounds=300,samples=1000)
    if result != 0:

        # Save initial graph, cut and flip sequence
        documentation = {
            "original_nodes": list(result["original_graph"].nodes()),
            "original_edges": [
                list(edge)
                for edge in result["original_graph"].edges()
            ],
            "S": sorted(result["S"]),
            "T": sorted(result["T"]),
            "initial_strain": result["initial_strain"],
            "flip_history": result["flip_history"]
        }

        with open("found_cut.json", "w", encoding="utf-8") as file:
            json.dump(documentation, file, indent=2)

        # Save strain development
        with open("strain_development.csv", "w", newline="") as file:
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
            range(1, 91),
            result["expected_changes"],
            label="Estimated expected change"
        )
        plt.axhline(0, color="black", linestyle="--")
        plt.xlabel("Flip step")
        plt.ylabel("Expected change in cut strain")
        plt.title("Expected cut strain change over 200 flips")
        plt.legend()
        plt.tight_layout()
        plt.show()


def flip_specific_edges(Graph: networkx.Graph, old_edges, new_edges):
        for edge in old_edges:
            Graph.remove(edge)
        for edge in new_edges:
            Graph.add_edge(edge)
        return Graph

def replay_flip_history(Graph, S, T, flip_history, samples= 1000):

        current_Graph = Graph.copy()

        current_Graph = Graph.copy()

        cut_strain_means = []
        expected_changes = []
        
    # Replay recorded flips
        for step in range(len(flip_history) + 1):
            

        # Actual mean cut strain
            cut_out, cut_in, mean = cut_strain(S, T, current_Graph)
            cut_strain_means.append(float(mean))
            if step == 87:
                print("Actual change:", mean)
            if step == 88:
                print("Actual Change:", mean)
        # Expected change in mean cut strain
            expected_change = expected_cut_strain_change(
                current_Graph, S, T, samples
            )
            expected_changes.append(float(expected_change))

            if step == 87:

                expec_out87 , expec_in87, direc87 = expected_cut_strain_change_in_and_out(current_Graph, S, T, 100000)
                print("cut_out 87", expec_out87)
                print("cut_in 87", expec_in87)
                print("expected change 87:", direc87)
            if step == 88:
                expec_out88 , expec_in88, direc88 = expected_cut_strain_change_in_and_out(current_Graph, S, T, 100000)
                print("cut_out 88", expec_out88)
                print("cut_in 88", expec_in88)
                print("expected change 88:", direc88)
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

        # Validate recorded flip
            if not all(current_Graph.has_edge(u, v) for u, v in old_edges):
                raise ValueError(
                    f"Invalid flip at step {flip['step']}"
            )

        # Execute recorded flip
            current_Graph.remove_edges_from(old_edges)
            current_Graph.add_edges_from(new_edges)

        return current_Graph, cut_strain_means, expected_changes


with open("second_found_cut.json", "r", encoding="utf-8") as file:
    data = json.load(file)

flip_history = data["flip_history"]
S = data["S"]
T = data["T"]

Replay = True
if Replay == True:
    new_Graph, replay_cut_strain, replay_expected_changes = replay_flip_history(Graph, S, T, flip_history)

    #print("Expected:" ,replay_expected_changes)
    #print("Actual:",replay_cut_strain)

    plt.figure(figsize=(10, 5))
    plt.plot(
            range(1, 152),
            replay_cut_strain,
            label="Actual change"
        )
    plt.axhline(0, color="black", linestyle="--")
    plt.xlabel("Flip step")
    plt.ylabel("Actual change in cut strain")
    plt.title("Actual cut strain change over 90 flips")
    plt.legend()
    plt.tight_layout()
    plt.show()


    plt.figure(figsize=(10, 5))
    plt.plot(
            range(1, 152),
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




def plot_expected_changes(Graph, S, T, flip_history,
                          step=87, repetitions=50, samples=100000):

    if not 0 <= step <= len(flip_history):
        raise ValueError("Step liegt außerhalb der Flip-History.")

    # Graphzustand des gewünschten Steps rekonstruieren
    current_Graph = Graph.copy()

    for i in range(step):
        flip = flip_history[i]

        old_edges = [tuple(e) for e in flip["removed_edges"]]
        new_edges = [tuple(e) for e in flip["added_edges"]]

        current_Graph.remove_edges_from(old_edges)
        current_Graph.add_edges_from(new_edges)

    # Ergebnisse speichern
    expected_out = []
    expected_in = []
    expected_directed = []

    # Erwartete Änderungen mehrfach schätzen
    for i in range(repetitions):

        out, incoming, directed = (
            expected_cut_strain_change_in_and_out(
                current_Graph, S, T, samples
            )
        )

        expected_out.append(out)
        expected_in.append(incoming)
        expected_directed.append(directed)

        print(f"Durchlauf {i + 1}/{repetitions}")

    # Diagramm
    x = range(1, repetitions + 1)

    plt.figure(figsize=(12, 6))

    plt.plot(x, expected_out,
             color="blue", label="Expected Outgoing")

    plt.plot(x, expected_in,
             color="orange", label="Expected Incoming")

    plt.plot(x, expected_directed,
             color="green", label="Expected Directed")

    plt.axhline(0, color="black", linestyle="--", linewidth=0.8)

    plt.xlabel("Durchlauf")
    plt.ylabel("Geschätzte erwartete Cut-Strain-Änderung")
    plt.title(f"Expected Cut Strain Change – Step {step}")

    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()

    return expected_out, expected_in, expected_directed


show_exp_changes = False
if show_exp_changes == True:
    out88, in88, directed88 = plot_expected_changes(
        Graph, S, T, flip_history,
        step=91,
        repetitions=50,
        samples=100000
    )
