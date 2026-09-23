"""B4 kandidat 1 — verifikation af MNQ-data mod NQ (antagelse A).

Ser ikke på signaler eller udfald og lægger intet til en tærskel. Kun datakvalitet:

    dækning     barer pr. RTH-dag og manglende minutter mod NYSE-kalenderen, MNQ mod NQ
    kontrakter  antal og tidspunkt for MNQ's kontraktskift (instrument_id), mod NQ's
    væger       hvor meget NQ og MNQ's 15m-høj/lav afviger i tick, som fordeling —
                testen af antagelse (A) i research/output/b4_hypoteser.md: et prisniveau
                i indekspoint er det samme på NQ og MNQ

    .venv/bin/python -m research.b4_mnq_verifikation

Vinduet er MNQ's notering 2019-05-06 til holdout-grænsen (``data.holdout.HOLDOUT_START``).
Begge serier hentes gennem ``data.holdout.load_in_sample`` — holdout-perioden åbnes ikke.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data import holdout, resample, sessions  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "output"

NQ, MNQ = "NQ.v.0", "MNQ.v.0"
MNQ_START = pd.Timestamp("2019-05-06", tz="UTC")
TICK = 0.25
BAR_MIN = 15


# ---------------------------------------------------------------------------
# Dækning
# ---------------------------------------------------------------------------

def _et_dag(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    return index.tz_convert(sessions.ET).tz_localize(None).normalize().as_unit("ns")


def rth_dage(start, slut) -> pd.DatetimeIndex:
    """XNYS-sessionernes datoer fra ``start`` til, men ikke med, ``slut``."""
    plan = pd.DatetimeIndex(sessions._xnys().schedule.index).as_unit("ns")
    d0, d1 = pd.Timestamp(pd.Timestamp(start).date()), pd.Timestamp(pd.Timestamp(slut).date())
    return plan[(plan >= d0) & (plan < d1)]


def dag_minutter(dage: pd.DatetimeIndex) -> pd.Series:
    """Forventede RTH-minutter pr. dag (390 en normal dag, 210 på en halv dag)."""
    plan = sessions._xnys().schedule
    varighed = (plan["close"] - plan["open"]) / pd.Timedelta(minutes=1)
    return varighed.reindex(dage)


def daekning(df_1m: pd.DataFrame, dage: pd.DatetimeIndex) -> pd.Series:
    """1m-barer i RTH pr. dag, reindekseret til ``dage`` (0 for dage uden data)."""
    rth = sessions.rth_mask(df_1m.index, 1)
    dag = _et_dag(df_1m.index[rth])
    return pd.Series(1, index=dag).groupby(level=0).size().reindex(dage, fill_value=0)


# ---------------------------------------------------------------------------
# Kontraktskift
# ---------------------------------------------------------------------------

def kontraktskift(df_1m: pd.DataFrame) -> pd.DataFrame:
    iid = df_1m["instrument_id"].to_numpy()
    idx = np.flatnonzero(iid[1:] != iid[:-1]) + 1
    return pd.DataFrame({"tid_utc": df_1m.index[idx], "fra": iid[idx - 1], "til": iid[idx]})


# ---------------------------------------------------------------------------
# Væger
# ---------------------------------------------------------------------------

def _rulle_generation(df: pd.DataFrame) -> np.ndarray:
    """Løbende tæller: hvor mange kontraktskift er set til og med hver bar."""
    iid = df["instrument_id"].to_numpy()
    g = np.zeros(len(df), dtype=int)
    g[np.flatnonzero(iid[1:] != iid[:-1]) + 1] = 1
    return np.cumsum(g)


def vaeger(nq_15m: pd.DataFrame, mnq_15m: pd.DataFrame) -> pd.DataFrame:
    """Fælles 15m-tidsstempler: high/low-afvigelse MNQ − NQ, i tick.

    ``rullevindue`` er sandt når NQ og MNQ ikke er på samme kontraktgeneration —
    de to serier ruller ikke altid samme dag (§4 i datakilder.md), og i det vindue er
    forskellen kalenderspread, ikke en afvigelse i samme prisniveau.
    """
    faelles = nq_15m.index.intersection(mnq_15m.index)
    a, b = nq_15m.loc[faelles], mnq_15m.loc[faelles]
    ud = pd.DataFrame({
        "high_diff_tick": (b["high"].to_numpy() - a["high"].to_numpy()) / TICK,
        "low_diff_tick": (b["low"].to_numpy() - a["low"].to_numpy()) / TICK,
    }, index=faelles)
    ud["rth"] = sessions.rth_mask(faelles, BAR_MIN)
    ud["rullevindue"] = _rulle_generation(a) != _rulle_generation(b)
    return ud


def _p(x, q: float) -> float:
    x = np.asarray(x, dtype=float)
    return float(np.percentile(x, q)) if len(x) else float("nan")


def vaeger_fordeling(v: pd.DataFrame, maske: np.ndarray) -> dict:
    sub = v[maske]
    h, l = sub["high_diff_tick"].abs(), sub["low_diff_tick"].abs()
    row = {"n": len(sub)}
    for navn, s in (("high", h), ("low", l)):
        row[f"{navn}_p50"] = _p(s, 50)
        row[f"{navn}_p90"] = _p(s, 90)
        row[f"{navn}_p99"] = _p(s, 99)
        row[f"{navn}_max"] = float(s.max()) if len(s) else float("nan")
        row[f"{navn}_0_tick_pct"] = 100 * (s == 0).sum() / len(s) if len(s) else float("nan")
        row[f"{navn}_le1_tick_pct"] = 100 * (s <= 1).sum() / len(s) if len(s) else float("nan")
    return row


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------

def _tal(v, nd: int = 2) -> str:
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "—"
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    return f"{v:.{nd}f}".replace(".", ",")


def outliers_md(v: pd.DataFrame, nq_15m: pd.DataFrame, mnq_15m: pd.DataFrame, n: int = 10) -> str:
    """De største væge-afvigelser uden for rullevinduerne, til gennemsigtighed."""
    sub = v[~v["rullevindue"]].copy()
    sub["stoerst"] = sub[["high_diff_tick", "low_diff_tick"]].abs().max(axis=1)
    top = sub.sort_values("stoerst", ascending=False).head(n)
    linjer = ["| tid_utc | high_diff_tick | low_diff_tick | NQ high/low | MNQ high/low |",
              "|---|---|---|---|---|"]
    for t, r in top.iterrows():
        na, nb = nq_15m.loc[t], mnq_15m.loc[t]
        linjer.append(f"| {t} | {_tal(r['high_diff_tick'],0)} | {_tal(r['low_diff_tick'],0)} | "
                      f"{_tal(na['high'])}/{_tal(na['low'])} | "
                      f"{_tal(nb['high'])}/{_tal(nb['low'])} |")
    return "\n".join(linjer) + "\n"


def skriv_md(meta: dict, dae: pd.DataFrame, kskift_nq: pd.DataFrame, kskift_mnq: pd.DataFrame,
            fordeling: dict, outliers: str, rullevindue_n: int) -> str:
    dele = [
        "# B4 kandidat 1 — MNQ-data, verifikation mod NQ\n",
        f"Kørt {meta['koert_utc']} UTC. Vindue {meta['start']} → {meta['slut']} (MNQ's "
        f"notering til holdout-grænsen). Ser ikke på signaler eller udfald og lægger "
        f"intet til en tærskel.\n",
        f"NQ.v.0: {meta['n_nq_1m']} 1m-barer → {meta['n_nq_15m']} 15m-barer. "
        f"MNQ.v.0: {meta['n_mnq_1m']} 1m-barer → {meta['n_mnq_15m']} 15m-barer. "
        f"Fælles 15m-tidsstempler: {meta['n_faelles_15m']}.\n",
        "## Dækning pr. RTH-dag\n",
        f"{meta['n_dage']} RTH-dage i vinduet (NYSE-kalenderen).\n",
        "| | NQ | MNQ |\n|---|---|---|\n"
        f"| dage med 0 manglende minutter | {_tal(dae['nq_dage_komplette_n'])} "
        f"({_tal(dae['nq_dage_komplette_pct'])}%) | {_tal(dae['mnq_dage_komplette_n'])} "
        f"({_tal(dae['mnq_dage_komplette_pct'])}%) |\n"
        f"| dage uden data overhovedet | {_tal(dae['nq_dage_uden_data_n'])} | "
        f"{_tal(dae['mnq_dage_uden_data_n'])} |\n"
        f"| manglende minutter, alle dage, sum | {_tal(dae['nq_manglende_min_sum'])} | "
        f"{_tal(dae['mnq_manglende_min_sum'])} |\n"
        f"| manglende minutter, andel af forventet | {_tal(dae['nq_manglende_pct'])}% | "
        f"{_tal(dae['mnq_manglende_pct'])}% |\n"
        f"| barer pr. dag, p10/p50/p90 | {_tal(dae['nq_barer_p10'],1)}/"
        f"{_tal(dae['nq_barer_p50'],1)}/{_tal(dae['nq_barer_p90'],1)} | "
        f"{_tal(dae['mnq_barer_p10'],1)}/{_tal(dae['mnq_barer_p50'],1)}/"
        f"{_tal(dae['mnq_barer_p90'],1)} |\n",
        f"Dage hvor MNQ og NQ's barantal afviger: {_tal(dae['dage_barantal_afviger_n'])} "
        f"af {meta['n_dage']} ({_tal(dae['dage_barantal_afviger_pct'])}%).\n",
        "## Kontraktskift\n",
        f"NQ: {len(kskift_nq)} skift i vinduet. MNQ: {len(kskift_mnq)} skift i vinduet.\n",
        "### MNQ, alle skift\n",
        "| tid_utc | fra instrument_id | til instrument_id |\n|---|---|---|\n" + "\n".join(
            f"| {r.tid_utc} | {r.fra} | {r.til} |" for r in kskift_mnq.itertuples()) + "\n",
        "### NQ, alle skift\n",
        "| tid_utc | fra instrument_id | til instrument_id |\n|---|---|---|\n" + "\n".join(
            f"| {r.tid_utc} | {r.fra} | {r.til} |" for r in kskift_nq.itertuples()) + "\n",
        "## 15m-vægernes afvigelse, MNQ mod NQ, i tick (0,25 point)\n",
        "Absolut afvigelse på fælles 15m-tidsstempler. `high` er lysets top, `low` bunden "
        "— begge indgår i kandidat 1's zonehøjde (\"væger medregnet\").\n",
        "| session | n | high p50 | high p90 | high p99 | high maks | high = 0 tick | "
        "high ≤ 1 tick | low p50 | low p90 | low p99 | low maks | low = 0 tick | "
        "low ≤ 1 tick |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n",
    ]
    for navn, row in fordeling.items():
        dele[-1] += (
            f"| {navn} | {row['n']} | {_tal(row['high_p50'])} | {_tal(row['high_p90'])} | "
            f"{_tal(row['high_p99'])} | {_tal(row['high_max'])} | "
            f"{_tal(row['high_0_tick_pct'])}% | {_tal(row['high_le1_tick_pct'])}% | "
            f"{_tal(row['low_p50'])} | {_tal(row['low_p90'])} | {_tal(row['low_p99'])} | "
            f"{_tal(row['low_max'])} | {_tal(row['low_0_tick_pct'])}% | "
            f"{_tal(row['low_le1_tick_pct'])}% |\n")
    dele.append(
        f"**Rullevinduer:** {rullevindue_n} af {meta['n_faelles_15m']} fælles 15m-barer "
        "ligger i et vindue hvor NQ og MNQ ikke er på samme kontraktgeneration — de to "
        "serier ruller ikke altid samme UTC-dag (datakilder.md §4). Der er forskellen "
        "kalenderspread mellem to forskellige kontrakter, ikke et brud på antagelse (A), "
        "og de bars er holdt uden for tabellen ovenfor og outlier-listen nedenfor.\n")
    dele.append(
        "### De 10 største afvigelser, uden for rullevinduer\n" + outliers +
        "\nSpredt over søndag-genåbningen (18:00 ET), den tynde time før RTH-åbning "
        "(07:00-09:00 ET) og markedsuro (marts 2020, december 2022) — øjeblikke hvor de "
        "to selvstændigt handlede ordrebøger kan have et enkelt tryk der rammer den ene "
        "bog og ikke den anden. Ikke undersøgt pr. bar om close konvergerer bagefter; "
        "listen er til gennemsigtighed, ikke en forklaring der er efterprøvet.\n")
    dele.append(
        "## Fortolkning — antagelse (A)\n"
        "Antagelsen i `research/output/b4_hypoteser.md` er at et prisniveau i indekspoint "
        "er det samme på NQ og MNQ. Tabellen ovenfor måler præcis det, på de kanter "
        "kandidat 1's zoner bruger. Kørslen tager ikke stilling til om afvigelsen er "
        "lille nok — det gøres når edge-testen præregistreres.\n")
    return "\n".join(dele)


def main() -> None:
    nq_1m_all = holdout.load_in_sample(NQ)
    mnq_1m = holdout.load_in_sample(MNQ)
    nq_1m = nq_1m_all[nq_1m_all.index >= MNQ_START]

    dage = rth_dage(MNQ_START, holdout.HOLDOUT_START)
    forventet = dag_minutter(dage)
    nq_barer = daekning(nq_1m, dage)
    mnq_barer = daekning(mnq_1m, dage)

    def _dae_stats(prefix: str, barer: pd.Series) -> dict:
        mangler = forventet - barer
        mangler_pct_pr_dag = 100 * mangler / forventet
        return {
            f"{prefix}_dage_komplette_n": int((mangler == 0).sum()),
            f"{prefix}_dage_komplette_pct": 100 * (mangler == 0).sum() / len(dage),
            f"{prefix}_dage_uden_data_n": int((barer == 0).sum()),
            f"{prefix}_manglende_min_sum": float(mangler.sum()),
            f"{prefix}_manglende_pct": 100 * mangler.sum() / forventet.sum(),
            f"{prefix}_barer_p10": _p(barer, 10), f"{prefix}_barer_p50": _p(barer, 50),
            f"{prefix}_barer_p90": _p(barer, 90),
        }

    dae = {**_dae_stats("nq", nq_barer), **_dae_stats("mnq", mnq_barer)}
    afviger = (nq_barer != mnq_barer)
    dae["dage_barantal_afviger_n"] = int(afviger.sum())
    dae["dage_barantal_afviger_pct"] = 100 * afviger.sum() / len(dage)

    kskift_nq = kontraktskift(nq_1m)
    kskift_mnq = kontraktskift(mnq_1m)

    nq_15m = resample.aggregate(nq_1m, BAR_MIN)
    mnq_15m = resample.aggregate(mnq_1m, BAR_MIN)
    v = vaeger(nq_15m, mnq_15m)
    ren = ~v["rullevindue"].to_numpy()
    rth = v["rth"].to_numpy()
    fordeling = {
        "alle, ekskl. rullevinduer": vaeger_fordeling(v, ren),
        "RTH, ekskl. rullevinduer": vaeger_fordeling(v, ren & rth),
        "ETH, ekskl. rullevinduer": vaeger_fordeling(v, ren & ~rth),
        "alle, med rullevinduer": vaeger_fordeling(v, np.ones(len(v), dtype=bool)),
    }
    outliers = outliers_md(v, nq_15m, mnq_15m)
    rullevindue_n = int(v["rullevindue"].sum())

    meta = {
        "koert_utc": pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M"),
        "start": MNQ_START.strftime("%Y-%m-%d"),
        "slut": holdout.HOLDOUT_START.strftime("%Y-%m-%d"),
        "n_nq_1m": len(nq_1m), "n_mnq_1m": len(mnq_1m),
        "n_nq_15m": len(nq_15m), "n_mnq_15m": len(mnq_15m),
        "n_faelles_15m": len(v), "n_dage": len(dage),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    md = skriv_md(meta, dae, kskift_nq, kskift_mnq, fordeling, outliers, rullevindue_n)
    (OUT / "b4_mnq_data.md").write_text(md, encoding="utf-8")
    print(md)
    print(f"skrev {OUT / 'b4_mnq_data.md'}")


if __name__ == "__main__":
    main()
