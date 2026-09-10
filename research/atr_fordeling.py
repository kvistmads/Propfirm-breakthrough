"""ATR-fordelingen pr. timeframe og session — fase 1's egentlige resultat (B2).

Hele §5 i STRATEGI_PROPFIRM.md står på ATR_15m = 0,168% målt over 60 dage. Her måles
fordelingen over hele Databento-historikken, pr. timeframe og session, og regnes om til
det sizingen skal bruge.

    .venv/bin/python -m research.atr_fordeling

## Metode — præregistreret 2026-09-11, før kørslen på Databento-data

    serie        NQ.v.0 1m (Databento GLBX.MDP3). 3m/5m/15m aggregeres fra den.
    session      RTH  = barer helt inde i NYSE's ordinære session, lagt efter hinanden.
                 døgn = alle barer.
    true range   max(H−L, |H−C₋₁|, |L−C₋₁|), men C₋₁ bruges ikke over et brud
                 (data.sessions.break_mask): ≥ 60 min fra forrige bars slut, eller en
                 rulle. Dér er TR = H−L. Et rullespring er kalenderspread, og et
                 overnatningshul er ikke barens støj — begge ville ligne volatilitet.
    ATR          Wilder, 14 barer — samme udglatning som data/indicators.calculate_atr.
    ATR_pct      ATR / close × 100 på hver bar. Fordelingen er over barer.
    percentiler  10/50/90, lineær interpolation.

    R_usd                        ATR_pct/100 × NQ-niveau × $2   (1 MNQ, 1-ATR-stop)
    risiko_pct_af_MLL_brutto     R_usd / $2.000 × 100
    risiko_pct_af_MLL_netto      (R_usd + omk) / $2.000 × 100
    omk_R_netto                  omk / R_usd
    be_WR_pct_netto              research.stats.breakeven_win_rate(2, 1, omk_R) × 100

    omk = $2,47 pr. rundtur, afledt af config.yaml via backtest.costs.
    NQ-niveau = seneste RTH-luk i serien. ATR_pct er prisuafhængig, så også årene
    regnes om ved DAGENS niveau og kan sammenlignes i nutidige dollar.

**Hver percentil er percentilen af sin EGEN kolonne**, beregnet bar for bar. Risiko
stiger med ATR, så dens p90 falder sammen med ATR's p90. Omkostning i R falder med ATR,
så omk_R_netto_p90 og be_WR_pct_netto_p90 falder sammen med ATR's p10. p90 er dermed
altid den ende hvor det gør ondt — estimat-invarianten.

**Go/no-go vurderes på p90** (metoderegel 11).

Følsomhed på 15m — rapporteres, afgør intet: ATR uden brudhåndtering
(``calculate_atr`` direkte på den kontinuerlige serie), og RTH med natten i true range.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backtest import costs  # noqa: E402
from data import resample, sessions  # noqa: E402
from research.stats import breakeven_win_rate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "output"

MNQ_USD_PR_POINT = 2.0
MLL_USD = 2_000.0
RR = 2.0
ATR_LEN = 14
BASIS_15M_PCT = 0.168          # §5b: 60 dage, Yahoo
DOEGN = "døgn"
SESSIONS = (sessions.RTH, DOEGN)


def omk_usd_rundtur(config: dict | None = None, price: float = 30_000.0) -> float:
    """Rundturen i USD for 1 MNQ, afledt af backtest.costs — ikke hardkodet."""
    if config is None:
        config = yaml.safe_load((ROOT / "config.yaml").read_text())
    params = costs._asset_costs(config, "MNQ")
    spread, slip_mean, _, commission = costs.cost_fractions(params, price)
    notional = float(params["contract_multiplier"]) * price
    return (spread + 2 * slip_mean + commission) * notional


# ---------------------------------------------------------------------------
# ATR
# ---------------------------------------------------------------------------

def true_range(df: pd.DataFrame, brud: np.ndarray) -> pd.Series:
    """True range hvor forrige luk ignoreres over et brud — dér er TR = H−L."""
    pc = df["close"].shift(1).where(~np.asarray(brud, dtype=bool))
    h, l = df["high"], df["low"]
    return pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)


def wilder(tr: pd.Series, n: int = ATR_LEN) -> pd.Series:
    return tr.ewm(alpha=1 / n, min_periods=n, adjust=False).mean()


def atr_pct(df: pd.DataFrame, bar_minutes: int,
            brud: np.ndarray | None = None) -> pd.Series:
    if brud is None:
        brud = sessions.break_mask(df, bar_minutes)
    return (wilder(true_range(df, brud)) / df["close"] * 100).rename("ATR_pct")


def session_series(df_1m: pd.DataFrame) -> dict[tuple[int, str], pd.DataFrame]:
    """(timeframe, session) → barer. RTH-serien er RTH-barerne alene."""
    out = {}
    for m in resample.TIMEFRAMES:
        bars = resample.aggregate(df_1m, m)
        out[(m, sessions.RTH)] = bars[sessions.rth_mask(bars.index, m)]
        out[(m, DOEGN)] = bars
    return out


def nq_niveau(df_1m: pd.DataFrame) -> tuple[float, pd.Timestamp]:
    """Seneste RTH-luk og tidspunktet for baren."""
    rth = df_1m[sessions.rth_mask(df_1m.index, 1)]
    return float(rth["close"].iloc[-1]), rth.index[-1]


# ---------------------------------------------------------------------------
# Fordelingen
# ---------------------------------------------------------------------------

def fordeling(atr: pd.Series, niveau: float, omk: float) -> dict:
    """Én tabelrække. Hver percentil tages af sin egen kolonne, bar for bar."""
    a = atr.dropna().to_numpy(dtype=float)
    nul = int((a <= 0).sum())
    a = a[a > 0]
    row: dict = {"n_barer": int(len(a)), "n_barer_ATR_nul": nul}
    if len(a) == 0:
        return row
    r = a / 100 * niveau * MNQ_USD_PR_POINT
    kolonner = {
        "ATR_pct": (a, (10, 50, 90)),
        "R_usd": (r, (10, 50, 90)),
        "risiko_pct_af_MLL_brutto": (r / MLL_USD * 100, (50, 90)),
        "risiko_pct_af_MLL_netto": ((r + omk) / MLL_USD * 100, (50, 90)),
        "omk_R_netto": (omk / r, (50, 90)),
    }
    for navn, (x, ps) in kolonner.items():
        for p in ps:
            row[f"{navn}_p{p}"] = float(np.percentile(x, p))
    row["be_WR_pct_brutto"] = 100 * breakeven_win_rate(RR, 1.0, 0.0)
    # be_WR er affin og stigende i omk_R, så percentilen af be_WR ER be_WR af percentilen.
    for p in (50, 90):
        row[f"be_WR_pct_netto_p{p}"] = 100 * breakeven_win_rate(RR, 1.0, row[f"omk_R_netto_p{p}"])
    return row


def tabel(series: dict[tuple[int, str], pd.DataFrame], niveau: float,
          omk: float) -> pd.DataFrame:
    """Hele perioden og pr. år (ET-kalenderår). ATR regnes på hele serien før opdeling."""
    rows = []
    for (m, s), df in series.items():
        atr = atr_pct(df, m)
        base = {"timeframe": f"{m}m", "session": s}
        rows.append({"periode": "hele", **base, **fordeling(atr, niveau, omk)})
        aar = atr.index.tz_convert(sessions.ET).year
        for y, g in atr.groupby(aar):
            rows.append({"periode": str(y), **base, **fordeling(g, niveau, omk)})
    ud = pd.DataFrame(rows)
    ud["_s"] = ud["session"].map({sessions.RTH: 0, DOEGN: 1})
    ud["_m"] = ud["timeframe"].str.rstrip("m").astype(int)
    ud["_p"] = ud["periode"].map(lambda p: "0" if p == "hele" else p)
    return ud.sort_values(["_p", "_s", "_m"]).drop(columns=["_s", "_m", "_p"]) \
             .reset_index(drop=True)


def sqrt_sammenligning(hele: pd.DataFrame) -> pd.DataFrame:
    """Målt mod §5b's kvadratrods-skalerede tabel — i niveau og i form."""
    rows = []
    for s in SESSIONS:
        sub = hele[hele["session"] == s].set_index("timeframe")
        if "15m" not in sub.index:
            continue
        base = sub.loc["15m", "ATR_pct_p50"]
        for m in resample.TIMEFRAMES:
            maalt = sub.loc[f"{m}m", "ATR_pct_p50"]
            skaleret = BASIS_15M_PCT * math.sqrt(m / 15)
            rows.append({
                "timeframe": f"{m}m", "session": s,
                "ATR_pct_p50_maalt": maalt,
                "ATR_pct_5b_kvadratrod": skaleret,
                "afvigelse_mod_5b_pct": (maalt / skaleret - 1) * 100,
                "forhold_til_15m_maalt": maalt / base,
                "forhold_til_15m_kvadratrod": math.sqrt(m / 15),
                "formafvigelse_pct": (maalt / base / math.sqrt(m / 15) - 1) * 100,
            })
    return pd.DataFrame(rows)


def foelsomhed_15m(series: dict[tuple[int, str], pd.DataFrame], niveau: float,
                   omk: float) -> pd.DataFrame:
    from data.indicators import calculate_atr

    d = series[(15, DOEGN)]
    r = series[(15, sessions.RTH)]
    kun_rulle = np.ones(len(r), dtype=bool)
    if len(r) > 1 and "instrument_id" in r.columns:
        iid = r["instrument_id"].to_numpy()
        kun_rulle[1:] = iid[1:] != iid[:-1]
    elif len(r) > 1:
        kun_rulle[1:] = False
    varianter = [
        ("døgn, præregistreret", atr_pct(d, 15)),
        ("døgn, uden brudhåndtering (calculate_atr)", calculate_atr(d) / d["close"] * 100),
        ("RTH, præregistreret", atr_pct(r, 15)),
        ("RTH, natten med i true range", atr_pct(r, 15, brud=kun_rulle)),
    ]
    return pd.DataFrame([{"variant": v, **fordeling(a, niveau, omk)} for v, a in varianter])


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------

HOVED = ["timeframe", "session", "n_barer", "ATR_pct_p10", "ATR_pct_p50", "ATR_pct_p90",
         "R_usd_p10", "R_usd_p50", "R_usd_p90", "risiko_pct_af_MLL_brutto_p90",
         "risiko_pct_af_MLL_netto_p50", "risiko_pct_af_MLL_netto_p90",
         "omk_R_netto_p50", "omk_R_netto_p90", "be_WR_pct_brutto",
         "be_WR_pct_netto_p50", "be_WR_pct_netto_p90"]
DECIMALER = {"ATR_pct": 4, "omk_R": 4, "forhold": 3, "n_": 0}


def _fmt(col: str, v) -> str:
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    if isinstance(v, (float, np.floating)):
        if not np.isfinite(v):
            return "—"
        nd = next((d for k, d in DECIMALER.items() if col.startswith(k)), 2)
        return f"{v:.{nd}f}"
    return str(v)


def md_tabel(df: pd.DataFrame, cols: list[str]) -> str:
    linjer = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        linjer.append("| " + " | ".join(_fmt(c, r[c]) for c in cols) + " |")
    return "\n".join(linjer) + "\n"


def pivot_aar(tab: pd.DataFrame, kolonne: str, session: str) -> pd.DataFrame:
    p = tab[(tab["periode"] != "hele") & (tab["session"] == session)]
    p = p.pivot(index="periode", columns="timeframe", values=kolonne)
    return p[[f"{m}m" for m in resample.TIMEFRAMES]].reset_index()


def skriv_md(tab: pd.DataFrame, sq: pd.DataFrame, foels: pd.DataFrame, meta: dict) -> str:
    hele = tab[tab["periode"] == "hele"]
    tf_cols = ["periode"] + [f"{m}m" for m in resample.TIMEFRAMES]
    dele = [
        "# ATR-fordeling pr. timeframe og session — NQ\n",
        f"Fase 1, B2. Kørt {meta['koert_utc'][:10]}. Kilde: Databento GLBX.MDP3, "
        f"{meta['symbol']} ohlcv-1m, {meta['foerste_bar_et']} → {meta['sidste_bar_et']} (ET).\n"
        f"NQ-niveau {meta['nq_niveau']:.2f} (RTH-luk {meta['nq_niveau_tid_et']}). "
        f"Omkostning ${meta['omk_usd']:.2f} pr. rundtur. MLL $2.000. RR 2:1.\n",
        "Metoden er præregistreret i `research/atr_fordeling.py` (modulets docstring) før "
        "kørslen. Hver percentil er percentilen af sin egen kolonne: `omk_R_netto_p90` og "
        "`be_WR_pct_netto_p90` hører til ATR's p10, risiko-p90 til ATR's p90. "
        "**p90 er go/no-go-kolonnen.**\n",
        "## Hele perioden\n", md_tabel(hele, HOVED),
        "## Mod §5b's kvadratrods-skalering (p50)\n",
        "`afvigelse_mod_5b_pct` er niveau + form mod tabellen i §5b (basis 0,168%). "
        "`formafvigelse_pct` er formen alene: målt forhold til 15m mod √(T/15).\n",
        md_tabel(sq, list(sq.columns)),
        "## Pr. år — risiko_pct_af_MLL_netto_p90 (go/no-go)\n",
        "### RTH\n", md_tabel(pivot_aar(tab, "risiko_pct_af_MLL_netto_p90", sessions.RTH), tf_cols),
        "### døgn\n", md_tabel(pivot_aar(tab, "risiko_pct_af_MLL_netto_p90", DOEGN), tf_cols),
        "## Pr. år — ATR_pct_p50\n",
        "### RTH\n", md_tabel(pivot_aar(tab, "ATR_pct_p50", sessions.RTH), tf_cols),
        "### døgn\n", md_tabel(pivot_aar(tab, "ATR_pct_p50", DOEGN), tf_cols),
        "## Følsomhed, 15m — afgør intet\n",
        md_tabel(foels, ["variant", "n_barer", "ATR_pct_p10", "ATR_pct_p50", "ATR_pct_p90",
                         "risiko_pct_af_MLL_netto_p90", "omk_R_netto_p90"]),
        "Alle rækker pr. år og session står i `atr_fordeling.csv`.\n",
    ]
    return "\n".join(dele)


def main() -> None:
    from research.fase1_data import NQ, load_databento

    df = load_databento(NQ, "ohlcv-1m")
    niveau, niveau_tid = nq_niveau(df)
    omk = omk_usd_rundtur(price=niveau)
    series = session_series(df)
    tab = tabel(series, niveau, omk)
    sq = sqrt_sammenligning(tab[tab["periode"] == "hele"])
    foels = foelsomhed_15m(series, niveau, omk)
    et = lambda t: t.tz_convert(sessions.ET).strftime("%Y-%m-%d %H:%M")
    meta = {"koert_utc": pd.Timestamp.now("UTC").isoformat(), "symbol": NQ,
            "foerste_bar_et": et(df.index[0]), "sidste_bar_et": et(df.index[-1]),
            "nq_niveau": niveau, "nq_niveau_tid_et": et(niveau_tid), "omk_usd": omk}
    OUT.mkdir(parents=True, exist_ok=True)
    tab.to_csv(OUT / "atr_fordeling.csv", index=False)
    (OUT / "atr_fordeling.md").write_text(skriv_md(tab, sq, foels, meta), encoding="utf-8")
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(tab[tab["periode"] == "hele"][HOVED].to_string(index=False))
        print(sq.to_string(index=False))
        print(foels.to_string(index=False))
    print(f"skrev {OUT / 'atr_fordeling.md'} og .csv")


if __name__ == "__main__":
    main()
