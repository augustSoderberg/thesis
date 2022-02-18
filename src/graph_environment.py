from agents_controller import AgentsController
from map import Map
from tensorforce.environments import Environment
import yaml

class GraphEnvironment(Environment):
    def __init__(self, manifest):
        super().__init__()
        with open("manifest.yml", "r") as stream:
            manifest = yaml.safe_load(stream)
        self.map = Map(manifest)
        self.agents_controller = AgentsController(self.map, manifest)
        self.total_runtime = self.map.get_from_yaml(manifest, 'total_runtime')

    def max_episode_timesteps(self):
        return self.total_runtime

    def states(self):
        return dict(type='float', shape=(4,))

    def actions(self):
        return dict(type='int', num_values=2)

    def close(self):
        super().close()

    def reset(self, manifest):
        self.map = Map(manifest)
        self.agents_controller = AgentsController(self.map, manifest)
        new_tasks = self.map.spawn_cargo()
        # prompts, candidates = self.agents_controller.tick(time, new_tasks)
        return [0, 0, 1, 1]

    def execute(self, actions):
        next_state = [0, 1, 1, 0]
        terminal = False
        reward = 0
        return next_state, terminal, reward