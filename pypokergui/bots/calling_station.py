import random
from collections import defaultdict, Counter
from functools import lru_cache
from pypokerengine.players import BasePokerPlayer

class CallingStation(BasePokerPlayer):
    def declare_action(self, valid_actions, hole_card, round_state):
        for action in valid_actions:
            if action['action'] == 'call':
                return 'call', action['amount']
    
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
    return CallingStation()