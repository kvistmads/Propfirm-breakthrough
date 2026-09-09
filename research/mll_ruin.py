"""Ruinmodel for Topstep $50K Trading Combine — aabent spoergsmaal 1.

Svarer paa: hvor stor maa en handel vaere, naar Maximum Loss Limit er $2.000 og
profitmaalet $3.000, og hvordan fordeler udfaldene sig mellem BESTAAET og RUIN?

Mekanikken er 1:1 med Topsteps egen (verificeret 2026-09-09 fra help.topstep.com):

  start            saldo $50.000, MLL $48.000
  MLL trailer      paa DAGSSLUTsaldo: mll = min(50.000, max(mll, saldo - 2.000))
                   Aldrig nedad. Laaser permanent naar den naar startsaldoen.
  MLL brydes       paa net P&L i REALTID inkl. urealiseret -> oejeblikkelig likvidering
  DLL              $1.000 (valgfri, slaaet TIL): dagen lukkes, kontoen lever
  profitmaal       $3.000
  konsistens       bedste dag skal under 50% af profitmaalet, ellers HAEVES maalet
                   -> bestaaet kraever profit >= max(3.000, 2 x bedste dag)
  min. dage        2

Trailet er dagsslut, bruddet er realtid. Det er ikke det samme, og forskellen er
hele grunden til at intradag give-back er gratis hos Topstep men ruinerende hos en
intraday-trailing udbyder.

## De to brudmodeller

Vi kender handlens udfald, men ikke dens vej. En vinder kan have vaeret dybt under
vand foerst; det er ikke maalt (aabent spoergsmaal 10, slippage/MAE). Derfor koeres
begge grænser frem for at gaette imellem dem:

  optimistisk   kontoen doer kun naar et stop FAKTISK rammes
  pessimistisk  kontoen doer saa snart en handel aabnes hvis stoppet ville bryde MLL

Sandheden ligger imellem. Spaendet mellem de to ER usikkerheden paa modellen, og
den er som regel stoerre end stikproveusikkerheden.

Gates hoerer til i live: modellen afviser ALDRIG en handel fordi den er farlig.
Den lader den blive taget og registrerer konsekvensen.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.stats import breakeven_win_rate, wilson_interval  # noqa: E402

START_BALANCE = 50_000.0
MLL_ROOM = 2_000.0
MLL_LOCK = 50_000.0
PROFIT_TARGET = 3_000.0
DLL = 1_000.0
MIN_DAYS = 2
CONSISTENCY_FRAC = 0.50

MNQ_MULTIPLIER = 2.0
NQ_PRICE = 29_639.50
ATR_PCT_15M = 0.00168
COST_USD_ROUND_TURN = 2.472

MAX_TRADES_PER_DAY = 3
MAX_DAYS = 200
N_PATHS = 20_000
SEED = 20260909


def r_per_contract(stop_atr: float) -> float:
    return ATR_PCT_15M * NQ_PRICE * MNQ_MULTIPLIER * stop_atr


def simulate(n_paths, wr, stop_atr, contracts, pessimistisk, net, rng):
    R_c = r_per_contract(stop_atr)
    c = COST_USD_ROUND_TURN if net else 0.0
    win_amt = contracts * (2.0 * R_c - c)
    loss_amt = contracts * (-R_c - c)
    mae = contracts * (R_c + c)

    bal = np.full(n_paths, START_BALANCE)
    mll = np.full(n_paths, START_BALANCE - MLL_ROOM)
    best_day = np.zeros(n_paths)
    days = np.zeros(n_paths, dtype=np.int32)
    alive = np.ones(n_paths, dtype=bool)
    passed = np.zeros(n_paths, dtype=bool)
    ruined = np.zeros(n_paths, dtype=bool)

    for _ in range(MAX_DAYS):
        if not alive.any():
            break
        day_pnl = np.zeros(n_paths)
        n_trades = rng.integers(1, MAX_TRADES_PER_DAY + 1, n_paths)

        for slot in range(MAX_TRADES_PER_DAY):
            take = alive & (slot < n_trades) & (day_pnl > -DLL)
            if not take.any():
                continue
            wins = rng.random(n_paths) < wr
            breach = (bal - mae) <= mll
            dead = take & breach if pessimistisk else take & breach & ~wins

            ruined |= dead
            alive &= ~dead

            live = take & ~dead
            delta = np.where(wins, win_amt, loss_amt)
            bal = np.where(live, bal + delta, bal)
            day_pnl = np.where(live, day_pnl + delta, day_pnl)

        days += alive
        best_day = np.where(alive, np.maximum(best_day, day_pnl), best_day)
        mll = np.where(alive, np.minimum(MLL_LOCK, np.maximum(mll, bal - MLL_ROOM)), mll)

        target = np.maximum(PROFIT_TARGET, best_day / CONSISTENCY_FRAC)
        won = alive & (days >= MIN_DAYS) & ((bal - START_BALANCE) >= target)
        passed |= won
        alive &= ~won

    return {
        "bestaaet": int(passed.sum()),
        "ruin": int(ruined.sum()),
        "uafgjort": int(alive.sum()),
        "median_dage_bestaaet": float(np.median(days[passed])) if passed.any() else float("nan"),
        "median_dage_ruin": float(np.median(days[ruined])) if ruined.any() else float("nan"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", type=int, default=N_PATHS)
    ap.add_argument("--out", default="research/output/mll_ruin")
    args = ap.parse_args()

    contracts_grid = (1, 2, 3)
    stop_grid = (0.50, 0.75, 1.00)
    wr_grid = (0.34, 0.37, 0.40, 0.45)

    rows = []
    for contracts in contracts_grid:
        for stop_atr in stop_grid:
            R_c = r_per_contract(stop_atr)
            omk_r = COST_USD_ROUND_TURN / R_c
            be_wr = breakeven_win_rate(2.0, 1.0, omk_r)
            for wr in wr_grid:
                row = {
                    "kontrakter": contracts,
                    "stop_ATR": stop_atr,
                    "R_pr_kontrakt_usd": round(R_c, 2),
                    "risiko_pr_handel_usd": round(contracts * (R_c + COST_USD_ROUND_TURN), 2),
                    "risiko_pct_af_MLL": round(100 * contracts * (R_c + COST_USD_ROUND_TURN) / MLL_ROOM, 2),
                    "omk_R_netto": round(omk_r, 4),
                    "be_WR_pct": round(100 * be_wr, 2),
                    "antaget_WR_pct": round(100 * wr, 1),
                    "edge_pp": round(100 * (wr - be_wr), 2),
                }
                for net, mrk in ((True, "netto"), (False, "brutto")):
                    for pess, pmrk in ((False, "opt"), (True, "pess")):
                        rng = np.random.default_rng(
                            SEED + contracts * 1000 + int(stop_atr * 100) * 10 + int(wr * 100)
                        )
                        r = simulate(args.paths, wr, stop_atr, contracts, pess, net, rng)
                        n = args.paths
                        lo, hi = wilson_interval(r["bestaaet"], n)
                        rlo, rhi = wilson_interval(r["ruin"], n)
                        row[f"bestaa_pct_{mrk}_{pmrk}"] = round(100 * r["bestaaet"] / n, 2)
                        row[f"bestaa_CI_{mrk}_{pmrk}"] = f"[{100*lo:.1f}, {100*hi:.1f}]"
                        row[f"ruin_pct_{mrk}_{pmrk}"] = round(100 * r["ruin"] / n, 2)
                        row[f"ruin_CI_{mrk}_{pmrk}"] = f"[{100*rlo:.1f}, {100*rhi:.1f}]"
                        row[f"uafgjort_pct_{mrk}_{pmrk}"] = round(100 * r["uafgjort"] / n, 2)
                        if mrk == "netto" and pmrk == "opt":
                            row["median_dage_bestaaet"] = r["median_dage_bestaaet"]
                rows.append(row)
                print(f"  {contracts}x {stop_atr:.2f}ATR WR{100*wr:.0f}%  "
                      f"bestaa {row['bestaa_pct_netto_opt']:.1f}%  "
                      f"ruin {row['ruin_pct_netto_opt']:.1f}%  "
                      f"(pess ruin {row['ruin_pct_netto_pess']:.1f}%)", flush=True)

    import csv
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out.with_suffix(".csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"\nskrevet: {out.with_suffix('.csv')}  ({len(rows)} celler, {args.paths} stier pr. celle)")


if __name__ == "__main__":
    main()
