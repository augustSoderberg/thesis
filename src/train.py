from graph_environment import GraphEnvironment
from tensorforce.agents import Agent, ActorCritic
from tensorforce import Environment

def train():
    environment = Environment.create(environment=GraphEnvironment)
    task_dispatcher = ActorCritic.create(environment=environment, states=dict(type='float', shape=(environment.num_agents, 5)))
    node_dispatcher = ActorCritic.create(environment=environment, states=dict(type='int', shape=(environment.num_agents, environment.map.num_nodes)))
    for _ in range(100):
        states = environment.reset()
        terminal = False
        while not terminal:
            actions = agent.act(states=states)
            states, terminal,reward = environment.execute(actions=actions)
            agent.observe(terminal=terminal, reward=reward)
    


if __name__ == '__main__':
    train()