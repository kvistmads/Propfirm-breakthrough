"""B4 kandidat 7 — henter ES.v.0 og ZN.v.0 ohlcv-1m til rebalanceringssignalet (§3, §11.1).

Trin 1, gratis: prisestimat for begge.

    .venv/bin/python -m research.b4_k7_data

Trin 2: udfør udtrækket. Det sker kun, hvis det samlede estimat er højst ``LOFT_USD``
($30, præregistreringens loft) og budgetvagten tillader det. Commit'en af
``research/prereg/b4_k7_rebalancering.md`` er ejerens godkendelse inden for loftet.

    .venv/bin/python -m research.b4_k7_data --hent

Vinduet er 2016-01-01 til holdout-grænsen ``data.holdout.HOLDOUT_START`` (2024-01-01).
Holdout-delen hentes ikke. Budgetvagten (``data.src_databento.BUDGET_USD``) håndhæves af
``pull`` selv; loftet på $30 håndhæves her, før første bid hentes.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data import holdout  # noqa: E402
from data import src_databento as dbs  # noqa: E402

SYMBOLER = ("ES.v.0", "ZN.v.0")
SCHEMA = "ohlcv-1m"
START = "2016-01-01"
END = holdout.HOLDOUT_START.strftime("%Y-%m-%d")
LOFT_USD = 30.0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hent", action="store_true", help="udfør udtrækket (ellers kun estimat)")
    args = ap.parse_args()

    cli = dbs.client()
    brugt = dbs.spent_usd()
    i_alt = 0.0
    for sym in SYMBOLER:
        p = dbs.plan(cli, sym, SCHEMA, START, END)
        print(p.drop(columns="sti").to_string(index=False))
        i_alt += float(p["estimat_usd"].sum())
        print(f"{sym} {SCHEMA} {START} -> {END} | estimat ${p['estimat_usd'].sum():.2f}\n")
    ok = i_alt <= LOFT_USD + 1e-9 and brugt + i_alt <= dbs.BUDGET_USD + 1e-9
    print(f"estimat i alt ${i_alt:.2f} | loft ${LOFT_USD:.2f} | brugt før ${brugt:.2f} | "
          f"budget ${dbs.BUDGET_USD:.2f} | {'inden for' if ok else 'OVER — hentes ikke'}")
    if not args.hent:
        return
    if not ok:
        raise SystemExit("estimatet er over loftet eller budgettet; intet hentet")
    for sym in SYMBOLER:
        _, df = dbs.pull(cli, sym, SCHEMA, START, END, execute=True)
        print(f"hentet {sym} {SCHEMA}: {len(df)} rækker, brugt nu ${dbs.spent_usd():.2f}")


if __name__ == "__main__":
    main()
