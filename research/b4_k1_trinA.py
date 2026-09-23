"""B4 kandidat 1 — trin A: handelsmodul, fra fyldning til udgang.

Præregistreret i ``research/prereg/b4_k1_trinA.md``. Bygger videre på zonefundet i
``research/b4_k1_optaelling.py`` (kerne v2, ``zoner_v2``/``klassificer_v2``), som står
uændret — dette modul lægger handelsmekanikken (§4) oven på den samme zoneliste.

**Trin 1 (byg og verificér) kører ikke selve edge-testen.** Se ``main()``:
``--regressionstjek`` og ``--tidsmaaling`` er de to ting trin 1 beder om. Trin 2 (6
varianter × N1 med 500 gentagelser, Westfall-Young) kræver Mads' godkendelse og er ikke
implementeret her.

## Hvorfor sizing regnes om, §4d

``research/b4_k1_optaelling.py``'s ``sizing()`` regner risiko i point ved en FAST
reference (NQ 29.138, jf. ``b4_hypoteser.md``, "Prisniveau"). Det er rigtigt til
optællingens beskrivende procentiler (sammenlignelige tal på tværs af år hvor NQ er
tredoblet), men det er IKKE den rigtige risiko for en faktisk handel: prisen var reel
historisk, ikke ved 29.138. §4d er eksplicit: **"Risiko = E − low = 1,1 × H"** — et
rigtigt pointtal fra zonens egne E/low/high, ikke en omregning. Handelsmodulet bruger
derfor sine egne ``*_ekte``-kolonner (``sizing_ekte``), regnet direkte på zonens rigtige
priser. Stoploftet (``under_stoploft``, en procent af den rigtige basislyspris) er
upåvirket og genbruges som det er.

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
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data import holdout, resample  # noqa: E402
from research import b4_k1_optaelling as k1  # noqa: E402
from research.stats import mean_ci_t, wilson_interval  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "output"
PREREG = ROOT / "research" / "prereg" / "b4_k1_trinA.md"

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

MAAL, STOP, BE_UDFALD, TIDSEXIT, CENSURERET = "maal", "stop", "BE", "tidsexit", "censureret"
UDFALD = (MAAL, STOP, BE_UDFALD, TIDSEXIT, CENSURERET)


# ---------------------------------------------------------------------------
# §4d: den ægte punktrisiko — erstatter k1's NQ 29.138-normerede sizing
# ---------------------------------------------------------------------------

def sizing_ekte(zoner: pd.DataFrame) -> pd.DataFrame:
    """Tilføjer ``risiko_pt_ekte``, ``kontrakter_ekte`` og ``omk_R_netto_ekte``.

    Risiko = E − zone_low (demand) / zone_high − E (supply) — reelle priser, §4d.
    Samme afrunding før floor som k1's ``sizing()`` (fjerner flydende tals støj).
    """
    z = zoner.copy()
    demand = (z["side"] == DEMAND).to_numpy()
    E = z["E"].to_numpy(dtype=float)
    low, high = z["zone_low"].to_numpy(dtype=float), z["zone_high"].to_numpy(dtype=float)
    risiko_pt = np.where(demand, E - low, high - E)
    risiko_usd = risiko_pt * MNQ_USD_PR_POINT
    z["risiko_pt_ekte"] = risiko_pt
    z["kontrakter_ekte"] = np.floor(np.round(RISIKO_USD / risiko_usd, 9))
    z["omk_R_netto_ekte"] = OMK_USD_RUNDTUR / risiko_usd
    return z


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
                   be_r: float | None, cutoff_i: int, n: int) -> tuple[str, float, int]:
    """Fra fyldningsbaren og frem, 1m-bar for 1m-bar. Returnerer (udfald, R_brutto, exit_i).

    ``cutoff_i`` er positionen for 14:50 CT-fladten (ekskl.), ``n`` seriens længde —
    løber vi ud over serien, er handlen censureret ved in-sample-slut, ikke tidsexit.
    """
    maal = entry_pris + RR * risiko_pt if demand else entry_pris - RR * risiko_pt
    stop_niveau = entry_pris - risiko_pt if demand else entry_pris + risiko_pt
    be_trigger = None
    if be_r is not None:
        be_trigger = entry_pris + be_r * risiko_pt if demand else entry_pris - be_r * risiko_pt
    be_armet = False
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
            return udfald, r, i
        maal_ramt = (hi >= maal) if demand else (lo <= maal)
        if maal_ramt:
            return MAAL, RR, i
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
    return udfald, r, sidste_i


# ---------------------------------------------------------------------------
# Dagens gennemløb, §4b — fyldningen og disciplinreglerne
# ---------------------------------------------------------------------------

def handler_for_variant(df_1m: pd.DataFrame, zoner: pd.DataFrame, be_r: float | None
                        ) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    """Alle handler for én BE-variant. ``zoner`` er kerne v2 (klassificeret, med
    ``sizing_ekte``-kolonnerne) for én buffer-variant.

    Kandidaterne er zoner med ``signal`` og mindst 1 ægte kontrakt, kronologisk pr. dag.
    En berøring mens en position er åben, eller efter dagen er lukket, springes over og
    tælles. Fyldes ordren ikke (strejf), regnes en kontrafaktisk handel til diagnose,
    §4c — den ændrer intet i tælling eller stat.
    """
    times = df_1m.index
    h = df_1m["high"].to_numpy(dtype=float)
    l = df_1m["low"].to_numpy(dtype=float)
    c = df_1m["close"].to_numpy(dtype=float)
    n = len(df_1m)

    kand = zoner[zoner["signal"] & (zoner["kontrakter_ekte"] > 0)]
    kand = kand.sort_values(["dag", "slut_tid", "basis_i"]).reset_index(drop=True)

    rows: list[dict] = []
    strejf_rows: list[dict] = []
    tael = {"signaler_sprunget_over_position_n": 0, "signaler_sprunget_over_dagslukket_n": 0}

    for dag, gruppe in kand.groupby("dag", sort=True):
        dagslukket = False
        be_count = 0
        fri_fra = None
        for r in gruppe.itertuples():
            t = r.slut_tid
            if dagslukket:
                tael["signaler_sprunget_over_dagslukket_n"] += 1
                continue
            if fri_fra is not None and t < fri_fra:
                tael["signaler_sprunget_over_position_n"] += 1
                continue
            demand = r.side == DEMAND
            E = r.E
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
                    udfald, r_brutto, _ = simuler_handel(
                        h, l, c, j, E, demand, r.risiko_pt_ekte, be_r, cutoff_i, n)
                    strejf_rows.append({
                        "dag": dag, "side": r.side, "basis_i": r.basis_i,
                        "udfald": udfald, "R_brutto": r_brutto,
                        "R_netto": r_brutto - r.omk_R_netto_ekte,
                    })
                continue
            fyld_i = i0 + int(np.argmax(gennem))
            cutoff_i = int(times.searchsorted(flad_tid_utc(times[fyld_i])))
            udfald, r_brutto, exit_i = simuler_handel(
                h, l, c, fyld_i, E, demand, r.risiko_pt_ekte, be_r, cutoff_i, n)
            r_netto = r_brutto - r.omk_R_netto_ekte
            rows.append({
                "dag": dag, "side": r.side, "basis_i": r.basis_i,
                "fyld_tid": times[fyld_i], "exit_tid": times[exit_i],
                "udfald": udfald, "R_brutto": r_brutto, "R_netto": r_netto,
                "risiko_pt": r.risiko_pt_ekte, "kontrakter": r.kontrakter_ekte,
                "omk_R_netto": r.omk_R_netto_ekte,
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
                                          "kontrakter", "omk_R_netto"])
    strejf = pd.DataFrame(strejf_rows, columns=["dag", "side", "basis_i", "udfald",
                                                "R_brutto", "R_netto"])
    return handler, tael, strejf


def simuler_alle_varianter(df_1m: pd.DataFrame, bars_15m: pd.DataFrame) -> dict:
    """Alle 6 varianter, §3: buffer × BE. Nøgle er (buffer_navn, be_navn)."""
    ud = {}
    for buffer_navn, buffer in BUFFER_VARIANTER.items():
        zoner = sizing_ekte(k1.zoner_v2(bars_15m, buffer))
        for be_navn, be_r in BE_VARIANTER.items():
            handler, tael, strejf = handler_for_variant(df_1m, zoner, be_r)
            ud[(buffer_navn, be_navn)] = {"handler": handler, "tael": tael,
                                          "strejf": strejf, "zoner": zoner}
    return ud


# ---------------------------------------------------------------------------
# Nøgletal, §8 (uddrag — den fulde rapport skrives først i trin 2)
# ---------------------------------------------------------------------------

def noegletal_handler(res: dict) -> dict:
    """Hovedtallene for én variant: middel-R, udfaldsfordeling, strejf-diagnosen."""
    handler, tael, strejf, zoner = res["handler"], res["tael"], res["strejf"], res["zoner"]
    row = dict(tael)
    row["handler_n"] = len(handler)
    if len(handler):
        row["middel_R_brutto"] = float(handler["R_brutto"].mean())
        row["middel_R_netto"] = float(handler["R_netto"].mean())
        row["middel_R_netto_ci95_lo"], row["middel_R_netto_ci95_hi"] = \
            mean_ci_t(handler["R_netto"])
        vundet = int((handler["udfald"] == MAAL).sum())
        lo, hi = wilson_interval(vundet, len(handler))
        row["win_rate_pct_netto"] = 100 * vundet / len(handler)
        row["win_rate_ci95_lo_pct"], row["win_rate_ci95_hi_pct"] = 100 * lo, 100 * hi
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
                     "win_rate_ci95_hi_pct", "tidsexit_middel_R_netto",
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
    sig = zoner[zoner["signal"] & (zoner["kontrakter_ekte"] > 0)]
    for q in (10, 50, 90):
        row[f"risiko_pt_p{q}"] = k1._p(sig["risiko_pt_ekte"], q)
        row[f"kontrakter_p{q}"] = k1._p(sig["kontrakter_ekte"], q)
    row["omk_R_netto_p50"] = k1._p(sig["omk_R_netto_ekte"], 50)
    return row


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


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--regressionstjek", action="store_true",
                     help="v2 på NQ skal gengive b4_k1_optaelling_v2.csv præcist")
    grp.add_argument("--tidsmaaling", action="store_true",
                     help="ét gennemløb over MNQ, fremskrevet til 6 × 500 N1-gentagelser")
    args = ap.parse_args(argv)

    if args.regressionstjek:
        ens = regressionstjek()
        print("REGRESSIONSTJEK: " + ("OK — identisk med b4_k1_optaelling_v2.csv" if ens
                                     else "AFVIGER — trin A køres ikke"))
        if not ens:
            sys.exit(1)
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
