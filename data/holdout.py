"""Forseglet holdout for B4 — in-sample 2016-01-01 til 2023-12-31, holdout fra 2024-01-01.

Besluttet 2026-09-22 (Mads): in-sample starter 2016-01-01, samme grundlag som ATR- og
sizing-tallene i fase 1. Holdout er alt fra 2024-01-01 og frem, og det åbnes **én gang**,
for en frosset hypotese.

Forseglingen er ikke en bøn om at lade være. Den er to spærringer i koden:

1. ``load_in_sample`` **åbner aldrig en holdout-fil.** Cachen er delt i kalenderår, og en fil
   der starter på eller efter grænsen bliver ikke læst — ikke bare filtreret bagefter.
2. ``load_holdout`` **kræver en frosset hypotese.** Filen skal findes, være committet, og
   arbejdskopien skal være identisk med den committede. Hver åbning skrives i
   ``research/output/holdout_log.md`` med tid, fil og commit.

Hvad forseglingen ikke dækker: fase 1 og 2 brugte 2016-2026 til ATR-fordelingen og
spreadet. Det var beskrivende målinger uden signaler eller udfald, så der er intet om
edgen at lække derfra. Reglen gælder signaler og resultater, ikke volatilitet.

Grænsen er 2024-01-01 00:00 UTC. Sidste in-sample-handelsdag er fredag 2023-12-29;
Globex genåbnede først mandag 2024-01-01 kl. 17:00 CT, så snittet falder i en lukket
periode og deler ingen handelsdag.

Al B4-kode skal hente pris gennem dette modul. ``tests/test_holdout.py`` fejler hvis en
``research/b4_*.py`` læser parquet direkte.
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from data.cache_parquet import CACHE_ROOT, ROOT, read_ohlcv

__all__ = [
    "IN_SAMPLE_START",
    "HOLDOUT_START",
    "HoldoutForseglet",
    "load_in_sample",
    "load_holdout",
]

IN_SAMPLE_START = pd.Timestamp("2016-01-01", tz="UTC")
HOLDOUT_START = pd.Timestamp("2024-01-01", tz="UTC")

_SERIE = ("databento", "GLBX.MDP3", "ohlcv-1m")
_LOG = ROOT / "research" / "output" / "holdout_log.md"


class HoldoutForseglet(PermissionError):
    """Holdout-perioden blev forsøgt åbnet uden en committet, frosset hypotese."""


def _filer(symbol: str, cache_root: Path) -> list[tuple[pd.Timestamp, pd.Timestamp, Path]]:
    mappe = Path(cache_root).joinpath(*_SERIE, symbol)
    ud = []
    for sti in sorted(mappe.glob("*.parquet")):
        start_txt, slut_txt = sti.stem.split("_", 1)
        ud.append((pd.Timestamp(start_txt, tz="UTC"), pd.Timestamp(slut_txt, tz="UTC"), sti))
    if not ud:
        raise FileNotFoundError(f"ingen cachefiler i {mappe}")
    return ud


def _saml(stier: list[Path]) -> pd.DataFrame:
    return pd.concat([read_ohlcv(s) for s in stier]).sort_index()


def load_in_sample(symbol: str = "NQ.v.0", cache_root: Path = CACHE_ROOT) -> pd.DataFrame:
    """1m-barer fra IN_SAMPLE_START til, men ikke med, HOLDOUT_START.

    Filer der starter på eller efter HOLDOUT_START åbnes ikke.
    """
    stier = [sti for start, slut, sti in _filer(symbol, cache_root)
             if slut > IN_SAMPLE_START and start < HOLDOUT_START]
    df = _saml(stier)
    df = df[(df.index >= IN_SAMPLE_START) & (df.index < HOLDOUT_START)]
    if len(df) and df.index.max() >= HOLDOUT_START:
        raise HoldoutForseglet("in-sample indeholder barer fra holdout-perioden")
    return df


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "--no-optional-locks", "-C", str(repo), *args],
                          capture_output=True, text=True)


def _committet_uaendret(frosset: Path, repo: Path) -> str:
    """Commit-hash for den frosne fil, hvis den er committet og uændret. Ellers fejl."""
    if not frosset.exists():
        raise HoldoutForseglet(f"den frosne hypotese findes ikke: {frosset}")
    rel = frosset.resolve().relative_to(repo.resolve()).as_posix()
    log = _git(repo, "log", "-1", "--format=%H", "--", rel)
    commit = log.stdout.strip()
    if log.returncode != 0 or not commit:
        raise HoldoutForseglet(f"{rel} er ikke committet. Commit den frosne hypotese først")
    diff = _git(repo, "diff", "--quiet", "HEAD", "--", rel)
    if diff.returncode != 0:
        raise HoldoutForseglet(f"{rel} er ændret siden commit {commit[:7]}")
    return commit


def load_holdout(frosset: Path, symbol: str = "NQ.v.0", cache_root: Path = CACHE_ROOT,
                 repo: Path = ROOT, log: Path = _LOG) -> pd.DataFrame:
    """1m-barer fra HOLDOUT_START og frem — kun for en committet, uændret hypotese.

    Hver åbning skrives i ``log``. Loggen er revisionssporet: står der mere end én linje
    pr. hypotese, er holdout brugt mere end én gang.
    """
    frosset = Path(frosset)
    commit = _committet_uaendret(frosset, Path(repo))
    stier = [sti for start, slut, sti in _filer(symbol, cache_root) if slut > HOLDOUT_START]
    df = _saml(stier)
    df = df[df.index >= HOLDOUT_START]

    log = Path(log)
    log.parent.mkdir(parents=True, exist_ok=True)
    ny = not log.exists()
    with log.open("a", encoding="utf-8") as f:
        if ny:
            f.write("# Holdout-log\n\nHver linje er én åbning af holdout-perioden.\n\n"
                    "| tid_utc | frosset_hypotese | commit | symbol |\n|---|---|---|---|\n")
        tid = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        rel = frosset.resolve().relative_to(Path(repo).resolve()).as_posix()
        f.write(f"| {tid} | {rel} | {commit[:12]} | {symbol} |\n")
    return df
