# Please read "Efficient Dispatching of Autonomous Cargo Vehicles" in the `documents` folder for more information on this repository.

# Simulation
Look through the manifest.yml file and change around the number of nodes, edge weights, number of agents, agent settings, and other graph settings. Manifest.yml fields are explained in comments in the file.

Run 'play_as_human.py' to play the simulation with human decisions.

This will start the simulation according to your specifications in 'manifest.yml'

Additionally a .svg file will appear showing you the graph you have created. Use this graph to inform your decisions as you play the simulation.

Information about the state of the agents will appear in the terminal and require user input to make decisions about which agents should complete which task and which charging node agents should navigate towards.

At the end of the simulation, you will see a value representing the total number of seconds that tasks waited before being picked up by agents. This is your efficiency metric to attempt to improve.

No part of the user input is time based, this means you can take as long as you would like to make all of your decisions.

# Reinforcement Learning
To train a reinforcement learning model use the `train.py` file. You can change any model specifications you would like. The training paradigm utilizes an [act-experience-update loop](https://tensorforce.readthedocs.io/en/latest/agents/agent.html#experience-update-interface) with early stopping once the performance dips below a desired threshold. You can load in your saved agents into `train.py` if you would like to continue training them with adjusted parameters.

To test your reinforcement learning model you can use the `collect_data.py` file and change the saved agent file names accordingly. Pre-task dispatching models are saved to `models_pre` and post-task to `models_post`.

# Optimization
To run the optimization and testing code go to `optimize.py`. The searching granularity and finishing function can be adjusted as seen fit. The `test` function can be run with manually defined weights as well for testing.

# Replicating the Reinforcement Learning Results
The models in `models_post` and `models_pre` are trained to the same specifications as described in the paper. To replicate the training procedure simply run `train.py` with the default `EARLY_STOP_THRESHOLD` value.

# Replicating the Optimization Results
Simply run the `optimize.py` file with the default specifications.

# Other Dispatchers
The "greedy dispatcher", "hopeful dispatcher", and "random dispatcher" are all specified in the appropriately named files. Running any of the files will show you the relevant performance on the current `manifest` configuration.

# Help
Please create a "new issue" on GitHub for any particular problems you discover in this repository.