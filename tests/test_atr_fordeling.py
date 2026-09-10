"""Tests for research/atr_fordeling.py — ATR-målingen der skal erstatte §5's ene tal.

Tre ting låses:

1. **Apparatet og dokumentet siger det samme.** Uden brud er ATR'en identisk med
   ``data/indicators.calculate_atr``, og en konstant ATR på 0,168% ved NQ 29.639,50
   genskaber §5b's 15m-række (R $99,59, 5,10% af MLL, 0,0248 R, 34,16%).
2. **En rulle og et overnatningshul er ikke volatilitet.** Over et brud er TR = H−L.
3. **p90 er altid den ende hvor det gør ondt.** For risiko hører den til høj ATR, for
   omkostning i R til lav ATR.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from data import sessions
from data.indicators import calculate_atr
from research import atr_fordeling as af


def _bars(start_utc: str, n: int, minutes: int = 1, price: float = 29_000.0,
          instrument_id: int = 1, seed: int = 3) -> pd.DataFrame:
    idx = pd.date_range(start_utc, periods=n, freq=f"{minutes}min", tz="UTC", name="time")
    rng = np.random.default_rng(seed)
    close = price + np.cumsum(rng.normal(0, 5, n))
    open_ = np.r_[price, close[:-1]]
    return pd.DataFrame({
        "open": open_, "close": close,
        "high": np.maximum(open_, close) + rng.uniform(0, 5, n),
        "low": np.minimum(open_, close) - rng.uniform(0, 5, n),
        "volume": np.full(n, 10.0), "instrument_id": np.int64(instrument_id),
    }, index=idx)


def test_cost_is_derived_from_config_and_matches_the_document():
    assert af.omk_usd_rundtur(price=29_639.50) == pytest.approx(2.47, abs=1e-9)
    assert af.omk_usd_rundtur(price=15_000.0) == pytest.approx(2.47, abs=1e-9)


def test_without_breaks_atr_equals_the_indicator_apparatus():
    df = _bars("2026-08-26 13:30", 200)
    ours = af.atr_pct(df, 1) * df["close"] / 100
    ref = calculate_atr(df)
    pd.testing.assert_series_equal(ours, ref, check_names=False)


def test_a_roll_jump_does_not_inflate_atr():
    a = _bars("2026-08-26 13:30", 100, instrument_id=1)
    b = _bars("2026-08-26 15:10", 100, price=a["close"].iloc[-1] + 250.0,
              instrument_id=2, seed=4)
    df = pd.concat([a, b])
    i = len(a)
    tr_klog = af.true_range(df, sessions.break_mask(df, 1))
    tr_naiv = af.true_range(df, np.r_[True, np.zeros(len(df) - 1, dtype=bool)])
    assert tr_klog.iloc[i] == pytest.approx(df["high"].iloc[i] - df["low"].iloc[i])
    assert tr_naiv.iloc[i] > 200
    assert af.atr_pct(df, 1).iloc[i] < 0.5 * (calculate_atr(df) / df["close"] * 100).iloc[i]


def test_the_overnight_gap_is_not_part_of_the_rth_true_range():
    d1 = _bars("2026-08-26 13:30", 390)
    d2 = _bars("2026-08-27 13:30", 390, price=d1["close"].iloc[-1] + 150.0, seed=9)
    df = pd.concat([d1, d2])
    tr = af.true_range(df, sessions.break_mask(df, 1))
    assert tr.iloc[390] == pytest.approx(df["high"].iloc[390] - df["low"].iloc[390])


def test_constant_atr_reproduces_the_15m_row_of_section_5b():
    atr = pd.Series(np.full(50, 0.168))
    row = af.fordeling(atr, niveau=29_639.50, omk=2.47)
    assert row["R_usd_p50"] == pytest.approx(99.59, abs=0.01)
    assert row["risiko_pct_af_MLL_netto_p90"] == pytest.approx(5.10, abs=0.01)
    assert row["omk_R_netto_p50"] == pytest.approx(0.0248, abs=0.0001)
    assert row["be_WR_pct_netto_p50"] == pytest.approx(34.16, abs=0.01)
    assert row["be_WR_pct_brutto"] == pytest.approx(100 / 3)


def test_p90_is_the_painful_end_of_every_column():
    atr = pd.Series(np.arange(1, 12, dtype=float) / 10)        # 0,1 … 1,1
    row = af.fordeling(atr, niveau=30_000.0, omk=2.47)
    r = lambda pct: pct / 100 * 30_000.0 * 2
    # Risiko: p90 hører til HØJ ATR (her 1,0 — 10. af 11 værdier).
    assert row["ATR_pct_p90"] == pytest.approx(1.0)
    assert row["risiko_pct_af_MLL_netto_p90"] == pytest.approx((r(1.0) + 2.47) / 2000 * 100)
    # Omkostning: p90 hører til LAV ATR (0,2 — 2. af 11 værdier).
    assert row["ATR_pct_p10"] == pytest.approx(0.2)
    assert row["omk_R_netto_p90"] == pytest.approx(2.47 / r(0.2))
    assert row["omk_R_netto_p90"] > row["omk_R_netto_p50"]
    assert row["be_WR_pct_netto_p90"] > row["be_WR_pct_netto_p50"] > row["be_WR_pct_brutto"]


def test_zero_atr_bars_are_counted_not_divided_by():
    row = af.fordeling(pd.Series([0.0, 0.1, 0.2, np.nan]), niveau=30_000.0, omk=2.47)
    assert row["n_barer"] == 2 and row["n_barer_ATR_nul"] == 1
    assert math.isfinite(row["omk_R_netto_p90"])


def test_session_series_split_rth_from_the_full_day():
    df = _bars("2026-08-26 12:00", 600)                      # 08:00-18:00 EDT
    s = af.session_series(df)
    for m in (1, 3, 5, 15):
        rth, doegn = s[(m, "RTH")], s[(m, af.DOEGN)]
        assert sessions.rth_mask(rth.index, m).all()
        assert len(doegn) > len(rth) > 0
    assert len(s[(15, "RTH")]) == 26


def test_sqrt_comparison_is_zero_when_the_document_was_right():
    hele = pd.DataFrame([{"timeframe": f"{m}m", "session": s,
                          "ATR_pct_p50": 0.168 * math.sqrt(m / 15)}
                         for s in af.SESSIONS for m in (1, 3, 5, 15)])
    sq = af.sqrt_sammenligning(hele)
    assert sq["afvigelse_mod_5b_pct"].abs().max() == pytest.approx(0, abs=1e-9)
    assert sq["formafvigelse_pct"].abs().max() == pytest.approx(0, abs=1e-9)
