"""Tests for data/holdout.py — forseglingen af holdout-perioden i B4.

Tre ting låses:

1. **Grænserne er beslutningen.** In-sample 2016-01-01, holdout 2024-01-01. Ændres de,
   skal det være et bevidst valg, ikke en tastefejl.
2. **In-sample åbner aldrig en holdout-fil.** Testen lægger en ødelagt fil i holdout-året;
   bliver den åbnet, fejler læsningen.
3. **Holdout kræver en committet, uændret hypotese**, og hver åbning logges.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from data import holdout
from data.cache_parquet import write_parquet

ROOT = Path(__file__).resolve().parent.parent


def _bars(start_utc: str, n: int) -> pd.DataFrame:
    idx = pd.date_range(start_utc, periods=n, freq="1min", tz="UTC", name="time")
    close = 100.0 + np.arange(n, dtype=float)
    return pd.DataFrame({"open": close, "high": close + 1, "low": close - 1,
                         "close": close, "volume": np.ones(n)}, index=idx)


def _cache(tmp_path: Path, odelagt_holdout: bool = True) -> Path:
    mappe = tmp_path.joinpath("cache", "databento", "GLBX.MDP3", "ohlcv-1m", "NQ.v.0")
    mappe.mkdir(parents=True)
    write_parquet(_bars("2015-12-31 23:40", 20), mappe / "2015-01-01_2016-01-01.parquet")
    write_parquet(_bars("2023-12-29 20:00", 30), mappe / "2023-01-01_2024-01-01.parquet")
    hold = mappe / "2024-01-01_2025-01-01.parquet"
    if odelagt_holdout:
        hold.write_bytes(b"ikke parquet - maa aldrig aabnes af in-sample")
    else:
        write_parquet(_bars("2024-01-01 23:00", 10), hold)
    return tmp_path / "cache"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "--no-optional-locks", "-C", str(repo),
                    "-c", "user.email=test@example.com", "-c", "user.name=test", *args],
                   check=True, capture_output=True)


def test_graenserne_er_beslutningen():
    assert holdout.IN_SAMPLE_START == pd.Timestamp("2016-01-01", tz="UTC")
    assert holdout.HOLDOUT_START == pd.Timestamp("2024-01-01", tz="UTC")


def test_in_sample_aabner_ikke_holdout_filen(tmp_path):
    df = holdout.load_in_sample(cache_root=_cache(tmp_path, odelagt_holdout=True))
    assert df.index.min() >= holdout.IN_SAMPLE_START
    assert df.index.max() < holdout.HOLDOUT_START


def test_in_sample_springer_aar_foer_start_over(tmp_path):
    df = holdout.load_in_sample(cache_root=_cache(tmp_path))
    assert not (df.index < holdout.IN_SAMPLE_START).any()
    assert len(df) == 30


def test_holdout_kraever_at_filen_findes(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    with pytest.raises(holdout.HoldoutForseglet):
        holdout.load_holdout(repo / "frosset.md", cache_root=_cache(tmp_path, False),
                             repo=repo, log=tmp_path / "log.md")


def test_holdout_kraever_commit(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    frosset = repo / "frosset.md"
    frosset.write_text("hypotesen\n")
    with pytest.raises(holdout.HoldoutForseglet, match="ikke committet"):
        holdout.load_holdout(frosset, cache_root=_cache(tmp_path, False),
                             repo=repo, log=tmp_path / "log.md")


def test_holdout_kraever_uaendret_fil(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    frosset = repo / "frosset.md"
    frosset.write_text("hypotesen\n")
    _git(repo, "add", "frosset.md")
    _git(repo, "commit", "-q", "-m", "frys")
    frosset.write_text("hypotesen, justeret bagefter\n")
    with pytest.raises(holdout.HoldoutForseglet, match="ændret"):
        holdout.load_holdout(frosset, cache_root=_cache(tmp_path, False),
                             repo=repo, log=tmp_path / "log.md")


def test_holdout_aabnes_og_logges_for_committet_hypotese(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    frosset = repo / "frosset.md"
    frosset.write_text("hypotesen\n")
    _git(repo, "add", "frosset.md")
    _git(repo, "commit", "-q", "-m", "frys")
    log = tmp_path / "log.md"
    df = holdout.load_holdout(frosset, cache_root=_cache(tmp_path, False), repo=repo, log=log)
    assert df.index.min() >= holdout.HOLDOUT_START
    assert len(df) == 10
    linjer = [l for l in log.read_text().splitlines() if l.startswith("| 20")]
    assert len(linjer) == 1 and "frosset.md" in linjer[0]


def test_b4_kode_laeser_ikke_parquet_direkte():
    """Al B4-kode skal gennem data/holdout.py. Tom mængde består — testen vogter fremtiden."""
    forbudt = re.compile(r"read_parquet|read_ohlcv|cached_ohlcv")
    synder = [p.name for p in (ROOT / "research").glob("b4_*.py")
              if forbudt.search(p.read_text(encoding="utf-8"))]
    assert synder == []
