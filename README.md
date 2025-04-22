# Text‑based Texas Hold’em ♠️♦️♣️♥️

A lightweight command‑line Texas Hold’em game (Python 3.8+).  
It pits **you against 3 random opponents** and shows real‑time
Monte‑Carlo equity (% chance to win / tie / lose) at every street.

## Quick start

```bash
python poker_simulator.py            # fully interactive
python poker_simulator.py -a         # automatic decisions (no input)
python poker_simulator.py -a -n 3    # play 3 auto hands then quit
python poker_simulator.py --sims 2000  # 2 000 Monte‑Carlo sims per street
```
