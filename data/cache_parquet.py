"""Parquet-cache: arkivet hentes én gang, ikke ved hver kørsel.

Validering sker FØR skrivning — et defekt svar caches aldrig — og igen ved læsning, så
en beskadiget fil ikke glider igennem. Skrivning går via en ``.part``-fil og
``os.replace``, så en afbrudt kørsel ikke efterlader noget der ligner en gyldig cache.

Cachen ligger i ``data/cache/`` og er git-ignoreret. Hverken Databento- eller
Yahoo-data må videredistribueres, og et pushet repo er videredistribution.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

import pandas as pd

from data.ohlcv import validate_ohlcv

ROOT = Path(__file__).resolve().parent.parent
CACHE_ROOT = ROOT / "data" / "cache"


def write_parquet(df: pd.DataFrame, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    df.to_parquet(tmp)
    os.replace(tmp, path)
    return path


def read_ohlcv(path: Path) -> pd.DataFrame:
    path = Path(path)
    return validate_ohlcv(pd.read_parquet(path), f"cache {path.name}")


def cached_ohlcv(path: Path, fetch: Callable[[], pd.DataFrame],
                 source: str = "") -> pd.DataFrame:
    """Læs fra cache hvis filen findes; ellers hent, validér og skriv."""
    path = Path(path)
    if path.exists():
        return read_ohlcv(path)
    df = validate_ohlcv(fetch(), source)
    write_parquet(df, path)
    return df
