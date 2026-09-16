"""Import-røgtest: hvert modul i repoets pakker skal kunne indlæses.

Fase 1 viste at en grøn testsuite ikke kunne skelne "modulet virker" fra "modulet blev
aldrig indlæst": ``research/diagnostics.py`` og ``research/bias_engine.py`` trak
``research/daily_bias.py``, som ikke findes, og ingen test rørte dem. Denne test rører
alle.

Moduler der vides at være ikke-funktionelle står i ``IKKE_FUNKTIONELLE`` med
begrundelse og skippes. De er kopieret fra det gamle repo og slettes ikke uden at spørge.
"""
from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PAKKER = ("backtest", "data", "research", "strategies")

IKKE_FUNKTIONELLE = {
    "research.bias_engine": "importerer research.daily_bias, som ikke findes i repoet "
                            "(fase 1-efterskrift 1.4)",
    "research.diagnostics": "importerer research.daily_bias og research.bias_engine; "
                            "peger desuden på data/historical/*.csv, som ikke findes "
                            "(fase 1-efterskrift 1.4)",
}


def _moduler() -> list[str]:
    ud = []
    for pakke in PAKKER:
        ud.append(pakke)
        for m in pkgutil.walk_packages([str(ROOT / pakke)], prefix=f"{pakke}."):
            ud.append(m.name)
    return sorted(ud)


@pytest.mark.parametrize("modul", [
    pytest.param(m, marks=pytest.mark.skip(reason=f"ikke-funktionelt: {IKKE_FUNKTIONELLE[m]}"))
    if m in IKKE_FUNKTIONELLE else m
    for m in _moduler()
])
def test_modulet_kan_importeres(modul):
    importlib.import_module(modul)


def test_skiplisten_peger_paa_eksisterende_filer():
    """En skip på et modul der er flyttet eller slettet skjuler ingenting — den er død."""
    for modul in IKKE_FUNKTIONELLE:
        assert (ROOT / (modul.replace(".", "/") + ".py")).exists(), modul
