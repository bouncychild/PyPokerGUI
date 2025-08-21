from collections import defaultdict

class OpponentModel:
    def __init__(self):
        self.stats = defaultdict(lambda: {
            'vpip': {'alpha': 1.5, 'beta': 1.5},
            'pfr': {'alpha': 1.5, 'beta': 1.5},
            'fold_to_cbet': {'alpha': 1.5, 'beta': 1.5}
        })
        
    def update(self, player_id, action, street):
        if street == 'preflop':
            self._update_stat(player_id, 'vpip', action != 'fold')
            if self._is_raise_opportunity():
                self._update_stat(player_id, 'pfr', action == 'raise')
        
        if street == 'flop' and self._is_cbet_situation():
            self._update_stat(player_id, 'fold_to_cbet', action == 'fold')
    
    def _update_stat(self, player_id, stat, condition):
        self.stats[player_id][stat]['alpha'] += int(condition)
        self.stats[player_id][stat]['beta'] += int(not condition)