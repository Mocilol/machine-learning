import random
import math
from environment import Agent, Environment
from planner import RoutePlanner
from simulator import Simulator

class LearningAgent(Agent):
    """ An agent that learns to drive in the Smartcab world.
        This is the object you will be modifying. """

    def __init__(self, env, learning=False, epsilon=1.0, alpha=0.5):
        super(LearningAgent, self).__init__(env)     # Set the agent in the evironment
        self.planner = RoutePlanner(self.env, self)  # Create a route planner
        self.valid_actions = self.env.valid_actions  # The set of valid actions

        # Set parameters of the learning agent
        self.learning = learning # Whether the agent is expected to learn
        self.Q = dict()          # Create a Q-table which will be a dictionary of tuples
        self.epsilon = epsilon   # Random exploration factor
        self.alpha = alpha       # Learning factor

        # Set any additional class parameters as needed
        self.total_trials = 0


    def reset(self, destination=None, testing=False):
        """ The reset function is called at the beginning of each trial.
            'testing' is set to True if testing trials are being used
            once training trials have completed. """

        # Select the destination as the new location to route to
        self.planner.route_to(destination)

        # Update epsilon using a decay function of your choice
        # Update additional class parameters as needed
        # If 'testing' is True, set epsilon and alpha to 0
        if testing:
            self.alpha = 0
            self.epsilon = 0
        else:
            self.total_trials = self.total_trials + 1
            #self.epsilon = math.exp(-self.alpha * self.total_trials)
            if self.total_trials < 25: self.epsilon = self.epsilon - 0.015  
            if self.total_trials >= 25: self.epsilon = self.epsilon - 0.025 
            #self.epsilon = self.epsilon - 0.02 #D
            #self.epsilon = math.exp(-self.alpha * self.total_trials)
            #self.epsilon = math.exp(-self.alpha * 0.3 * self.total_trials)
            #self.epsilon = math.pow(self.alpha, self.total_trials) #F nochance
            #self.epsilon = 1 / math.pow(self.total_trials, 2) #F
            #self.epsilon = math.cos(self.total_trials * self.alpha) #F
            #print('reset: ', self.epsilon, self.alpha, self.total_trials)

        return None

    def build_state(self):
        """ The build_state function is called when the agent requests data from the
            environment. The next waypoint, the intersection inputs, and the deadline
            are all features available to the agent. """

        # Collect data about the environment
        waypoint = self.planner.next_waypoint() # The next waypoint
        inputs = self.env.sense(self)           # Visual input - intersection light and traffic
        #deadline = self.env.get_deadline(self)  # Remaining deadline

        # Set 'state' as a tuple of relevant data for the agent
        oncoming = 'right' if inputs['oncoming'] == 'forward' else inputs['oncoming']
        left = 'forward' if inputs['left'] == 'forward' else None
        state = (waypoint, inputs['light'], oncoming, left)

        return state


    def get_maxQ(self, state):
        """ The get_max_Q function is called when the agent is asked to find the
            maximum Q-value of all actions based on the 'state' the smartcab is in. """

        # Calculate the maximum Q-value of all actions for a given state
        state_q = self.Q[state]
        key = max(state_q, key=lambda k: state_q[k])
        maxQ = state_q[key]

        return maxQ


    def createQ(self, state):
        """ The createQ function is called when a state is generated by the agent. """

        # When learning, check if the 'state' is not in the Q-table
        # If it is not, create a new dictionary for that state
        #   Then, for each action available, set the initial Q-value to 0.0
        if self.learning:
            if not self.Q.has_key(state):
                self.Q[state] = {k:0.0 for k in self.valid_actions}

            return self.Q[state]
        else:
            return


    def choose_action(self, state):
        """ The choose_action function is called when the agent is asked to choose
            which action to take, based on the 'state' the smartcab is in. """

        # Set the agent state and default action
        self.state = state
        self.next_waypoint = self.planner.next_waypoint()
        action = None

        # When not learning, choose a random action
        # When learning, choose a random action with 'epsilon' probability
        #   Otherwise, choose an action with the highest Q-value for the current state
        if self.learning:
            if random.random() <= self.epsilon:
                action = random.choice(self.valid_actions)
            else:
                state_q = self.Q[state]
                action = max(state_q, key=lambda k: state_q[k])
                print(state, state_q, action)
        else:
            action = random.choice(self.valid_actions)

        return action


    def learn(self, state, action, reward):
        """ The learn function is called after the agent completes an action and
            receives an award. This function does not consider future rewards
            when conducting learning. """

        # When learning, implement the value iteration update rule
        #   Use only the learning rate 'alpha' (do not use the discount factor 'gamma')
        if self.learning:
            lastq = self.Q[state]
            nextstate = self.build_state()
            nextmaxq = self.get_maxQ(nextstate) if self.Q.has_key(nextstate) else 0
            lastq[action] = (1 - self.alpha) * lastq[action] + self.alpha * (reward + 0)#nextmaxq)
            #print(state, nextstate)
        return


    def update(self):
        """ The update function is called when a time step is completed in the
            environment for a given trial. This function will build the agent
            state, choose an action, receive a reward, and learn if enabled. """

        state = self.build_state()          # Get current state
        self.createQ(state)                 # Create 'state' in Q-table
        action = self.choose_action(state)  # Choose an action
        reward = self.env.act(self, action) # Receive a reward
        self.learn(state, action, reward)   # Q-learn

        return


def run():
    """ Driving function for running the simulation.
        Press ESC to close the simulation, or [SPACE] to pause the simulation. """

    ##############
    # Create the environment
    # Flags:
    #   verbose     - set to True to display additional output from the simulation
    #   num_dummies - discrete number of dummy agents in the environment, default is 100
    #   grid_size   - discrete number of intersections (columns, rows), default is (8, 6)
    env = Environment()

    ##############
    # Create the driving agent
    # Flags:
    #   learning   - set to True to force the driving agent to use Q-learning
    #    * epsilon - continuous value for the exploration factor, default is 1
    #    * alpha   - continuous value for the learning rate, default is 0.5
    agent = env.create_agent(LearningAgent, learning=True, alpha=0.2)
    #agent = env.create_agent(LearningAgent, learning=False, alpha = 0.2)

    ##############
    # Follow the driving agent
    # Flags:
    #   enforce_deadline - set to True to enforce a deadline metric
    env.set_primary_agent(agent, enforce_deadline=True)

    ##############
    # Create the simulation
    # Flags:
    #   update_delay - continuous time (in seconds) between actions, default is 2.0 seconds
    #   display      - set to False to disable the GUI if PyGame is enabled
    #   log_metrics  - set to True to log trial and simulation results to /logs
    #   optimized    - set to True to change the default log file name
    sim = Simulator(env, update_delay=0, log_metrics=True, display=False, optimized=True)
    #sim = Simulator(env, update_delay=0.001, log_metrics=False, display=True, optimized=False)

    ##############
    # Run the simulator
    # Flags:
    #   tolerance  - epsilon tolerance before beginning testing, default is 0.05
    #   n_test     - discrete number of testing trials to perform, default is 0
    sim.run(n_test=20)


if __name__ == '__main__':
    run()

