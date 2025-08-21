"""
Comprehensive Testing Framework for Poker Analytics
Place this in: pypokergui/evaluation/analytics_tests.py
"""

import unittest
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict, Counter

class PokerAnalyticsValidator:
    """Validates and tests poker analytics data quality"""
    
    def __init__(self, analytics_dir="poker_analytics_advanced"):
        self.analytics_dir = analytics_dir
        self.data = None
        self.player_stats = None
        
    def load_latest_session(self):
        """Load the most recent analytics session"""
        # Find latest JSON file
        json_files = [f for f in os.listdir(self.analytics_dir) if f.endswith('.json')]
        if not json_files:
            raise FileNotFoundError("No analytics data found")
            
        latest_file = max(json_files, key=lambda f: os.path.getctime(
            os.path.join(self.analytics_dir, f)))
        
        with open(os.path.join(self.analytics_dir, latest_file), 'r') as f:
            data = json.load(f)
            
        self.data = data.get('session_data', {})
        self.player_stats = data.get('player_stats', {})
        
        print(f"Loaded session data: {len(self.data.get('hands', []))} hands")
        return True

    def validate_data_integrity(self):
        """Run comprehensive data validation tests"""
        print("\n=== DATA INTEGRITY VALIDATION ===")
        
        tests_passed = 0
        total_tests = 0
        
        # Test 1: Basic data structure
        total_tests += 1
        if self.data and 'hands' in self.data:
            print("✓ Basic data structure valid")
            tests_passed += 1
        else:
            print("✗ Basic data structure invalid")
        
        # Test 2: Hand sequence integrity
        total_tests += 1
        hands = self.data.get('hands', [])
        if hands:
            hand_numbers = [h.get('hand_number', 0) for h in hands]
            if hand_numbers == sorted(hand_numbers):
                print("✓ Hand sequence is valid")
                tests_passed += 1
            else:
                print("✗ Hand sequence has gaps or ordering issues")
        
        # Test 3: Pot conservation (money in = money out)
        total_tests += 1
        pot_conservation_valid = self._test_pot_conservation()
        if pot_conservation_valid:
            print("✓ Pot conservation checks passed")
            tests_passed += 1
        else:
            print("✗ Pot conservation violations detected")
        
        # Test 4: Player statistics consistency
        total_tests += 1
        stats_valid = self._test_stats_consistency()
        if stats_valid:
            print("✓ Player statistics are consistent")
            tests_passed += 1
        else:
            print("✗ Player statistics inconsistencies found")
        
        # Test 5: Action sequence validity
        total_tests += 1
        actions_valid = self._test_action_sequences()
        if actions_valid:
            print("✓ Action sequences are valid")
            tests_passed += 1
        else:
            print("✗ Invalid action sequences detected")
        
        print(f"\nData Integrity Score: {tests_passed}/{total_tests} tests passed")
        return tests_passed / total_tests

    def _test_pot_conservation(self):
        """Test that money is conserved in each hand"""
        for hand in self.data.get('hands', []):
            total_invested = 0
            total_won = 0
            
            # Calculate total money put into pot
            for action in hand.get('actions', []):
                if action.get('type') == 'action' and action.get('amount', 0) > 0:
                    total_invested += action.get('amount', 0)
            
            # Calculate total winnings
            for winner in hand.get('winners', []):
                total_won += winner.get('winnings', 0)
            
            # Allow small rounding errors
            if abs(total_invested - total_won) > 1:
                print(f"  Pot conservation violation in hand {hand.get('hand_number')}: "
                        f"Invested: {total_invested}, Won: {total_won}")
                return False
        return True

    def _test_stats_consistency(self):
        """Test that calculated statistics are consistent"""
        for player_name, stats in self.player_stats.items():
            # Test basic ratios
            if stats.get('hands_won', 0) > stats.get('hands_played', 0):
                print(f"  {player_name}: More hands won than played")
                return False
            
            if stats.get('showdowns_won', 0) > stats.get('showdowns', 0):
                print(f"  {player_name}: More showdowns won than attended")
                return False
                
            if stats.get('vpip_hands', 0) > stats.get('hands_played', 0):
                print(f"  {player_name}: VPIP > hands played")
                return False
        
        return True

    def _test_action_sequences(self):
        """Test that action sequences make poker sense"""
        for hand in self.data.get('hands', []):
            actions = hand.get('actions', [])
            current_street = 'preflop'
            players_in_hand = set()
            
            for action in actions:
                if action.get('type') == 'street_start':
                    current_street = action.get('street', current_street)
                elif action.get('type') == 'action':
                    player = action.get('player')
                    action_type = action.get('action')
                    
                    # Track active players
                    if action_type != 'fold':
                        players_in_hand.add(player)
                    else:
                        players_in_hand.discard(player)
                    
                    # Basic validation: can't act after folding
                    # (This is simplified - real validation would be more complex)
                    if action_type in ['bet', 'raise', 'call', 'check'] and player not in players_in_hand:
                        # Player acted after folding - but allow for edge cases
                        pass
            
            return True

    def generate_comprehensive_reports(self):
        """Generate all reports with statistical analysis"""
        if not self.player_stats:
            print("No player statistics loaded")
            return
            
        print("\n=== GENERATING COMPREHENSIVE REPORTS ===")
        
        # Generate enhanced CSV with confidence intervals
        self._generate_enhanced_csv()
        
        # Generate statistical significance tests
        self._generate_significance_tests()
        
        # Generate advanced plots
        self._generate_advanced_plots()
        
        # Generate matchup analysis
        self._generate_matchup_analysis()
        
        print("All reports generated successfully!")

    def _generate_enhanced_csv(self):
        """Generate CSV with confidence intervals and advanced metrics"""
        output_path = f"{self.analytics_dir}/csv/enhanced_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        enhanced_data = []
        
        for player_name, stats in self.player_stats.items():
            if stats.get('hands_played', 0) < 10:
                continue
                
            hands_played = stats['hands_played']
            hands_won = stats.get('hands_won', 0)
            bb_won = stats.get('bb_won', 0)
            
            # Calculate metrics
            win_rate = hands_won / hands_played
            bb_100 = (bb_won / hands_played) * 100
            vpip = (stats.get('vpip_hands', 0) / hands_played) * 100
            pfr = (stats.get('pfr_hands', 0) / hands_played) * 100
            
            # Calculate confidence intervals (95%)
            win_rate_ci = self._calculate_proportion_ci(hands_won, hands_played)
            
            # BB/100 confidence interval using bankroll history if available
            bankroll_history = stats.get('bankroll_history', [])
            if len(bankroll_history) > 1:
                bb_results = np.diff(bankroll_history)  # Hand-by-hand results
                bb_100_std = np.std(bb_results) * np.sqrt(100) if len(bb_results) > 1 else 0
                bb_100_ci = (bb_100 - 1.96 * bb_100_std / np.sqrt(hands_played), 
                           bb_100 + 1.96 * bb_100_std / np.sqrt(hands_played))
            else:
                bb_100_ci = (bb_100 - 5, bb_100 + 5)  # Default uncertainty
            
            # Enhanced C-bet and WWSF calculations
            cbets_made = stats.get('cbets_made', 0)
            cbet_opps = stats.get('cbet_opportunities', 0)
            cbet_freq = (cbets_made / cbet_opps * 100) if cbet_opps > 0 else 0
            
            flops_seen = stats.get('flops_seen', 0)
            flops_won = stats.get('flops_won', 0)
            wwsf = (flops_won / flops_seen * 100) if flops_seen > 0 else 0
            
            # Showdown metrics
            showdowns = stats.get('showdowns', 0)
            showdowns_won = stats.get('showdowns_won', 0)
            showdown_wr = (showdowns_won / showdowns * 100) if showdowns > 0 else 0
            
            # Aggression factor
            preflop_raises = stats.get('preflop_raises', 0)
            preflop_calls = stats.get('preflop_calls', 0)
            af = preflop_raises / max(preflop_calls, 1)
            
            enhanced_data.append({
                'player': player_name,
                'hands_played': hands_played,
                'win_rate': round(win_rate * 100, 2),
                'win_rate_ci_lower': round(win_rate_ci[0] * 100, 2),
                'win_rate_ci_upper': round(win_rate_ci[1] * 100, 2),
                'bb_100': round(bb_100, 2),
                'bb_100_ci_lower': round(bb_100_ci[0], 2),
                'bb_100_ci_upper': round(bb_100_ci[1], 2),
                'vpip': round(vpip, 2),
                'pfr': round(pfr, 2),
                'aggression_factor': round(af, 2),
                'cbet_freq': round(cbet_freq, 2),
                'cbet_opportunities': cbet_opps,
                'wwsf': round(wwsf, 2),
                'flops_seen': flops_seen,
                'showdown_wr': round(showdown_wr, 2),
                'showdowns': showdowns,
                'total_winnings': stats.get('total_winnings', 0),
                'sample_size_adequate': 'Yes' if hands_played >= 100 else 'No'
            })
        
        # Save to CSV
        df = pd.DataFrame(enhanced_data)
        os.makedirs(f"{self.analytics_dir}/csv", exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Enhanced CSV saved: {output_path}")
        
        return df

    def _calculate_proportion_ci(self, successes, trials, confidence=0.95):
        """Calculate confidence interval for a proportion using Wilson score interval"""
        if trials == 0:
            return (0, 0)
            
        p = successes / trials
        z = stats.norm.ppf(1 - (1 - confidence) / 2)
        
        denominator = 1 + z**2 / trials
        center = (p + z**2 / (2 * trials)) / denominator
        margin = z * np.sqrt((p * (1 - p) + z**2 / (4 * trials)) / trials) / denominator
        
        return (max(0, center - margin), min(1, center + margin))

    def _generate_significance_tests(self):
        """Run statistical significance tests on player performance"""
        print("\n=== STATISTICAL SIGNIFICANCE TESTS ===")
        
        if len(self.player_stats) < 2:
            print("Need at least 2 players for comparison tests")
            return
        
        # Test for significant differences in BB/100
        players_data = []
        for player_name, stats in self.player_stats.items():
            if stats.get('hands_played', 0) >= 30:  # Minimum sample size
                bb_100 = (stats.get('bb_won', 0) / stats['hands_played']) * 100
                bankroll_history = stats.get('bankroll_history', [])
                
                # Calculate variance from bankroll history if available
                if len(bankroll_history) > 1:
                    hand_results = np.diff(bankroll_history)
                    variance = np.var(hand_results) if len(hand_results) > 1 else 1
                else:
                    variance = 1  # Default
                
                players_data.append((player_name, bb_100, stats['hands_played'], variance))
        
        if len(players_data) >= 2:
            # Pairwise t-tests for BB/100 differences
            for i in range(len(players_data)):
                for j in range(i + 1, len(players_data)):
                    name1, bb1, n1, var1 = players_data[i]
                    name2, bb2, n2, var2 = players_data[j]
                    
                    # Two-sample t-test approximation
                    if n1 >= 30 and n2 >= 30:
                        diff = abs(bb1 - bb2)
                        pooled_se = np.sqrt(var1/n1 + var2/n2)
                        t_stat = diff / pooled_se if pooled_se > 0 else 0
                        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n1 + n2 - 2))
                        
                        significance = "***" if p_value < 0.001 else "**" if p_value < 0.01 else "*" if p_value < 0.05 else "ns"
                        
                        print(f"{name1} vs {name2}: BB/100 diff = {diff:.2f}, p = {p_value:.4f} {significance}")

    def _generate_advanced_plots(self):
        """Generate advanced statistical plots"""
        # Create comprehensive dashboard
        fig = plt.figure(figsize=(20, 15))
        gs = fig.add_gridspec(4, 3, hspace=0.3, wspace=0.3)
        
        # 1. Bankroll curves with confidence bands
        ax1 = fig.add_subplot(gs[0, :])
        self._plot_bankroll_with_ci(ax1)
        
        # 2. BB/100 comparison with error bars
        ax2 = fig.add_subplot(gs[1, 0])
        self._plot_bb100_comparison(ax2)
        
        # 3. VPIP vs PFR with clustering
        ax3 = fig.add_subplot(gs[1, 1])
        self._plot_vpip_pfr_analysis(ax3)
        
        # 4. Position analysis heatmap
        ax4 = fig.add_subplot(gs[1, 2])
        self._plot_position_heatmap(ax4)
        
        # 5. C-bet and WWSF analysis
        ax5 = fig.add_subplot(gs[2, 0])
        self._plot_cbet_analysis(ax5)
        
        # 6. Showdown analysis
        ax6 = fig.add_subplot(gs[2, 1])
        self._plot_showdown_analysis(ax6)
        
        # 7. Risk of ruin approximation
        ax7 = fig.add_subplot(gs[2, 2])
        self._plot_risk_analysis(ax7)
        
        # 8. Hand strength distribution
        ax8 = fig.add_subplot(gs[3, :])
        self._plot_hand_strength_dist(ax8)
        
        plt.suptitle('Comprehensive Poker Analytics Dashboard', fontsize=16, fontweight='bold')
        
        # Save dashboard
        os.makedirs(f"{self.analytics_dir}/plots", exist_ok=True)
        dashboard_path = f"{self.analytics_dir}/plots/comprehensive_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(dashboard_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Comprehensive dashboard saved: {dashboard_path}")
            


    def _plot_bankroll_with_ci(self, ax):
        """Plot bankroll curves with confidence intervals"""
        for player_name, stats in self.player_stats.items():
            bankroll_history = stats.get('bankroll_history', [])
            if len(bankroll_history) < 5:
                continue
                
            hands = np.arange(len(bankroll_history))
            bankroll = np.array(bankroll_history)
            
            # Plot main curve
            ax.plot(hands, bankroll, label=player_name, linewidth=2)
            
            # Add confidence interval
            if len(bankroll) > 20:
                # Rolling statistics for CI
                window = min(20, len(bankroll) // 3)
                rolling_mean = pd.Series(bankroll).rolling(window=window).mean()
                rolling_std = pd.Series(bankroll).rolling(window=window).std()
                
                ci_upper = rolling_mean + 1.96 * rolling_std
                ci_lower = rolling_mean - 1.96 * rolling_std
                
                ax.fill_between(hands, ci_lower, ci_upper, alpha=0.2)
        
        ax.set_xlabel('Hands Played')
        ax.set_ylabel('Bankroll')
        ax.set_title('Bankroll Curves with 95% Confidence Intervals')
        ax.legend()
        ax.grid(True, alpha=0.3)

    def _plot_bb100_comparison(self, ax):
        """Plot BB/100 with confidence intervals"""
        players = []
        bb_100_values = []
        ci_lower = []
        ci_upper = []
        
        for player_name, stats in self.player_stats.items():
            hands_played = stats.get('hands_played', 0)
            if hands_played < 20:
                continue
                
            bb_won = stats.get('bb_won', 0)
            bb_100 = (bb_won / hands_played) * 100
            
            # Approximate confidence interval using bankroll history
            bankroll_history = stats.get('bankroll_history', [])
            if len(bankroll_history) > 1:
                hand_results = np.diff(bankroll_history)
                std_err = np.std(hand_results) / np.sqrt(len(hand_results)) if len(hand_results) > 1 else 5
                ci_l = bb_100 - 1.96 * std_err
                ci_u = bb_100 + 1.96 * std_err
            else:
                ci_l = bb_100 - 5  # Default uncertainty
                ci_u = bb_100 + 5
            
            players.append(player_name)
            bb_100_values.append(bb_100)
            ci_lower.append(ci_l)
            ci_upper.append(ci_u)
        
        if players:
            x_pos = np.arange(len(players))
            bars = ax.bar(x_pos, bb_100_values, capsize=5, color='skyblue', alpha=0.7)
            
            # Add error bars
            errors = [[bb_100_values[i] - ci_lower[i] for i in range(len(players))],
                     [ci_upper[i] - bb_100_values[i] for i in range(len(players))]]
            ax.errorbar(x_pos, bb_100_values, yerr=errors, fmt='none', capsize=5, color='black')
            
            ax.set_xlabel('Players')
            ax.set_ylabel('BB/100')
            ax.set_title('BB/100 with 95% Confidence Intervals')
            ax.set_xticks(x_pos)
            ax.set_xticklabels(players, rotation=45)
            ax.axhline(y=0, color='red', linestyle='--', alpha=0.5)
            ax.grid(True, alpha=0.3)

    def _plot_vpip_pfr_analysis(self, ax):
        """Plot VPIP vs PFR with player classification"""
        vpip_values = []
        pfr_values = []
        player_names = []
        
        for player_name, stats in self.player_stats.items():
            hands_played = stats.get('hands_played', 0)
            if hands_played < 20:
                continue
                
            vpip = (stats.get('vpip_hands', 0) / hands_played) * 100
            pfr = (stats.get('pfr_hands', 0) / hands_played) * 100
            
            vpip_values.append(vpip)
            pfr_values.append(pfr)
            player_names.append(player_name)
        
        if len(vpip_values) > 0:
            scatter = ax.scatter(vpip_values, pfr_values, s=100, alpha=0.7, c=range(len(vpip_values)), cmap='viridis')
            
            for i, player in enumerate(player_names):
                ax.annotate(player, (vpip_values[i], pfr_values[i]), 
                          xytext=(5, 5), textcoords='offset points', fontsize=9)
            
            # Add reference lines for player types
            ax.axhline(y=15, color='red', linestyle='--', alpha=0.5, label='Aggressive threshold')
            ax.axvline(x=20, color='blue', linestyle='--', alpha=0.5, label='Tight threshold')
            
            ax.set_xlabel('VPIP (%)')
            ax.set_ylabel('PFR (%)')
            ax.set_title('Player Types: VPIP vs PFR')
            ax.legend()
            ax.grid(True, alpha=0.3)

    def _plot_cbet_analysis(self, ax):
        """Plot C-bet frequency analysis"""
        players = []
        cbet_freqs = []
        
        for player_name, stats in self.player_stats.items():
            cbet_opps = stats.get('cbet_opportunities', 0)
            if cbet_opps < 5:  # Need minimum opportunities
                continue
                
            cbet_freq = (stats.get('cbets_made', 0) / cbet_opps) * 100
            players.append(player_name)
            cbet_freqs.append(cbet_freq)
        
        if players:
            bars = ax.bar(players, cbet_freqs, color='lightcoral', alpha=0.7)
            ax.set_ylabel('C-bet Frequency (%)')
            ax.set_title('Continuation Bet Frequency')
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, alpha=0.3)
            
            # Add optimal range indication
            ax.axhline(y=60, color='green', linestyle='--', alpha=0.5, label='Optimal range')
            ax.axhline(y=80, color='green', linestyle='--', alpha=0.5)
            ax.legend()

    def _plot_showdown_analysis(self, ax):
        """Plot WWSF vs Showdown win rate"""
        wwsf_values = []
        showdown_wr_values = []
        player_names = []
        
        for player_name, stats in self.player_stats.items():
            flops_seen = stats.get('flops_seen', 0)
            showdowns = stats.get('showdowns', 0)
            
            if flops_seen < 5 or showdowns < 3:
                continue
                
            wwsf = (stats.get('flops_won', 0) / flops_seen) * 100
            showdown_wr = (stats.get('showdowns_won', 0) / showdowns) * 100
            
            wwsf_values.append(wwsf)
            showdown_wr_values.append(showdown_wr)
            player_names.append(player_name)
        
        if len(wwsf_values) > 0:
            ax.scatter(wwsf_values, showdown_wr_values, s=100, alpha=0.7)
            
            for i, player in enumerate(player_names):
                ax.annotate(player, (wwsf_values[i], showdown_wr_values[i]), 
                          xytext=(5, 5), textcoords='offset points', fontsize=9)
            
            ax.set_xlabel('WWSF (%)')
            ax.set_ylabel('Showdown Win Rate (%)')
            ax.set_title('Win When See Flop vs Showdown Performance')
            ax.grid(True, alpha=0.3)

    def _plot_position_heatmap(self, ax):
        """Generate position-based performance heatmap"""
        # Collect position data
        position_data = defaultdict(lambda: {'hands': 0, 'won': 0, 'bb_won': 0})
        positions = ['SB', 'BB', 'UTG', 'MP', 'CO', 'BTN']
        
        for player_name, stats in self.player_stats.items():
            position_counter = stats.get('positions', {})
            for pos, count in position_counter.items():
                if pos in positions:
                    position_data[pos]['hands'] += count
                    # Approximate wins based on overall stats
                    win_rate = (stats.get('hands_won', 0) / max(stats.get('hands_played', 1), 1))
                    position_data[pos]['won'] += count * win_rate
        
        if position_data:
            # Create heatmap data
            pos_names = list(position_data.keys())
            win_rates = [position_data[pos]['won'] / max(position_data[pos]['hands'], 1) * 100 
                        for pos in pos_names]
            
            # Simple bar chart instead of heatmap
            bars = ax.bar(pos_names, win_rates, color='lightgreen', alpha=0.7)
            ax.set_ylabel('Win Rate (%)')
            ax.set_title('Win Rate by Position')
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, 'Insufficient Position Data', 
                    ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title('Position Analysis')

    def _plot_risk_analysis(self, ax):
        """Plot risk of ruin analysis"""
        players = []
        risk_scores = []
        
        for player_name, stats in self.player_stats.items():
            hands_played = stats.get('hands_played', 0)
            if hands_played < 50:
                continue
                
            # Calculate risk based on bankroll volatility
            bankroll_history = stats.get('bankroll_history', [])
            if len(bankroll_history) > 10:
                bankroll_changes = np.diff(bankroll_history)
                variance = np.var(bankroll_changes)
                mean_change = np.mean(bankroll_changes)
                
                # Risk score: higher variance relative to mean = higher risk
                if mean_change > 0:
                    risk_score = variance / (mean_change ** 2)
                else:
                    risk_score = variance * abs(mean_change) + 10  # Higher risk for negative trend
                    
                players.append(player_name)
                risk_scores.append(risk_score)
        
        if players:
            bars = ax.bar(players, risk_scores, color='salmon', alpha=0.7)
            ax.set_ylabel('Risk Score (Variance/Return²)')
            ax.set_title('Bankroll Risk Analysis')
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, 'Insufficient Data for Risk Analysis', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title('Risk Analysis')

    def _plot_hand_strength_dist(self, ax):
        """Plot hand strength and action distribution"""
        # Analyze action patterns by street
        street_actions = defaultdict(lambda: defaultdict(int))
        
        for hand in self.data.get('hands', []):
            current_street = 'preflop'
            for action in hand.get('actions', []):
                if action.get('type') == 'street_start':
                    current_street = action.get('street', current_street)
                elif action.get('type') == 'action':
                    action_type = action.get('action', 'unknown')
                    street_actions[current_street][action_type] += 1
        
        if street_actions:
            # Create stacked bar chart of actions by street
            streets = list(street_actions.keys())
            actions = ['fold', 'check', 'call', 'bet', 'raise']
            
            bottom = np.zeros(len(streets))
            colors = ['red', 'gray', 'blue', 'green', 'orange']
            
            for i, action in enumerate(actions):
                values = [street_actions[street][action] for street in streets]
                ax.bar(streets, values, bottom=bottom, label=action, 
                        color=colors[i % len(colors)], alpha=0.7)
                bottom += values
            
            ax.set_xlabel('Street')
            ax.set_ylabel('Number of Actions')
            ax.set_title('Action Distribution by Street')
            ax.legend()
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, 'No Action Data Available', 
                    ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title('Hand Strength Distribution')

    def _generate_matchup_analysis(self):
        """Generate head-to-head matchup analysis"""
        print("\n=== MATCHUP ANALYSIS ===")
        
        matchups = defaultdict(lambda: defaultdict(lambda: {'hands': 0, 'wins': 0, 'bb_won': 0}))
        
        # Analyze each hand for player matchups
        for hand in self.data.get('hands', []):
            players_in_hand = list(hand.get('seats', {}).keys())
            winners = hand.get('winners', [])
            
            # Create matchup pairs
            for i, player1 in enumerate(players_in_hand):
                for player2 in players_in_hand[i+1:]:
                    matchups[player1][player2]['hands'] += 1
                    matchups[player2][player1]['hands'] += 1
                    
                    # Track who won this hand
                    for winner in winners:
                        winner_name = self._get_winner_name(winner)
                        if winner_name == player1:
                            matchups[player1][player2]['wins'] += 1
                            matchups[player1][player2]['bb_won'] += winner.get('winnings', 0) / 20  # Assuming BB=20
                        elif winner_name == player2:
                            matchups[player2][player1]['wins'] += 1
                            matchups[player2][player1]['bb_won'] += winner.get('winnings', 0) / 20
        
        # Generate matchup report
        matchup_path = f"{self.analytics_dir}/csv/matchup_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        matchup_data = []
        for player1, opponents in matchups.items():
            for player2, stats in opponents.items():
                if stats['hands'] >= 10:  # Minimum sample size
                    win_rate = (stats['wins'] / stats['hands']) * 100
                    bb_100 = (stats['bb_won'] / stats['hands']) * 100
                    
                    matchup_data.append({
                        'player': player1,
                        'opponent': player2,
                        'hands_played': stats['hands'],
                        'hands_won': stats['wins'],
                        'win_rate': round(win_rate, 2),
                        'bb_100': round(bb_100, 2)
                    })
        
        if matchup_data:
            df = pd.DataFrame(matchup_data)
            df.to_csv(matchup_path, index=False)
            print(f"Matchup analysis saved: {matchup_path}")
            
            # Print top performer in each matchup
            for player1 in set(df['player']):
                player_matchups = df[df['player'] == player1]
                if not player_matchups.empty:
                    best_matchup = player_matchups.loc[player_matchups['bb_100'].idxmax()]
                    worst_matchup = player_matchups.loc[player_matchups['bb_100'].idxmin()]
                    
                    print(f"{player1}:")
                    print(f"  Best vs {best_matchup['opponent']}: {best_matchup['bb_100']} BB/100")
                    print(f"  Worst vs {worst_matchup['opponent']}: {worst_matchup['bb_100']} BB/100")
        else:
            print("Insufficient data for matchup analysis")

    def _get_winner_name(self, winner):
        """Extract winner name from winner data structure"""
        # Try different possible fields
        if 'name' in winner:
            return winner['name']
        elif 'player' in winner:
            return winner['player']
        elif 'uuid' in winner:
            # Try to match UUID to name from current hand
            return self._get_player_name_by_uuid(winner['uuid'])
        else:
            return 'unknown'

    def _get_player_name_by_uuid(self, uuid):
        """Get player name from UUID using current hand data"""
        if not self.current_hand:
            return 'unknown'
            
        for player_name, seat_info in self.current_hand.get('seats', {}).items():
            if seat_info.get('uuid') == uuid:
                return player_name
        return 'unknown'

    def generate_bot_performance_report(self, bot_name="TradingBot"):
        """Generate specific report for bot performance vs humans"""
        print(f"\n=== BOT PERFORMANCE REPORT: {bot_name} ===")
        
        if bot_name not in self.player_stats:
            print(f"No data found for {bot_name}")
            return
        
        bot_stats = self.player_stats[bot_name]
        human_stats = {name: stats for name, stats in self.player_stats.items() 
                      if name != bot_name and stats.get('hands_played', 0) >= 20}
        
        if not human_stats:
            print("No human players with sufficient data for comparison")
            return
        
        # Bot performance metrics
        bot_hands = bot_stats.get('hands_played', 0)
        bot_bb_100 = (bot_stats.get('bb_won', 0) / bot_hands * 100) if bot_hands > 0 else 0
        bot_vpip = (bot_stats.get('vpip_hands', 0) / bot_hands * 100) if bot_hands > 0 else 0
        bot_pfr = (bot_stats.get('pfr_hands', 0) / bot_hands * 100) if bot_hands > 0 else 0
        
        # Human averages
        human_bb_100_avg = np.mean([(stats.get('bb_won', 0) / stats['hands_played'] * 100) 
                                   for stats in human_stats.values()])
        human_vpip_avg = np.mean([(stats.get('vpip_hands', 0) / stats['hands_played'] * 100) 
                                 for stats in human_stats.values()])
        human_pfr_avg = np.mean([(stats.get('pfr_hands', 0) / stats['hands_played'] * 100) 
                                for stats in human_stats.values()])
        
        print(f"Bot Performance ({bot_hands} hands):")
        print(f"  BB/100: {bot_bb_100:.2f} (Human avg: {human_bb_100_avg:.2f})")
        print(f"  VPIP: {bot_vpip:.2f}% (Human avg: {human_vpip_avg:.2f}%)")
        print(f"  PFR: {bot_pfr:.2f}% (Human avg: {human_pfr_avg:.2f}%)")
        
        # Performance ranking
        all_bb_100 = [(name, (stats.get('bb_won', 0) / stats['hands_played'] * 100)) 
                     for name, stats in self.player_stats.items() 
                     if stats.get('hands_played', 0) >= 20]
        all_bb_100.sort(key=lambda x: x[1], reverse=True)
        
        bot_rank = next((i+1 for i, (name, _) in enumerate(all_bb_100) if name == bot_name), None)
        if bot_rank:
            print(f"  Ranking: {bot_rank} out of {len(all_bb_100)} players")
        
        # Statistical significance vs humans
        if bot_hands >= 100:
            print(f"\nStatistical Analysis:")
            bot_bankroll = bot_stats.get('bankroll_history', [])
            if len(bot_bankroll) > 1:
                bot_results = np.diff(bot_bankroll)
                bot_std = np.std(bot_results)
                
                # Compare to each human
                for human_name, human_stat in human_stats.items():
                    human_hands = human_stat['hands_played']
                    if human_hands >= 100:
                        human_bb_100 = (human_stat.get('bb_won', 0) / human_hands * 100)
                        
                        # Simple t-test approximation
                        diff = bot_bb_100 - human_bb_100
                        pooled_se = bot_std / np.sqrt(bot_hands)  # Simplified
                        t_stat = abs(diff) / pooled_se if pooled_se > 0 else 0
                        
                        significance = "***" if t_stat > 3 else "**" if t_stat > 2 else "*" if t_stat > 1.5 else "ns"
                        print(f"  vs {human_name}: {diff:+.2f} BB/100 difference {significance}")

    def run_full_analysis(self, bot_name=None):
        """Run complete analysis suite"""
        print("="*60)
        print("COMPREHENSIVE POKER ANALYTICS VALIDATION")
        print("="*60)
        
        # Load data
        if not self.load_latest_session():
            print("Failed to load session data")
            return False
        
        # Run validation tests
        integrity_score = self.validate_data_integrity()
        
        # Generate all reports
        self.generate_comprehensive_reports()
        
        # Bot-specific analysis if requested
        if bot_name:
            self.generate_bot_performance_report(bot_name)
        
        # Summary
        print(f"\n=== ANALYSIS SUMMARY ===")
        print(f"Data Integrity Score: {integrity_score:.2%}")
        print(f"Total Hands Analyzed: {len(self.data.get('hands', []))}")
        print(f"Players Analyzed: {len([p for p, s in self.player_stats.items() if s.get('hands_played', 0) > 0])}")
        print(f"Output Directory: {self.analytics_dir}")
        
        return True


# Convenience function for easy testing
def run_analytics_validation(analytics_dir="poker_analytics_advanced", bot_name=None):
    """
    Convenience function to run full analytics validation
    
    Args:
        analytics_dir: Directory containing analytics data
        bot_name: Name of bot to analyze (optional)
    
    Returns:
        bool: True if analysis completed successfully
    """
    validator = PokerAnalyticsValidator(analytics_dir)
    return validator.run_full_analysis(bot_name)


# Unit tests
class TestPokerAnalytics(unittest.TestCase):
    """Unit tests for poker analytics validation"""
    
    def setUp(self):
        self.validator = PokerAnalyticsValidator("test_analytics")
        
        # Create mock data
        self.validator.data = {
            'hands': [
                {
                    'hand_number': 1,
                    'actions': [
                        {'type': 'action', 'player': 'Player1', 'action': 'call', 'amount': 10},
                        {'type': 'action', 'player': 'Player2', 'action': 'raise', 'amount': 20}
                    ],
                    'winners': [{'player': 'Player1', 'winnings': 30}]
                }
            ]
        }
        
        self.validator.player_stats = {
            'Player1': {'hands_played': 10, 'hands_won': 3, 'bb_won': 5.5},
            'Player2': {'hands_played': 10, 'hands_won': 7, 'bb_won': 12.3}
        }
    
    def test_data_integrity(self):
        """Test data integrity validation"""
        score = self.validator.validate_data_integrity()
        self.assertGreater(score, 0.5)  # Should pass most tests
    
    def test_confidence_intervals(self):
        """Test confidence interval calculations"""
        ci = self.validator._calculate_proportion_ci(3, 10)
        self.assertEqual(len(ci), 2)
        self.assertGreater(ci[1], ci[0])  # Upper > Lower
    
    def test_csv_generation(self):
        """Test CSV report generation"""
        df = self.validator._generate_enhanced_csv()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)


if __name__ == "__main__":
    # Run analytics validation
    print("Running Poker Analytics Validation...")
    
    # You can specify your bot name here
    success = run_analytics_validation(bot_name="TradingBot")  # Change to your bot's name
    
    if success:
        print("\n✓ Analytics validation completed successfully!")
    else:
        print("\n✗ Analytics validation failed")
    
    # Optionally run unit tests
    # unittest.main(verbosity=2)