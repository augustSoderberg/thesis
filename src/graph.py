import yaml

class Graph:
    def __init__(self, manifest):
        self.adj_matrix = self.read_graph_from_manifest(manifest)
        if not self.is_fully_connected():
            raise ValueError("Graph is not connected. "
                            "Please edit 'manifest.yml")
        self.routes = self.calculate_all_shortest_paths()

    def read_graph_from_manifest(self, manifest):
        try:
            yaml_graph = manifest["graph"]
        except KeyError as e:
            raise KeyError("Please define the graph structure in 'manifest.yml'. "
                            "See 'example_manifest.yml' for formatting") from e
        adj_matrix = []
        for i, weights in enumerate(yaml_graph):
            if i == 0: 
                adj_matrix = [[0] * len(weights) for _ in range(len(weights))]
            if not len(weights) == len(adj_matrix):
                raise ValueError("Please make all edge weight lists the same length in 'manifest.yml. "
                                "See 'example_manifest.yml' for formatting")
            for j, weight in enumerate(weights):
                if j > i:
                    adj_matrix[i][j] = weight
                    adj_matrix[j][i] = weight
        return adj_matrix
    
    def is_fully_connected(self):
        visited = [False] * len(self.adj_matrix)
        visited = self.depth_first_search(visited, 0)
        for seen in visited:
            if not seen:
                return False
        return True
        
    def depth_first_search(self, visited, curr_node):
        for i, weight in enumerate(self.adj_matrix[curr_node]):
            if weight >= 0 and not visited[i]:
                visited[i] = True
                visited = self.depth_first_search(visited, i)
        return visited

    def calculate_all_shortest_paths(self):
        