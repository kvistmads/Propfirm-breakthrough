"""B4 kandidat 1 — signaloptællingen: hvor mange handelsdage har mindst ét signal fra kernen?

Præregistreret i ``research/prereg/b4_k1_optaelling.md``. Implementeringsdetaljerne står i
``research/prereg/b4_k1_optaelling_tillaeg.md``. Begge er committet før kørslen, og
kørslen nægter at starte hvis de, eller denne fil, ikke er committet og uændrede.

    .venv/bin/python -m research.b4_k1_optaelling --kerne v1

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

## Kerne v2, ``research/prereg/b4_k1_optaelling_v2.md`` §2 — demand, supply spejlvendt

Tilføjet efter optælling 1. v1 står uændret ved siden af og kan stadig køres. Tillægget er
``research/prereg/b4_k1_optaelling_v2_tillaeg.md``.

    buffer, E       B = 0,10 × H og E = high + B. Supply: E = low − B.
    aktivering      første lys fra og med udbrudslyset med low > E (supply: high < E).
    ugyldig         et lys efter udbrudslyset og før aktiveringen med close < low
                    (supply: close > high). Zonen dør.
    berøring        første lys efter aktiveringslyset med low ≤ E (supply: high ≥ E).
                    Berøringer før aktiveringen tæller ikke, og zonen lever videre.
    risiko          E − low = 1,1 × H. Stoploft, kontrakter og omk_R regnes på risikoen.
    kontraktskift   som i v1, i alle faser.

Varianten uden buffer er B = 0. E sammenlignes eksakt i skaleret form, 10·low > 10·high + H,
fordi priserne ligger i hele tick og 0,1 × H ellers ville give afrundingsfejl.

    .venv/bin/python -m research.b4_k1_optaelling --kerne v1
    .venv/bin/python -m research.b4_k1_optaelling --kerne v2
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from fractions import Fraction
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
PREREG_V2 = ROOT / "research" / "prereg" / "b4_k1_optaelling_v2.md"
TILLAEG_V2 = ROOT / "research" / "prereg" / "b4_k1_optaelling_v2_tillaeg.md"
# Kørslen sker kun når disse er committet og uændrede.
COMMITTEDE = (
    Path(__file__).resolve(), ROOT / "tests" / "test_b4_k1_optaelling.py", PREREG, TILLAEG,
    PREREG_V2, TILLAEG_V2,
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

BUFFER_V2 = Fraction(1, 10)                 # B = 0,10 × H

DEMAND, SUPPLY, ALLE = "demand", "supply", "alle"
BEROERT, KONTRAKTSKIFT, AABEN = "beroert", "kontraktskift", "aaben"
# Kerne v2: ugyldig før aktivering, og to censurerede forløb i stedet for v1's "aaben".
UGYLDIG, AKTIV, ALDRIG_AKTIV = "ugyldig", "aktiv", "aldrig_aktiv"
CENSURERET = (AABEN, AKTIV, ALDRIG_AKTIV)   # lever stadig ved in-sample-slut
ZONEKOLONNER = ["side", "basis_i", "udbrud_i", "basis_tid", "udbrud_tid", "zone_high",
                "zone_low", "basis_close", "hoejde_pct", "over_hul", "status", "slut_i",
                "slut_tid"]
ZONEKOLONNER_V2 = ZONEKOLONNER + ["buffer_andel", "E", "aktiv_i", "aktiv_tid"]
V2, V2_UDEN_BUFFER = "v2", "v2_uden_buffer"
# §5: dage_med_signal_n. Kategorien er den laveste som konfidensintervallet rører.
KATEGORIER = ((590, "≥ 590: testbar, også med filtersøgning — edge-testen præregistreres"),
              (390, "390-589: kernen alene er testbar — kun kernen testes"),
              (0, "< 390: for få handler — kandidaten parkeres"))


# ---------------------------------------------------------------------------
# Zoner
# ---------------------------------------------------------------------------

def _kandidater(bars: pd.DataFrame):
    """Priserne, basislys-kandidaterne og næste kontraktskift. Fælles for v1 og v2."""
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
    return o, h, l, c, n, er_demand, er_supply, naeste_skift


def find_zoner(bars: pd.DataFrame) -> pd.DataFrame:
    """Alle zoner i 15m-serien, én række pr. zone, og hvordan hver af dem døde. Kerne v1.

    ``slut_i`` er positionen af berøringslyset eller skiftelyset, -1 for en zone der
    stadig lever ved seriens slut. Kalenderen indgår ikke her, se ``klassificer``.
    """
    o, h, l, c, n, er_demand, er_supply, naeste_skift = _kandidater(bars)

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


def find_zoner_v2(bars: pd.DataFrame, buffer: Fraction = BUFFER_V2) -> pd.DataFrame:
    """Zonerne efter kerne v2, én række pr. zone og præcis ét af fem forløb.

    Prisen skal først forlade zonen med bufferen (aktivering). Lukker et lys igennem
    zonen før det, er zonen ugyldig. Berøringen er første lys efter aktiveringslyset der
    når E. ``aktiv_i`` er aktiveringslyset, -1 hvis zonen aldrig blev aktiv.

    Med buffer = p/q holdes E i skaleret form, q·E = q·high + p·H (supply q·low − p·H), og
    priserne ganges med q. På priser i hele tick er alle led da eksakte i float64.
    """
    o, h, l, c, n, er_demand, er_supply, naeste_skift = _kandidater(bars)
    p, q = buffer.numerator, buffer.denominator

    rows = []
    for b in np.flatnonzero(er_demand | er_supply):
        demand = bool(er_demand[b])
        u, k = b + 1, int(naeste_skift[b])
        qe = q * h[b] + p * (h[b] - l[b]) if demand else q * l[b] - p * (h[b] - l[b])
        aktiv = -1
        if k <= u:
            # Udbrudslyset ligger i en ny kontrakt: zonen dør ved skiftet, før den er gyldig.
            status, slut = KONTRAKTSKIFT, k
        else:
            # Fra og med udbrudslyset til lyset før næste kontraktskift.
            forladt = q * l[u:k] > qe if demand else q * h[u:k] < qe
            gennem = c[u:k] < l[b] if demand else c[u:k] > h[b]
            gennem[0] = False                  # kun lys efter udbrudslyset gør zonen ugyldig
            ia = int(np.argmax(forladt)) if forladt.any() else None
            ig = int(np.argmax(gennem)) if gennem.any() else None
            if ig is not None and (ia is None or ig < ia):
                status, slut = UGYLDIG, u + ig
            elif ia is not None:
                aktiv = u + ia
                ramt = (q * l[aktiv + 1:k] <= qe) if demand else (q * h[aktiv + 1:k] >= qe)
                if ramt.any():
                    status, slut = BEROERT, aktiv + 1 + int(np.argmax(ramt))
                elif k < n:
                    status, slut = KONTRAKTSKIFT, k
                else:
                    status, slut = AKTIV, -1
            elif k < n:
                status, slut = KONTRAKTSKIFT, k
            else:
                status, slut = ALDRIG_AKTIV, -1
        rows.append((DEMAND if demand else SUPPLY, b, u, bars.index[b], bars.index[u],
                     h[b], l[b], c[b], (h[b] - l[b]) / c[b] * 100,
                     bool(bars.index[u] - bars.index[b] > BAR), status, slut,
                     bars.index[slut] if slut >= 0 else pd.NaT,
                     float(buffer), qe / q, aktiv,
                     bars.index[aktiv] if aktiv >= 0 else pd.NaT))
    z = pd.DataFrame(rows, columns=ZONEKOLONNER_V2)
    for kol in ("basis_tid", "udbrud_tid", "slut_tid", "aktiv_tid"):
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

def sizing(risiko_pct) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Risiko i point ved NQ 29.138, kontrakter inden for $250 og omkostning i R.

    Stoppet er zonens fjerne kant. I v1 er risikoen pr. kontrakt zonehøjden H, i v2
    E − low = 1,1 × H. Afrundingen før floor fjerner flydende tals støj, så 62,5 point
    giver 2 kontrakter, ikke 1.
    """
    pt = np.asarray(risiko_pct, dtype=float) / 100 * NQ_NIVEAU
    risiko_usd = pt * MNQ_USD_PR_POINT
    kontrakter = np.floor(np.round(RISIKO_USD / risiko_usd, 9))
    return pt, kontrakter, OMK_USD_RUNDTUR / risiko_usd


def klassificer(bars: pd.DataFrame, zoner: pd.DataFrame,
                risiko_faktor: float = 1.0) -> pd.DataFrame:
    """Berøringerne holdt op mod vinduet og stoploftet. Én række pr. zone, som i ind.

    ``risiko_faktor`` er risikoen i zonehøjder: 1 i v1 og i varianten uden buffer, 1,1 i
    v2. Stoploft, kontrakter og omk_R regnes på risikoen, ``zonehoejde_pt`` er altid H.
    """
    z = zoner.copy()
    vindue = vindue_mask(bars.index)
    rth = sessions.rth_mask(bars.index, BAR_MIN)
    beroert = (z["status"] == BEROERT).to_numpy()
    slut = z["slut_i"].to_numpy(dtype=np.int64)
    z["i_vindue"] = beroert & vindue[np.where(beroert, slut, 0)]
    hoejde_pct = z["hoejde_pct"].to_numpy(dtype=float)
    risiko_pct = hoejde_pct * risiko_faktor
    # 0,429% inklusive. Afrundet så en zone på præcis grænsen ikke afvises af støj.
    z["under_stoploft"] = np.round(risiko_pct, 10) <= STOPLOFT_PCT
    z["signal"] = z["i_vindue"] & z["under_stoploft"]
    z["dannet_i_rth"] = rth[z["udbrud_i"].to_numpy(dtype=np.int64)]
    t = pd.DatetimeIndex(z["slut_tid"])
    z["dag"] = pd.Series(_et_dag(t), index=z.index).where(beroert)
    alder = (t - (pd.DatetimeIndex(z["udbrud_tid"]) + BAR)) / pd.Timedelta(hours=1)
    z["zonealder_timer"] = pd.Series(np.asarray(alder, dtype=float), index=z.index).where(beroert)
    z["zonehoejde_pt"] = hoejde_pct / 100 * NQ_NIVEAU
    z["risiko_pt"], z["kontrakter"], z["omk_R_netto"] = sizing(risiko_pct)
    return z


def klassificer_v2(bars: pd.DataFrame, zoner: pd.DataFrame,
                   buffer: Fraction = BUFFER_V2) -> pd.DataFrame:
    """``klassificer`` med risikoen (1 + buffer) × H og tiderne omkring aktiveringen."""
    z = klassificer(bars, zoner, risiko_faktor=float(1 + buffer))
    beroert = (z["status"] == BEROERT).to_numpy()
    aktiv = pd.DatetimeIndex(z["aktiv_tid"])
    time = pd.Timedelta(hours=1)
    # Udbrudslysets lukning til aktiveringslysets åbning: −0,25 når udbrudslyset aktiverer.
    til = (aktiv - (pd.DatetimeIndex(z["udbrud_tid"]) + BAR)) / time
    # Aktiveringslysets lukning til berøringslysets åbning.
    efter = (pd.DatetimeIndex(z["slut_tid"]) - (aktiv + BAR)) / time
    z["tid_til_aktiv_timer"] = pd.Series(np.asarray(til, dtype=float), index=z.index).where(beroert)
    z["tid_efter_aktiv_timer"] = pd.Series(np.asarray(efter, dtype=float), index=z.index).where(beroert)
    z["beroering_lige_efter_aktivering"] = beroert & (
        z["slut_i"].to_numpy(dtype=np.int64) == z["aktiv_i"].to_numpy(dtype=np.int64) + 1)
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
    # Lever stadig ved in-sample-slut. I v1 kun "aaben", i v2 aktive og aldrig aktive.
    row.update(_andel("zoner_aldrig_beroert", z["status"].isin(CENSURERET).sum(), len(z)))
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


def noegletal_v2(z: pd.DataFrame, dage: pd.DatetimeIndex) -> dict:
    """v1's nøgletal plus præregistreringen v2 §4's nye rækker."""
    row = noegletal(z, dage)
    for navn, status in (("zoner_ugyldige_foer_aktiv", UGYLDIG),
                         ("zoner_aktive_ikke_beroert", AKTIV),
                         ("zoner_aldrig_aktive", ALDRIG_AKTIV)):
        row.update(_andel(navn, (z["status"] == status).sum(), len(z)))
    sig = z[z["signal"]]
    for q in (10, 50, 90):
        row[f"risiko_pt_p{q}"] = _p(sig["risiko_pt"], q)
    for navn in ("tid_til_aktiv_timer", "tid_efter_aktiv_timer"):
        for q in (50, 90):
            row[f"{navn}_p{q}"] = _p(sig[navn], q)
    row.update(_andel("beroering_lige_efter_aktivering",
                      sig["beroering_lige_efter_aktivering"].sum(), len(sig)))
    row["signaler_aktiveret_i_udbrudslyset_n"] = int((sig["aktiv_i"] == sig["udbrud_i"]).sum())
    return row


def _sider(z: pd.DataFrame):
    return ((ALLE, z), (DEMAND, z[z["side"] == DEMAND]), (SUPPLY, z[z["side"] == SUPPLY]))


def tabel(z: pd.DataFrame, dage: pd.DatetimeIndex, noegle=noegletal) -> pd.DataFrame:
    """Hele perioden med alle nøgletal, og hvert år med dagtallene. Pr. side.

    ``noegle`` er ``noegletal`` for v1 og ``noegletal_v2`` for v2.
    """
    hele = f"{dage[0].year}-{dage[-1].year}"
    rows = [{"periode": hele, "side": s, **noegle(sub, dage)} for s, sub in _sider(z)]
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
    """1m → 15m → zoner, klassificeret. Kerne v1. Returnerer (15m-barer, zoner)."""
    bars = resample.aggregate(df_1m, BAR_MIN)
    return bars, klassificer(bars, find_zoner(bars))


def zoner_v2(bars: pd.DataFrame, buffer: Fraction = BUFFER_V2) -> pd.DataFrame:
    """15m-barer → zoner efter kerne v2, klassificeret."""
    return klassificer_v2(bars, find_zoner_v2(bars, buffer), buffer)


def optaelling_v2(df_1m: pd.DataFrame, buffer: Fraction = BUFFER_V2):
    """1m → 15m → zoner efter kerne v2. Returnerer (15m-barer, zoner)."""
    bars = resample.aggregate(df_1m, BAR_MIN)
    return bars, zoner_v2(bars, buffer)


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
# Præregistreringen v2 §4: v1's rækker plus forløbene, risikoen og tiderne omkring aktiveringen.
RAEKKER_V2 = [
    ("RTH_dage_n", "n"), ("signaler_n", "n"), ("dage_med_signal_n", "n"),
    ("dage_med_signal_pct", "andel"),
    ("signaler_pr_dag_p50", 1), ("signaler_pr_dag_p90", 1),
    ("zoner_dannet_n", "n"), ("zoner_beroert_n", "n"),
    ("zoner_ugyldige_foer_aktiv_n", "n"), ("zoner_ugyldige_foer_aktiv_pct", "andel"),
    ("zoner_doede_ved_kontraktskift_n", "n"), ("zoner_doede_ved_kontraktskift_pct", "andel"),
    ("zoner_aktive_ikke_beroert_n", "n"), ("zoner_aktive_ikke_beroert_pct", "andel"),
    ("zoner_aldrig_aktive_n", "n"), ("zoner_aldrig_aktive_pct", "andel"),
    ("zoner_aldrig_beroert_pct", "andel"),
    ("beroeringer_n", "n"), ("beroeringer_uden_for_vindue_pct", "andel"),
    ("beroeringer_i_vindue_n", "n"), ("afvist_af_stoploft_pct", "andel"),
    ("zonehoejde_pt_p10", 1), ("zonehoejde_pt_p50", 1), ("zonehoejde_pt_p90", 1),
    ("risiko_pt_p10", 1), ("risiko_pt_p50", 1), ("risiko_pt_p90", 1),
    ("kontrakter_p10", 1), ("kontrakter_p50", 1), ("kontrakter_p90", 1),
    ("omk_R_brutto", 4),
    ("omk_R_netto_p10", 4), ("omk_R_netto_p50", 4), ("omk_R_netto_p90", 4),
    ("be_WR_pct_brutto", 2), ("be_WR_pct_netto_p50", 2), ("be_WR_pct_netto_p90", 2),
    ("zonealder_timer_p50", 1), ("zonealder_timer_p90", 1),
    ("tid_til_aktiv_timer_p50", 2), ("tid_til_aktiv_timer_p90", 2),
    ("tid_efter_aktiv_timer_p50", 2), ("tid_efter_aktiv_timer_p90", 2),
    ("beroering_lige_efter_aktivering_pct", "andel"),
    ("dannet_uden_for_RTH_pct", "andel"),
]
FORLOEB_V2 = (("zoner_beroert_n", "berørt"), ("zoner_ugyldige_foer_aktiv_n", "ugyldig"),
              ("zoner_doede_ved_kontraktskift_n", "kontraktskift"),
              ("zoner_aktive_ikke_beroert_n", "aktiv, ikke berørt"),
              ("zoner_aldrig_aktive_n", "aldrig aktiv"))


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


def _hele(tab: pd.DataFrame) -> pd.DataFrame:
    return tab[~tab["periode"].astype(str).str.fullmatch(r"\d{4}")].set_index("side")


def hovedtabel(tab: pd.DataFrame, raekker=RAEKKER) -> str:
    hele = _hele(tab)
    linjer = ["| størrelse | alle | demand | supply |", "|---|---|---|---|"]
    for navn, fmt in raekker:
        linjer.append(f"| {navn} | " + " | ".join(_celle(hele.loc[s], navn, fmt)
                                                for s in (ALLE, DEMAND, SUPPLY)) + " |")
    return "\n".join(linjer) + "\n"


def varianttabel(tab: pd.DataFrame) -> str:
    """Den korte tabel for varianten uden buffer, præregistreringen v2 §4."""
    hele = _hele(tab)
    linjer = ["| side | signaler_n | dage_med_signal_n | dage_med_signal_pct |",
              "|---|---|---|---|"]
    for s in (ALLE, DEMAND, SUPPLY):
        r = hele.loc[s]
        linjer.append(f"| {s} | {_celle(r, 'signaler_n', 'n')} | "
                      f"{_celle(r, 'dage_med_signal_n', 'n')} | "
                      f"{_celle(r, 'dage_med_signal_pct', 'andel')} |")
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


def _serie(meta: dict) -> str:
    return (f"Serie: {SYMBOL} ohlcv-1m gennem `data.holdout.load_in_sample`, "
            f"{meta['foerste_bar_utc']} → {meta['sidste_bar_utc']} UTC. {meta['n_1m']} 1m-barer "
            f"→ {meta['n_15m']} 15m-barer, {meta['n_kontraktskift']} kontraktskift. RTH-dage "
            f"in-sample: {meta['rth_dage_n']}, heraf uden RTH-barer i data: "
            f"{meta['rth_dage_uden_barer_n']}.\n")


def skriv_md_v2(tab: pd.DataFrame, meta: dict) -> str:
    """Rapporten for optælling 2. ``tab`` har kolonnen ``kerne``: v2 og v2_uden_buffer."""
    v2 = tab[tab["kerne"] == V2]
    v0 = tab[tab["kerne"] == V2_UDEN_BUFFER]
    alle = _hele(v2).loc[ALLE]
    lav, uafgjort = beslutning(alle)
    ci = (f"{_tal(alle['dage_med_signal_ci95_lo_n'])}–"
          f"{_tal(alle['dage_med_signal_ci95_hi_n'])}")
    andel = lambda r, stam: (f"{_tal(r[f'{stam}_pct'])}% ({_tal(r[f'{stam}_ci95_lo_pct'])}–"
                             f"{_tal(r[f'{stam}_ci95_hi_pct'])})")
    forloeb = " + ".join(f"{int(alle[k])} {t}" for k, t in FORLOEB_V2)
    c = meta["commits"]
    dele = [
        "# B4 kandidat 1 — signaloptælling 2, kerne v2\n",
        f"Kørt {meta['koert_utc']} UTC fra commit `{meta['head'][:7]}`, med modul, tests, "
        f"præregistreringer, tillæg og datalag committet og uændrede. Præregistrering "
        f"`{_rel(PREREG_V2)}` (commit `{c[_rel(PREREG_V2)][:7]}`), tillæg `{_rel(TILLAEG_V2)}` "
        f"(commit `{c[_rel(TILLAEG_V2)][:7]}`). Bygger på `{_rel(PREREG)}` "
        f"(commit `{c[_rel(PREREG)][:7]}`) og `{_rel(TILLAEG)}` "
        f"(commit `{c[_rel(TILLAEG)][:7]}`), som gælder medmindre v2 ændrer dem. Kode "
        f"`{_rel(Path(__file__))}` (commit `{c[_rel(Path(__file__))][:7]}`).\n",
        _serie(meta),
        "**Kørslen tæller signaler og ser ikke på udfald.** Den lægger intet til tælleren "
        "for den deflaterede tærskel.\n",
        "## Hovedtal, kerne v2 (buffer 10%)\n",
        "Andele i procent med Wilson 95%-CI i parentes. Percentilerne er lineære, tages af "
        "hver størrelse for sig og kun over signaler. `signaler_pr_dag` er fordelingen over "
        "alle RTH-dage, også dage uden signal. `risiko_pt` er 1,1 × H, og stoploft, "
        "kontrakter og omk_R regnes på den; `zonehoejde_pt` er H. `zoner_aldrig_beroert` er "
        "de to censurerede forløb tilsammen. `tid_til_aktiv_timer` er −0,25 når udbrudslyset "
        "selv er aktiveringslyset. Nævnerne står i tillæggene.\n",
        hovedtabel(v2, RAEKKER_V2),
        f"De fem forløb: {forloeb} = {int(alle['zoner_dannet_n'])} zoner dannet.\n",
        "## Pr. år — dage_med_signal_pct, alle, kerne v2\n",
        aarstabel(v2),
        "Demand og supply pr. år står i `b4_k1_optaelling_v2.csv`.\n",
        "## Varianten uden buffer, §3 — B = 0\n",
        "Kun til at kunne regne MDE for varianten senere. Beslutningsreglen gælder den ikke.\n",
        varianttabel(v0),
        "## Beslutningsreglen, §5, anvendt mekanisk — kerne v2\n",
        f"dage_med_signal_n = {int(alle['dage_med_signal_n'])} af "
        f"{int(alle['RTH_dage_n'])}. Wilson 95%-CI i dage: {ci}. Grænserne er 590 og 390.\n",
        (f"CI'et krydser en grænse: uafgjort, og den laveste kategori gælder: **{lav}**.\n"
         if uafgjort else f"CI'et ligger inden for én kategori: **{lav}**.\n"),
        "## Forventningen, §7 — ikke et kriterium\n",
        f"- Forventet mellem 60% og 90% af RTH-dagene med signal. Målt "
        f"{andel(alle, 'dage_med_signal')}.\n"
        f"- Andelen af signaler med berøringen i lyset lige efter aktiveringslyset forventet "
        f"langt under v1's 55,4%. Målt {andel(alle, 'beroering_lige_efter_aktivering')}.\n",
        "## Gennemsigtighed — erklæret i tillæggene før kørslen\n",
        f"- Zoner hvor basis- og udbrudslys er naboer i serien, men med et hul i tid imellem: "
        f"{int(alle['zoner_over_hul_n'])}. Signaler fra dem: "
        f"{int(alle['signaler_fra_zoner_over_hul_n'])}.\n"
        f"- Zoner hvor basis- og udbrudslys ligger i hver sin kontrakt (døde ved skiftet): "
        f"{int(alle['zoner_basis_og_udbrud_i_hver_sin_kontrakt_n'])}.\n"
        f"- Signaler hvor formlen giver 0 kontrakter (risiko over 125 point, men højst "
        f"0,429%): {int(alle['kontrakter_nul_n'])}.\n"
        f"- Signaler hvor udbrudslyset selv er aktiveringslyset: "
        f"{int(alle['signaler_aktiveret_i_udbrudslyset_n'])}.\n",
        "Alle tal, også hele tabellen for varianten og demand og supply pr. år: "
        "`b4_k1_optaelling_v2.csv`, kolonnen `kerne`.\n",
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
    ap.add_argument("--kerne", choices=("v1", "v2"), required=True,
                    help="v1: optælling 1. v2: kerne v2 og varianten uden buffer")
    ap.add_argument("--ud", type=Path, default=None,
                    help="mappe til md og csv, standard research/output")
    ap.add_argument("--zoner", type=Path, default=None,
                    help="skriv zonelisten som parquet hertil, til gennemgang. Uden for "
                         "repoet: den indeholder prisniveauer")
    args = ap.parse_args(argv)
    if args.zoner is not None and args.zoner.resolve().is_relative_to(ROOT.resolve()):
        raise RuntimeError("zonelisten indeholder prisniveauer og skrives ikke i repoet")
    ud = args.ud if args.ud is not None else OUT

    commits = committede(COMMITTEDE)
    head = _git("rev-parse", "HEAD").stdout.strip()

    df = holdout.load_in_sample(SYMBOL)
    dage = rth_dage(holdout.IN_SAMPLE_START, holdout.HOLDOUT_START)
    if args.kerne == "v1":
        bars, z = optaelling(df)
        tab = tabel(z, dage)
        navn, skriv = "b4_k1_optaelling", skriv_md
    else:
        bars = resample.aggregate(df, BAR_MIN)
        tabeller, zonelister = [], []
        for kerne, buffer in ((V2, BUFFER_V2), (V2_UDEN_BUFFER, Fraction(0))):
            zk = zoner_v2(bars, buffer)
            t = tabel(zk, dage, noegletal_v2)
            t.insert(0, "kerne", kerne)
            tabeller.append(t)
            zonelister.append(zk.assign(kerne=kerne))
        tab = pd.concat(tabeller, ignore_index=True)
        z = pd.concat(zonelister, ignore_index=True)
        navn, skriv = "b4_k1_optaelling_v2", skriv_md_v2

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
    ud.mkdir(parents=True, exist_ok=True)
    tab.to_csv(ud / f"{navn}.csv", index=False)
    md = skriv(tab, meta)
    (ud / f"{navn}.md").write_text(md, encoding="utf-8")
    if args.zoner is not None:
        args.zoner.parent.mkdir(parents=True, exist_ok=True)
        z.to_parquet(args.zoner)
    print(md)
    print(f"skrev {ud / navn}.md og .csv")


if __name__ == "__main__":
    main()
