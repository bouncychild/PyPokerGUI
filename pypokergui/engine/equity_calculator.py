from functools import lru_cache
import numpy as np

class EquityCalculator:
    def __init__(self):
        self.rng = np.random.default_rng(42)
        self.deck_cache = {}
        
    @lru_cache(maxsize=10000)
    def equity_vs_range(self, hero_cards, board_cards, range_id, n=1500):
        deck = self._get_cached_deck(hero_cards, board_cards)
        wins = 0
        
        for _ in range(n):
            # Use shared RNG for reproducibility
            villain_hand = self._sample_from_range(range_id)
            runout = self.rng.choice(deck, size=5-len(board_cards), replace=False)
            
            # Evaluate hands
            hero_strength = self._evaluate_hand(hero_cards + board_cards + runout)
            villain_strength = self._evaluate_hand(villain_hand + board_cards + runout)
            
            if hero_strength > villain_strength:
                wins += 1
            elif hero_strength == villain_strength:
                wins += 0.5
                
        return wins / n