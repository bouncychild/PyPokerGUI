METRICS = 
    analytics_enabled = False
    output_dir = None
    setup_output_directory()
        
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