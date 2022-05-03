from map import Map
from agents_controller import AgentsController
import csv
import numpy as np
from scipy import optimize
import yaml

SIMULATION_ITERATIONS = 150

# Selects the closest agent
def pre_task_decision(agents_data):
    return min(agents_data, key = lambda x: x[1])[0]

def post_task_decision(charger_data, post_task_weights):
    bids = {}
    for node_data in charger_data:
        bids[node_data[0]] = np.dot(np.asarray(node_data[1:]), np.asarray(post_task_weights))
    return max(bids.items(), key=lambda x: x[1])[0]

# Optimization function
def func(weights):
    times = []
    for episode in range(SIMULATION_ITERATIONS):

        with open("manifest.yml", "r") as stream:
            manifest = yaml.safe_load(stream)

        map = Map(manifest)
        agents_controller = AgentsController(map, manifest)

        try:
            total_runtime = manifest['total_runtime']
        except KeyError as e:
            raise KeyError("Please define 'total_runtime' in 'manifest.yml'. "
                        "See 'example_manifest.yml' for formatting.") from e

        for time in range(total_runtime):

            new_tasks = map.spawn_cargo()
            _, candidates = agents_controller.tick(time, new_tasks)

            for i, candidate in enumerate(candidates):
                if len(candidate) > 0:
                    agents_data = [agents_controller.get_agent_data_for_task(i, agent) for agent in candidate]
                    response = pre_task_decision(agents_data)
                    agents_controller.ack_task(response, i, time)
                else:
                    agents_controller.handle_not_enough_agents()

            for id in agents_controller.agents_to_dispatch:
                candidates = agents_controller.get_charging_prompts(id)
                if candidates is not None:
                    response = post_task_decision(candidates, weights)
                    agents_controller.ack_charger(response, time, id)

        times.append(agents_controller.get_total_waiting_time(total_runtime))
    return times
                    
def run_optimization():
    # Searchable area
    ranges = (slice(0, 1, 0.1), slice(0, 1, 0.1), slice(0, 1, 0.1), slice(-1, 0, 0.1))
    resbrute = optimize.brute(func, ranges, full_output=True, workers=-1)
    return resbrute[0]

def test(weights):
    print("Total task waiting time for each iteration:", func(weights))
    
if __name__ == '__main__':
    weights = run_optimization()
    test(weights)