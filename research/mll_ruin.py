"""Ruinmodel v2 for Topstep $50K Trading Combine — B6: sizing på det målte grundlag.

    .venv/bin/python -m research.mll_ruin k1        K1-regressionstjekket
    .venv/bin/python -m research.mll_ruin gitter    gitteret, kræver at K1 holdt

Svarer på: hvor stor må en handel være, når Maximum Loss Limit er $2.000 og profitmålet
$3.000, og hvordan fordeler udfaldene sig mellem BESTÅET, RUIN og UAFGJORT (horisonten
nået)? Opgaven står i ``PRD_FASE2_RUINMODEL.md``; kriterierne K1-K5 i dens afsnit 3.

Mekanikken er 1:1 med Topsteps egen (verificeret 2026-09-09 fra help.topstep.com):

  start            saldo $50.000, MLL $48.000
  MLL trailer      på DAGSSLUTsaldo: mll = min(50.000, max(mll, saldo - 2.000))
                   Aldrig nedad. Låser permanent når den når startsaldoen.
  MLL brydes       på net P&L i REALTID inkl. urealiseret -> øjeblikkelig likvidering
  DLL              $1.000 (valgfri, slået TIL): dagen lukkes, kontoen lever
  profitmål        $3.000
  konsistens       bedste dag skal under 50% af profitmålet, ellers HÆVES målet
                   -> bestået kræver profit >= max(3.000, 2 x bedste dag)
  min. dage        2

Trailet er dagsslut, bruddet er realtid. Trailet regnes på en flad konto: ingen position
er åben ved dagsgrænsen. **Det var en antagelse (A) i v1 og er nu en regel (V):** Topstep
kræver alt fladt kl. 15:10 CT hver hverdag (verificeret 2026-09-12, STRATEGI_PROPFIRM §3).

## Hvad v2 ændrer — og kun det

v1 (kørt 2026-09-09) gav hver handel samme dollarrisiko: ATR 0,168% × NQ 29.639,50. v2
trækker **R pr. handel fra den empiriske ATR-fordeling** for cellens timeframe i US RTH:
et uafhængigt træk med tilbagelægning blandt de faktisk målte barer. Ingen tilpasset
fordeling — halen er pointen, og en normalfordeling ville skære den af.

ATR-trækkene kommer fra **en egen tilfældighedsstrøm**. Vinder/taber-trækkene og antal
handler pr. dag bruger præcis samme strøm og rækkefølge som v1. Fodres modellen med én
konstant ATR, reproducerer den derfor v1 træk for træk — det er K1.

Hver handel er uafhængig af den forrige, også i sin ATR. Modellen ser dermed at en høj
ATR gør et tab dyrere, men ikke at høje ATR'er klumper sig i tid (flere dyre handler i
samme uge). Det er ikke modelleret.

## De to brudmodeller

Vi kender handlens udfald, men ikke dens vej. En vinder kan have været dybt under vand
først; det er ikke målt (C4, slippage og sti). Derfor køres begge grænser:

  optimistisk   kontoen dør kun når et stop FAKTISK rammes
  pessimistisk  kontoen dør så snart en handel åbnes hvis stoppet ville bryde MLL

Sandheden ligger imellem. Spændet mellem de to er usikkerheden på modellen (K4).

Gates hører til i live: modellen afviser ALDRIG en handel fordi den er farlig.

## Nulmodellen

Hver celle køres også med win rate sat til cellens egen break-even — nul edge. Uden den
ved man ikke om en høj beståelsesrate kommer fra strategien eller fra at Topsteps
regelgeometri er mild ved den sizing (metoderegel 12).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.stats import proportion_diff_interval, wilson_interval  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "output"

START_BALANCE = 50_000.0
MLL_ROOM = 2_000.0
MLL_LOCK = 50_000.0
PROFIT_TARGET = 3_000.0
DLL = 1_000.0
MIN_DAYS = 2
CONSISTENCY_FRAC = 0.50

MNQ_MULTIPLIER = 2.0
RR = 2.0

MAX_TRADES_PER_DAY = 3
MAX_DAYS = 200
N_PATHS = 20_000
SEED = 20260909

# K1 — regressionens input: gitteret fra 2026-09-09 (research/output/mll_ruin.csv).
# Bruges KUN af k1(). Ingen af tallene indgår i gitteret.
K1_ATR_PCT = 0.168
K1_NQ = 29_639.50
K1_OMK_USD = 2.472
K1_KONTRAKTER = (1, 2, 3)
K1_STOP_ATR = (0.50, 0.75, 1.00)
K1_WR = (0.34, 0.37, 0.40, 0.45)
K1_REFERENCE = OUT / "mll_ruin.csv"
K1_UD = OUT / "mll_ruin_v2_k1.csv"
K1_RESUME = OUT / "mll_ruin_v2_k1.json"


# ---------------------------------------------------------------------------
# Modellen
# ---------------------------------------------------------------------------

def r_usd(atr_pct, nq: float, stop_atr: float):
    """1R for én MNQ: stopafstanden i dollar. ``atr_pct`` i procent af prisen.

    ``nq`` er ÉT fast, nutidigt prisniveau for alle træk — ikke barens historiske pris.
    MLL'en er $2.000 i dagens dollar. NQ lukkede RTH i 4.490 den 2016-01-04, 7.808,50
    den 2019-05-06 og 29.138 den 2026-09-10, så samme ATR i procent er 6,5 gange flere
    dollar i dag end i 2016. Trak vi prisen med fra baren, ville modellen blande regimer
    og systematisk undervurdere risikoen mod et gulv der står i nutidige dollar.
    """
    return atr_pct / 100.0 * nq * MNQ_MULTIPLIER * stop_atr


def seed_v1(contracts: int, stop_atr: float, wr: float) -> int:
    """v1's seed pr. celle. Kun til K1."""
    return SEED + contracts * 1000 + int(stop_atr * 100) * 10 + int(wr * 100)


def simulate(n_paths: int, wr: float, stop_atr: float, contracts: int, pessimistisk: bool,
             omk_usd: float, atr_pct, nq: float, seed: int) -> dict:
    """Én celle. ``atr_pct`` er den empiriske fordeling (array) eller én konstant.

    ``omk_usd`` er rundturen pr. kontrakt; 0 giver brutto.
    """
    rng = np.random.default_rng(seed)
    atr = np.atleast_1d(np.asarray(atr_pct, dtype=float))
    konstant = atr.size == 1
    # Egen strøm til ATR: vinder/taber-trækkene er de samme som i v1 (K1).
    rng_atr = None if konstant else np.random.default_rng([seed, 1])
    r_konstant = r_usd(float(atr[0]), nq, stop_atr) if konstant else None
    c = float(omk_usd)

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
            # Trækkes før `take`, så ATR-strømmen forbruges ens uanset tilstand.
            R_c = r_konstant if konstant else r_usd(
                atr[rng_atr.integers(0, atr.size, n_paths)], nq, stop_atr)
            take = alive & (slot < n_trades) & (day_pnl > -DLL)
            if not take.any():
                continue
            win_amt = contracts * (RR * R_c - c)
            loss_amt = contracts * (-R_c - c)
            mae = contracts * (R_c + c)
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
        "n": n_paths,
        "bestaaet": int(passed.sum()),
        "ruin": int(ruined.sum()),
        "uafgjort": int(alive.sum()),
        "median_dage_bestaaet": float(np.median(days[passed])) if passed.any() else float("nan"),
        "median_dage_ruin": float(np.median(days[ruined])) if ruined.any() else float("nan"),
    }


def be_wr(omk_usd: float, r_middel_usd: float) -> float:
    """Break-even win rate ved 2:1: nul forventet P&L pr. handel.

        EV = WR·(2·E[R] − c) − (1−WR)·(E[R] + c) = 0  ⇔  WR = (1 + c/E[R]) / 3

    Med R trukket pr. handel er det MIDDELVÆRDIEN af R der giver nul edge.
    """
    return (1.0 + omk_usd / r_middel_usd) / (RR + 1.0)


# ---------------------------------------------------------------------------
# K1 — regressionstjek mod gitteret fra 2026-09-09
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class K1Resultat:
    n_sammenligninger: int
    n_inden_for_CI: int
    n_identiske: int
    max_afvigelse_pp: float
    deterministiske_ok: bool

    @property
    def holdt(self) -> bool:
        return self.n_inden_for_CI == self.n_sammenligninger and self.deterministiske_ok


def _laes_reference() -> list[dict]:
    with open(K1_REFERENCE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def k1(n_paths: int = N_PATHS) -> K1Resultat:
    """Konstant ATR 0,168%, NQ 29.639,50, omk. $2,472 — hver celle mod sit 95%-CI.

    CI'et er v1's Wilson-interval, genberegnet af v1's andel (antal = andel × n).
    ``identisk`` betyder samme tal op til v1's afrunding på to decimaler.
    """
    ref = {(int(r["kontrakter"]), float(r["stop_ATR"]), float(r["antaget_WR_pct"])): r
           for r in _laes_reference()}
    rows, det_ok = [], True
    for k in K1_KONTRAKTER:
        for stop in K1_STOP_ATR:
            R_c = r_usd(K1_ATR_PCT, K1_NQ, stop)
            omk_r = K1_OMK_USD / R_c
            for wr in K1_WR:
                v1 = ref[(k, stop, round(100 * wr, 1))]
                det = {
                    "R_pr_kontrakt_usd": round(R_c, 2),
                    "risiko_pr_handel_usd": round(k * (R_c + K1_OMK_USD), 2),
                    "risiko_pct_af_MLL": round(100 * k * (R_c + K1_OMK_USD) / MLL_ROOM, 2),
                    "omk_R_netto": round(omk_r, 4),
                    "be_WR_pct": round(100 * be_wr(K1_OMK_USD, R_c), 2),
                }
                for navn, v in det.items():
                    if abs(float(v1[navn]) - v) > 1e-9:
                        det_ok = False
                for omk, omk_navn in ((K1_OMK_USD, "netto"), (0.0, "brutto")):
                    for pess, bm in ((False, "opt"), (True, "pess")):
                        r = simulate(n_paths, wr, stop, k, pess, omk, K1_ATR_PCT, K1_NQ,
                                     seed_v1(k, stop, wr))
                        for maal, noegle in (("bestaa", "bestaaet"), ("ruin", "ruin"),
                                             ("uafgjort", "uafgjort")):
                            p1 = float(v1[f"{maal}_pct_{omk_navn}_{bm}"])
                            lo, hi = wilson_interval(round(p1 / 100 * n_paths), n_paths)
                            p2 = 100 * r[noegle] / n_paths
                            rows.append({
                                "kontrakter": k, "stop_ATR": stop, "WR_pct": round(100 * wr, 1),
                                "omk": omk_navn, "brudmodel": bm, "maal": maal,
                                "pct_v1": p1, "CI95_lav_v1": round(100 * lo, 3),
                                "CI95_hoej_v1": round(100 * hi, 3), "pct_v2": p2,
                                "afvigelse_pp": round(p2 - p1, 3),
                                "inden_for_CI": 100 * lo <= p2 <= 100 * hi,
                                "identisk": abs(p2 - p1) <= 0.005 + 1e-9,
                            })
    K1_UD.parent.mkdir(parents=True, exist_ok=True)
    with open(K1_UD, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    res = K1Resultat(
        n_sammenligninger=len(rows),
        n_inden_for_CI=sum(r["inden_for_CI"] for r in rows),
        n_identiske=sum(r["identisk"] for r in rows),
        max_afvigelse_pp=max(abs(r["afvigelse_pp"]) for r in rows),
        deterministiske_ok=det_ok,
    )
    K1_RESUME.write_text(json.dumps({**res.__dict__, "holdt": res.holdt, "n_stier": n_paths},
                                    indent=2), encoding="utf-8")
    return res


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("koersel", choices=["k1"])
    ap.add_argument("--paths", type=int, default=N_PATHS)
    args = ap.parse_args()
    if args.koersel == "k1":
        res = k1(args.paths)
        print(json.dumps({**res.__dict__, "holdt": res.holdt}, indent=2))
        print(f"skrev {K1_UD} og {K1_RESUME}")


if __name__ == "__main__":
    main()
