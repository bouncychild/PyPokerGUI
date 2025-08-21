import matplotlib as plt
import numpy as np

def plot_results(results):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    # BB/100 with CI
    ax1.bar([r['opponent'] for r in results],
            [r['bb_per_100'] for r in results],
            yerr=[(r['bb_per_100']-r['ci'][0]) for r in results],
            capsize=5)
    ax1.set_title('BB/100 vs Opponents (95% CI)')
    ax1.axhline(8, color='red', linestyle='--')
    
    # Cumulative BB
    for r in results:
        ax2.plot(np.cumsum(r['bb_history']), label=r['opponent'])
    ax2.set_title('Cumulative Bankroll')
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig('results.png')