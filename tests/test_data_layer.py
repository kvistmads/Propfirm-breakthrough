"""Tests for datalaget i fase 1 — kontrakt, sessioner, aggregering, cache og kilder.

Fire ting er lette at tabe og låses her:

1. **Validering reparerer aldrig.** Et svar der bryder kontrakten afvises; det
   sorteres, dedupes eller udfyldes ikke. Ellers kan K4 ikke tælle det.
2. **Alle timeframes deler bar-grænser.** 3m/5m/15m bygges af den samme 1m-serie og
   forankres i UTC-epoken. Separate udtræk gav 20% ATR-forskel på guld.
3. **RTH følger NYSE-kalenderen** — sommertid, halve dage og helligdage hvor futures
   handler men kontantmarkedet er lukket.
4. **Budgettet håndhæves før der hentes.** Et udtræk over $25 må aldrig nå API'et.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from data import cache_parquet, resample, sessions, src_databento, src_yahoo
from data.ohlcv import OHLCVValidationError, count_non_increasing, validate_ohlcv


def _bars(start_utc: str, n: int, minutes: int = 1, price: float = 100.0,
          instrument_id: int | None = None) -> pd.DataFrame:
    idx = pd.date_range(start_utc, periods=n, freq=f"{minutes}min", tz="UTC", name="time")
    rng = np.random.default_rng(7)
    close = price + np.cumsum(rng.normal(0, 1, n))
    open_ = np.r_[price, close[:-1]]
    df = pd.DataFrame({
        "open": open_, "close": close,
        "high": np.maximum(open_, close) + 0.5, "low": np.minimum(open_, close) - 0.5,
        "volume": np.full(n, 10.0),
    }, index=idx)
    if instrument_id is not None:
        df["instrument_id"] = np.int64(instrument_id)
    return df


def _ts(s: str) -> pd.Timestamp:
    return pd.Timestamp(s, tz="UTC")


# ---------------------------------------------------------------------------
# Kontrakten
# ---------------------------------------------------------------------------

def test_a_valid_frame_passes_unchanged():
    df = _bars("2026-08-26 13:30", 30)
    assert validate_ohlcv(df) is df


def test_empty_response_is_rejected():
    with pytest.raises(OHLCVValidationError, match="tomt"):
        validate_ohlcv(_bars("2026-08-26 13:30", 5).iloc[0:0])
    with pytest.raises(OHLCVValidationError, match="tomt"):
        validate_ohlcv(None)


def test_missing_column_is_rejected():
    with pytest.raises(OHLCVValidationError, match="manglende"):
        validate_ohlcv(_bars("2026-08-26 13:30", 5).drop(columns="low"))


def test_nan_is_rejected_not_filled():
    df = _bars("2026-08-26 13:30", 5)
    df.iloc[3, df.columns.get_loc("close")] = np.nan
    with pytest.raises(OHLCVValidationError, match="NaN"):
        validate_ohlcv(df)


def test_non_monotone_timestamps_are_rejected_not_sorted():
    df = _bars("2026-08-26 13:30", 10)
    shuffled = df.iloc[[0, 1, 3, 2, 4, 5, 6, 7, 8, 9]]
    with pytest.raises(OHLCVValidationError, match="ikke-monotone"):
        validate_ohlcv(shuffled)
    assert count_non_increasing(shuffled.index) == 1


def test_duplicate_timestamps_are_rejected():
    df = _bars("2026-08-26 13:30", 5)
    with pytest.raises(OHLCVValidationError, match="ikke-monotone"):
        validate_ohlcv(pd.concat([df.iloc[:3], df.iloc[2:]]))


def test_naive_or_non_utc_index_is_rejected():
    df = _bars("2026-08-26 13:30", 5)
    with pytest.raises(OHLCVValidationError, match="UTC"):
        validate_ohlcv(df.tz_convert("America/New_York"))
    naive = df.copy()
    naive.index = naive.index.tz_localize(None)
    with pytest.raises(OHLCVValidationError, match="UTC"):
        validate_ohlcv(naive)


# ---------------------------------------------------------------------------
# Sessioner
# ---------------------------------------------------------------------------

def _rth(ts_utc: str, bar_minutes: int = 1) -> bool:
    return bool(sessions.rth_mask(pd.DatetimeIndex([_ts(ts_utc)]), bar_minutes)[0])


def test_rth_is_0930_to_1600_new_york_in_summer():
    assert _rth("2026-08-26 13:30")          # 09:30 EDT
    assert not _rth("2026-08-26 13:29")
    assert _rth("2026-08-26 19:59")          # sidste 1m-bar slutter 16:00
    assert not _rth("2026-08-26 20:00")
    assert _rth("2026-08-26 19:45", 15)      # 15:45-16:00
    assert not _rth("2026-08-26 13:15", 15)  # 09:15-09:30


def test_rth_follows_daylight_saving_time():
    assert _rth("2026-01-14 14:30")          # 09:30 EST
    assert not _rth("2026-01-14 13:30")      # 08:30 EST — ville være RTH om sommeren


def test_half_day_closes_at_1300():
    assert _rth("2025-11-28 17:59")          # 12:59 EST
    assert not _rth("2025-11-28 18:00")


def test_nyse_holidays_have_no_rth_even_though_futures_trade():
    assert not _rth("2026-01-19 15:00")      # MLK Day, 10:00 EST
    assert not _rth("2025-11-27 15:00")      # Thanksgiving
    assert not _rth("2026-08-29 15:00")      # lørdag


def test_rth_mask_fejler_uden_for_kalenderens_vindue():
    """Uden for exchange_calendars' vindue ville alt tavst blive ETH — nu en fejl."""
    plan = sessions._xnys().schedule
    foer = plan.index[0] - pd.Timedelta(days=30) + pd.Timedelta(hours=15)
    efter = plan.index[-1] + pd.Timedelta(days=30) + pd.Timedelta(hours=15)
    for ts in (foer, efter):
        idx = pd.DatetimeIndex([ts.tz_localize("UTC"), _ts("2026-08-26 13:30")])
        with pytest.raises(ValueError, match=r"XNYS-kalenderen dækker .* serien spænder"):
            sessions.rth_mask(idx, 1)


def test_globex_day_starts_at_1800_new_york():
    idx = pd.DatetimeIndex([_ts("2026-08-26 20:59"), _ts("2026-08-26 22:00"),
                            _ts("2026-08-30 22:00")])
    assert list(sessions.globex_day(idx)) == [pd.Timestamp("2026-08-26"),
                                              pd.Timestamp("2026-08-27"),
                                              pd.Timestamp("2026-08-31")]


def test_break_mask_marks_trading_breaks_but_not_short_holes():
    a = _bars("2026-08-26 13:30", 5)                 # 13:30-13:34
    kort = _bars("2026-08-26 14:05", 3)              # 30 min efter forrige bars slut
    lang = _bars("2026-08-26 15:08", 3)              # 60 min efter forrige bars slut
    mask = sessions.break_mask(pd.concat([a, kort, lang]), bar_minutes=1)
    assert mask.tolist() == [True, False, False, False, False,
                             False, False, False,
                             True, False, False]


def test_break_mask_marks_a_roll():
    a = _bars("2026-08-26 13:30", 3, instrument_id=1)
    b = _bars("2026-08-26 13:33", 3, instrument_id=2)
    assert sessions.break_mask(pd.concat([a, b]), 1).tolist() == [True, False, False,
                                                                   True, False, False]


# ---------------------------------------------------------------------------
# Aggregering
# ---------------------------------------------------------------------------

def test_aggregate_builds_ohlcv_from_1m():
    df = _bars("2026-08-26 13:30", 30)
    b15 = resample.aggregate(df, 15)
    assert list(b15.index) == [_ts("2026-08-26 13:30"), _ts("2026-08-26 13:45")]
    first, row = df.iloc[:15], b15.iloc[0]
    assert row["open"] == first["open"].iloc[0]
    assert row["high"] == first["high"].max()
    assert row["low"] == first["low"].min()
    assert row["close"] == first["close"].iloc[-1]
    assert row["volume"] == first["volume"].sum()
    assert row["n_1m"] == 15


def test_bins_are_anchored_to_the_clock_not_to_the_first_bar():
    b15 = resample.aggregate(_bars("2026-08-26 13:37", 20), 15)
    assert b15.index[0] == _ts("2026-08-26 13:30")
    assert b15["n_1m"].tolist() == [8, 12]


def test_higher_timeframes_share_boundaries_by_construction():
    df = _bars("2026-08-25 22:00", 60 * 24)
    t3, t5, t15 = (set(resample.aggregate(df, m).index) for m in (3, 5, 15))
    assert t15 <= t5 and t15 <= t3


def test_rth_open_is_a_boundary_for_every_timeframe_in_both_dst_regimes():
    for aabning in ("2026-08-26 13:30", "2026-01-14 14:30"):
        ts = _ts(aabning)
        for m in resample.TIMEFRAMES:
            assert ts.floor(f"{m}min") == ts


def test_no_aggregated_bar_straddles_the_rth_open_or_close():
    df = _bars("2026-08-26 12:00", 60 * 10)          # 08:00-18:00 EDT
    m1_rth = sessions.rth_mask(df.index, 1)
    for m in resample.TIMEFRAMES:
        b = resample.aggregate(df, m)
        bar_rth = pd.Series(sessions.rth_mask(b.index, m), index=b.index)
        parent = bar_rth.reindex(df.index.floor(f"{m}min")).to_numpy()
        assert (parent == m1_rth).all(), f"{m}m-bar skræver over en sessionsgrænse"


def test_a_roll_inside_a_bin_is_refused():
    a = _bars("2026-08-26 13:30", 7, instrument_id=1)
    b = _bars("2026-08-26 13:37", 8, instrument_id=2)
    with pytest.raises(ValueError, match="blander kontrakter"):
        resample.aggregate(pd.concat([a, b]), 15)


def test_a_roll_on_a_boundary_keeps_the_instrument_per_bar():
    a = _bars("2026-08-26 13:30", 15, instrument_id=1)
    b = _bars("2026-08-26 13:45", 15, instrument_id=2)
    assert resample.aggregate(pd.concat([a, b]), 15)["instrument_id"].tolist() == [1, 2]


def test_empty_bins_are_not_filled():
    df = _bars("2026-08-26 13:30", 60)
    df = df.drop(index=pd.date_range("2026-08-26 13:45", periods=15, freq="1min", tz="UTC"))
    assert _ts("2026-08-26 13:45") not in resample.aggregate(df, 15).index


def test_timeframes_that_do_not_divide_the_hour_are_refused():
    with pytest.raises(ValueError):
        resample.aggregate(_bars("2026-08-26 13:30", 30), 7)


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def test_cache_roundtrip_keeps_utc_index_and_skips_refetch(tmp_path):
    df = _bars("2026-08-26 13:30", 20, instrument_id=5)
    kald = []

    def fetch():
        kald.append(1)
        return df

    p = tmp_path / "x.parquet"
    a = cache_parquet.cached_ohlcv(p, fetch, "test")
    b = cache_parquet.cached_ohlcv(p, fetch, "test")
    assert len(kald) == 1
    assert str(b.index.tz) == "UTC" and b.index.equals(a.index)
    np.testing.assert_array_equal(b[["open", "high", "low", "close", "volume"]].to_numpy(),
                                  df[["open", "high", "low", "close", "volume"]].to_numpy())
    assert b["instrument_id"].dtype == np.int64


def test_an_invalid_response_is_never_written_to_cache(tmp_path):
    p = tmp_path / "x.parquet"
    with pytest.raises(OHLCVValidationError):
        cache_parquet.cached_ohlcv(p, lambda: _bars("2026-08-26 13:30", 5).iloc[0:0], "t")
    assert not any(tmp_path.iterdir())


# ---------------------------------------------------------------------------
# Kilder
# ---------------------------------------------------------------------------

def test_yahoo_frame_is_converted_from_new_york_to_utc():
    idx = pd.date_range("2026-08-26 09:30", periods=3, freq="15min",
                        tz="America/New_York", name="Datetime")
    raw = pd.DataFrame({"Open": [1.0, 2, 3], "High": [2.0, 3, 4], "Low": [0.5, 1, 2],
                        "Close": [1.5, 2.5, 3.5], "Volume": [10, 20, 30],
                        "Dividends": 0.0, "Stock Splits": 0.0}, index=idx)
    df = src_yahoo.from_yfinance(raw)
    assert df.index[0] == _ts("2026-08-26 13:30")
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert sessions.rth_mask(df.index, 15).all()


def test_yahoo_frame_without_timezone_is_rejected():
    raw = pd.DataFrame({"Open": [1.0], "High": [1.0], "Low": [1.0], "Close": [1.0],
                        "Volume": [1]}, index=pd.DatetimeIndex(["2026-08-26 09:30"]))
    with pytest.raises(OHLCVValidationError, match="tidszone"):
        src_yahoo.from_yfinance(raw)


def _db_raw(start: str = "2026-08-26 13:30", n: int = 5) -> pd.DataFrame:
    idx = pd.date_range(start, periods=n, freq="1min", tz="UTC", name="ts_event")
    px = 29_000.0 + np.arange(n)
    return pd.DataFrame({"rtype": 33, "publisher_id": 1,
                         "instrument_id": np.full(n, 42_000, dtype=np.uint32),
                         "open": px, "high": px + 1, "low": px - 1, "close": px + 0.25,
                         "volume": np.full(n, 3, dtype=np.uint64), "symbol": "NQ.v.0"},
                        index=idx)


class _FakeClient:
    """Databento-klient uden netværk: fast estimat, tæller hvor mange gange der hentes."""

    def __init__(self, cost: float, raw: pd.DataFrame):
        self.cost, self.raw = cost, raw
        self.estimates = self.fetches = 0
        self.metadata, self.timeseries = self, self

    def get_cost(self, **kw):
        self.estimates += 1
        return self.cost

    def get_range(self, **kw):
        self.fetches += 1
        return self

    def to_df(self, **kw):
        return self.raw


def test_databento_ohlcv_keeps_instrument_id_for_roll_tracking():
    df = src_databento.from_ohlcv(_db_raw())
    assert df["instrument_id"].dtype == np.int64
    assert df.index.name == "time" and str(df.index.tz) == "UTC"


def _pull(cli, tmp_path, execute=True, budget=25.0):
    return src_databento.pull(cli, "NQ.v.0", "ohlcv-1m", "2026-08-26", "2026-08-27",
                              execute=execute, budget=budget,
                              ledger=tmp_path / "l.jsonl", cache_root=tmp_path)


def test_budget_guard_refuses_before_anything_is_fetched(tmp_path):
    cli = _FakeClient(cost=30.0, raw=_db_raw())
    with pytest.raises(src_databento.BudgetOverskredet):
        _pull(cli, tmp_path)
    assert cli.fetches == 0


def test_budget_counts_what_is_already_spent(tmp_path):
    (tmp_path / "l.jsonl").write_text(json.dumps({"estimat_usd": 20.0}) + "\n")
    cli = _FakeClient(cost=6.0, raw=_db_raw())
    with pytest.raises(src_databento.BudgetOverskredet):
        _pull(cli, tmp_path)
    assert cli.fetches == 0


def test_a_dry_run_estimates_but_never_fetches(tmp_path):
    cli = _FakeClient(cost=1.5, raw=_db_raw())
    plan, df = _pull(cli, tmp_path, execute=False)
    assert df is None and cli.fetches == 0
    assert plan["estimat_usd"].sum() == pytest.approx(1.5)


def test_an_executed_pull_is_booked_cached_and_not_paid_twice(tmp_path):
    cli = _FakeClient(cost=1.5, raw=_db_raw())
    _, df = _pull(cli, tmp_path)
    assert cli.fetches == 1 and len(df) == 5
    assert src_databento.spent_usd(tmp_path / "l.jsonl") == pytest.approx(1.5)
    _, df2 = _pull(cli, tmp_path)
    assert cli.fetches == 1 and cli.estimates == 1
    assert src_databento.spent_usd(tmp_path / "l.jsonl") == pytest.approx(1.5)
    assert df2.index.equals(df.index)


def test_year_chunks_split_on_calendar_years():
    assert src_databento.year_chunks("2024-11-01", "2026-02-01") == [
        ("2024-11-01", "2025-01-01"), ("2025-01-01", "2026-01-01"),
        ("2026-01-01", "2026-02-01")]
    assert src_databento.year_chunks("2025-01-01", "2026-01-01") == [
        ("2025-01-01", "2026-01-01")]


def test_mnq_is_never_requested_before_its_listing(tmp_path):
    """MNQ blev noteret 2019-05-06. En anmodning før afvises før prisen overhovedet slås op."""
    cli = _FakeClient(cost=0.01, raw=_db_raw())
    with pytest.raises(ValueError, match="2019-05-06"):
        src_databento.plan(cli, "MNQ.v.0", "bbo-1m", "2019-05-01", "2019-05-10",
                           cache_root=tmp_path)
    assert cli.estimates == 0
    src_databento.plan(cli, "MNQ.v.0", "bbo-1s", "2019-05-06T22:00", "2019-05-07T21:00",
                       cache_root=tmp_path)
    src_databento.plan(cli, "NQ.v.0", "ohlcv-1m", "2010-06-06", "2010-06-07",
                       cache_root=tmp_path)
    assert cli.estimates == 2


def test_the_phase_budget_is_forty_dollars():
    """Hævet fra $25 den 2026-09-11 — spread skal måles, ikke skønnes."""
    assert src_databento.BUDGET_USD == 40.0
