"""Ruinmodel v2 for Topstep $50K Trading Combine — B6: sizing på det målte grundlag.

    .venv/bin/python -m research.mll_ruin k1        K1-regressionstjekket
    .venv/bin/python -m research.mll_ruin gitter    gitteret, kræver at K1 holdt på denne kode

Svarer på: hvor stor må en handel være, når Maximum Loss Limit er $2.000 og profitmålet
$3.000, og hvordan fordeler udfaldene sig mellem BESTÅET, RUIN og UAFGJORT (horisonten
nået)? Opgaven står i ``PRD_FASE2_RUINMODEL.md``; kriterierne K1-K5 i dens afsnit 3, og
valgreglen, vinduerne og operationaliseringen i ``research/prereg/fase2_valgregel.md``.

Mekanikken er 1:1 med Topsteps egen (verificeret 2026-09-09 fra help.topstep.com):

  start            saldo $50.000, MLL $48.000
  MLL trailer      på DAGSSLUTsaldo: mll = min(50.000, max(mll, saldo - 2.000))
                   Aldrig nedad. Låser permanent når den når startsaldoen.
  MLL brydes       på net P&L i REALTID inkl. urealiseret -> øjeblikkelig likvidering
  DLL              $1.000 (valgfri, slået TIL): dagen lukkes, kontoen lever
  profitmål        $3.000
  konsistens       bedste dag skal under 50% af profitmålet, ellers HÆVES målet
                   -> bestået kræver profit >= max(3.000, 2 x bedste dag)
  min. dage        2

Trailet er dagsslut, bruddet er realtid. Trailet regnes på en flad konto: ingen position
er åben ved dagsgrænsen. **Det var en antagelse (A) i v1 og er nu en regel (V):** Topstep
kræver alt fladt kl. 15:10 CT hver hverdag (verificeret 2026-09-12, STRATEGI_PROPFIRM §3).

## Hvad v2 ændrer

v1 (kørt 2026-09-09) gav hver handel samme dollarrisiko: ATR 0,168% × NQ 29.639,50. v2
trækker **R pr. handel fra den empiriske ATR-fordeling** for cellens timeframe i US RTH:
et uafhængigt træk med tilbagelægning blandt de faktisk målte barer. Ingen tilpasset
fordeling — halen er pointen, og en normalfordeling ville skære den af.

**Parrede stier.** Alle celler kører med samme seed. Vinder/taber-uniformen og antal
handler pr. dag trækkes i hver slot uanset stiens tilstand, og ATR trækkes som kvantil u
af cellens sorterede fordeling med samme u i alle celler. Sti i ser dermed samme
tilfældighed i hver celle; kun tærsklerne er forskellige. Forskelle mellem celler får et
parret konfidensinterval.

ATR har sin egen tilfældighedsstrøm. Fodres modellen med én konstant ATR, trækkes intet
fra den, og vinder/taber-trækkene er v1's — det er K1.

Hver handel er uafhængig af den forrige, også i sin ATR. Modellen ser at en høj ATR gør et
tab dyrere, men ikke at høje ATR'er klumper sig i tid. Det er ikke modelleret.

## De to brudmodeller

Vi kender handlens udfald, men ikke dens vej. Derfor køres begge grænser:

  optimistisk   kontoen dør kun når et stop FAKTISK rammes
  pessimistisk  kontoen dør så snart en handel åbnes hvis stoppet ville bryde MLL

Sandheden ligger imellem. Spændet mellem de to er usikkerheden på modellen (K4).

Gates hører til i live: modellen afviser ALDRIG en handel fordi den er farlig.

## Nulmodellen

Hver celle køres også med win rate sat til cellens egen break-even — nul edge. Uden den
ved man ikke om en høj beståelsesrate kommer fra strategien eller fra at Topsteps
regelgeometri er mild ved den sizing (metoderegel 12).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.stats import paired_proportion_diff_interval, wilson_interval  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "output"

START_BALANCE = 50_000.0
MLL_ROOM = 2_000.0
MLL_LOCK = 50_000.0
PROFIT_TARGET = 3_000.0
DLL = 1_000.0
MIN_DAYS = 2
CONSISTENCY_FRAC = 0.50

MNQ_MULTIPLIER = 2.0
RR = 2.0

MAX_TRADES_PER_DAY = 3
MAX_DAYS = 200
N_PATHS = 20_000
SEED = 20260909

# K1 — regressionens input: gitteret fra 2026-09-09 (research/output/mll_ruin.csv).
# Bruges KUN af k1(). Ingen af tallene indgår i gitteret.
K1_ATR_PCT = 0.168
K1_NQ = 29_639.50
K1_OMK_USD = 2.472
K1_KONTRAKTER = (1, 2, 3)
K1_STOP_ATR = (0.50, 0.75, 1.00)
K1_WR = (0.34, 0.37, 0.40, 0.45)
K1_REFERENCE = OUT / "mll_ruin.csv"
K1_UD = OUT / "mll_ruin_v2_k1.csv"
K1_RESUME = OUT / "mll_ruin_v2_k1.json"

# Gitteret og valget — research/prereg/fase2_valgregel.md
PRIMAER = "primaer"
REF_K3 = "reference_K3"
REF_12M = "reference_12m"
VINDUE_START = "2019-05-06"
TIMEFRAMES = (15, 5, 3, 1)
STOP_ATR = (1.00, 0.75, 0.50)
WR_ABSOLUT = (0.34, 0.37, 0.40, 0.45)
WR_RELATIV_PP = (0, 3, 6, 11)
VALG_WR = 0.40
ROBUST_RELATIV_PP = 6
K2_RUIN_MAX_PCT = 20.0
K3_RISIKO_P90_MAX_PCT = 10.0
K4_SPAEND_MAX_PP = 5.0
BRUD = (("opt", False), ("pess", True))

UD_CSV = OUT / "mll_ruin_v2.csv"
UD_ATR = OUT / "mll_ruin_v2_atr.csv"
UD_MD = OUT / "mll_ruin_v2.md"
UD_KRITERIER = OUT / "mll_ruin_v2_kriterier.json"


# ---------------------------------------------------------------------------
# Modellen
# ---------------------------------------------------------------------------

def r_usd(atr_pct, nq: float, stop_atr: float):
    """1R for én MNQ: stopafstanden i dollar. ``atr_pct`` i procent af prisen.

    ``nq`` er ÉT fast, nutidigt prisniveau for alle træk — ikke barens historiske pris.
    MLL'en er $2.000 i dagens dollar. NQ lukkede RTH i 4.490 den 2016-01-04, 7.808,50
    den 2019-05-06 og 29.138 den 2026-09-10, så samme ATR i procent er 6,5 gange flere
    dollar i dag end i 2016. Trak vi prisen med fra baren, ville modellen blande regimer
    og systematisk undervurdere risikoen mod et gulv der står i nutidige dollar.
    """
    return atr_pct / 100.0 * nq * MNQ_MULTIPLIER * stop_atr


def seed_v1(contracts: int, stop_atr: float, wr: float) -> int:
    """v1's seed pr. celle. Kun til K1."""
    return SEED + contracts * 1000 + int(stop_atr * 100) * 10 + int(wr * 100)


def simulate(n_paths: int, wr: float, stop_atr: float, contracts: int, pessimistisk: bool,
             omk_usd: float, atr_pct, nq: float, seed: int) -> dict:
    """Én kørsel. ``atr_pct`` er den empiriske fordeling (array) eller én konstant.

    ``omk_usd`` er rundturen pr. kontrakt; 0 giver brutto. Returnerer udfaldene som antal,
    udfaldet pr. sti (til parrede sammenligninger) og realiseret P&L pr. taget handel.
    Hver taget handel tæller med sit nominelle udfald — også den der slår kontoen ihjel —
    så middelværdien er handlens forventning og kan holdes op mod nulmodellens nul.
    """
    rng = np.random.default_rng(seed)
    atr = np.atleast_1d(np.asarray(atr_pct, dtype=float))
    konstant = atr.size == 1
    if konstant:
        r_konstant = r_usd(float(atr[0]), nq, stop_atr)
    else:
        atr = np.sort(atr)
        # Egen strøm til ATR: vinder/taber-trækkene er de samme som med en konstant (K1).
        rng_atr = np.random.default_rng([seed, 1])
    c = float(omk_usd)

    bal = np.full(n_paths, START_BALANCE)
    mll = np.full(n_paths, START_BALANCE - MLL_ROOM)
    best_day = np.zeros(n_paths)
    days = np.zeros(n_paths, dtype=np.int32)
    alive = np.ones(n_paths, dtype=bool)
    passed = np.zeros(n_paths, dtype=bool)
    ruined = np.zeros(n_paths, dtype=bool)
    n_handler, pnl_sum, pnl_sum2 = 0, 0.0, 0.0

    for _ in range(MAX_DAYS):
        if not alive.any():
            break
        day_pnl = np.zeros(n_paths)
        n_trades = rng.integers(1, MAX_TRADES_PER_DAY + 1, n_paths)

        for slot in range(MAX_TRADES_PER_DAY):
            # Begge træk sker før `take`, så strømmene forbruges ens i alle celler og
            # sti i ser samme tilfældighed uanset tilstand — parrede stier.
            if konstant:
                R_c = r_konstant
            else:
                u = rng_atr.random(n_paths)
                idx = np.minimum((u * atr.size).astype(np.int64), atr.size - 1)
                R_c = r_usd(atr[idx], nq, stop_atr)
            wins = rng.random(n_paths) < wr
            take = alive & (slot < n_trades) & (day_pnl > -DLL)
            if not take.any():
                continue
            win_amt = contracts * (RR * R_c - c)
            loss_amt = contracts * (-R_c - c)
            mae = contracts * (R_c + c)
            delta = np.where(wins, win_amt, loss_amt)
            breach = (bal - mae) <= mll
            dead = take & breach if pessimistisk else take & breach & ~wins

            d_take = delta[take]
            n_handler += d_take.size
            pnl_sum += float(d_take.sum())
            pnl_sum2 += float((d_take * d_take).sum())

            ruined |= dead
            alive &= ~dead

            live = take & ~dead
            bal = np.where(live, bal + delta, bal)
            day_pnl = np.where(live, day_pnl + delta, day_pnl)

        days += alive
        best_day = np.where(alive, np.maximum(best_day, day_pnl), best_day)
        mll = np.where(alive, np.minimum(MLL_LOCK, np.maximum(mll, bal - MLL_ROOM)), mll)

        target = np.maximum(PROFIT_TARGET, best_day / CONSISTENCY_FRAC)
        won = alive & (days >= MIN_DAYS) & ((bal - START_BALANCE) >= target)
        passed |= won
        alive &= ~won

    middel = pnl_sum / n_handler if n_handler else float("nan")
    var = (pnl_sum2 / n_handler - middel ** 2) if n_handler else float("nan")
    se = float(np.sqrt(max(var, 0.0) * n_handler / max(n_handler - 1, 1)) / np.sqrt(n_handler)) \
        if n_handler else float("nan")
    return {
        "n": n_paths,
        "bestaaet": int(passed.sum()),
        "ruin": int(ruined.sum()),
        "uafgjort": int(alive.sum()),
        "median_dage_bestaaet": float(np.median(days[passed])) if passed.any() else float("nan"),
        "median_dage_ruin": float(np.median(days[ruined])) if ruined.any() else float("nan"),
        "bestaaet_sti": passed,
        "ruin_sti": ruined,
        "n_handler": n_handler,
        "pnl_middel_pr_handel_usd": middel,
        "pnl_middel_CI95": (middel - 1.959963984540054 * se, middel + 1.959963984540054 * se),
    }


def be_wr(omk_usd: float, r_middel_usd: float) -> float:
    """Break-even win rate ved 2:1: nul forventet P&L pr. handel.

        EV = WR·(2·E[R] − c) − (1−WR)·(E[R] + c) = 0  ⇔  WR = (1 + c/E[R]) / 3

    Med R trukket pr. handel er det MIDDELVÆRDIEN af R der giver nul edge.
    """
    return (1.0 + omk_usd / r_middel_usd) / (RR + 1.0)


def parret_diff_pp(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    """(andel_x − andel_y, CI-nedre, CI-øvre) i procentpoint, på de samme stier."""
    x, y = np.asarray(x, dtype=bool), np.asarray(y, dtype=bool)
    a = int((x & y).sum())
    b = int((x & ~y).sum())
    c = int((~x & y).sum())
    d = x.size - a - b - c
    lo, hi = paired_proportion_diff_interval(a, b, c, d)
    return 100 * (x.mean() - y.mean()), 100 * lo, 100 * hi


def _kode_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# K1 — regressionstjek mod gitteret fra 2026-09-09
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class K1Resultat:
    n_sammenligninger: int
    n_inden_for_CI: int
    n_identiske: int
    max_afvigelse_pp: float
    deterministiske_ok: bool

    @property
    def holdt(self) -> bool:
        return self.n_inden_for_CI == self.n_sammenligninger and self.deterministiske_ok


def _laes_reference() -> list[dict]:
    with open(K1_REFERENCE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def k1(n_paths: int = N_PATHS) -> K1Resultat:
    """Konstant ATR 0,168%, NQ 29.639,50, omk. $2,472 — hver celle mod sit 95%-CI.

    CI'et er v1's Wilson-interval, genberegnet af v1's andel (antal = andel × n).
    ``identisk`` betyder samme tal op til v1's afrunding på to decimaler.
    """
    ref = {(int(r["kontrakter"]), float(r["stop_ATR"]), float(r["antaget_WR_pct"])): r
           for r in _laes_reference()}
    rows, det_ok = [], True
    for k in K1_KONTRAKTER:
        for stop in K1_STOP_ATR:
            R_c = r_usd(K1_ATR_PCT, K1_NQ, stop)
            omk_r = K1_OMK_USD / R_c
            for wr in K1_WR:
                v1 = ref[(k, stop, round(100 * wr, 1))]
                det = {
                    "R_pr_kontrakt_usd": round(R_c, 2),
                    "risiko_pr_handel_usd": round(k * (R_c + K1_OMK_USD), 2),
                    "risiko_pct_af_MLL": round(100 * k * (R_c + K1_OMK_USD) / MLL_ROOM, 2),
                    "omk_R_netto": round(omk_r, 4),
                    "be_WR_pct": round(100 * be_wr(K1_OMK_USD, R_c), 2),
                }
                for navn, v in det.items():
                    if abs(float(v1[navn]) - v) > 1e-9:
                        det_ok = False
                for omk, omk_navn in ((K1_OMK_USD, "netto"), (0.0, "brutto")):
                    for bm, pess in BRUD:
                        r = simulate(n_paths, wr, stop, k, pess, omk, K1_ATR_PCT, K1_NQ,
                                     seed_v1(k, stop, wr))
                        for maal, noegle in (("bestaa", "bestaaet"), ("ruin", "ruin"),
                                             ("uafgjort", "uafgjort")):
                            p1 = float(v1[f"{maal}_pct_{omk_navn}_{bm}"])
                            lo, hi = wilson_interval(round(p1 / 100 * n_paths), n_paths)
                            p2 = 100 * r[noegle] / n_paths
                            rows.append({
                                "kontrakter": k, "stop_ATR": stop, "WR_pct": round(100 * wr, 1),
                                "omk": omk_navn, "brudmodel": bm, "maal": maal,
                                "pct_v1": p1, "CI95_lav_v1": round(100 * lo, 3),
                                "CI95_hoej_v1": round(100 * hi, 3), "pct_v2": p2,
                                "afvigelse_pp": round(p2 - p1, 3),
                                "inden_for_CI": 100 * lo <= p2 <= 100 * hi,
                                "identisk": abs(p2 - p1) <= 0.005 + 1e-9,
                            })
    K1_UD.parent.mkdir(parents=True, exist_ok=True)
    with open(K1_UD, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    res = K1Resultat(
        n_sammenligninger=len(rows),
        n_inden_for_CI=sum(r["inden_for_CI"] for r in rows),
        n_identiske=sum(r["identisk"] for r in rows),
        max_afvigelse_pp=max(abs(r["afvigelse_pp"]) for r in rows),
        deterministiske_ok=det_ok,
    )
    K1_RESUME.write_text(json.dumps({**res.__dict__, "holdt": res.holdt, "n_stier": n_paths,
                                     "kode_sha256": _kode_sha256()}, indent=2),
                         encoding="utf-8")
    return res


# ---------------------------------------------------------------------------
# Grundlaget: ATR-fordelinger pr. vindue, NQ-niveau og omkostning
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Fordeling:
    vindue: str
    timeframe: int
    session: str
    atr_pct: np.ndarray
    foerste_dato: str
    sidste_dato: str

    @property
    def n(self) -> int:
        return int(self.atr_pct.size)

    def p(self, q: float) -> float:
        return float(np.percentile(self.atr_pct, q))

    def r_middel_usd(self, nq: float, stop_atr: float) -> float:
        """E[R] af den array simulationen sampler fra."""
        return float(r_usd(self.atr_pct, nq, stop_atr).mean())


@dataclass(frozen=True)
class Grundlag:
    nq: float
    nq_tid_et: str
    serie_foerste_et: str
    serie_sidste_et: str
    k3_aar: tuple
    fordelinger: dict
    omk_rth: object
    omk_eth: object


def indlaes_grundlag() -> Grundlag:
    import pandas as pd
    import yaml

    from backtest import costs
    from data import sessions
    from research import atr_fordeling as af
    from research.fase1_data import NQ, load_databento

    df = load_databento(NQ, "ohlcv-1m")
    nq, nq_tid = af.nq_niveau(df)
    k3 = af.k3_aar(df)
    series = af.session_series(df)
    et = lambda t: t.tz_convert(sessions.ET).strftime("%Y-%m-%d %H:%M")
    ud = {}
    for (m, s), bars in series.items():
        a = af.atr_pct(bars, m).dropna()
        a = a[a > 0]
        dato = a.index.tz_convert(sessions.ET).tz_localize(None).normalize()
        start_12m = dato.max() - pd.DateOffset(months=12) + pd.Timedelta(days=1)
        for v, mask in ((PRIMAER, dato >= pd.Timestamp(VINDUE_START)),
                        (REF_K3, np.isin(dato.year, k3)),
                        (REF_12M, dato >= start_12m)):
            mask = np.asarray(mask, dtype=bool)
            d = dato[mask]
            ud[(v, m, s)] = Fordeling(v, m, s, np.sort(a.to_numpy(dtype=float)[mask]),
                                      str(d.min().date()), str(d.max().date()))
    config = yaml.safe_load((ROOT / "config.yaml").read_text())
    return Grundlag(nq=nq, nq_tid_et=et(nq_tid), serie_foerste_et=et(df.index[0]),
                    serie_sidste_et=et(df.index[-1]), k3_aar=tuple(k3), fordelinger=ud,
                    omk_rth=costs.rundtur_dekomponering(config, "MNQ", sessions.RTH),
                    omk_eth=costs.rundtur_dekomponering(config, "MNQ", sessions.ETH))


def konstant_fordeling(fd: Fordeling, atr_pct: float, navn: str) -> Fordeling:
    return Fordeling(f"{fd.vindue}, {navn}", fd.timeframe, fd.session,
                     np.array([atr_pct]), fd.foerste_dato, fd.sidste_dato)


# ---------------------------------------------------------------------------
# Kørsler og rækker
# ---------------------------------------------------------------------------

class Koersel:
    """Holder simulationerne, så samme (fordeling, stop, kontrakter, WR, omk, brud)
    kun køres én gang — og så parrede sammenligninger kan slå stierne op igen."""

    def __init__(self, nq: float, n_paths: int):
        self.nq, self.n_paths = nq, n_paths
        self._cache: dict = {}
        self.antal = 0

    def sim(self, fd: Fordeling, stop: float, k: int, wr: float, omk: float,
            pess: bool) -> dict:
        key = (fd.vindue, fd.timeframe, fd.session, stop, k, round(wr, 12),
               round(omk, 12), pess)
        if key not in self._cache:
            self._cache[key] = simulate(self.n_paths, wr, stop, k, pess, omk, fd.atr_pct,
                                        self.nq, SEED)
            self.antal += 1
        return self._cache[key]


def celle_meta(fd: Fordeling, nq: float, stop: float, k: int, omk: float) -> dict:
    """Cellens deterministiske kolonner. Formlerne står i rapportens kolonneafsnit."""
    r50, r90 = r_usd(fd.p(50), nq, stop), r_usd(fd.p(90), nq, stop)
    rm = fd.r_middel_usd(nq, stop)
    return {
        "vindue": fd.vindue, "vindue_datoer": f"{fd.foerste_dato} til {fd.sidste_dato}",
        "timeframe": f"{fd.timeframe}m", "session": fd.session, "kontrakter": k,
        "stop_ATR": stop, "n_barer_ATR": fd.n,
        "ATR_pct_p50": fd.p(50), "ATR_pct_p90": fd.p(90),
        "ATR_pct_middel": float(fd.atr_pct.mean()),
        "R_usd_ved_ATR_p50": r50, "R_usd_ved_ATR_p90": r90, "R_usd_middel": rm,
        "omk_usd_rundtur_netto": omk,
        "risiko_pct_af_MLL_brutto_ved_ATR_p90": 100 * k * r90 / MLL_ROOM,
        "risiko_pct_af_MLL_netto_ved_ATR_p50": 100 * k * (r50 + omk) / MLL_ROOM,
        "risiko_pct_af_MLL_netto_ved_ATR_p90": 100 * k * (r90 + omk) / MLL_ROOM,
        "omk_R_ved_middel_R": omk / rm,
        "be_WR_pct_ved_middel_R": 100 * be_wr(omk, rm),
        "be_WR_pct_ved_R_p50": 100 * be_wr(omk, r50),
    }


def punkt(K: Koersel, fd: Fordeling, stop: float, k: int, wr: float, akse: str, rolle: str,
          omk: float, variant: str = "basis") -> dict:
    """Én række: netto og brutto × begge brudmodeller, med nulmodellen på samme stier."""
    meta = celle_meta(fd, K.nq, stop, k, omk)
    be = meta["be_WR_pct_ved_middel_R"] / 100
    row = {**meta, "variant": variant, "WR_akse": akse, "WR_rolle": rolle,
           "WR_pct": 100 * wr, "edge_pp_over_be_WR": 100 * (wr - be)}
    stier = {}
    for omk_navn, c, wr_nul in (("netto", omk, be), ("brutto", 0.0, 1.0 / 3.0)):
        for bm, pess in BRUD:
            r = K.sim(fd, stop, k, wr, c, pess)
            z = K.sim(fd, stop, k, wr_nul, c, pess)
            stier[(omk_navn, bm)] = r
            stier[("nul_" + omk_navn, bm)] = z
            n = r["n"]
            for maal, noegle in (("bestaa", "bestaaet"), ("ruin", "ruin")):
                lo, hi = wilson_interval(r[noegle], n)
                row[f"{maal}_pct_{omk_navn}_{bm}"] = 100 * r[noegle] / n
                row[f"{maal}_CI95_lav_{omk_navn}_{bm}"] = 100 * lo
                row[f"{maal}_CI95_hoej_{omk_navn}_{bm}"] = 100 * hi
            row[f"uafgjort_pct_{omk_navn}_{bm}"] = 100 * r["uafgjort"] / n
            d, lo, hi = parret_diff_pp(r["bestaaet_sti"], z["bestaaet_sti"])
            row[f"nulmodel_bestaa_pct_{omk_navn}_{bm}"] = 100 * z["bestaaet"] / n
            row[f"bestaa_pp_over_nulmodel_{omk_navn}_{bm}"] = d
            row[f"bestaa_pp_over_nulmodel_CI95_lav_{omk_navn}_{bm}"] = lo
            row[f"bestaa_pp_over_nulmodel_CI95_hoej_{omk_navn}_{bm}"] = hi
            row[f"pnl_middel_pr_handel_usd_{omk_navn}_{bm}"] = r["pnl_middel_pr_handel_usd"]
    row["median_dage_bestaaet_netto_pess"] = stier[("netto", "pess")]["median_dage_bestaaet"]
    row["_stier"] = stier
    return row


def wr_punkter(be: float) -> list[tuple[float, str, str]]:
    return ([(wr, "absolut", f"{round(100 * wr)}") for wr in WR_ABSOLUT]
            + [(be + pp / 100, "relativ", "be" if pp == 0 else f"be+{pp}")
               for pp in WR_RELATIV_PP])


def celle_raekker(K: Koersel, fd: Fordeling, stop: float, k: int, omk: float) -> list[dict]:
    be = celle_meta(fd, K.nq, stop, k, omk)["be_WR_pct_ved_middel_R"] / 100
    return [punkt(K, fd, stop, k, wr, akse, rolle, omk) for wr, akse, rolle in wr_punkter(be)]


def _celle(r: dict) -> str:
    return f"{r['timeframe']} / {_f(r['stop_ATR'])} ATR"


# ---------------------------------------------------------------------------
# Valget og kriterierne
# ---------------------------------------------------------------------------

def status_taerskel(lo: float, hi: float, max_: float) -> str:
    """Andel eller forskel mod en øvre tærskel: holdt, ikke holdt eller uafgjort."""
    if hi <= max_:
        return "holdt"
    if lo > max_:
        return "ikke holdt"
    return "uafgjort"


def vaelg(rows: list[dict]) -> dict:
    """Valgreglen (prereg §4) på rækker med samme WR-punkt.

    Målfunktion bestaa_pct_netto_pess, K3 som filter, parret CI mod nummer to."""
    maal = "bestaa_pct_netto_pess"
    p90 = "risiko_pct_af_MLL_netto_ved_ATR_p90"
    alle = sorted(rows, key=lambda r: -r[maal])
    feas = [r for r in alle if r[p90] <= K3_RISIKO_P90_MAX_PCT]
    res = {"n_kandidater": len(rows), "n_klarer_K3": len(feas), "valgt": None,
           "nummer_to": None, "diff": None, "uafgjort": False, "tiebreak": False,
           "udpeget": None, "modpart": None, "maks_uden_K3": alle[0], "maks_diff": None}
    if not feas:
        return res
    v = feas[0]
    res["valgt"] = res["udpeget"] = v
    if len(feas) > 1:
        n2 = feas[1]
        d = parret_diff_pp(v["_stier"][("netto", "pess")]["bestaaet_sti"],
                           n2["_stier"][("netto", "pess")]["bestaaet_sti"])
        res.update(nummer_to=n2, diff=d, modpart=n2, uafgjort=d[1] <= 0)
        if res["uafgjort"]:
            res["tiebreak"] = True
            res["udpeget"], res["modpart"] = sorted((v, n2), key=lambda r: r[p90])
    if alle[0] is not v:
        res["maks_diff"] = parret_diff_pp(
            alle[0]["_stier"][("netto", "pess")]["bestaaet_sti"],
            v["_stier"][("netto", "pess")]["bestaaet_sti"])
    return res


def k2(rows: list[dict]) -> dict:
    ruin = [(r, r["ruin_CI95_lav_netto_pess"], r["ruin_CI95_hoej_netto_pess"]) for r in rows]
    bedst = min(ruin, key=lambda x: x[0]["ruin_pct_netto_pess"])
    if any(hi <= K2_RUIN_MAX_PCT for _, _, hi in ruin):
        status = "holdt"
    elif all(lo > K2_RUIN_MAX_PCT for _, lo, _ in ruin):
        status = "ikke holdt"
    else:
        status = "uafgjort"
    return {"status": status, "laveste_ruin": bedst[0],
            "celler_med_oevre_CI_under": [_celle(r) for r, _, hi in ruin if hi <= K2_RUIN_MAX_PCT]}


def k4(row: dict) -> dict:
    s = row["_stier"]
    d, lo, hi = parret_diff_pp(s[("netto", "pess")]["ruin_sti"], s[("netto", "opt")]["ruin_sti"])
    return {"status": status_taerskel(lo, hi, K4_SPAEND_MAX_PP), "diff": (d, lo, hi)}


def k5(udpeget_12m: dict, modpart_12m: dict | None) -> dict:
    p90 = "risiko_pct_af_MLL_netto_ved_ATR_p90"
    if udpeget_12m[p90] > K3_RISIKO_P90_MAX_PCT:
        return {"status": "ikke holdt", "grund": "den valgte celle fejler K3-filteret", "diff": None}
    if modpart_12m is None or modpart_12m[p90] > K3_RISIKO_P90_MAX_PCT:
        return {"status": "holdt", "grund": "modparten findes ikke eller fejler K3-filteret",
                "diff": None}
    d = parret_diff_pp(udpeget_12m["_stier"][("netto", "pess")]["bestaaet_sti"],
                       modpart_12m["_stier"][("netto", "pess")]["bestaaet_sti"])
    if d[1] > 0:
        return {"status": "holdt", "grund": "forskellens CI ligger over nul", "diff": d}
    if d[2] < 0:
        return {"status": "ikke holdt", "grund": "forskellens CI ligger under nul", "diff": d}
    return {"status": "uafgjort", "grund": "forskellens CI krydser nul", "diff": d}


def konklusion(row: dict) -> dict:
    """Følsomhedens 'konklusion' (prereg §7): K2-tærsklen, K3 og K4 på cellen."""
    return {
        "K2_taerskel": status_taerskel(row["ruin_CI95_lav_netto_pess"],
                                      row["ruin_CI95_hoej_netto_pess"], K2_RUIN_MAX_PCT),
        "K3": "holdt" if row["risiko_pct_af_MLL_netto_ved_ATR_p90"] <= K3_RISIKO_P90_MAX_PCT
        else "ikke holdt",
        "K4": k4(row)["status"],
    }


# ---------------------------------------------------------------------------
# Gitterkørslen
# ---------------------------------------------------------------------------

def _k1_tjek() -> dict:
    if not K1_RESUME.exists():
        raise SystemExit("K1 er ikke kørt. Kør `python -m research.mll_ruin k1` først.")
    k = json.loads(K1_RESUME.read_text())
    if k.get("kode_sha256") != _kode_sha256():
        raise SystemExit("K1-resultatet er fra en anden version af mll_ruin.py. Kør k1 igen.")
    if not k.get("holdt"):
        raise SystemExit("K1 holdt ikke. Intet nyt tal er troværdigt før det holder.")
    return k


def gitter(n_paths: int = N_PATHS) -> dict:
    from backtest import costs
    from data import sessions
    from research import atr_fordeling as af

    k1_res = _k1_tjek()
    G = indlaes_grundlag()
    K = Koersel(G.nq, n_paths)
    omk = G.omk_rth.i_alt_usd
    fd = lambda v, m, s=sessions.RTH: G.fordelinger[(v, m, s)]
    er = lambda r, akse, rolle: r["WR_akse"] == akse and r["WR_rolle"] == rolle

    # 1. Primært gitter: 12 celler × 8 WR-punkter, 1 kontrakt
    primaer = []
    for m in TIMEFRAMES:
        for stop in STOP_ATR:
            primaer += celle_raekker(K, fd(PRIMAER, m), stop, 1, omk)
            print(f"  primært {m}m/{stop:.2f} ATR  ({K.antal} simulationer)", flush=True)
    ved_40 = [r for r in primaer if er(r, "absolut", "40")]
    ved_be6 = [r for r in primaer if er(r, "relativ", f"be+{ROBUST_RELATIV_PP}")]

    # 2. Valget, K2, K3, relativ robusthed
    valg = vaelg(ved_40)
    valg_rel = vaelg(ved_be6)
    res_k2 = k2(ved_40)
    udp = valg["udpeget"]

    ekstra, res = [], {"valg": valg, "valg_relativ": valg_rel, "K2": res_k2}
    if udp is not None:
        tf = int(udp["timeframe"].rstrip("m"))
        stop_u = udp["stop_ATR"]
        res["K3"] = {"status": "holdt"}
        res["K4"] = k4(udp)

        # 3. Referencevinduer: udpeget og modpart ved WR 40% absolut
        par = [udp] + ([valg["modpart"]] if valg["modpart"] is not None else [])
        ref = {}
        for v in (REF_K3, REF_12M):
            ref[v] = [punkt(K, fd(v, int(r["timeframe"].rstrip("m"))), r["stop_ATR"], 1, VALG_WR,
                            "absolut", "40", omk) for r in par]
            ekstra += ref[v]
        res["K5"] = k5(ref[REF_12M][0], ref[REF_12M][1] if len(par) > 1 else None)
        res["referencer"] = ref

        # 4. Fordeling mod konstant
        f_u = fd(PRIMAER, tf)
        konst = {
            "E[R]": punkt(K, konstant_fordeling(f_u, float(f_u.atr_pct.mean()), "R fast ved E[R]"),
                          stop_u, 1, VALG_WR, "absolut", "40", omk, "R fast ved E[R]"),
            "R_p50": punkt(K, konstant_fordeling(f_u, f_u.p(50), "R fast ved R_p50"),
                           stop_u, 1, VALG_WR, "absolut", "40", omk, "R fast ved R_p50"),
        }
        ekstra += list(konst.values())
        res["konstant"] = {}
        for navn, kr in konst.items():
            for bm, _ in BRUD:
                res["konstant"][(navn, bm)] = parret_diff_pp(
                    udp["_stier"][("netto", bm)]["ruin_sti"], kr["_stier"][("netto", bm)]["ruin_sti"])
        res["konstant_raekker"] = konst

        # 5. Følsomhed på slippage og spread
        import yaml
        config = yaml.safe_load((ROOT / "config.yaml").read_text())
        slip0 = costs.slippage_realiseret(0.5, 0.5)
        varianter = [("basis", 1.73, slip0), ("slippage 0", 1.73, 0.0),
                     ("slippage 1,0", 1.73, 1.0), ("spread 1,50", 1.50, slip0),
                     ("spread 2,17", 2.17, slip0)]
        foels = []
        for navn, sp, sl in varianter:
            o = costs.rundtur_dekomponering(config, "MNQ", sessions.RTH, spread_ticks=sp,
                                            slippage_ticks_pr_side=sl)
            r = punkt(K, f_u, stop_u, 1, VALG_WR, "absolut", "40", o.i_alt_usd, navn)
            r["spread_ticks"], r["slippage_ticks_pr_side"] = sp, sl
            r["_konklusion"] = konklusion(r)
            foels.append(r)
        ekstra += foels[1:]
        res["foelsomhed"] = foels
        k_basis = foels[0]["_konklusion"]
        res["C4_blokerende"] = foels[2]["_konklusion"] != k_basis
        res["spread_afhaengig"] = foels[3]["_konklusion"] != foels[4]["_konklusion"]

        # 6. Referencerækker: 2 og 3 kontrakter på den udpegede timeframe
        ref_k = []
        for kk in (2, 3):
            for stop in STOP_ATR:
                ref_k += celle_raekker(K, f_u, stop, kk, omk)
        ekstra += ref_k
        res["ref_kontrakter"] = ref_k
        print(f"  referencer, konstant og følsomhed færdige ({K.antal} simulationer)", flush=True)

    # 7. Nulmodellens selvtjek
    nul_tjek = []
    for r in (x for x in primaer if er(x, "absolut", "40")):
        for bm, _ in BRUD:
            z = r["_stier"][("nul_netto", bm)]
            lo, hi = z["pnl_middel_CI95"]
            nul_tjek.append({"celle": _celle(r), "brudmodel": bm, "n_handler": z["n_handler"],
                             "pnl_middel_pr_handel_usd": z["pnl_middel_pr_handel_usd"],
                             "CI95_lav": lo, "CI95_hoej": hi, "nul_i_CI": lo <= 0 <= hi})
    res["nul_tjek"] = nul_tjek

    # 8. §5a's ATR-tabel på primærvinduet
    atr_tab = []
    for s, o in ((sessions.RTH, G.omk_rth.i_alt_usd), (af.DOEGN, G.omk_eth.i_alt_usd)):
        for m in sorted(TIMEFRAMES):
            f = fd(PRIMAER, m, s)
            meta = celle_meta(f, G.nq, 1.0, 1, o)
            atr_tab.append({
                "timeframe": f"{m}m", "session": s, "n_barer": f.n,
                "ATR_pct_p10": f.p(10), "ATR_pct_p50": f.p(50), "ATR_pct_p90": f.p(90),
                "ATR_pct_middel": meta["ATR_pct_middel"],
                "R_usd_ved_ATR_p50": meta["R_usd_ved_ATR_p50"],
                "R_usd_ved_ATR_p90": meta["R_usd_ved_ATR_p90"], "R_usd_middel": meta["R_usd_middel"],
                "risiko_pct_af_MLL_netto_ved_ATR_p50": meta["risiko_pct_af_MLL_netto_ved_ATR_p50"],
                "risiko_pct_af_MLL_netto_ved_ATR_p90": meta["risiko_pct_af_MLL_netto_ved_ATR_p90"],
                "omk_usd_rundtur": o, "omk_R_ved_R_p50": o / meta["R_usd_ved_ATR_p50"],
                "be_WR_pct_ved_R_p50": meta["be_WR_pct_ved_R_p50"],
                "be_WR_pct_ved_middel_R": meta["be_WR_pct_ved_middel_R"],
            })
    res["atr_tabel"] = atr_tab

    # 9. §4.4: be_WR_pct_netto_p90 under fase 1's og overblikssessionens definition
    f15 = fd(REF_K3, 15)
    r_arr = r_usd(f15.atr_pct, G.nq, 1.0)
    res["be_wr_definitioner"] = {
        "fase1": 100 * be_wr(1.0, 1.0 / float(np.percentile(2.4717 / r_arr, 90))),
        "fase1_omk_usd": 2.4717,
        "overblik": 100 * be_wr(2.59, r_usd(0.459, G.nq, 1.0)),
    }

    alle = primaer + ekstra
    skriv_csv(alle, atr_tab)
    meta = {"k1": k1_res, "grundlag": G, "n_paths": n_paths, "n_sim": K.antal,
            "commit": _git_commit()}
    UD_MD.write_text(skriv_md(primaer, res, meta), encoding="utf-8")
    UD_KRITERIER.write_text(json.dumps(kriterier_json(res, meta), indent=2, ensure_ascii=False),
                            encoding="utf-8")
    print(chat_tabel(ved_40, valg))
    print(f"skrev {UD_MD}, {UD_CSV}, {UD_ATR} og {UD_KRITERIER}")
    return res


def _git_commit() -> str:
    try:
        h = subprocess.run(["git", "--no-optional-locks", "rev-parse", "--short", "HEAD"],
                           cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        beskidt = subprocess.run(["git", "--no-optional-locks", "status", "--porcelain",
                                  "research/mll_ruin.py"], cwd=ROOT, capture_output=True,
                                 text=True).stdout.strip()
        return h + (" (mll_ruin.py ændret siden commit)" if beskidt else "")
    except Exception:
        return "ukendt"


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def skriv_csv(rows: list[dict], atr_tab: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    felter: list[str] = []
    for r in rows:
        for k in r:
            if not k.startswith("_") and k not in felter:
                felter.append(k)
    with open(UD_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=felter)
        w.writeheader()
        for r in rows:
            w.writerow({k: v for k, v in r.items() if not k.startswith("_")})
    with open(UD_ATR, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(atr_tab[0]))
        w.writeheader()
        w.writerows(atr_tab)


def _f(v, nd: int = 2) -> str:
    if v is None:
        return "—"
    if isinstance(v, (bool, np.bool_)):
        return "ja" if v else "nej"
    if isinstance(v, (int, np.integer)):
        return f"{int(v)}"
    if isinstance(v, float) and not np.isfinite(v):
        return "—"
    return f"{v:.{nd}f}".replace(".", ",")


def _ci(lo: float, hi: float, nd: int = 2) -> str:
    return f"[{_f(lo, nd)}; {_f(hi, nd)}]"


def _md(rows: list[dict], kolonner: list[tuple[str, callable]]) -> str:
    linjer = ["| " + " | ".join(n for n, _ in kolonner) + " |",
              "|" + "---|" * len(kolonner)]
    for r in rows:
        linjer.append("| " + " | ".join(fn(r) for _, fn in kolonner) + " |")
    return "\n".join(linjer) + "\n"


def _andel(maal: str, omk: str, bm: str):
    return lambda r: (f"{_f(r[f'{maal}_pct_{omk}_{bm}'])} "
                      f"{_ci(r[f'{maal}_CI95_lav_{omk}_{bm}'], r[f'{maal}_CI95_hoej_{omk}_{bm}'])}")


def _pp_nul(omk: str, bm: str):
    return lambda r: (f"{_f(r[f'bestaa_pp_over_nulmodel_{omk}_{bm}'])} "
                      f"{_ci(r[f'bestaa_pp_over_nulmodel_CI95_lav_{omk}_{bm}'], r[f'bestaa_pp_over_nulmodel_CI95_hoej_{omk}_{bm}'])}")


def _d(d) -> str:
    return "—" if d is None else f"{_f(d[0])} {_ci(d[1], d[2])}"


KOL_CELLE = [
    ("timeframe", lambda r: r["timeframe"]),
    ("stop_ATR", lambda r: _f(r["stop_ATR"])),
    ("risiko_pct_af_MLL_netto_ved_ATR_p90", lambda r: _f(r["risiko_pct_af_MLL_netto_ved_ATR_p90"])),
]
KOL_WR = [
    ("WR_pct", lambda r: _f(r["WR_pct"])),
    ("edge_pp_over_be_WR", lambda r: _f(r["edge_pp_over_be_WR"])),
]
KOL_UDFALD = [
    ("bestaa_pct_netto_pess [CI95]", _andel("bestaa", "netto", "pess")),
    ("bestaa_pct_brutto_pess [CI95]", _andel("bestaa", "brutto", "pess")),
    ("ruin_pct_netto_pess [CI95]", _andel("ruin", "netto", "pess")),
    ("ruin_pct_netto_opt [CI95]", _andel("ruin", "netto", "opt")),
    ("ruin_pct_brutto_pess", lambda r: _f(r["ruin_pct_brutto_pess"])),
    ("uafgjort_pct_netto_pess", lambda r: _f(r["uafgjort_pct_netto_pess"])),
    ("bestaa_pp_over_nulmodel_netto_pess [CI95]", _pp_nul("netto", "pess")),
]


def chat_tabel(ved_40: list[dict], valg: dict) -> str:
    udp = valg["udpeget"]
    linjer = ["| celle | risiko_pct_af_MLL_p90 | bestaa_pct_pess [CI] | ruin_pct_pess [CI] | ruin_pct_opt | bestaa_pp_over_nul |",
              "|---|---|---|---|---|---|"]
    for r in ved_40:
        mrk = " ←" if udp is not None and r is udp else ""
        linjer.append(
            f"| {r['timeframe']}/{_f(r['stop_ATR'])}{mrk} | {_f(r['risiko_pct_af_MLL_netto_ved_ATR_p90'], 1)} | "
            f"{_f(r['bestaa_pct_netto_pess'], 1)} {_ci(r['bestaa_CI95_lav_netto_pess'], r['bestaa_CI95_hoej_netto_pess'], 1)} | "
            f"{_f(r['ruin_pct_netto_pess'], 1)} {_ci(r['ruin_CI95_lav_netto_pess'], r['ruin_CI95_hoej_netto_pess'], 1)} | "
            f"{_f(r['ruin_pct_netto_opt'], 1)} | {_f(r['bestaa_pp_over_nulmodel_netto_pess'], 1)} |")
    return "\n".join(linjer)


def kriterier_json(res: dict, meta: dict) -> dict:
    c = lambda r: None if r is None else _celle(r)
    v = res["valg"]
    ud = {
        "K1": {k: meta["k1"][k] for k in ("holdt", "n_sammenligninger", "n_inden_for_CI",
                                          "n_identiske", "max_afvigelse_pp")},
        "K2": {"status": res["K2"]["status"],
               "celler_med_oevre_CI_under_20": res["K2"]["celler_med_oevre_CI_under"]},
        "valg": {"valgt": c(v["valgt"]), "nummer_to": c(v["nummer_to"]), "diff_pp": v["diff"],
                 "uafgjort": v["uafgjort"], "tiebreak": v["tiebreak"], "udpeget": c(v["udpeget"]),
                 "maks_uden_K3": c(v["maks_uden_K3"]), "maks_diff_pp": v["maks_diff"],
                 "valgt_relativ_be+6": c(res["valg_relativ"]["valgt"])},
    }
    if v["udpeget"] is not None:
        ud.update({"K3": res["K3"]["status"], "K4": {"status": res["K4"]["status"], "diff_pp": res["K4"]["diff"]},
                   "K5": {"status": res["K5"]["status"], "grund": res["K5"]["grund"], "diff_pp": res["K5"]["diff"]},
                   "fordeling_mod_konstant_ruin_pp": {f"{n}|{bm}": d for (n, bm), d in res["konstant"].items()},
                   "C4_blokerende": res["C4_blokerende"], "spread_afhaengig": res["spread_afhaengig"],
                   "foelsomhed": {r["variant"]: r["_konklusion"] for r in res["foelsomhed"]}})
    ud["nulmodel_selvtjek_alle_nul_i_CI"] = all(x["nul_i_CI"] for x in res["nul_tjek"])
    ud["commit"] = meta["commit"]
    return ud


def skriv_md(primaer: list[dict], res: dict, meta: dict) -> str:
    import datetime as _dt

    G: Grundlag = meta["grundlag"]
    o = G.omk_rth
    e = G.omk_eth
    v = res["valg"]
    udp = v["udpeget"]
    k1r = meta["k1"]
    er = lambda r, akse, rolle: r["WR_akse"] == akse and r["WR_rolle"] == rolle
    ved_40 = [r for r in primaer if er(r, "absolut", "40")]
    fp = G.fordelinger[(PRIMAER, 15, "RTH")]
    fk = G.fordelinger[(REF_K3, 15, "RTH")]
    f12 = G.fordelinger[(REF_12M, 15, "RTH")]
    D = []
    D.append("# Ruinmodel v2 — B6, sizing på det målte grundlag\n")
    D.append(
        f"Kørt {_dt.date.today().isoformat()} på commit `{meta['commit']}`. "
        f"**NQ-niveau {_f(G.nq)} — sidste RTH-luk i serien, {G.nq_tid_et} ET.** "
        f"Alle dollartal i dokumentet står på det niveau. Serien: Databento GLBX.MDP3 NQ.v.0 "
        f"ohlcv-1m, {G.serie_foerste_et} til {G.serie_sidste_et} ET. {_f(meta['n_paths'], 0)} "
        f"parrede stier pr. kørsel, seed {SEED}, horisont {MAX_DAYS} handelsdage, 1-3 handler "
        f"pr. dag, RR 2:1, 1 MNQ = $2/indekspoint. {meta['n_sim']} simulationer i alt.\n")
    D.append("Opgave: `PRD_FASE2_RUINMODEL.md`. Valgregel, vinduer og operationalisering af "
             "K2-K5: `research/prereg/fase2_valgregel.md` (committet før kørslen). Kode: "
             "`research/mll_ruin.py`. Alle rækker: `mll_ruin_v2.csv`.\n")

    D.append("## Grundlag\n")
    D.append(_md([
        {"v": "Primært (hele gitteret)", "d": f"{fp.foerste_dato} til {fp.sidste_dato}", "n": fp.n},
        {"v": "Reference A: K3-årene 2016-2026", "d": f"{fk.foerste_dato} til {fk.sidste_dato}", "n": fk.n},
        {"v": "Reference B: seneste 12 måneder (K5)", "d": f"{f12.foerste_dato} til {f12.sidste_dato}", "n": f12.n},
    ], [("vindue, NQ RTH", lambda r: r["v"]), ("ET-datoer", lambda r: r["d"]),
        ("n_barer_ATR_15m", lambda r: _f(r["n"], 0))]))
    D.append("**Instrument: NQ, ikke MNQ (antagelse).** Mads besluttede MNQ som primær serie, "
             "men MNQ-1m-barer ligger ikke i cachen, og et udtræk ville koste ~$9,46. Valget "
             "blev NQ fra 2019-05-06 uden udgift. At ATR i procent er den samme på NQ og MNQ er "
             "derfor **ikke målt**. Risikoen kommer fra NQ, spreadet fra MNQ.\n")
    D.append("### Omkostning pr. rundtur, 1 MNQ — `backtest.costs.rundtur_dekomponering`\n")
    D.append(_md([
        {"led": "Kommission", "r": o.kommission_usd, "e": e.kommission_usd, "s": "V — TopstepX"},
        {"led": f"Spread, 1 × fuld ({_f(o.spread_ticks)} / {_f(e.spread_ticks)} tick)",
         "r": o.spread_usd, "e": e.spread_usd, "s": "M — fase 1, med forbehold"},
        {"led": f"Slippage, realiseret {_f(o.slippage_ticks_pr_side, 4)} tick pr. side",
         "r": o.slippage_usd, "e": e.slippage_usd, "s": "S — ikke målt"},
        {"led": "**I alt rundtur**", "r": o.i_alt_usd, "e": e.i_alt_usd, "s": ""},
    ], [("led", lambda r: r["led"]), ("usd_RTH", lambda r: _f(r["r"], 3)),
        ("usd_uden_for_RTH", lambda r: _f(r["e"], 3)), ("status", lambda r: r["s"])]))
    D.append("Slippage er `max(0, N(0,5; 0,5))` tick pr. side. Afskæringen ved nul løfter "
             "middelværdien fra 0,50 til 0,5417, og den betyder også at **modellen aldrig "
             "tillader gunstig slippage**. Slippage er nu det største uverificerede led. "
             "Konfigurationen erklærer den realiserede værdi, og en test holder den op mod "
             "koden.\n")

    D.append("## Hvorfor nulmodellen\n")
    D.append("En beståelsesrate på 88% lyder som en edge. Men uden nulmodellen ved man ikke om "
             "den kommer fra strategien eller fra at Topsteps regelgeometri er mild ved den "
             "sizing. Nulmodellen er samme celle, samme stier, samme omkostning og samme "
             "mekanik — med win rate sat til cellens egen break-even, altså nul forventet P&L "
             "pr. handel. Kolonnen der betyder noget er forskellen, `bestaa_pp_over_nulmodel`, "
             "med sit CI. **Det er også formen på falsifikationstesten for hver fremtidig "
             "strategi** (metoderegel 12).\n")
    D.append("Nul forventning betyder ikke nul beståelse. En driftløs vandring mod et gulv på "
             "$2.000 og et mål på $3.000 rammer målet først i en betydelig del af stierne. Det "
             "er derfor nulmodellen er referencen — ikke et tegn på at noget er galt.\n")
    D.append("Nulmodellen er et mål for regelgeometrien, ikke valgets målfunktion. Valget "
             "træffes på beståelsesraten (prereg §4).\n")

    D.append("## Kolonner og formler\n")
    D.append(_md([
        {"k": "`ATR_pct_pXX`, `ATR_pct_middel`", "f": "XX. percentil (lineær) / middel af ATR i % af prisen over vinduets barer. Wilder 14, brudhåndtering som fase 1"},
        {"k": "`R_usd_ved_ATR_pXX`", "f": "`NQ × ATR_pct_pXX/100 × 2 × stop_ATR` — 1R for én MNQ ved den percentil"},
        {"k": "`R_usd_middel`", "f": "middel af `NQ × ATR_pct/100 × 2 × stop_ATR` over den array simulationen sampler fra = E[R]"},
        {"k": "`risiko_pct_af_MLL_netto_ved_ATR_pXX`", "f": "`kontrakter × (R_usd_ved_ATR_pXX + omk) / 2.000 × 100`. p90 er go/no-go og K3-filteret"},
        {"k": "`risiko_pct_af_MLL_brutto_ved_ATR_p90`", "f": "`kontrakter × R_usd_ved_ATR_p90 / 2.000 × 100`"},
        {"k": "`omk_R_ved_middel_R`", "f": "`omk / R_usd_middel`"},
        {"k": "`be_WR_pct_ved_middel_R`", "f": "`(1 + omk / R_usd_middel) / 3 × 100` — nul forventet P&L når R trækkes. **Nulmodellens WR**"},
        {"k": "`be_WR_pct_ved_R_p50`", "f": "`(1 + omk / R_usd_ved_ATR_p50) / 3 × 100` — §5a's gamle kolonne. Break-even for en konstant-model med R = R_p50, ikke for en fordeling"},
        {"k": "`edge_pp_over_be_WR`", "f": "`WR_pct − be_WR_pct_ved_middel_R`"},
        {"k": "`bestaa_pct`, `ruin_pct`, `uafgjort_pct`", "f": "andel af stierne der når målet / bryder MLL / står ved horisonten. `_netto`/`_brutto` = med/uden omkostning, `_opt`/`_pess` = brudmodel. CI95 = Wilson"},
        {"k": "`bestaa_pp_over_nulmodel`", "f": "`bestaa_pct(WR) − bestaa_pct(nulmodel)` på de samme stier. Netto-nulmodellen kører ved `be_WR_pct_ved_middel_R`, brutto-nulmodellen ved 33,33%. CI95 = Newcombe, parret (metode 10)"},
        {"k": "`pnl_middel_pr_handel_usd`", "f": "realiseret middel-P&L pr. taget handel, nominelt udfald inkl. den handel der slår kontoen ihjel"},
    ], [("kolonne", lambda r: r["k"]), ("formel", lambda r: r["f"])]))
    bd = res["be_wr_definitioner"]
    D.append("### `be_WR_pct_netto_p90` fra fase 1 (PRD 4.4)\n")
    D.append(f"**Formlen er den samme, percentilen er ikke.** Begge regner `(1 + omk_R) / 3 × 100`. "
             f"Fase 1 tog `omk_R_netto_p90` som 90. percentil af `omk/R` bar for bar — og da "
             f"`omk/R` falder med ATR, er det omkostningen ved ATR's **p10**. Det giver "
             f"{_f(bd['fase1'])}% på 15m RTH, K3 2016-2026, ${_f(bd['fase1_omk_usd'], 2)}: den "
             f"høje ende, hvor omkostningen gør ondt. Overblikssessionens definition tager `omk_R` "
             f"ved `R_usd_p90`, altså ATR's p90, og giver {_f(bd['overblik'])}% med $2,59. "
             f"Fase 1's kolonne er dermed rigtig for sin definition, men navnet sagde ikke hvad den "
             f"var percentil af. Her har kolonnerne navn efter hvad de står ved: "
             f"`be_WR_pct_ved_R_p50` og `be_WR_pct_ved_middel_R`.\n")

    D.append("## K1 — regressionstjek\n")
    D.append(f"Konstant ATR 0,168%, NQ 29.639,50, omkostning $2,472, v1's seeds, "
             f"{_f(k1r['n_stier'], 0)} stier. **{'Holdt' if k1r['holdt'] else 'Holdt IKKE'}:** "
             f"{k1r['n_inden_for_CI']} af {k1r['n_sammenligninger']} andele inden for v1's Wilson-CI "
             f"(bestået, ruin og uafgjort × netto/brutto × begge brudmodeller × 36 celler). "
             f"{k1r['n_identiske']} er identiske op til v1's afrunding; største afvigelse "
             f"{_f(k1r['max_afvigelse_pp'], 3)} pp. De deterministiske kolonner (R, risiko, omk_R, "
             f"be_WR) er {'ens' if k1r['deterministiske_ok'] else 'IKKE ens'}. Kørt på den kode der "
             f"har kørt gitteret (sha256 tjekket). Første K1-kørsel, før stierne blev parret "
             f"(commit `0aa23bc`): 432/432 inden for CI, 432 identiske. Detaljer: "
             f"`mll_ruin_v2_k1.csv`.\n")

    D.append("## K2-K5\n")
    kr = [{"k": "K1", "t": "hver celle inden for sit 95%-CI", "v": f"{k1r['n_inden_for_CI']}/{k1r['n_sammenligninger']}",
           "s": "holdt" if k1r["holdt"] else "ikke holdt"}]
    lr = res["K2"]["laveste_ruin"]
    kr.append({"k": "K2", "t": "∃ celle, 1 kontrakt: ruin_pct_netto_pess ≤ 20 ved WR 40%",
               "v": f"laveste: {_celle(lr)} {_andel('ruin', 'netto', 'pess')(lr)}. Øvre CI ≤ 20: "
                    f"{', '.join(res['K2']['celler_med_oevre_CI_under']) or 'ingen'}",
               "s": res["K2"]["status"]})
    if udp is not None:
        kr.append({"k": "K3", "t": "risiko_pct_af_MLL_netto_ved_ATR_p90 ≤ 10 (filter)",
                   "v": f"{_celle(udp)}: {_f(udp['risiko_pct_af_MLL_netto_ved_ATR_p90'])}. "
                        f"{v['n_klarer_K3']} af 12 celler klarer filteret", "s": res["K3"]["status"]})
        kr.append({"k": "K4", "t": "ruin_pess − ruin_opt ≤ 5 pp, netto, WR 40%",
                   "v": f"{_d(res['K4']['diff'])} pp", "s": res["K4"]["status"]})
        kr.append({"k": "K5", "t": "samme celle under seneste 12 måneder",
                   "v": f"{res['K5']['grund']}. Forskel {_d(res['K5']['diff'])} pp", "s": res["K5"]["status"]})
    else:
        kr.append({"k": "K3", "t": "risiko p90 ≤ 10 (filter)", "v": "ingen af de 12 celler klarer den",
                   "s": "ikke holdt"})
    D.append(_md(kr, [("#", lambda r: f"**{r['k']}**"), ("tærskel", lambda r: r["t"]),
                      ("værdi [CI95]", lambda r: r["v"]), ("status", lambda r: f"**{r['s']}**")]))

    D.append("## Valget (prereg §4)\n")
    if udp is None:
        D.append("Ingen celle klarer K3-filteret. Der vælges ingen celle.\n")
    else:
        D.append(f"Målfunktion `bestaa_pct_netto_pess` ved WR 40% absolut, blandt de "
                 f"{v['n_klarer_K3']} celler der klarer `risiko_pct_af_MLL_netto_ved_ATR_p90 ≤ 10`.\n")
        D.append(f"- **Højeste: {_celle(v['valgt'])}** — {_andel('bestaa', 'netto', 'pess')(v['valgt'])}%.")
        if v["nummer_to"] is not None:
            D.append(f"- Nummer to: {_celle(v['nummer_to'])} — {_andel('bestaa', 'netto', 'pess')(v['nummer_to'])}%.")
            D.append(f"- Forskel, parret: {_d(v['diff'])} pp. "
                     + ("**CI'et krydser nul: valget er uafgjort.** Begge celler rapporteres. "
                        f"Tiebreak på laveste risiko p90 udpeger {_celle(udp)} til K4, K5, "
                        "følsomhed og konstant-sammenligningen — **det er en tiebreak, ikke et resultat.**"
                        if v["uafgjort"] else "CI'et ligger over nul: valget er afgjort."))
        m = v["maks_uden_K3"]
        if v["maks_diff"] is None:
            D.append("- Maksimum uden K3-filteret er den samme celle. Filteret bestemte ikke valget.")
        else:
            D.append(f"- **Maksimum uden K3-filteret: {_celle(m)}** — {_andel('bestaa', 'netto', 'pess')(m)}%, "
                     f"risiko p90 {_f(m['risiko_pct_af_MLL_netto_ved_ATR_p90'])}. Forskel til den valgte, "
                     f"parret: {_d(v['maks_diff'])} pp. **Det er hvad K3-filteret koster.**")
        vr = res["valg_relativ"]
        if vr["valgt"] is None:
            D.append("- Relativ akse (be_WR + 6 pp): ingen celle klarer filteret.")
        else:
            skifter = _celle(vr["valgt"]) != _celle(v["valgt"])
            D.append(f"- **Robusthed, relativ akse (be_WR + 6 pp):** højeste er {_celle(vr['valgt'])} — "
                     f"{_andel('bestaa', 'netto', 'pess')(vr['valgt'])}%"
                     + (f"; nummer to {_celle(vr['nummer_to'])}, forskel {_d(vr['diff'])} pp"
                        + (" (uafgjort)" if vr["uafgjort"] else "") if vr["nummer_to"] is not None else "")
                     + (". **Valget skifter under den relative akse: cellen er et artefakt af "
                        "sammenligningsgrundlaget.**" if skifter else ". Valget skifter ikke."))
        D.append("")

        D.append("## Nulmodellen i den udpegede celle\n")
        D.append(f"**{_celle(udp)}, netto: be_WR {_f(udp['be_WR_pct_ved_middel_R'])}% → "
                 f"bestaa_pct {_f(udp['nulmodel_bestaa_pct_netto_pess'])}% (pessimistisk) og "
                 f"{_f(udp['nulmodel_bestaa_pct_netto_opt'])}% (optimistisk).** Det er "
                 f"beståelsesraten ved nul edge med denne sizing — referencepunktet for hver "
                 f"strategi der senere måles i cellen. Ved WR 40% ligger cellen "
                 f"{_pp_nul('netto', 'pess')(udp)} pp over.\n")
        z = [r for r in primaer if er(r, "relativ", "be") and _celle(r) == _celle(udp)][0]
        D.append(f"Nulmodellens ruin: {_andel('ruin', 'netto', 'pess')(z)}% pessimistisk, "
                 f"{_andel('ruin', 'netto', 'opt')(z)}% optimistisk; uafgjort "
                 f"{_f(z['uafgjort_pct_netto_pess'])}%.\n")

    nt = res["nul_tjek"]
    D.append("### Selvtjek: er nulmodellen nul?\n")
    D.append(f"Realiseret middel-P&L pr. taget handel i de 12 nul-celler, netto, begge brudmodeller: "
             f"**{sum(x['nul_i_CI'] for x in nt)} af {len(nt)} har 0 inden for 95%-CI.** "
             + ("Formel og simulation er enige." if all(x["nul_i_CI"] for x in nt)
                else "**Ikke alle — formel og simulation er uenige et sted.**") + "\n")
    D.append(_md(nt, [("celle", lambda r: r["celle"]), ("brudmodel", lambda r: r["brudmodel"]),
                      ("n_handler", lambda r: _f(r["n_handler"], 0)),
                      ("pnl_middel_pr_handel_usd [CI95]", lambda r: f"{_f(r['pnl_middel_pr_handel_usd'], 3)} {_ci(r['CI95_lav'], r['CI95_hoej'], 3)}"),
                      ("0_i_CI", lambda r: _f(r["nul_i_CI"]))]))

    if udp is not None:
        D.append("## Fordeling mod konstant\n")
        kk = res["konstant"]
        D.append(f"**{_celle(udp)}, WR 40%, netto, pessimistisk: `ruin_pct(fordeling) − ruin_pct(R fast "
                 f"ved E[R])` = {_d(kk[('E[R]', 'pess')])} pp.** Samme forventning, samme stier, nul "
                 f"spredning — forskellen skyldes fordelingens varians og intet andet.\n")
        kr_ = res["konstant_raekker"]
        D.append(_md([
            {"n": "fordeling (primært vindue)", "r": udp, "d_p": None, "d_o": None},
            {"n": "R fast ved E[R]", "r": kr_["E[R]"], "d_p": kk[("E[R]", "pess")], "d_o": kk[("E[R]", "opt")]},
            {"n": "R fast ved R_p50 (som den gamle model)", "r": kr_["R_p50"], "d_p": kk[("R_p50", "pess")], "d_o": kk[("R_p50", "opt")]},
        ], [("R-model", lambda r: r["n"]),
            ("R_usd_middel", lambda r: _f(r["r"]["R_usd_middel"])),
            ("ruin_pct_netto_pess [CI95]", lambda r: _andel("ruin", "netto", "pess")(r["r"])),
            ("ruin_pct_netto_opt [CI95]", lambda r: _andel("ruin", "netto", "opt")(r["r"])),
            ("bestaa_pct_netto_pess", lambda r: _f(r["r"]["bestaa_pct_netto_pess"])),
            ("ruin_pp_fordeling_minus_denne_pess [CI95]", lambda r: _d(r["d_p"])),
            ("ruin_pp_fordeling_minus_denne_opt [CI95]", lambda r: _d(r["d_o"]))]))

    D.append("## Gitteret, 1 kontrakt, WR 40% absolut — primært vindue\n")
    D.append(_md(ved_40, KOL_CELLE + [("R_usd_middel", lambda r: _f(r["R_usd_middel"])),
                                      ("be_WR_pct_ved_middel_R", lambda r: _f(r["be_WR_pct_ved_middel_R"]))]
                 + KOL_WR + KOL_UDFALD))
    for akse, titel in (("absolut", "absolut WR-akse"), ("relativ", "relativ WR-akse (be_WR + pp)")):
        D.append(f"## Hele gitteret, {titel} — primært vindue\n")
        D.append(_md([r for r in primaer if r["WR_akse"] == akse],
                     KOL_CELLE + [("WR_rolle", lambda r: r["WR_rolle"])] + KOL_WR + KOL_UDFALD))

    if udp is not None:
        D.append("## Referencevinduer — udpeget celle og modpart, WR 40% absolut\n")
        rr = []
        for vn, navn in ((PRIMAER, "primært"), (REF_K3, "K3 2016-2026"), (REF_12M, "seneste 12 mdr")):
            for r in ([x for x in ved_40 if x is udp or x is v["modpart"]] if vn == PRIMAER
                      else res["referencer"][vn]):
                rr.append({**r, "_navn": navn})
        D.append(_md(rr, [("vindue", lambda r: r["_navn"])] + KOL_CELLE
                     + [("ATR_pct_p90", lambda r: _f(r["ATR_pct_p90"], 4)),
                        ("be_WR_pct_ved_middel_R", lambda r: _f(r["be_WR_pct_ved_middel_R"]))] + KOL_UDFALD))

        D.append("## Følsomhed — udpeget celle, WR 40% absolut, netto\n")
        fs = res["foelsomhed"]
        D.append(_md(fs, [("variant", lambda r: r["variant"]),
                          ("spread_ticks", lambda r: _f(r["spread_ticks"])),
                          ("slippage_ticks_pr_side", lambda r: _f(r["slippage_ticks_pr_side"], 4)),
                          ("omk_usd_rundtur_netto", lambda r: _f(r["omk_usd_rundtur_netto"], 3)),
                          ("risiko_pct_af_MLL_netto_ved_ATR_p90", lambda r: _f(r["risiko_pct_af_MLL_netto_ved_ATR_p90"])),
                          ("be_WR_pct_ved_middel_R", lambda r: _f(r["be_WR_pct_ved_middel_R"])),
                          ("ruin_pct_netto_pess [CI95]", _andel("ruin", "netto", "pess")),
                          ("ruin_pct_netto_opt", lambda r: _f(r["ruin_pct_netto_opt"])),
                          ("bestaa_pct_netto_pess", lambda r: _f(r["bestaa_pct_netto_pess"])),
                          ("bestaa_pp_over_nulmodel_netto_pess [CI95]", _pp_nul("netto", "pess")),
                          ("K2_taerskel / K3 / K4", lambda r: " / ".join(r["_konklusion"].values()))]))
        D.append(("**Konklusionen skifter mellem slippage 0,5417 og 1,0 tick pr. side: C4 er "
                  "blokerende og skal måles før live.**" if res["C4_blokerende"]
                  else "Konklusionen (K2-tærskel, K3, K4) skifter ikke mellem slippage 0,5417 og 1,0 "
                       "tick pr. side.")
                 + (" **Den skifter mellem spread 1,50 og 2,17 tick** — cellen afhænger af "
                    "spreadmålingens ubekræftede antagelser." if res["spread_afhaengig"]
                    else " Den skifter heller ikke mellem spread 1,50 og 2,17 tick.") + "\n")

        D.append(f"## Referencerækker — 2 og 3 kontrakter på {udp['timeframe']}, primært vindue\n")
        D.append("Referencer, ikke kandidater. 1 MNQ er gulvet.\n")
        refk = [r for r in primaer if er(r, "absolut", "40") and r["timeframe"] == udp["timeframe"]]
        refk += [r for r in res["ref_kontrakter"] if er(r, "absolut", "40")]
        D.append("WR 40% absolut. Begge WR-akser for alle tre stopbredder står i `mll_ruin_v2.csv`.\n")
        D.append(_md(refk, [("kontrakter", lambda r: _f(r["kontrakter"], 0))] + KOL_CELLE + KOL_WR
                     + KOL_UDFALD))
    D.append("## §5a's ATR-tabel regnet om på primærvinduet\n")
    D.append(f"NQ RTH og døgn, {fp.foerste_dato} til {fp.sidste_dato}. 1 MNQ, 1-ATR-stop. RTH regnet med "
             f"${_f(o.i_alt_usd, 3)}, døgn med ${_f(e.i_alt_usd, 3)} (spread uden for RTH). Alle rækker i "
             f"`mll_ruin_v2_atr.csv`.\n")
    D.append(_md(res["atr_tabel"], [
        ("timeframe", lambda r: r["timeframe"]), ("session", lambda r: r["session"]),
        ("n_barer", lambda r: _f(r["n_barer"], 0)),
        ("ATR_pct_p50", lambda r: _f(r["ATR_pct_p50"], 4)), ("ATR_pct_p90", lambda r: _f(r["ATR_pct_p90"], 4)),
        ("ATR_pct_middel", lambda r: _f(r["ATR_pct_middel"], 4)),
        ("R_usd_ved_ATR_p50", lambda r: _f(r["R_usd_ved_ATR_p50"])),
        ("R_usd_ved_ATR_p90", lambda r: _f(r["R_usd_ved_ATR_p90"])),
        ("R_usd_middel", lambda r: _f(r["R_usd_middel"])),
        ("risiko_pct_af_MLL_netto_ved_ATR_p50", lambda r: _f(r["risiko_pct_af_MLL_netto_ved_ATR_p50"])),
        ("risiko_pct_af_MLL_netto_ved_ATR_p90", lambda r: _f(r["risiko_pct_af_MLL_netto_ved_ATR_p90"])),
        ("omk_R_ved_R_p50", lambda r: _f(r["omk_R_ved_R_p50"], 4)),
        ("be_WR_pct_ved_R_p50", lambda r: _f(r["be_WR_pct_ved_R_p50"])),
        ("be_WR_pct_ved_middel_R", lambda r: _f(r["be_WR_pct_ved_middel_R"]))]))
    D.append("### Den gamle §5a til sammenligning\n")
    D.append("Citeret fra `STRATEGI_PROPFIRM.md` §5a (2026-09-13): K3 2016-2026, NQ 29.138, $2,59 i "
             "RTH og $2,80 uden for. `be_WR_pct_p50` dér er det der her hedder `be_WR_pct_ved_R_p50`. "
             "Forskellen til tabellen ovenfor er vinduet, en omkostning $0,04 højere, og at §5a "
             "regnede på ATR afrundet til tre decimaler.\n")
    D.append(_md(GAMMEL_5A, [(k, (lambda kk: lambda r: r[kk])(k)) for k in GAMMEL_5A[0]]))

    D.append("## Hvad modellen ikke svarer på\n")
    D.append("- **ATR på MNQ.** Fordelingen er målt på NQ. Instrumenttjekket blev fravalgt (ingen udgift) og står som antagelse.\n"
             "- **Klumpning i tid.** Hver handel trækker sin ATR uafhængigt. Høje ATR'er der kommer i samme uge er ikke modelleret; handlerne er også uafhængige af hinanden i udfald.\n"
             "- **Hvordan win rate ændrer sig med stopbredden** (vej 2). Derfor både absolut og relativ WR-akse.\n"
             "- **Vejen inde i en handel.** Derfor to brudmodeller. Stoppet antages ramt præcist; slippage indgår kun som middelomkostning.\n"
             "- **Spor B.** Målfunktionen er Combine: nå $3.000 før ruin. XFA og LFA er ikke modelleret.\n"
             f"- **Censurering.** Stier der hverken består eller ruinerer inden {MAX_DAYS} handelsdage står som uafgjort.\n")
    return "\n".join(D)


# Citeret fra STRATEGI_PROPFIRM.md §5a, 2026-09-13 — kun til sammenligning i rapporten.
GAMMEL_5A = [
    {"timeframe": "1m", "session": "RTH", "ATR_pct_p50": "0,057", "ATR_pct_p90": "0,123", "R_usd_p50": "33,22", "R_usd_p90": "71,68", "risiko_pct_af_MLL_p50": "1,79", "risiko_pct_af_MLL_p90": "3,71", "omk_R_p50": "0,0780", "be_WR_pct_p50": "35,93"},
    {"timeframe": "3m", "session": "RTH", "ATR_pct_p50": "0,101", "ATR_pct_p90": "0,210", "R_usd_p50": "58,86", "R_usd_p90": "122,38", "risiko_pct_af_MLL_p50": "3,07", "risiko_pct_af_MLL_p90": "6,25", "omk_R_p50": "0,0440", "be_WR_pct_p50": "34,80"},
    {"timeframe": "5m", "session": "RTH", "ATR_pct_p50": "0,132", "ATR_pct_p90": "0,271", "R_usd_p50": "76,92", "R_usd_p90": "157,93", "risiko_pct_af_MLL_p50": "3,98", "risiko_pct_af_MLL_p90": "8,03", "omk_R_p50": "0,0337", "be_WR_pct_p50": "34,46"},
    {"timeframe": "15m", "session": "RTH", "ATR_pct_p50": "0,232", "ATR_pct_p90": "0,459", "R_usd_p50": "135,20", "R_usd_p90": "267,49", "risiko_pct_af_MLL_p50": "6,89", "risiko_pct_af_MLL_p90": "13,50", "omk_R_p50": "0,0192", "be_WR_pct_p50": "33,97"},
    {"timeframe": "15m", "session": "døgn", "ATR_pct_p50": "0,132", "ATR_pct_p90": "0,296", "R_usd_p50": "76,92", "R_usd_p90": "172,50", "risiko_pct_af_MLL_p50": "3,99", "risiko_pct_af_MLL_p90": "8,76", "omk_R_p50": "0,0364", "be_WR_pct_p50": "34,55"},
]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("koersel", choices=["k1", "gitter"])
    ap.add_argument("--paths", type=int, default=N_PATHS)
    args = ap.parse_args()
    if args.koersel == "k1":
        res = k1(args.paths)
        print(json.dumps({**res.__dict__, "holdt": res.holdt}, indent=2))
        print(f"skrev {K1_UD} og {K1_RESUME}")
    else:
        gitter(args.paths)


if __name__ == "__main__":
    main()
