import networkx
import random

def create_ring_of_cliques(cliquesize:int)-> networkx.Graph:
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
    
    return Graph


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

        if (node1 == node3 or node2 == node4 or node3 == node4):
            continue


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


def cut(Graph:networkx.Graph):
    S = set()
    T = set()
    for node in Graph.nodes():
        if random.random() < 0.5:
            S.add(node)
        else:
            T.add(node)
    return S,T

def cut_size(S:set, T:set, Graph: networkx.Graph)-> int:
    outgoing = []
    # Calculate the cut size by checking which edges go from S to V. The number of incoming edges is equal to the number of
    # outgoing edges so i only calculate the outgoing edges
    for u, v in Graph.edges():
        if u in S and v in T:
            outgoing.append((u, v))
    return len(outgoing)

def cut_strain(S:set, T:set, Graph: networkx.Graph)-> int:
    
    cut_strain = 0
    for node in Graph.nodes:
        neighbours_in_S = 0
        neighbours_in_T = 0
        for u,v in Graph.edges:
            if v in S:
                neighbours_in_S += 1
            else:
                neighbours_in_T += 1
        # Calculate the partial sum. Correct?
        cut_strain += ((neighbours_in_S/Graph.number_of_nodes())*(neighbours_in_T/Graph.number_of_nodes()))
    return cut_strain



def avg_cutsize_in_30_runs(Graph: networkx.Graph) -> int:
    sum = 0
    for i in range(0,29):
        current_Graph = flip_edge(Graph)
        S,T = cut(current_Graph)
        sum += cut_size(S,T,current_Graph)
    result = round((sum/30), 4)
    return result

def avg_cutstrain_in_30_runs(Graph: networkx.Graph) -> int:
    sum = 0
    for i in range(0,29):
        current_Graph = flip_edge(Graph)
        S,T = cut(current_Graph)
        sum += cut_strain(S,T,current_Graph)
    result = round((sum/30), 4)
    return result

def convergance(Graph: networkx.Graph, rounds: int)-> (list[int],list[int]):
    # the lists of size and strain shall document the change over time during the rounds. they are equivilent to the data points
    # that i want to visualize in a graphic picture later
    avg_size = []
    avg_strain = []
    current_Graph = Graph
    for i in range(1,rounds):
        current_Graph = flip_edge(current_Graph)
        # for big roundnumbers, only every 10th average is added to the list to shorten the listlength and reduce the number of
        # datapoints 
        if rounds > 100:
            if i%10 == 0:
                avg_size.append(avg_cutsize_in_30_runs(current_Graph))
                avg_strain.append(avg_cutstrain_in_30_runs(current_Graph))
        else:
            avg_size.append(avg_cutsize_in_30_runs(current_Graph))
            avg_strain.append(avg_cutstrain_in_30_runs(current_Graph))
    
    return (avg_size,avg_strain)


Graph = create_ring_of_cliques(7)

Size, Strain = convergance(Graph,1000)
print(Size)
print(Strain)