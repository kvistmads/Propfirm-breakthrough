"""Tests for research/maks_sharpe.py.

Formålet med filen er at tallene i `PRD_FASE3_B4_EDGE.md` §4 kan genskabes, og
at de bliver ved med at kunne det. Derfor holdes integralet op mod
referenceværdier beregnet i 50 decimalers præcision med mpmath og skrevet ind
som konstanter — ikke mod en anden implementering i samme miljø. Testen består
altså også på en maskine uden scipy og uden mpmath.

To af værdierne kan efterprøves i hånden og gør det muligt at se at referencen
ikke selv er forkert: N = 1 giver 0, og N = 2 giver 1/√π, som er den lukkede
form for forventet maksimum af to standardnormale.

En fejl her ville ikke give en exception. Den ville give en for mild tærskel
for hvor stor en observeret Sharpe skal være efter N afprøvninger — altså
præcis den fejl hele §4 findes for at undgå.
"""

from __future__ import annotations

import math

import pytest

from research.maks_sharpe import deflationsfaktor, forventet_maks_sharpe
from research.multipletesting import expected_maximum_sharpe

TOL = 1e-10

REFERENCE = {
    2: 0.56418958354775629,
    3: 0.84628437532163443,
    5: 1.1629644736405196,
    10: 1.5387527308351729,
    50: 2.2490736293898503,
    100: 2.5075936364416844,
    500: 3.0366993459289314,
    1000: 3.2414357691334409,
    5000: 3.6775587907974878,
    10000: 3.8516158170666748,
    100000: 4.3843194031075881,
}

PRD_TABEL = {
    3: (0.846, 1.000),
    10: (1.539, 1.818),
    100: (2.508, 2.963),
    1000: (3.241, 3.830),
    10000: (3.852, 4.551),
}


@pytest.mark.parametrize("n_forsoeg,ventet", sorted(REFERENCE.items()))
def test_mod_mpmath_reference(n_forsoeg, ventet):
    assert forventet_maks_sharpe(n_forsoeg) == pytest.approx(ventet, abs=TOL)


def test_to_forsoeg_rammer_den_lukkede_form():
    assert forventet_maks_sharpe(2) == pytest.approx(1.0 / math.sqrt(math.pi), abs=TOL)


def test_et_forsoeg_er_nul():
    assert forventet_maks_sharpe(1) == 0.0


@pytest.mark.parametrize("n_forsoeg,ventet", sorted(PRD_TABEL.items()))
def test_prd_tabellens_vaerdier(n_forsoeg, ventet):
    vaerdi, faktor = ventet
    assert round(forventet_maks_sharpe(n_forsoeg), 3) == vaerdi
    assert round(deflationsfaktor(n_forsoeg), 3) == faktor


def test_tærsklen_vokser_med_antallet_af_forsoeg():
    n_liste = sorted(REFERENCE)
    vaerdier = [forventet_maks_sharpe(n) for n in n_liste]
    assert all(b > a for a, b in zip(vaerdier, vaerdier[1:]))


def test_proportional_med_sigma():
    enhed = forventet_maks_sharpe(100)
    assert forventet_maks_sharpe(100, sigma_sr=2.5) == pytest.approx(2.5 * enhed, abs=TOL)
    assert forventet_maks_sharpe(100, sigma_sr=0.0) == 0.0


def test_faktoren_er_uafhaengig_af_sigma():
    assert deflationsfaktor(10000) == pytest.approx(
        forventet_maks_sharpe(10000, sigma_sr=7.3) / forventet_maks_sharpe(3, sigma_sr=7.3),
        abs=TOL,
    )


def test_egen_reference_er_en():
    assert deflationsfaktor(3) == pytest.approx(1.0, abs=TOL)


@pytest.mark.parametrize("ugyldig", [0, -1, 2.5])
def test_ugyldigt_antal_forsoeg(ugyldig):
    with pytest.raises(ValueError):
        forventet_maks_sharpe(ugyldig)


def test_negativ_sigma():
    with pytest.raises(ValueError):
        forventet_maks_sharpe(100, sigma_sr=-1.0)


@pytest.mark.parametrize("n_forsoeg", [3, 10, 100, 1000, 10000])
def test_den_lukkede_form_ligger_hoejt_men_taet_paa(n_forsoeg):
    """Dokumenterer forskellen på det lånte modul og vores egen integration.

    Den lukkede form i `multipletesting.py` er en approksimation. På hele det
    interval PRD-tabellen dækker ligger den over definitionen, men under 3%
    over. Testen er ikke en påstand om at den er forkert at bruge; den
    fastholder hvor stor forskellen er, så ingen senere bytter den ene ud med
    den anden i troen på at de giver det samme.
    """
    lukket = expected_maximum_sharpe(n_forsoeg, 1.0)
    integreret = forventet_maks_sharpe(n_forsoeg)
    afvigelse = (lukket - integreret) / integreret
    assert 0.0 < afvigelse < 0.03


def test_den_lukkede_forms_afvigelse_har_en_pukkel():
    """Fejlen er ikke monoton i N, og den er ikke ensidig.

    Ved N = 2 ligger den lukkede form 7,9% for lavt; den topper omkring N = 5
    med 2,5% for højt og falder derefter monotont. Det er grunden til at
    definitionen integreres numerisk i stedet: en approksimation hvis fejl
    skifter fortegn og topper midt i vores eget interval er ikke et godt
    grundlag for et forhold mellem to tærskler.
    """

    def afvigelse(n):
        integreret = forventet_maks_sharpe(n)
        return (expected_maximum_sharpe(n, 1.0) - integreret) / integreret

    assert afvigelse(2) < 0.0
    assert afvigelse(5) > afvigelse(3) > 0.0
    assert afvigelse(10) > afvigelse(100) > afvigelse(1000) > afvigelse(10000) > 0.0


def test_den_gamle_kvadratrodsapproksimation_var_for_mild():
    """Fastholder hvorfor PRD-tabellen blev rettet.

    `√(2 ln N)` er kun rækkens førsteled. Den overvurderer den absolutte
    tærskel mest ved små N, og fordi nævneren i forholdet rammer mest ved
    siden af, bliver selve deflationsfaktoren for lille — altså for mild.
    """
    gammel_absolut = lambda n: math.sqrt(2.0 * math.log(n))

    assert gammel_absolut(3) / forventet_maks_sharpe(3) == pytest.approx(1.75, abs=0.01)
    assert gammel_absolut(10000) / forventet_maks_sharpe(10000) == pytest.approx(
        1.11, abs=0.01
    )

    gammelt_forhold = gammel_absolut(10000) / gammel_absolut(3)
    assert gammelt_forhold == pytest.approx(2.895, abs=0.001)
    assert gammelt_forhold / deflationsfaktor(10000) == pytest.approx(0.636, abs=0.002)
