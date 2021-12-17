from priority_queue import PriorityQueue
import random, yaml

# If you choose to randomly create the task spawning probabilities--
# this is the total probability of a task to spawn any given second.
CARGO_SPAWNING_CONST = 0.003

# This is the entire map the agents and tasks are operating on.
class Map:
    def __init__(self, manifest):
        self.create_graph(manifest)
        self.routes = self.calculate_all_shortest_paths()
        self.relative_spawning_probs = self.calculate_relative_spawning_probability()

    def create_graph(self, manifest):
        yaml_graph = self.get_from_yaml(manifest, "map")
        self.create_edges(yaml_graph)
        self.num_nodes = len(self.adj_matrix)
        self.create_chargers(yaml_graph)
        self.create_cargo_spawners(yaml_graph)
    
    def create_cargo_spawners(self, yaml_graph):
        if self.get_from_yaml(yaml_graph, "randomize_cargo_spawn_probability"):
            self.cargo_spawning_rates = [0] * self.num_nodes
            cargo_spawning_factor = CARGO_SPAWNING_CONST / self.num_nodes
            created_spawning_probability = 0
            while created_spawning_probability < CARGO_SPAWNING_CONST:
                node = random.randrange(0, self.num_nodes)
                self.cargo_spawning_rates[node] += cargo_spawning_factor
                created_spawning_probability += cargo_spawning_factor
        else:
            self.cargo_spawning_rates = self.get_from_yaml(yaml_graph, "cargo_spawn_probability")

    #This is a factor for each node based on how likely it is for tasks to spawn near this node.
    def calculate_relative_spawning_probability(self):
        longest_path = max(self.routes.values(), key=lambda x:x[1])[1]
        relative_spawning_probs = [0] * self.num_nodes
        for (i ,j), (_, dist) in self.routes.items():
            relative_spawning_probs[i] += (1 - (dist / longest_path)) * self.cargo_spawning_rates[j]
        return relative_spawning_probs

    def create_chargers(self, yaml_graph):
        randomize_chargers = self.get_from_yaml(yaml_graph, "randomize_chargers")
        self.is_charging_node = [False] * self.num_nodes
        if randomize_chargers:
            num_chargers = self.get_from_yaml(yaml_graph, "number_of_random_chargers")
            if num_chargers > self.num_nodes:
                raise ValueError("Please make the number of charger nodes less in 'manifest.yml. "
                                "Cannot exceed the number of nodes")
            created_chargers = 0
            while created_chargers < num_chargers:
                node_candidate = random.randrange(0, self.num_nodes)
                if not self.is_charging_node[node_candidate]:
                    self.is_charging_node[node_candidate] = True
                    created_chargers += 1
        else:
            for node in self.get_from_yaml(yaml_graph, "charger_nodes"):
                try:
                    self.is_charging_node[node] = True
                except IndexError as e:
                    raise IndexError("Please made charging node indices valid. "
                            "See 'example_manifest.yml' for formatting") from e

    def create_edges(self, yaml_graph):
        yaml_edge_weights = self.get_from_yaml(yaml_graph, "edge_weights")
        adj_matrix = []
        for i, weights in enumerate(yaml_edge_weights):
            if i == 0: 
                adj_matrix = [[0] * len(weights) for _ in range(len(weights))]
            if not len(weights) == len(adj_matrix):
                raise ValueError("Please make all edge weight lists the same length in 'manifest.yml. "
                                "See 'example_manifest.yml' for formatting")
            for j, weight in enumerate(weights):
                if j > i:
                    adj_matrix[i][j] = weight
                    adj_matrix[j][i] = weight
        self.adj_matrix = adj_matrix
        if len(self.adj_matrix) <= 1:
            raise ValueError("Please define 2 or more nodes in 'manifest.yml. "
                                "See 'example_manifest.yml' for formatting")
        if not self.is_fully_connected():
            raise ValueError("Graph is not connected. Please edit 'manifest.yml")
    
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
        paths = {}
        for i in range(self.num_nodes):
            for j in range(self.num_nodes):
                if i == j:
                    paths[(i, j)] = ([], 0)
                elif not paths.__contains__((i, j)):
                    paths[(i, j)] = self.run_dijkstra(i, j)
                    paths[(j, i)] = paths[(i, j)]
        return paths        
    
    def run_dijkstra(self, i, j):
        prev_node = [-1] * self.num_nodes
        visited = [False] * self.num_nodes
        min_queue = PriorityQueue(self.num_nodes)
        curr_node = (i, 0)
        while curr_node is not None and not visited[j]:
            node, priority = curr_node
            for k, weight in enumerate(self.adj_matrix[node]):
                if k is not node and weight >= 0 and not visited[k]:
                    should_update_prev = min_queue.push(k, weight + priority)
                    if should_update_prev:
                        prev_node[k] = node
            visited[node] = True
            curr_node = min_queue.pop()
        if visited[j]:
            path = [j]
            node = j
            while prev_node[node] != -1:
                path.insert(0, prev_node[node])
                node = prev_node[node]
            return (path, priority)
        else:
            raise ValueError("Graph is not connected. Please edit 'manifest.yml")

    def spawn_cargo(self):
        cargo_tasks = []
        for i, rate in enumerate(self.cargo_spawning_rates):
            if random.random() <= rate:
                end = random.randrange(0, self.num_nodes)
                while end == i:
                    end = random.randrange(0, self.num_nodes)
                cargo_tasks.append((i, end))
        return cargo_tasks
    
    def get_from_yaml(self, manifest_dict, key):
        try:
            return manifest_dict[key]
        except KeyError as e:
            raise KeyError("Please define \"{}\" in \"manifest.yml\". \
                See \"example_manifest.yml\" for formatting".format(key)) from e