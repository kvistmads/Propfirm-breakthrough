"""Tests for research/b4_k5_holdout.py — holdout-testen af kandidat 5, §9.3.

- Kørt på in-sample giver den præcis kandidat 5's tal (læser in-sample gennem
  ``k5.mnq``; springes over, hvis serien ikke findes lokalt).
- Syntetiske tests af H2's énsidede grænse, E_f og alle 4 rækker i §5.
- Afskæringen ved 2026-09-30.
- Holdout hentes kun gennem ``load_holdout`` med den frosne hypotese.
- Kandidat 5's modul er uændret fra 9d4bd2e, og hele kørslen går på syntetiske serier.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from research import b4_k5_holdout as kh
from research import b4_k5_vwap_trend as k5
from research.stats import t_critical
from tests.test_b4_k5_vwap_trend import Bygger, sav


# ===========================================================================
# In-sample: præcis kandidat 5's tal
# ===========================================================================

def _in_sample_findes() -> bool:
    try:
        k5.mnq()
    except (FileNotFoundError, OSError):
        return False
    return True


@pytest.mark.skipif(not _in_sample_findes(), reason="MNQ in-sample findes ikke lokalt")
def test_in_sample_giver_kandidat_5s_tal():
    r = kh.in_sample()
    assert r["handler_n"] == 14831 and r["dage_n"] == 1169
    assert round(r["netto_usd_dag"], 2) == 41.07
    assert (round(r["ci95_lo"], 2), round(r["ci95_hi"], 2)) == (9.02, 73.12)
    assert round(r["p_H1"], 4) == 0.0020


# ===========================================================================
# H2, E_f og §5
# ===========================================================================

class TestH2:
    def test_ensidet_95_er_tosidet_90(self):
        rng = np.random.default_rng(1)
        x = rng.normal(5, 40, 300)
        ventet = x.mean() - t_critical(299, 0.10) * x.std(ddof=1) / math.sqrt(300)
        assert kh.nedre_90(x) == pytest.approx(ventet)
        # t-værdien er den énsidede 95%-fraktil.
        assert t_critical(10**6, 0.10) == pytest.approx(1.6449, abs=1e-3)

    def test_graensen(self):
        x = np.array([1.0, -1.0] * 50) + 0.5
        lo = kh.nedre_90(x)
        assert lo > 0
        assert kh.nedre_90(x - (lo + 1e-9)) < 0


def _serie(netto, null_over=0, n_null=500):
    """Et serie-resultat med kun det afgørelsen bruger."""
    netto = np.asarray(netto, dtype=float)
    m = float(netto.mean())
    null = np.r_[np.full(null_over, m + 1), np.full(n_null - null_over, m - 100)]
    lo90 = kh.nedre_90(netto)
    return {"tal": {"_netto_dag": netto}, "netto_usd_dag": m, "ci90_lo": lo90,
            "p_H1": kh.p_h1(m, null)}


class TestRaekker:
    INS = np.array([60.0, 20.0] * 300)

    def test_p_h1(self):
        assert kh.p_h1(5.0, np.array([1.0, 5.0, 6.0, 2.0])) == pytest.approx(3 / 5)
        assert kh.p_h1(10.0, np.zeros(500)) == 1 / 501

    def test_raekke_1(self):
        a = kh.afgoerelse(_serie([50.0, 30.0] * 200), {"tal": {"_netto_dag": self.INS}})
        assert a["H1"] and a["H2"] and a["raekke"] == 1

    def test_raekke_2(self):
        a = kh.afgoerelse(_serie([400.0, -380.0] * 50), {"tal": {"_netto_dag": self.INS}})
        assert a["H1"] and not a["H2"] and a["raekke"] == 2

    def test_raekke_3(self):
        a = kh.afgoerelse(_serie([100.0, -110.0] * 50), {"tal": {"_netto_dag": self.INS}})
        assert a["H1"] and a["raekke"] == 3

    def test_raekke_4(self):
        a = kh.afgoerelse(_serie([50.0, 30.0] * 200, null_over=30),
                          {"tal": {"_netto_dag": self.INS}})
        assert not a["H1"] and a["H2"] and a["raekke"] == 4
        assert kh.raekke(False, False, -5.0) == 4

    def test_graensen_for_h1(self):
        assert kh.p_h1(1.0, np.r_[np.full(24, 2.0), np.zeros(476)]) == 25 / 501
        assert kh.p_h1(1.0, np.r_[np.full(24, 2.0), np.zeros(476)]) <= kh.ALFA_H1
        assert kh.p_h1(1.0, np.r_[np.full(25, 2.0), np.zeros(475)]) > kh.ALFA_H1

    def test_e_f_er_samlet_nedre_grænse(self):
        hold = np.array([10.0, -4.0] * 100)
        a = kh.afgoerelse(_serie(hold), {"tal": {"_netto_dag": self.INS}})
        samlet = np.r_[self.INS, hold]
        assert a["E_f"] == pytest.approx(kh.nedre_90(samlet))
        assert a["samlet_dage_n"] == len(samlet)
        assert a["E_f_over_0"] == (a["E_f"] > 0)


# ===========================================================================
# Afskæringen og åbningen
# ===========================================================================

class TestAfskaering:
    def test_sidste_dag_er_2026_09_30(self):
        b = Bygger(dage=("2026-09-30", "2026-10-01"))
        df = kh.afskaer(b.df)
        et = df.index.tz_convert("America/New_York").normalize().tz_localize(None)
        assert et.max() == pd.Timestamp("2026-09-30")
        assert len(df) == len(b.df) // 2

    def test_dagene(self):
        d = kh.holdout_dage()
        assert d[0] == pd.Timestamp("2024-01-02") and d[-1] == pd.Timestamp("2026-09-30")


class TestAabning:
    def test_kun_load_holdout_med_den_frosne_fil(self, monkeypatch):
        kald = []
        b = Bygger(dage=("2026-09-30", "2026-10-01"))

        def falsk(frosset, symbol="NQ.v.0", **kw):
            kald.append((frosset, symbol, kw))
            return b.df

        monkeypatch.setattr(kh.holdout, "load_holdout", falsk)
        df = kh.holdout_serie()
        assert kald == [(kh.FROSSET, "MNQ.v.0", {})]
        assert kh.FROSSET.name == "b4_k5_holdout.md" and kh.FROSSET.exists()
        assert len(df) == len(b.df) // 2

    def test_ingen_anden_vej_til_data(self):
        kilde = (kh.ROOT / "research" / "b4_k5_holdout.py").read_text(encoding="utf-8")
        assert kilde.count("load_holdout(") == 1
        for x in ("read_parquet", "read_ohlcv", "src_databento", "load_in_sample("):
            assert x not in kilde, x

    def test_kandidat_5_er_uaendret(self):
        assert kh.k5_uaendret()


# ===========================================================================
# Hele kørslen på syntetiske serier
# ===========================================================================

class TestHeleKoerslen:
    def test_analyse_og_rapport(self):
        bh = Bygger(dage=("2026-09-29", "2026-09-30", "2026-10-01"))
        for d in ("2026-09-29", "2026-09-30", "2026-10-01"):
            sav(bh, dag=d)
        bi = Bygger(dage=("2023-06-14", "2023-06-15"))
        for d in ("2023-06-14", "2023-06-15"):
            sav(bi, dag=d, trin=15)
        with np.errstate(all="ignore"):
            res = kh.analyse(bh.df, bi.df, n_reps=20)
        H = res["holdout"]
        assert H["dage_n"] == 2                       # 2026-10-01 er skåret væk
        assert len(H["null"]) == 20 and res["afgoerelse"]["raekke"] in (1, 2, 3, 4)
        assert H["aar"][0]["aar"] == 2026
        md = kh.skriv_md(res, {"koert_utc": "x", "head": "0" * 40, "frosset": "a" * 40})
        assert "Hovedtabel" in md and "E_f" in md and "Række" in md
        tabel = kh.lang_tabel(res)
        assert (tabel["tabel"] == "hoved").sum() == 2
        assert not any(c.startswith("_") for c in tabel.columns)
