"""B4 kandidat 2 — Nowick: lys uden væge i trendens retning, MNQ 5m.

Præregistreret i ``research/prereg/b4_k2_nowick.md``. Kilden er
``research/kilder/bardfx_nowick_reel_noter.md``. Motoren er kandidat 1's rettede
``research/b4_k1_trinA.simuler_handel``, der har fået målet som parameter (``maal_r``);
standardværdien bevarer kandidat 1's 2R. Swing-koden og vinduet er
``research/b4_k1_filtre.py``'s, uændret.

    .venv/bin/python -m research.b4_k2_nowick --regressionstjek
    .venv/bin/python -m research.b4_k2_nowick --optaelling
    .venv/bin/python -m research.b4_k2_nowick --tidsmaaling
    .venv/bin/python -m research.b4_k2_nowick --koer

Pris hentes kun gennem ``data.holdout.load_in_sample``; holdout åbnes ikke.
``--optaelling`` og ``--tidsmaaling`` viser ingen R, ingen vinderrate og intet udfald.
``--koer`` er den rigtige kørsel og kræver ejerens godkendelse (§11.6).

## Vejen gennem modulet

1. ``forskelsjuster`` og ``byg_htf``: daily og 4H bygget af den samme 1m-serie, §4b. HTF-
   lysene regnes på den forskelsjusterede serie; handelspriserne justeres ikke.
2. ``htf_tilstand``: op, ned eller udefineret pr. HTF-lys ved lukningen, §4b.
3. ``lys_tabel``: alle 5m-lys i vinduet der ikke er doji, med side, linje, stop, sizing og
   HTF-tilstanden ved lysets lukning. Både signaler uden væge og nulmodellens lys med væge
   kommer herfra, med præcis samme kode.
4. ``foerste_fyld``: for hvert lys den første 1m-bar inden for ordrens længst mulige liv
   hvor prisen handler igennem linjen, og den første hvor den rører den.
5. ``forudregn_handler``: handlen fra den bar, med ``simuler_handel``, for 1R og 2R og for
   begge fyldningsregler. En handels udfald afhænger kun af fyldningsbaren, så den kan
   regnes én gang og slås op — testet mod direkte simulering.
6. ``dagsgennemloeb``: ordrerne pr. dag: N lys, nyeste erstatter, trendskift, vinduets
   slutning, én handel om dagen, §4c og §4f.
7. ``nalm_traek``: nulmodellen, §6.
8. ``westfall_young`` og ``beslutning``: §7 og §8.

## Læsninger — valgt af Code, skrevet op før kørslen

Præregistreringen fastlægger ikke disse detaljer. De er valgt her og skal bekræftes.

1. **HTF-lysets lukketid er den nominelle**: daily 16:00 CT, 4H 21, 01, 05, 09, 13 og 16
   CT. Ikke tidspunktet for den sidste 1m-bar i lyset; et lys er først lukket når dets tid
   er gået.
2. **1m-barer i pausen 16:00-17:00 CT hører ikke til noget HTF-lys.** Der er 2 i serien.
   De tælles og bruges ikke til trenden.
3. **Forskelsjusteringen sker på 1m, før HTF-lysene bygges.** Alle 19 ruller ligger kl.
   18:00 eller 19:00 CT, altså inde i et daily- og et 4H-lys. Springet er første open i
   den nye kontrakt minus sidste close i den gamle, og al forudgående historik flyttes.
4. **Swing-niveauet ved et HTF-lys' lukning** er det seneste der er kendt ved netop den
   lukning (``fl._seneste_niveau``), som kandidat 1's kriterium 6.
5. **Lukker et HTF-lys både over toppen og under bunden** (det kan ske når den seneste
   swing-bund ligger over den seneste swing-top), er tilstanden **uændret**. Se
   ``KONFLIKT``.
6. **N lys er N × 5 minutter** på 5m-gitteret fra signallysets lukning. Der er 4 huller i
   5m-gitteret inden for vinduet i hele serien; her tæller et lys uden handel som et lys.
7. **Regel 8 på halve dage:** hvilende ordrer annulleres ved vinduets slutning, altså
   ``min(14:30 CT, RTH-luk − 30 min)``, 11:30 CT på en halv dag. Det er den grænse
   ``fl.vindue_mask`` bruger for nye signaler.
8. **Rul:** et signal springes over hvis en rul ligger fra det første af de 10 stoplys til
   14:50 CT samme dag. Det dækker 10-lys-vinduet, ordrens levetid og handlen, og det kan
   afgøres ved signallysets lukning, fordi rullerne ligger fast på forhånd.
9. **Nulmodellen følger §4d fuldt ud**, også reglen om at lyset selv er 10-lys-ekstremet.
   Matchingen sker pr. ET-dag **og** HTF-tilstand: på 4H kan dagen have to tilstande, og
   k trækkes for hver for sig.
10. **Strejf** er en ordre der rører linjen uden at handle igennem og slutter uden fyld
    (udløb, erstatning eller annullering). Den kontrafaktiske handel er fyldt ved den
    første berøring, altså samme handel som under berøringsreglen.
11. **Fyldningsraten pr. N** er andelen af signaler hvis linje handles igennem inden for N
    lys, regnet for hvert signal for sig: uden erstatning og uden disciplin, men med
    vinduets slutning og trendskiftet.
12. **sd_v i Westfall-Young** er stikprøvespredningen (ddof = 1) over gentagelserne.
13. **§8's +0,20 R gælder punktestimatet**; CI-betingelsen er CI-nedre > 0. Det er den
    læsning trin 2-tillægget godkendte for kandidat 1.
14. **Tvetydig** uden BE: stoppet ramt i en 1m-bar efter fyldningsbaren hvor også målet
    kunne nås. Bedste fald gør netop de handler til mål. Det regnes her, efter
    ``simuler_handel``, så kandidat 1's motor ikke røres.
15. **Tællerne for udfaldne signaler** tælles i rækkefølgen udefineret trend → mod trenden
    (intet signal, ikke et udfald) → ingen stopplads → rul → nul kontrakter. Et lys tælles
    kun ét sted.
"""
from __future__ import annotations

import argparse
import math
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import partial
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data import holdout, resample, sessions  # noqa: E402
from research import b4_k1_filtre as fl  # noqa: E402
from research import b4_k1_optaelling as k1  # noqa: E402
from research import b4_k1_trinA as trinA  # noqa: E402
from research.stats import breakeven_win_rate, mean_ci_t, t_critical, wilson_interval  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "output"
PREREG = ROOT / "research" / "prereg" / "b4_k2_nowick.md"
KILDE = ROOT / "research" / "kilder" / "bardfx_nowick_reel_noter.md"
# Den rigtige kørsel sker kun når disse er committet og uændrede.
COMMITTEDE = (
    Path(__file__).resolve(), ROOT / "tests" / "test_b4_k2_nowick.py", PREREG, KILDE,
    ROOT / "research" / "b4_k1_trinA.py", ROOT / "research" / "b4_k1_filtre.py",
    ROOT / "research" / "b4_k1_optaelling.py", ROOT / "research" / "stats.py",
    ROOT / "data" / "holdout.py", ROOT / "data" / "resample.py",
    ROOT / "data" / "sessions.py",
)

CT = k1.CT
TICK = trinA.TICK
BAR_MIN = 5
BAR_NS = BAR_MIN * 60 * 10**9
EVIG = np.iinfo(np.int64).max

HTF_NAVNE = ("daily", "4H")
N_LYS = (3, 5, 9)
MAAL_R = (1.0, 2.0)
REGLER = ("gennem", "beroering")        # §4c regel 1, og §9's fyld ved berøring
VARIANTER = tuple((htf, n, m) for htf in HTF_NAVNE for n in N_LYS for m in MAAL_R)
HOVEDVARIANT = ("daily", 5, 1.0)        # står øverst, ingen særstatus, §5

SWING_N = fl.SWING_N                    # 5, som kandidat 1
STOP_LYS = 10                           # §4d
STOP_TICKS = 2                          # §4d
MAKS_LIV_NS = max(N_LYS) * BAR_NS       # ordrens længst mulige liv

KONTRAKTER_LOFT = trinA.KONTRAKTER_LOFT  # 50
RISIKO_USD = trinA.RISIKO_USD            # 250
MNQ_USD_PR_POINT = trinA.MNQ_USD_PR_POINT
OMK_USD_RUNDTUR = trinA.OMK_USD_RUNDTUR  # 2,627

OP, NED, UDEF = 1, -1, 0
# Læsning 5: et HTF-lys der lukker både over toppen og under bunden, ændrer ikke tilstanden.
KONFLIKT = "uaendret"

MAAL, STOP, TIDSEXIT, CENSURERET = trinA.MAAL, trinA.STOP, trinA.TIDSEXIT, trinA.CENSURERET
UDFALD_KODE = {MAAL: 1, STOP: 2, TIDSEXIT: 3, CENSURERET: 4}
KODE_UDFALD = {v: k for k, v in UDFALD_KODE.items()}

NALM_REPS = 500                         # §6, sænkes ikke
NALM_SEED = 9100
AAR_LISTE = list(range(2019, 2024))

# §7: MDE, én-sidet α = 0,05, 80% styrke. σ_R er antaget, uden edge.
Z_UKORR = 2.4865
Z_SIDAK12 = 3.4719
SIGMA_R = {1.0: 1.0, 2.0: 1.414}
MDE_GRAENSE_R = 0.20
MIN_HANDLER = {1.0: 301, 2.0: 603}      # §7's tal, som præregistreret
OEKONOMISK_KRAV_R = 0.20

# §11.3: motorrettelsens tal for buffer 10% / BE +1,2R med den udvidede simuler_handel.
REGRESSION_HANDLER_N = 1226
REGRESSION_MIDDEL_R_NETTO = -0.0115


# ---------------------------------------------------------------------------
# Serien
# ---------------------------------------------------------------------------

def mnq() -> pd.DataFrame:
    """MNQ.v.0 1m, 2019-05-06 → 2023-12-31, kun gennem holdout-modulet."""
    df = holdout.load_in_sample(trinA.MNQ)
    return df[(df.index >= trinA.MNQ_START) & (df.index < trinA.TRIN_A_SLUT)]


def _ns(index) -> np.ndarray:
    return pd.DatetimeIndex(index).as_unit("ns").asi8.copy()


def tick(x) -> np.ndarray:
    """Priser i hele ticks, §4a: ``round(pris / 0,25)``."""
    return np.round(np.asarray(x, dtype=float) / TICK).astype(np.int64)


# ---------------------------------------------------------------------------
# §4b: HTF-lysene, på den forskelsjusterede serie
# ---------------------------------------------------------------------------

def forskelsjuster(df_1m: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(forskelsjusteret 1m-OHLC, rultabel).

    Ved hver rul flyttes al forudgående historik med springet: første open i den nye
    kontrakt minus sidste close i den gamle. Seneste kontrakt står urørt. Det flytter kun
    niveauer med konstanter, så sammenligninger inden for en kontrakt er uændrede, og
    sammenligninger hen over en rul bruger kun spring der er sket.
    """
    o, h, l, c = (df_1m[k].to_numpy(dtype=float) for k in ("open", "high", "low", "close"))
    n = len(df_1m)
    iid = (df_1m["instrument_id"].to_numpy() if "instrument_id" in df_1m.columns
           else np.zeros(n, dtype=np.int64))
    rul = np.flatnonzero(iid[1:] != iid[:-1]) + 1
    spring = np.zeros(n)
    spring[rul] = o[rul] - c[rul - 1]
    fra_og_med = np.cumsum(spring[::-1])[::-1]          # sum over ruller på eller efter i
    forskydning = np.r_[fra_og_med[1:], 0.0]            # kun ruller efter i
    adj = pd.DataFrame({"open": o + forskydning, "high": h + forskydning,
                        "low": l + forskydning, "close": c + forskydning},
                       index=df_1m.index)
    ct = df_1m.index[rul].tz_convert(CT)
    ruller = pd.DataFrame({
        "tid_utc": df_1m.index[rul], "tid_ct": ct.strftime("%Y-%m-%d %H:%M"),
        "ugedag_ct": ct.day_name(), "fra_iid": iid[rul - 1], "til_iid": iid[rul],
        "spring_pt": spring[rul]})
    return adj, ruller


_FORSKYD = pd.Timedelta(hours=7)        # 17:00 CT → 00:00 i den forskudte tid


def htf_noegler(index: pd.DatetimeIndex, htf: str
                ) -> tuple[pd.DatetimeIndex, pd.DatetimeIndex, np.ndarray]:
    """(start, nominel lukning, uden for) pr. 1m-bar, i naiv CT-vægurstid.

    Globex-dagen løber 17:00 CT dagen før til 16:00 CT; i den forskudte tid ``CT + 7 t``
    er det 00:00-23:00, og søndag aften lander på mandag. 4H er de fire timer fra 17:00
    CT: 17-21, 21-01, 01-05, 05-09, 09-13 og 13-16, det sidste afkortet. 1m-barer i pausen
    16:00-17:00 CT (forskudt time 23) hører ikke til noget lys, læsning 2.

    Vægurstid i CT er sikker her: sommertid skifter søndag kl. 02, mens Globex er lukket.
    """
    ct = index.tz_convert(CT).tz_localize(None)
    s = ct + _FORSKYD
    dag = s.normalize()
    time_s = np.asarray(s.hour)
    udenfor = time_s >= 23
    if htf == "daily":
        spand = np.zeros(len(index), dtype=np.int64)
        slut_t = np.full(len(index), 23, dtype=np.int64)
    elif htf == "4H":
        spand = np.minimum(time_s // 4, 5).astype(np.int64)
        slut_t = np.where(spand == 5, 23, (spand + 1) * 4).astype(np.int64)
    else:
        raise ValueError(f"ukendt HTF {htf}")
    start = dag + pd.to_timedelta(spand * 4, unit="h") - _FORSKYD
    luk = dag + pd.to_timedelta(slut_t, unit="h") - _FORSKYD
    return pd.DatetimeIndex(start), pd.DatetimeIndex(luk), udenfor


def byg_htf(df_1m: pd.DataFrame, htf: str) -> tuple[pd.DataFrame, int]:
    """(HTF-lys, antal 1m-barer uden for et lys). §4b.

    Ny funktion, fordi ``data.resample.aggregate`` kun laver tidsrammer der går op i en
    time. Lysene bygges af den forskelsjusterede 1m-serie. Indekset er lysets start i
    UTC; kolonnen ``luk`` er den nominelle lukning i UTC (læsning 1).
    """
    adj, _ = forskelsjuster(df_1m)
    start, luk, udenfor = htf_noegler(adj.index, htf)
    behold = ~udenfor
    sub = adj[behold]
    noegle = start[behold]
    g = sub.groupby(noegle, sort=True)
    ud = pd.DataFrame({
        "open": g["open"].first(), "high": g["high"].max(),
        "low": g["low"].min(), "close": g["close"].last(),
        "n_1m": g["open"].size()})
    luk_pr = pd.Series(luk[behold], index=noegle).groupby(level=0).first()
    ud.index = pd.DatetimeIndex(ud.index).tz_localize(CT).tz_convert("UTC").rename("time")
    ud["luk"] = pd.DatetimeIndex(luk_pr.to_numpy()).tz_localize(CT).tz_convert("UTC")
    return ud, int(udenfor.sum())


def htf_tilstand(htf: pd.DataFrame, swing_n: int = SWING_N) -> tuple[np.ndarray, dict]:
    """(tilstand pr. HTF-lys, tællere). §4b, svar 3A.

    Op når lyset lukker over den seneste kendte swing-top, ned når det lukker under den
    seneste kendte swing-bund, ellers uændret. Udefineret indtil det første brud. Et
    swing-punkt er kendt fra og med lys ``i + swing_n`` (``fl._seneste_niveau``).
    """
    h = htf["high"].to_numpy(dtype=float)
    l = htf["low"].to_numpy(dtype=float)
    c = htf["close"].to_numpy(dtype=float)
    sh, sl = fl.swing_punkter(h, l, swing_n)
    top = fl._seneste_niveau(h, sh, swing_n)
    bund = fl._seneste_niveau(l, sl, swing_n)
    with np.errstate(invalid="ignore"):
        op = c > top
        ned = c < bund
    tilstand = np.zeros(len(c), dtype=np.int8)
    cur = UDEF
    for j in range(len(c)):
        if op[j] and not ned[j]:
            cur = OP
        elif ned[j] and not op[j]:
            cur = NED
        # Begge: læsning 5, uændret. Ingen af dem: uændret.
        tilstand[j] = cur
    return tilstand, {"konflikt_n": int((op & ned).sum()), "lys_n": int(len(c)),
                      "brud_op_n": int(op.sum()), "brud_ned_n": int(ned.sum())}


def tilstand_ved(luk_ns: np.ndarray, htf_luk_ns: np.ndarray, tilstand: np.ndarray
                 ) -> tuple[np.ndarray, np.ndarray]:
    """(tilstand, trend_slut) for tidspunkter ``luk_ns``.

    Tilstanden er den fra det seneste HTF-lys der er lukket senest ved ``luk_ns`` — intet
    kig frem. ``trend_slut`` er lukningen af det første senere HTF-lys med en anden
    tilstand: der annulleres en ordre i den gamle retning, §4c.3. ``EVIG`` hvis den aldrig
    skifter.
    """
    m = np.searchsorted(htf_luk_ns, luk_ns, side="right") - 1
    st = np.where(m >= 0, tilstand[np.maximum(m, 0)], UDEF).astype(np.int8)
    skift = np.flatnonzero(tilstand[1:] != tilstand[:-1]) + 1
    j = np.searchsorted(skift, m, side="right")
    har = j < len(skift)
    slut = np.full(len(luk_ns), EVIG, dtype=np.int64)
    if len(skift):
        slut[har] = htf_luk_ns[skift[j[har]]]
    return st, slut


# ---------------------------------------------------------------------------
# §4a og §4d: signallyset, stoppet og sizing
# ---------------------------------------------------------------------------

def lys_flag(o, h, l, c) -> dict[str, np.ndarray]:
    """§4a og §6 i hele ticks. Doji er aldrig et signal og aldrig en nulkandidat."""
    o_t, h_t, l_t, c_t = tick(o), tick(h), tick(l), tick(c)
    roed, groen = c_t < o_t, c_t > o_t
    return {
        "roed": roed, "groen": groen,
        "short_uden_vaege": roed & (h_t == o_t), "long_uden_vaege": groen & (l_t == o_t),
        "short_med_vaege": roed & (h_t > o_t), "long_med_vaege": groen & (l_t < o_t),
    }


def stop_og_plads(h_t: np.ndarray, l_t: np.ndarray, o_t: np.ndarray, i: np.ndarray,
                  long: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(stop i ticks, ingen_stopplads) for lysene ``i``, §4d.

    Short: højeste high i de 10 lys til og med signallyset + 2 ticks. Long: laveste low − 2
    ticks. Er signallyset selv det højeste (short) eller laveste (long) af de 10, også ved
    lighed, er der ingen plads til et stop.
    """
    if len(i) and int(i.min()) < STOP_LYS - 1:
        raise ValueError("et lys har færre end 10 lys bag sig")
    vh = np.lib.stride_tricks.sliding_window_view(h_t, STOP_LYS)   # vh[k] = h_t[k:k+10]
    vl = np.lib.stride_tricks.sliding_window_view(l_t, STOP_LYS)
    k = i - (STOP_LYS - 1)
    maks10, min10 = vh[k].max(axis=1), vl[k].min(axis=1)
    maks9, min9 = vh[k, :-1].max(axis=1), vl[k, :-1].min(axis=1)
    stop_t = np.where(long, min10 - STOP_TICKS, maks10 + STOP_TICKS)
    ingen = np.where(long, l_t[i] <= min9, h_t[i] >= maks9)
    return stop_t.astype(np.int64), ingen.astype(bool)


def sizing(risiko_t: np.ndarray) -> dict[str, np.ndarray]:
    """``kontrakter = floor(250 / (risiko_pt × 2))``, loftet ved 50, §3. Samme afrunding
    før floor som ``trinA.sizing_ekte``."""
    risiko_pt = risiko_t * TICK
    risiko_usd = risiko_pt * MNQ_USD_PR_POINT
    with np.errstate(divide="ignore"):
        raa = np.floor(np.round(RISIKO_USD / risiko_usd, 9))
    return {"risiko_pt": risiko_pt, "kontrakter_raa": raa,
            "kontrakter": np.minimum(raa, KONTRAKTER_LOFT),
            "omk_R": OMK_USD_RUNDTUR / risiko_usd}


def _dag_tider(dage: pd.DatetimeIndex) -> tuple[np.ndarray, np.ndarray]:
    """(vindue_slut, flad) i ns pr. ET-dag. Vinduets slutning er ``min(14:30 CT,
    RTH-luk − 30 min)`` (læsning 7); fladning 14:50 CT som ``trinA.flad_tid_utc``."""
    d = pd.DatetimeIndex(dage)
    kl1430 = (d + pd.Timedelta(hours=14, minutes=30)).tz_localize(CT).tz_convert("UTC")
    luk = pd.DatetimeIndex(sessions._xnys().schedule["close"].reindex(d))
    slut = np.minimum(_ns(kl1430), _ns(luk - k1.LUK_MARGIN))
    flad = np.array([_ns(pd.DatetimeIndex([trinA.flad_tid_utc(t)]))[0]
                     for t in kl1430], dtype=np.int64)
    return slut, flad


def lys_tabel(df_1m: pd.DataFrame, bars5: pd.DataFrame,
              htf: dict[str, tuple[pd.DataFrame, np.ndarray]]) -> pd.DataFrame:
    """Alle 5m-lys i vinduet der ikke er doji, med alt §4a, §4b og §4d kræver.

    ``htf`` er {navn: (HTF-lys, tilstand)}. Både modellens signaler (uden væge) og
    nulmodellens kandidater (med væge) er rækker her, og gyldigheden regnes ens for dem.
    """
    o_t = tick(bars5["open"]); h_t = tick(bars5["high"]); l_t = tick(bars5["low"])
    flag = lys_flag(bars5["open"], bars5["high"], bars5["low"], bars5["close"])
    vindue = fl.vindue_mask(bars5.index, BAR_MIN)
    i = np.flatnonzero(vindue & (flag["roed"] | flag["groen"]))
    long = flag["groen"][i]
    uden = np.where(long, flag["long_uden_vaege"][i], flag["short_uden_vaege"][i])
    stop_t, ingen = stop_og_plads(h_t, l_t, o_t, i, long)
    risiko_t = np.where(long, o_t[i] - stop_t, stop_t - o_t[i])
    sz = sizing(risiko_t)

    tid = _ns(bars5.index)
    tid_i, luk_i = tid[i], tid[i] + BAR_NS
    dag = k1._et_dag(bars5.index[i])
    unikke = pd.DatetimeIndex(pd.unique(dag))
    slut_d, flad_d = _dag_tider(unikke)
    pos = unikke.get_indexer(dag)
    vindue_slut, flad = slut_d[pos], flad_d[pos]

    # Læsning 8: en rul fra det første stoplys til 14:50 CT samme dag.
    iid = (df_1m["instrument_id"].to_numpy() if "instrument_id" in df_1m.columns
           else np.zeros(len(df_1m), dtype=np.int64))
    rul_ns = _ns(df_1m.index)[np.flatnonzero(iid[1:] != iid[:-1]) + 1]
    fra = tid[i - (STOP_LYS - 1)]
    rul = (np.searchsorted(rul_ns, flad, side="left")
           - np.searchsorted(rul_ns, fra, side="right")) > 0

    t = pd.DataFrame({
        "i5": i, "tid_ns": tid_i, "luk_ns": luk_i, "dag": dag, "long": long,
        "uden_vaege": uden, "linje_t": o_t[i], "linje": o_t[i] * TICK, "stop_t": stop_t,
        "risiko_t": risiko_t, "risiko_pt": sz["risiko_pt"],
        "kontrakter_raa": sz["kontrakter_raa"], "kontrakter": sz["kontrakter"],
        "omk_R": sz["omk_R"], "ingen_stopplads": ingen, "rul": rul,
        "vindue_slut_ns": vindue_slut, "flad_ns": flad,
    })
    for navn, (bars_htf, tilstand) in htf.items():
        st, slut = tilstand_ved(luk_i, _ns(bars_htf["luk"]), tilstand)
        t[f"tilstand_{navn}"] = st
        t[f"trend_slut_{navn}"] = slut
    return t


def gyldighed(lys: pd.DataFrame, htf: str) -> dict[str, np.ndarray]:
    """Masker for én HTF, i læsning 15's rækkefølge. ``gyldig`` er et signal hvis lyset
    er uden væge, og en nulkandidat hvis det har væge."""
    st = lys[f"tilstand_{htf}"].to_numpy()
    long = lys["long"].to_numpy(dtype=bool)
    udef = st == UDEF
    mod = ~udef & ~np.where(long, st == OP, st == NED)
    rest = ~udef & ~mod
    ingen = rest & lys["ingen_stopplads"].to_numpy(dtype=bool)
    rest &= ~ingen
    rul = rest & lys["rul"].to_numpy(dtype=bool)
    rest &= ~rul
    nul = rest & (lys["kontrakter"].to_numpy(dtype=float) < 1)
    rest &= ~nul
    return {"udefineret": udef, "mod_trenden": mod, "ingen_stopplads": ingen,
            "rul": rul, "kontrakter_nul": nul, "gyldig": rest}


# ---------------------------------------------------------------------------
# §4c: fyldning, og handlen fra fyldningsbaren
# ---------------------------------------------------------------------------

@dataclass
class Serie1m:
    """1m-serien som rå arrays — det motoren og fyldningen læser."""
    tider: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    h_t: np.ndarray
    l_t: np.ndarray

    @classmethod
    def af(cls, df_1m: pd.DataFrame) -> "Serie1m":
        h = df_1m["high"].to_numpy(dtype=float)
        l = df_1m["low"].to_numpy(dtype=float)
        return cls(tider=_ns(df_1m.index), h=h, l=l,
                   c=df_1m["close"].to_numpy(dtype=float), h_t=tick(h), l_t=tick(l))

    @property
    def n(self) -> int:
        return len(self.tider)


def foerste_fyld(s: Serie1m, lys: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """(gennem_i, beroering_i): første 1m-bar fra signallysets lukning, inden for ordrens
    længst mulige liv (9 lys, til vinduets slutning), hvor prisen handler mindst ét tick
    igennem linjen (§4a regel 1), og hvor den rører linjen. −1 hvis ingen.

    Det kortere liv for N = 3 og 5, erstatning og trendskift lægges på i
    ``dagsgennemloeb``; den første bar er den samme, så længe den ligger inden for livet.
    """
    luk = lys["luk_ns"].to_numpy(dtype=np.int64)
    slut = np.minimum(luk + MAKS_LIV_NS, lys["vindue_slut_ns"].to_numpy(dtype=np.int64))
    i0 = np.searchsorted(s.tider, luk, side="left")
    i1 = np.searchsorted(s.tider, slut, side="left")
    bredde = max(N_LYS) * BAR_MIN
    j = i0[:, None] + np.arange(bredde)[None, :]
    inde = j < i1[:, None]
    jj = np.minimum(j, s.n - 1)
    long = lys["long"].to_numpy(dtype=bool)[:, None]
    linje = lys["linje_t"].to_numpy(dtype=np.int64)[:, None]
    gennem = inde & np.where(long, s.l_t[jj] <= linje - 1, s.h_t[jj] >= linje + 1)
    rort = inde & np.where(long, s.l_t[jj] <= linje, s.h_t[jj] >= linje)

    def _foerste(m: np.ndarray) -> np.ndarray:
        return np.where(m.any(axis=1), i0 + m.argmax(axis=1), -1).astype(np.int64)

    return _foerste(gennem), _foerste(rort)


def simuler(s: Serie1m, fyld_i: int, linje: float, long: bool, risiko_pt: float,
            maal_r: float, cutoff_i: int) -> tuple[str, float, int, bool]:
    """(udfald, R_brutto, exit_i, tvetydig) for én handel. Kandidat 1's rettede motor,
    uden BE; tvetydig regnes bagefter (læsning 14)."""
    udfald, r, exit_i, _ = trinA.simuler_handel(
        s.h, s.l, s.c, fyld_i, linje, long, risiko_pt, None, cutoff_i, s.n, True, maal_r)
    tvetydig = False
    if udfald == STOP and exit_i > fyld_i:
        maal = linje + maal_r * risiko_pt if long else linje - maal_r * risiko_pt
        tvetydig = bool(s.h[exit_i] >= maal) if long else bool(s.l[exit_i] <= maal)
    return udfald, r, exit_i, tvetydig


def forudregn_handler(s: Serie1m, lys: pd.DataFrame, raekker: np.ndarray) -> pd.DataFrame:
    """Handlen for hvert lys i ``raekker``, fyldt ved den første bar efter hver regel og
    kørt til mål, stop eller 14:50 CT, for 1R og 2R. Kolonnerne lægges på ``lys``.

    Udfaldet afhænger kun af fyldningsbaren, linjen, siden og risikoen, ikke af hvilken
    variant der fyldte, så hver handel regnes én gang.
    """
    lys = lys.copy()
    flad = lys["flad_ns"].to_numpy(dtype=np.int64)
    cutoff = np.searchsorted(s.tider, flad, side="left")
    linje = lys["linje"].to_numpy(dtype=float)
    long = lys["long"].to_numpy(dtype=bool)
    risiko = lys["risiko_pt"].to_numpy(dtype=float)
    for regel in REGLER:
        fyld = lys[f"{regel}_i"].to_numpy(dtype=np.int64)
        for m in MAAL_R:
            kode = np.zeros(len(lys), dtype=np.int8)
            r_b = np.full(len(lys), np.nan)
            ex = np.full(len(lys), -1, dtype=np.int64)
            tv = np.zeros(len(lys), dtype=bool)
            for k in raekker:
                if fyld[k] < 0:
                    continue
                u, r, e, t = simuler(s, int(fyld[k]), float(linje[k]), bool(long[k]),
                                     float(risiko[k]), m, int(cutoff[k]))
                kode[k], r_b[k], ex[k], tv[k] = UDFALD_KODE[u], r, e, t
            sfx = f"{regel}_{int(m)}R"
            lys[f"udfald_{sfx}"] = kode
            lys[f"R_brutto_{sfx}"] = r_b
            lys[f"exit_i_{sfx}"] = ex
            lys[f"tvetydig_{sfx}"] = tv
    return lys


# ---------------------------------------------------------------------------
# §4c og §4f: dagens ordrer
# ---------------------------------------------------------------------------

@dataclass
class Dagsresultat:
    """Hvad ét gennemløb gav: de fyldte lys (højst ét pr. dag), strejfene og tællerne."""
    fyldt: np.ndarray
    strejf: np.ndarray
    tael: dict = field(default_factory=dict)


def ordre_slut(lys: pd.DataFrame, htf: str, n_lys: int) -> np.ndarray:
    """Ordrens naturlige slutning: N lys, vinduets slutning eller trendskiftet, §4c."""
    luk = lys["luk_ns"].to_numpy(dtype=np.int64)
    return np.minimum.reduce([luk + n_lys * BAR_NS,
                              lys["vindue_slut_ns"].to_numpy(dtype=np.int64),
                              lys[f"trend_slut_{htf}"].to_numpy(dtype=np.int64)])


def dagsgennemloeb(raekker: np.ndarray, dag: np.ndarray, luk: np.ndarray,
                   n_slut: np.ndarray, fyld_tid: np.ndarray, rort_tid: np.ndarray,
                   vindue_slut: np.ndarray, trend_slut: np.ndarray, n_lys: int
                   ) -> Dagsresultat:
    """§4c og §4f for signalerne ``raekker`` (rækkeindeks i lystabellen, i tidsorden).

    Én ventende ordre ad gangen. Et nyt signal erstatter den ventende ordre ved sin
    lukning; den gamle kan altså fyldes inde i det nye signallys. Den første ordre der
    fyldes, er dagens handel, og resten af dagens signaler ignoreres. ``fyld_tid`` og
    ``rort_tid`` er tidspunktet for den første gennemhandling og berøring (``EVIG`` hvis
    ingen). Arrays er over hele lystabellen.
    """
    tael = {"ordrer_n": 0, "erstattet_n": 0, "udloebet_n": 0, "annulleret_trend_n": 0,
            "annulleret_vindue_n": 0, "ignoreret_dagslukket_n": 0}
    fyldt: list[int] = []
    strejf: list[int] = []

    def _slut_uden_fyld(p: int, slut: int, erstattet: bool) -> None:
        if rort_tid[p] < slut:
            strejf.append(p)
        if erstattet:
            tael["erstattet_n"] += 1
        elif slut == luk[p] + n_lys * BAR_NS:
            tael["udloebet_n"] += 1
        elif slut == trend_slut[p] and trend_slut[p] < vindue_slut[p]:
            tael["annulleret_trend_n"] += 1
        else:
            tael["annulleret_vindue_n"] += 1

    m = len(raekker)
    if m == 0:
        return Dagsresultat(np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64), tael)
    d = dag[raekker]
    graenser = np.r_[np.flatnonzero(np.r_[True, d[1:] != d[:-1]]), m]
    for gi in range(len(graenser) - 1):
        a, b = int(graenser[gi]), int(graenser[gi + 1])
        p = -1
        lukket = False
        for q in range(a, b):
            k = int(raekker[q])
            if p >= 0:
                slut = min(int(n_slut[p]), int(luk[k]))
                if fyld_tid[p] < slut:
                    fyldt.append(p)
                    tael["ignoreret_dagslukket_n"] += b - q
                    lukket = True
                    break
                _slut_uden_fyld(p, slut, erstattet=int(luk[k]) < int(n_slut[p]))
            tael["ordrer_n"] += 1
            p = k
        if not lukket and p >= 0:
            if fyld_tid[p] < n_slut[p]:
                fyldt.append(p)
            else:
                _slut_uden_fyld(p, int(n_slut[p]), erstattet=False)
    return Dagsresultat(np.asarray(fyldt, dtype=np.int64),
                        np.asarray(strejf, dtype=np.int64), tael)


@dataclass
class Grundlag:
    """Alt der er fast gennem kørslen: lystabellen med fyldning og forudregnede handler,
    gyldighedsmaskerne pr. HTF, HTF-lysene og deres tællere, rullerne."""
    lys: pd.DataFrame
    gyldig: dict[str, dict[str, np.ndarray]]
    htf: dict[str, pd.DataFrame]
    htf_tael: dict[str, dict]
    ruller: pd.DataFrame
    n_1m: int
    n_5m: int
    rth_dage: pd.DatetimeIndex
    handler_forudregnet: bool = False


def byg_grundlag(df_1m: pd.DataFrame, med_handler: bool = True,
                 htf: dict[str, pd.DataFrame] | None = None) -> Grundlag:
    """Hele kørslens faste del. ``med_handler=False`` springer motoren over: det er
    optællingen, som ingen handel simulerer. ``htf`` ({navn: lys med ``luk`` og
    ``tilstand``}) bruges kun af testene, til at styre trenden direkte."""
    bars5 = resample.aggregate(df_1m, BAR_MIN)
    htf_tael = {}
    if htf is None:
        htf = {}
        for navn in HTF_NAVNE:
            bars_htf, udenfor = byg_htf(df_1m, navn)
            tilstand, tael = htf_tilstand(bars_htf)
            htf[navn] = bars_htf.assign(tilstand=tilstand)
            htf_tael[navn] = {**tael, "udenfor_1m_n": udenfor}
    lys = lys_tabel(df_1m, bars5, {n: (b, b["tilstand"].to_numpy()) for n, b in htf.items()})
    s = Serie1m.af(df_1m)
    gi, bi = foerste_fyld(s, lys)
    lys["gennem_i"], lys["beroering_i"] = gi, bi
    lys["gennem_tid"] = np.where(gi >= 0, s.tider[np.maximum(gi, 0)], EVIG)
    lys["beroering_tid"] = np.where(bi >= 0, s.tider[np.maximum(bi, 0)], EVIG)
    gyldig = {navn: gyldighed(lys, navn) for navn in HTF_NAVNE}
    _, ruller = forskelsjuster(df_1m)
    g = Grundlag(lys=lys, gyldig=gyldig, htf=htf, htf_tael=htf_tael, ruller=ruller,
                 n_1m=len(df_1m), n_5m=len(bars5),
                 rth_dage=k1.rth_dage(trinA.MNQ_START, trinA.TRIN_A_SLUT))
    if med_handler:
        relevante = np.flatnonzero(np.logical_or.reduce(
            [gyldig[n]["gyldig"] for n in HTF_NAVNE]))
        g.lys = forudregn_handler(s, lys, relevante)
        g.handler_forudregnet = True
    return g


# ---------------------------------------------------------------------------
# Ét signalsæt gennem alle varianter for én HTF
# ---------------------------------------------------------------------------

def koer_signalsaet(g: Grundlag, htf: str, raekker: np.ndarray,
                    regler: tuple[str, ...] = REGLER) -> dict:
    """{(n_lys, regel): Dagsresultat} for ét signalsæt. Mål deler fyldningerne: dagens
    handel afhænger ikke af målet, fordi handlen lukker efter vinduets slutning eller ved
    mål/stop, og dagen er slut i begge tilfælde."""
    lys = g.lys
    dag = lys["dag"].to_numpy()
    luk = lys["luk_ns"].to_numpy(dtype=np.int64)
    vs = lys["vindue_slut_ns"].to_numpy(dtype=np.int64)
    ts = lys[f"trend_slut_{htf}"].to_numpy(dtype=np.int64)
    rort = lys["beroering_tid"].to_numpy(dtype=np.int64)
    ud = {}
    for n_lys in N_LYS:
        n_slut = ordre_slut(lys, htf, n_lys)
        for regel in regler:
            fyld = lys[f"{regel}_tid"].to_numpy(dtype=np.int64)
            ud[(n_lys, regel)] = dagsgennemloeb(raekker, dag, luk, n_slut, fyld, rort,
                                                vs, ts, n_lys)
    return ud


def handelstabel(g: Grundlag, fyldt: np.ndarray, regel: str, maal_r: float) -> pd.DataFrame:
    """De fyldte handler som tabel. Kræver forudregnede handler."""
    if not g.handler_forudregnet:
        raise RuntimeError("handlerne er ikke forudregnet — optællingen simulerer ingen")
    sfx = f"{regel}_{int(maal_r)}R"
    t = g.lys.iloc[fyldt]
    r_b = t[f"R_brutto_{sfx}"].to_numpy(dtype=float)
    tv = t[f"tvetydig_{sfx}"].to_numpy(dtype=bool)
    omk = t["omk_R"].to_numpy(dtype=float)
    koder = t[f"udfald_{sfx}"].to_numpy()
    if (koder == 0).any():
        raise RuntimeError(f"{int((koder == 0).sum())} rækker har ingen forudregnet handel "
                           f"({sfx}) — kun gyldige lys med fyld er forudregnet")
    udfald = np.array([KODE_UDFALD[int(k)] for k in koder], dtype=object)
    r_bedste = np.where(tv, maal_r, r_b)
    return pd.DataFrame({
        "raekke": fyldt, "dag": t["dag"].to_numpy(),
        "side": np.where(t["long"].to_numpy(dtype=bool), "long", "short"),
        "udfald": udfald, "R_brutto": r_b, "R_netto": r_b - omk,
        "tvetydig": tv, "udfald_bedste": np.where(tv, MAAL, udfald),
        "R_netto_bedste": r_bedste - omk,
        "risiko_pt": t["risiko_pt"].to_numpy(dtype=float),
        "kontrakter": t["kontrakter"].to_numpy(dtype=float), "omk_R": omk,
    })


# ---------------------------------------------------------------------------
# §6: nulmodellen N-alm
# ---------------------------------------------------------------------------

@dataclass
class Matching:
    """For én HTF: cellerne (ET-dag, tilstand) med k signaler uden væge, og
    nulkandidaterne i hver celle. Fast gennem alle gentagelser."""
    k: np.ndarray
    kandidater: list[np.ndarray]
    celler_for_faa_n: int
    dage_for_faa_n: int
    dage_n: int


def matching(g: Grundlag, htf: str) -> Matching:
    """§6: k_d pr. ET-dag og HTF-tilstand (læsning 9) og dagens nulkandidater i samme
    celle. Nulkandidaterne er lys med væge i trendens retning med plads til stop og
    ``kontrakter ≥ 1`` — samme ``gyldighed`` som signalerne."""
    lys = g.lys
    gyld = g.gyldig[htf]["gyldig"]
    uden = lys["uden_vaege"].to_numpy(dtype=bool)
    sig, kand = np.flatnonzero(gyld & uden), np.flatnonzero(gyld & ~uden)
    dag = lys["dag"].to_numpy()
    st = lys[f"tilstand_{htf}"].to_numpy()
    celle_sig = pd.Series(sig).groupby([dag[sig], st[sig]]).size()
    kand_df = pd.DataFrame({"r": kand, "dag": dag[kand], "st": st[kand]})
    grupper = {key: grp["r"].to_numpy(dtype=np.int64)
               for key, grp in kand_df.groupby(["dag", "st"], sort=False)}
    k_liste, kand_liste, for_faa_dage = [], [], set()
    for (d, s_), k in celle_sig.items():
        c = grupper.get((d, s_), np.zeros(0, dtype=np.int64))
        k_liste.append(int(k))
        kand_liste.append(c)
        if len(c) < k:
            for_faa_dage.add(d)
    k_arr = np.asarray(k_liste, dtype=np.int64)
    return Matching(k=k_arr, kandidater=kand_liste,
                    celler_for_faa_n=int(sum(len(c) < k for c, k in zip(kand_liste, k_arr))),
                    dage_for_faa_n=len(for_faa_dage),
                    dage_n=int(pd.Series(dag[sig]).nunique()))


def nalm_traek(mt: Matching, rng: np.random.Generator) -> np.ndarray:
    """Én trækning: k lys uden tilbagelægning pr. celle, alle hvis cellen har færre."""
    dele = []
    for k, c in zip(mt.k, mt.kandidater):
        if len(c) <= k:
            dele.append(c)
        else:
            dele.append(rng.choice(c, size=int(k), replace=False))
    if not dele:
        return np.zeros(0, dtype=np.int64)
    return np.sort(np.concatenate(dele)).astype(np.int64)


def nalm_rng(rep: int, htf: str) -> np.random.Generator:
    """Daily og 4H trækkes hver for sig, §6 — hver sin strøm pr. gentagelse."""
    return np.random.default_rng([NALM_SEED, rep, HTF_NAVNE.index(htf)])


# ---------------------------------------------------------------------------
# Nøgletal — middel-R kun i den rigtige kørsel og i gentagelserne, aldrig i optællingen
# ---------------------------------------------------------------------------

def middel_R(g: Grundlag, fyldt: np.ndarray, regel: str, maal_r: float
             ) -> tuple[float, float]:
    """(middel netto-R forsigtigt, i bedste fald) — gentagelsernes eneste tal."""
    if len(fyldt) == 0:
        return float("nan"), float("nan")
    sfx = f"{regel}_{int(maal_r)}R"
    r_b = g.lys[f"R_brutto_{sfx}"].to_numpy(dtype=float)[fyldt]
    tv = g.lys[f"tvetydig_{sfx}"].to_numpy(dtype=bool)[fyldt]
    omk = g.lys["omk_R"].to_numpy(dtype=float)[fyldt]
    return float((r_b - omk).mean()), float((np.where(tv, maal_r, r_b) - omk).mean())


def noegletal(handler: pd.DataFrame, bedste: bool = False) -> dict:
    """§10's kolonner for én handelstabel.

    ``win_rate_pct`` er mål ramt / handler_n (§10's formel). Brutto og netto er det samme
    tal efter den formel; de står begge, som §10 beder om.
    """
    n = len(handler)
    r_net = handler["R_netto_bedste" if bedste else "R_netto"].to_numpy(dtype=float)
    udfald = handler["udfald_bedste" if bedste else "udfald"].to_numpy()
    r_brutto = r_net + handler["omk_R"].to_numpy(dtype=float)
    row = {"handler_n": n, "dage_med_handel_n": int(pd.Series(handler["dag"]).nunique()),
           "tvetydig_n": int(handler["tvetydig"].sum()),
           "censureret_n": int((udfald == CENSURERET).sum())}
    if n == 0:
        for k in ("middel_R_brutto", "middel_R_netto", "middel_R_netto_ci95_lo",
                  "middel_R_netto_ci95_hi", "win_rate_pct_brutto", "win_rate_pct_netto",
                  "win_rate_ci95_lo_pct", "win_rate_ci95_hi_pct", "udfald_maal_pct",
                  "udfald_stop_pct", "udfald_tidsexit_pct"):
            row[k] = float("nan")
        return row
    row["middel_R_brutto"] = float(r_brutto.mean())
    row["middel_R_netto"] = float(r_net.mean())
    lo, hi = mean_ci_t(r_net) if n >= 2 else (float("nan"), float("nan"))
    row["middel_R_netto_ci95_lo"], row["middel_R_netto_ci95_hi"] = lo, hi
    vundet = int((udfald == MAAL).sum())
    w_lo, w_hi = wilson_interval(vundet, n)
    row["win_rate_pct_brutto"] = row["win_rate_pct_netto"] = 100 * vundet / n
    row["win_rate_ci95_lo_pct"], row["win_rate_ci95_hi_pct"] = 100 * w_lo, 100 * w_hi
    row["udfald_maal_pct"] = 100 * vundet / n
    row["udfald_stop_pct"] = 100 * int((udfald == STOP).sum()) / n
    row["udfald_tidsexit_pct"] = 100 * int(np.isin(udfald, (TIDSEXIT, CENSURERET)).sum()) / n
    return row


def forskel_ci(a, b) -> tuple[float, float, float]:
    """(forskel, CI95 lo, hi) på middelværdierne af to uafhængige stikprøver, Welch."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if len(a) < 2 or len(b) < 2:
        return float("nan"), float("nan"), float("nan")
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    se = math.sqrt(va + vb)
    d = float(a.mean() - b.mean())
    if se == 0:
        return d, float("nan"), float("nan")
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    tcrit = t_critical(df, 0.05)
    return d, d - tcrit * se, d + tcrit * se


# ---------------------------------------------------------------------------
# §7 og §8: Westfall-Young og beslutningsreglen
# ---------------------------------------------------------------------------

def westfall_young(observeret: dict, null: dict) -> dict:
    """§7, standardiseret maks-statistik.

    ``observeret`` er {variant: m_v}, ``null`` {variant: array af m_v^(r)}. For hver
    variant: ``med_v`` og ``sd_v`` (ddof = 1, læsning 12) over gentagelserne, ``t_v =
    (m_v − med_v) / sd_v``, og ``p_FWE,v = (1 + #{r: maks^(r) ≥ t_v}) / (1 + R)`` med
    ``maks^(r) = max_v (m_v^(r) − med_v) / sd_v``.
    """
    v = list(observeret)
    M = np.column_stack([np.asarray(null[x], dtype=float) for x in v])
    R = M.shape[0]
    med = np.nanmedian(M, axis=0)
    sd = np.nanstd(M, axis=0, ddof=1)
    Z = (M - med) / sd
    maks = np.nanmax(Z, axis=1)
    m_obs = np.array([observeret[x] for x in v], dtype=float)
    t = (m_obs - med) / sd
    p = (1 + (maks[:, None] >= t[None, :]).sum(axis=0)) / (1 + R)
    return {"varianter": v, "R": R, "maks": maks,
            "pr_variant": {x: {"med": float(med[i]), "sd": float(sd[i]), "t": float(t[i]),
                               "p_FWE": float(p[i]),
                               "p5": float(np.nanpercentile(M[:, i], 5)),
                               "p50": float(np.nanpercentile(M[:, i], 50)),
                               "p95": float(np.nanpercentile(M[:, i], 95))}
                           for i, x in enumerate(v)}}


def beslutning(raekker: dict, alfa: float = 0.05) -> dict:
    """§8, mekanisk. ``raekker`` er {variant: {"p_FWE", "middel_R_netto",
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
                "tekst": "Kandidat 2 parkeres: lys uden væge tilføjer intet målbart"}
    return {"raekke": 4, "variant": None, "kandidater": [], "tekst": "Kandidat 2 parkeres"}


def mde(handler_n: int, maal_r: float, z: float = Z_SIDAK12) -> float:
    """§7: ``(z_α + z_0,20) × σ / √n``."""
    return z * SIGMA_R[maal_r] / math.sqrt(handler_n) if handler_n > 0 else float("inf")


# ---------------------------------------------------------------------------
# §11.4: optællingen uden udfald
# ---------------------------------------------------------------------------

def _p(x, q) -> float:
    x = np.asarray(x, dtype=float)
    return float(np.percentile(x, q)) if len(x) else float("nan")


def skyggefyld_pct(g: Grundlag, htf: str, raekker: np.ndarray, n_lys: int,
                   regel: str) -> float:
    """Læsning 11: andelen af signaler hvis linje nås inden for N lys, hver for sig."""
    if len(raekker) == 0:
        return float("nan")
    n_slut = ordre_slut(g.lys, htf, n_lys)[raekker]
    fyld = g.lys[f"{regel}_tid"].to_numpy(dtype=np.int64)[raekker]
    return 100 * float((fyld < n_slut).mean())


def trenddaekning(g: Grundlag, htf: str) -> dict:
    """§9: andel af RTH-dage med op-, ned- og udefineret trend ved lukningen af vinduets
    første lys (08:35 CT), dage hvor tilstanden er en anden ved vinduets slutning (kun
    muligt på 4H), og andel af vinduets lys (uden doji) pr. tilstand."""
    b = g.htf[htf]
    luk_ns, st_arr = _ns(b["luk"]), b["tilstand"].to_numpy()
    d = pd.DatetimeIndex(g.rth_dage)
    start = _ns((d + pd.Timedelta(hours=8, minutes=35)).tz_localize(CT).tz_convert("UTC"))
    slut, _ = _dag_tider(d)
    st0, _ = tilstand_ved(start, luk_ns, st_arr)
    st1, _ = tilstand_ved(slut, luk_ns, st_arr)
    st_lys = g.lys[f"tilstand_{htf}"].to_numpy()
    ud = {"dage_n": int(len(d))}
    for navn, v in (("op", OP), ("ned", NED), ("udefineret", UDEF)):
        ud[f"dage_{navn}_pct"] = 100 * float((st0 == v).mean())
        ud[f"lys_{navn}_pct"] = 100 * float((st_lys == v).mean())
    ud["dage_med_skift_i_vinduet_n"] = int((st0 != st1).sum())
    return ud


def sizing_raekke(lys: pd.DataFrame, raekker: np.ndarray) -> dict:
    """§9's omkostnings- og størrelseskolonner over signalerne."""
    t = lys.iloc[raekker]
    omk = t["omk_R"].to_numpy(dtype=float)
    row = {"risiko_pt_p10": _p(t["risiko_pt"], 10), "risiko_pt_p50": _p(t["risiko_pt"], 50),
           "risiko_pt_p90": _p(t["risiko_pt"], 90), "omk_R_netto_p50": _p(omk, 50),
           "omk_R_netto_p90": _p(omk, 90),
           "kontrakter_p50": _p(t["kontrakter"], 50),
           "kontrakter_maks": float(t["kontrakter"].max()) if len(t) else float("nan"),
           "kontrakter_loftet_n": int((t["kontrakter_raa"] > KONTRAKTER_LOFT).sum())}
    for m in MAAL_R:
        row[f"be_WR_pct_netto_p50_{int(m)}R"] = (
            100 * breakeven_win_rate(m, 1.0, row["omk_R_netto_p50"]) if len(t)
            else float("nan"))
    return row


def tael_signaler(g: Grundlag, htf: str) -> dict:
    """§9's udfaldne signaler for én HTF, over lys uden væge i vinduet."""
    gy = g.gyldig[htf]
    uden = g.lys["uden_vaege"].to_numpy(dtype=bool)
    ud = {"lys_uden_vaege_i_vindue_n": int(uden.sum())}
    for navn in ("udefineret", "mod_trenden", "ingen_stopplads", "rul", "kontrakter_nul"):
        ud[f"{navn}_n"] = int((gy[navn] & uden).sum())
    ud["sprunget_over_udefineret_n"] = ud.pop("udefineret_n")
    ud["ikke_i_trendens_retning_n"] = ud.pop("mod_trenden_n")
    ud["sprunget_over_ingen_stopplads_n"] = ud.pop("ingen_stopplads_n")
    ud["sprunget_over_rul_n"] = ud.pop("rul_n")
    ud["afvist_kontrakter_nul_n"] = ud.pop("kontrakter_nul_n")
    ud["signaler_n"] = int((gy["gyldig"] & uden).sum())
    ud["signaler_long_n"] = int((gy["gyldig"] & uden & g.lys["long"].to_numpy()).sum())
    ud["signaler_short_n"] = ud["signaler_n"] - ud["signaler_long_n"]
    ud["dage_med_signal_n"] = int(pd.Series(
        g.lys["dag"].to_numpy()[gy["gyldig"] & uden]).nunique())
    return ud


def optaelling(g: Grundlag, nalm_rep: int = 0) -> dict:
    """§11.4. Pr. variant: signaler, handler_n, dage med handel og de udfaldne signaler.
    Det samme for N-alm i én gentagelse. Ingen handel simuleres; ingen R regnes."""
    ud = {"varianter": [], "signaler": {}, "trend": {}, "sizing": {}, "nalm": {},
          "nalm_varianter": []}
    for htf in HTF_NAVNE:
        gy = g.gyldig[htf]["gyldig"]
        uden = g.lys["uden_vaege"].to_numpy(dtype=bool)
        sig = np.flatnonzero(gy & uden)
        ud["signaler"][htf] = tael_signaler(g, htf)
        ud["trend"][htf] = trenddaekning(g, htf)
        ud["sizing"][htf] = sizing_raekke(g.lys, sig)
        res = koer_signalsaet(g, htf, sig)
        for (n_lys, regel), r in res.items():
            for m in MAAL_R:
                handler_n = len(r.fyldt)
                ud["varianter"].append({
                    "htf": htf, "n_lys": n_lys, "maal_R": m, "regel": regel,
                    "signaler_n": len(sig), "handler_n": handler_n,
                    "dage_med_handel_n": int(pd.Series(
                        g.lys["dag"].to_numpy()[r.fyldt]).nunique()),
                    "strejf_n": len(r.strejf) if regel == "gennem" else 0,
                    "skyggefyld_pct": skyggefyld_pct(g, htf, sig, n_lys, regel),
                    **r.tael,
                    "MDE_R_sidak12": mde(handler_n, m),
                    "MDE_R_ukorr": mde(handler_n, m, Z_UKORR),
                    "min_handler_n": MIN_HANDLER[m],
                    "betingelse_ok": bool(handler_n >= MIN_HANDLER[m]
                                          and mde(handler_n, m) <= MDE_GRAENSE_R),
                })
        mt = matching(g, htf)
        nsig = nalm_traek(mt, nalm_rng(nalm_rep, htf))
        kand_n = int((gy & ~uden).sum())
        ud["nalm"][htf] = {"kandidater_n": kand_n, "celler_n": len(mt.k),
                           "celler_for_faa_n": mt.celler_for_faa_n,
                           "dage_for_faa_kandidater_n": mt.dage_for_faa_n,
                           "dage_med_signal_n": mt.dage_n,
                           "trukne_n": len(nsig), "signaler_n": len(sig)}
        res_n = koer_signalsaet(g, htf, nsig)
        for (n_lys, regel), r in res_n.items():
            ud["nalm_varianter"].append({
                "htf": htf, "n_lys": n_lys, "regel": regel, "signaler_n": len(nsig),
                "handler_n": len(r.fyldt),
                "dage_med_handel_n": int(pd.Series(
                    g.lys["dag"].to_numpy()[r.fyldt]).nunique()),
                "skyggefyld_pct": skyggefyld_pct(g, htf, nsig, n_lys, regel),
                **r.tael})
    return ud


# ---------------------------------------------------------------------------
# Gentagelserne — parallelt, hver arbejder får grundlaget én gang
# ---------------------------------------------------------------------------

_G: Grundlag | None = None
_MT: dict[str, Matching] | None = None


def _init_arbejder(g: Grundlag, mt: dict[str, Matching]) -> None:
    global _G, _MT
    _G, _MT = g, mt


def nalm_gentagelse(rep: int, g: Grundlag | None = None,
                    mt: dict[str, Matching] | None = None) -> dict:
    """Én N-alm-gentagelse: {(variant, regel): (handler_n, m_forsigtig, m_bedste)}.
    Samme trækning for begge fyldningsregler, alle N og begge mål, §6."""
    g = g if g is not None else _G
    mt = mt if mt is not None else _MT
    ud = {}
    for htf in HTF_NAVNE:
        nsig = nalm_traek(mt[htf], nalm_rng(rep, htf))
        res = koer_signalsaet(g, htf, nsig)
        for (n_lys, regel), r in res.items():
            for m in MAAL_R:
                m_f, m_b = middel_R(g, r.fyldt, regel, m)
                ud[((htf, n_lys, m), regel)] = (len(r.fyldt), m_f, m_b)
    return ud


def _gentagelse_med_tid(rep: int) -> tuple[int, float, dict]:
    t0 = time.perf_counter()
    r = nalm_gentagelse(rep)
    return rep, time.perf_counter() - t0, r


def koer_nalm(g: Grundlag, n_reps: int, max_workers: int | None = None,
              start: int = 0) -> tuple[list[dict], dict]:
    """``n_reps`` gentagelser over kernerne. Returnerer (gentagelser i rækkefølge, tid)."""
    mt = {htf: matching(g, htf) for htf in HTF_NAVNE}
    n_workere = max_workers or (os.cpu_count() or 1)
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=n_workere, initializer=_init_arbejder,
                             initargs=(g, mt)) as pool:
        res = list(pool.map(_gentagelse_med_tid, range(start, start + n_reps)))
    vaeg = time.perf_counter() - t0
    res.sort(key=lambda x: x[0])
    return [r for _, _, r in res], {
        "vaeg_s": vaeg, "n_workere": n_workere, "cpu_count": os.cpu_count(),
        "middel_s_pr_gentagelse": float(np.mean([t for _, t, _ in res])) if res else 0.0}


# ---------------------------------------------------------------------------
# Den rigtige kørsel, §7-§10
# ---------------------------------------------------------------------------

def koer_virkelig(g: Grundlag) -> dict:
    """De 12 varianter med begge fyldningsregler: handelstabeller og strejf."""
    ud = {}
    for htf in HTF_NAVNE:
        uden = g.lys["uden_vaege"].to_numpy(dtype=bool)
        sig = np.flatnonzero(g.gyldig[htf]["gyldig"] & uden)
        res = koer_signalsaet(g, htf, sig)
        for (n_lys, regel), r in res.items():
            for m in MAAL_R:
                ud[((htf, n_lys, m), regel)] = {
                    "handler": handelstabel(g, r.fyldt, regel, m),
                    "strejf": (handelstabel(g, r.strejf, "beroering", m)
                               if regel == "gennem" else None),
                    "tael": r.tael, "signaler": sig}
    return ud


def _wy_for(virkelig: dict, gentagelser: list[dict], regel: str, bedste: bool) -> dict:
    obs = {v: noegletal(virkelig[(v, regel)]["handler"], bedste)["middel_R_netto"]
           for v in VARIANTER}
    null = {v: np.array([rep[(v, regel)][2 if bedste else 1] for rep in gentagelser])
            for v in VARIANTER}
    return westfall_young(obs, null)


def afgoerelse(virkelig: dict, gentagelser: list[dict], regel: str, bedste: bool) -> dict:
    wy = _wy_for(virkelig, gentagelser, regel, bedste)
    raekker = {}
    for v in VARIANTER:
        n = noegletal(virkelig[(v, regel)]["handler"], bedste)
        raekker[v] = {**n, **{f"N_alm_{k}": x for k, x in wy["pr_variant"][v].items()},
                      "t_v": wy["pr_variant"][v]["t"], "p_FWE": wy["pr_variant"][v]["p_FWE"]}
    return {"wy": wy, "raekker": raekker, "beslutning": beslutning(raekker)}


def diagnoser(g: Grundlag, virkelig: dict, gentagelser: list[dict]) -> dict:
    """§9: side, år, fyldningsrate, trend, udfaldne signaler, sizing, strejf."""
    side, aar, strejf = [], [], []
    for v in VARIANTER:
        h = virkelig[(v, "gennem")]["handler"]
        lo = h[h["side"] == "long"]["R_netto"]
        sh = h[h["side"] == "short"]["R_netto"]
        d, dlo, dhi = forskel_ci(lo, sh)
        side.append({"variant": v, "long_n": len(lo), "short_n": len(sh),
                     "long_middel_R_netto": float(lo.mean()) if len(lo) else float("nan"),
                     "short_middel_R_netto": float(sh.mean()) if len(sh) else float("nan"),
                     "forskel": d, "forskel_ci95_lo": dlo, "forskel_ci95_hi": dhi})
        aarstal = pd.DatetimeIndex(h["dag"]).year if len(h) else np.zeros(0)
        for a in AAR_LISTE:
            sub = h[np.asarray(aarstal) == a]
            aar.append({"variant": v, "aar": a, **noegletal(sub)})
        s = virkelig[(v, "gennem")]["strejf"]
        strejf.append({"variant": v, "strejf_n": len(s),
                       "strejf_hvis_fyldt_middel_R_netto":
                           float(s["R_netto"].mean()) if len(s) else float("nan")})
    return {"side": side, "aar": aar, "strejf": strejf}


def koer(n_reps: int = NALM_REPS, max_workers: int | None = None) -> dict:
    """§7-§10. Regressionstjekket først — afviger det, køres intet."""
    reg = regressionstjek_motor()
    if not reg["ok"]:
        raise RuntimeError(f"regressionstjekket afveg, kørslen sker ikke: {reg}")
    df = mnq()
    g = byg_grundlag(df)
    virkelig = koer_virkelig(g)
    gentagelser, tid = koer_nalm(g, n_reps, max_workers)
    afg = {navn: afgoerelse(virkelig, gentagelser, regel, bedste)
           for navn, regel, bedste in (("gennem", "gennem", False),
                                       ("beroering", "beroering", False),
                                       ("gennem_bedste_fald", "gennem", True))}
    return {"g": g, "virkelig": virkelig, "gentagelser": gentagelser, "tid": tid,
            "afgoerelse": afg, "diagnoser": diagnoser(g, virkelig, gentagelser),
            "optaelling": optaelling(g), "regression": reg, "n_reps": n_reps,
            "n_1m": len(df)}


# ---------------------------------------------------------------------------
# Rapporten, §10
# ---------------------------------------------------------------------------

def _t(v, nd: int = 3) -> str:
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "—"
    if isinstance(v, (bool, np.bool_)):
        return "ja" if v else "nej"
    if isinstance(v, (int, np.integer)):
        return f"{int(v):,}".replace(",", ".")
    return f"{v:.{nd}f}".replace(".", ",")


def _vnavn(v) -> str:
    return f"{v[0]} · {v[1]} lys · {int(v[2])}R"


def _rel(sti: Path) -> str:
    return Path(sti).resolve().relative_to(ROOT.resolve()).as_posix()


def _orden() -> list:
    return [HOVEDVARIANT] + [v for v in VARIANTER if v != HOVEDVARIANT]


def hovedtabel_md(afg: dict) -> str:
    linjer = ["| variant | handler_n | dage | tvetydig_n | censureret_n | middel_R_brutto | "
              "middel_R_netto | CI95 | win_rate_pct_brutto | win_rate_pct_netto [Wilson] | "
              "mål/stop/tid_pct | N_alm p5/p50/p95 | t_v | p_FWE |", "|" + "---|" * 14]
    for v in _orden():
        r = afg["raekker"][v]
        linjer.append(
            f"| {_vnavn(v)} | {_t(r['handler_n'])} | {_t(r['dage_med_handel_n'])} | "
            f"{_t(r['tvetydig_n'])} | {_t(r['censureret_n'])} | {_t(r['middel_R_brutto'], 4)} | "
            f"{_t(r['middel_R_netto'], 4)} | [{_t(r['middel_R_netto_ci95_lo'], 4)}; "
            f"{_t(r['middel_R_netto_ci95_hi'], 4)}] | {_t(r['win_rate_pct_brutto'], 1)} | "
            f"{_t(r['win_rate_pct_netto'], 1)} [{_t(r['win_rate_ci95_lo_pct'], 1)}; "
            f"{_t(r['win_rate_ci95_hi_pct'], 1)}] | {_t(r['udfald_maal_pct'], 1)}/"
            f"{_t(r['udfald_stop_pct'], 1)}/{_t(r['udfald_tidsexit_pct'], 1)} | "
            f"{_t(r['N_alm_p5'], 4)}/{_t(r['N_alm_p50'], 4)}/{_t(r['N_alm_p95'], 4)} | "
            f"{_t(r['t_v'], 2)} | {_t(r['p_FWE'], 4)} |")
    return "\n".join(linjer) + "\n"


def _beslutning_md(navn: str, afg: dict) -> str:
    b = afg["beslutning"]
    v = f" Frosset variant: **{_vnavn(b['variant'])}**." if b["variant"] else ""
    return f"**{navn}: række {b['raekke']}: {b['tekst']}.**{v}\n"


def lang_tabel(res: dict) -> pd.DataFrame:
    rows = []
    for navn, afg in res["afgoerelse"].items():
        for v in VARIANTER:
            rows.append({"afgoerelse": navn, "htf": v[0], "n_lys": v[1], "maal_R": v[2],
                         "side": "alle", "periode": "2019-2023", **afg["raekker"][v]})
    for r in res["diagnoser"]["aar"]:
        v = r["variant"]
        rows.append({"afgoerelse": "gennem", "htf": v[0], "n_lys": v[1], "maal_R": v[2],
                     "side": "alle", "periode": str(r["aar"]),
                     **{k: x for k, x in r.items() if k not in ("variant", "aar")}})
    for r in res["diagnoser"]["side"]:
        v = r["variant"]
        rows.append({"afgoerelse": "gennem", "htf": v[0], "n_lys": v[1], "maal_R": v[2],
                     "side": "long_mod_short", "periode": "2019-2023",
                     **{k: x for k, x in r.items() if k != "variant"}})
    for r in res["diagnoser"]["strejf"]:
        v = r["variant"]
        rows.append({"afgoerelse": "gennem", "htf": v[0], "n_lys": v[1], "maal_R": v[2],
                     "side": "strejf", "periode": "2019-2023",
                     **{k: x for k, x in r.items() if k != "variant"}})
    optael = optaelling_csv(res["optaelling"]).assign(afgoerelse="optaelling")
    return pd.concat([pd.DataFrame(rows), optael], ignore_index=True)


def skriv_md(res: dict, meta: dict) -> str:
    afg = res["afgoerelse"]
    d = res["diagnoser"]
    dele = [
        "# B4 kandidat 2 — Nowick: lys uden væge i trendens retning\n",
        f"Kørt {meta['koert_utc']} UTC fra commit `{meta['head'][:7]}`. Præregistrering "
        f"`{_rel(PREREG)}` (commit `{meta['commits'][_rel(PREREG)][:7]}`). Kode "
        f"`{_rel(Path(__file__))}` (commit `{meta['commits'][_rel(Path(__file__))][:7]}`).\n",
        f"Serie: MNQ.v.0 1m, {trinA.MNQ_START.date()} → 2023-12-31, {res['n_1m']} 1m-barer. "
        f"12 varianter. N-alm: {res['n_reps']} gentagelser.\n",
        "**Regressionstjek: OK.**\n",
        "## Hovedtabel — gennemhandling, forsigtigt (afgørelsen tages her)\n",
        hovedtabel_md(afg["gennem"]),
        "## Afgørelsen, §8, mekanisk\n",
        _beslutning_md("Gennemhandling", afg["gennem"]),
        _beslutning_md("Fyld ved berøring (diagnose)", afg["beroering"]),
        _beslutning_md("Bedste fald, tvetydige minutter (diagnose)",
                       afg["gennem_bedste_fald"]),
    ]
    if afg["beroering"]["beslutning"]["raekke"] != afg["gennem"]["beslutning"]["raekke"]:
        dele.append("Afgørelsen er en anden ved berøring: resultatet er **afhængigt af "
                    "køplacering**, §9.\n")
    if (afg["gennem_bedste_fald"]["beslutning"]["raekke"]
            != afg["gennem"]["beslutning"]["raekke"]):
        dele.append("Afgørelsen er en anden i bedste fald: resultatet er **afhængigt af "
                    "data under minutniveau**, §9.\n")
    dele += [
        "## Fyld ved berøring — samme tabel\n", hovedtabel_md(afg["beroering"]),
        "## Strejf\n",
        "| variant | strejf_n | strejf_hvis_fyldt_middel_R_netto |\n|---|---|---|\n" +
        "".join(f"| {_vnavn(r['variant'])} | {_t(r['strejf_n'])} | "
                f"{_t(r['strejf_hvis_fyldt_middel_R_netto'], 4)} |\n" for r in d["strejf"]),
        "## Long mod short\n",
        "| variant | long_n | short_n | long R_netto | short R_netto | forskel [CI95] |\n"
        "|---|---|---|---|---|---|\n" +
        "".join(f"| {_vnavn(r['variant'])} | {_t(r['long_n'])} | {_t(r['short_n'])} | "
                f"{_t(r['long_middel_R_netto'], 4)} | {_t(r['short_middel_R_netto'], 4)} | "
                f"{_t(r['forskel'], 4)} [{_t(r['forskel_ci95_lo'], 4)}; "
                f"{_t(r['forskel_ci95_hi'], 4)}] |\n" for r in d["side"]),
        "## Pr. år — middel_R_netto (handler_n)\n",
        aarstabel_md(d["aar"]),
        "## Optælling og øvrige diagnoser, §9\n",
        optaelling_md(res["optaelling"], res["g"], meta, kun_tabeller=True),
        "## Efter kørslen, §13\n",
        "Stop. Ingen ændring af definitioner, ingen nye varianter, ingen forslag.\n",
        f"Alle tal: `{_rel(OUT / 'b4_k2_nowick.csv')}`.\n",
    ]
    return "\n".join(dele)


def aarstabel_md(aar: list[dict]) -> str:
    linjer = ["| variant | " + " | ".join(str(a) for a in AAR_LISTE) + " |",
              "|" + "---|" * (1 + len(AAR_LISTE))]
    pr_v: dict = {}
    for r in aar:
        pr_v.setdefault(r["variant"], {})[r["aar"]] = r
    for v in _orden():
        celler = [f"{_t(pr_v[v][a]['middel_R_netto'], 3)} ({_t(pr_v[v][a]['handler_n'])})"
                  for a in AAR_LISTE]
        linjer.append(f"| {_vnavn(v)} | " + " | ".join(celler) + " |")
    return "\n".join(linjer) + "\n"


def _arbejdskopi(stier) -> str:
    """Hvilke af ``stier`` der afviger fra HEAD — skrevet i rapportens hoved."""
    rel = [_rel(s) for s in stier]
    ud = _git("status", "--porcelain", "--", *rel).stdout.strip()
    if not ud:
        return "kode, tests og præregistrering committet og uændrede"
    return "med ændringer i arbejdskopien: " + ", ".join(
        f"`{linje[3:]}`" for linje in ud.splitlines())


# ---------------------------------------------------------------------------
# §11.3: regressionstjek
# ---------------------------------------------------------------------------

@contextmanager
def _simuler_handel_med_maal(maal_r: float):
    """``trinA.handler_for_variant`` kalder ``simuler_handel`` uden mål; her sendes målet
    eksplicit, så tjekket viser at parameteren — ikke kun standardværdien — giver 2R."""
    oprindelig = trinA.simuler_handel
    trinA.simuler_handel = partial(oprindelig, maal_r=maal_r)
    try:
        yield
    finally:
        trinA.simuler_handel = oprindelig


def regressionstjek_motor(df: pd.DataFrame | None = None) -> dict:
    """§11.3, anden del: den udvidede ``simuler_handel`` gengiver motorrettelsens tal for
    buffer 10% / BE +1,2R — én gang med standardværdien og én gang med ``maal_r=2``."""
    df = mnq() if df is None else df
    bars = resample.aggregate(df, k1.BAR_MIN)
    zoner = trinA.sizing_ekte(k1.zoner_v2(bars, trinA.BUFFER_VARIANTER["buffer_10"]))
    ud = {}
    for navn, maal in (("standard", None), ("eksplicit_2R", 2.0)):
        if maal is None:
            handler, _, _ = trinA.handler_for_variant(df, zoner, 1.2)
        else:
            with _simuler_handel_med_maal(maal):
                handler, _, _ = trinA.handler_for_variant(df, zoner, 1.2)
        m = float(handler["R_netto"].mean())
        ud[navn] = {"handler_n": len(handler), "middel_R_netto": m,
                    "ok": len(handler) == REGRESSION_HANDLER_N
                    and round(m, 4) == REGRESSION_MIDDEL_R_NETTO}
    ud["ok"] = all(x["ok"] for x in ud.values() if isinstance(x, dict))
    return ud


# ---------------------------------------------------------------------------
# §11.4 og §11.5: optællingen og tidsmålingen — uden R
# ---------------------------------------------------------------------------

def optaelling_md(o: dict, g: Grundlag, meta: dict, kun_tabeller: bool = False) -> str:
    hoved = [
        "# B4 kandidat 2 — optælling uden udfald (§11.4)\n",
        f"Kørt {meta['koert_utc']} UTC fra commit `{meta['head'][:7]}`, "
        f"{_arbejdskopi(COMMITTEDE)}. **Ingen handel er simuleret; intet R, ingen "
        f"vinderrate og intet udfald er regnet.**\n",
    ]
    dele = [] if kun_tabeller else hoved
    dele += [
        f"Serie: MNQ.v.0 1m gennem `data.holdout.load_in_sample`, "
        f"{trinA.MNQ_START.date()} → 2023-12-31. {g.n_1m} 1m-barer → {g.n_5m} 5m-lys. "
        f"{len(g.rth_dage)} RTH-dage. 5m-lys i vinduet uden doji: {len(g.lys)}.\n",
        "## Kontraktskift, §4b\n",
        f"{len(g.ruller)} ruller. Tid i CT:\n",
        "| tid_ct | ugedag | spring_pt |\n|---|---|---|\n" +
        "".join(f"| {r.tid_ct} | {r.ugedag_ct} | {_t(float(r.spring_pt), 2)} |\n"
                for r in g.ruller.itertuples()),
        "## HTF-lys og trenddækning, §4b og §9\n",
        "| HTF | lys_n | 1m uden for et lys | brud op | brud ned | konflikt (begge) | "
        "dage op % | dage ned % | dage udef. % | lys op % | lys ned % | lys udef. % | "
        "dage med skift i vinduet |", "|" + "---|" * 13,
    ]
    for htf in HTF_NAVNE:
        ht = {"lys_n": len(g.htf[htf]), "udenfor_1m_n": None, "brud_op_n": None,
              "brud_ned_n": None, "konflikt_n": None, **g.htf_tael.get(htf, {})}
        tr = o["trend"][htf]
        dele.append(
            f"| {htf} | {_t(ht['lys_n'])} | {_t(ht['udenfor_1m_n'])} | {_t(ht['brud_op_n'])} | "
            f"{_t(ht['brud_ned_n'])} | {_t(ht['konflikt_n'])} | {_t(tr['dage_op_pct'], 1)} | "
            f"{_t(tr['dage_ned_pct'], 1)} | {_t(tr['dage_udefineret_pct'], 1)} | "
            f"{_t(tr['lys_op_pct'], 1)} | {_t(tr['lys_ned_pct'], 1)} | "
            f"{_t(tr['lys_udefineret_pct'], 1)} | {_t(tr['dage_med_skift_i_vinduet_n'])} |")
    dele += ["", "## Signaler og udfaldne signaler, §9\n",
             "Over 5m-lys uden væge i vinduet. Hvert lys tælles ét sted (læsning 15).\n",
             "| HTF | uden væge | udefineret trend | ikke i trendens retning | ingen stopplads | "
             "rul | kontrakter nul | **signaler** | long | short | dage med signal |",
             "|" + "---|" * 11]
    for htf in HTF_NAVNE:
        s = o["signaler"][htf]
        dele.append(
            f"| {htf} | {_t(s['lys_uden_vaege_i_vindue_n'])} | {_t(s['sprunget_over_udefineret_n'])} | "
            f"{_t(s['ikke_i_trendens_retning_n'])} | {_t(s['sprunget_over_ingen_stopplads_n'])} | "
            f"{_t(s['sprunget_over_rul_n'])} | {_t(s['afvist_kontrakter_nul_n'])} | "
            f"**{_t(s['signaler_n'])}** | {_t(s['signaler_long_n'])} | "
            f"{_t(s['signaler_short_n'])} | {_t(s['dage_med_signal_n'])} |")
    dele += ["", "## Pr. variant — handler og betingelsen i §7\n",
             "Gennemhandling (§4c regel 1). handler_n = dage med handel, fordi der er én "
             "handel om dagen. Mål deler fyldningerne, så 1R og 2R har samme handler_n. "
             "MDE i R, Šidák 12.\n",
             "| variant | signaler | handler_n | dage | strejf_n | skyggefyld % | ordrer | "
             "erstattet | udløbet | annull. trend | annull. vindue | MDE Šidák | ≥ krav | "
             "betingelse |", "|" + "---|" * 14]
    for r in o["varianter"]:
        if r["regel"] != "gennem":
            continue
        v = (r["htf"], r["n_lys"], r["maal_R"])
        dele.append(
            f"| {_vnavn(v)} | {_t(r['signaler_n'])} | {_t(r['handler_n'])} | "
            f"{_t(r['dage_med_handel_n'])} | {_t(r['strejf_n'])} | {_t(r['skyggefyld_pct'], 1)} | "
            f"{_t(r['ordrer_n'])} | {_t(r['erstattet_n'])} | {_t(r['udloebet_n'])} | "
            f"{_t(r['annulleret_trend_n'])} | {_t(r['annulleret_vindue_n'])} | "
            f"{_t(r['MDE_R_sidak12'], 3)} | {_t(r['min_handler_n'])} | "
            f"{'OK' if r['betingelse_ok'] else '**UNDER**'} |")
    dele += ["", "Fyld ved berøring (§9), samme signaler:\n",
             "| HTF · N | handler_n | skyggefyld % |", "|---|---|---|"]
    for r in o["varianter"]:
        if r["regel"] == "beroering" and r["maal_R"] == 1.0:
            dele.append(f"| {r['htf']} · {r['n_lys']} lys | {_t(r['handler_n'])} | "
                        f"{_t(r['skyggefyld_pct'], 1)} |")
    dele += ["", "## Sizing over signalerne, §9\n",
             "| HTF | risiko_pt p10/p50/p90 | omk_R_netto p50/p90 | be_WR_pct_netto_p50 1R/2R | "
             "kontrakter p50/maks | kontrakter_loftet_n |", "|---|---|---|---|---|---|"]
    for htf in HTF_NAVNE:
        z = o["sizing"][htf]
        dele.append(
            f"| {htf} | {_t(z['risiko_pt_p10'], 2)}/{_t(z['risiko_pt_p50'], 2)}/"
            f"{_t(z['risiko_pt_p90'], 2)} | {_t(z['omk_R_netto_p50'], 3)}/"
            f"{_t(z['omk_R_netto_p90'], 3)} | {_t(z['be_WR_pct_netto_p50_1R'], 1)}/"
            f"{_t(z['be_WR_pct_netto_p50_2R'], 1)} | {_t(z['kontrakter_p50'], 0)}/"
            f"{_t(z['kontrakter_maks'], 0)} | {_t(z['kontrakter_loftet_n'])} |")
    dele += ["", "## N-alm, én gentagelse (seed-strøm 0), §6\n",
             "| HTF | nulkandidater | celler (dag, tilstand) | celler med for få | "
             "dage med for få | trukne | signaler uden væge |", "|---|---|---|---|---|---|---|"]
    for htf in HTF_NAVNE:
        z = o["nalm"][htf]
        dele.append(f"| {htf} | {_t(z['kandidater_n'])} | {_t(z['celler_n'])} | "
                    f"{_t(z['celler_for_faa_n'])} | {_t(z['dage_for_faa_kandidater_n'])} | "
                    f"{_t(z['trukne_n'])} | {_t(z['signaler_n'])} |")
    dele += ["", "| HTF · N · regel | handler_n | dage | skyggefyld % | ordrer | erstattet |",
             "|---|---|---|---|---|---|"]
    for r in o["nalm_varianter"]:
        dele.append(f"| {r['htf']} · {r['n_lys']} lys · {r['regel']} | {_t(r['handler_n'])} | "
                    f"{_t(r['dage_med_handel_n'])} | {_t(r['skyggefyld_pct'], 1)} | "
                    f"{_t(r['ordrer_n'])} | {_t(r['erstattet_n'])} |")
    ok = all(r["betingelse_ok"] for r in o["varianter"] if r["regel"] == "gennem")
    dele += ["", "## Betingelsen i §7\n",
             ("Alle 12 varianter opfylder `handler_n ≥ 301` (1R) / `≥ 603` (2R) og MDE "
              "(Šidák 12) ≤ 0,20 R.\n" if ok else
              "**Mindst én variant ligger under kravet. Code stopper, og ejeren beslutter "
              "(§7).**\n")]
    return "\n".join(dele)


def optaelling_csv(o: dict) -> pd.DataFrame:
    rows = []
    for r in o["varianter"]:
        rows.append({"model": "uden_vaege", **r})
    for r in o["nalm_varianter"]:
        rows.append({"model": "N_alm_rep0", **r})
    for htf in HTF_NAVNE:
        rows.append({"model": "signaler", "htf": htf, **o["signaler"][htf]})
        rows.append({"model": "trend", "htf": htf, **o["trend"][htf]})
        rows.append({"model": "sizing", "htf": htf, **o["sizing"][htf]})
        rows.append({"model": "N_alm_matching", "htf": htf, **o["nalm"][htf]})
    return pd.DataFrame(rows)


def tidsmaaling(n_reps: int = 5, max_workers: int | None = None) -> dict:
    """§11.5: ét gennemløb og ``n_reps`` N-alm-gentagelser, fremskrevet til R = 500.
    Returnerer kun tider og antal — ingen R."""
    t0 = time.perf_counter()
    df = mnq()
    load_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    g = byg_grundlag(df, med_handler=False)
    grundlag_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    uden = g.lys["uden_vaege"].to_numpy(dtype=bool)
    relevante = np.flatnonzero(np.logical_or.reduce(
        [g.gyldig[n]["gyldig"] for n in HTF_NAVNE]))
    g.lys = forudregn_handler(Serie1m.af(df), g.lys, relevante)
    g.handler_forudregnet = True
    handler_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    virkelig = koer_virkelig(g)
    gennemloeb_s = time.perf_counter() - t0
    gentagelser, tid = koer_nalm(g, n_reps, max_workers)
    runder = math.ceil(NALM_REPS / tid["n_workere"])
    # Arbejderne får grundlaget ved start; den faste udgift er indlæsning, grundlag og
    # handler én gang, plus én batch-opstart (målt i vaeg_s minus selve gentagelserne).
    opstart_s = max(tid["vaeg_s"] - tid["middel_s_pr_gentagelse"]
                    * math.ceil(n_reps / tid["n_workere"]), 0.0)
    forventet = (load_s + grundlag_s + handler_s + gennemloeb_s + opstart_s
                 + tid["middel_s_pr_gentagelse"] * runder)
    return {"load_s": load_s, "grundlag_s": grundlag_s, "handler_s": handler_s,
            "forudregnede_lys_n": int(len(relevante)),
            "gennemloeb_s": gennemloeb_s, "n_reps": n_reps, "nalm": tid,
            "opstart_s": opstart_s, "runder": runder, "forventet_s": forventet,
            "handler_n_pr_variant": {f"{_vnavn(v)} · {r}": len(x["handler"])
                                     for (v, r), x in virkelig.items()},
            "gentagelser_handler_n": [{f"{_vnavn(v)} · {r}": x[0]
                                       for (v, r), x in rep.items()} for rep in gentagelser],
            "uden_vaege_lys_n": int(uden.sum())}


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "--no-optional-locks", "-C", str(ROOT), *args],
                          capture_output=True, text=True)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--regressionstjek", action="store_true",
                     help="§11.3: den udvidede simuler_handel gengiver motorrettelsen")
    grp.add_argument("--optaelling", action="store_true",
                     help="§11.4: optælling uden udfald. Skriver b4_k2_nowick_optaelling")
    grp.add_argument("--tidsmaaling", action="store_true",
                     help="§11.5: ét gennemløb og 5 N-alm-gentagelser, uden R")
    grp.add_argument("--koer", action="store_true",
                     help="§7-§10: den rigtige kørsel. Kræver ejerens godkendelse")
    ap.add_argument("--reps", type=int, default=NALM_REPS)
    ap.add_argument("--maalte-reps", type=int, default=5)
    ap.add_argument("--max-workers", type=int, default=None)
    args = ap.parse_args(argv)
    meta = {"koert_utc": pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M"),
            "head": _git("rev-parse", "HEAD").stdout.strip()}

    if args.regressionstjek:
        r = regressionstjek_motor()
        for navn in ("standard", "eksplicit_2R"):
            x = r[navn]
            print(f"simuler_handel, {navn}: handler_n {x['handler_n']} (ventet "
                  f"{REGRESSION_HANDLER_N}), middel_R_netto {x['middel_R_netto']:.4f} "
                  f"(ventet {REGRESSION_MIDDEL_R_NETTO}): {'OK' if x['ok'] else 'AFVIGER'}")
        if not r["ok"]:
            sys.exit(1)
        return

    if args.optaelling:
        df = mnq()
        g = byg_grundlag(df, med_handler=False)
        o = optaelling(g)
        md = optaelling_md(o, g, meta)
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "b4_k2_nowick_optaelling.md").write_text(md, encoding="utf-8")
        optaelling_csv(o).to_csv(OUT / "b4_k2_nowick_optaelling.csv", index=False)
        print(md)
        return

    if args.tidsmaaling:
        t = tidsmaaling(args.maalte_reps, args.max_workers)
        print(f"CPU'er: {t['nalm']['cpu_count']}, arbejdere: {t['nalm']['n_workere']}")
        print(f"Indlæsning {t['load_s']:.1f} s, grundlag {t['grundlag_s']:.1f} s, "
              f"forudregnede handler {t['handler_s']:.1f} s ({t['forudregnede_lys_n']} lys "
              f"x 2 regler x 2 mål), gennemløb af 12 varianter x 2 regler "
              f"{t['gennemloeb_s']:.1f} s")
        print(f"{t['n_reps']} N-alm-gentagelser: {t['nalm']['vaeg_s']:.1f} s væg-ur, "
              f"{t['nalm']['middel_s_pr_gentagelse']:.2f} s pr. gentagelse målt i arbejderen, "
              f"opstart {t['opstart_s']:.1f} s")
        print(f"Fremskrevet til R = {NALM_REPS}: {t['runder']} runder -> "
              f"{t['forventet_s']:.0f} s ({t['forventet_s'] / 60:.1f} min)")
        return

    commits = k1.committede(COMMITTEDE)
    res = koer(n_reps=args.reps, max_workers=args.max_workers)
    meta["commits"] = commits
    md = skriv_md(res, meta)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "b4_k2_nowick.md").write_text(md, encoding="utf-8")
    lang_tabel(res).to_csv(OUT / "b4_k2_nowick.csv", index=False)
    print(md)


if __name__ == "__main__":
    main()
