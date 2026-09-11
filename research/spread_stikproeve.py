"""MNQ-spread på en stratificeret stikprøve af handelsdage — B3.

Spread er i dag et SKØN på 1,5 tick, og det indgår i hvert omkostningstal i projektet.
Her måles det på MNQ — det er mikroens spread der betales — på repræsentative dage
fordelt på rolige og volatile perioder, i RTH og uden for RTH hver for sig.

    .venv/bin/python -m research.spread_stikproeve --estimat
    .venv/bin/python -m research.spread_stikproeve --hent
    .venv/bin/python -m research.spread_stikproeve --analyse

## Design — præregistreret 2026-09-11, før udtrækket

Univers    XNYS-sessioner fra MNQ's notering 2019-05-06 til og med 2026-09-10, minus
           halve handelsdage og minus skiftedagen og de 5 handelsdage før hvert skift af
           MNQ.v.0 — dér ligger serien på den udløbende kontrakt (jf. rulletjekket).
Regime     NQ's RTH-range pr. session i procent af RTH-åbningen, fra NQ.v.0 1m.
           Terciler over hele universet: rolig / mellem / volatil.
Udtræk     4 dage pr. (kalenderår × tercil), trukket med numpy default_rng(20260911).
           Har en celle færre end 4 dage, tages alle. Højst 8 × 3 × 4 = 96 dage.
Dag        hele Globex-handelsdagen der ender på datoen: 18:00 ET dagen før → 17:00 ET.
Data       MNQ.v.0 bbo-1s (Databento GLBX.MDP3), inden for fasens budget på $40.
Spread     (ask − bid) / 0,25 i ticks. En quote gælder til den ændres, så hver dag lægges
           på et 1-sekunds gitter og fremføres — dog højst 60 s (handelsstop, datahul).
           Låste, krydsede og tomme sider udelades og tælles.
Mål        tidsvægtet (alle sekunder) og ved minutgrænser (sekund :00 — det øjeblik en
           bar lukker og en markedsordre sendes).
Session    RTH = sekundet ligger i NYSE's ordinære session (data.sessions), ellers ETH.
Tabeller   pr. session og mål; pr. tercil × session; pr. år × session; pr. 30-min-blok
           (ET). n, gennemsnit, p10/p50/p90 i ticks, andel på præcis 1 tick.

Omkostningsmodellen bruger GENNEMSNITTET (spread_ticks × $0,50 pr. rundtur);
percentilerne viser halen.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data import sessions  # noqa: E402
from data import src_databento as dbs  # noqa: E402
from data.cache_parquet import CACHE_ROOT  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "output"
ET = sessions.ET
MNQ = "MNQ.v.0"
SCHEMA = "bbo-1s"
START = "2019-05-06"
SLUT = "2026-09-10"
K_PR_CELLE = 4
SEED = 20260911
ROLL_DAGE = 5
TICK = 0.25
TICK_USD = 0.50
MAX_FREMFOER_S = 60
BLOK_MIN = 30
STIK_ROOT = CACHE_ROOT / "stikproeve"
SYMBOLOGI = CACHE_ROOT / "databento" / "symbologi_continuous.json"


# ---------------------------------------------------------------------------
# Udvælgelse
# ---------------------------------------------------------------------------

def nq_rth_range(nq_1m: pd.DataFrame) -> pd.DataFrame:
    """NQ's RTH-range pr. session i procent af RTH-åbningen."""
    rth = nq_1m[sessions.rth_mask(nq_1m.index, 1)]
    dag = rth.index.tz_convert(ET).tz_localize(None).normalize()
    g = rth.groupby(dag)
    ud = pd.DataFrame({"aabning": g["open"].first(), "high": g["high"].max(),
                       "low": g["low"].min(), "n_1m": g["open"].size()})
    ud["rth_range_pct"] = (ud["high"] - ud["low"]) / ud["aabning"] * 100
    return ud


def skiftedage(symbologi: dict, symbol: str = MNQ) -> list[pd.Timestamp]:
    """d0 for hvert kontraktskift. Første interval begynder ved forespørgslen — intet skift."""
    iv = symbologi[symbol]["result"][symbol]
    return [pd.Timestamp(m["d0"]) for m in iv[1:]]


def univers(dagsrange: pd.DataFrame, skift: list[pd.Timestamp], start: str = START,
            slut: str = SLUT, roll_dage: int = ROLL_DAGE) -> pd.DataFrame:
    """Sessionerne der kan trækkes, med tercil og år."""
    cal = sessions._xnys()
    alle = cal.schedule.index
    sess = alle[(alle >= pd.Timestamp(start)) & (alle <= pd.Timestamp(slut))]
    udeluk = set(pd.DatetimeIndex(cal.early_closes))
    for d0 in skift:
        pos = int(alle.searchsorted(pd.Timestamp(d0)))
        udeluk.update(alle[max(0, pos - roll_dage):min(len(alle), pos + 1)])
    sess = sess[~sess.isin(list(udeluk))]
    u = dagsrange.reindex(sess).dropna(subset=["rth_range_pct"]).copy()
    graense = u["rth_range_pct"].quantile([1 / 3, 2 / 3]).to_numpy()
    u["tercil"] = np.select([u["rth_range_pct"] <= graense[0],
                             u["rth_range_pct"] <= graense[1]], ["rolig", "mellem"], "volatil")
    u["aar"] = u.index.year
    u.index.name = "dato"
    return u


def vaelg(u: pd.DataFrame, k: int = K_PR_CELLE, seed: int = SEED) -> pd.DataFrame:
    """k dage pr. (år, tercil), trukket deterministisk. Små celler tages hele."""
    rng = np.random.default_rng(seed)
    dele = []
    for _, g in u.groupby(["aar", "tercil"], sort=True):
        if len(g) <= k:
            dele.append(g)
        else:
            dele.append(g.iloc[np.sort(rng.choice(len(g), size=k, replace=False))])
    return pd.concat(dele).sort_index()


def globex_vindue(dato: pd.Timestamp) -> tuple[str, str]:
    """Globex-handelsdagen der ender på ``dato``: [18:00 ET dagen før, 17:00 ET) i UTC."""
    dato = pd.Timestamp(dato).normalize()
    s = pd.Timestamp(f"{dato - pd.Timedelta(days=1):%Y-%m-%d} 18:00").tz_localize(ET)
    e = pd.Timestamp(f"{dato:%Y-%m-%d} 17:00").tz_localize(ET)
    fmt = "%Y-%m-%dT%H:%M"
    return s.tz_convert("UTC").strftime(fmt), e.tz_convert("UTC").strftime(fmt)


# ---------------------------------------------------------------------------
# Udtræk
# ---------------------------------------------------------------------------

def dag_sti(dato: pd.Timestamp) -> Path:
    s, e = globex_vindue(dato)
    return dbs.chunk_path(STIK_ROOT, MNQ, SCHEMA, *dbs.year_chunks(s, e)[0])


def plan_alle(cli, dage: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for dato in dage.index:
        s, e = globex_vindue(dato)
        rows.append(dbs.plan(cli, MNQ, SCHEMA, s, e, cache_root=STIK_ROOT).assign(dato=dato))
    return pd.concat(rows, ignore_index=True)


def hent(cli, dage: pd.DataFrame, plan: pd.DataFrame) -> None:
    """Hele stikprøvens estimat skal rummes i budgettet før første dag hentes."""
    dbs.check_budget(float(plan["estimat_usd"].sum()), dbs.spent_usd())
    for i, dato in enumerate(dage.index, 1):
        s, e = globex_vindue(dato)
        dbs.pull(cli, MNQ, SCHEMA, s, e, execute=True, cache_root=STIK_ROOT)
        if i % 12 == 0 or i == len(dage):
            print(f"  {i}/{len(dage)} dage, brugt ${dbs.spent_usd():.2f}", flush=True)


# ---------------------------------------------------------------------------
# Måling
# ---------------------------------------------------------------------------

def sekundgitter(bbo: pd.DataFrame, max_fremfoer_s: int = MAX_FREMFOER_S) -> pd.DataFrame:
    """Bid/ask på et 1-sekunds gitter, fremført højst ``max_fremfoer_s`` sekunder."""
    if len(bbo) == 0:
        return bbo[["bid", "ask"]]
    b = bbo[["bid", "ask"]].groupby(bbo.index.floor("1s")).last()
    gitter = pd.date_range(b.index[0], b.index[-1], freq="1s")
    return b.reindex(gitter).ffill(limit=max_fremfoer_s).dropna()


def spread_dag(bbo: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Spread i ticks pr. sekund med session, minutgrænse og 30-min-blok. + antal udeladte."""
    g = sekundgitter(bbo)
    ticks = ((g["ask"] - g["bid"]) / TICK).to_numpy()
    gyldig = (g["bid"].to_numpy() > 0) & (g["ask"].to_numpy() > 0) & (ticks > 0)
    idx = g.index[gyldig]
    et = idx.tz_convert(ET).tz_localize(None)
    ud = pd.DataFrame({
        "ticks": ticks[gyldig].astype("float32"),
        "rth": sessions.rth_mask(idx, 1 / 60),
        "minutgraense": np.asarray(idx.second == 0),
        "blok": np.asarray((et.hour * 60 + et.minute) // BLOK_MIN, dtype="int16"),
    })
    return ud, int((~gyldig).sum())


def saml(dage: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    dele, meta = [], []
    for dato, r in dage.iterrows():
        sti = dag_sti(dato)
        if not sti.exists():
            raise FileNotFoundError(f"mangler {sti.name} — kør --hent")
        bbo = pd.read_parquet(sti)
        d, udeladt = spread_dag(bbo)
        d["aar"] = np.int16(r["aar"])
        d["tercil"] = r["tercil"]
        dele.append(d)
        meta.append({"dato": dato, "aar": int(r["aar"]), "tercil": r["tercil"],
                     "rth_range_pct": float(r["rth_range_pct"]), "raa_records": len(bbo),
                     "sekunder": len(d), "udeladt_laast_krydset": udeladt,
                     "instrument_ids": ",".join(map(str, sorted(bbo["instrument_id"].unique())))})
    alle = pd.concat(dele, ignore_index=True)
    alle["tercil"] = alle["tercil"].astype("category")
    return alle, pd.DataFrame(meta)


def _stats(x: pd.Series) -> pd.Series:
    return pd.Series({"n": len(x), "gns_ticks": float(x.mean()),
                      "p10_ticks": float(x.quantile(0.1)), "p50_ticks": float(x.quantile(0.5)),
                      "p90_ticks": float(x.quantile(0.9)),
                      "andel_1_tick_pct": float((x == 1).mean() * 100)})


def tabeller(alle: pd.DataFrame) -> dict[str, pd.DataFrame]:
    alle = alle.assign(session=np.where(alle["rth"], sessions.RTH, sessions.ETH))
    mg = alle[alle["minutgraense"]]
    st = lambda df, by: df.groupby(by, observed=True)["ticks"].apply(_stats).unstack()
    blok = st(alle, ["session", "blok"]).reset_index()
    blok["blok_et"] = blok["blok"].map(lambda b: f"{b * BLOK_MIN // 60:02d}:{b * BLOK_MIN % 60:02d}")
    return {
        "pr_session": pd.concat({"tidsvægtet": st(alle, "session"),
                                 "ved_minutgrænse": st(mg, "session")}, names=["mål"]),
        "pr_tercil": st(alle, ["tercil", "session"]),
        "pr_aar": st(alle, ["aar", "session"]),
        "pr_blok": blok.drop(columns="blok").set_index(["session", "blok_et"]),
    }


def omkostning(t: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Rundturens pris med målt spread i stedet for skønnet. Gebyr og slippage uændret."""
    import yaml

    from backtest import costs
    from research.atr_fordeling import omk_usd_rundtur

    config = yaml.safe_load((ROOT / "config.yaml").read_text())
    skoen_ticks = float(costs._asset_costs(config, "MNQ")["spread_ticks"])
    uden_spread = omk_usd_rundtur(config) - skoen_ticks * TICK_USD
    ps = t["pr_session"]
    varianter = [("skøn i config.yaml", skoen_ticks)] + [
        (f"målt {s}, {m.replace('_', ' ')}", float(ps.loc[(m, s), "gns_ticks"]))
        for m in ("tidsvægtet", "ved_minutgrænse") for s in (sessions.RTH, sessions.ETH)]
    return pd.DataFrame([{"variant": v, "spread_ticks_gns": x,
                          "spread_usd_rundtur": x * TICK_USD,
                          "omk_usd_rundtur": uden_spread + x * TICK_USD} for v, x in varianter])


def skriv_md(t: dict, omk: pd.DataFrame, meta: pd.DataFrame, u: pd.DataFrame,
             dage: pd.DataFrame, graense: np.ndarray) -> str:
    from research.atr_fordeling import md_tabel

    def tab(df: pd.DataFrame) -> str:
        d = df.reset_index()
        if "n" in d.columns:
            d["n"] = d["n"].astype(int)
        return md_tabel(d, list(d.columns))

    komp = dage.groupby(["aar", "tercil"]).size().unstack(fill_value=0)
    uni = u.groupby(["aar", "tercil"]).size().unstack(fill_value=0)
    komp = komp.join(uni, rsuffix="_i_univers")
    return "\n".join([
        "# MNQ-spread — stratificeret stikprøve\n",
        f"Fase 1, B3. Kørt {pd.Timestamp.now('UTC'):%Y-%m-%d}. Kilde: Databento GLBX.MDP3, "
        f"{MNQ} {SCHEMA}. {len(dage)} Globex-handelsdage trukket fra {len(u)} i universet "
        f"({START} → {SLUT}).\n",
        "Designet er præregistreret i `research/spread_stikproeve.py` før udtrækket. "
        f"Tercilgrænser for NQ's RTH-range: {graense[0]:.3f}% og {graense[1]:.3f}%.\n",
        "## Pr. session\n", tab(t["pr_session"]),
        "## Omkostning pr. rundtur med målt spread\n",
        "Gebyr ($1,22) og slippage (0,5 tick pr. side) er uændrede; kun spread-leddet skifter.\n",
        md_tabel(omk, list(omk.columns)),
        "## Pr. regime (tidsvægtet)\n", tab(t["pr_tercil"]),
        "## Pr. år (tidsvægtet)\n", tab(t["pr_aar"]),
        "## Pr. 30-min-blok, ET (tidsvægtet)\n", tab(t["pr_blok"]),
        "## Stikprøvens sammensætning (dage)\n", tab(komp),
        f"Udeladte sekunder (låst/krydset/tom side): {int(meta['udeladt_laast_krydset'].sum())} "
        f"af {int(meta['sekunder'].sum() + meta['udeladt_laast_krydset'].sum())}.\n",
    ])


def main() -> None:
    from research.fase1_data import NQ, load_databento

    ap = argparse.ArgumentParser()
    trin = ap.add_mutually_exclusive_group(required=True)
    trin.add_argument("--estimat", action="store_true")
    trin.add_argument("--hent", action="store_true")
    trin.add_argument("--analyse", action="store_true")
    args = ap.parse_args()
    pd.set_option("display.width", 220)

    dr = nq_rth_range(load_databento(NQ, "ohlcv-1m"))
    u = univers(dr, skiftedage(json.loads(SYMBOLOGI.read_text())))
    graense = u["rth_range_pct"].quantile([1 / 3, 2 / 3]).to_numpy()
    dage = vaelg(u)
    OUT.mkdir(parents=True, exist_ok=True)
    dage.to_csv(OUT / "spread_mnq_stikproeve_dage.csv")
    print(f"univers {len(u)} sessioner | tercilgrænser {graense.round(3)} | "
          f"stikprøve {len(dage)} dage")
    print(dage.groupby(["aar", "tercil"]).size().unstack(fill_value=0).to_string())

    if args.estimat or args.hent:
        cli = dbs.client()
        plan = plan_alle(cli, dage)
        brugt = dbs.spent_usd()
        est = float(plan["estimat_usd"].sum())
        print(f"estimat ${est:.2f} | brugt før ${brugt:.2f} | i alt efter ${brugt + est:.2f} "
              f"| budget ${dbs.BUDGET_USD:.2f}")
        plan.drop(columns="sti").to_csv(OUT / "spread_mnq_plan.csv", index=False)
        if args.hent:
            hent(cli, dage, plan)
        return

    alle, meta = saml(dage)
    t = tabeller(alle)
    omk = omkostning(t)
    for navn, df in t.items():
        df.to_csv(OUT / f"spread_mnq_{navn}.csv")
    meta.to_csv(OUT / "spread_mnq_dage_meta.csv", index=False)
    (OUT / "spread_mnq.md").write_text(skriv_md(t, omk, meta, u, dage, graense), encoding="utf-8")
    print(t["pr_session"].to_string())
    print(omk.to_string(index=False))
    print(t["pr_tercil"].to_string())
    print(t["pr_aar"].to_string())
    print(f"skrev {OUT / 'spread_mnq.md'}")


if __name__ == "__main__":
    main()
