"""Tests for research/spread_stikproeve.py — MNQ-spread på en stratificeret stikprøve.

Låst her: at universet udelader halve dage og rullevinduer, at udtrækket er
deterministisk, at en quote fremføres men ikke over et handelsstop, og at et sekund
markeres RTH, ETH og minutgrænse korrekt.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research import spread_stikproeve as ss


def test_globex_day_window_in_utc_follows_dst():
    assert ss.globex_vindue(pd.Timestamp("2026-08-24")) == ("2026-08-23T22:00",
                                                            "2026-08-24T21:00")
    assert ss.globex_vindue(pd.Timestamp("2026-01-14")) == ("2026-01-13T23:00",
                                                            "2026-01-14T22:00")


def _dagsrange(datoer, vaerdier) -> pd.DataFrame:
    return pd.DataFrame({"aabning": 100.0, "high": 101.0, "low": 99.0, "n_1m": 390,
                         "rth_range_pct": vaerdier}, index=pd.DatetimeIndex(datoer))


def test_universe_drops_the_roll_window_and_the_switch_day():
    sess = pd.bdate_range("2026-06-08", "2026-06-24")
    dr = _dagsrange(sess, np.linspace(0.5, 3.0, len(sess)))
    u = ss.univers(dr, [pd.Timestamp("2026-06-17")], start="2026-06-08", slut="2026-06-24")
    got = set(u.index.strftime("%Y-%m-%d"))
    assert not got & {"2026-06-10", "2026-06-11", "2026-06-12", "2026-06-15",
                      "2026-06-16", "2026-06-17"}
    assert "2026-06-19" not in got                      # Juneteenth, ingen NYSE-session
    assert {"2026-06-08", "2026-06-09", "2026-06-18", "2026-06-22"} <= got
    assert set(u["tercil"]) <= {"rolig", "mellem", "volatil"}


def test_universe_drops_half_days():
    sess = pd.bdate_range("2025-11-24", "2025-12-03")
    u = ss.univers(_dagsrange(sess, np.linspace(0.5, 3.0, len(sess))), [],
                   start="2025-11-24", slut="2025-12-03")
    got = set(u.index.strftime("%Y-%m-%d"))
    assert "2025-11-28" not in got and "2025-11-27" not in got
    assert "2025-11-26" in got


def test_sampling_is_deterministic_and_takes_small_cells_whole():
    idx = pd.bdate_range("2024-01-01", "2025-12-31")
    rng = np.random.default_rng(0)
    u = pd.DataFrame({"rth_range_pct": rng.uniform(0.5, 3.0, len(idx))}, index=idx)
    u["tercil"] = pd.qcut(u["rth_range_pct"], 3, labels=["rolig", "mellem", "volatil"]).astype(str)
    u["aar"] = u.index.year
    a, b = ss.vaelg(u, k=4, seed=1), ss.vaelg(u, k=4, seed=1)
    assert a.index.equals(b.index)
    assert len(a) == 24 and (a.groupby(["aar", "tercil"]).size() == 4).all()
    assert len(ss.vaelg(u[u["aar"] == 2024].head(2), k=4, seed=1)) == 2


def test_rth_range_is_measured_on_rth_bars_only():
    idx = pd.date_range("2026-08-26 12:00", periods=600, freq="1min", tz="UTC")
    px = np.full(600, 100.0)
    df = pd.DataFrame({"open": px, "high": px + 0.5, "low": px - 0.5, "close": px,
                       "volume": 1.0}, index=idx)
    df.iloc[10, df.columns.get_loc("high")] = 150.0       # 08:10 EDT — uden for RTH
    df.iloc[100, df.columns.get_loc("high")] = 102.0      # 09:40 EDT — i RTH
    r = ss.nq_rth_range(df).loc[pd.Timestamp("2026-08-26")]
    assert r["rth_range_pct"] == pytest.approx(2.5)
    assert r["n_1m"] == 390


def test_second_grid_carries_quotes_forward_but_not_across_halts():
    t0 = pd.Timestamp("2026-08-26 14:00:00", tz="UTC")
    s = lambda n: t0 + pd.Timedelta(seconds=n)
    bbo = pd.DataFrame({"bid": [100.0, 100.25, 101.0], "ask": [100.25, 100.75, 101.25]},
                       index=pd.DatetimeIndex([s(0), s(5), s(200)]))
    g = ss.sekundgitter(bbo, max_fremfoer_s=60)
    assert g.loc[s(4), "ask"] == 100.25                  # fremført
    assert s(65) in g.index and s(66) not in g.index     # højst 60 s efter sidste quote
    assert s(200) in g.index and len(g) == 67


def test_spread_day_labels_session_and_minute_boundaries_and_drops_crossed_quotes():
    idx = pd.date_range("2026-08-26 13:29:58", periods=5, freq="1s", tz="UTC")  # 09:29:58 EDT
    bbo = pd.DataFrame({"bid": [100.0, 100.0, 100.0, 100.5, 100.0],
                        "ask": [100.5, 100.25, 100.25, 100.25, 100.25]}, index=idx)
    d, udeladt = ss.spread_dag(bbo)
    assert udeladt == 1                                   # 13:30:01 er krydset
    assert d["rth"].tolist() == [False, False, True, True]
    assert d["minutgraense"].tolist() == [False, False, True, False]
    assert d["ticks"].tolist() == [2.0, 1.0, 1.0, 1.0]


def test_tables_split_measure_and_session():
    alle = pd.DataFrame({
        "ticks": np.array([1, 1, 2, 3, 1, 1], dtype="float32"),
        "rth": [True, True, True, False, False, False],
        "minutgraense": [True, False, False, True, False, False],
        "blok": np.array([19, 19, 20, 2, 2, 3], dtype="int16"),
        "aar": np.int16(2026), "tercil": pd.Categorical(["rolig"] * 6)})
    t = ss.tabeller(alle)
    ps = t["pr_session"]
    assert ps.loc[("tidsvægtet", "RTH"), "gns_ticks"] == pytest.approx(4 / 3)
    assert ps.loc[("ved_minutgrænse", "RTH"), "n"] == 1
    assert ps.loc[("tidsvægtet", "ETH"), "andel_1_tick_pct"] == pytest.approx(200 / 3)
    assert ("RTH", "09:30") in t["pr_blok"].index
