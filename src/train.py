from tensorforce import Agent
from map import Map
from agents_controller import AgentsController
import yaml

TOTAL_TRAINING_ITERATIONS = 25000

# Number of iterations before the value is output
PRINT_FREQUENCY = 10

# Total waiting time which if any model achieves less than, it will be saved and training ended.
EARLY_STOP_THRESHOLD = 550


def post_task_decision(post_task, charger_data, episode_states, internals, episode_internals):
    all_states = [[0, 0, 0]]*20
    for data in charger_data:
        all_states[data[0]] = data[1:3] + data[4:]
    episode_states.append(all_states)
    episode_internals.append(internals)
    weights, internals = post_task.act(states=all_states, internals = internals, independent=True)
    return weights, internals, max(charger_data, key=lambda x: weights[x[0]])[0]

def pre_task_decision(dispatcher, states, episode_states, internals, episode_internals):
    all_states = [[-1, -1, 0, 0, 0]]*8
    for state in states:
        all_states[state[0]] = state[1:]
    episode_states.append(all_states)
    episode_internals.append(internals)
    weights, internals = dispatcher.act(states=all_states, internals = internals, independent=True)
    return weights, internals, max(states, key=lambda x: weights[x[0]])[0]

def train(manifest, pre_task_dispatcher, post_task_dispatcher):
    waiting_times = []
    for episode in range(TOTAL_TRAINING_ITERATIONS):

        pre_task_episode_states = list()
        pre_task_episode_internals = list()
        pre_task_episode_actions = list()
        pre_task_episode_terminal = list()

        post_task_episode_states = list()
        post_task_episode_internals = list()
        post_task_episode_actions = list()
        post_task_episode_terminal = list()

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

            internals = pre_task_dispatcher.initial_internals()
            post_internals = post_task_dispatcher.initial_internals()
            terminal = False

            for i, candidate in enumerate(candidates):
                if len(candidate) > 0:
                    agents_data = [agents_controller.get_agent_data_for_task(i, agent) for agent in candidate]
                    actions, internals, response = pre_task_decision(pre_task_dispatcher, agents_data, pre_task_episode_states, internals, pre_task_episode_internals)
                    pre_task_episode_actions.append(actions)
                    pre_task_episode_terminal.append(terminal)
                    agents_controller.ack_task(response, i, time)
                else:
                    agents_controller.handle_not_enough_agents()

            for id in agents_controller.agents_to_dispatch:
                candidates = agents_controller.get_charging_prompts(id)
                if candidates is not None:
                    post_actions, post_internals, response = post_task_decision(post_task_dispatcher, candidates, post_task_episode_states, post_internals, post_task_episode_internals)
                    post_task_episode_actions.append(post_actions)
                    post_task_episode_terminal.append(terminal)
                    agents_controller.ack_charger(response, time, id)

        episode_reward = [len(pre_task_episode_terminal)/agents_controller.get_total_waiting_time(total_runtime)] * len(pre_task_episode_terminal)
        post_episode_reward = [len(post_task_episode_terminal)/agents_controller.get_total_waiting_time(total_runtime)] * len(post_task_episode_terminal)

        if episode % PRINT_FREQUENCY == 0:
            waiting_times.append(agents_controller.get_total_waiting_time(total_runtime))
            print(waiting_times[-1])

        # For early stopping
        if waiting_times[-1] < EARLY_STOP_THRESHOLD:
            post_task_dispatcher.save("models_post")
            pre_task_dispatcher.save("models_pre")
            quit()

        pre_task_episode_terminal[-1] = True
        post_task_episode_terminal[-1] = True

        pre_task_dispatcher.experience(states=pre_task_episode_states, internals=pre_task_episode_internals, actions=pre_task_episode_actions, terminal=pre_task_episode_terminal, reward=episode_reward)
        post_task_dispatcher.experience(states=post_task_episode_states, internals=post_task_episode_internals, actions=post_task_episode_actions, terminal=post_task_episode_terminal, reward=post_episode_reward)
        pre_task_dispatcher.update()
        post_task_dispatcher.update()
    
    post_task_dispatcher.save("models_post")
    pre_task_dispatcher.save("models_pre")

    print("Total task waiting time for each iteration:", waiting_times)    


if __name__ == '__main__':
    with open("manifest.yml", "r") as stream:
        manifest = yaml.safe_load(stream)
    pre_task_dispatcher = Agent.create(agent='ppo', max_episode_timesteps=manifest["total_runtime"], batch_size=1, states=dict(type='float', shape=(8,5)), actions=dict(type='float', shape=(8,)), learning_rate=0.01)
    post_task_dispatcher = Agent.create(agent='ppo', max_episode_timesteps=manifest["total_runtime"], batch_size=1, states=dict(type='float', shape=(20,3)), actions=dict(type='float', shape=(20,)), learning_rate=0.01)
    train(manifest, pre_task_dispatcher, post_task_dispatcher)