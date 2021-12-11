from graph import Graph
import yaml

if __name__ == '__main__':
    with open("manifest.yml", "r") as stream:
        manifest = yaml.safe_load(stream)
    graph = Graph(manifest)