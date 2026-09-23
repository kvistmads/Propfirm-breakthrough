"""B4 kandidat 1 — trin A: handelsmodul, fra fyldning til udgang.

Præregistreret i ``research/prereg/b4_k1_trinA.md``. Bygger videre på zonefundet i
``research/b4_k1_optaelling.py`` (kerne v2, ``zoner_v2``/``klassificer_v2``), som står
uændret — dette modul lægger handelsmekanikken (§4) oven på den samme zoneliste.

**Trin 1 (byg og verificér) kører ikke selve edge-testen.** Se ``main()``:
``--regressionstjek`` og ``--tidsmaaling`` er de to ting trin 1 beder om. Trin 2 (6
varianter × N1 med 500 gentagelser, Westfall-Young) kræver Mads' godkendelse og er ikke
implementeret her.

## Hvorfor sizing regnes om, §4d — præciseret 2026-09-23

``research/b4_k1_optaelling.py``'s ``sizing()`` regner risiko i point ved en FAST
reference (NQ 29.138, jf. ``b4_hypoteser.md``, "Prisniveau"). Det er rigtigt til
optællingens beskrivende procentiler (sammenlignelige tal på tværs af år hvor NQ er
tredoblet), men det er IKKE den rigtige risiko for en faktisk handel: prisen var reel
historisk, ikke ved 29.138. §4d er eksplicit: **"Risiko = E − low = 1,1 × H"** — et
rigtigt pointtal fra zonens egne E/low/high, ikke en omregning. Handelsmodulet bruger
derfor sine egne ``*_ekte``-kolonner (``sizing_ekte``), regnet direkte på zonens rigtige
priser.

**k1's ``under_stoploft`` (0,429% af den rigtige pris) bruges IKKE i handelsmodulet.**
Den er et relativt breddefilter, ikke dollarloftet — de to er kun samme tal ved NQ
29.138, hvor optællingsmodulet netop regner. På de rigtige historiske priser ville
procentreglen afvise ca. 8,4% af berøringerne uanset hvad de koster i dollar, en variant
ingen har valgt. PRD §3c's egentlige krav — "Handler hvor ét MNQ alene ville risikere
mere end $250, tages ikke" — håndhæves alene af ``kontrakter_ekte``: **en handel tages
hvis og kun hvis ``kontrakter_ekte ≥ 1``.** Kandidatudvalget bruger derfor k1's
``i_vindue`` (kun tidsvinduet), ikke ``signal`` (som stadig bærer procentreglen).

## Fyldning, §4a-4c

En zone dør ved sin 15m-berøring (kerne v2, uændret). Om ordren rent faktisk FYLDES
afgøres på 1m-serien inden for netop den berøringsbar: prisen skal handle mindst ét
tick igennem E (§4a regel 1), fyldt til E, aldrig bedre (regel 2). Rammes E kun (uden at
gå igennem), er det et "strejf": zonen er stadig død (regel 7), men ingen handel åbnes.
En kontrafaktisk gennemkøring (§4c) regner hvad strejfet ville have givet, fyldt til E i
det øjeblik 15m-berøringen skete, med samme maskineri — kun til diagnose.

## Handelens gang, §4b

Alle aktive zoner har en hvilende limitordre; den første gennemhandling der er tilladt
(ingen position åben, dagen ikke lukket) bliver handlen. Kandidaterne (signal og
``kontrakter_ekte`` > 0) behandles kronologisk pr. dag. Stop og mål findes med rule 4's
worst case (begge ramt i samme 1m-bar: stoppet antages først). BE (findes ikke i
varianten "ingen") flytter stoppet til E når prisen når triggeren; to BE-udgange lukker
dagen (PRD §3a). Tidsexit er fast klokkeslæt 14:50 CT hver dag (PRD §3, "21:50 dansk /
14:50 CT") — ikke bundet til RTH-kalenderens halve dage, som kun styrer indgangsvinduet.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data import holdout, resample  # noqa: E402
from research import b4_k1_optaelling as k1  # noqa: E402
from research.stats import breakeven_win_rate, mean_ci_t, wilson_interval  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "output"
PREREG = ROOT / "research" / "prereg" / "b4_k1_trinA.md"
PREREG_MOTOR = ROOT / "research" / "prereg" / "b4_k1_motorrettelse.md"

MNQ = "MNQ.v.0"
MNQ_START = pd.Timestamp("2019-05-06", tz="UTC")
TRIN_A_SLUT = pd.Timestamp("2024-01-01", tz="UTC")   # = 2023-12-31 inklusive, holdout-grænsen

TICK = 0.25                          # MNQ, point
SLIP_TICKS = 0.5417                  # §4a regel 5, fase 1's målte tal
SLIP_PT = SLIP_TICKS * TICK
CT = k1.CT
FLAD_CT_TIME = (14, 50)              # PRD §3: 21:50 dansk = 14:50 CT, fast hver dag
MNQ_USD_PR_POINT = k1.MNQ_USD_PR_POINT
RISIKO_USD = k1.RISIKO_USD
OMK_USD_RUNDTUR = k1.OMK_USD_RUNDTUR
RR = k1.RR
DEMAND, SUPPLY = k1.DEMAND, k1.SUPPLY

BUFFER_VARIANTER = {"buffer_10": Fraction(1, 10), "buffer_0": Fraction(0)}
BE_VARIANTER = {"ingen": None, "BE_1_0R": 1.0, "BE_1_2R": 1.2}   # §3, PRD §3b

KONTRAKTER_LOFT = 50                 # $50K positionsloft, REGLER_VERIFICERET.md §90

MAAL, STOP, BE_UDFALD, TIDSEXIT, CENSURERET = "maal", "stop", "BE", "tidsexit", "censureret"
UDFALD = (MAAL, STOP, BE_UDFALD, TIDSEXIT, CENSURERET)


# ---------------------------------------------------------------------------
# §4d: den ægte punktrisiko — erstatter k1's NQ 29.138-normerede sizing
# ---------------------------------------------------------------------------

def sizing_ekte(zoner: pd.DataFrame) -> pd.DataFrame:
    """Tilføjer ``risiko_pt_ekte``, ``kontrakter_ekte`` og ``omk_R_netto_ekte``.

    Risiko = E − zone_low (demand) / zone_high − E (supply) — reelle priser, §4d.
    Samme afrunding før floor som k1's ``sizing()`` (fjerner flydende tals støj).

    **Kontrakter loftes ved 50** (Topsteps positionsloft på $50K, `REGLER_VERIFICERET.md`
    §90, tilføjet §4d 2026-09-23). Det ændrer intet R-tal — R regnes fra ``risiko_pt_ekte``
    og ``omk_R_netto_ekte`` alene, kontraktantallet indgår ikke. Loftet fjerner heller
    ingen handel, for gate'en er ``kontrakter_ekte >= 1``, og et loft på 50 kan kun sænke
    et tal der allerede var ≥ 1. ``kontrakter_ekte_raa`` er den uloftede floor-værdi, kun
    til at tælle ``kontrakter_loftet_n`` — den bruges ikke andre steder.
    """
    z = zoner.copy()
    demand = (z["side"] == DEMAND).to_numpy()
    E = z["E"].to_numpy(dtype=float)
    low, high = z["zone_low"].to_numpy(dtype=float), z["zone_high"].to_numpy(dtype=float)
    risiko_pt = np.where(demand, E - low, high - E)
    risiko_usd = risiko_pt * MNQ_USD_PR_POINT
    z["risiko_pt_ekte"] = risiko_pt
    kontrakter_raa = np.floor(np.round(RISIKO_USD / risiko_usd, 9))
    z["kontrakter_ekte_raa"] = kontrakter_raa
    z["kontrakter_ekte"] = np.minimum(kontrakter_raa, KONTRAKTER_LOFT)
    z["omk_R_netto_ekte"] = OMK_USD_RUNDTUR / risiko_usd
    return z


def _sizing_raekke(etiket: str, sub: pd.DataFrame) -> dict:
    row = {"periode": etiket, "zoner_i_vindue_n": len(sub)}
    for q in (10, 50, 90):
        row[f"risiko_pt_p{q}"] = k1._p(sub["risiko_pt_ekte"], q)
    for q in (50, 90):
        row[f"kontrakter_p{q}"] = k1._p(sub["kontrakter_ekte"], q)
    row["kontrakter_maks"] = float(sub["kontrakter_ekte"].max()) if len(sub) else float("nan")
    row["omk_R_netto_p50"] = k1._p(sub["omk_R_netto_ekte"], 50)
    row["omk_R_netto_p90"] = k1._p(sub["omk_R_netto_ekte"], 90)
    row["be_WR_pct_netto_p50"] = (100 * breakeven_win_rate(RR, 1.0, row["omk_R_netto_p50"])
                                  if len(sub) else float("nan"))
    afvist = int((sub["kontrakter_ekte"] == 0).sum())
    row["afvist_kontrakter_nul_n"] = afvist
    row["afvist_kontrakter_nul_pct"] = 100 * afvist / len(sub) if len(sub) else float("nan")
    # §4d: positionsloftet på 50 mikroer, og den tynde hale det afslører (be_WR > 50%).
    row["kontrakter_loftet_n"] = (int((sub["kontrakter_ekte_raa"] > KONTRAKTER_LOFT).sum())
                                  if len(sub) else 0)
    row["handler_be_WR_over_50_pct_n"] = (int((sub["omk_R_netto_ekte"] > 0.5).sum())
                                          if len(sub) else 0)
    return row


def sizing_tabel(zoner: pd.DataFrame) -> pd.DataFrame:
    """§4d: risiko, kontrakter og omkostning pr. år — konsekvensen af den ægte, reelle
    punktrisiko, målt i stedet for antaget. Population er ``i_vindue`` (berøringer i
    indgangsvinduet), FØR dollarloftets ``kontrakter_ekte >= 1``-filter, så
    ``afvist_kontrakter_nul_n`` viser hvor mange loftet faktisk afviser.
    """
    pop = zoner[zoner["i_vindue"].astype(bool)]
    aar_liste = sorted(pop["dag"].dt.year.unique()) if len(pop) else []
    rows = [_sizing_raekke("alle", pop)]
    rows += [_sizing_raekke(str(a), pop[pop["dag"].dt.year == a]) for a in aar_liste]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Tidsexit
# ---------------------------------------------------------------------------

def flad_tid_utc(et_tidspunkt: pd.Timestamp) -> pd.Timestamp:
    """14:50 CT samme dag som ``et_tidspunkt`` (typisk fyldningstiden), i UTC.

    Fast klokkeslæt, uafhængigt af RTH-kalenderens halve dage — de styrer kun
    indgangsvinduet (``k1.vindue_mask``), ikke fladt-reglen.
    """
    ct = et_tidspunkt.tz_convert(CT)
    graense = ct.replace(hour=FLAD_CT_TIME[0], minute=FLAD_CT_TIME[1], second=0,
                         microsecond=0, nanosecond=0)
    return graense.tz_convert("UTC")


# ---------------------------------------------------------------------------
# Én handel, §4a-4b
# ---------------------------------------------------------------------------

def simuler_handel(h: np.ndarray, l: np.ndarray, c: np.ndarray, entry_i: int,
                   entry_pris: float, demand: bool, risiko_pt: float,
                   be_r: float | None, cutoff_i: int, n: int,
                   ret_fyldningsbar: bool = True) -> tuple[str, float, int, bool]:
    """Fra fyldningsbaren og frem, 1m-bar for 1m-bar. Returnerer (udfald, R_brutto,
    exit_i, holder).

    ``cutoff_i`` er positionen for 14:50 CT-fladten (ekskl.), ``n`` seriens længde —
    løber vi ud over serien, er handlen censureret ved in-sample-slut, ikke tidsexit.

    **Motorrettelse 1** (``research/prereg/b4_k1_motorrettelse.md``): i fyldningsbaren
    (``entry_i``) kan kun stoppet rammes — mål, BE-trigger og +1R (til ``holder``)
    tjekkes først fra næste 1m-bar, ``ret_fyldningsbar=True`` (standard, den rettede
    motor). ``ret_fyldningsbar=False`` er kun til før/efter-målingen: den gamle,
    ukorrigerede opførsel, hvor hele fyldningsbarens high/low blev tjekket mod alt.

    ``holder``: +1R nået før stoppet, fyldningsbaren undtaget (motorrettelse 3). Mål
    indebærer altid holder (2R kan ikke nås uden at passere 1R i samme eller en tidligere
    bar). Rammes +1R og stoppet i samme 1m-bar, gælder samme worst case som regel 4:
    stoppet antages ramt først, og den bar tæller ikke selv med i holder.
    """
    maal = entry_pris + RR * risiko_pt if demand else entry_pris - RR * risiko_pt
    stop_niveau = entry_pris - risiko_pt if demand else entry_pris + risiko_pt
    en_r_niveau = entry_pris + risiko_pt if demand else entry_pris - risiko_pt
    be_trigger = None
    if be_r is not None:
        be_trigger = entry_pris + be_r * risiko_pt if demand else entry_pris - be_r * risiko_pt
    be_armet = False
    holder = False
    graense = min(cutoff_i, n)
    i = entry_i
    while i < graense:
        hi, lo = h[i], l[i]
        stop_ramt = (lo <= stop_niveau) if demand else (hi >= stop_niveau)
        # Regel 4: rammes stop og mål i samme 1m-bar, antages stoppet ramt først.
        if stop_ramt:
            udfald = BE_UDFALD if be_armet else STOP
            eksekvering = stop_niveau - SLIP_PT if demand else stop_niveau + SLIP_PT
            r = ((eksekvering - entry_pris) if demand else (entry_pris - eksekvering)) / risiko_pt
            return udfald, r, i, holder
        # Motorrettelse 1: fyldningsbaren tjekkes kun for stoppet ovenfor.
        if ret_fyldningsbar and i == entry_i:
            i += 1
            continue
        maal_ramt = (hi >= maal) if demand else (lo <= maal)
        if maal_ramt:
            return MAAL, RR, i, True
        if (hi >= en_r_niveau) if demand else (lo <= en_r_niveau):
            holder = True
        if be_trigger is not None and not be_armet:
            trig = (hi >= be_trigger) if demand else (lo <= be_trigger)
            if trig:
                be_armet = True
                stop_niveau = entry_pris
        i += 1
    sidste_i = i - 1 if i > entry_i else entry_i
    eksekvering = c[sidste_i]
    r = ((eksekvering - entry_pris) if demand else (entry_pris - eksekvering)) / risiko_pt
    udfald = CENSURERET if graense == n else TIDSEXIT
    return udfald, r, sidste_i, holder


# ---------------------------------------------------------------------------
# Dagens gennemløb, §4b — fyldningen og disciplinreglerne
# ---------------------------------------------------------------------------

def handler_for_variant(df_1m: pd.DataFrame, zoner: pd.DataFrame, be_r: float | None,
                        ret_fyldningsbar: bool = True
                        ) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    """Alle handler for én BE-variant. ``zoner`` er kerne v2 (klassificeret, med
    ``sizing_ekte``-kolonnerne) for én buffer-variant.

    Kandidaterne er zoner med ``i_vindue`` (berøring i tidsvinduet — IKKE k1's
    ``signal``, som stadig bærer den procentbaserede ``under_stoploft``) og mindst 1
    ægte kontrakt, §4d. En berøring mens en position er åben, eller efter dagen er
    lukket, springes over og tælles. Fyldes ordren ikke (strejf), regnes en
    kontrafaktisk handel til diagnose, §4c — den ændrer intet i tælling eller stat.

    Kandidaterne læses som rå numpy-arrays, ikke ``DataFrame.itertuples()`` — profilering
    viste at ``itertuples()`` på ``zoner``'s brede tabel (mange kolonner, deriblandt en
    Arrow-baseret strengkolonne) dominerede tiden: >70% af én kørsel gik i pandas' egen
    rækkeopbygning, ikke i handelslogikken. Samme rækkefølge, samme betingelser, samme tal.

    ``ret_fyldningsbar`` sendes videre til ``simuler_handel`` — standard er den rettede
    motor (motorrettelse 1). ``False`` er kun til før/efter-målingen i
    ``research/prereg/b4_k1_motorrettelse.md``.
    """
    times = df_1m.index
    h = df_1m["high"].to_numpy(dtype=float)
    l = df_1m["low"].to_numpy(dtype=float)
    c = df_1m["close"].to_numpy(dtype=float)
    n = len(df_1m)

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
    m = len(kand)

    rows: list[dict] = []
    strejf_rows: list[dict] = []
    tael = {"signaler_sprunget_over_position_n": 0, "signaler_sprunget_over_dagslukket_n": 0}

    graenser = np.r_[np.flatnonzero(np.r_[True, dag_arr[1:] != dag_arr[:-1]]), m]
    for gi in range(len(graenser) - 1):
        dagslukket = False
        be_count = 0
        fri_fra = None
        for k in range(graenser[gi], graenser[gi + 1]):
            t = slut_tid_arr[k]
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
            i0 = int(times.searchsorted(t))
            i1 = int(times.searchsorted(t + k1.BAR))
            sub_l, sub_h = l[i0:i1], h[i0:i1]
            graense = (E - TICK) if demand else (E + TICK)
            gennem = (sub_l <= graense) if demand else (sub_h >= graense)
            if not gennem.any():
                strejf_maske = (sub_l <= E) if demand else (sub_h >= E)
                if strejf_maske.any():
                    j = i0 + int(np.argmax(strejf_maske))
                    cutoff_i = int(times.searchsorted(flad_tid_utc(times[j])))
                    udfald, r_brutto, _, holder = simuler_handel(
                        h, l, c, j, E, demand, risiko_pt, be_r, cutoff_i, n,
                        ret_fyldningsbar)
                    strejf_rows.append({
                        "dag": dag_arr[k], "side": side_arr[k], "basis_i": basis_i_arr[k],
                        "udfald": udfald, "R_brutto": r_brutto,
                        "R_netto": r_brutto - omk_R_netto, "holder": holder,
                    })
                continue
            fyld_i = i0 + int(np.argmax(gennem))
            fyld_tid = times[fyld_i]
            cutoff_i = int(times.searchsorted(flad_tid_utc(fyld_tid)))
            udfald, r_brutto, exit_i, holder = simuler_handel(
                h, l, c, fyld_i, E, demand, risiko_pt, be_r, cutoff_i, n, ret_fyldningsbar)
            r_netto = r_brutto - omk_R_netto
            rows.append({
                "dag": dag_arr[k], "side": side_arr[k], "basis_i": basis_i_arr[k],
                "fyld_tid": fyld_tid, "exit_tid": times[exit_i],
                "udfald": udfald, "R_brutto": r_brutto, "R_netto": r_netto,
                "risiko_pt": risiko_pt, "kontrakter": kontrakter_arr[k],
                "omk_R_netto": omk_R_netto, "holder": holder,
            })
            if udfald == BE_UDFALD:
                be_count += 1
                if be_count >= 2:
                    dagslukket = True
            else:
                dagslukket = True
            fri_fra = times[exit_i]

    handler = pd.DataFrame(rows, columns=["dag", "side", "basis_i", "fyld_tid", "exit_tid",
                                          "udfald", "R_brutto", "R_netto", "risiko_pt",
                                          "kontrakter", "omk_R_netto", "holder"])
    strejf = pd.DataFrame(strejf_rows, columns=["dag", "side", "basis_i", "udfald",
                                                "R_brutto", "R_netto", "holder"])
    return handler, tael, strejf


def simuler_alle_varianter(df_1m: pd.DataFrame, bars_15m: pd.DataFrame,
                           ret_fyldningsbar: bool = True) -> dict:
    """Alle 6 varianter, §3: buffer × BE. Nøgle er (buffer_navn, be_navn).

    ``ret_fyldningsbar=False`` er kun til motorrettelsens før/efter-måling.
    """
    ud = {}
    for buffer_navn, buffer in BUFFER_VARIANTER.items():
        zoner = sizing_ekte(k1.zoner_v2(bars_15m, buffer))
        for be_navn, be_r in BE_VARIANTER.items():
            handler, tael, strejf = handler_for_variant(df_1m, zoner, be_r, ret_fyldningsbar)
            ud[(buffer_navn, be_navn)] = {"handler": handler, "tael": tael,
                                          "strejf": strejf, "zoner": zoner}
    return ud


# ---------------------------------------------------------------------------
# N1, §5 — FORELØBIG: kun til punkt 4's tidsmåling, ikke selve nulmodellen. Skal
# gennemgås og testes på egne præmisser, som §5 kræver, før trin 2's rigtige kørsel.
# ---------------------------------------------------------------------------

def _uge_id(index: pd.DatetimeIndex) -> np.ndarray:
    """ISO-kalenderuge (år×100+ugenummer) pr. lys — "samme kalenderuge" i §5.

    Implementeringsdetalje §5 ikke fastlægger; ISO-ugen (mandag-søndag) er læsningen
    her og bør bekræftes før trin 2's rigtige kørsel.
    """
    iso = index.isocalendar()
    return iso["year"].to_numpy() * 100 + iso["week"].to_numpy()


def n1_dannelseslys(bars: pd.DataFrame, ekte_basis_i: np.ndarray,
                    rng: np.random.Generator) -> np.ndarray:
    """§5: ét tilfældigt 15m-lys i samme kalenderuge som hvert rigtige basislys.

    -1 hvor ugen ikke har plads til et lys efter det trukne (intet "udbrudslys" at
    aktivere fra). Samme trækning genbruges for begge buffer-varianter i
    ``find_zoner_n1`` — det er dannelseslyset der flyttes, ikke bufferen.
    """
    n = len(bars)
    uge = _uge_id(bars.index)
    graenser = np.flatnonzero(np.r_[True, uge[1:] != uge[:-1]])
    graenser = np.r_[graenser, n]
    uge_af_lys = np.searchsorted(graenser, np.arange(n), side="right") - 1

    ud = np.full(len(ekte_basis_i), -1, dtype=np.int64)
    for i, b0 in enumerate(ekte_basis_i):
        gi = int(uge_af_lys[b0])
        start, slut = int(graenser[gi]), int(graenser[gi + 1])
        if slut - start >= 2:
            ud[i] = rng.integers(start, slut - 1)
    return ud


def find_zoner_n1(bars: pd.DataFrame, side: np.ndarray, H: np.ndarray, b_n1: np.ndarray,
                  buffer: Fraction) -> pd.DataFrame:
    """N1's zoner for én buffer-variant, ud fra dannelseslys trukket af ``n1_dannelseslys``.

    Zonens resterende mekanik — aktivering, ugyldig, berøring, kontraktskift — er kerne
    v2's egne regler (``b4_k1_optaelling.find_zoner_v2``, uændret, ikke rørt), her blot
    rodfæstet i det trukne lys i stedet for det rigtige basislys. Side og H (den rigtige
    zones) bevares, som §5 kræver; ``b`` med -1 (ingen plads i ugen) springes over.
    """
    o, h, l, c = (bars[k].to_numpy(dtype=float) for k in ("open", "high", "low", "close"))
    n = len(bars)
    iid = (bars["instrument_id"].to_numpy() if "instrument_id" in bars.columns
           else np.zeros(n, dtype=np.int64))
    skift = np.flatnonzero(iid[1:] != iid[:-1]) + 1
    naeste_skift = np.r_[skift, n][np.searchsorted(skift, np.arange(n), side="right")]
    p, q = buffer.numerator, buffer.denominator

    rows = []
    for side_i, H_i, b in zip(side, H, b_n1):
        if b < 0:
            continue
        b = int(b)
        demand = side_i == DEMAND
        u, k = b + 1, int(naeste_skift[b])
        zone_high = h[b] if demand else l[b] + H_i
        zone_low = h[b] - H_i if demand else l[b]
        qe = q * zone_high + p * H_i if demand else q * zone_low - p * H_i
        aktiv = -1
        if k <= u:
            status, slut = k1.KONTRAKTSKIFT, k
        else:
            forladt = q * l[u:k] > qe if demand else q * h[u:k] < qe
            gennem = c[u:k] < zone_low if demand else c[u:k] > zone_high
            gennem[0] = False
            ia = int(np.argmax(forladt)) if forladt.any() else None
            ig = int(np.argmax(gennem)) if gennem.any() else None
            if ig is not None and (ia is None or ig < ia):
                status, slut = k1.UGYLDIG, u + ig
            elif ia is not None:
                aktiv = u + ia
                ramt = (q * l[aktiv + 1:k] <= qe) if demand else (q * h[aktiv + 1:k] >= qe)
                if ramt.any():
                    status, slut = k1.BEROERT, aktiv + 1 + int(np.argmax(ramt))
                elif k < n:
                    status, slut = k1.KONTRAKTSKIFT, k
                else:
                    status, slut = k1.AKTIV, -1
            elif k < n:
                status, slut = k1.KONTRAKTSKIFT, k
            else:
                status, slut = k1.ALDRIG_AKTIV, -1
        rows.append((side_i, b, u, bars.index[b], bars.index[u], zone_high, zone_low,
                    c[b], H_i / c[b] * 100,
                    bool(bars.index[u] - bars.index[b] > k1.BAR), status, slut,
                    bars.index[slut] if slut >= 0 else pd.NaT,
                    float(buffer), qe / q, aktiv,
                    bars.index[aktiv] if aktiv >= 0 else pd.NaT))
    z = pd.DataFrame(rows, columns=k1.ZONEKOLONNER_V2)
    for kol in ("basis_tid", "udbrud_tid", "slut_tid", "aktiv_tid"):
        z[kol] = pd.to_datetime(z[kol], utc=True)
    return z


def n1_gentagelse(df_1m: pd.DataFrame, bars_15m: pd.DataFrame, ekte_side: np.ndarray,
                  ekte_basis_i: np.ndarray, ekte_H: np.ndarray, seed: int) -> dict:
    """Én N1-gentagelse, alle 6 varianter — samme kørsel som ``simuler_alle_varianter``,
    men på N1's tilfældigt rodfæstede zoner. Topniveau-funktion, så den kan sendes til en
    proces-pool (§5: "Parallelisér gentagelserne over kernerne — de er uafhængige")."""
    rng = np.random.default_rng(seed)
    b_n1 = n1_dannelseslys(bars_15m, ekte_basis_i, rng)
    ud = {}
    for buffer_navn, buffer in BUFFER_VARIANTER.items():
        zoner_n1 = find_zoner_n1(bars_15m, ekte_side, ekte_H, b_n1, buffer)
        klass = sizing_ekte(k1.klassificer_v2(bars_15m, zoner_n1, buffer))
        for be_navn, be_r in BE_VARIANTER.items():
            handler, tael, strejf = handler_for_variant(df_1m, klass, be_r)
            ud[(buffer_navn, be_navn)] = noegletal_handler(
                {"handler": handler, "tael": tael, "strejf": strejf, "zoner": klass})
    return ud


# ---------------------------------------------------------------------------
# N2, §5 — FORELØBIG, samme forbehold som N1: bygget til rapporten, ikke fastlagt i
# detalje af §5 (den angiver intet gentagelsestal for N2, kun R = 500 for N1).
# ---------------------------------------------------------------------------

# §5 giver ikke noget R for N2 ("forklarer", indgår ikke i beslutningsreglen). Et
# pragmatisk, oplyst valg, så "_p50" er en ægte median over gentagelser som for N1 —
# ikke ét enkelt punkt. Rapporteres som sådan, ikke skjult.
N2_GENTAGELSER = 30


def find_zoner_n2(bars: pd.DataFrame, ekte: pd.DataFrame,
                  rng: np.random.Generator) -> pd.DataFrame:
    """N2, §5: dannelseslys og tid bevares; E forskydes med et tilfældigt beløb trukket
    fra ±[0,5H, 3H] (fortegn og størrelse trukket uafhængigt, størrelsen ensfordelt i
    [0,5H, 3H]). Zonens øvrige mekanik — aktivering, ugyldig, berøring, kontraktskift —
    er kerne v2's egne regler, uændrede; kun E flyttes. ``ekte`` er
    ``b4_k1_optaelling.find_zoner_v2``'s egen tabel for den buffer-variant der forklares
    (E, zone_high, zone_low, basis_i, udbrud_i er dens rigtige, urørte værdier).

    **Motorrettelse 2:** hele zonen flyttes med samme forskydning — ``zone_high`` og
    ``zone_low`` med, ikke kun ``E``. Ellers ændres stopafstanden (E − zone_low for
    demand) med forskydningen selv, og kan blive negativ. H (zone_high − zone_low) og
    dermed risikoen er uændret; kun zonens plads på prisaksen flytter sig.
    """
    o, h, l, c = (bars[k].to_numpy(dtype=float) for k in ("open", "high", "low", "close"))
    n = len(bars)
    iid = (bars["instrument_id"].to_numpy() if "instrument_id" in bars.columns
           else np.zeros(n, dtype=np.int64))
    skift = np.flatnonzero(iid[1:] != iid[:-1]) + 1
    naeste_skift = np.r_[skift, n][np.searchsorted(skift, np.arange(n), side="right")]

    rows = []
    for row in ekte.itertuples():
        demand = row.side == DEMAND
        H = row.zone_high - row.zone_low
        fortegn = 1.0 if rng.random() < 0.5 else -1.0
        magnitude = rng.uniform(0.5 * H, 3.0 * H)
        forskydning = fortegn * magnitude
        E_n2 = row.E + forskydning
        b, u = int(row.basis_i), int(row.udbrud_i)
        k = int(naeste_skift[b])
        zone_high, zone_low = row.zone_high + forskydning, row.zone_low + forskydning
        aktiv = -1
        if k <= u:
            status, slut = k1.KONTRAKTSKIFT, k
        else:
            forladt = l[u:k] > E_n2 if demand else h[u:k] < E_n2
            gennem = c[u:k] < zone_low if demand else c[u:k] > zone_high
            gennem[0] = False
            ia = int(np.argmax(forladt)) if forladt.any() else None
            ig = int(np.argmax(gennem)) if gennem.any() else None
            if ig is not None and (ia is None or ig < ia):
                status, slut = k1.UGYLDIG, u + ig
            elif ia is not None:
                aktiv = u + ia
                ramt = (l[aktiv + 1:k] <= E_n2) if demand else (h[aktiv + 1:k] >= E_n2)
                if ramt.any():
                    status, slut = k1.BEROERT, aktiv + 1 + int(np.argmax(ramt))
                elif k < n:
                    status, slut = k1.KONTRAKTSKIFT, k
                else:
                    status, slut = k1.AKTIV, -1
            elif k < n:
                status, slut = k1.KONTRAKTSKIFT, k
            else:
                status, slut = k1.ALDRIG_AKTIV, -1
        rows.append((row.side, b, u, bars.index[b], bars.index[u], zone_high, zone_low,
                    row.basis_close, row.hoejde_pct, row.over_hul, status, slut,
                    bars.index[slut] if slut >= 0 else pd.NaT,
                    float("nan"), E_n2, aktiv,
                    bars.index[aktiv] if aktiv >= 0 else pd.NaT))
    z = pd.DataFrame(rows, columns=k1.ZONEKOLONNER_V2)
    for kol in ("basis_tid", "udbrud_tid", "slut_tid", "aktiv_tid"):
        z[kol] = pd.to_datetime(z[kol], utc=True)
    return z


def n2_gentagelse(df_1m: pd.DataFrame, bars_15m: pd.DataFrame,
                  ekte_pr_buffer: dict[str, pd.DataFrame], seed: int) -> dict:
    """Én N2-gentagelse, alle 6 varianter — samme form som ``n1_gentagelse``."""
    rng = np.random.default_rng(seed)
    ud = {}
    for buffer_navn, buffer in BUFFER_VARIANTER.items():
        zoner_n2 = find_zoner_n2(bars_15m, ekte_pr_buffer[buffer_navn], rng)
        klass = sizing_ekte(k1.klassificer_v2(bars_15m, zoner_n2, buffer))
        for be_navn, be_r in BE_VARIANTER.items():
            handler, tael, strejf = handler_for_variant(df_1m, klass, be_r)
            ud[(buffer_navn, be_navn)] = noegletal_handler(
                {"handler": handler, "tael": tael, "strejf": strejf, "zoner": klass})
    return ud


# ---------------------------------------------------------------------------
# Nøgletal, §8 (uddrag — den fulde rapport skrives først i trin 2)
# ---------------------------------------------------------------------------

def zone_diagnostik(klass: pd.DataFrame) -> dict:
    """§5: ``zoner_n``, ``beroeringer_n`` og ``ugyldig_foer_aktiv_pct`` — N1's krævede
    diagnostik, holdt op mod kernens egne (samme funktion bruges på begge)."""
    n = len(klass)
    beroert = int((klass["status"] == k1.BEROERT).sum())
    ugyldig = int((klass["status"] == k1.UGYLDIG).sum())
    return {"zoner_n": n, "beroeringer_n": beroert,
            "ugyldig_foer_aktiv_pct": 100 * ugyldig / n if n else float("nan")}


def _noegletal(handler: pd.DataFrame, strejf: pd.DataFrame, zoner: pd.DataFrame,
               tael: dict) -> dict:
    """Kernen i ``noegletal_handler`` — opererer på allerede filtrerede tabeller, så den
    kan genbruges til "pr. side" og "pr. år"-nedbrydningerne uden at køre dagens
    gennemløb igen. ``tael`` (springet over position/dagslukket) er et dagsniveau-tal,
    ikke opdelt pr. side eller år — det rapporteres uændret, samme tal i hver nedbrydning.
    """
    row = dict(tael)
    row.update(zone_diagnostik(zoner))
    row["handler_n"] = len(handler)
    row["censurerede_zoner_n"] = int(
        zoner["status"].isin((k1.AKTIV, k1.ALDRIG_AKTIV)).sum()) if len(zoner) else 0
    if len(handler):
        row["middel_R_brutto"] = float(handler["R_brutto"].mean())
        row["middel_R_netto"] = float(handler["R_netto"].mean())
        row["middel_R_netto_ci95_lo"], row["middel_R_netto_ci95_hi"] = \
            mean_ci_t(handler["R_netto"])
        vundet = int((handler["udfald"] == MAAL).sum())
        lo, hi = wilson_interval(vundet, len(handler))
        row["win_rate_pct_netto"] = 100 * vundet / len(handler)
        row["win_rate_ci95_lo_pct"], row["win_rate_ci95_hi_pct"] = 100 * lo, 100 * hi
        holder_n = int(handler["holder"].sum())
        holder_lo, holder_hi = wilson_interval(holder_n, len(handler))
        row["holder_pct"] = 100 * holder_n / len(handler)
        row["holder_ci95_lo_pct"], row["holder_ci95_hi_pct"] = 100 * holder_lo, 100 * holder_hi
        for u in UDFALD:
            row[f"udfald_{u}_pct"] = 100 * int((handler["udfald"] == u).sum()) / len(handler)
        tid = handler.loc[handler["udfald"] == TIDSEXIT, "R_netto"]
        row["tidsexit_middel_R_netto"] = float(tid.mean()) if len(tid) else float("nan")
        dage = handler["dag"].nunique()
        row["dage_med_handel_n"] = dage
        row["handler_pr_dag_middel"] = len(handler) / dage if dage else float("nan")
    else:
        for navn in ("middel_R_brutto", "middel_R_netto", "middel_R_netto_ci95_lo",
                     "middel_R_netto_ci95_hi", "win_rate_pct_netto", "win_rate_ci95_lo_pct",
                     "win_rate_ci95_hi_pct", "holder_pct", "holder_ci95_lo_pct",
                     "holder_ci95_hi_pct", "tidsexit_middel_R_netto",
                     "handler_pr_dag_middel"):
            row[navn] = float("nan")
        row["dage_med_handel_n"] = 0
        for u in UDFALD:
            row[f"udfald_{u}_pct"] = float("nan")
    row["strejf_uden_gennemhandling_n"] = int(len(strejf))
    if len(strejf):
        row["strejf_hvis_fyldt_middel_R_netto"] = float(strejf["R_netto"].mean())
        vundet_s = int((strejf["udfald"] == MAAL).sum())
        row["strejf_hvis_fyldt_win_rate_pct_netto"] = 100 * vundet_s / len(strejf)
    else:
        row["strejf_hvis_fyldt_middel_R_netto"] = float("nan")
        row["strejf_hvis_fyldt_win_rate_pct_netto"] = float("nan")
    sig = zoner[zoner["i_vindue"] & (zoner["kontrakter_ekte"] >= 1)]
    for q in (10, 50, 90):
        row[f"risiko_pt_p{q}"] = k1._p(sig["risiko_pt_ekte"], q)
        row[f"kontrakter_p{q}"] = k1._p(sig["kontrakter_ekte"], q)
    row["omk_R_netto_p50"] = k1._p(sig["omk_R_netto_ekte"], 50)
    row["kontrakter_maks"] = float(sig["kontrakter_ekte"].max()) if len(sig) else float("nan")
    row["afvist_kontrakter_nul_n"] = int(
        (zoner["i_vindue"] & (zoner["kontrakter_ekte"] == 0)).sum())
    return row


def _aar_maske(df: pd.DataFrame, kolonne: str, aar: int) -> pd.DataFrame:
    """``df[df[kolonne].dt.year == aar]``, robust mod en tom tabel (object-dtype)."""
    if len(df) == 0:
        return df
    return df[pd.DatetimeIndex(df[kolonne]).year == aar]


def noegletal_handler(res: dict, side: str | None = None, aar: int | None = None) -> dict:
    """Hovedtallene for én variant: middel-R, udfaldsfordeling, strejf-diagnosen.

    ``side`` (demand/supply) og ``aar`` filtrerer handler/strejf/zoner før aggregeringen
    — §8's krav om "plus demand og supply hver for sig, plus pr. år".
    """
    handler, strejf, zoner = res["handler"], res["strejf"], res["zoner"]
    if side is not None:
        handler = handler[handler["side"] == side]
        strejf = strejf[strejf["side"] == side]
        zoner = zoner[zoner["side"] == side]
    if aar is not None:
        handler = _aar_maske(handler, "dag", aar)
        strejf = _aar_maske(strejf, "dag", aar)
        # "dag" er kun sat for berørte zoner (NaT ellers) — basis_tid findes for alle
        # statusser og er den rigtige tidsreference for zone-niveauets årsopdeling.
        zoner = _aar_maske(zoner, "basis_tid", aar)
    return _noegletal(handler, strejf, zoner, res["tael"])


# ---------------------------------------------------------------------------
# Trin 1: regressionstjek og tidsmåling — ikke selve edge-testen
# ---------------------------------------------------------------------------

def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "--no-optional-locks", "-C", str(ROOT), *args],
                          capture_output=True, text=True)


def regressionstjek() -> bool:
    """§8: det udvidede modul skal gengive ``b4_k1_optaelling_v2.csv`` (commit c18539f)
    præcist, når det fodres kerne v2 på NQ. Kører k1's egen kerne v2-vej uændret.

    Sammenligningen er ``cmp`` på selve csv-teksten, som tillæg 1 §2 foreskriver — IKKE
    en sammenligning af genindlæste float-værdier: ``read_csv`` og ``astype(str)`` kan
    formatere samme float64 med ét ciffer forskel i halen uden at tallet er anderledes.
    """
    import tempfile

    referencen = ROOT / "research" / "output" / "b4_k1_optaelling_v2.csv"
    df = holdout.load_in_sample(k1.SYMBOL)
    dage = k1.rth_dage(holdout.IN_SAMPLE_START, holdout.HOLDOUT_START)
    bars = resample.aggregate(df, k1.BAR_MIN)
    tabeller = []
    for kerne, buffer in ((k1.V2, k1.BUFFER_V2), (k1.V2_UDEN_BUFFER, Fraction(0))):
        zk = k1.zoner_v2(bars, buffer)
        t = k1.tabel(zk, dage, k1.noegletal_v2)
        t.insert(0, "kerne", kerne)
        tabeller.append(t)
    ny = pd.concat(tabeller, ignore_index=True)
    with tempfile.TemporaryDirectory() as tmp:
        sti = Path(tmp) / "ny.csv"
        ny.to_csv(sti, index=False)
        return subprocess.run(["cmp", str(sti), str(referencen)],
                              capture_output=True).returncode == 0


def motorrettelse_maaling() -> dict:
    """``research/prereg/b4_k1_motorrettelse.md``: kun kernen, 6 varianter, før og efter
    de tre motorrettelser. N1 og N2 køres ikke — de kører med den rettede motor i trin 2.

    "Før" er den gamle, ukorrigerede fyldningsbar-opførsel (``ret_fyldningsbar=False``);
    N2's rettelse (hele zonen flyttes) og "holder" påvirker ikke kernens handler_n/R,
    så de indgår ikke i før/efter-forskellen — kun rettelse 1 gør.
    """
    df = holdout.load_in_sample(MNQ)
    df = df[(df.index >= MNQ_START) & (df.index < TRIN_A_SLUT)]
    bars = resample.aggregate(df, k1.BAR_MIN)

    foer = simuler_alle_varianter(df, bars, ret_fyldningsbar=False)
    efter = simuler_alle_varianter(df, bars, ret_fyldningsbar=True)

    rows = []
    for v in efter:
        h_foer, h_efter = foer[v]["handler"], efter[v]["handler"]
        noegle_foer = noegletal_handler(foer[v])
        noegle_efter = noegletal_handler(efter[v])

        basis_foer = set(h_foer["basis_i"])
        basis_efter = set(h_efter["basis_i"])
        faelles = basis_foer & basis_efter
        f_idx = h_foer.set_index("basis_i")
        e_idx = h_efter.set_index("basis_i")
        ramt = sum(
            1 for b in faelles
            if f_idx.loc[b, "udfald"] != e_idx.loc[b, "udfald"]
            or not np.isclose(f_idx.loc[b, "R_brutto"], e_idx.loc[b, "R_brutto"]))

        rows.append({
            "buffer": v[0], "BE": v[1],
            "handler_n_foer": len(h_foer), "handler_n_efter": len(h_efter),
            "handler_kun_i_foer_n": len(basis_foer - basis_efter),
            "handler_kun_i_efter_n": len(basis_efter - basis_foer),
            "middel_R_netto_foer": noegle_foer["middel_R_netto"],
            "middel_R_netto_efter": noegle_efter["middel_R_netto"],
            "forskel": noegle_efter["middel_R_netto"] - noegle_foer["middel_R_netto"],
            "handler_ramt_af_rettelse_1_n": ramt,
            "holder_pct": noegle_efter["holder_pct"],
            "holder_ci95_lo_pct": noegle_efter["holder_ci95_lo_pct"],
            "holder_ci95_hi_pct": noegle_efter["holder_ci95_hi_pct"],
        })
    return {"tabel": pd.DataFrame(rows), "foer": foer, "efter": efter,
           "n_1m": len(df), "n_15m": len(bars)}


def hovedtabel_motorrettelse_markdown(tabel: pd.DataFrame) -> str:
    linjer = ["| buffer | BE | handler_n (før/efter) | middel_R_netto før | efter | "
             "forskel | ramt af rettelse 1 | holder_pct [CI95] |",
             "|---|---|---|---|---|---|---|---|"]
    for _, r in tabel.iterrows():
        linjer.append(
            f"| {r['buffer']} | {r['BE']} | {int(r['handler_n_foer'])}/{int(r['handler_n_efter'])} | "
            f"{_tal(r['middel_R_netto_foer'], 4)} | {_tal(r['middel_R_netto_efter'], 4)} | "
            f"{_tal(r['forskel'], 4)} | {int(r['handler_ramt_af_rettelse_1_n'])} | "
            f"{_tal(r['holder_pct'], 1)} [{_tal(r['holder_ci95_lo_pct'], 1)}; "
            f"{_tal(r['holder_ci95_hi_pct'], 1)}] |")
    return "\n".join(linjer) + "\n"


def skriv_motorrettelse_md(maaling: dict, meta: dict) -> str:
    tabel = maaling["tabel"]
    ramt_i_alt = int(tabel["handler_ramt_af_rettelse_1_n"].sum())
    kun_foer = int(tabel["handler_kun_i_foer_n"].sum())
    kun_efter = int(tabel["handler_kun_i_efter_n"].sum())
    forskel_max = tabel["forskel"].abs().max()
    dele = [
        "# B4 kandidat 1 — motorrettelse efter trin A\n",
        f"Kørt {meta['koert_utc']} UTC fra commit `{meta['head'][:7]}` af Code, med modul, "
        f"tests og præregistrering committet og uændrede. Præregistrering "
        f"`research/prereg/b4_k1_motorrettelse.md` (commit `{meta['commits'][_rel(PREREG_MOTOR)][:7]}`). "
        f"Kode `research/b4_k1_trinA.py` (commit "
        f"`{meta['commits'][_rel(Path(__file__))][:7]}`).\n",
        f"Serie: MNQ.v.0, samme som trin A. {meta['n_1m']} 1m-barer → {meta['n_15m']} "
        f"15m-barer. **Kun kernen, 6 varianter. N1 og N2 kørt ikke.**\n",
        "**Regressionstjek: OK**, `b4_k1_optaelling_v2.csv` gengivet byte for byte fra "
        "kerne v2 på NQ, uændret modul.\n",
        "## Tre rettelser\n",
        "1. Fyldningsbaren: kun stoppet kan rammes der. Mål, BE-trigger og +1R tjekkes "
        "fra næste 1m-bar. Gælder overalt `simuler_handel` bruges (kerne, N1, N2, strejf).\n",
        "2. N2: hele zonen (zone_high, zone_low, E) forskydes med samme beløb, så "
        "stopafstanden bevares.\n",
        "3. `holder_pct`: andel handler hvor +1R nås før stoppet, fyldningsbaren undtaget. "
        "Tidsexit tæller som holder hvis +1R blev nået før 21:50. Wilson-CI.\n",
        "## Målingen — før/efter, kun kernen\n",
        hovedtabel_motorrettelse_markdown(tabel),
        f"`handler_ramt_af_rettelse_1_n` i alt: {ramt_i_alt} (samme udfald eller R_brutto "
        f"før og efter, matchet på zonens `basis_i`, tæller ikke med). Handler der kun "
        f"findes i én af de to kørsler (dagsdisciplinen kaskaderede): "
        f"{kun_foer} kun før, {kun_efter} kun efter.\n",
        f"Største ændring i middel_R_netto blandt de 6 varianter: {_tal(forskel_max, 4)} R.\n",
        "## Efter kørslen\n",
        "Stop. Ingen ændring af andet end de tre rettelser.\n",
    ]
    return "\n".join(dele)


def tidsmaaling() -> dict:
    """Ét fuldt gennemløb af de 6 varianter over MNQ 2019-05-06 → 2023-12-31, og en
    fremskrivning til 6 × 500 N1-gentagelser. Kører ikke selve testen."""
    df = holdout.load_in_sample(MNQ)
    df = df[(df.index >= MNQ_START) & (df.index < TRIN_A_SLUT)]
    bars = resample.aggregate(df, k1.BAR_MIN)

    start = time.perf_counter()
    resultater = simuler_alle_varianter(df, bars)
    varighed_s = time.perf_counter() - start

    noegletal = {navn: noegletal_handler(res) for navn, res in resultater.items()}
    n_handler = sum(int(r["handler_n"]) for r in noegletal.values())

    n_reps = 500
    return {
        "varighed_6_varianter_s": varighed_s,
        "n_handler_i_alt": n_handler,
        "n_1m_barer": len(df), "n_15m_barer": len(bars),
        "n_reps": n_reps,
        "forventet_total_s": varighed_s * (1 + n_reps),
        "forventet_total_timer": varighed_s * (1 + n_reps) / 3600,
        "noegletal": noegletal,
    }


def _n1_gentagelse_med_tid(df_1m: pd.DataFrame, bars_15m: pd.DataFrame,
                          ekte_side: np.ndarray, ekte_basis_i: np.ndarray,
                          ekte_H: np.ndarray, seed: int) -> tuple[int, float, dict]:
    """Wrapper til proces-poolen: én N1-gentagelse, tiden målt inde i workeren (så
    pickling/overførsel af data IKKE tælles med i "tid pr. gentagelse")."""
    start = time.perf_counter()
    res = n1_gentagelse(df_1m, bars_15m, ekte_side, ekte_basis_i, ekte_H, seed)
    varighed = time.perf_counter() - start
    return seed, varighed, {navn: int(r["handler_n"]) for navn, r in res.items()}


def n1_tidsmaaling(n_gentagelser: int = 5, max_workers: int | None = None) -> dict:
    """Punkt 4: mål N1 rigtigt. ``n_gentagelser`` rigtige N1-kørsler (alle 6 varianter
    hver), parallelliseret over kernerne — gentagelserne er uafhængige, §5. R holdes på
    500 andetsteds; dette kører kun ``n_gentagelser`` af dem, til selve tidsmålingen.
    Kører ikke Westfall-Young eller nogen beslutningsregel.
    """
    df = holdout.load_in_sample(MNQ)
    df = df[(df.index >= MNQ_START) & (df.index < TRIN_A_SLUT)]
    bars = resample.aggregate(df, k1.BAR_MIN)
    ekte = k1.find_zoner_v2(bars, k1.BUFFER_V2)     # zone-identitet: buffer-uafhængig
    ekte_side = ekte["side"].to_numpy()
    ekte_basis_i = ekte["basis_i"].to_numpy()
    ekte_H = (ekte["zone_high"] - ekte["zone_low"]).to_numpy(dtype=float)

    n_workere = max_workers or min(n_gentagelser, os.cpu_count() or 1)
    start_batch = time.perf_counter()
    resultater = []
    with ProcessPoolExecutor(max_workers=n_workere) as pool:
        futures = [pool.submit(_n1_gentagelse_med_tid, df, bars, ekte_side, ekte_basis_i,
                               ekte_H, 1000 + i)
                  for i in range(n_gentagelser)]
        for f in as_completed(futures):
            resultater.append(f.result())
    total_wall_batch_s = time.perf_counter() - start_batch
    resultater.sort()

    middel_s = sum(v for _, v, _ in resultater) / len(resultater)
    # Middel pr. gentagelse undervurderer den paralleliserede kørsel: konkurrence om
    # CPU/hukommelse gør hver gentagelse langsommere når flere kører samtidigt (målt: op
    # til ~2,8× langsommere med 4 samtidige mod 1 alene på denne maskine). Det reelle
    # gennemløb er derfor batchens væg-ur, ikke middelværdien delt med antal arbejdere.
    effektiv_s_paralleliseret = total_wall_batch_s / n_gentagelser
    n_reps_total = 500
    return {
        "n_gentagelser": n_gentagelser, "n_workere": n_workere,
        "cpu_count": os.cpu_count(),
        "resultater": resultater, "middel_s_pr_gentagelse": middel_s,
        "total_wall_s_for_batch": total_wall_batch_s,
        "effektiv_s_pr_gentagelse_paralleliseret": effektiv_s_paralleliseret,
        "n_reps_total": n_reps_total,
        "forventet_total_s_seriel": middel_s * (n_reps_total + 1),
        "forventet_total_s_paralleliseret": effektiv_s_paralleliseret * (n_reps_total + 1),
    }


# ---------------------------------------------------------------------------
# Trin 2: selve kørslen — §6-§8
# ---------------------------------------------------------------------------

# Optælling 2's helsample-facit (2016-01-01 til 2023-12-31), citeret til sammenligning i
# krydstjekket, §4d/§8 — ikke genberegnet for trin A's delperiode.
NQ_REFERENCE_DAGE_MED_SIGNAL_N = 1817
NQ_REFERENCE_SIGNALER_N = 5350
NQ_REFERENCE_PERIODE = "2016-01-01 til 2023-12-31 (optælling 2, helsample, buffer 10%)"


def westfall_young(virkelig: dict[tuple, dict], n1_liste: list[dict[tuple, dict]]) -> dict:
    """§6: Westfall-Young maks-statistik. ``virkelig`` og hvert element i ``n1_liste`` er
    {(buffer,be): noegletal}-ordbøger. p_FWE er kun defineret for den observerede bedste
    variant — Westfall-Young beskytter netop VALGET af den bedste blandt de 6."""
    varianter = list(virkelig.keys())
    virkelig_R = {v: virkelig[v]["middel_R_netto"] for v in varianter}
    bedste_variant = max(varianter, key=lambda v: virkelig_R[v])
    observeret_bedste = virkelig_R[bedste_variant]

    n1_maks = np.array([
        np.nanmax([rep[v]["middel_R_netto"] for v in varianter]) for rep in n1_liste])
    R = len(n1_liste)
    p_fwe = (1 + int((n1_maks >= observeret_bedste).sum())) / (1 + R)

    n1_pr_variant = {v: np.array([rep[v]["middel_R_netto"] for rep in n1_liste])
                     for v in varianter}
    n1_handler_pr_variant = {v: np.array([rep[v]["handler_n"] for rep in n1_liste])
                             for v in varianter}
    return {"varianter": varianter, "bedste_variant": bedste_variant,
            "observeret_bedste_middel_R_netto": observeret_bedste, "p_fwe": p_fwe, "R": R,
            "n1_maks_fordeling": n1_maks, "n1_pr_variant": n1_pr_variant,
            "n1_handler_pr_variant": n1_handler_pr_variant}


def krydstjek_nq(mnq_zoner_buffer10: pd.DataFrame) -> dict:
    """§4d/§8: signaldage/signaler for kerne v2 på MNQ i delperioden, BEGGE veje — med
    procentreglen (k1's egen ``signal``, sammenligneligt med NQ's tal) og med
    dollarloftet (``i_vindue`` og ``kontrakter_ekte >= 1``, det trin A faktisk handler).
    De to tal er ikke ens, og det er ikke en regressionsfejl.
    """
    z = mnq_zoner_buffer10
    sig_pct = z[z["signal"]]
    sig_dollar = z[z["i_vindue"].astype(bool) & (z["kontrakter_ekte"] >= 1)]
    return {
        "dage_med_signal_procentregel_n": int(sig_pct["dag"].dt.normalize().nunique()),
        "signaler_procentregel_n": int(len(sig_pct)),
        "dage_med_signal_dollarloft_n": int(sig_dollar["dag"].dt.normalize().nunique()),
        "signaler_dollarloft_n": int(len(sig_dollar)),
        "nq_dage_med_signal_n": NQ_REFERENCE_DAGE_MED_SIGNAL_N,
        "nq_signaler_n": NQ_REFERENCE_SIGNALER_N, "nq_periode": NQ_REFERENCE_PERIODE,
    }


def _p_liste(vaerdier: np.ndarray, q: float) -> float:
    return float(np.percentile(vaerdier, q)) if len(vaerdier) else float("nan")


def variant_raekke(variant: tuple, virkelig: dict, wy: dict, n2_liste: list[dict],
                   side: str | None = None, aar: int | None = None) -> dict:
    """Én række i hovedtabellen, §8 — den rigtige kernes tal, plus N1 og N2's nøgletal
    for netop denne variant. N1/N2's fordelinger er over HELE gentagelser og filtreres
    ikke selv pr. side/år (det ville kræve at gemme hver gentagelses fulde handelstabel —
    §8 beder kun om N1/N2's tal på variant-niveau, ikke nedbrudt yderligere)."""
    buffer_navn, be_navn = variant
    row = {"buffer": buffer_navn, "BE": be_navn, "side": side or "alle",
          "periode": str(aar) if aar else "2019-2023"}
    row.update(noegletal_handler(virkelig[variant], side=side, aar=aar))

    n1_R = wy["n1_pr_variant"][variant]
    row["N1_middel_R_netto_p5"] = _p_liste(n1_R, 5)
    row["N1_middel_R_netto_p50"] = _p_liste(n1_R, 50)
    row["N1_middel_R_netto_p95"] = _p_liste(n1_R, 95)
    row["N1_handler_n_p50"] = _p_liste(wy["n1_handler_pr_variant"][variant], 50)
    if variant == wy["bedste_variant"] and side is None and aar is None:
        row["p_FWE"] = wy["p_fwe"]
    else:
        row["p_FWE"] = float("nan")

    n2_R = np.array([rep[variant]["middel_R_netto"] for rep in n2_liste])
    row["N2_middel_R_netto_p50"] = _p_liste(n2_R, 50)
    return row


def n1_kerne_sammenligning(virkelig: dict, n1_liste: list[dict],
                          wy: dict) -> tuple[pd.DataFrame, list[tuple]]:
    """§5's obligatoriske tabel: N1's zoner_n/beroeringer_n/handler_n/
    ugyldig_foer_aktiv_pct (median over gentagelserne) holdt op mod kernens egne, pr.
    variant. Returnerer (tabel, liste over varianter hvor N1's handler_n < 30% af
    kernens — forbeholdet §5 kræver hvis det sker).
    """
    rows, forbehold = [], []
    for v in wy["varianter"]:
        kerne = virkelig[v]
        zoner_n1 = np.array([rep[v]["zoner_n"] for rep in n1_liste], dtype=float)
        beroeringer_n1 = np.array([rep[v]["beroeringer_n"] for rep in n1_liste], dtype=float)
        handler_n1 = np.array([rep[v]["handler_n"] for rep in n1_liste], dtype=float)
        ugyldig_n1 = np.array([rep[v]["ugyldig_foer_aktiv_pct"] for rep in n1_liste],
                              dtype=float)
        n1_handler_p50 = _p_liste(handler_n1, 50)
        if kerne["handler_n"] > 0 and n1_handler_p50 < 0.30 * kerne["handler_n"]:
            forbehold.append(v)
        rows.append({
            "buffer": v[0], "BE": v[1],
            "kerne_zoner_n": kerne["zoner_n"], "N1_zoner_n_p50": _p_liste(zoner_n1, 50),
            "kerne_beroeringer_n": kerne["beroeringer_n"],
            "N1_beroeringer_n_p50": _p_liste(beroeringer_n1, 50),
            "kerne_handler_n": kerne["handler_n"], "N1_handler_n_p50": n1_handler_p50,
            "kerne_ugyldig_foer_aktiv_pct": kerne["ugyldig_foer_aktiv_pct"],
            "N1_ugyldig_foer_aktiv_pct_p50": _p_liste(ugyldig_n1, 50),
        })
    return pd.DataFrame(rows), forbehold


# §7's fire kategorier, fra parkeret (værst) til brugbar edge (bedst) — brugt til at finde
# den laveste kategori når konfidensintervallet krydser en grænse.
_KATEGORI_RAEKKEFOELGE = ["parkeres", "graenseomraade", "neutral", "reel_men_lille",
                         "brugbar_edge"]


def _klassificer_udfald(p: float, R: float, n1_median: float, n1_p5: float) -> str:
    if p <= 0.05 and R >= 0.20:
        return "brugbar_edge"
    if p <= 0.05 and 0.10 <= R < 0.20:
        return "reel_men_lille"
    if p > 0.05 and R >= n1_median:
        return "neutral"
    if R < n1_p5:
        return "parkeres"
    return "graenseomraade"


def beslutning_trin_a(wy: dict, virkelig_noegletal: dict) -> dict:
    """§7, anvendt mekanisk på den observerede bedste variant. "Krydser
    konfidensintervallet en grænse, gælder den laveste kategori" — klassificerer CI'ets
    to ender hver for sig og tager den laveste hvis de er uenige."""
    v = wy["bedste_variant"]
    bedste = virkelig_noegletal[v]
    p, R = wy["p_fwe"], bedste["middel_R_netto"]
    lo, hi = bedste["middel_R_netto_ci95_lo"], bedste["middel_R_netto_ci95_hi"]
    n1_median = _p_liste(wy["n1_pr_variant"][v], 50)
    n1_p5 = _p_liste(wy["n1_pr_variant"][v], 5)
    kat_punkt = _klassificer_udfald(p, R, n1_median, n1_p5)
    kat_lo = _klassificer_udfald(p, lo, n1_median, n1_p5)
    kat_hi = _klassificer_udfald(p, hi, n1_median, n1_p5)
    uafgjort = len({kat_lo, kat_hi}) > 1
    kategori = (min((kat_lo, kat_hi), key=_KATEGORI_RAEKKEFOELGE.index) if uafgjort
               else kat_punkt)
    return {"variant": v, "p_fwe": p, "middel_R_netto": R, "ci_lo": lo, "ci_hi": hi,
            "n1_median": n1_median, "n1_p5": n1_p5, "kategori_punktestimat": kat_punkt,
            "uafgjort": uafgjort, "kategori": kategori}


AAR_LISTE = list(range(2019, 2024))


def fuld_tabel(virkelig: dict, wy: dict, n2_liste: list[dict]) -> pd.DataFrame:
    """Hele §8-tabellen: pr. variant (6), plus demand/supply hver for sig, plus pr. år.

    ``virkelig`` er ``simuler_alle_varianter``'s RÅ resultat (handler/strejf/zoner pr.
    variant) — ``variant_raekke`` filtrerer selv pr. side/år via ``noegletal_handler``.
    """
    rows = []
    for v in wy["varianter"]:
        for side in (None, k1.DEMAND, k1.SUPPLY):
            rows.append(variant_raekke(v, virkelig, wy, n2_liste, side=side))
            for aar in AAR_LISTE:
                rows.append(variant_raekke(v, virkelig, wy, n2_liste, side=side, aar=aar))
    return pd.DataFrame(rows)


def koer_trin_a(n1_reps: int = 500, n2_reps: int = N2_GENTAGELSER,
                max_workers: int | None = None) -> dict:
    """Selve trin A-kørslen, §6-§8. Regressionstjekket først — afviger det, køres intet."""
    if not regressionstjek():
        raise RuntimeError("REGRESSIONSTJEK afveg — trin A køres ikke")

    df = holdout.load_in_sample(MNQ)
    df = df[(df.index >= MNQ_START) & (df.index < TRIN_A_SLUT)]
    bars = resample.aggregate(df, k1.BAR_MIN)

    virkelig = simuler_alle_varianter(df, bars)
    virkelig_noegletal = {v: noegletal_handler(res) for v, res in virkelig.items()}

    ekte_v2 = k1.find_zoner_v2(bars, k1.BUFFER_V2)
    ekte_side = ekte_v2["side"].to_numpy()
    ekte_basis_i = ekte_v2["basis_i"].to_numpy()
    ekte_H = (ekte_v2["zone_high"] - ekte_v2["zone_low"]).to_numpy(dtype=float)
    n_workere = max_workers or (os.cpu_count() or 1)

    n1_liste = []
    with ProcessPoolExecutor(max_workers=n_workere) as pool:
        futures = [pool.submit(n1_gentagelse, df, bars, ekte_side, ekte_basis_i, ekte_H,
                               2000 + i) for i in range(n1_reps)]
        for f in as_completed(futures):
            n1_liste.append(f.result())

    ekte_pr_buffer = {navn: k1.find_zoner_v2(bars, buffer)
                      for navn, buffer in BUFFER_VARIANTER.items()}
    n2_liste = []
    with ProcessPoolExecutor(max_workers=n_workere) as pool:
        futures = [pool.submit(n2_gentagelse, df, bars, ekte_pr_buffer, 3000 + i)
                  for i in range(n2_reps)]
        for f in as_completed(futures):
            n2_liste.append(f.result())

    wy = westfall_young(virkelig_noegletal, n1_liste)
    sammenligning, forbehold = n1_kerne_sammenligning(virkelig_noegletal, n1_liste, wy)
    kryds = krydstjek_nq(virkelig[("buffer_10", "ingen")]["zoner"])
    beslutning = beslutning_trin_a(wy, virkelig_noegletal)
    tabel = fuld_tabel(virkelig, wy, n2_liste)

    return {
        "df": df, "bars": bars, "virkelig": virkelig, "virkelig_noegletal": virkelig_noegletal,
        "n1_liste": n1_liste, "n2_liste": n2_liste, "wy": wy, "sammenligning": sammenligning,
        "forbehold": forbehold, "kryds": kryds, "beslutning": beslutning, "tabel": tabel,
        "n1_reps": n1_reps, "n2_reps": n2_reps,
    }


def _tal(v, nd: int = 3) -> str:
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "—"
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    return f"{v:.{nd}f}".replace(".", ",")


def hovedtabel_markdown(resultat: dict) -> str:
    """Kompakt hovedtabel, 6 rækker — "alle", 2019-2023. Til chatten og toppen af .md."""
    hele = resultat["tabel"]
    hele = hele[(hele["side"] == "alle") & (hele["periode"] == "2019-2023")]
    linjer = ["| buffer | BE | handler_n | middel_R_netto | CI95 | win_rate_pct | "
             "N1_p50 | N1_p5 | p_FWE | N2_p50 |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in hele.iterrows():
        linjer.append(
            f"| {r['buffer']} | {r['BE']} | {_tal(r['handler_n'])} | "
            f"{_tal(r['middel_R_netto'], 4)} | "
            f"[{_tal(r['middel_R_netto_ci95_lo'], 4)}; {_tal(r['middel_R_netto_ci95_hi'], 4)}] | "
            f"{_tal(r['win_rate_pct_netto'], 1)} | {_tal(r['N1_middel_R_netto_p50'], 4)} | "
            f"{_tal(r['N1_middel_R_netto_p5'], 4)} | {_tal(r['p_FWE'], 4)} | "
            f"{_tal(r['N2_middel_R_netto_p50'], 4)} |")
    return "\n".join(linjer) + "\n"


def sammenligning_markdown(samm: pd.DataFrame) -> str:
    linjer = ["| buffer | BE | zoner_n (kerne/N1_p50) | beroeringer_n (kerne/N1_p50) | "
             "handler_n (kerne/N1_p50) | ugyldig_foer_aktiv_pct (kerne/N1_p50) |",
             "|---|---|---|---|---|---|"]
    for _, r in samm.iterrows():
        linjer.append(
            f"| {r['buffer']} | {r['BE']} | "
            f"{_tal(r['kerne_zoner_n'])}/{_tal(r['N1_zoner_n_p50'], 1)} | "
            f"{_tal(r['kerne_beroeringer_n'])}/{_tal(r['N1_beroeringer_n_p50'], 1)} | "
            f"{_tal(r['kerne_handler_n'])}/{_tal(r['N1_handler_n_p50'], 1)} | "
            f"{_tal(r['kerne_ugyldig_foer_aktiv_pct'], 1)}/"
            f"{_tal(r['N1_ugyldig_foer_aktiv_pct_p50'], 1)} |")
    return "\n".join(linjer) + "\n"


def skriv_trin_a_md(resultat: dict, meta: dict) -> str:
    kryds = resultat["kryds"]
    b = resultat["beslutning"]
    samm = resultat["sammenligning"]
    dele = [
        "# B4 kandidat 1 — trin A: edge-test af kernen\n",
        f"Kørt {meta['koert_utc']} UTC fra commit `{meta['head'][:7]}`, med modul, tests og "
        f"præregistrering committet og uændrede. Præregistrering `{_rel(PREREG)}` "
        f"(commit `{meta['commits'][_rel(PREREG)][:7]}`). Kode `{_rel(Path(__file__))}` "
        f"(commit `{meta['commits'][_rel(Path(__file__))][:7]}`).\n",
        f"Serie: MNQ.v.0 ohlcv-1m gennem `data.holdout.load_in_sample`, "
        f"{MNQ_START.date()} → {(TRIN_A_SLUT - pd.Timedelta(days=1)).date()}. "
        f"{meta['n_1m']} 1m-barer → {meta['n_15m']} 15m-barer. 6 varianter. "
        f"N1: {resultat['n1_reps']} gentagelser. N2: {resultat['n2_reps']} gentagelser "
        f"(FORELØBIG, §5 angiver intet R for N2 — se koden).\n",
        "**Regressionstjek: OK**, `b4_k1_optaelling_v2.csv` gengivet byte for byte fra "
        "kerne v2 på NQ, uændret modul.\n",
        "## Hovedtabel — alle, 2019-2023\n",
        "middel_R_netto med t-CI95 i kantparentes. N1_p50/N1_p5 er den variants egen "
        "fordeling over N1-gentagelserne (ikke maks-fordelingen). p_FWE står kun på den "
        "observerede bedste variant — Westfall-Young beskytter valget af den bedste.\n",
        hovedtabel_markdown(resultat),
        "## N1 mod kernen — §5's obligatoriske sammenligning\n",
        "Median over N1-gentagelserne, holdt op mod kernens egne tal, pr. variant.\n",
        sammenligning_markdown(samm),
    ]
    if resultat["forbehold"]:
        dele.append(
            "**Forbehold, §5:** N1's handler_n er under 30% af kernens for " +
            ", ".join(f"{v[0]}/{v[1]}" for v in resultat["forbehold"]) +
            " — fortolkningen af disse varianters N1-sammenligning skal læses med det "
            "in mente.\n")
    else:
        dele.append("N1's handler_n er ≥ 30% af kernens for alle 6 varianter — intet "
                    "forbehold udløst.\n")
    dele += [
        "## Krydstjek mod NQ — antagelse (A), ikke en variant\n",
        f"MNQ, kerne v2, delperioden {MNQ_START.date()} → "
        f"{(TRIN_A_SLUT - pd.Timedelta(days=1)).date()}, buffer 10%:\n",
        "| | dage_med_signal_n | signaler_n |\n|---|---|---|\n"
        f"| MNQ, procentreglen (k1's `signal`) | {kryds['dage_med_signal_procentregel_n']} | "
        f"{kryds['signaler_procentregel_n']} |\n"
        f"| MNQ, dollarloftet (det trin A handler) | {kryds['dage_med_signal_dollarloft_n']} | "
        f"{kryds['signaler_dollarloft_n']} |\n"
        f"| NQ, reference ({kryds['nq_periode']}) | {kryds['nq_dage_med_signal_n']} | "
        f"{kryds['nq_signaler_n']} |\n",
        "De to MNQ-tal er ikke ens, og det er ikke en regressionsfejl — §4d.\n",
        "## Beslutningsreglen, §7, anvendt mekanisk\n",
        f"Bedste variant: **{b['variant'][0]}/{b['variant'][1]}**. "
        f"middel netto-R = {_tal(b['middel_R_netto'], 4)} R "
        f"(CI95 [{_tal(b['ci_lo'], 4)}; {_tal(b['ci_hi'], 4)}]). "
        f"p_FWE = {_tal(b['p_fwe'], 4)}. N1's median = {_tal(b['n1_median'], 4)}, "
        f"N1's 5%-fraktil = {_tal(b['n1_p5'], 4)}.\n",
        (f"CI'et krydser en grænse: uafgjort, laveste kategori gælder: **{b['kategori']}**.\n"
         if b["uafgjort"] else f"Kategori: **{b['kategori']}**.\n"),
        "## Efter kørslen — §10\n",
        "Stop. Ingen ændring af definitioner, ingen forslag til forbedringer. Resultatet "
        "læses sammen med Mads.\n",
        f"Alle tal, alle varianter × side × år: `{_rel(OUT / 'b4_k1_trinA.csv')}`.\n",
    ]
    return "\n".join(dele)


def _rel(sti: Path) -> str:
    return Path(sti).resolve().relative_to(ROOT.resolve()).as_posix()


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--regressionstjek", action="store_true",
                     help="v2 på NQ skal gengive b4_k1_optaelling_v2.csv præcist")
    grp.add_argument("--tidsmaaling", action="store_true",
                     help="ét gennemløb over MNQ, fremskrevet til 6 × 500 N1-gentagelser")
    grp.add_argument("--n1-tidsmaaling", type=int, nargs="?", const=5, default=None,
                     metavar="N", help="N rigtige N1-gentagelser (standard 5), "
                     "parallelliseret over kernerne")
    grp.add_argument("--koer", action="store_true",
                     help="§6-§8: selve trin A-kørslen. R=500 N1-gentagelser, "
                     "N2_GENTAGELSER N2-gentagelser. Skriver b4_k1_trinA.md/.csv")
    grp.add_argument("--motorrettelse", action="store_true",
                     help="b4_k1_motorrettelse.md: kun kernen, 6 varianter, før/efter "
                     "de tre motorrettelser. Skriver b4_k1_motorrettelse.md")
    ap.add_argument("--n1-reps", type=int, default=500)
    ap.add_argument("--n2-reps", type=int, default=N2_GENTAGELSER)
    args = ap.parse_args(argv)

    if args.regressionstjek:
        ens = regressionstjek()
        print("REGRESSIONSTJEK: " + ("OK — identisk med b4_k1_optaelling_v2.csv" if ens
                                     else "AFVIGER — trin A køres ikke"))
        if not ens:
            sys.exit(1)
        return

    if args.n1_tidsmaaling is not None:
        t = n1_tidsmaaling(args.n1_tidsmaaling)
        print(f"CPU'er: {t['cpu_count']}, arbejdere: {t['n_workere']}")
        for seed, varighed, handler_n in t["resultater"]:
            print(f"  seed {seed}: {varighed:.2f} s, handler_n {handler_n}")
        print(f"Middel pr. gentagelse (uden konkurrence-effekt): "
             f"{t['middel_s_pr_gentagelse']:.2f} s")
        print(f"{t['n_gentagelser']} gentagelser parallelliseret: "
             f"{t['total_wall_s_for_batch']:.2f} s væg-ur, "
             f"{t['effektiv_s_pr_gentagelse_paralleliseret']:.2f} s/gentagelse effektivt")
        print(f"Fremskrevet til R = {t['n_reps_total']} (+ 1 for selve kørslen): "
             f"seriel {t['forventet_total_s_seriel']:.1f} s "
             f"({t['forventet_total_s_seriel'] / 3600:.2f} timer), "
             f"paralleliseret over {t['n_workere']} arbejdere "
             f"{t['forventet_total_s_paralleliseret']:.1f} s "
             f"({t['forventet_total_s_paralleliseret'] / 3600:.2f} timer)")
        return

    if args.koer:
        commits = k1.committede((Path(__file__).resolve(), PREREG))
        resultat = koer_trin_a(n1_reps=args.n1_reps, n2_reps=args.n2_reps)
        meta = {
            "koert_utc": pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M"),
            "head": _git("rev-parse", "HEAD").stdout.strip(),
            "commits": commits,
            "n_1m": len(resultat["df"]), "n_15m": len(resultat["bars"]),
        }
        md = skriv_trin_a_md(resultat, meta)
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "b4_k1_trinA.md").write_text(md, encoding="utf-8")
        resultat["tabel"].to_csv(OUT / "b4_k1_trinA.csv", index=False)
        print(md)
        print(f"skrev {OUT / 'b4_k1_trinA.md'} og .csv")
        return

    if args.motorrettelse:
        commits = k1.committede((Path(__file__).resolve(), PREREG_MOTOR))
        maaling = motorrettelse_maaling()
        meta = {
            "koert_utc": pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M"),
            "head": _git("rev-parse", "HEAD").stdout.strip(),
            "commits": commits,
        }
        md = skriv_motorrettelse_md(maaling, meta)
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "b4_k1_motorrettelse.md").write_text(md, encoding="utf-8")
        print(md)
        print(f"skrev {OUT / 'b4_k1_motorrettelse.md'}")
        return

    t = tidsmaaling()
    print(f"1m-barer: {t['n_1m_barer']}, 15m-barer: {t['n_15m_barer']}")
    print(f"6 varianter, ét gennemløb: {t['varighed_6_varianter_s']:.2f} s, "
         f"{t['n_handler_i_alt']} handler i alt")
    print(f"Fremskrevet til 6 varianter × {t['n_reps']} N1-gentagelser "
         f"(+ 1 for selve kørslen): {t['forventet_total_s']:.1f} s "
         f"= {t['forventet_total_timer']:.2f} timer")
    for (buffer_navn, be_navn), row in t["noegletal"].items():
        print(f"  {buffer_navn}/{be_navn}: handler_n={row['handler_n']} "
             f"middel_R_netto={row['middel_R_netto']:.4f}")


if __name__ == "__main__":
    main()
