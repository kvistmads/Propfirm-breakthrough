"""Tests for research/b4_k1_optaelling.py — signaloptællingen for kandidat 1.

Hver definition i præregistreringens §3 låses med syntetiske 15m-lys: basislys og
udbrudslys, zonen gyldig fra udbrudslysets lukning, død ved første berøring, død ved nyt
instrument_id, vinduet 08:30-14:30 CT, halve dage og stoploftet 0,429%.

Dertil tre ting:

1. **Tillæggets implementeringsdetaljer** — nabolys over et hul, zonealder, "dannet" og
   nævnerne i rapporten.
2. **En reference lys for lys.** ``find_zoner`` skal give det samme som en løkke uden
   genveje på tilfældige serier med huller, dojier, tick-lighed og kontraktskift.
3. **Intet efter berøringslyset indgår.** Serien skæres af lige efter hver zones
   slutlys, og af slutlyset beholdes kun den kant der afgør berøringen. Zonens forløb
   må ikke ændre sig.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from data import holdout
from research import b4_k1_optaelling as k1
from research.stats import wilson_interval

CT = "America/Chicago"
KVARTER = pd.Timedelta(minutes=15)

# Demand ved 10.000: rødt basislys, kroppen 10.000-10.010, vægerne til 9.995 og 10.015.
# Zonen er 9.995-10.015, højde 0,2%. Udbrudslyset dykker ned i zonen og lukker over.
BASIS_D = (10_010, 10_015, 9_995, 10_000)
UDBRUD_D = (10_000, 10_030, 9_998, 10_020)
OVER = (10_022, 10_025, 10_020, 10_022)       # doji over zonen, rører den ikke
BEROER_D = (10_018, 10_021, 10_014, 10_018)   # doji, low 10.014 ≤ 10.015
# Supply spejlet: grønt basislys, zonen 9.985-10.005.
BASIS_S = (9_990, 10_005, 9_985, 10_000)
UDBRUD_S = (10_000, 10_002, 9_970, 9_980)
UNDER = (9_978, 9_980, 9_975, 9_978)          # doji under zonen
BEROER_S = (9_978, 9_986, 9_975, 9_978)       # doji, high 9.986 ≥ 9.985

DAG = "2023-06-14"          # onsdag, almindelig RTH-dag, CDT


def _ct(t) -> pd.Timestamp:
    t = pd.Timestamp(t)
    return t.tz_localize(CT) if t.tzinfo is None else t.tz_convert(CT)


def _barer(lys, start_ct=None, tider_ct=None, iid=1) -> pd.DataFrame:
    """15m-lys fra (open, high, low, close). Tider i CT: nabokvarterer fra ``start_ct``
    eller eksplicitte ``tider_ct``."""
    if tider_ct is None:
        idx = pd.date_range(_ct(start_ct or f"{DAG} 09:00"), periods=len(lys), freq="15min")
    else:
        idx = pd.DatetimeIndex([_ct(t) for t in tider_ct])
    a = np.asarray(lys, dtype=float)
    return pd.DataFrame({
        "open": a[:, 0], "high": a[:, 1], "low": a[:, 2], "close": a[:, 3], "volume": 1.0,
        "instrument_id": np.broadcast_to(np.asarray(iid, dtype=np.int64), len(lys)).copy(),
    }, index=idx.tz_convert("UTC").rename("time"))


def _zoner(bars: pd.DataFrame) -> pd.DataFrame:
    return k1.klassificer(bars, k1.find_zoner(bars))


def _zone(z: pd.DataFrame, basis_i: int) -> pd.Series:
    r = z[z["basis_i"] == basis_i]
    assert len(r) == 1
    return r.iloc[0]


# ---------------------------------------------------------------------------
# §3 Basislys og udbrudslys
# ---------------------------------------------------------------------------

def test_demand_er_roedt_basislys_og_udbrud_der_lukker_over_high():
    z = _zoner(_barer([BASIS_D, UDBRUD_D, OVER]))
    assert len(z) == 1
    r = z.iloc[0]
    assert (r["side"], r["basis_i"], r["udbrud_i"]) == ("demand", 0, 1)


@pytest.mark.parametrize("udbrud_close, zone", [(10_015.0, False), (10_015.25, True)])
def test_demand_udbruddet_skal_lukke_strengt_over_basislysets_high(udbrud_close, zone):
    udbrud = (10_000, 10_030, 9_998, udbrud_close)
    assert (len(_zoner(_barer([BASIS_D, udbrud, OVER]))) == 1) is zone


def test_supply_er_groent_basislys_og_udbrud_der_lukker_under_low():
    z = _zoner(_barer([BASIS_S, UDBRUD_S, UNDER]))
    assert len(z) == 1
    r = z.iloc[0]
    assert (r["side"], r["zone_low"], r["zone_high"]) == ("supply", 9_985, 10_005)


@pytest.mark.parametrize("udbrud_close, zone", [(9_985.0, False), (9_984.75, True)])
def test_supply_udbruddet_skal_lukke_strengt_under_basislysets_low(udbrud_close, zone):
    udbrud = (10_000, 10_002, 9_970, udbrud_close)
    assert (len(_zoner(_barer([BASIS_S, udbrud, UNDER]))) == 1) is zone


def test_farven_skal_passe_til_siden():
    groen = (10_000, 10_015, 9_995, 10_010)      # grønt under et demand-udbrud
    roed = (10_000, 10_005, 9_985, 9_990)        # rødt over et supply-udbrud
    assert _zoner(_barer([groen, UDBRUD_D, OVER])).empty
    assert _zoner(_barer([roed, UDBRUD_S, UNDER])).empty


def test_doji_er_hverken_roedt_eller_groent_og_kan_ikke_vaere_basislys():
    doji = (10_005, 10_015, 9_995, 10_005)
    assert _zoner(_barer([doji, UDBRUD_D, OVER])).empty
    assert _zoner(_barer([doji, UDBRUD_S, UNDER])).empty


def test_basis_og_udbrud_er_naboer_ikke_lys_med_et_lys_imellem():
    mellem = (10_005, 10_012, 10_001, 10_005)     # doji inde i basislysets krop
    assert len(_zoner(_barer([BASIS_D, UDBRUD_D, OVER]))) == 1
    assert _zoner(_barer([BASIS_D, mellem, UDBRUD_D, OVER])).empty


# ---------------------------------------------------------------------------
# §3 Zonen: basislysets high til low, væger medregnet, gyldig fra udbrudslysets lukning
# ---------------------------------------------------------------------------

def test_zonen_er_basislysets_high_til_low_med_vaeger():
    r = _zoner(_barer([BASIS_D, UDBRUD_D, OVER])).iloc[0]
    assert (r["zone_low"], r["zone_high"]) == (9_995, 10_015)     # ikke kroppen 10.000-10.010
    assert r["basis_close"] == 10_000
    assert r["hoejde_pct"] == pytest.approx(20 / 10_000 * 100)


def test_en_beroering_af_vaegen_er_en_beroering():
    vaeg = (10_018, 10_021, 10_012, 10_018)       # low over kroppen, inde i vægen
    r = _zone(_zoner(_barer([BASIS_D, UDBRUD_D, OVER, vaeg])), 0)
    assert (r["status"], r["slut_i"]) == ("beroert", 3)


def test_zonen_er_gyldig_fra_udbrudslysets_lukning():
    """Udbrudslyset dykker ned i zonen, men det er ikke en berøring."""
    assert UDBRUD_D[2] <= BASIS_D[1]
    r = _zone(_zoner(_barer([BASIS_D, UDBRUD_D, OVER, OVER, BEROER_D])), 0)
    assert (r["status"], r["slut_i"]) == ("beroert", 4)


def test_lyset_lige_efter_udbruddet_kan_vaere_beroeringen():
    r = _zone(_zoner(_barer([BASIS_D, UDBRUD_D, BEROER_D])), 0)
    assert (r["status"], r["slut_i"], r["zonealder_timer"]) == ("beroert", 2, 0.0)


@pytest.mark.parametrize("low, beroert", [(10_015.0, True), (10_015.25, False)])
def test_demand_beroering_er_low_mindre_end_eller_lig_zonens_high(low, beroert):
    lys = (10_018, 10_021, low, 10_018)
    r = _zone(_zoner(_barer([BASIS_D, UDBRUD_D, lys])), 0)
    assert r["status"] == ("beroert" if beroert else "aaben")


@pytest.mark.parametrize("high, beroert", [(9_985.0, True), (9_984.75, False)])
def test_supply_beroering_er_high_stoerre_end_eller_lig_zonens_low(high, beroert):
    lys = (9_978, high, 9_975, 9_978)
    r = _zone(_zoner(_barer([BASIS_S, UDBRUD_S, lys])), 0)
    assert r["status"] == ("beroert" if beroert else "aaben")


# ---------------------------------------------------------------------------
# §3 Død ved første berøring, uanset tidspunkt
# ---------------------------------------------------------------------------

def test_zonen_doer_ved_foerste_beroering_ogsaa_uden_for_vinduet():
    """Natberøringen 03:00 CT er ikke et signal, men zonen er brugt. 09:30 tæller ikke."""
    tider = [f"{DAG} 02:30", f"{DAG} 02:45", f"{DAG} 03:00", f"{DAG} 09:30"]
    z = _zoner(_barer([BASIS_D, UDBRUD_D, BEROER_D, BEROER_D], tider_ct=tider))
    r = _zone(z, 0)
    assert (r["status"], r["slut_i"]) == ("beroert", 2)
    assert not r["i_vindue"] and not r["signal"]
    assert not z["signal"].any()
    # Uden natberøringen er 09:30 den første, og så er den et signal.
    r2 = _zone(_zoner(_barer([BASIS_D, UDBRUD_D, OVER, BEROER_D], tider_ct=tider)), 0)
    assert (r2["slut_i"], r2["signal"]) == (3, True)


def test_en_berort_zone_giver_ikke_flere_signaler():
    z = _zoner(_barer([BASIS_D, UDBRUD_D, BEROER_D, OVER, BEROER_D]))
    assert int(z["signal"].sum()) == 1


# ---------------------------------------------------------------------------
# §3 Kontraktskift
# ---------------------------------------------------------------------------

def test_zonen_doer_ved_nyt_instrument_id_uden_beroering():
    """Skiftelyset ville røre zonen, men det vurderes ikke som berøring."""
    bars = _barer([BASIS_D, UDBRUD_D, OVER, BEROER_D], iid=[1, 1, 1, 2])
    r = _zone(_zoner(bars), 0)
    assert (r["status"], r["slut_i"], r["signal"]) == ("kontraktskift", 3, False)


def test_zonen_doer_ved_foerste_skift_ogsaa_hvis_kontrakten_vender_tilbage():
    bars = _barer([BASIS_D, UDBRUD_D, OVER, BEROER_D], iid=[1, 1, 2, 1])
    r = _zone(_zoner(bars), 0)
    assert (r["status"], r["slut_i"]) == ("kontraktskift", 2)


def test_basis_og_udbrud_i_hver_sin_kontrakt_doer_ved_udbrudslyset():
    """Tillægget: parret tælles som dannet og dør ved skiftet, før det er gyldigt."""
    z = _zoner(_barer([BASIS_D, UDBRUD_D, BEROER_D], iid=[1, 2, 2]))
    r = _zone(z, 0)
    assert (r["status"], r["slut_i"], r["signal"]) == ("kontraktskift", 1, False)
    row = k1.noegletal(z, k1.rth_dage(DAG, "2023-06-15"))
    assert row["zoner_basis_og_udbrud_i_hver_sin_kontrakt_n"] == 1
    assert row["zoner_doede_ved_kontraktskift_n"] == 1


def test_en_zone_i_den_nye_kontrakt_lever_normalt():
    z = _zoner(_barer([OVER, BASIS_D, UDBRUD_D, BEROER_D], iid=[1, 2, 2, 2]))
    r = _zone(z, 1)
    assert (r["status"], r["slut_i"], r["signal"]) == ("beroert", 3, True)


# ---------------------------------------------------------------------------
# §3 Vinduet 08:30 ≤ t < 14:30 CT på lysets åbningstid, på en RTH-dag
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("dag", ["2023-01-11", "2023-06-14"])     # CST og CDT
@pytest.mark.parametrize("tid, i_vindue", [("08:15", False), ("08:30", True),
                                           ("14:15", True), ("14:30", False)])
def test_vinduet_er_0830_til_1430_ct(dag, tid, i_vindue):
    beroering = _ct(f"{dag} {tid}")
    r = _zone(_zoner(_barer([BASIS_D, UDBRUD_D, BEROER_D], beroering - 2 * KVARTER)), 0)
    assert (r["status"], r["slut_i"]) == ("beroert", 2)
    assert bool(r["i_vindue"]) is i_vindue
    assert bool(r["signal"]) is i_vindue


def test_vinduet_regnes_i_chicago_tid_paa_begge_sider_af_sommertiden():
    idx = pd.DatetimeIndex([
        "2023-01-11 14:15", "2023-01-11 14:30", "2023-01-11 20:15", "2023-01-11 20:30",
        "2023-06-14 13:15", "2023-06-14 13:30", "2023-06-14 19:15", "2023-06-14 19:30",
    ], tz="UTC")
    assert k1.vindue_mask(idx).tolist() == [False, True, True, False] * 2


@pytest.mark.parametrize("tid", ["2023-01-16 10:00",     # MLK Day: NQ handler, NYSE lukket
                                 "2023-06-19 10:00",     # Juneteenth
                                 "2023-06-11 18:00",     # søndag aften, Globex åben
                                 "2023-06-14 03:00"])    # natten
def test_uden_for_rth_er_ingen_signal(tid):
    assert not k1.vindue_mask(pd.DatetimeIndex([_ct(tid)]).tz_convert("UTC"))[0]


def test_beroering_paa_en_dag_uden_rth_bruger_zonen():
    tider = ["2023-01-16 09:00", "2023-01-16 09:15", "2023-01-16 09:30", "2023-01-17 09:30"]
    z = _zoner(_barer([BASIS_D, UDBRUD_D, BEROER_D, BEROER_D], tider_ct=tider))
    r = _zone(z, 0)
    assert (r["status"], r["slut_i"], r["signal"]) == ("beroert", 2, False)
    assert not z["signal"].any()


# ---------------------------------------------------------------------------
# §3 Halve dage: vinduet slutter 30 minutter før RTH lukker
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("dag", ["2023-11-24", "2023-07-03"])     # NYSE lukker 12:00 CT
@pytest.mark.parametrize("tid, i_vindue", [("08:30", True), ("11:15", True),
                                           ("11:30", False), ("11:45", False),
                                           ("12:00", False)])
def test_halve_dage_vinduet_slutter_1130_ct(dag, tid, i_vindue):
    beroering = _ct(f"{dag} {tid}")
    r = _zone(_zoner(_barer([BASIS_D, UDBRUD_D, BEROER_D], beroering - 2 * KVARTER)), 0)
    assert bool(r["signal"]) is i_vindue


def test_paa_en_almindelig_dag_er_1130_i_vinduet():
    assert k1.vindue_mask(pd.DatetimeIndex([_ct("2023-11-22 11:30")]).tz_convert("UTC"))[0]


# ---------------------------------------------------------------------------
# §3 Stoploftet: zonehøjde ≤ 0,429% af basislysets close
# ---------------------------------------------------------------------------

def _stop_scenarie(basis_low: float) -> pd.DataFrame:
    basis = (25_050, 25_080, basis_low, 25_000)
    udbrud = (25_000, 25_095, 25_000, 25_090)
    beroer = (25_085, 25_090, 25_079, 25_085)
    return _zoner(_barer([basis, udbrud, beroer]))


def test_stoploftet_er_inklusive_0429_pct():
    """107,25 point ved close 25.000 er præcis 0,429%, i hele tick."""
    r = _zone(_stop_scenarie(24_972.75), 0)
    assert r["hoejde_pct"] == pytest.approx(0.429)
    assert r["under_stoploft"] and r["i_vindue"] and r["signal"]


def test_et_tick_over_stoploftet_er_ikke_et_signal_og_taelles_som_afvist():
    z = _stop_scenarie(24_972.50)                  # 107,50 point = 0,43%
    r = _zone(z, 0)
    assert r["i_vindue"] and not r["under_stoploft"] and not r["signal"]
    row = k1.noegletal(z, k1.rth_dage(DAG, "2023-06-15"))
    assert (row["afvist_af_stoploft_n"], row["beroeringer_i_vindue_n"]) == (1, 1)
    assert row["signaler_n"] == 0


def test_stoploftet_maales_mod_basislysets_close():
    """Samme 107,50 point, men ved close 25.100 i basislyset, er under loftet."""
    basis = (25_150, 25_180, 25_072.50, 25_100)    # 107,50 point ved close 25.100 = 0,4283%
    udbrud = (25_100, 25_195, 25_100, 25_190)
    beroer = (25_185, 25_190, 25_179, 25_185)
    r = _zone(_zoner(_barer([basis, udbrud, beroer])), 0)
    assert r["under_stoploft"] and r["signal"]


# ---------------------------------------------------------------------------
# Sizing, §4
# ---------------------------------------------------------------------------

def test_sizing_foelger_formlerne():
    pt, kontrakter, omk = k1.sizing([0.2, 125 / 29_138 * 100, 62.5 / 29_138 * 100, 0.429])
    assert pt == pytest.approx([58.276, 125.0, 62.5, 0.429 / 100 * 29_138])
    # 0,429% er 125,002 point, så formlen giver 0 kontrakter. Tillægget: brugt som skrevet.
    assert kontrakter.tolist() == [2, 1, 2, 0]
    assert omk[0] == pytest.approx(2.627 / (2 * 58.276))


def test_konstanterne_er_praeregistreringens():
    assert (k1.SYMBOL, k1.BAR_MIN, k1.STOPLOFT_PCT, k1.NQ_NIVEAU) == ("NQ.v.0", 15, 0.429, 29_138)
    assert (k1.RISIKO_USD, k1.MNQ_USD_PR_POINT, k1.RR) == (250, 2, 2)
    assert k1.VINDUE_CT == (8 * 60 + 30, 14 * 60 + 30)
    assert k1.LUK_MARGIN == pd.Timedelta(minutes=30)
    assert 125 / 29_138 * 100 == pytest.approx(k1.STOPLOFT_PCT, abs=5e-4)


def test_omkostningen_er_fase_2s_rundtur_fra_konfigurationen():
    from research.atr_fordeling import omk_usd_rundtur

    assert k1.OMK_USD_RUNDTUR == pytest.approx(omk_usd_rundtur(), abs=5e-4)


# ---------------------------------------------------------------------------
# Tillæggets implementeringsdetaljer
# ---------------------------------------------------------------------------

def test_nabolys_over_et_hul_i_tid_er_stadig_basis_og_udbrud():
    """Fredag 15:45 CT og søndag 17:00 CT er naboer i serien."""
    tider = ["2023-06-09 15:45", "2023-06-11 17:00", "2023-06-12 09:00"]
    r = _zone(_zoner(_barer([BASIS_D, UDBRUD_D, BEROER_D], tider_ct=tider)), 0)
    assert r["over_hul"] and r["signal"]
    assert not _zone(_zoner(_barer([BASIS_D, UDBRUD_D, BEROER_D])), 0)["over_hul"]


def test_zonealder_fra_udbrudslysets_lukning_til_beroeringslysets_aabning():
    tider = [f"{DAG} 09:00", f"{DAG} 09:15", f"{DAG} 09:30", f"{DAG} 11:30"]
    r = _zone(_zoner(_barer([BASIS_D, UDBRUD_D, OVER, BEROER_D], tider_ct=tider)), 0)
    assert r["zonealder_timer"] == pytest.approx(2.0)


@pytest.mark.parametrize("udbrud_ct, i_rth", [("08:15", False), ("08:30", True),
                                              ("03:00", False), ("14:45", True)])
def test_dannet_afgoeres_af_udbrudslyset_og_zonen_maa_vaere_dannet_naar_som_helst(udbrud_ct, i_rth):
    udbrud = _ct(f"{DAG} {udbrud_ct}")
    beroering = _ct(f"{DAG} 14:15") if udbrud_ct != "14:45" else _ct("2023-06-15 08:30")
    r = _zone(_zoner(_barer([BASIS_D, UDBRUD_D, BEROER_D],
                            tider_ct=[udbrud - KVARTER, udbrud, beroering])), 0)
    assert bool(r["dannet_i_rth"]) is i_rth
    assert r["signal"]


def test_en_zone_der_aldrig_beroeres_er_aaben_og_censureret():
    z = _zoner(_barer([BASIS_D, UDBRUD_D, OVER, OVER]))
    r = _zone(z, 0)
    assert (r["status"], r["slut_i"], r["signal"]) == ("aaben", -1, False)
    assert pd.isna(r["slut_tid"]) and pd.isna(r["dag"]) and pd.isna(r["zonealder_timer"])


def test_rth_dagene_in_sample_er_2012():
    d = k1.rth_dage(holdout.IN_SAMPLE_START, holdout.HOLDOUT_START)
    assert len(d) == 2012
    assert (d[0], d[-1]) == (pd.Timestamp("2016-01-04"), pd.Timestamp("2023-12-29"))
    assert pd.Series(d.year).value_counts().sort_index().to_dict() == {
        2016: 252, 2017: 251, 2018: 251, 2019: 252, 2020: 253, 2021: 252, 2022: 251, 2023: 250}


def test_signaler_pr_dag_er_fordelingen_over_alle_rth_dage_ogsaa_dem_uden_signal():
    dage = k1.rth_dage(DAG, "2023-06-22")            # 14., 15., 16., 20. og 21. juni
    assert len(dage) == 5
    signaler = pd.Series(pd.to_datetime([DAG, DAG, "2023-06-15"]))
    row = k1.dagtal(signaler, dage)
    assert (row["signaler_n"], row["dage_med_signal_n"], row["RTH_dage_n"]) == (3, 2, 5)
    assert row["dage_med_signal_pct"] == pytest.approx(40.0)
    # [2, 1, 0, 0, 0] → p50 0 og p90 1,6. Uden nuldagene ville p50 være 1,5.
    assert (row["signaler_pr_dag_p50"], row["signaler_pr_dag_p90"]) == pytest.approx((0.0, 1.6))


def test_signaler_uden_for_rth_dagene_er_en_fejl():
    with pytest.raises(ValueError):
        k1.dagtal(pd.Series([pd.Timestamp("2023-06-15")]), k1.rth_dage(DAG, "2023-06-15"))


def _blandet() -> pd.DataFrame:
    """Seks zoner, hver i sin serie. noegletal læser kun zonetabellen, så de kan samles."""
    d15 = "2023-06-15"
    scenarier = [
        # A: demand-signal 14. juni, dannet i RTH, alder 0
        _barer([BASIS_D, UDBRUD_D, BEROER_D]),
        # B: berørt 03:00 CT 15. juni, uden for vinduet
        _barer([BASIS_D, UDBRUD_D, BEROER_D], tider_ct=[f"{d15} 02:30", f"{d15} 02:45",
                                                       f"{d15} 03:00"]),
        # C: berørt i vinduet 15. juni, afvist af stoploftet (0,43%)
        _barer([(25_050, 25_080, 24_972.50, 25_000), (25_000, 25_095, 25_000, 25_090),
                (25_085, 25_090, 25_079, 25_085)], f"{d15} 09:00"),
        # D: aldrig berørt, åben ved seriens slut
        _barer([BASIS_D, UDBRUD_D, OVER]),
        # E: død ved kontraktskift
        _barer([BASIS_D, UDBRUD_D, OVER, BEROER_D], iid=[1, 1, 1, 2]),
        # F: supply-signal 15. juni 08:30, dannet om natten, alder 6 timer
        _barer([BASIS_S, UDBRUD_S, BEROER_S], tider_ct=[f"{d15} 02:00", f"{d15} 02:15",
                                                       f"{d15} 08:30"]),
    ]
    return pd.concat([_zoner(b) for b in scenarier], ignore_index=True)


def test_noegletallene_og_deres_naevnere():
    z = _blandet()
    dage = k1.rth_dage(DAG, "2023-06-17")            # 14., 15. og 16. juni
    row = k1.noegletal(z, dage)
    assert (row["RTH_dage_n"], row["signaler_n"], row["dage_med_signal_n"]) == (3, 2, 2)
    assert row["dage_med_signal_pct"] == pytest.approx(200 / 3)
    lo, hi = wilson_interval(2, 3)
    assert (row["dage_med_signal_ci95_lo_pct"], row["dage_med_signal_ci95_hi_pct"]) == \
        pytest.approx((100 * lo, 100 * hi))
    assert row["dage_med_signal_ci95_lo_n"] == pytest.approx(3 * lo)
    assert (row["signaler_pr_dag_p50"], row["signaler_pr_dag_p90"]) == (1.0, 1.0)
    # Zonernes forløb: seks dannet, fire berørt, én død ved skift, én åben.
    assert (row["zoner_dannet_n"], row["zoner_beroert_n"]) == (6, 4)
    assert (row["zoner_doede_ved_kontraktskift_n"], row["zoner_aldrig_beroert_n"]) == (1, 1)
    assert row["zoner_aldrig_beroert_pct"] == pytest.approx(100 / 6)
    assert row["zoner_doede_ved_kontraktskift_pct"] == pytest.approx(100 / 6)
    # Berøringer: B uden for vinduet af fire; C afvist af tre i vinduet.
    assert (row["beroeringer_uden_for_vindue_n"], row["beroeringer_n"]) == (1, 4)
    assert row["beroeringer_uden_for_vindue_pct"] == pytest.approx(25.0)
    lo, hi = wilson_interval(1, 4)
    assert (row["beroeringer_uden_for_vindue_ci95_lo_pct"],
            row["beroeringer_uden_for_vindue_ci95_hi_pct"]) == pytest.approx((100 * lo, 100 * hi))
    assert (row["afvist_af_stoploft_n"], row["beroeringer_i_vindue_n"]) == (1, 3)
    assert row["afvist_af_stoploft_pct"] == pytest.approx(100 / 3)
    # Kun signaler: A og F, begge 0,2%.
    for q in (10, 50, 90):
        assert row[f"zonehoejde_pt_p{q}"] == pytest.approx(58.276)
        assert row[f"kontrakter_p{q}"] == 2
        assert row[f"omk_R_netto_p{q}"] == pytest.approx(2.627 / 116.552)
    assert row["omk_R_brutto"] == 0
    assert row["be_WR_pct_brutto"] == pytest.approx(100 / 3)
    assert row["be_WR_pct_netto_p50"] == pytest.approx((1 + 2.627 / 116.552) / 3 * 100)
    assert (row["zonealder_timer_p50"], row["zonealder_timer_p90"]) == \
        pytest.approx((3.0, 5.4))
    assert (row["dannet_uden_for_RTH_n"], row["dannet_uden_for_RTH_pct"]) == (1, 50.0)


def test_tabellen_har_hver_side_og_hvert_aar():
    tab = k1.tabel(_blandet(), k1.rth_dage(DAG, "2023-06-17"))
    hele = tab[tab["periode"] == "2023-2023"].set_index("side")
    assert hele.loc["alle", "signaler_n"] == 2
    assert (hele.loc["demand", "signaler_n"], hele.loc["supply", "signaler_n"]) == (1, 1)
    assert (hele.loc["demand", "zoner_dannet_n"], hele.loc["supply", "zoner_dannet_n"]) == (5, 1)
    aar = tab[tab["periode"] == "2023"].set_index("side")
    assert aar.loc["alle", "dage_med_signal_n"] == 2 and aar.loc["alle", "RTH_dage_n"] == 3


@pytest.mark.parametrize("lo, hi, kategori, uafgjort", [
    (600, 700, "≥ 590", False), (590, 600, "≥ 590", False), (580, 600, "390-589", True),
    (400, 500, "390-589", False), (380, 400, "< 390", True), (380, 600, "< 390", True),
    (100, 200, "< 390", False)])
def test_beslutningsreglen_den_laveste_kategori_gaelder(lo, hi, kategori, uafgjort):
    tekst, u = k1.beslutning({"dage_med_signal_ci95_lo_n": lo, "dage_med_signal_ci95_hi_n": hi})
    assert tekst.startswith(kategori) and u is uafgjort


# ---------------------------------------------------------------------------
# Fra 1m, og datavejen
# ---------------------------------------------------------------------------

def _fra_15m(lys15, start_ct) -> pd.DataFrame:
    """Femten 1m-lys pr. 15m-lys: åbner i open, lukker i close, når high og low undervejs."""
    rows = []
    for o, h, l, c in lys15:
        sti = np.linspace(o, c, 15)
        for i, p in enumerate(sti):
            rows.append((p, h if i == 5 else p, l if i == 10 else p, p))
    a = np.asarray(rows)
    idx = pd.date_range(_ct(start_ct), periods=len(a), freq="1min").tz_convert("UTC")
    return pd.DataFrame({"open": a[:, 0], "high": a[:, 1], "low": a[:, 2], "close": a[:, 3],
                         "volume": 1.0, "instrument_id": np.int64(1)}, index=idx.rename("time"))


def test_optaellingen_gaar_fra_1m_gennem_15m_aggregeringen():
    bars, z = k1.optaelling(_fra_15m([BASIS_D, UDBRUD_D, BEROER_D], f"{DAG} 09:00"))
    assert len(bars) == 3
    assert bars[["open", "high", "low", "close"]].to_numpy().tolist() == \
        [list(map(float, x)) for x in (BASIS_D, UDBRUD_D, BEROER_D)]
    r = _zone(z, 0)
    assert (r["side"], r["status"], r["signal"]) == ("demand", "beroert", True)


def test_pris_hentes_kun_gennem_load_in_sample():
    kilde = Path(k1.__file__).read_text(encoding="utf-8")
    assert "holdout.load_in_sample(" in kilde
    assert "load_holdout" not in kilde


def test_zonelisten_skrives_ikke_i_repoet():
    with pytest.raises(RuntimeError, match="repoet"):
        k1.main(["--zoner", str(k1.ROOT / "research" / "output" / "zoner.parquet")])


def test_main_fra_ende_til_anden_paa_syntetiske_data(monkeypatch, tmp_path):
    """Hele kørslen med datavejen og git skiftet ud, så rapportdelen ikke fejler første
    gang den møder rigtige data. Én demand-zone med signal 14. juni 2023."""
    df = _fra_15m([OVER, BASIS_D, UDBRUD_D, BEROER_D, OVER], f"{DAG} 08:45")
    kaldt = []
    monkeypatch.setattr(k1.holdout, "load_in_sample", lambda s: kaldt.append(s) or df)
    monkeypatch.setattr(k1, "committede", lambda stier: {k1._rel(s): "f" * 40 for s in stier})
    monkeypatch.setattr(k1, "_git", lambda *a: type("Svar", (), {"stdout": "e" * 40})())
    monkeypatch.setattr(k1, "OUT", tmp_path / "output")
    k1.main(["--zoner", str(tmp_path / "zoner.parquet")])

    assert kaldt == ["NQ.v.0"]
    md = (tmp_path / "output" / "b4_k1_optaelling.md").read_text(encoding="utf-8")
    assert "dage_med_signal_n = 1 af 2012" in md
    assert "| dage_med_signal_pct | 0,0 (0,0–0,3) |" in md
    assert "**< 390: for få handler — kandidaten parkeres**" in md
    for navn, _ in k1.RAEKKER:
        assert f"| {navn} |" in md
    tab = pd.read_csv(tmp_path / "output" / "b4_k1_optaelling.csv")
    assert len(tab) == 3 + 8 * 3
    assert tab.loc[(tab["periode"] == "2023") & (tab["side"] == "alle"),
                   "dage_med_signal_n"].item() == 1
    assert tab.loc[(tab["periode"] == "2016-2023") & (tab["side"] == "alle"),
                   "RTH_dage_n"].item() == 2012
    zoner = pd.read_parquet(tmp_path / "zoner.parquet")
    assert len(zoner) == 1 and bool(zoner["signal"].iloc[0])


def test_koerslen_kraever_committede_og_uaendrede_filer(monkeypatch):
    class Svar:
        def __init__(self, stdout="", returncode=0):
            self.stdout, self.returncode = stdout, returncode

    monkeypatch.setattr(k1, "_git", lambda *a: Svar("") if a[0] == "log" else Svar())
    with pytest.raises(RuntimeError, match="ikke committet"):
        k1.committede([k1.PREREG])
    monkeypatch.setattr(k1, "_git", lambda *a: Svar("abc123") if a[0] == "log" else Svar(returncode=1))
    with pytest.raises(RuntimeError, match="ændret"):
        k1.committede([k1.PREREG])


# ---------------------------------------------------------------------------
# Reference lys for lys, og intet efter berøringslyset
# ---------------------------------------------------------------------------

def _tilfaeldige_barer(n: int, seed: int) -> pd.DataFrame:
    """Tilfældig vandring i hele tick: huller i tid, dojier og fire kontraktblokke, hvoraf
    én kontrakt vender tilbage."""
    rng = np.random.default_rng(seed)
    trin = rng.choice([1] * 30 + [2, 4, 100], size=n)
    idx = pd.Timestamp("2023-03-01", tz="UTC") + pd.to_timedelta(np.cumsum(trin) * 15, unit="min")
    blok = np.searchsorted([n // 3, n // 2, 3 * n // 4], np.arange(n), side="right")
    iid = np.array([1, 2, 1, 3])[blok]
    close = 10_000 + np.cumsum(rng.normal(0, 6, n)) + np.array([0.0, 60.0, 0.0, 120.0])[blok]
    open_ = np.r_[close[0], close[:-1]] + rng.normal(0, 2, n)
    doji = rng.random(n) < 0.05
    open_[doji] = close[doji]
    tick = lambda x, f: f(np.asarray(x) * 4) / 4
    return pd.DataFrame({
        "open": tick(open_, np.round), "close": tick(close, np.round),
        "high": tick(np.maximum(open_, close) + rng.exponential(3, n), np.ceil),
        "low": tick(np.minimum(open_, close) - rng.exponential(3, n), np.floor),
        "volume": 1.0, "instrument_id": iid.astype(np.int64),
    }, index=pd.DatetimeIndex(idx, name="time"))


def _reference(bars: pd.DataFrame) -> list[tuple]:
    """Definitionerne lys for lys, uden genveje."""
    o, h, l, c = (bars[k].tolist() for k in ("open", "high", "low", "close"))
    iid = bars["instrument_id"].tolist()
    ud = []
    for b in range(len(bars) - 1):
        u = b + 1
        if c[b] < o[b] and c[u] > h[b]:
            side = "demand"
        elif c[b] > o[b] and c[u] < l[b]:
            side = "supply"
        else:
            continue
        status, slut = "aaben", -1
        for j in range(u, len(bars)):
            if iid[j] != iid[b]:
                status, slut = "kontraktskift", j
                break
            if j > u and (l[j] <= h[b] if side == "demand" else h[j] >= l[b]):
                status, slut = "beroert", j
                break
        ud.append((b, side, status, slut))
    return ud


@pytest.mark.parametrize("seed", [1, 2, 3, 4])
def test_find_zoner_er_lig_referencen_lys_for_lys(seed):
    bars = _tilfaeldige_barer(1500, seed)
    z = k1.find_zoner(bars)
    faktisk = list(zip(z["basis_i"].tolist(), z["side"].tolist(), z["status"].tolist(),
                       z["slut_i"].tolist()))
    assert faktisk == _reference(bars)
    assert {"beroert", "kontraktskift"} <= set(z["status"]) and len(z) > 100


def test_referencen_daekker_alle_forloeb_og_tick_lighed():
    """Testen ovenfor er kun noget værd hvis de tilfældige serier rammer alle tilfælde."""
    status, lighed = set(), 0
    for seed in (1, 2, 3, 4):
        bars = _tilfaeldige_barer(1500, seed)
        z = k1.find_zoner(bars)
        status |= set(z["status"])
        b = z[(z["status"] == "beroert") & (z["side"] == "demand")]
        lighed += int((bars["low"].to_numpy()[b["slut_i"]] == b["zone_high"].to_numpy()).sum())
    assert status == {"beroert", "kontraktskift", "aaben"}
    assert lighed > 0


def test_intet_efter_beroeringslyset_indgaar():
    bars = _tilfaeldige_barer(800, seed=5)
    z = k1.find_zoner(bars)
    kandidater = z[z["slut_i"] > z["udbrud_i"]]
    for _, r in kandidater.sample(min(60, len(kandidater)), random_state=0).iterrows():
        kort = bars.iloc[: r["slut_i"] + 1].copy()
        # Af slutlyset beholdes kun den kant der afgør berøringen.
        kant = kort.iloc[-1]["low" if r["side"] == "demand" else "high"]
        kort.iloc[-1, [kort.columns.get_loc(k) for k in ("open", "high", "low", "close")]] = kant
        r2 = _zone(k1.find_zoner(kort), r["basis_i"])
        assert (r2["status"], r2["slut_i"], r2["zone_high"], r2["zone_low"]) == \
            (r["status"], r["slut_i"], r["zone_high"], r["zone_low"])
