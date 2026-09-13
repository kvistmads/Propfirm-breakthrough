"""Tests for research/mll_ruin.py — ruinmodel v2.

Det der låses fast er det K1 hviler på: fodres v2 med én konstant ATR, er den v1 — bortset
fra én bevidst forskel. For at parre stierne trækker v2 vinder/taber-uniformen i hver slot,
også når ingen sti handler i den. v1 sprang trækket over, så når få stier er tilbage, kan de
få andre træk. Referencetallene er kørt med v1-koden (commit 8c29938) før omskrivningen.
"""
from __future__ import annotations

import numpy as np
import pytest

from research import mll_ruin as m
from research.stats import proportion_diff_interval

# (kontrakter, stop_ATR, WR, pessimistisk, netto) -> v1's udfald ved 3.000 stier
V1_REFERENCE = {
    (1, 1.00, 0.40, False, True): (2618, 328, 54),
    (1, 1.00, 0.40, True, True): (2570, 382, 48),
    (2, 0.50, 0.37, True, False): (2083, 790, 127),
    (3, 0.75, 0.34, False, True): (728, 2272, 0),
}


@pytest.mark.parametrize("celle", list(V1_REFERENCE))
def test_konstant_atr_reproducerer_v1(celle):
    """Højst en håndfuld stier må afvige — dem der er tilbage når en slot er tom."""
    k, stop, wr, pess, netto = celle
    r = m.simulate(3000, wr, stop, k, pess, m.K1_OMK_USD if netto else 0.0,
                   m.K1_ATR_PCT, m.K1_NQ, m.seed_v1(k, stop, wr))
    for faktisk, v1 in zip((r["bestaaet"], r["ruin"], r["uafgjort"]), V1_REFERENCE[celle]):
        assert abs(faktisk - v1) <= 5


def test_atr_stroemmen_roerer_ikke_vinder_taber_stroemmen():
    """En 'fordeling' af ens værdier trækker fra ATR-strømmen, men giver samme udfald."""
    args = dict(n_paths=2000, wr=0.40, stop_atr=0.75, contracts=1, pessimistisk=True,
                omk_usd=2.627, nq=29_138.0, seed=m.SEED)
    a = m.simulate(atr_pct=0.2319, **args)
    b = m.simulate(atr_pct=np.full(5, 0.2319), **args)
    for noegle in ("bestaaet", "ruin", "uafgjort", "n_handler"):
        assert a[noegle] == b[noegle]
    assert (a["bestaaet_sti"] == b["bestaaet_sti"]).all()


def test_udfaldene_summerer_til_antal_stier():
    atr = np.array([0.10, 0.20, 0.40, 0.80])
    r = m.simulate(2000, 0.37, 1.0, 1, False, 2.627, atr, 29_138.0, m.SEED)
    assert r["bestaaet"] + r["ruin"] + r["uafgjort"] == 2000


def test_pessimistisk_ruin_er_mindst_den_optimistiske():
    atr = np.array([0.10, 0.20, 0.40, 0.80])
    kw = dict(n_paths=3000, wr=0.37, stop_atr=1.0, contracts=1, omk_usd=2.627,
              atr_pct=atr, nq=29_138.0, seed=m.SEED)
    assert (m.simulate(pessimistisk=True, **kw)["ruin"]
            >= m.simulate(pessimistisk=False, **kw)["ruin"])


def test_r_usd_ved_nutidigt_niveau():
    assert m.r_usd(0.2319, 29_138.0, 1.0) == pytest.approx(135.14, abs=0.01)
    assert m.r_usd(0.2319, 29_138.0, 0.5) == pytest.approx(135.14 / 2, abs=0.01)


def test_be_wr_giver_nul_forventet_pnl_med_trukket_R():
    rng = np.random.default_rng(1)
    R = m.r_usd(rng.lognormal(-1.5, 0.5, 200_000), 29_138.0, 1.0)
    c = 2.627
    wr = m.be_wr(c, R.mean())
    ev = wr * (2 * R - c).mean() - (1 - wr) * (R + c).mean()
    assert ev == pytest.approx(0.0, abs=1e-9)
    assert m.be_wr(0.0, 100.0) == pytest.approx(1 / 3)


def test_stierne_er_parrede_paa_tvaers_af_win_rate():
    """Samme seed og samme uniformer: højere WR kan kun give flere vindere pr. slot. Med en
    ren optimistisk konto uden omkostning og en høj WR-forskel består flere stier."""
    atr = np.array([0.10, 0.20, 0.40])
    kw = dict(n_paths=4000, stop_atr=0.5, contracts=1, pessimistisk=False, omk_usd=0.0,
              atr_pct=atr, nq=29_138.0, seed=m.SEED)
    lav = m.simulate(wr=0.36, **kw)
    hoej = m.simulate(wr=0.44, **kw)
    _, lo, hi = m.parret_diff_pp(hoej["bestaaet_sti"], lav["bestaaet_sti"])
    assert lo > 0
    ulo, uhi = proportion_diff_interval(hoej["bestaaet"], 4000, lav["bestaaet"], 4000)
    assert (hi - lo) < 100 * (uhi - ulo)


def test_nulmodellen_har_nul_forventet_pnl_i_simulationen():
    rng = np.random.default_rng(3)
    atr = np.sort(rng.lognormal(-1.5, 0.5, 5000))
    c, stop = 2.627, 0.75
    be = m.be_wr(c, float(m.r_usd(atr, 29_138.0, stop).mean()))
    for pess in (False, True):
        r = m.simulate(20_000, be, stop, 1, pess, c, atr, 29_138.0, m.SEED)
        lo, hi = r["pnl_middel_CI95"]
        assert lo <= 0 <= hi


def test_valgreglen_bruger_k3_som_filter_og_parret_uafgjort():
    def raekke(tf, stop, p90, sti):
        s = {("netto", "pess"): {"bestaaet_sti": sti}}
        return {"timeframe": tf, "stop_ATR": stop, "risiko_pct_af_MLL_netto_ved_ATR_p90": p90,
                "bestaa_pct_netto_pess": 100 * sti.mean(), "_stier": s}
    n = 2000
    base = np.zeros(n, dtype=bool)
    base[:1000] = True
    hoej = base.copy(); hoej[1000:1400] = True           # 70%, men p90 over 10
    midt = base.copy(); midt[1000:1100] = True           # 55%
    naesten = base.copy(); naesten[1000:1098] = True     # 54,9%, næsten samme stier
    rows = [raekke("15m", 1.0, 14.0, hoej), raekke("5m", 1.0, 8.0, midt),
            raekke("3m", 1.0, 6.0, naesten)]
    v = m.vaelg(rows)
    assert v["valgt"] is rows[1] and v["maks_uden_K3"] is rows[0]
    assert v["maks_diff"][1] > 0
    assert v["uafgjort"] and v["tiebreak"] and v["udpeget"] is rows[2]
