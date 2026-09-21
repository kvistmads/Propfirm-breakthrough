"""Forventet maksimal Sharpe blandt N rene støjstrategier — ved numerisk integration.

Tallet svarer på ét spørgsmål: hvor høj en Sharpe ville den bedste af N
strategier vise, hvis ingen af dem havde nogen edge overhovedet? Det er den
tærskel en observeret Sharpe skal slå for at betyde noget, og den vokser med
antallet af afprøvninger. Derfor skal tælleren rapporteres — se
`PRD_FASE3_B4_EDGE.md` §4.

Definitionen, og det denne fil regner:

    E[maks] = ∫ x · N · φ(x) · Φ(x)^(N-1) dx

hvor φ og Φ er standardnormalfordelingens tæthed og fordelingsfunktion.
Integranden er tætheden for maksimum af N uafhængige standardnormale.

**Numerisk integration af definitionen er den autoritative metode her.** Den
lukkede form hos Bailey og López de Prado,

    E[maks] ≈ (1 - g) · Z⁻¹(1 - 1/N) + g · Z⁻¹(1 - 1/(N·e)),   g = 0,5772…

er en approksimation, og den findes allerede i det lånte
`research/multipletesting.py` som `expected_maximum_sharpe`. Dens fejl er
hverken lille eller ensrettet på det interval vi bruger: −7,9% ved N = 2,
+0,77% ved N = 3, +2,5% ved N = 5, og derefter faldende til +0,24% ved
N = 10.000. Den topper altså midt i vores eget interval og skifter fortegn
under det. Den ældre `√(2 ln N)` er endnu ringere: kun rækkens førsteled, 75%
for høj ved N = 3 og 11% for høj ved N = 10.000, hvilket gav en deflationsfaktor
36% for mild.

Hvorfor integrere numerisk i stedet for at bruge den lukkede form: en
approksimation der er god nok til en tærskel er ikke nødvendigvis god nok til
et forhold mellem to tærskler, og forskellen er gratis at undgå. `multipletesting.py`
er lånt uændret og røres ikke — se `research/LAANTE_MODULER.md`. Denne fil er vores
egen, og den er den der gælder når de to er uenige.

Metoden er Simpsons regel på et fast interval, med intervalantallet fordoblet
indtil to på hinanden følgende værdier er enige til `tol`. Konvergensen er
altså målt ved kørslen, ikke antaget. Integrationsgrænserne ±12 er sat efter
halen: bidraget uden for dem er under 1e-30 for ethvert N vi kan tælle til.

Ingen scipy, ingen numpy. `math.erfc` via `research/normal.py`.
"""

from __future__ import annotations

import math

from research.normal import norm

__all__ = ["forventet_maks_sharpe", "deflationsfaktor"]

_SQRT_2PI = math.sqrt(2.0 * math.pi)

_GRAENSE_LAV = -12.0
_GRAENSE_HOEJ = 12.0

_INTERVALLER_START = 4096
_INTERVALLER_MAKS = 2 ** 21


def _integrand(x: float, n_forsoeg: int) -> float:
    """x · N · φ(x) · Φ(x)^(N-1), regnet så halen ikke mister cifre.

    Φ(x)^(N-1) skrives som exp((N-1)·log1p(-Φ(-x))). Den omvej er ikke pynt:
    for store N ligger massen dér hvor Φ(x) er tæt på 1, og `log(Φ(x))` mister
    netop dér de cifre der afgør resultatet.
    """
    hale = norm.sf(x)
    if hale >= 1.0:
        return 0.0
    taethed = math.exp(-0.5 * x * x) / _SQRT_2PI
    log_potens = (n_forsoeg - 1) * math.log1p(-hale)
    if log_potens < -745.0:
        return 0.0
    return x * n_forsoeg * taethed * math.exp(log_potens)


def _simpson(n_forsoeg: int, intervaller: int) -> float:
    h = (_GRAENSE_HOEJ - _GRAENSE_LAV) / intervaller
    total = _integrand(_GRAENSE_LAV, n_forsoeg) + _integrand(_GRAENSE_HOEJ, n_forsoeg)
    for i in range(1, intervaller):
        x = _GRAENSE_LAV + i * h
        vaegt = 4.0 if i % 2 else 2.0
        total += vaegt * _integrand(x, n_forsoeg)
    return total * h / 3.0


def forventet_maks_sharpe(
    n_forsoeg: int,
    sigma_sr: float = 1.0,
    tol: float = 1e-11,
) -> float:
    """Forventet maksimal Sharpe blandt `n_forsoeg` strategier uden edge.

    Args:
        n_forsoeg: antal afprøvede varianter. Tælleren, ikke antallet af
            varianter man endte med at kunne lide.
        sigma_sr: spredningen på Sharpe-estimatet på tværs af forsøgene.
            Resultatet er proportionalt med den, så sigma_sr = 1 giver tabellen
            i standardenheder.
        tol: relativ enighed mellem to på hinanden følgende gitre før
            integralet accepteres.

    Returns:
        Tærsklen i samme enhed som `sigma_sr`. Ved n_forsoeg = 1 er den 0.

    Raises:
        ValueError: hvis n_forsoeg < 1, sigma_sr < 0, eller integralet ikke
            konvergerer inden for gitterloftet.
    """
    if int(n_forsoeg) != n_forsoeg or n_forsoeg < 1:
        raise ValueError(f"n_forsoeg skal være et helt tal >= 1, fik {n_forsoeg!r}")
    if sigma_sr < 0.0 or math.isnan(sigma_sr):
        raise ValueError(f"sigma_sr skal være >= 0, fik {sigma_sr!r}")
    n_forsoeg = int(n_forsoeg)
    if n_forsoeg == 1:
        return 0.0

    intervaller = _INTERVALLER_START
    forrige = _simpson(n_forsoeg, intervaller)
    while intervaller < _INTERVALLER_MAKS:
        intervaller *= 2
        naevaerende = _simpson(n_forsoeg, intervaller)
        if abs(naevaerende - forrige) <= tol * max(1.0, abs(naevaerende)):
            return sigma_sr * naevaerende
        forrige = naevaerende
    raise ValueError(
        f"integralet konvergerede ikke til {tol} ved {_INTERVALLER_MAKS} intervaller "
        f"for n_forsoeg={n_forsoeg}"
    )


def deflationsfaktor(n_forsoeg: int, n_reference: int = 3) -> float:
    """Hvor meget højere tærsklen ligger ved `n_forsoeg` end ved `n_reference`.

    Forholdet er uafhængigt af sigma_sr, fordi den går ud med sig selv.
    Referencen er 3 fordi PRD'ens plan er tre til fem præregistrerede
    hypoteser; skifter planen, skifter referencen.
    """
    naevner = forventet_maks_sharpe(n_reference)
    if naevner <= 0.0:
        raise ValueError(f"n_reference skal give en tærskel > 0, fik {n_reference!r}")
    return forventet_maks_sharpe(n_forsoeg) / naevner


if __name__ == "__main__":
    print(f"{'N':>8}  {'E[maks Sharpe]':>15}  {'faktor mod N=3':>15}")
    for n in (3, 10, 100, 1000, 10000):
        print(f"{n:>8}  {forventet_maks_sharpe(n):>15.3f}  {deflationsfaktor(n):>14.3f}x")
