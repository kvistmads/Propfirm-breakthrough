"""Fase 1 — verifikation af datagrundlaget: K1-K4, Yahoo-sammenligning, ruller og spread.

    .venv/bin/python -m research.fase1_verifikation [--kun-yahoo]

``research/diagnostics.py`` kan ikke bruges: den importerer ``research.daily_bias``, som
ikke findes i repoet, og er skrevet til de daglige CSV'er fra det gamle repo. Tjekkene
her bruger dens definitioner (flad bar = H == L, huller målt som tidsforskel,
krydsvalidering på range som i ``gold_sources``) uden at importere den.

## Operationalisering — præregistreret 2026-09-11, før kørslen på Databento-data

Tærsklerne er PRD'ens §3. Hvordan de måles:

K1  dybde     første og sidste 1m-bar i NQ.v.0; år = (sidste − første) / 365,25.
              Holder ved ≥ 3. De fem største huller rapporteres med dato.
K2  kilder    pr. CME-handelsdag (18:00–17:00 ET), på hver kildes EGNE 15m-barer:
              |range_yahoo − range_databento| / range_databento. Median < 5% holder.
              Kun dage hvor kildernes barantal er inden for 10% af hinanden; første og
              sidste dag i overlappet udelades (delvise). RTH-range rapporteres ved siden
              af, afgør ikke. Supplement: 2026-08-26 bar for bar (15m og 1m RTH), og
              tidsforskydning på 1m-afkast (Spearman ved −90..+90 min; top forventet i 0).
K3  dækning   manglende RTH-minutter i 1m mod NYSE-kalenderen. Holder ved < 2%.
              3m/5m/15m arver dækningen — de er bygget af samme 1m.
K4  degeneration  flade barer (H == L) pr. timeframe og session. Holder ved < 1% i
              hver celle. Ikke-monotone timestamps: validering afviser udtrækket, så de
              er 0, eller også findes udtrækket ikke.

Ruller    hvert skift af instrument_id i NQ.v.0; spring = open(ny) − close(forrige) i
          ticks. "Uforklarede spring": |open − forrige close| ≥ 1 × ATR14 (1m) inden for
          samme kontrakt og uden brud. Tælles pr. år.
Spread    MNQ.v.0 bbo-1m. spread_ticks = (ask − bid) / 0,25 pr. snapshot. Et snapshot
          ved t beskriver minuttet [t−1m, t) og markeres RTH/ETH derefter. Låste,
          krydsede og tomme sider tælles og udelades. Pr. session og pr. 30-min-blok
          (ET): n, gennemsnit, p10/p50/p90, andel på præcis 1 tick.
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
from data.cache_parquet import read_ohlcv  # noqa: E402
from data.ohlcv import OHLC  # noqa: E402
from research.atr_fordeling import DOEGN, atr_pct, fordeling, session_series, true_range, wilder  # noqa: E402,E501

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "output"
ET = sessions.ET
TICK = 0.25
BAR_DAG = "2026-08-26"
K1_AAR, K2_PCT, K3_PCT, K4_PCT = 3.0, 5.0, 2.0, 1.0


def _et_dato(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    return index.tz_convert(ET).tz_localize(None).normalize()


# ---------------------------------------------------------------------------
# K1 — dybde
# ---------------------------------------------------------------------------

def k1_dybde(df: pd.DataFrame, top: int = 5) -> dict:
    t = df.index
    timer = np.diff(((t - t[0]) / pd.Timedelta(hours=1)).to_numpy(dtype=float))
    orden = np.argsort(timer)[::-1][:top]
    aar = float((t[-1] - t[0]) / pd.Timedelta(days=365.25))
    return {
        "foerste_bar_utc": str(t[0]), "sidste_bar_utc": str(t[-1]), "barer": int(len(t)),
        "aar": round(aar, 2), "holder": bool(aar >= K1_AAR),
        "stoerste_huller": [{"efter_bar_et": str(t[i].tz_convert(ET)),
                             "timer": round(float(timer[i]), 1)} for i in orden],
    }


# ---------------------------------------------------------------------------
# K3 — dækning i RTH
# ---------------------------------------------------------------------------

def k3_rth_daekning(df: pd.DataFrame, bar_minutes: int = 1) -> pd.DataFrame:
    """Manglende RTH-barer pr. år mod NYSE-kalenderen, for sessioner seriens span dækker."""
    plan = sessions._xnys().schedule
    plan = plan[(plan["open"] >= df.index[0])
                & (plan["close"] <= df.index[-1] + pd.Timedelta(minutes=bar_minutes))]
    forventet = ((plan["close"] - plan["open"]) / pd.Timedelta(minutes=1)).round() \
        .astype(int) // bar_minutes
    dag = _et_dato(df.index[sessions.rth_mask(df.index, bar_minutes)])
    til_stede = pd.Series(1, index=dag).groupby(level=0).sum() \
        .reindex(plan.index, fill_value=0)
    d = pd.DataFrame({"forventet": forventet, "til_stede": til_stede})
    d["mangler"] = (d["forventet"] - d["til_stede"]).clip(lower=0)
    g = d.groupby(d.index.year)
    ud = pd.DataFrame({
        "sessioner": g.size(),
        "forventede_barer": g["forventet"].sum(),
        "manglende_barer": g["mangler"].sum(),
        "sessioner_med_huller": g["mangler"].agg(lambda x: int((x > 0).sum())),
        "sessioner_uden_data": g["til_stede"].agg(lambda x: int((x == 0).sum())),
    })
    ud.index = ud.index.astype(str)
    total = ud.sum().to_frame("hele").T
    ud = pd.concat([ud, total])
    ud["mangler_pct"] = ud["manglende_barer"] / ud["forventede_barer"] * 100
    ud.index.name = "aar"
    return ud


# ---------------------------------------------------------------------------
# K4 — degeneration
# ---------------------------------------------------------------------------

def k4_flade(series: dict[tuple[int, str], pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for (m, s), df in series.items():
        flad = (df["high"] == df["low"]).to_numpy()
        pct = float(100 * flad.mean()) if len(flad) else float("nan")
        rows.append({"timeframe": f"{m}m", "session": s, "barer": int(len(flad)),
                     "flade": int(flad.sum()), "flade_pct": pct, "holder": bool(pct < K4_PCT)})
    return pd.DataFrame(rows)


def flade_pr_aar(df: pd.DataFrame) -> pd.Series:
    flad = (df["high"] == df["low"]).astype(float)
    return flad.groupby(df.index.tz_convert(ET).year).mean() * 100


# ---------------------------------------------------------------------------
# K2 — to kilder
# ---------------------------------------------------------------------------

def daglige_ranges(df: pd.DataFrame, bar_minutes: int, session: str) -> pd.DataFrame:
    if session == sessions.RTH:
        d = df[sessions.rth_mask(df.index, bar_minutes)]
        dag = _et_dato(d.index)
    else:
        d, dag = df, sessions.globex_day(df.index)
    g = d.groupby(dag)
    return pd.DataFrame({"high": g["high"].max(), "low": g["low"].min(),
                         "close": g["close"].last(), "n": g["open"].size()})


def k2_ranges(yahoo: pd.DataFrame, databento: pd.DataFrame, bar_minutes: int,
              session: str) -> tuple[pd.DataFrame, dict]:
    start = max(yahoo.index[0], databento.index[0])
    slut = min(yahoo.index[-1], databento.index[-1])
    y = yahoo[(yahoo.index >= start) & (yahoo.index <= slut)]
    d = databento[(databento.index >= start) & (databento.index <= slut)]
    j = daglige_ranges(y, bar_minutes, session).join(
        daglige_ranges(d, bar_minutes, session), lsuffix="_yahoo", rsuffix="_databento",
        how="inner").iloc[1:-1].copy()
    j["range_yahoo"] = j["high_yahoo"] - j["low_yahoo"]
    j["range_databento"] = j["high_databento"] - j["low_databento"]
    j["afv_pct"] = (j["range_yahoo"] - j["range_databento"]).abs() / j["range_databento"] * 100
    j["niveau_diff_point"] = j["close_yahoo"] - j["close_databento"]
    j["brugt"] = ((j["n_yahoo"] >= 0.9 * j["n_databento"])
                  & (j["n_databento"] >= 0.9 * j["n_yahoo"]))
    u = j[j["brugt"]]
    med = float(u["afv_pct"].median()) if len(u) else float("nan")
    return j, {
        "session": session, "dage_i_overlap": int(len(j)), "dage_brugt": int(len(u)),
        "median_abs_afv_pct": med,
        "p90_abs_afv_pct": float(u["afv_pct"].quantile(0.9)) if len(u) else float("nan"),
        "max_abs_afv_pct": float(u["afv_pct"].max()) if len(u) else float("nan"),
        "median_range_databento_point": float(u["range_databento"].median()) if len(u)
        else float("nan"),
        "holder": bool(med < K2_PCT),
    }


def bar_for_bar(yahoo: pd.DataFrame, databento: pd.DataFrame, dag: str,
                bar_minutes: int) -> tuple[pd.DataFrame, dict]:
    def rth_dag(df):
        d = df[sessions.rth_mask(df.index, bar_minutes)]
        return d[_et_dato(d.index) == pd.Timestamp(dag)]

    y, d = rth_dag(yahoo), rth_dag(databento)
    j = y[list(OHLC)].join(d[list(OHLC)], lsuffix="_yahoo", rsuffix="_databento",
                           how="outer")
    for f in OHLC:
        j[f"{f}_diff_ticks"] = (j[f"{f}_yahoo"] - j[f"{f}_databento"]) / TICK
    j.index = j.index.tz_convert(ET)
    niveau = float(j["close_diff_ticks"].median()) if len(j) else float("nan")
    begge = j[[f"{f}_diff_ticks" for f in OHLC]].notna().all(axis=1)
    return j, {
        "dag": dag, "timeframe": f"{bar_minutes}m", "barer_yahoo": int(len(y)),
        "barer_databento": int(len(d)), "barer_begge": int(begge.sum()),
        "niveauforskel_ticks_median": niveau,
        "median_abs_diff_ticks_efter_niveau": {
            f: float((j.loc[begge, f"{f}_diff_ticks"] - niveau).abs().median()) for f in OHLC},
        "range_yahoo_point": float(y["high"].max() - y["low"].min()) if len(y) else None,
        "range_databento_point": float(d["high"].max() - d["low"].min()) if len(d) else None,
    }


def _spearman(a: pd.Series, b: pd.Series) -> float:
    """Pearson på gennemsnitsrange — samme definition som ``research.stats.spearman``.

    Vektoriseret, fordi den her køres 181 gange på ~25.000 punkter og apparatets
    rangering løkker i Python. scipy er ikke en afhængighed i repoet.
    """
    if len(a) < 3:
        return float("nan")
    ra = a.rank(method="average").to_numpy()
    rb = b.rank(method="average").to_numpy()
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def forskydning(yahoo_1m: pd.DataFrame, databento_1m: pd.DataFrame,
                max_min: int = 90) -> pd.DataFrame:
    """Spearman-korrelation af 1m-afkast ved tidsforskydning af Databento-serien."""
    ry = np.log(yahoo_1m["close"]).diff().where(~sessions.break_mask(yahoo_1m, 1))
    rd = np.log(databento_1m["close"]).diff().where(~sessions.break_mask(databento_1m, 1))
    rows = []
    for k in range(-max_min, max_min + 1):
        s = rd.copy()
        s.index = s.index + pd.Timedelta(minutes=k)
        j = pd.concat([ry.rename("y"), s.rename("d")], axis=1, join="inner").dropna()
        rows.append({"forskydning_min": k, "n": int(len(j)),
                     "spearman": _spearman(j["y"], j["d"])})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Ruller og spring
# ---------------------------------------------------------------------------

def ruller(df: pd.DataFrame) -> pd.DataFrame:
    iid = df["instrument_id"].to_numpy()
    i = np.flatnonzero(iid[1:] != iid[:-1]) + 1
    t = df.index
    return pd.DataFrame({
        "tid_et": t[i].tz_convert(ET),
        "fra_instrument_id": iid[i - 1], "til_instrument_id": iid[i],
        "spring_ticks": (df["open"].to_numpy()[i] - df["close"].to_numpy()[i - 1]) / TICK,
        "minutter_siden_forrige_bar": ((t[i] - t[i - 1]) / pd.Timedelta(minutes=1)),
    })


def uforklarede_spring(df: pd.DataFrame, top: int = 10) -> tuple[pd.DataFrame, pd.DataFrame]:
    brud = sessions.break_mask(df, 1)
    atr = wilder(true_range(df, brud)).shift(1)
    gap = (df["open"] - df["close"].shift(1)).abs()
    flag = pd.Series((~brud) & (gap >= atr).to_numpy(), index=df.index)
    aar = df.index.tz_convert(ET).year
    pr_aar = pd.DataFrame({"barer": flag.groupby(aar).size(), "spring": flag.groupby(aar).sum()})
    pr_aar["spring_pr_100k_barer"] = pr_aar["spring"] / pr_aar["barer"] * 1e5
    f = pd.DataFrame({"tid_et": df.index.tz_convert(ET), "gap_ticks": gap / TICK,
                      "atr_ticks": atr / TICK})[flag.to_numpy()]
    f["gap_i_atr"] = f["gap_ticks"] / f["atr_ticks"]
    return pr_aar, f.sort_values("gap_i_atr", ascending=False).head(top)


# ---------------------------------------------------------------------------
# Spread
# ---------------------------------------------------------------------------

def _spread_stats(x: pd.Series) -> pd.Series:
    return pd.Series({"n": len(x), "gns_ticks": x.mean(), "p10_ticks": x.quantile(0.1),
                      "p50_ticks": x.quantile(0.5), "p90_ticks": x.quantile(0.9),
                      "andel_1_tick_pct": (x == 1).mean() * 100})


def spread(bbo: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    start = bbo.index.floor("1min") - pd.Timedelta(minutes=1)
    ticks = ((bbo["ask"] - bbo["bid"]) / TICK).to_numpy()
    gyldig = (bbo["bid"].to_numpy() > 0) & (bbo["ask"].to_numpy() > 0) & (ticks > 0)
    ses = np.where(sessions.rth_mask(start, 1), sessions.RTH, sessions.ETH)
    blok = start.tz_convert(ET).tz_localize(None).floor("30min").strftime("%H:%M")
    df = pd.DataFrame({"ticks": ticks, "session": ses, "blok": blok}, index=bbo.index)
    g = df[gyldig]
    pr_session = g.groupby("session")["ticks"].apply(_spread_stats).unstack()
    pr_blok = g.groupby(["session", "blok"])["ticks"].apply(_spread_stats).unstack()
    meta = {"snapshots": int(len(df)), "udeladt_laast_krydset_tom": int((~gyldig).sum()),
            "foerste_et": str(bbo.index[0].tz_convert(ET)),
            "sidste_et": str(bbo.index[-1].tz_convert(ET))}
    return pr_session, pr_blok, meta


# ---------------------------------------------------------------------------
# Kørsel
# ---------------------------------------------------------------------------

def _records(df: pd.DataFrame) -> list[dict]:
    return json.loads(df.reset_index().to_json(orient="records", date_format="iso"))


def yahoo_del(snapshot: str) -> tuple[dict, dict[str, pd.DataFrame]]:
    from research.fase1_data import yahoo_paths

    p = yahoo_paths(snapshot)
    y = {iv: read_ohlcv(p[iv]) for iv in ("1m", "5m", "15m")}
    series = {}
    for iv, m in (("1m", 1), ("5m", 5), ("15m", 15)):
        series[(m, sessions.RTH)] = y[iv][sessions.rth_mask(y[iv].index, m)]
        series[(m, DOEGN)] = y[iv]
    res = {"snapshot": snapshot,
           "k3": {iv: _records(k3_rth_daekning(y[iv], m).loc[["hele"]])
                  for iv, m in (("1m", 1), ("5m", 5), ("15m", 15))},
           "k4": _records(k4_flade(series))}
    return res, y


def main() -> None:
    from research.fase1_data import MNQ, NQ, latest_yahoo_snapshot, load_databento

    ap = argparse.ArgumentParser()
    ap.add_argument("--kun-yahoo", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)

    res: dict = {"koert_utc": pd.Timestamp.now("UTC").isoformat()}
    res["yahoo"], y = yahoo_del(latest_yahoo_snapshot())
    print("YAHOO K3 (hele):", json.dumps(res["yahoo"]["k3"], ensure_ascii=False))
    print(pd.DataFrame(res["yahoo"]["k4"]).to_string(index=False))

    if not args.kun_yahoo:
        nq = load_databento(NQ, "ohlcv-1m")
        series = session_series(nq)
        res["k1"] = k1_dybde(nq)
        k3 = k3_rth_daekning(nq, 1)
        res["k3"] = _records(k3)
        k4 = k4_flade(series)
        res["k4"] = _records(k4)
        res["k4_1m_doegn_pr_aar_pct"] = flade_pr_aar(series[(1, DOEGN)]).round(3).to_dict()

        d15, d1 = series[(15, DOEGN)], series[(1, DOEGN)]
        k2 = []
        for s in (DOEGN, sessions.RTH):
            dage, summ = k2_ranges(y["15m"], d15, 15, s)
            k2.append(summ)
            dage.to_csv(OUT / f"fase1_k2_dage_{'RTH' if s == sessions.RTH else 'doegn'}.csv")
        res["k2"] = k2
        bb15, res["bar_for_bar_15m"] = bar_for_bar(y["15m"], d15, BAR_DAG, 15)
        bb1, res["bar_for_bar_1m"] = bar_for_bar(y["1m"], d1, BAR_DAG, 1)
        bb15.to_csv(OUT / "fase1_bar_for_bar_15m.csv")
        fs = forskydning(y["1m"], d1)
        top = fs.loc[fs["spearman"].idxmax()]
        res["forskydning"] = {"top_min": int(top["forskydning_min"]),
                              "spearman_top": float(top["spearman"]),
                              "spearman_0": float(fs.loc[fs["forskydning_min"] == 0,
                                                         "spearman"].iloc[0])}
        vindue = d15[d15.index >= y["15m"].index[0]]
        yv = y["15m"][y["15m"].index <= d15.index[-1]]
        res["atr_60d_15m"] = {
            kilde: {s: fordeling(atr_pct(df[sessions.rth_mask(df.index, 15)]
                                         if s == sessions.RTH else df, 15), 1.0, 1.0)["ATR_pct_p50"]
                    for s in (sessions.RTH, DOEGN)}
            for kilde, df in (("yahoo", yv), ("databento", vindue))}

        rl = ruller(nq)
        rl.to_csv(OUT / "fase1_ruller.csv", index=False)
        res["ruller"] = {"antal": int(len(rl)),
                         "pr_aar": rl.groupby(rl["tid_et"].dt.year).size().to_dict(),
                         "median_abs_spring_ticks": float(rl["spring_ticks"].abs().median())
                         if len(rl) else None}
        sp_aar, sp_top = uforklarede_spring(nq)
        res["uforklarede_spring"] = {"pr_aar": _records(sp_aar), "stoerste": _records(sp_top)}

        print(json.dumps({k: res[k] for k in ("k1", "k2", "forskydning", "atr_60d_15m",
                                              "ruller")}, indent=1, default=str,
                         ensure_ascii=False))
        print(k3.to_string())
        print(k4.to_string(index=False))
        try:
            bbo = load_databento(MNQ, "bbo-1m")
        except FileNotFoundError as e:
            print("spread springes over:", e)
        else:
            ps, pb, meta = spread(bbo)
            res["spread"] = {"meta": meta, "pr_session": _records(ps)}
            pb.to_csv(OUT / "fase1_spread_mnq_pr_blok.csv")
            print(ps.to_string())

    navn = "fase1_verifikation_yahoo.json" if args.kun_yahoo else "fase1_verifikation.json"
    (OUT / navn).write_text(json.dumps(res, indent=1, default=str, ensure_ascii=False),
                            encoding="utf-8")
    print(f"skrev {OUT / navn}")


if __name__ == "__main__":
    main()
