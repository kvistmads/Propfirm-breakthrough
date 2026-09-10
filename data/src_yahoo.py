"""Yahoo Finance (NQ=F) — anden kilde til K2. Ikke egnet som arkiv.

Målt 2026-09-11: 1m rækker 30 dage tilbage (højst 7 dage pr. kald), 5m og 15m 60 dage,
1h 730 dage. 3m findes ikke. Timestamps kommer i America/New_York og konverteres til
UTC. NQ=F er Yahoos egen kontinuerlige front-kontrakt; rulledatoen er ikke dokumenteret.

Vinduet ruller, så en cache-fil er et øjebliksbillede og navngives med hentedatoen.
"""
from __future__ import annotations

import warnings

import pandas as pd

from data.ohlcv import COLUMNS, OHLCVValidationError, validate_ohlcv

SYMBOL = "NQ=F"


def from_yfinance(raw: pd.DataFrame | None) -> pd.DataFrame:
    """yfinance-ramme (NY-tid, store forbogstaver, actions-kolonner) → kontrakten."""
    if raw is None or len(raw) == 0:
        raise OHLCVValidationError("tomt svar [yahoo]")
    df = raw.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(c).lower() for c in df.columns]
    df = df[[c for c in COLUMNS if c in df.columns]].astype("float64")
    if not isinstance(df.index, pd.DatetimeIndex) or df.index.tz is None:
        raise OHLCVValidationError("index uden tidszone [yahoo]")
    df.index = df.index.tz_convert("UTC")
    df.index.name = "time"
    return validate_ohlcv(df, "yahoo")


def fetch(interval: str, start: str | None = None, end: str | None = None,
          period: str | None = None, symbol: str = SYMBOL) -> pd.DataFrame:
    import yfinance as yf

    warnings.filterwarnings("ignore")
    kw = {"interval": interval, "auto_adjust": False, "prepost": True, "actions": False}
    if period:
        kw["period"] = period
    else:
        kw.update(start=start, end=end)
    return from_yfinance(yf.Ticker(symbol).history(**kw))


def fetch_1m(end: pd.Timestamp, days: int = 28, symbol: str = SYMBOL) -> pd.DataFrame:
    """1m i ikke-overlappende syvdagesvinduer bagud fra ``end`` (eksklusiv)."""
    end = pd.Timestamp(end).normalize()
    start = end - pd.Timedelta(days=days)
    parts = []
    s = start
    while s < end:
        e = min(s + pd.Timedelta(days=7), end)
        parts.append(fetch("1m", s.strftime("%Y-%m-%d"), e.strftime("%Y-%m-%d"),
                           symbol=symbol))
        s = e
    return validate_ohlcv(pd.concat(parts), "yahoo 1m samlet")
