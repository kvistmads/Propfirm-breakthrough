"""Tests for research/b4_k6_holdout.py — holdout-testen af kandidat 6's V2 · salg, §9.3.

- Kørt på in-sample giver den præcis kandidat 6's tal for V2 · salg ved $2,85 (læser
  in-sample gennem ``k6.serie``; springes over, hvis serien ikke findes lokalt), og N-nat er
  kandidat 6's egen.
- Salgsdagen for den første holdout-nat tages fra 2023-12-29 (syntetisk serie).
- Syntetiske tests af H2's énsidede grænse, E_f og alle 4 rækker i §5.
- Afskæringen ved 2026-09-30.
- Holdout hentes kun gennem ``load_holdout`` med den frosne fil og kun for NQ.v.0.
- Rapporten indeholder ingen andre vinduer, ingen "alle nætter" og ingen long hele natten.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from research import b4_k1_optaelling as k1
from research import b4_k6_holdout as kh
from research import b4_k6_overnight as k6
from research.stats import t_critical
from tests.test_b4_k6_overnight import P, Bygger, _ct


def _xnys(fra: str, til: str) -> pd.DatetimeIndex:
    return k1.rth_dage(fra, til)


# ===========================================================================
# In-sample: præcis kandidat 6's tal for V2 · salg
# ===========================================================================

def _in_sample_findes() -> bool:
    try:
        k6.serie(kh.SYMBOL)
    except (FileNotFoundError, OSError):
        return False
    return True


@pytest.mark.skipif(not _in_sample_findes(), reason="NQ in-sample findes ikke lokalt")
def test_in_sample_giver_kandidat_6s_tal_for_V2_salg():
    assert kh.regression_k6()["ok"]
    r = kh.in_sample(n_reps=5)
    s = r["netto_285_seg"]
    assert s["n"] == 902 and r["naetter_n"] == 902
    assert round(s["middel"], 2) == 11.07
    assert (round(s["lo"], 2), round(s["hi"], 2)) == (-0.95, 23.09)
    assert round(r["netto_usd_nat"], 2) == 10.82          # §4: in-sample ved $3,10
    # N-nat er kandidat 6's egen, gentagelse for gentagelse
    g = r["g"]
    nvs = k6.forbered_nnat(g)
    ventet = [k6.nnat_gentagelse(g, nvs, rep)[kh.V] for rep in range(5)]
    assert r["null"] + kh.OMK == pytest.approx(np.array(ventet) + k6.OMK_USD)


# ===========================================================================
# Den samlede serie
# ===========================================================================

def test_salgsdag_for_foerste_holdout_nat_fra_2023_12_29():
    dage = _xnys("2023-12-20", "2024-01-10")
    for luk, ventet in ((P - 10.0, 1.0), (P + 10.0, 0.0)):
        b = Bygger(dage)
        b.saet(_ct("2023-12-29", "14:59"), close=luk)
        g = k6.byg_grundlag(b.df, dage, "syntetisk")
        i = int(np.flatnonzero(g.dage == pd.Timestamp("2024-01-02"))[0])
        assert g.forrige[i] == pd.Timestamp("2023-12-29")
        assert g.salg[i] == ventet
        um = kh.udsnit_masker(g)
        assert um["holdout"][i] and not um["in_sample"][i]
        assert g.dage[um["in_sample"]].max() == pd.Timestamp("2023-12-29")
        assert g.dage[um["holdout"]].min() == pd.Timestamp("2024-01-02")


def test_in_sample_delen_er_den_samme_som_in_sample_alene():
    """Grundlag, handel og N-nat på den samlede serie giver in-sample-nætterne præcis som en
    kørsel på in-sample alene (læsning 4: trækket er det samme i de første rækker)."""
    dage = _xnys("2023-11-01", "2024-02-01")
    b = Bygger(dage, rng=np.random.default_rng(5))
    for d in dage[::2]:                        # nogle salgsdage
        b.saet(_ct(str(d.date()), "14:59"), close=b.df.loc[_ct(str(d.date()), "08:30"),
                                                            "open"] - 5)
    ins_dage = dage[dage <= kh.IN_SAMPLE_SLUT]
    df_ins = b.df[b.df.index < pd.Timestamp("2024-01-01", tz="UTC")]
    g_s = k6.byg_grundlag(b.df, dage, "s")
    g_i = k6.byg_grundlag(df_ins, ins_dage, "i")
    h_s, h_i = k6.handel(g_s, "V2", kh.OMK), k6.handel(g_i, "V2", kh.OMK)
    nv_s = k6.nnat_vaerdier(g_s, k6.nat_gitter(g_s), "V2")
    nv_i = k6.nnat_vaerdier(g_i, k6.nat_gitter(g_i), "V2")
    a = kh.serie_resultat(g_s, h_s, nv_s, kh.udsnit_masker(g_s)["in_sample"], n_reps=10)
    c = kh.serie_resultat(g_i, h_i, nv_i, np.ones(len(ins_dage), bool), n_reps=10)
    assert a["naetter_n"] == c["naetter_n"] > 0
    assert a["netto"] == pytest.approx(c["netto"])
    assert a["null"] == pytest.approx(c["null"])
    # og nulmodellen er kandidat 6's ved $2,85
    nvs = k6.forbered_nnat(g_i)
    ventet = [k6.nnat_gentagelse(g_i, nvs, rep)[kh.V] for rep in range(10)]
    assert c["null"] + kh.OMK - k6.OMK_USD == pytest.approx(ventet)


# ===========================================================================
# H2, E_f og §5
# ===========================================================================

class TestH2:
    def test_ensidet_95_er_tosidet_90(self):
        x = np.random.default_rng(1).normal(5, 190, 309)
        ventet = x.mean() - t_critical(308, 0.10) * x.std(ddof=1) / math.sqrt(309)
        assert kh.nedre_90(x) == pytest.approx(ventet)
        assert t_critical(10**6, 0.10) == pytest.approx(1.6449, abs=1e-3)

    def test_p_h1(self):
        assert kh.p_h1(1.0, np.array([0.0, 1.0, 2.0, -1.0])) == pytest.approx(3 / 5)
        assert kh.p_h1(9.0, np.zeros(500)) == pytest.approx(1 / 501)

    def test_alle_fire_raekker(self):
        assert kh.raekke(True, True, 5.0) == 1
        assert kh.raekke(True, False, 0.1) == 2
        assert kh.raekke(True, False, 0.0) == 3
        assert kh.raekke(True, False, -2.0) == 3
        assert kh.raekke(False, True, 5.0) == 4
        assert kh.raekke(False, False, -1.0) == 4

    def test_e_f_er_samlet_nedre_graense(self):
        rng = np.random.default_rng(2)
        a, b = rng.normal(10, 190, 902), rng.normal(-5, 190, 309)
        hold = {"p_H1": 0.04, "ci90_lo": kh.nedre_90(b), "netto_usd_nat": b.mean(),
                "netto": b, "netto_285": b + 0.25}
        ins = {"netto": a, "netto_285": a + 0.25}
        A = kh.afgoerelse(hold, ins)
        assert A["E_f"] == pytest.approx(kh.nedre_90(np.r_[a, b]))
        assert A["E_f_285"] == pytest.approx(A["E_f"] + 0.25)
        assert A["H1"] and A["samlet_naetter_n"] == 1211
        assert A["raekke"] == kh.raekke(True, kh.nedre_90(b) > 0, b.mean())
        assert A["tekst"] == kh.TEKST[A["raekke"]]

    @pytest.mark.parametrize("p, mu, nr", [(0.01, 60.0, 1), (0.01, 5.0, 2), (0.01, -5.0, 3),
                                           (0.20, 60.0, 4), (0.20, -5.0, 4)])
    def test_afgoerelse_alle_fire_raekker(self, p, mu, nr):
        b = mu + np.random.default_rng(3).normal(0, 190, 300)
        b = b - b.mean() + mu
        hold = {"p_H1": p, "ci90_lo": kh.nedre_90(b), "netto_usd_nat": float(b.mean()),
                "netto": b, "netto_285": b + 0.25}
        assert kh.afgoerelse(hold, {"netto": b, "netto_285": b})["raekke"] == nr

    def test_koncentration(self):
        dage = pd.bdate_range("2024-01-02", periods=40)
        x = np.r_[100.0, np.ones(39)]
        k = kh.koncentration(x, dage)
        assert k["bedste_nat_andel"] == pytest.approx(100 / 139)
        assert k["bedste_5pct_n"] == 2 and k["bedste_5pct_andel"] == pytest.approx(101 / 139)
        assert k["uden_5_bedste"] == pytest.approx(1.0)
        assert k["bedste_maaned"] == "2024-01"
        jan = np.asarray(dage.month == 1)
        assert k["uden_bedste_maaned"] == pytest.approx(x[~jan].mean())


# ===========================================================================
# Afskæringen og åbningen
# ===========================================================================

def test_afskaering_ved_2026_09_30():
    b = Bygger(_xnys("2026-09-28", "2026-10-06"))
    df = kh.afskaer(b.df)
    et = df.index.tz_convert("America/New_York").normalize().tz_localize(None)
    assert et.max() == pd.Timestamp("2026-09-30")
    d = kh.nat_dage()
    assert d[0] == pd.Timestamp("2016-01-04") and d[-1] == pd.Timestamp("2026-09-30")
    assert (d <= kh.IN_SAMPLE_SLUT).sum() == len(k6.xnys_dage(kh.SYMBOL))


class TestAabning:
    def test_kun_load_holdout_med_den_frosne_fil_og_kun_NQ(self, monkeypatch):
        kald = []
        b = Bygger(_xnys("2026-09-28", "2026-10-06"))

        def falsk(frosset, symbol="NQ.v.0", **kw):
            kald.append((frosset, symbol, kw))
            return b.df

        monkeypatch.setattr(kh.holdout, "load_holdout", falsk)
        kh.holdout_serie("NQ.v.0")
        assert kald == [(kh.FROSSET, "NQ.v.0", {})]
        assert kh.FROSSET.name == "b4_k6_holdout.md" and kh.FROSSET.exists()
        for sym in ("MNQ.v.0", "ES.v.0", "ZN.v.0"):
            with pytest.raises(PermissionError):
                kh.holdout_serie(sym)
        assert len(kald) == 1

    def test_ingen_anden_vej_til_data(self):
        kilde = (kh.ROOT / "research" / "b4_k6_holdout.py").read_text(encoding="utf-8")
        assert kilde.count("load_holdout(") == 1
        for x in ("read_parquet", "read_ohlcv", "src_databento", "MNQ.v.0", "KONTROL"):
            assert x not in kilde, x
        assert kh.SYMBOL == "NQ.v.0"

    def test_kandidat_6_er_uaendret(self):
        assert kh.k6_uaendret()


# ===========================================================================
# Hele kørslen på en syntetisk serie, og hvad rapporten må indeholde
# ===========================================================================

def test_analyse_og_rapport_kun_V2_salg(monkeypatch):
    dage = _xnys("2023-11-01", "2024-03-01")
    b = Bygger(dage, rng=np.random.default_rng(7))
    for d in dage[::2]:
        b.saet(_ct(str(d.date()), "14:59"), close=b.df.loc[_ct(str(d.date()), "08:30"),
                                                            "open"] - 5)
    # det der regner V1, "alle" eller hele natten, må ikke kaldes
    def forbudt(*a, **kw):
        raise AssertionError("må ikke kaldes på holdout")

    for navn in ("analyse", "diagnoser", "lang_hele_natten", "nnat_gentagelse", "forbered",
                 "forbered_nnat", "optaelling"):
        monkeypatch.setattr(k6, navn, forbudt)
    vinduer = []
    ægte = k6.handel
    monkeypatch.setattr(k6, "handel", lambda g, w, *a, **kw: (vinduer.append(w),
                                                              ægte(g, w, *a, **kw))[1])
    with np.errstate(all="ignore"):
        res = kh.analyse(b.df, dage, n_reps=20)
    assert vinduer == ["V2"]
    H, I = res["holdout"], res["in_sample"]
    assert H["dage"].min() >= pd.Timestamp("2024-01-02")
    assert I["dage"].max() <= pd.Timestamp("2023-12-29")
    assert len(H["null"]) == 20 and res["afgoerelse"]["raekke"] in (1, 2, 3, 4)
    assert res["afgoerelse"]["samlet_naetter_n"] == H["naetter_n"] + I["naetter_n"]
    assert {a["aar"] for a in H["aar"]} == {2024}
    md = kh.skriv_md(res, {"koert_utc": "x", "head": "0" * 40, "frosset": "a" * 40})
    assert "Hovedtabel" in md and "E_f" in md and "række" in md and "V2 · salg" in md
    lav = md.lower()
    for x in ("v1", "v2 · alle", "alle nætter", "hele natten", "17:00", "08:30", "long hele"):
        assert x not in lav, x
    tabel = kh.lang_tabel(res)
    assert (tabel["tabel"] == "hoved").sum() == 2
    assert not any("V1" in str(c) or "hele" in str(c) or "alle" in str(c)
                   for c in tabel.columns)
