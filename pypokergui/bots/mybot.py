import random
from collections import defaultdict, Counter
from functools import lru_cache
from pypokerengine.players import BasePokerPlayer
from enum import Enum
import math

class ActionType(Enum):
    VALUE_BET = "value_bet"
    BLUFF = "bluff" 
    PROTECTION = "protection"
    STEAL = "steal"
    CALL_DRAW = "call_draw"
    FOLD_WEAK = "fold_weak"

class CodeforcesNoob(BasePokerPlayer):
    PREFLOP_RANGES = {
        "premium": {"AA","KK","QQ","JJ","AKs","AKo"},
        "strong": {"TT","99","88","AQs","AQo","AJs","KQs"},
        "playable": {"77","66","ATs","KJs","QJs","JTs","KQo"},
    }
    
    # setting up equity buckets
    def __init__(self):
        super().__init__()
        self.opponent_stats = defaultdict(lambda: {
            "vpip": 0.0, "pfr": 0.0, "aggression": 0.0,
            "hands_seen": 0, "raises_this_street": defaultdict(int),
            "fold_to_raise": 0.0, "cbet_frequency": 0.0
        })
        self._rng = random.Random()
        self._equity_cache = {}
        self._street_raises = defaultdict(int)  # Track raises per street
        self._last_street = None
        
    def _reset_street_counters(self, current_street):
        """Reset raise counters when street changes"""
        if self._last_street != current_street:
            self._street_raises.clear()
            self._last_street = current_street

    def _raise_count_this_street(self, street):
        """Count how many times we've raised this street"""
        return self._street_raises.get(street, 0)

    def _get_pot_raise(self, raise_action):
        """Convert raise action to pot-sized raise if available"""
        if raise_action and "amount" in raise_action:
            return raise_action
        return None

    def _update_stats(self, player_uuid, street, action):
        """Update opponent statistics based on their actions"""
        stats = self.opponent_stats[player_uuid]
        stats["hands_seen"] += 1
        
        if action["action"] == "raise":
            stats["raises_this_street"][street] += 1
            stats["aggression"] = (stats["aggression"] * 0.9 + 1.0) * 0.1
        elif action["action"] == "fold":
            stats["fold_to_raise"] = (stats["fold_to_raise"] * 0.9 + 1.0) * 0.1

    def _get_position(self, round_state):
        btn = round_state["dealer_btn"]
        my_pos = next(i for i,s in enumerate(round_state["seats"]) if s["uuid"] == self.uuid)
        return (my_pos - btn) % len(round_state["seats"])

    def _position_adjustment(self, pos, num_players=6):
        """Dynamic position adjustment based on table size"""
        if num_players <= 6:
            adjustments = [1.4, 1.2, 1.0, 0.85, 0.7, 0.6]
        else:
            adjustments = [1.3, 1.1, 1.0, 0.9, 0.8, 0.7, 0.6, 0.6, 0.5, 0.5]
        return adjustments[pos] if pos < len(adjustments) else 1.0

    def _classify_preflop(self, hole):
        r1, s1 = hole[0][0], hole[0][1]
        r2, s2 = hole[1][0], hole[1][1]
        ranks = "".join(sorted([r1, r2], key="23456789TJQKA".index, reverse=True))
        suited = "s" if s1 == s2 else "o"
        key = ranks + suited if r1 != r2 else r1 + r2

        if key in self.PREFLOP_RANGES["premium"]: return "premium"
        if key in self.PREFLOP_RANGES["strong"]: return "strong"
        if key in self.PREFLOP_RANGES["playable"]: return "playable"
        if key.endswith("s") and key[0] == "A" and key[1] in "23456789": return "marginal"
        return "weak"

    def _preflop_equity_proxy(self, hole):
        return {"premium":0.78,"strong":0.62,"playable":0.56,"marginal":0.52,"weak":0.46}[self._classify_preflop(hole)]

    @lru_cache(maxsize=1024)
    def _build_deck(self, hole_tuple, community_tuple):
        all_cards = [s+r for s in "SCDH" for r in "23456789TJQKA"]
        used = set(hole_tuple) | set(community_tuple)
        return [c for c in all_cards if c not in used]

    def _evaluate_hand_strength(self, cards):
        if len(cards) < 5: return 0
        rank_map = "23456789TJQKA"
        ranks = sorted([rank_map.index(c[1]) for c in cards], reverse=True)
        suits = [c[0] for c in cards]

        flush = any(suits.count(s) >= 5 for s in set(suits))
        uniq = sorted(set(ranks), reverse=True)
        
        # Fixed straight detection including wheel (A-2-3-4-5)
        is_wheel = set([12,0,1,2,3]).issubset(set(uniq))
        regular_straight = any(uniq[i] - uniq[i+4] == 4 for i in range(len(uniq)-4))
        straight = is_wheel or regular_straight

        counts = sorted(Counter(ranks).values(), reverse=True)
        max_rank = max(ranks)

        if flush and straight and max_rank == 12: return 9  # Royal flush
        if flush and straight: return 8  # Straight flush
        if counts[0] == 4: return 7  # Quads
        if counts[0] == 3 and counts[1] == 2: return 6  # Full house
        if flush: return 5  # Flush
        if straight: return 4  # Straight
        if counts[0] == 3: return 3  # Trips
        if counts[0] == 2 and counts[1] == 2: return 2  # Two pair
        if counts[0] == 2: return 1  # Pair
        return 0  # High card

    def _cached_monte_carlo(self, hero, board, n=1000):
        """Simplified Monte Carlo without villain cards"""      

        cache_key = (tuple(sorted(hero)), tuple(sorted(board)), n)
        if cache_key in self._equity_cache:
            return self._equity_cache[cache_key]

        deck = self._build_deck(tuple(hero), tuple(board))
        wins = 0.0

        for _ in range(n):
            remaining = 5 - len(board)
            # Draw random opponent hole cards and remaining board
            sample_size = remaining + 2
            if len(deck) < sample_size:
                # Fallback if deck too small
                return 0.5
                
            draw = self._rng.sample(deck, sample_size)
            add_board = draw[:remaining]
            opp_hole = draw[remaining:]

            full_board = board + add_board
            my_score = self._evaluate_hand_strength(hero + full_board)
            opp_score = self._evaluate_hand_strength(opp_hole + full_board)

            if my_score > opp_score: 
                wins += 1.0
            elif my_score == opp_score: 
                wins += 0.5

        equity = wins / n
        if len(self._equity_cache) < 10000:  # Prevent unbounded growth
            self._equity_cache[cache_key] = equity
        return equity

    def _calculate_equity(self, hole, community, num_simulations=1000):
        if not community: 
            return self._preflop_equity_proxy(hole)
        return self._cached_monte_carlo(hole, community, num_simulations)

    def _get_opponent_tendencies(self, round_state):
        """Analyze opponent behavior for this hand"""
        active_opponents = []
        for seat in round_state["seats"]:
            if seat["uuid"] != self.uuid and seat["state"] == "participating":
                stats = self.opponent_stats[seat["uuid"]]
                active_opponents.append({
                    "uuid": seat["uuid"],
                    "stack": seat["stack"],
                    "aggression": stats["aggression"],
                    "fold_to_raise": stats["fold_to_raise"]
                })
        
        avg_aggression = sum(p["aggression"] for p in active_opponents) / len(active_opponents) if active_opponents else 0.5
        avg_fold_frequency = sum(p["fold_to_raise"] for p in active_opponents) / len(active_opponents) if active_opponents else 0.5
        
        return {
            "avg_aggression": avg_aggression,
            "avg_fold_frequency": avg_fold_frequency,
            "num_opponents": len(active_opponents)
        }

    def _calculate_bet_sizing(self, action_type, equity, pot_size, position_factor, opponent_tendencies):
        """Dynamic bet sizing based on situation"""
        base_size = pot_size * 0.75  # Default 3/4 pot
        
        if action_type == ActionType.VALUE_BET:
            # Size up with strong hands, especially against calling stations
            fold_frequency = opponent_tendencies["avg_fold_frequency"]
            size_multiplier = 1.0 + (1.0 - fold_frequency) * 0.5
            return base_size * size_multiplier * min(equity * 2, 1.2)
            
        elif action_type == ActionType.BLUFF:
            # Smaller bluffs against tight opponents
            fold_frequency = opponent_tendencies["avg_fold_frequency"]
            return base_size * (0.6 + fold_frequency * 0.4)
            
        elif action_type == ActionType.PROTECTION:
            # Bet to charge draws
            return pot_size * 0.8
            
        elif action_type == ActionType.STEAL:
            # Position-based steal sizing
            return pot_size * (0.4 + position_factor * 0.3)
            
        return base_size

    def _determine_action_type(self, equity, position, board_texture, opponent_tendencies):
        """Classify what type of action we should take"""
        pos_factor = self._position_adjustment(position)
        
        # Strong hands - value bet
        if equity > 0.65:
            return ActionType.VALUE_BET
            
        # Decent hands - protection bet if board is draw-heavy
        elif equity > 0.55 and self._is_draw_heavy_board(board_texture):
            return ActionType.PROTECTION
            
        # Marginal hands in position - potential steal
        elif 0.45 <= equity <= 0.55 and pos_factor > 1.0:
            if opponent_tendencies["avg_fold_frequency"] > 0.6:
                return ActionType.STEAL
            else:
                return ActionType.CALL_DRAW
                
        # Weak hands but good bluff spots
        elif equity < 0.45 and pos_factor > 1.1 and opponent_tendencies["avg_fold_frequency"] > 0.7:
            return ActionType.BLUFF
            
        # Drawing hands
        elif 0.35 <= equity <= 0.55:
            return ActionType.CALL_DRAW
            
        # Weak hands
        else:
            return ActionType.FOLD_WEAK

    def _is_draw_heavy_board(self, community_cards):
        """Check if board has many drawing opportunities"""
        if len(community_cards) < 3:
            return False
            
        suits = [card[0] for card in community_cards]
        ranks = [card[1] for card in community_cards]
        
        # Flush draws
        flush_draws = any(suits.count(suit) >= 3 for suit in set(suits))
        
        # Straight draws (simplified check)
        rank_values = ["23456789TJQKA".index(r) for r in ranks]
        rank_values.sort()
        straight_draws = any(
            rank_values[i+1] - rank_values[i] <= 2 
            for i in range(len(rank_values)-1)
        )
        
        return flush_draws or straight_draws

    def declare_action(self, valid_actions, hole_card, round_state):
        street = round_state['street']
        self._reset_street_counters(street)
        
        # Get available actions
        fold_action = next((a for a in valid_actions if a["action"] == "fold"), None)
        call_action = next((a for a in valid_actions if a["action"] == "call"), None)
        raise_action = next((a for a in valid_actions if a["action"] == "raise"), None)
        
        # Basic game state
        position = self._get_position(round_state)
        community_cards = round_state.get("community_card", [])
        pot_size = round_state.get("pot", {}).get("main", {}).get("amount", 0)
        
        # Calculate equity and position factor
        equity = self._calculate_equity(hole_card, community_cards)
        pos_factor = self._position_adjustment(position, len(round_state["seats"]))
        adjusted_equity = min(1.0, equity * pos_factor)
        
        # Get opponent information
        opponent_tendencies = self._get_opponent_tendencies(round_state)
        
        # Calculate pot odds
        call_amount = call_action["amount"] if call_action else 0
        pot_odds = call_amount / (pot_size + call_amount) if call_amount > 0 else 0.0
        
        # Limit raises per street
        if self._raise_count_this_street(street) >= 2:
            raise_action = None
            
        # Determine action type
        action_type = self._determine_action_type(
            adjusted_equity, position, community_cards, opponent_tendencies
        )
        
        # Execute decision based on action type
        if action_type == ActionType.VALUE_BET and raise_action:
            bet_size = self._calculate_bet_sizing(
                action_type, adjusted_equity, pot_size, pos_factor, opponent_tendencies
            )
            bet_size = max(raise_action["amount"]["min"], min(bet_size, raise_action["amount"]["max"]))
            self._street_raises[street] += 1
            return "raise", int(bet_size)
            
        elif action_type == ActionType.BLUFF and raise_action:
            if self._rng.random() < 0.3:  # Don't bluff too often
                bet_size = self._calculate_bet_sizing(
                    action_type, adjusted_equity, pot_size, pos_factor, opponent_tendencies
                )
                bet_size = max(raise_action["amount"]["min"], min(bet_size, raise_action["amount"]["max"]))
                self._street_raises[street] += 1
                return "raise", int(bet_size)
                
        elif action_type == ActionType.PROTECTION and raise_action:
            bet_size = self._calculate_bet_sizing(
                action_type, adjusted_equity, pot_size, pos_factor, opponent_tendencies
            )
            bet_size = max(raise_action["amount"]["min"], min(bet_size, raise_action["amount"]["max"]))
            self._street_raises[street] += 1
            return "raise", int(bet_size)
            
        elif action_type == ActionType.STEAL and raise_action:
            if opponent_tendencies["avg_fold_frequency"] > 0.6:
                bet_size = self._calculate_bet_sizing(
                    action_type, adjusted_equity, pot_size, pos_factor, opponent_tendencies
                )
                bet_size = max(raise_action["amount"]["min"], min(bet_size, raise_action["amount"]["max"]))
                self._street_raises[street] += 1
                return "raise", int(bet_size)
                
        elif action_type == ActionType.CALL_DRAW and call_action:
            # Call if we have proper odds or implied odds
            if adjusted_equity >= pot_odds or (adjusted_equity > pot_odds * 0.7 and pos_factor > 1.0):
                return "call", call_amount
                
        # Default: fold weak hands or when pot odds don't justify call
        if call_action and adjusted_equity > pot_odds + 0.1:
            return "call", call_amount
            
        return "fold", 0

    def receive_game_start_message(self, game_info): 
        pass
        
    def receive_round_start_message(self, round_count, hole_card, seats): 
        pass
        
    def receive_street_start_message(self, street, round_state): 
        pass
        
    def receive_game_update_message(self, action, round_state): 
        # Update opponent stats based on their actions
        actor_uuid = action['player_uuid']
        if actor_uuid != self.uuid:
            street = round_state['street']
            self._update_stats(actor_uuid, street, action)
            
    def receive_round_result_message(self, winners, hand_info, round_state): 
        pass

def setup_ai():
    return CodeforcesNoob()