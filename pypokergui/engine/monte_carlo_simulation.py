from bots.mybot import setup_ai as cf_noob
from bots.sample_player.fish_player_setup import FishPlayer
from pypokergui.engine.batch_test import SimulationEngineWrapper

def run_simulation():
    # Create simulation engine
    engine = SimulationEngineWrapper()

    # Register players
    players = {
        "ai1": cf_noob(),
        "ai2": FishPlayer()
    }

    # Configure game
    config = engine.gen_game_config(
        max_round=1000,
        initial_stack=1000,
        small_blind=10,
        ante=0
    )

    # Run simulation
    engine.run_simulation(players, config, n_rounds=1000)

    # Generate report
    engine.generate_report()