from map import Map
from agents_controller import AgentsController
import yaml

if __name__ == '__main__':
    with open("manifest.yml", "r") as stream:
        manifest = yaml.safe_load(stream)
    map = Map(manifest)
    agents_controller = AgentsController(map, manifest)
