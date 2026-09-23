"""Tests for research/b4_mnq_verifikation.py — MNQ mod NQ, dækning/kontrakter/væger.

Ingen af testene ser på signaler eller udfald; modulet gør det heller ikke. Der testes
kun mod syntetiske barer, aldrig mod cachen.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research import b4_mnq_verifikation as v

UTC = "UTC"


def _bars_1m(start: str, n: int, iid: int = 1) -> pd.DataFrame:
    idx = pd.date_range(start, periods=n, freq="1min", tz=UTC, name="time")
    close = 100.0 + np.arange(n, dtype=float)
    return pd.DataFrame({"open": close, "high": close + 1, "low": close - 1, "close": close,
                         "volume": 1.0, "instrument_id": np.full(n, iid, dtype=np.int64)},
                        index=idx)


def _bars_15m(tider_utc, ohlc, iid=1) -> pd.DataFrame:
    idx = pd.DatetimeIndex([pd.Timestamp(t, tz=UTC) for t in tider_utc], name="time")
    a = np.asarray(ohlc, dtype=float)
    return pd.DataFrame({"open": a[:, 0], "high": a[:, 1], "low": a[:, 2], "close": a[:, 3],
                         "volume": 1.0,
                         "instrument_id": np.broadcast_to(np.asarray(iid, dtype=np.int64),
                                                          len(a)).copy()},
                        index=idx)


# ---------------------------------------------------------------------------
# Kalender
# ---------------------------------------------------------------------------

def test_rth_dage_ligger_i_vinduet_og_er_stigende():
    dage = v.rth_dage("2023-06-01", "2023-07-01")
    assert dage.is_monotonic_increasing
    assert dage.min() >= pd.Timestamp("2023-06-01")
    assert dage.max() < pd.Timestamp("2023-07-01")
    # Juneteenth (2023-06-19) er NYSE-helligdag: ingen session.
    assert pd.Timestamp("2023-06-19") not in dage


def test_dag_minutter_kender_halve_dage():
    # Dagen før Thanksgiving 2023 (11-24) er en halv dag, 09:30-13:00 = 210 minutter.
    dage = v.rth_dage("2023-11-20", "2023-11-25")
    m = v.dag_minutter(dage)
    normal = m[m.index != pd.Timestamp("2023-11-24")]
    halv = m.loc[pd.Timestamp("2023-11-24")]
    assert (normal == 390).all()
    assert halv == 210


# ---------------------------------------------------------------------------
# Dækning
# ---------------------------------------------------------------------------

def test_daekning_taeller_rth_barer_pr_dag():
    # 2023-06-14 er en almindelig onsdag. RTH 09:30-16:00 ET = 13:30-20:00 UTC (sommertid).
    bars = _bars_1m("2023-06-14 13:30", 390)
    dage = v.rth_dage("2023-06-14", "2023-06-15")
    d = v.daekning(bars, dage)
    assert d.loc[pd.Timestamp("2023-06-14")] == 390


def test_daekning_er_nul_uden_data():
    bars = _bars_1m("2023-06-14 13:30", 390)
    dage = v.rth_dage("2023-06-14", "2023-06-16")
    d = v.daekning(bars, dage)
    assert d.loc[pd.Timestamp("2023-06-15")] == 0


# ---------------------------------------------------------------------------
# Kontraktskift
# ---------------------------------------------------------------------------

def test_kontraktskift_finder_skiftene():
    a = _bars_1m("2023-06-14 00:00", 3, iid=1)
    b = _bars_1m("2023-06-14 00:03", 2, iid=2)
    c = _bars_1m("2023-06-14 00:05", 2, iid=3)
    bars = pd.concat([a, b, c])
    k = v.kontraktskift(bars)
    assert list(k["fra"]) == [1, 2]
    assert list(k["til"]) == [2, 3]
    assert k["tid_utc"].iloc[0] == bars.index[3]
    assert k["tid_utc"].iloc[1] == bars.index[5]


def test_kontraktskift_tom_uden_skift():
    bars = _bars_1m("2023-06-14 00:00", 5, iid=7)
    assert len(v.kontraktskift(bars)) == 0


# ---------------------------------------------------------------------------
# Væger
# ---------------------------------------------------------------------------

def test_vaeger_regner_tick_afvigelse():
    tider = ["2023-06-14 13:30", "2023-06-14 13:45"]
    nq = _bars_15m(tider, [(100, 110, 90, 105), (105, 115, 95, 110)])
    mnq = _bars_15m(tider, [(100, 110.5, 90, 105), (105, 115, 94, 110)])
    ud = v.vaeger(nq, mnq)
    assert ud.loc[pd.Timestamp(tider[0], tz=UTC), "high_diff_tick"] == pytest.approx(2.0)
    assert ud.loc[pd.Timestamp(tider[0], tz=UTC), "low_diff_tick"] == 0
    assert ud.loc[pd.Timestamp(tider[1], tz=UTC), "low_diff_tick"] == pytest.approx(-4.0)
    assert not ud["rullevindue"].any()


def test_vaeger_flager_rullevindue_ved_forskellig_generation():
    tider = ["2023-06-14 13:30", "2023-06-14 13:45", "2023-06-14 14:00"]
    # MNQ ruller ved anden bar, NQ ruller først ved tredje: midterste bar er et rullevindue.
    nq = _bars_15m(tider, [(100, 110, 90, 105)] * 3, iid=[1, 1, 2])
    mnq = _bars_15m(tider, [(100, 110, 90, 105)] * 3, iid=[1, 2, 2])
    ud = v.vaeger(nq, mnq)
    assert list(ud["rullevindue"]) == [False, True, False]


def test_vaeger_bruger_kun_faelles_tidsstempler():
    nq = _bars_15m(["2023-06-14 13:30", "2023-06-14 13:45"],
                   [(100, 110, 90, 105), (105, 115, 95, 110)])
    mnq = _bars_15m(["2023-06-14 13:30"], [(100, 110, 90, 105)])
    ud = v.vaeger(nq, mnq)
    assert len(ud) == 1


def test_vaeger_fordeling_percentiler_og_andele():
    idx = pd.date_range("2023-06-14 13:30", periods=4, freq="15min", tz=UTC)
    df = pd.DataFrame({"high_diff_tick": [0.0, 0.0, 1.0, 4.0],
                       "low_diff_tick": [0.0, -1.0, 0.0, 0.0]}, index=idx)
    row = v.vaeger_fordeling(df, np.ones(len(df), dtype=bool))
    assert row["n"] == 4
    assert row["high_0_tick_pct"] == pytest.approx(50.0)
    assert row["high_le1_tick_pct"] == pytest.approx(75.0)
    assert row["high_max"] == 4.0
    assert row["low_0_tick_pct"] == pytest.approx(75.0)
