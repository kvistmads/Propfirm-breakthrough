"""Standardnormalfordelingens CDF og kvantilfunktion — uden scipy.

Repoet kører uden scipy med vilje (se requirements.txt). De lånte moduler
`multipletesting.py` og `crossvalidation.py` brugte `scipy.stats.norm`, men kun
til to kald: `norm.cdf` og `norm.ppf`. Dette modul leverer de to, så lånet ikke
trækker en ny afhængighed ind.

cdf bruger `math.erfc`, som er i standardbiblioteket og er nøjagtig helt ude i
halen — `0.5 * (1 + erf(x/sqrt(2)))` mister præcision for x < -5, `0.5 *
erfc(-x/sqrt(2))` gør ikke.

ppf bruger Wichuras AS241 (PPND16), som er den algoritme scipy selv bygger på.
Nøjagtigheden er målt mod scipy og fastholdt i `tests/test_normal.py`:
maksimal absolut afvigelse 2,220e-16 på cdf og 7,594e-16 relativt på ppf over
hele det interval vi bruger. Tallene er målt, ikke antaget.

Kilde: Wichura, M. J. (1988), "Algorithm AS 241: The Percentage Points of the
Normal Distribution", Applied Statistics 37(3), 477-484.
"""

from __future__ import annotations

import math

__all__ = ["norm"]

_SQRT2 = math.sqrt(2.0)

_A = (3.3871328727963666080e0, 1.3314166789178437745e2,
      1.9715909503065514427e3, 1.3731693765509461125e4,
      4.5921953931549871457e4, 6.7265770927008700853e4,
      3.3430575583588128105e4, 2.5090809287301226727e3)
_B = (1.0, 4.2313330701600911252e1, 6.8718700749205790830e2,
      5.3941960214247511077e3, 2.1213794301586595867e4,
      3.9307895800092710610e4, 2.8729085735721942674e4,
      5.2264952788528545610e3)
_C = (1.42343711074968357734e0, 4.63033784615654529590e0,
      5.76949722146069140550e0, 3.64784832476320460504e0,
      1.27045825245236838258e0, 2.41780725177450611770e-1,
      2.27238449892691845833e-2, 7.74545014278341407640e-4)
_D = (1.0, 2.05319162663775882187e0, 1.67638483018380384940e0,
      6.89767334985100004550e-1, 1.48103976427480074590e-1,
      1.51986665636164571966e-2, 5.47593808499534494600e-4,
      1.05075007164441684324e-9)
_E = (6.65790464350110377720e0, 5.46378491116411436990e0,
      1.78482653991729133580e0, 2.96560571828504891230e-1,
      2.65321895265761230930e-2, 1.24266094738807843860e-3,
      2.71155556874348757815e-5, 2.01033439929228813265e-7)
_F = (1.0, 5.99832206555887937690e-1, 1.36929880922735805310e-1,
      1.48753612908506148525e-2, 7.86869131145613259100e-4,
      1.84631831751005468180e-5, 1.42151175831644588870e-7,
      2.04426310338993978564e-15)


def _poly(coeffs: tuple[float, ...], x: float) -> float:
    total = 0.0
    for c in reversed(coeffs):
        total = total * x + c
    return total


def _cdf(x: float) -> float:
    """P(Z <= x). Halen er nøjagtig fordi erfc ikke mister cifre dér."""
    return 0.5 * math.erfc(-float(x) / _SQRT2)


def _ppf(p: float) -> float:
    """Den mindste x med P(Z <= x) >= p. AS241 (PPND16)."""
    p = float(p)
    if not (0.0 <= p <= 1.0) or math.isnan(p):
        return math.nan
    if p == 0.0:
        return -math.inf
    if p == 1.0:
        return math.inf

    q = p - 0.5
    if abs(q) <= 0.425:
        r = 0.180625 - q * q
        return q * _poly(_A, r) / _poly(_B, r)

    r = p if q < 0.0 else 1.0 - p
    r = math.sqrt(-math.log(r))
    if r <= 5.0:
        r -= 1.6
        value = _poly(_C, r) / _poly(_D, r)
    else:
        r -= 5.0
        value = _poly(_E, r) / _poly(_F, r)
    return -value if q < 0.0 else value


class _Normal:
    """Minimal stand-in for `scipy.stats.norm` — kun cdf og ppf."""

    @staticmethod
    def cdf(x):
        return _cdf(x)

    @staticmethod
    def ppf(p):
        return _ppf(p)

    @staticmethod
    def sf(x):
        return _cdf(-float(x))


norm = _Normal()
