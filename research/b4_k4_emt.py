"""B4 kandidat 4 — EMT: tilbage til VWAP efter et udmattelseslys, MNQ 5m.

Præregistreret i ``research/prereg/b4_k4_emt.md``. Kilden er
``research/kilder/emt_reel_noter.md``. Fyldning, omkostning, sizing og disciplin er kandidat
1-3's. Motoren er ny, fordi målet bevæger sig: ``simuler_handel_maal`` har
``trinA.simuler_handel``'s regler (kun stop i fyldningsbaren, regel 4, slippage på stoppet,
fladning) og giver bit for bit samme resultat med et konstant mål (test 13).
Forskelsjusteringen, Westfall-Young, Welch-intervallet og §10's nøgletal er
``research/b4_k2_nowick.py``'s, TR, ATR og sizing ``research/b4_k3_vending.py``'s, brugt
uændret. Ingen af kandidat 1-3's moduler røres.

    .venv/bin/python -m research.b4_k4_emt --regressionstjek
    .venv/bin/python -m research.b4_k4_emt --optaelling
    .venv/bin/python -m research.b4_k4_emt --tidsmaaling
    .venv/bin/python -m research.b4_k4_emt --koer

Pris hentes kun gennem ``data.holdout.load_in_sample``; holdout åbnes ikke.
``--optaelling`` og ``--tidsmaaling`` viser ingen R, ingen vinderrate og intet udfald.
``--koer`` er den rigtige kørsel og kræver ejerens godkendelse (§11.6).

## Vejen gennem modulet

1. ``Serie``: 1m-serien i handelspriser, den forskelsjusterede serie
   (``k2.forskelsjuster``), sessionens VWAP på den (§4a) og målet pr. 1m-bar oversat til
   handelspris (§4f).
2. ``lystabel``: hvert 5m-lys i vinduet med EMA9, ATR(14) og VWAP ved lysets lukning,
   vægen i hele ticks og — for begge sider — trigger og stop. Modellen og N-tid går tilbage
   mod VWAP (``TILBAGE``), N-mod går med strækket (``FORTSAET``). De kommer fra samme kode.
3. ``straek_retning`` og ``udmattelse``: §4b og §4c.
4. ``find_fyld``: stop-ordren i lys i+1, med gap-reglen (§4d).
5. ``dagsforloeb``: dagens setups i tidsorden: vindue, udløb, 1R-reglen (§4g), sizing og 1
   eller 2 handler om dagen (§4h). Samme funktion kører modellen, N-mod og N-tid.
6. ``simuler_handel_maal`` og ``handel``: handlen fra fyldningsbaren med VWAP-målet minut
   for minut (modellen, N-tid) eller et konstant mål (N-mod). Hver handel regnes én gang og
   slås op.
7. ``ntid_variant`` og ``ntid_traek``: nulmodellen N-tid (§6), matchet pr. dag,
   retning og klokketime (tillæg §2).
8. ``k2.westfall_young`` og ``beslutning``: §7 og §8.

## Læsninger — valgt af Code, skrevet op før kørslen

Præregistreringen fastlægger ikke disse detaljer. De er valgt her og skal bekræftes. Dem
der kan flytte et resultat, er mærket **[spørgsmål]**.

1. **Dagen er XNYS-sessionsdagen** (ET-datoen, ``k1._et_dag``), som i kandidat 1-3.
2. **Vinduet:** udmattelseslyset skal opfylde ``fl.vindue_mask(…, 5)`` på sin start, og
   lys i+1 på sin nominelle start (lysets start + 5 min). Et udmattelseslys kl. 14:25 CT,
   eller 11:25 CT på en halv dag, kan derfor aldrig fyldes. Det tælles
   (``naeste_uden_for_vindue_n``).
3. **VWAP's session** nulstilles ved hver 17:00 CT i vægurstid. 1m-barer i pausen
   16:00-17:00 CT hører til sessionen fra 17:00 CT dagen før. Nøglen er kandidat 2's
   forskudte tid, CT + 7 timer. Er sessionens summerede volumen 0, er VWAP udefineret, og
   lyset er ikke strakt. Alle barer i serien har volumen > 0.
4. **Forskelsjusteringen** er ``k2.forskelsjuster``: ved hver rul flyttes al forudgående
   historik med springet. VWAP, EMA9 og ATR regnes på den justerede serie og dens 5m-lys.
   Handelsprisen er den justerede pris minus barens forskydning. Lysets OHLC til væge,
   trigger og stop er den rå serie (handelspriser). Inden for en RTH-dag er forskellen en
   konstant, så strakt-betingelsen er den samme i begge.
5. **EMA9 og ATR(14) starter** i seriens første 5m-lys med ``EMA_0 = close_0`` og
   ``ATR_0 = TR_0 = high_0 − low_0`` (kandidat 3's læsning 3). Første signallys ligger 162
   5m-lys senere, hvor startens vægt er under ``0,8^162`` og ``(13/14)^162 ≈ 6e-6``.
6. **"Strakt"** sammenlignes i flydende tal, direkte som skrevet: ``close − VWAP ≥ k ×
   ATR`` og ``VWAP < EMA9 < close``. Lighed i ``≥`` tæller som strakt.
7. **Vægen** regnes i hele ticks: ``2 × (high − max(open, close)) ≥ high − low``. Præcis
   50% er derfor nok, uden flydende tals støj.
8. **"Det næste 5m-lys"** er lyset der starter 5 min efter udmattelseslysets start. Ordren
   er aktiv i 1m-barer der starter i ``[start + 5, start + 10)`` min. Mangler de, udløber
   setuppet.
9. **Udløsningen:** en buy-stop udløses når ``high ≥ trigger``, en sell-stop når ``low ≤
   trigger``, i hele ticks. Fyldet er triggeren ± 0,5417 tick. Ligger 1m-barens open på
   eller forbi triggeren, fyldes der på open ± 0,5417 tick.
10. **VWAP ved fyldtidspunktet** er målet i fyldningsbaren j: VWAP ved lukningen af 1m-baren
    før j (den foregående bar i serien), oversat med bar j's forskydning. Afstanden har
    fortegn i målets retning (``fyld − VWAP`` for en short). ``RR = afstand /
    risiko_pt``. **1R-reglen:** handlen tages kun ved ``RR ≥ 1``. VWAP på den forkerte side
    af fyldet giver RR < 0 og falder for reglen. **[spørgsmål]**
11. **Rækkefølgen for et udløst setup:** 1R-reglen, så ``kontrakter ≥ 1``. Et setup tælles
    kun ét sted. Kontrakter regnes ved fyldet, med den faktiske ``risiko_pt`` (et gap-fyld
    giver større risiko).
12. **Det bevægelige mål:** i bar j efter fyldningsbaren er målet ``fyld ± m_j ×
    risiko_pt`` med ``m_j = ±(VWAP_{j−1} − fyld) / risiko_pt``. Det er samme regneudtryk som
    ``simuler_handel``'s konstante mål, og ramt mål giver ``R_brutto = m_j``. Målet fyldes
    til målprisen, også når baren åbner forbi den, som i ``simuler_handel``. Har VWAP
    krydset indgangen (``m_j ≤ 0``), lukker handlen ved målet med R ≤ 0. Den forsigtige
    side: en limit på den forkerte side af prisen ville fylde på åbningen, ikke dårligere.
    Det tælles i rapporten (``maal_R_under_0_n``). **[spørgsmål]**
13. **Fladning og halve dage** som kandidat 1-3: ``trinA.flad_tid_utc`` giver 14:50 CT, og
    tidsexit sker til close i den sidste bar før.
14. **1/dag:** dagens første handel der tages. Setups der udløber eller afvises (1R,
    kontrakter), afslutter ikke dagen. Når handlen er taget, ignoreres resten af dagens
    setups, også mens den er åben.
15. **2/dag:** ordren fra et setup kan kun fyldes i 1m-barer **efter** exit-baren for dagens
    første handel (fra ``exit_i + 1``). Ligger hele lys i+1 før det, er setuppet blokeret
    (``blokeret_n``). Ellers gælder udløsning, gap-regel, 1R-regel og sizing fra den første
    tilladte bar. En ordre der først må fyldes efter exit, og hvor prisen allerede er forbi
    triggeren, fyldes på den bars åbning. **[spørgsmål]**
16. **Erstatningsreglen** (§4d) ændrer intet: ordren lever kun i lys i+1, og et nyt
    udmattelseslys kendes tidligst ved lukningen af i+1, hvor den gamle ordre er udløbet.
    Der venter aldrig to ordrer.
17. **N-tid matches pr. (ET-dag, retning):** for hver dag og retning trækkes lige så mange
    kandidater, som modellen havde handler i den retning den dag. Det er kandidat 2's
    godkendte læsning 9 (dag og HTF-tilstand). Så adskiller nulmodellen sig kun på vægen,
    ikke på long/short-blandingen. **[spørgsmål]**
18. **N-tid's pulje** for variant (k, n): lys i vinduet der er strakt ved samme k, uanset
    væge (udmattelseslysene er med), hvor lys i+1 ligger i vinduet og udløser ordren (første
    udløsning i i+1, uden hensyn til åbne handler), og hvor fyldet består 1R-reglen og har
    ``kontrakter ≥ 1``.
19. **N-tid's disciplin:** dagens trukne kandidater køres gennem ``dagsforloeb``, ligesom
    modellens setups (læsning 14-15). Ved 1/dag er det én handel. Ved 2/dag kan den anden
    blive blokeret, udløbe eller falde for 1R-reglen, når den kun må fyldes efter den første
    handels exit. Det tælles som en udfalden N-tid-handel. ``N_tid_udfaldne_n`` er
    modellens handler minus N-tid's.
20. **N-tid's tilfældige tal:** én strøm pr. gentagelse og variant,
    ``default_rng([9400, gentagelse, variantindeks])``. Varianterne trækkes uafhængigt
    (kandidat 3's godkendte læsning 11). Uden tilbagelægning: ved to handler trækkes to
    forskellige pladser i cellen.
21. **N-mod:** samme udmattelseslys, ordren på den anden side (buy-stop ``high + 1 tick``
    efter et stræk op, stop ``low − 2 ticks``), samme vindue, gap-regel og disciplin, kørt
    for sig selv og uafhængigt af modellen. **Målet er konstant:** afstanden fra N-mod's
    eget fyld til VWAP ved fyldet (som i læsning 10), lagt den anden vej. 1R-reglen gælder
    med den afstand. Med et konstant mål er N-mod's handel præcis ``simuler_handel`` med
    ``maal_r = RR``. **[spørgsmål]**
22. **+0,20 R gælder punktestimatet;** CI-betingelsen er CI-nedre > 0, som kandidat 1-3.
23. **CI ved 2/dag** er CR1 pr. ET-dag for en middelværdi, kandidat 1's
    ``klyngerobust_ols`` med kun en konstant: ``se² = G/(G−1) × Σ_g (Σ_i u_i)² / n²``,
    ``df = G − 1``. Med én handel pr. dag er det præcis t-intervallet. 1/dag bruger
    t-intervallet. Welch for N-mod-forskellen og long mod short, som præregistreret.
24. **Tvetydig:** stoppet ramt i en bar efter fyldningsbaren, hvor den bars mål også kunne
    nås. Bedste fald gør netop de handler til mål med barens ``m_j``. Det regnes inde i
    ``simuler_handel_maal``, så det bruger samme mål som handlen.
25. **Signaltiden** er udmattelseslysets start (CT). p10/p50/p90 er empiriske kvantiler
    (``inverted_cdf``), altid et tidspunkt der forekommer.
26. **handler_n ved 2/dag i optællingen** kræver at vide, hvornår dagens første handel
    lukker. Motoren køres for netop de handler, men kun exit-baren bruges. R og udfald
    forlader ikke funktionen (``exit_kun``). 1/dag simulerer ingen handel.
27. **MDE:** ``σ_R = √(middel RR)`` over variantens handler i optællingen, z = 3,2278
    (Šidák 6). Det ukorrigerede (2,4865) står ved siden af.
28. **En rul mellem 08:30 og 14:50 CT** springer dagen over, og den tælles. Ventet 0, fordi
    alle 19 ruller ligger kl. 18:00-19:01 CT (kandidat 3's læsning 5).
29. **N-tid matches også på klokketimen** (tillæg §2, supplerer læsning 17 og 20): hver
    model-handel matches i (ET-dag, retning, klokketime CT for udmattelseslysets start).
    Har timen ingen kandidat i puljen, bruges den nærmeste time med kandidater samme dag
    og retning, og ved lige afstand den tidligste. Det tælles (``nabotime_n``,
    ``nabotime_lige_langt_n``). Model-handler der ender i samme time, deler celle og
    trækkes uden tilbagelægning. Har dagen ingen kandidater i retningen, er cellen tom og
    tælles som før.
"""
from __future__ import annotations

import argparse
import math
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data import resample  # noqa: E402
from research import b4_k1_filtre as fl  # noqa: E402
from research import b4_k1_optaelling as k1  # noqa: E402
from research import b4_k1_trinA as trinA  # noqa: E402
from research import b4_k2_nowick as k2  # noqa: E402
from research import b4_k3_vending as k3  # noqa: E402
from research.stats import mean_ci_t, t_critical  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "output"
PREREG = ROOT / "research" / "prereg" / "b4_k4_emt.md"
KILDE = ROOT / "research" / "kilder" / "emt_reel_noter.md"
# Den rigtige kørsel sker kun når disse er committet og uændrede.
COMMITTEDE = (
    Path(__file__).resolve(), ROOT / "tests" / "test_b4_k4_emt.py", PREREG, KILDE,
    ROOT / "research" / "b4_k3_vending.py", ROOT / "research" / "b4_k2_nowick.py",
    ROOT / "research" / "b4_k1_trinA.py", ROOT / "research" / "b4_k1_filtre.py",
    ROOT / "research" / "b4_k1_optaelling.py", ROOT / "research" / "stats.py",
    ROOT / "data" / "holdout.py", ROOT / "data" / "resample.py",
    ROOT / "data" / "sessions.py",
)

CT = k1.CT
TICK = trinA.TICK
SLIP_PT = trinA.SLIP_PT                  # 0,5417 tick, §3
BAR_MIN = 5                              # §3, svar 3A
BAR_NS = BAR_MIN * 60 * 10**9
_FORSKYD = pd.Timedelta(hours=7)         # 17:00 CT → 00:00 i den forskudte tid, som k2

EMA_N = 9                                # §4a: α = 2/10
ATR_N = 14                               # §4a: Wilder, α = 1/14
TRIGGER_TICKS = 1                        # §4d
STOP_TICKS = 2                           # §4e
MIN_RR = 1.0                             # §4g

K_VAERDIER = (1.5, 2.0, 3.0)             # §5
PR_DAG = (1, 2)                          # §4h
VARIANTER = tuple((k, n) for k in K_VAERDIER for n in PR_DAG)

TILBAGE, FORTSAET = "tilbage", "fortsaet"   # mod VWAP (modellen, N-tid), med strækket (N-mod)
SIDER = (TILBAGE, FORTSAET)
OP, NED = 1, -1

KONTRAKTER_LOFT = trinA.KONTRAKTER_LOFT  # 50
RISIKO_USD = trinA.RISIKO_USD            # 250
MNQ_USD_PR_POINT = trinA.MNQ_USD_PR_POINT
OMK_USD_RUNDTUR = trinA.OMK_USD_RUNDTUR  # 2,627

MAAL, STOP, TIDSEXIT, CENSURERET = trinA.MAAL, trinA.STOP, trinA.TIDSEXIT, trinA.CENSURERET

NTID_REPS = 500                          # §6, sænkes ikke
NTID_SEED = 9400
AAR_LISTE = list(range(2019, 2024))

# §7: MDE, én-sidet α = 0,05, 80% styrke. σ_R = √(middel RR) fra optællingen.
Z_UKORR = 2.4865
Z_SIDAK6 = 3.2278
MDE_GRAENSE_R = 0.20
OEKONOMISK_KRAV_R = 0.20

# §11.3: kandidat 3's k = 1,0 (commit 77f7621) og kandidat 2's hovedvariant (f053ece).
REGRESSION_K3_HANDLER_N = 1168
REGRESSION_K3_MIDDEL_R_NETTO = -0.0712

TAEL_NOEGLER = ("ordrer_n", "naeste_uden_for_vindue_n", "blokeret_n", "udloebet_n",
                "udloest_n", "sprunget_over_under_1R_n", "afvist_kontrakter_nul_n",
                "handler_n", "ignoreret_efter_dagens_sidste_handel_n")


# ---------------------------------------------------------------------------
# Serien og §4a: VWAP, EMA9 og ATR
# ---------------------------------------------------------------------------

def mnq() -> pd.DataFrame:
    """MNQ.v.0 1m, 2019-05-06 → 2023-12-31, kun gennem holdout-modulet."""
    return k2.mnq()


def session_noegle(index: pd.DatetimeIndex) -> np.ndarray:
    """Sessionen pr. 1m-bar: datoen i den forskudte tid CT + 7 t (læsning 3). 17:00 CT
    starter en ny session; 16:00-17:00 CT hører til den der startede dagen før."""
    ct = pd.DatetimeIndex(index).tz_convert(CT).tz_localize(None)
    return k2._ns((ct + _FORSKYD).normalize())


def session_vwap(index: pd.DatetimeIndex, h, l, c, volumen) -> np.ndarray:
    """§4a: ``Σ(hlc3 × volume) / Σ(volume)`` fra sessionens start til og med hver 1m-bar.
    Udefineret (NaN) så længe sessionens volumen er 0."""
    h, l, c, v = (np.asarray(x, dtype=float) for x in (h, l, c, volumen))
    noegle = session_noegle(index)
    spv = pd.Series((h + l + c) / 3.0 * v).groupby(noegle).cumsum().to_numpy()
    sv = pd.Series(v).groupby(noegle).cumsum().to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(sv > 0, spv / np.where(sv > 0, sv, 1.0), np.nan)


def ema(x, n: int = EMA_N) -> np.ndarray:
    """Eksponentielt gennemsnit, α = 2/(n+1), startet med ``EMA_0 = x_0`` (læsning 5).
    ``EMA[i]`` er kendt ved lukningen af lys i."""
    x = np.asarray(x, dtype=float)
    ud = np.empty(len(x))
    if len(x) == 0:
        return ud
    alfa = 2.0 / (n + 1)
    e = float(x[0])
    ud[0] = e
    for j, v in enumerate(x[1:].tolist(), start=1):
        e += alfa * (v - e)
        ud[j] = e
    return ud


def justeret(df_1m: pd.DataFrame) -> pd.DataFrame:
    """Den forskelsjusterede 1m-serie med volumen (læsning 4)."""
    adj, _ = k2.forskelsjuster(df_1m)
    return adj.assign(volume=df_1m["volume"].to_numpy(dtype=float))


@dataclass
class Serie:
    """1m-serien som rå arrays: handelspriser, forskydningen og målet pr. bar."""
    tider: np.ndarray
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    o_t: np.ndarray
    h_t: np.ndarray
    l_t: np.ndarray
    iid: np.ndarray
    forskyd: np.ndarray       # justeret − handelspris, pr. bar
    vwap_adj: np.ndarray      # VWAP ved barens lukning, justeret
    maal_vwap: np.ndarray     # målet i bar j: VWAP ved lukningen af bar j−1, i handelspris

    @classmethod
    def af(cls, df_1m: pd.DataFrame, adj: pd.DataFrame | None = None) -> "Serie":
        adj = justeret(df_1m) if adj is None else adj
        o, h, l, c = (df_1m[k].to_numpy(dtype=float) for k in ("open", "high", "low", "close"))
        iid = (df_1m["instrument_id"].to_numpy() if "instrument_id" in df_1m.columns
               else np.zeros(len(df_1m), dtype=np.int64))
        forskyd = adj["close"].to_numpy(dtype=float) - c
        vwap_adj = session_vwap(df_1m.index, adj["high"], adj["low"], adj["close"],
                                adj["volume"])
        maal = np.full(len(c), np.nan)
        maal[1:] = vwap_adj[:-1] - forskyd[1:]
        return cls(tider=k2._ns(df_1m.index), o=o, h=h, l=l, c=c, o_t=k2.tick(o),
                   h_t=k2.tick(h), l_t=k2.tick(l), iid=iid, forskyd=forskyd,
                   vwap_adj=vwap_adj, maal_vwap=maal)

    @property
    def n(self) -> int:
        return len(self.tider)


# ---------------------------------------------------------------------------
# 5m-lysene i vinduet, §4a-§4e
# ---------------------------------------------------------------------------

def _dag_tider(dage: pd.DatetimeIndex) -> tuple[np.ndarray, np.ndarray]:
    """(08:30 CT, fladning 14:50 CT) pr. RTH-dag i UTC-ns."""
    d = pd.DatetimeIndex(dage)
    t0830 = (d + pd.Timedelta(hours=8, minutes=30)).tz_localize(CT).tz_convert("UTC")
    flad = np.array([k2._ns(pd.DatetimeIndex([trinA.flad_tid_utc(t)]))[0] for t in t0830],
                    dtype=np.int64)
    return k2._ns(t0830), flad


def vaege(o_t, h_t, l_t, c_t) -> tuple[np.ndarray, np.ndarray]:
    """§4c i hele ticks (læsning 7): (væge op, væge ned). Mindst halvdelen af lysets
    længde, og ``high − low > 0``."""
    o_t, h_t, l_t, c_t = (np.asarray(x, dtype=np.int64) for x in (o_t, h_t, l_t, c_t))
    laengde = h_t - l_t
    op = (laengde > 0) & (2 * (h_t - np.maximum(o_t, c_t)) >= laengde)
    ned = (laengde > 0) & (2 * (np.minimum(o_t, c_t) - l_t) >= laengde)
    return op, ned


def straek_retning(c_adj, vwap, ema9, atr, k: float) -> np.ndarray:
    """§4b: ``OP`` hvis ``close − VWAP ≥ k × ATR`` og ``VWAP < EMA9 < close``, ``NED``
    spejlvendt, ellers 0. Alt i den justerede serie, ved lysets lukning."""
    c_adj, vwap, ema9, atr = (np.asarray(x, dtype=float) for x in (c_adj, vwap, ema9, atr))
    with np.errstate(invalid="ignore"):
        op = (c_adj - vwap >= k * atr) & (vwap < ema9) & (ema9 < c_adj)
        ned = (vwap - c_adj >= k * atr) & (c_adj < ema9) & (ema9 < vwap)
    return np.where(op, OP, np.where(ned, NED, 0)).astype(np.int8)


def lystabel(df_1m: pd.DataFrame, s: Serie, adj: pd.DataFrame,
             dage: pd.DatetimeIndex) -> tuple[pd.DataFrame, dict]:
    """Hvert 5m-lys i vinduet på en RTH-dag uden rul i handelstiden, i tidsorden, med alt
    §4a-§4e kræver for begge sider. Indikatorerne er for hele serien, også om natten."""
    raa5 = resample.aggregate(df_1m, BAR_MIN)
    adj5 = resample.aggregate(adj, BAR_MIN)
    if not raa5.index.equals(adj5.index):
        raise ValueError("de rå og de justerede 5m-lys har forskellige grænser")
    c_adj = adj5["close"].to_numpy(dtype=float)
    ema9 = ema(c_adj)
    atr = k3.wilder_atr(k3.true_range(adj5["high"], adj5["low"], adj5["close"]), ATR_N)
    tid5 = k2._ns(raa5.index)
    # VWAP ved lysets lukning: den sidste 1m-bar der starter før lysets slutning, §4a.
    sidste = np.searchsorted(s.tider, tid5 + BAR_NS, side="left") - 1
    vwap5 = np.where(sidste >= 0, s.vwap_adj[np.maximum(sidste, 0)], np.nan)

    dage = pd.DatetimeIndex(dage)
    t0830, flad = _dag_tider(dage)
    rul_ns = s.tider[np.flatnonzero(s.iid[1:] != s.iid[:-1]) + 1]
    rul_dag = (np.searchsorted(rul_ns, flad, side="right")
               - np.searchsorted(rul_ns, t0830, side="left")) > 0
    dag_pos = dage.get_indexer(k1._et_dag(raa5.index))
    vindue = fl.vindue_mask(raa5.index, BAR_MIN) & (dag_pos >= 0)
    rul = vindue & rul_dag[np.maximum(dag_pos, 0)]
    naeste_vindue = fl.vindue_mask(raa5.index + pd.Timedelta(minutes=BAR_MIN), BAR_MIN)
    i = np.flatnonzero(vindue & ~rul)

    dp = dag_pos[i].astype(np.int64)
    ct = raa5.index[i].tz_convert(CT)
    o_t, h_t, l_t, c_t = (k2.tick(raa5[x].to_numpy(dtype=float)[i])
                          for x in ("open", "high", "low", "close"))
    v_op, v_ned = vaege(o_t, h_t, l_t, c_t)
    a = np.searchsorted(s.tider, tid5[i] + BAR_NS, side="left")
    b = np.searchsorted(s.tider, tid5[i] + 2 * BAR_NS, side="left")
    with np.errstate(invalid="ignore"):
        op = c_adj[i] > vwap5[i]
    t = pd.DataFrame({
        "i5": i, "tid_ns": tid5[i], "dag_pos": dp, "aar": dage.year[dp],
        "minut": np.asarray(ct.hour * 60 + ct.minute),
        "o_t": o_t, "h_t": h_t, "l_t": l_t, "c_t": c_t,
        "c_adj": c_adj[i], "vwap": vwap5[i], "ema9": ema9[i], "atr": atr[i],
        "vaege_op": v_op, "vaege_ned": v_ned,
        "naeste_ok": naeste_vindue[i], "a_i": a, "b_i": b,
        "cutoff_i": np.searchsorted(s.tider, flad[dp], side="left"),
    })
    for side in SIDER:
        # Modellen går short efter et stræk op; N-mod går long med det.
        long = op if side == FORTSAET else ~op
        t[f"long_{side}"] = long
        t[f"trigger_t_{side}"] = np.where(long, h_t + TRIGGER_TICKS, l_t - TRIGGER_TICKS)
        t[f"stop_t_{side}"] = np.where(long, l_t - STOP_TICKS, h_t + STOP_TICKS)
    info = {"n_1m": s.n, "n_5m": len(raa5), "rth_dage_n": len(dage),
            "vindue_lys_n": int(vindue.sum()), "rul_dage_n": int(rul_dag.sum()),
            "vindue_lys_paa_rul_dage_n": int(rul.sum()), "lys_n": len(i),
            "naeste_uden_for_vindue_n": int((~naeste_vindue[i]).sum()),
            "naeste_uden_barer_n": int((a >= b).sum()),
            "vwap_udefineret_n": int(np.isnan(vwap5[i]).sum())}
    return t, info


# ---------------------------------------------------------------------------
# §4d-§4g: fyldet, stoppet, afstanden og sizing
# ---------------------------------------------------------------------------

def find_fyld(s: Serie, start: int, slut: int, trigger_t: int, long: bool
              ) -> tuple[int, float]:
    """(fyldningsbar, fyld) for en stop-ordre aktiv i 1m-barerne ``[start, slut)``, eller
    (−1, NaN). Læsning 9: udløst når baren handler til triggeren; open på eller forbi
    triggeren fyldes på open. Slippage 0,5417 tick imod."""
    for j in range(start, slut):
        if long:
            if s.h_t[j] >= trigger_t:
                basis = s.o[j] if s.o_t[j] >= trigger_t else trigger_t * TICK
                return j, float(basis) + SLIP_PT
        elif s.l_t[j] <= trigger_t:
            basis = s.o[j] if s.o_t[j] <= trigger_t else trigger_t * TICK
            return j, float(basis) - SLIP_PT
    return -1, float("nan")


def risiko_pt(fyld: float, stop_t: int, long: bool) -> float:
    """§4e: ``|fyld − stop|``."""
    return fyld - stop_t * TICK if long else stop_t * TICK - fyld


def afstand(vwap_j: float, fyld: float, long: bool, side: str) -> float:
    """Læsning 10 og 21: afstanden fra fyldet til VWAP med fortegn i målets retning. For
    modellen ligger målet ved VWAP, for N-mod lige så langt væk den anden vej."""
    mod_vwap = (vwap_j - fyld) if long else (fyld - vwap_j)
    return mod_vwap if side == TILBAGE else -mod_vwap


def kontrakter_raa(risiko: float) -> float:
    """``floor(250 / (risiko_pt × 2))`` før loftet, med ``k3.sizing``'s afrunding."""
    return float(np.floor(np.round(RISIKO_USD / (risiko * MNQ_USD_PR_POINT), 9)))


# ---------------------------------------------------------------------------
# Motoren med bevægeligt mål, §4f
# ---------------------------------------------------------------------------

def simuler_handel_maal(h: np.ndarray, l: np.ndarray, c: np.ndarray, entry_i: int,
                        entry_pris: float, long: bool, risiko_pt: float, maal_r,
                        cutoff_i: int, n: int) -> tuple[str, float, int, bool, float]:
    """Fra fyldningsbaren og frem, 1m-bar for 1m-bar. Returnerer (udfald, R_brutto,
    exit_i, tvetydig, R_brutto_bedste).

    ``trinA.simuler_handel``'s regler uden BE: i fyldningsbaren kan kun stoppet rammes
    (motorrettelse 1); rammes stop og mål samme bar, tæller stoppet (regel 4); stoppet
    fyldes med 0,5417 tick slippage, målet uden; tidsexit til close i sidste bar før
    ``cutoff_i``, censur ved seriens slutning.

    ``maal_r`` er målet i R fra indgangen: et tal (konstant mål) eller et array hvor
    ``maal_r[i − entry_i]`` gælder i bar i. Målprisen regnes med samme udtryk som i
    ``simuler_handel``, så et konstant mål giver bit for bit samme resultat (test 13).

    ``tvetydig``: stoppet ramt i en bar efter fyldningsbaren, hvor barens mål også kunne
    nås. ``R_brutto_bedste`` er da barens mål, ellers ``R_brutto`` (læsning 24).
    """
    konstant = np.ndim(maal_r) == 0
    stop_niveau = entry_pris - risiko_pt if long else entry_pris + risiko_pt
    graense = min(cutoff_i, n)
    i = entry_i
    while i < graense:
        hi, lo = h[i], l[i]
        m = maal_r if konstant else maal_r[i - entry_i]
        maal = entry_pris + m * risiko_pt if long else entry_pris - m * risiko_pt
        stop_ramt = (lo <= stop_niveau) if long else (hi >= stop_niveau)
        if stop_ramt:
            eksekvering = stop_niveau - SLIP_PT if long else stop_niveau + SLIP_PT
            r = ((eksekvering - entry_pris) if long else (entry_pris - eksekvering)) / risiko_pt
            tvetydig = bool(i > entry_i and ((hi >= maal) if long else (lo <= maal)))
            return STOP, r, i, tvetydig, (float(m) if tvetydig else r)
        if i == entry_i:
            i += 1
            continue
        if (hi >= maal) if long else (lo <= maal):
            return MAAL, m, i, False, m
        i += 1
    sidste_i = i - 1 if i > entry_i else entry_i
    eksekvering = c[sidste_i]
    r = ((eksekvering - entry_pris) if long else (entry_pris - eksekvering)) / risiko_pt
    udfald = CENSURERET if graense == n else TIDSEXIT
    return udfald, r, sidste_i, False, r


# ---------------------------------------------------------------------------
# Grundlaget
# ---------------------------------------------------------------------------

@dataclass
class Grundlag:
    """Alt der er fast gennem kørslen, og opslaget af handler der allerede er regnet."""
    s: Serie
    lys: pd.DataFrame
    dage: pd.DatetimeIndex
    info: dict
    cache: dict = field(default_factory=dict)
    _a: dict = field(default_factory=dict, repr=False)

    def a(self, navn: str) -> np.ndarray:
        x = self._a.get(navn)
        if x is None:
            x = self.lys[navn].to_numpy()
            self._a[navn] = x
        return x


def straek(g: Grundlag, k: float) -> np.ndarray:
    return straek_retning(g.a("c_adj"), g.a("vwap"), g.a("ema9"), g.a("atr"), k)


def udmattelse(g: Grundlag, k: float) -> np.ndarray:
    """§4c: strakt ved k med væge i strækkets retning."""
    r = straek(g, k)
    return ((r == OP) & g.a("vaege_op").astype(bool)) | ((r == NED) & g.a("vaege_ned").astype(bool))


def _fyld_uden_blokering(g: Grundlag) -> None:
    """Pr. side: fyldet i lys i+1 uden hensyn til åbne handler, for hvert lys der er strakt
    ved mindste k. Det er N-tid's pulje (læsning 18) og optællingens tragt."""
    t = g.lys
    kand = np.flatnonzero((straek(g, min(K_VAERDIER)) != 0) & g.a("naeste_ok").astype(bool))
    a, b = g.a("a_i"), g.a("b_i")
    for side in SIDER:
        trig, stop, long = g.a(f"trigger_t_{side}"), g.a(f"stop_t_{side}"), g.a(f"long_{side}")
        j0 = np.full(len(t), -1, dtype=np.int64)
        fyld0, ris0, rr0 = (np.full(len(t), np.nan) for _ in range(3))
        for r in kand.tolist():
            lg = bool(long[r])
            j, f = find_fyld(g.s, int(a[r]), int(b[r]), int(trig[r]), lg)
            if j < 0:
                continue
            ri = risiko_pt(f, int(stop[r]), lg)
            j0[r], fyld0[r], ris0[r] = j, f, ri
            rr0[r] = afstand(g.s.maal_vwap[j], f, lg, side) / ri
        t[f"j0_{side}"], t[f"fyld0_{side}"], t[f"risiko0_{side}"], t[f"rr0_{side}"] = (
            j0, fyld0, ris0, rr0)
        with np.errstate(divide="ignore", invalid="ignore"):
            t[f"kontrakter_raa0_{side}"] = k3.sizing(ris0)["kontrakter_raa"]
    g._a.clear()


def byg_grundlag(df_1m: pd.DataFrame, dage: pd.DatetimeIndex | None = None) -> Grundlag:
    """Serien, VWAP, vinduets 5m-lys og de ublokerede fyld. Ingen handel simuleres her.
    ``dage`` er RTH-dagene; standard er XNYS-dagene som serien spænder over."""
    adj = justeret(df_1m)
    s = Serie.af(df_1m, adj)
    if dage is None:
        et = k1._et_dag(df_1m.index[[0, -1]])
        dage = k1.rth_dage(et[0], et[1] + pd.Timedelta(days=1))
    lys, info = lystabel(df_1m, s, adj, dage)
    g = Grundlag(s=s, lys=lys, dage=pd.DatetimeIndex(dage), info=info)
    _fyld_uden_blokering(g)
    return g


# ---------------------------------------------------------------------------
# Handlen, med opslag
# ---------------------------------------------------------------------------

def _maal_r(g: Grundlag, side: str, r: int, j: int, fyld: float, risiko: float, rr: float):
    """Målet i R fra fyldningsbaren: VWAP minut for minut for modellen (læsning 12),
    konstant for N-mod (læsning 21)."""
    if side == FORTSAET:
        return rr
    cutoff = int(g.a("cutoff_i")[r])
    seg = g.s.maal_vwap[j:max(cutoff, j)]
    return (seg - fyld) / risiko if bool(g.a(f"long_{side}")[r]) else (fyld - seg) / risiko


def _motor(g: Grundlag, side: str, r: int, j: int, fyld: float, risiko: float, rr: float):
    return simuler_handel_maal(g.s.h, g.s.l, g.s.c, j, fyld, bool(g.a(f"long_{side}")[r]),
                               risiko, _maal_r(g, side, r, j, fyld, risiko, rr),
                               int(g.a("cutoff_i")[r]), g.s.n)


def handel(g: Grundlag, side: str, r: int, j: int, fyld: float, risiko: float,
           rr: float) -> tuple:
    """(udfald, R_brutto, exit_i, tvetydig, R_brutto_bedste). Fyldet og risikoen er
    bestemt af (side, lys, fyldningsbar), så handlen regnes én gang og slås op."""
    noegle = (side, r, j)
    res = g.cache.get(noegle)
    if res is None:
        res = _motor(g, side, r, j, fyld, risiko, rr)
        g.cache[noegle] = res
    return res


ExitFn = Callable[[str, int, int, float, float, float], int]


def exit_fuld(g: Grundlag) -> ExitFn:
    """Den rigtige kørsel: handlen regnes og gemmes, exit-baren gives videre."""
    return lambda side, r, j, fyld, risiko, rr: handel(g, side, r, j, fyld, risiko, rr)[2]


def exit_kun(g: Grundlag) -> ExitFn:
    """Optællingen (læsning 26): kun exit-baren forlader funktionen. Intet gemmes."""
    return lambda side, r, j, fyld, risiko, rr: _motor(g, side, r, j, fyld, risiko, rr)[2]


# ---------------------------------------------------------------------------
# §4d-§4h: dagens forløb
# ---------------------------------------------------------------------------

@dataclass
class Forloeb:
    """De handler et sæt setups gav (i tidsorden) og tællerne. Ingen udfald."""
    raekke: np.ndarray
    j: np.ndarray
    fyld: np.ndarray
    risiko: np.ndarray
    rr: np.ndarray
    nr: np.ndarray
    tael: dict

    @property
    def n(self) -> int:
        return len(self.raekke)


def dagsforloeb(g: Grundlag, side: str, raekker: np.ndarray, max_pr_dag: int,
                exit_fn: ExitFn) -> Forloeb:
    """§4d-§4h for setups ``raekker`` (rækker i lystabellen, i tidsorden) på ``side``.

    Pr. dag i tidsorden: lys i+1 skal ligge i vinduet; ordren er aktiv i lys i+1, ved
    2/dag kun fra baren efter dagens første handels exit (læsning 15); udløses den ikke,
    er setuppet væk; et udløst setup tages kun ved RR ≥ 1 og ``kontrakter ≥ 1``. Når
    dagens sidste tilladte handel er taget, ignoreres resten. ``exit_fn`` kaldes kun når
    en senere handel samme dag afhænger af exit-baren.
    """
    raekker = np.asarray(raekker, dtype=np.int64)
    tael = dict.fromkeys(TAEL_NOEGLER, 0)
    ud: dict[str, list] = {x: [] for x in ("raekke", "j", "fyld", "risiko", "rr", "nr")}
    if len(raekker):
        dag = g.a("dag_pos")[raekker]
        a, b, ok = g.a("a_i"), g.a("b_i"), g.a("naeste_ok")
        trig, stop = g.a(f"trigger_t_{side}"), g.a(f"stop_t_{side}")
        long = g.a(f"long_{side}")
        vwap = g.s.maal_vwap
        graenser = np.r_[np.flatnonzero(np.r_[True, dag[1:] != dag[:-1]]), len(raekker)]
        for gi in range(len(graenser) - 1):
            lo, hi = int(graenser[gi]), int(graenser[gi + 1])
            taget, fri = 0, -1
            for q in range(lo, hi):
                r = int(raekker[q])
                if taget >= max_pr_dag:
                    tael["ignoreret_efter_dagens_sidste_handel_n"] += hi - q
                    break
                tael["ordrer_n"] += 1
                if not ok[r]:
                    tael["naeste_uden_for_vindue_n"] += 1
                    continue
                ar, br = int(a[r]), int(b[r])
                if fri >= br > ar:
                    tael["blokeret_n"] += 1
                    continue
                lg = bool(long[r])
                j, fyld = find_fyld(g.s, max(ar, fri), br, int(trig[r]), lg)
                if j < 0:
                    tael["udloebet_n"] += 1
                    continue
                tael["udloest_n"] += 1
                ri = risiko_pt(fyld, int(stop[r]), lg)
                rr = afstand(float(vwap[j]), fyld, lg, side) / ri
                if not rr >= MIN_RR:
                    tael["sprunget_over_under_1R_n"] += 1
                    continue
                if kontrakter_raa(ri) < 1:
                    tael["afvist_kontrakter_nul_n"] += 1
                    continue
                taget += 1
                for navn, v in (("raekke", r), ("j", j), ("fyld", fyld), ("risiko", ri),
                                ("rr", rr), ("nr", taget)):
                    ud[navn].append(v)
                if taget < max_pr_dag and q + 1 < hi:
                    fri = int(exit_fn(side, r, j, fyld, ri, rr)) + 1
    tael["handler_n"] = len(ud["raekke"])
    return Forloeb(raekke=np.asarray(ud["raekke"], dtype=np.int64),
                   j=np.asarray(ud["j"], dtype=np.int64),
                   fyld=np.asarray(ud["fyld"], dtype=float),
                   risiko=np.asarray(ud["risiko"], dtype=float),
                   rr=np.asarray(ud["rr"], dtype=float),
                   nr=np.asarray(ud["nr"], dtype=np.int64), tael=tael)


def setups(g: Grundlag, k: float) -> np.ndarray:
    """Udmattelseslysene ved k — modellens og N-mod's setups."""
    return np.flatnonzero(udmattelse(g, k))


# ---------------------------------------------------------------------------
# Handelstabellen — kun i den rigtige kørsel
# ---------------------------------------------------------------------------

HANDELSKOL = ("raekke", "dag", "aar", "minut", "side", "nr", "fyld_j", "exit_i", "RR",
              "risiko_pt", "kontrakter_raa", "kontrakter", "omk_R", "udfald", "R_brutto",
              "R_netto", "tvetydig", "udfald_bedste", "R_netto_bedste", "maal_R_under_0")


def handelstabel(g: Grundlag, side: str, f: Forloeb) -> pd.DataFrame:
    """Handlerne som tabel, i ``k2.noegletal``'s format. Regner dem der mangler."""
    if f.n == 0:
        return pd.DataFrame({k: pd.Series(dtype=object if k in ("udfald", "udfald_bedste",
                                                                  "side", "dag") else float)
                             for k in HANDELSKOL})
    res = [handel(g, side, int(r), int(j), float(fy), float(ri), float(rr))
           for r, j, fy, ri, rr in zip(f.raekke, f.j, f.fyld, f.risiko, f.rr)]
    udfald = np.array([x[0] for x in res], dtype=object)
    r_b = np.array([x[1] for x in res], dtype=float)
    tv = np.array([x[3] for x in res], dtype=bool)
    r_best = np.array([x[4] for x in res], dtype=float)
    sz = k3.sizing(f.risiko)
    omk = sz["omk_R"]
    dp = g.a("dag_pos")[f.raekke]
    return pd.DataFrame({
        "raekke": f.raekke, "dag": g.dage[dp], "aar": g.dage.year[dp],
        "minut": g.a("minut")[f.raekke],
        "side": np.where(g.a(f"long_{side}")[f.raekke].astype(bool), "long", "short"),
        "nr": f.nr, "fyld_j": f.j, "exit_i": np.array([x[2] for x in res], dtype=np.int64),
        "RR": f.rr, "risiko_pt": f.risiko, "kontrakter_raa": sz["kontrakter_raa"],
        "kontrakter": sz["kontrakter"], "omk_R": omk, "udfald": udfald, "R_brutto": r_b,
        "R_netto": r_b - omk, "tvetydig": tv,
        "udfald_bedste": np.where(tv, MAAL, udfald), "R_netto_bedste": r_best - omk,
        "maal_R_under_0": (udfald == MAAL) & (r_b <= 0),
    })


def middel_R(g: Grundlag, side: str, f: Forloeb) -> tuple[float, float]:
    """(middel netto-R forsigtigt, i bedste fald) — gentagelsernes eneste tal."""
    if f.n == 0:
        return float("nan"), float("nan")
    res = [handel(g, side, int(r), int(j), float(fy), float(ri), float(rr))
           for r, j, fy, ri, rr in zip(f.raekke, f.j, f.fyld, f.risiko, f.rr)]
    omk = OMK_USD_RUNDTUR / (f.risiko * MNQ_USD_PR_POINT)
    r_b = np.array([x[1] for x in res], dtype=float)
    r_best = np.array([x[4] for x in res], dtype=float)
    return float((r_b - omk).mean()), float((r_best - omk).mean())


# ---------------------------------------------------------------------------
# §6: nulmodellen N-tid
# ---------------------------------------------------------------------------

def ntid_pulje(g: Grundlag, k: float) -> np.ndarray:
    """Læsning 18: strakt ved k (uanset væge), lys i+1 i vinduet og udløst, RR ≥ 1 og
    ``kontrakter ≥ 1`` ved det ublokerede fyld."""
    with np.errstate(invalid="ignore"):
        return np.flatnonzero((straek(g, k) != 0) & g.a("naeste_ok").astype(bool)
                              & (g.a(f"j0_{TILBAGE}") >= 0)
                              & (g.a(f"rr0_{TILBAGE}") >= MIN_RR)
                              & (g.a(f"kontrakter_raa0_{TILBAGE}") >= 1))


@dataclass
class NtidVariant:
    """For én variant: cellerne (ET-dag, retning, klokketime) med modellens m handler og
    puljens kandidater, celle for celle. Fast gennem alle gentagelser."""
    m: np.ndarray
    start: np.ndarray
    laengde: np.ndarray
    pulje: np.ndarray
    faste: np.ndarray        # rækker fra celler med højst m kandidater: bruges alle
    tael: dict


def ntid_variant(g: Grundlag, k: float, model: Forloeb) -> NtidVariant:
    """§6, læsning 17 og 29: matching pr. (ET-dag, retning, klokketime CT), ellers den
    nærmeste time med kandidater samme dag og retning."""
    pulje = ntid_pulje(g, k)
    dp, lg = g.a("dag_pos"), g.a(f"long_{TILBAGE}").astype(bool)
    time_ = g.a("minut") // 60
    pdf = pd.DataFrame({"r": pulje, "dag": dp[pulje], "long": lg[pulje], "time": time_[pulje]})
    grupper = {key: grp["r"].to_numpy(dtype=np.int64)
               for key, grp in pdf.groupby(["dag", "long", "time"], sort=False)}
    timer: dict = {}
    for (d, lo, t) in grupper:
        timer.setdefault((d, lo), []).append(int(t))
    effektiv, nabo, lige = [], 0, 0
    for d, lo, t0 in zip(dp[model.raekke], lg[model.raekke], time_[model.raekke]):
        mulige = timer.get((d, lo), [])
        t = int(t0)
        if mulige and t not in mulige:
            afst = min(abs(h - t) for h in mulige)
            naermeste = sorted(h for h in mulige if abs(h - t) == afst)
            nabo += 1
            lige += len(naermeste) > 1
            t = naermeste[0]
        effektiv.append(t)
    celler = pd.DataFrame({"dag": dp[model.raekke], "long": lg[model.raekke],
                           "time": np.asarray(effektiv, dtype=np.int64)}).groupby(
        ["dag", "long", "time"], sort=True).size()
    m_l, l_l, dele, faste, for_faa_dage = [], [], [], [], set()
    for (d, lo, t), m in celler.items():
        c = grupper.get((d, lo, t), np.zeros(0, dtype=np.int64))
        if m > 2:
            raise ValueError("højst to handler om dagen")
        m_l.append(int(m))
        l_l.append(len(c))
        dele.append(c)
        if len(c) <= m:
            faste.append(c)
        if len(c) < m:
            for_faa_dage.add(int(d))
    m_a, l_a = np.asarray(m_l, dtype=np.int64), np.asarray(l_l, dtype=np.int64)
    pulje_flad = (np.concatenate(dele).astype(np.int64) if dele
                  else np.zeros(0, dtype=np.int64))
    tael = {"pulje_n": len(pulje),
            "pulje_paa_modeldage_n": int(np.isin(dp[pulje], dp[model.raekke]).sum()),
            "modelhandler_n": model.n, "celler_n": len(m_a),
            "celler_for_faa_n": int((l_a < m_a).sum()), "dage_for_faa_n": len(for_faa_dage),
            "manglende_n": int(np.maximum(m_a - l_a, 0).sum()),
            "nabotime_n": nabo, "nabotime_lige_langt_n": int(lige)}
    return NtidVariant(m=m_a, start=(np.cumsum(l_a) - l_a).astype(np.int64),
                       laengde=l_a, pulje=pulje_flad,
                       faste=(np.concatenate(faste).astype(np.int64) if faste
                              else np.zeros(0, dtype=np.int64)), tael=tael)


def ntid_traek(nv: NtidVariant, rng: np.random.Generator) -> np.ndarray:
    """Én trækning: m kandidater uden tilbagelægning pr. celle, alle hvis cellen har
    højst m. Rækkerne i tidsorden."""
    L, m, st = nv.laengde, nv.m, nv.start
    alle = L <= m
    en, to = ~alle & (m == 1), ~alle & (m == 2)
    dele = [nv.faste]
    if en.any():
        dele.append(nv.pulje[st[en] + rng.integers(0, L[en])])
    if to.any():
        f = rng.integers(0, L[to])
        s2 = rng.integers(0, L[to] - 1)
        s2 = s2 + (s2 >= f)
        dele += [nv.pulje[st[to] + f], nv.pulje[st[to] + s2]]
    return np.sort(np.concatenate(dele)).astype(np.int64)


def ntid_rng(rep: int, v: tuple) -> np.random.Generator:
    """Læsning 20: én strøm pr. gentagelse og variant."""
    return np.random.default_rng([NTID_SEED, rep, VARIANTER.index(v)])


def ntid_gentagelse(g: Grundlag, nt: dict, rep: int) -> dict:
    """{v: {handler_n, udfaldne_n, m, m_bedste}} for én N-tid-gentagelse."""
    exit_fn = exit_fuld(g)
    ud = {}
    for v in VARIANTER:
        f = dagsforloeb(g, TILBAGE, ntid_traek(nt[v], ntid_rng(rep, v)), v[1], exit_fn)
        m, m_b = middel_R(g, TILBAGE, f)
        ud[v] = {"handler_n": f.n, "udfaldne_n": nt[v].tael["modelhandler_n"] - f.n,
                 "m": m, "m_bedste": m_b}
    return ud


# ---------------------------------------------------------------------------
# §7 og §8
# ---------------------------------------------------------------------------

def middel_ci_cr1(r, klynge, alfa: float = 0.05) -> tuple[float, float]:
    """Læsning 23: CI95 for en middelværdi, klyngerobust (CR1) pr. ``klynge``,
    ``df = G − 1``. Med én observation pr. klynge er det t-intervallet."""
    r = np.asarray(r, dtype=float)
    n = len(r)
    if n < 2:
        return float("nan"), float("nan")
    _, idx = np.unique(np.asarray(klynge), return_inverse=True)
    G = int(idx.max()) + 1
    if G < 2:
        return float("nan"), float("nan")
    m = float(r.mean())
    s = np.bincount(idx, weights=r - m, minlength=G)
    se = math.sqrt(G / (G - 1) * float((s ** 2).sum()) / n ** 2)
    tcrit = t_critical(G - 1, alfa)
    return m - tcrit * se, m + tcrit * se


def sigma_R(rr) -> float:
    """§7: uden edge er ``σ_R ≈ √(middel RR)``."""
    rr = np.asarray(rr, dtype=float)
    return math.sqrt(float(rr.mean())) if len(rr) else float("nan")


def mde(handler_n: int, sigma: float, z: float = Z_SIDAK6) -> float:
    """§7: ``(z_α + z_0,20) × σ / √n``."""
    return z * sigma / math.sqrt(handler_n) if handler_n > 0 else float("inf")


def noegletal(h: pd.DataFrame, v: tuple, bedste: bool = False) -> dict:
    """§10's kolonner for én handelstabel: ``k2.noegletal``, CR1-intervallet ved 2/dag
    (læsning 23), RR og andelen af dagens anden handel."""
    row = k2.noegletal(h, bedste)
    kol = "R_netto_bedste" if bedste else "R_netto"
    row["ci_metode"] = "CR1 pr. dag" if v[1] == 2 else "t"
    if v[1] == 2 and len(h) >= 2:
        lo, hi = middel_ci_cr1(h[kol].to_numpy(dtype=float), pd.DatetimeIndex(h["dag"]).asi8)
        row["middel_R_netto_ci95_lo"], row["middel_R_netto_ci95_hi"] = lo, hi
    rr = h["RR"].to_numpy(dtype=float)
    row["RR_p50"] = _p(rr, 50)
    row["RR_middel"] = float(rr.mean()) if len(rr) else float("nan")
    row["anden_handel_n"] = int((h["nr"].to_numpy() == 2).sum())
    row["maal_R_under_0_n"] = int(np.asarray(h["maal_R_under_0"], dtype=bool).sum())
    return row


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
                "tekst": "Parkeres: udmattelseslyset tilføjer intet ud over et tilfældigt "
                         "strakt lys"}
    return {"raekke": 4, "variant": None, "kandidater": [], "tekst": "Kandidat 4 parkeres"}


# ---------------------------------------------------------------------------
# Den rigtige kørsel, §6-§10
# ---------------------------------------------------------------------------

def forbered(g: Grundlag) -> tuple[dict, dict, dict]:
    """(modellen, N-mod, N-tid) pr. variant. Modellens og N-mod's handler og alle N-tid-
    kandidaters handler fra det ublokerede fyld regnes her og gemmes."""
    exit_fn = exit_fuld(g)
    model = {v: dagsforloeb(g, TILBAGE, setups(g, v[0]), v[1], exit_fn) for v in VARIANTER}
    nmod = {v: dagsforloeb(g, FORTSAET, setups(g, v[0]), v[1], exit_fn) for v in VARIANTER}
    j0, f0 = g.a(f"j0_{TILBAGE}"), g.a(f"fyld0_{TILBAGE}")
    r0, rr0 = g.a(f"risiko0_{TILBAGE}"), g.a(f"rr0_{TILBAGE}")
    for r in ntid_pulje(g, min(K_VAERDIER)).tolist():
        handel(g, TILBAGE, r, int(j0[r]), float(f0[r]), float(r0[r]), float(rr0[r]))
    nt = {v: ntid_variant(g, v[0], model[v]) for v in VARIANTER}
    return model, nmod, nt


def koer_virkelig(g: Grundlag, model: dict, nmod: dict) -> dict:
    """{v: {"model": handler, "nmod": handler}}."""
    return {v: {"model": handelstabel(g, TILBAGE, model[v]),
                "nmod": handelstabel(g, FORTSAET, nmod[v])} for v in VARIANTER}


def afgoerelse(virkelig: dict, gentagelser: list[dict], bedste: bool) -> dict:
    """Westfall-Young mod N-tid, §8 og N-mod-sammenligningen for én opgørelse."""
    felt = "m_bedste" if bedste else "m"
    kol = "R_netto_bedste" if bedste else "R_netto"
    obs = {v: noegletal(virkelig[v]["model"], v, bedste)["middel_R_netto"] for v in VARIANTER}
    null = {v: np.array([rep[v][felt] for rep in gentagelser]) for v in VARIANTER}
    wy = k2.westfall_young(obs, null)
    raekker = {}
    for v in VARIANTER:
        model, nmod = virkelig[v]["model"], virkelig[v]["nmod"]
        n = noegletal(model, v, bedste)
        nm = noegletal(nmod, v, bedste)
        d, dlo, dhi = k2.forskel_ci(nmod[kol], model[kol])
        pv = wy["pr_variant"][v]
        sig = sigma_R(model["RR"])
        raekker[v] = {**n, **{f"N_tid_{x}": pv[x] for x in ("p5", "p50", "p95", "med", "sd")},
                      "t_v": pv["t"], "p_FWE": pv["p_FWE"],
                      "N_tid_handler_n_middel": float(np.mean(
                          [rep[v]["handler_n"] for rep in gentagelser])),
                      "N_tid_udfaldne_n_middel": float(np.mean(
                          [rep[v]["udfaldne_n"] for rep in gentagelser])),
                      "N_mod_handler_n": nm["handler_n"], "N_mod_RR_p50": nm["RR_p50"],
                      "N_mod_middel_R_netto": nm["middel_R_netto"],
                      "N_mod_middel_R_netto_ci95_lo": nm["middel_R_netto_ci95_lo"],
                      "N_mod_middel_R_netto_ci95_hi": nm["middel_R_netto_ci95_hi"],
                      "N_mod_minus_model": d, "N_mod_minus_model_ci95_lo": dlo,
                      "N_mod_minus_model_ci95_hi": dhi,
                      "N_mod_fortsaettelsesfund": bool(
                          nm["middel_R_netto_ci95_lo"] > 0 and dlo > 0),
                      "sigma_R": sig, "MDE_R_sidak6": mde(n["handler_n"], sig),
                      "MDE_R_ukorr": mde(n["handler_n"], sig, Z_UKORR)}
    return {"wy": wy, "raekker": raekker, "beslutning": beslutning(raekker)}


def _gruppe(r: np.ndarray) -> dict:
    lo, hi = mean_ci_t(r) if len(r) >= 2 else (float("nan"), float("nan"))
    return {"n": len(r), "middel_R_netto": float(r.mean()) if len(r) else float("nan"),
            "ci95_lo": lo, "ci95_hi": hi}


def diagnoser(virkelig: dict) -> dict:
    """§9: long mod short og pr. år. Optællingens diagnoser står i ``optaelling``."""
    side, aar = [], []
    for v in VARIANTER:
        h = virkelig[v]["model"]
        lo, sh = h[h["side"] == "long"]["R_netto"], h[h["side"] == "short"]["R_netto"]
        d, dlo, dhi = k2.forskel_ci(lo, sh)
        side.append({"k": v[0], "pr_dag": v[1], "long_n": len(lo), "short_n": len(sh),
                     "long_middel_R_netto": float(lo.mean()) if len(lo) else float("nan"),
                     "short_middel_R_netto": float(sh.mean()) if len(sh) else float("nan"),
                     "forskel": d, "forskel_ci95_lo": dlo, "forskel_ci95_hi": dhi})
        for a in AAR_LISTE:
            aar.append({"k": v[0], "pr_dag": v[1], "aar": a,
                        **_gruppe(h[h["aar"] == a]["R_netto"].to_numpy(dtype=float))})
    return {"side": side, "aar": aar}


def analyse(g: Grundlag, n_reps: int = NTID_REPS) -> dict:
    """§6-§9 på et grundlag. ``koer`` kalder den efter regressionstjekket."""
    model, nmod, nt = forbered(g)
    virkelig = koer_virkelig(g, model, nmod)
    t0 = time.perf_counter()
    gentagelser = [ntid_gentagelse(g, nt, rep) for rep in range(n_reps)]
    ntid_s = time.perf_counter() - t0
    afg = {"forsigtig": afgoerelse(virkelig, gentagelser, bedste=False),
           "bedste_fald": afgoerelse(virkelig, gentagelser, bedste=True)}
    return {"g": g, "virkelig": virkelig, "gentagelser": gentagelser, "afgoerelse": afg,
            "diagnoser": diagnoser(virkelig), "optaelling": optaelling(g),
            "n_reps": n_reps, "ntid_s": ntid_s}


def koer(n_reps: int = NTID_REPS) -> dict:
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

def _p(x, q) -> float:
    x = np.asarray(x, dtype=float)
    return float(np.percentile(x, q)) if len(x) else float("nan")


def _minut(x, q) -> float:
    """Læsning 25: empirisk kvantil, altid et tidspunkt der forekommer."""
    x = np.asarray(x, dtype=float)
    return float(np.percentile(x, q, method="inverted_cdf")) if len(x) else float("nan")


def _stoerrelse(risiko: np.ndarray) -> dict:
    """Risiko, omkostning og størrelse over et sæt handler (§9)."""
    risiko = np.asarray(risiko, dtype=float)
    sz = k3.sizing(risiko) if len(risiko) else {"omk_R": risiko, "kontrakter": risiko,
                                                 "kontrakter_raa": risiko}
    row = {f"risiko_pt_p{q}": _p(risiko, q) for q in (10, 50, 90)}
    row.update({f"omk_R_netto_p{q}": _p(sz["omk_R"], q) for q in (10, 50, 90)})
    row["kontrakter_p50"] = _p(sz["kontrakter"], 50)
    row["kontrakter_maks"] = float(np.max(sz["kontrakter"])) if len(risiko) else float("nan")
    row["kontrakter_loftet_n"] = int((np.asarray(sz["kontrakter_raa"]) > KONTRAKTER_LOFT).sum())
    return row


def _rr_raekke(rr: np.ndarray) -> dict:
    rr = np.asarray(rr, dtype=float)
    return {**{f"RR_p{q}": _p(rr, q) for q in (10, 50, 90)},
            "RR_middel": float(rr.mean()) if len(rr) else float("nan"),
            "sigma_R": sigma_R(rr)}


def _tid(minutter: np.ndarray) -> dict:
    return {f"signaltid_p{q}": _minut(minutter, q) for q in (10, 50, 90)}


def _vaegtet_minut(x, w, q) -> float:
    """Empirisk kvantil med vægte (``inverted_cdf``): det første tidspunkt hvor den
    kumulerede vægt når q%."""
    x, w = np.asarray(x, dtype=float), np.asarray(w, dtype=float)
    if len(x) == 0 or w.sum() <= 0:
        return float("nan")
    o = np.argsort(x, kind="stable")
    kum = np.cumsum(w[o]) / w.sum()
    return float(x[o][np.searchsorted(kum, q / 100 - 1e-12, side="left")])


def ntid_tidsprofil(g: Grundlag, nv: NtidVariant) -> dict:
    """Tillæg §4.2: signaltiden for N-tid's trækning, som forventning. En kandidat i en
    celle med L kandidater og m model-handler trækkes med sandsynlighed min(1, m/L).
    Ingen trækning og ingen simulering."""
    w = np.repeat(np.minimum(1.0, nv.m / np.maximum(nv.laengde, 1)), nv.laengde)
    mi = g.a("minut")[nv.pulje]
    return {f"traek_signaltid_p{q}": _vaegtet_minut(mi, w, q) for q in (10, 50, 90)}


def optaelling(g: Grundlag) -> dict:
    """§11.4: pr. variant strakte lys, udmattelseslys, udløste ordrer, 1R-reglen, handler_n,
    RR og dermed σ_R og MDE, risiko, omkostning og signaltid. Det samme for N-mod og N-tid's
    pulje. Intet R, ingen vinderrate, intet udfald (læsning 26)."""
    exit_fn = exit_kun(g)
    minut, aar_a = g.a("minut"), g.a("aar")
    long_t = g.a(f"long_{TILBAGE}").astype(bool)
    varianter, aar, ntid = [], [], []
    for v in VARIANTER:
        k, n = v
        st = straek(g, k)
        rows = setups(g, k)
        model_f = None
        for side, navn in ((TILBAGE, "EMT"), (FORTSAET, "N_mod")):
            f = dagsforloeb(g, side, rows, n, exit_fn)
            lg = g.a(f"long_{side}").astype(bool)[f.raekke]
            row = {"model": navn, "k": k, "pr_dag": n, "straekte_lys_n": int((st != 0).sum()),
                   "straekte_op_n": int((st == OP).sum()), "straekte_ned_n": int((st == NED).sum()),
                   "udmattelseslys_n": len(rows), **f.tael,
                   "dage_med_handel_n": int(np.unique(g.a("dag_pos")[f.raekke]).size),
                   "anden_handel_n": int((f.nr == 2).sum()),
                   "long_n": int(lg.sum()), "short_n": int((~lg).sum()),
                   **_rr_raekke(f.rr), **_tid(minut[f.raekke]), **_stoerrelse(f.risiko)}
            if side == TILBAGE:
                model_f = f
                row["MDE_R_sidak6"] = mde(f.n, row["sigma_R"])
                row["MDE_R_ukorr"] = mde(f.n, row["sigma_R"], Z_UKORR)
                row["betingelse_ok"] = bool(row["MDE_R_sidak6"] <= MDE_GRAENSE_R)
                fa = aar_a[f.raekke]
                for a in AAR_LISTE:
                    sub = fa == a
                    aar.append({"k": k, "pr_dag": n, "aar": a, "handler_n": int(sub.sum()),
                                "RR_p50": _p(f.rr[sub], 50), **_stoerrelse(f.risiko[sub])})
            varianter.append(row)
        # N-tid's pulje, §6 og læsning 18: tragten fra strakte lys til puljen.
        nv = ntid_variant(g, k, model_f)
        s_ok = (st != 0) & g.a("naeste_ok").astype(bool)
        j0 = g.a(f"j0_{TILBAGE}")
        rr0 = g.a(f"rr0_{TILBAGE}")
        udl = s_ok & (j0 >= 0)
        with np.errstate(invalid="ignore"):
            over = udl & (rr0 >= MIN_RR)
        pulje = ntid_pulje(g, k)
        ntid.append({"k": k, "pr_dag": n, "straekte_lys_n": int((st != 0).sum()),
                     "naeste_i_vindue_n": int(s_ok.sum()), "udloest_n": int(udl.sum()),
                     "sprunget_over_under_1R_n": int((udl & ~over).sum()),
                     "afvist_kontrakter_nul_n": int(over.sum()) - len(pulje),
                     **nv.tael, "pulje_long_n": int(long_t[pulje].sum()),
                     "pulje_short_n": int((~long_t[pulje]).sum()),
                     **_rr_raekke(rr0[pulje]), **_tid(minut[pulje]),
                     "pulje_risiko_pt_p50": _p(g.a(f"risiko0_{TILBAGE}")[pulje], 50),
                     **{f"model_signaltid_p{q}": _minut(minut[model_f.raekke], q)
                        for q in (10, 50, 90)}, **ntid_tidsprofil(g, nv)})
    return {"serie": dict(g.info), "varianter": varianter, "aar": aar, "ntid": ntid}


# ---------------------------------------------------------------------------
# Formatering
# ---------------------------------------------------------------------------

def _hhmm(m) -> str:
    if m is None or not np.isfinite(m):
        return "—"
    m = int(round(m))
    return f"{m // 60:02d}:{m % 60:02d}"


def _knavn(k) -> str:
    return f"k = {k:.1f}".replace(".", ",")


def _vnavn(v) -> str:
    return f"{_knavn(v[0])} · {v[1]}/dag"


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


def _tre(r: dict, navn: str, nd: int = 2, tid: bool = False) -> str:
    f = _hhmm if tid else (lambda x: k2._t(x, nd))
    return "/".join(f(r[f"{navn}_p{q}"]) for q in (10, 50, 90))


def optaelling_md(o: dict, meta: dict, kun_tabeller: bool = False) -> str:
    _t = k2._t
    s = o["serie"]
    hoved = [
        "# B4 kandidat 4 — optælling uden udfald (§11.4)\n",
        f"Kørt {meta['koert_utc']} UTC fra commit `{meta['head'][:7]}`, "
        f"{_arbejdskopi(COMMITTEDE)}. **Intet R, ingen vinderrate og intet udfald er "
        f"regnet.** Ved 2/dag er motoren kørt for dagens første handel, når et senere setup "
        f"samme dag afhænger af, hvornår den lukker; kun exit-minuttet er brugt (læsning "
        f"26).\n",
    ]
    dele = [] if kun_tabeller else hoved
    dele += [
        f"Serie: MNQ.v.0 1m gennem `data.holdout.load_in_sample`, "
        f"{trinA.MNQ_START.date()} → 2023-12-31, {_t(s['n_1m'])} 1m-barer, "
        f"{_t(s['n_5m'])} 5m-lys. {_t(s['rth_dage_n'])} RTH-dage. 5m-lys i vinduet "
        f"08:30-14:30 CT: {_t(s['vindue_lys_n'])}. Dage med rul 08:30-14:50 CT: "
        f"{_t(s['rul_dage_n'])}. Lys hvor lys i+1 ligger uden for vinduet: "
        f"{_t(s['naeste_uden_for_vindue_n'])}; uden 1m-barer i lys i+1: "
        f"{_t(s['naeste_uden_barer_n'])}. Lys uden VWAP: {_t(s['vwap_udefineret_n'])}.\n",
        "## Pr. variant — fra strakt lys til handel, §11.4\n",
        "Strakte og udmattelseslys er alle lys i vinduet. Ordrer er de setups dagens forløb "
        "nåede, før dagens sidste handel var taget. `blokeret` er ved 2/dag et lys i+1 der "
        "helt lå i dagens første handel (læsning 15).\n",
        "| model | variant | strakte lys (op/ned) | udmattelseslys | ordrer | i+1 uden for "
        "vindue | blokeret | udløbet | udløst | sprunget over, under 1R | kontrakter 0 | "
        "**handler_n** | 2. handel | long/short | ignoreret efter dagens sidste |",
        "|" + "---|" * 15,
    ]
    for r in o["varianter"]:
        dele.append(
            f"| {r['model']} | {_vnavn((r['k'], r['pr_dag']))} | {_t(r['straekte_lys_n'])} "
            f"({_t(r['straekte_op_n'])}/{_t(r['straekte_ned_n'])}) | "
            f"{_t(r['udmattelseslys_n'])} | {_t(r['ordrer_n'])} | "
            f"{_t(r['naeste_uden_for_vindue_n'])} | {_t(r['blokeret_n'])} | "
            f"{_t(r['udloebet_n'])} | {_t(r['udloest_n'])} | "
            f"{_t(r['sprunget_over_under_1R_n'])} | {_t(r['afvist_kontrakter_nul_n'])} | "
            f"**{_t(r['handler_n'])}** | {_t(r['anden_handel_n'])} | {_t(r['long_n'])}/"
            f"{_t(r['short_n'])} | {_t(r['ignoreret_efter_dagens_sidste_handel_n'])} |")
    dele += ["", "## Pr. variant — RR ved indgangen, σ_R og MDE, §7\n",
             "RR = afstand til målet / risiko_pt ved fyldet; kendt ved indgangen. "
             "σ_R = √(middel RR). MDE = z × σ_R / √handler_n, z = 3,2278 med Šidák 6 og "
             "2,4865 ukorrigeret.\n",
             "| model | variant | handler_n | RR p10/p50/p90 | RR middel | σ_R | MDE_R_ukorr | "
             "MDE_R_sidak6 | ≤ 0,20 |", "|---|---|---|---|---|---|---|---|---|"]
    for r in o["varianter"]:
        if r["model"] == "EMT":
            mde_t = (f"{_t(r['MDE_R_ukorr'], 3)} | **{_t(r['MDE_R_sidak6'], 3)}** | "
                     f"{'OK' if r['betingelse_ok'] else '**OVER**'}")
        else:
            mde_t = "— | — | —"
        dele.append(f"| {r['model']} | {_vnavn((r['k'], r['pr_dag']))} | {_t(r['handler_n'])} | "
                    f"{_tre(r, 'RR')} | {_t(r['RR_middel'], 2)} | {_t(r['sigma_R'], 3)} | "
                    f"{mde_t} |")
    dele += ["", "## Pr. variant — risiko, omkostning, størrelse og signaltid, §9\n",
             "Over handlerne. Signaltid er udmattelseslysets start, CT.\n",
             "| model | variant | risiko_pt p10/p50/p90 | omk_R_netto p10/p50/p90 | "
             "kontrakter p50/maks | kontrakter_loftet_n | signaltid p10/p50/p90 |",
             "|---|---|---|---|---|---|---|"]
    for r in o["varianter"]:
        dele.append(f"| {r['model']} | {_vnavn((r['k'], r['pr_dag']))} | "
                    f"{_tre(r, 'risiko_pt')} | {_tre(r, 'omk_R_netto', 3)} | "
                    f"{_t(r['kontrakter_p50'], 0)}/{_t(r['kontrakter_maks'], 0)} | "
                    f"{_t(r['kontrakter_loftet_n'])} | {_tre(r, 'signaltid', tid=True)} |")
    dele += ["", "## Modellen pr. år — risiko og omkostning, §9\n",
             "| variant | år | handler_n | RR p50 | risiko_pt p10/p50/p90 | "
             "omk_R_netto p10/p50/p90 | kontrakter_loftet_n |", "|---|---|---|---|---|---|---|"]
    for r in o["aar"]:
        dele.append(f"| {_vnavn((r['k'], r['pr_dag']))} | {r['aar']} | {_t(r['handler_n'])} | "
                    f"{_t(r['RR_p50'], 2)} | {_tre(r, 'risiko_pt')} | "
                    f"{_tre(r, 'omk_R_netto', 3)} | {_t(r['kontrakter_loftet_n'])} |")
    dele += ["", "## N-tid's pulje, §6\n",
             "Strakte lys ved samme k uanset væge, med lys i+1 i vinduet, udløst i i+1 og "
             "bestået 1R-reglen (læsning 18). Matching pr. (ET-dag, retning, klokketime CT), "
             "ellers nærmeste time med kandidater (læsning 17 og 29, tillæg §2). `celler "
             "for få` er celler med færre kandidater end modellens handler; så bruges alle.\n",
             "| variant | strakte lys | i+1 i vinduet | udløst | under 1R | kontrakter 0 | "
             "**pulje** | heraf på modeldage | long/short | modelhandler | celler | celler for "
             "få | dage for få | manglende | RR p10/p50/p90 | signaltid p10/p50/p90 |",
             "|" + "---|" * 16]
    for r in o["ntid"]:
        dele.append(
            f"| {_vnavn((r['k'], r['pr_dag']))} | {_t(r['straekte_lys_n'])} | "
            f"{_t(r['naeste_i_vindue_n'])} | {_t(r['udloest_n'])} | "
            f"{_t(r['sprunget_over_under_1R_n'])} | {_t(r['afvist_kontrakter_nul_n'])} | "
            f"**{_t(r['pulje_n'])}** | {_t(r['pulje_paa_modeldage_n'])} | "
            f"{_t(r['pulje_long_n'])}/{_t(r['pulje_short_n'])} | {_t(r['modelhandler_n'])} | "
            f"{_t(r['celler_n'])} | {_t(r['celler_for_faa_n'])} | {_t(r['dage_for_faa_n'])} | "
            f"{_t(r['manglende_n'])} | {_tre(r, 'RR')} | {_tre(r, 'signaltid', tid=True)} |")
    dele += ["", "## N-tid's tidsprofil efter matching på klokketimen, tillæg §2\n",
             "Signaltid for modellens handler og for N-tid's trækning (forventet: en kandidat "
             "trækkes med sandsynlighed min(1, m/L) i sin celle). Puljens profil står i "
             "tabellen ovenfor.\n",
             "| variant | model p10/p50/p90 | N-tid-trækning p10/p50/p90 | matchet til nabotime "
             "| heraf lige langt |", "|---|---|---|---|---|"]
    for r in o["ntid"]:
        dele.append(f"| {_vnavn((r['k'], r['pr_dag']))} | "
                    f"{_tre(r, 'model_signaltid', tid=True)} | "
                    f"{_tre(r, 'traek_signaltid', tid=True)} | {_t(r['nabotime_n'])} | "
                    f"{_t(r['nabotime_lige_langt_n'])} |")
    model = [r for r in o["varianter"] if r["model"] == "EMT"]
    ok = all(r["betingelse_ok"] for r in model)
    dele += ["", "## Betingelsen i §7\n",
             ("Alle 6 varianter har MDE med Šidák 6 ≤ 0,20 R.\n" if ok else
              "**Mindst én variant har MDE med Šidák 6 over 0,20 R: "
              + ", ".join(_vnavn((r["k"], r["pr_dag"])) for r in model
                          if not r["betingelse_ok"])
              + ". Code stopper, og ejeren beslutter (§7).**\n")]
    return "\n".join(dele)


def optaelling_csv(o: dict) -> pd.DataFrame:
    rows = [{"tabel": "variant", **r} for r in o["varianter"]]
    rows += [{"tabel": "aar", **r} for r in o["aar"]]
    rows += [{"tabel": "N_tid_pulje", **r} for r in o["ntid"]]
    rows.append({"tabel": "serie", **o["serie"]})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Rapporten, §10
# ---------------------------------------------------------------------------

def hovedtabel_md(afg: dict) -> str:
    _t = k2._t
    linjer = ["| variant | handler_n | dage | RR_p50 | tvetydig_n | censureret_n | "
              "middel_R_brutto | middel_R_netto | CI95 (metode) | win_rate_pct_brutto "
              "[Wilson] | win_rate_pct_netto [Wilson] | mål/stop/tid_pct | N_tid p5/p50/p95 | "
              "t_v | p_FWE |", "|" + "---|" * 15]
    for v in VARIANTER:
        r = afg["raekker"][v]
        linjer.append(
            f"| {_vnavn(v)} | {_t(r['handler_n'])} | {_t(r['dage_med_handel_n'])} | "
            f"{_t(r['RR_p50'], 2)} | {_t(r['tvetydig_n'])} | {_t(r['censureret_n'])} | "
            f"{_t(r['middel_R_brutto'], 4)} | {_t(r['middel_R_netto'], 4)} | "
            f"[{_t(r['middel_R_netto_ci95_lo'], 4)}; {_t(r['middel_R_netto_ci95_hi'], 4)}] "
            f"({r['ci_metode']}) | {_t(r['win_rate_pct_brutto'], 1)} "
            f"[{_t(r['win_rate_pct_brutto_ci95_lo'], 1)}; "
            f"{_t(r['win_rate_pct_brutto_ci95_hi'], 1)}] | "
            f"{_t(r['win_rate_pct_netto'], 1)} [{_t(r['win_rate_pct_netto_ci95_lo'], 1)}; "
            f"{_t(r['win_rate_pct_netto_ci95_hi'], 1)}] | {_t(r['udfald_maal_pct'], 1)}/"
            f"{_t(r['udfald_stop_pct'], 1)}/{_t(r['udfald_tidsexit_pct'], 1)} | "
            f"{_t(r['N_tid_p5'], 4)}/{_t(r['N_tid_p50'], 4)}/{_t(r['N_tid_p95'], 4)} | "
            f"{_t(r['t_v'], 2)} | {_t(r['p_FWE'], 4)} |")
    return "\n".join(linjer) + "\n"


def nmod_md(afg: dict) -> str:
    _t = k2._t
    linjer = ["| variant | N_mod_handler_n | N_mod_RR_p50 | N_mod_middel_R_netto [CI95] | "
              "N_mod − model [Welch-CI95] | in-sample-fund om fortsættelse |",
              "|---|---|---|---|---|---|"]
    for v in VARIANTER:
        r = afg["raekker"][v]
        linjer.append(
            f"| {_vnavn(v)} | {_t(r['N_mod_handler_n'])} | {_t(r['N_mod_RR_p50'], 2)} | "
            f"{_t(r['N_mod_middel_R_netto'], 4)} [{_t(r['N_mod_middel_R_netto_ci95_lo'], 4)}; "
            f"{_t(r['N_mod_middel_R_netto_ci95_hi'], 4)}] | {_t(r['N_mod_minus_model'], 4)} "
            f"[{_t(r['N_mod_minus_model_ci95_lo'], 4)}; "
            f"{_t(r['N_mod_minus_model_ci95_hi'], 4)}] | {_t(r['N_mod_fortsaettelsesfund'])} |")
    return "\n".join(linjer) + "\n"


def _beslutning_md(navn: str, afg: dict) -> str:
    b = afg["beslutning"]
    v = f" Frosset variant: **{_vnavn(b['variant'])}**." if b["variant"] is not None else ""
    return f"**{navn}: række {b['raekke']}: {b['tekst']}.**{v}\n"


def skriv_md(res: dict, meta: dict) -> str:
    _t = k2._t
    afg = res["afgoerelse"]
    f = afg["forsigtig"]["raekker"]
    d = res["diagnoser"]
    dele = [
        "# B4 kandidat 4 — EMT, tilbage til VWAP efter et udmattelseslys\n",
        f"Kørt {meta['koert_utc']} UTC fra commit `{meta['head'][:7]}`. Præregistrering "
        f"`{_rel(PREREG)}` (commit `{meta['commits'][_rel(PREREG)][:7]}`). Kode "
        f"`{_rel(Path(__file__))}` (commit `{meta['commits'][_rel(Path(__file__))][:7]}`).\n",
        f"Serie: MNQ.v.0 1m, {trinA.MNQ_START.date()} → 2023-12-31, "
        f"{_t(res['g'].s.n)} 1m-barer, 5m-lys. 6 varianter. N-tid: {res['n_reps']} "
        f"gentagelser.\n",
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
        "## N-mod — med strækket i stedet for tilbage (forklarer, ændrer ikke rækken)\n",
        nmod_md(afg["forsigtig"]),
        "## MDE og N-tid\n",
        "| variant | σ_R | MDE_R_sidak6 | MDE_R_ukorr | N_tid handler_n (middel) | N_tid "
        "udfaldne (middel) | 2. handel | mål med R ≤ 0 |\n|---|---|---|---|---|---|---|---|\n" +
        "".join(f"| {_vnavn(v)} | {_t(f[v]['sigma_R'], 3)} | {_t(f[v]['MDE_R_sidak6'], 3)} | "
                f"{_t(f[v]['MDE_R_ukorr'], 3)} | {_t(f[v]['N_tid_handler_n_middel'], 1)} | "
                f"{_t(f[v]['N_tid_udfaldne_n_middel'], 1)} | {_t(f[v]['anden_handel_n'])} | "
                f"{_t(f[v]['maal_R_under_0_n'])} |\n" for v in VARIANTER),
        "## Bedste fald — samme tabel\n", hovedtabel_md(afg["bedste_fald"]),
        "## Long mod short\n",
        "| variant | long_n | short_n | long R_netto | short R_netto | forskel [Welch-CI95] |\n"
        "|---|---|---|---|---|---|\n" +
        "".join(f"| {_vnavn((r['k'], r['pr_dag']))} | {_t(r['long_n'])} | {_t(r['short_n'])} | "
                f"{_t(r['long_middel_R_netto'], 4)} | {_t(r['short_middel_R_netto'], 4)} | "
                f"{_t(r['forskel'], 4)} [{_t(r['forskel_ci95_lo'], 4)}; "
                f"{_t(r['forskel_ci95_hi'], 4)}] |\n" for r in d["side"]),
        "## Pr. år — middel_R_netto (handler_n)\n",
        "| variant | " + " | ".join(str(a) for a in AAR_LISTE) + " |\n|" +
        "---|" * (1 + len(AAR_LISTE)) + "\n" +
        "".join(f"| {_vnavn(v)} | " + " | ".join(
            f"{_t(r['middel_R_netto'], 3)} ({_t(r['n'])})"
            for r in d["aar"] if (r["k"], r["pr_dag"]) == v) + " |\n" for v in VARIANTER),
        "## Optælling og øvrige diagnoser, §9\n",
        optaelling_md(res["optaelling"], meta, kun_tabeller=True),
        "## Efter kørslen, §13\n",
        "Stop. Ingen ændring af definitioner, ingen nye varianter, ingen forslag.\n",
        f"Alle tal: `{_rel(OUT / 'b4_k4_emt.csv')}`.\n",
    ]
    return "\n".join(dele)


def lang_tabel(res: dict) -> pd.DataFrame:
    rows = []
    for navn, afg in res["afgoerelse"].items():
        for v in VARIANTER:
            rows.append({"tabel": "hoved", "afgoerelse": navn, "k": v[0], "pr_dag": v[1],
                         "raekke_8": afg["beslutning"]["raekke"], **afg["raekker"][v]})
    for tabel in ("side", "aar"):
        rows += [{"tabel": tabel, "afgoerelse": "forsigtig", **r}
                 for r in res["diagnoser"][tabel]]
    optael = optaelling_csv(res["optaelling"]).rename(columns={"tabel": "optaelling"})
    optael.insert(0, "tabel", "optaelling")
    return pd.concat([pd.DataFrame(rows), optael], ignore_index=True)


# ---------------------------------------------------------------------------
# §11.3: regressionstjek
# ---------------------------------------------------------------------------

def regression_k3(df: pd.DataFrame) -> dict:
    """Kandidat 3's k = 1,0 gengiver 1.168 handler og −0,0712 R (commit 77f7621). Kører
    kandidat 3's egen vej, uændret."""
    g = k3.byg_grundlag(df, k1.rth_dage(trinA.MNQ_START, trinA.TRIN_A_SLUT))
    v = k3.foerste_signal(g, k3.MOD, 1.0)
    k3.forudregn(g, k3.MOD, v.raekker)
    h = k3.handelstabel(g, v.raekker, k3.MOD)
    m = float(h["R_netto"].mean())
    return {"handler_n": len(h), "middel_R_netto": m,
            "ok": len(h) == REGRESSION_K3_HANDLER_N
            and round(m, 4) == REGRESSION_K3_MIDDEL_R_NETTO}


def regressionstjek(df: pd.DataFrame | None = None) -> dict:
    """§11.3: kandidat 1's tre tjek, ``simuler_handel``'s 1.226 handler og −0,0115 R,
    kandidat 2's hovedvariant (611 og −0,1430) og kandidat 3's k = 1,0 (1.168 og
    −0,0712)."""
    df = mnq() if df is None else df
    t0 = time.perf_counter()
    ud = k3.regressionstjek(df)
    ud["k3_k1"] = regression_k3(df)
    ud["sekunder"] = time.perf_counter() - t0
    ud["ok"] = bool(ud["ok"] and ud["k3_k1"]["ok"])
    return ud


# ---------------------------------------------------------------------------
# §11.5: tidsmålingen — uden R
# ---------------------------------------------------------------------------

def tidsmaaling(n_reps: int = 5) -> dict:
    """§11.5: ét gennemløb og ``n_reps`` N-tid-gentagelser, fremskrevet til R = 500.
    Returnerer kun tider og antal. R regnes inde i gennemløbet og gentagelserne, fordi det
    er arbejdet der måles, men det forlader ikke funktionen."""
    t0 = time.perf_counter()
    df = mnq()
    load_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    g = byg_grundlag(df, k1.rth_dage(trinA.MNQ_START, trinA.TRIN_A_SLUT))
    grundlag_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    model, nmod, nt = forbered(g)
    forbered_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    virkelig = koer_virkelig(g, model, nmod)
    for v in VARIANTER:
        noegletal(virkelig[v]["model"], v)
        noegletal(virkelig[v]["nmod"], v)
    gennemloeb_s = time.perf_counter() - t0
    cache_foer = len(g.cache)
    t0 = time.perf_counter()
    taelle = []
    for rep in range(n_reps):
        r = ntid_gentagelse(g, nt, rep)
        taelle.append({_vnavn(v): (x["handler_n"], x["udfaldne_n"]) for v, x in r.items()})
    ntid_s = time.perf_counter() - t0
    pr_rep = ntid_s / n_reps if n_reps else 0.0
    forventet = load_s + grundlag_s + forbered_s + gennemloeb_s + pr_rep * NTID_REPS
    return {"load_s": load_s, "grundlag_s": grundlag_s, "forbered_s": forbered_s,
            "handler_regnet_n": cache_foer, "handler_regnet_i_gentagelser_n":
            len(g.cache) - cache_foer, "gennemloeb_s": gennemloeb_s, "n_reps": n_reps,
            "ntid_s": ntid_s, "pr_rep_s": pr_rep, "forventet_s": forventet,
            "handler_n": {f"{navn} {_vnavn(v)}": d[v].n
                          for navn, d in (("EMT", model), ("N_mod", nmod)) for v in VARIANTER},
            "ntid_handler_og_udfaldne_n": taelle}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--regressionstjek", action="store_true",
                     help="§11.3: kandidat 1's tre tjek, simuler_handel, kandidat 2 og 3")
    grp.add_argument("--optaelling", action="store_true",
                     help="§11.4: optælling uden udfald. Skriver b4_k4_emt_optaelling")
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
        k1r, mo, k2r, k3r = r["k1"], r["motor"], r["k2_hovedvariant"], r["k3_k1"]
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
              f"{k3.REGRESSION_K2_HANDLER_N}), middel_R_netto {k2r['middel_R_netto']:.4f} "
              f"(ventet {k3.REGRESSION_K2_MIDDEL_R_NETTO}): {'OK' if k2r['ok'] else 'AFVIGER'}")
        print(f"Kandidat 3, k = 1,0: handler_n {k3r['handler_n']} (ventet "
              f"{REGRESSION_K3_HANDLER_N}), middel_R_netto {k3r['middel_R_netto']:.4f} "
              f"(ventet {REGRESSION_K3_MIDDEL_R_NETTO}): {'OK' if k3r['ok'] else 'AFVIGER'}")
        print(f"Tid: {r['sekunder']:.0f} s")
        if not r["ok"]:
            sys.exit(1)
        return

    if args.optaelling:
        g = byg_grundlag(mnq(), k1.rth_dage(trinA.MNQ_START, trinA.TRIN_A_SLUT))
        o = optaelling(g)
        md = optaelling_md(o, meta)
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "b4_k4_emt_optaelling.md").write_text(md, encoding="utf-8")
        optaelling_csv(o).to_csv(OUT / "b4_k4_emt_optaelling.csv", index=False)
        print(md)
        return

    if args.tidsmaaling:
        t = tidsmaaling(args.maalte_reps)
        print(f"Indlæsning {t['load_s']:.1f} s, grundlag {t['grundlag_s']:.1f} s, "
              f"model og N-mod for 6 varianter plus N-tid's pulje {t['forbered_s']:.1f} s "
              f"({t['handler_regnet_n']} handler regnet), handelstabeller og nøgletal "
              f"{t['gennemloeb_s']:.2f} s")
        print(f"{t['n_reps']} N-tid-gentagelser: {t['ntid_s']:.2f} s, "
              f"{t['pr_rep_s'] * 1000:.0f} ms pr. gentagelse "
              f"({t['handler_regnet_i_gentagelser_n']} nye handler regnet undervejs)")
        print(f"Fremskrevet til R = {NTID_REPS}: {t['forventet_s']:.0f} s "
              f"({t['forventet_s'] / 60:.1f} min), regressionstjekket ikke medregnet")
        print(f"handler_n: {t['handler_n']}")
        print(f"N-tid (handler_n, udfaldne) pr. gentagelse: {t['ntid_handler_og_udfaldne_n']}")
        return

    commits = k1.committede(COMMITTEDE)
    res = koer(n_reps=args.reps)
    meta["commits"] = commits
    md = skriv_md(res, meta)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "b4_k4_emt.md").write_text(md, encoding="utf-8")
    lang_tabel(res).to_csv(OUT / "b4_k4_emt.csv", index=False)
    print(md)


if __name__ == "__main__":
    main()
