"""Fase 1 — hent og cache prisdata. Ét trin pr. kald; intet analyseres her.

    .venv/bin/python -m research.fase1_data yahoo
    .venv/bin/python -m research.fase1_data databento            # kun prisestimat
    .venv/bin/python -m research.fase1_data databento --hent     # estimat, så udtræk

## Udtræksplanen — præregistreret 2026-09-11, før første udtræk

    NQ.v.0   ohlcv-1m  fra datasættets start (2010-06-06) til seneste hele UTC-døgn.
                       ATR-grundlaget. 3m/5m/15m aggregeres fra denne ene serie.
    MNQ.v.0  bbo-1m    de seneste 182 døgn før samme slutdato. Spread-grundlaget —
                       det er mikroens spread vi betaler.

``.v.0`` er kontrakten med størst volumen; rullen ses som skift i ``instrument_id``.

**Hvis planen ikke kan rummes:** NQ's start rykkes frem ét kalenderår ad gangen til
det samlede estimat er ≤ $20 — $5 af de $25 holdes til genhentning. Starten rykkes
aldrig senere end tre hele år før slutdatoen (K1). MNQ-vinduet forkortes ikke.

Yahoo hentes som øjebliksbillede (vinduet ruller): 15m og 5m for 60 dage, 1m for 28.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data import src_databento as dbs  # noqa: E402
from data import src_yahoo  # noqa: E402
from data.cache_parquet import CACHE_ROOT, cached_ohlcv  # noqa: E402
from data.ohlcv import OHLCVValidationError, validate_ohlcv  # noqa: E402

NQ, MNQ = "NQ.v.0", "MNQ.v.0"
NQ_START = "2010-06-06"
MNQ_DAYS = 182
PLAN_LOFT_USD = 20.0
OUT = Path(__file__).resolve().parent / "output"


# ---------------------------------------------------------------------------
# Yahoo
# ---------------------------------------------------------------------------

def yahoo_paths(hentet: str) -> dict[str, Path]:
    base = CACHE_ROOT / "yahoo" / src_yahoo.SYMBOL
    return {iv: base / iv / f"hentet_{hentet}.parquet" for iv in ("1m", "5m", "15m")}


def latest_yahoo_snapshot() -> str:
    filer = sorted((CACHE_ROOT / "yahoo" / src_yahoo.SYMBOL / "15m").glob("hentet_*.parquet"))
    if not filer:
        raise FileNotFoundError("ingen Yahoo-snapshot — kør `research.fase1_data yahoo`")
    return filer[-1].stem.removeprefix("hentet_")


def hent_yahoo(hentet: str | None = None) -> dict[str, pd.DataFrame]:
    hentet = hentet or pd.Timestamp.now("UTC").strftime("%Y-%m-%d")
    p = yahoo_paths(hentet)
    end = pd.Timestamp(hentet) + pd.Timedelta(days=1)
    out = {
        "15m": cached_ohlcv(p["15m"], lambda: src_yahoo.fetch("15m", period="60d"),
                            "yahoo 15m"),
        "5m": cached_ohlcv(p["5m"], lambda: src_yahoo.fetch("5m", period="60d"),
                           "yahoo 5m"),
        "1m": cached_ohlcv(p["1m"], lambda: src_yahoo.fetch_1m(end, days=28), "yahoo 1m"),
    }
    for iv, df in out.items():
        print(f"yahoo {iv:>3}: {len(df):6d} barer  {df.index[0]} -> {df.index[-1]}")
    return out


# ---------------------------------------------------------------------------
# Databento
# ---------------------------------------------------------------------------

def slutdato(cli) -> str:
    """Seneste hele UTC-døgn datasættet dækker."""
    r = cli.metadata.get_dataset_range(dbs.DATASET)
    end = pd.Timestamp(r["end"])
    end = end.tz_localize("UTC") if end.tz is None else end.tz_convert("UTC")
    return end.floor("D").strftime("%Y-%m-%d")


def load_databento(symbol: str, schema: str) -> pd.DataFrame:
    """Den cachede serie som én ramme: en ubrudt kæde af bidder fra tidligste start.

    Har flere bidder samme start (et senere udtræk med ny slutdato), vælges den der
    rækker længst. Kæden valideres samlet, så overlap eller uorden afvises.
    """
    base = CACHE_ROOT / "databento" / dbs.DATASET / schema / symbol
    bidder: dict[str, list[tuple[str, Path]]] = {}
    for f in base.glob("*.parquet"):
        s, e = f.stem.split("_", 1)
        bidder.setdefault(s, []).append((e, f))
    if not bidder:
        raise FileNotFoundError(f"ingen cache for {symbol} {schema} — "
                                "kør `research.fase1_data databento --hent`")
    cur, valgt = min(bidder), []
    while cur in bidder:
        e, f = max(bidder[cur])
        valgt.append(f)
        cur = e
    df = pd.concat([pd.read_parquet(f) for f in valgt])
    if schema.startswith("ohlcv"):
        return validate_ohlcv(df, f"databento {symbol} {schema}")
    if not (df.index.is_monotonic_increasing and df.index.is_unique):
        raise OHLCVValidationError(f"ikke-monotone timestamps [databento {symbol} {schema}]")
    return df


def planer(cli, slut: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """NQ- og MNQ-planen efter den præregistrerede regel."""
    mnq_start = (pd.Timestamp(slut) - pd.Timedelta(days=MNQ_DAYS)).strftime("%Y-%m-%d")
    mnq = dbs.plan(cli, MNQ, "bbo-1m", mnq_start, slut)
    nq = dbs.plan(cli, NQ, "ohlcv-1m", NQ_START, slut)
    senest_start = pd.Timestamp(slut) - pd.DateOffset(years=3)
    while (nq["estimat_usd"].sum() + mnq["estimat_usd"].sum() > PLAN_LOFT_USD
           and len(nq) > 1 and pd.Timestamp(nq["start"].iloc[1]) <= senest_start):
        nq = nq.iloc[1:].reset_index(drop=True)
    return nq, mnq


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("kilde", choices=("yahoo", "databento"))
    ap.add_argument("--hent", action="store_true", help="udfør udtrækket (ellers kun estimat)")
    args = ap.parse_args()

    if args.kilde == "yahoo":
        hent_yahoo()
        return

    cli = dbs.client()
    slut = slutdato(cli)
    nq, mnq = planer(cli, slut)
    alle = pd.concat([nq, mnq], ignore_index=True)
    brugt = dbs.spent_usd()
    print(alle.drop(columns="sti").to_string(index=False))
    print(f"\nslutdato {slut} | estimat i alt ${alle['estimat_usd'].sum():.2f} | "
          f"brugt før ${brugt:.2f} | budget ${dbs.BUDGET_USD:.2f}")
    OUT.mkdir(parents=True, exist_ok=True)
    alle.drop(columns="sti").assign(estimeret_utc=pd.Timestamp.now("UTC").isoformat()) \
        .to_csv(OUT / "databento_plan.csv", index=False)
    if not args.hent:
        return
    for p in (nq, mnq):
        sym, schema = p["symbol"].iloc[0], p["schema"].iloc[0]
        _, df = dbs.pull(cli, sym, schema, p["start"].iloc[0], slut, execute=True)
        print(f"hentet {sym} {schema}: {len(df)} rækker, brugt nu ${dbs.spent_usd():.2f}")


if __name__ == "__main__":
    main()
