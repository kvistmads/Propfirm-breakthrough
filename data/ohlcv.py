"""Den kanoniske OHLCV-kontrakt — én form for alle kilder, valideret ved indlæsning.

Kontrakten er den samme som ``data/fetcher._validate_ohlcv`` i det gamle repo: afvis
tomme svar, manglende kolonner, NaN og ikke-monotone timestamps. Den er skrevet igen
her, ikke importeret — apparatet kopieres, deles ikke.

Formen:

    index          DatetimeIndex, tz=UTC, navn ``time``, barens ÅBNINGStid, strengt stigende
    open..close    float64
    volume         float64
    instrument_id  valgfri int64 — hvilken kontrakt baren stammer fra. Uden den kan en
                   rulle i en kontinuerlig serie ikke skelnes fra et prisspring.

**Validering reparerer aldrig.** Et svar der bryder kontrakten afvises. Sortering,
dedup eller udfyldning ville skjule præcis de fejl K4 skal tælle.
"""
from __future__ import annotations

import pandas as pd

OHLC = ("open", "high", "low", "close")
COLUMNS = OHLC + ("volume",)


class OHLCVValidationError(ValueError):
    """Et svar der ikke opfylder kontrakten."""


def validate_ohlcv(df: pd.DataFrame | None, source: str = "") -> pd.DataFrame:
    """Returnér ``df`` uændret hvis den opfylder kontrakten, ellers rejs fejl."""
    hvor = f" [{source}]" if source else ""
    if df is None or len(df) == 0:
        raise OHLCVValidationError(f"tomt svar{hvor}")
    mangler = [c for c in COLUMNS if c not in df.columns]
    if mangler:
        raise OHLCVValidationError(f"manglende kolonner {mangler}{hvor}")
    if not isinstance(df.index, pd.DatetimeIndex):
        raise OHLCVValidationError(f"index er ikke tidsstempler{hvor}")
    if df.index.tz is None or str(df.index.tz) != "UTC":
        raise OHLCVValidationError(f"index skal være UTC, er {df.index.tz}{hvor}")
    nan = df[list(COLUMNS)].isna().sum()
    if nan.any():
        raise OHLCVValidationError(f"NaN i {nan[nan > 0].to_dict()}{hvor}")
    if df.index.hasnans:
        raise OHLCVValidationError(f"NaT i index{hvor}")
    if not (df.index.is_monotonic_increasing and df.index.is_unique):
        n = count_non_increasing(df.index)
        raise OHLCVValidationError(f"{n} ikke-monotone eller duplikerede timestamps{hvor}")
    return df


def count_non_increasing(index: pd.DatetimeIndex) -> int:
    """Antal steder hvor et timestamp ikke er strengt større end det foregående."""
    if len(index) < 2:
        return 0
    return int((index[1:] <= index[:-1]).sum())
