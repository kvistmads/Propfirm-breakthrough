"""B4 kandidat 6 — overnight drift ved Europas åbning, NQ 2016-2023 og MNQ 2019-2023.

Præregistreret i ``research/prereg/b4_k6_overnight.md``. Baggrunden er
``research/output/b4_screening.md`` §3A og §4. Long i én time (V1) eller to (V2) omkring
Europas åbning, alle nætter eller kun efter en salgsdag. Målet er netto-dollar pr. handlet
nat pr. MNQ ved dagens niveau. Nulmodellen N-nat er samme længde på en tilfældig anden tid
samme nat. Westfall-Young og forskelsjusteringen er ``research/b4_k2_nowick.py``'s, brugt
uændret. Kandidat 1-5's moduler importeres og røres ikke.

    .venv/bin/python -m research.b4_k6_overnight --regressionstjek
    .venv/bin/python -m research.b4_k6_overnight --optaelling
    .venv/bin/python -m research.b4_k6_overnight --tidsmaaling
    .venv/bin/python -m research.b4_k6_overnight --koer

Pris hentes kun gennem ``data.holdout.load_in_sample``; holdout åbnes ikke.
``--optaelling`` og ``--tidsmaaling`` viser ingen P&L, ingen hit ratio og intet udfald.
``--koer`` er den rigtige kørsel og kræver ejerens godkendelse (§11.6).

## Vejen gennem modulet

1. ``serie`` og ``byg_grundlag``: serien, den forskelsjusterede pris, nætterne (§4a),
   udførelsespunkterne (§4b), salgsdagene (§4c) og de udelukkede nætter.
2. ``handel``: punktforskel, L_n, skala og brutto pr. nat for et vindue (§4f). Kun i den
   rigtige kørsel og tidsmålingen.
3. ``nat_gitter``, ``nnat_vaerdier``, ``nnat_traek`` og ``nnat_gentagelse``: N-nat (§6).
   ``k2.westfall_young`` og ``beslutning``: §7 og §8.
4. ``sigma_nat``, ``mde``, ``styrke_fwe`` og ``styrke_ci``: §7's MDE og styrke, uden udfald.
5. ``optaelling`` (§11.4), ``tidsmaaling`` (§11.5), ``analyse`` og ``skriv_md`` (§9-§10).

## Læsninger — valgt af Code, skrevet op før kørslen

Præregistreringen fastlægger ikke disse detaljer. De er valgt her og skal bekræftes. Dem
der kan flytte et resultat, eller hvor præregistreringen kan læses på to måder, er mærket
**[tvivl]**.

1. **Nætterne** er én pr. XNYS-dag d i perioden: NQ 2016-01-04 → 2023-12-29 og MNQ
   2019-05-06 → 2023-12-29. Natten går fra 17:00 CT på kalenderdagen før d til 08:30 CT
   på d (§4a). For en mandag er det søndag 17:00, og efter en mandagshelligdag er det
   mandag 17:00. **Forrige RTH-dag** er XNYS-sessionen før d i kalenderen
   (``exchange_calendars``), også når den ligger før serien.
2. **Tiderne** regnes som vægur i hver sin zone: vinduerne i New York-tid, natten i CT.
   Et sommertidsskifte sker søndag kl. 02:00 og falder aldrig inde i en nat, der starter
   søndag kl. 17:00 eller senere. Koden stopper, hvis en nat ikke er 930 minutter.
3. **MNQ hentes uafskåret** med ``load_in_sample("MNQ.v.0")``, ikke med ``k2.mnq()``, som
   skærer ved 2019-05-06 00:00 UTC og ville tage starten af den første nat. Første bar i
   serien er 2019-05-05 19:00 CT, så den nat mangler 17:00-19:00. Det rammer kun lang hele
   natten og N-nat-trækningerne den nat.
4. **Udførelse** (§4b): første bar der starter på eller efter det nominelle tidspunkt,
   til dens open. Forsinkelsen er barens start minus det nominelle tidspunkt. Over 5
   minutter udelukker; præcis 5 er med. Forsinkelser på 1-5 minutter tælles pr. variant.
5. **Udelukkelse i alle varianter** [tvivl]: natten udelukkes i alle 4 varianter og i
   N-nat, hvis ét af de fire punkter (V1 ind 02:00, V1 ud 03:00, V2 ind 01:30, V2 ud
   03:30 NY) er mere end 5 minutter forsinket. Det er læst ud af "i alle varianter" i §4b.
   Den anden læsning er, at en forsinkelse i V2 kun udelukker V2-varianterne. Grunden
   skrives som "ingen barer i natten", "ingen barer i et vindue" eller "bar over 5 min
   forsinket".
6. **Salgsdagen** (§4c) regnes på den forskelsjusterede serie: close af dagens sidste
   RTH-1m-bar < open af dens første (``sessions.rth_mask``, som giver 12:00 CT på
   kortdage). Lighed er ikke en salgsdag. Har forrige RTH-dag ingen RTH-barer i serien
   (NQ's første nat: 2015-12-31; MNQ's første nat: 2019-05-03), er salgsdagen ukendt, og
   natten er kun med i "alle". Det tælles.
7. **Punktforskellen** er ``open_adj(udgang) − open_adj(indgang)`` på
   ``k2.forskelsjuster`` af hele serien. ``L_n`` er den ujusterede open af indgangsbaren.
   ``netto_usd_n = Δpt × (29.138 / L_n) × 2 − 2,85`` (§4f).
8. **Middel pr. kalendernat** = middel netto × handlede nætter / alle XNYS-nætter i
   perioden.
9. **N-nat** (§6): starten er minutter efter 17:00 CT på gitteret 0 … 930 − længde, og
   vinduet [s, s + længde] må ikke overlappe variantens vindue. At røre det (slutte, når
   det starter, eller starte, når det slutter) er ikke overlap. [tvivl] For V1 er det
   752 mulige starter, for V2 572. Trækningen er ``default_rng([9600, gentagelse,
   længde]).integers(0, antal starter, (alle nætter, 64))``. Rækken er nattens plads blandt
   alle XNYS-nætter i serien, og den første af de 64 kandidater, der kan udføres efter
   §4b's regel i begge ender, bruges ("trækkes igen"). Er ingen af de 64 udførbare,
   stopper koden. "Alle" og "salg" med samme længde læser samme række og får samme start.
10. **N-nat's normering** bruger den trukne indgangsbars egen ujusterede open som L
    [tvivl]. Den anden læsning er variantens L_n. Forskellen er højst en brøkdel af en
    procent af en nats bevægelse.
11. **Westfall-Young** er ``k2.westfall_young`` uændret: énsidet, sd med ddof = 1, R = 500,
    på middel netto pr. handlet nat.
12. **σ_nat** (§7): summen går over barerne i [indgangsbar, udgangsbar) for variantens
    nætter. ``Δclose`` er mod forrige bar i serien, også for den første bar i vinduet.
    [tvivl] P&L'en går fra indgangsbarens open; at bruge ``close − open`` for den første
    bar ville give et lidt mindre σ.
13. **Styrken** (§7) er en normalapproksimation og regnes to måder [tvivl]:
    ``styrke_FWE = Φ(√n × effekt / σ_nat − 2,2340)`` for testen mod N-nat, hvor effekten
    læses som overskud over en tilfældig time (omkostningen går ud, fordi N-nat betaler
    den samme), og ``styrke_CI = Φ(√n × (effekt − 2,85) / σ_nat − 1,96)`` for CI-nedre > 0.
    2,2340 er 3,0756 − z₀,₈₀, og ved MDE_sidak4 er styrke_FWE 80%. Effekterne $8,6 og $17,2
    er brutto pr. nat ved dagens niveau.
14. **Omkostningen i bp** (§11.4) er ``2,85 / (2 × L) × 10⁴`` ved årets median af L_n for
    variantens nætter.
15. **Long hele natten** (§6): open af første bar fra 17:00 CT til open af første bar fra
    08:30 CT, samme 5-minutters regel for sig selv. Rapporteres for de nætter, der indgår i
    "alle", og for salgsnætterne. Den udelukker ikke nætter i varianterne.
16. **Før og efter publiceringen** (§9) deles ved dag d: d < 2020-03-01 og d ≥ 2020-03-01.
17. **$3,10** (§9): N-nat flyttes med samme omkostning, så t_v og p_FWE er de samme som ved
    $2,85; kun intervallet og dermed rækken i §8 kan flytte sig.
18. **Break-even** (§9): ``c_middel`` = middel brutto. ``c_CI`` = nedre grænse i
    t-intervallet for brutto, fordi der er én handel pr. nat, så netto er brutto − c.
19. **Terciler** (§9) [tvivl]: salgsnætterne deles i tre lige store grupper efter forrige
    RTH-dags afkast i procent (``np.quantile`` ved 1/3 og 2/3). Mest negativ er "største
    salg". Middel brutto med CI pr. gruppe for V1 · salg og V2 · salg.
20. **Hit ratio** er andelen af nætter med netto > 0 (og brutto > 0). **Gevinst/tab** er
    middel af gevinsterne over |middel af tabene|; præcis 0 indgår i ingen af dem.
21. **Største tab inden for vinduet** (§9): ``(close_adj − open_adj(indgang)) × skala × 2 −
    2,85`` ved hver bars close i [indgangsbar, udgangsbar) og nattens netto ved udgangen.
    ``min(0, …)`` pr. nat. Hele omkostningen trækkes ved indgangen, som i kandidat 5.
22. **Ruller i vinduet** er nætter, hvor indgangs- og udgangsbaren har forskelligt
    ``instrument_id``.
23. **Kandidat 5's regressionstjek** (§11.3) er ``k5.regressionstjek`` (kandidat 1-4) og
    ``k5.handler`` / ``k5.variant_tal`` for "1m · uden middag", uændret.
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
from research import b4_k1_trinA as trinA  # noqa: E402
from research import b4_k2_nowick as k2  # noqa: E402
from research import b4_k4_emt as k4  # noqa: E402
from research import b4_k5_vwap_trend as k5  # noqa: E402
from research.normal import norm  # noqa: E402
from research.stats import mean_ci_t  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "output"
PREREG = ROOT / "research" / "prereg" / "b4_k6_overnight.md"
SCREENING = ROOT / "research" / "output" / "b4_screening.md"
# Den rigtige kørsel sker kun når disse er committet og uændrede.
COMMITTEDE = (
    Path(__file__).resolve(), ROOT / "tests" / "test_b4_k6_overnight.py", PREREG, SCREENING,
    ROOT / "research" / "b4_k5_vwap_trend.py", ROOT / "research" / "b4_k4_emt.py",
    ROOT / "research" / "b4_k2_nowick.py", ROOT / "research" / "b4_k1_trinA.py",
    ROOT / "research" / "b4_k1_optaelling.py",
    ROOT / "research" / "stats.py", ROOT / "research" / "normal.py",
    ROOT / "data" / "holdout.py", ROOT / "data" / "sessions.py",
)

CT = k1.CT
NY = sessions.ET
MIN_NS = 60 * 10**9

HOVED, KONTROL = "NQ.v.0", "MNQ.v.0"                       # §3, svar 3A
PERIODE = {HOVED: ("2016-01-01", "2024-01-01"), KONTROL: ("2019-05-06", "2024-01-01")}

NAT_START = pd.Timedelta(hours=17)       # §4a: 17:00 CT dagen før
NAT_SLUT = pd.Timedelta(hours=8, minutes=30)
NAT_MIN = 930                            # 17:00 → 08:30 CT
MAKS_FORSINK_MIN = 5                     # §4b

# §4b, New York-tid: (indgang, udgang) som tid efter midnat på dag d.
VINDUER = {"V1": (pd.Timedelta(hours=2), pd.Timedelta(hours=3)),
           "V2": (pd.Timedelta(hours=1, minutes=30), pd.Timedelta(hours=3, minutes=30))}
ALLE, SALG = "alle", "salg"
VARIANTER = (("V1", ALLE), ("V1", SALG), ("V2", ALLE), ("V2", SALG))
PUNKTER = ("V1_ind", "V1_ud", "V2_ind", "V2_ud")

MNQ_USD_PR_POINT = trinA.MNQ_USD_PR_POINT    # 2
NQ_NIVEAU = k1.NQ_NIVEAU                     # 29.138, §4f
OMK_USD = 2.85                               # §4e
OMK_DIAGNOSE_USD = 3.10                      # §4e, §9

NNAT_REPS = 500                          # §6, sænkes ikke
NNAT_SEED = 9600
NNAT_KANDIDATER = 64                     # læsning 9

# §7: énsidet α = 0,05 med Šidák 4 og tosidet 95%, begge + z_0,80.
Z_SIDAK4 = 3.0756
Z_CI = 2.8016
Z_80 = float(norm.ppf(0.80))
EFFEKTER_USD = (8.6, 17.2)               # §7: artiklens effekt og det dobbelte
PUBLICERET = pd.Timestamp("2020-03-01")  # §9

# §11.3: kandidat 5 in-sample, 1m · uden middag.
REGRESSION_K5_HANDLER_N = 14831
REGRESSION_K5_NETTO_USD = 41.07


# ---------------------------------------------------------------------------
# Serien og nætterne, §3 og §4a
# ---------------------------------------------------------------------------

def serie(symbol: str) -> pd.DataFrame:
    """1m-serien, kun gennem holdout-modulet. Læsning 3: MNQ skæres ikke."""
    return holdout.load_in_sample(symbol)


def xnys_dage(symbol: str) -> pd.DatetimeIndex:
    return k1.rth_dage(*PERIODE[symbol])


def _plan() -> pd.DatetimeIndex:
    return pd.DatetimeIndex(sessions._xnys().schedule.index).as_unit("ns")


def naetter(dage: pd.DatetimeIndex) -> pd.DataFrame:
    """§4a og læsning 1: pr. XNYS-dag d nattens start og slut (UTC) og forrige RTH-dag."""
    d = pd.DatetimeIndex(dage).as_unit("ns").normalize()
    start = (d - pd.Timedelta(days=1) + NAT_START).tz_localize(CT).tz_convert("UTC")
    slut = (d + NAT_SLUT).tz_localize(CT).tz_convert("UTC")
    plan = _plan()
    pos = plan.get_indexer(d)
    if (pos < 1).any():
        raise ValueError("en dag er ikke en XNYS-dag, eller kalenderen dækker ikke dagen før")
    laengde = (slut - start) / pd.Timedelta(minutes=1)
    if not (np.asarray(laengde) == NAT_MIN).all():
        raise ValueError("en nat er ikke 930 minutter (læsning 2)")
    return pd.DataFrame({"start": start, "slut": slut, "forrige": plan[pos - 1]}, index=d)


def vindue_tider(dage: pd.DatetimeIndex, vindue: str) -> tuple[pd.DatetimeIndex,
                                                                 pd.DatetimeIndex]:
    """§4b: det nominelle indgangs- og udgangstidspunkt i UTC, sat i New York-tid."""
    d = pd.DatetimeIndex(dage).as_unit("ns").normalize()
    a, b = VINDUER[vindue]
    return ((d + a).tz_localize(NY).tz_convert("UTC"),
            (d + b).tz_localize(NY).tz_convert("UTC"))


def vindue_min(vindue: str) -> tuple[int, int]:
    """Vinduets start og slut i minutter efter 17:00 CT. CT er New York − 1 time."""
    a, b = VINDUER[vindue]
    f = lambda x: int((x - pd.Timedelta(hours=1) + pd.Timedelta(hours=24) - NAT_START)
                      / pd.Timedelta(minutes=1))
    return f(a), f(b)


def vindue_laengde(vindue: str) -> int:
    a, b = vindue_min(vindue)
    return b - a


def udfoer(t_ns: np.ndarray, nominel_ns) -> tuple[np.ndarray, np.ndarray]:
    """Læsning 4: (indeks for første bar fra det nominelle tidspunkt, forsinkelse i min).
    Uden en bar efter tidspunktet er forsinkelsen uendelig."""
    nom = np.asarray(nominel_ns, dtype=np.int64)
    i = np.searchsorted(t_ns, nom, side="left")
    findes = i < len(t_ns)
    ic = np.minimum(i, len(t_ns) - 1)
    forsink = np.where(findes, (t_ns[ic] - nom) / MIN_NS, np.inf)
    return ic, forsink


def _ns(index) -> np.ndarray:
    return pd.DatetimeIndex(index).as_unit("ns").asi8.copy()


# ---------------------------------------------------------------------------
# Grundlaget
# ---------------------------------------------------------------------------

@dataclass
class Grundlag:
    symbol: str
    dage: pd.DatetimeIndex           # alle nætter: én pr. XNYS-dag d
    t_ns: np.ndarray                 # barernes start, UTC ns
    o: np.ndarray                    # forskelsjusteret open
    c: np.ndarray                    # forskelsjusteret close
    o_raa: np.ndarray                # ujusteret open
    iid: np.ndarray
    nat_start_ns: np.ndarray
    nat_slut_ns: np.ndarray
    forrige: pd.DatetimeIndex
    salg: np.ndarray                 # 1 salgsdag, 0 ikke, nan ukendt
    rth_afkast_pct: np.ndarray       # forrige RTH-dags afkast i %
    pkt: dict                        # navn → (serieindeks, forsinkelse i min)
    med: np.ndarray                  # natten indgår
    grund: np.ndarray                # "" eller grunden til udelukkelsen
    ruller: pd.DataFrame
    info: dict = field(default_factory=dict)

    @property
    def n_alle(self) -> int:
        return len(self.dage)

    @property
    def aar(self) -> np.ndarray:
        return self.dage.year.to_numpy()

    def maske(self, v: tuple) -> np.ndarray:
        if v[1] == ALLE:
            return self.med.copy()
        return self.med & (self.salg == 1)


def _rth_tabel(df: pd.DataFrame) -> dict:
    """ET-dato → (første RTH-bar, sidste RTH-bar), serieindeks."""
    m = sessions.rth_mask(df.index, 1)
    pos = np.flatnonzero(m)
    if len(pos) == 0:
        return {}
    et = k1._et_dag(df.index[pos]).asi8
    _, foerste = np.unique(et, return_index=True)
    _, sidste_r = np.unique(et[::-1], return_index=True)
    sidste = len(et) - 1 - sidste_r
    return {int(et[f]): (int(pos[f]), int(pos[s])) for f, s in zip(foerste, sidste)}


def salgsdage(df: pd.DataFrame, adj: pd.DataFrame, forrige: pd.DatetimeIndex
              ) -> tuple[np.ndarray, np.ndarray]:
    """§4c og læsning 6: (salg 1/0/nan, afkast i %) for hver forrige RTH-dag."""
    tab = _rth_tabel(df)
    o, c = adj["open"].to_numpy(float), adj["close"].to_numpy(float)
    o_raa = df["open"].to_numpy(float)
    salg = np.full(len(forrige), np.nan)
    afk = np.full(len(forrige), np.nan)
    for j, p in enumerate(pd.DatetimeIndex(forrige).as_unit("ns").asi8):
        if int(p) in tab:
            f, s = tab[int(p)]
            salg[j] = 1.0 if c[s] < o[f] else 0.0
            afk[j] = (c[s] - o[f]) / o_raa[f] * 100.0
    return salg, afk


def byg_grundlag(df: pd.DataFrame, dage: pd.DatetimeIndex, symbol: str = "") -> Grundlag:
    """Nætterne, udførelsespunkterne, salgsdagene og udelukkelserne. Ingen P&L."""
    if not df.index.is_monotonic_increasing or df.index.has_duplicates:
        raise ValueError("serien skal være sorteret og uden dubletter")
    adj, ruller = k2.forskelsjuster(df)
    t_ns = _ns(df.index)
    nt = naetter(dage)
    s_ns, e_ns = _ns(nt["start"]), _ns(nt["slut"])
    pkt = {}
    for w in VINDUER:
        ind, ud = vindue_tider(nt.index, w)
        pkt[f"{w}_ind"] = udfoer(t_ns, _ns(ind))
        pkt[f"{w}_ud"] = udfoer(t_ns, _ns(ud))
    pkt["nat_ind"] = udfoer(t_ns, s_ns)
    pkt["nat_ud"] = udfoer(t_ns, e_ns)

    def antal_i(a_ns, b_ns):
        return np.searchsorted(t_ns, b_ns, side="right") - np.searchsorted(t_ns, a_ns)

    i_natten = np.searchsorted(t_ns, e_ns) - np.searchsorted(t_ns, s_ns)
    tom_vindue = np.zeros(len(nt), dtype=bool)
    for w in VINDUER:
        ind, ud = vindue_tider(nt.index, w)
        tom_vindue |= antal_i(_ns(ind), _ns(ud)) == 0
    forsinket = np.zeros(len(nt), dtype=bool)
    for p in PUNKTER:
        forsinket |= pkt[p][1] > MAKS_FORSINK_MIN
    grund = np.full(len(nt), "", dtype=object)
    grund[forsinket] = "bar over 5 min forsinket"
    grund[forsinket & tom_vindue] = "ingen barer i et vindue"
    grund[forsinket & (i_natten == 0)] = "ingen barer i natten"
    med = ~forsinket

    salg, afk = salgsdage(df, adj, pd.DatetimeIndex(nt["forrige"]))
    iid = (df["instrument_id"].to_numpy() if "instrument_id" in df.columns
           else np.zeros(len(df), dtype=np.int64))
    g = Grundlag(symbol=symbol, dage=pd.DatetimeIndex(nt.index), t_ns=t_ns,
                 o=adj["open"].to_numpy(float), c=adj["close"].to_numpy(float),
                 o_raa=df["open"].to_numpy(float), iid=iid,
                 nat_start_ns=s_ns, nat_slut_ns=e_ns,
                 forrige=pd.DatetimeIndex(nt["forrige"]), salg=salg, rth_afkast_pct=afk,
                 pkt=pkt, med=med, grund=grund, ruller=ruller)
    g.info = {
        "symbol": symbol, "n_1m": len(df),
        "foerste_bar_ct": df.index[0].tz_convert(CT).strftime("%Y-%m-%d %H:%M") if len(df)
        else "", "naetter_alle_n": len(nt),
        "naetter_med_n": int(med.sum()),
        **{f"udelukket_{gr}_n": int((grund == gr).sum())
           for gr in ("ingen barer i natten", "ingen barer i et vindue",
                      "bar over 5 min forsinket")},
        "salg_ukendt_n": int((med & np.isnan(salg)).sum()),
        "salgsdage_n": int((med & (salg == 1)).sum()),
        "salg_kendt_n": int((med & ~np.isnan(salg)).sum()),
        "ruller_n": len(ruller),
        "rul_tider_ct": ", ".join(sorted(set(ruller["tid_ct"].str[11:]))) if len(ruller)
        else "",
    }
    return g


# ---------------------------------------------------------------------------
# §4f: handlen pr. nat
# ---------------------------------------------------------------------------

def handel(g: Grundlag, vindue: str, omk: float = OMK_USD) -> dict:
    """Pr. nat (alle nætter, også de udelukkede): Δpt, L_n, skala, brutto og netto."""
    ind, ud = g.pkt[f"{vindue}_ind"][0], g.pkt[f"{vindue}_ud"][0]
    pt = g.o[ud] - g.o[ind]
    L = g.o_raa[ind]
    skala = NQ_NIVEAU / L
    brutto = pt * skala * MNQ_USD_PR_POINT
    return {"ind": ind, "ud": ud, "pt": pt, "L": L, "skala": skala, "brutto_usd": brutto,
            "netto_usd": brutto - omk, "nominelt_usd": pt * MNQ_USD_PR_POINT - omk}


def lang_hele_natten(g: Grundlag, omk: float = OMK_USD) -> dict:
    """§6 og læsning 15: long 17:00 → 08:30 CT pr. nat, og om den kan udføres."""
    ind, f_ind = g.pkt["nat_ind"]
    ud, f_ud = g.pkt["nat_ud"]
    pt = g.o[ud] - g.o[ind]
    skala = NQ_NIVEAU / g.o_raa[ind]
    brutto = pt * skala * MNQ_USD_PR_POINT
    return {"udfoerbar": (f_ind <= MAKS_FORSINK_MIN) & (f_ud <= MAKS_FORSINK_MIN),
            "brutto_usd": brutto, "netto_usd": brutto - omk}


# ---------------------------------------------------------------------------
# §6: N-nat
# ---------------------------------------------------------------------------

@dataclass
class NatGitter:
    """Pr. nat og minut efter 17:00 CT (0 … 930): bar og om den kan bruges."""
    idx: np.ndarray
    ok: np.ndarray


def nat_gitter(g: Grundlag) -> NatGitter:
    nom = g.nat_start_ns[:, None] + np.arange(NAT_MIN + 1, dtype=np.int64)[None, :] * MIN_NS
    i, f = udfoer(g.t_ns, nom.ravel())
    return NatGitter(idx=i.reshape(nom.shape), ok=(f <= MAKS_FORSINK_MIN).reshape(nom.shape))


def nnat_starter(vindue: str) -> np.ndarray:
    """Læsning 9: mulige starter i minutter efter 17:00 CT, uden overlap med vinduet."""
    a, b = vindue_min(vindue)
    L = b - a
    s = np.arange(0, NAT_MIN - L + 1)
    return s[(s + L <= a) | (s >= b)]


@dataclass
class NNatVaerdier:
    vindue: str
    starter: np.ndarray              # mulige starter, minutter efter 17:00 CT
    brutto: np.ndarray               # (nætter, starter)
    ok: np.ndarray                   # (nætter, starter): kan udføres i begge ender


def nnat_vaerdier(g: Grundlag, gitter: NatGitter, vindue: str) -> NNatVaerdier:
    """Brutto for hver mulig start hver nat. Læsning 10: L fra den trukne indgangsbar."""
    S = nnat_starter(vindue)
    L = vindue_laengde(vindue)
    i0, i1 = gitter.idx[:, S], gitter.idx[:, S + L]
    ok = gitter.ok[:, S] & gitter.ok[:, S + L]
    brutto = (g.o[i1] - g.o[i0]) * (NQ_NIVEAU / g.o_raa[i0]) * MNQ_USD_PR_POINT
    return NNatVaerdier(vindue=vindue, starter=S, brutto=brutto, ok=ok)


def nnat_traek(nv: NNatVaerdier, rep: int, behov: np.ndarray | None = None) -> np.ndarray:
    """Læsning 9: søjle i ``nv.starter`` pr. nat, deterministisk pr. (gentagelse, nat,
    længde). −1 hvor ingen af kandidaterne kan udføres; det må kun ske uden for ``behov``."""
    n = nv.ok.shape[0]
    rng = np.random.default_rng([NNAT_SEED, rep, vindue_laengde(nv.vindue)])
    kand = rng.integers(0, len(nv.starter), size=(n, NNAT_KANDIDATER))
    okk = nv.ok[np.arange(n)[:, None], kand]
    har = okk.any(axis=1)
    valg = np.where(har, kand[np.arange(n), np.argmax(okk, axis=1)], -1)
    if behov is not None and (behov & ~har).any():
        raise RuntimeError(f"N-nat: ingen udførbar start blandt {NNAT_KANDIDATER} "
                           f"kandidater for {int((behov & ~har).sum())} nætter")
    return valg


def nnat_gentagelse(g: Grundlag, nvs: dict, rep: int, omk: float = OMK_USD) -> dict:
    """Én gentagelse: middel netto pr. handlet nat for hver variant."""
    ud = {}
    for w, nv in nvs.items():
        valg = nnat_traek(nv, rep, behov=g.med)
        netto = nv.brutto[np.arange(len(valg)), np.maximum(valg, 0)] - omk
        for v in VARIANTER:
            if v[0] == w:
                m = g.maske(v)
                ud[v] = float(netto[m].mean()) if m.any() else float("nan")
    return ud


def forbered_nnat(g: Grundlag) -> dict:
    gitter = nat_gitter(g)
    return {w: nnat_vaerdier(g, gitter, w) for w in VINDUER}


# ---------------------------------------------------------------------------
# §7: σ_nat, MDE og styrke — uden udfald
# ---------------------------------------------------------------------------

def sigma_nat(g: Grundlag, v: tuple) -> float:
    """§7 og læsning 12: ``2 × √(middel_n[(29.138 / L_n)² × Σ_t Δclose_t²])``."""
    m = g.maske(v)
    if not m.any():
        return float("nan")
    ind, ud = g.pkt[f"{v[0]}_ind"][0], g.pkt[f"{v[0]}_ud"][0]
    dc = np.r_[0.0, np.diff(g.c)]
    cs = np.r_[0.0, np.cumsum(dc * dc)]
    s = cs[ud] - cs[ind]
    skala = NQ_NIVEAU / g.o_raa[ind]
    return 2.0 * math.sqrt(float(np.mean((skala ** 2 * s)[m])))


def mde(sigma: float, n: int, z: float = Z_SIDAK4) -> float:
    """§7: ``z × σ_nat / √n``."""
    return z * sigma / math.sqrt(n) if n > 0 else float("inf")


def styrke_fwe(sigma: float, n: int, effekt: float) -> float:
    """Læsning 13: testen mod N-nat, Šidák 4."""
    if n <= 0 or not sigma > 0:
        return float("nan")
    return float(norm.cdf(math.sqrt(n) * effekt / sigma - (Z_SIDAK4 - Z_80)))


def styrke_ci(sigma: float, n: int, effekt: float, omk: float = OMK_USD) -> float:
    """Læsning 13: CI-nedre > 0 for netto = effekt − omkostning."""
    if n <= 0 or not sigma > 0:
        return float("nan")
    return float(norm.cdf(math.sqrt(n) * (effekt - omk) / sigma - (Z_CI - Z_80)))


# ---------------------------------------------------------------------------
# §8
# ---------------------------------------------------------------------------

def beslutning(raekker: dict, alfa: float = 0.05) -> dict:
    """§8, mekanisk. ``raekker`` er {variant: {"p_FWE", "ci95_lo"}}. Første række der
    passer, gælder."""
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
                "tekst": "Parkeres som \"timen er særlig, men betaler ikke omkostningen\""}
    if ci:
        return {"raekke": 3, "variant": None, "kandidater": ci,
                "tekst": "Parkeres: gevinsten er ikke knyttet til Europas åbning"}
    return {"raekke": 4, "variant": None, "kandidater": [], "tekst": "Kandidat 6 parkeres"}


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
    """Læsning 20: (hit ratio i %, gevinst/tab-forhold)."""
    x = np.asarray(x, dtype=float)
    if len(x) == 0:
        return float("nan"), float("nan")
    v, t = x[x > 0], x[x < 0]
    forhold = float(v.mean() / abs(t.mean())) if len(v) and len(t) else float("nan")
    return 100.0 * len(v) / len(x), forhold


def stoerste_tab(g: Grundlag, h: dict, m: np.ndarray, omk: float = OMK_USD) -> np.ndarray:
    """Læsning 21: ``min(0, …)`` pr. nat i ``m``, mark-to-market på 1m-close."""
    ind, ud = h["ind"][m], h["ud"][m]
    n_bar = ud - ind
    if len(ind) == 0:
        return np.zeros(0)
    if (n_bar < 1).any():
        raise ValueError("et vindue uden barer")
    nat = np.repeat(np.arange(len(ind)), n_bar)
    start = np.r_[0, np.cumsum(n_bar)[:-1]]
    i = np.arange(n_bar.sum()) - np.repeat(start, n_bar) + np.repeat(ind, n_bar)
    v = (g.c[i] - g.o[ind][nat]) * h["skala"][m][nat] * MNQ_USD_PR_POINT - omk
    laveste = np.minimum.reduceat(v, start)
    return np.minimum(0.0, np.minimum(laveste, h["netto_usd"][m]))


def variant_tal(g: Grundlag, v: tuple, h: dict) -> dict:
    """§10's hovedtabel uden nulmodellen, og nætterne til diagnoserne."""
    m = g.maske(v)
    b, n = h["brutto_usd"][m], h["netto_usd"][m]
    lo, hi = _ci(n)
    return {"variant": v, "naetter_n": int(m.sum()),
            "middel_brutto_usd": _middel(b), "middel_netto_usd": _middel(n),
            "ci95_lo": lo, "ci95_hi": hi,
            "netto_usd_pr_kalendernat": _middel(n) * m.sum() / g.n_alle,
            "_m": m, "_brutto": b, "_netto": n}


def diagnoser(g: Grundlag, hd: dict, tal: dict, null_t: dict | None = None) -> dict:
    """§9. ``null_t`` er {variant: p_FWE}, så rækken ved $3,10 kan regnes."""
    ud = {"variant": {}, "aar": [], "terciler": [], "hele_natten": {}}
    d = g.dage
    for v in VARIANTER:
        t, h = tal[v], hd[v[0]]
        m = t["_m"]
        b, n = t["_brutto"], t["_netto"]
        foer = (d < PUBLICERET)[m]
        nom = h["nominelt_usd"][m]
        n310 = b - OMK_DIAGNOSE_USD
        hn, fn = hit(n)
        hb, fb = hit(b)
        tab = stoerste_tab(g, h, m)
        r = {"naetter_foer_n": int(foer.sum()), "naetter_efter_n": int((~foer).sum())}
        for navn, s in (("foer", foer), ("efter", ~foer)):
            lo, hi = _ci(n[s])
            r.update({f"netto_{navn}": _middel(n[s]), f"netto_{navn}_lo": lo,
                      f"netto_{navn}_hi": hi})
        lo, hi = _ci(n310)
        r.update({"netto_310": _middel(n310), "netto_310_lo": lo, "netto_310_hi": hi})
        lo, hi = _ci(nom)
        r.update({"nominelt": _middel(nom), "nominelt_lo": lo, "nominelt_hi": hi})
        r.update({"breakeven_middel": _middel(b), "breakeven_CI": _ci(b)[0]})
        r.update({"hit_netto_pct": hn, "gevinst_tab_netto": fn,
                  "hit_brutto_pct": hb, "gevinst_tab_brutto": fb})
        r.update({f"netto_p{q}": _p(n, q) for q in (1, 5, 50, 95, 99)})
        r.update({"netto_vaerst": float(n.min()) if len(n) else float("nan"),
                  "netto_bedst": float(n.max()) if len(n) else float("nan")})
        r.update({f"tab_i_vindue_p{q}": _p(tab, q) for q in (1, 5, 50)})
        r["tab_i_vindue_vaerst"] = float(tab.min()) if len(tab) else float("nan")
        ud["variant"][v] = r
        for a in sorted(set(g.aar.tolist())):
            s = (g.aar == a)[m]
            lo, hi = _ci(n[s])
            ud["aar"].append({"variant": v, "aar": a, "naetter_n": int(s.sum()),
                              "netto": _middel(n[s]), "netto_lo": lo, "netto_hi": hi,
                              "nominelt": _middel(nom[s])})
        if v[1] == SALG and m.sum() >= 3:
            x = g.rth_afkast_pct[m]
            q1, q2 = np.quantile(x, [1 / 3, 2 / 3])
            for navn, s in (("største salg", x <= q1), ("mellem", (x > q1) & (x <= q2)),
                            ("mindste salg", x > q2)):
                lo, hi = _ci(b[s])
                ud["terciler"].append({"variant": v, "gruppe": navn, "naetter_n": int(s.sum()),
                                       "rth_afkast_pct_median": _p(x[s], 50),
                                       "brutto": _middel(b[s]), "brutto_lo": lo,
                                       "brutto_hi": hi})
    hn = lang_hele_natten(g)
    for b_ in (ALLE, SALG):
        m = g.maske(("V1", b_)) & hn["udfoerbar"]
        lo, hi = _ci(hn["netto_usd"][m])
        ud["hele_natten"][b_] = {"naetter_n": int(m.sum()),
                                 "brutto": _middel(hn["brutto_usd"][m]),
                                 "netto": _middel(hn["netto_usd"][m]), "netto_lo": lo,
                                 "netto_hi": hi}
    if null_t is not None:
        ud["beslutning_310"] = beslutning({v: {"p_FWE": null_t[v],
                                               "ci95_lo": ud["variant"][v]["netto_310_lo"]}
                                           for v in VARIANTER})
    return ud


def forbered(g: Grundlag) -> dict:
    return {w: handel(g, w) for w in VINDUER}


def analyse(g: Grundlag, n_reps: int = NNAT_REPS) -> dict:
    """Én serie: tallene, N-nat, Westfall-Young, §8 og diagnoserne."""
    hd = forbered(g)
    tal = {v: variant_tal(g, v, hd[v[0]]) for v in VARIANTER}
    nvs = forbered_nnat(g)
    null = [nnat_gentagelse(g, nvs, rep) for rep in range(n_reps)]
    wy = k2.westfall_young({v: tal[v]["middel_netto_usd"] for v in VARIANTER},
                           {v: np.array([r[v] for r in null]) for v in VARIANTER})
    for v in VARIANTER:
        tal[v].update({f"N_nat_{k}": wy["pr_variant"][v][k] for k in ("p5", "p50", "p95")})
        tal[v]["t_v"] = wy["pr_variant"][v]["t"]
        tal[v]["p_FWE"] = wy["pr_variant"][v]["p_FWE"]
        sig = sigma_nat(g, v)
        tal[v].update({"sigma_nat": sig, "MDE_sidak4": mde(sig, tal[v]["naetter_n"]),
                       "MDE_CI": mde(sig, tal[v]["naetter_n"], Z_CI)})
    afg = beslutning({v: {"p_FWE": tal[v]["p_FWE"], "ci95_lo": tal[v]["ci95_lo"]}
                      for v in VARIANTER})
    diag = diagnoser(g, hd, tal, {v: tal[v]["p_FWE"] for v in VARIANTER})
    return {"symbol": g.symbol, "tal": tal, "wy": wy, "beslutning": afg, "diag": diag,
            "optaelling": optaelling(g, nvs), "R": n_reps}


def koer(n_reps: int = NNAT_REPS) -> dict:
    """Den rigtige kørsel: NQ afgør, MNQ er kontrol."""
    ud = {}
    for sym in (HOVED, KONTROL):
        g = byg_grundlag(serie(sym), xnys_dage(sym), sym)
        ud[sym] = analyse(g, n_reps)
    return ud


# ---------------------------------------------------------------------------
# §11.4: optællingen uden udfald
# ---------------------------------------------------------------------------

def optaelling(g: Grundlag, nvs: dict | None = None) -> dict:
    """§11.4: nætter, udelukkelser, forsinkelser, ruller, salgsdage, L_n, σ_nat, MDE og
    styrke. Ingen punktforskel i en handel indgår: ingen P&L, ingen hit ratio, intet udfald.
    (Salgsdagen er forrige RTH-dags fortegn og σ_nat markedets egen svingning.)"""
    varianter, aar_rows = [], []
    for v in VARIANTER:
        m = g.maske(v)
        n = int(m.sum())
        ind_i, f_ind = g.pkt[f"{v[0]}_ind"]
        ud_i, f_ud = g.pkt[f"{v[0]}_ud"]
        L = g.o_raa[ind_i]
        sig = sigma_nat(g, v)
        r = {"variant": _vnavn(v), "naetter_n": n,
             "forsinket_ind_n": int((m & (f_ind > 0)).sum()),
             "forsinket_ud_n": int((m & (f_ud > 0)).sum()),
             "ruller_i_vinduet_n": int((m & (g.iid[ind_i] != g.iid[ud_i])).sum()),
             "sigma_nat": sig, "MDE_sidak4": mde(sig, n), "MDE_CI": mde(sig, n, Z_CI)}
        for e in EFFEKTER_USD:
            r[f"styrke_FWE_{e}"] = styrke_fwe(sig, n, e)
            r[f"styrke_CI_{e}"] = styrke_ci(sig, n, e)
        varianter.append(r)
        for a in sorted(set(g.aar.tolist())):
            s = m & (g.aar == a)
            med_L = _p(L[s], 50)
            aar_rows.append({"variant": _vnavn(v), "aar": a, "naetter_n": int(s.sum()),
                             "L_median": med_L,
                             "omk_bp": OMK_USD / (2.0 * med_L) * 1e4 if s.any()
                             else float("nan")})
    udel = [{"dag": str(d.date()), "grund": gr} for d, gr in zip(g.dage, g.grund) if gr]
    rul_v = g.ruller.copy()
    if len(rul_v):
        t = pd.to_datetime(rul_v["tid_utc"]).dt.tz_convert(NY)
        rul_v["tid_ny"] = t.dt.strftime("%Y-%m-%d %H:%M")
    hn_ok = lang_hele_natten(g)["udfoerbar"]
    o = {"serie": dict(g.info), "varianter": varianter, "aar": aar_rows,
         "udelukket": udel, "ruller": rul_v,
         "salg_andel_pct": 100.0 * g.info["salgsdage_n"] / g.info["salg_kendt_n"]
         if g.info["salg_kendt_n"] else float("nan"),
         "hele_natten_udfoerbar_n": int((g.med & hn_ok).sum())}
    if nvs is not None:
        o["nnat"] = {w: {"starter_n": len(nv.starter),
                         "udfoerbare_pct_p1": _p(100 * nv.ok[g.med].mean(axis=1), 1),
                         "udfoerbare_pct_p50": _p(100 * nv.ok[g.med].mean(axis=1), 50)}
                     for w, nv in nvs.items()}
    return o


# ---------------------------------------------------------------------------
# Formatering
# ---------------------------------------------------------------------------

def _vnavn(v) -> str:
    return f"{v[0]} · {v[1]}"


def _rel(sti: Path) -> str:
    return Path(sti).resolve().relative_to(ROOT.resolve()).as_posix()


def _usd(x, nd: int = 2) -> str:
    return k2._t(x, nd)


def _ci_txt(lo, hi, nd: int = 2) -> str:
    return f"[{k2._t(lo, nd)}; {k2._t(hi, nd)}]"


def _pct(x, nd: int = 0) -> str:
    return f"{k2._t(100 * x, nd)}%"


def optaelling_md(oo: dict, meta: dict) -> str:
    _t = k2._t
    dele = [
        "# B4 kandidat 6 — optælling uden udfald (§11.4)\n",
        f"Kørt {meta['koert_utc']} UTC fra commit `{meta['head'][:7]}`, "
        f"{k4._arbejdskopi(COMMITTEDE)}. **Ingen P&L, ingen hit ratio og intet udfald er "
        f"regnet.** Nætterne og udførelsespunkterne er bestemt af kalenderen og barernes "
        f"tider alene. σ_nat er markedets egen svingning i vinduet (§7), og salgsdagen er "
        f"forrige RTH-dags fortegn (§4c).\n",
    ]
    for sym, o in oo.items():
        s = o["serie"]
        rolle = "hovedserie, afgør" if sym == HOVED else "kontrol, afgør intet"
        dele += [
            f"## {sym} — {rolle}\n",
            f"`data.holdout.load_in_sample(\"{sym}\")`: {_t(s['n_1m'])} 1m-barer, første bar "
            f"{s['foerste_bar_ct']} CT. Nætter for XNYS-dagene {PERIODE[sym][0]} → "
            f"2023-12-29.\n",
            "| emne | antal |", "|---|---|",
            f"| nætter i alt (XNYS-dage) | {_t(s['naetter_alle_n'])} |",
            f"| udelukket, ingen barer i natten | {_t(s['udelukket_ingen barer i natten_n'])} |",
            f"| udelukket, ingen barer i et vindue | "
            f"{_t(s['udelukket_ingen barer i et vindue_n'])} |",
            f"| udelukket, bar over 5 min forsinket | "
            f"{_t(s['udelukket_bar over 5 min forsinket_n'])} |",
            f"| **nætter der indgår** | **{_t(s['naetter_med_n'])}** |",
            f"| salgsdag ukendt (forrige RTH-dag uden barer) | {_t(s['salg_ukendt_n'])} |",
            f"| salgsdage / kendte | {_t(s['salgsdage_n'])} / {_t(s['salg_kendt_n'])} = "
            f"**{_t(o['salg_andel_pct'], 1)}%** |",
            f"| ruller i serien | {_t(s['ruller_n'])}, kl. {s['rul_tider_ct']} CT |",
            f"| long hele natten udførbar (af dem der indgår) | "
            f"{_t(o['hele_natten_udfoerbar_n'])} |",
            "",
        ]
        if o["udelukket"]:
            dele += ["Udelukkede nætter (dag d):\n", "| dag | grund |", "|---|---|"]
            dele += [f"| {r['dag']} | {r['grund']} |" for r in o["udelukket"]]
            dele.append("")
        if "nnat" in o:
            dele += ["N-nat: mulige starter og andelen af dem, der kan udføres pr. nat "
                     "(p1 / median over nætterne der indgår).\n",
                     "| længde | mulige starter | udførbare p1 | udførbare median |",
                     "|---|---|---|---|"]
            for w, x in o["nnat"].items():
                dele.append(f"| {vindue_laengde(w)} min ({w}) | {_t(x['starter_n'])} | "
                            f"{_t(x['udfoerbare_pct_p1'], 1)}% | "
                            f"{_t(x['udfoerbare_pct_p50'], 1)}% |")
            dele.append("")
        dele += [
            "Pr. variant. Forsinket = indgangs- eller udgangsbaren startede 1-5 minutter "
            "efter det nominelle tidspunkt. σ_nat = 2 × √(middel_n[(29.138 / L_n)² × "
            "Σ Δclose²]). MDE_sidak4 = 3,0756 × σ_nat / √n, MDE_CI = 2,8016 × σ_nat / √n. "
            "Styrke FWE er testen mod N-nat ved en bruttoeffekt over en tilfældig time; "
            "styrke CI er CI-nedre > 0 ved netto = effekt − $2,85 (læsning 13).\n",
            "| variant | nætter | forsinket ind/ud | ruller i vinduet | σ_nat | MDE_sidak4 | "
            "MDE_CI | styrke FWE $8,6 / $17,2 | styrke CI $8,6 / $17,2 |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for r in o["varianter"]:
            dele.append(
                f"| {r['variant']} | {_t(r['naetter_n'])} | {_t(r['forsinket_ind_n'])}/"
                f"{_t(r['forsinket_ud_n'])} | {_t(r['ruller_i_vinduet_n'])} | "
                f"{_usd(r['sigma_nat'], 1)} | **{_usd(r['MDE_sidak4'], 1)}** | "
                f"{_usd(r['MDE_CI'], 1)} | {_pct(r['styrke_FWE_8.6'])} / "
                f"{_pct(r['styrke_FWE_17.2'])} | {_pct(r['styrke_CI_8.6'])} / "
                f"{_pct(r['styrke_CI_17.2'])} |")
        aar = sorted({r["aar"] for r in o["aar"]})
        dele += ["", "Median af L_n og omkostningen $2,85 i bp pr. round trip, pr. år. "
                 f"Ved dagens niveau (NQ {_t(NQ_NIVEAU, 0)}) er den "
                 f"{_t(OMK_USD / (2 * NQ_NIVEAU) * 1e4, 2)} bp.\n",
                 "| variant | " + " | ".join(str(a) for a in aar) + " |",
                 "|" + "---|" * (1 + len(aar))]
        for v in VARIANTER:
            celler = [f"{_t(r['L_median'], 0)} / {_t(r['omk_bp'], 2)} bp ({_t(r['naetter_n'])})"
                      for r in o["aar"] if r["variant"] == _vnavn(v)]
            dele.append(f"| {_vnavn(v)} | " + " | ".join(celler) + " |")
        dele.append("")
    return "\n".join(dele)


def optaelling_csv(oo: dict) -> pd.DataFrame:
    rows = []
    for sym, o in oo.items():
        rows += [{"serie": sym, "tabel": "variant", **r} for r in o["varianter"]]
        rows += [{"serie": sym, "tabel": "aar", **r} for r in o["aar"]]
        rows += [{"serie": sym, "tabel": "udelukket", **r} for r in o["udelukket"]]
        rows.append({"serie": sym, "tabel": "serie", **o["serie"],
                     "salg_andel_pct": o["salg_andel_pct"]})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Rapporten, §10
# ---------------------------------------------------------------------------

def hovedtabel_md(res: dict) -> str:
    _t = k2._t
    linjer = ["| variant | naetter_n | middel_brutto_usd | middel_netto_usd | CI95_netto | "
              "N_nat_p5/p50/p95 | t_v | p_FWE | netto_usd_pr_kalendernat | MDE_sidak4 | "
              "MDE_CI |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for v in VARIANTER:
        r = res["tal"][v]
        linjer.append(
            f"| {_vnavn(v)} | {_t(r['naetter_n'])} | {_usd(r['middel_brutto_usd'])} | "
            f"**{_usd(r['middel_netto_usd'])}** | {_ci_txt(r['ci95_lo'], r['ci95_hi'])} | "
            f"{_usd(r['N_nat_p5'])}/{_usd(r['N_nat_p50'])}/{_usd(r['N_nat_p95'])} | "
            f"{_t(r['t_v'], 2)} | **{_t(r['p_FWE'], 3)}** | "
            f"{_usd(r['netto_usd_pr_kalendernat'])} | {_usd(r['MDE_sidak4'], 1)} | "
            f"{_usd(r['MDE_CI'], 1)} |")
    return "\n".join(linjer)


def _beslutning_md(afg: dict) -> str:
    navne = ", ".join(_vnavn(v) for v in afg["kandidater"]) or "ingen"
    tekst = f"**Række {afg['raekke']}: {afg['tekst']}.** Varianter: {navne}."
    if afg.get("variant") is not None:
        tekst += f" Frosset: **{_vnavn(afg['variant'])}**."
    if afg.get("in_sample_fund"):
        tekst += " In-sample-fund: " + ", ".join(_vnavn(v) for v in afg["in_sample_fund"]) + "."
    return tekst


def _diag_md(res: dict) -> list[str]:
    _t = k2._t
    dv = res["diag"]["variant"]
    d = ["### Før og efter 2020-03-01 (artiklen udkom)\n",
         "| variant | nætter før / efter | netto før | CI | netto efter | CI |",
         "|---|---|---|---|---|---|"]
    for v in VARIANTER:
        r = dv[v]
        d.append(f"| {_vnavn(v)} | {_t(r['naetter_foer_n'])} / {_t(r['naetter_efter_n'])} | "
                 f"{_usd(r['netto_foer'])} | {_ci_txt(r['netto_foer_lo'], r['netto_foer_hi'])} | "
                 f"{_usd(r['netto_efter'])} | "
                 f"{_ci_txt(r['netto_efter_lo'], r['netto_efter_hi'])} |")
    aar = sorted({r["aar"] for r in res["diag"]["aar"]})
    d += ["", "### Pr. år: netto ved dagens niveau / nominelt\n",
          "| variant | " + " | ".join(str(a) for a in aar) + " |", "|" + "---|" * (1 + len(aar))]
    for v in VARIANTER:
        celler = [f"{_usd(r['netto'])} / {_usd(r['nominelt'])}" for r in res["diag"]["aar"]
                  if r["variant"] == v]
        d.append(f"| {_vnavn(v)} | " + " | ".join(celler) + " |")
    d += ["", "### Netto ved $3,10, nominelt og break-even\n",
          "| variant | netto ved $3,10 | CI | nominelt | CI | break-even middel | "
          "break-even CI |", "|---|---|---|---|---|---|---|"]
    for v in VARIANTER:
        r = dv[v]
        d.append(f"| {_vnavn(v)} | {_usd(r['netto_310'])} | "
                 f"{_ci_txt(r['netto_310_lo'], r['netto_310_hi'])} | {_usd(r['nominelt'])} | "
                 f"{_ci_txt(r['nominelt_lo'], r['nominelt_hi'])} | "
                 f"{_usd(r['breakeven_middel'])} | {_usd(r['breakeven_CI'])} |")
    if "beslutning_310" in res["diag"]:
        d += ["", "Rækken i §8 ved $3,10 (afgør intet): "
              + _beslutning_md(res["diag"]["beslutning_310"]), ""]
    d += ["### Brutto efter salgsdagens størrelse (terciler af RTH-afkastet)\n",
          "| variant | gruppe | nætter | median RTH-afkast | brutto | CI |",
          "|---|---|---|---|---|---|"]
    for r in res["diag"]["terciler"]:
        d.append(f"| {_vnavn(r['variant'])} | {r['gruppe']} | {_t(r['naetter_n'])} | "
                 f"{_t(r['rth_afkast_pct_median'], 2)}% | {_usd(r['brutto'])} | "
                 f"{_ci_txt(r['brutto_lo'], r['brutto_hi'])} |")
    d += ["", "### Long hele natten, 17:00 → 08:30 CT\n",
          "| nætter | n | brutto | netto | CI |", "|---|---|---|---|---|"]
    for b_, r in res["diag"]["hele_natten"].items():
        d.append(f"| {b_} | {_t(r['naetter_n'])} | {_usd(r['brutto'])} | {_usd(r['netto'])} | "
                 f"{_ci_txt(r['netto_lo'], r['netto_hi'])} |")
    d += ["", "### Profil, natfordeling og største tab i vinduet (netto, $)\n",
          "| variant | hit netto | gevinst/tab netto | hit brutto | p1/p5/p50/p95/p99 | "
          "værst / bedst | tab i vindue p1/p5/p50 | værste tab i vindue |",
          "|---|---|---|---|---|---|---|---|"]
    for v in VARIANTER:
        r = dv[v]
        d.append(f"| {_vnavn(v)} | {_t(r['hit_netto_pct'], 1)}% | "
                 f"{_t(r['gevinst_tab_netto'], 2)} | {_t(r['hit_brutto_pct'], 1)}% | "
                 + "/".join(_usd(r[f'netto_p{q}'], 0) for q in (1, 5, 50, 95, 99))
                 + f" | {_usd(r['netto_vaerst'], 0)} / {_usd(r['netto_bedst'], 0)} | "
                 + "/".join(_usd(r[f'tab_i_vindue_p{q}'], 0) for q in (1, 5, 50))
                 + f" | {_usd(r['tab_i_vindue_vaerst'], 0)} |")
    d.append("")
    return d


def skriv_md(res: dict, meta: dict) -> str:
    nq, mnq = res[HOVED], res[KONTROL]
    dele = [
        "# B4 kandidat 6 — overnight drift ved Europas åbning\n",
        f"Kørt {meta['koert_utc']} UTC fra commit `{meta['head'][:7]}`. Præregistrering: "
        f"`{_rel(PREREG)}`. R = {nq['R']}. Afgørelsen tages på {HOVED} ved $2,85 og dagens "
        f"niveau (§8).\n",
        f"## Hovedtabel — {HOVED}\n", hovedtabel_md(nq), "",
        "## §8 anvendt mekanisk\n", _beslutning_md(nq["beslutning"]), "",
        f"## Diagnoser — {HOVED} (afgør intet)\n", *_diag_md(nq),
        f"## Kontrol — {KONTROL} 2019-2023 (afgør intet)\n", hovedtabel_md(mnq), "",
        "Rækken i §8 på kontrolserien: " + _beslutning_md(mnq["beslutning"]), "",
        *_diag_md(mnq),
        "## Datakvalitet\n",
        optaelling_md({HOVED: nq["optaelling"], KONTROL: mnq["optaelling"]},
                      meta).split("\n", 3)[-1],
    ]
    if meta.get("commits"):
        dele += ["## Commits\n", "| fil | commit |", "|---|---|"]
        dele += [f"| `{f}` | `{c[:7]}` |" for f, c in meta["commits"].items()]
    return "\n".join(dele)


def lang_tabel(res: dict) -> pd.DataFrame:
    rows = []
    for sym, r in res.items():
        for v in VARIANTER:
            t = {k: x for k, x in r["tal"][v].items() if not k.startswith("_") and k != "variant"}
            rows.append({"serie": sym, "tabel": "hoved", "variant": _vnavn(v), **t,
                         "raekke": r["beslutning"]["raekke"]})
            rows.append({"serie": sym, "tabel": "diagnose", "variant": _vnavn(v),
                         **r["diag"]["variant"][v]})
        rows += [{"serie": sym, "tabel": "aar", **{**x, "variant": _vnavn(x["variant"])}}
                 for x in r["diag"]["aar"]]
        rows += [{"serie": sym, "tabel": "tercil", **{**x, "variant": _vnavn(x["variant"])}}
                 for x in r["diag"]["terciler"]]
        rows += [{"serie": sym, "tabel": "hele_natten", "variant": b_, **x}
                 for b_, x in r["diag"]["hele_natten"].items()]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# §11.3: regressionstjek
# ---------------------------------------------------------------------------

def regression_k5(df: pd.DataFrame) -> dict:
    """Læsning 23: kandidat 5 in-sample, 1m · uden middag, 14.831 handler og $41,07."""
    g = k5.byg_grundlag(df, k1.rth_dage(trinA.MNQ_START, trinA.TRIN_A_SLUT))
    v = (1, k5.UDEN)
    h = k5.handler(g, v)
    t = k5.variant_tal(g, h)
    m = t["middel_netto_usd_dag"]
    return {"handler_n": h.n, "middel_netto_usd_dag": m,
            "ok": h.n == REGRESSION_K5_HANDLER_N and round(m, 2) == REGRESSION_K5_NETTO_USD}


def regressionstjek() -> dict:
    """§11.3: kandidat 1's tre tjek, ``simuler_handel``, kandidat 2, 3, 4 og 5."""
    df = k5.mnq()
    t0 = time.perf_counter()
    ud = k5.regressionstjek(df)
    ud["k5_1m_uden"] = regression_k5(df)
    ud["sekunder"] = time.perf_counter() - t0
    ud["ok"] = bool(ud["ok"] and ud["k5_1m_uden"]["ok"])
    return ud


# ---------------------------------------------------------------------------
# §11.5: tidsmålingen — uden P&L
# ---------------------------------------------------------------------------

def tidsmaaling(n_reps: int = 5, symbol: str = HOVED) -> dict:
    """§11.5: ét gennemløb og ``n_reps`` N-nat-gentagelser, fremskrevet til R = 500.
    Returnerer kun tider og antal; P&L regnes inde i gennemløbet, men forlader det ikke."""
    t0 = time.perf_counter()
    df = serie(symbol)
    load_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    g = byg_grundlag(df, xnys_dage(symbol), symbol)
    grundlag_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    hd = forbered(g)
    tal = {v: variant_tal(g, v, hd[v[0]]) for v in VARIANTER}
    diagnoser(g, hd, tal)
    for v in VARIANTER:
        sigma_nat(g, v)
    gennemloeb_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    nvs = forbered_nnat(g)
    nnat_forbered_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    for rep in range(n_reps):
        nnat_gentagelse(g, nvs, rep)
    nnat_s = time.perf_counter() - t0
    pr_rep = nnat_s / n_reps if n_reps else 0.0
    t0 = time.perf_counter()
    k2.westfall_young({v: 0.0 for v in VARIANTER},       # tallene er ligegyldige her
                      {v: np.arange(NNAT_REPS, dtype=float) for v in VARIANTER})
    wy_s = time.perf_counter() - t0
    forventet = (load_s + grundlag_s + gennemloeb_s + nnat_forbered_s + pr_rep * NNAT_REPS
                 + wy_s)
    return {"symbol": symbol, "load_s": load_s, "grundlag_s": grundlag_s,
            "gennemloeb_s": gennemloeb_s, "nnat_forbered_s": nnat_forbered_s,
            "n_reps": n_reps, "nnat_s": nnat_s, "pr_rep_s": pr_rep, "wy_s": wy_s,
            "forventet_s": forventet, "naetter_n": {_vnavn(v): tal[v]["naetter_n"]
                                                    for v in VARIANTER}}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--regressionstjek", action="store_true",
                     help="§11.3: kandidat 1's tre tjek, simuler_handel, kandidat 2-5")
    grp.add_argument("--optaelling", action="store_true",
                     help="§11.4: optælling uden udfald. Skriver b4_k6_overnight_optaelling")
    grp.add_argument("--tidsmaaling", action="store_true",
                     help="§11.5: ét gennemløb og 5 N-nat-gentagelser, uden P&L")
    grp.add_argument("--koer", action="store_true",
                     help="§6-§10: den rigtige kørsel. Kræver ejerens godkendelse")
    ap.add_argument("--reps", type=int, default=NNAT_REPS)
    ap.add_argument("--maalte-reps", type=int, default=5)
    args = ap.parse_args(argv)
    meta = {"koert_utc": pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M"),
            "head": k4._git("rev-parse", "HEAD").stdout.strip()}

    if args.regressionstjek:
        r = regressionstjek()
        k1r, mo, k2r, k3r, k4r, k5r = (r["k1"], r["motor"], r["k2_hovedvariant"], r["k3_k1"],
                                       r["k4_k15_1"], r["k5_1m_uden"])
        ok = lambda x: "OK" if x else "AFVIGER"
        print(f"Kandidat 1, 1. b4_k1_optaelling_v2.csv byte for byte: "
              f"{ok(k1r['csv_byte_for_byte'])}")
        print(f"Kandidat 1, 2. spor A, score >= 0: handler_n {k1r['motor_handler_n']}, "
              f"middel_R_netto {k1r['motor_middel_R_netto']:.4f}: {ok(k1r['motor_ok'])}")
        print(f"Kandidat 1, 3. scorefordelingen ({k1r['score_rader_n']} raekker): "
              f"{ok(k1r['score_ok'])}")
        for navn in ("standard", "eksplicit_2R"):
            x = mo[navn]
            print(f"simuler_handel, {navn}: handler_n {x['handler_n']} (ventet "
                  f"{k2.REGRESSION_HANDLER_N}), middel_R_netto {x['middel_R_netto']:.4f} "
                  f"(ventet {k2.REGRESSION_MIDDEL_R_NETTO}): {ok(x['ok'])}")
        print(f"Kandidat 2, daily · 5 lys · 1R: handler_n {k2r['handler_n']}, middel_R_netto "
              f"{k2r['middel_R_netto']:.4f}: {ok(k2r['ok'])}")
        print(f"Kandidat 3, k = 1,0: handler_n {k3r['handler_n']} (ventet "
              f"{k4.REGRESSION_K3_HANDLER_N}), middel_R_netto {k3r['middel_R_netto']:.4f} "
              f"(ventet {k4.REGRESSION_K3_MIDDEL_R_NETTO}): {ok(k3r['ok'])}")
        print(f"Kandidat 4, k = 1,5 · 1/dag: handler_n {k4r['handler_n']} (ventet "
              f"{k5.REGRESSION_K4_HANDLER_N}), middel_R_netto {k4r['middel_R_netto']:.4f} "
              f"(ventet {k5.REGRESSION_K4_MIDDEL_R_NETTO:.4f}): {ok(k4r['ok'])}")
        print(f"Kandidat 5, 1m · uden middag: handler_n {k5r['handler_n']} (ventet "
              f"{REGRESSION_K5_HANDLER_N}), middel_netto_usd_dag "
              f"{k5r['middel_netto_usd_dag']:.2f} (ventet {REGRESSION_K5_NETTO_USD:.2f}): "
              f"{ok(k5r['ok'])}")
        print(f"Tid: {r['sekunder']:.0f} s")
        if not r["ok"]:
            sys.exit(1)
        return

    if args.optaelling:
        oo = {}
        for sym in (HOVED, KONTROL):
            g = byg_grundlag(serie(sym), xnys_dage(sym), sym)
            oo[sym] = optaelling(g, forbered_nnat(g))
        md = optaelling_md(oo, meta)
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "b4_k6_overnight_optaelling.md").write_text(md, encoding="utf-8")
        optaelling_csv(oo).to_csv(OUT / "b4_k6_overnight_optaelling.csv", index=False)
        print(md)
        return

    if args.tidsmaaling:
        t = tidsmaaling(args.maalte_reps)
        print(f"{t['symbol']}: indlæsning {t['load_s']:.1f} s, grundlag {t['grundlag_s']:.1f} s, "
              f"P&L, nøgletal, diagnoser og σ_nat for 4 varianter {t['gennemloeb_s']:.2f} s")
        print(f"N-nat: gitter og værdier {t['nnat_forbered_s']:.2f} s, {t['n_reps']} "
              f"gentagelser {t['nnat_s']:.3f} s, {t['pr_rep_s'] * 1000:.1f} ms pr. gentagelse. "
              f"Westfall-Young {t['wy_s']:.3f} s")
        print(f"Fremskrevet til R = {NNAT_REPS}: {t['forventet_s']:.0f} s "
              f"({t['forventet_s'] / 60:.1f} min) for {t['symbol']}, regressionstjekket ikke "
              f"medregnet")
        print(f"naetter_n: {t['naetter_n']}")
        return

    commits = k1.committede(COMMITTEDE)
    res = koer(n_reps=args.reps)
    meta["commits"] = commits
    md = skriv_md(res, meta)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "b4_k6_overnight.md").write_text(md, encoding="utf-8")
    lang_tabel(res).to_csv(OUT / "b4_k6_overnight.csv", index=False)
    print(md)


if __name__ == "__main__":
    main()
