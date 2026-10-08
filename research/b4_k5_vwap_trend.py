"""B4 kandidat 5 — VWAP-trend efter Zarattini og Aziz (2023), MNQ 1m og 5m.

Præregistreret i ``research/prereg/b4_k5_vwap_trend.md``. Kilden er
``research/kilder/zarattini_aziz_vwap_noter.md``. Strategien har intet stop og måles ikke i
R, men i netto-dollar pr. dag pr. MNQ ved dagens niveau (§4g). Motoren er derfor ny og
ligger på et minutgitter: VWAP, signaler, ønsket position og handelstid er arrays med én
række pr. dag og én søjle pr. minut efter 08:30 CT. Westfall-Young er
``research/b4_k2_nowick.py``'s, brugt uændret. Kandidat 1-4's moduler importeres til serien,
kalenderen og regressionstjekket og røres ikke.

    .venv/bin/python -m research.b4_k5_vwap_trend --regressionstjek
    .venv/bin/python -m research.b4_k5_vwap_trend --optaelling
    .venv/bin/python -m research.b4_k5_vwap_trend --tidsmaaling
    .venv/bin/python -m research.b4_k5_vwap_trend --koer

Pris hentes kun gennem ``data.holdout.load_in_sample`` (``k2.mnq``); holdout åbnes ikke.
``--optaelling`` og ``--tidsmaaling`` viser ingen P&L, ingen hit ratio, ingen andel long
eller short og intet udfald. ``--koer`` er den rigtige kørsel og kræver ejerens godkendelse
(§11.6).

## Vejen gennem modulet

1. ``byg_grundlag``: RTH-1m-barerne (``data.sessions.rth_mask``) lagt på gitteret. Rultjek
   (§3), udelukkelse (§4h), VWAP (§4a), L_d (§4g) og lysene: 1m-barerne selv og 5m-lys
   bygget med ``data.resample.aggregate`` (§3).
2. ``tilstand``, ``vindue`` og ``positioner``: signalet ved hvert lys' lukning, den ønskede
   position over hver 1m-bar og handelstiden (§4b, §4d, §4e).
3. ``handler``: handlerne som sammenhængende stræk med samme position, udført på
   1m-barernes åbning (§4c). Ingen pris indgår.
4. ``resultat``: brutto og netto pr. handel (§4g). Kun i den rigtige kørsel og
   tidsmålingen.
5. ``nret_gentagelse``: nulmodellen N-retning (§6). ``k2.westfall_young`` og
   ``beslutning``: §7 og §8.
6. ``sigma_dag``, ``mde`` og ``styrke``: §7's MDE, betingelse og styrke, uden udfald.
7. ``optaelling`` (§11.4), ``tidsmaaling`` (§11.5), ``analyse`` og ``skriv_md`` (§9-§10).

## Læsninger — valgt af Code, skrevet op før kørslen

Præregistreringen fastlægger ikke disse detaljer. De er valgt her og skal bekræftes. Dem
der kan flytte et resultat, eller hvor præregistreringen kan læses på to måder, er mærket
**[tvivl]**.

1. **Dagen** er XNYS-sessionsdagen (ET-datoen, ``k1._et_dag``), som i kandidat 1-4. Alt
   regnes i CT. 08:30 CT er altid 09:30 ET, fordi Chicago og New York skifter sommertid
   samme dag. Åbner XNYS ikke kl. 08:30 CT på en dag, stopper koden.
2. **Fladt-tidspunktet** er XNYS' lukketid minus 5 minutter: 14:55 CT på hele dage og
   11:55 CT på kortdage (§4d). I 2019-2023 lukker XNYS kun kl. 15:00 eller 12:00 CT.
3. **Hullet i §4h** er antallet af manglende minutter mellem to RTH-1m-barer, altså
   afstanden mellem starttiderne minus 1, som ``sessions.break_mask`` regner et hul. En dag
   udelukkes ved mere end 5. Det passer med grænsen for første bar: starter dagen kl. 08:35
   (5 manglende minutter), er den med; kl. 08:36 er den ude. **[tvivl]** "Hul" kan også
   læses som afstanden mellem starttiderne, og så udelukker 5 manglende minutter. I serien
   er afstandene 1, 3, 4, 14 og 15 minutter, så begge læsninger udelukker de samme 4 dage.
4. **Manglende barer sidst på dagen** (efter dagens sidste RTH-bar) er ikke dækket af §4h
   og udelukker ikke. Mangler alle barer fra fladt-tidspunktet, lukkes positionen på
   åbningen af næste bar i serien efter RTH. Det tælles (``udgang_efter_rth_n``). I serien
   slutter alle dage med 14:59- eller 11:59-baren.
5. **Dage uden RTH-barer** udelukkes og tælles for sig. Der er ingen i serien.
6. **Rultjekket** (§3, test 12): skifter ``instrument_id`` mellem to RTH-1m-barer samme
   dag, stopper koden med en fejl. Det gælder alle dage, også de udelukkede. Desuden skal
   en handels udgangsbar være i samme kontrakt som indgangsbaren.
7. **VWAP** regnes kun på dagens RTH-barer fra 08:30 CT (§4a). En manglende bar bidrager
   med intet, og VWAP i et manglende minut er VWAP ved forrige bar. Er dagens volumen
   indtil da 0, er VWAP udefineret, og lyset giver intet signal. Det tælles; alle barer i
   serien har volumen > 0.
8. **5m-lyset** er ``data.resample.aggregate`` af dagens RTH-1m-barer. Dets VWAP er VWAP
   ved lysets sidste 1m-bar der findes. Den bars close er også lysets close. Koden tjekker,
   at gitteret og ``aggregate`` giver de samme lys med samme close.
9. **Close = VWAP** sammenlignes direkte i flydende tal. Lighed giver intet signal.
10. **Den ønskede position følges hele dagen,** også i pausen. Den er det seneste signal ≠ 0
    fra et lukket lys. Den faktiske position er den ønskede inden for handelstiden og 0
    uden for. Kl. 14:00 åbnes derfor efter det sidst lukkede lys (1m-lyset kl. 13:59 eller
    5m-lyset 13:55-14:00). Lukkede det præcis på VWAP, gælder signalet før. **[tvivl]**
    §4b's regel for dagens første handel (vent på et lys over eller under) kunne også
    læses som gældende kl. 14:00. Forskellen opstår kun, hvis lyset kl. 13:59 lukker
    præcis på VWAP.
11. **Første handel:** mangler 08:30-baren (tilladt til 08:35), er dagens første 1m-lys den
    første bar der findes. 5m-lyset 08:30-08:35 består af de barer der findes.
12. **Udførelsen** af en ændring sker på åbningen af den første 1m-bar, der starter på
    eller efter det nominelle tidspunkt. Det nominelle tidspunkt er lysets slutning ved et
    signal, 11:00 eller 14:00 CT ved pausen og fladt-tidspunktet ved fladt. Om et signal
    "skulle udføres kl. 14:55 CT eller senere" (eller i pausen), afgøres af den bar der
    faktisk bruges. Udførelser på en senere bar, fordi minuttet manglede, tælles
    (``udfoert_senere_n``).
13. **En handel** er et sammenhængende stræk af 1m-barer med samme position ≠ 0. Indgangen
    er åbningen af strækkets første bar, udgangen åbningen af næste bar i serien. En
    vending lukker og åbner på samme bar til samme pris.
14. **Normeringen** (§4g): ``skala_d = 29.138 / L_d`` og ``netto_usd_i = brutto_pt_i ×
    skala_d × 2 − 2,627``. Middel over alle dage der indgår; en dag uden handel tæller med
    0. CI95 er t-intervallet over dagene (``stats.mean_ci_t``).
15. **N-retning** (§6): retningen er ``2 × bit − 1``, hvor bit er cellen (dag,
    indgangsminut) i ``default_rng([9500, gentagelse, tidsramme]).integers(0, 2,
    (XNYS-dage, 390))``. Dagen er dens plads blandt alle XNYS-dage i perioden, indgangs-
    minuttet er minutter efter 08:30 CT. De to middagsvarianter med samme tidsramme deler
    gitter, så samme indgangsminut giver samme retning. 1m og 5m trækkes uafhængigt.
16. **Westfall-Young** er ``k2.westfall_young`` uændret: énsidet, sd med ddof = 1.
17. **σ_dag** (§7): summen går over variantens lys, der ligger helt i handelstiden regnet
    fra den første mulige udførelse (08:31 for 1m, 08:35 for 5m), ikke fra modellens
    faktiske første handel. Det er 1m-lys 08:31-14:54 og 5m-lys 08:35-14:50; uden middag
    kun til 10:59 eller 10:55 og igen fra 14:00. ``Δclose`` er mod forrige lys samme dag,
    også når det ligger uden for handelstiden (08:30-lyset, 13:59-lyset). **[tvivl]**
18. **Styrken for netto** (§7): nettoeffekten er ``82 − handler_n × 2,627 / n_dage``, og
    styrken er ``Φ(√n_dage × netto / σ_dag − 1,96)``, en normalapproksimation for
    CI-nedre > 0. **[tvivl]** "handler pr. dag" er læst som middel, ikke median, fordi
    omkostningen pr. dag er et middel.
19. **Omkostningen i bp** (§11.4) er ``2,627 / (2 × L) × 10⁴`` pr. round trip ved årets
    median af L_d. Pr. variant og år desuden middel over dagene af ``handler_d × 2,627 /
    (2 × L_d) × 10⁴``.
20. **Holdetid** er minutter fra indgangsbarens start til udgangsbarens start.
21. **Break-even-omkostningen** (§9): ``c_middel = Σ brutto_usd / handler_n`` ved dagens
    niveau. ``c_CI`` er den omkostning, hvor t-intervallets nedre grænse for
    ``dag_brutto_d − c × handler_d`` er 0, fundet ved halvering. Den nedre grænse falder
    strengt i c, når middel handler pr. dag er større end ``t × sd(handler_d) / √n``.
22. **Hit ratio** er andelen af handler med P&L > 0. **Gevinst/tab-forholdet** er middel af
    gevinsterne over |middel af tabene|; handler på præcis 0 indgår i ingen af dem. Brutto
    og netto er ved dagens niveau.
23. **Brutto pr. halve time** (§9): hver holdt 1m-bar bidrager med ``retning ×
    (open_næste − open) × skala × 2`` til sin halve time i New York-tid. Det summer præcis
    til handlens brutto. Rapporteret som middel pr. dag over alle dage.
24. **De sidste 5 minutter** (§9): positionen der lukkes ved fladt, holdt til close af
    dagens sidste RTH-bar (14:59 eller 11:59 CT): ``retning × (close_sidste − open_fladt) ×
    skala × 2``.
25. **Største tab inden for dagen** (§9): dagens løbende P&L ved hver holdt 1m-bars close
    og efter hver handel, med hele round trip-omkostningen trukket ved indgangen.
    ``min(0, …)`` pr. dag. **[tvivl]** At trække omkostningen ved indgangen er den
    forsigtige side; forskellen er højst $2,627 for den åbne handel.
26. **Konsistens** (§9): bedste dags andel er ``max_d / Σ_d``, og de 5% bedste dages andel
    er summen af de ``ceil(0,05 × n_dage)`` bedste dage over ``Σ_d``. Kun når ``Σ_d > 0``.
27. **Altid-long** (§6): køb på åbningen af første bar fra 08:31 CT, sælg på åbningen af
    første bar fra fladt-tidspunktet. Én serie for alle varianter, samme omkostning og
    normering.
28. **Årlig Sharpe** = middel / sd (ddof = 1) af ``dag_netto_usd`` × √252.
29. **Nominelt** (§9) er ``brutto_pt × 2 − 2,627`` uden normering. **$3,169** er
    ``2,627 + 2 × 0,5417 × 0,25 × 2 = 3,1687``. Nulmodellen flyttes med samme omkostning,
    så t_v og p_FWE er de samme som ved $2,627; kun intervallet flytter sig.
30. **§8's række 2** er erstattet af tillæggets §2 (``b4_k5_vwap_trend_tillaeg.md``):
    mindst én variant har p_FWE ≤ 0,05, men ingen opfylder række 1. Varianter med CI-nedre
    > 0 uden p_FWE ≤ 0,05 skrives da op som in-sample-fund (``in_sample_fund``).
31. **Kandidat 4's regressionstjek** (§11.3, k = 1,5 · 1/dag) køres ad kandidat 4's egen
    vej: ``k4.byg_grundlag``, ``k4.dagsforloeb`` og ``k4.handelstabel``, uændret.

Tillæggets §3 (godkendt sammen med læsningerne): de dage §4h udelukker, rapporteres for sig
pr. variant (``udelukkede_dage``). De regnes på deres eget gitter uden udelukkelse, med
præcis samme motor: positionen holdes gennem stoppet, og udførelsen sker ved første bar
efter det (læsning 12). De indgår ikke i middel, CI, nulmodel eller §8.
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

from data import resample, sessions  # noqa: E402
from research import b4_k1_optaelling as k1  # noqa: E402
from research import b4_k1_trinA as trinA  # noqa: E402
from research import b4_k2_nowick as k2  # noqa: E402
from research import b4_k4_emt as k4  # noqa: E402
from research.normal import norm  # noqa: E402
from research.stats import mean_ci_t, t_critical  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "output"
PREREG = ROOT / "research" / "prereg" / "b4_k5_vwap_trend.md"
KILDE = ROOT / "research" / "kilder" / "zarattini_aziz_vwap_noter.md"
TILLAEG = ROOT / "research" / "prereg" / "b4_k5_vwap_trend_tillaeg.md"
# Den rigtige kørsel sker kun når disse er committet og uændrede.
COMMITTEDE = (
    Path(__file__).resolve(), ROOT / "tests" / "test_b4_k5_vwap_trend.py", PREREG, TILLAEG,
    KILDE,
    ROOT / "research" / "b4_k4_emt.py", ROOT / "research" / "b4_k3_vending.py",
    ROOT / "research" / "b4_k2_nowick.py", ROOT / "research" / "b4_k1_trinA.py",
    ROOT / "research" / "b4_k1_filtre.py", ROOT / "research" / "b4_k1_optaelling.py",
    ROOT / "research" / "stats.py", ROOT / "research" / "normal.py",
    ROOT / "data" / "holdout.py", ROOT / "data" / "resample.py",
    ROOT / "data" / "sessions.py",
)

CT = k1.CT
NY = sessions.ET
MIN_NS = 60 * 10**9
DAG_MIN = 390                            # 08:30-15:00 CT
FLAD_FOER_LUK = 5                        # §4d: fladt 5 min før NYSE lukker
PAUSE = (150, 330)                       # §4e: 11:00 og 14:00 CT, minutter efter 08:30
FOERSTE_SENEST = 5                       # §4h: første bar senest 08:35 CT
MAKS_HUL = 5                             # §4h: højst 5 manglende minutter i træk

TIDSRAMMER = (1, 5)                      # §3, svar 3A
HELE, UDEN = "hele dagen", "uden middag"
MIDDAG = (HELE, UDEN)
VARIANTER = tuple((tf, m) for tf in TIDSRAMMER for m in MIDDAG)
ARTIKLENS = (1, HELE)                    # §5: artiklens strategi

MNQ_USD_PR_POINT = trinA.MNQ_USD_PR_POINT
OMK_USD = trinA.OMK_USD_RUNDTUR          # 2,627, §4f
OMK_DIAGNOSE_USD = OMK_USD + 2 * trinA.SLIP_PT * MNQ_USD_PR_POINT   # 3,1687, §4f
NQ_NIVEAU = k1.NQ_NIVEAU                 # 29.138, §4g

VENDING, PAUSE_UD, FLADT, EFTER_RTH = 1, 2, 3, 4
UDGANGE = {VENDING: "vending", PAUSE_UD: "pause", FLADT: "fladt", EFTER_RTH: "efter_rth"}

NRET_REPS = 500                          # §6, sænkes ikke
NRET_SEED = 9500

# §7: énsidet α = 0,05 med Šidák 4 (z = 2,2340) og tosidet 95%, begge + z_0,80.
Z_SIDAK4 = 3.0756
Z_CI = 2.8016
MDE_GRAENSE_USD = 82.0                   # §7: artiklens effekt ved dagens niveau
ARTIKEL_BRUTTO_USD = 82.0
HANDELSDAGE_AAR = 252
AAR_LISTE = list(range(2019, 2024))

# §11.3: kandidat 4's k = 1,5 · 1/dag (commit 0291052).
REGRESSION_K4_HANDLER_N = 1104
REGRESSION_K4_MIDDEL_R_NETTO = -0.0920


# ---------------------------------------------------------------------------
# Serien og gitteret, §3, §4a og §4h
# ---------------------------------------------------------------------------

def mnq() -> pd.DataFrame:
    """MNQ.v.0 1m, 2019-05-06 → 2023-12-31, kun gennem holdout-modulet."""
    return k2.mnq()


def _ffill_idx(maske: np.ndarray) -> np.ndarray:
    """Pr. række: søjlen for det seneste True til og med hver søjle, −1 før det første."""
    k = np.where(maske, np.arange(maske.shape[1]), -1)
    return np.maximum.accumulate(k, axis=1)


def _signal(close: np.ndarray, vwap: np.ndarray) -> np.ndarray:
    """§4b: +1 over VWAP, −1 under, 0 ved lighed eller udefineret VWAP (læsning 7, 9)."""
    with np.errstate(invalid="ignore"):
        return np.where(close > vwap, 1, np.where(close < vwap, -1, 0)).astype(np.int8)


@dataclass
class Lys:
    """Én tidsrammes lys på gitteret: (dage, 390 / tf). Lys k slutter i minut (k+1) × tf."""
    tf: int
    findes: np.ndarray
    close: np.ndarray        # NaN hvor lyset mangler
    vwap: np.ndarray         # VWAP ved lysets sidste 1m-bar
    signal: np.ndarray       # int8: +1, −1 eller 0


@dataclass
class Grundlag:
    """Alt der er fast gennem kørslen. Gitteret har én række pr. dag der indgår og én søjle
    pr. minut efter 08:30 CT."""
    dage: pd.DatetimeIndex   # alle XNYS-dage i perioden
    inkl: np.ndarray         # pladsen i ``dage`` for hver række i gitteret
    udelukket: pd.DataFrame  # dag og grund, §4h
    t0830: np.ndarray        # 08:30 CT i UTC-ns pr. række
    n_min: np.ndarray        # RTH-minutter pr. række: 390 eller 210
    flad: np.ndarray         # fladt-minuttet pr. række: n_min − 5, §4d
    gi: np.ndarray           # serieindeks pr. celle, −1 hvor baren mangler
    o: np.ndarray
    c: np.ndarray
    vwap: np.ndarray         # VWAP ved barens lukning, §4a
    L: np.ndarray            # L_d, §4g
    sidste_i: np.ndarray     # serieindeks for dagens sidste RTH-bar
    s_o: np.ndarray          # hele seriens open, close, kontrakt, tid og gitterminut
    s_c: np.ndarray
    s_iid: np.ndarray
    s_tid: np.ndarray
    s_min: np.ndarray
    lys: dict
    info: dict
    df_1m: pd.DataFrame | None = field(default=None, repr=False)   # til tillæggets §3

    @property
    def n(self) -> int:
        return len(self.inkl)

    @property
    def findes(self) -> np.ndarray:
        return self.gi >= 0

    @property
    def aar(self) -> np.ndarray:
        return np.asarray(self.dage.year[self.inkl])

    @property
    def skala(self) -> np.ndarray:
        return NQ_NIVEAU / self.L


def _lys1(findes, c, vwap) -> Lys:
    close = np.where(findes, c, np.nan)
    v = np.where(findes, vwap, np.nan)
    return Lys(tf=1, findes=findes, close=close, vwap=v, signal=_signal(close, v))


def _lys5(findes, c, vwap) -> Lys:
    """Læsning 8: lysets close og VWAP er dem ved dets sidste 1m-bar der findes."""
    n = findes.shape[0]
    j = np.where(findes.reshape(n, DAG_MIN // 5, 5), np.arange(5), -1).max(axis=2)
    f5 = j >= 0
    g = np.arange(DAG_MIN // 5)[None, :] * 5 + np.maximum(j, 0)
    rr = np.arange(n)[:, None]
    close = np.where(f5, c[rr, g], np.nan)
    v = np.where(f5, vwap[rr, g], np.nan)
    return Lys(tf=5, findes=f5, close=close, vwap=v, signal=_signal(close, v))


def _tjek_5m(df_1m: pd.DataFrame, gi: np.ndarray, t0830: np.ndarray, lys5: Lys) -> None:
    """Læsning 8: gitterets 5m-lys er ``data.resample.aggregate``'s, lys for lys."""
    rth = df_1m.iloc[gi[gi >= 0]]
    a5 = resample.aggregate(rth, 5)
    rad, k = np.nonzero(lys5.findes)
    start = t0830[rad] + k * 5 * MIN_NS
    if (len(a5) != len(rad) or not np.array_equal(k2._ns(a5.index), start)
            or not np.array_equal(a5["close"].to_numpy(dtype=float), lys5.close[rad, k])):
        raise ValueError("5m-lysene fra gitteret og fra data.resample.aggregate er forskellige")


def byg_grundlag(df_1m: pd.DataFrame, dage: pd.DatetimeIndex | None = None,
                 udeluk: bool = True) -> Grundlag:
    """Gitteret, rultjekket, udelukkelsen, VWAP, L_d og lysene. Ingen handel her.
    ``dage`` er XNYS-dagene; standard er dem serien spænder over. ``udeluk=False`` springer
    §4h's huller over og bruges kun til diagnosen i tillæggets §3."""
    if dage is None:
        et = k1._et_dag(df_1m.index[[0, -1]])
        dage = k1.rth_dage(et[0], et[1] + pd.Timedelta(days=1))
    dage = pd.DatetimeIndex(dage)
    plan = sessions._xnys().schedule.loc[dage]
    aabner, lukker = pd.DatetimeIndex(plan["open"]), pd.DatetimeIndex(plan["close"])
    a_ct = aabner.tz_convert(CT)
    if not ((a_ct.hour == 8) & (a_ct.minute == 30)).all():
        raise ValueError("XNYS åbner ikke kl. 08:30 CT på alle dage (læsning 1)")
    t0 = k2._ns(aabner)
    n_min_alle = (k2._ns(lukker) - t0) // MIN_NS
    if ((n_min_alle > DAG_MIN) | (n_min_alle <= PAUSE[0])).any():
        raise ValueError("en RTH-dag er længere end 390 eller kortere end 150 minutter")

    idx = df_1m.index
    tid = k2._ns(idx)
    ri = np.flatnonzero(sessions.rth_mask(idx, 1))
    dp = dage.get_indexer(k1._et_dag(idx[ri]))
    ri, dp = ri[dp >= 0], dp[dp >= 0]
    m = (tid[ri] - t0[dp]) // MIN_NS
    if ((m < 0) | (m >= n_min_alle[dp])).any():
        raise ValueError("en RTH-bar ligger uden for dagens gitter")
    iid = (df_1m["instrument_id"].to_numpy() if "instrument_id" in df_1m.columns
           else np.zeros(len(df_1m), dtype=np.int64))

    # §3 og læsning 6: ingen rul mellem to RTH-barer samme dag.
    samme = dp[1:] == dp[:-1]
    rul = samme & (iid[ri[1:]] != iid[ri[:-1]])
    if rul.any():
        dd = ", ".join(str(d.date()) for d in dage[np.unique(dp[1:][rul])])
        raise ValueError(f"rul inden for RTH ({dd}): koden stopper, §3")

    # §4h og læsning 3-5.
    nd = len(dage)
    n_bar = np.bincount(dp, minlength=nd)
    foerste = np.full(nd, DAG_MIN, dtype=np.int64)
    np.minimum.at(foerste, dp, m)
    hul = np.zeros(nd, dtype=np.int64)
    np.maximum.at(hul, dp[1:][samme], (m[1:] - m[:-1] - 1)[samme])
    grund = np.full(nd, "", dtype=object)
    if udeluk:
        grund[hul > MAKS_HUL] = "hul over 5 min"
        grund[foerste > FOERSTE_SENEST] = "første bar efter 08:35 CT"
    grund[n_bar == 0] = "ingen RTH-barer"
    inkl = np.flatnonzero(grund == "")
    n = len(inkl)
    if n == 0:
        raise ValueError("ingen dage tilbage efter §4h")
    ude = np.flatnonzero(grund != "")
    udelukket = pd.DataFrame({"dag": dage[ude], "grund": grund[ude].astype(str),
                              "maks_hul_min": hul[ude], "foerste_bar_min": foerste[ude]})

    rad = np.full(nd, -1, dtype=np.int64)
    rad[inkl] = np.arange(n)
    r = rad[dp]
    hold = r >= 0
    gi = np.full((n, DAG_MIN), -1, dtype=np.int64)
    gi[r[hold], m[hold]] = ri[hold]
    findes = gi >= 0

    def gitter(kol: str) -> np.ndarray:
        x = df_1m[kol].to_numpy(dtype=float)
        ud = np.full((n, DAG_MIN), np.nan)
        ud[findes] = x[gi[findes]]
        return ud

    o, h, l, c, v = (gitter(k) for k in ("open", "high", "low", "close", "volume"))
    # §4a: Σ(hlc3 × volume) / Σ(volume) fra 08:30 CT til og med baren.
    pv = np.cumsum(np.where(findes, (h + l + c) / 3.0 * v, 0.0), axis=1)
    sv = np.cumsum(np.where(findes, v, 0.0), axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        vwap = np.where(sv > 0, pv / np.where(sv > 0, sv, 1.0), np.nan)
    rr = np.arange(n)
    L = o[rr, np.argmax(findes, axis=1)]
    sidste_i = gi[rr, DAG_MIN - 1 - np.argmax(findes[:, ::-1], axis=1)]
    s_min = np.full(len(df_1m), -1, dtype=np.int64)
    s_min[gi[findes]] = np.nonzero(findes)[1]

    lys = {1: _lys1(findes, c, vwap), 5: _lys5(findes, c, vwap)}
    t0830 = t0[inkl]
    _tjek_5m(df_1m, gi, t0830, lys[5])

    n_min = n_min_alle[inkl]
    alle_rul = np.flatnonzero(iid[1:] != iid[:-1]) + 1
    mangler = n_min - n_bar[inkl]
    info = {"n_1m": len(df_1m), "rth_dage_n": nd, "dage_n": n, "udelukket_n": len(ude),
            **{f"udelukket_{x}_n": int((grund == x).sum())
               for x in ("hul over 5 min", "første bar efter 08:35 CT", "ingen RTH-barer")},
            "kortdage_n": int((n_min < DAG_MIN).sum()),
            "manglende_minutter_n": int(mangler.sum()),
            "dage_med_manglende_minutter_n": int((mangler > 0).sum()),
            "ruller_n": len(alle_rul), "ruller_i_rth_n": 0,
            "rul_tider_ct": ", ".join(sorted(set(
                idx[alle_rul].tz_convert(CT).strftime("%H:%M")))),
            "vwap_udefineret_n": int((findes & np.isnan(vwap)).sum())}
    for tf, ly in lys.items():
        info[f"lys_{tf}m_n"] = int(ly.findes.sum())
        info[f"close_lig_vwap_{tf}m_n"] = int((ly.findes & (ly.signal == 0)
                                               & np.isfinite(ly.vwap)).sum())
    return Grundlag(dage=dage, inkl=inkl, udelukket=udelukket, t0830=t0830, n_min=n_min,
                    flad=n_min - FLAD_FOER_LUK, gi=gi, o=o, c=c, vwap=vwap, L=L,
                    sidste_i=sidste_i, s_o=df_1m["open"].to_numpy(dtype=float),
                    s_c=df_1m["close"].to_numpy(dtype=float), s_iid=iid, s_tid=tid,
                    s_min=s_min, lys=lys, info=info, df_1m=df_1m)


# ---------------------------------------------------------------------------
# §4b-§4e: ønsket position, handelstid og handlerne
# ---------------------------------------------------------------------------

def tilstand(lys: Lys) -> np.ndarray:
    """Den ønskede position over hver 1m-bar, (dage, 390): det seneste signal ≠ 0 fra et
    lys der er lukket ved barens start (læsning 10). 0 før dagens første signal."""
    n = lys.signal.shape[0]
    sig = np.zeros((n, DAG_MIN + 1), dtype=np.int8)
    sig[:, lys.tf::lys.tf] = lys.signal          # lys k virker fra minut (k+1) × tf
    j = _ffill_idx(sig != 0)
    st = np.where(j >= 0, np.take_along_axis(sig, np.maximum(j, 0), axis=1), 0)
    return st[:, :DAG_MIN].astype(np.int8)


def vindue(g: Grundlag, middag: str) -> np.ndarray:
    """Handelstiden pr. 1m-bar: før fladt (§4d), og uden middag ikke 11:00-14:00 CT og på
    kortdage intet efter 11:00 (§4e)."""
    m = np.arange(DAG_MIN)[None, :]
    flad = g.flad[:, None]
    if middag == HELE:
        return m < flad
    return (m < np.minimum(PAUSE[0], flad)) | ((m >= PAUSE[1]) & (m < flad))


def positioner(g: Grundlag, v: tuple) -> np.ndarray:
    """Positionen over hver 1m-bar i gitteret, også de manglende minutter."""
    return (tilstand(g.lys[v[0]]) * vindue(g, v[1])).astype(np.int8)


@dataclass
class Handler:
    """Variantens handler i tidsorden. Ingen pris."""
    rad: np.ndarray          # række i gitteret
    ind_g: np.ndarray        # indgangsminut efter 08:30 CT
    ud_g: np.ndarray         # udgangsminut efter 08:30 CT
    ind_i: np.ndarray        # serieindeks for indgangsbaren
    ud_i: np.ndarray         # serieindeks for udgangsbaren
    retning: np.ndarray      # +1 long, −1 short
    udgang: np.ndarray       # VENDING, PAUSE_UD, FLADT eller EFTER_RTH
    tael: dict

    @property
    def n(self) -> int:
        return len(self.rad)


def handler(g: Grundlag, v: tuple) -> Handler:
    """§4c og læsning 12-13: handlerne er stræk af 1m-barer med samme position ≠ 0.
    Indgang på strækkets første bar, udgang på næste bar i serien."""
    pos = positioner(g, v)
    d, m = np.nonzero(g.findes)                  # i tidsorden: dag, så minut
    P = pos[d, m].astype(np.int64)
    S = g.gi[d, m]
    ny = np.r_[True, d[1:] != d[:-1]]
    sidst = np.r_[d[1:] != d[:-1], True]
    forrige = np.where(ny, 0, np.r_[0, P[:-1]])
    naeste = np.where(sidst, 0, np.r_[P[1:], 0])
    a = np.flatnonzero((P != 0) & (P != forrige))
    b = np.flatnonzero((P != 0) & (P != naeste))
    rad, ind_i, ud_i = d[a], S[a], S[b] + 1
    if len(ud_i) and ud_i.max() >= len(g.s_o):
        raise ValueError("en handel har ingen udgangsbar i serien")
    if (g.s_iid[ind_i] != g.s_iid[ud_i]).any():
        raise ValueError("en handel går over en rul (læsning 6)")
    ud_g = (g.s_tid[ud_i] - g.t0830[rad]) // MIN_NS
    udgang = np.where(sidst[b], EFTER_RTH,
                      np.where(naeste[b] == -P[b], VENDING,
                               np.where(ud_g >= g.flad[rad], FLADT, PAUSE_UD)))
    # Læsning 12: en ændring der skulle være sket i et manglende minut lige før baren.
    senere = (P != forrige) & (m >= 1)
    k = np.flatnonzero(senere)
    senere[k] = ~g.findes[d[k], m[k] - 1] & (pos[d[k], m[k] - 1] != forrige[k])
    tael = {"udfoert_senere_n": int(senere.sum()),
            "udgang_efter_rth_n": int((udgang == EFTER_RTH).sum())}
    return Handler(rad=rad, ind_g=m[a], ud_g=ud_g, ind_i=ind_i, ud_i=ud_i,
                   retning=P[a], udgang=udgang, tael=tael)


# ---------------------------------------------------------------------------
# §4g: resultatet — kun i den rigtige kørsel og tidsmålingen
# ---------------------------------------------------------------------------

def resultat(g: Grundlag, h: Handler, omk: float = OMK_USD) -> dict:
    """Pr. handel: point, skala, brutto og netto ved dagens niveau, nominelt og bp."""
    pt = (g.s_o[h.ud_i] - g.s_o[h.ind_i]) * h.retning
    skala = NQ_NIVEAU / g.L[h.rad]
    brutto = pt * skala * MNQ_USD_PR_POINT
    return {"pt": pt, "skala": skala, "brutto_usd": brutto, "netto_usd": brutto - omk,
            "nominelt_usd": pt * MNQ_USD_PR_POINT - omk, "bp": pt / g.L[h.rad] * 1e4}


def pr_dag(g: Grundlag, h: Handler, x) -> np.ndarray:
    """Summen pr. dag i gitteret; en dag uden handel giver 0 (læsning 14)."""
    return np.bincount(h.rad, weights=np.asarray(x, dtype=float), minlength=g.n)


def handler_pr_dag(g: Grundlag, h: Handler) -> np.ndarray:
    return np.bincount(h.rad, minlength=g.n)


# ---------------------------------------------------------------------------
# §6: N-retning
# ---------------------------------------------------------------------------

@dataclass
class Flyt:
    """Variantens handler set uden retning: dagens plads blandt alle XNYS-dage,
    indgangsminuttet og bevægelsen i long-retning i dollar ved dagens niveau."""
    dag: np.ndarray
    ind_g: np.ndarray
    flyt_usd: np.ndarray

    @property
    def n(self) -> int:
        return len(self.dag)


def flyt(g: Grundlag, h: Handler) -> Flyt:
    pt = g.s_o[h.ud_i] - g.s_o[h.ind_i]
    return Flyt(dag=g.inkl[h.rad], ind_g=h.ind_g,
                flyt_usd=pt * NQ_NIVEAU / g.L[h.rad] * MNQ_USD_PR_POINT)


def nret_bits(n_dage_alle: int, rep: int, tf: int) -> np.ndarray:
    """Læsning 15: én bit pr. (XNYS-dag, indgangsminut) for (gentagelse, tidsramme)."""
    return np.random.default_rng([NRET_SEED, rep, tf]).integers(
        0, 2, size=(n_dage_alle, DAG_MIN), dtype=np.int8)


def nret_retning(bits: np.ndarray, f: Flyt) -> np.ndarray:
    return 2 * bits[f.dag, f.ind_g].astype(np.int64) - 1


def nret_gentagelse(g: Grundlag, flyt_v: dict, rep: int, omk: float = OMK_USD) -> dict:
    """{v: middel dag_netto_usd} for én gentagelse: samme handler, tilfældig retning."""
    ud = {}
    for tf in TIDSRAMMER:
        bits = nret_bits(len(g.dage), rep, tf)
        for mid in MIDDAG:
            f = flyt_v[(tf, mid)]
            d = nret_retning(bits, f)
            ud[(tf, mid)] = (float(d @ f.flyt_usd) - omk * f.n) / g.n
    return ud


# ---------------------------------------------------------------------------
# §7: σ_dag, MDE og styrke — uden udfald
# ---------------------------------------------------------------------------

def i_handelstid(start: np.ndarray, tf: int, flad: np.ndarray, middag: str) -> np.ndarray:
    """Læsning 17: lys der ligger helt i handelstiden, fra første mulige udførelse."""
    s = np.asarray(start)[None, :]
    e = s + tf
    f = np.asarray(flad)[:, None]
    if middag == HELE:
        return (s >= tf) & (e <= f)
    return ((s >= tf) & (e <= np.minimum(PAUSE[0], f))) | ((s >= PAUSE[1]) & (e <= f))


def sigma_dag(g: Grundlag, v: tuple) -> float:
    """§7: ``2 × √(middel_d[(29.138 / L_d)² × Σ_t Δclose_t²])`` over variantens lys i
    handelstiden. Ingen handel indgår."""
    tf, mid = v
    lys = g.lys[tf]
    K = lys.findes.shape[1]
    j = _ffill_idx(lys.findes)
    forrige = np.full_like(j, -1)
    forrige[:, 1:] = j[:, :-1]
    rr = np.arange(g.n)[:, None]
    c_forrige = np.where(forrige >= 0, lys.close[rr, np.maximum(forrige, 0)], np.nan)
    with np.errstate(invalid="ignore"):
        dc = lys.close - c_forrige
    med = lys.findes & np.isfinite(dc) & i_handelstid(np.arange(K) * tf, tf, g.flad, mid)
    s = np.where(med, dc * dc, 0.0).sum(axis=1)
    return 2.0 * math.sqrt(float(np.mean(g.skala ** 2 * s)))


def mde(sigma: float, n_dage: int, z: float = Z_SIDAK4) -> float:
    """§7: ``z × σ_dag / √n_dage``."""
    return z * sigma / math.sqrt(n_dage) if n_dage > 0 else float("inf")


def styrke(sigma: float, n_dage: int, netto: float) -> float:
    """Læsning 18: P(CI-nedre > 0) ved en sand nettoeffekt, normalapproksimation."""
    if n_dage <= 0 or not sigma > 0:
        return float("nan")
    return float(norm.cdf(math.sqrt(n_dage) * netto / sigma - norm.ppf(0.975)))


# ---------------------------------------------------------------------------
# §8 og break-even
# ---------------------------------------------------------------------------

def beslutning(raekker: dict, alfa: float = 0.05) -> dict:
    """§8 med tillæggets §2, mekanisk. ``raekker`` er {variant: {"p_FWE", "ci95_lo"}}.
    Første række der passer, gælder."""
    sig = {v for v, r in raekker.items() if r["p_FWE"] <= alfa}
    ci = {v for v, r in raekker.items() if r["ci95_lo"] > 0}
    begge = [v for v in raekker if v in sig and v in ci]
    if begge:
        frosset = max(begge, key=lambda v: raekker[v]["ci95_lo"])
        return {"raekke": 1, "variant": frosset, "kandidater": begge,
                "tekst": "Varianten fryses"}
    if sig:
        return {"raekke": 2, "variant": None, "kandidater": [v for v in raekker if v in sig],
                "in_sample_fund": [v for v in raekker if v in ci and v not in sig],
                "tekst": "Parkeres som \"VWAP-retningen bærer, men betaler ikke "
                         "omkostningen\""}
    if not sig and ci:
        return {"raekke": 3, "variant": None, "kandidater": [v for v in raekker if v in ci],
                "tekst": "Parkeres: gevinsten kommer ikke fra VWAP-retningen"}
    return {"raekke": 4, "variant": None, "kandidater": [], "tekst": "Kandidat 5 parkeres"}


def breakeven_middel(brutto_usd: np.ndarray) -> float:
    """Læsning 21: omkostningen pr. handel hvor middel netto er 0."""
    b = np.asarray(brutto_usd, dtype=float)
    return float(b.mean()) if len(b) else float("nan")


def breakeven_ci(dag_brutto: np.ndarray, handler_d: np.ndarray, alfa: float = 0.05) -> float:
    """Læsning 21: omkostningen pr. handel hvor t-intervallets nedre grænse for
    ``dag_brutto − c × handler_d`` er 0, ved halvering."""
    b = np.asarray(dag_brutto, dtype=float)
    k = np.asarray(handler_d, dtype=float)
    n = len(b)
    if n < 2 or k.sum() == 0:
        return float("nan")
    tcrit = t_critical(n - 1, alfa)

    def nedre(c: float) -> float:
        x = b - c * k
        return float(x.mean() - tcrit * x.std(ddof=1) / math.sqrt(n))

    hi = float(b.sum() / k.sum())               # her er middel 0, så nedre ≤ 0
    trin = max(1.0, abs(hi))
    lo = hi - trin
    while nedre(lo) <= 0:
        trin *= 2
        lo = hi - trin
        if trin > 1e9:
            return float("nan")
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if nedre(mid) > 0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------------------
# Nøgletal og diagnoser, §9-§10
# ---------------------------------------------------------------------------

def _p(x, q) -> float:
    x = np.asarray(x, dtype=float)
    return float(np.percentile(x, q)) if len(x) else float("nan")


def _ci(x) -> tuple[float, float]:
    x = np.asarray(x, dtype=float)
    return mean_ci_t(x) if len(x) >= 2 else (float("nan"), float("nan"))


def _middel(x) -> float:
    x = np.asarray(x, dtype=float)
    return float(x.mean()) if len(x) else float("nan")


def hit(x) -> tuple[float, float]:
    """Læsning 22: (hit ratio i %, gevinst/tab-forhold)."""
    x = np.asarray(x, dtype=float)
    if len(x) == 0:
        return float("nan"), float("nan")
    v, t = x[x > 0], x[x < 0]
    forhold = float(v.mean() / abs(t.mean())) if len(v) and len(t) else float("nan")
    return 100.0 * len(v) / len(x), forhold


def _intervaller(a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(handel, serieindeks) for alle barer i ``[a_j, b_j)``."""
    laengde = np.asarray(b - a, dtype=np.int64)
    hvem = np.repeat(np.arange(len(a)), laengde)
    start = np.repeat(np.cumsum(laengde) - laengde, laengde)
    return hvem, a[hvem] + (np.arange(int(laengde.sum())) - start)


def halvtimer(g: Grundlag, h: Handler, skala: np.ndarray) -> np.ndarray:
    """Læsning 23: brutto i dollar ved dagens niveau pr. halve time i New York-tid
    (09:30-10:00, …, 15:30-16:00), summeret over alle handler."""
    hvem, i = _intervaller(h.ind_i, h.ud_i)
    inc = h.retning[hvem] * (g.s_o[i + 1] - g.s_o[i]) * skala[hvem] * MNQ_USD_PR_POINT
    return np.bincount(g.s_min[i] // 30, weights=inc, minlength=DAG_MIN // 30)


def stoerste_tab(g: Grundlag, h: Handler, res: dict, omk: float = OMK_USD) -> np.ndarray:
    """Læsning 25: pr. dag ``min(0, løbende P&L)`` på 1m-close, ved dagens niveau."""
    netto = res["netto_usd"]
    kum = pd.Series(netto).groupby(h.rad).cumsum().to_numpy()
    foer = kum - netto
    hvem, i = _intervaller(h.ind_i, h.ud_i)
    urealiseret = (h.retning[hvem] * (g.s_c[i] - g.s_o[h.ind_i[hvem]]) * res["skala"][hvem]
                   * MNQ_USD_PR_POINT)
    loebende = foer[hvem] - omk + urealiseret
    ud = np.zeros(g.n)
    np.minimum.at(ud, h.rad[hvem], loebende)
    np.minimum.at(ud, h.rad, kum)
    return ud


def sidste_5(g: Grundlag, h: Handler, skala: np.ndarray) -> np.ndarray:
    """Læsning 24: pr. dag hvad positionen ved fladt ville have givet til RTH-lukningen."""
    f = np.flatnonzero(h.udgang == FLADT)
    x = (h.retning[f] * (g.s_c[g.sidste_i[h.rad[f]]] - g.s_o[h.ud_i[f]]) * skala[f]
         * MNQ_USD_PR_POINT)
    return np.bincount(h.rad[f], weights=x, minlength=g.n)


def altid_long(g: Grundlag) -> dict:
    """§6 og læsning 27: én handel om dagen, 08:31 CT til fladt."""
    rr = np.arange(g.n)
    m = np.arange(DAG_MIN)[None, :]
    ind = g.findes & (m >= 1)
    ud = g.findes & (m >= g.flad[:, None])
    if not ind.any(axis=1).all():
        raise ValueError("en dag har ingen bar fra 08:31 CT")
    ind_i = g.gi[rr, np.argmax(ind, axis=1)]
    ud_i = np.where(ud.any(axis=1), g.gi[rr, np.argmax(ud, axis=1)], g.sidste_i + 1)
    pt = g.s_o[ud_i] - g.s_o[ind_i]
    netto = pt * g.skala * MNQ_USD_PR_POINT - OMK_USD
    lo, hi = _ci(netto)
    return {"dage_n": g.n, "middel_netto_usd_dag": _middel(netto), "ci95_lo": lo,
            "ci95_hi": hi}


def variant_tal(g: Grundlag, h: Handler) -> dict:
    """Én variants handler og dage: alt i §10's hovedtabel uden nulmodellen, og dagserierne
    til diagnoserne."""
    res = resultat(g, h)
    k = handler_pr_dag(g, h)
    b_dag = pr_dag(g, h, res["brutto_usd"])
    netto_dag = b_dag - OMK_USD * k
    d3169 = b_dag - OMK_DIAGNOSE_USD * k
    nom_dag = pr_dag(g, h, res["nominelt_usd"])
    lo, hi = _ci(netto_dag)
    lo3, hi3 = _ci(d3169)
    lon, hin = _ci(nom_dag)
    hb, fb = hit(res["brutto_usd"])
    hn, fn = hit(res["netto_usd"])
    return {
        "dage_n": g.n, "handler_n": h.n, "handler_pr_dag_p50": _p(k, 50),
        "middel_brutto_usd_dag": _middel(b_dag), "middel_netto_usd_dag": _middel(netto_dag),
        "netto_ci95_lo": lo, "netto_ci95_hi": hi,
        "breakeven_omk_middel": breakeven_middel(res["brutto_usd"]),
        "breakeven_omk_CI": breakeven_ci(b_dag, k),
        "hit_ratio_pct_brutto": hb, "gevinst_tab_forhold": fb,
        "hit_ratio_pct_netto": hn, "gevinst_tab_forhold_netto": fn,
        "netto_usd_dag_nominelt": _middel(nom_dag), "nominelt_ci95_lo": lon,
        "nominelt_ci95_hi": hin,
        "netto_usd_dag_ved_3169": _middel(d3169), "ved_3169_ci95_lo": lo3,
        "ved_3169_ci95_hi": hi3,
        "_res": res, "_k": k, "_brutto_dag": b_dag, "_netto_dag": netto_dag,
        "_netto_dag_3169": d3169, "_nominelt_dag": nom_dag,
    }


def afgoerelse(tal: dict, null: dict, felt: str = "middel_netto_usd_dag",
               lo: str = "netto_ci95_lo") -> dict:
    """§7-§8: Westfall-Young mod N-retning og beslutningsreglen."""
    obs = {v: tal[v][felt] for v in VARIANTER}
    wy = k2.westfall_young(obs, null)
    raekker = {}
    for v in VARIANTER:
        pv = wy["pr_variant"][v]
        raekker[v] = {"middel": obs[v], "ci95_lo": tal[v][lo], "t_v": pv["t"],
                      "p_FWE": pv["p_FWE"], **{f"N_retning_{x}": pv[x]
                                               for x in ("p5", "p50", "p95", "med", "sd")}}
    return {"wy": wy, "raekker": raekker, "beslutning": beslutning(raekker)}


def diagnoser(g: Grundlag, hd: dict, tal: dict) -> dict:
    """§9, pr. variant."""
    ud = {"variant": {}, "halvtime": {}, "aar": []}
    for v in VARIANTER:
        h, t = hd[v], tal[v]
        res, k, netto = t["_res"], t["_k"], t["_netto_dag"]
        sd = float(netto.std(ddof=1)) if g.n >= 2 else float("nan")
        s5 = sidste_5(g, h, res["skala"])
        s5lo, s5hi = _ci(s5)
        tab = stoerste_tab(g, h, res)
        total = float(netto.sum())
        top = int(math.ceil(0.05 * g.n))
        lg = h.retning == 1
        d, dlo, dhi = k2.forskel_ci(res["brutto_usd"][lg], res["brutto_usd"][~lg])
        ud["variant"][v] = {
            "bp_pr_handel": _middel(res["bp"]),
            "bp_pr_dag": _middel(pr_dag(g, h, res["bp"])),
            **{f"handler_pr_dag_p{q}": _p(k, q) for q in (10, 50, 90)},
            **{f"holdetid_min_p{q}": _p(h.ud_g - h.ind_g, q) for q in (10, 50, 90)},
            "sidste_5_usd_dag": _middel(s5), "sidste_5_ci95_lo": s5lo,
            "sidste_5_ci95_hi": s5hi, "sidste_5_dage_n": int((h.udgang == FLADT).sum()),
            **{f"dag_p{q}": _p(netto, q) for q in (1, 5, 50, 95, 99)},
            "dag_vaerste": float(netto.min()), "dag_bedste": float(netto.max()),
            "intradag_tab_p1": _p(tab, 1), "intradag_tab_p5": _p(tab, 5),
            "intradag_tab_vaerste": float(tab.min()),
            "bedste_dag_andel": float(netto.max() / total) if total > 0 else float("nan"),
            "top5pct_dage_andel": (float(np.sort(netto)[::-1][:top].sum() / total)
                                   if total > 0 else float("nan")),
            "long_n": int(lg.sum()), "short_n": int((~lg).sum()),
            "long_brutto_usd": _middel(res["brutto_usd"][lg]),
            "short_brutto_usd": _middel(res["brutto_usd"][~lg]),
            "long_minus_short": d, "long_minus_short_ci95_lo": dlo,
            "long_minus_short_ci95_hi": dhi,
            "sharpe_aar": (float(netto.mean() / sd * math.sqrt(HANDELSDAGE_AAR))
                           if sd > 0 else float("nan")),
        }
        ud["halvtime"][v] = halvtimer(g, h, res["skala"]) / g.n
        aar = g.aar
        for a in AAR_LISTE:
            s = aar == a
            lo, hi = _ci(netto[s])
            ud["aar"].append({"tf": v[0], "middag": v[1], "aar": a, "dage_n": int(s.sum()),
                              "netto_usd_dag": _middel(netto[s]), "ci95_lo": lo,
                              "ci95_hi": hi, "nominelt_usd_dag": _middel(t["_nominelt_dag"][s]),
                              "handler_pr_dag": _middel(k[s]),
                              "L_median": _p(g.L[s], 50)})
    ud["altid_long"] = altid_long(g)
    return ud


# ---------------------------------------------------------------------------
# Den rigtige kørsel
# ---------------------------------------------------------------------------

def forbered(g: Grundlag) -> tuple[dict, dict]:
    """(handler, flyt) pr. variant."""
    hd = {v: handler(g, v) for v in VARIANTER}
    return hd, {v: flyt(g, hd[v]) for v in VARIANTER}


def analyse(g: Grundlag, n_reps: int = NRET_REPS) -> dict:
    """§6-§9 på et grundlag. ``koer`` kalder den efter regressionstjekket."""
    hd, fl = forbered(g)
    tal = {v: variant_tal(g, hd[v]) for v in VARIANTER}
    t0 = time.perf_counter()
    gentagelser = [nret_gentagelse(g, fl, rep) for rep in range(n_reps)]
    nret_s = time.perf_counter() - t0
    null = {v: np.array([r[v] for r in gentagelser]) for v in VARIANTER}
    flyt_omk = {v: (OMK_DIAGNOSE_USD - OMK_USD) * hd[v].n / g.n for v in VARIANTER}
    null_3169 = {v: null[v] - flyt_omk[v] for v in VARIANTER}
    afg = {"hoved": afgoerelse(tal, null),
           "ved_3169": afgoerelse(tal, null_3169, "netto_usd_dag_ved_3169",
                                  "ved_3169_ci95_lo")}
    for v in VARIANTER:
        sig = sigma_dag(g, v)
        tal[v]["sigma_dag"] = sig
        tal[v]["MDE_sidak4"] = mde(sig, g.n)
        tal[v]["MDE_CI"] = mde(sig, g.n, Z_CI)
    return {"g": g, "handler": hd, "tal": tal, "null": null, "afgoerelse": afg,
            "diagnoser": diagnoser(g, hd, tal), "optaelling": optaelling(g, hd),
            "udelukkede": udelukkede_dage(g), "n_reps": n_reps, "nret_s": nret_s}


def udelukkede_dage(g: Grundlag) -> list[dict]:
    """Tillæggets §3: pr. variant og udelukket dag ``dag_netto_usd`` ved dagens niveau og
    nominelt, og største tab inden for dagen. Dagene regnes på deres eget gitter; intet
    herfra når middel, CI, nulmodel eller §8. Dage uden RTH-barer har intet at vise."""
    u = g.udelukket[g.udelukket["grund"] != "ingen RTH-barer"]
    if g.df_1m is None or len(u) == 0:
        return []
    gu = byg_grundlag(g.df_1m, pd.DatetimeIndex(u["dag"]), udeluk=False)
    grund = dict(zip(pd.DatetimeIndex(u["dag"]), u["grund"]))
    ud = []
    for v in VARIANTER:
        h = handler(gu, v)
        res = resultat(gu, h)
        netto = pr_dag(gu, h, res["netto_usd"])
        nom = pr_dag(gu, h, res["nominelt_usd"])
        tab = stoerste_tab(gu, h, res)
        k = handler_pr_dag(gu, h)
        for r in range(gu.n):
            d = gu.dage[gu.inkl[r]]
            ud.append({"tf": v[0], "middag": v[1], "dag": str(d.date()), "grund": grund[d],
                       "handler_n": int(k[r]), "dag_netto_usd": float(netto[r]),
                       "dag_netto_usd_nominelt": float(nom[r]),
                       "intradag_tab_vaerste": float(tab[r])})
    return ud


def koer(n_reps: int = NRET_REPS) -> dict:
    """§6-§10. Regressionstjekket først — afviger det, køres intet."""
    df = mnq()
    reg = regressionstjek(df)
    if not reg["ok"]:
        raise RuntimeError(f"regressionstjekket afveg, kørslen sker ikke: {reg}")
    g = byg_grundlag(df, k1.rth_dage(trinA.MNQ_START, trinA.TRIN_A_SLUT))
    res = analyse(g, n_reps)
    res["regression"] = reg
    return res


# ---------------------------------------------------------------------------
# §11.4: optællingen uden udfald
# ---------------------------------------------------------------------------

def optaelling(g: Grundlag, hd: dict | None = None) -> dict:
    """§11.4: dage, handler, holdetid, omkostning, L_d, σ_dag, MDE, betingelsen og styrken.
    Ingen pris i en handel indgår: ingen P&L, ingen hit ratio, ingen andel long eller
    short og intet udfald."""
    hd = {v: handler(g, v) for v in VARIANTER} if hd is None else hd
    aar = g.aar
    omk_bp_dag = OMK_USD / (2.0 * g.L) * 1e4
    varianter, aar_rows = [], []
    for v in VARIANTER:
        h = hd[v]
        k = handler_pr_dag(g, h)
        sig = sigma_dag(g, v)
        omk_dag = h.n * OMK_USD / g.n
        varianter.append({
            "tf": v[0], "middag": v[1], "dage_n": g.n, "handler_n": h.n,
            "handler_pr_dag_middel": _middel(k),
            **{f"handler_pr_dag_p{q}": _p(k, q) for q in (10, 50, 90)},
            "dage_uden_handel_n": int((k == 0).sum()),
            **{f"holdetid_min_p{q}": _p(h.ud_g - h.ind_g, q) for q in (10, 50, 90)},
            "omk_usd_dag": omk_dag,
            **{f"udgang_{navn}_n": int((h.udgang == kode).sum())
               for kode, navn in UDGANGE.items()},
            **h.tael,
            "sigma_dag": sig, "MDE_sidak4": mde(sig, g.n), "MDE_CI": mde(sig, g.n, Z_CI),
            "betingelse_ok": bool(mde(sig, g.n) <= MDE_GRAENSE_USD),
            "netto_ved_82_brutto": ARTIKEL_BRUTTO_USD - omk_dag,
            "styrke_netto_ved_82": styrke(sig, g.n, ARTIKEL_BRUTTO_USD - omk_dag),
        })
        for a in AAR_LISTE:
            s = aar == a
            aar_rows.append({"tf": v[0], "middag": v[1], "aar": a, "dage_n": int(s.sum()),
                             "handler_pr_dag_middel": _middel(k[s]),
                             "omk_usd_dag": _middel(k[s] * OMK_USD),
                             "omk_bp_dag": _middel(k[s] * omk_bp_dag[s])})
    L_aar = []
    for a in AAR_LISTE:
        s = aar == a
        med = _p(g.L[s], 50)
        L_aar.append({"aar": a, "dage_n": int(s.sum()), "L_median": med,
                      "omk_bp_rundtur": OMK_USD / (2.0 * med) * 1e4 if s.any()
                      else float("nan")})
    return {"serie": dict(g.info), "udelukket": g.udelukket.copy(), "varianter": varianter,
            "aar": aar_rows, "L_aar": L_aar}


# ---------------------------------------------------------------------------
# Formatering
# ---------------------------------------------------------------------------

def _vnavn(v) -> str:
    return f"{v[0]}m · {v[1]}"


def _rel(sti: Path) -> str:
    return Path(sti).resolve().relative_to(ROOT.resolve()).as_posix()


def _tre(r: dict, navn: str, nd: int = 1) -> str:
    return "/".join(k2._t(r[f"{navn}_p{q}"], nd) for q in (10, 50, 90))


def _usd(x, nd: int = 2) -> str:
    return k2._t(x, nd)


def _ci_txt(lo, hi, nd: int = 2) -> str:
    return f"[{k2._t(lo, nd)}; {k2._t(hi, nd)}]"


def _hhmm_ny(k: int) -> str:
    m = 9 * 60 + 30 + 30 * k
    return f"{m // 60:02d}:{m % 60:02d}-{(m + 30) // 60:02d}:{(m + 30) % 60:02d}"


def optaelling_md(o: dict, meta: dict, kun_tabeller: bool = False) -> str:
    _t = k2._t
    s = o["serie"]
    hoved = [
        "# B4 kandidat 5 — optælling uden udfald (§11.4)\n",
        f"Kørt {meta['koert_utc']} UTC fra commit `{meta['head'][:7]}`, "
        f"{k4._arbejdskopi(COMMITTEDE)}. **Ingen P&L, ingen hit ratio, ingen andel long eller "
        f"short og intet udfald er regnet.** Handlerne er bestemt af signalerne og "
        f"handelstiden alene; ingen pris i en handel indgår. σ_dag er markedets egen "
        f"svingning i handelstiden (§7).\n",
    ]
    dele = [] if kun_tabeller else hoved
    dele += [
        "## Serie og dage, §3 og §4h\n",
        f"MNQ.v.0 1m gennem `data.holdout.load_in_sample`, {trinA.MNQ_START.date()} → "
        f"2023-12-31: {_t(s['n_1m'])} 1m-barer. {_t(s['rth_dage_n'])} XNYS-dage, heraf "
        f"{_t(s['kortdage_n'])} kortdage blandt dem der indgår.\n",
        "| emne | antal |", "|---|---|",
        f"| XNYS-dage | {_t(s['rth_dage_n'])} |",
        f"| udelukket, hul over 5 min | {_t(s['udelukket_hul over 5 min_n'])} |",
        f"| udelukket, første bar efter 08:35 CT | "
        f"{_t(s['udelukket_første bar efter 08:35 CT_n'])} |",
        f"| udelukket, ingen RTH-barer | {_t(s['udelukket_ingen RTH-barer_n'])} |",
        f"| **dage der indgår (n_dage)** | **{_t(s['dage_n'])}** |",
        f"| manglende RTH-minutter på dagene der indgår | {_t(s['manglende_minutter_n'])} "
        f"(på {_t(s['dage_med_manglende_minutter_n'])} dage) |",
        f"| ruller i serien | {_t(s['ruller_n'])}, kl. {s['rul_tider_ct']} CT |",
        f"| ruller inden for RTH | {_t(s['ruller_i_rth_n'])} |",
        f"| RTH-barer uden VWAP | {_t(s['vwap_udefineret_n'])} |",
        f"| 1m-lys / heraf close = VWAP | {_t(s['lys_1m_n'])} / {_t(s['close_lig_vwap_1m_n'])} |",
        f"| 5m-lys / heraf close = VWAP | {_t(s['lys_5m_n'])} / {_t(s['close_lig_vwap_5m_n'])} |",
        "",
    ]
    if len(o["udelukket"]):
        dele += ["Udelukkede dage:\n", "| dag | grund | største hul, min | første bar, min "
                 "efter 08:30 |", "|---|---|---|---|"]
        for _, r in o["udelukket"].iterrows():
            dele.append(f"| {pd.Timestamp(r['dag']).date()} | {r['grund']} | "
                        f"{_t(int(r['maks_hul_min']))} | {_t(int(r['foerste_bar_min']))} |")
        dele.append("")
    dele += [
        "## Pr. variant — handler og holdetid, §11.4\n",
        "Handler pr. dag er over alle n_dage, også dage uden handel. Holdetid i minutter fra "
        "indgangsbar til udgangsbar. `udført senere` er ændringer der faldt i et manglende "
        "minut og blev udført på næste bar (§4c).\n",
        "| variant | handler_n | handler pr. dag p10/p50/p90 | middel | dage uden handel | "
        "holdetid p10/p50/p90 | omk. $/dag | udgang vending/pause/fladt/efter RTH | "
        "udført senere |", "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in o["varianter"]:
        dele.append(
            f"| {_vnavn((r['tf'], r['middag']))} | {_t(r['handler_n'])} | "
            f"{_tre(r, 'handler_pr_dag', 0)} | {_t(r['handler_pr_dag_middel'], 2)} | "
            f"{_t(r['dage_uden_handel_n'])} | {_tre(r, 'holdetid_min', 0)} | "
            f"{_usd(r['omk_usd_dag'])} | {_t(r['udgang_vending_n'])}/{_t(r['udgang_pause_n'])}/"
            f"{_t(r['udgang_fladt_n'])}/{_t(r['udgang_efter_rth_n'])} | "
            f"{_t(r['udfoert_senere_n'])} |")
    dele += [
        "", "## Pr. variant — σ_dag, MDE og styrke, §7\n",
        "σ_dag = 2 × √(middel_d[(29.138 / L_d)² × Σ Δclose²]) over variantens lys i "
        "handelstiden. MDE_sidak4 = 3,0756 × σ_dag / √n_dage, MDE_CI = 2,8016 × σ_dag / "
        "√n_dage. Styrken er for CI-nedre > 0, hvis bruttogevinsten er $82 pr. dag og "
        "omkostningen variantens egen.\n",
        "| variant | n_dage | σ_dag | MDE_sidak4 | MDE_CI | MDE_sidak4 ≤ $82 | omk. $/dag | "
        "netto ved $82 brutto | styrke |", "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in o["varianter"]:
        dele.append(
            f"| {_vnavn((r['tf'], r['middag']))} | {_t(r['dage_n'])} | {_usd(r['sigma_dag'], 1)} | "
            f"**{_usd(r['MDE_sidak4'], 1)}** | {_usd(r['MDE_CI'], 1)} | "
            f"{'OK' if r['betingelse_ok'] else '**OVER**'} | {_usd(r['omk_usd_dag'])} | "
            f"{_usd(r['netto_ved_82_brutto'])} | {_t(100 * r['styrke_netto_ved_82'], 1)}% |")
    dele += ["", "## L_d og omkostningen pr. år, §4g\n",
             "Omkostningen i bp er $2,627 / (2 × L) × 10⁴ pr. round trip ved årets median af "
             f"L_d. Ved dagens niveau (NQ {_t(NQ_NIVEAU, 0)}) er den "
             f"{_t(OMK_USD / (2 * NQ_NIVEAU) * 1e4, 2)} bp.\n",
             "| år | dage | median L_d | omk. bp pr. round trip |", "|---|---|---|---|"]
    for r in o["L_aar"]:
        dele.append(f"| {r['aar']} | {_t(r['dage_n'])} | {_t(r['L_median'], 2)} | "
                    f"{_t(r['omk_bp_rundtur'], 2)} |")
    dele += ["", "Pr. variant og år: handler pr. dag (middel) og omkostning pr. dag i bp af "
             "positionen, middel over dagene.\n",
             "| variant | " + " | ".join(str(a) for a in AAR_LISTE) + " |",
             "|" + "---|" * (1 + len(AAR_LISTE))]
    for v in VARIANTER:
        celler = [f"{_t(r['handler_pr_dag_middel'], 1)} / {_t(r['omk_bp_dag'], 1)} bp"
                  for r in o["aar"] if (r["tf"], r["middag"]) == v]
        dele.append(f"| {_vnavn(v)} | " + " | ".join(celler) + " |")
    ok = all(r["betingelse_ok"] for r in o["varianter"])
    dele += ["", "## Betingelsen i §7\n",
             ("Alle 4 varianter har MDE_sidak4 ≤ $82.\n" if ok else
              "**Mindst én variant har MDE_sidak4 over $82: "
              + ", ".join(_vnavn((r["tf"], r["middag"])) for r in o["varianter"]
                          if not r["betingelse_ok"])
              + ". Code stopper, og ejeren beslutter (§7).**\n")]
    return "\n".join(dele)


def optaelling_csv(o: dict) -> pd.DataFrame:
    rows = [{"tabel": "variant", **r} for r in o["varianter"]]
    rows += [{"tabel": "aar", **r} for r in o["aar"]]
    rows += [{"tabel": "L_aar", **r} for r in o["L_aar"]]
    rows += [{"tabel": "udelukket", "dag": str(pd.Timestamp(r["dag"]).date()),
              "grund": r["grund"]} for _, r in o["udelukket"].iterrows()]
    rows.append({"tabel": "serie", **o["serie"]})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Rapporten, §10
# ---------------------------------------------------------------------------

def hovedtabel_md(res: dict) -> str:
    _t = k2._t
    afg = res["afgoerelse"]["hoved"]["raekker"]
    linjer = ["| variant | dage_n | handler_n | handler_pr_dag_p50 | middel_brutto_usd_dag | "
              "middel_netto_usd_dag | CI95_netto | N_retning_p5/p50/p95 | t_v | p_FWE | "
              "breakeven_omk_middel | breakeven_omk_CI | hit_ratio_pct_brutto | "
              "gevinst_tab_forhold | netto_usd_dag_nominelt | netto_usd_dag_ved_3169 | "
              "MDE_sidak4 | MDE_CI |", "|" + "---|" * 18]
    for v in VARIANTER:
        t, a = res["tal"][v], afg[v]
        linjer.append(
            f"| {_vnavn(v)} | {_t(t['dage_n'])} | {_t(t['handler_n'])} | "
            f"{_t(t['handler_pr_dag_p50'], 0)} | {_usd(t['middel_brutto_usd_dag'])} | "
            f"{_usd(t['middel_netto_usd_dag'])} | {_ci_txt(t['netto_ci95_lo'], t['netto_ci95_hi'])} | "
            f"{_usd(a['N_retning_p5'])}/{_usd(a['N_retning_p50'])}/{_usd(a['N_retning_p95'])} | "
            f"{_t(a['t_v'], 2)} | {_t(a['p_FWE'], 4)} | {_t(t['breakeven_omk_middel'], 3)} | "
            f"{_t(t['breakeven_omk_CI'], 3)} | {_t(t['hit_ratio_pct_brutto'], 1)} | "
            f"{_t(t['gevinst_tab_forhold'], 2)} | {_usd(t['netto_usd_dag_nominelt'])} | "
            f"{_usd(t['netto_usd_dag_ved_3169'])} | {_usd(t['MDE_sidak4'], 1)} | "
            f"{_usd(t['MDE_CI'], 1)} |")
    return "\n".join(linjer) + "\n"


def _beslutning_md(navn: str, afg: dict) -> str:
    b = afg["beslutning"]
    v = f" Frosset variant: **{_vnavn(b['variant'])}**." if b["variant"] is not None else ""
    if b.get("in_sample_fund"):
        v += (" In-sample-fund (CI-nedre > 0 uden p_FWE ≤ 0,05, tillæggets §2): "
              + ", ".join(_vnavn(x) for x in b["in_sample_fund"]) + ".")
    return f"**{navn}: række {b['raekke']}: {b['tekst']}.**{v}\n"


def skriv_md(res: dict, meta: dict) -> str:
    _t = k2._t
    g, tal, d = res["g"], res["tal"], res["diagnoser"]
    dv = d["variant"]
    afg = res["afgoerelse"]

    def tabel(hoved: list[str], celler) -> str:
        linjer = ["| variant | " + " | ".join(hoved) + " |", "|" + "---|" * (1 + len(hoved))]
        linjer += [f"| {_vnavn(v)} | " + " | ".join(celler(v)) + " |" for v in VARIANTER]
        return "\n".join(linjer) + "\n"

    al = d["altid_long"]
    dele = [
        "# B4 kandidat 5 — VWAP-trend efter Zarattini og Aziz (2023)\n",
        f"Kørt {meta['koert_utc']} UTC fra commit `{meta['head'][:7]}`. Præregistrering "
        f"`{_rel(PREREG)}` (commit `{meta['commits'][_rel(PREREG)][:7]}`). Kode "
        f"`{_rel(Path(__file__))}` (commit `{meta['commits'][_rel(Path(__file__))][:7]}`).\n",
        f"Serie: MNQ.v.0 1m, {trinA.MNQ_START.date()} → 2023-12-31, {_t(g.n)} dage. 4 "
        f"varianter. N-retning: {res['n_reps']} gentagelser. Netto-dollar pr. dag pr. MNQ ved "
        f"NQ {_t(NQ_NIVEAU, 0)}, omkostning ${_t(OMK_USD, 3)} pr. round trip.\n",
        "**Regressionstjek: OK.**\n",
        "## Hovedtabel, §10\n", hovedtabel_md(res),
        "## Afgørelsen, §8, mekanisk\n",
        _beslutning_md("Ved $2,627", afg["hoved"]),
        _beslutning_md("Ved $3,169 (diagnose, ændrer ikke rækken)", afg["ved_3169"]),
        "## Omkostningen, §9\n",
        tabel(["break-even, middel = 0", "break-even, CI-nedre = 0", "netto ved $3,169 [CI95]",
               "nominelt [CI95]"],
              lambda v: [_t(tal[v]["breakeven_omk_middel"], 3),
                         _t(tal[v]["breakeven_omk_CI"], 3),
                         f"{_usd(tal[v]['netto_usd_dag_ved_3169'])} "
                         f"{_ci_txt(tal[v]['ved_3169_ci95_lo'], tal[v]['ved_3169_ci95_hi'])}",
                         f"{_usd(tal[v]['netto_usd_dag_nominelt'])} "
                         f"{_ci_txt(tal[v]['nominelt_ci95_lo'], tal[v]['nominelt_ci95_hi'])}"]),
        "## Brutto i bp, handler og holdetid, §9\n",
        "Artiklen: cirka 0,93 bp pr. handel og 14,1 bp pr. dag, cirka 15 handler om dagen.\n",
        tabel(["bp pr. handel", "bp pr. dag", "handler pr. dag p10/p50/p90",
               "holdetid min p10/p50/p90"],
              lambda v: [_t(dv[v]["bp_pr_handel"], 3), _t(dv[v]["bp_pr_dag"], 2),
                         _tre(dv[v], "handler_pr_dag", 0), _tre(dv[v], "holdetid_min", 0)]),
        "## Hit ratio og gevinst/tab-forhold, §9\n",
        "Artiklen: 17% og 5,67.\n",
        tabel(["hit ratio brutto %", "gevinst/tab brutto", "hit ratio netto %",
               "gevinst/tab netto"],
              lambda v: [_t(tal[v]["hit_ratio_pct_brutto"], 1),
                         _t(tal[v]["gevinst_tab_forhold"], 2),
                         _t(tal[v]["hit_ratio_pct_netto"], 1),
                         _t(tal[v]["gevinst_tab_forhold_netto"], 2)]),
        "## Brutto pr. halve time, New York-tid, $ pr. dag, §9\n",
        "Mark-to-market minut for minut. Artiklens figur 7: gevinst kl. 9:30-12 og 15-16.\n",
        "| halve time NY | " + " | ".join(_vnavn(v) for v in VARIANTER) + " |\n|" +
        "---|" * (1 + len(VARIANTER)) + "\n" +
        "".join(f"| {_hhmm_ny(k)} | " + " | ".join(_usd(d["halvtime"][v][k])
                                                   for v in VARIANTER) + " |\n"
                for k in range(DAG_MIN // 30)),
        "## De sidste 5 minutter, §9\n",
        tabel(["dage med position ved fladt", "brutto $/dag 14:55-15:00 CT [CI95]"],
              lambda v: [_t(dv[v]["sidste_5_dage_n"]),
                         f"{_usd(dv[v]['sidste_5_usd_dag'])} "
                         f"{_ci_txt(dv[v]['sidste_5_ci95_lo'], dv[v]['sidste_5_ci95_hi'])}"]),
        "## Dagsfordelingen ved dagens niveau, $ netto, §9\n",
        tabel(["p1", "p5", "p50", "p95", "p99", "værste", "bedste"],
              lambda v: [_usd(dv[v][f"dag_p{q}"], 1) for q in (1, 5, 50, 95, 99)]
              + [_usd(dv[v]["dag_vaerste"], 1), _usd(dv[v]["dag_bedste"], 1)]),
        "## Største tab inden for dagen, $ netto, mark-to-market på 1m-close, §9\n",
        tabel(["p1", "p5", "værste"],
              lambda v: [_usd(dv[v]["intradag_tab_p1"], 1), _usd(dv[v]["intradag_tab_p5"], 1),
                         _usd(dv[v]["intradag_tab_vaerste"], 1)]),
        "## Konsistens, §9\n",
        tabel(["bedste dags andel af samlet netto", "de 5% bedste dages andel"],
              lambda v: [_t(dv[v]["bedste_dag_andel"], 3), _t(dv[v]["top5pct_dage_andel"], 3)]),
        "## Long mod short, brutto $ pr. handel, §9\n",
        tabel(["long_n", "short_n", "long", "short", "long − short [Welch-CI95]"],
              lambda v: [_t(dv[v]["long_n"]), _t(dv[v]["short_n"]),
                         _usd(dv[v]["long_brutto_usd"]), _usd(dv[v]["short_brutto_usd"]),
                         f"{_usd(dv[v]['long_minus_short'])} "
                         f"{_ci_txt(dv[v]['long_minus_short_ci95_lo'], dv[v]['long_minus_short_ci95_hi'])}"]),
        "## De udelukkede dage, tillæggets §3 (diagnose, ændrer intet)\n",
        "Circuit breaker-dagene i marts 2020, udelukket efter §4h. Regnet med samme motor; "
        "positionen holdes gennem stoppet og udføres ved første bar efter det. Ikke med i "
        "middel, CI, nulmodel eller §8.\n",
        "| variant | dag | handler_n | netto $ ved dagens niveau | nominelt $ | største tab "
        "inden for dagen $ |\n|---|---|---|---|---|---|\n" +
        "".join(f"| {_vnavn((r['tf'], r['middag']))} | {r['dag']} | {_t(r['handler_n'])} | "
                f"{_usd(r['dag_netto_usd'])} | {_usd(r['dag_netto_usd_nominelt'])} | "
                f"{_usd(r['intradag_tab_vaerste'])} |\n" for r in res["udelukkede"]),
        "## Altid-long, §6 (forklarer, ændrer intet)\n",
        f"Køb 08:31 CT, sælg ved fladt, {_t(al['dage_n'])} dage: middel netto "
        f"{_usd(al['middel_netto_usd_dag'])} $/dag {_ci_txt(al['ci95_lo'], al['ci95_hi'])}.\n",
        "## Årlig Sharpe af den daglige netto, §9\n",
        "Artiklen: 2,1.\n",
        tabel(["Sharpe"], lambda v: [_t(dv[v]["sharpe_aar"], 2)]),
        "## Pr. år, §9\n",
        "| variant | år | dage | netto $/dag [CI95] | nominelt $/dag | handler pr. dag | median "
        "L_d |\n|---|---|---|---|---|---|---|\n" +
        "".join(f"| {_vnavn((r['tf'], r['middag']))} | {r['aar']} | {_t(r['dage_n'])} | "
                f"{_usd(r['netto_usd_dag'])} {_ci_txt(r['ci95_lo'], r['ci95_hi'])} | "
                f"{_usd(r['nominelt_usd_dag'])} | {_t(r['handler_pr_dag'], 1)} | "
                f"{_t(r['L_median'], 2)} |\n" for r in d["aar"]),
        "## Optælling og datakvalitet\n",
        optaelling_md(res["optaelling"], meta, kun_tabeller=True),
        "## Efter kørslen, §13\n",
        "Stop. Ingen ændring af definitioner, ingen nye varianter og ingen forslag.\n",
        f"Alle tal: `{_rel(OUT / 'b4_k5_vwap_trend.csv')}`.\n",
    ]
    return "\n".join(dele)


def lang_tabel(res: dict) -> pd.DataFrame:
    rows = []
    for navn, afg in res["afgoerelse"].items():
        for v in VARIANTER:
            t = {k: x for k, x in res["tal"][v].items() if not k.startswith("_")}
            rows.append({"tabel": "hoved", "afgoerelse": navn, "tf": v[0], "middag": v[1],
                         "raekke_8": afg["beslutning"]["raekke"], **t, **afg["raekker"][v]})
    for v in VARIANTER:
        rows.append({"tabel": "diagnose", "tf": v[0], "middag": v[1],
                     **res["diagnoser"]["variant"][v]})
        for kk, x in enumerate(res["diagnoser"]["halvtime"][v]):
            rows.append({"tabel": "halvtime", "tf": v[0], "middag": v[1],
                         "halvtime_ny": _hhmm_ny(kk), "brutto_usd_dag": x})
    rows += [{"tabel": "aar", **r} for r in res["diagnoser"]["aar"]]
    rows.append({"tabel": "altid_long", **res["diagnoser"]["altid_long"]})
    rows += [{"tabel": "udelukket_dag", **r} for r in res["udelukkede"]]
    optael = optaelling_csv(res["optaelling"]).rename(columns={"tabel": "optaelling"})
    optael.insert(0, "tabel", "optaelling")
    return pd.concat([pd.DataFrame(rows), optael], ignore_index=True)


# ---------------------------------------------------------------------------
# §11.3: regressionstjek
# ---------------------------------------------------------------------------

def regression_k4(df: pd.DataFrame) -> dict:
    """Læsning 31: kandidat 4's k = 1,5 · 1/dag gengiver 1.104 handler og −0,0920 R."""
    g = k4.byg_grundlag(df, k1.rth_dage(trinA.MNQ_START, trinA.TRIN_A_SLUT))
    f = k4.dagsforloeb(g, k4.TILBAGE, k4.setups(g, 1.5), 1, k4.exit_fuld(g))
    h = k4.handelstabel(g, k4.TILBAGE, f)
    m = float(h["R_netto"].mean())
    return {"handler_n": len(h), "middel_R_netto": m,
            "ok": len(h) == REGRESSION_K4_HANDLER_N
            and round(m, 4) == REGRESSION_K4_MIDDEL_R_NETTO}


def regressionstjek(df: pd.DataFrame | None = None) -> dict:
    """§11.3: kandidat 1's tre tjek, ``simuler_handel``'s 1.226 handler og −0,0115 R,
    kandidat 2's hovedvariant (611 og −0,1430), kandidat 3's k = 1,0 (1.168 og −0,0712) og
    kandidat 4's k = 1,5 · 1/dag (1.104 og −0,0920)."""
    df = mnq() if df is None else df
    t0 = time.perf_counter()
    ud = k4.regressionstjek(df)
    ud["k4_k15_1"] = regression_k4(df)
    ud["sekunder"] = time.perf_counter() - t0
    ud["ok"] = bool(ud["ok"] and ud["k4_k15_1"]["ok"])
    return ud


# ---------------------------------------------------------------------------
# §11.5: tidsmålingen — uden P&L
# ---------------------------------------------------------------------------

def tidsmaaling(n_reps: int = 5) -> dict:
    """§11.5: ét gennemløb og ``n_reps`` N-retning-gentagelser, fremskrevet til R = 500.
    Returnerer kun tider og antal. P&L regnes inde i gennemløbet og gentagelserne, fordi
    det er arbejdet der måles, men det forlader ikke funktionen."""
    t0 = time.perf_counter()
    df = mnq()
    load_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    g = byg_grundlag(df, k1.rth_dage(trinA.MNQ_START, trinA.TRIN_A_SLUT))
    grundlag_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    hd, fl = forbered(g)
    handler_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    tal = {v: variant_tal(g, hd[v]) for v in VARIANTER}
    diagnoser(g, hd, tal)
    for v in VARIANTER:
        sigma_dag(g, v)
    gennemloeb_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    for rep in range(n_reps):
        nret_gentagelse(g, fl, rep)
    nret_s = time.perf_counter() - t0
    pr_rep = nret_s / n_reps if n_reps else 0.0
    t0 = time.perf_counter()
    k2.westfall_young({v: 0.0 for v in VARIANTER},       # tallene er ligegyldige her
                      {v: np.arange(NRET_REPS, dtype=float) for v in VARIANTER})
    wy_s = time.perf_counter() - t0
    forventet = load_s + grundlag_s + handler_s + gennemloeb_s + pr_rep * NRET_REPS + wy_s
    return {"load_s": load_s, "grundlag_s": grundlag_s, "handler_s": handler_s,
            "gennemloeb_s": gennemloeb_s, "n_reps": n_reps, "nret_s": nret_s,
            "pr_rep_s": pr_rep, "wy_s": wy_s, "forventet_s": forventet,
            "handler_n": {_vnavn(v): hd[v].n for v in VARIANTER}}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--regressionstjek", action="store_true",
                     help="§11.3: kandidat 1's tre tjek, simuler_handel, kandidat 2, 3 og 4")
    grp.add_argument("--optaelling", action="store_true",
                     help="§11.4: optælling uden udfald. Skriver b4_k5_vwap_trend_optaelling")
    grp.add_argument("--tidsmaaling", action="store_true",
                     help="§11.5: ét gennemløb og 5 N-retning-gentagelser, uden P&L")
    grp.add_argument("--koer", action="store_true",
                     help="§6-§10: den rigtige kørsel. Kræver ejerens godkendelse")
    ap.add_argument("--reps", type=int, default=NRET_REPS)
    ap.add_argument("--maalte-reps", type=int, default=5)
    args = ap.parse_args(argv)
    meta = {"koert_utc": pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M"),
            "head": k4._git("rev-parse", "HEAD").stdout.strip()}

    if args.regressionstjek:
        r = regressionstjek()
        k1r, mo, k2r, k3r, k4r = (r["k1"], r["motor"], r["k2_hovedvariant"], r["k3_k1"],
                                  r["k4_k15_1"])
        print(f"Kandidat 1, 1. b4_k1_optaelling_v2.csv byte for byte: "
              f"{'OK' if k1r['csv_byte_for_byte'] else 'AFVIGER'}")
        print(f"Kandidat 1, 2. spor A, score >= 0: handler_n {k1r['motor_handler_n']}, "
              f"middel_R_netto {k1r['motor_middel_R_netto']:.4f}: "
              f"{'OK' if k1r['motor_ok'] else 'AFVIGER'}")
        print(f"Kandidat 1, 3. scorefordelingen ({k1r['score_rader_n']} raekker): "
              f"{'OK' if k1r['score_ok'] else 'AFVIGER'}")
        for navn in ("standard", "eksplicit_2R"):
            x = mo[navn]
            print(f"simuler_handel, {navn}: handler_n {x['handler_n']} (ventet "
                  f"{k2.REGRESSION_HANDLER_N}), middel_R_netto {x['middel_R_netto']:.4f} "
                  f"(ventet {k2.REGRESSION_MIDDEL_R_NETTO}): {'OK' if x['ok'] else 'AFVIGER'}")
        print(f"Kandidat 2, daily · 5 lys · 1R: handler_n {k2r['handler_n']}, middel_R_netto "
              f"{k2r['middel_R_netto']:.4f}: {'OK' if k2r['ok'] else 'AFVIGER'}")
        print(f"Kandidat 3, k = 1,0: handler_n {k3r['handler_n']} (ventet "
              f"{k4.REGRESSION_K3_HANDLER_N}), middel_R_netto {k3r['middel_R_netto']:.4f} "
              f"(ventet {k4.REGRESSION_K3_MIDDEL_R_NETTO}): {'OK' if k3r['ok'] else 'AFVIGER'}")
        print(f"Kandidat 4, k = 1,5 · 1/dag: handler_n {k4r['handler_n']} (ventet "
              f"{REGRESSION_K4_HANDLER_N}), middel_R_netto {k4r['middel_R_netto']:.4f} "
              f"(ventet {REGRESSION_K4_MIDDEL_R_NETTO:.4f}): {'OK' if k4r['ok'] else 'AFVIGER'}")
        print(f"Tid: {r['sekunder']:.0f} s")
        if not r["ok"]:
            sys.exit(1)
        return

    if args.optaelling:
        g = byg_grundlag(mnq(), k1.rth_dage(trinA.MNQ_START, trinA.TRIN_A_SLUT))
        o = optaelling(g)
        md = optaelling_md(o, meta)
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "b4_k5_vwap_trend_optaelling.md").write_text(md, encoding="utf-8")
        optaelling_csv(o).to_csv(OUT / "b4_k5_vwap_trend_optaelling.csv", index=False)
        print(md)
        return

    if args.tidsmaaling:
        t = tidsmaaling(args.maalte_reps)
        print(f"Indlæsning {t['load_s']:.1f} s, grundlag {t['grundlag_s']:.1f} s, handler for "
              f"4 varianter {t['handler_s']:.2f} s, P&L, nøgletal, diagnoser og σ_dag "
              f"{t['gennemloeb_s']:.2f} s")
        print(f"{t['n_reps']} N-retning-gentagelser: {t['nret_s']:.2f} s, "
              f"{t['pr_rep_s'] * 1000:.0f} ms pr. gentagelse. Westfall-Young {t['wy_s']:.3f} s")
        print(f"Fremskrevet til R = {NRET_REPS}: {t['forventet_s']:.0f} s "
              f"({t['forventet_s'] / 60:.1f} min), regressionstjekket ikke medregnet")
        print(f"handler_n: {t['handler_n']}")
        return

    commits = k1.committede(COMMITTEDE)
    res = koer(n_reps=args.reps)
    meta["commits"] = commits
    md = skriv_md(res, meta)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "b4_k5_vwap_trend.md").write_text(md, encoding="utf-8")
    lang_tabel(res).to_csv(OUT / "b4_k5_vwap_trend.csv", index=False)
    print(md)


if __name__ == "__main__":
    main()
