import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from pypokerengine.api.game import setup_config, start_poker
from collections import defaultdict
import json
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import logging


@dataclass
class PlayerResult:
    """Results for a single player"""
    name: str
    uuid: str
    final_stack: int
    initial_stack: int
    hands_played: int
    vpip: float = 0.0
    pfr: float = 0.0
    cbet: float = 0.0
    aggression_factor: float = 0.0
    bb_per_100: float = 0.0
    
    def __post_init__(self):
        if self.hands_played > 0:
            stack_change = self.final_stack - self.initial_stack
            # Assuming small blind of 10 for BB calculation
            self.bb_per_100 = (stack_change / 10) * (100 / self.hands_played)

@dataclass 
class SimulationConfig:
    """Configuration for simulation runs"""
    n_simulations: int = 1000
    hands_per_simulation: int = 100
    initial_stack: int = 10000
    small_blind: int = 10
    big_blind: int = 20
    ante: int = 0
    max_round: int = 10
    verbose: bool = False

class PokerSimulator:
    """Advanced Monte Carlo poker simulator with statistical analysis"""
    
    def __init__(self, config: SimulationConfig = None):
        self.config = config or SimulationConfig()
        self.results = []
        self.player_stats = defaultdict(lambda: {
            'vpip': {'actions': 0, 'opportunities': 0},
            'pfr': {'actions': 0, 'opportunities': 0}, 
            'cbet': {'actions': 0, 'opportunities': 0},
            'raises': 0, 'calls': 0, 'folds': 0,
            'hands_played': 0,
            'stacks': []
        })
        self.simulation_history = []
        
        # Setup logging
        logging.basicConfig(level=logging.INFO if config and config.verbose else logging.WARNING)
        self.logger = logging.getLogger(__name__)
    
    def run_monte_carlo_simulation(self, players_info: List[Dict], n_runs: int = None) -> Dict:
        """Run multiple simulations for statistical significance"""
        n_runs = n_runs or self.config.n_simulations
        self.logger.info(f"Starting Monte Carlo simulation with {n_runs} runs")
        
        all_results = []
        start_time = time.time()
        
        for run in range(n_runs):
            if run % 100 == 0:
                self.logger.info(f"Completed {run}/{n_runs} simulations")
                
            try:
                run_results = self._run_single_simulation(players_info)
                all_results.append(run_results)
                
            except Exception as e:
                self.logger.error(f"Simulation {run} failed: {e}")
                continue
        
        end_time = time.time()
        self.logger.info(f"Completed {len(all_results)} simulations in {end_time - start_time:.2f} seconds")
        
        return self._analyze_results(all_results, players_info)
    
    def _run_single_simulation(self, players_info: List[Dict]) -> List[PlayerResult]:
        """Run a single poker simulation"""
        # Reset player stats for this simulation
        simulation_stats = defaultdict(lambda: {
            'vpip': {'actions': 0, 'opportunities': 0},
            'pfr': {'actions': 0, 'opportunities': 0},
            'cbet': {'actions': 0, 'opportunities': 0},
            'raises': 0, 'calls': 0, 'folds': 0,
            'hands_played': 0
        })
        
        # Setup game config
        config = setup_config(
            max_round=self.config.hands_per_simulation,
            initial_stack=self.config.initial_stack,
            small_blind_amount=self.config.small_blind,
            ante_amount=self.config.ante
        )
        
        # Register players
        for player_info in players_info:
            config.register_player(
                name=player_info['name'],
                algorithm=player_info['algorithm']
            )
        
        # Custom game callbacks to track stats
        def update_stats(round_state, action):
            player_uuid = action.get('player_uuid')
            if not player_uuid:
                return
                
            street = round_state.get('street', 'preflop')
            action_type = action.get('action')
            stats = simulation_stats[player_uuid]
            
            # Track basic action counts
            if action_type == 'raise':
                stats['raises'] += 1
            elif action_type == 'call':
                stats['calls'] += 1
            elif action_type == 'fold':
                stats['folds'] += 1
            
            # Track VPIP (Voluntarily Put $ In Pot)
            if street == 'preflop':
                if self._is_vpip_opportunity(round_state, player_uuid):
                    stats['vpip']['opportunities'] += 1
                    if action_type in ['call', 'raise']:
                        stats['vpip']['actions'] += 1
                
                # Track PFR (Pre-Flop Raise)
                if self._is_pfr_opportunity(round_state, player_uuid):
                    stats['pfr']['opportunities'] += 1
                    if action_type == 'raise':
                        stats['pfr']['actions'] += 1
            
            # Track C-bet (Continuation Bet)
            elif street == 'flop':
                if self._is_cbet_opportunity(round_state, player_uuid):
                    stats['cbet']['opportunities'] += 1
                    if action_type == 'raise':
                        stats['cbet']['actions'] += 1
        
        # Run the game with callbacks
        try:
            game_result = start_poker(config, verbose=0)
            
            # Process results
            results = []
            for player in game_result['players']:
                uuid = player['uuid']
                stats = simulation_stats[uuid]
                
                result = PlayerResult(
                    name=player['name'],
                    uuid=uuid,
                    final_stack=player['stack'],
                    initial_stack=self.config.initial_stack,
                    hands_played=self.config.hands_per_simulation,
                    vpip=self._calculate_percentage(stats['vpip']),
                    pfr=self._calculate_percentage(stats['pfr']),
                    cbet=self._calculate_percentage(stats['cbet']),
                    aggression_factor=self._calculate_aggression_factor(stats)
                )
                results.append(result)
                
            return results
            
        except Exception as e:
            self.logger.error(f"Game simulation failed: {e}")
            raise
    
    def _is_vpip_opportunity(self, round_state: Dict, player_uuid: str) -> bool:
        """Check if player had opportunity to voluntarily put money in pot"""
        # Simplified - in real implementation, check if player had option to call/raise
        return round_state.get('street') == 'preflop'
    
    def _is_pfr_opportunity(self, round_state: Dict, player_uuid: str) -> bool:
        """Check if player had opportunity to raise preflop"""
        # Simplified - check if no previous raises and player can raise
        return round_state.get('street') == 'preflop'
    
    def _is_cbet_opportunity(self, round_state: Dict, player_uuid: str) -> bool:
        """Check if player had continuation bet opportunity"""
        # Simplified - check if player was preflop aggressor
        return round_state.get('street') == 'flop'
    
    def _calculate_percentage(self, stat_dict: Dict) -> float:
        """Calculate percentage from actions/opportunities"""
        opportunities = stat_dict.get('opportunities', 0)
        actions = stat_dict.get('actions', 0)
        return actions / opportunities if opportunities > 0 else 0.0
    
    def _calculate_aggression_factor(self, stats: Dict) -> float:
        """Calculate aggression factor: (raises + bets) / calls"""
        raises = stats.get('raises', 0)
        calls = stats.get('calls', 0)
        return raises / calls if calls > 0 else float('inf') if raises > 0 else 0.0
    
    def _analyze_results(self, all_results: List[List[PlayerResult]], players_info: List[Dict]) -> Dict:
        """Perform statistical analysis on simulation results"""
        analysis = {}
        
        # Organize results by player
        player_results = defaultdict(list)
        for simulation_results in all_results:
            for player_result in simulation_results:
                player_results[player_result.name].append(player_result)
        
        # Calculate statistics for each player
        for player_name, results in player_results.items():
            bb_per_100_values = [r.bb_per_100 for r in results]
            vpip_values = [r.vpip for r in results]
            pfr_values = [r.pfr for r in results]
            
            analysis[player_name] = {
                'bb_per_100': {
                    'mean': np.mean(bb_per_100_values),
                    'std': np.std(bb_per_100_values),
                    'confidence_interval': self._calculate_confidence_interval(bb_per_100_values),
                    'win_rate': sum(1 for x in bb_per_100_values if x > 0) / len(bb_per_100_values)
                },
                'vpip': {
                    'mean': np.mean(vpip_values),
                    'std': np.std(vpip_values)
                },
                'pfr': {
                    'mean': np.mean(pfr_values), 
                    'std': np.std(pfr_values)
                },
                'total_simulations': len(results)
            }
        
        return analysis
    
    def _calculate_confidence_interval(self, values: List[float], confidence: float = 0.95) -> Tuple[float, float]:
        """Calculate confidence interval for a set of values"""
        if len(values) < 2:
            return (0.0, 0.0)
            
        n = len(values)
        mean = np.mean(values)
        std_err = stats.sem(values)
        
        # Use t-distribution for small samples
        if n < 30:
            t_val = stats.t.ppf((1 + confidence) / 2, n - 1)
            margin_error = t_val * std_err
        else:
            z_val = stats.norm.ppf((1 + confidence) / 2)
            margin_error = z_val * std_err
        
        return (mean - margin_error, mean + margin_error)
    
    def generate_comprehensive_report(self, analysis_results: Dict, save_plots: bool = True):
        """Generate comprehensive analysis report with plots"""
        print("\n" + "="*60)
        print("MONTE CARLO POKER SIMULATION REPORT")
        print("="*60)
        
        # Statistical summary
        for player_name, stats in analysis_results.items():
            print(f"\nPlayer: {player_name}")
            print("-" * 40)
            
            bb_stats = stats['bb_per_100']
            print(f"BB/100 Hands:")
            print(f"  Mean: {bb_stats['mean']:.2f}")
            print(f"  Std Dev: {bb_stats['std']:.2f}")
            print(f"  95% CI: ({bb_stats['confidence_interval'][0]:.2f}, {bb_stats['confidence_interval'][1]:.2f})")
            print(f"  Win Rate: {bb_stats['win_rate']:.1%}")
            
            print(f"\nPlaying Style:")
            print(f"  VPIP: {stats['vpip']['mean']:.1%} (±{stats['vpip']['std']:.1%})")
            print(f"  PFR: {stats['pfr']['mean']:.1%} (±{stats['pfr']['std']:.1%})")
            
            print(f"  Simulations: {stats['total_simulations']}")
        
        # Generate plots
        if save_plots:
            self._create_performance_plots(analysis_results)
    
    def _create_performance_plots(self, analysis_results: Dict):
        """Create various performance visualization plots"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        players = list(analysis_results.keys())
        
        # BB/100 with confidence intervals
        bb_means = [analysis_results[p]['bb_per_100']['mean'] for p in players]
        bb_stds = [analysis_results[p]['bb_per_100']['std'] for p in players]
        
        bars = ax1.bar(players, bb_means, yerr=bb_stds, capsize=5, alpha=0.7)
        ax1.set_title('BB/100 Performance with Error Bars')
        ax1.set_ylabel('BB/100')
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        
        # Color bars based on performance
        for bar, mean in zip(bars, bb_means):
            bar.set_color('green' if mean > 0 else 'red')
        
        # VPIP vs PFR scatter
        vpip_means = [analysis_results[p]['vpip']['mean'] * 100 for p in players]
        pfr_means = [analysis_results[p]['pfr']['mean'] * 100 for p in players]
        
        ax2.scatter(vpip_means, pfr_means, s=100, alpha=0.7)
        for i, player in enumerate(players):
            ax2.annotate(player, (vpip_means[i], pfr_means[i]), 
                        xytext=(5, 5), textcoords='offset points')
        ax2.set_xlabel('VPIP (%)')
        ax2.set_ylabel('PFR (%)')
        ax2.set_title('Playing Style Analysis (VPIP vs PFR)')
        ax2.grid(True, alpha=0.3)
        
        # Win rate comparison
        win_rates = [analysis_results[p]['bb_per_100']['win_rate'] * 100 for p in players]
        ax3.bar(players, win_rates, alpha=0.7, color='blue')
        ax3.set_title('Win Rate (%)')
        ax3.set_ylabel('Win Rate (%)')
        ax3.grid(True, alpha=0.3)
        
        # Confidence intervals visualization
        for i, player in enumerate(players):
            ci = analysis_results[player]['bb_per_100']['confidence_interval']
            ax4.errorbar(i, bb_means[i], 
                        yerr=[[bb_means[i] - ci[0]], [ci[1] - bb_means[i]]], 
                        fmt='o', capsize=10, markersize=8)
        
        ax4.set_xticks(range(len(players)))
        ax4.set_xticklabels(players, rotation=45)
        ax4.set_title('95% Confidence Intervals for BB/100')
        ax4.set_ylabel('BB/100')
        ax4.grid(True, alpha=0.3)
        ax4.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        plt.savefig('poker_simulation_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def run_head_to_head_analysis(self, player1_info: Dict, player2_info: Dict, n_runs: int = 1000) -> Dict:
        """Run head-to-head comparison between two players"""
        players_info = [player1_info, player2_info]
        results = self.run_monte_carlo_simulation(players_info, n_runs)
        
        # Perform statistical significance test
        p1_results = [r.bb_per_100 for sim in self.simulation_history for r in sim if r.name == player1_info['name']]
        p2_results = [r.bb_per_100 for sim in self.simulation_history for r in sim if r.name == player2_info['name']]
        
        # Perform t-test
        t_stat, p_value = stats.ttest_ind(p1_results, p2_results)
        
        comparison = {
            'player1': player1_info['name'],
            'player2': player2_info['name'],
            't_statistic': t_stat,
            'p_value': p_value,
            'significant_difference': p_value < 0.05,
            'effect_size': (np.mean(p1_results) - np.mean(p2_results)) / np.sqrt((np.var(p1_results) + np.var(p2_results)) / 2)
        }
        
        return {**results, 'statistical_comparison': comparison}

# Example usage function
def run_example_simulation():
    """Example of how to use the simulator"""
    from bots.mybot import CodeforcesNoob 
    
    # Setup players
    players_info = [
        {'name': 'CodeforcesNoob', 'algorithm': CodeforcesNoob()},
        {'name': 'RandomPlayer', 'algorithm': FishPlayer()}  # You'd need to implement this
    ]
    
    # Configure simulation
    config = SimulationConfig(
        n_simulations=500,
        hands_per_simulation=100,
        verbose=True
    )
    
    # Run simulation
    simulator = PokerSimulator(config)
    results = simulator.run_monte_carlo_simulation(players_info)
    
    # Generate report
    simulator.generate_comprehensive_report(results)
    
    return results

# Simple fish player for testing
class FishPlayer:
    """Simple loose-passive player for testing"""
    def __init__(self):
        self.uuid = None
        
    def declare_action(self, valid_actions, hole_card, round_state):
        import random
        
        call_action = next((a for a in valid_actions if a["action"] == "call"), None)
        fold_action = next((a for a in valid_actions if a["action"] == "fold"), None)
        
        # Loose player - calls 60% of the time, folds 40%
        if call_action and random.random() < 0.6:
            return "call", call_action["amount"]
        else:
            return "fold", 0
    
    def receive_game_start_message(self, game_info): pass
    def receive_round_start_message(self, round_count, hole_card, seats): pass
    def receive_street_start_message(self, street, round_state): pass
    def receive_game_update_message(self, action, round_state): pass
    def receive_round_result_message(self, winners, hand_info, round_state): pass