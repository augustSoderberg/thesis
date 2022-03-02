from graph_environment import GraphEnvironment
from tensorforce.agents import ProximalPolicyOptimization
from tensorforce import Environment, Agent
from map import Map
from agents_controller import AgentsController
import yaml

MIN_CHARGE_THRESHOLD_PERCENTAGE = 0.3

def handle_charging_decision(charger_data, charge_percentage):
    if charge_percentage > MIN_CHARGE_THRESHOLD_PERCENTAGE:
        return -1
    else:
        return charger_data[min(charger_data)]

def choose_vehicle_to_dispatch(dispatcher, states, episode_states, internals, episode_internals):
    all_states = [-1]*4
    for state in states:
        all_states[state["id"]] = state["dist_to_start"]
    episode_states.append(all_states)
    episode_internals.append(internals)
    weights, internals = dispatcher.act(states=all_states, internals = internals, independent=True)
    return weights, internals, max(states, key=lambda x: weights[x["id"]])["id"]

def train(manifest, dispatcher):
    waiting_times = []
    for episode in range(3000):
        episode_states = list()
        episode_internals = list()
        episode_actions = list()
        episode_terminal = list()
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
            internals = dispatcher.initial_internals()
            terminal = False
            for i, candidate in enumerate(candidates):
                if len(candidate) > 0:
                    agents_data = [agents_controller.get_agent_data_for_task(i, agent) for agent in candidate]
                    actions, internals, response = choose_vehicle_to_dispatch(dispatcher, agents_data, episode_states, internals, episode_internals)
                    episode_actions.append(actions)
                    agents_controller.ack_task(response, i, time)
                    episode_terminal.append(terminal)
                else:
                    agents_controller.handle_not_enough_agents()
            for id in agents_controller.agents_to_dispatch:
                candidates = agents_controller.get_charging_prompts(id)
                if candidates is not None:
                    response = handle_charging_decision(candidates, agents_controller.agents[id].range / agents_controller.agents[id].max_range)
                    agents_controller.ack_charger(response, time, id)
        episode_reward = [-1*agents_controller.get_total_waiting_time(total_runtime)] * len(episode_terminal)
        if episode % 40 == 0:
            waiting_times.append(agents_controller.get_total_waiting_time(total_runtime))
        episode_terminal[-1] = True
        dispatcher.experience(states=episode_states, internals=episode_internals, actions=episode_actions, terminal=episode_terminal, reward=episode_reward)
        dispatcher.update()
    print(waiting_times)    


if __name__ == '__main__':
    with open("manifest.yml", "r") as stream:
        manifest = yaml.safe_load(stream)
    dispatcher = Agent.create(agent='ppo', max_episode_timesteps=manifest["total_runtime"], batch_size=1, states=dict(type='float', shape=(4,)), actions=dict(type='float', shape=(4,)))
    train(manifest, dispatcher)