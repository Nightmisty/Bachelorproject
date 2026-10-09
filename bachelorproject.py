import networkx 
import random
import math

def create_ring_of_cliques(cliquesize:int):
    Graph = networkx.DiGraph()
    cliques = []
    for i in range(cliquesize):
        clique = networkx.complete_graph(cliquesize, create_using=networkx.DiGraph)
        rename_nodes = {}
        for node in clique.nodes():
            rename_nodes[node] = node + i * cliquesize

        clique = networkx.relabel_nodes(clique, rename_nodes)
        Graph = networkx.compose(Graph, clique)
        cliques.append(list(clique.nodes()))

    for i in range(cliquesize):
        first_node = cliques[i][0]
        last_node = cliques[i][-1]
        next_first_node = cliques[(i+1)%cliquesize][0]
        Graph.remove_edge(last_node,first_node)
        Graph.add_edge(last_node,next_first_node)
    # divide the Graph in two sets that are only connected by 2 edges
    S = set(range(math.floor(cliquesize/2)*cliquesize))
    T = set(Graph.nodes())- S
    return Graph, S, T


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

        
        if len(old_edges) != 3:
            continue
        if len(new_edges) != 3:
            continue

        # has a successful flip been found? I not: continue searching
        is_in_graph = False
        for edge in new_edges:
            if Graph.has_edge(*edge) and edge not in old_edges:
                is_in_graph  = True
                break

        if is_in_graph:
            continue
        
        break

    new_Graph = Graph.copy()
    new_Graph.remove_edges_from(old_edges)
    new_Graph.add_edges_from(new_edges)

    return new_Graph

Graph, S, T = create_ring_of_cliques(3)
print("#### Create a Ring of 3-Cliques and check the edgeflip function")
print("Edges before flip:")
print(Graph.edges)
flipped_Graph = flip_edge(Graph)
print("Edges after flip:")
print(flipped_Graph.edges)



def cut_size(S:set, T:set, Graph: networkx.Graph)-> int:
    outgoing = []
    # Calculate the cut size by checking which edges go from S to V. The number of incoming edges is equal to the number of
    # outgoing edges so i only calculate the outgoing edges
    for u, v in Graph.edges():
        if u in S and v in T:
            outgoing.append((u, v))
    return len(outgoing)

print("##### Test the cut size and cut strain functions on the original graph and the flipped graph")
print("The Set S:")
print(S)
print("Cut size original:")
print(cut_size(S,T,Graph))
print("Cut size flipped:")
print(cut_size(S,T,flipped_Graph))



def cut_strain(S:set, T:set, Graph: networkx.Graph)-> float:
    cut_strain = 0
    for node in Graph.nodes:
        neighbours_in_S = 0
        neighbours_in_T = 0
        for u,v in Graph.edges:
            if u == node:
                if v in S:
                    neighbours_in_S += 1
                else:
                    neighbours_in_T += 1
        all_neighbours = neighbours_in_S + neighbours_in_T
        cut_strain += ((neighbours_in_S/all_neighbours)*(neighbours_in_T/all_neighbours))
    return cut_strain

print("Cut strain original:")
print(cut_strain(S,T,Graph))
print("Cut strain flipped:")
print(cut_strain(S,T,flipped_Graph))



def flip_chain_simulation(Graph: networkx.Graph, S, T , rounds: int):
    # the lists of size and strain shall document the change over time during the rounds. they are equivilent to the data points
    # that i want to visualize in a graphic picture later
    cut_sizes = []
    cut_strains = []
    current_Graph = Graph
    for i in range(1,rounds):
        current_Graph = flip_edge(current_Graph)
        # for big roundnumbers, only every 10th average is added to the list to shorten the listlength and reduce the number of
        # datapoints 
        if rounds > 100:
            if i%10 == 0:
                cut_sizes.append(cut_size(S,T,current_Graph))
                cut_strains.append(cut_strain(S,T,current_Graph))
        else:
            cut_sizes.append(cut_size(S,T,current_Graph))
            cut_strains.append(cut_strain(S,T,current_Graph))
    
    return (cut_sizes,cut_strains)

def average_over_30_simulations(Graph, S, T, rounds):

    avg_sizes = []
    avg_strains = []

    for i in range(30):
        sizes, strains = flip_chain_simulation(Graph, S, T, rounds)
        if i == 0:
            avg_sizes = sizes.copy()
            avg_strains = strains.copy()
        else:
            for j in range(len(sizes)):
                avg_sizes[j] += sizes[j]
            for j in range(len(strains)):
                avg_strains[j] += strains[j]

    for j in range(len(avg_sizes)):
        avg_sizes[j] /= 30
    for j in range(len(avg_strains)):
        avg_strains[j] /= 30

    return avg_sizes, avg_strains

Graph2, S, T = create_ring_of_cliques(7)

Size, Strain = average_over_30_simulations(Graph2,S , T,1000)
print("\n ####Check on Cut Size and Cut Strain of a 7-Ring-of-cliques over 1000 runs")
print(Size)
print(Strain)
