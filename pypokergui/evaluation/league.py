import numpy as np
from bots.random_bot import RandomBot
from bots.calling_station import CallingStation
from bots.NitBot import NitBot
from bots.TAGBot import TAGBot


class LeagueEvaluator:
    def __init__(self):
        self.opponents = {
            'Random': RandomBot(),
            'CallingStation': CallingStation(),
            'Nit': NitBot(),
            'TAG': TAGBot()
        }

    def run_league(self, n_hands=10000):
        results = []
        for name, bot in self.opponents.items():
            match_result = self._run_match(bot, n_hands)
            results.append({
                'opponent': name,
                'bb_per_100': match_result['bb_per_100'],
                'ci': self._calculate_ci(match_result['bb_history'])
            })
        return results

    def _calculate_ci(self, bb_history):
        mean = np.mean(bb_history)
        std_err = np.std(bb_history) / np.sqrt(len(bb_history)/100)
        return (mean - 1.96*std_err, mean + 1.96*std_err)
