# PokerHack by HackMelbourne

Welcome to the PokerHack repository!
You will be working primarily in this repository for your submission to PokerHack

## What you need to do:
- Edit the "mybot.py" file in submission/mybot.py
- Rename the file and class to your team name
- For example, rename the file to "Team-Bots.py
  ```python
  def setup_ai():
    return MyBot()

    class MyBot(BasePokerPlayer):  # Do not forget to make parent class as "BasePokerPlayer"

        #  we define the logic to make an action through this method. (so this method would be the core of your AI)
        def declare_action(self, valid_actions, hole_card, round_state):
  ```
  should now be

  ```python
  def setup_ai():
    return Team-Bots()

    class Team-Bots(BasePokerPlayer):  # Do not forget to make parent class as "BasePokerPlayer"

        #  we define the logic to make an action through this method. (so this method would be the core of your AI)
        def declare_action(self, valid_actions, hole_card, round_state):
  ```
- Start coding!
- Most of your bot logic should go in the "declare_action" function
  ```python
    class MyBot(BasePokerPlayer):  # Do not forget to make parent class as "BasePokerPlayer"

    #  we define the logic to make an action through this method. (so this method would be the core of your AI)
    def declare_action(self, valid_actions, hole_card, round_state):
        # for your convenience:
        community_card = round_state['community_card']                  
        street = round_state['street']                                  
        pot = round_state['pot']                                        
        dealer_btn = round_state['dealer_btn']                          
        next_player = round_state['next_player']                        
        small_blind_pos = round_state['small_blind_pos']                
        big_blind_pos = round_state['big_blind_pos']                    
        round_count = round_state['round_count']                        
        small_blind_amount = round_state['small_blind_amount']          
        seats = round_state['seats']                                    
        action_histories = round_state['action_histories']             

        # valid_actions format => [raise_action_info, call_action_info, fold_action_info]
        action = random.choice(valid_actions)["action"]
        if action == "raise":
            action_info = valid_actions[2]
            amount = random.randint(action_info["amount"]["min"], action_info["amount"]["max"])
            if amount == -1: action = "call"
        if action == "call":
            return self.do_call(valid_actions)
        if action == "fold":
            return self.do_call(valid_actions)
        return self.do_raise(valid_actions, amount)   # action returned here is sent to the poker engine

  ```
## Setting up your environment
First, make sure to fork this repository, or download the repository as a .zip file and create a new GitHub repo from it.
You can use GitHub codespaces instead of running the code locally on your machine. Doing this means that you don't have to download dependencies on your machine.

### How to use GitHub codespaces
Starting from your GitHub repository on a browser
- Click on the green "Code" button
- Click on the "Codespaces" tab
- Create a new Codespace by pressing the + button
- GitHub will automatically create and setup your codespace. If this takes too long ( > 3 mins), try reloading the page
- You can now code, run files and commit changes within the online environment

Before you can run the code, run
```bash
pip install -r requirements.txt
```

## Testing 
To see how your bot plays against other bots:
- Register your bot in poker_conf.yaml:
```yaml
ai_players:
  - name: "calling_station"
    path: pypokergui/bots/calling_station.py
  - name: "NitBot"
    path: pypokergui/bots/NitBot.py
  - name: "Rando"
    path: pypokergui/bots/random_bot.py
  - name: "TAGBot"
    path: pypokergui/bots/TAGBot.py
  - name: Fish1
    path: pypokergui/bots/sample_player/fish_player_setup.py
  - name: Fish2
    path: pypokergui/bots/sample_player/fish_player_setup.py
  - name: Fish3
    path: pypokergui/bots/sample_player/random_player_setup.py
  - name: "CodeforcesNoob"
    path: pypokergui/bots/mybot.py
ante: 0
blind_structure: null
initial_stack: 1000
max_round: 100
small_blind: 10

# UI settings
ui_config:
  speed: "moderate"  # slow, moderate, fast
  auto_play: true   # Set to true for automated play
  show_hand_strength: true
  show_pot_odds: true
```
In this code block, mybot is the eighth player
The other players codes are in the sample_player folder (you do not need to work in this folder)
You can also play around with different ante's, initial stacks, max number of rounds and the small blind

Then, start the server
If using a GitHub codespace, open the terminal and run 
```bash
./start-poker.sh
```
If running locally on your computer, run
```bash
python -m pypokergui serve ./poker_conf.yaml --port 8000 --speed moderate
```
You can also use "slow" or "fast"
- Their game event speeds are defined in pypokergui/message_manager/py from line 279 onwards

A new browser tab should open
Then you can click on Start Poker to start the simulation
Alternatively, you can also register yourself as a player to play against the AI players

If a port error shows up, such as "OSError: [WinError 10048] Only one usage of each socket address (protocol/network address/port) is normally permitted"
- Rerun the bash command but with a different port (such as 8001)

To close the server, go to the terminal and input Ctrl+C

Additional resources:

PyPokerEngine resources : https://ishikota.github.io/PyPokerEngine/
How to play poker : https://www.youtube.com/watch?v=CpSewSHZhmo
Notion on Poker : https://www.notion.so/How-to-play-poker-An-extensive-guide-for-beginners-1e63f0dcdde3803996e5d2e85a437303?pvs=4


## Example on how to use Reinforcement Learning for your AI agent
```python
from pypokerengine.players import BasePokerPlayer
from pypokerengine.api.emulator import Emulator
from pypokerengine.utils.game_state_utils import restore_game_state
from pypokerengine.players import BasePokerPlayer
from mymodule.poker_ai.player_model import SomePlayerModel

class RLPLayer(BasePokerPlayer):

    # Setup Emulator object by registering game information
    def receive_game_start_message(self, game_info):
        player_num = game_info["player_num"]
        max_round = game_info["rule"]["max_round"]
        small_blind_amount = game_info["rule"]["small_blind_amount"]
        ante_amount = game_info["rule"]["ante"]
        blind_structure = game_info["rule"]["blind_structure"]
        
        self.emulator = Emulator()
        self.emulator.set_game_rule(player_num, max_round, small_blind_amount, ante_amount)
        self.emulator.set_blind_structure(blind_structure)
        
        # Register algorithm of each player which used in the simulation.
        for player_info in game_info["seats"]["players"]:
            self.emulator.register_player(player_info["uuid"], SomePlayerModel())

    def declare_action(self, valid_actions, hole_card, round_state):
        game_state = restore_game_state(round_state)
        # decide action by using some simulation result
        # updated_state, events = self.emulator.apply_action(game_state, "fold")
        # updated_state, events = self.emulator.run_until_round_finish(game_state)
        # updated_state, events = self.emulator.run_until_game_finish(game_state)
        if self.is_good_simulation_result(updated_state):
            return # you would declare CALL or RAISE action
        else:
            return "fold", 0
    
```

## Notes for GUI
- The order for bots in the GUI is from top left to top right, then bottom left to bottom right
