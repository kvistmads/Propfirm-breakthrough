"""Tests for research/mll_ruin.py — ruinmodel v2.

Det der låses fast er det K1 hviler på: fodres v2 med én konstant ATR, er den v1 træk for
træk. Referencetallene nedenfor er kørt med v1-koden (commit 8c29938) før omskrivningen.
"""
from __future__ import annotations

import numpy as np
import pytest

from research import mll_ruin as m

# (kontrakter, stop_ATR, WR, pessimistisk, netto) -> v1's udfald ved 3.000 stier
V1_REFERENCE = {
    (1, 1.00, 0.40, False, True): (2618, 328, 54),
    (1, 1.00, 0.40, True, True): (2570, 382, 48),
    (2, 0.50, 0.37, True, False): (2083, 790, 127),
    (3, 0.75, 0.34, False, True): (728, 2272, 0),
}


@pytest.mark.parametrize("celle", list(V1_REFERENCE))
def test_konstant_atr_reproducerer_v1_traek_for_traek(celle):
    k, stop, wr, pess, netto = celle
    r = m.simulate(3000, wr, stop, k, pess, m.K1_OMK_USD if netto else 0.0,
                   m.K1_ATR_PCT, m.K1_NQ, m.seed_v1(k, stop, wr))
    assert (r["bestaaet"], r["ruin"], r["uafgjort"]) == V1_REFERENCE[celle]


def test_atr_stroemmen_roerer_ikke_vinder_taber_stroemmen():
    """En 'fordeling' af ens værdier trækker fra ATR-strømmen, men giver samme udfald."""
    args = dict(n_paths=2000, wr=0.40, stop_atr=0.75, contracts=1, pessimistisk=True,
                omk_usd=2.627, nq=29_138.0, seed=m.SEED)
    a = m.simulate(atr_pct=0.2319, **args)
    b = m.simulate(atr_pct=np.full(5, 0.2319), **args)
    assert a == b


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
