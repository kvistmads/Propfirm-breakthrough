"""B4 kandidat 6 — holdout-testen af "V2 · salg", overnight drift efter salgsdage.

Præregistreret i ``research/prereg/b4_k6_holdout.md``, som også er den frosne hypotese til
``data.holdout.load_holdout``. Strategien, nulmodellen N-nat og alle definitioner er
``research/b4_k6_overnight.py`` som i commit 583dfd9, importeret uændret. Kun serien
skifter. Her ligger alene det præregistreringen tilføjer: den samlede serie, H1, H2, rækken
i §5, E_f og diagnoserne i §7, kun for V2 · salg, side om side med in-sample.

    .venv/bin/python -m research.b4_k6_holdout --regressionstjek
    .venv/bin/python -m research.b4_k6_holdout --in-sample
    .venv/bin/python -m research.b4_k6_holdout --koer

``--regressionstjek`` er kandidat 1-5's tjek og kandidat 6's 902 nætter / $11,07.
``--in-sample`` kører samme vej på in-sample alene og må køres når som helst. ``--koer``
åbner NQ.v.0's holdout (én gang) og kræver ejerens godkendelse (§9, trin 2).

## Hvad der aldrig regnes på holdout-nætterne (§7, svar 4A)

Kun V2 · salg og dens N-nat. ``k6.handel`` kaldes kun med "V2". ``k6.analyse``,
``k6.diagnoser``, ``k6.lang_hele_natten``, ``k6.nnat_gentagelse`` og ``k6.forbered`` kaldes
ikke, fordi de regner V1, "alle nætter" eller long hele natten. ``k6.byg_grundlag`` finder
udførelsespunkterne for V1 og hele natten (tider, ingen priser), fordi udelukkelsen i
in-sample-kørslen bruger dem (læsning 3).

## Læsninger — valgt af Code, skrevet op før kørslen

Dem der kan flytte et resultat, eller hvor præregistreringen kan læses på to måder, er
mærket **[tvivl]**.

1. **Den samlede serie** er ``load_in_sample("NQ.v.0")`` efterfulgt af
   ``load_holdout`` med den frosne fil og "NQ.v.0", skåret ved ET-dag < 2026-10-01
   (``afskaer``).
   Nætterne er XNYS-dagene 2016-01-04 → 2026-09-30. ``k6.byg_grundlag`` køres én gang på
   den samlede serie, så forskelsjusteringen dækker begge dele, og salgsdagen for natten før
   2024-01-02 er 2023-12-29.
2. **Holdout-nætterne** er d med 2024-01-02 ≤ d ≤ 2026-09-30, in-sample-nætterne d ≤
   2023-12-29. Delingen sker med en maske på den samlede ``Grundlag`` (``V2 · salg``-masken
   og dagene), ikke ved at bygge to grundlag.
3. **Udelukkelsen** er ``k6``'s læsning 5 uændret: en nat udelukkes, hvis ét af de fire
   punkter (også V1's) er over 5 minutter forsinket. Det er kun bartider, ingen priser.
   [tvivl] §2 siger "mangler en bar ... udelukkes natten" for V2 alene; at følge modulet
   uændret er læst som det bindende, fordi §2 også siger, at koden ikke må ændres.
4. **N-nat** er ``k6.nnat_traek`` på ``k6.nnat_vaerdier(g, k6.nat_gitter(g), "V2")`` for den
   samlede serie, R = 500, seed som i kandidat 6. Trækket er en matrix med én række pr. nat
   i serien; de første rækker er de samme, uanset hvor mange nætter der følger (numpy's
   ``integers`` fylder rækkevis), så in-sample-udsnittet får præcis kandidat 6's træk for
   V2. Pr. gentagelse er nulværdien middel netto over udsnittets V2 · salg-nætter, ved samme
   omkostning som varianten. ``behov`` er V2 · salg-nætterne i udsnittet. [tvivl] Kandidat
   6 brugte ``behov = alle nætter der indgår``; det giver samme træk, men stopper kun ved
   nætter, der faktisk bruges.
5. **p_H1** = ``(1 + #{N-nattens middel netto ≥ variantens middel netto}) / 501``, énsidet,
   ved $3,10. Omkostningen går ud af sammenligningen, så p_H1 er den samme ved $2,85.
6. **H2** er bestået, når den nedre grænse i det tosidede 90%-t-interval over holdout-
   nætternes netto ved $3,10 er > 0. **E_f** er samme grænse for in-sample og holdout
   samlet, nat for nat (§5), ved $3,10 og ved $2,85.
7. **Rækken i §5:** 1 = H1 og H2; 2 = H1, ikke H2, middel netto > 0; 3 = H1, middel netto ≤
   0; 4 = alt andet. Middel netto er holdout ved $3,10.
8. **Nominelt** (§7) er ``Δpt × 2 − 3,10`` uden normering; **break-even** er
   ``k6``'s læsning 18 (middel brutto og CI95-nedre for brutto).
9. **Koncentration** (§7) [tvivl]: andelen af summen af netto ved $3,10, som den bedste nat
   og de ⌈5% × n⌉ bedste nætter står for (som kandidat 7). "Uden de 5 bedste" er middel
   netto over de øvrige nætter. "Uden den bedste kalendermåned" er middel netto uden
   nætterne i den måned (dag d's måned), hvis netto-sum er størst. Er summen ≤ 0, er
   andelene ikke meningsfulde og vises, men skal læses med det.
10. **Natfordelingen**: p1/p5/p50/p95/p99, værste og bedste nat og σ (ddof = 1) af netto ved
    $3,10. **Hit ratio** og **gevinst/tab** er ``k6.hit`` på netto ved $3,10.
11. **Største tab i vinduet** er ``k6.stoerste_tab`` ved $3,10.
12. **Datakvalitet** pr. udsnit: andel salgsnætter = salgsdage / nætter med kendt salgsdag
    blandt dem der indgår; udelukkede nætter med grund; forsinkede udførelser = V2 · salg-
    nætter med indgangs- eller udgangsbar 1-5 min forsinket; ruller i vinduet = V2 · salg-
    nætter med forskelligt ``instrument_id`` i ind- og udgang.
13. **Pr. år** (§7): middel brutto og netto med CI95 pr. kalenderår for dag d.
14. **Hovedtabellen** har "brutto_usd_nat" og "netto_usd_nat" ved $3,10. Netto ved $2,85 står
    i diagnoserne.
"""
from __future__ import annotations

import argparse
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data import holdout  # noqa: E402
from research import b4_k1_optaelling as k1  # noqa: E402
from research import b4_k6_overnight as k6  # noqa: E402
from research.stats import mean_ci_t  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "output"
FROSSET = ROOT / "research" / "prereg" / "b4_k6_holdout.md"
K6_COMMIT = "583dfd9"
K6_STI = "research/b4_k6_overnight.py"
COMMITTEDE = (Path(__file__).resolve(), ROOT / "tests" / "test_b4_k6_holdout.py", FROSSET,
              ROOT / "research" / "b4_k6_holdout_data.py", *k6.COMMITTEDE)

SYMBOL = k6.HOVED                          # NQ.v.0; intet andet symbol åbnes
V = ("V2", k6.SALG)
VINDUE = "V2"
NAT_FRA = "2016-01-01"
IN_SAMPLE_SLUT = pd.Timestamp("2023-12-29")
HOLDOUT_FRA = pd.Timestamp("2024-01-02")
HOLDOUT_TIL = "2026-10-01"                 # til, men ikke med: sidste nat 2026-09-30
OMK = 3.10                                 # svar 3A: afgør
OMK_DIAG = k6.OMK_USD                      # 2,85: rapporteres
NNAT_REPS = k6.NNAT_REPS                   # 500
ALFA_H1 = 0.05
ALFA_H2 = 0.10                             # tosidet 90% = énsidet 5%

TEKST = {1: "Bekræftet", 2: "Timen er bekræftet, nettogevinsten er ikke bevist",
         3: "Parkeres: timen er særlig, men betaler ikke omkostningen efter 2023",
         4: "Parkeres for godt: driften efter salgsdage holdt ikke efter 2023"}

# §9.3: kandidat 6's in-sample-tal for V2 · salg ved $2,85.
REGRESSION_V2_SALG = (902, 11.07, -0.95, 23.09)


# ---------------------------------------------------------------------------
# Serien
# ---------------------------------------------------------------------------

def afskaer(df: pd.DataFrame, til: str = HOLDOUT_TIL) -> pd.DataFrame:
    """Læsning 1: kun barer hvis ET-dag ligger før ``til``."""
    return df[k1._et_dag(df.index) < pd.Timestamp(til)]


def nat_dage(til: str = HOLDOUT_TIL) -> pd.DatetimeIndex:
    return k1.rth_dage(NAT_FRA, til)


def holdout_serie(symbol: str = SYMBOL) -> pd.DataFrame:
    """Holdout åbnes kun her, gennem ``load_holdout`` med den frosne hypotese."""
    if symbol != SYMBOL:
        raise PermissionError(f"{symbol}'s holdout åbnes ikke af kandidat 6")
    return afskaer(holdout.load_holdout(FROSSET, symbol=symbol))


def samlet(df_ins: pd.DataFrame, df_hold: pd.DataFrame) -> pd.DataFrame:
    df = pd.concat([df_ins, afskaer(df_hold)]).sort_index()
    if df.index.has_duplicates:
        raise ValueError("in-sample og holdout overlapper")
    return df


def k6_uaendret() -> bool:
    """Kandidat 6's modul er det samme som i commit 583dfd9."""
    r = subprocess.run(["git", "--no-optional-locks", "-C", str(ROOT), "diff", "--quiet",
                        K6_COMMIT, "--", K6_STI], capture_output=True)
    return r.returncode == 0


def udsnit_masker(g: k6.Grundlag) -> dict:
    """Læsning 2: dagmasker for in-sample og holdout på den samlede serie."""
    return {"in_sample": np.asarray(g.dage <= IN_SAMPLE_SLUT),
            "holdout": np.asarray(g.dage >= HOLDOUT_FRA)}


# ---------------------------------------------------------------------------
# H1, H2, E_f og §5
# ---------------------------------------------------------------------------

def p_h1(middel: float, null: np.ndarray) -> float:
    null = np.asarray(null, dtype=float)
    return (1 + int((null >= middel).sum())) / (1 + len(null))


def nedre_90(x) -> float:
    """Den nedre grænse i det tosidede 90%-t-interval: énsidet 5%."""
    return mean_ci_t(np.asarray(x, dtype=float), alpha=ALFA_H2)[0]


def raekke(h1: bool, h2: bool, middel: float) -> int:
    if h1 and h2:
        return 1
    if h1 and middel > 0:
        return 2
    if h1:
        return 3
    return 4


def koncentration(netto: np.ndarray, dage: pd.DatetimeIndex) -> dict:
    """Læsning 9."""
    netto = np.asarray(netto, float)
    x = np.sort(netto)[::-1]
    tot = float(x.sum())
    k = max(1, math.ceil(0.05 * len(x)))
    mdr = pd.Series(netto, index=pd.DatetimeIndex(dage).to_period("M"))
    bedste_md = mdr.groupby(level=0).sum().idxmax() if len(netto) else None
    uden_md = netto[np.asarray(mdr.index != bedste_md)] if bedste_md is not None else netto
    return {"sum": tot, "bedste_nat_andel": float(x[0] / tot) if tot else float("nan"),
            "bedste_5pct_n": k,
            "bedste_5pct_andel": float(x[:k].sum() / tot) if tot else float("nan"),
            "uden_5_bedste": float(x[5:].mean()) if len(x) > 5 else float("nan"),
            "bedste_maaned": str(bedste_md),
            "uden_bedste_maaned": float(uden_md.mean()) if len(uden_md) else float("nan")}


# ---------------------------------------------------------------------------
# V2 · salg på ét udsnit
# ---------------------------------------------------------------------------

def _seg(x, s=None) -> dict:
    x = np.asarray(x, float)
    s = np.ones(len(x), bool) if s is None else np.asarray(s, bool)
    lo, hi = mean_ci_t(x[s]) if s.sum() >= 2 else (float("nan"), float("nan"))
    return {"n": int(s.sum()), "middel": float(x[s].mean()) if s.any() else float("nan"),
            "lo": lo, "hi": hi}


def nnat_null(g: k6.Grundlag, nv: k6.NNatVaerdier, m: np.ndarray, omk: float = OMK,
              n_reps: int = NNAT_REPS) -> np.ndarray:
    """Læsning 4: N-nattens middel netto over nætterne i ``m`` pr. gentagelse."""
    rk = np.arange(len(g.dage))
    ud = np.empty(n_reps)
    for rep in range(n_reps):
        valg = k6.nnat_traek(nv, rep, behov=m)
        ud[rep] = float((nv.brutto[rk, np.maximum(valg, 0)][m] - omk).mean())
    return ud


def kvalitet(g: k6.Grundlag, dag_m: np.ndarray, m: np.ndarray) -> dict:
    """Læsning 12. ``dag_m`` er udsnittets nætter, ``m`` dets V2 · salg-nætter."""
    ind_i, f_ind = g.pkt[f"{VINDUE}_ind"]
    ud_i, f_ud = g.pkt[f"{VINDUE}_ud"]
    med = g.med & dag_m
    kendt = med & ~np.isnan(g.salg)
    return {"naetter_i_alt_n": int(dag_m.sum()), "naetter_med_n": int(med.sum()),
            "salgsdage_n": int((med & (g.salg == 1)).sum()), "salg_kendt_n": int(kendt.sum()),
            "salg_ukendt_n": int((med & np.isnan(g.salg)).sum()),
            "salg_andel_pct": 100.0 * (med & (g.salg == 1)).sum() / kendt.sum()
            if kendt.any() else float("nan"),
            "udelukket": [f"{d.date()} ({gr})" for d, gr, x in zip(g.dage, g.grund, dag_m)
                          if x and gr],
            "forsinket_n": int((m & ((f_ind > 0) | (f_ud > 0))).sum()),
            "forsinket_ind_n": int((m & (f_ind > 0)).sum()),
            "forsinket_ud_n": int((m & (f_ud > 0)).sum()),
            "ruller_i_vinduet_n": int((m & (g.iid[ind_i] != g.iid[ud_i])).sum())}


def serie_resultat(g: k6.Grundlag, h: dict, nv: k6.NNatVaerdier, dag_m: np.ndarray,
                   n_reps: int = NNAT_REPS) -> dict:
    """V2 · salg på nætterne i ``dag_m``: hovedtallene, N-nat og §7's diagnoser."""
    m = g.maske(V) & dag_m
    b = h["brutto_usd"][m]
    netto, netto285 = b - OMK, b - OMK_DIAG
    nom = h["pt"][m] * k6.MNQ_USD_PR_POINT - OMK
    d = g.dage[m]
    null = nnat_null(g, nv, m, OMK, n_reps)
    lo90, hi90 = mean_ci_t(netto, alpha=ALFA_H2)
    lo95, hi95 = mean_ci_t(netto)
    hn, fn = k6.hit(netto)
    tab = k6.stoerste_tab(g, h, m, OMK)
    aar = []
    for a in sorted(set(d.year.tolist())):
        s = d.year == a
        aar.append({"aar": a, "n": int(s.sum()), "brutto": float(b[s].mean()),
                    **{f"netto_{k}": v for k, v in _seg(netto, s).items() if k != "n"}})
    return {
        "naetter_n": int(m.sum()), "netto": netto, "netto_285": netto285, "dage": d,
        "null": null, "brutto_usd_nat": float(b.mean()), "netto_usd_nat": float(netto.mean()),
        "ci90_lo": lo90, "ci90_hi": hi90, "ci95_lo": lo95, "ci95_hi": hi95,
        **{f"N_nat_p{q}": float(np.percentile(null, q)) for q in (5, 50, 95)},
        "p_H1": p_h1(float(netto.mean()), null),
        "netto_285_seg": _seg(netto285), "nominelt": _seg(nom),
        "breakeven_middel": float(b.mean()), "breakeven_CI": mean_ci_t(b)[0],
        "aar": aar, "koncentration": koncentration(netto, d),
        "hit_pct": hn, "gevinst_tab": fn,
        **{f"netto_p{q}": float(np.percentile(netto, q)) for q in (1, 5, 50, 95, 99)},
        "netto_vaerst": float(netto.min()), "netto_bedst": float(netto.max()),
        "sigma": float(netto.std(ddof=1)),
        **{f"tab_i_vindue_p{q}": float(np.percentile(tab, q)) for q in (1, 5, 50)},
        "tab_i_vindue_vaerst": float(tab.min()),
        "kvalitet": kvalitet(g, dag_m, m),
    }


def afgoerelse(hold: dict, ins: dict) -> dict:
    """§4-§5: H1 og H2 på holdout, rækken og E_f på begge udsnit samlet."""
    h1 = hold["p_H1"] <= ALFA_H1
    h2 = hold["ci90_lo"] > 0
    nr = raekke(h1, h2, hold["netto_usd_nat"])
    alle = np.concatenate([ins["netto"], hold["netto"]])
    alle285 = np.concatenate([ins["netto_285"], hold["netto_285"]])
    e_f = nedre_90(alle)
    return {"H1": h1, "H2": h2, "raekke": nr, "tekst": TEKST[nr], "E_f": e_f,
            "E_f_over_0": bool(e_f > 0), "E_f_285": nedre_90(alle285),
            "samlet_middel": float(alle.mean()), "samlet_naetter_n": len(alle)}


def analyse(df: pd.DataFrame, dage: pd.DatetimeIndex, n_reps: int = NNAT_REPS) -> dict:
    """Grundlag og N-nat på den samlede serie, så in-sample og holdout hver for sig."""
    g = k6.byg_grundlag(df, dage, SYMBOL)
    h = k6.handel(g, VINDUE, OMK)
    nv = k6.nnat_vaerdier(g, k6.nat_gitter(g), VINDUE)
    um = udsnit_masker(g)
    ins = serie_resultat(g, h, nv, um["in_sample"], n_reps)
    hold = serie_resultat(g, h, nv, um["holdout"], n_reps)
    return {"holdout": hold, "in_sample": ins, "afgoerelse": afgoerelse(hold, ins),
            "n_reps": n_reps}


# ---------------------------------------------------------------------------
# Rapporten, §8
# ---------------------------------------------------------------------------

_t = k6.k2._t


def _ci(lo, hi, nd: int = 2) -> str:
    return f"[{_t(lo, nd)}; {_t(hi, nd)}]"


def _seg_txt(s: dict) -> str:
    return f"{_t(s['middel'])} {_ci(s['lo'], s['hi'])} (n {s['n']})"


def skriv_md(res: dict, meta: dict) -> str:
    H, I, A = res["holdout"], res["in_sample"], res["afgoerelse"]
    ja = lambda b: "**bestået**" if b else "**ikke bestået**"
    rk = lambda navn, r: (
        f"| {navn} | {_t(r['naetter_n'], 0)} | {_t(r['brutto_usd_nat'])} | "
        f"**{_t(r['netto_usd_nat'])}** | {_ci(r['ci90_lo'], r['ci90_hi'])} | "
        f"{_ci(r['ci95_lo'], r['ci95_hi'])} | "
        f"{_t(r['N_nat_p5'])}/{_t(r['N_nat_p50'])}/{_t(r['N_nat_p95'])} | "
        f"**{_t(r['p_H1'], 3)}** |")
    dele = [
        "# B4 kandidat 6 — holdout-testen af V2 · salg: resultat", "",
        f"**Kørt:** {meta['koert_utc']} UTC fra `{meta['head'][:12]}`, frosset hypotese "
        f"`research/prereg/b4_k6_holdout.md` (commit `{meta.get('frosset', '—')[:12]}`). "
        f"Kandidat 6's modul uændret fra {K6_COMMIT}. R = {res['n_reps']}. {SYMBOL}, MNQ-"
        "økonomi, $3,10 pr. round trip, dagens niveau. Kun V2 · salg og dens N-nat (§7).", "",
        "## Hovedtabel", "",
        "| serie | naetter_n | brutto_usd_nat | netto_usd_nat | CI90_netto | CI95_netto | "
        "N_nat_p5/p50/p95 | p_H1 |", "|" + "---|" * 8,
        rk("holdout 2024-01-02 → 2026-09-30", H), rk("in-sample 2016-01-04 → 2023-12-29", I),
        "",
        f"- **H1** (p_H1 ≤ 0,05 på holdout): {ja(A['H1'])}, p_H1 = {_t(H['p_H1'], 3)}.",
        f"- **H2** (CI90-nedre > 0 på holdout): {ja(A['H2'])}, CI90-nedre = "
        f"{_t(H['ci90_lo'])}.",
        f"- **§5 anvendt mekanisk:** række {A['raekke']}: {A['tekst']}.",
        f"- **E_f** (énsidet 95%-nedre, in-sample og holdout samlet, n "
        f"{A['samlet_naetter_n']}): {_t(A['E_f'])} ved $3,10 (middel "
        f"{_t(A['samlet_middel'])}), {_t(A['E_f_285'])} ved $2,85. E_f > 0: "
        f"{'ja' if A['E_f_over_0'] else 'nej'}.",
        "", "## Diagnoser (§7, afgør intet)", "",
        "| diagnose | holdout | in-sample |", "|---|---|---|"]
    rows = [
        ("netto ved $2,85", lambda r: _seg_txt(r["netto_285_seg"])),
        ("nominelt ved $3,10", lambda r: _seg_txt(r["nominelt"])),
        ("break-even pr. round trip, middel / CI-nedre",
         lambda r: f"{_t(r['breakeven_middel'])} / {_t(r['breakeven_CI'])}"),
        ("bedste nats andel af netto i alt",
         lambda r: f"{_t(100 * r['koncentration']['bedste_nat_andel'], 1)}%"),
        ("de 5% bedste nætters andel",
         lambda r: f"{_t(100 * r['koncentration']['bedste_5pct_andel'], 1)}% "
                   f"(n {r['koncentration']['bedste_5pct_n']})"),
        ("netto uden de 5 bedste nætter", lambda r: _t(r["koncentration"]["uden_5_bedste"])),
        ("netto uden den bedste kalendermåned",
         lambda r: f"{_t(r['koncentration']['uden_bedste_maaned'])} "
                   f"(uden {r['koncentration']['bedste_maaned']})"),
        ("hit ratio / gevinst-tab", lambda r: f"{_t(r['hit_pct'], 1)}% / "
                                              f"{_t(r['gevinst_tab'], 2)}"),
        ("netto p1/p5/p50/p95/p99", lambda r: "/".join(_t(r[f"netto_p{q}"], 0)
                                                     for q in (1, 5, 50, 95, 99))),
        ("værste / bedste nat", lambda r: f"{_t(r['netto_vaerst'], 0)} / "
                                          f"{_t(r['netto_bedst'], 0)}"),
        ("σ pr. nat", lambda r: _t(r["sigma"], 0)),
        ("største tab i vinduet p1/p5/p50/værst",
         lambda r: "/".join(_t(r[f"tab_i_vindue_{q}"], 0)
                            for q in ("p1", "p5", "p50", "vaerst"))),
        ("andel salgsnætter", lambda r: f"{_t(r['kvalitet']['salg_andel_pct'], 1)}% "
                                        f"({r['kvalitet']['salgsdage_n']} / "
                                        f"{r['kvalitet']['salg_kendt_n']})"),
        ("nætter / udelukkede", lambda r: f"{r['kvalitet']['naetter_i_alt_n']} / "
                                          f"{len(r['kvalitet']['udelukket'])}"),
        ("forsinkede udførelser (ind / ud)",
         lambda r: f"{r['kvalitet']['forsinket_n']} ({r['kvalitet']['forsinket_ind_n']} / "
                   f"{r['kvalitet']['forsinket_ud_n']})"),
        ("ruller i vinduet", lambda r: str(r["kvalitet"]["ruller_i_vinduet_n"])),
    ]
    for navn, f in rows:
        dele.append(f"| {navn} | {f(H)} | {f(I)} |")
    dele += ["", "Udelukkede holdout-nætter: " + (", ".join(H["kvalitet"]["udelukket"]) or
                                                  "ingen") + ".", "",
             "| år | nætter | brutto $/nat | netto $/nat [CI95] |", "|---|---|---|---|"]
    for navn, r in (("holdout", H), ("in-sample", I)):
        for a in r["aar"]:
            dele.append(f"| {a['aar']} ({navn}) | {a['n']} | {_t(a['brutto'])} | "
                        f"{_t(a['netto_middel'])} {_ci(a['netto_lo'], a['netto_hi'])} |")
    return "\n".join(dele) + "\n"


def lang_tabel(res: dict) -> pd.DataFrame:
    rows = []
    for navn in ("holdout", "in_sample"):
        r = res[navn]
        flad = {k: v for k, v in r.items() if isinstance(v, (int, float, np.floating))}
        rows.append({"serie": navn, "tabel": "hoved", **flad})
        for k in ("netto_285_seg", "nominelt", "koncentration", "kvalitet"):
            d = {kk: (len(x) if isinstance(x, list) else x) for kk, x in r[k].items()}
            rows.append({"serie": navn, "tabel": k, **d})
        rows += [{"serie": navn, "tabel": "aar", **a} for a in r["aar"]]
    rows.append({"serie": "samlet", "tabel": "afgoerelse", **res["afgoerelse"]})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Kørslen
# ---------------------------------------------------------------------------

def in_sample(n_reps: int = NNAT_REPS) -> dict:
    """Samme vej på in-sample alene: grundlag på in-sample-serien og -nætterne."""
    g = k6.byg_grundlag(k6.serie(SYMBOL), k6.xnys_dage(SYMBOL), SYMBOL)
    h = k6.handel(g, VINDUE, OMK)
    nv = k6.nnat_vaerdier(g, k6.nat_gitter(g), VINDUE)
    return {"g": g, **serie_resultat(g, h, nv, np.ones(len(g.dage), bool), n_reps)}


def regression_k6() -> dict:
    """§9.4: kandidat 6's V2 · salg på in-sample ved $2,85 med k6's egne funktioner."""
    g = k6.byg_grundlag(k6.serie(SYMBOL), k6.xnys_dage(SYMBOL), SYMBOL)
    t = k6.variant_tal(g, V, k6.handel(g, VINDUE))
    tal = (t["naetter_n"], t["middel_netto_usd"], t["ci95_lo"], t["ci95_hi"])
    ok = (tal[0] == REGRESSION_V2_SALG[0]
          and all(round(a, 2) == b for a, b in zip(tal[1:], REGRESSION_V2_SALG[1:])))
    return {"V2_salg": tal, "ok": ok}


def koer(n_reps: int = NNAT_REPS) -> dict:
    """§9, trin 2: kandidat 6's modul uændret, regressionstjekket OK, så én åbning."""
    if not k6_uaendret():
        raise RuntimeError(f"{K6_STI} afviger fra {K6_COMMIT}; holdout åbnes ikke")
    reg = regression_k6()
    if not reg["ok"]:
        raise RuntimeError(f"regressionstjekket afveg; holdout åbnes ikke: {reg}")
    df = samlet(k6.serie(SYMBOL), holdout_serie(SYMBOL))
    return analyse(df, nat_dage(), n_reps)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--regressionstjek", action="store_true",
                     help="§9.4: kandidat 1-5's tjek og kandidat 6's V2 · salg")
    grp.add_argument("--in-sample", action="store_true",
                     help="samme vej på in-sample; åbner ikke holdout")
    grp.add_argument("--koer", action="store_true",
                     help="§9 trin 2: åbner holdout én gang. Kræver ejerens godkendelse")
    args = ap.parse_args(argv)
    meta = {"koert_utc": pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M"),
            "head": k6.k4._git("rev-parse", "HEAD").stdout.strip()}
    if args.regressionstjek:
        r = regression_k6()
        n, m, lo, hi = r["V2_salg"]
        print(f"Kandidat 6, V2 · salg ved $2,85: naetter {n}, netto {m:.2f}, CI95 "
              f"[{lo:.2f}; {hi:.2f}]: {'OK' if r['ok'] else 'AFVIGER'}")
        if not r["ok"]:
            sys.exit(1)
        return
    if args.in_sample:
        r = in_sample()
        print(f"in-sample V2 · salg ved $3,10: naetter {r['naetter_n']}, netto "
              f"{r['netto_usd_nat']:.2f} $/nat, CI95 [{r['ci95_lo']:.2f}; {r['ci95_hi']:.2f}], "
              f"p_H1 {r['p_H1']:.4f}")
        return
    commits = k1.committede(COMMITTEDE)
    meta["frosset"] = commits[k1._rel(FROSSET)]
    res = koer()
    md = skriv_md(res, meta)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "b4_k6_holdout.md").write_text(md, encoding="utf-8")
    lang_tabel(res).to_csv(OUT / "b4_k6_holdout.csv", index=False)
    print(md)


if __name__ == "__main__":
    main()
