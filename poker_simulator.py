# poker_simulator.py
"""
Text‑based Texas Hold’em Simulator – COMPLETE & RUNNABLE
=======================================================
Run examples
------------
```bash
python poker_simulator.py           # fully interactive
python poker_simulator.py -a        # auto decisions
python poker_simulator.py -a -n 3   # play 3 auto hands then quit
python poker_simulator.py --sims 2000  # use 2k Monte‑Carlo sims
```

"""

from __future__ import annotations

import argparse
import itertools
import random
import sys
from collections import Counter
from typing import Dict, List, Tuple

# ────────── Card helpers ──────────
RANKS = "23456789TJQKA"
SUITS = "cdhs"
SUIT_SYM = {"c": "♣", "d": "♦", "h": "♥", "s": "♠"}
RANK_VAL: Dict[str, int] = {r: i for i, r in enumerate(RANKS, start=2)}

def deck() -> List[str]:
    return [r + s for r in RANKS for s in SUITS]

def pc(card: str) -> str:
    return f"{card[0]}{SUIT_SYM[card[1]]}"

def join(cs: List[str]) -> str:
    return " ".join(pc(c) for c in cs)

# ────────── Hand ranking ──────────
CATS = ["High Card","One Pair","Two Pair","Trips","Straight","Flush","Full House","Quads","Straight Flush"]
CAT_SCORE = {n: i for i, n in enumerate(CATS)}

def _is_straight(vals: List[int]) -> Tuple[bool,int]:
    vals = sorted(set(vals), reverse=True)
    if {14,5,4,3,2}.issubset(vals):
        return True,5
    for i in range(len(vals)-4):
        if vals[i]-vals[i+4]==4:
            return True, vals[i]
    return False,0

def _rank5(cards: Tuple[str,...]) -> Tuple[int,List[int]]:
    vals = sorted((RANK_VAL[c[0]] for c in cards), reverse=True)
    suits = [c[1] for c in cards]
    cnt = Counter(vals).most_common()
    flush = len(set(suits))==1
    straight, top = _is_straight(vals)
    if flush and straight:
        return CAT_SCORE["Straight Flush"],[top]
    if cnt[0][1]==4:
        quad=cnt[0][0]
        kicker=max(v for v in vals if v!=quad)
        return CAT_SCORE["Quads"],[quad,kicker]
    if cnt[0][1]==3 and cnt[1][1]==2:
        return CAT_SCORE["Full House"],[cnt[0][0],cnt[1][0]]
    if flush:
        return CAT_SCORE["Flush"],vals
    if straight:
        return CAT_SCORE["Straight"],[top]
    if cnt[0][1]==3:
        trips=cnt[0][0]
        kick=[v for v in vals if v!=trips][:2]
        return CAT_SCORE["Trips"],[trips]+kick
    if cnt[0][1]==2 and cnt[1][1]==2:
        high, low = max(cnt[0][0],cnt[1][0]), min(cnt[0][0],cnt[1][0])
        kicker=max(v for v in vals if v not in (high,low))
        return CAT_SCORE["Two Pair"],[high,low,kicker]
    if cnt[0][1]==2:
        pair=cnt[0][0]
        kick=[v for v in vals if v!=pair][:3]
        return CAT_SCORE["One Pair"],[pair]+kick
    return CAT_SCORE["High Card"],vals

def best7(seven: List[str]) -> Tuple[int,List[int]]:
    return max(_rank5(comb) for comb in itertools.combinations(seven,5))

# ────────── Monte‑Carlo equity ──────────

def equity(player: List[str], board: List[str], opp_n:int, sims:int) -> Tuple[float,float,float]:
    wins=ties=0
    master=deck()
    for c in player+board:
        master.remove(c)
    need=(5-len(board))+opp_n*2
    if need>len(master):
        return 0,0,100
    for _ in range(sims):
        d=master.copy(); random.shuffle(d)
        comm=board+[d.pop() for _ in range(5-len(board))]
        opps=[[d.pop(),d.pop()] for _ in range(opp_n)]
        pr=best7(player+comm)
        opp_rs=[best7(o+comm) for o in opps]
        best=max([pr]+opp_rs)
        if pr==best:
            if opp_rs.count(best)==0: wins+=1
            else: ties+=1
    total=sims
    return wins*100/total, ties*100/total, (total-wins-ties)*100/total

# ────────── AI helpers ──────────

def suggest(win:float)->str:
    if win>=55: return "RAISE"
    if win>=35: return "CALL/CHECK"
    return "FOLD"

def auto_decision(win:float, street:int)->str:
    if win<25: return "fold"
    if street==0 and win<40: return "call"
    return "check"

# ────────── Play one hand ──────────

def play_hand(interactive:bool,sims:int)->bool:
    d=deck(); random.shuffle(d)
    player=[d.pop(),d.pop()]
    opps=[[d.pop(),d.pop()] for _ in range(3)]
    board:List[str]=[]
    stage={0:"Pre‑flop",3:"Flop",4:"Turn",5:"River"}
    while True:
        win,tie,lose=equity(player,board,3,sims)
        print("\n"+"="*60)
        print(f"*** {stage[len(board)]} ***")
        print("Your hand  :",join(player))
        print("Board      :",join(board) if board else "--")
        print(f"Win/Tie/Lose: {win:5.1f}% | {tie:4.1f}% | {lose:5.1f}%")
        print("Suggested  :",suggest(win))
        valid=("fold","call","raise") if len(board)==0 else ("fold","check","call","raise")
        if interactive:
            try:
                move=input(f"Your move ({'/'.join(valid)}): ").strip().lower()
            except (EOFError,OSError):
                print("⚠️ stdin lost – auto mode")
                interactive=False; move=auto_decision(win,len(board)); print(f"[AUTO] {move.upper()}")
            while interactive and move not in valid:
                move=input("❌ Invalid – try again: ").strip().lower()
        else:
            move=auto_decision(win,len(board)); print(f"[AUTO] {move.upper()}")
        if move=="fold":
            print("\n🚪 You folded."); return True
        # deal next street
        if len(board)==0:
            board.extend([d.pop() for _ in range(3)])
        elif len(board)==3:
            board.append(d.pop())
        elif len(board)==4:
            board.append(d.pop())
        else:
            break
    # showdown
    print("\n"+"="*60)
    print("*** Showdown ***")
    print("Board :",join(board))
    print("You   :",join(player))
    for i,o in enumerate(opps,1):
        print(f"Opp {i}:",join(o))
    pr=best7(player+board)
    opp_rs=[best7(o+board) for o in opps]
    everyone=[("You",pr)]+[(f"Opp {i+1}",r) for i,r in enumerate(opp_rs)]
    best=max(r for _,r in everyone)
    winners=[n for n,r in everyone if r==best]
    print("\nResult:"," / ".join(winners),"win!" if len(winners)==1 else "split pot")
    return True

# ────────── Main ──────────

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('-a','--auto',action='store_true',help='auto mode')
    ap.add_argument('-n','--hands',type=int,help='hands to play (auto)')
    ap.add_argument('--sims',type=int,default=1000,help='Monte‑Carlo sims')
    args=ap.parse_args()
    interactive=not args.auto
    remaining=args.hands if args.auto else None
    try:
        while True:
            play_hand(interactive,args.sims)
            if interactive:
                again=input("\nPlay another hand? (y/n): ").strip().lower()
                if again!='y': break
            else:
                if remaining is not None:
                    remaining-=1
                    if remaining<=0: break
    except KeyboardInterrupt:
        print("\n👋 Exiting. Bye!")
        sys.exit()

if __name__=='__main__':
    main()
