from pypokerengine.players import BasePokerPlayer
import sys
import json
import os
import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from collections import defaultdict, Counter
import scipy.stats as stats

class AdvancedAnalyticsSpectator(BasePokerPlayer):
    """
    Comprehensive poker analytics bot that tracks all key metrics
    """
    
    def __init__(self):
        super().__init__()
        self.analytics_enabled = False
        self.output_dir = None
        self.setup_output_directory()
        
        # Core session data
        self.session_data = {
            'hands': [],
            'players': {},
            'session_start': datetime.now().isoformat(),
            'game_info': {}
        }
        
        # Player statistics tracking
        self.player_stats = defaultdict(lambda: {
            'hands_played': 0,
            'hands_won': 0,
            'total_winnings': 0,
            'total_invested': 0,
            'bb_won': 0,  # Big blinds won
            'showdowns': 0,
            'showdowns_won': 0,
            'flops_seen': 0,
            'flops_won': 0,
            'cbets_made': 0,
            'cbet_opportunities': 0,
            'preflop_raises': 0,
            'preflop_calls': 0,
            'preflop_folds': 0,
            'vpip_hands': 0,  # Voluntarily put money in pot
            'pfr_hands': 0,   # Preflop raise
            'three_bet': 0,
            'fold_to_three_bet': 0,
            'bankroll_history': [],
            'hand_results': [],
            'positions': Counter(),
            'starting_hands': Counter(),
            'by_position': defaultdict(lambda: {
                'hands': 0, 'won': 0, 'winnings': 0
            })
        })
        
        # Hand tracking
        self.current_hand = None
        self.hand_count = 0
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.big_blind_size = 0
        
        # Preflop tracking
        self.preflop_aggressor = None
        self.preflop_actions = {}
        
    def setup_output_directory(self):
        """Setup output directory with fallbacks"""
        self.output_dir = "poker_analytics_advanced"
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(f"{self.output_dir}/plots", exist_ok=True)
        os.makedirs(f"{self.output_dir}/csv", exist_ok=True)
        self.analytics_enabled = True
        print(f"[Analytics] Advanced analytics enabled - output: {self.output_dir}")

    def declare_action(self, valid_actions, hole_card, round_state):
        """Always fold - just observing"""
        return 'fold', 0

    def receive_game_start_message(self, game_info):
        """Record game setup and extract blind levels"""
        
        self.session_data['game_info'] = game_info
        
        # Extract blind levels
        if 'rule' in game_info and 'small_blind_amount' in game_info['rule']:
            self.big_blind_size = game_info['rule']['small_blind_amount'] * 2
        else:
            self.big_blind_size = 20  # Default fallback

    def receive_round_start_message(self, round_count, hole_card, seats):
        """Start tracking a new hand"""
        self.hand_count = round_count
        
        # Initialize player bankrolls if first hand
        if round_count == 1:
            for seat in seats:
                player_name = seat.get('name', 'unknown')
                self.player_stats[player_name]['bankroll_history'] = [seat.get('stack', 0)]
        
        self.current_hand = {
            'hand_number': round_count,
            'hole_cards': hole_card if hole_card else [],
            'seats': {seat.get('name', f"player_{i}"): seat for i, seat in enumerate(seats) if seat},
            'actions': [],
            'pot_history': [],
            'streets': [],
            'showdown': False,
            'winners': [],
            'preflop_actions': {},
            'flop_seen': False,
            'board': []
        }
        
        # Track positions
        for seat in seats:
            player_name = seat.get('name', 'unknown')
            position = self._get_position(seat.get('pos', 0), len(seats))
            self.player_stats[player_name]['positions'][position] += 1
            
        # Reset preflop tracking
        self.preflop_aggressor = None
        self.preflop_actions = {}
        

    def receive_street_start_message(self, street, round_state):
        """Track street changes"""
        if not self.current_hand or not round_state:
            return
            
        pot_amount = self._extract_pot_amount(round_state)
        board = round_state.get('community_card', [])
        
        self.current_hand['streets'].append(street)
        self.current_hand['actions'].append({
            'type': 'street_start',
            'street': street,
            'pot': pot_amount,
            'board': board
        })
        
        if street == 'flop':
            self.current_hand['flop_seen'] = True
            # Track players who saw flop
            for player_name in self.current_hand['seats']:
                if self._player_saw_flop(player_name):
                    self.player_stats[player_name]['flops_seen'] += 1
                    

    def receive_game_update_message(self, action, round_state):
        """Track all player actions"""
        if not self.current_hand or not action or not round_state:
            return
            
        player_uuid = action.get('player_uuid', 'unknown')
        player_name = self._get_player_name_by_uuid(player_uuid)
        action_type = action.get('action', 'unknown')
        amount = action.get('amount', 0)
        pot_amount = self._extract_pot_amount(round_state)
        current_street = self._get_current_street()
        
        # Record action
        action_data = {
            'type': 'action',
            'player': player_name,
            'player_uuid': player_uuid,
            'action': action_type,
            'amount': amount,
            'pot': pot_amount,
            'street': current_street
        }
        self.current_hand['actions'].append(action_data)
        
        # Update statistics based on action
        self._update_action_stats(player_name, action_type, amount, current_street)

    def receive_round_result_message(self, winners, hand_info, round_state):
        """Complete hand data and update all statistics"""
        if not self.current_hand:
            return
            
        # Finalize hand data
        self.current_hand['winners'] = winners if winners else []
        self.current_hand['final_board'] = hand_info if hand_info else {}
        self.current_hand['final_pot'] = self._extract_pot_amount(round_state) if round_state else 0
            
        # Determine if showdown occurred
        self.current_hand['showdown'] = len(self.current_hand.get('board', [])) == 5
        
        # Update player statistics
        self._update_hand_results(winners, round_state)
        
        # Add to session data
        self.session_data['hands'].append(self.current_hand)
        
        # Save periodically and generate reports
        if self.hand_count % 50 == 0 and self.analytics_enabled:
            self._save_all_data()
            self._generate_reports()
            print(f"[Analytics] Generated reports for {self.hand_count} hands")

    def _update_action_stats(self, player_name, action_type, amount, street):
        """Update player statistics based on their action"""
        stats = self.player_stats[player_name]
        
        if street == 'preflop':
            if action_type in ['call', 'raise']:
                stats['vpip_hands'] += 1
                stats['total_invested'] += amount
            if action_type == 'raise':
                stats['pfr_hands'] += 1
                stats['preflop_raises'] += 1
                if not self.preflop_aggressor:
                    self.preflop_aggressor = player_name
            elif action_type == 'call':
                stats['preflop_calls'] += 1
                if self.preflop_aggressor and amount > self.big_blind_size:
                    # This could be a 3-bet call
                    pass
            elif action_type == 'fold':
                stats['preflop_folds'] += 1
        
        # Enhanced C-bet tracking
        elif street == 'flop':
            if player_name == self.preflop_aggressor:
                stats['cbet_opportunities'] += 1
                if action_type in ['bet', 'raise']:
                    stats['cbets_made'] += 1
            
            # Track who saw flop and their actions
            if action_type != 'fold':
                if 'flop_actions' not in stats:
                    stats['flop_actions'] = 0
                stats['flop_actions'] += 1
        
        # Track street-specific actions for better WWSF calculation
        if street in ['flop', 'turn', 'river']:
            street_key = f"{street}_actions"
            if street_key not in stats:
                stats[street_key] = {'fold': 0, 'call': 0, 'bet': 0, 'raise': 0, 'check': 0}
            if action_type in stats[street_key]:
                stats[street_key][action_type] += 1

    def _update_hand_results(self, winners, round_state):
        """Update final hand statistics"""
        # Update hand counts
        for player_name in self.current_hand['seats']:
            self.player_stats[player_name]['hands_played'] += 1
        
        # Update winners
        if winners:
            for winner in winners:
                winner_name = self._get_player_name_by_uuid(winner.get('uuid', ''))
                if winner_name:
                    winnings = winner.get('winnings', 0)
                    self.player_stats[winner_name]['hands_won'] += 1
                    self.player_stats[winner_name]['total_winnings'] += winnings
                    self.player_stats[winner_name]['bb_won'] += winnings / self.big_blind_size
                    
                    # Update bankroll
                    current_bankroll = self.player_stats[winner_name]['bankroll_history'][-1] if self.player_stats[winner_name]['bankroll_history'] else 0
                    new_bankroll = current_bankroll + winnings
                    self.player_stats[winner_name]['bankroll_history'].append(new_bankroll)
                    
                    # Track showdown wins
                    if self.current_hand['showdown']:
                        self.player_stats[winner_name]['showdowns_won'] += 1
                    
                    # Track flop wins
                    if self.current_hand['flop_seen']:
                        self.player_stats[winner_name]['flops_won'] += 1
        
        # Update showdown statistics
        if self.current_hand['showdown']:
            for player_name in self.current_hand['seats']:
                if self._player_saw_showdown(player_name):
                    self.player_stats[player_name]['showdowns'] += 1

    def _generate_reports(self):
        """Generate comprehensive CSV reports and plots"""
        if not self.analytics_enabled:
            return

        # Generate CSV reports
        self._generate_player_stats_csv()
        self._generate_hand_history_csv()
        self._generate_position_analysis_csv()
        
        # Generate plots
        self._generate_bankroll_plots()
        self._generate_performance_plots()
        self._generate_position_plots()
            

    def _generate_player_stats_csv(self):
        """Generate comprehensive player statistics CSV"""
        csv_path = f"{self.output_dir}/csv/player_stats_{self.session_id}.csv"
        
        with open(csv_path, 'w', newline='') as csvfile:
            fieldnames = [
                'player', 'hands_played', 'hands_won', 'win_rate', 
                'total_winnings', 'bb_100', 'vpip', 'pfr', 'af',
                'showdowns', 'showdowns_won', 'showdown_win_rate',
                'flops_seen', 'flops_won', 'wwsf', 'cbet_freq'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for player_name, stats in self.player_stats.items():
                if stats['hands_played'] == 0:
                    continue
                    
                # Calculate derived statistics
                win_rate = (stats['hands_won'] / stats['hands_played']) * 100
                bb_100 = (stats['bb_won'] / stats['hands_played']) * 100
                vpip = (stats['vpip_hands'] / stats['hands_played']) * 100
                pfr = (stats['pfr_hands'] / stats['hands_played']) * 100
                
                showdown_wr = (stats['showdowns_won'] / stats['showdowns']) * 100 if stats['showdowns'] > 0 else 0
                wwsf = (stats['flops_won'] / stats['flops_seen']) * 100 if stats['flops_seen'] > 0 else 0
                cbet_freq = (stats['cbets_made'] / stats['cbet_opportunities']) * 100 if stats['cbet_opportunities'] > 0 else 0
                
                # Aggression factor (simplified)
                total_actions = stats['preflop_raises'] + stats['preflop_calls'] + stats['preflop_folds']
                af = stats['preflop_raises'] / max(stats['preflop_calls'], 1)
                
                writer.writerow({
                    'player': player_name,
                    'hands_played': stats['hands_played'],
                    'hands_won': stats['hands_won'],
                    'win_rate': round(win_rate, 2),
                    'total_winnings': stats['total_winnings'],
                    'bb_100': round(bb_100, 2),
                    'vpip': round(vpip, 2),
                    'pfr': round(pfr, 2),
                    'af': round(af, 2),
                    'showdowns': stats['showdowns'],
                    'showdowns_won': stats['showdowns_won'],
                    'showdown_win_rate': round(showdown_wr, 2),
                    'flops_seen': stats['flops_seen'],
                    'flops_won': stats['flops_won'],
                    'wwsf': round(wwsf, 2),
                    'cbet_freq': round(cbet_freq, 2)
                })

    def _generate_bankroll_plots(self):
        """Generate bankroll curves with confidence intervals"""

        plt.figure(figsize=(12, 8))
        
        for player_name, stats in self.player_stats.items():
            if len(stats['bankroll_history']) < 2:
                continue
                
            bankroll = np.array(stats['bankroll_history'])
            hands = np.arange(len(bankroll))
            
            # Plot bankroll curve
            plt.plot(hands, bankroll, label=f"{player_name}", linewidth=2)
            
            # Add 95% confidence interval (simplified)
            if len(bankroll) > 10:
                # Calculate rolling standard deviation
                window = min(20, len(bankroll) // 2)
                rolling_std = pd.Series(bankroll).rolling(window=window).std().fillna(0)
                
                # 95% CI approximation
                ci_upper = bankroll + 1.96 * rolling_std
                ci_lower = bankroll - 1.96 * rolling_std
                
                plt.fill_between(hands, ci_lower, ci_upper, alpha=0.2)
        
        plt.xlabel('Hands Played')
        plt.ylabel('Bankroll')
        plt.title('Bankroll Curves with 95% Confidence Intervals')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/plots/bankroll_curves_{self.session_id}.png", dpi=300, bbox_inches='tight')
        plt.close()

    def _generate_performance_plots(self):
        """Generate BB/100 and other performance metrics plots"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        players = []
        bb_100_values = []
        win_rates = []
        vpip_values = []
        pfr_values = []
        
        for player_name, stats in self.player_stats.items():
            if stats['hands_played'] < 10:  # Minimum sample size
                continue
                
            players.append(player_name)
            bb_100_values.append((stats['bb_won'] / stats['hands_played']) * 100)
            win_rates.append((stats['hands_won'] / stats['hands_played']) * 100)
            vpip_values.append((stats['vpip_hands'] / stats['hands_played']) * 100)
            pfr_values.append((stats['pfr_hands'] / stats['hands_played']) * 100)
        
        # BB/100 plot
        axes[0, 0].bar(players, bb_100_values, color='skyblue')
        axes[0, 0].set_title('BB/100 by Player')
        axes[0, 0].set_ylabel('BB/100')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Win rate plot
        axes[0, 1].bar(players, win_rates, color='lightgreen')
        axes[0, 1].set_title('Win Rate by Player')
        axes[0, 1].set_ylabel('Win Rate (%)')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # VPIP vs PFR scatter
        axes[1, 0].scatter(vpip_values, pfr_values, s=100, alpha=0.7)
        for i, player in enumerate(players):
            axes[1, 0].annotate(player, (vpip_values[i], pfr_values[i]), 
                                xytext=(5, 5), textcoords='offset points')
        axes[1, 0].set_xlabel('VPIP (%)')
        axes[1, 0].set_ylabel('PFR (%)')
        axes[1, 0].set_title('VPIP vs PFR')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Risk of ruin approximation (simplified)
        axes[1, 1].bar(players, [abs(min(0, bb)) for bb in bb_100_values], color='salmon')
        axes[1, 1].set_title('Downside Risk (Negative BB/100)')
        axes[1, 1].set_ylabel('Risk Level')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/plots/performance_metrics_{self.session_id}.png", dpi=300, bbox_inches='tight')
        plt.close()

    # Helper methods
    def _extract_pot_amount(self, round_state):
        """Safely extract pot amount from round state"""
        if 'pot' in round_state and round_state['pot']:
            if isinstance(round_state['pot'], dict):
                return round_state['pot'].get('main', {}).get('amount', 0)
            else:
                return round_state['pot']
        return 0

    def _get_player_name_by_uuid(self, uuid):
        """Get player name from UUID"""
        for player_name, seat_info in self.current_hand.get('seats', {}).items():
            if seat_info.get('uuid') == uuid:
                return player_name
        return 'unknown'

    def _get_current_street(self):
        """Get current street from actions"""
        if self.current_hand and self.current_hand['streets']:
            return self.current_hand['streets'][-1]
        return 'preflop'

    def _get_position(self, pos, num_players):
        """Convert position number to name"""
        if num_players <= 2:
            return 'HU' if pos == 0 else 'HU'
        elif num_players <= 6:  # 6-max
            positions = ['SB', 'BB', 'UTG', 'MP', 'CO', 'BTN']
            return positions[pos % len(positions)]
        else:  # Full ring
            positions = ['SB', 'BB', 'UTG', 'UTG+1', 'MP', 'MP+1', 'CO', 'BTN', 'BTN+1']
            return positions[pos % len(positions)]

    def _player_saw_flop(self, player_name):
        """Check if player saw the flop based on actions"""
        if not self.current_hand:
            return False
            
        # Check if player folded preflop
        for action in self.current_hand['actions']:
            if (action.get('type') == 'action' and 
                action.get('player') == player_name and 
                action.get('street', 'preflop') == 'preflop' and 
                action.get('action') == 'fold'):
                return False
        
        # If they didn't fold preflop and flop was dealt, they saw it
        return self.current_hand['flop_seen']

    def _player_saw_showdown(self, player_name):
        """Check if player saw showdown based on actions"""
        if not self.current_hand or not self.current_hand['showdown']:
            return False
            
        # Check if player folded on any street
        for action in self.current_hand['actions']:
            if (action.get('type') == 'action' and 
                action.get('player') == player_name and 
                action.get('action') == 'fold'):
                return False
        
        return True

    def _save_all_data(self):
        """Save all collected data"""
        if not self.analytics_enabled:
            return
            
        # Save JSON data
        filename = f"{self.output_dir}/session_{self.session_id}.json"
        with open(filename, 'w') as f:
            json.dump({
                'session_data': self.session_data,
                'player_stats': dict(self.player_stats)
            }, f, indent=2, default=str)

    def _generate_hand_history_csv(self):
        """Generate detailed hand history CSV"""
        pass  # Implement if needed

    def _generate_position_analysis_csv(self):
        """Generate position-based analysis CSV"""
        pass  # Implement if needed

    def _generate_position_plots(self):
        """Generate position-based performance plots"""
        pass  # Implement if needed

    def __del__(self):
        """Save data and generate final reports when session ends"""
        if self.analytics_enabled:
            self._save_all_data()
            self._generate_reports()
            print(f"[Analytics] Final reports generated for session {self.session_id}")

# PyPokerGUI setup functions
def setup_ai():
    return AdvancedAnalyticsSpectator()
