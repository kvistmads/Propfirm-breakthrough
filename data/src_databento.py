"""Databento GLBX.MDP3 — primærkilde i fase 1. CME's egen Globex-feed.

Betingelser fra Mads (2026-09-11), håndhævet her:

1. **Maks $40 af den gratis kredit i fase 1** — hævet fra $25 samme dag, så spread kan
   måles i stedet for at blive skønnet. Prisen estimeres med et gratis metadata-kald
   FØR hvert udtræk, og et udtræk der ville bringe summen over budgettet afvises før der
   hentes noget.
2. **Kun 1m OHLCV hentes.** 3m/5m/15m aggregeres lokalt i ``data.resample``, så alle
   timeframes deler bar-grænser pr. konstruktion.
3. **NQ til ATR, MNQ til spread.** MNQ blev noteret 2019-05-06; der anmodes aldrig om
   MNQ-data før den dato.
4. **Rullen skal kunne ses.** Kontinuerlig serie ``<ROD>.v.0`` (kontrakten med størst
   volumen), og ``instrument_id`` bevares på hver bar, så et rullespring kan skelnes
   fra et prisspring.

Udtræk bogføres i ``data/cache/databento/udtraek.jsonl``. Nøglen læses fra ``.env`` ved
hvert klientkald — filen vinder over en ældre værdi i miljøet — og skrives aldrig ud.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd

from data.cache_parquet import CACHE_ROOT, ROOT, read_ohlcv, write_parquet
from data.ohlcv import OHLCVValidationError, validate_ohlcv

DATASET = "GLBX.MDP3"
BUDGET_USD = 40.0
LEDGER = CACHE_ROOT / "databento" / "udtraek.jsonl"

# CME: første handelsdag. Der findes ingen data før, og der må ikke bedes om dem.
NOTERING = {"MNQ": "2019-05-06"}


class BudgetOverskredet(RuntimeError):
    """Et udtræk ville bringe forbruget over fasens budget."""


def client():
    """Historical-klient. Nøglen hentes fra DATABENTO_API_KEY i .env (eller miljøet)."""
    from dotenv import load_dotenv

    # override=True: nøglen kan være rulleret mens en ældre værdi ligger i miljøet.
    load_dotenv(ROOT / ".env", override=True)
    if not os.environ.get("DATABENTO_API_KEY"):
        raise RuntimeError("DATABENTO_API_KEY mangler — læg den i .env i repo-roden")
    import databento as db

    return db.Historical()


# ---------------------------------------------------------------------------
# Budget og notering
# ---------------------------------------------------------------------------

def spent_usd(ledger: Path = LEDGER) -> float:
    ledger = Path(ledger)
    if not ledger.exists():
        return 0.0
    return sum(json.loads(l)["estimat_usd"]
               for l in ledger.read_text().splitlines() if l.strip())


def check_budget(estimate_usd: float, spent: float, budget: float = BUDGET_USD) -> None:
    if spent + estimate_usd > budget + 1e-9:
        raise BudgetOverskredet(f"udtræk ${estimate_usd:.2f} + brugt ${spent:.2f} "
                                f"> budget ${budget:.2f}")


def check_listing(symbol: str, start: str) -> None:
    """Afvis en anmodning der begynder før kontraktens notering."""
    sym = symbol.upper()
    for rod, noteret in NOTERING.items():
        if sym.startswith(rod):
            s = pd.Timestamp(start)
            s = s.tz_convert(None) if s.tz is not None else s
            if s < pd.Timestamp(noteret):
                raise ValueError(f"{rod} blev noteret {noteret} — der findes ingen data "
                                 f"før; start {start} afvises")


def _book(ledger: Path, entry: dict) -> None:
    ledger = Path(ledger)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with open(ledger, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Konvertering til kontrakten
# ---------------------------------------------------------------------------

def from_ohlcv(raw: pd.DataFrame | None) -> pd.DataFrame:
    """``DBNStore.to_df()`` for ohlcv-1m → kontrakten. ts_event er barens åbning."""
    if raw is None or len(raw) == 0:
        raise OHLCVValidationError("tomt svar [databento]")
    df = raw[[c for c in ("open", "high", "low", "close", "volume") if c in raw.columns]]
    df = df.astype("float64")
    if "instrument_id" not in raw.columns:
        raise OHLCVValidationError("manglende kolonner ['instrument_id'] [databento]")
    df["instrument_id"] = raw["instrument_id"].astype("int64")
    df.index = pd.DatetimeIndex(raw.index).tz_convert("UTC")
    df.index.name = "time"
    return validate_ohlcv(df, "databento")


def from_bbo(raw: pd.DataFrame | None) -> pd.DataFrame:
    """``DBNStore.to_df()`` for bbo-1s/-1m → bid/ask pr. interval. Index er ts_recv (UTC)."""
    if raw is None or len(raw) == 0:
        raise OHLCVValidationError("tomt svar [databento bbo]")
    need = ("bid_px_00", "ask_px_00", "bid_sz_00", "ask_sz_00", "instrument_id")
    mangler = [c for c in need if c not in raw.columns]
    if mangler:
        raise OHLCVValidationError(f"manglende kolonner {mangler} [databento bbo]")
    df = pd.DataFrame({
        "bid": raw["bid_px_00"].astype("float64"),
        "ask": raw["ask_px_00"].astype("float64"),
        "bid_sz": raw["bid_sz_00"].astype("float64"),
        "ask_sz": raw["ask_sz_00"].astype("float64"),
        "instrument_id": raw["instrument_id"].astype("int64"),
    })
    df.index = pd.DatetimeIndex(raw.index).tz_convert("UTC")
    df.index.name = "time"
    if not (df.index.is_monotonic_increasing and df.index.is_unique):
        raise OHLCVValidationError("ikke-monotone timestamps [databento bbo]")
    return df


CONVERT = {"ohlcv-1m": from_ohlcv, "bbo-1m": from_bbo, "bbo-1s": from_bbo}


# ---------------------------------------------------------------------------
# Udtræk
# ---------------------------------------------------------------------------

def year_chunks(start: str, end: str) -> list[tuple[str, str]]:
    """[start, end) delt på kalenderår, som datostrenge."""
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    graenser = [s] + [pd.Timestamp(year=y, month=1, day=1)
                      for y in range(s.year + 1, e.year + 1)] + [e]
    graenser = sorted({g for g in graenser if s <= g <= e})
    fmt = lambda t: t.strftime("%Y-%m-%d") if t == t.normalize() else t.isoformat()
    return [(fmt(a), fmt(b)) for a, b in zip(graenser[:-1], graenser[1:])]


def chunk_path(cache_root: Path, symbol: str, schema: str, start: str, end: str) -> Path:
    safe = lambda x: x.replace(":", "")
    return (Path(cache_root) / "databento" / DATASET / schema / symbol
            / f"{safe(start)}_{safe(end)}.parquet")


def estimate_cost(cli, symbol: str, schema: str, start: str, end: str) -> float:
    return float(cli.metadata.get_cost(dataset=DATASET, symbols=[symbol], schema=schema,
                                       stype_in="continuous", start=start, end=end))


def plan(cli, symbol: str, schema: str, start: str, end: str,
         cache_root: Path = CACHE_ROOT) -> pd.DataFrame:
    """Én række pr. årsbid: er den cachet, og hvad koster den (gratis metadata-kald)."""
    check_listing(symbol, start)
    rows = []
    for s, e in year_chunks(start, end):
        p = chunk_path(cache_root, symbol, schema, s, e)
        cachet = p.exists()
        rows.append({"symbol": symbol, "schema": schema, "start": s, "slut": e,
                     "cachet": cachet,
                     "estimat_usd": 0.0 if cachet else estimate_cost(cli, symbol, schema, s, e),
                     "sti": p})
    return pd.DataFrame(rows)


def pull(cli, symbol: str, schema: str, start: str, end: str, *, execute: bool,
         budget: float = BUDGET_USD, ledger: Path = LEDGER,
         cache_root: Path = CACHE_ROOT) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    """Estimér — og hvis ``execute`` — hent [start, end) i årsbidder.

    Hele planens estimat skal kunne rummes i budgettet før første bid hentes, og hver
    bid tjekkes igen umiddelbart før den hentes. Cachede bidder koster ingenting.
    """
    p = plan(cli, symbol, schema, start, end, cache_root)
    check_budget(float(p["estimat_usd"].sum()), spent_usd(ledger), budget)
    if not execute:
        return p, None

    frames = []
    for r in p.to_dict("records"):
        if r["cachet"]:
            frames.append(read_ohlcv(r["sti"]) if schema.startswith("ohlcv")
                          else pd.read_parquet(r["sti"]))
            continue
        check_budget(r["estimat_usd"], spent_usd(ledger), budget)
        store = cli.timeseries.get_range(dataset=DATASET, symbols=[symbol], schema=schema,
                                         stype_in="continuous", start=r["start"],
                                         end=r["slut"])
        df = CONVERT[schema](store.to_df())
        write_parquet(df, r["sti"])
        _book(ledger, {"tid_utc": pd.Timestamp.now("UTC").isoformat(), "symbol": symbol,
                       "schema": schema, "start": r["start"], "slut": r["slut"],
                       "estimat_usd": r["estimat_usd"], "raekker": len(df)})
        frames.append(df)
    samlet = pd.concat(frames)
    if schema.startswith("ohlcv"):
        validate_ohlcv(samlet, f"databento {symbol} {schema} samlet")
    return p, samlet
