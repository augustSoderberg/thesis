from tensorforce import Agent
from map import Map
from agents_controller import AgentsController
import yaml

SIMULATION_ITERATIONS = 150

# Number of iterations before the value is output
PRINT_FREQUENCY = 10

def post_task_decision(post_task, charger_data):
    all_states = [[0, 0, 0]]*20
    for data in charger_data:
        all_states[data[0]] = data[1:3] + data[4:]
    weights = post_task.act(states=all_states, independent=True)
    return max(charger_data, key=lambda x: weights[x[0]])[0]

def pre_task_decision(dispatcher, states):
    all_states = [[-1, -1, 0, 0, 0]]*8
    for state in states:
        all_states[state[0]] = state[1:]
    weights = dispatcher.act(states=all_states, independent=True)
    return max(states, key=lambda x: weights[x[0]])[0]

def test(manifest, pre_task_dispatcher, post_task_dispatcher):
    waiting_times = []
    for episode in range(SIMULATION_ITERATIONS):

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
                    response = pre_task_decision(pre_task_dispatcher, agents_data)
                    agents_controller.ack_task(response, i, time)
                else:
                    agents_controller.handle_not_enough_agents()

            for id in agents_controller.agents_to_dispatch:
                candidates = agents_controller.get_charging_prompts(id)
                if candidates is not None:
                    response = post_task_decision(post_task_dispatcher, candidates)
                    agents_controller.ack_charger(response, time, id)

        if episode % PRINT_FREQUENCY == 0:
            waiting_times.append(agents_controller.get_total_waiting_time(total_runtime))

    print("Total task waiting time for each iteration:", waiting_times)    


if __name__ == '__main__':
    with open("manifest.yml", "r") as stream:
        manifest = yaml.safe_load(stream)
    pre_task_dispatcher = Agent.load(directory="models_pre", filename='agent-2')
    post_task_dispatcher = Agent.load(directory="models_post", filename='agent-2')
    test(manifest, pre_task_dispatcher, post_task_dispatcher)