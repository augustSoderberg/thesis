from map import Map
from agents_controller import AgentsController
import graphviz, yaml

# This creates and displays the graphviz graph
def create_graph(complete_map):
    dot = graphviz.Graph("Map")
    for i in range(len(complete_map.adj_matrix)):
        color = 'grey'
        if complete_map.is_charging_node[i]:
            color = 'green'
        dot.node("{}".format(i), "Node: {}\nP: {}".format(i, complete_map.cargo_spawning_rates[i]), color='{}'.format(color))
    for i, node in enumerate(complete_map.adj_matrix):
        for j, weight in enumerate(node):
            if j > i and weight > 0:
                dot.edge("{}".format(i), "{}".format(j), label="{}".format(weight))
    dot.format = 'svg'
    dot.render(directory='doctest-output', view=True)

if __name__ == '__main__':
    with open("manifest.yml", "r") as stream:
        manifest = yaml.safe_load(stream)
    map = Map(manifest)
    create_graph(map)
    agents_controller = AgentsController(map, manifest)
    try:
        total_runtime = manifest['total_runtime']
    except KeyError as e:
        raise KeyError("Please define 'total_runtime' in 'manifest.yml'. "
                    "See 'example_manifest.yml' for formatting.") from e
    for time in range(total_runtime):
        print("\nCurrent time: {} seconds out of {}.".format(time, total_runtime))
        new_tasks = map.spawn_cargo()
        prompts, candidates = agents_controller.tick(time, new_tasks)
        not_enough_agents = False
        for i, (prompt, candidate) in enumerate(zip(prompts, candidates)):
            if len(candidate) > 0:
                for agent in candidate:
                    print(agents_controller.get_agent_data_for_task(i, agent))
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
    print("The total amount of time tasks waited was {} seconds".format(agents_controller.get_total_waiting_time(total_runtime)))


