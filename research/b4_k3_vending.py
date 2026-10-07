"""B4 kandidat 3 — vending efter åbningen: volatilitetslys i modsat retning, MNQ 1m.

Præregistreret i ``research/prereg/b4_k3_vending.md``. Kilden er
``research/kilder/bktraders_nasdaq_routine_noter.md``. Motoren er kandidat 1's rettede
``research/b4_k1_trinA.simuler_handel``, kaldt med ``be_r=None`` og ``maal_r=1.5``. Serien,
Westfall-Young, Welch-intervallet og §10's nøgletal er ``research/b4_k2_nowick.py``'s,
brugt uændret. Ingen af kandidat 1's og 2's moduler røres.

    .venv/bin/python -m research.b4_k3_vending --regressionstjek
    .venv/bin/python -m research.b4_k3_vending --optaelling
    .venv/bin/python -m research.b4_k3_vending --tidsmaaling
    .venv/bin/python -m research.b4_k3_vending --koer

Pris hentes kun gennem ``data.holdout.load_in_sample``; holdout åbnes ikke.
``--optaelling`` og ``--tidsmaaling`` viser ingen R, ingen vinderrate og intet udfald.
``--koer`` er den rigtige kørsel og kræver ejerens godkendelse (§11.6).

## Vejen gennem modulet

1. ``true_range`` og ``wilder_atr``: TR og ATR(14) på hele den kontinuerlige 1m-serie, §4b.
2. ``dagtabel``: åbningens retning pr. RTH-dag (§4a), fladningen, rullerne og
   overnatafkastets fortegn (§9).
3. ``bartabel``: hver 1m-bar der starter i [09:00, 11:00) CT, med farve, TR, ``ATR_{i−1}``,
   ``ATR_i``, næste bar og — for begge sider — indgang, stop og sizing. Handlen mod
   åbningen (modellen og N-tid) og med åbningen (N-med) kommer herfra med samme kode.
4. ``foerste_signal``: dagens første signal der kan handles, pr. side og k, §4f.
5. ``forudregn``: handlen fra en bar med ``simuler_handel``. Udfaldet afhænger kun af
   signalbaren og siden, ikke af k, så hver handel regnes én gang og slås op — testet mod
   direkte simulering. Mod åbningen regnes alle barer i vinduet, fordi N-tid kan trække
   dem alle.
6. ``ntid_traek``: nulmodellen N-tid, §6.
7. ``k2.westfall_young`` og ``beslutning``: §7 og §8.

## Læsninger — valgt af Code, skrevet op før kørslen

Præregistreringen fastlægger ikke disse detaljer. De er valgt her og skal bekræftes.

1. **Dagen er XNYS-sessionsdagen** (ET-datoen, ``k1._et_dag``). 08:30- og 08:59-baren er de
   1m-barer, der starter 08:30 og 08:59 CT den dag. ``r_aabning`` regnes i hele ticks.
2. **Retningsløse dage tælles i rækkefølgen** manglende bar → rul → ``r_aabning = 0``. En
   dag tælles kun ét sted.
3. **ATR'ens start:** Wilders rekursion ``ATR_i = ATR_{i−1} + (TR_i − ATR_{i−1}) / 14``
   starter i seriens første bar med ``ATR_0 = TR_0 = high_0 − low_0`` (der er intet
   ``close_{−1}``). Seriens første bar er 2019-05-05 19:00 CT; dagens første signalbar
   ligger over 800 barer senere, hvor startens vægt er under ``(13/14)^800 ≈ 1e-26``.
4. **ATR over ruller justeres ikke.** "Hele den kontinuerlige 1m-serie" læses bogstaveligt.
   De 19 ruller ligger kl. 18:00-19:01 CT. Springets vægt i ATR kl. 09:00 CT næste dag er
   under ``(13/14)^800``.
5. **En rul mellem 08:30 og 14:50 CT** springer dagen over, og den tælles. Ventet 0, fordi
   alle ruller ligger kl. 18-19 CT. Det samme som kandidat 2's læsning 8.
6. **Hul:** "mere end 1 minut til næste bar" læses som at næste bar starter mere end 1
   minut efter signalbarens start, altså at næste minut mangler. Signalet springes over,
   men **dagen er ikke slut**: det næste signal i vinduet prøves, ligesom et signal der
   ikke kan sizes (§4f). "Det første signal der kan sizes" læses som "det første signal
   der kan handles".
7. **"Indgangen" i §4d er fyldprisen med slippage.** Stoppet ligger 2 × ``ATR_i`` fra
   ``åbning(næste bar) ± 0,5417 tick``, rundet til helt tick væk fra den. ``risiko_pt =
   |fyld − stop|``. Det er det ``simuler_handel`` regner med: dens stop er ``entry_pris ∓
   risiko_pt`` og dens R regnes fra ``entry_pris``. Målet ``fyld ± 1,5 × risiko_pt`` ligger
   derfor ikke på tick-gitteret. Det fyldes, når barens high/low når det (motorens regel).
8. **Afrunding:** ``floor`` (long) og ``ceil`` (short) tages efter afrunding til 9
   decimaler, så flydende tals støj ikke flytter et stop der ligger præcis på et tick.
   Samme greb som sizing i ``trinA.sizing_ekte``.
9. **Signalminuttet** er minuttet (CT), hvor signalbaren starter. N-tid's fordeling for
   variant v er minutterne for **modellens handler** i varianten, én pr. handelsdag, samlet
   over alle dage. Der trækkes med tilbagelægning, altså en tilfældig af modellens handlers
   minutter. Det giver "samme tidsprofil" som modellens handler.
10. **N-tid på det trukne minut:** signalbaren er baren der starter i det minut den dag.
    Indgang, hul, stop, mål, sizing og omkostning er modellens, i modellens retning. Er
    baren der ikke, er der hul, eller er ``kontrakter < 1``, har dagen ingen N-tid-handel i
    den gentagelse, og det tælles. I serien har alle 1.173 dage alle 120 minutter.
11. **N-tid's tilfældige tal:** én strøm pr. gentagelse og variant,
    ``default_rng([9300, gentagelse, variantindeks])``. Varianterne trækkes uafhængigt.
12. **N-med** er dagens første handlebare volatilitetslys i åbningens farve, handlet i
    åbningens retning, uafhængigt af modellen. En dag kan have både en model- og en
    N-med-handel.
13. **Forskellen i §6 og §8 er N-med minus modellen**, med ``k2.forskel_ci`` (Welch).
14. **+0,20 R gælder punktestimatet**; CI-betingelsen er CI-nedre > 0. Det er kandidat 1's
    og 2's læsning.
15. **Tvetydig** som kandidat 2's læsning 14: stoppet ramt i en bar efter indgangsbaren,
    hvor også målet kunne nås. Bedste fald gør netop de handler til mål (R_brutto 1,5).
    Indgangsbaren kan ikke være tvetydig, fordi motoren kun tjekker stoppet der. Bedste
    fald regnes for modellen og N-tid ens.
16. **Overnatafkastet** (§9) er ``open(08:30) − close`` for den sidste 1m-bar der starter
    før 16:00 CT på den forrige XNYS-dag (på en halv dag den sidste bar før Globex lukker).
    Rulspring imellem trækkes fra. Den første dag i serien har intet fortegn ("ukendt").
17. **``fl.vindue_mask(…, 1)``** lægges oven på [09:00, 11:00) CT. Den er altid sand der på
    en RTH-dag og er kun et værn.
18. **Signalminuttets p10/p50/p90** er empiriske kvantiler (``inverted_cdf``). De er altid
    et minut der forekommer.
19. **handler_n i optællingen** er antallet af dage med et signal der kan handles. En
    markedsordre fyldes altid, så ingen handel skal simuleres for at tælle dem.
20. **Fladning på halve dage:** ``trinA.flad_tid_utc`` giver 14:50 CT. På en halv dag lukker
    handlen derfor til close i den sidste bar før Globex lukker. Det er kandidat 1's og 2's
    regel.
"""
from __future__ import annotations

import argparse
import math
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research import b4_k1_filtre as fl  # noqa: E402
from research import b4_k1_optaelling as k1  # noqa: E402
from research import b4_k1_trinA as trinA  # noqa: E402
from research import b4_k2_nowick as k2  # noqa: E402
from research.stats import breakeven_win_rate, mean_ci_t  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "output"
PREREG = ROOT / "research" / "prereg" / "b4_k3_vending.md"
KILDE = ROOT / "research" / "kilder" / "bktraders_nasdaq_routine_noter.md"
# Den rigtige kørsel sker kun når disse er committet og uændrede.
COMMITTEDE = (
    Path(__file__).resolve(), ROOT / "tests" / "test_b4_k3_vending.py", PREREG, KILDE,
    ROOT / "research" / "b4_k2_nowick.py", ROOT / "research" / "b4_k1_trinA.py",
    ROOT / "research" / "b4_k1_filtre.py", ROOT / "research" / "b4_k1_optaelling.py",
    ROOT / "research" / "stats.py", ROOT / "data" / "holdout.py",
    ROOT / "data" / "sessions.py",
)

CT = k1.CT
TICK = trinA.TICK
SLIP_PT = trinA.SLIP_PT                 # 0,5417 tick, §4c og §3
MIN_NS = 60 * 10**9

AABNING_FRA = (8, 30)                   # §4a: open af 08:30-baren
AABNING_TIL = (8, 59)                   # §4a: close af 08:59-baren
VINDUE_MIN = (9 * 60, 11 * 60)          # §4b: signalbaren starter i [09:00, 11:00) CT
VINDUE_N = VINDUE_MIN[1] - VINDUE_MIN[0]

ATR_N = 14                              # §4b
K_VAERDIER = (1.0, 1.5, 2.0)            # §5, de tre varianter
STOP_ATR = 2.0                          # §4d
MAAL_R = 1.5                            # §4e

OP, NED, INGEN = 1, -1, 0
MOD, MED = "mod", "med"                 # mod åbningen (modellen, N-tid), med den (N-med)
SIDER = (MOD, MED)

KONTRAKTER_LOFT = trinA.KONTRAKTER_LOFT  # 50
RISIKO_USD = trinA.RISIKO_USD            # 250
MNQ_USD_PR_POINT = trinA.MNQ_USD_PR_POINT
OMK_USD_RUNDTUR = trinA.OMK_USD_RUNDTUR  # 2,627

MAAL, STOP, TIDSEXIT, CENSURERET = trinA.MAAL, trinA.STOP, trinA.TIDSEXIT, trinA.CENSURERET
UDFALD_KODE = k2.UDFALD_KODE
KODE_UDFALD = k2.KODE_UDFALD

NTID_REPS = 500                         # §6, sænkes ikke
NTID_SEED = 9300
AAR_LISTE = list(range(2019, 2024))

# §7: MDE, én-sidet α = 0,05, 80% styrke. σ_R = 1,225 er antaget, 1,5R uden edge.
Z_UKORR = 2.4865
Z_SIDAK3 = 2.9628
SIGMA_R = 1.225
MDE_GRAENSE_R = 0.20
MIN_HANDLER = 330                       # §7: MDE med Šidák 3 ≤ 0,20 R
OEKONOMISK_KRAV_R = 0.20

# §11.3: kandidat 2's hovedvariant, daily · 5 lys · 1R, gennemhandling (commit f053ece).
REGRESSION_K2_HANDLER_N = 611
REGRESSION_K2_MIDDEL_R_NETTO = -0.1430


# ---------------------------------------------------------------------------
# Serien og §4b: TR og ATR
# ---------------------------------------------------------------------------

def mnq() -> pd.DataFrame:
    """MNQ.v.0 1m, 2019-05-06 → 2023-12-31, kun gennem holdout-modulet."""
    return k2.mnq()


def true_range(h, l, c) -> np.ndarray:
    """§4b: ``TR_i = max(high_i, close_{i−1}) − min(low_i, close_{i−1})``. Den første bar
    har intet ``close_{i−1}`` og får ``high − low`` (læsning 3)."""
    h, l, c = (np.asarray(x, dtype=float) for x in (h, l, c))
    forrige = np.r_[np.nan, c[:-1]]
    return np.fmax(h, forrige) - np.fmin(l, forrige)


def wilder_atr(tr, n: int = ATR_N) -> np.ndarray:
    """Wilders ATR, α = 1/n: ``ATR_i = ATR_{i−1} + (TR_i − ATR_{i−1}) / n``, startet med
    ``ATR_0 = TR_0`` (læsning 3). ``ATR[i]`` er kendt ved lukningen af bar i."""
    tr = np.asarray(tr, dtype=float)
    ud = np.empty(len(tr))
    if len(tr) == 0:
        return ud
    a = float(tr[0])
    ud[0] = a
    for j, x in enumerate(tr[1:].tolist(), start=1):
        a += (x - a) / n
        ud[j] = a
    return ud


@dataclass
class Serie:
    """1m-serien som rå arrays — det motoren og signalet læser."""
    tider: np.ndarray
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    tr: np.ndarray
    atr: np.ndarray
    iid: np.ndarray

    @classmethod
    def af(cls, df_1m: pd.DataFrame) -> "Serie":
        o, h, l, c = (df_1m[k].to_numpy(dtype=float) for k in ("open", "high", "low", "close"))
        tr = true_range(h, l, c)
        iid = (df_1m["instrument_id"].to_numpy() if "instrument_id" in df_1m.columns
               else np.zeros(len(df_1m), dtype=np.int64))
        return cls(tider=k2._ns(df_1m.index), o=o, h=h, l=l, c=c, tr=tr,
                   atr=wilder_atr(tr), iid=iid)

    @property
    def n(self) -> int:
        return len(self.tider)


def ruller(s: Serie) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(position, tid_ns, spring_pt) for hver rul: første bar i den nye kontrakt, og
    første open i den minus sidste close i den gamle."""
    pos = np.flatnonzero(s.iid[1:] != s.iid[:-1]) + 1
    return pos, s.tider[pos], s.o[pos] - s.c[pos - 1]


# ---------------------------------------------------------------------------
# §4a: åbningens retning, og dagens faste tider
# ---------------------------------------------------------------------------

def _kl(dage: pd.DatetimeIndex, t: int, m: int) -> np.ndarray:
    """Klokkeslæt t:m CT på hver dag, i UTC-ns."""
    d = pd.DatetimeIndex(dage) + pd.Timedelta(hours=t, minutes=m)
    return k2._ns(d.tz_localize(CT).tz_convert("UTC"))


def _find(tider: np.ndarray, t: np.ndarray) -> np.ndarray:
    """Positionen for baren der starter præcis i ``t``, −1 hvis den mangler."""
    pos = np.searchsorted(tider, t, side="left")
    ok = (pos < len(tider)) & (tider[np.minimum(pos, len(tider) - 1)] == t)
    return np.where(ok, pos, -1).astype(np.int64)


def dagtabel(s: Serie, dage: pd.DatetimeIndex) -> pd.DataFrame:
    """Pr. RTH-dag: åbningens retning og status (§4a, læsning 1 og 2), fladningen (§3) og
    overnatafkastets fortegn (§9, læsning 16)."""
    d = pd.DatetimeIndex(dage)
    i0830 = _find(s.tider, _kl(d, *AABNING_FRA))
    i0859 = _find(s.tider, _kl(d, *AABNING_TIL))
    t0830 = _kl(d, *AABNING_FRA)
    flad = np.array([k2._ns(pd.DatetimeIndex([trinA.flad_tid_utc(t)]))[0]
                     for t in pd.DatetimeIndex(t0830, tz="UTC")], dtype=np.int64)
    mangler = (i0830 < 0) | (i0859 < 0)
    r_t = np.where(mangler, 0,
                   k2.tick(s.c[np.maximum(i0859, 0)]) - k2.tick(s.o[np.maximum(i0830, 0)]))

    _, rul_ns, spring = ruller(s)
    rul = (np.searchsorted(rul_ns, flad, side="right")
           - np.searchsorted(rul_ns, t0830, side="left")) > 0

    status = np.where(mangler, "mangler", np.where(rul, "rul",
                                                   np.where(r_t == 0, "nul", "ok")))
    retning = np.where(status == "ok", np.sign(r_t), INGEN).astype(np.int8)

    # Læsning 16: overnatafkastet fra forrige XNYS-dags sidste bar før 16:00 CT.
    fortegn = np.full(len(d), np.nan)
    if len(d) > 1:
        t1600 = _kl(d[:-1], 16, 0)
        i_f = np.searchsorted(s.tider, t1600, side="left") - 1
        dag_f = k1._et_dag(pd.DatetimeIndex(s.tider[np.maximum(i_f, 0)], tz="UTC"))
        gyldig = (i_f >= 0) & (np.asarray(dag_f) == np.asarray(d[:-1])) & (i0830[1:] >= 0)
        spring_t = np.r_[0, np.cumsum(k2.tick(spring))]
        fra = np.searchsorted(rul_ns, s.tider[np.maximum(i_f, 0)], side="right")
        til = np.searchsorted(rul_ns, t0830[1:], side="right")
        ovn_t = (k2.tick(s.o[np.maximum(i0830[1:], 0)]) - k2.tick(s.c[np.maximum(i_f, 0)])
                 - (spring_t[til] - spring_t[fra]))
        fortegn[1:] = np.where(gyldig, np.sign(ovn_t), np.nan)

    return pd.DataFrame({
        "i_0830": i0830, "i_0859": i0859, "r_aabning_t": r_t, "status": status,
        "retning": retning, "t0830_ns": t0830, "flad_ns": flad,
        "cutoff_i": np.searchsorted(s.tider, flad, side="left"),
        "overnat_fortegn": fortegn, "aar": d.year,
    }, index=d.rename("dag"))


# ---------------------------------------------------------------------------
# §4b-§4d: vinduets barer, signalet, indgangen, stoppet og sizing
# ---------------------------------------------------------------------------

def sizing(risiko_pt) -> dict[str, np.ndarray]:
    """``kontrakter = floor(250 / (risiko_pt × 2))``, loftet ved 50, §3. Samme afrunding før
    floor som ``trinA.sizing_ekte``."""
    risiko_usd = np.asarray(risiko_pt, dtype=float) * MNQ_USD_PR_POINT
    with np.errstate(divide="ignore"):
        raa = np.floor(np.round(RISIKO_USD / risiko_usd, 9))
    return {"kontrakter_raa": raa, "kontrakter": np.minimum(raa, KONTRAKTER_LOFT),
            "omk_R": OMK_USD_RUNDTUR / risiko_usd}


def indgang_og_stop(aabning_naeste, atr_i, long) -> dict[str, np.ndarray]:
    """§4c og §4d, læsning 7 og 8. Fyld = næste bars åbning ± 0,5417 tick imod. Stoppet
    ligger 2 × ``ATR_i`` fra fyldet, rundet til helt tick væk fra det."""
    long = np.asarray(long, dtype=bool)
    aabning_naeste = np.asarray(aabning_naeste, dtype=float)
    atr_i = np.asarray(atr_i, dtype=float)
    fyld = aabning_naeste + np.where(long, SLIP_PT, -SLIP_PT)
    afstand = STOP_ATR * atr_i
    stop = np.where(long, np.floor(np.round((fyld - afstand) / TICK, 9)),
                    np.ceil(np.round((fyld + afstand) / TICK, 9))) * TICK
    risiko = np.where(long, fyld - stop, stop - fyld)
    return {"fyld": fyld, "stop": stop, "risiko_pt": risiko, **sizing(risiko)}


def bartabel(s: Serie, dage: pd.DataFrame) -> pd.DataFrame:
    """Hver 1m-bar der starter i [09:00, 11:00) CT på en RTH-dag, i tidsorden, med alt §4b-§4d
    kræver for begge sider."""
    idx = pd.DatetimeIndex(s.tider, tz="UTC")
    ct = idx.tz_convert(CT)
    minut = np.asarray(ct.hour * 60 + ct.minute)
    kand = np.flatnonzero((minut >= VINDUE_MIN[0]) & (minut < VINDUE_MIN[1]))
    vindue = fl.vindue_mask(idx[kand], 1)                      # læsning 17
    dag_pos = pd.DatetimeIndex(dage.index).get_indexer(k1._et_dag(idx[kand]))
    behold = vindue & (dag_pos >= 0)
    i = kand[behold]
    dag_pos = dag_pos[behold].astype(np.int64)
    if len(i) and int(i.min()) < 1:
        raise ValueError("en signalbar har ingen bar før sig, så ATR_{i−1} findes ikke")

    o_t, c_t = k2.tick(s.o[i]), k2.tick(s.c[i])
    naeste = np.minimum(i + 1, s.n - 1)
    naeste_ok = (i + 1 < s.n) & (s.tider[naeste] - s.tider[i] == MIN_NS)   # læsning 6
    retning = dage["retning"].to_numpy()[dag_pos]
    t = pd.DataFrame({
        "i": i, "entry_i": i + 1, "dag_pos": dag_pos, "minut_off": minut[i] - VINDUE_MIN[0],
        "tid_ns": s.tider[i], "retning": retning, "aktiv": retning != INGEN,
        "groen": c_t > o_t, "roed": c_t < o_t,
        "tr": s.tr[i], "atr_foer": s.atr[i - 1], "atr_i": s.atr[i],
        "naeste_ok": naeste_ok, "aabning_naeste": s.o[naeste],
        "cutoff_i": dage["cutoff_i"].to_numpy()[dag_pos],
    })
    for side in SIDER:
        # Mod åbningen: long efter en åbning ned. Med åbningen: long efter en åbning op.
        long = retning == (NED if side == MOD else OP)
        ind = indgang_og_stop(t["aabning_naeste"], t["atr_i"], long)
        t[f"long_{side}"] = long
        # Long kræver et grønt lys, short et rødt (§4b.1, og §6 for N-med).
        t[f"farve_{side}"] = t["aktiv"] & np.where(long, t["groen"], t["roed"])
        for k_, v in ind.items():
            t[f"{k_}_{side}"] = v
        t[f"handlebar_{side}"] = (t["aktiv"] & t["naeste_ok"]
                                  & (t[f"kontrakter_{side}"] >= 1))
    return t


@dataclass
class Grundlag:
    """Alt der er fast gennem kørslen."""
    s: Serie
    dage: pd.DataFrame
    bar: pd.DataFrame
    forudregnet: set = field(default_factory=set)

    @property
    def n_1m(self) -> int:
        return self.s.n


def byg_grundlag(df_1m: pd.DataFrame, dage: pd.DatetimeIndex | None = None) -> Grundlag:
    """Serien, dagene og vinduets barer. Ingen handel simuleres her. ``dage`` er RTH-dagene;
    standard er XNYS-dagene som serien spænder over."""
    s = Serie.af(df_1m)
    if dage is None:
        et = k1._et_dag(df_1m.index[[0, -1]])
        dage = k1.rth_dage(et[0], et[1] + pd.Timedelta(days=1))
    d = dagtabel(s, dage)
    return Grundlag(s=s, dage=d, bar=bartabel(s, d))


def signal_maske(g: Grundlag, side: str, k: float) -> np.ndarray:
    """§4b: farven passer til siden og ``TR_i > k × ATR_{i−1}``, på en dag med retning."""
    b = g.bar
    return (b[f"farve_{side}"].to_numpy(dtype=bool)
            & (b["tr"].to_numpy(dtype=float) > k * b["atr_foer"].to_numpy(dtype=float)))


@dataclass
class Valg:
    """Dagens handel pr. dag (rækker i bartabellen, i tidsorden) og tællerne."""
    raekker: np.ndarray
    tael: dict


def foerste_signal(g: Grundlag, side: str, k: float) -> Valg:
    """§4f: dagens første signal der kan handles (læsning 6). Signaler før det, der springes
    over for hul eller afvises for ``kontrakter < 1``, tælles, i den rækkefølge."""
    b = g.bar
    sig = signal_maske(g, side, k)
    hul = sig & ~b["naeste_ok"].to_numpy(dtype=bool)
    nul = sig & ~hul & (b[f"kontrakter_{side}"].to_numpy(dtype=float) < 1)
    ok = sig & ~hul & ~nul
    dag = b["dag_pos"].to_numpy(dtype=np.int64)
    r_ok = np.flatnonzero(ok)
    _, forst = np.unique(dag[r_ok], return_index=True)
    valgt = r_ok[forst].astype(np.int64)
    graense = np.full(len(g.dage), np.iinfo(np.int64).max)
    graense[dag[valgt]] = valgt
    foer = np.arange(len(b)) < graense[dag]
    long_n = int(b[f"long_{side}"].to_numpy(dtype=bool)[valgt].sum())
    return Valg(valgt, {
        "signaler_n": int(sig.sum()),
        "dage_med_signal_n": int(np.unique(dag[sig]).size),
        "sprunget_over_hul_n": int((hul & foer).sum()),
        "afvist_kontrakter_nul_n": int((nul & foer).sum()),
        "handler_n": len(valgt), "long_n": long_n, "short_n": len(valgt) - long_n,
    })


def alle_valg(g: Grundlag) -> dict:
    return {(side, k): foerste_signal(g, side, k) for side in SIDER for k in K_VAERDIER}


# ---------------------------------------------------------------------------
# Handlen, med kandidat 1's rettede motor
# ---------------------------------------------------------------------------

def simuler(s: Serie, entry_i: int, fyld: float, long: bool, risiko_pt: float,
            cutoff_i: int) -> tuple[str, float, int, bool]:
    """(udfald, R_brutto, exit_i, tvetydig) for én handel. ``trinA.simuler_handel`` med
    ``be_r=None`` og ``maal_r=1.5``; i indgangsbaren kan kun stoppet rammes. Tvetydig
    regnes bagefter (læsning 15), så motoren ikke røres."""
    udfald, r, exit_i, _ = trinA.simuler_handel(
        s.h, s.l, s.c, entry_i, fyld, long, risiko_pt, be_r=None, cutoff_i=cutoff_i,
        n=s.n, ret_fyldningsbar=True, maal_r=MAAL_R)
    tvetydig = False
    if udfald == STOP and exit_i > entry_i:
        maal = fyld + MAAL_R * risiko_pt if long else fyld - MAAL_R * risiko_pt
        tvetydig = bool(s.h[exit_i] >= maal) if long else bool(s.l[exit_i] <= maal)
    return udfald, r, exit_i, tvetydig


def forudregn(g: Grundlag, side: str, raekker: np.ndarray) -> None:
    """Handlen fra hver række i ``raekker`` for ``side``, lagt på bartabellen. Udfaldet
    afhænger kun af signalbaren og siden, ikke af k eller af hvem der valgte baren."""
    b = g.bar
    navne = (f"udfald_{side}", f"R_brutto_{side}", f"exit_i_{side}", f"tvetydig_{side}")
    if navne[0] not in b.columns:
        b[navne[0]] = np.zeros(len(b), dtype=np.int8)
        b[navne[1]] = np.full(len(b), np.nan)
        b[navne[2]] = np.full(len(b), -1, dtype=np.int64)
        b[navne[3]] = np.zeros(len(b), dtype=bool)
    kode, r_b = b[navne[0]].to_numpy().copy(), b[navne[1]].to_numpy().copy()
    ex, tv = b[navne[2]].to_numpy().copy(), b[navne[3]].to_numpy().copy()
    entry = b["entry_i"].to_numpy(dtype=np.int64)
    fyld = b[f"fyld_{side}"].to_numpy(dtype=float)
    long = b[f"long_{side}"].to_numpy(dtype=bool)
    risiko = b[f"risiko_pt_{side}"].to_numpy(dtype=float)
    cutoff = b["cutoff_i"].to_numpy(dtype=np.int64)
    handlebar = b[f"handlebar_{side}"].to_numpy(dtype=bool)
    for r in np.asarray(raekker, dtype=np.int64):
        if not handlebar[r]:
            raise ValueError(f"række {r} kan ikke handles ({side})")
        u, rr, e, t = simuler(g.s, int(entry[r]), float(fyld[r]), bool(long[r]),
                              float(risiko[r]), int(cutoff[r]))
        kode[r], r_b[r], ex[r], tv[r] = UDFALD_KODE[u], rr, e, t
    b[navne[0]], b[navne[1]], b[navne[2]], b[navne[3]] = kode, r_b, ex, tv
    g.forudregnet.add(side)


def handelstabel(g: Grundlag, raekker: np.ndarray, side: str) -> pd.DataFrame:
    """De valgte handler som tabel, i ``k2.noegletal``'s format. Kræver forudregnede
    handler."""
    if side not in g.forudregnet:
        raise RuntimeError("handlerne er ikke forudregnet — optællingen simulerer ingen")
    t = g.bar.iloc[np.asarray(raekker, dtype=np.int64)]
    koder = t[f"udfald_{side}"].to_numpy()
    if (koder == 0).any():
        raise RuntimeError(f"{int((koder == 0).sum())} rækker har ingen forudregnet handel")
    r_b = t[f"R_brutto_{side}"].to_numpy(dtype=float)
    tv = t[f"tvetydig_{side}"].to_numpy(dtype=bool)
    omk = t[f"omk_R_{side}"].to_numpy(dtype=float)
    udfald = np.array([KODE_UDFALD[int(x)] for x in koder], dtype=object)
    dp = t["dag_pos"].to_numpy(dtype=np.int64)
    return pd.DataFrame({
        "raekke": np.asarray(raekker, dtype=np.int64), "dag": g.dage.index[dp],
        "aar": g.dage["aar"].to_numpy()[dp], "minut_off": t["minut_off"].to_numpy(),
        "side": np.where(t[f"long_{side}"].to_numpy(dtype=bool), "long", "short"),
        "udfald": udfald, "R_brutto": r_b, "R_netto": r_b - omk, "tvetydig": tv,
        "udfald_bedste": np.where(tv, MAAL, udfald),
        "R_netto_bedste": np.where(tv, MAAL_R, r_b) - omk,
        "risiko_pt": t[f"risiko_pt_{side}"].to_numpy(dtype=float),
        "kontrakter": t[f"kontrakter_{side}"].to_numpy(dtype=float), "omk_R": omk,
        "overnat_fortegn": g.dage["overnat_fortegn"].to_numpy()[dp],
    })


def middel_R(g: Grundlag, raekker: np.ndarray, side: str) -> tuple[float, float]:
    """(middel netto-R forsigtigt, i bedste fald) — gentagelsernes eneste tal."""
    if len(raekker) == 0:
        return float("nan"), float("nan")
    b = g.bar
    r_b = b[f"R_brutto_{side}"].to_numpy(dtype=float)[raekker]
    tv = b[f"tvetydig_{side}"].to_numpy(dtype=bool)[raekker]
    omk = b[f"omk_R_{side}"].to_numpy(dtype=float)[raekker]
    return float((r_b - omk).mean()), float((np.where(tv, MAAL_R, r_b) - omk).mean())


# ---------------------------------------------------------------------------
# §6: nulmodellen N-tid
# ---------------------------------------------------------------------------

@dataclass
class NtidGrundlag:
    """Fast gennem gentagelserne: pr. variant modellens handelsdage og signalminutter, og
    opslaget (dag, minut) → række i bartabellen, −1 hvis baren ikke kan handles mod
    åbningen."""
    dage: dict
    pulje: dict
    opslag: np.ndarray


def ntid_grundlag(g: Grundlag, model: dict) -> NtidGrundlag:
    """``model`` er {k: Valg} for siden mod åbningen (læsning 9 og 10)."""
    b = g.bar
    opslag = np.full((len(g.dage), VINDUE_N), -1, dtype=np.int64)
    h = np.flatnonzero(b[f"handlebar_{MOD}"].to_numpy(dtype=bool))
    opslag[b["dag_pos"].to_numpy()[h], b["minut_off"].to_numpy()[h]] = h
    dp, mo = b["dag_pos"].to_numpy(), b["minut_off"].to_numpy()
    return NtidGrundlag(dage={k: dp[v.raekker] for k, v in model.items()},
                        pulje={k: mo[v.raekker] for k, v in model.items()},
                        opslag=opslag)


def ntid_traek(nt: NtidGrundlag, k: float, rng: np.random.Generator
               ) -> tuple[np.ndarray, int]:
    """Én trækning for variant k: et minut pr. modelhandelsdag fra variantens egen pulje.
    Returnerer (rækker der kan handles, antal dage uden N-tid-handel)."""
    d, p = nt.dage[k], nt.pulje[k]
    if len(d) == 0:
        return np.zeros(0, dtype=np.int64), 0
    r = nt.opslag[d, p[rng.integers(0, len(p), size=len(d))]]
    return r[r >= 0], int((r < 0).sum())


def ntid_rng(rep: int, k: float) -> np.random.Generator:
    """Læsning 11: én strøm pr. gentagelse og variant."""
    return np.random.default_rng([NTID_SEED, rep, K_VAERDIER.index(k)])


def ntid_gentagelse(g: Grundlag, nt: NtidGrundlag, rep: int) -> dict:
    """{k: {handler_n, udfaldne_n, m, m_bedste}} for én N-tid-gentagelse."""
    ud = {}
    for k in K_VAERDIER:
        r, udfaldne = ntid_traek(nt, k, ntid_rng(rep, k))
        m, m_b = middel_R(g, r, MOD)
        ud[k] = {"handler_n": len(r), "udfaldne_n": udfaldne, "m": m, "m_bedste": m_b}
    return ud


# ---------------------------------------------------------------------------
# §7 og §8
# ---------------------------------------------------------------------------

def mde(handler_n: int, z: float = Z_SIDAK3) -> float:
    """§7: ``(z_α + z_0,20) × σ / √n``."""
    return z * SIGMA_R / math.sqrt(handler_n) if handler_n > 0 else float("inf")


def beslutning(raekker: dict, alfa: float = 0.05) -> dict:
    """§8, mekanisk. ``raekker`` er {k: {"p_FWE", "middel_R_netto",
    "middel_R_netto_ci95_lo"}}. Første række der passer, gælder."""
    def _sig(r):
        return r["p_FWE"] <= alfa

    def _ci(r):
        return r["middel_R_netto_ci95_lo"] > 0

    raekke1 = [v for v, r in raekker.items()
               if _sig(r) and _ci(r) and r["middel_R_netto"] >= OEKONOMISK_KRAV_R]
    if raekke1:
        frosset = max(raekke1, key=lambda v: raekker[v]["middel_R_netto_ci95_lo"])
        return {"raekke": 1, "variant": frosset, "kandidater": raekke1,
                "tekst": "Varianten fryses"}
    raekke2 = [v for v, r in raekker.items() if _sig(r) and _ci(r)]
    if raekke2:
        return {"raekke": 2, "variant": None, "kandidater": raekke2,
                "tekst": "Parkeres som reel, men under det økonomiske krav"}
    if not any(_sig(r) for r in raekker.values()) and any(_ci(r) for r in raekker.values()):
        return {"raekke": 3, "variant": None,
                "kandidater": [v for v, r in raekker.items() if _ci(r)],
                "tekst": "Kandidat 3 parkeres: volatilitetslyset tilføjer intet ud over "
                         "tidspunktet"}
    return {"raekke": 4, "variant": None, "kandidater": [], "tekst": "Kandidat 3 parkeres"}


# ---------------------------------------------------------------------------
# Den rigtige kørsel, §6-§10
# ---------------------------------------------------------------------------

def forbered(g: Grundlag) -> tuple[dict, NtidGrundlag]:
    """Valgene, de forudregnede handler og N-tid's opslag. Mod åbningen regnes alle barer
    der kan handles; med åbningen kun N-med's valgte."""
    valg = alle_valg(g)
    forudregn(g, MOD, np.flatnonzero(g.bar[f"handlebar_{MOD}"].to_numpy(dtype=bool)))
    forudregn(g, MED, np.unique(np.concatenate(
        [valg[(MED, k)].raekker for k in K_VAERDIER] + [np.zeros(0, dtype=np.int64)])))
    nt = ntid_grundlag(g, {k: valg[(MOD, k)] for k in K_VAERDIER})
    return valg, nt


def koer_virkelig(g: Grundlag, valg: dict) -> dict:
    """{k: {"model": handler, "nmed": handler}}."""
    return {k: {"model": handelstabel(g, valg[(MOD, k)].raekker, MOD),
                "nmed": handelstabel(g, valg[(MED, k)].raekker, MED)}
            for k in K_VAERDIER}


def afgoerelse(virkelig: dict, gentagelser: list[dict], bedste: bool) -> dict:
    """Westfall-Young mod N-tid, §8 og N-med-sammenligningen for én opgørelse."""
    felt = "m_bedste" if bedste else "m"
    obs = {k: k2.noegletal(virkelig[k]["model"], bedste)["middel_R_netto"]
           for k in K_VAERDIER}
    null = {k: np.array([rep[k][felt] for rep in gentagelser]) for k in K_VAERDIER}
    wy = k2.westfall_young(obs, null)
    raekker = {}
    for k in K_VAERDIER:
        model, nmed = virkelig[k]["model"], virkelig[k]["nmed"]
        n = k2.noegletal(model, bedste)
        nm = k2.noegletal(nmed, bedste)
        kol = "R_netto_bedste" if bedste else "R_netto"
        d, dlo, dhi = k2.forskel_ci(nmed[kol], model[kol])
        pv = wy["pr_variant"][k]
        raekker[k] = {**n, **{f"N_tid_{x}": pv[x] for x in ("p5", "p50", "p95", "med", "sd")},
                      "t_v": pv["t"], "p_FWE": pv["p_FWE"],
                      "N_tid_handler_n_middel": float(np.mean(
                          [rep[k]["handler_n"] for rep in gentagelser])),
                      "N_tid_udfaldne_n_middel": float(np.mean(
                          [rep[k]["udfaldne_n"] for rep in gentagelser])),
                      "N_med_handler_n": nm["handler_n"],
                      "N_med_middel_R_netto": nm["middel_R_netto"],
                      "N_med_middel_R_netto_ci95_lo": nm["middel_R_netto_ci95_lo"],
                      "N_med_middel_R_netto_ci95_hi": nm["middel_R_netto_ci95_hi"],
                      "N_med_minus_model": d, "N_med_minus_model_ci95_lo": dlo,
                      "N_med_minus_model_ci95_hi": dhi,
                      "N_med_fortsaettelsesfund": bool(
                          nm["middel_R_netto_ci95_lo"] > 0 and dlo > 0),
                      "MDE_R_sidak3": mde(n["handler_n"]),
                      "MDE_R_ukorr": mde(n["handler_n"], Z_UKORR)}
    return {"wy": wy, "raekker": raekker, "beslutning": beslutning(raekker)}


def _gruppe(h: pd.DataFrame, kol: str = "R_netto") -> dict:
    r = h[kol].to_numpy(dtype=float)
    lo, hi = mean_ci_t(r) if len(r) >= 2 else (float("nan"), float("nan"))
    return {"n": len(r), "middel_R_netto": float(r.mean()) if len(r) else float("nan"),
            "ci95_lo": lo, "ci95_hi": hi}


def _p(x, q) -> float:
    x = np.asarray(x, dtype=float)
    return float(np.percentile(x, q)) if len(x) else float("nan")


def _minut(x, q) -> float:
    """Læsning 18: empirisk kvantil, altid et minut der forekommer."""
    x = np.asarray(x, dtype=float)
    return float(np.percentile(x, q, method="inverted_cdf")) if len(x) else float("nan")


def sizing_raekke(t: pd.DataFrame, side: str) -> dict:
    """§9's omkostnings- og størrelseskolonner over de valgte barer."""
    omk = t[f"omk_R_{side}"].to_numpy(dtype=float)
    k_ = t[f"kontrakter_{side}"].to_numpy(dtype=float)
    row = {"n": len(t)}
    for q in (10, 50, 90):
        row[f"risiko_pt_p{q}"] = _p(t[f"risiko_pt_{side}"], q)
    row["omk_R_netto_p50"] = _p(omk, 50)
    row["omk_R_netto_p90"] = _p(omk, 90)
    row["be_WR_pct_netto_p50"] = (100 * breakeven_win_rate(MAAL_R, 1.0, row["omk_R_netto_p50"])
                                  if len(t) else float("nan"))
    row["kontrakter_p50"] = _p(k_, 50)
    row["kontrakter_maks"] = float(k_.max()) if len(k_) else float("nan")
    row["kontrakter_loftet_n"] = int(
        (t[f"kontrakter_raa_{side}"].to_numpy(dtype=float) > KONTRAKTER_LOFT).sum())
    return row


def diagnoser(g: Grundlag, virkelig: dict) -> dict:
    """§9: long mod short, overnatafkastet og år. Optællingens diagnoser står i
    ``optaelling``."""
    side, overnat, aar = [], [], []
    navne = {1.0: "positivt", -1.0: "negativt", 0.0: "nul"}
    for k in K_VAERDIER:
        h = virkelig[k]["model"]
        lo, sh = h[h["side"] == "long"]["R_netto"], h[h["side"] == "short"]["R_netto"]
        d, dlo, dhi = k2.forskel_ci(lo, sh)
        side.append({"k": k, "long_n": len(lo), "short_n": len(sh),
                     "long_middel_R_netto": float(lo.mean()) if len(lo) else float("nan"),
                     "short_middel_R_netto": float(sh.mean()) if len(sh) else float("nan"),
                     "forskel": d, "forskel_ci95_lo": dlo, "forskel_ci95_hi": dhi})
        f = h["overnat_fortegn"].to_numpy(dtype=float)
        for v, navn in navne.items():
            overnat.append({"k": k, "overnat": navn, **_gruppe(h[f == v])})
        overnat.append({"k": k, "overnat": "ukendt", **_gruppe(h[np.isnan(f)])})
        for a in AAR_LISTE:
            aar.append({"k": k, "aar": a, **k2.noegletal(h[h["aar"] == a])})
    return {"side": side, "overnat": overnat, "aar": aar}


def koer(n_reps: int = NTID_REPS) -> dict:
    """§6-§10. Regressionstjekket først — afviger det, køres intet."""
    df = mnq()
    reg = regressionstjek(df)
    if not reg["ok"]:
        raise RuntimeError(f"regressionstjekket afveg, kørslen sker ikke: {reg}")
    g = byg_grundlag(df, k1.rth_dage(trinA.MNQ_START, trinA.TRIN_A_SLUT))
    valg, nt = forbered(g)
    virkelig = koer_virkelig(g, valg)
    t0 = time.perf_counter()
    gentagelser = [ntid_gentagelse(g, nt, rep) for rep in range(n_reps)]
    ntid_s = time.perf_counter() - t0
    afg = {"forsigtig": afgoerelse(virkelig, gentagelser, bedste=False),
           "bedste_fald": afgoerelse(virkelig, gentagelser, bedste=True)}
    return {"g": g, "valg": valg, "virkelig": virkelig, "gentagelser": gentagelser,
            "afgoerelse": afg, "diagnoser": diagnoser(g, virkelig),
            "optaelling": optaelling(g, valg), "regression": reg, "n_reps": n_reps,
            "ntid_s": ntid_s}


# ---------------------------------------------------------------------------
# §11.4: optællingen uden udfald
# ---------------------------------------------------------------------------

def optaelling(g: Grundlag, valg: dict | None = None) -> dict:
    """§11.4. Dage, signaler, handler_n, signalminut, risiko og omkostning pr. variant, for
    modellen og N-med, og pr. år. Ingen handel simuleres; intet R regnes."""
    valg = alle_valg(g) if valg is None else valg
    st = g.dage["status"].to_numpy()
    ret = g.dage["retning"].to_numpy()
    dage = {"rth_dage_n": len(g.dage), "dage_med_aabningsretning_n": int((st == "ok").sum()),
            "aabning_ned_n": int(((st == "ok") & (ret == NED)).sum()),
            "aabning_op_n": int(((st == "ok") & (ret == OP)).sum()),
            "r_aabning_nul_n": int((st == "nul").sum()),
            "mangler_bar_n": int((st == "mangler").sum()), "rul_n": int((st == "rul").sum()),
            "vindue_barer_n": len(g.bar),
            "vindue_barer_uden_naeste_minut_n": int((~g.bar["naeste_ok"]).sum())}
    varianter, aar = [], []
    for side in SIDER:
        for k in K_VAERDIER:
            v = valg[(side, k)]
            t = g.bar.iloc[v.raekker]
            mo = t["minut_off"].to_numpy() + VINDUE_MIN[0]
            row = {"model": "vending" if side == MOD else "N_med", "k": k,
                   "dage_med_aabningsretning_n": dage["dage_med_aabningsretning_n"],
                   **v.tael,
                   "dage_uden_signal_n": dage["dage_med_aabningsretning_n"]
                   - v.tael["dage_med_signal_n"],
                   "dage_med_handel_n": int(np.unique(t["dag_pos"]).size),
                   **{f"signalminut_p{q}": _minut(mo, q) for q in (10, 50, 90)},
                   **sizing_raekke(t, side)}
            row.pop("n")
            if side == MOD:
                row["MDE_R_sidak3"] = mde(row["handler_n"])
                row["MDE_R_ukorr"] = mde(row["handler_n"], Z_UKORR)
                row["betingelse_ok"] = bool(row["handler_n"] >= MIN_HANDLER
                                            and row["MDE_R_sidak3"] <= MDE_GRAENSE_R)
            varianter.append(row)
            aarstal = g.dage["aar"].to_numpy()[t["dag_pos"].to_numpy()]
            for a in AAR_LISTE:
                sub = t[aarstal == a]
                aar.append({"model": row["model"], "k": k, "aar": a,
                            "handler_n": len(sub), **sizing_raekke(sub, side)})
    nt = ntid_grundlag(g, {k: valg[(MOD, k)] for k in K_VAERDIER})
    ntid = {k: {"modeldage_n": len(nt.dage[k]),
                "puljens_minutter_n": int(np.unique(nt.pulje[k]).size),
                "celler_uden_handlebar_bar_n": int(
                    (nt.opslag[nt.dage[k]][:, np.unique(nt.pulje[k])] < 0).sum())}
            for k in K_VAERDIER}
    return {"dage": dage, "varianter": varianter, "aar": aar, "ntid": ntid}


def _hhmm(m) -> str:
    if m is None or not np.isfinite(m):
        return "—"
    m = int(round(m))
    return f"{m // 60:02d}:{m % 60:02d}"


def _knavn(k) -> str:
    return f"k = {k:.1f}".replace(".", ",")


def _rel(sti: Path) -> str:
    return Path(sti).resolve().relative_to(ROOT.resolve()).as_posix()


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "--no-optional-locks", "-C", str(ROOT), *args],
                          capture_output=True, text=True)


def _arbejdskopi(stier) -> str:
    rel = [_rel(s) for s in stier]
    ud = _git("status", "--porcelain", "--", *rel).stdout.strip()
    if not ud:
        return "kode, tests og præregistrering committet og uændrede"
    return "med ændringer i arbejdskopien: " + ", ".join(
        f"`{linje[3:]}`" for linje in ud.splitlines())


def optaelling_md(o: dict, g: Grundlag, meta: dict, kun_tabeller: bool = False) -> str:
    _t = k2._t
    d = o["dage"]
    hoved = [
        "# B4 kandidat 3 — optælling uden udfald (§11.4)\n",
        f"Kørt {meta['koert_utc']} UTC fra commit `{meta['head'][:7]}`, "
        f"{_arbejdskopi(COMMITTEDE)}. **Ingen handel er simuleret; intet R, ingen "
        f"vinderrate og intet udfald er regnet.**\n",
    ]
    dele = [] if kun_tabeller else hoved
    dele += [
        f"Serie: MNQ.v.0 1m gennem `data.holdout.load_in_sample`, "
        f"{trinA.MNQ_START.date()} → 2023-12-31, {_t(g.n_1m)} 1m-barer. "
        f"{_t(d['rth_dage_n'])} RTH-dage. 1m-barer i [09:00, 11:00) CT: "
        f"{_t(d['vindue_barer_n'])}, heraf uden en bar i næste minut: "
        f"{_t(d['vindue_barer_uden_naeste_minut_n'])}.\n",
        "## Åbningens retning, §4a\n",
        "| RTH-dage | med retning | ned (long) | op (short) | r_aabning = 0 | manglende bar | "
        "rul 08:30-14:50 CT |", "|---|---|---|---|---|---|---|",
        f"| {_t(d['rth_dage_n'])} | {_t(d['dage_med_aabningsretning_n'])} | "
        f"{_t(d['aabning_ned_n'])} | {_t(d['aabning_op_n'])} | {_t(d['r_aabning_nul_n'])} | "
        f"{_t(d['mangler_bar_n'])} | {_t(d['rul_n'])} |",
        "", "## Pr. variant — dækning og handler, §9 og §11.4\n",
        "Én handel om dagen, så handler_n = dage med handel. Signaler er alle 1m-barer i "
        "vinduet der opfylder §4b, også dem efter dagens handel.\n",
        "| model | variant | dage med retning | signaler | dage med signal | dage uden signal | "
        "sprunget over (hul) | afvist (kontrakter 0) | **handler_n** | long | short | "
        "signalminut p10/p50/p90 CT |", "|" + "---|" * 12,
    ]
    for r in o["varianter"]:
        dele.append(
            f"| {r['model']} | {_knavn(r['k'])} | {_t(r['dage_med_aabningsretning_n'])} | "
            f"{_t(r['signaler_n'])} | {_t(r['dage_med_signal_n'])} | "
            f"{_t(r['dage_uden_signal_n'])} | {_t(r['sprunget_over_hul_n'])} | "
            f"{_t(r['afvist_kontrakter_nul_n'])} | **{_t(r['handler_n'])}** | "
            f"{_t(r['long_n'])} | {_t(r['short_n'])} | {_hhmm(r['signalminut_p10'])}/"
            f"{_hhmm(r['signalminut_p50'])}/{_hhmm(r['signalminut_p90'])} |")
    dele += ["", "## Pr. variant — risiko, omkostning og størrelse, §9\n",
             "Over de valgte barer. be_WR_pct_netto_p50 = (1 + omk_R_netto_p50) / 2,5 (§6, N0).\n",
             "| model | variant | risiko_pt p10/p50/p90 | omk_R_netto p50/p90 | "
             "be_WR_pct_netto_p50 | kontrakter p50/maks | kontrakter_loftet_n |",
             "|---|---|---|---|---|---|---|"]
    for r in o["varianter"]:
        dele.append(
            f"| {r['model']} | {_knavn(r['k'])} | {_t(r['risiko_pt_p10'], 2)}/"
            f"{_t(r['risiko_pt_p50'], 2)}/{_t(r['risiko_pt_p90'], 2)} | "
            f"{_t(r['omk_R_netto_p50'], 3)}/{_t(r['omk_R_netto_p90'], 3)} | "
            f"{_t(r['be_WR_pct_netto_p50'], 1)} | {_t(r['kontrakter_p50'], 0)}/"
            f"{_t(r['kontrakter_maks'], 0)} | {_t(r['kontrakter_loftet_n'])} |")
    dele += ["", "## Pr. år — risiko og omkostning, §9\n",
             "| model | variant | år | handler_n | risiko_pt p10/p50/p90 | omk_R_netto p50/p90 | "
             "kontrakter_loftet_n |", "|---|---|---|---|---|---|---|"]
    for r in o["aar"]:
        dele.append(
            f"| {r['model']} | {_knavn(r['k'])} | {r['aar']} | {_t(r['handler_n'])} | "
            f"{_t(r['risiko_pt_p10'], 2)}/{_t(r['risiko_pt_p50'], 2)}/"
            f"{_t(r['risiko_pt_p90'], 2)} | {_t(r['omk_R_netto_p50'], 3)}/"
            f"{_t(r['omk_R_netto_p90'], 3)} | {_t(r['kontrakter_loftet_n'])} |")
    dele += ["", "## N-tid's opslag, §6\n",
             "Pr. variant: modellens handelsdage, hvor mange forskellige minutter puljen har, "
             "og hvor mange (dag, puljeminut)-celler der ikke kan handles (læsning 10).\n",
             "| variant | modeldage | minutter i puljen | celler uden handlebar bar |",
             "|---|---|---|---|"]
    for k in K_VAERDIER:
        z = o["ntid"][k]
        dele.append(f"| {_knavn(k)} | {_t(z['modeldage_n'])} | {_t(z['puljens_minutter_n'])} | "
                    f"{_t(z['celler_uden_handlebar_bar_n'])} |")
    model = [r for r in o["varianter"] if r["model"] == "vending"]
    dele += ["", "## Betingelsen i §7\n",
             "| variant | handler_n | MDE_R_ukorr | MDE_R_sidak3 | ≥ 330 |", "|---|---|---|---|---|"]
    for r in model:
        dele.append(f"| {_knavn(r['k'])} | {_t(r['handler_n'])} | {_t(r['MDE_R_ukorr'], 3)} | "
                    f"{_t(r['MDE_R_sidak3'], 3)} | "
                    f"{'OK' if r['betingelse_ok'] else '**UNDER**'} |")
    ok = all(r["betingelse_ok"] for r in model)
    dele += ["", ("Alle 3 varianter har `handler_n ≥ 330`, så MDE (Šidák 3) ≤ 0,20 R.\n" if ok
                  else "**Mindst én variant ligger under kravet. Code stopper, og ejeren "
                       "beslutter (§7).**\n")]
    return "\n".join(dele)


def optaelling_csv(o: dict) -> pd.DataFrame:
    rows = [{"tabel": "variant", **r} for r in o["varianter"]]
    rows += [{"tabel": "aar", **r} for r in o["aar"]]
    rows.append({"tabel": "dage", **o["dage"]})
    rows += [{"tabel": "N_tid_opslag", "k": k, **z} for k, z in o["ntid"].items()]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Rapporten, §10
# ---------------------------------------------------------------------------

def hovedtabel_md(afg: dict) -> str:
    _t = k2._t
    linjer = ["| variant | handler_n | dage | tvetydig_n | censureret_n | middel_R_brutto | "
              "middel_R_netto | CI95 | win_rate_pct_brutto [Wilson] | "
              "win_rate_pct_netto [Wilson] | mål/stop/tid_pct | N_tid p5/p50/p95 | t_v | "
              "p_FWE |", "|" + "---|" * 14]
    for k in K_VAERDIER:
        r = afg["raekker"][k]
        linjer.append(
            f"| {_knavn(k)} | {_t(r['handler_n'])} | {_t(r['dage_med_handel_n'])} | "
            f"{_t(r['tvetydig_n'])} | {_t(r['censureret_n'])} | {_t(r['middel_R_brutto'], 4)} | "
            f"{_t(r['middel_R_netto'], 4)} | [{_t(r['middel_R_netto_ci95_lo'], 4)}; "
            f"{_t(r['middel_R_netto_ci95_hi'], 4)}] | {_t(r['win_rate_pct_brutto'], 1)} "
            f"[{_t(r['win_rate_pct_brutto_ci95_lo'], 1)}; "
            f"{_t(r['win_rate_pct_brutto_ci95_hi'], 1)}] | "
            f"{_t(r['win_rate_pct_netto'], 1)} [{_t(r['win_rate_pct_netto_ci95_lo'], 1)}; "
            f"{_t(r['win_rate_pct_netto_ci95_hi'], 1)}] | {_t(r['udfald_maal_pct'], 1)}/"
            f"{_t(r['udfald_stop_pct'], 1)}/{_t(r['udfald_tidsexit_pct'], 1)} | "
            f"{_t(r['N_tid_p5'], 4)}/{_t(r['N_tid_p50'], 4)}/{_t(r['N_tid_p95'], 4)} | "
            f"{_t(r['t_v'], 2)} | {_t(r['p_FWE'], 4)} |")
    return "\n".join(linjer) + "\n"


def nmed_md(afg: dict) -> str:
    _t = k2._t
    linjer = ["| variant | N_med_handler_n | N_med_middel_R_netto [CI95] | "
              "N_med − model [Welch-CI95] | in-sample-fund om fortsættelse |",
              "|---|---|---|---|---|"]
    for k in K_VAERDIER:
        r = afg["raekker"][k]
        linjer.append(
            f"| {_knavn(k)} | {_t(r['N_med_handler_n'])} | {_t(r['N_med_middel_R_netto'], 4)} "
            f"[{_t(r['N_med_middel_R_netto_ci95_lo'], 4)}; "
            f"{_t(r['N_med_middel_R_netto_ci95_hi'], 4)}] | {_t(r['N_med_minus_model'], 4)} "
            f"[{_t(r['N_med_minus_model_ci95_lo'], 4)}; "
            f"{_t(r['N_med_minus_model_ci95_hi'], 4)}] | "
            f"{_t(r['N_med_fortsaettelsesfund'])} |")
    return "\n".join(linjer) + "\n"


def _beslutning_md(navn: str, afg: dict) -> str:
    b = afg["beslutning"]
    v = f" Frosset variant: **{_knavn(b['variant'])}**." if b["variant"] is not None else ""
    return f"**{navn}: række {b['raekke']}: {b['tekst']}.**{v}\n"


def skriv_md(res: dict, meta: dict) -> str:
    _t = k2._t
    afg = res["afgoerelse"]
    d = res["diagnoser"]
    dele = [
        "# B4 kandidat 3 — vending efter åbningen\n",
        f"Kørt {meta['koert_utc']} UTC fra commit `{meta['head'][:7]}`. Præregistrering "
        f"`{_rel(PREREG)}` (commit `{meta['commits'][_rel(PREREG)][:7]}`). Kode "
        f"`{_rel(Path(__file__))}` (commit `{meta['commits'][_rel(Path(__file__))][:7]}`).\n",
        f"Serie: MNQ.v.0 1m, {trinA.MNQ_START.date()} → 2023-12-31, {_t(res['g'].n_1m)} "
        f"1m-barer. 3 varianter. N-tid: {res['n_reps']} gentagelser.\n",
        "**Regressionstjek: OK.**\n",
        "## Hovedtabel — forsigtigt (afgørelsen tages her)\n",
        hovedtabel_md(afg["forsigtig"]),
        "## Afgørelsen, §8, mekanisk\n",
        _beslutning_md("Forsigtigt", afg["forsigtig"]),
        _beslutning_md("Bedste fald, tvetydige minutter (diagnose)", afg["bedste_fald"]),
    ]
    if afg["bedste_fald"]["beslutning"]["raekke"] != afg["forsigtig"]["beslutning"]["raekke"]:
        dele.append("Afgørelsen er en anden i bedste fald: resultatet er **afhængigt af data "
                    "under minutniveau**, §9.\n")
    dele += [
        "## N-med — fortsættelse i stedet for vending (forklarer, ændrer ikke rækken)\n",
        nmed_md(afg["forsigtig"]),
        "## Bedste fald — samme tabel\n", hovedtabel_md(afg["bedste_fald"]),
        "## Long mod short\n",
        "| variant | long_n | short_n | long R_netto | short R_netto | forskel [CI95] |\n"
        "|---|---|---|---|---|---|\n" +
        "".join(f"| {_knavn(r['k'])} | {_t(r['long_n'])} | {_t(r['short_n'])} | "
                f"{_t(r['long_middel_R_netto'], 4)} | {_t(r['short_middel_R_netto'], 4)} | "
                f"{_t(r['forskel'], 4)} [{_t(r['forskel_ci95_lo'], 4)}; "
                f"{_t(r['forskel_ci95_hi'], 4)}] |\n" for r in d["side"]),
        "## Efter overnatafkastets fortegn (beskrivende)\n",
        "| variant | overnat | n | middel_R_netto [CI95] |\n|---|---|---|---|\n" +
        "".join(f"| {_knavn(r['k'])} | {r['overnat']} | {_t(r['n'])} | "
                f"{_t(r['middel_R_netto'], 4)} [{_t(r['ci95_lo'], 4)}; "
                f"{_t(r['ci95_hi'], 4)}] |\n" for r in d["overnat"]),
        "## Pr. år — middel_R_netto (handler_n)\n",
        "| variant | " + " | ".join(str(a) for a in AAR_LISTE) + " |\n|" +
        "---|" * (1 + len(AAR_LISTE)) + "\n" +
        "".join(f"| {_knavn(k)} | " + " | ".join(
            f"{_t(r['middel_R_netto'], 3)} ({_t(r['handler_n'])})"
            for r in d["aar"] if r["k"] == k) + " |\n" for k in K_VAERDIER),
        "## Optælling og øvrige diagnoser, §9\n",
        optaelling_md(res["optaelling"], res["g"], meta, kun_tabeller=True),
        "## Efter kørslen, §13\n",
        "Stop. Ingen ændring af definitioner, ingen nye varianter, ingen forslag.\n",
        f"Alle tal: `{_rel(OUT / 'b4_k3_vending.csv')}`.\n",
    ]
    return "\n".join(dele)


def lang_tabel(res: dict) -> pd.DataFrame:
    rows = []
    for navn, afg in res["afgoerelse"].items():
        for k in K_VAERDIER:
            rows.append({"tabel": "hoved", "afgoerelse": navn, "k": k,
                         "raekke_8": afg["beslutning"]["raekke"], **afg["raekker"][k]})
    for tabel in ("side", "overnat", "aar"):
        rows += [{"tabel": tabel, "afgoerelse": "forsigtig", **r}
                 for r in res["diagnoser"][tabel]]
    optael = optaelling_csv(res["optaelling"]).rename(columns={"tabel": "optaelling"})
    optael.insert(0, "tabel", "optaelling")
    return pd.concat([pd.DataFrame(rows), optael], ignore_index=True)


# ---------------------------------------------------------------------------
# §11.3: regressionstjek
# ---------------------------------------------------------------------------

def regression_k2_hovedvariant(df: pd.DataFrame) -> dict:
    """Kandidat 2's hovedvariant, daily · 5 lys · 1R med gennemhandling, gengiver 611
    handler og −0,1430 R (commit f053ece). Kører kandidat 2's egen vej, uændret."""
    g = k2.byg_grundlag(df)
    uden = g.lys["uden_vaege"].to_numpy(dtype=bool)
    sig = np.flatnonzero(g.gyldig["daily"]["gyldig"] & uden)
    res = k2.koer_signalsaet(g, "daily", sig, regler=("gennem",))
    h = k2.handelstabel(g, res[(5, "gennem")].fyldt, "gennem", 1.0)
    m = float(h["R_netto"].mean())
    return {"handler_n": len(h), "middel_R_netto": m,
            "ok": len(h) == REGRESSION_K2_HANDLER_N
            and round(m, 4) == REGRESSION_K2_MIDDEL_R_NETTO}


def regressionstjek(df: pd.DataFrame | None = None) -> dict:
    """§11.3: kandidat 1's tre tjek, ``simuler_handel``'s 1.226 handler og −0,0115 R (med
    standardværdien og med ``maal_r=2`` eksplicit), og kandidat 2's hovedvariant."""
    from research import b4_k1_trin2 as trin2   # tung; kun her
    df = mnq() if df is None else df
    t0 = time.perf_counter()
    ud = {"k1": trin2.regressionstjek(df), "motor": k2.regressionstjek_motor(df),
          "k2_hovedvariant": regression_k2_hovedvariant(df)}
    ud["sekunder"] = time.perf_counter() - t0
    ud["ok"] = bool(ud["k1"]["alle_ok"] and ud["motor"]["ok"] and ud["k2_hovedvariant"]["ok"])
    return ud


# ---------------------------------------------------------------------------
# §11.5: tidsmålingen — uden R
# ---------------------------------------------------------------------------

def tidsmaaling(n_reps: int = 5) -> dict:
    """§11.5: ét gennemløb og ``n_reps`` N-tid-gentagelser, fremskrevet til R = 500.
    Returnerer kun tider og antal. R regnes inde i gentagelserne, fordi det er arbejdet der
    måles, men det forlader ikke funktionen."""
    t0 = time.perf_counter()
    df = mnq()
    load_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    g = byg_grundlag(df, k1.rth_dage(trinA.MNQ_START, trinA.TRIN_A_SLUT))
    grundlag_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    valg, nt = forbered(g)
    forudregn_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    virkelig = koer_virkelig(g, valg)
    for k in K_VAERDIER:
        k2.noegletal(virkelig[k]["model"])
        k2.noegletal(virkelig[k]["nmed"])
    gennemloeb_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    taelle = []
    for rep in range(n_reps):
        r = ntid_gentagelse(g, nt, rep)
        taelle.append({k: (x["handler_n"], x["udfaldne_n"]) for k, x in r.items()})
    ntid_s = time.perf_counter() - t0
    pr_rep = ntid_s / n_reps if n_reps else 0.0
    forventet = load_s + grundlag_s + forudregn_s + gennemloeb_s + pr_rep * NTID_REPS
    return {"load_s": load_s, "grundlag_s": grundlag_s, "forudregn_s": forudregn_s,
            "forudregnede_mod_n": int(g.bar[f"handlebar_{MOD}"].sum()),
            "forudregnede_med_n": int((g.bar[f"udfald_{MED}"] > 0).sum()),
            "gennemloeb_s": gennemloeb_s, "n_reps": n_reps, "ntid_s": ntid_s,
            "pr_rep_s": pr_rep, "forventet_s": forventet,
            "handler_n": {f"{'vending' if s == MOD else 'N_med'} {_knavn(k)}":
                          len(valg[(s, k)].raekker) for s in SIDER for k in K_VAERDIER},
            "ntid_handler_og_udfaldne_n": taelle}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--regressionstjek", action="store_true",
                     help="§11.3: kandidat 1's tre tjek, simuler_handel og kandidat 2")
    grp.add_argument("--optaelling", action="store_true",
                     help="§11.4: optælling uden udfald. Skriver b4_k3_vending_optaelling")
    grp.add_argument("--tidsmaaling", action="store_true",
                     help="§11.5: ét gennemløb og 5 N-tid-gentagelser, uden R")
    grp.add_argument("--koer", action="store_true",
                     help="§6-§10: den rigtige kørsel. Kræver ejerens godkendelse")
    ap.add_argument("--reps", type=int, default=NTID_REPS)
    ap.add_argument("--maalte-reps", type=int, default=5)
    args = ap.parse_args(argv)
    meta = {"koert_utc": pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M"),
            "head": _git("rev-parse", "HEAD").stdout.strip()}

    if args.regressionstjek:
        r = regressionstjek()
        k1r, mo, k2r = r["k1"], r["motor"], r["k2_hovedvariant"]
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
        print(f"Kandidat 2, daily · 5 lys · 1R: handler_n {k2r['handler_n']} (ventet "
              f"{REGRESSION_K2_HANDLER_N}), middel_R_netto {k2r['middel_R_netto']:.4f} "
              f"(ventet {REGRESSION_K2_MIDDEL_R_NETTO}): {'OK' if k2r['ok'] else 'AFVIGER'}")
        print(f"Tid: {r['sekunder']:.0f} s")
        if not r["ok"]:
            sys.exit(1)
        return

    if args.optaelling:
        df = mnq()
        g = byg_grundlag(df, k1.rth_dage(trinA.MNQ_START, trinA.TRIN_A_SLUT))
        o = optaelling(g)
        md = optaelling_md(o, g, meta)
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "b4_k3_vending_optaelling.md").write_text(md, encoding="utf-8")
        optaelling_csv(o).to_csv(OUT / "b4_k3_vending_optaelling.csv", index=False)
        print(md)
        return

    if args.tidsmaaling:
        t = tidsmaaling(args.maalte_reps)
        print(f"Indlæsning {t['load_s']:.1f} s, grundlag {t['grundlag_s']:.1f} s, "
              f"forudregnede handler {t['forudregn_s']:.1f} s ({t['forudregnede_mod_n']} barer "
              f"mod åbningen, {t['forudregnede_med_n']} med), gennemløb af 3 varianter og "
              f"N-med {t['gennemloeb_s']:.2f} s")
        print(f"{t['n_reps']} N-tid-gentagelser: {t['ntid_s']:.2f} s, "
              f"{t['pr_rep_s'] * 1000:.1f} ms pr. gentagelse")
        print(f"Fremskrevet til R = {NTID_REPS}: {t['forventet_s']:.0f} s "
              f"({t['forventet_s'] / 60:.1f} min), regressionstjekket ikke medregnet")
        print(f"handler_n: {t['handler_n']}")
        print(f"N-tid (handler_n, dage uden N-tid-handel) pr. gentagelse: "
              f"{t['ntid_handler_og_udfaldne_n']}")
        return

    commits = k1.committede(COMMITTEDE)
    res = koer(n_reps=args.reps)
    meta["commits"] = commits
    md = skriv_md(res, meta)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "b4_k3_vending.md").write_text(md, encoding="utf-8")
    lang_tabel(res).to_csv(OUT / "b4_k3_vending.csv", index=False)
    print(md)


if __name__ == "__main__":
    main()
