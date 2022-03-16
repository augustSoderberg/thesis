from map import Map
from agents_controller import AgentsController
import yaml

MIN_CHARGE_THRESHOLD_PERCENTAGE = 0.3
class ParamDispatchers:
    
    def __init__(charge)

    def choose_agent_for_task(agents_data):
        return min(agents_data, key = lambda x: x[1])[0]

    def handle_charging_decision(charger_data, charge_percentage):
        closest_charger = -1
        range_left = 0
        highest_spawning_prob = -1
        prob = 0
        for node in charger_data:
            if node[1] >= range_left and node[2]:
                closest_charger = node[0]
                range_left = node[1]
            if node[3] >= prob:
                highest_spawning_prob = node[0]
                prob = node[3]
        if charge_percentage > MIN_CHARGE_THRESHOLD_PERCENTAGE:
            return highest_spawning_prob
        else:
            return closest_charger

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
                    