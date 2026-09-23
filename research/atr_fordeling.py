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
(``calculate_atr`` direkte på den kontinuerlige serie), RTH med natten i true range, og
fordelingen uden rullevinduer (barer i de 5 handelsdage før hvert kontraktskift).

Rullevinduet er tilføjet 2026-09-11 efter tjekket af dagsvolumen pr. kontrakt og FØR
NQ-prisdata er hentet: ``.v.0`` skiftede først 1-2 handelsdage efter volumenskiftet ved
rullerne i december 2025, marts 2026 og juni 2026.

## Tilføjet efter første kørsel — rapportering, ikke metode

Tilføjet 2026-09-11 efter ejerens instruks, efter at K3 viste huller i 2010-2015. Metoden
ovenfor er uændret; kun rapporteringen er udvidet:

- Helhistorik-tabellen står uændret. Ved siden af står samme tabel for de år der består
  K3 (< 2% manglende RTH-minutter). Det er go/no-go-grundlaget.
- RTH og døgn side om side i alle tabeller.
- §5b og §5a's risikotabeller genberegnet på den målte fordeling. Kun ATR skiftes;
  NQ-niveauet holdes på §5's 29.639,50, så forskellen alene skyldes målingen.
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
NQ_NIVEAU_5 = 29_639.50        # §5's NQ-niveau, 2026-09-07
DOEGN = "døgn"
SESSIONS = (sessions.RTH, DOEGN)
ROLL_WINDOW_DAYS = 5


def omk_usd_rundtur(config: dict | None = None, price: float = 30_000.0) -> float:
    """Rundturen i USD for 1 MNQ i RTH, afledt af backtest.costs — ikke hardkodet.

    Fase 2: slippage er nu den realiserede middelværdi (0,5417 tick/side), ikke
    parameteren 0,50. Fase 1's tabeller er regnet med den gamle definition og $2,47.
    ``price`` er uden betydning i ``mode: contract`` og bevares for bagudkompatibilitet.
    """
    if config is None:
        config = yaml.safe_load((ROOT / "config.yaml").read_text())
    return costs.rundtur_dekomponering(config, "MNQ", sessions.RTH).i_alt_usd


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


def k3_etiket(aar: list[int]) -> str:
    aar = sorted(aar)
    if not aar:
        return "K3 ingen år"
    if len(aar) == 1:
        return f"K3 {aar[0]}"
    if aar == list(range(aar[0], aar[-1] + 1)):
        return f"K3 {aar[0]}-{aar[-1]}"
    return "K3 " + ",".join(map(str, aar))


def k3_aar(df_1m: pd.DataFrame) -> list[int]:
    """År der består K3: under 2% manglende RTH-minutter (research.fase1_verifikation)."""
    from research.fase1_verifikation import K3_PCT, k3_rth_daekning

    k3 = k3_rth_daekning(df_1m, 1).drop(index="hele")
    return [int(a) for a, r in k3.iterrows() if r["mangler_pct"] < K3_PCT]


def tabel(series: dict[tuple[int, str], pd.DataFrame], niveau: float, omk: float,
          k3: list[int] | None = None) -> pd.DataFrame:
    """Hele perioden, de K3-beståede år samlet, og hvert år (ET-kalenderår).

    ATR regnes på hele serien før opdeling, så opvarmningen aldrig starter forfra.
    """
    rows = []
    for (m, s), df in series.items():
        atr = atr_pct(df, m)
        base = {"timeframe": f"{m}m", "session": s}
        aar = atr.index.tz_convert(sessions.ET).year
        rows.append({"periode": "hele", **base, **fordeling(atr, niveau, omk)})
        if k3:
            rows.append({"periode": k3_etiket(k3), **base,
                         **fordeling(atr[np.isin(aar, k3)], niveau, omk)})
        for y, g in atr.groupby(aar):
            rows.append({"periode": str(y), **base, **fordeling(g, niveau, omk)})
    ud = pd.DataFrame(rows)
    ud["_s"] = ud["session"].map({sessions.RTH: 0, DOEGN: 1})
    ud["_m"] = ud["timeframe"].str.rstrip("m").astype(int)
    ud["_p"] = ud["periode"].map(
        lambda p: "0" if p == "hele" else ("1" if p.startswith("K3") else p))
    return ud.sort_values(["_p", "_s", "_m"]).drop(columns=["_s", "_m", "_p"]) \
             .reset_index(drop=True)


def side_om_side(periode_tab: pd.DataFrame, kolonner: list[str]) -> pd.DataFrame:
    """Én række pr. timeframe; hver kolonne med RTH og døgn ved siden af hinanden."""
    rows = []
    for m in resample.TIMEFRAMES:
        r = {"timeframe": f"{m}m"}
        for k in kolonner:
            for s in SESSIONS:
                x = periode_tab[(periode_tab["timeframe"] == f"{m}m")
                                & (periode_tab["session"] == s)]
                r[f"{k}_{s}"] = x[k].iloc[0] if len(x) else float("nan")
        rows.append(r)
    return pd.DataFrame(rows)


def pivot_aar_side(tab: pd.DataFrame, kolonne: str,
                   k3: list[int] | None = None) -> pd.DataFrame:
    """År som rækker; for hver timeframe RTH og døgn side om side."""
    p = tab[tab["periode"].str.fullmatch(r"\d{4}")]
    p = p.pivot_table(index="periode", columns=["timeframe", "session"], values=kolonne)
    cols = [(f"{m}m", s) for m in resample.TIMEFRAMES for s in SESSIONS]
    p = p.reindex(columns=cols)
    p.columns = [f"{m} {s}" for m, s in cols]
    p = p.reset_index()
    if k3 is not None:
        p.insert(1, "K3", np.where(p["periode"].astype(int).isin(k3), "ja", "nej"))
    return p


def sqrt_sammenligning(periode_tab: pd.DataFrame) -> pd.DataFrame:
    """Målt mod §5b's kvadratrods-skalerede tabel — i niveau og i form."""
    rows = []
    for s in SESSIONS:
        sub = periode_tab[periode_tab["session"] == s].set_index("timeframe")
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


# ---------------------------------------------------------------------------
# §5 genberegnet
# ---------------------------------------------------------------------------

def _r_usd(atr_pct_: float, niveau: float) -> float:
    return atr_pct_ / 100 * niveau * MNQ_USD_PR_POINT


def paragraf5b(periode_tab: pd.DataFrame, omk: float,
               niveau: float = NQ_NIVEAU_5) -> tuple[pd.DataFrame, pd.DataFrame]:
    """§5b's timeframe-tabel: risiko og omkostning. Kun ATR skiftes, niveauet er §5's."""
    risiko = lambda pct: (_r_usd(pct, niveau) + omk) / MLL_USD * 100
    be = lambda omk_r: 100 * breakeven_win_rate(RR, 1.0, omk_r)
    rrows, orows = [], []
    for m in resample.TIMEFRAMES:
        ref = BASIS_15M_PCT * math.sqrt(m / 15)
        x = {s: periode_tab[(periode_tab["timeframe"] == f"{m}m")
                            & (periode_tab["session"] == s)].iloc[0] for s in SESSIONS}
        rr = {"timeframe": f"{m}m", "risiko_pct_af_MLL_netto_5b": risiko(ref)}
        for p in ("p50", "p90"):
            for s in SESSIONS:
                rr[f"risiko_pct_af_MLL_netto_{p}_{s}"] = risiko(x[s][f"ATR_pct_{p}"])
        oo = {"timeframe": f"{m}m", "omk_R_netto_5b": omk / _r_usd(ref, niveau)}
        # omk_R's p90 hører til ATR's p10 — den ende hvor omkostningen gør ondt.
        for p, atr_p in (("p50", "ATR_pct_p50"), ("p90", "ATR_pct_p10")):
            for s in SESSIONS:
                oo[f"omk_R_netto_{p}_{s}"] = omk / _r_usd(x[s][atr_p], niveau)
        oo["be_WR_pct_netto_5b"] = be(oo["omk_R_netto_5b"])
        for s in SESSIONS:
            oo[f"be_WR_pct_netto_p90_{s}"] = be(oo[f"omk_R_netto_p90_{s}"])
        rrows.append(rr)
        orows.append(oo)
    return pd.DataFrame(rrows), pd.DataFrame(orows)


def paragraf5a(periode_tab: pd.DataFrame, omk: float,
               niveau: float = NQ_NIVEAU_5) -> pd.DataFrame:
    """§5a's sizing-gitter på 15m: kontrakter × stop_ATR → risiko i % af MLL."""
    x = {s: periode_tab[(periode_tab["timeframe"] == "15m")
                        & (periode_tab["session"] == s)].iloc[0] for s in SESSIONS}
    rows = []
    for k in (1, 2, 3):
        for stop in (0.50, 0.75, 1.00):
            pct = lambda atr: k * (stop * _r_usd(atr, niveau) + omk) / MLL_USD * 100
            r = {"kontrakter": k, "stop_ATR": stop, "risiko_pct_af_MLL_netto_5a": pct(BASIS_15M_PCT)}
            for p in ("p50", "p90"):
                for s in SESSIONS:
                    r[f"risiko_pct_af_MLL_netto_{p}_{s}"] = pct(x[s][f"ATR_pct_{p}"])
            rows.append(r)
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
        ("døgn, uden rullevinduer (5 handelsdage før skift)",
         atr_pct(d, 15)[~rullevindue_mask(d)]),
        ("RTH, præregistreret", atr_pct(r, 15)),
        ("RTH, natten med i true range", atr_pct(r, 15, brud=kun_rulle)),
        ("RTH, uden rullevinduer (5 handelsdage før skift)",
         atr_pct(r, 15)[~rullevindue_mask(r)]),
    ]
    return pd.DataFrame([{"variant": v, **fordeling(a, niveau, omk)} for v, a in varianter])


def rullevindue_mask(df: pd.DataFrame, dage: int = ROLL_WINDOW_DAYS) -> np.ndarray:
    """True for barer i de ``dage`` Globex-handelsdage der går forud for et kontraktskift.

    ``.v.0`` skifter først 1-2 handelsdage efter at den nye kontrakt har overtaget
    volumenen (dagsvolumen pr. kontrakt ved de tre seneste ruller). I vinduet kan serien
    ligge på den udløbende kontrakt. Dagene tælles i seriens egne handelsdage.
    """
    n = len(df)
    if n < 2 or "instrument_id" not in df.columns:
        return np.zeros(n, dtype=bool)
    dag = sessions.globex_day(df.index)
    iid = df["instrument_id"].to_numpy()
    skift = np.flatnonzero(iid[1:] != iid[:-1]) + 1
    unikke = pd.DatetimeIndex(dag.unique())
    vindue = {unikke[q] for p in unikke.get_indexer(dag[skift])
              for q in range(max(0, p - dage), p)}
    return np.asarray(dag.isin(list(vindue)), dtype=bool)


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------

HOVED = ["timeframe", "session", "n_barer", "ATR_pct_p10", "ATR_pct_p50", "ATR_pct_p90",
         "R_usd_p10", "R_usd_p50", "R_usd_p90", "risiko_pct_af_MLL_brutto_p90",
         "risiko_pct_af_MLL_netto_p50", "risiko_pct_af_MLL_netto_p90",
         "omk_R_netto_p50", "omk_R_netto_p90", "be_WR_pct_brutto",
         "be_WR_pct_netto_p50", "be_WR_pct_netto_p90"]
DECIMALER = {"ATR_pct": 4, "omk_R": 4, "forhold": 3, "n_": 0}


def _fmt(col: str, v, nd: int | None = None) -> str:
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    if isinstance(v, (float, np.floating)):
        if not np.isfinite(v):
            return "—"
        d = nd if nd is not None else next((d for k, d in DECIMALER.items()
                                            if col.startswith(k)), 2)
        return f"{v:.{d}f}"
    return str(v)


def md_tabel(df: pd.DataFrame, cols: list[str], nd: int | None = None) -> str:
    linjer = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        linjer.append("| " + " | ".join(_fmt(c, r[c], nd) for c in cols) + " |")
    return "\n".join(linjer) + "\n"


def noegletal(tab: pd.DataFrame, etiket: str, p5b_r: pd.DataFrame) -> list[str]:
    k = tab[tab["periode"] == etiket]
    g = lambda tf, s, c: float(k[(k["timeframe"] == tf) & (k["session"] == s)][c].iloc[0])
    r50, r90 = g("15m", sessions.RTH, "ATR_pct_p50"), g("15m", sessions.RTH, "ATR_pct_p90")
    d50, d90 = g("15m", DOEGN, "ATR_pct_p50"), g("15m", DOEGN, "ATR_pct_p90")
    b = p5b_r.set_index("timeframe").loc["15m"]
    return [
        f"- **15m, {etiket}:** RTH p50 {r50:.3f}% og p90 {r90:.3f}%; døgn p50 {d50:.3f}% og "
        f"p90 {d90:.3f}%. RTH ligger {100 * (r50 / d50 - 1):.0f}% over døgn på medianen og "
        f"{100 * (r90 / d90 - 1):.0f}% på p90.",
        f"- **§5's 0,168%** ligger {100 * (BASIS_15M_PCT / d50 - 1):+.0f}% fra døgnseriens "
        f"p50 og {100 * (BASIS_15M_PCT / r50 - 1):+.0f}% fra RTH-seriens p50.",
        f"- **1 MNQ, 1-ATR-stop, 15m, ved §5's NQ-niveau:** §5 regnede "
        f"{b['risiko_pct_af_MLL_netto_5b']:.2f}% af MLL. Målt RTH: "
        f"{b[f'risiko_pct_af_MLL_netto_p50_{sessions.RTH}']:.2f}% på p50 og "
        f"{b[f'risiko_pct_af_MLL_netto_p90_{sessions.RTH}']:.2f}% på p90. Målt døgn: "
        f"{b[f'risiko_pct_af_MLL_netto_p50_{DOEGN}']:.2f}% og "
        f"{b[f'risiko_pct_af_MLL_netto_p90_{DOEGN}']:.2f}%.",
    ]


def skriv_md(tab: pd.DataFrame, sq: pd.DataFrame, foels: pd.DataFrame,
             p5b_r: pd.DataFrame, p5b_o: pd.DataFrame, p5a: pd.DataFrame, meta: dict,
             k3: list[int], etiket: str) -> str:
    hele = tab[tab["periode"] == "hele"]
    k3tab = tab[tab["periode"] == etiket]
    aar_cols = ["periode", "K3"] + [f"{m}m {s}" for m in resample.TIMEFRAMES for s in SESSIONS]
    sos = lambda cols: (lambda d: md_tabel(d, list(d.columns)))(side_om_side(k3tab, cols))
    dele = [
        "# ATR-fordeling pr. timeframe og session — NQ\n",
        f"Fase 1, B2. Kørt {meta['koert_utc'][:10]}. Kilde: Databento GLBX.MDP3, "
        f"{meta['symbol']} ohlcv-1m, {meta['foerste_bar_et']} → {meta['sidste_bar_et']} (ET). "
        f"NQ-niveau {meta['nq_niveau']:.2f} (RTH-luk {meta['nq_niveau_tid_et']}). "
        f"Omkostning ${meta['omk_usd']:.2f} pr. rundtur. MLL $2.000. RR 2:1.\n",
        "Metoden er præregistreret i `research/atr_fordeling.py` (modulets docstring) før "
        "kørslen. Hver percentil er percentilen af sin egen kolonne: `omk_R_netto_p90` og "
        "`be_WR_pct_netto_p90` hører til ATR's p10, risiko-p90 til ATR's p90. "
        "**p90 er go/no-go-kolonnen.**\n",
        "## Nøgletal\n", "\n".join(noegletal(tab, etiket, p5b_r)) + "\n",
        f"## Go/no-go: {etiket} — RTH og døgn side om side\n",
        f"År der består K3 (< 2% manglende RTH-minutter; se `datakilder.md`): "
        f"{', '.join(map(str, k3))}. NQ-niveau {meta['nq_niveau']:.2f}.\n",
        "### ATR\n", sos(["ATR_pct_p10", "ATR_pct_p50", "ATR_pct_p90"]),
        "### R og risiko, 1 MNQ, 1-ATR-stop\n",
        sos(["R_usd_p50", "R_usd_p90", "risiko_pct_af_MLL_brutto_p90",
             "risiko_pct_af_MLL_netto_p50", "risiko_pct_af_MLL_netto_p90"]),
        "### Omkostning i R og break-even ved 2:1 (brutto er 33,33 i alle celler)\n",
        sos(["omk_R_netto_p50", "omk_R_netto_p90", "be_WR_pct_netto_p50",
             "be_WR_pct_netto_p90"]),
        "## Hele perioden (præregistreret, uændret)\n",
        "Indeholder 2010-2015, som ikke består K3.\n", md_tabel(hele, HOVED),
        f"## {etiket} — samme kolonner\n", md_tabel(k3tab, HOVED),
        "## §5 genberegnet på den målte fordeling\n",
        f"Kun ATR er skiftet. NQ-niveauet er holdt på §5's {NQ_NIVEAU_5:.2f}, så forskellen "
        f"alene skyldes målingen. Fordeling: {etiket}. Omkostning ${meta['omk_usd']:.2f} pr. "
        "rundtur. `_5b`/`_5a` er dokumentets tal på 0,168% med kvadratrods-skalering.\n",
        "### §5b — risiko pr. handel, 1 MNQ, 1-ATR-stop\n",
        md_tabel(p5b_r, list(p5b_r.columns)),
        "### §5b — omkostning i R og break-even ved 2:1\n",
        md_tabel(p5b_o, list(p5b_o.columns)),
        "### §5a — sizing-gitteret på 15m\n",
        md_tabel(p5a.astype({"kontrakter": str}), list(p5a.columns)),
        "Ruinsandsynlighederne i §5a er ikke genberegnet. De kræver en ny kørsel af "
        "`research/mll_ruin.py` med et andet ATR-input.\n",
        "## Mod §5b's kvadratrods-skalering (p50)\n",
        "`afvigelse_mod_5b_pct` er niveau + form mod tabellen i §5b (basis 0,168%). "
        "`formafvigelse_pct` er formen alene: målt forhold til 15m mod √(T/15).\n",
        md_tabel(sq, list(sq.columns)),
        "## Pr. år — risiko_pct_af_MLL_netto_p90 (go/no-go), RTH og døgn side om side\n",
        md_tabel(pivot_aar_side(tab, "risiko_pct_af_MLL_netto_p90", k3), aar_cols),
        "## Pr. år — ATR_pct_p50\n",
        md_tabel(pivot_aar_side(tab, "ATR_pct_p50", k3), aar_cols, nd=3),
        "## Pr. år — ATR_pct_p90\n",
        md_tabel(pivot_aar_side(tab, "ATR_pct_p90", k3), aar_cols, nd=3),
        "## Følsomhed, 15m, hele perioden — afgør intet\n",
        md_tabel(foels, ["variant", "n_barer", "ATR_pct_p10", "ATR_pct_p50", "ATR_pct_p90",
                         "risiko_pct_af_MLL_netto_p90", "omk_R_netto_p90"]),
        "Alle rækker pr. periode, timeframe og session står i `atr_fordeling.csv`.\n",
    ]
    return "\n".join(dele)


def main() -> None:
    from research.fase1_data import NQ, load_databento

    df = load_databento(NQ, "ohlcv-1m")
    niveau, niveau_tid = nq_niveau(df)
    omk = omk_usd_rundtur(price=niveau)
    k3 = k3_aar(df)
    etiket = k3_etiket(k3)
    series = session_series(df)
    tab = tabel(series, niveau, omk, k3)
    k3tab = tab[tab["periode"] == etiket]
    sq = pd.concat([sqrt_sammenligning(tab[tab["periode"] == p]).assign(periode=p)
                    for p in ("hele", etiket)], ignore_index=True)
    sq = sq[["periode"] + [c for c in sq.columns if c != "periode"]]
    foels = foelsomhed_15m(series, niveau, omk)
    p5b_r, p5b_o = paragraf5b(k3tab, omk)
    p5a = paragraf5a(k3tab, omk)
    et = lambda t: t.tz_convert(sessions.ET).strftime("%Y-%m-%d %H:%M")
    meta = {"koert_utc": pd.Timestamp.now("UTC").isoformat(), "symbol": NQ,
            "foerste_bar_et": et(df.index[0]), "sidste_bar_et": et(df.index[-1]),
            "nq_niveau": niveau, "nq_niveau_tid_et": et(niveau_tid), "omk_usd": omk}
    OUT.mkdir(parents=True, exist_ok=True)
    tab.to_csv(OUT / "atr_fordeling.csv", index=False)
    p5b_r.merge(p5b_o, on="timeframe").to_csv(OUT / "atr_paragraf5b_genberegnet.csv",
                                              index=False)
    p5a.to_csv(OUT / "atr_paragraf5a_genberegnet.csv", index=False)
    (OUT / "atr_fordeling.md").write_text(
        skriv_md(tab, sq, foels, p5b_r, p5b_o, p5a, meta, k3, etiket), encoding="utf-8")
    with pd.option_context("display.width", 250, "display.max_columns", 40):
        print("K3-beståede år:", k3)
        print(k3tab[HOVED].to_string(index=False))
        print(p5b_r.to_string(index=False))
        print(p5b_o.to_string(index=False))
        print(p5a.to_string(index=False))
        print("\n".join(noegletal(tab, etiket, p5b_r)))
    print(f"skrev {OUT / 'atr_fordeling.md'} og .csv")


if __name__ == "__main__":
    main()
