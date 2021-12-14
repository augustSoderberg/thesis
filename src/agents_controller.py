import random

class AgentsController:
    def __init__(self, map, manifest):
        self.map = map
        vehicle_settings = self.get_from_yaml(manifest, "vehicle")
        self.num_agents = self.get_from_yaml(vehicle_settings, "num_vehicles")
        if self.num_agents <= 0:
            raise ValueError("Please specify a number of vehicles greater than 0. "
                        "See 'example_manifest.yml' for formatting.")
        self.battery_capacity = self.get_from_yaml(vehicle_settings, "battery_capacity")
        self.time_to_full_charge = self.get_from_yaml(vehicle_settings, "time_for_complete_charge")
        self.vehicle_speed = self.get_from_yaml(vehicle_settings, "vehicle_speed")
        self.agents = self.spawn_agents()
    
    def spawn_agents(self):
        agents = []
        for i in range(self.num_agents):
            agents.append(Agent(i, random.randrange(0, self.map.num_nodes), self.battery_capacity))
        return agents
            
    def get_from_yaml(self, manifest_dict, key):
        try:
            return manifest_dict[key]
        except KeyError as e:
            raise KeyError("Please define \"{}\" in \"manifest.yml\". \
                See \"example_manifest.yml\" for formatting".format(key)) from e
    
class Agent:
    def __init__(self, id, location, max_range):
        self.id = id
        self.location = location
        self.range = max_range
        self.available = True
        self.charging = False