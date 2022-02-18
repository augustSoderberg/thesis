from graph_environment import GraphEnvironment
from tensorforce.agents import ProximalPolicyOptimization
from tensorforce import Environment, Agent
from map import Map
from agents_controller import AgentsController
import yaml

MIN_CHARGE_THRESHOLD_PERCENTAGE = 0.5

def handle_charging_decision(charger_data, charge_percentage):
    if charge_percentage > MIN_CHARGE_THRESHOLD_PERCENTAGE:
        return -1
    else:
        return charger_data[min(charger_data)]

def choose_vehicle_to_dispatch(dispatcher, states, not_final=True):
    all_states = [-1]*2
    for state in states:
        all_states[state["id"]] = state["dist_to_start"]
    weights = dispatcher.act(states=all_states, independent=not_final)
    return max(states, key=lambda x: weights[x["id"]])["id"]

def train(manifest, dispatcher):
    waiting_times = []
    for _ in range(1000):
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
                    response = choose_vehicle_to_dispatch(dispatcher, agents_data)
                    agents_controller.ack_task(response, i, time)
                else:
                    agents_controller.handle_not_enough_agents()
            for id in agents_controller.agents_to_dispatch:
                candidates = agents_controller.get_charging_prompts(id)
                if candidates is not None:
                    response = handle_charging_decision(candidates, agents_controller.agents[id].range / agents_controller.agents[id].max_range)
                    agents_controller.ack_charger(response, time, id)
        waiting_times.append(agents_controller.get_total_waiting_time(total_runtime))
        choose_vehicle_to_dispatch(dispatcher, agents_data, not_final=False)
        dispatcher.observe(terminal=False, reward=-1*agents_controller.get_total_waiting_time(total_runtime))
    print(waiting_times)    


if __name__ == '__main__':
    with open("manifest.yml", "r") as stream:
        manifest = yaml.safe_load(stream)
    dispatcher = Agent.create(agent='ppo', max_episode_timesteps=manifest["total_runtime"], batch_size=1, states=dict(type='float', shape=(2,)), actions=dict(type='float', shape=(2,)))
    train(manifest, dispatcher)