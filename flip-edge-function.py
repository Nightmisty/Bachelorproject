import networkx
import random
import math

def degree_changes(edges):
    in_changes = {}
    out_changes = {}

    for u, v in edges:
        out_changes[u] = out_changes.get(u, 0) + 1
        in_changes[v] = in_changes.get(v, 0) + 1

    return in_changes, out_changes

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

def flip_edge_at_path(Graph: networkx.Graph, path):

    node1, node2, node3, node4 = path

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


    if not all(Graph.has_edge(*edge) for edge in old_edges):
        raise ValueError("Not all edges exist.")


    if len(old_edges) != 3:
        raise ValueError("An edge has been choosen twice.")


    if any(
        Graph.has_edge(*edge) and edge not in old_edges
        for edge in new_edges
    ):
        raise ValueError("A new edge already exists.")

    removed_edges = old_edges - new_edges
    added_edges = new_edges - old_edges

    if degree_changes(removed_edges) != degree_changes(added_edges):
        raise ValueError("Flip changes degrees.")

    new_Graph = Graph.copy()
    new_Graph.remove_edges_from(old_edges)
    new_Graph.add_edges_from(new_edges)

    return new_Graph, old_edges, new_edges

Ring_of_cliques, S, T = create_ring_of_cliques(2)

path = [8, 5, 9, 8]

new_clique, old, new = flip_edge_at_path(
    Ring_of_cliques, path
)

print("Old edges:", sorted(old))
print("New edges:", sorted(new))

print("Edges after one flip:")

for u, v in new_clique.edges:
    print(u, v)




