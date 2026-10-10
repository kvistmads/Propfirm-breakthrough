"""B4 kandidat 7 holdout — henter ES.v.0 og ZN.v.0 ohlcv-1m [2024-01-01, 2026-10-01) (§3, §9.1).

Trin 1, gratis: prisestimat for begge.

    .venv/bin/python -m research.b4_k7_holdout_data

Trin 2: udfør udtrækket, kun hvis det samlede estimat er højst ``LOFT_USD`` ($15) og
budgetvagten tillader det.

    .venv/bin/python -m research.b4_k7_holdout_data --hent

Efter hentningen vises kun antal rækker og første og sidste tidsstempel pr. fil, taget fra
indekset på det, ``pull`` returnerer. Ingen priser læses eller vises. NQ.v.0 røres ikke.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data import src_databento as dbs  # noqa: E402

SYMBOLER = ("ES.v.0", "ZN.v.0")
SCHEMA = "ohlcv-1m"
START = "2024-01-01"
END = "2026-10-01"
LOFT_USD = 15.0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hent", action="store_true", help="udfør udtrækket (ellers kun estimat)")
    args = ap.parse_args()

    cli = dbs.client()
    brugt = dbs.spent_usd()
    planer = {}
    for sym in SYMBOLER:
        p = dbs.plan(cli, sym, SCHEMA, START, END)
        planer[sym] = p
        print(p.drop(columns="sti").to_string(index=False))
        print(f"{sym} {SCHEMA} {START} -> {END} | estimat ${p['estimat_usd'].sum():.2f}\n")
    i_alt = sum(float(p["estimat_usd"].sum()) for p in planer.values())
    ok = i_alt <= LOFT_USD + 1e-9 and brugt + i_alt <= dbs.BUDGET_USD + 1e-9
    print(f"estimat i alt ${i_alt:.2f} | loft ${LOFT_USD:.2f} | brugt før ${brugt:.2f} | "
          f"budget ${dbs.BUDGET_USD:.2f} | {'inden for' if ok else 'OVER — hentes ikke'}")
    if not args.hent:
        return
    if not ok:
        raise SystemExit("estimatet er over loftet eller budgettet; intet hentet")
    for sym in SYMBOLER:
        p, df = dbs.pull(cli, sym, SCHEMA, START, END, execute=True)
        idx = df.index
        for r in p.to_dict("records"):
            s = idx[(idx >= r["start"]) & (idx < r["slut"])] if len(idx) else idx
            print(f"{sym} {r['sti'].name}: {len(s)} rækker, første {s.min()}, sidste {s.max()}")
    print(f"brugt nu ${dbs.spent_usd():.2f} af ${dbs.BUDGET_USD:.2f}")


if __name__ == "__main__":
    main()
