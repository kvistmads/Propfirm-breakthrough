"""Tests for research/normal.py.

Normalfordelingen er håndskrevet fordi repoet ikke har scipy (se
requirements.txt). Den holdes derfor op mod referenceværdier beregnet i 50-60
decimalers præcision med mpmath og skrevet ind som konstanter — ikke mod en
anden implementering i samme miljø. Så testen består også på en maskine hvor
hverken scipy eller mpmath findes.

En fejl her ville ikke give en exception. Den ville give en lidt forkert
deflateret tærskel i multipletesting.py, og dermed en strategi der ser
troværdig ud uden at være det. Derfor er tolerancen sat til det dobbelte af
maskinpræcisionen og ikke løsere.
"""
from __future__ import annotations

import math

import pytest

from research.normal import norm

TOL = 1e-14

CDF_REFERENCE = [
    (-8.0, 6.22096057427178387e-16),
    (-5.0, 2.86651571879193912e-07),
    (-3.0, 1.34989803163009458e-03),
    (-1.959963984540054, 2.50000000000000153e-02),
    (-1.0, 1.58655253931457046e-01),
    (0.0, 5.00000000000000000e-01),
    (0.5, 6.91462461274013118e-01),
    (1.0, 8.41344746068542926e-01),
    (1.959963984540054, 9.74999999999999978e-01),
    (3.0, 9.98650101968369897e-01),
    (5.0, 9.99999713348428076e-01),
]

PPF_REFERENCE = [
    (1e-12, -7.03448382530113214e00),
    (1e-06, -4.75342430882289868e00),
    (0.001, -3.09023230616781364e00),
    (0.025, -1.95996398454005427e00),
    (0.05, -1.64485362695147264e00),
    (0.1, -1.28155156554460037e00),
    (0.25, -6.74489750196081705e-01),
    (0.5, 0.0),
    (0.75, 6.74489750196081705e-01),
    (0.9, 1.28155156554460037e00),
    (0.95, 1.64485362695147264e00),
    (0.975, 1.95996398454005427e00),
    (0.999, 3.09023230616781364e00),
    (0.9999, 3.71901648545568042e00),
]


class TestCdf:
    @pytest.mark.parametrize("x,forventet", CDF_REFERENCE)
    def test_mod_reference(self, x, forventet):
        assert norm.cdf(x) == pytest.approx(forventet, rel=TOL, abs=1e-300)

    def test_halen_mister_ikke_cifre(self):
        """0.5*(1+erf(x/sqrt2)) ville give 0 her. erfc-formen giver ikke."""
        assert norm.cdf(-20.0) > 0.0
        assert norm.cdf(-20.0) == pytest.approx(2.753624e-89, rel=1e-6)

    def test_symmetri(self):
        for x in (0.3, 1.0, 2.5, 4.0, 7.0):
            assert norm.cdf(-x) + norm.cdf(x) == pytest.approx(1.0, abs=1e-15)

    def test_monotont(self):
        xs = [i / 100.0 for i in range(-800, 801)]
        vaerdier = [norm.cdf(x) for x in xs]
        assert all(a <= b for a, b in zip(vaerdier, vaerdier[1:]))

    def test_sf_er_cdf_spejlet(self):
        for x in (-3.0, 0.0, 1.5, 6.0):
            assert norm.sf(x) == pytest.approx(norm.cdf(-x), rel=1e-15)


class TestPpf:
    @pytest.mark.parametrize("p,forventet", PPF_REFERENCE)
    def test_mod_reference(self, p, forventet):
        assert norm.ppf(p) == pytest.approx(forventet, rel=TOL, abs=1e-15)

    def test_de_tre_grene_moedes_glat(self):
        """AS241 skifter formel ved |q|=0.425 og r=5. Ingen spring i sømmene."""
        for p in (0.075, 0.075 + 1e-12, 0.925 - 1e-12, 0.925):
            venstre = norm.ppf(p - 1e-9)
            hoejre = norm.ppf(p + 1e-9)
            assert abs(hoejre - venstre) < 1e-7

    def test_invers_af_cdf(self):
        for p in (1e-10, 0.01, 0.2, 0.5, 0.8, 0.99, 1 - 1e-10):
            assert norm.cdf(norm.ppf(p)) == pytest.approx(p, rel=1e-12)

    def test_randtilfaelde(self):
        assert norm.ppf(0.0) == -math.inf
        assert norm.ppf(1.0) == math.inf
        assert math.isnan(norm.ppf(-0.1))
        assert math.isnan(norm.ppf(1.1))


class TestBrugtAfMultipletesting:
    """De to kvantiler multipletesting.py faktisk slaar op, ved de N vi bruger.

    Referencevaerdier fra mpmath i 60 decimaler. Disse to tal ER
    deflationstaersklen — rammer de ved siden af, rammer hele B4's
    troevaerdighedsgraense ved siden af.
    """

    KVANTILER = [
        (3, 4.30727299295457500e-01, 1.16195692891273272e00),
        (10, 1.28155156554460037e00, 1.78924176458162831e00),
        (100, 2.32634787404084120e00, 2.68021044496688265e00),
        (1000, 3.09023230616781364e00, 3.37589539106181169e00),
        (10000, 3.71901648545568042e00, 3.96441587197223955e00),
    ]

    @pytest.mark.parametrize("n,forventet_a,forventet_b", KVANTILER)
    def test_kvantiler(self, n, forventet_a, forventet_b):
        assert norm.ppf(1.0 - 1.0 / n) == pytest.approx(forventet_a, rel=TOL)
        assert norm.ppf(1.0 - 1.0 / (n * math.e)) == pytest.approx(
            forventet_b, rel=TOL
        )
