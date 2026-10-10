"""B4 kandidat 7 — rebalancering: presser 60/40-porteføljerne aktierne, når de er overvægtede?

Præregistreret i ``research/prereg/b4_k7_rebalancering.md``. Baggrunden er
``research/output/b4_screening_2.md`` §3A. Signalet er en 60/40-portefølje af ES og ZN
(Harvey, Mazzoleni og Melone, NBER w33554): tærskelsignalet T (middel af 26 bånd) og
kalendersignalet c. Positionen sættes ved signalets close på XNYS-dag t og holdes i
Topstep-dagen for næste XNYS-dag d, 17:00 CT → 15:08 CT, i MES (ES.v.0 som pris). Målet er
netto-dollar pr. aktiv dag pr. MES-enhed ved dagens niveau. Nulmodellen N-retning er samme
positioner med tilfældigt fortegn. Westfall-Young og forskelsjusteringen er
``research/b4_k2_nowick.py``'s, kandidat 6's nætter regnes med
``research/b4_k6_overnight.py``'s egne funktioner. Kandidat 1-6's moduler importeres og
røres ikke.

    .venv/bin/python -m research.b4_k7_rebalancering --regressionstjek
    .venv/bin/python -m research.b4_k7_rebalancering --optaelling
    .venv/bin/python -m research.b4_k7_rebalancering --tidsmaaling
    .venv/bin/python -m research.b4_k7_rebalancering --koer

Pris hentes kun gennem ``data.holdout.load_in_sample``; holdout åbnes ikke.
``--optaelling`` og ``--tidsmaaling`` viser ingen P&L, ingen hit ratio og intet udfald.
``--koer`` er den rigtige kørsel og kræver ejerens godkendelse (§11.8).

## Vejen gennem modulet

1. ``signal_close``, ``dagsafkast``, ``taerskel_signal``, ``kalender_signal`` og
   ``byg_signal``: §4a-§4d.
2. ``position_T`` og ``position_K``: §4e.
3. ``handelsdage`` og ``byg_handel``: Topstep-dagen, udførelsen og udelukkelserne (§4g).
   ``dag_pnl`` regner brutto og netto (§4f-§4g); kun i den rigtige kørsel og tidsmålingen.
4. ``fortegn``, ``nret_gentagelse`` og ``k2.westfall_young``: N-retning og §7. ``beslutning``:
   §8.
5. ``sigma_v``, ``mde``, ``e_v``, ``styrke_fwe`` og ``styrke_ci``: §7 uden udfald.
6. ``optaelling`` (§11.5), ``tidsmaaling`` (§11.6), ``analyse``, ``diagnoser`` og
   ``skriv_md`` (§9-§10).

## Læsninger — valgt af Code, skrevet op før kørslen

Præregistreringen fastlægger ikke disse detaljer. De er valgt her og skal bekræftes. Dem
der kan flytte et resultat, eller hvor præregistreringen kan læses på to måder, er mærket
**[tvivl]**.

1. **Signaldagene** er XNYS-dagene 2016-01-04 → 2023-12-29 (``k1.rth_dage``). Serien har
   barer fra 2016-01-03 17:00 CT, så første close er 2016-01-04, og der sættes w = 0,60 dér.
   Første drift og første signal er 2016-01-05. **Handelsdagene** er de d = næste XNYS-dag
   efter t med 2016-04-01 ≤ d ≤ 2023-12-29, altså t fra 2016-03-31 til 2023-12-28.
2. **Signalets bar** (§4b) er den sidste bar med start før RTH-slut (XNYS-planens
   ``close``) og start på eller efter RTH-start samme dag. Forsinkelsen er RTH-slut − 1 min −
   barens start. Er den over 0, er baren "manglende", og den seneste bruges; over 5 minutter
   tælles for sig. Findes ingen bar i dagens RTH, stopper koden. ES og ZN slås op hver for
   sig efter samme regel [tvivl]: mangler baren kl. 14:59 kun i den ene serie, er de to
   closes ikke helt samtidige. Den anden læsning er at bruge den seneste bar, begge har.
3. **Afkastet** ``R_t = (C^adj_t − C^adj_(t−1)) / C^raw_(t−1)`` på ``k2.forskelsjuster`` af
   hele in-sample-serien. Den første signaldag har intet afkast.
4. **Båndene** er ``round(0,001 × k, 3)`` for k = 0 … 25. "|s| ≥ δ" sammenlignes i
   flydende tal; ved δ = 0 rebalanceres hver dag. [tvivl] Artiklens tekst siger "by more
   than δ", mens formlen i appendiks B har ≥; lighed sker i praksis ikke med flydende tal.
5. **Månedens sidste XNYS-dag** slås op i hele XNYS-planen (næste planlagte session ligger i
   en anden måned), så en helligdag på månedens sidste hverdag flytter rebalanceringen til
   dagen før. Den første signaldag (2016-01-04) er startpunktet, ikke en rebalancering.
6. **K's dage** (§4e): "de 5 sidste XNYS-dage" er t med højst 4 planlagte sessioner efter
   sig i samme måned. "Første XNYS-dag" er t uden planlagte sessioner før sig i samme måned.
   ``c_(t−4)`` er c på signaldagen 4 pladser før t i rækken af XNYS-dage, dvs. månedens
   4.-sidste dag, som skrevet [tvivl]: vendingen bruger altså ikke månedens sidste c. Det er
   præregistreringens tekst og rettes ikke her.
7. **Topstep-dagen** (§4g): indgang ved første bar fra 17:00 CT på kalenderdagen før d
   (``k6.udfoer``); over 5 minutter forsinket udelukker. Udgang: findes baren, der starter
   præcis kl. 15:08 CT (kortdage: RTH-slut − 2 min), bruges dens open. Ellers bruges close
   af den seneste bar før; dagen udelukkes, hvis den bar starter mere end 5 minutter før
   det nominelle tidspunkt [tvivl] (målt fra barens start; målt fra dens close ville
   tillade 1 minut mere). Ligger den bar før indgangsbaren, udelukkes dagen også.
   Udelukkede dage gælder alle varianter, N-retning og long hele dagen. Kortdag: RTH-slut
   før 15:00 CT.
8. **Brutto og netto** (§4g): ``Δpt = udgang_adj − open_adj(indgangsbar)``, ``L_d`` =
   ujusteret open af indgangsbaren, ``brutto = w × Δpt × (7.800 / L_d) × 5``, ``netto =
   brutto − |w| × 4,45``. Nasdaq-kontrollen: NQ.v.0's egne barer og udelukkelser,
   ``29.138 / L_d``, $2 og $2,85, med ES/ZN-signalet.
9. **Aktive dage** er handelsdage, der ikke er udelukket, og hvor w ≠ 0.
   **Netto pr. handelsdag** = summen af netto på aktive dage / antal ikke-udelukkede
   handelsdage [tvivl] (udelukkede dage tæller ikke med i nævneren).
10. **N-retning** (§6): fortegnet for handelsdag nr. j (blandt alle handelsdage, også de
    udelukkede) i gentagelse r er ``2 × default_rng([9700, r]).integers(0, 2, antal
    handelsdage)[j] − 1``. T, K, ½(T + K) og Nasdaq-kontrollen læser samme række. Netto i
    nulmodellen er ``fortegn × |w| × Δpt × skala × $/pt − |w| × omk``.
11. **Westfall-Young** er ``k2.westfall_young`` uændret over de 2 varianter: énsidet,
    sd med ddof = 1, R = 500, på middel netto pr. aktiv dag. Nasdaq-kontrollen får sin
    egen, som kun rapporteres.
12. **RV_d** (§7): stien er open af indgangsbaren, close af hver bar fra indgangsbaren til
    sidste bar før udgangen, og til sidst udgangsbarens open (eller, ved manglende
    udgangsbar, close af den seneste bar, som så er stiens sidste punkt). ``RV_d = Σ (Δ ×
    skala × $/pt)²``. ``σ_v = √(middel over aktive dage af w² × RV_d)``.
13. **E_v** (§7): ``z = signal / sd(signal)``, hvor sd (ddof = 1) tages over alle
    signaldage med et signal (2016-01-05 → 2023-12-29) [tvivl]; den anden læsning er kun
    handelsdagenes signaldage. For K er signalet c_t; på vendingsdagene er E = 0. Ved
    Nasdaq-kontrollen er dollarleddet ``29.138 × 2``.
14. **Styrken** er en normalapproksimation som i kandidat 6 [tvivl]:
    ``styrke_FWE = Φ(√n × E / σ − (2,7961 − z₀,₈₀))`` mod N-retning (omkostningen går ud,
    fordi nulmodellen betaler den samme), og ``styrke_CI = Φ(√n × (E − omk_v) / σ −
    (2,8016 − z₀,₈₀))`` for CI-nedre > 0, hvor ``omk_v`` = middel |w| × omkostning over de
    aktive dage. Ved MDE_sidak2 er styrke_FWE 80%.
15. **Opvarmningen** (§11.5): T med start 2016-02-01 er samme simulation med w = 0,60 sat
    ved close 2016-02-01. Korrelationen tages over handelsdagenes signaldage.
16. **Omkostningen i bp pr. år** (§11.5) er ``omk / ($/pt × median L_d) × 10⁴`` ved det
    historiske niveau. Ved dagens niveau er den fast 1,14 bp (ES) hhv. 0,49 bp (NQ).
17. **Korrelationen med kandidat 6** (§9): kandidat 6's nat for d er k6's nat med samme
    dato d (17:00 CT dagen før → 08:30 CT), V2 · salg, netto og 0 på nætter uden handel
    eller udelukket. Den parres med dagens netto for T og K over handelsdagene, der ikke er
    udelukket; inaktive K-dage tæller som 0. Samlet Sharpe ved lige risiko er
    ``√252 × middel / sd`` af summen af de to serier, hver divideret med sin sd.
18. **Driftjusteret brutto** (§9): middel over aktive dage af ``brutto_d − w_d × μ``, hvor μ
    er middel brutto for long hele dagen over de ikke-udelukkede handelsdage.
19. **Kvartalsslut for K** (§9): en K-dag hører til måneden for signaldagen t, og
    vendingsdagen til forrige måned (måneden for t's forrige XNYS-dag). Kvartalsslut er
    marts, juni, september og december. For T: t blandt månedens 5 sidste XNYS-dage mod
    resten.
20. **Nat og RTH** (§9): punktet er open af første bar fra 08:30 CT på d. Nat = w × (det
    punkt − indgang), RTH = w × (udgang − det punkt), samme skala.
21. **Close → close** (§9): ``w × (C^adj_d − C^adj_t) × (L_ref / C^raw_t) × $/pt`` med
    signalbarerne fra læsning 2 på handelsinstrumentet.
22. **$5,70** (§9): N-retning flyttes med samme omkostning pr. |w|, så t_v og p_FWE er
    uændrede; kun intervallet og dermed rækken kan flytte sig.
23. **Break-even** (§9): middel brutto / middel |w| og den nedre grænse i t-intervallet for
    brutto / middel |w|.
24. **Største tab inden for dagen** (§9) pr. MES-enhed: ``fortegn(w) × (close_adj −
    open_adj(indgang)) × skala × 5 − 4,45`` ved hver bars close langs stien og dagens netto
    pr. enhed ved udgangen, ``min(0, …)``. Hele omkostningen trækkes ved indgangen.
25. **Ruller i vinduet** er dage, hvor indgangs- og udgangsbaren har forskelligt
    ``instrument_id``.
26. **Hit ratio, gevinst/tab** som kandidat 6's læsning 20. **Skævhed** er
    ``middel((x − x̄)³) / sd³`` med sd ddof = 0.
27. **Kandidat 1-5's regressionstjek** er ``k6.regressionstjek()`` uændret. Kandidat 6 er
    ``k6.byg_grundlag``, ``k6.handel`` og ``k6.variant_tal`` for NQ, V2 · salg.
"""
from __future__ import annotations

import argparse
import math
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data import holdout, sessions  # noqa: E402
from research import b4_k1_optaelling as k1  # noqa: E402
from research import b4_k2_nowick as k2  # noqa: E402
from research import b4_k4_emt as k4  # noqa: E402
from research import b4_k6_overnight as k6  # noqa: E402
from research.normal import norm  # noqa: E402
from research.stats import mean_ci_t  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "output"
PREREG = ROOT / "research" / "prereg" / "b4_k7_rebalancering.md"
SCREENING = ROOT / "research" / "output" / "b4_screening_2.md"
# Den rigtige kørsel sker kun når disse er committet og uændrede.
COMMITTEDE = (
    Path(__file__).resolve(), ROOT / "tests" / "test_b4_k7_rebalancering.py", PREREG,
    SCREENING, ROOT / "research" / "b4_k7_data.py",
    ROOT / "research" / "b4_k6_overnight.py", ROOT / "research" / "b4_k5_vwap_trend.py",
    ROOT / "research" / "b4_k4_emt.py", ROOT / "research" / "b4_k2_nowick.py",
    ROOT / "research" / "b4_k1_trinA.py", ROOT / "research" / "b4_k1_optaelling.py",
    ROOT / "research" / "stats.py", ROOT / "research" / "normal.py",
    ROOT / "data" / "holdout.py", ROOT / "data" / "sessions.py",
)

CT = k1.CT
MIN_NS = 60 * 10**9

ES, ZN, NQ = "ES.v.0", "ZN.v.0", "NQ.v.0"
HOVED, KONTROL = ES, NQ
SIGNAL_START, SIGNAL_SLUT = "2016-01-01", "2024-01-01"
HANDEL_START = pd.Timestamp("2016-04-01")              # §3: opvarmning
OPVARM_ALT = pd.Timestamp("2016-02-01")                # §11.5

W0 = 0.60
BAAND = np.round(0.001 * np.arange(26), 3)             # §4c: 0,000 … 0,025
SKALA_T = 0.015                                        # §4e
K_SIDSTE = 5

T_VAR, K_VAR = "T", "K"
VARIANTER = (T_VAR, K_VAR)
NAVN = {T_VAR: "T · tærskel", K_VAR: "K · kalender", "C": "½(T + K)", "T_hel": "T · hele MES"}

INDGANG = pd.Timedelta(hours=17)                       # §4g, kalenderdagen før d
UDGANG = pd.Timedelta(hours=15, minutes=8)
KORTDAG_FOER = pd.Timedelta(minutes=2)
MIDT = pd.Timedelta(hours=8, minutes=30)               # §9: nat og RTH
MAKS_FORSINK_MIN = 5

OEKONOMI = {   # §4f-§4g: (L_ref, $/pt, omkostning pr. round trip pr. enhed)
    ES: (7800.0, 5.0, 4.45),
    NQ: (k6.NQ_NIVEAU, k6.MNQ_USD_PR_POINT, k6.OMK_USD),
}
OMK_DIAGNOSE_USD = 5.70                                # §4f, §9

NRET_REPS = 500                                        # §6, sænkes ikke
NRET_SEED = 9700

Z_SIDAK2 = 2.7961                                      # §7
Z_CI = 2.8016
Z_80 = float(norm.ppf(0.80))
ARTIKEL_HAELDNING = 0.00165                            # §7: 16,5 bp pr. sd
ARTIKEL_SLUT = pd.Timestamp("2023-03-17")              # §9
MARTS_2020 = (pd.Timestamp("2020-03-01"), pd.Timestamp("2020-04-01"))
K6_VARIANT = ("V2", k6.SALG)                           # §9: 07:30-09:30 · efter salg

# §11.4: kandidat 6, NQ, 07:30-09:30 · efter salg.
REGRESSION_K6_NAETTER_N = 902
REGRESSION_K6_NETTO_USD = 11.07


# ---------------------------------------------------------------------------
# Dagene, §4a
# ---------------------------------------------------------------------------

def serie(symbol: str) -> pd.DataFrame:
    """1m-serien, kun gennem holdout-modulet."""
    return holdout.load_in_sample(symbol)


def signal_dage() -> pd.DatetimeIndex:
    return k1.rth_dage(SIGNAL_START, SIGNAL_SLUT)


def _plan() -> pd.DataFrame:
    return sessions._xnys().schedule


def _ns(index) -> np.ndarray:
    return pd.DatetimeIndex(index).as_unit("ns").asi8.copy()


def rth_tider(dage: pd.DatetimeIndex) -> tuple[np.ndarray, np.ndarray]:
    """(RTH-start, RTH-slut) i UTC ns pr. XNYS-dag."""
    p = _plan().reindex(pd.DatetimeIndex(dage).as_unit("ns"))
    if p["close"].isna().any():
        raise ValueError("en dag er ikke en XNYS-dag")
    return _ns(p["open"]), _ns(p["close"])


def maanedens_plads(dage: pd.DatetimeIndex) -> tuple[np.ndarray, np.ndarray]:
    """Læsning 5 og 6: (sessioner efter t i samme måned, sessioner før t i samme måned),
    slået op i hele XNYS-planen."""
    plan = pd.DatetimeIndex(_plan().index).as_unit("ns")
    d = pd.DatetimeIndex(dage).as_unit("ns")
    pos = plan.get_indexer(d)
    if (pos < 0).any():
        raise ValueError("en dag er ikke en XNYS-dag")
    mnd = plan.year * 12 + plan.month
    mnd_d = mnd[pos]
    efter = np.array([np.searchsorted(mnd, m, side="right") - 1 - p
                      for m, p in zip(mnd_d, pos)])
    foer = np.array([p - np.searchsorted(mnd, m, side="left") for m, p in zip(mnd_d, pos)])
    return efter, foer


def maanedsslut(dage: pd.DatetimeIndex) -> np.ndarray:
    return maanedens_plads(dage)[0] == 0


# ---------------------------------------------------------------------------
# Signalet, §4b-§4d
# ---------------------------------------------------------------------------

def signal_close(t_ns: np.ndarray, dage: pd.DatetimeIndex) -> tuple[np.ndarray, np.ndarray]:
    """Læsning 2: (serieindeks for signalbaren, forsinkelse i minutter) pr. dag."""
    aab, luk = rth_tider(dage)
    i = np.searchsorted(t_ns, luk, side="left") - 1
    if (i < 0).any() or (t_ns[np.maximum(i, 0)] < aab).any():
        mangler = [str(d.date()) for d, ok in
                   zip(dage, (i >= 0) & (t_ns[np.maximum(i, 0)] >= aab)) if not ok]
        raise ValueError(f"ingen signalbar i dagens RTH: {mangler[:5]}")
    return i, (luk - MIN_NS - t_ns[i]) / MIN_NS


def dagsafkast(c_adj: np.ndarray, c_raa: np.ndarray, i: np.ndarray) -> np.ndarray:
    """§4b: ``R_t = (C^adj_t − C^adj_(t−1)) / C^raw_(t−1)``. Første dag er nan."""
    R = np.full(len(i), np.nan)
    R[1:] = (c_adj[i[1:]] - c_adj[i[:-1]]) / c_raa[i[:-1]]
    return R


def _drift(w: np.ndarray, r_es: float, r_zn: float) -> np.ndarray:
    a = w * (1.0 + r_es)
    return a / (a + (1.0 - w) * (1.0 + r_zn))


def taerskel_signal(R_es: np.ndarray, R_zn: np.ndarray, start: int = 0,
                    baand: np.ndarray = BAAND) -> np.ndarray:
    """§4c: s^δ_t pr. dag og bånd. w = 0,60 ved close på dag ``start``; før og på den dag
    er signalet nan."""
    s = np.full((len(R_es), len(baand)), np.nan)
    w = np.full(len(baand), W0)
    for t in range(start + 1, len(R_es)):
        wt = _drift(w, R_es[t], R_zn[t])
        s[t] = wt - W0
        w = np.where(np.abs(s[t]) >= baand, W0, wt)
    return s


def kalender_signal(R_es: np.ndarray, R_zn: np.ndarray, sidste: np.ndarray,
                    start: int = 0) -> np.ndarray:
    """§4d: c_t, driften siden forrige måneds sidste XNYS-dag, før rebalanceringen."""
    c = np.full(len(R_es), np.nan)
    w = W0
    for t in range(start + 1, len(R_es)):
        wt = float(_drift(np.array(w), R_es[t], R_zn[t]))
        c[t] = wt - W0
        w = W0 if sidste[t] else wt
    return c


@dataclass
class Signal:
    dage: pd.DatetimeIndex
    R_es: np.ndarray
    R_zn: np.ndarray
    s: np.ndarray                    # (dage, 26)
    T: np.ndarray
    c: np.ndarray
    efter: np.ndarray                # sessioner efter t i måneden
    foer: np.ndarray                 # sessioner før t i måneden
    info: dict = field(default_factory=dict)


def byg_signal(df_es: pd.DataFrame, df_zn: pd.DataFrame, dage: pd.DatetimeIndex) -> Signal:
    """§4b-§4d fra de to 1m-serier."""
    ud = {}
    for navn, df in (("ES", df_es), ("ZN", df_zn)):
        adj, _ = k2.forskelsjuster(df)
        i, f = signal_close(_ns(df.index), dage)
        ud[navn] = (dagsafkast(adj["close"].to_numpy(float), df["close"].to_numpy(float), i),
                    f)
    return signal_fra_afkast(ud["ES"][0], ud["ZN"][0], dage, ud["ES"][1], ud["ZN"][1])


def signal_fra_afkast(R_es, R_zn, dage, f_es=None, f_zn=None) -> Signal:
    dage = pd.DatetimeIndex(dage).as_unit("ns")
    efter, foer = maanedens_plads(dage)
    s = taerskel_signal(R_es, R_zn)
    c = kalender_signal(R_es, R_zn, efter == 0)
    info = {}
    for navn, f in (("ES", f_es), ("ZN", f_zn)):
        if f is not None:
            info[f"signalbar_mangler_{navn}_n"] = int((f > 0).sum())
            info[f"signalbar_over_5_min_{navn}_n"] = int((f > MAKS_FORSINK_MIN).sum())
            info[f"signalbar_mangler_{navn}_dage"] = [str(d.date()) for d, x in zip(dage, f)
                                                     if x > 0]
    return Signal(dage=dage, R_es=np.asarray(R_es, float), R_zn=np.asarray(R_zn, float),
                  s=s, T=s.mean(axis=1), c=c, efter=efter, foer=foer, info=info)


# ---------------------------------------------------------------------------
# Positionerne, §4e
# ---------------------------------------------------------------------------

def position_T(T: np.ndarray) -> np.ndarray:
    """§4e: ``w^T = −T / 0,015``; signal 0 giver 0."""
    w = -np.asarray(T, float) / SKALA_T
    return np.where(w == 0, 0.0, w)


def position_K(c: np.ndarray, efter: np.ndarray, foer: np.ndarray) -> np.ndarray:
    """§4e og læsning 6: sign(−c_t) på månedens 5 sidste XNYS-dage, sign(c_(t−4)) på
    månedens første, ellers 0."""
    c = np.asarray(c, float)
    w = np.zeros(len(c))
    sidste = efter <= K_SIDSTE - 1
    w[sidste] = np.sign(-c[sidste])
    j = np.flatnonzero((foer == 0) & ~sidste)
    j = j[j >= 4]
    w[j] = np.sign(c[j - 4])
    return np.nan_to_num(w, nan=0.0) + 0.0


def positioner(sig: Signal) -> dict:
    wT = position_T(sig.T)
    wK = position_K(sig.c, sig.efter, sig.foer)
    return {T_VAR: wT, K_VAR: wK, "C": 0.5 * (wT + wK), "T_hel": np.round(wT) + 0.0}


# ---------------------------------------------------------------------------
# Topstep-dagen og handlen, §4f-§4g
# ---------------------------------------------------------------------------

def handelsdage(dage: pd.DatetimeIndex) -> np.ndarray:
    """Læsning 1: indeks i ``dage`` for signaldagene t, hvis næste dag d er en handelsdag."""
    dage = pd.DatetimeIndex(dage)
    j = np.arange(len(dage) - 1)
    return j[dage[1:] >= HANDEL_START]


def topstep_tider(d: pd.DatetimeIndex) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(indgang, udgang, 08:30) i UTC ns for handelsdagene d. Læsning 7."""
    d = pd.DatetimeIndex(d).as_unit("ns").normalize()
    ind = (d - pd.Timedelta(days=1) + INDGANG).tz_localize(CT).tz_convert("UTC")
    ud = (d + UDGANG).tz_localize(CT).tz_convert("UTC")
    midt = (d + MIDT).tz_localize(CT).tz_convert("UTC")
    _, luk = rth_tider(d)
    luk_ct = pd.DatetimeIndex(luk).tz_localize("UTC").tz_convert(CT)
    kort = np.asarray(luk_ct.hour * 60 + luk_ct.minute < 15 * 60)
    ud_ns = np.where(kort, luk - KORTDAG_FOER.value, _ns(ud))
    return _ns(ind), ud_ns, _ns(midt)


def udgang(t_ns: np.ndarray, nominel: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Læsning 7: (serieindeks, præcis bar fundet, minutter før det nominelle tidspunkt).
    Præcis: baren der starter på tidspunktet (open). Ellers den seneste bar før (close)."""
    i = np.searchsorted(t_ns, nominel, side="left")
    ic = np.minimum(i, len(t_ns) - 1)
    praecis = (i < len(t_ns)) & (t_ns[ic] == nominel)
    j = np.where(praecis, ic, i - 1)
    foer = np.where(j >= 0, (nominel - t_ns[np.maximum(j, 0)]) / MIN_NS, np.inf)
    return np.maximum(j, 0), praecis, np.where(praecis, 0.0, foer)


@dataclass
class Handel:
    symbol: str
    t_pos: np.ndarray                # signaldagens plads i Signal.dage, pr. handelsdag
    dage: pd.DatetimeIndex           # handelsdagene d
    t_ns: np.ndarray
    o: np.ndarray                    # forskelsjusteret
    c: np.ndarray
    o_raa: np.ndarray
    c_raa: np.ndarray
    iid: np.ndarray
    ind: np.ndarray
    f_ind: np.ndarray
    ud: np.ndarray
    praecis: np.ndarray
    f_ud: np.ndarray
    midt: np.ndarray
    med: np.ndarray
    grund: np.ndarray
    L_ref: float
    usd_pt: float
    omk: float
    sig_i: np.ndarray                # signalbar på handelsinstrumentet pr. signaldag
    ruller: pd.DataFrame
    info: dict = field(default_factory=dict)

    @property
    def n(self) -> int:
        return len(self.dage)

    @property
    def ud_pris(self) -> np.ndarray:
        return np.where(self.praecis, self.o[self.ud], self.c[self.ud])

    @property
    def sidste(self) -> np.ndarray:
        """Sidste bar hvis close er på stien."""
        return np.where(self.praecis, self.ud - 1, self.ud)

    @property
    def L(self) -> np.ndarray:
        return self.o_raa[self.ind]

    @property
    def skala(self) -> np.ndarray:
        return self.L_ref / self.L

    @property
    def pt(self) -> np.ndarray:
        return self.ud_pris - self.o[self.ind]

    @property
    def G(self) -> np.ndarray:
        """Brutto i $ pr. enhed long (w = 1), §4g."""
        return self.pt * self.skala * self.usd_pt

    @property
    def aar(self) -> np.ndarray:
        return self.dage.year.to_numpy()


def byg_handel(df: pd.DataFrame, sig_dage: pd.DatetimeIndex, symbol: str,
               oekonomi: tuple | None = None) -> Handel:
    """Handelsdagene, udførelsen og udelukkelserne for ét instrument. Ingen P&L."""
    if not df.index.is_monotonic_increasing or df.index.has_duplicates:
        raise ValueError("serien skal være sorteret og uden dubletter")
    L_ref, usd_pt, omk = oekonomi or OEKONOMI[symbol]
    sig_dage = pd.DatetimeIndex(sig_dage).as_unit("ns")
    adj, ruller = k2.forskelsjuster(df)
    t_ns = _ns(df.index)
    tp = handelsdage(sig_dage)
    d = sig_dage[tp + 1]
    ind_nom, ud_nom, midt_nom = topstep_tider(d)
    ind, f_ind = k6.udfoer(t_ns, ind_nom)
    ud, praecis, f_ud = udgang(t_ns, ud_nom)
    midt, _ = k6.udfoer(t_ns, midt_nom)
    grund = np.full(len(d), "", dtype=object)
    sen_ud = f_ud > MAKS_FORSINK_MIN
    foer_ind = ud < ind
    sen_ind = f_ind > MAKS_FORSINK_MIN
    grund[sen_ud | foer_ind] = "udgang mangler (over 5 min)"
    grund[sen_ind] = "indgang over 5 min forsinket"
    grund[sen_ind & (sen_ud | foer_ind)] = "ingen barer i Topstep-dagen"
    med = grund == ""
    iid = (df["instrument_id"].to_numpy() if "instrument_id" in df.columns
           else np.zeros(len(df), dtype=np.int64))
    sig_i, _ = signal_close(t_ns, sig_dage)
    h = Handel(symbol=symbol, t_pos=tp, dage=d, t_ns=t_ns, o=adj["open"].to_numpy(float),
               c=adj["close"].to_numpy(float), o_raa=df["open"].to_numpy(float),
               c_raa=df["close"].to_numpy(float), iid=iid, ind=ind, f_ind=f_ind, ud=ud,
               praecis=praecis, f_ud=f_ud, midt=np.minimum(midt, ud), med=med, grund=grund,
               L_ref=L_ref, usd_pt=usd_pt, omk=omk, sig_i=sig_i, ruller=ruller)
    h.info = {
        "symbol": symbol, "n_1m": len(df), "handelsdage_n": len(d),
        "handelsdage_med_n": int(med.sum()),
        **{f"udelukket_{g}_n": int((grund == g).sum())
           for g in ("indgang over 5 min forsinket", "udgang mangler (over 5 min)",
                     "ingen barer i Topstep-dagen")},
        "indgang_forsinket_1_5_n": int((med & (f_ind > 0)).sum()),
        "udgang_tidligere_bar_n": int((med & ~praecis).sum()),
        "kortdage_n": int((ud_nom != _ns(pd.DatetimeIndex(d).normalize().tz_localize(CT)
                                         + UDGANG)).sum()),
        "ruller_i_vinduet_n": int((med & (iid[ind] != iid[np.maximum(ud, ind)])).sum()),
        "ruller_n": len(ruller),
    }
    return h


def dag_pnl(h: Handel, w: np.ndarray, omk: float | None = None) -> dict:
    """§4g pr. handelsdag. ``w`` er pr. signaldag (Signal.dage)."""
    omk = h.omk if omk is None else omk
    wd = np.asarray(w, float)[h.t_pos]
    brutto = wd * h.G
    netto = brutto - np.abs(wd) * omk
    nominelt = wd * h.pt * h.usd_pt - np.abs(wd) * omk
    aktiv = h.med & (wd != 0)
    return {"w": wd, "brutto": brutto, "netto": netto, "nominelt": nominelt, "aktiv": aktiv}


def lang_hele_dagen(h: Handel) -> dict:
    """§6: long 1 enhed hver dag fra indgang til udgang."""
    return {"brutto": h.G, "netto": h.G - h.omk, "med": h.med.copy()}


# ---------------------------------------------------------------------------
# §6: N-retning
# ---------------------------------------------------------------------------

def fortegn(rep: int, n: int) -> np.ndarray:
    """Læsning 10: ±1 pr. handelsdag, deterministisk pr. (gentagelse, dag) og delt."""
    rng = np.random.default_rng([NRET_SEED, rep])
    return 2 * rng.integers(0, 2, size=n) - 1


def nret_gentagelse(h: Handel, ws: dict, rep: int, omk: float | None = None) -> dict:
    """Én gentagelse: middel netto pr. aktiv dag for hver position i ``ws``."""
    omk = h.omk if omk is None else omk
    s = fortegn(rep, h.n)
    G = h.G
    ud = {}
    for v, w in ws.items():
        a = np.abs(np.asarray(w, float)[h.t_pos])
        m = h.med & (a != 0)
        x = s * a * G - a * omk
        ud[v] = float(x[m].mean()) if m.any() else float("nan")
    return ud


# ---------------------------------------------------------------------------
# §7: σ_v, MDE, E_v og styrke — uden udfald
# ---------------------------------------------------------------------------

def rv(h: Handel) -> np.ndarray:
    """Læsning 12: ``RV_d`` i $² pr. enhed langs stien indgang → udgang."""
    dc = np.r_[0.0, np.diff(h.c)]
    cs = np.r_[0.0, np.cumsum(dc * dc)]
    ind, sidste = h.ind, np.maximum(h.sidste, h.ind)
    s = (h.c[ind] - h.o[ind]) ** 2 + (cs[sidste + 1] - cs[ind + 1])
    s = s + np.where(h.praecis, (h.o[h.ud] - h.c[sidste]) ** 2, 0.0)
    return s * (h.skala * h.usd_pt) ** 2


def sigma_v(h: Handel, w: np.ndarray, rv_d: np.ndarray | None = None) -> float:
    """§7: ``√(middel over aktive dage af w² × RV_d)``."""
    wd = np.asarray(w, float)[h.t_pos]
    m = h.med & (wd != 0)
    if not m.any():
        return float("nan")
    r = rv(h) if rv_d is None else rv_d
    return math.sqrt(float(np.mean((wd ** 2 * r)[m])))


def mde(sigma: float, n: int, z: float = Z_SIDAK2) -> float:
    return z * sigma / math.sqrt(n) if n > 0 else float("inf")


def signal_sd(x: np.ndarray) -> float:
    """Læsning 13: sd over alle signaldage med et signal."""
    x = np.asarray(x, float)
    return float(np.nanstd(x, ddof=1))


def e_v(h: Handel, sig: Signal, v: str, w: np.ndarray) -> float:
    """§7: ``middel over aktive dage af |w| × 0,00165 × |z| × L_ref × $/pt``."""
    x = sig.T if v == T_VAR else sig.c
    z = np.abs(x / signal_sd(x))[h.t_pos]
    wd = np.asarray(w, float)[h.t_pos]
    m = h.med & (wd != 0)
    e = np.abs(wd) * ARTIKEL_HAELDNING * z * h.L_ref * h.usd_pt
    if v == K_VAR:
        e = np.where(sig.foer[h.t_pos] == 0, 0.0, e)     # vendingen
    return float(np.mean(e[m])) if m.any() else float("nan")


def styrke_fwe(sigma: float, n: int, effekt: float) -> float:
    if n <= 0 or not sigma > 0:
        return float("nan")
    return float(norm.cdf(math.sqrt(n) * effekt / sigma - (Z_SIDAK2 - Z_80)))


def styrke_ci(sigma: float, n: int, effekt: float, omk: float) -> float:
    if n <= 0 or not sigma > 0:
        return float("nan")
    return float(norm.cdf(math.sqrt(n) * (effekt - omk) / sigma - (Z_CI - Z_80)))


# ---------------------------------------------------------------------------
# §8
# ---------------------------------------------------------------------------

def beslutning(raekker: dict, alfa: float = 0.05) -> dict:
    """§8, mekanisk. ``raekker`` er {variant: {"p_FWE", "ci95_lo"}}."""
    sig = [v for v, r in raekker.items() if r["p_FWE"] <= alfa]
    ci = [v for v, r in raekker.items() if r["ci95_lo"] > 0]
    begge = [v for v in sig if v in ci]
    if begge:
        frosset = max(begge, key=lambda v: raekker[v]["ci95_lo"])
        return {"raekke": 1, "variant": frosset, "kandidater": begge,
                "tekst": "Varianten fryses"}
    if sig:
        return {"raekke": 2, "variant": None, "kandidater": sig,
                "in_sample_fund": [v for v in ci if v not in sig],
                "tekst": "Parkeres som \"retningen bærer, men betaler ikke omkostningen\""}
    if ci:
        return {"raekke": 3, "variant": None, "kandidater": ci,
                "tekst": "Parkeres: gevinsten følger ikke signalets retning"}
    return {"raekke": 4, "variant": None, "kandidater": [], "tekst": "Kandidat 7 parkeres"}


# ---------------------------------------------------------------------------
# Nøgletal og diagnoser, §9-§10
# ---------------------------------------------------------------------------

_p, _middel, hit = k6._p, k6._middel, k6.hit


def _ci(x) -> tuple[float, float]:
    x = np.asarray(x, dtype=float)
    return mean_ci_t(x) if len(x) >= 2 else (float("nan"), float("nan"))


def skaevhed(x) -> float:
    x = np.asarray(x, float)
    if len(x) < 3 or x.std() == 0:
        return float("nan")
    return float(np.mean((x - x.mean()) ** 3) / x.std() ** 3)


def stoerste_tab(h: Handel, wd: np.ndarray, m: np.ndarray) -> np.ndarray:
    """Læsning 24: pr. aktiv dag og MES-enhed, ``min(0, …)``."""
    ind, sidste = h.ind[m], np.maximum(h.sidste[m], h.ind[m])
    if len(ind) == 0:
        return np.zeros(0)
    sg = np.sign(wd[m])
    n_bar = sidste - ind + 1
    dag = np.repeat(np.arange(len(ind)), n_bar)
    start = np.r_[0, np.cumsum(n_bar)[:-1]]
    i = np.arange(n_bar.sum()) - np.repeat(start, n_bar) + np.repeat(ind, n_bar)
    sk = h.skala[m]
    v = sg[dag] * (h.c[i] - h.o[ind][dag]) * sk[dag] * h.usd_pt - h.omk
    laveste = np.minimum.reduceat(v, start)
    slut = sg * h.pt[m] * sk * h.usd_pt - h.omk
    return np.minimum(0.0, np.minimum(laveste, slut))


def variant_tal(h: Handel, w: np.ndarray, omk: float | None = None) -> dict:
    """§10's hovedtabel uden nulmodellen."""
    p = dag_pnl(h, w, omk)
    m = p["aktiv"]
    b, n = p["brutto"][m], p["netto"][m]
    lo, hi = _ci(n)
    wd = p["w"][m]
    return {"aktive_dage_n": int(m.sum()),
            "andel_long": float((wd > 0).mean()) if m.any() else float("nan"),
            "andel_short": float((wd < 0).mean()) if m.any() else float("nan"),
            "middel_w": _middel(wd), "middel_abs_w": _middel(np.abs(wd)),
            "middel_brutto_usd": _middel(b), "middel_netto_usd": _middel(n),
            "ci95_lo": lo, "ci95_hi": hi,
            "netto_usd_pr_handelsdag": float(n.sum()) / max(int(h.med.sum()), 1),
            "_p": p}


def _seg(x, s) -> dict:
    lo, hi = _ci(x[s])
    return {"n": int(s.sum()), "netto": _middel(x[s]), "lo": lo, "hi": hi}


def k6_naetter() -> np.ndarray | None:
    """Læsning 17: kandidat 6's netto pr. dato d (V2 · salg, 0 uden handel)."""
    g = k6.byg_grundlag(k6.serie(k6.HOVED), k6.xnys_dage(k6.HOVED), k6.HOVED)
    hd = k6.handel(g, K6_VARIANT[0])
    m = g.maske(K6_VARIANT)
    return pd.Series(np.where(m, hd["netto_usd"], 0.0), index=g.dage)


def diagnoser(h: Handel, sig: Signal, ws: dict, tal: dict, p_fwe: dict | None = None,
              k6_netto: pd.Series | None = None) -> dict:
    """§9."""
    ud = {"variant": {}, "aar": [], "ekstra": {}}
    lh = lang_hele_dagen(h)
    mu = _middel(lh["brutto"][h.med])
    lo, hi = _ci(lh["netto"][h.med])
    ud["lang"] = {"n": int(h.med.sum()), "brutto": mu, "netto": _middel(lh["netto"][h.med]),
                  "lo": lo, "hi": hi}
    d = h.dage
    efter_t = sig.efter[h.t_pos]
    foer_t = sig.foer[h.t_pos]
    # K-dagens måned (læsning 19): vendingsdagen hører til forrige måned
    mnd_t = sig.dage[h.t_pos].month.to_numpy()
    mnd_forrige = sig.dage[np.maximum(h.t_pos - 1, 0)].month.to_numpy()
    k_mnd = np.where(foer_t == 0, mnd_forrige, mnd_t)
    kvartal = np.isin(k_mnd, (3, 6, 9, 12))
    i_m = np.minimum(h.midt, h.ud)
    for v in list(VARIANTER) + ["C", "T_hel"]:
        p = tal[v]["_p"] if v in tal else dag_pnl(h, ws[v])
        m = p["aktiv"]
        wd, b, n, nom = p["w"], p["brutto"], p["netto"], p["nominelt"]
        r = {}
        if v in ("C", "T_hel"):
            r.update(variant_tal(h, ws[v]))
            r.pop("_p")
        # driftjusteret
        dj = (b - wd * mu)[m]
        r["driftjusteret"] = _seg(dj, np.ones(len(dj), bool))
        r["korr_lang"] = _korr(np.where(m, n, 0.0)[h.med], lh["netto"][h.med])
        r["inden_artiklen"] = _seg(n, m & (d <= ARTIKEL_SLUT))
        r["efter_artiklen"] = _seg(n, m & (d > ARTIKEL_SLUT))
        r["uden_marts_2020"] = _seg(n, m & ~((d >= MARTS_2020[0]) & (d < MARTS_2020[1])))
        if v == K_VAR:
            r["kvartalsslut"] = _seg(n, m & kvartal)
            r["andre_maaneder"] = _seg(n, m & ~kvartal)
        if v == T_VAR:
            r["sidste_5"] = _seg(n, m & (efter_t <= 4))
            r["resten"] = _seg(n, m & (efter_t > 4))
        nat = wd * (h.o[i_m] - h.o[h.ind]) * h.skala * h.usd_pt
        rth = wd * (h.ud_pris - h.o[i_m]) * h.skala * h.usd_pt
        r["brutto_nat"] = _seg(nat, m)
        r["brutto_rth"] = _seg(rth, m)
        ci_t, ci_d = h.sig_i[h.t_pos], h.sig_i[h.t_pos + 1]
        cc = wd * (h.c[ci_d] - h.c[ci_t]) * (h.L_ref / h.c_raa[ci_t]) * h.usd_pt
        r["brutto_close_close"] = _seg(cc, m)
        n570 = b - np.abs(wd) * OMK_DIAGNOSE_USD
        r["netto_570"] = _seg(n570, m)
        aw = _middel(np.abs(wd[m]))
        r["breakeven_middel"] = _middel(b[m]) / aw if m.any() else float("nan")
        r["breakeven_CI"] = _ci(b[m])[0] / aw if m.any() else float("nan")
        r["nominelt"] = _seg(nom, m)
        hn, fn = hit(n[m])
        r.update({"hit_netto_pct": hn, "gevinst_tab_netto": fn, "skaevhed": skaevhed(n[m])})
        r.update({f"netto_p{q}": _p(n[m], q) for q in (1, 5, 50, 95, 99)})
        r.update({"netto_vaerst": float(n[m].min()) if m.any() else float("nan"),
                  "netto_bedst": float(n[m].max()) if m.any() else float("nan"),
                  "sd_aktiv": float(np.std(n[m], ddof=1)) if m.sum() > 1 else float("nan"),
                  "sd_handelsdag": float(np.std(np.where(m, n, 0.0)[h.med], ddof=1))})
        tab = stoerste_tab(h, wd, m)
        r.update({f"tab_i_dagen_p{q}": _p(tab, q) for q in (1, 5, 50)})
        r["tab_i_dagen_vaerst"] = float(tab.min()) if len(tab) else float("nan")
        if k6_netto is not None and v in VARIANTER:
            k6n = k6_netto.reindex(d).fillna(0.0).to_numpy()
            a = np.where(m, n, 0.0)[h.med]
            b6 = k6n[h.med]
            r["korr_k6"] = _korr(a, b6)
            sa, sb = np.std(a, ddof=1), np.std(b6, ddof=1)
            if sa > 0 and sb > 0:
                x = a / sa + b6 / sb
                r["sharpe_med_k6"] = float(math.sqrt(252) * x.mean() / x.std(ddof=1))
                r["sharpe_alene"] = float(math.sqrt(252) * a.mean() / sa)
                r["sharpe_k6"] = float(math.sqrt(252) * b6.mean() / sb)
        ud["variant"][v] = r
        if v in VARIANTER:
            for a_ in sorted(set(h.aar.tolist())):
                s = m & (h.aar == a_)
                lo, hi = _ci(n[s])
                ud["aar"].append({"variant": v, "aar": a_, "n": int(s.sum()),
                                  "netto": _middel(n[s]), "lo": lo, "hi": hi,
                                  "nominelt": _middel(nom[s])})
    if p_fwe is not None:
        ud["beslutning_570"] = beslutning(
            {v: {"p_FWE": p_fwe[v], "ci95_lo": ud["variant"][v]["netto_570"]["lo"]}
             for v in VARIANTER})
    return ud


def _korr(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 3 or a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def analyse(h: Handel, sig: Signal, n_reps: int = NRET_REPS,
            k6_netto: pd.Series | None = None) -> dict:
    """Ét instrument: tallene, N-retning, Westfall-Young, §8 og diagnoserne."""
    ws = positioner(sig)
    tal = {v: variant_tal(h, ws[v]) for v in VARIANTER}
    null = [nret_gentagelse(h, {v: ws[v] for v in VARIANTER}, r) for r in range(n_reps)]
    wy = k2.westfall_young({v: tal[v]["middel_netto_usd"] for v in VARIANTER},
                           {v: np.array([r[v] for r in null]) for v in VARIANTER})
    r_d = rv(h)
    for v in VARIANTER:
        pv = wy["pr_variant"][v]
        tal[v].update({f"N_retning_{k}": pv[k] for k in ("p5", "p50", "p95")})
        tal[v]["t_v"], tal[v]["p_FWE"] = pv["t"], pv["p_FWE"]
        s = sigma_v(h, ws[v], r_d)
        tal[v].update({"sigma_v": s, "MDE_sidak2": mde(s, tal[v]["aktive_dage_n"]),
                       "MDE_CI": mde(s, tal[v]["aktive_dage_n"], Z_CI)})
    afg = beslutning({v: {"p_FWE": tal[v]["p_FWE"], "ci95_lo": tal[v]["ci95_lo"]}
                      for v in VARIANTER})
    diag = diagnoser(h, sig, ws, tal, {v: tal[v]["p_FWE"] for v in VARIANTER}, k6_netto)
    return {"symbol": h.symbol, "tal": tal, "wy": wy, "beslutning": afg, "diag": diag,
            "optaelling": optaelling(h, sig), "R": n_reps}


def koer(n_reps: int = NRET_REPS) -> dict:
    """Den rigtige kørsel: ES afgør, NQ er kontrol."""
    dage = signal_dage()
    df_es = serie(ES)
    sig = byg_signal(df_es, serie(ZN), dage)
    k6n = k6_naetter()
    ud = {"signal": sig}
    for sym, df in ((ES, df_es), (NQ, serie(NQ))):
        h = byg_handel(df, dage, sym)
        ud[sym] = analyse(h, sig, n_reps, k6n)
    return ud


# ---------------------------------------------------------------------------
# §11.5: optællingen uden udfald
# ---------------------------------------------------------------------------

def optaelling(h: Handel, sig: Signal) -> dict:
    """§11.5. Ingen punktforskel i en handel indgår: ingen P&L, ingen hit ratio, intet
    udfald. (σ_v og RV er markedets egen svingning, E_v er artiklens tal.)"""
    ws = positioner(sig)
    tp = h.t_pos
    r_d = rv(h)
    varianter = []
    for v in VARIANTER:
        wd = ws[v][tp]
        m = h.med & (wd != 0)
        n = int(m.sum())
        s = sigma_v(h, ws[v], r_d)
        e = e_v(h, sig, v, ws[v])
        omk_v = _middel(np.abs(wd[m])) * h.omk
        r = {"variant": v, "aktive_dage_n": n,
             "andel_long": float((wd[m] > 0).mean()) if n else float("nan"),
             "andel_short": float((wd[m] < 0).mean()) if n else float("nan"),
             "middel_abs_w": _middel(np.abs(wd[m])), "omk_pr_aktiv_dag": omk_v,
             "sigma_v": s, "MDE_sidak2": mde(s, n), "MDE_CI": mde(s, n, Z_CI), "E_v": e}
        for navn, eff in (("E", e), ("E_halv", e / 2)):
            r[f"styrke_FWE_{navn}"] = styrke_fwe(s, n, eff)
            r[f"styrke_CI_{navn}"] = styrke_ci(s, n, eff, omk_v)
        if v == T_VAR:
            r.update({f"w_p{q}": _p(wd[m], q) for q in (5, 50, 95)})
        varianter.append(r)
    aar_rows = []
    for a in sorted(set(h.aar.tolist())):
        s = h.med & (h.aar == a)
        med_L = _p(h.L[s], 50)
        aar_rows.append({"aar": a, "handelsdage_n": int(s.sum()), "L_median": med_L,
                         "omk_bp": h.omk / (h.usd_pt * med_L) * 1e4 if s.any()
                         else float("nan")})
    t_mask = np.zeros(len(sig.dage), bool)
    t_mask[tp] = True
    # opvarmningen: T med start 2016-02-01
    start2 = int(np.searchsorted(sig.dage, OPVARM_ALT))
    T2 = taerskel_signal(sig.R_es, sig.R_zn, start=start2).mean(axis=1)
    efter_d, foer_d = sig.efter[tp + 1], sig.foer[tp + 1]
    sidste_t = sig.efter[tp] == 0
    udel = [{"dag": str(d.date()), "grund": g} for d, g in zip(h.dage, h.grund) if g]
    rul = h.ruller
    i_vind = h.med & (h.iid[h.ind] != h.iid[np.maximum(h.ud, h.ind)])
    return {
        "serie": dict(h.info), "signal": {k: v for k, v in sig.info.items()
                                          if not k.endswith("_dage")},
        "signal_mangler_dage": {k: v for k, v in sig.info.items() if k.endswith("_dage")},
        "varianter": varianter, "aar": aar_rows, "udelukket": udel,
        "ruller_i_vinduet": [str(d.date()) for d, x in zip(h.dage, i_vind) if x],
        "ruller_n": len(rul),
        "maanedsslut_n": int((h.med & sidste_t).sum()),
        "kvartalsslut_n": int((h.med & sidste_t
                               & np.isin(sig.dage[tp].month, (3, 6, 9, 12))).sum()),
        "sd_T": signal_sd(sig.T), "sd_c": signal_sd(sig.c),
        "korr_T_opvarmning": _korr(sig.T[t_mask], T2[t_mask]),
        "korr_wT_R_es": _korr(position_T(sig.T)[t_mask], sig.R_es[t_mask]),
        "_d_efter": efter_d, "_d_foer": foer_d,
    }


# ---------------------------------------------------------------------------
# Formatering
# ---------------------------------------------------------------------------

def _rel(sti: Path) -> str:
    return Path(sti).resolve().relative_to(ROOT.resolve()).as_posix()


_t = k2._t


def _usd(x, nd: int = 2) -> str:
    return _t(x, nd)


def _ci_txt(lo, hi, nd: int = 2) -> str:
    return f"[{_t(lo, nd)}; {_t(hi, nd)}]"


def _pct(x, nd: int = 0) -> str:
    return f"{_t(100 * x, nd)}%"


def optaelling_md(oo: dict, meta: dict) -> str:
    dele = [
        "# B4 kandidat 7 — optælling uden udfald (§11.5)",
        "",
        f"**Kørt:** {meta['koert_utc']} UTC fra `{meta['head'][:12]}` (arbejdskopien kan "
        "indeholde ucommittet modul og tests). Præregistrering "
        f"`{_rel(PREREG)}`. Ingen P&L, ingen hit ratio, intet udfald.",
        "",
    ]
    for sym, o in oo.items():
        s, sg = o["serie"], o["signal"]
        navn = "ES (MES-økonomi, afgør)" if sym == ES else "Nasdaq-kontrol (NQ, MNQ-økonomi)"
        dele += [f"## {navn}", "", "| emne | antal |", "|---|---|",
                 f"| 1m-barer | {_t(s['n_1m'], 0)} |",
                 f"| handelsdage i alt (d 2016-04-01 → 2023-12-29) | "
                 f"{_t(s['handelsdage_n'], 0)} |",
                 f"| udelukket: indgang over 5 min forsinket | "
                 f"{s['udelukket_indgang over 5 min forsinket_n']} |",
                 f"| udelukket: udgang mangler (over 5 min) | "
                 f"{s['udelukket_udgang mangler (over 5 min)_n']} |",
                 f"| udelukket: ingen barer i Topstep-dagen | "
                 f"{s['udelukket_ingen barer i Topstep-dagen_n']} |",
                 f"| handelsdage med | {_t(s['handelsdage_med_n'], 0)} |",
                 f"| indgang forsinket 1–5 min | {s['indgang_forsinket_1_5_n']} |",
                 f"| udgang fra tidligere bar (≤ 5 min) | {s['udgang_tidligere_bar_n']} |",
                 f"| kortdage | {s['kortdage_n']} |",
                 f"| ruller i serien / i vinduet | {o['ruller_n']} / "
                 f"{s['ruller_i_vinduet_n']} |",
                 f"| manglende signalbarer ES (heraf over 5 min) | "
                 f"{sg.get('signalbar_mangler_ES_n', '—')} "
                 f"({sg.get('signalbar_over_5_min_ES_n', '—')}) |",
                 f"| manglende signalbarer ZN (heraf over 5 min) | "
                 f"{sg.get('signalbar_mangler_ZN_n', '—')} "
                 f"({sg.get('signalbar_over_5_min_ZN_n', '—')}) |",
                 f"| månedsslut / kvartalsslut blandt signaldagene | {o['maanedsslut_n']} / "
                 f"{o['kvartalsslut_n']} |",
                 ""]
        if o["udelukket"]:
            dele += ["Udelukkede dage: " + ", ".join(f"{u['dag']} ({u['grund']})"
                                                     for u in o["udelukket"]), ""]
        if o["ruller_i_vinduet"]:
            dele += ["Ruller i vinduet: " + ", ".join(o["ruller_i_vinduet"]), ""]
        dele += ["| variant | aktive dage | andel long | andel short | middel \\|w\\| | "
                 "omk. pr. aktiv dag | σ_v | MDE_sidak2 | MDE_CI | E_v | styrke FWE mod E_v | "
                 "mod E_v/2 | styrke CI mod E_v | mod E_v/2 |",
                 "|" + "---|" * 14]
        for r in o["varianter"]:
            dele.append(
                f"| {NAVN[r['variant']]} | {_t(r['aktive_dage_n'], 0)} | "
                f"{_pct(r['andel_long'])} | {_pct(r['andel_short'])} | "
                f"{_t(r['middel_abs_w'], 3)} | {_usd(r['omk_pr_aktiv_dag'])} | "
                f"{_usd(r['sigma_v'], 1)} | **{_usd(r['MDE_sidak2'], 1)}** | "
                f"{_usd(r['MDE_CI'], 1)} | **{_usd(r['E_v'], 1)}** | "
                f"{_pct(r['styrke_FWE_E'])} | {_pct(r['styrke_FWE_E_halv'])} | "
                f"{_pct(r['styrke_CI_E'])} | {_pct(r['styrke_CI_E_halv'])} |")
        rT = o["varianter"][0]
        dele += ["", f"w^T: p5 {_t(rT['w_p5'], 3)}, p50 {_t(rT['w_p50'], 3)}, "
                 f"p95 {_t(rT['w_p95'], 3)}, middel |w| {_t(rT['middel_abs_w'], 3)}. "
                 f"sd(T) {_t(o['sd_T'], 5)}, sd(c) {_t(o['sd_c'], 5)}.",
                 f"Korrelation T (start første close 2016) mod T (start 2016-02-01) over "
                 f"handelsdagene: {_t(o['korr_T_opvarmning'], 4)}. Korrelation w^T mod ES' "
                 f"afkast på t: {_t(o['korr_wT_R_es'], 3)}.", "",
                 "| år | handelsdage | median L_d | omkostning i bp (historisk niveau) |",
                 "|---|---|---|---|"]
        for r in o["aar"]:
            dele.append(f"| {r['aar']} | {r['handelsdage_n']} | {_t(r['L_median'], 2)} | "
                        f"{_t(r['omk_bp'], 2)} |")
        dele.append("")
    return "\n".join(dele)


def optaelling_csv(oo: dict) -> pd.DataFrame:
    rows = []
    for sym, o in oo.items():
        for r in o["varianter"]:
            rows.append({"symbol": sym, "tabel": "variant", **r})
        for r in o["aar"]:
            rows.append({"symbol": sym, "tabel": "aar", **r})
        rows.append({"symbol": sym, "tabel": "serie", **o["serie"], **o["signal"],
                     "maanedsslut_n": o["maanedsslut_n"], "kvartalsslut_n": o["kvartalsslut_n"],
                     "sd_T": o["sd_T"], "sd_c": o["sd_c"],
                     "korr_T_opvarmning": o["korr_T_opvarmning"],
                     "korr_wT_R_es": o["korr_wT_R_es"]})
    return pd.DataFrame(rows)


def hovedtabel_md(res: dict) -> str:
    ud = ["| variant | aktive_dage_n | andel_long | middel_brutto_usd | middel_netto_usd | "
          "CI95_netto | N_retning_p5/p50/p95 | t_v | p_FWE | netto_usd_pr_handelsdag | "
          "MDE_sidak2 | MDE_CI |", "|" + "---|" * 12]
    for v in VARIANTER:
        t = res["tal"][v]
        ud.append(
            f"| {NAVN[v]} | {_t(t['aktive_dage_n'], 0)} | {_pct(t['andel_long'])} | "
            f"{_usd(t['middel_brutto_usd'])} | **{_usd(t['middel_netto_usd'])}** | "
            f"{_ci_txt(t['ci95_lo'], t['ci95_hi'])} | {_usd(t['N_retning_p5'])}/"
            f"{_usd(t['N_retning_p50'])}/{_usd(t['N_retning_p95'])} | {_t(t['t_v'], 2)} | "
            f"**{_t(t['p_FWE'], 3)}** | {_usd(t['netto_usd_pr_handelsdag'])} | "
            f"{_usd(t['MDE_sidak2'], 1)} | {_usd(t['MDE_CI'], 1)} |")
    return "\n".join(ud)


def _beslutning_md(afg: dict) -> str:
    v = NAVN.get(afg.get("variant"), "—")
    kand = ", ".join(NAVN[x] for x in afg["kandidater"]) or "ingen"
    return f"**Række {afg['raekke']}:** {afg['tekst']}. Frosset: {v}. Kandidater: {kand}."


def _seg_txt(s: dict) -> str:
    return f"{_usd(s['netto'])} {_ci_txt(s['lo'], s['hi'])} (n {s['n']})"


def _diag_md(res: dict) -> list[str]:
    dg = res["diag"]
    ud = [f"Long hele Topstep-dagen: brutto {_usd(dg['lang']['brutto'])}, netto "
          f"{_usd(dg['lang']['netto'])} {_ci_txt(dg['lang']['lo'], dg['lang']['hi'])} "
          f"(n {dg['lang']['n']}).", ""]
    rows = [("korrelation med kandidat 6", lambda r: _t(r.get("korr_k6"), 3)),
            ("Sharpe alene / kandidat 6 / sammen (lige risiko)",
             lambda r: f"{_t(r.get('sharpe_alene'), 2)} / {_t(r.get('sharpe_k6'), 2)} / "
                       f"{_t(r.get('sharpe_med_k6'), 2)}"),
            ("korrelation med long hele dagen", lambda r: _t(r["korr_lang"], 3)),
            ("driftjusteret brutto", lambda r: _seg_txt(r["driftjusteret"])),
            ("inden for artiklens prøve", lambda r: _seg_txt(r["inden_artiklen"])),
            ("efter artiklens prøve", lambda r: _seg_txt(r["efter_artiklen"])),
            ("uden marts 2020", lambda r: _seg_txt(r["uden_marts_2020"])),
            ("K: kvartalsslut / andre", lambda r: (_seg_txt(r["kvartalsslut"]) + " / "
                                                   + _seg_txt(r["andre_maaneder"]))
             if "kvartalsslut" in r else "—"),
            ("T: 5 sidste dage / resten", lambda r: (_seg_txt(r["sidste_5"]) + " / "
                                                     + _seg_txt(r["resten"]))
             if "sidste_5" in r else "—"),
            ("brutto nat / RTH", lambda r: _seg_txt(r["brutto_nat"]) + " / "
             + _seg_txt(r["brutto_rth"])),
            ("brutto close → close", lambda r: _seg_txt(r["brutto_close_close"])),
            ("netto ved $5,70", lambda r: _seg_txt(r["netto_570"])),
            ("break-even pr. round trip, middel / CI-nedre",
             lambda r: f"{_usd(r['breakeven_middel'])} / {_usd(r['breakeven_CI'])}"),
            ("nominelt", lambda r: _seg_txt(r["nominelt"])),
            ("hit ratio / gevinst-tab / skævhed",
             lambda r: f"{_t(r['hit_netto_pct'], 1)}% / {_t(r['gevinst_tab_netto'], 2)} / "
                       f"{_t(r['skaevhed'], 2)}"),
            ("netto p1/p5/p50/p95/p99", lambda r: "/".join(_usd(r[f"netto_p{q}"], 0)
                                                         for q in (1, 5, 50, 95, 99))),
            ("værste / bedste dag", lambda r: f"{_usd(r['netto_vaerst'], 0)} / "
                                              f"{_usd(r['netto_bedst'], 0)}"),
            ("σ pr. aktiv dag / pr. handelsdag", lambda r: f"{_usd(r['sd_aktiv'], 0)} / "
                                                          f"{_usd(r['sd_handelsdag'], 0)}"),
            ("største tab i dagen pr. enhed p1/p5/p50/værst",
             lambda r: "/".join(_usd(r[f"tab_i_dagen_{q}"], 0)
                                for q in ("p1", "p5", "p50", "vaerst")))]
    kol = list(VARIANTER) + ["C", "T_hel"]
    ud += ["| diagnose | " + " | ".join(NAVN[v] for v in kol) + " |",
           "|" + "---|" * (len(kol) + 1)]
    for navn, f in rows:
        ud.append(f"| {navn} | " + " | ".join(f(dg["variant"][v]) for v in kol) + " |")
    for v in ("C", "T_hel"):
        r = dg["variant"][v]
        ud.append("")
        ud.append(f"{NAVN[v]}: aktive dage {r['aktive_dage_n']}, netto "
                  f"{_usd(r['middel_netto_usd'])} {_ci_txt(r['ci95_lo'], r['ci95_hi'])}.")
    if "beslutning_570" in dg:
        ud += ["", "Rækken ved $5,70: " + _beslutning_md(dg["beslutning_570"])]
    ud += ["", "| variant | år | aktive dage | netto [CI] | nominelt |", "|---|---|---|---|---|"]
    for r in dg["aar"]:
        ud.append(f"| {NAVN[r['variant']]} | {r['aar']} | {r['n']} | {_usd(r['netto'])} "
                  f"{_ci_txt(r['lo'], r['hi'])} | {_usd(r['nominelt'])} |")
    return ud


def skriv_md(res: dict, meta: dict) -> str:
    dele = ["# B4 kandidat 7 — rebalancering: resultat", "",
            f"**Kørt:** {meta['koert_utc']} UTC fra `{meta['head'][:12]}`. R = "
            f"{res[ES]['R']}. Præregistrering `{_rel(PREREG)}`.", ""]
    for sym in (ES, NQ):
        r = res[sym]
        navn = "ES (MES-økonomi, afgør)" if sym == ES else "Nasdaq-kontrol (afgør intet)"
        dele += [f"## Hovedtabel — {navn}", "", hovedtabel_md(r), "",
                 "### §8 anvendt mekanisk" + ("" if sym == ES else " (kun til orientering)"),
                 "", _beslutning_md(r["beslutning"]), "", "### Diagnoser", ""]
        dele += _diag_md(r)
        dele.append("")
    return "\n".join(dele)


def lang_tabel(res: dict) -> pd.DataFrame:
    rows = []
    for sym in (ES, NQ):
        if sym not in res:
            continue
        r = res[sym]
        for v in VARIANTER:
            t = {k: x for k, x in r["tal"][v].items() if not k.startswith("_")}
            rows.append({"symbol": sym, "tabel": "hoved", "variant": v, **t})
        for v, d in r["diag"]["variant"].items():
            flad = {}
            for k, x in d.items():
                if isinstance(x, dict):
                    flad.update({f"{k}_{kk}": xx for kk, xx in x.items()})
                else:
                    flad[k] = x
            rows.append({"symbol": sym, "tabel": "diagnose", "variant": v, **flad})
        for a in r["diag"]["aar"]:
            rows.append({"symbol": sym, "tabel": "aar", **a})
        rows.append({"symbol": sym, "tabel": "lang", **r["diag"]["lang"]})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# §11.4: regressionstjek
# ---------------------------------------------------------------------------

def regression_k6() -> dict:
    """Læsning 27: kandidat 6, NQ, V2 · salg: 902 nætter og $11,07 netto."""
    g = k6.byg_grundlag(k6.serie(k6.HOVED), k6.xnys_dage(k6.HOVED), k6.HOVED)
    hd = k6.handel(g, K6_VARIANT[0])
    t = k6.variant_tal(g, K6_VARIANT, hd)
    m = t["middel_netto_usd"]
    return {"naetter_n": t["naetter_n"], "middel_netto_usd": m,
            "ok": t["naetter_n"] == REGRESSION_K6_NAETTER_N
            and round(m, 2) == REGRESSION_K6_NETTO_USD}


def regressionstjek() -> dict:
    t0 = time.perf_counter()
    ud = k6.regressionstjek()
    ud["k6_v2_salg"] = regression_k6()
    ud["sekunder"] = time.perf_counter() - t0
    ud["ok"] = bool(ud["ok"] and ud["k6_v2_salg"]["ok"])
    return ud


# ---------------------------------------------------------------------------
# §11.6: tidsmålingen — uden P&L
# ---------------------------------------------------------------------------

def tidsmaaling(n_reps: int = 5) -> dict:
    """§11.6: ét gennemløb og ``n_reps`` N-retning-gentagelser, fremskrevet til R = 500.
    Returnerer kun tider og antal; P&L regnes inde i gennemløbet, men forlader det ikke."""
    t0 = time.perf_counter()
    dage = signal_dage()
    df_es, df_zn = serie(ES), serie(ZN)
    load_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    sig = byg_signal(df_es, df_zn, dage)
    h = byg_handel(df_es, dage, ES)
    grundlag_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    ws = positioner(sig)
    tal = {v: variant_tal(h, ws[v]) for v in VARIANTER}
    diagnoser(h, sig, ws, tal)
    for v in VARIANTER:
        sigma_v(h, ws[v])
    gennemloeb_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    for rep in range(n_reps):
        nret_gentagelse(h, {v: ws[v] for v in VARIANTER}, rep)
    nret_s = time.perf_counter() - t0
    pr_rep = nret_s / n_reps if n_reps else 0.0
    t0 = time.perf_counter()
    k2.westfall_young({v: 0.0 for v in VARIANTER},
                      {v: np.arange(NRET_REPS, dtype=float) for v in VARIANTER})
    wy_s = time.perf_counter() - t0
    forventet = load_s + grundlag_s + gennemloeb_s + pr_rep * NRET_REPS + wy_s
    return {"load_s": load_s, "grundlag_s": grundlag_s, "gennemloeb_s": gennemloeb_s,
            "n_reps": n_reps, "nret_s": nret_s, "pr_rep_s": pr_rep, "wy_s": wy_s,
            "forventet_s": forventet,
            "aktive_dage_n": {v: tal[v]["aktive_dage_n"] for v in VARIANTER}}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--regressionstjek", action="store_true",
                     help="§11.4: kandidat 1's tre tjek, simuler_handel, kandidat 2-6")
    grp.add_argument("--optaelling", action="store_true",
                     help="§11.5: optælling uden udfald. Skriver b4_k7_rebalancering_optaelling")
    grp.add_argument("--tidsmaaling", action="store_true",
                     help="§11.6: ét gennemløb og 5 N-retning-gentagelser, uden P&L")
    grp.add_argument("--koer", action="store_true",
                     help="§6-§10: den rigtige kørsel. Kræver ejerens godkendelse")
    ap.add_argument("--reps", type=int, default=NRET_REPS)
    ap.add_argument("--maalte-reps", type=int, default=5)
    args = ap.parse_args(argv)
    meta = {"koert_utc": pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M"),
            "head": k4._git("rev-parse", "HEAD").stdout.strip()}

    if args.regressionstjek:
        r = regressionstjek()
        ok = lambda x: "OK" if x else "AFVIGER"
        k1r, mo = r["k1"], r["motor"]
        print(f"Kandidat 1, 1. b4_k1_optaelling_v2.csv byte for byte: "
              f"{ok(k1r['csv_byte_for_byte'])}")
        print(f"Kandidat 1, 2. spor A: handler_n {k1r['motor_handler_n']}, middel_R_netto "
              f"{k1r['motor_middel_R_netto']:.4f}: {ok(k1r['motor_ok'])}")
        print(f"Kandidat 1, 3. scorefordelingen: {ok(k1r['score_ok'])}")
        for navn in ("standard", "eksplicit_2R"):
            x = mo[navn]
            print(f"simuler_handel, {navn}: handler_n {x['handler_n']}, middel_R_netto "
                  f"{x['middel_R_netto']:.4f}: {ok(x['ok'])}")
        for navn, x in (("Kandidat 2", r["k2_hovedvariant"]), ("Kandidat 3", r["k3_k1"]),
                        ("Kandidat 4", r["k4_k15_1"])):
            print(f"{navn}: handler_n {x['handler_n']}, middel_R_netto "
                  f"{x['middel_R_netto']:.4f}: {ok(x['ok'])}")
        x = r["k5_1m_uden"]
        print(f"Kandidat 5, 1m · uden middag: handler_n {x['handler_n']}, "
              f"middel_netto_usd_dag {x['middel_netto_usd_dag']:.2f}: {ok(x['ok'])}")
        x = r["k6_v2_salg"]
        print(f"Kandidat 6, NQ 07:30-09:30 · efter salg: naetter_n {x['naetter_n']} (ventet "
              f"{REGRESSION_K6_NAETTER_N}), middel_netto_usd {x['middel_netto_usd']:.2f} "
              f"(ventet {REGRESSION_K6_NETTO_USD:.2f}): {ok(x['ok'])}")
        print(f"Tid: {r['sekunder']:.0f} s")
        if not r["ok"]:
            sys.exit(1)
        return

    if args.optaelling:
        dage = signal_dage()
        df_es = serie(ES)
        sig = byg_signal(df_es, serie(ZN), dage)
        oo = {ES: optaelling(byg_handel(df_es, dage, ES), sig),
              NQ: optaelling(byg_handel(serie(NQ), dage, NQ), sig)}
        md = optaelling_md(oo, meta)
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "b4_k7_rebalancering_optaelling.md").write_text(md, encoding="utf-8")
        optaelling_csv(oo).to_csv(OUT / "b4_k7_rebalancering_optaelling.csv", index=False)
        print(md)
        return

    if args.tidsmaaling:
        t = tidsmaaling(args.maalte_reps)
        print(f"ES: indlæsning ES+ZN {t['load_s']:.1f} s, signal og handelsgrundlag "
              f"{t['grundlag_s']:.1f} s, P&L, nøgletal, diagnoser og σ_v {t['gennemloeb_s']:.2f} s")
        print(f"N-retning: {t['n_reps']} gentagelser {t['nret_s']:.3f} s, "
              f"{t['pr_rep_s'] * 1000:.2f} ms pr. gentagelse. Westfall-Young {t['wy_s']:.3f} s")
        print(f"Fremskrevet til R = {NRET_REPS}: {t['forventet_s']:.0f} s for ES; NQ-kontrollen "
              f"og kandidat 6's nætter kommer oveni")
        print(f"aktive_dage_n: {t['aktive_dage_n']}")
        return

    commits = k1.committede(COMMITTEDE)
    res = koer(n_reps=args.reps)
    meta["commits"] = commits
    md = skriv_md(res, meta)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "b4_k7_rebalancering.md").write_text(md, encoding="utf-8")
    lang_tabel(res).to_csv(OUT / "b4_k7_rebalancering.csv", index=False)
    print(md)


if __name__ == "__main__":
    main()
