"""Tests for research/b4_k1_trin2.py — B4 kandidat 1, trin 2.

Præregistreringen er ``research/prereg/b4_k1_trin2.md``. Seks lag testes:

1. **Motoren er trin A's.** ``motor(bedste_fald=False)`` giver samme (udfald, R, exit_i,
   holder) som ``b4_k1_trinA.simuler_handel`` på tilfældige serier, og ``gennemloeb``
   med disciplin og 15m-barer giver samme handelstabel som
   ``b4_k1_trinA.handler_for_variant``. Det er det der gør trin 2's tal sammenlignelige
   med trin A's.
2. **Bedste fald og tvetydige minutter, §8.** Flaget sættes præcis når stoppet og målet
   (eller BE-triggeren) ligger i samme 1m-bar, bedste fald vender netop de bar om, og
   bedste fald er aldrig dårligere end det forsigtige.
3. **Skyggehandler mod disciplin, §4.** Uden disciplinreglerne bliver hvert signal en
   handel; med dem er de en delmængde.
4. **Statistikken, §4.** Den klyngerobuste OLS gengiver hældningen, falder sammen med
   den almindelige robuste standardfejl når hver klynge har ét element, og vokser når
   klyngerne er positivt korrelerede. Testen er én-sidet.
5. **Varianterne og Westfall-Young, §5.** Maskerne er præregistreringens, og p_FWE er
   maks-statistikkens.
6. **Kørslen:** de faste opslagstabeller ændrer ingen filterværdi, N1's zoner får deres
   egne filtre, rapporten kan skrives, og §10's regressionstjek er bundet til de
   præregistrerede tal.
"""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from research import b4_k1_filtre as fl
from research import b4_k1_optaelling as k1
from research import b4_k1_trin2 as t2
from research import b4_k1_trinA as trinA

START_UTC = "2023-06-14 14:00"      # 09:00 CT, midt i indgangsvinduet


# ===========================================================================
# Byggeklodser
# ===========================================================================

def _1m(rows, start: str = START_UTC, iid: int = 1) -> pd.DataFrame:
    a = np.asarray(rows, dtype=float)
    idx = pd.date_range(pd.Timestamp(start, tz="UTC"), periods=len(a), freq="1min")
    return pd.DataFrame({"open": a[:, 0], "high": a[:, 1], "low": a[:, 2], "close": a[:, 3],
                         "volume": 1.0, "instrument_id": np.int64(iid)},
                        index=idx.rename("time"))


def _tilfaeldig_1m(n: int, seed: int, tick: float = 0.25, start: str = "2023-06-05 13:30",
                   iid: int = 1) -> pd.DataFrame:
    """En sammenhængende 1m-serie i hele tick — nok til at motoren kan køre på den."""
    rng = np.random.default_rng(seed)
    close = 15000 + np.cumsum(rng.normal(0, 2.0, n)).round(2)
    close = np.round(close / tick) * tick
    spread = np.abs(rng.normal(0, 2.0, n)).round(2)
    high = np.round((close + spread) / tick) * tick
    low = np.round((close - spread) / tick) * tick
    idx = pd.date_range(pd.Timestamp(start, tz="UTC"), periods=n, freq="1min")
    return pd.DataFrame({"open": close, "high": high, "low": low, "close": close,
                         "volume": 1.0, "instrument_id": np.int64(iid)},
                        index=idx.rename("time"))


# ===========================================================================
# 1. Motoren er trin A's
# ===========================================================================

@pytest.mark.parametrize("seed", range(6))
@pytest.mark.parametrize("be_r", [None, 1.0, 1.2])
def test_motor_er_trin_As_naar_regel_4_staar(seed, be_r):
    df = _tilfaeldig_1m(600, seed)
    h, l, c = (df[k].to_numpy(dtype=float) for k in ("high", "low", "close"))
    n = len(df)
    rng = np.random.default_rng(1000 + seed)
    for _ in range(40):
        entry_i = int(rng.integers(0, n - 60))
        demand = bool(rng.integers(0, 2))
        risiko_pt = float(rng.uniform(2, 20))
        cutoff_i = int(rng.integers(entry_i + 1, n))
        arg = (h, l, c, entry_i, float(c[entry_i]), demand, risiko_pt, be_r, cutoff_i, n)
        ventet = trinA.simuler_handel(*arg)
        faktisk = t2.motor(*arg)
        assert faktisk[:4] == ventet


def _to_dages_serie(seed: int = 11) -> pd.DataFrame:
    """To RTH-dage i 1m, nok til at 15m-zoner kan dannes, berøres og handles."""
    dele = [_tilfaeldig_1m(500, seed, start="2023-06-05 13:30"),
            _tilfaeldig_1m(500, seed + 1, start="2023-06-06 13:30")]
    return pd.concat(dele)


def test_gennemloeb_med_disciplin_er_trin_As_handelstabel():
    from data import resample
    df = _to_dages_serie()
    bars = resample.aggregate(df, 15)
    z = trinA.sizing_ekte(fl.klassificer(bars, k1.find_zoner_v2(bars, k1.BUFFER_V2), 15))
    ventet, tael_v, strejf_v = trinA.handler_for_variant(df, z, 1.2)
    faktisk, tael_f, strejf_f = t2.gennemloeb(df, z, 15, 1.2, disciplin=True)
    assert len(faktisk) == len(ventet)
    for kol in ("udfald", "R_brutto", "R_netto", "holder", "basis_i"):
        assert list(faktisk[kol]) == list(ventet[kol]), kol
    assert tael_f == tael_v
    assert len(strejf_f) == len(strejf_v)


# ===========================================================================
# 2. Bedste fald og tvetydige minutter, §8
# ===========================================================================

def _bar_serie(rows) -> tuple:
    df = _1m(rows)
    return (df["high"].to_numpy(float), df["low"].to_numpy(float),
            df["close"].to_numpy(float), len(df))


def test_tvetydig_naar_stop_og_maal_ligger_i_samme_bar():
    # Fyldning ved 100, risiko 10: stop 90, maal 120. Bar 1 rammer begge.
    h, l, c, n = _bar_serie([(100, 100, 100, 100), (100, 121, 89, 100),
                             (100, 100, 100, 100)])
    forsigtig = t2.motor(h, l, c, 0, 100.0, True, 10.0, None, n, n)
    bedste = t2.motor(h, l, c, 0, 100.0, True, 10.0, None, n, n, bedste_fald=True)
    assert forsigtig[0] == t2.STOP and forsigtig[4] is True
    assert bedste[0] == t2.MAAL and bedste[1] == t2.RR and bedste[4] is True


def test_tvetydig_naar_stop_og_BE_trigger_ligger_i_samme_bar():
    # BE +1,2R: trigger 112. Bar 1 rammer bade 112 og stoppet 90, men ikke maalet 120.
    h, l, c, n = _bar_serie([(100, 100, 100, 100), (100, 113, 89, 100),
                             (100, 100, 100, 100)])
    forsigtig = t2.motor(h, l, c, 0, 100.0, True, 10.0, 1.2, n, n)
    bedste = t2.motor(h, l, c, 0, 100.0, True, 10.0, 1.2, n, n, bedste_fald=True)
    assert forsigtig[0] == t2.STOP and forsigtig[4] is True
    assert bedste[0] == t2.BE_UDFALD and bedste[4] is True
    assert bedste[1] > forsigtig[1]


def test_rent_stop_er_ikke_tvetydigt_og_bedste_fald_aendrer_intet():
    h, l, c, n = _bar_serie([(100, 100, 100, 100), (100, 101, 89, 100),
                             (100, 100, 100, 100)])
    forsigtig = t2.motor(h, l, c, 0, 100.0, True, 10.0, 1.2, n, n)
    bedste = t2.motor(h, l, c, 0, 100.0, True, 10.0, 1.2, n, n, bedste_fald=True)
    assert forsigtig[0] == t2.STOP and forsigtig[4] is False
    assert bedste[:4] == forsigtig[:4]


def test_fyldningsbaren_kan_ikke_vaere_tvetydig_motorrettelse_1():
    # Baade stop og maal i fyldningsbaren: motorrettelse 1 tjekker kun stoppet, begge veje.
    h, l, c, n = _bar_serie([(100, 121, 89, 100), (100, 100, 100, 100)])
    forsigtig = t2.motor(h, l, c, 0, 100.0, True, 10.0, 1.2, n, n)
    bedste = t2.motor(h, l, c, 0, 100.0, True, 10.0, 1.2, n, n, bedste_fald=True)
    assert forsigtig[0] == t2.STOP and forsigtig[4] is False
    assert bedste[:4] == forsigtig[:4]


@pytest.mark.parametrize("seed", range(8))
def test_bedste_fald_er_aldrig_daarligere_end_det_forsigtige(seed):
    df = _tilfaeldig_1m(600, seed)
    h, l, c = (df[k].to_numpy(dtype=float) for k in ("high", "low", "close"))
    n = len(df)
    rng = np.random.default_rng(2000 + seed)
    for _ in range(40):
        entry_i = int(rng.integers(0, n - 60))
        demand = bool(rng.integers(0, 2))
        risiko_pt = float(rng.uniform(2, 20))
        cutoff_i = int(rng.integers(entry_i + 1, n))
        arg = (h, l, c, entry_i, float(c[entry_i]), demand, risiko_pt, 1.2, cutoff_i, n)
        forsigtig = t2.motor(*arg)
        bedste = t2.motor(*arg, bedste_fald=True)
        assert bedste[1] >= forsigtig[1] - 1e-12
        assert bedste[3] >= forsigtig[3]          # holder kan kun blive sandere
        if not forsigtig[4]:
            # Uden en tvetydig bar er udfaldet, R og udgangsbaren de samme. `holder` kan
            # stadig skifte: +1R og stoppet i samme bar er trin A's egen worst case, og
            # den vender bedste fald om — men holder er en diagnose, ikke et udfald.
            assert bedste[:3] == forsigtig[:3]


# ===========================================================================
# 3. Skyggehandler mod disciplin, §4
# ===========================================================================

def test_skyggehandler_tager_hvert_signal_og_disciplin_en_delmaengde():
    df = _to_dages_serie(21)
    bars = k1.resample.aggregate(df, 15) if hasattr(k1, "resample") else None
    from data import resample
    bars = resample.aggregate(df, 15)
    z = trinA.sizing_ekte(fl.klassificer(bars, k1.find_zoner_v2(bars, k1.BUFFER_V2), 15))
    skygge, tael_s, _ = t2.gennemloeb(df, z, 15, 1.2, disciplin=False)
    disciplin, tael_d, _ = t2.gennemloeb(df, z, 15, 1.2, disciplin=True)
    assert len(skygge) >= len(disciplin)
    assert tael_s == {"signaler_sprunget_over_position_n": 0,
                      "signaler_sprunget_over_dagslukket_n": 0}
    assert set(disciplin["basis_i"]) <= set(skygge["basis_i"])
    for _, dag in disciplin.groupby(pd.DatetimeIndex(disciplin["dag"])):
        assert int((dag["udfald"] == t2.BE_UDFALD).sum()) <= 2
        assert len(dag) - int((dag["udfald"] == t2.BE_UDFALD).sum()) <= 1


# ===========================================================================
# 4. Statistikken, §4
# ===========================================================================

def test_ols_gengiver_haeldningen():
    rng = np.random.default_rng(3)
    x = rng.integers(0, 6, 400).astype(float)
    y = 0.3 + 0.12 * x + rng.normal(0, 0.5, 400)
    r = t2.klyngerobust_ols(y, x, np.arange(400))
    a, b = np.polyfit(x, y, 1)
    assert r["beta"] == pytest.approx(a, rel=1e-9)
    assert r["skaering"] == pytest.approx(b, rel=1e-9)
    assert r["klynger_n"] == 400


def _sandwich_med_loekke(y, x, klynge) -> float:
    """Liang-Zeger regnet forfra med en løkke over klyngerne — uafhængigt af modulets
    bincount-vej, så formlen kan efterprøves og ikke bare gentages."""
    y, x, klynge = np.asarray(y, float), np.asarray(x, float), np.asarray(klynge)
    n = len(y)
    X = np.column_stack([np.ones(n), x])
    bread = np.linalg.inv(X.T @ X)
    beta = bread @ (X.T @ y)
    u = y - X @ beta
    meat = np.zeros((2, 2))
    koder = np.unique(klynge)
    for kode in koder:
        m = klynge == kode
        s = X[m].T @ u[m]
        meat += np.outer(s, s)
    g = len(koder)
    V = bread @ meat @ bread * (g / (g - 1)) * ((n - 1) / (n - 2))
    return float(np.sqrt(V[1, 1]))


def test_klyngerobust_se_er_liang_zeger_sandwichen():
    rng = np.random.default_rng(5)
    g, pr_g = 40, 10
    klynge = np.repeat(np.arange(g), pr_g)
    x = rng.integers(0, 6, g * pr_g).astype(float)
    y = 0.1 * x + np.repeat(rng.normal(0, 0.8, g), pr_g) + rng.normal(0, 0.2, g * pr_g)
    r = t2.klyngerobust_ols(y, x, klynge)
    assert r["se"] == pytest.approx(_sandwich_med_loekke(y, x, klynge), rel=1e-10)
    assert r["df"] == g - 1
    assert r["klynger_n"] == g


def test_klyngerobust_se_vokser_naar_hele_dagen_traekker_samme_vej():
    """Scoren er ens inden for dagen, og dagen har sit eget stød: så er de ti handler
    reelt én observation, og den klyngerobuste standardfejl skal sige det. Den
    i.i.d.-robuste tror den har 400."""
    rng = np.random.default_rng(5)
    g, pr_g = 40, 10
    klynge = np.repeat(np.arange(g), pr_g)
    x = np.repeat(rng.integers(0, 6, g).astype(float), pr_g)
    y = 0.1 * x + np.repeat(rng.normal(0, 0.8, g), pr_g) + rng.normal(0, 0.2, g * pr_g)
    smal = t2.klyngerobust_ols(y, x, np.arange(g * pr_g))
    bred = t2.klyngerobust_ols(y, x, klynge)
    assert bred["beta"] == pytest.approx(smal["beta"])
    assert bred["se"] > 2 * smal["se"]
    assert bred["df"] == g - 1


def test_ensidet_p_er_halvdelen_over_nul_og_over_halvdelen_under():
    rng = np.random.default_rng(7)
    x = rng.integers(0, 6, 300).astype(float)
    op = t2.klyngerobust_ols(0.2 * x + rng.normal(0, 0.3, 300), x, np.arange(300))
    ned = t2.klyngerobust_ols(-0.2 * x + rng.normal(0, 0.3, 300), x, np.arange(300))
    assert op["p_ensidet"] < 0.025 and op["signifikant"]
    assert ned["p_ensidet"] > 0.975 and not ned["signifikant"]


def test_ols_uden_variation_i_scoren_giver_intet():
    r = t2.klyngerobust_ols(np.ones(50), np.full(50, 3.0), np.arange(50))
    assert np.isnan(r["beta"]) and not r["signifikant"]


def test_score_loeftet_slaar_5_6_og_7_sammen():
    assert list(t2.score_loft([0, 1, 4, 5, 6, 7])) == [0, 1, 4, 5, 5, 5]


def test_hovedtesten_bruger_det_loftede_score_og_dagen_som_klynge():
    dage = pd.to_datetime(["2023-06-05"] * 3 + ["2023-06-06"] * 3, utc=True)
    h = pd.DataFrame({"R_netto": [0.0, 1.0, 2.0, 0.5, 1.5, 2.5],
                      "score": [0, 5, 7, 1, 6, 7], "dag": dage})
    r = t2.hovedtest(h)
    ventet = t2.klyngerobust_ols(h["R_netto"], [0, 5, 5, 1, 5, 5], pd.DatetimeIndex(dage).asi8)
    assert r["beta"] == pytest.approx(ventet["beta"])
    assert r["klynger_n"] == 2


# ===========================================================================
# 5. Varianterne og Westfall-Young, §5
# ===========================================================================

def _sig(score, brud=None) -> pd.DataFrame:
    n = len(score)
    d = {"score": np.asarray(score, dtype=np.int64)}
    for i, kol in enumerate(t2.KOL):
        d[kol] = np.zeros(n, dtype=bool)
    if brud is not None:
        d[t2.KOL[0]] = np.asarray(brud, dtype=bool)
    return pd.DataFrame(d)


def test_variantmaskerne_er_praeregistreringens():
    sig = _sig([0, 1, 2, 3, 4, 5, 7], brud=[True, False, True, False, True, False, True])
    assert list(t2.variant_maske(sig, "brud_alene")) == [True, False, True, False, True,
                                                         False, True]
    assert list(t2.variant_maske(sig, "score_ge_2")) == [False, False, True, True, True,
                                                         True, True]
    assert list(t2.variant_maske(sig, "score_ge_3")) == [False, False, False, True, True,
                                                          True, True]
    assert list(t2.variant_maske(sig, "score_ge_4")) == [False, False, False, False, True,
                                                          True, True]
    with pytest.raises(ValueError):
        t2.variant_maske(sig, "score_ge_9x")


def test_der_er_fire_varianter_pr_spor_og_otte_i_alt():
    assert len(t2.VARIANTER) == 4 and len(t2.SPOR) == 2
    assert len(t2.VARIANTER) * len(t2.SPOR) == 8


def _kunstig_wy(obs: dict, n1: list[dict]):
    virkelig = {spor: {v: {"noegletal": {"middel_R_netto": obs[(spor, v)]}}
                       for v in t2.VARIANTER} for spor in ("A", "B")}
    liste = [{"A": {"varianter": {v: rep[("A", v)] for v in t2.VARIANTER},
                    "handler_n": {v: 100 for v in t2.VARIANTER}},
              "B": {"varianter": {v: rep[("B", v)] for v in t2.VARIANTER},
                    "handler_n": {v: 100 for v in t2.VARIANTER}}} for rep in n1]
    return virkelig, liste


def test_westfall_young_er_maks_statistikken_over_alle_otte():
    par = [(s, v) for s in ("A", "B") for v in t2.VARIANTER]
    obs = {p: 0.05 for p in par}
    obs[("B", "score_ge_4")] = 0.40
    # 9 gentagelser: to har et maksimum over 0,40 — men kun fordi EN anden variant er hoej.
    n1 = []
    for i in range(9):
        rep = {p: 0.01 for p in par}
        if i < 2:
            rep[("A", "brud_alene")] = 0.50
        n1.append(rep)
    virkelig, liste = _kunstig_wy(obs, n1)
    wy = t2.westfall_young(virkelig, liste)
    assert wy["bedste"] == ("B", "score_ge_4")
    assert wy["p_fwe"] == pytest.approx((1 + 2) / (1 + 9))
    assert len(wy["par"]) == 8


def test_westfall_young_udelader_varianter_uden_handler_i_en_gentagelse():
    par = [(s, v) for s in ("A", "B") for v in t2.VARIANTER]
    obs = {p: 0.05 for p in par}
    obs[("A", "brud_alene")] = 0.30
    rep = {p: float("nan") for p in par}
    rep[("B", "score_ge_2")] = 0.10
    virkelig, liste = _kunstig_wy(obs, [rep])
    wy = t2.westfall_young(virkelig, liste)
    assert wy["maks_fordeling"][0] == pytest.approx(0.10)
    assert wy["p_fwe"] == pytest.approx(1 / 2)


def test_n1_beta_taeller_andelen_over_den_observerede():
    liste = [{"A": {"beta": b}} for b in (-0.1, 0.0, 0.1, 0.2, 0.3)]
    r = t2.n1_beta(liste, "A", 0.1)
    assert r["andel_ge_observeret"] == pytest.approx(3 / 5)
    assert r["p50"] == pytest.approx(0.1)


# ===========================================================================
# §7's beslutningsregel
# ===========================================================================

def _beslut(p_a, p_b, p_fwe, R, lo, hi):
    hovedtests = {"A": {"signifikant": p_a <= 0.025, "p_ensidet": p_a},
                  "B": {"signifikant": p_b <= 0.025, "p_ensidet": p_b}}
    wy = {"bedste": ("A", "score_ge_2"), "p_fwe": p_fwe}
    virkelig = {"A": {"score_ge_2": {"noegletal": {
        "middel_R_netto": R, "middel_R_netto_ci95_lo": lo, "middel_R_netto_ci95_hi": hi}}}}
    return t2.beslutning(hovedtests, wy, virkelig)


def test_stopreglen_gaelder_naar_hovedtesten_fejler_paa_begge_spor():
    b = _beslut(0.4, 0.9, 0.001, 0.5, 0.3, 0.7)
    assert b["kategori"] == "parkeres_stopreglen"


def test_varianten_fryses_kun_naar_alle_tre_krav_er_opfyldt():
    assert _beslut(0.01, 0.9, 0.04, 0.25, 0.05, 0.45)["kategori"] == "varianten_fryses"
    assert _beslut(0.01, 0.9, 0.06, 0.25, 0.05, 0.45)["kategori"] == "parkeres_ingen_variant"
    assert _beslut(0.01, 0.9, 0.04, 0.19, 0.05, 0.33)["kategori"] == "parkeres_ingen_variant"
    assert _beslut(0.01, 0.9, 0.04, 0.25, -0.01, 0.51)["kategori"] == "parkeres_ingen_variant"


def test_alfa_er_bonferroni_over_to_spor():
    assert t2.ALFA_SPOR == pytest.approx(0.05 / 2)


def test_R_er_500_og_saenkes_ikke():
    assert t2.N1_REPS == 500


# ===========================================================================
# 6. Kørslen: faste opslag, N1's egne filtre, rapport og regressionstjek
# ===========================================================================

def _lille_spor(seed: int = 31, n_dage: int = 6) -> tuple:
    from data import resample
    dele = [_tilfaeldig_1m(430, seed + i,
                           start=f"2023-06-{5 + i:02d} 13:30") for i in range(n_dage)]
    df = pd.concat(dele)
    bars = resample.aggregate(df, 15)
    htf = resample.aggregate(df, 60)
    return df, bars, htf


def test_faste_opslag_aendrer_ingen_filterverdi():
    df, bars, htf = _lille_spor()
    z = trinA.sizing_ekte(fl.klassificer(bars, k1.find_zoner_v2(bars, k1.BUFFER_V2), 15))
    sig = z[z["status"] == k1.BEROERT].copy()
    uden = fl.beregn_filtre(sig, bars, htf, 15, 60, k1.BUFFER_V2)
    htf_luk = fl._luk(htf.index, 60)
    mod = fl._modzoner(bars, k1.BUFFER_V2)
    stak = fl._htf_zoner(htf, htf_luk)
    with t2.faste_opslag(bars, htf, htf_luk, mod, stak):
        med = fl.beregn_filtre(sig, bars, htf, 15, 60, k1.BUFFER_V2)
    assert med.equals(uden)
    assert fl._modzoner is not None and fl._htf_zoner is not None
    assert fl._modzoner(bars, k1.BUFFER_V2).keys() == mod.keys()   # sat tilbage


def test_faste_opslag_rejser_hvis_de_kaldes_med_en_anden_serie():
    df, bars, htf = _lille_spor()
    htf_luk = fl._luk(htf.index, 60)
    mod, stak = fl._modzoner(bars, k1.BUFFER_V2), fl._htf_zoner(htf, htf_luk)
    with t2.faste_opslag(bars, htf, htf_luk, mod, stak):
        with pytest.raises(RuntimeError):
            fl._modzoner(bars.iloc[:-1], k1.BUFFER_V2)
        with pytest.raises(RuntimeError):
            fl._modzoner(bars, Fraction(0))
        with pytest.raises(RuntimeError):
            fl._htf_zoner(htf, htf_luk + 1)
        # Lukketidspunkterne regnes forfra hver gang: samme indhold, nyt array, samme svar.
        assert fl._htf_zoner(htf, fl._luk(htf.index, 60)) is stak


def test_faste_opslag_saettes_tilbage_ogsaa_naar_kroppen_fejler():
    df, bars, htf = _lille_spor()
    htf_luk = fl._luk(htf.index, 60)
    oprindelig = fl._modzoner
    with pytest.raises(ZeroDivisionError):
        with t2.faste_opslag(bars, htf, htf_luk, {}, {}):
            raise ZeroDivisionError
    assert fl._modzoner is oprindelig


def test_n1_zoner_faar_deres_egne_filtre_og_egen_score():
    """§5: den flyttede zone får sine egne filterværdier, ikke den rigtige zones."""
    df, bars, htf = _lille_spor(41, 8)
    spor = t2.Spor(navn="A", tf_min=15, htf_min=60, bars=bars, htf=htf,
                   htf_luk=fl._luk(htf.index, 60), mod=fl._modzoner(bars, k1.BUFFER_V2),
                   stak=fl._htf_zoner(htf, fl._luk(htf.index, 60)),
                   zoner=None, sig=None,
                   ekte_side=None, ekte_basis_i=None, ekte_H=None)
    z = trinA.sizing_ekte(fl.klassificer(bars, k1.find_zoner_v2(bars, k1.BUFFER_V2), 15))
    spor.zoner = z
    spor.ekte_side = z["side"].to_numpy()
    spor.ekte_basis_i = z["basis_i"].to_numpy(dtype=np.int64)
    spor.ekte_H = (z["zone_high"] - z["zone_low"]).to_numpy(dtype=float)
    sig = t2.n1_signaler(spor, 0)
    assert set(t2.KOL + ("score",)) <= set(sig.columns)
    assert sig["score"].between(0, 7).all()
    # Dannelseslyset er flyttet: mindst én zone ligger et andet sted end den rigtige.
    if len(sig):
        assert not np.array_equal(np.sort(sig["basis_i"].to_numpy()),
                                  np.sort(spor.ekte_basis_i))


def test_to_gentagelser_med_samme_seed_giver_samme_tal():
    df, bars, htf = _lille_spor(51, 8)
    z = trinA.sizing_ekte(fl.klassificer(bars, k1.find_zoner_v2(bars, k1.BUFFER_V2), 15))
    spor = t2.Spor(navn="A", tf_min=15, htf_min=60, bars=bars, htf=htf,
                   htf_luk=fl._luk(htf.index, 60), mod=fl._modzoner(bars, k1.BUFFER_V2),
                   stak=fl._htf_zoner(htf, fl._luk(htf.index, 60)), zoner=z, sig=z.iloc[:0],
                   ekte_side=z["side"].to_numpy(),
                   ekte_basis_i=z["basis_i"].to_numpy(dtype=np.int64),
                   ekte_H=(z["zone_high"] - z["zone_low"]).to_numpy(dtype=float))
    a = t2.n1_signaler(spor, 3)
    b = t2.n1_signaler(spor, 3)
    c = t2.n1_signaler(spor, 4)
    assert a["basis_i"].tolist() == b["basis_i"].tolist()
    assert a["score"].tolist() == b["score"].tolist()
    assert a["basis_i"].tolist() != c["basis_i"].tolist() or len(a) == 0


def test_noegletal_paa_tom_tabel_er_tomt_men_ikke_en_fejl():
    tom = pd.DataFrame(columns=t2.HANDELSKOL + ["score"])
    r = t2.noegletal(tom)
    assert r["handler_n"] == 0 and np.isnan(r["middel_R_netto"])


def test_regressionstjekkets_tal_er_de_praeregistrerede():
    assert t2.REGRESSION_HANDLER_N == 1226
    assert t2.REGRESSION_MIDDEL_R_NETTO == pytest.approx(-0.0115)
    tekst = t2.PREREG.read_text(encoding="utf-8")
    assert "1.226" in tekst and "0,0115" in tekst


def test_praeregistreringerne_og_filtrene_staar_paa_listen_over_committede_filer():
    stier = {Path(p).name for p in t2.COMMITTEDE}
    assert {"b4_k1_trin2.md", "b4_k1_trin2_optaelling.md",
            "b4_k1_trin2_optaelling_tillaeg.md", "b4_k1_filtre.py", "b4_k1_trinA.py",
            "b4_k1_optaelling.py", "test_b4_k1_trin2.py"} <= stier


def test_pris_hentes_kun_gennem_load_in_sample():
    kilde = Path(t2.__file__).read_text(encoding="utf-8")
    assert "load_in_sample" in kilde
    assert "load_holdout" not in kilde and "HOLDOUT_START" not in kilde


def test_rapporten_kan_skrives_paa_et_kunstigt_resultat():
    """Rapporten må kunne skrives uden at kende de rigtige tal — ellers opdages en
    formateringsfejl først efter en kørsel på flere timer."""
    par = [(s, v) for s in ("A", "B") for v in t2.VARIANTER]
    skygge = pd.DataFrame({
        "dag": pd.to_datetime(["2023-06-05"] * 4 + ["2023-06-06"] * 4, utc=True),
        "side": [k1.DEMAND, k1.SUPPLY] * 4, "R_netto": [0.1, -0.2, 1.9, -1.0] * 2,
        "R_brutto": [0.2, -0.1, 2.0, -0.9] * 2, "score": [0, 2, 5, 7, 1, 3, 4, 6],
        "udfald": [t2.MAAL, t2.STOP, t2.MAAL, t2.STOP] * 2,
        "holder": [True, False] * 4, "tvetydig": [False, True] * 4,
        **{kol: ([True, False] * 4) for kol in t2.KOL}})
    strejf = skygge.assign(R_netto=skygge["R_netto"] / 2)
    noegle = t2.noegletal(skygge)
    noegle.update({"signaler_n": 8, "omk_R_netto_p50": 0.06, "omk_R_netto_p90": 0.18})
    virkelig = {}
    for s in ("A", "B"):
        virkelig[s] = {"spor": None, "signaler_n": 8, "skygge": skygge, "strejf": strejf,
                       "skygge_bedste_fald": skygge, "hovedtest": t2.hovedtest(skygge),
                       "hovedtest_bedste_fald": t2.hovedtest(skygge)}
        for v in t2.VARIANTER:
            virkelig[s][v] = {"noegletal": dict(noegle), "handler": skygge, "strejf": strejf}
    n1 = [{s: {"beta": 0.01 * i, "varianter": {v: 0.01 for v in t2.VARIANTER},
               "handler_n": {v: 50 for v in t2.VARIANTER}} for s in ("A", "B")}
          for i in range(5)]
    wy = t2.westfall_young(virkelig, n1)
    beta_n1 = {s: t2.n1_beta(n1, s, virkelig[s]["hovedtest"]["beta"]) for s in ("A", "B")}
    bf = {"spor": wy["bedste"][0], "variant": wy["bedste"][1], **noegle}
    b = t2.beslutning({s: r["hovedtest"] for s, r in virkelig.items()}, wy, virkelig)
    tabel = t2.lang_tabel(virkelig, wy, n1, beta_n1, bf)
    assert set(tabel.columns) == {"spor", "tabel", "noegle", "stoerrelse", "vaerdi"}
    assert tabel["vaerdi"].map(lambda v: isinstance(v, float)).all()
    md = t2.skriv_md(
        {"virkelig": virkelig, "wy": wy, "beta_n1": beta_n1, "beslutning": b,
         "bedste_fald_variant": bf},
        {"koert_utc": "2026-09-24 00:00", "head": "0" * 40,
         "commits": {p: "0" * 40 for p in
                     ("research/b4_k1_trin2.py", "tests/test_b4_k1_trin2.py",
                      "research/prereg/b4_k1_trin2.md",
                      "research/prereg/b4_k1_trin2_optaelling.md",
                      "research/prereg/b4_k1_trin2_optaelling_tillaeg.md",
                      "research/b4_k1_filtre.py", "research/b4_k1_optaelling.py",
                      "research/b4_k1_trinA.py")},
         "foerste_bar_utc": "2019-05-06 00:00", "sidste_bar_utc": "2023-12-29 21:59",
         "n_1m": 1638282,
         "regression": {"csv_byte_for_byte": True, "motor_ok": True, "score_ok": True,
                        "motor_handler_n": 1226, "motor_middel_R_netto": -0.0115,
                        "score_rader_n": 80}})
    for overskrift in ("Hovedtesten, §4", "Varianterne, §5", "Beslutningsreglen, §7",
                       "Diagnoserne, §8", "Regressionstjek, §10"):
        assert overskrift in md
    assert "|" in md and "β" in md


def test_scorelinjerne_laeses_af_optaellingens_csv_som_raa_tekst():
    """§10's tjek 3 sammenligner csv-tekst, ikke genindlæste floats: en float der har
    været gennem decimaltekst kan komme tilbage én ULP ved siden af sig selv."""
    linjer = t2._score_linjer_af_fil(t2.OPTAELLING_CSV)
    assert len(linjer) == 80                      # 2 spor × 8 scorer × 5 størrelser
    assert {x.split(",")[0] for x in linjer} == {"A", "B"}
    assert {x.split(",")[1] for x in linjer} == {"score"}
    assert "A,score,alle,alle,0,signaler_n,36.0" in linjer


def test_scorelinjer_nu_har_optaellingens_kolonneorden():
    from data import resample
    df, bars, htf = _lille_spor(61, 6)
    z = trinA.sizing_ekte(fl.klassificer(bars, k1.find_zoner_v2(bars, k1.BUFFER_V2), 15))
    sig = z[z["status"] == k1.BEROERT].copy()
    sig = pd.concat([sig, fl.beregn_filtre(sig, bars, htf, 15, 60, k1.BUFFER_V2)], axis=1)
    spor = t2.Spor(navn="A", tf_min=15, htf_min=60, bars=bars, htf=htf,
                   htf_luk=fl._luk(htf.index, 60), mod={}, stak={}, zoner=z, sig=sig,
                   ekte_side=z["side"].to_numpy(),
                   ekte_basis_i=z["basis_i"].to_numpy(dtype=np.int64),
                   ekte_H=(z["zone_high"] - z["zone_low"]).to_numpy(dtype=float))
    dage = pd.DatetimeIndex(sorted(set(pd.DatetimeIndex(sig["dag"]).dropna())))
    linjer = t2._score_linjer_nu((spor,), dage)
    assert len(linjer) == 8 * 5
    assert all(x.split(",")[:2] == ["A", "score"] for x in linjer)
