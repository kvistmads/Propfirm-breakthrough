"""B4 — henter MNQ.v.0 ohlcv-1m til kandidat 1's krydstjek mod NQ (antagelse A).

Trin 1, gratis: prisestimat.

    .venv/bin/python -m research.b4_mnq_data

Trin 2, kun efter Mads' godkendelse: udfør udtrækket.

    .venv/bin/python -m research.b4_mnq_data --hent

Vinduet er MNQ's notering 2019-05-06 til holdout-grænsen ``data.holdout.HOLDOUT_START``
(2024-01-01). Holdout-delen hentes ikke — grænsen er den samme og falder i en filgrænse,
fordi ``data.src_databento.pull`` deler udtrækket i kalenderår, ligesom NQ i fase 1.
Budgetvagten (``data.src_databento.BUDGET_USD``, delt med NQ og MNQ-spreadmålingen fra
fase 1) håndhæves af ``pull`` selv: et udtræk der ville bringe forbruget over loftet
afvises før der hentes noget.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data import holdout  # noqa: E402
from data import src_databento as dbs  # noqa: E402

SYMBOL = "MNQ.v.0"
SCHEMA = "ohlcv-1m"
START = "2019-05-06"
END = holdout.HOLDOUT_START.strftime("%Y-%m-%d")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hent", action="store_true", help="udfør udtrækket (ellers kun estimat)")
    args = ap.parse_args()

    cli = dbs.client()
    p = dbs.plan(cli, SYMBOL, SCHEMA, START, END)
    brugt = dbs.spent_usd()
    print(p.drop(columns="sti").to_string(index=False))
    print(f"\n{SYMBOL} {SCHEMA} {START} -> {END} | estimat i alt "
          f"${p['estimat_usd'].sum():.2f} | brugt før ${brugt:.2f} | "
          f"budget ${dbs.BUDGET_USD:.2f}")
    if not args.hent:
        return
    _, df = dbs.pull(cli, SYMBOL, SCHEMA, START, END, execute=True)
    print(f"hentet {SYMBOL} {SCHEMA}: {len(df)} rækker, brugt nu ${dbs.spent_usd():.2f}")


if __name__ == "__main__":
    main()
