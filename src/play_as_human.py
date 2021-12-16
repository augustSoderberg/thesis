from map import Map
from agents_controller import AgentsController
import yaml

if __name__ == '__main__':
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
        for agent in agents_controller.agents:
            print("TIME:", time, "ID:", agent.id, "Loc:", agent.location, "Batt:", agent.range)
        new_tasks = map.spawn_cargo()
        prompts, candidates = agents_controller.tick(time, new_tasks)
        not_enough_agents = False
        for i, (prompt, candidate) in enumerate(zip(prompts, candidates)):
            if len(candidate) > 0:
                response = input(prompt.format(candidate))
                valid, message = agents_controller.ack_task(response, i, time)
                while not valid:
                    response = input(message.format(candidate))
                    valid, message = agents_controller.ack_task(response, i, time)
            else:
                not_enough_agents = True
                agents_controller.handle_not_enough_agents()
        if not_enough_agents and len(agents_controller.agents_to_dispatch) > 0:
            print("You have pending tasks without any agents of sufficient charge",
            "Please consider charging one of the following agents.")
        for id in agents_controller.agents_to_dispatch:
            prompt = agents_controller.get_charging_prompts(id)
            if prompt is not None:
                response = input(prompt)
                valid, message = agents_controller.ack_charger(response, time, id)
                while not valid:
                    response = input(message)
                    valid, message = agents_controller.ack_charger(response, time, id)
    print(agents_controller.total_waiting_time)


