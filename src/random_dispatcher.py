from map import Map
from agents_controller import AgentsController
import random
import yaml

MIN_CHARGE_THRESHOLD_PERCENTAGE = 0.3

def choose_agent_for_task(agents_data):
    return agents_data[random.randint(0, len(agents_data) - 1)][0]

def handle_charging_decision(charger_data, charge_percentage):
    return charger_data[random.randint(0, len(charger_data) - 1)][0]

if __name__ == '__main__':
    times = []
    for episode in range(150):
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
            # print("\nCurrent time: {} seconds out of {}.".format(time, total_runtime))
            new_tasks = map.spawn_cargo()
            _, candidates = agents_controller.tick(time, new_tasks)
            for i, candidate in enumerate(candidates):
                if len(candidate) > 0:
                    agents_data = [agents_controller.get_agent_data_for_task(i, agent) for agent in candidate]
                    response = choose_agent_for_task(agents_data)
                    agents_controller.ack_task(response, i, time)
                else:
                    agents_controller.handle_not_enough_agents()
            for id in agents_controller.agents_to_dispatch:
                candidates = agents_controller.get_charging_prompts(id)
                if candidates is not None:
                    response = handle_charging_decision(candidates, agents_controller.agents[id].range / agents_controller.agents[id].max_range)
                    agents_controller.ack_charger(response, time, id)
        times.append(agents_controller.get_total_waiting_time(total_runtime))
    print(times)
                    