"""Sessionsmarkering og handelsbrud.

RTH er NYSE's ordinære session for datoen: 09:30–16:00 ET, 13:00 på halve dage, slået
op i ``exchange_calendars`` (XNYS) frem for en hardkodet helligdagsliste. Nasdaq-100
futures handler også på NYSE-helligdage (MLK Day, Presidents' Day til 13:00 ET), men
der findes ingen kontantsession de dage — de barer er uden for RTH.

En bar er RTH når HELE baren ligger i sessionen: ``open <= start`` og
``start + barlængde <= close``. Med barer forankret i UTC-epoken (``data.resample``) er
09:30 ET en grænse for 1m, 3m, 5m og 15m, så ingen bar skræver over åbningen.

**Tidszonen er ikke en detalje.** Alt internt er UTC; ET bruges kun til at slå datoen op.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd

ET = "America/New_York"
RTH, ETH = "RTH", "ETH"

# Et hul på mindst så mange minutter fra forrige bars slut til denne bars start er et
# handelsbrud (dagligt stop 17-18 ET, weekend, helligdag, nat mellem to RTH-sessioner),
# ikke et manglende datapunkt.
BREAK_MINUTES = 60


@lru_cache(maxsize=1)
def _xnys():
    import exchange_calendars as xcals

    return xcals.get_calendar("XNYS")


def rth_mask(index: pd.DatetimeIndex, bar_minutes: int) -> np.ndarray:
    """True for barer der ligger helt inde i NYSE's ordinære session."""
    if len(index) == 0:
        return np.zeros(0, dtype=bool)
    et_dag = index.tz_convert(ET).tz_localize(None).normalize()
    plan = _xnys().schedule
    # exchange_calendars dækker kørselsdato −20/+1 år. Uden for vinduet ville alle barer
    # tavst blive ETH — et resultat der ligner et resultat. Fase 1-efterskrift 1.2.
    if et_dag.min() < plan.index[0] or et_dag.max() > plan.index[-1]:
        raise ValueError(
            f"XNYS-kalenderen dækker {plan.index[0].date()} → {plan.index[-1].date()}, "
            f"serien spænder {et_dag.min().date()} → {et_dag.max().date()} (ET)")
    aabner = pd.DatetimeIndex(plan["open"].reindex(et_dag))
    lukker = pd.DatetimeIndex(plan["close"].reindex(et_dag))
    slut = index + pd.Timedelta(minutes=bar_minutes)
    # NaT (ingen session den dato) sammenligner falsk begge veje.
    return np.asarray((index >= aabner) & (slut <= lukker), dtype=bool)


def session_labels(index: pd.DatetimeIndex, bar_minutes: int) -> np.ndarray:
    return np.where(rth_mask(index, bar_minutes), RTH, ETH)


def globex_day(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """CME-handelsdagen: en bar fra 18:00 ET hører til næste kalenderdag.

    Regnet i vægurstid, så sommertidsskiftet ikke flytter grænsen.
    """
    return (index.tz_convert(ET).tz_localize(None) + pd.Timedelta(hours=6)).normalize()


def break_mask(df: pd.DataFrame, bar_minutes: int,
               min_gap_minutes: int = BREAK_MINUTES) -> np.ndarray:
    """True hvor forrige bars luk ikke må indgå i denne bars true range.

    To slags brud: et hul på mindst ``min_gap_minutes`` fra forrige bars slut til denne
    bars start, og et skift af ``instrument_id`` — en rulle. Et rullespring er
    kalenderspread, ikke volatilitet. Første bar er altid et brud.
    """
    n = len(df)
    brud = np.ones(n, dtype=bool)
    if n < 2:
        return brud
    minutter = ((df.index - df.index[0]) / pd.Timedelta(minutes=1)).to_numpy(dtype=float)
    brud[1:] = (np.diff(minutter) - bar_minutes) >= min_gap_minutes
    if "instrument_id" in df.columns:
        iid = df["instrument_id"].to_numpy()
        brud[1:] |= iid[1:] != iid[:-1]
    return brud
