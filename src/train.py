from graph_environment import GraphEnvironment
from tensorforce.agents import ProximalPolicyOptimization
from tensorforce import Environment, Agent
from map import Map
from agents_controller import AgentsController
import yaml


def handle_charging_decision(post_task, charger_data, episode_states, internals, episode_internals):
    all_states = [[0, 0, 0]]*20
    for data in charger_data:
        all_states[data[0]] = data[1:3] + data[4:]
    episode_states.append(all_states)
    episode_internals.append(internals)
    weights, internals = post_task.act(states=all_states, internals = internals, independent=True)
    return weights, internals, max(charger_data, key=lambda x: weights[x[0]])[0]

def choose_vehicle_to_dispatch(dispatcher, states, episode_states, internals, episode_internals):
    all_states = [[-1, -1, 0, 0, 0]]*8
    for state in states:
        all_states[state[0]] = state[1:]
    episode_states.append(all_states)
    episode_internals.append(internals)
    weights, internals = dispatcher.act(states=all_states, internals = internals, independent=True)
    return weights, internals, max(states, key=lambda x: weights[x[0]])[0]

def train(manifest, dispatcher, post_task):
    waiting_times = []
    for episode in range(25000):
        episode_states = list()
        episode_internals = list()
        episode_actions = list()
        episode_terminal = list()
        post_episode_states = list()
        post_episode_internals = list()
        post_episode_actions = list()
        post_episode_terminal = list()
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
            post_internals = post_task.initial_internals()
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
                    post_actions, post_internals, response = handle_charging_decision(post_task, candidates, post_episode_states, post_internals, post_episode_internals)
                    post_episode_actions.append(post_actions)
                    agents_controller.ack_charger(response, time, id)
                    post_episode_terminal.append(terminal)
        episode_reward = [len(episode_terminal)/agents_controller.get_total_waiting_time(total_runtime)] * len(episode_terminal)
        post_episode_reward = [len(post_episode_terminal)/agents_controller.get_total_waiting_time(total_runtime)] * len(post_episode_terminal)
        if episode % 1 == 0:
            waiting_times.append(agents_controller.get_total_waiting_time(total_runtime))
            # if waiting_times[-1] < 2800:
                # post_task.save("models_post")
                # dispatcher.save("models_disp")
            print(waiting_times[-1])
        episode_terminal[-1] = True
        post_episode_terminal[-1] = True
        dispatcher.experience(states=episode_states, internals=episode_internals, actions=episode_actions, terminal=episode_terminal, reward=episode_reward)
        post_task.experience(states=post_episode_states, internals=post_episode_internals, actions=post_episode_actions, terminal=post_episode_terminal, reward=post_episode_reward)
        dispatcher.update()
        post_task.update()
    print(waiting_times)    


if __name__ == '__main__':
    with open("manifest.yml", "r") as stream:
        manifest = yaml.safe_load(stream)
    # dispatcher = Agent.create(agent='ppo', max_episode_timesteps=manifest["total_runtime"], batch_size=1, states=dict(type='float', shape=(8,5)), actions=dict(type='float', shape=(8,)), learning_rate=0.01)
    # post_task = Agent.create(agent='ppo', max_episode_timesteps=manifest["total_runtime"], batch_size=1, states=dict(type='float', shape=(20,3)), actions=dict(type='float', shape=(20,)), learning_rate=0.01)
    dispatcher = Agent.load(directory="models_disp", filename='agent-28', learning_rate=0.001)
    post_task = Agent.load(directory="models_post", filename='agent-28', learning_rate=0.001)
    train(manifest, dispatcher, post_task)