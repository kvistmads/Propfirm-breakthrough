"""B4 kandidat 1 — signaloptællingen: hvor mange handelsdage har mindst ét signal fra kernen?

Præregistreret i ``research/prereg/b4_k1_optaelling.md``. Implementeringsdetaljerne står i
``research/prereg/b4_k1_optaelling_tillaeg.md``. Begge er committet før kørslen, og
kørslen nægter at starte hvis de, eller denne fil, ikke er committet og uændrede.

    .venv/bin/python -m research.b4_k1_optaelling

**Kørslen ser ikke på udfald.** Hver zone får et forløb — dannet, og derefter berørt, død
ved kontraktskift eller åben ved seriens slut — og intet andet. Der læses ingen pris efter
berøringslyset, og af berøringslyset kun den kant der afgør berøringen. Derfor lægger
kørslen intet til tælleren for den deflaterede tærskel.

Pris hentes kun gennem ``data.holdout.load_in_sample``. Holdout-perioden åbnes ikke.

## Definitionerne, præregistreringen §3

    basis, udbrud   to nabolys i 15m-døgnserien. Demand: basis close < open og udbrud
                    close > basis high. Supply: basis close > open og udbrud close <
                    basis low. close = open er hverken rødt eller grønt.
    zone            basislysets high til low, væger med. Gyldig fra udbrudslysets lukning.
    berøring        første lys efter udbrudslyset med demand: low ≤ zonens high,
                    supply: high ≥ zonens low. Zonen dør, uanset tidspunkt.
    kontraktskift   første lys efter basislyset med et andet instrument_id. Zonen dør dér
                    uden berøring, og lyset vurderes ikke som berøring.
    signal          en berøring hvor lysets åbningstid ligger i 08:30 ≤ t < 14:30 CT på en
                    RTH-dag og før RTH-luk − 30 min (halve dage: 11:30 CT), og zonehøjden
                    er ≤ 0,429% af basislysets close.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data import holdout, resample, sessions  # noqa: E402
from research.stats import breakeven_win_rate, wilson_interval  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "output"
PREREG = ROOT / "research" / "prereg" / "b4_k1_optaelling.md"
TILLAEG = ROOT / "research" / "prereg" / "b4_k1_optaelling_tillaeg.md"
# Kørslen sker kun når disse er committet og uændrede.
COMMITTEDE = (
    Path(__file__).resolve(), ROOT / "tests" / "test_b4_k1_optaelling.py", PREREG, TILLAEG,
    ROOT / "data" / "holdout.py", ROOT / "data" / "resample.py",
    ROOT / "data" / "sessions.py", ROOT / "research" / "stats.py",
)

SYMBOL = "NQ.v.0"
BAR_MIN = 15
BAR = pd.Timedelta(minutes=BAR_MIN)
CT = "America/Chicago"
VINDUE_CT = (8 * 60 + 30, 14 * 60 + 30)    # minutter efter midnat CT, [start, slut)
LUK_MARGIN = pd.Timedelta(minutes=30)       # vinduet slutter 30 min før RTH lukker
STOPLOFT_PCT = 0.429
NQ_NIVEAU = 29_138.0
RISIKO_USD = 250.0
MNQ_USD_PR_POINT = 2.0
OMK_USD_RUNDTUR = 2.627                     # pr. kontrakt, RTH — fase 2
RR = 2.0

DEMAND, SUPPLY, ALLE = "demand", "supply", "alle"
BEROERT, KONTRAKTSKIFT, AABEN = "beroert", "kontraktskift", "aaben"
ZONEKOLONNER = ["side", "basis_i", "udbrud_i", "basis_tid", "udbrud_tid", "zone_high",
                "zone_low", "basis_close", "hoejde_pct", "over_hul", "status", "slut_i",
                "slut_tid"]
# §5: dage_med_signal_n. Kategorien er den laveste som konfidensintervallet rører.
KATEGORIER = ((590, "≥ 590: testbar, også med filtersøgning — edge-testen præregistreres"),
              (390, "390-589: kernen alene er testbar — kun kernen testes"),
              (0, "< 390: for få handler — kandidaten parkeres"))


# ---------------------------------------------------------------------------
# Zoner
# ---------------------------------------------------------------------------

def find_zoner(bars: pd.DataFrame) -> pd.DataFrame:
    """Alle zoner i 15m-serien, én række pr. zone, og hvordan hver af dem døde.

    ``slut_i`` er positionen af berøringslyset eller skiftelyset, -1 for en zone der
    stadig lever ved seriens slut. Kalenderen indgår ikke her, se ``klassificer``.
    """
    o, h, l, c = (bars[k].to_numpy(dtype=float) for k in ("open", "high", "low", "close"))
    n = len(bars)
    iid = (bars["instrument_id"].to_numpy() if "instrument_id" in bars.columns
           else np.zeros(n, dtype=np.int64))
    basis = np.arange(max(n - 1, 0))
    er_demand = (c[basis] < o[basis]) & (c[basis + 1] > h[basis])
    er_supply = (c[basis] > o[basis]) & (c[basis + 1] < l[basis])
    # Første lys efter i med et andet instrument_id end i's: starten på næste kontraktblok.
    skift = np.flatnonzero(iid[1:] != iid[:-1]) + 1
    naeste_skift = np.r_[skift, n][np.searchsorted(skift, basis, side="right")]

    rows = []
    for b in np.flatnonzero(er_demand | er_supply):
        demand = bool(er_demand[b])
        u, k = b + 1, int(naeste_skift[b])
        if k <= u:
            # Udbrudslyset ligger i en ny kontrakt: zonen dør ved skiftet, før den er gyldig.
            status, slut = KONTRAKTSKIFT, k
        else:
            ramt = l[u + 1:k] <= h[b] if demand else h[u + 1:k] >= l[b]
            if ramt.any():
                status, slut = BEROERT, u + 1 + int(np.argmax(ramt))
            elif k < n:
                status, slut = KONTRAKTSKIFT, k
            else:
                status, slut = AABEN, -1
        rows.append((DEMAND if demand else SUPPLY, b, u, bars.index[b], bars.index[u],
                     h[b], l[b], c[b], (h[b] - l[b]) / c[b] * 100,
                     bool(bars.index[u] - bars.index[b] > BAR), status, slut,
                     bars.index[slut] if slut >= 0 else pd.NaT))
    z = pd.DataFrame(rows, columns=ZONEKOLONNER)
    for kol in ("basis_tid", "udbrud_tid", "slut_tid"):
        z[kol] = pd.to_datetime(z[kol], utc=True)
    return z


# ---------------------------------------------------------------------------
# Kalender og vindue
# ---------------------------------------------------------------------------

def _et_dag(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    return index.tz_convert(sessions.ET).tz_localize(None).normalize().as_unit("ns")


def vindue_mask(index: pd.DatetimeIndex) -> np.ndarray:
    """True for 15m-lys hvis åbningstid ligger i indgangsvinduet på en RTH-dag.

    08:30 ≤ t < 14:30 CT og t < RTH-luk − 30 min, så vinduet på en halv dag slutter
    11:30 CT. ``rth_mask`` kræver desuden at lyset ligger helt i NYSE-sessionen, og den
    fejler hvis serien ligger uden for kalenderens rækkevidde.
    """
    if len(index) == 0:
        return np.zeros(0, dtype=bool)
    rth = sessions.rth_mask(index, BAR_MIN)
    ct = index.tz_convert(CT)
    minut = np.asarray(ct.hour * 60 + ct.minute)
    luk = pd.DatetimeIndex(sessions._xnys().schedule["close"].reindex(_et_dag(index)))
    foer_luk = np.asarray(index < luk - LUK_MARGIN, dtype=bool)   # NaT → False
    return rth & (minut >= VINDUE_CT[0]) & (minut < VINDUE_CT[1]) & foer_luk


def rth_dage(start, slut) -> pd.DatetimeIndex:
    """XNYS-sessionernes datoer fra ``start`` til, men ikke med, ``slut`` (kalenderdatoer)."""
    plan = pd.DatetimeIndex(sessions._xnys().schedule.index).as_unit("ns")
    d0, d1 = pd.Timestamp(pd.Timestamp(start).date()), pd.Timestamp(pd.Timestamp(slut).date())
    if d0 < plan[0] or d1 > plan[-1] + pd.Timedelta(days=1):
        raise ValueError(f"XNYS-kalenderen dækker {plan[0].date()} → {plan[-1].date()}, "
                         f"ikke {d0.date()} → {d1.date()}")
    return plan[(plan >= d0) & (plan < d1)]


# ---------------------------------------------------------------------------
# Signal og sizing
# ---------------------------------------------------------------------------

def sizing(hoejde_pct) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Zonehøjde i point ved NQ 29.138, kontrakter inden for $250 og omkostning i R.

    Stoppet er zonens fjerne kant, så risikoen pr. kontrakt er zonehøjden. Afrundingen
    før floor fjerner flydende tals støj, så 62,5 point giver 2 kontrakter, ikke 1.
    """
    pt = np.asarray(hoejde_pct, dtype=float) / 100 * NQ_NIVEAU
    risiko_usd = pt * MNQ_USD_PR_POINT
    kontrakter = np.floor(np.round(RISIKO_USD / risiko_usd, 9))
    return pt, kontrakter, OMK_USD_RUNDTUR / risiko_usd


def klassificer(bars: pd.DataFrame, zoner: pd.DataFrame) -> pd.DataFrame:
    """Berøringerne holdt op mod vinduet og stoploftet. Én række pr. zone, som i ind."""
    z = zoner.copy()
    vindue = vindue_mask(bars.index)
    rth = sessions.rth_mask(bars.index, BAR_MIN)
    beroert = (z["status"] == BEROERT).to_numpy()
    slut = z["slut_i"].to_numpy(dtype=np.int64)
    z["i_vindue"] = beroert & vindue[np.where(beroert, slut, 0)]
    # 0,429% inklusive. Afrundet så en zone på præcis grænsen ikke afvises af støj.
    z["under_stoploft"] = np.round(z["hoejde_pct"].to_numpy(dtype=float), 10) <= STOPLOFT_PCT
    z["signal"] = z["i_vindue"] & z["under_stoploft"]
    z["dannet_i_rth"] = rth[z["udbrud_i"].to_numpy(dtype=np.int64)]
    t = pd.DatetimeIndex(z["slut_tid"])
    z["dag"] = pd.Series(_et_dag(t), index=z.index).where(beroert)
    alder = (t - (pd.DatetimeIndex(z["udbrud_tid"]) + BAR)) / pd.Timedelta(hours=1)
    z["zonealder_timer"] = pd.Series(np.asarray(alder, dtype=float), index=z.index).where(beroert)
    z["zonehoejde_pt"], z["kontrakter"], z["omk_R_netto"] = sizing(z["hoejde_pct"])
    return z


# ---------------------------------------------------------------------------
# Optælling
# ---------------------------------------------------------------------------

def _andel(navn: str, k, n) -> dict:
    """Tæller, andel i procent og Wilson 95%-CI."""
    k, n = int(k), int(n)
    lo, hi = wilson_interval(k, n)
    return {f"{navn}_n": k, f"{navn}_pct": 100 * k / n if n else float("nan"),
            f"{navn}_ci95_lo_pct": 100 * lo if n else float("nan"),
            f"{navn}_ci95_hi_pct": 100 * hi if n else float("nan")}


def _p(x, q: float) -> float:
    x = np.asarray(x, dtype=float)
    return float(np.percentile(x, q)) if len(x) else float("nan")


def dagtal(signal_dage: pd.Series, dage: pd.DatetimeIndex) -> dict:
    """Signaler pr. RTH-dag. ``signal_dage`` har én dato pr. signal."""
    s = pd.DatetimeIndex(signal_dage).as_unit("ns")
    if not s.isin(dage).all():
        raise ValueError("signaler på dage uden for RTH-dagene")
    pr_dag = pd.Series(1, index=s).groupby(level=0).size().reindex(dage, fill_value=0)
    row = {"RTH_dage_n": len(dage), "signaler_n": len(s)}
    row.update(_andel("dage_med_signal", (pr_dag > 0).sum(), len(dage)))
    for g in ("lo", "hi"):
        row[f"dage_med_signal_ci95_{g}_n"] = row[f"dage_med_signal_ci95_{g}_pct"] / 100 * len(dage)
    row["signaler_pr_dag_p50"] = _p(pr_dag, 50)
    row["signaler_pr_dag_p90"] = _p(pr_dag, 90)
    return row


def noegletal(z: pd.DataFrame, dage: pd.DatetimeIndex) -> dict:
    """Præregistreringens §4 for ét udsnit af zonerne (alle, demand eller supply)."""
    beroert = z[z["status"] == BEROERT]
    i_vindue = beroert[beroert["i_vindue"]]
    sig = z[z["signal"]]
    row = dagtal(sig["dag"], dage)
    row["zoner_dannet_n"] = len(z)
    row["zoner_beroert_n"] = len(beroert)
    row.update(_andel("zoner_doede_ved_kontraktskift", (z["status"] == KONTRAKTSKIFT).sum(), len(z)))
    row.update(_andel("zoner_aldrig_beroert", (z["status"] == AABEN).sum(), len(z)))
    row["beroeringer_n"] = len(beroert)
    row.update(_andel("beroeringer_uden_for_vindue", (~beroert["i_vindue"]).sum(), len(beroert)))
    row["beroeringer_i_vindue_n"] = len(i_vindue)
    row.update(_andel("afvist_af_stoploft", (~i_vindue["under_stoploft"]).sum(), len(i_vindue)))
    for q in (10, 50, 90):
        row[f"zonehoejde_pt_p{q}"] = _p(sig["zonehoejde_pt"], q)
    for q in (10, 50, 90):
        row[f"kontrakter_p{q}"] = _p(sig["kontrakter"], q)
    row["kontrakter_nul_n"] = int((sig["kontrakter"] == 0).sum())
    row["omk_R_brutto"] = 0.0
    for q in (10, 50, 90):
        row[f"omk_R_netto_p{q}"] = _p(sig["omk_R_netto"], q)
    row["be_WR_pct_brutto"] = 100 * breakeven_win_rate(RR, 1.0, 0.0)
    # be_WR er affin og stigende i omk_R, så be_WR af percentilen ER percentilen af be_WR.
    for q in (50, 90):
        row[f"be_WR_pct_netto_p{q}"] = 100 * breakeven_win_rate(RR, 1.0, row[f"omk_R_netto_p{q}"])
    for q in (50, 90):
        row[f"zonealder_timer_p{q}"] = _p(sig["zonealder_timer"], q)
    row.update(_andel("dannet_uden_for_RTH", (~sig["dannet_i_rth"]).sum(), len(sig)))
    row["zoner_over_hul_n"] = int(z["over_hul"].sum())
    row["signaler_fra_zoner_over_hul_n"] = int(sig["over_hul"].sum())
    row["zoner_basis_og_udbrud_i_hver_sin_kontrakt_n"] = int(
        ((z["status"] == KONTRAKTSKIFT) & (z["slut_i"] == z["udbrud_i"])).sum())
    return row


def _sider(z: pd.DataFrame):
    return ((ALLE, z), (DEMAND, z[z["side"] == DEMAND]), (SUPPLY, z[z["side"] == SUPPLY]))


def tabel(z: pd.DataFrame, dage: pd.DatetimeIndex) -> pd.DataFrame:
    """Hele perioden med alle nøgletal, og hvert år med dagtallene. Pr. side."""
    hele = f"{dage[0].year}-{dage[-1].year}"
    rows = [{"periode": hele, "side": s, **noegletal(sub, dage)} for s, sub in _sider(z)]
    for aar in sorted(set(dage.year)):
        d = dage[dage.year == aar]
        for s, sub in _sider(z):
            sd = pd.DatetimeIndex(sub.loc[sub["signal"], "dag"])
            rows.append({"periode": str(aar), "side": s, **dagtal(sd[sd.year == aar], d)})
    return pd.DataFrame(rows)


def kategori(dage_n: float) -> str:
    return next(tekst for graense, tekst in KATEGORIER if dage_n >= graense)


def beslutning(row: dict) -> tuple[str, bool]:
    """§5: kategorien for CI'ets nedre grænse, og om CI'et krydser en grænse (uafgjort)."""
    lav = kategori(row["dage_med_signal_ci95_lo_n"])
    return lav, kategori(row["dage_med_signal_ci95_hi_n"]) != lav


def optaelling(df_1m: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """1m → 15m → zoner, klassificeret. Returnerer (15m-barer, zoner)."""
    bars = resample.aggregate(df_1m, BAR_MIN)
    return bars, klassificer(bars, find_zoner(bars))


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------

RAEKKER = [
    ("RTH_dage_n", "n"), ("signaler_n", "n"), ("dage_med_signal_n", "n"),
    ("dage_med_signal_pct", "andel"),
    ("signaler_pr_dag_p50", 1), ("signaler_pr_dag_p90", 1),
    ("zoner_dannet_n", "n"), ("zoner_beroert_n", "n"),
    ("zoner_doede_ved_kontraktskift_n", "n"), ("zoner_doede_ved_kontraktskift_pct", "andel"),
    ("zoner_aldrig_beroert_n", "n"), ("zoner_aldrig_beroert_pct", "andel"),
    ("beroeringer_n", "n"), ("beroeringer_uden_for_vindue_pct", "andel"),
    ("beroeringer_i_vindue_n", "n"), ("afvist_af_stoploft_pct", "andel"),
    ("zonehoejde_pt_p10", 1), ("zonehoejde_pt_p50", 1), ("zonehoejde_pt_p90", 1),
    ("kontrakter_p10", 1), ("kontrakter_p50", 1), ("kontrakter_p90", 1),
    ("omk_R_brutto", 4),
    ("omk_R_netto_p10", 4), ("omk_R_netto_p50", 4), ("omk_R_netto_p90", 4),
    ("be_WR_pct_brutto", 2), ("be_WR_pct_netto_p50", 2), ("be_WR_pct_netto_p90", 2),
    ("zonealder_timer_p50", 1), ("zonealder_timer_p90", 1),
    ("dannet_uden_for_RTH_pct", "andel"),
]


def _tal(v, nd: int = 1) -> str:
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    if v is None or not np.isfinite(v):
        return "—"
    return f"{v:.{nd}f}".replace(".", ",")


def _celle(r: pd.Series, navn: str, fmt) -> str:
    if fmt == "n":
        return _tal(int(r[navn]))
    if fmt == "andel":
        if not np.isfinite(r[navn]):
            return "—"
        stam = navn[: -len("_pct")]
        return (f"{_tal(r[navn])} ({_tal(r[f'{stam}_ci95_lo_pct'])}–"
                f"{_tal(r[f'{stam}_ci95_hi_pct'])})")
    return _tal(float(r[navn]), fmt)


def hovedtabel(tab: pd.DataFrame) -> str:
    hele = tab[~tab["periode"].str.fullmatch(r"\d{4}")].set_index("side")
    linjer = ["| størrelse | alle | demand | supply |", "|---|---|---|---|"]
    for navn, fmt in RAEKKER:
        linjer.append(f"| {navn} | " + " | ".join(_celle(hele.loc[s], navn, fmt)
                                                for s in (ALLE, DEMAND, SUPPLY)) + " |")
    return "\n".join(linjer) + "\n"


def aarstabel(tab: pd.DataFrame, side: str = ALLE) -> str:
    aar = tab[tab["periode"].str.fullmatch(r"\d{4}") & (tab["side"] == side)]
    linjer = ["| aar | RTH_dage_n | signaler_n | dage_med_signal_n | dage_med_signal_pct "
              "| ci95_lo_pct | ci95_hi_pct |", "|---|---|---|---|---|---|---|"]
    for _, r in aar.iterrows():
        linjer.append(f"| {r['periode']} | {int(r['RTH_dage_n'])} | {int(r['signaler_n'])} | "
                      f"{int(r['dage_med_signal_n'])} | {_tal(r['dage_med_signal_pct'])} | "
                      f"{_tal(r['dage_med_signal_ci95_lo_pct'])} | "
                      f"{_tal(r['dage_med_signal_ci95_hi_pct'])} |")
    return "\n".join(linjer) + "\n"


def skriv_md(tab: pd.DataFrame, meta: dict) -> str:
    alle = tab[(tab["side"] == ALLE) & ~tab["periode"].str.fullmatch(r"\d{4}")].iloc[0]
    lav, uafgjort = beslutning(alle)
    ci = (f"{_tal(alle['dage_med_signal_ci95_lo_n'])}–"
          f"{_tal(alle['dage_med_signal_ci95_hi_n'])}")
    c = meta["commits"]
    dele = [
        "# B4 kandidat 1 — signaloptælling\n",
        f"Kørt {meta['koert_utc']} UTC fra commit `{meta['head'][:7]}`, med modul, tests, "
        f"præregistrering, tillæg og datalag committet og uændrede. Præregistrering "
        f"`{_rel(PREREG)}` (commit `{c[_rel(PREREG)][:7]}`), tillæg `{_rel(TILLAEG)}` "
        f"(commit `{c[_rel(TILLAEG)][:7]}`). Kode `{_rel(Path(__file__))}` "
        f"(commit `{c[_rel(Path(__file__))][:7]}`).\n",
        f"Serie: {SYMBOL} ohlcv-1m gennem `data.holdout.load_in_sample`, "
        f"{meta['foerste_bar_utc']} → {meta['sidste_bar_utc']} UTC. {meta['n_1m']} 1m-barer "
        f"→ {meta['n_15m']} 15m-barer, {meta['n_kontraktskift']} kontraktskift. RTH-dage "
        f"in-sample: {meta['rth_dage_n']}, heraf uden RTH-barer i data: "
        f"{meta['rth_dage_uden_barer_n']}.\n",
        "**Kørslen tæller signaler og ser ikke på udfald.** Den lægger intet til tælleren "
        "for den deflaterede tærskel.\n",
        "## Hovedtal\n",
        "Andele i procent med Wilson 95%-CI i parentes. Percentilerne er lineære, tages af "
        "hver størrelse for sig og kun over signaler (zonehøjde, kontrakter, omk_R, "
        "zonealder). `signaler_pr_dag` er fordelingen over alle RTH-dage, også dage uden "
        "signal. `zoner_aldrig_beroert` er zonerne der stadig lever ved in-sample-slut "
        "(censurerede). Nævnerne står i tillægget.\n",
        hovedtabel(tab),
        "## Pr. år — dage_med_signal_pct, alle\n",
        aarstabel(tab),
        "Demand og supply pr. år står i `b4_k1_optaelling.csv`.\n",
        "## Beslutningsreglen, §5, anvendt mekanisk\n",
        f"dage_med_signal_n = {int(alle['dage_med_signal_n'])} af "
        f"{int(alle['RTH_dage_n'])}. Wilson 95%-CI i dage: {ci}. Grænserne er 590 og 390.\n",
        (f"CI'et krydser en grænse: uafgjort, og den laveste kategori gælder: **{lav}**.\n"
         if uafgjort else f"CI'et ligger inden for én kategori: **{lav}**.\n"),
        "## Forventningen, §6 — ikke et kriterium\n",
        f"Forventet over 70% af RTH-dagene. Målt {_tal(alle['dage_med_signal_pct'])}% "
        f"({_tal(alle['dage_med_signal_ci95_lo_pct'])}–"
        f"{_tal(alle['dage_med_signal_ci95_hi_pct'])}).\n",
        "## Gennemsigtighed — erklæret i tillægget før kørslen\n",
        f"- Zoner hvor basis- og udbrudslys er naboer i serien, men med et hul i tid imellem "
        f"(dagligt stop, weekend, helligdag, manglende bin): {int(alle['zoner_over_hul_n'])}. "
        f"Signaler fra dem: {int(alle['signaler_fra_zoner_over_hul_n'])}.\n"
        f"- Zoner hvor basis- og udbrudslys ligger i hver sin kontrakt (døde ved skiftet): "
        f"{int(alle['zoner_basis_og_udbrud_i_hver_sin_kontrakt_n'])}.\n"
        f"- Signaler hvor formlen giver 0 kontrakter (zonehøjde over 125 point, men højst "
        f"0,429%): {int(alle['kontrakter_nul_n'])}.\n",
        "Alle tal, også demand og supply pr. år: `b4_k1_optaelling.csv`.\n",
    ]
    return "\n".join(dele)


# ---------------------------------------------------------------------------
# Kørslen
# ---------------------------------------------------------------------------

def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "--no-optional-locks", "-C", str(ROOT), *args],
                          capture_output=True, text=True)


def _rel(sti: Path) -> str:
    return Path(sti).resolve().relative_to(ROOT.resolve()).as_posix()


def committede(stier) -> dict[str, str]:
    """Commit-hash pr. fil. Fejler hvis en fil ikke er committet eller er ændret siden."""
    ud = {}
    for sti in stier:
        rel = _rel(sti)
        commit = _git("log", "-1", "--format=%H", "--", rel).stdout.strip()
        if not commit:
            raise RuntimeError(f"{rel} er ikke committet. Kørslen sker kun fra committet kode")
        if _git("diff", "--quiet", "HEAD", "--", rel).returncode != 0:
            raise RuntimeError(f"{rel} er ændret siden commit {commit[:7]}")
        ud[rel] = commit
    return ud


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--zoner", type=Path, default=None,
                    help="skriv zonelisten som parquet hertil, til gennemgang. Uden for "
                         "repoet: den indeholder prisniveauer")
    args = ap.parse_args(argv)
    if args.zoner is not None and args.zoner.resolve().is_relative_to(ROOT.resolve()):
        raise RuntimeError("zonelisten indeholder prisniveauer og skrives ikke i repoet")

    commits = committede(COMMITTEDE)
    head = _git("rev-parse", "HEAD").stdout.strip()

    df = holdout.load_in_sample(SYMBOL)
    bars, z = optaelling(df)
    dage = rth_dage(holdout.IN_SAMPLE_START, holdout.HOLDOUT_START)
    tab = tabel(z, dage)

    rth = sessions.rth_mask(bars.index, BAR_MIN)
    iid = bars["instrument_id"].to_numpy()
    meta = {
        "koert_utc": pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M"),
        "head": head, "commits": commits,
        "foerste_bar_utc": df.index[0].strftime("%Y-%m-%d %H:%M"),
        "sidste_bar_utc": df.index[-1].strftime("%Y-%m-%d %H:%M"),
        "n_1m": len(df), "n_15m": len(bars),
        "n_kontraktskift": int((iid[1:] != iid[:-1]).sum()),
        "rth_dage_n": len(dage),
        "rth_dage_uden_barer_n": len(dage.difference(_et_dag(bars.index[rth]).unique())),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    tab.to_csv(OUT / "b4_k1_optaelling.csv", index=False)
    md = skriv_md(tab, meta)
    (OUT / "b4_k1_optaelling.md").write_text(md, encoding="utf-8")
    if args.zoner is not None:
        args.zoner.parent.mkdir(parents=True, exist_ok=True)
        z.to_parquet(args.zoner)
    print(md)
    print(f"skrev {OUT / 'b4_k1_optaelling.md'} og .csv")


if __name__ == "__main__":
    main()
