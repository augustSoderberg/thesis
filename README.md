# Simulation for my thesis
This is a human playable version of the simulation to later be used for reinforcement learning.

The idea of the simulation is that you have several electric autonomous agents which need to perform tasks on a graph network. The tasks spawn in randomly as cargo which needs to be moved from a start node to an end node. Some nodes will charge the agents over time; agents lose charge as they drive long distances over edges.

The simulation is designed such that you will never become stuck, you can only make inefficient decisions, not incorrect decisions.

Look through the manifest.yml file and change around the number of nodes, edge weights, number of agents, agent settings, and other graph settings. Manifest.yml fields are explained in comments in the file.

Run 'play_as_human.py' to play the simulation.

This will start the simulation according to your specifications in 'manifest.yml'

Additionally a .svg file will appear showing you the graph you have created. Use this graph to inform your decisions as you play the simulation.

Information about the state of the agents will appear in the terminal and require user input to make decisions about which agents should complete which task and which charging node agents should navigate towards.

At the end of the simulation, you will see a value representing the total number of seconds that tasks waited before being picked up by agents. This is your efficiency metric to attempt to improve.

No part of the user input is time based, this means you can take as long as you would like to make all of your decisions.