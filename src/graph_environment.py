from agents_controller import AgentsController
from map import Map
from tensorforce.environments import Environment
import yaml

class GraphEnvironment(Environment):
    def __init__(self):
        super().__init__()
        with open("manifest.yml", "r") as stream:
            manifest = yaml.safe_load(stream)
        self.map = Map(manifest)
        self.agents_controller = AgentsController(map, manifest)
        self.total_runtime = self.map.get_from_yaml(manifest, 'total_runtime')

    def max_episode_timesteps(self):
        return self.total_runtime

    def close(self):
        super().close()

    def reset(self):
        self.map = Map(manifest)
        self.agents_controller = AgentsController(map, manifest)
        new_tasks = map.spawn_cargo()
        prompts, candidates = agents_controller.tick(time, new_tasks)

    def execute(self, actions):
        next_state = 0
        terminal = False
        reward = 0
        return next_state, terminal, reward