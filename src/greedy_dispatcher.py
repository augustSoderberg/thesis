from map import Map
from agents_controller import AgentsController
from statistics import mean
import yaml

# Minimum charge percentage of a vehicle before it is sent to go charge
MIN_CHARGE_THRESHOLD_PERCENTAGE = 0.2
SIMULATION_ITERATIONS = 150

# Selects the closest agent
def pre_task_decision(agents_data):
    return min(agents_data, key = lambda x: x[1])[0]

# Leaves vehicles where they are unless they need to go charge
def post_task_decision(charger_data, charge_percentage):

    closest_charger = -1
    range_left = 0

    for node in charger_data:
        if node[1] >= range_left and node[2]:
            closest_charger = node[0]
            range_left = node[1]

    if charge_percentage > MIN_CHARGE_THRESHOLD_PERCENTAGE:
        return -1
    else:
        return closest_charger

if __name__ == '__main__':
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
                    response = post_task_decision(candidates, agents_controller.agents[id].range / agents_controller.agents[id].max_range)
                    agents_controller.ack_charger(response, time, id)

        times.append(agents_controller.get_total_waiting_time(total_runtime))
    print("Total task waiting time for each iteration:", times)
                    