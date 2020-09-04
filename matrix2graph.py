# drug-drug = (1519, 1519)
# drug-protein = (1519, 1025)
# drug-side effect = (1519, 12904)
# drug-sim BP net = (1519, 1519)
# drug-sim CC net = (1519, 1519)
# drug-sim Chemical net = (1519, 1519)
# drug-sim Meta net = (1519, 1519)
# drug-sim MF net = (1519, 1519)
# drug-sim Therapeutic net = (1519, 1519)
# drug-sim Wm net = (1519, 1519)

import numpy as np
import networkx as nx


def load_dict(path):
    list = []
    with open(path, 'r') as fin:
        tmp = fin.read().splitlines()
        for line in tmp:
            list.append(line.split(':'))
    return np.array(list)


def load_matrix(path):
    list = []
    with open(path, 'r') as fin:
        tmp = fin.read().splitlines()
        for line in tmp:
            list.append(line.split('\t'))
    return np.array(list, dtype=float)


def matrix2graph(matrix, dict1=None, dict2=None, dict2_type=None):
    # Build the graph with node no labeled
    if dict1 is None:
        graph = nx.convert_matrix.from_numpy_matrix(matrix)
        return graph

    # Build the graph with labeled node
    graph = nx.Graph()
    if dict2 is None:
        graph.add_nodes_from(dict1, type='drug')
        for i in range(0, matrix.shape[0]):
            for j in range(0, matrix.shape[1]):
                if matrix[i, j] != 0:
                    graph.add_edge(dict1[i], dict1[j], weight=matrix[i, j])
        return graph

    graph.add_nodes_from(dict1, type='drug')
    graph.add_nodes_from(dict2, type=dict2_type)
    for i in range(0, matrix.shape[0]):
        for j in range(0, matrix.shape[1]):
            if matrix[i, j] != 0:
                graph.add_edge(dict1[i], dict2[j], weight=matrix[i, j])
    return graph


# Load the dictionaries
path = './dataset/drug_dict'
drugs = load_dict(path)
path = './dataset/disease_dict'
disease = load_dict(path)
path = './dataset/protein_dict'
protein = load_dict(path)
path = './dataset/se_dict'
se = load_dict(path)

# Build the graphs and save them
path = './dataset/drugNets/drugdrug'
print('BUILD GRAPH: ', path)
matrix = load_matrix(path + '.txt')
graph = matrix2graph(matrix=matrix, dict1=drugs[:, 0])
nx.write_graphml(graph, path + '.graphml')

path = './dataset/drugNets/drugProtein'
print('BUILD GRAPH: ', path)
matrix = load_matrix(path + '.txt')
graph = matrix2graph(matrix=matrix, dict1=drugs[:, 0], dict2=protein[:, 0], dict2_type='protein')
nx.write_graphml(graph, path + '.graphml')

path = './dataset/drugNets/drugsideEffect'
print('BUILD GRAPH: ', path)
matrix = load_matrix(path + '.txt')
graph = matrix2graph(matrix=matrix, dict1=drugs[:, 0], dict2=se[:, 0], dict2_type='side effect')
nx.write_graphml(graph, path + '.graphml')

path = './dataset/drugNets/drugsimBPnet'
print('BUILD GRAPH: ', path)
matrix = load_matrix(path + '.txt')
graph = matrix2graph(matrix=matrix, dict1=drugs[:, 0])
nx.write_graphml(graph, path + '.graphml')

path = './dataset/drugNets/drugsimCCnet'
print('BUILD GRAPH: ', path)
matrix = load_matrix(path + '.txt')
graph = matrix2graph(matrix=matrix, dict1=drugs[:, 0])
nx.write_graphml(graph, path + '.graphml')

path = './dataset/drugNets/drugsimChemicalnet'
print('BUILD GRAPH: ', path)
matrix = load_matrix(path + '.txt')
graph = matrix2graph(matrix=matrix, dict1=drugs[:, 0])
nx.write_graphml(graph, path + '.graphml')

path = './dataset/drugNets/drugsimMetanet'
print('BUILD GRAPH: ', path)
matrix = load_matrix(path + '.txt')
graph = matrix2graph(matrix=matrix, dict1=drugs[:, 0])
nx.write_graphml(graph, path + '.graphml')

path = './dataset/drugNets/drugsimMFnet'
print('BUILD GRAPH: ', path)
matrix = load_matrix(path + '.txt')
graph = matrix2graph(matrix=matrix, dict1=drugs[:, 0])
nx.write_graphml(graph, path + '.graphml')

path = './dataset/drugNets/drugsimTherapeuticnet'
print('BUILD GRAPH: ', path)
matrix = load_matrix(path + '.txt')
graph = matrix2graph(matrix=matrix, dict1=drugs[:, 0])
nx.write_graphml(graph, path + '.graphml')

path = './dataset/drugNets/drugsimWmnet'
print('BUILD GRAPH: ', path)
matrix = load_matrix(path + '.txt')
graph = matrix2graph(matrix=matrix, dict1=drugs[:, 0])
nx.write_graphml(graph, path + '.graphml')