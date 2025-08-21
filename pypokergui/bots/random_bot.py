import random
from collections import defaultdict, Counter
from functools import lru_cache
from pypokerengine.players import BasePokerPlayer

class RandomBot(BasePokerPlayer):
    def declare_action(self, valid_actions, hole_card, round_state):
        # Choose a random action from valid actions
        chosen_action = random.choice(valid_actions)
        action = chosen_action['action']
        
        # Handle different action types
        if action == 'fold':
            return 'fold', 0
        elif action == 'call':
            return 'call', chosen_action['amount']
        elif action == 'raise':
            # For raise, we need to pick an amount between min and max
            min_raise = chosen_action['amount']['min']
            max_raise = chosen_action['amount']['max']
            raise_amount = random.randint(min_raise, max_raise)
            return 'raise', raise_amount
        else:
            # Fallback to fold if something unexpected happens
            return 'fold', 0
    
    def _estimate_equity(self, hole_card, round_state):
        # for now, return a random value for testing
        return random.uniform(0, 1)
    
    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass
    
    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

def setup_ai():
    return RandomBot()