"""Tests for research/b4_edgekrav.py — præregistreringens §7.2, test 1-8.

Ingen kursdata. Alle træk har faste frø, så testene er deterministiske.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from research import b4_edgekrav as b
from research import mll_ruin
from research.stats import wilson_interval

R = b.Regler()
KS_1PCT = 1.628


def _ks_formel(M: np.ndarray, X: float, sigma: float) -> float:
    """Kolmogorov-Smirnov-afstanden mellem M og P(M ≤ m) = exp(−2m(m−X)/σ²)."""
    m = np.sort(M)
    F = np.exp(-2.0 * m * (m - X) / sigma ** 2)
    n = m.size
    i = np.arange(1, n + 1)
    return float(max((i / n - F).max(), (F - (i - 1) / n).max()))


def _random_walk_min(X: float, sigma: float, n: int, skridt: int, froe: int) -> np.ndarray:
    """Minimum af en finmasket random walk, tvunget til at ende i X (bridge-konstruktion).

    Diskret overvågning ligger ca. 0,58·σ/√skridt over det kontinuerte minimum. Ved 50.000
    skridt er det $0,78 ved σ = $300 — små nok til at KS ikke ser dem.
    """
    rng = np.random.default_rng(froe)
    t = np.arange(1, skridt + 1) / skridt
    ud = []
    for _ in range(n // 100):
        W = np.cumsum(rng.standard_normal((100, skridt)), axis=1) * sigma / math.sqrt(skridt)
        ud.append(np.minimum(0.0, (W - t * W[:, -1:] + t * X).min(axis=1)))
    return np.concatenate(ud)


def test_1_brownian_bridge_minimum():
    """KS mod formlen og mod en finmasket random walk, for tre dagsslut."""
    sigma, n = 300.0, 20_000
    rng = np.random.default_rng(1)
    for X in (-300.0, 0.0, 450.0):
        U = 1.0 - rng.random(n)
        M = b.bridge_minimum(np.full(n, X), sigma, U)
        assert (M <= min(0.0, X) + 1e-9).all()
        assert _ks_formel(M, X, sigma) < KS_1PCT / math.sqrt(n)

        n_rw = 2_000
        rw = _random_walk_min(X, sigma, n_rw, 50_000, froe=int(X) + 1000)
        assert _ks_formel(rw, X, sigma) < KS_1PCT / math.sqrt(n_rw)


def test_2_gamblers_ruin():
    """Uden edge, trailing, DLL og konsistens: +3.000 før −2.000 med p ≈ 2.000/5.000."""
    r0 = b.Regler(dll=None, konsistens=None, trailing=False)
    n = 20_000
    o = b.combine_alene(n, 60_000, b.brownian_dag(0.0, 40.0), r0, froe=2)
    assert o["uafgjort"] == 0
    p = o["bestaaet"] / n
    se = math.sqrt(0.4 * 0.6 / n)
    assert abs(p - 0.40) < 3 * se


def test_3_graensetilfaelde():
    stoej = b.traek_stoej(4_000, df=b.DF, froe=3)
    op = b.simuler_aar(20.0, 300.0, 300.0, stoej)
    ned = b.simuler_aar(-20.0, 300.0, 300.0, stoej)
    assert (op["foerste_bestaaet"] <= 252).mean() > 0.99
    assert (ned["foerste_bestaaet"] <= 252).mean() < 0.001
    assert ned["udbetalt"].sum() == 0.0


def test_4_combine_mll():
    a = np.array
    # Trailing på dagsslut, aldrig nedad.
    assert b.trail(a([-2000.0]), a([500.0]), R)[0] == -1500.0
    assert b.trail(a([-1500.0]), a([200.0]), R)[0] == -1500.0
    # Låser ved start (0), også når saldoen stiger videre.
    assert b.trail(a([-500.0]), a([2000.0]), R)[0] == 0.0
    assert b.trail(a([0.0]), a([2600.0]), R)[0] == 0.0

    # Brud i realtid: dagen ender i plus, men minimum rammer MLL.
    pnl, brud, dll = b.dagens_udfald(a([-1200.0]), a([-2000.0]), a([500.0]), a([-850.0]), R)
    assert brud[0] and not dll[0]
    # DLL før MLL: dagen flades på −1.000, intet brud.
    pnl, brud, dll = b.dagens_udfald(a([0.0]), a([-2000.0]), a([-1500.0]), a([-1200.0]), R)
    assert dll[0] and not brud[0] and pnl[0] == -1000.0
    # MLL før DLL: brud ved −500, selv om DLL ligger ved −1.000.
    pnl, brud, dll = b.dagens_udfald(a([-1500.0]), a([-2000.0]), a([-300.0]), a([-600.0]), R)
    assert brud[0] and not dll[0]
    # Lige langt: brud (læsning 2).
    pnl, brud, dll = b.dagens_udfald(a([-1000.0]), a([-2000.0]), a([-1000.0]), a([-1000.0]), R)
    assert brud[0]
    # Ingen hændelse: dagsslut uændret.
    pnl, brud, dll = b.dagens_udfald(a([0.0]), a([-2000.0]), a([-300.0]), a([-900.0]), R)
    assert not brud[0] and not dll[0] and pnl[0] == -300.0

    # Hele året: DLL dag 1 (−1.000), −200 dag 2, brud i realtid dag 3 trods +500 ved
    # dagsslut, reset til $0 og MLL −2.000 dag 4.
    X = a([[-1200.0, -200.0, 500.0, -900.0]])
    M = a([[-1200.0, -200.0, -850.0, -900.0]])
    res = b.simuler_aar(0.0, 1.0, 1.0, None, horisont=4, X_fast=X, M_fast=M)
    assert res["resets"][0] == 1
    assert res["slut_fase"][0] == b.COMBINE and res["slut_saldo"][0] == -900.0


def test_5_konsistens():
    a = np.array
    assert b.combine_maal(a([1650.0]), R)[0] == pytest.approx(3000.0)
    assert b.combine_maal(a([2000.0]), R)[0] == pytest.approx(2000.0 / 0.55)
    # 1.650 + 1.350: bestået dag 2. 2.000 + 1.500 = 3.500 < 3.636: ikke bestået.
    s, m, bd, d, ok = b.combine_dagsslut(a([1650.0]), a([-350.0]), a([1650.0]), a([1]),
                                         a([1350.0]), R)
    assert ok[0]
    s, m, bd, d, ok = b.combine_dagsslut(a([2000.0]), a([0.0]), a([2000.0]), a([1]),
                                         a([1500.0]), R)
    assert not ok[0]
    s, m, bd, d, ok = b.combine_dagsslut(s, m, bd, d, a([200.0]), R)
    assert ok[0]
    # Mindst 2 dage: én dag over målet består ikke uden konsistens.
    rk = b.Regler(konsistens=None)
    *_, ok = b.combine_dagsslut(a([0.0]), a([-2000.0]), a([0.0]), a([0]), a([3500.0]), rk)
    assert not ok[0]


def test_6_xfa():
    a = np.array
    # Vindende dage à $150: 149,99 tæller ikke, 150 gør.
    _, _, v, _ = b.xfa_dagsslut(a([0.0]), a([-2000.0]), a([0]), a([149.99]), R)
    assert v[0] == 0
    _, _, v, _ = b.xfa_dagsslut(a([0.0]), a([-2000.0]), a([0]), a([150.0]), R)
    assert v[0] == 1
    # 50% af saldoen, loft $4.000, minimum $125.
    s, m, v, ud = b.xfa_dagsslut(a([9850.0]), a([0.0]), a([4]), a([150.0]), R)
    assert ud[0] == 4000.0 and s[0] == 6000.0
    s, m, v, ud = b.xfa_dagsslut(a([1000.0]), a([-1000.0]), a([4]), a([200.0]), R)
    assert ud[0] == 600.0 and s[0] == 600.0
    # MLL til $0 og ny tæller efter udbetaling.
    assert m[0] == 0.0 and v[0] == 0
    # Under minimum: ingen udbetaling, tælleren beholdes.
    s, m, v, ud = b.xfa_dagsslut(a([50.0]), a([-2000.0]), a([4]), a([150.0]), R)
    assert ud[0] == 0.0 and v[0] == 5 and s[0] == 200.0
    s, m, v, ud = b.xfa_dagsslut(s, m, v, a([60.0]), R)
    assert ud[0] == 130.0 and v[0] == 0
    # Loftet uden DLL er $2.000.
    _, _, _, ud = b.xfa_dagsslut(a([9850.0]), a([0.0]), a([4]), a([150.0]), b.regler_uden_dll())
    assert ud[0] == 2000.0
    # Låsning ved $0.
    _, m, _, _ = b.xfa_dagsslut(a([1900.0]), a([-500.0]), a([0]), a([100.0]), R)
    assert m[0] == 0.0
    _, m, _, _ = b.xfa_dagsslut(a([2000.0]), a([0.0]), a([0]), a([900.0]), R)
    assert m[0] == 0.0

    # Permanent lukning: bestået dag 2, udbetaling dag 7, brud dag 8, nyt Combine dag 9.
    X = a([[1600.0, 1500.0] + [200.0] * 5 + [-600.0, 0.0, 0.0]])
    M = np.minimum(0.0, X)
    res = b.simuler_aar(0.0, 1.0, 1.0, None, horisont=10, X_fast=X, M_fast=M)
    assert res["foerste_bestaaet"][0] == 2
    assert res["foerste_udbetaling"][0] == 7
    assert res["udbetalt"][0] == 500.0
    assert res["lukninger"][0] == 1
    assert res["slut_fase"][0] == b.COMBINE
    assert res["n_bestaaet"][0] == 1


def test_7_gebyrer():
    assert [b.abonnement_blokke(d) for d in (1, 21, 22, 42, 43)] == [1, 1, 2, 2, 3]
    assert b.api_gebyr(252) == pytest.approx(12 * 14.50)

    # 43 Combine-dage, DLL dag 9 og brud dag 10: abonnement dag 1, 22, 43; ét reset;
    # API 3 blokke.
    X = np.zeros((1, 43))
    X[0, 8], X[0, 9] = -1000.0, -1100.0
    res = b.simuler_aar(0.0, 1.0, 1.0, None, horisont=43, X_fast=X, M_fast=np.minimum(0.0, X))
    assert res["resets"][0] == 1
    assert res["gebyr"][0] == pytest.approx(3 * 49 + 49 + 3 * 14.50)

    # Bestået dag 2, XFA lukket dag 8, nyt forløb dag 9: 49 + 149 + 49 + API 14,50.
    X = np.array([[1600.0, 1500.0] + [200.0] * 5 + [-600.0, 0.0, 0.0]])
    res = b.simuler_aar(0.0, 1.0, 1.0, None, horisont=10, X_fast=X, M_fast=np.minimum(0.0, X))
    assert res["gebyr"][0] == pytest.approx(49 + 149 + 49 + 14.50)
    assert res["netto"][0] == pytest.approx(0.9 * 500 - (49 + 149 + 49 + 14.50))

    # $95-planen uden aktivering.
    res = b.simuler_aar(0.0, 1.0, 1.0, None, r=b.regler_95(), horisont=10, X_fast=X,
                        M_fast=np.minimum(0.0, X))
    assert res["gebyr"][0] == pytest.approx(95 + 95 + 14.50)


@pytest.mark.parametrize("wr", [0.40, 0.34])
def test_8_krydstjek_mll_ruin(wr):
    """Diskret 2:1 med konstant R = $300: inden for mll_ruin's Wilson-interval.

    R = 0,5% × 30.000 × 2 × 1,0 stop. Tre tab á $301,22 er $903,66, så DLL binder aldrig
    i nogen af modellerne. mll_ruin kører optimistisk brud med 1-3 handler om dagen.
    """
    atr_pct, nq, stop, omk, dage = 0.5, 30_000.0, 1.0, 1.22, 200
    R_usd = mll_ruin.r_usd(atr_pct, nq, stop)
    assert R_usd == pytest.approx(300.0)
    ref = mll_ruin.simulate(20_000, wr, stop, 1, False, omk, atr_pct, nq, mll_ruin.SEED,
                            konsistens=0.55, max_days=dage)
    lo, hi = wilson_interval(ref["bestaaet"], ref["n"])
    o = b.combine_alene(100_000, dage, b.diskret_2til1_dag(wr, R_usd, omk), R, froe=8)
    assert lo <= o["bestaaet"] / o["n"] <= hi
