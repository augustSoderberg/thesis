from priority_queue import PriorityQueue
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
        self.charge_per_second = self.battery_capacity / self.time_to_full_charge
        self.vehicle_speed = self.get_from_yaml(vehicle_settings, "vehicle_speed")
        self.agents = self.spawn_agents()
        self.next_awake_agent = PriorityQueue(self.num_agents)
        self.pending_tasks = []
        self.total_waiting_time = 0
    
    def spawn_agents(self):
        agents = []
        for i in range(self.num_agents):
            agents.append(Agent(i, random.randrange(0, self.map.num_nodes), self.battery_capacity, self.vehicle_speed))
        return agents

    def tick(self, time, new_tasks):
        for agent in self.agents:
            if agent.is_charging:
                agent.charge(self.charge_per_second)
        self.agents_to_dispatch = []
        while self.next_awake_agent.peek() is not None and self.next_awake_agent.peek()[1] <= time:
            agent = self.agents[self.next_awake_agent.pop()[0]]
            agent.arrive(self.map.is_charging_node)
            if not agent.is_charging:
                self.agents_to_dispatch.append(agent.id)
        self.prompts = []
        self.candidates = []
        self.new_tasks = []
        for start, end in new_tasks:
            self.pending_tasks.append((start, end, time))
            self.new_tasks.append((start, end))
            self.candidates.append([agent.id for agent in self.agents if 
                    agent.can_go(self.map.is_charging_node, self.map.routes, start, end)])
            self.prompts.append("Please select from agents {} to complete delivery from node {} to node {}: ".format("{}", start, end))
        return (self.prompts, self.candidates)

    def ack_task(self, id, index, time):
        try:
            valid_id = int(id)
            if not valid_id in self.candidates[index]:
                raise ValueError()
        except ValueError:
            return False, "Please enter a valid integer from the following: {}: "
        agent = self.agents[valid_id]
        new_task = self.new_tasks[index]
        self.next_awake_agent.push(agent.id, agent.dispatch_task(new_task, self.map.routes, time))
        start, end = new_task
        task = self.get_pending_task(start, end)
        self.total_waiting_time += time - task[2] + self.map.routes[(agent.location, start)][1]
        try:
            self.pending_tasks.remove(task)
            self.agents_to_dispatch.remove(agent.id)
        except ValueError:
            pass
        self.remove_from_candidates(valid_id, index)
        return True, ""

    def handle_not_enough_agents(self):
        self.agents_to_dispatch = [agent.id for agent in self.agents if agent.available and not agent.is_charging]

    def remove_from_candidates(self, id, index):
        for i in range(index + 1, len(self.candidates)):
            try:
                self.candidates[i].remove(id)
            except ValueError:
                pass

    def get_charging_prompts(self, id):
        agent = self.agents[id]
        prompt = "Agent {} has {} meters of range left. ".format(agent.id, agent.range)
        self.curr_valid_chargers = [i for i in range(len(self.map.is_charging_node)) 
                    if self.map.is_charging_node[i] 
                    and agent.can_go(self.map.is_charging_node, self.map.routes, agent.location, i)]
        for charger in self.curr_valid_chargers:
            prompt += "Charger {} is {} meters away. ".format(charger, self.map.routes[(agent.location, charger)][1])
        prompt += "Please select a charger from the following list: {} Or select -1 to not move to a charger: ".format(self.curr_valid_chargers)
        return prompt
    
    def ack_charger(self, response, time, id):
        try:
            valid_node = int(response)
            if not valid_node == -1 and not valid_node in self.curr_valid_chargers:
                raise ValueError()
        except ValueError:
            return False, "Please enter a valid integer from the following: {} Or -1 to not charge :".format(self.curr_valid_chargers)
        if not valid_node == -1:
            print(valid_node)
            self.next_awake_agent.push(id, self.agents[id].dispatch_charger(valid_node, self.map.routes, time))
        return True, ""

    def get_pending_task(self, start, end):
        for task in self.pending_tasks:
            if task[0] == start and task[1] == end:
                return task
        return None
            
    def get_from_yaml(self, manifest_dict, key):
        try:
            return manifest_dict[key]
        except KeyError as e:
            raise KeyError("Please define \"{}\" in \"manifest.yml\". \
                See \"example_manifest.yml\" for formatting".format(key)) from e

    
class Agent:
    def __init__(self, id, location, max_range, speed):
        self.id = id
        self.location = location
        self.range = max_range
        self.max_range = max_range
        self.available = True
        self.is_charging = False
        self.speed = speed

    def can_go(self, is_charging_node, routes, start, end):
        if self.available:
            nearest_charger_dist = float('inf')
            for i, is_charging_node in enumerate(is_charging_node):
                if is_charging_node:
                    dist = routes[(end, i)][1]
                    if dist < nearest_charger_dist:
                        nearest_charger_dist = dist
            if routes[(self.location, start)][1] + routes[(start, end)][1] + dist <= self.range:
                return True
        return False
    
    def arrive(self, is_charging_node):
        self.available = True
        if is_charging_node[self.location]:
            self.is_charging = True

    def dispatch_task(self, task, routes, time):
        start, end = task
        self.charging = False
        self.available = False
        distance = routes[(self.location, start)][1] + routes[(start, end)][1]
        self.range -= distance
        self.location = end
        return (distance / self.speed) + time
    
    def dispatch_charger(self, charger, routes, time):
        self.charging = False
        self.available = False
        distance = routes[(self.location, charger)][1]
        self.range -= distance
        self.location = charger
        return (distance / self.speed) + time


    def charge(self, charge_per_second):
        self.range = self.range + charge_per_second
        if self.range > self.max_range:
            self.range = self.max_range
            self.is_charging = False