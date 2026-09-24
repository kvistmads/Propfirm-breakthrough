"""B4 kandidat 1 — trin 2: videoens otte kriterier som score.

Præregistreret i ``research/prereg/b4_k1_trin2.md``. Definitionerne af de syv kriterier
står i ``research/prereg/b4_k1_trin2_optaelling.md`` §3b med de fire præciseringer i
tillægget; de er implementeret i ``research/b4_k1_filtre.py``, som står uændret. Motoren
er den rettede fra ``research/b4_k1_trinA.py`` (motorrettelse 1-3), og kernen er
``research/b4_k1_optaelling.py`` (kerne v2). Ingen af de tre moduler røres her.

    .venv/bin/python -m research.b4_k1_trin2 --regressionstjek
    .venv/bin/python -m research.b4_k1_trin2 --tidsmaaling
    .venv/bin/python -m research.b4_k1_trin2 --koer

Pris hentes kun gennem ``data.holdout.load_in_sample``; holdout åbnes ikke.

## Hvad kørslen afgør, §1

1. **Hovedtesten, §4:** stiger middel netto-R med scoren? Enheden er *skyggehandler* —
   hvert signal simuleres for sig, uden disciplinreglerne. Statistikken er hældningen β i
   en OLS af ``R_netto`` på scoren (0, 1, 2, 3, 4, 5+), med klyngerobust standardfejl pr.
   handelsdag. Én-sidet, H1: β > 0, α = 0,025 pr. spor (Bonferroni over 2).
2. **Varianterne, §5:** fire pr. spor — brud alene, score ≥ 2, ≥ 3, ≥ 4 — hver handlet
   med disciplinreglerne. Westfall-Young maks-statistik over alle otte på tværs af
   sporene, med N1 som nulmodel, R = 500.

## De tre motorer og hvorfor der kun er én

``gennemloeb`` er modulets eneste handelsgennemløb. Den gør tre ting med samme kode:

- ``disciplin=True`` er trin A's dagsgennemløb: én afgjort handel om dagen, to BE-udgange
  lukker dagen. Det er varianterne, §5.
- ``disciplin=False`` er skyggehandlerne, §4: hvert signal for sig, ingen dagsdisciplin.
- ``bedste_fald=True`` vender regel 4's antagelse om, §8.

``gennemloeb(disciplin=True, bedste_fald=False)`` med ``bar_min=15`` gengiver
``b4_k1_trinA.handler_for_variant`` handel for handel — testet i
``tests/test_b4_k1_trin2.py`` og igen af §10's regressionstjek 2 på den rigtige serie.
``motor`` gengiver tilsvarende ``b4_k1_trinA.simuler_handel`` når ``bedste_fald=False``.
Motoren er altså trin A's, med tre tilføjelser der ikke ændrer et eneste tal på spor A:
berøringsbarens længde som argument (trin A kendte kun 15m og havde ``k1.BAR`` hårdkodet
— på spor B's 5m-barer ville den lede efter fyldningen tre barer frem), flaget
``tvetydig``, og bedste-fald-grenen.

## Tvetydige minutter, §8

``tvetydig`` sættes for en handel hvor regel 4's antagelse faktisk bandt: i den bar hvor
stoppet blev ramt, kunne **også** målet eller BE-triggeren nås. Det er præcis §8's
formulering ("når stop og mål — eller stop og BE-trigger — ligger i samme 1m-bar"), og
det er kun i de handler at bedste fald kan give et andet udfald. Fyldningsbaren kan ikke
være tvetydig: motorrettelse 1 tjekker kun stoppet der, både forsigtigt og i bedste fald.

## Bedste fald, §8

I bedste fald afgøres den samme bar den anden vej: målet før stoppet, og BE-triggeren før
stoppet, så en fuld stop-tabende handel i stedet lukker på BE. Motorrettelse 1 står ved
magt — fyldningsbaren tjekkes stadig kun for stoppet, for ordren blev fyldt et sted inde i
den bar, og §8 handler alene om regel 4. Bedste fald kan derfor aldrig give et dårligere
udfald end det forsigtige.

## De to faste opslagstabeller

``b4_k1_filtre.beregn_filtre`` bygger selv modzonelisten (kriterium 2) og HTF-zonelisten
(kriterium 5) ud af de serier den får. Begge afhænger kun af ``bars``/``htf`` og bufferen,
som er de samme i alle 500 N1-gentagelser, og de koster tilsammen ~16 s pr. kald på spor
B. ``faste_opslag`` lægger dem i en kontekst hvor ``beregn_filtre`` finder dem færdige.
Vagten i ``_fast`` rejser en fejl hvis den kaldes med andre serier end dem tabellen er
bygget af, så en cache aldrig kan levere et forkert svar. At tabellen er den samme, er
testet: samme ``beregn_filtre``-resultat med og uden konteksten.
"""
from __future__ import annotations

import argparse
import math
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data import holdout  # noqa: E402
from research import b4_k1_filtre as fl  # noqa: E402
from research import b4_k1_optaelling as k1  # noqa: E402
from research import b4_k1_trinA as trinA  # noqa: E402
from research.stats import mean_ci_t, t_critical, t_test_p_value, wilson_interval  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "output"
PREREG = ROOT / "research" / "prereg" / "b4_k1_trin2.md"
PREREG_OPT = ROOT / "research" / "prereg" / "b4_k1_trin2_optaelling.md"
PREREG_TIL = ROOT / "research" / "prereg" / "b4_k1_trin2_optaelling_tillaeg.md"
OPTAELLING_CSV = OUT / "b4_k1_trin2_optaelling.csv"
# Kørslen sker kun når disse er committet og uændrede.
COMMITTEDE = (
    Path(__file__).resolve(), ROOT / "tests" / "test_b4_k1_trin2.py",
    PREREG, PREREG_OPT, PREREG_TIL,
    ROOT / "research" / "b4_k1_filtre.py", ROOT / "research" / "b4_k1_optaelling.py",
    ROOT / "research" / "b4_k1_trinA.py", ROOT / "research" / "stats.py",
    ROOT / "data" / "holdout.py", ROOT / "data" / "resample.py",
    ROOT / "data" / "sessions.py",
)

SPOR = fl.SPOR                      # {"A": (15, 60), "B": (5, 15)}, §2
BUFFER = k1.BUFFER_V2               # 10%, fast, §2
BE_R = 1.2                          # BE +1,2R, fast, §2
SCORE_LOFT = 5                      # score 5, 6 og 7 slås sammen til "5+", §2
SCORE_NAVNE = ("0", "1", "2", "3", "4", "5+")
ALFA_SPOR = 0.025                   # §4: Bonferroni over 2 spor
N1_REPS = 500                       # §5, sænkes ikke
N1_SEED = 7000                      # fast udgangspunkt, så kørslen kan gentages
AAR_LISTE = list(range(2019, 2024))

RR = trinA.RR
TICK = trinA.TICK
SLIP_PT = trinA.SLIP_PT
DEMAND, SUPPLY = k1.DEMAND, k1.SUPPLY
MAAL, STOP, BE_UDFALD = trinA.MAAL, trinA.STOP, trinA.BE_UDFALD
TIDSEXIT, CENSURERET = trinA.TIDSEXIT, trinA.CENSURERET
UDFALD = trinA.UDFALD
KOL = fl.KOL                        # f1_brud … f7_discount
EKSTRA_KOL = ("score",) + KOL       # bæres med fra zonen ud på handelsrækken

# §5's fire varianter pr. spor. Navnet er nøglen i rapporten; funktionen er reglen.
VARIANTER = ("brud_alene", "score_ge_2", "score_ge_3", "score_ge_4")
VARIANT_TEKST = {"brud_alene": "kriterium 1 sandt", "score_ge_2": "score ≥ 2",
                 "score_ge_3": "score ≥ 3", "score_ge_4": "score ≥ 4"}

# §10's regressionstjek 2: motorrettelsens tal for buffer 10% / BE +1,2R på spor A.
REGRESSION_HANDLER_N = 1226
REGRESSION_MIDDEL_R_NETTO = -0.0115

# §4 og §5's præregistrerede MDE-tal, skrevet før kørslen. Rapporteres, regnes ikke om.
MDE_BETA = {"A": 0.055, "B": 0.040}
MDE_VARIANT = {"A": {"brud_alene": 0.13, "score_ge_2": 0.13, "score_ge_3": 0.14,
                     "score_ge_4": 0.17},
               "B": {"brud_alene": 0.12, "score_ge_2": 0.12, "score_ge_3": 0.12,
                     "score_ge_4": 0.13}}


# ---------------------------------------------------------------------------
# Motoren — trin A's, med flaget og bedste-fald-grenen
# ---------------------------------------------------------------------------

def motor(h: np.ndarray, l: np.ndarray, c: np.ndarray, entry_i: int, entry_pris: float,
          demand: bool, risiko_pt: float, be_r: float | None, cutoff_i: int, n: int,
          bedste_fald: bool = False) -> tuple[str, float, int, bool, bool]:
    """(udfald, R_brutto, exit_i, holder, tvetydig) for én handel, 1m-bar for 1m-bar.

    ``bedste_fald=False`` er ``b4_k1_trinA.simuler_handel`` med ``ret_fyldningsbar=True``,
    handel for handel — låst af ``tests/test_b4_k1_trin2.py``. ``tvetydig`` er det eneste
    nye: den bar hvor stoppet blev ramt, kunne også nå målet eller BE-triggeren, §8.

    ``bedste_fald=True`` afgør netop de bar den anden vej: målet før stoppet, og
    BE-triggeren før stoppet, så handlen lukker på BE i stedet for på fuldt stop.
    Motorrettelse 1 gælder begge veje: i fyldningsbaren kan kun stoppet rammes.
    """
    maal = entry_pris + RR * risiko_pt if demand else entry_pris - RR * risiko_pt
    stop_niveau = entry_pris - risiko_pt if demand else entry_pris + risiko_pt
    en_r_niveau = entry_pris + risiko_pt if demand else entry_pris - risiko_pt
    be_trigger = None
    if be_r is not None:
        be_trigger = entry_pris + be_r * risiko_pt if demand else entry_pris - be_r * risiko_pt
    be_armet = False
    holder = False
    tvetydig = False
    graense = min(cutoff_i, n)
    i = entry_i

    def _stop_r(niveau: float) -> float:
        eksekvering = niveau - SLIP_PT if demand else niveau + SLIP_PT
        return ((eksekvering - entry_pris) if demand
                else (entry_pris - eksekvering)) / risiko_pt

    while i < graense:
        hi, lo = h[i], l[i]
        stop_ramt = (lo <= stop_niveau) if demand else (hi >= stop_niveau)
        if i == entry_i:
            # Motorrettelse 1: kun stoppet kan rammes i fyldningsbaren.
            if stop_ramt:
                return (BE_UDFALD if be_armet else STOP), _stop_r(stop_niveau), i, holder, False
            i += 1
            continue
        maal_ramt = (hi >= maal) if demand else (lo <= maal)
        en_r_ramt = (hi >= en_r_niveau) if demand else (lo <= en_r_niveau)
        be_trig = (be_trigger is not None and not be_armet
                   and ((hi >= be_trigger) if demand else (lo <= be_trigger)))
        if stop_ramt and (maal_ramt or be_trig):
            tvetydig = True
        if bedste_fald:
            if maal_ramt:
                return MAAL, RR, i, True, tvetydig
            if en_r_ramt:
                holder = True
            if stop_ramt:
                # BE-triggeren nås før stoppet: stoppet står da på E, og udfaldet er BE.
                if be_trig or be_armet:
                    return BE_UDFALD, _stop_r(entry_pris), i, holder, tvetydig
                return STOP, _stop_r(stop_niveau), i, holder, tvetydig
            if be_trig:
                be_armet = True
                stop_niveau = entry_pris
        else:
            # Regel 4, forsigtigt: rammes stop og mål i samme 1m-bar, antages stoppet først.
            if stop_ramt:
                return ((BE_UDFALD if be_armet else STOP), _stop_r(stop_niveau), i,
                        holder, tvetydig)
            if maal_ramt:
                return MAAL, RR, i, True, tvetydig
            if en_r_ramt:
                holder = True
            if be_trig:
                be_armet = True
                stop_niveau = entry_pris
        i += 1

    sidste_i = i - 1 if i > entry_i else entry_i
    r = ((c[sidste_i] - entry_pris) if demand else (entry_pris - c[sidste_i])) / risiko_pt
    return (CENSURERET if graense == n else TIDSEXIT), r, sidste_i, holder, tvetydig


HANDELSKOL = ["dag", "side", "basis_i", "fyld_tid", "exit_tid", "udfald", "R_brutto",
              "R_netto", "risiko_pt", "kontrakter", "omk_R_netto", "holder", "tvetydig"]
STREJFKOL = ["dag", "side", "basis_i", "udfald", "R_brutto", "R_netto", "holder",
             "tvetydig"]


def gennemloeb(df_1m: pd.DataFrame, zoner: pd.DataFrame, bar_min: int,
               be_r: float | None = BE_R, disciplin: bool = True,
               bedste_fald: bool = False) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    """(handler, tæller, strejf) for én zoneliste. Kandidaterne er ``i_vindue`` og
    ``kontrakter_ekte ≥ 1`` — trin A-motorens egen regel, §4d.

    ``bar_min`` er handelstimeframen i minutter: 15 på spor A, 5 på spor B. Fyldningen
    søges inden for netop berøringsbaren, §4a regel 1, så den længde skal følge sporet —
    trin A kendte kun 15m og skrev ``k1.BAR`` direkte.

    ``disciplin=True`` er trin A §4b's dagsgennemløb, uændret: kandidaterne behandles
    kronologisk pr. dag, en berøring mens en position er åben eller efter dagen er lukket
    springes over og tælles, to BE-udgange lukker dagen, ethvert andet afgjort udfald
    lukker dagen. ``disciplin=False`` er §4's skyggehandler: hvert signal simuleres for
    sig, uafhængigt af de andre, fordi spørgsmålet er om scoren forudsiger udfaldet.

    Fyldningen er §4a's otte regler, uændret: prisen skal handle mindst ét tick gennem E
    inden for berøringsbaren, og fyldes til E. Rammes E kun, er det et strejf — zonen er
    stadig død, ingen handel åbnes, og §4c's kontrafaktiske gennemkøring regnes til
    diagnose. Kolonner i ``EKSTRA_KOL`` (scoren og de syv kriterier) bæres med fra zonen
    ud på handelsrækken, så handlen kan grupperes på scoren uden et opslag bagefter —
    N1's zoner kan dele ``basis_i``, så et opslag ville være tvetydigt.
    """
    times = df_1m.index
    h = df_1m["high"].to_numpy(dtype=float)
    l = df_1m["low"].to_numpy(dtype=float)
    c = df_1m["close"].to_numpy(dtype=float)
    n = len(df_1m)
    bar = pd.Timedelta(minutes=int(bar_min))

    kand = zoner[zoner["i_vindue"].to_numpy(dtype=bool) & (zoner["kontrakter_ekte"] >= 1)]
    kand = kand.sort_values(["dag", "slut_tid", "basis_i"])
    dag_arr = kand["dag"].to_numpy()
    slut_tid_arr = kand["slut_tid"].to_numpy()
    side_arr = kand["side"].to_numpy()
    E_arr = kand["E"].to_numpy(dtype=float)
    risiko_arr = kand["risiko_pt_ekte"].to_numpy(dtype=float)
    kontrakter_arr = kand["kontrakter_ekte"].to_numpy(dtype=float)
    omk_arr = kand["omk_R_netto_ekte"].to_numpy(dtype=float)
    basis_i_arr = kand["basis_i"].to_numpy()
    ekstra = {navn: kand[navn].to_numpy() for navn in EKSTRA_KOL if navn in kand.columns}
    m = len(kand)

    rows: list[dict] = []
    strejf_rows: list[dict] = []
    tael = {"signaler_sprunget_over_position_n": 0, "signaler_sprunget_over_dagslukket_n": 0}

    if m == 0:
        graenser = np.zeros(1, dtype=np.int64)
    else:
        graenser = np.r_[np.flatnonzero(np.r_[True, dag_arr[1:] != dag_arr[:-1]]), m]
    for gi in range(len(graenser) - 1):
        dagslukket = False
        be_count = 0
        fri_fra = None
        for k in range(graenser[gi], graenser[gi + 1]):
            t = slut_tid_arr[k]
            if disciplin:
                if dagslukket:
                    tael["signaler_sprunget_over_dagslukket_n"] += 1
                    continue
                if fri_fra is not None and t < fri_fra:
                    tael["signaler_sprunget_over_position_n"] += 1
                    continue
            demand = side_arr[k] == DEMAND
            E = E_arr[k]
            risiko_pt = risiko_arr[k]
            omk_R_netto = omk_arr[k]
            ekstra_k = {navn: v[k] for navn, v in ekstra.items()}
            i0 = int(times.searchsorted(t))
            i1 = int(times.searchsorted(t + bar))
            sub_l, sub_h = l[i0:i1], h[i0:i1]
            graense = (E - TICK) if demand else (E + TICK)
            gennem = (sub_l <= graense) if demand else (sub_h >= graense)
            if not gennem.any():
                strejf_maske = (sub_l <= E) if demand else (sub_h >= E)
                if strejf_maske.any():
                    j = i0 + int(np.argmax(strejf_maske))
                    cutoff_i = int(times.searchsorted(trinA.flad_tid_utc(times[j])))
                    udfald, r_brutto, _, holder, tvetydig = motor(
                        h, l, c, j, E, demand, risiko_pt, be_r, cutoff_i, n, bedste_fald)
                    strejf_rows.append({
                        "dag": dag_arr[k], "side": side_arr[k], "basis_i": basis_i_arr[k],
                        "udfald": udfald, "R_brutto": r_brutto,
                        "R_netto": r_brutto - omk_R_netto, "holder": holder,
                        "tvetydig": tvetydig, **ekstra_k,
                    })
                continue
            fyld_i = i0 + int(np.argmax(gennem))
            fyld_tid = times[fyld_i]
            cutoff_i = int(times.searchsorted(trinA.flad_tid_utc(fyld_tid)))
            udfald, r_brutto, exit_i, holder, tvetydig = motor(
                h, l, c, fyld_i, E, demand, risiko_pt, be_r, cutoff_i, n, bedste_fald)
            rows.append({
                "dag": dag_arr[k], "side": side_arr[k], "basis_i": basis_i_arr[k],
                "fyld_tid": fyld_tid, "exit_tid": times[exit_i], "udfald": udfald,
                "R_brutto": r_brutto, "R_netto": r_brutto - omk_R_netto,
                "risiko_pt": risiko_pt, "kontrakter": kontrakter_arr[k],
                "omk_R_netto": omk_R_netto, "holder": holder, "tvetydig": tvetydig,
                **ekstra_k,
            })
            if disciplin:
                if udfald == BE_UDFALD:
                    be_count += 1
                    if be_count >= 2:
                        dagslukket = True
                else:
                    dagslukket = True
                fri_fra = times[exit_i]

    kolonner = HANDELSKOL + [navn for navn in EKSTRA_KOL if navn in ekstra]
    strejfkol = STREJFKOL + [navn for navn in EKSTRA_KOL if navn in ekstra]
    return (pd.DataFrame(rows, columns=kolonner), tael,
            pd.DataFrame(strejf_rows, columns=strejfkol))



# ---------------------------------------------------------------------------
# Statistikken, §4 — OLS med klyngerobust standardfejl pr. handelsdag
# ---------------------------------------------------------------------------

def klyngerobust_ols(y, x, klynge, alfa: float = ALFA_SPOR) -> dict:
    """Hældningen β i ``y = a + b·x`` med klyngerobust standardfejl, §4.

    Klyngen er handelsdagen: handler samme dag deler marked og kan overlappe, så
    residualerne er korrelerede inden for dagen og uafhængige på tværs. Sandwichen er
    Liang-Zeger's, ``(X'X)⁻¹ (Σ_g X_g'u_g u_g'X_g) (X'X)⁻¹``, med den sædvanlige
    endelig-stikprøve-korrektion ``G/(G−1) · (n−1)/(n−k)`` (CR1, Statas standard).
    Frihedsgrader er ``G − 1``, antallet af klynger minus én — den gængse konvention,
    og den konservative: den er meget mindre end ``n − 2``.

    Testen er én-sidet, H1: β > 0. ``p_ensidet`` er derfor ``P(T > t)``, og ``signifikant``
    er ``p_ensidet ≤ alfa``. CI95 er tosidet, som §9 beder om.
    """
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    klynge = np.asarray(klynge)
    tom = {"n": int(len(y)), "klynger_n": 0, "beta": float("nan"), "se": float("nan"),
           "t": float("nan"), "df": float("nan"), "ci95_lo": float("nan"),
           "ci95_hi": float("nan"), "p_ensidet": float("nan"), "alfa": alfa,
           "signifikant": False, "skaering": float("nan")}
    n = len(y)
    if n < 3 or np.ptp(x) == 0:
        return tom
    _, idx = np.unique(klynge, return_inverse=True)
    g = int(idx.max()) + 1
    if g < 2:
        return tom

    X = np.column_stack([np.ones(n), x])
    XtX = X.T @ X
    if not np.isfinite(np.linalg.cond(XtX)) or np.linalg.cond(XtX) > 1e12:
        return tom
    XtX_inv = np.linalg.inv(XtX)
    beta = XtX_inv @ (X.T @ y)
    u = y - X @ beta
    Xu = X * u[:, None]
    sums = np.column_stack([np.bincount(idx, weights=Xu[:, j], minlength=g)
                            for j in range(X.shape[1])])
    meat = sums.T @ sums
    korrektion = (g / (g - 1)) * ((n - 1) / (n - X.shape[1]))
    V = XtX_inv @ meat @ XtX_inv * korrektion
    se = float(np.sqrt(V[1, 1])) if V[1, 1] > 0 else float("nan")
    ud = dict(tom, n=n, klynger_n=g, beta=float(beta[1]), skaering=float(beta[0]), se=se)
    if not np.isfinite(se) or se == 0:
        return ud
    t = float(beta[1]) / se
    df = float(g - 1)
    p2 = t_test_p_value(t, df)
    p_ensidet = p2 / 2 if t >= 0 else 1.0 - p2 / 2
    tcrit = t_critical(df, 0.05)
    ud.update(t=t, df=df, p_ensidet=float(p_ensidet),
              ci95_lo=float(beta[1] - tcrit * se), ci95_hi=float(beta[1] + tcrit * se),
              signifikant=bool(p_ensidet <= alfa))
    return ud


def score_loft(score) -> np.ndarray:
    """Scoren som regressoren bruger den: 5, 6 og 7 slås sammen til "5+", §2."""
    return np.minimum(np.asarray(score, dtype=float), SCORE_LOFT)


def hovedtest(handler: pd.DataFrame) -> dict:
    """§4's hovedtest på skyggehandlerne: β for ``R_netto`` på scoren, klynge = dag."""
    if len(handler) == 0:
        return klyngerobust_ols(np.zeros(0), np.zeros(0), np.zeros(0))
    return klyngerobust_ols(handler["R_netto"].to_numpy(dtype=float),
                            score_loft(handler["score"]),
                            pd.DatetimeIndex(handler["dag"]).asi8)


def middel_ci(vaerdier) -> tuple[float, float, float]:
    """(middel, CI95 nedre, CI95 øvre) med Students t — trin A §8's interval."""
    arr = np.asarray(vaerdier, dtype=float)
    if len(arr) == 0:
        return float("nan"), float("nan"), float("nan")
    lo, hi = mean_ci_t(arr)
    return float(arr.mean()), lo, hi


def forskel_ci(a, b) -> tuple[float, float, float]:
    """(forskel i middelværdi, CI95 nedre, CI95 øvre) for to uafhængige grupper, Welch.

    Bruges til §8's "demand og supply hver for sig, med CI på forskellen".
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if len(a) < 2 or len(b) < 2:
        return float("nan"), float("nan"), float("nan")
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    se = math.sqrt(va + vb)
    if se == 0:
        return float(a.mean() - b.mean()), float("nan"), float("nan")
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    tcrit = t_critical(df, 0.05)
    d = float(a.mean() - b.mean())
    return d, d - tcrit * se, d + tcrit * se


# ---------------------------------------------------------------------------
# De to faste opslagstabeller — samme svar, regnet én gang
# ---------------------------------------------------------------------------

def _samme(a, forventet) -> bool:
    """Om et argument er det samme som det opslagstabellen blev bygget af.

    Serier og zonetabeller er de samme objekter gennem hele kørslen, så identitet er
    svaret for dem — elementvis lighed på en DataFrame er hverken entydig eller billig.
    Lukketidspunkterne regner ``beregn_filtre`` selv hver gang, så dér er der et nyt
    array med samme indhold, og det er indholdet der afgør svaret.
    """
    if a is forventet:
        return True
    if isinstance(a, np.ndarray) and isinstance(forventet, np.ndarray):
        return bool(a.shape == forventet.shape and np.array_equal(a, forventet))
    if isinstance(a, (pd.DataFrame, pd.Series, pd.Index)):
        return False
    try:
        return bool(a == forventet)
    except Exception:
        return False


def _fast(vaerdi, *forventet):
    """Et opslag der returnerer ``vaerdi``, men kun for de argumenter det blev bygget af.

    Vagten er hele pointen: en cache der tier ved forkerte argumenter kan levere et
    forkert filter uden at nogen opdager det. Denne rejser i stedet.
    """
    def _kald(*args):
        if len(args) != len(forventet) or not all(
                _samme(a, f) for a, f in zip(args, forventet)):
            raise RuntimeError("fast opslagstabel kaldt med andre serier end den blev "
                               "bygget af")
        return vaerdi
    return _kald


@contextmanager
def faste_opslag(bars: pd.DataFrame, htf: pd.DataFrame, htf_luk: np.ndarray,
                 mod: dict, stak: dict, buffer: Fraction = BUFFER):
    """``b4_k1_filtre.beregn_filtre`` finder modzonelisten og HTF-zonelisten færdige.

    Begge er rene funktioner af ``bars``/``htf`` og bufferen, som ikke ændrer sig mellem
    N1's gentagelser, og de koster ~16 s pr. kald på spor B. Konteksten sætter dem
    tilbage igen, også hvis kroppen fejler.
    """
    oprindelige = (fl._modzoner, fl._htf_zoner)
    fl._modzoner = _fast(mod, bars, buffer)
    fl._htf_zoner = _fast(stak, htf, htf_luk)
    try:
        yield
    finally:
        fl._modzoner, fl._htf_zoner = oprindelige


# ---------------------------------------------------------------------------
# Sporet — alt der er fast gennem hele kørslen
# ---------------------------------------------------------------------------

@dataclass
class Spor:
    """Ét spor: serierne, den rigtige zoneliste, signalerne med filtre, og N1's råstof."""
    navn: str
    tf_min: int
    htf_min: int
    bars: pd.DataFrame
    htf: pd.DataFrame
    htf_luk: np.ndarray
    mod: dict
    stak: dict
    zoner: pd.DataFrame
    sig: pd.DataFrame
    ekte_side: np.ndarray
    ekte_basis_i: np.ndarray
    ekte_H: np.ndarray

    def filtre(self, zoner: pd.DataFrame) -> pd.DataFrame:
        """De syv kriterier og scoren for ``zoner``, med de faste opslag på plads."""
        with faste_opslag(self.bars, self.htf, self.htf_luk, self.mod, self.stak):
            return fl.beregn_filtre(zoner, self.bars, self.htf, self.tf_min,
                                    self.htf_min, BUFFER)


def byg_spor(df_1m: pd.DataFrame, navn: str) -> Spor:
    """Sporet bygget af 1m-serien: begge timeframes, kerne v2-zonerne, signalerne med
    filtre og score. Præcis ``b4_k1_filtre.signaler_med_filtre``'s vej, uændret."""
    tf_min, htf_min = SPOR[navn]
    bars, htf, z = fl.spor_data(df_1m, tf_min, htf_min, BUFFER)
    htf_luk = fl._luk(htf.index, htf_min)
    mod = fl._modzoner(bars, BUFFER)
    stak = fl._htf_zoner(htf, htf_luk)
    spor = Spor(navn=navn, tf_min=tf_min, htf_min=htf_min, bars=bars, htf=htf,
                htf_luk=htf_luk, mod=mod, stak=stak, zoner=z, sig=z.iloc[:0].copy(),
                ekte_side=z["side"].to_numpy(),
                ekte_basis_i=z["basis_i"].to_numpy(dtype=np.int64),
                ekte_H=(z["zone_high"] - z["zone_low"]).to_numpy(dtype=float))
    sig = z[z["signal"].to_numpy(dtype=bool)].copy()
    spor.sig = pd.concat([sig, spor.filtre(sig)], axis=1)
    return spor


def n1_signaler(spor: Spor, seed: int) -> pd.DataFrame:
    """§5's nulmodel for ét spor: hver zones dannelseslys flyttes til et tilfældigt lys i
    samme ISO-uge, side og H bevares, og den flyttede zone får **sine egne filterværdier
    og sin egen score**, regnet med samme kode på samme serie.

    Zonens øvrige mekanik — aktivering, ugyldig, berøring, kontraktskift — er kerne v2's
    egne regler gennem ``b4_k1_trinA.find_zoner_n1``, uændret. Signalbegrebet er det
    samme som den rigtige kørsels: berøring i indgangsvinduet og ``kontrakter_ekte ≥ 1``.
    """
    rng = np.random.default_rng([N1_SEED, sorted(SPOR).index(spor.navn), seed])
    b_n1 = trinA.n1_dannelseslys(spor.bars, spor.ekte_basis_i, rng)
    z_n1 = trinA.find_zoner_n1(spor.bars, spor.ekte_side, spor.ekte_H, b_n1, BUFFER)
    klass = trinA.sizing_ekte(fl.klassificer(spor.bars, z_n1, spor.tf_min))
    signal = (klass["i_vindue"].to_numpy(dtype=bool)
              & (klass["kontrakter_ekte"].to_numpy(dtype=float) >= 1))
    sig = klass[signal].copy().reset_index(drop=True)
    return pd.concat([sig, spor.filtre(sig)], axis=1)


# ---------------------------------------------------------------------------
# Varianterne, §5
# ---------------------------------------------------------------------------

def variant_maske(sig: pd.DataFrame, variant: str) -> np.ndarray:
    """§5's regel for én variant, vurderet ved lukningen af lyset før berøringen (§3)."""
    if variant == "brud_alene":
        return sig[KOL[0]].to_numpy(dtype=bool)
    if variant.startswith("score_ge_"):
        return sig["score"].to_numpy(dtype=np.int64) >= int(variant.rsplit("_", 1)[1])
    raise ValueError(f"ukendt variant: {variant}")


def noegletal(handler: pd.DataFrame) -> dict:
    """§9's tal for én samling handler: antal, brutto og netto med CI, win rate,
    udfaldsandele, `holder_pct` og de tvetydige."""
    n = len(handler)
    ud = {"handler_n": n, "dage_med_handel_n": 0}
    if n == 0:
        for navn in ("middel_R_brutto", "middel_R_netto", "middel_R_netto_ci95_lo",
                     "middel_R_netto_ci95_hi", "win_rate_pct_netto", "holder_pct",
                     "tvetydige_pct"):
            ud[navn] = float("nan")
        for u in UDFALD:
            ud[f"udfald_{u}_pct"] = float("nan")
        ud["tvetydige_n"] = 0
        return ud
    middel, lo, hi = middel_ci(handler["R_netto"])
    vundet = int((handler["udfald"] == MAAL).sum())
    holder_n = int(handler["holder"].sum())
    tvetydige_n = int(handler["tvetydig"].sum())
    w_lo, w_hi = wilson_interval(vundet, n)
    h_lo, h_hi = wilson_interval(holder_n, n)
    ud.update({
        "middel_R_brutto": float(handler["R_brutto"].mean()),
        "middel_R_netto": middel, "middel_R_netto_ci95_lo": lo,
        "middel_R_netto_ci95_hi": hi,
        "win_rate_pct_netto": 100 * vundet / n,
        "win_rate_ci95_lo_pct": 100 * w_lo, "win_rate_ci95_hi_pct": 100 * w_hi,
        "holder_pct": 100 * holder_n / n, "holder_ci95_lo_pct": 100 * h_lo,
        "holder_ci95_hi_pct": 100 * h_hi,
        "tvetydige_n": tvetydige_n, "tvetydige_pct": 100 * tvetydige_n / n,
        "dage_med_handel_n": int(pd.DatetimeIndex(handler["dag"]).normalize().nunique()),
    })
    for u in UDFALD:
        ud[f"udfald_{u}_pct"] = 100 * int((handler["udfald"] == u).sum()) / n
    return ud


def koer_varianter(df_1m: pd.DataFrame, spor: Spor, sig: pd.DataFrame,
                   bedste_fald: bool = False, kun: tuple[str, ...] = VARIANTER) -> dict:
    """§5's varianter for ét spor. Hver handles med disciplinreglerne som i trin A.

    Gennemløbet er ``gennemloeb``, ikke ``b4_k1_trinA.handler_for_variant`` selv, af én
    grund: trin A kendte kun 15m og søger fyldningen i ``t … t + k1.BAR`` med ``k1.BAR``
    hårdkodet til 15 minutter. På spor B er berøringsbaren 5 minutter, og trin A's
    funktion ville dér lede efter fyldningen tre barer frem — et kig frem der ikke står
    nogen steder. ``gennemloeb`` tager berøringsbarens længde som argument og er ellers
    trin A's kode, handel for handel; på spor A's 15m gengiver den den præcist, hvilket
    er både en test og §10's regressionstjek 2.
    """
    ud = {}
    for navn in kun:
        del_sig = sig[variant_maske(sig, navn)]
        handler, tael, strejf = gennemloeb(df_1m, del_sig, spor.tf_min, BE_R,
                                           disciplin=True, bedste_fald=bedste_fald)
        row = noegletal(handler)
        row.update(tael)
        row["signaler_n"] = len(del_sig)
        row["omk_R_netto_p50"] = k1._p(del_sig["omk_R_netto_ekte"], 50)
        row["omk_R_netto_p90"] = k1._p(del_sig["omk_R_netto_ekte"], 90)
        row["strejf_uden_gennemhandling_n"] = len(strejf)
        ud[navn] = {"noegletal": row, "handler": handler, "strejf": strejf}
    return ud


def koer_skygge(df_1m: pd.DataFrame, spor: Spor, sig: pd.DataFrame,
                bedste_fald: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """§4's skyggehandler for ét spor: hvert signal for sig, ingen disciplinregler."""
    handler, _, strejf = gennemloeb(df_1m, sig, spor.tf_min, BE_R, disciplin=False,
                                    bedste_fald=bedste_fald)
    return handler, strejf


# ---------------------------------------------------------------------------
# N1 — én gentagelse for begge spor
# ---------------------------------------------------------------------------

_KONTEKST: dict[str, object] = {}


def _init_arbejder(spor_navne: tuple[str, ...]) -> None:
    """Hver arbejder bygger sporene én gang og genbruger dem på tværs af gentagelserne.

    Serierne hentes i arbejderen selv i stedet for at blive sendt med hver opgave: 1,6
    mio. 1m-barer koster mere at pakke ned og sende 500 gange end at læse én gang pr.
    proces.
    """
    df = mnq()
    _KONTEKST["df"] = df
    for navn in spor_navne:
        _KONTEKST[navn] = byg_spor(df, navn)


def n1_gentagelse(seed: int, spor_navne: tuple[str, ...] = ("A", "B"),
                  kontekst: dict | None = None) -> dict:
    """Én N1-gentagelse for begge spor: hovedtestens β og de fire varianters middel-R.

    Gentagelserne er uafhængige, og sporenes trækninger inden for samme gentagelse er
    det også — de to spor har hver sit lysgitter (15m og 5m), så der findes ingen fælles
    trækning at dele. Gentagelse *r* på spor A parres med gentagelse *r* på spor B, og
    maks-statistikken tages over alle otte, §5.
    """
    kontekst = _KONTEKST if kontekst is None else kontekst
    df = kontekst["df"]
    ud = {"seed": seed}
    for navn in spor_navne:
        spor = kontekst[navn]
        sig = n1_signaler(spor, seed)
        skygge, _ = koer_skygge(df, spor, sig)
        varianter = koer_varianter(df, spor, sig)
        ud[navn] = {
            "beta": hovedtest(skygge)["beta"],
            "skygge_n": len(skygge),
            "signaler_n": len(sig),
            "varianter": {v: varianter[v]["noegletal"]["middel_R_netto"] for v in VARIANTER},
            "handler_n": {v: varianter[v]["noegletal"]["handler_n"] for v in VARIANTER},
        }
    return ud


def _n1_med_tid(seed: int, spor_navne: tuple[str, ...]) -> tuple[float, dict]:
    start = time.perf_counter()
    res = n1_gentagelse(seed, spor_navne)
    return time.perf_counter() - start, res


def koer_n1(n_reps: int, spor_navne: tuple[str, ...] = ("A", "B"),
            max_workers: int | None = None) -> tuple[list[dict], dict]:
    """``n_reps`` N1-gentagelser, parallelliseret over kernerne. Gentagelserne er
    uafhængige, så de kan deles frit; hver arbejder bygger sporene én gang."""
    n_workere = max_workers or (os.cpu_count() or 1)
    start = time.perf_counter()
    resultater: list[tuple[float, dict]] = []
    with ProcessPoolExecutor(max_workers=n_workere, initializer=_init_arbejder,
                             initargs=(spor_navne,)) as pool:
        futures = [pool.submit(_n1_med_tid, i, spor_navne) for i in range(n_reps)]
        for f in as_completed(futures):
            resultater.append(f.result())
    vaeg_s = time.perf_counter() - start
    tider = [t for t, _ in resultater]
    liste = sorted((r for _, r in resultater), key=lambda r: r["seed"])
    tid = {"n_reps": n_reps, "n_workere": n_workere, "cpu_count": os.cpu_count(),
           "vaeg_s": vaeg_s, "middel_s_pr_gentagelse": float(np.mean(tider)),
           "effektiv_s_pr_gentagelse": vaeg_s / n_reps if n_reps else float("nan")}
    return liste, tid


# ---------------------------------------------------------------------------
# Westfall-Young over de otte varianter, §5
# ---------------------------------------------------------------------------

def _p(vaerdier, q: float) -> float:
    arr = np.asarray(vaerdier, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.percentile(arr, q)) if len(arr) else float("nan")


def westfall_young(virkelig: dict, n1_liste: list[dict]) -> dict:
    """§5: maks-statistikken over alle otte varianter på tværs af begge spor.

    For hver N1-gentagelse gemmes den største middel netto-R blandt de otte, og den
    observerede bedste variant holdes op mod den fordeling. ``p_FWE`` er kun defineret
    for den observerede bedste — Westfall-Young beskytter netop **valget** af den bedste.
    En variant uden handler i en gentagelse er ikke et resultat på nul, men et manglende
    tal, og udelades af den gentagelses maksimum (``nanmax``, som i trin A).
    """
    par = [(spor, v) for spor in sorted(virkelig) for v in VARIANTER]
    obs = {p: virkelig[p[0]][p[1]]["noegletal"]["middel_R_netto"] for p in par}
    bedste = max(par, key=lambda p: (obs[p] if np.isfinite(obs[p]) else -np.inf))
    observeret = obs[bedste]

    maks = []
    for rep in n1_liste:
        vaerdier = [rep[spor]["varianter"][v] for spor, v in par]
        vaerdier = [v for v in vaerdier if np.isfinite(v)]
        maks.append(max(vaerdier) if vaerdier else float("nan"))
    maks = np.asarray(maks, dtype=float)
    gyldige = maks[np.isfinite(maks)]
    R = len(n1_liste)
    p_fwe = (1 + int((gyldige >= observeret).sum())) / (1 + R)

    pr_variant = {p: np.array([rep[p[0]]["varianter"][p[1]] for rep in n1_liste],
                              dtype=float) for p in par}
    return {"par": par, "bedste": bedste, "observeret_middel_R_netto": observeret,
            "p_fwe": p_fwe, "R": R, "maks_fordeling": maks, "n1_pr_variant": pr_variant,
            "n1_handler_pr_variant": {
                p: np.array([rep[p[0]]["handler_n"][p[1]] for rep in n1_liste], dtype=float)
                for p in par}}


def n1_beta(n1_liste: list[dict], spor_navn: str, observeret: float) -> dict:
    """§4's sekundære tal: hovedtestens β i N1, p5/p50/p95 og andelen ≥ den observerede."""
    arr = np.array([rep[spor_navn]["beta"] for rep in n1_liste], dtype=float)
    gyldige = arr[np.isfinite(arr)]
    andel = (float((gyldige >= observeret).mean()) if len(gyldige) and np.isfinite(observeret)
             else float("nan"))
    return {"p5": _p(arr, 5), "p50": _p(arr, 50), "p95": _p(arr, 95),
            "andel_ge_observeret": andel, "R": len(n1_liste), "gyldige_n": int(len(gyldige))}


# ---------------------------------------------------------------------------
# Beslutningsreglen, §7
# ---------------------------------------------------------------------------

def beslutning(hovedtests: dict, wy: dict, virkelig: dict) -> dict:
    """§7's tre rækker, anvendt mekanisk. Tabellen er udtømmende — tredje række er
    "alt andet" — så der er ingen kategori tilbage at falde ned i; sætningen om at den
    laveste kategori gælder når et konfidensinterval krydser en grænse, rapporteres som
    en aflæsning ved siden af, ikke som en fjerde regel."""
    holder = {s: bool(h["signifikant"]) for s, h in hovedtests.items()}
    spor_navn, variant = wy["bedste"]
    bedste = virkelig[spor_navn][variant]["noegletal"]
    R = bedste["middel_R_netto"]
    lo, hi = bedste["middel_R_netto_ci95_lo"], bedste["middel_R_netto_ci95_hi"]
    p_fwe = wy["p_fwe"]
    variant_ok = bool(p_fwe <= 0.05 and np.isfinite(R) and R >= 0.20
                      and np.isfinite(lo) and lo > 0)
    if not any(holder.values()):
        kategori = "parkeres_stopreglen"
        tekst = ("Hovedtesten er ikke signifikant over 0 på noget spor. Stopreglen: "
                 "kandidat 1 parkeres. Varianterne rapporteres, men afgør intet.")
    elif variant_ok:
        kategori = "varianten_fryses"
        tekst = ("Hovedtesten holder på mindst ét spor, og den bedste variant opfylder "
                 "alle tre krav. Varianten fryses.")
    else:
        kategori = "parkeres_ingen_variant"
        tekst = ("Kandidat 1 parkeres som \"kriterierne hjælper, men ingen variant kan "
                 "handles\". Tallene skrives ned.")
    return {"kategori": kategori, "tekst": tekst, "hovedtest_holder": holder,
            "bedste_spor": spor_navn, "bedste_variant": variant, "p_fwe": p_fwe,
            "middel_R_netto": R, "ci95_lo": lo, "ci95_hi": hi,
            "ci_krydser_020": bool(np.isfinite(lo) and np.isfinite(hi)
                                   and lo < 0.20 < hi),
            "ci_krydser_nul": bool(np.isfinite(lo) and np.isfinite(hi) and lo < 0 < hi)}


# ---------------------------------------------------------------------------
# Diagnoserne, §8 — rapporteres, afgør intet
# ---------------------------------------------------------------------------

def diagnose_score(skygge: pd.DataFrame) -> list[dict]:
    """Middel netto-R pr. score 0-5+, med CI, `holder_pct` og de tvetydige handler."""
    rows = []
    s = score_loft(skygge["score"]) if len(skygge) else np.zeros(0)
    for k, navn in enumerate(SCORE_NAVNE):
        sub = skygge[s == k] if len(skygge) else skygge
        rows.append({"noegle": navn, **noegletal(sub)})
    return rows


def diagnose_kriterier(skygge: pd.DataFrame) -> list[dict]:
    """Middel netto-R når hvert kriterium er sandt mod falsk. **Beskrivende.** Må ikke
    bruges til nye varianter uden ny præregistrering, og en sådan brug koster fuldt N."""
    rows = []
    for kol in KOL:
        sand = skygge[skygge[kol].to_numpy(dtype=bool)]["R_netto"]
        falsk = skygge[~skygge[kol].to_numpy(dtype=bool)]["R_netto"]
        d, lo, hi = forskel_ci(sand, falsk)
        rows.append({"noegle": kol, "sand_n": len(sand), "falsk_n": len(falsk),
                     "sand_middel_R_netto": float(sand.mean()) if len(sand) else float("nan"),
                     "falsk_middel_R_netto": float(falsk.mean()) if len(falsk) else float("nan"),
                     "forskel_R_netto": d, "forskel_ci95_lo": lo, "forskel_ci95_hi": hi})
    return rows


def diagnose_side(skygge: pd.DataFrame) -> list[dict]:
    """Demand og supply hver for sig, med CI på forskellen — §8's drift-diagnose."""
    d = skygge[skygge["side"] == DEMAND]["R_netto"]
    s = skygge[skygge["side"] == SUPPLY]["R_netto"]
    rows = []
    for navn, sub in ((DEMAND, d), (SUPPLY, s)):
        middel, lo, hi = middel_ci(sub)
        rows.append({"noegle": navn, "handler_n": len(sub), "middel_R_netto": middel,
                     "middel_R_netto_ci95_lo": lo, "middel_R_netto_ci95_hi": hi})
    forskel, lo, hi = forskel_ci(d, s)
    rows.append({"noegle": "demand_minus_supply", "handler_n": len(d) + len(s),
                 "middel_R_netto": forskel, "middel_R_netto_ci95_lo": lo,
                 "middel_R_netto_ci95_hi": hi})
    return rows


def diagnose_aar(skygge: pd.DataFrame) -> list[dict]:
    """Pr. år — §8's koncentrationsdiagnose."""
    aar = pd.DatetimeIndex(skygge["dag"]).year if len(skygge) else np.zeros(0, dtype=int)
    rows = []
    for a in AAR_LISTE:
        sub = skygge[aar == a] if len(skygge) else skygge
        middel, lo, hi = middel_ci(sub["R_netto"])
        rows.append({"noegle": str(a), "handler_n": len(sub), "middel_R_netto": middel,
                     "middel_R_netto_ci95_lo": lo, "middel_R_netto_ci95_hi": hi,
                     "tvetydige_n": int(sub["tvetydig"].sum()) if len(sub) else 0})
    return rows


def diagnose_strejf(strejf: pd.DataFrame) -> dict:
    """Strejf pr. spor med kontrafaktisk middel-R, som i trin A — fyldningsreglens pris."""
    n = len(strejf)
    if n == 0:
        return {"strejf_n": 0, "hvis_fyldt_middel_R_netto": float("nan"),
                "hvis_fyldt_win_rate_pct_netto": float("nan")}
    return {"strejf_n": n,
            "hvis_fyldt_middel_R_netto": float(strejf["R_netto"].mean()),
            "hvis_fyldt_win_rate_pct_netto":
                100 * int((strejf["udfald"] == MAAL).sum()) / n}


# ---------------------------------------------------------------------------
# Kørslen, §4-§8
# ---------------------------------------------------------------------------

def mnq() -> pd.DataFrame:
    """MNQ.v.0 1m, 2019-05-06 → 2023-12-31, kun gennem holdout-modulet. Holdout åbnes ikke."""
    df = holdout.load_in_sample(trinA.MNQ)
    return df[(df.index >= trinA.MNQ_START) & (df.index < trinA.TRIN_A_SLUT)]


def koer_virkelig(df_1m: pd.DataFrame, spor_navne: tuple[str, ...] = ("A", "B"),
                  kontekst: dict | None = None) -> dict:
    """Den rigtige kørsel: hovedtesten og de fire varianter pr. spor, plus §8's
    diagnoser og bedste-fald-følsomheden. Ingen N1 her."""
    ud = {}
    for navn in spor_navne:
        spor = (byg_spor(df_1m, navn) if kontekst is None else kontekst[navn])
        sig = spor.sig
        skygge, strejf = koer_skygge(df_1m, spor, sig)
        skygge_bf, _ = koer_skygge(df_1m, spor, sig, bedste_fald=True)
        varianter = koer_varianter(df_1m, spor, sig)
        ud[navn] = {
            "spor": spor, "signaler_n": len(sig), "skygge": skygge, "strejf": strejf,
            "skygge_bedste_fald": skygge_bf,
            "hovedtest": hovedtest(skygge),
            "hovedtest_bedste_fald": hovedtest(skygge_bf),
            **varianter,
        }
    return ud


def bedste_fald_variant(df_1m: pd.DataFrame, virkelig: dict, wy: dict) -> dict:
    """§8: den bedste variant regnet også i bedste fald, hvor målet antages ramt først."""
    spor_navn, variant = wy["bedste"]
    spor = virkelig[spor_navn]["spor"]
    res = koer_varianter(df_1m, spor, spor.sig, bedste_fald=True, kun=(variant,))
    return {"spor": spor_navn, "variant": variant, **res[variant]["noegletal"]}


# ---------------------------------------------------------------------------
# Regressionstjek, §10 — alle tre skal holde, ellers køres intet
# ---------------------------------------------------------------------------

OPTAELLING_KOL = ["spor", "tabel", "periode", "side", "noegle", "stoerrelse", "vaerdi"]


def _score_linjer_af_fil(sti: Path) -> list[str]:
    """Scorefordelingens linjer, som de står i optællingens csv — rå tekst."""
    linjer = sti.read_text(encoding="utf-8").splitlines()
    return [x for x in linjer[1:] if x.split(",")[1] == "score"]


def _score_linjer_nu(spor_liste, dage: pd.DatetimeIndex) -> list[str]:
    """Scorefordelingen regnet forfra, skrevet med samme ``to_csv`` som optællingen.

    Sammenligningen sker på csv-teksten, ikke på genindlæste float-værdier: en float der
    har været en tur gennem decimaltekst kan komme tilbage én ULP ved siden af sig selv
    uden at tallet er et andet — samme fælde som trin A's regressionstjek beskriver.
    """
    import tempfile
    dele = []
    for spor in spor_liste:
        t = pd.DataFrame(fl.scoretabel(spor.sig, dage))
        t.insert(0, "spor", spor.navn)
        dele.append(t)
    tabel = pd.concat(dele, ignore_index=True)[OPTAELLING_KOL]
    with tempfile.TemporaryDirectory() as tmp:
        sti = Path(tmp) / "score.csv"
        tabel.to_csv(sti, index=False)
        return sti.read_text(encoding="utf-8").splitlines()[1:]


def regressionstjek(df_1m: pd.DataFrame | None = None,
                    kontekst: dict | None = None) -> dict:
    """§10's tre tjek.

    1. ``b4_k1_optaelling.py`` gengiver ``b4_k1_optaelling_v2.csv`` byte for byte.
    2. Spor A, variant "score ≥ 0" med buffer 10% og BE +1,2R gengiver motorrettelsens
       tal: ``handler_n`` 1.226 og ``middel_R_netto`` −0,0115.
    3. Scorefordelingen gengiver ``b4_k1_trin2_optaelling.csv``.
    """
    csv_ok = trinA.regressionstjek()
    df = mnq() if df_1m is None else df_1m
    spor_a = (byg_spor(df, "A") if kontekst is None else kontekst["A"])
    spor_b = (byg_spor(df, "B") if kontekst is None else kontekst["B"])

    handler, _, _ = gennemloeb(df, spor_a.sig, spor_a.tf_min, BE_R, disciplin=True)
    handler_n = len(handler)
    middel = float(handler["R_netto"].mean()) if handler_n else float("nan")
    motor_ok = (handler_n == REGRESSION_HANDLER_N
                and round(middel, 4) == REGRESSION_MIDDEL_R_NETTO)

    dage = k1.rth_dage(trinA.MNQ_START, trinA.TRIN_A_SLUT)
    ny = _score_linjer_nu((spor_a, spor_b), dage)
    gammel = _score_linjer_af_fil(OPTAELLING_CSV)
    score_ok = bool(ny == gammel)
    return {"csv_byte_for_byte": bool(csv_ok), "motor_handler_n": handler_n,
            "motor_middel_R_netto": middel, "motor_ok": bool(motor_ok),
            "score_rader_n": len(ny), "score_linjer_i_reference_n": len(gammel),
            "score_ok": score_ok,
            "alle_ok": bool(csv_ok and motor_ok and score_ok)}


# ---------------------------------------------------------------------------
# Den lange tabel, §9's .csv
# ---------------------------------------------------------------------------

def _rk(spor: str, tabel: str, noegle: str, **maal) -> list[dict]:
    rows = []
    for k, v in maal.items():
        if isinstance(v, (bool, np.bool_)):
            v = float(bool(v))
        try:
            v = float(v)
        except (TypeError, ValueError):
            continue
        rows.append({"spor": spor, "tabel": tabel, "noegle": noegle, "stoerrelse": k,
                     "vaerdi": v})
    return rows


def lang_tabel(virkelig: dict, wy: dict, n1_liste: list[dict], beta_n1: dict,
               bf_variant: dict) -> pd.DataFrame:
    """Alle tal i langt format: én række pr. (spor, tabel, nøgle, størrelse)."""
    rows: list[dict] = []
    for spor_navn, res in virkelig.items():
        h = res["hovedtest"]
        rows += _rk(spor_navn, "hovedtest", "beta", mde_beta=MDE_BETA[spor_navn],
                    signaler_n=res["signaler_n"], skygge_n=len(res["skygge"]), **h)
        rows += _rk(spor_navn, "hovedtest_bedste_fald", "beta", **res["hovedtest_bedste_fald"])
        rows += _rk(spor_navn, "hovedtest_N1", "beta", **beta_n1[spor_navn])
        for r in diagnose_score(res["skygge"]):
            rows += _rk(spor_navn, "score", r.pop("noegle"), **r)
        for r in diagnose_score(res["skygge_bedste_fald"]):
            rows += _rk(spor_navn, "score_bedste_fald", r.pop("noegle"), **r)
        for r in diagnose_kriterier(res["skygge"]):
            rows += _rk(spor_navn, "diagnose_kriterier", r.pop("noegle"), **r)
        for r in diagnose_side(res["skygge"]):
            rows += _rk(spor_navn, "diagnose_side", r.pop("noegle"), **r)
        for r in diagnose_aar(res["skygge"]):
            rows += _rk(spor_navn, "diagnose_aar", r.pop("noegle"), **r)
        rows += _rk(spor_navn, "diagnose_strejf", "skygge", **diagnose_strejf(res["strejf"]))
        for variant in VARIANTER:
            n = res[variant]["noegletal"]
            rows += _rk(spor_navn, "variant", variant,
                        mde_middel_R_netto=MDE_VARIANT[spor_navn][variant], **n)
            rows += _rk(spor_navn, "variant_strejf", variant,
                        **diagnose_strejf(res[variant]["strejf"]))
            n1 = wy["n1_pr_variant"][(spor_navn, variant)]
            rows += _rk(spor_navn, "variant_N1", variant, p5=_p(n1, 5), p50=_p(n1, 50),
                        p95=_p(n1, 95),
                        handler_n_p50=_p(wy["n1_handler_pr_variant"][(spor_navn, variant)], 50),
                        gyldige_n=int(np.isfinite(n1).sum()), R=wy["R"])
    rows += _rk("alle", "westfall_young", f"{wy['bedste'][0]}|{wy['bedste'][1]}",
                p_fwe=wy["p_fwe"], observeret_middel_R_netto=wy["observeret_middel_R_netto"],
                R=wy["R"], maks_p5=_p(wy["maks_fordeling"], 5),
                maks_p50=_p(wy["maks_fordeling"], 50), maks_p95=_p(wy["maks_fordeling"], 95))
    rows += _rk("alle", "bedste_fald_variant", f"{bf_variant['spor']}|{bf_variant['variant']}",
                **{k: v for k, v in bf_variant.items() if k not in ("spor", "variant")})
    b = beslutning({s: r["hovedtest"] for s, r in virkelig.items()}, wy, virkelig)
    rows += _rk("alle", "beslutning", b["kategori"], p_fwe=b["p_fwe"],
                middel_R_netto=b["middel_R_netto"], ci95_lo=b["ci95_lo"],
                ci95_hi=b["ci95_hi"], ci_krydser_020=b["ci_krydser_020"],
                ci_krydser_nul=b["ci_krydser_nul"],
                **{f"hovedtest_holder_{s}": v for s, v in b["hovedtest_holder"].items()})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Rapporten, §9
# ---------------------------------------------------------------------------

def _t(v, nd: int = 3) -> str:
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "—"
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    return f"{float(v):.{nd}f}".replace(".", ",")


def _rel(sti: Path) -> str:
    return Path(sti).resolve().relative_to(ROOT.resolve()).as_posix()


def hovedtabel_md(virkelig: dict, beta_n1: dict) -> str:
    """§9's hovedtest-tabel: β pr. spor med CI, p og N1's fordeling."""
    linjer = ["| spor | skyggehandler_n | dage_n | β_R_pr_scoretrin | CI95 | "
              "p_ensidet | α | MDE_β | N1_β p5/p50/p95 | andel_N1_β ≥ obs |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for navn, res in virkelig.items():
        h, n1 = res["hovedtest"], beta_n1[navn]
        linjer.append(
            f"| {navn} | {h['n']} | {h['klynger_n']} | {_t(h['beta'], 4)} | "
            f"[{_t(h['ci95_lo'], 4)}; {_t(h['ci95_hi'], 4)}] | {_t(h['p_ensidet'], 4)} | "
            f"{_t(ALFA_SPOR, 3)} | {_t(MDE_BETA[navn], 3)} | "
            f"{_t(n1['p5'], 4)}/{_t(n1['p50'], 4)}/{_t(n1['p95'], 4)} | "
            f"{_t(n1['andel_ge_observeret'], 3)} |")
    return "\n".join(linjer) + "\n"


def scoretabel_md(virkelig: dict) -> str:
    """Middel netto-R pr. score 0-5+, pr. spor."""
    linjer = ["| spor | score | handler_n | middel_R_brutto | middel_R_netto | CI95 | "
              "win_rate_pct_netto | holder_pct | tvetydige_n |",
              "|---|---|---|---|---|---|---|---|---|"]
    for navn, res in virkelig.items():
        for r in diagnose_score(res["skygge"]):
            linjer.append(
                f"| {navn} | {r['noegle']} | {r['handler_n']} | "
                f"{_t(r['middel_R_brutto'], 4)} | {_t(r['middel_R_netto'], 4)} | "
                f"[{_t(r['middel_R_netto_ci95_lo'], 4)}; {_t(r['middel_R_netto_ci95_hi'], 4)}] | "
                f"{_t(r['win_rate_pct_netto'], 1)} | {_t(r['holder_pct'], 1)} | "
                f"{r['tvetydige_n']} |")
    return "\n".join(linjer) + "\n"


def varianttabel_md(virkelig: dict, wy: dict) -> str:
    """§9's varianttabel: de otte varianter, med N1 og p_FWE på den bedste."""
    linjer = ["| spor | variant | handler_n | middel_R_brutto | middel_R_netto | CI95 | "
              "win_rate_pct_netto | maal/stop/BE/tidsexit_pct | N1_p50 | N1_p5 | p_FWE |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    for navn, res in virkelig.items():
        for variant in VARIANTER:
            n = res[variant]["noegletal"]
            n1 = wy["n1_pr_variant"][(navn, variant)]
            p_fwe = _t(wy["p_fwe"], 4) if wy["bedste"] == (navn, variant) else "—"
            linjer.append(
                f"| {navn} | {VARIANT_TEKST[variant]} | {n['handler_n']} | "
                f"{_t(n['middel_R_brutto'], 4)} | {_t(n['middel_R_netto'], 4)} | "
                f"[{_t(n['middel_R_netto_ci95_lo'], 4)}; {_t(n['middel_R_netto_ci95_hi'], 4)}] | "
                f"{_t(n['win_rate_pct_netto'], 1)} | "
                f"{_t(n['udfald_maal_pct'], 1)}/{_t(n['udfald_stop_pct'], 1)}/"
                f"{_t(n['udfald_BE_pct'], 1)}/{_t(n['udfald_tidsexit_pct'], 1)} | "
                f"{_t(_p(n1, 50), 4)} | {_t(_p(n1, 5), 4)} | {p_fwe} |")
    return "\n".join(linjer) + "\n"


def kriterietabel_md(virkelig: dict) -> str:
    linjer = ["| spor | kriterium | sand_n | sand_middel_R_netto | falsk_n | "
              "falsk_middel_R_netto | forskel | CI95 på forskellen |",
              "|---|---|---|---|---|---|---|---|"]
    for navn, res in virkelig.items():
        for r in diagnose_kriterier(res["skygge"]):
            linjer.append(
                f"| {navn} | {r['noegle'].split('_', 1)[1]} | {r['sand_n']} | "
                f"{_t(r['sand_middel_R_netto'], 4)} | {r['falsk_n']} | "
                f"{_t(r['falsk_middel_R_netto'], 4)} | {_t(r['forskel_R_netto'], 4)} | "
                f"[{_t(r['forskel_ci95_lo'], 4)}; {_t(r['forskel_ci95_hi'], 4)}] |")
    return "\n".join(linjer) + "\n"


def sidetabel_md(virkelig: dict) -> str:
    linjer = ["| spor | nøgle | handler_n | middel_R_netto | CI95 |", "|---|---|---|---|---|"]
    for navn, res in virkelig.items():
        for r in diagnose_side(res["skygge"]):
            linjer.append(f"| {navn} | {r['noegle']} | {r['handler_n']} | "
                          f"{_t(r['middel_R_netto'], 4)} | "
                          f"[{_t(r['middel_R_netto_ci95_lo'], 4)}; "
                          f"{_t(r['middel_R_netto_ci95_hi'], 4)}] |")
    return "\n".join(linjer) + "\n"


def aarstabel_md(virkelig: dict) -> str:
    linjer = ["| spor | " + " | ".join(str(a) for a in AAR_LISTE) + " |",
              "|---" * (len(AAR_LISTE) + 1) + "|"]
    for navn, res in virkelig.items():
        r = {x["noegle"]: x for x in diagnose_aar(res["skygge"])}
        linjer.append(f"| {navn} | " + " | ".join(
            f"{_t(r[str(a)]['middel_R_netto'], 4)} (n={r[str(a)]['handler_n']})"
            for a in AAR_LISTE) + " |")
    return "\n".join(linjer) + "\n"


def omkostningstabel_md(virkelig: dict) -> str:
    linjer = ["| spor | variant | signaler_n | omk_R_netto_p50 | omk_R_netto_p90 | "
              "strejf_n | strejf_hvis_fyldt_middel_R_netto |",
              "|---|---|---|---|---|---|---|"]
    for navn, res in virkelig.items():
        for variant in VARIANTER:
            n = res[variant]["noegletal"]
            s = diagnose_strejf(res[variant]["strejf"])
            linjer.append(
                f"| {navn} | {VARIANT_TEKST[variant]} | {n['signaler_n']} | "
                f"{_t(n['omk_R_netto_p50'], 4)} | {_t(n['omk_R_netto_p90'], 4)} | "
                f"{s['strejf_n']} | {_t(s['hvis_fyldt_middel_R_netto'], 4)} |")
    return "\n".join(linjer) + "\n"


def skriv_md(resultat: dict, meta: dict) -> str:
    """§9's rapport. Brutto og netto side om side, enheden i kolonnenavnet."""
    virkelig, wy, beta_n1 = resultat["virkelig"], resultat["wy"], resultat["beta_n1"]
    b, bf = resultat["beslutning"], resultat["bedste_fald_variant"]
    c = meta["commits"]
    dele = [
        "# B4 kandidat 1 — trin 2: videoens kriterier som score\n",
        f"Kørt {meta['koert_utc']} UTC fra commit `{meta['head'][:7]}`, med modul, tests, "
        f"præregistreringer, filtre, kerne, motor og datalag committet og uændrede. "
        f"Præregistrering `{_rel(PREREG)}` (commit `{c[_rel(PREREG)][:7]}`), definitioner "
        f"`{_rel(PREREG_OPT)}` (commit `{c[_rel(PREREG_OPT)][:7]}`) med tillæg "
        f"`{_rel(PREREG_TIL)}` (commit `{c[_rel(PREREG_TIL)][:7]}`). Kode "
        f"`{_rel(Path(__file__))}` (commit `{c[_rel(Path(__file__))][:7]}`), filtre "
        f"`research/b4_k1_filtre.py` (commit `{c['research/b4_k1_filtre.py'][:7]}`), motor "
        f"`research/b4_k1_trinA.py` (commit `{c['research/b4_k1_trinA.py'][:7]}`), kerne "
        f"`research/b4_k1_optaelling.py` (commit "
        f"`{c['research/b4_k1_optaelling.py'][:7]}`).\n",
        f"Serie: MNQ.v.0 ohlcv-1m gennem `data.holdout.load_in_sample`, "
        f"{meta['foerste_bar_utc']} → {meta['sidste_bar_utc']} UTC, {meta['n_1m']} "
        f"1m-barer. Kerne v2, buffer 10%, BE +1,2R, den rettede motor. Spor A: 15m med "
        f"1h. Spor B: 5m med 15m. N1: {wy['R']} gentagelser pr. spor.\n",
        "## Regressionstjek, §10 — før kørslen\n",
        f"1. `research/b4_k1_optaelling.py` gengiver `b4_k1_optaelling_v2.csv` byte for "
        f"byte: **{'OK' if meta['regression']['csv_byte_for_byte'] else 'AFVIGER'}**.\n"
        f"2. Spor A, score ≥ 0, buffer 10%, BE +1,2R: `handler_n` "
        f"{meta['regression']['motor_handler_n']} og `middel_R_netto` "
        f"{_t(meta['regression']['motor_middel_R_netto'], 4)} mod motorrettelsens "
        f"{REGRESSION_HANDLER_N} og {_t(REGRESSION_MIDDEL_R_NETTO, 4)}: "
        f"**{'OK' if meta['regression']['motor_ok'] else 'AFVIGER'}**.\n"
        f"3. Scorefordelingen gengiver `b4_k1_trin2_optaelling.csv` "
        f"({meta['regression']['score_rader_n']} rækker): "
        f"**{'OK' if meta['regression']['score_ok'] else 'AFVIGER'}**.\n",
        "## Hovedtesten, §4 — stiger middel netto-R med scoren?\n",
        "Enheden er skyggehandler: hvert signal simuleres for sig, uden disciplinregler. "
        "β er hældningen i en OLS af `R_netto` på scoren (0, 1, 2, 3, 4, 5+), med "
        "klyngerobust standardfejl pr. handelsdag. Én-sidet, H1: β > 0, α = 0,025 pr. "
        "spor (Bonferroni over 2). `dage_n` er antallet af klynger.\n",
        hovedtabel_md(virkelig, beta_n1),
        "### Middel netto-R pr. score\n",
        scoretabel_md(virkelig),
        "## Varianterne, §5 — handlet med disciplinreglerne\n",
        "Westfall-Young maks-statistik over alle otte varianter på tværs af begge spor: "
        "for hver N1-gentagelse gemmes den største middel netto-R blandt de otte. `p_FWE` "
        "står kun på den observerede bedste variant. `N1_p50`/`N1_p5` er den variants "
        "egen fordeling over gentagelserne, ikke maks-fordelingen.\n",
        varianttabel_md(virkelig, wy),
        f"Bedste variant: **spor {wy['bedste'][0]}, {VARIANT_TEKST[wy['bedste'][1]]}** med "
        f"middel netto-R {_t(wy['observeret_middel_R_netto'], 4)}. N1's maks-fordeling: "
        f"p5 {_t(_p(wy['maks_fordeling'], 5), 4)}, p50 {_t(_p(wy['maks_fordeling'], 50), 4)}, "
        f"p95 {_t(_p(wy['maks_fordeling'], 95), 4)}. `p_FWE` = {_t(wy['p_fwe'], 4)}.\n",
        "## Beslutningsreglen, §7 — anvendt mekanisk\n",
        "| krav | tal | opfyldt |\n|---|---|---|\n"
        + "\n".join(
            f"| Hovedtesten signifikant på spor {s} (p ≤ 0,025) | "
            f"p = {_t(virkelig[s]['hovedtest']['p_ensidet'], 4)} | "
            f"{'ja' if v else 'nej'} |" for s, v in b["hovedtest_holder"].items())
        + f"\n| Bedste variant: p_FWE ≤ 0,05 | {_t(b['p_fwe'], 4)} | "
          f"{'ja' if b['p_fwe'] <= 0.05 else 'nej'} |\n"
          f"| Bedste variant: middel netto-R ≥ +0,20 R | {_t(b['middel_R_netto'], 4)} | "
          f"{'ja' if np.isfinite(b['middel_R_netto']) and b['middel_R_netto'] >= 0.20 else 'nej'} |\n"
          f"| Bedste variant: CI-nedre > 0 | {_t(b['ci95_lo'], 4)} | "
          f"{'ja' if np.isfinite(b['ci95_lo']) and b['ci95_lo'] > 0 else 'nej'} |\n",
        f"**Kategori: {b['kategori']}.** {b['tekst']}\n",
        "§7's tre rækker er udtømmende — tredje række er \"alt andet\" — så hvert udfald "
        "falder i præcis én. Sætningen om at den laveste kategori gælder når et "
        "konfidensinterval krydser en grænse, har derfor intet at afgøre her; "
        f"intervallet for den bedste variant krydser "
        f"{'0,20' if b['ci_krydser_020'] else 'ikke 0,20'} og "
        f"{'nul' if b['ci_krydser_nul'] else 'ikke nul'}.\n",
        "## Diagnoserne, §8 — rapporteres, afgør intet\n",
        "### Tvetydige minutter og bedste fald\n",
        "En handel er tvetydig når stoppet blev ramt i en 1m-bar hvor **også** målet "
        "eller BE-triggeren kunne nås. Regel 4 antager stoppet først; bedste fald vender "
        "netop de bar om. Motorrettelse 1 står ved magt begge veje: i fyldningsbaren "
        "tjekkes kun stoppet.\n",
        "| spor | skyggehandler_n | tvetydige_n | tvetydige_pct | β forsigtigt | "
        "β bedste fald | p_ensidet bedste fald |\n|---|---|---|---|---|---|---|\n"
        + "\n".join(
            f"| {navn} | {len(res['skygge'])} | "
            f"{int(res['skygge']['tvetydig'].sum()) if len(res['skygge']) else 0} | "
            f"{_t(100 * res['skygge']['tvetydig'].mean() if len(res['skygge']) else float('nan'), 1)} | "
            f"{_t(res['hovedtest']['beta'], 4)} | "
            f"{_t(res['hovedtest_bedste_fald']['beta'], 4)} | "
            f"{_t(res['hovedtest_bedste_fald']['p_ensidet'], 4)} |"
            for navn, res in virkelig.items()) + "\n",
        f"Den bedste variant (spor {bf['spor']}, {VARIANT_TEKST[bf['variant']]}) i bedste "
        f"fald: `handler_n` {bf['handler_n']}, middel netto-R {_t(bf['middel_R_netto'], 4)} "
        f"[{_t(bf['middel_R_netto_ci95_lo'], 4)}; {_t(bf['middel_R_netto_ci95_hi'], 4)}] "
        f"mod {_t(b['middel_R_netto'], 4)} forsigtigt. "
        "**Afgørelsen i §7 er taget på det forsigtige tal.**\n",
        "### Middel netto-R pr. kriterium, sandt mod falsk\n",
        "Beskrivende. **Må ikke bruges til nye varianter uden ny præregistrering, og en "
        "sådan brug koster fuldt N.**\n",
        kriterietabel_md(virkelig),
        "### Demand og supply hver for sig\n",
        sidetabel_md(virkelig),
        "### Pr. år — middel netto-R på skyggehandlerne\n",
        aarstabel_md(virkelig),
        "### Omkostninger og strejf pr. variant\n",
        omkostningstabel_md(virkelig),
        "## Efter kørslen — §12\n",
        "Stop. Ingen ændring af definitioner, ingen nye varianter, ingen forslag. "
        "Resultatet læses sammen med ejeren, og §7 anvendes mekanisk.\n",
        f"Alle tal: `{_rel(OUT / 'b4_k1_trin2.csv')}` (langt format: `spor`, `tabel`, "
        "`noegle`, `stoerrelse`, `vaerdi`).\n",
    ]
    return "\n".join(dele)


# ---------------------------------------------------------------------------
# Tidsmålingen, §10
# ---------------------------------------------------------------------------

def tidsmaaling(n_reps: int = 5, max_workers: int | None = None) -> dict:
    """§10: ét gennemløb pr. spor og ``n_reps`` N1-gentagelser pr. spor, fremskrevet til
    R = 500. Kører hverken Westfall-Young eller nogen beslutningsregel."""
    t0 = time.perf_counter()
    df = mnq()
    load_s = time.perf_counter() - t0

    opbygning, gennemloeb_s, kontekst = {}, {}, {}
    for navn in SPOR:
        t0 = time.perf_counter()
        kontekst[navn] = byg_spor(df, navn)
        opbygning[navn] = time.perf_counter() - t0
        t0 = time.perf_counter()
        res = koer_virkelig(df, (navn,), kontekst)
        gennemloeb_s[navn] = time.perf_counter() - t0
        opbygning[f"{navn}_signaler_n"] = res[navn]["signaler_n"]
        opbygning[f"{navn}_skygge_n"] = len(res[navn]["skygge"])

    n_workere = max_workers or (os.cpu_count() or 1)
    _, tid = koer_n1(n_reps, tuple(SPOR), n_workere)
    init_s = load_s + sum(opbygning[n] for n in SPOR)
    runde = math.ceil(N1_REPS / tid["n_workere"])
    forventet_s = init_s + tid["middel_s_pr_gentagelse"] * runde
    return {"load_s": load_s, "opbygning_s": opbygning, "gennemloeb_s": gennemloeb_s,
            "init_s_pr_arbejder": init_s, "n1": tid, "n_reps_maalt": n_reps,
            "R": N1_REPS, "runder": runde, "forventet_vaeg_s": forventet_s,
            "forventet_vaeg_timer": forventet_s / 3600}


# ---------------------------------------------------------------------------
# Selve kørslen
# ---------------------------------------------------------------------------

def koer(n1_reps: int = N1_REPS, max_workers: int | None = None) -> dict:
    """§4-§8. Regressionstjekket først — afviger ét, køres intet."""
    df = mnq()
    kontekst = {navn: byg_spor(df, navn) for navn in SPOR}
    regression = regressionstjek(df, kontekst)
    if not regression["alle_ok"]:
        raise RuntimeError(f"regressionstjekket afveg, trin 2 køres ikke: {regression}")

    virkelig = koer_virkelig(df, tuple(SPOR), kontekst)
    n1_liste, tid = koer_n1(n1_reps, tuple(SPOR), max_workers)
    wy = westfall_young(virkelig, n1_liste)
    beta_n1 = {navn: n1_beta(n1_liste, navn, virkelig[navn]["hovedtest"]["beta"])
               for navn in virkelig}
    bf = bedste_fald_variant(df, virkelig, wy)
    b = beslutning({s: r["hovedtest"] for s, r in virkelig.items()}, wy, virkelig)
    tabel = lang_tabel(virkelig, wy, n1_liste, beta_n1, bf)
    return {"df": df, "virkelig": virkelig, "n1_liste": n1_liste, "wy": wy,
            "beta_n1": beta_n1, "bedste_fald_variant": bf, "beslutning": b,
            "tabel": tabel, "regression": regression, "tid": tid, "n1_reps": n1_reps}


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "--no-optional-locks", "-C", str(ROOT), *args],
                          capture_output=True, text=True)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--regressionstjek", action="store_true",
                     help="§10's tre tjek. Kører ikke trin 2")
    grp.add_argument("--tidsmaaling", action="store_true",
                     help="§10: ét gennemløb pr. spor og 5 N1-gentagelser, fremskrevet "
                          "til R = 500")
    grp.add_argument("--koer", action="store_true",
                     help="§4-§8: selve kørslen. Skriver b4_k1_trin2.md og .csv")
    ap.add_argument("--n1-reps", type=int, default=N1_REPS)
    ap.add_argument("--maalte-reps", type=int, default=5)
    ap.add_argument("--max-workers", type=int, default=None)
    ap.add_argument("--ud", type=Path, default=None)
    args = ap.parse_args(argv)

    if args.regressionstjek:
        r = regressionstjek()
        print(f"1. b4_k1_optaelling_v2.csv byte for byte: "
              f"{'OK' if r['csv_byte_for_byte'] else 'AFVIGER'}")
        print(f"2. spor A, score >= 0: handler_n {r['motor_handler_n']} "
              f"(ventet {REGRESSION_HANDLER_N}), middel_R_netto "
              f"{r['motor_middel_R_netto']:.4f} (ventet {REGRESSION_MIDDEL_R_NETTO}): "
              f"{'OK' if r['motor_ok'] else 'AFVIGER'}")
        print(f"3. scorefordelingen mod b4_k1_trin2_optaelling.csv "
              f"({r['score_rader_n']} raekker): {'OK' if r['score_ok'] else 'AFVIGER'}")
        if not r["alle_ok"]:
            sys.exit(1)
        return

    if args.tidsmaaling:
        t = tidsmaaling(args.maalte_reps, args.max_workers)
        print(f"CPU'er: {t['n1']['cpu_count']}, arbejdere: {t['n1']['n_workere']}")
        print(f"Indlaesning: {t['load_s']:.1f} s")
        for navn in SPOR:
            print(f"  spor {navn}: opbygning {t['opbygning_s'][navn]:.1f} s, "
                  f"gennemloeb {t['gennemloeb_s'][navn]:.1f} s, "
                  f"signaler {t['opbygning_s'][f'{navn}_signaler_n']}, "
                  f"skyggehandler {t['opbygning_s'][f'{navn}_skygge_n']}")
        print(f"{t['n_reps_maalt']} N1-gentagelser (begge spor hver): "
              f"{t['n1']['vaeg_s']:.1f} s vaeg-ur, "
              f"{t['n1']['middel_s_pr_gentagelse']:.1f} s pr. gentagelse maalt i arbejderen")
        print(f"Fremskrevet til R = {t['R']}: {t['runder']} runder a "
              f"{t['n1']['middel_s_pr_gentagelse']:.1f} s + {t['init_s_pr_arbejder']:.1f} s "
              f"opbygning = {t['forventet_vaeg_s']:.0f} s "
              f"({t['forventet_vaeg_timer']:.2f} timer)")
        return

    commits = k1.committede(COMMITTEDE)
    head = _git("rev-parse", "HEAD").stdout.strip()
    resultat = koer(n1_reps=args.n1_reps, max_workers=args.max_workers)
    df = resultat["df"]
    meta = {"koert_utc": pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M"),
            "head": head, "commits": commits,
            "foerste_bar_utc": df.index[0].strftime("%Y-%m-%d %H:%M"),
            "sidste_bar_utc": df.index[-1].strftime("%Y-%m-%d %H:%M"),
            "n_1m": len(df), "regression": resultat["regression"]}
    ud = args.ud if args.ud is not None else OUT
    ud.mkdir(parents=True, exist_ok=True)
    md = skriv_md(resultat, meta)
    (ud / "b4_k1_trin2.md").write_text(md, encoding="utf-8")
    resultat["tabel"].to_csv(ud / "b4_k1_trin2.csv", index=False)
    print(md)
    print(f"skrev {ud / 'b4_k1_trin2.md'} og .csv")
    print(f"N1: {resultat['n1_reps']} gentagelser, {resultat['tid']['vaeg_s']:.0f} s vaeg-ur")


if __name__ == "__main__":
    main()
