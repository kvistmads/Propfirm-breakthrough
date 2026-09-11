"""Tests for research/fase1_verifikation.py — målingerne bag K1-K4, ruller og spread.

Det der låses er at hver måling rammer det den påstår at måle: at et manglende minut
tælles, at en tidsforskydning findes, at en rulle ikke tælles som et prisspring, og at
et krydset quote ikke trækker spreadet ned.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research import fase1_verifikation as fv


def _bars(start_utc: str, n: int, price: float = 29_000.0, instrument_id: int = 1,
          seed: int = 5, minutes: int = 1) -> pd.DataFrame:
    idx = pd.date_range(start_utc, periods=n, freq=f"{minutes}min", tz="UTC", name="time")
    rng = np.random.default_rng(seed)
    close = price + np.cumsum(rng.normal(0, 3, n))
    open_ = np.r_[price, close[:-1]]
    return pd.DataFrame({
        "open": open_, "close": close,
        "high": np.maximum(open_, close) + rng.uniform(0.25, 3, n),
        "low": np.minimum(open_, close) - rng.uniform(0.25, 3, n),
        "volume": 5.0, "instrument_id": np.int64(instrument_id),
    }, index=idx)


def test_k3_counts_missing_rth_minutes_against_the_calendar():
    d1 = _bars("2026-08-26 13:30", 390)
    d2 = _bars("2026-08-27 13:30", 390).drop(
        index=pd.date_range("2026-08-27 15:00", periods=5, freq="1min", tz="UTC"))
    k3 = fv.k3_rth_daekning(pd.concat([d1, d2]), 1)
    hele = k3.loc["hele"]
    assert hele["forventede_barer"] == 780 and hele["manglende_barer"] == 5
    assert hele["sessioner_med_huller"] == 1
    assert hele["mangler_pct"] == pytest.approx(5 / 780 * 100)


def test_k3_on_15m_expects_26_bars_per_regular_session():
    d = _bars("2026-08-26 13:30", 26, minutes=15)
    assert fv.k3_rth_daekning(d, 15).loc["hele", "forventede_barer"] == 26


def test_k4_counts_flat_bars_per_cell():
    d = _bars("2026-08-26 13:30", 100)
    d.iloc[:3, d.columns.get_loc("high")] = d["low"].iloc[:3].to_numpy()
    k4 = fv.k4_flade({(1, "RTH"): d})
    assert k4.loc[0, "flade"] == 3 and k4.loc[0, "flade_pct"] == pytest.approx(3.0)
    assert not k4.loc[0, "holder"]


def _days(scale: float = 1.0) -> pd.DataFrame:
    """Fem Globex-dage i 15m. Skaleret om et fast centrum, så dagsrange skalerer præcist."""
    df = _bars("2026-08-23 22:00", 92 * 5, minutes=15, seed=11)
    c = 29_000.0
    return df.assign(high=c + (df["high"] - c) * scale, low=c + (df["low"] - c) * scale)


def test_k2_is_zero_for_identical_sources():
    _, s = fv.k2_ranges(_days(), _days(), 15, fv.DOEGN)
    assert s["median_abs_afv_pct"] == pytest.approx(0.0)
    assert s["holder"] and s["dage_brugt"] == s["dage_i_overlap"] > 0


def test_k2_measures_a_ten_percent_range_difference():
    _, s = fv.k2_ranges(_days(1.1), _days(), 15, fv.DOEGN)
    assert s["median_abs_afv_pct"] == pytest.approx(10.0, rel=0.02)
    assert not s["holder"]


def test_shift_test_finds_a_one_minute_label_offset():
    y = _bars("2026-08-26 13:30", 600, seed=21)
    d = y.copy()
    d.index = d.index + pd.Timedelta(minutes=1)       # samme barer, mærket et minut senere
    fs = fv.forskydning(y, d, max_min=5)
    assert fs.loc[fs["spearman"].idxmax(), "forskydning_min"] == -1
    fs0 = fv.forskydning(y, y, max_min=5)
    assert fs0.loc[fs0["spearman"].idxmax(), "forskydning_min"] == 0


def test_rolls_are_listed_with_their_jump_in_ticks():
    a = _bars("2026-08-26 13:30", 10, instrument_id=1)
    b = _bars("2026-08-26 13:40", 10, price=a["close"].iloc[-1] + 250.0, instrument_id=2)
    rl = fv.ruller(pd.concat([a, b]))
    assert len(rl) == 1
    assert rl.loc[0, "spring_ticks"] == pytest.approx(1000.0)


def test_a_roll_is_not_an_unexplained_jump_but_a_same_contract_gap_is():
    a = _bars("2026-08-26 13:30", 60, instrument_id=1)
    b = _bars("2026-08-26 14:30", 60, price=a["close"].iloc[-1] + 250.0, instrument_id=2)
    df = pd.concat([a, b])
    pr_aar, top = fv.uforklarede_spring(df)
    assert int(pr_aar["spring"].sum()) == 0
    df.iloc[90, df.columns.get_loc("open")] += 100.0
    df.iloc[90, df.columns.get_loc("high")] += 100.0
    pr_aar, top = fv.uforklarede_spring(df)
    assert int(pr_aar["spring"].sum()) == 1


def test_spread_excludes_crossed_quotes_and_labels_the_minute_before():
    idx = pd.DatetimeIndex(pd.to_datetime(["2026-08-26 13:30", "2026-08-26 13:31",
                                           "2026-08-26 13:32", "2026-08-26 13:33"], utc=True))
    bbo = pd.DataFrame({"bid": [100.0, 100.0, 100.0, 100.5],
                        "ask": [100.25, 100.5, 100.25, 100.25],
                        "bid_sz": 1.0, "ask_sz": 1.0, "instrument_id": 7}, index=idx)
    ps, pb, meta = fv.spread(bbo)
    assert meta["udeladt_laast_krydset_tom"] == 1
    # 13:30-snapshottet beskriver 09:29-09:30 EDT: uden for RTH.
    assert ps.loc["ETH", "n"] == 1 and ps.loc["RTH", "n"] == 2
    assert ps.loc["RTH", "gns_ticks"] == pytest.approx(1.5)
    assert ps.loc["RTH", "andel_1_tick_pct"] == pytest.approx(50.0)


def test_vectorised_spearman_matches_the_apparatus():
    """Forskydningstesten må ikke få sin egen definition af Spearman."""
    from research.stats import spearman

    rng = np.random.default_rng(1)
    x = pd.Series(rng.normal(size=200))
    y = pd.Series(x.to_numpy() + rng.normal(size=200))
    y.iloc[:20] = y.iloc[0]                     # bindinger
    assert fv._spearman(x, y) == pytest.approx(spearman(x, y).r, abs=1e-12)
