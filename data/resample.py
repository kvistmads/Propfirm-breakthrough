"""1m → 3m, 5m og 15m. Alle højere timeframes bygges af den SAMME 1m-serie.

Separate udtræk pr. timeframe kan have forskellige bar-grænser — det er den fejl der
formentlig gav 20% ATR-forskel mellem to guldkilder. Her deler timeframes grænser pr.
konstruktion: bins er venstrelukkede, mærket med binnens start og forankret i
UNIX-epoken (UTC). Dermed er hver 15m-grænse også en 5m- og en 3m-grænse, og 09:30 ET
(13:30/14:30 UTC) er en grænse for alle fire.

Tomme bins udelades — der udfyldes intet. ``n_1m`` tæller de 1m-barer en bar er bygget
af, så dækning også kan måles på den aggregerede serie.
"""
from __future__ import annotations

import pandas as pd

from data.ohlcv import validate_ohlcv

TIMEFRAMES = (1, 3, 5, 15)


def aggregate(df_1m: pd.DataFrame, minutes: int) -> pd.DataFrame:
    """Aggregér en valideret 1m-serie til ``minutes``-minutters barer."""
    validate_ohlcv(df_1m, "aggregate input")
    if minutes < 1 or 60 % minutes:
        # Kun divisorer af 60: så er epoke-forankring det samme som urforankring.
        raise ValueError(f"timeframe {minutes}m deler ikke timen")
    noegle = df_1m.index.floor(f"{minutes}min")
    g = df_1m.groupby(noegle, sort=True)
    ud = pd.DataFrame({
        "open": g["open"].first(),
        "high": g["high"].max(),
        "low": g["low"].min(),
        "close": g["close"].last(),
        "volume": g["volume"].sum(),
        "n_1m": g["open"].size(),
    })
    if "instrument_id" in df_1m.columns:
        blandet = g["instrument_id"].nunique() > 1
        if blandet.any():
            raise ValueError(f"{int(blandet.sum())} bins blander kontrakter — "
                             "rullen ligger ikke på en bar-grænse")
        ud["instrument_id"] = g["instrument_id"].first()
    ud.index.name = "time"
    return validate_ohlcv(ud, f"aggregate {minutes}m")
