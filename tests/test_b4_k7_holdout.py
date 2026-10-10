"""Tests for research/b4_k7_holdout.py — holdout-testen af kandidat 7's T, §9.3.

- Kørt på in-sample giver den præcis kandidat 7's tal for T (læser in-sample gennem
  ``k7.serie``; springes over, hvis serierne ikke findes lokalt).
- Signalets tilstand ved 2023-12-29 er den samme, uanset om serien slutter dér eller
  fortsætter (syntetisk serie).
- Syntetiske tests af H2's énsidede grænse, E_f og alle 4 rækker i §5.
- Afskæringen ved 2026-09-30 og definitionen af urolige måneder.
- Holdout hentes kun gennem ``load_holdout`` med den frosne fil, og NQ.v.0's åbnes ikke.
- Kandidat 7's modul er uændret fra 4c5cc8e, og hele kørslen går på syntetiske serier.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from research import b4_k2_nowick as k2
from research import b4_k7_holdout as kh
from research import b4_k7_rebalancering as k7
from research.stats import t_critical
from tests.test_b4_k7_rebalancering import P_ZN, Bygger, _ct, _xnys


# ===========================================================================
# In-sample: præcis kandidat 7's tal for T
# ===========================================================================

def _in_sample_findes() -> bool:
    try:
        k7.serie(k7.ES), k7.serie(k7.ZN)
    except (FileNotFoundError, OSError):
        return False
    return True


@pytest.mark.skipif(not _in_sample_findes(), reason="ES/ZN in-sample findes ikke lokalt")
def test_in_sample_giver_kandidat_7s_tal_for_T():
    r = kh.in_sample()
    assert r["aktive_dage_n"] == 1949
    assert round(r["netto_usd_dag"], 2) == 16.42
    assert (round(r["ci95_lo"], 2), round(r["ci95_hi"], 2)) == (3.43, 29.42)
    # p_FWE 0,006: Westfall-Young over T og K på samme handel og nulmodel
    ws = k7.positioner(r["sig"])
    tal = {v: k7.variant_tal(r["h"], ws[v]) for v in k7.VARIANTER}
    null = [k7.nret_gentagelse(r["h"], {v: ws[v] for v in k7.VARIANTER}, rep)
            for rep in range(k7.NRET_REPS)]
    wy = k2.westfall_young({v: tal[v]["middel_netto_usd"] for v in k7.VARIANTER},
                           {v: np.array([x[v] for x in null]) for v in k7.VARIANTER})
    assert round(wy["pr_variant"]["T"]["p_FWE"], 3) == 0.006
    # nulmodellen for T alene er den samme række som kandidat 7's
    assert r["null"] == pytest.approx(np.array([x["T"] for x in null]))


# ===========================================================================
# Signalet kører videre uden ny start
# ===========================================================================

def _par(dage, seed=1):
    rng = np.random.default_rng(seed)
    return Bygger(dage, rng=rng, sd=0.5), Bygger(dage, P_ZN, rng=rng, sd=0.01)


def test_signalets_tilstand_ved_2023_12_29_uafhaengig_af_fortsaettelse():
    alle = _xnys("2023-11-01", "2024-02-01")
    es, zn = _par(alle)
    kort = alle[alle <= pd.Timestamp("2023-12-29")]
    slut = _ct("2023-12-29", "16:00")
    s_kort = k7.byg_signal(es.df[es.df.index < slut], zn.df[zn.df.index < slut], kort)
    s_lang = k7.byg_signal(es.df, zn.df, alle)
    n = len(kort)
    assert s_lang.T[:n] == pytest.approx(s_kort.T, nan_ok=True)
    assert s_lang.c[:n] == pytest.approx(s_kort.c, nan_ok=True)
    assert s_lang.s[:n] == pytest.approx(s_kort.s, nan_ok=True)
    # første holdout-dag 2024-01-02 har signaldag 2023-12-29
    h = k7.byg_handel(es.df, alle, k7.ES)
    _, hh = kh.del_op(h)
    assert hh.dage[0] == pd.Timestamp("2024-01-02")
    assert s_lang.dage[hh.t_pos[0]] == pd.Timestamp("2023-12-29")


def test_udsnit_deler_dagene_uden_overlap():
    alle = _xnys("2023-12-01", "2024-01-20")
    es, _ = _par(alle)
    h = k7.byg_handel(es.df, alle, k7.ES)
    hi, hh = kh.del_op(h)
    assert hi.n + hh.n == h.n and hi.dage.max() <= kh.IN_SAMPLE_SLUT
    assert hh.dage.min() >= kh.HOLDOUT_FRA
    assert (hh.G == h.G[h.dage >= kh.HOLDOUT_FRA]).all()


# ===========================================================================
# H2, E_f og §5
# ===========================================================================

class TestH2:
    def test_ensidet_95_er_tosidet_90(self):
        x = np.random.default_rng(1).normal(5, 40, 300)
        ventet = x.mean() - t_critical(299, 0.10) * x.std(ddof=1) / math.sqrt(300)
        assert kh.nedre_90(x) == pytest.approx(ventet)
        assert t_critical(10**6, 0.10) == pytest.approx(1.6449, abs=1e-3)

    def test_p_h1(self):
        assert kh.p_h1(1.0, np.array([0.0, 1.0, 2.0, -1.0])) == pytest.approx(3 / 5)

    def test_alle_fire_raekker(self):
        assert kh.raekke(True, True, 5.0) == 1
        assert kh.raekke(True, False, 0.1) == 2
        assert kh.raekke(True, False, 0.0) == 3
        assert kh.raekke(False, True, 5.0) == 4
        assert kh.raekke(False, False, -1.0) == 4

    def test_e_f_er_samlet_nedre_graense(self):
        rng = np.random.default_rng(2)
        a, b = rng.normal(10, 50, 400), rng.normal(-5, 50, 100)
        dage_a = pd.bdate_range("2019-01-01", periods=400)
        dage_b = pd.bdate_range("2024-01-02", periods=100)
        hold = {"p_H1": 0.04, "ci90_lo": kh.nedre_90(b), "netto_usd_dag": b.mean(),
                "netto": b, "dage": dage_b}
        ins = {"netto": a, "dage": dage_a}
        A = kh.afgoerelse(hold, ins)
        assert A["E_f"] == pytest.approx(kh.nedre_90(np.r_[a, b]))
        assert A["H1"] and A["samlet_dage_n"] == 500
        assert A["raekke"] == kh.raekke(True, kh.nedre_90(b) > 0, b.mean())

    def test_koncentration(self):
        k = kh.koncentration(np.r_[100.0, np.ones(39)])
        assert k["bedste_dag_andel"] == pytest.approx(100 / 139)
        assert k["bedste_5pct_n"] == 2 and k["bedste_5pct_andel"] == pytest.approx(101 / 139)
        assert k["uden_5_bedste"] == pytest.approx(1.0)


# ===========================================================================
# Afskæringen, urolige måneder og åbningen
# ===========================================================================

def test_afskaering_ved_2026_09_30():
    b = Bygger(_xnys("2026-09-29", "2026-10-03"))
    df = kh.afskaer(b.df)
    et = df.index.tz_convert("America/New_York").normalize().tz_localize(None)
    assert et.max() == pd.Timestamp("2026-09-30")
    d = kh.signal_dage()
    assert d[0] == pd.Timestamp("2016-01-04") and d[-1] == pd.Timestamp("2026-09-30")


def test_urolige_maaneder():
    dage = _xnys("2020-01-01", "2020-12-31")
    rng = np.random.default_rng(3)
    R = rng.normal(0, 0.01, len(dage))
    marts = dage.month == 3
    R[marts] *= 6
    R[0] = np.nan
    u = kh.uro_graense(R, dage)
    sd = pd.Series(R, index=dage).dropna()
    sd = sd.groupby(sd.index.to_period("M")).std(ddof=1)
    assert u["graense"] == pytest.approx(np.percentile(sd.to_numpy(), 90))
    assert u["maaneder_n"] == 12 and "2020-03" in u["urolige"]
    assert u["urolige"] == [str(p) for p in sd.index[sd > u["graense"]]]
    m = kh.urolige_dage(dage, R, dage, u["graense"])
    assert m[marts].all() and m.sum() == sum((dage.to_period("M") == pd.Period(p)).sum()
                                            for p in u["urolige"])


class TestAabning:
    def test_kun_load_holdout_med_den_frosne_fil(self, monkeypatch):
        kald = []
        b = Bygger(_xnys("2026-09-29", "2026-10-03"))

        def falsk(frosset, symbol="NQ.v.0", **kw):
            kald.append((frosset, symbol, kw))
            return b.df

        monkeypatch.setattr(kh.holdout, "load_holdout", falsk)
        kh.holdout_serie(k7.ES)
        kh.holdout_serie(k7.ZN)
        assert kald == [(kh.FROSSET, "ES.v.0", {}), (kh.FROSSET, "ZN.v.0", {})]
        assert kh.FROSSET.name == "b4_k7_holdout.md" and kh.FROSSET.exists()
        with pytest.raises(PermissionError):
            kh.holdout_serie("NQ.v.0")
        with pytest.raises(PermissionError):
            kh.holdout_serie("MNQ.v.0")
        assert len(kald) == 2

    def test_ingen_anden_vej_til_data(self):
        kilde = (kh.ROOT / "research" / "b4_k7_holdout.py").read_text(encoding="utf-8")
        assert kilde.count("load_holdout(") == 1
        for x in ("read_parquet", "read_ohlcv", "src_databento", "NQ.v.0\")"):
            assert x not in kilde, x
        assert "NQ" not in "".join(kh.SYMBOLER)

    def test_kandidat_7_er_uaendret(self):
        assert kh.k7_uaendret()


# ===========================================================================
# Hele kørslen på syntetiske serier
# ===========================================================================

def test_analyse_og_rapport():
    alle = _xnys("2023-10-02", "2024-03-01")
    es, zn = _par(alle, seed=7)
    with np.errstate(all="ignore"):
        res = kh.analyse(es.df, zn.df, alle, uro=0.002, n_reps=20)
    H, I = res["holdout"], res["in_sample"]
    assert H["dage"].min() >= pd.Timestamp("2024-01-02")
    assert I["dage"].max() <= pd.Timestamp("2023-12-29")
    assert len(H["null"]) == 20 and res["afgoerelse"]["raekke"] in (1, 2, 3, 4)
    assert res["afgoerelse"]["samlet_dage_n"] == H["aktive_dage_n"] + I["aktive_dage_n"]
    md = kh.skriv_md(res, {"koert_utc": "x", "head": "0" * 40, "frosset": "a" * 40})
    assert "Hovedtabel" in md and "E_f" in md and "række" in md
    tabel = kh.lang_tabel(res)
    assert (tabel["tabel"] == "hoved").sum() == 2
