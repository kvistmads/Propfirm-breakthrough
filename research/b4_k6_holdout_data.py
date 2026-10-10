"""B4 kandidat 6 holdout — henter NQ.v.0 ohlcv-1m [2026-09-11, 2026-10-01) (§3, §9.1).

Trin 1, gratis: prisestimat for det manglende stykke.

    .venv/bin/python -m research.b4_k6_holdout_data

Trin 2: udfør udtrækket, kun hvis estimatet er højst ``LOFT_USD`` ($2) og budgetvagten
tillader det.

    .venv/bin/python -m research.b4_k6_holdout_data --hent

Efter hentningen vises kun antal rækker og første og sidste tidsstempel, taget fra indekset
på det, ``pull`` returnerer. Ingen priser læses eller vises. Intet andet symbol røres.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data import src_databento as dbs  # noqa: E402

SYMBOL = "NQ.v.0"
SCHEMA = "ohlcv-1m"
START = "2026-09-11"
END = "2026-10-01"
LOFT_USD = 2.0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hent", action="store_true", help="udfør udtrækket (ellers kun estimat)")
    args = ap.parse_args()

    cli = dbs.client()
    brugt = dbs.spent_usd()
    p = dbs.plan(cli, SYMBOL, SCHEMA, START, END)
    print(p.drop(columns="sti").to_string(index=False))
    est = float(p["estimat_usd"].sum())
    ok = est <= LOFT_USD + 1e-9 and brugt + est <= dbs.BUDGET_USD + 1e-9
    print(f"{SYMBOL} {SCHEMA} {START} -> {END} | estimat ${est:.2f} | loft ${LOFT_USD:.2f} | "
          f"brugt før ${brugt:.2f} | budget ${dbs.BUDGET_USD:.2f} | "
          f"{'inden for' if ok else 'OVER — hentes ikke'}")
    if not args.hent:
        return
    if not ok:
        raise SystemExit("estimatet er over loftet eller budgettet; intet hentet")
    _, df = dbs.pull(cli, SYMBOL, SCHEMA, START, END, execute=True)
    idx = df.index
    print(f"{SYMBOL}: {len(idx)} rækker, første {idx.min()}, sidste {idx.max()}")
    print(f"brugt nu ${dbs.spent_usd():.2f} af ${dbs.BUDGET_USD:.2f}")


if __name__ == "__main__":
    main()
