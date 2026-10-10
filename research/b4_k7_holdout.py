"""B4 kandidat 7 — holdout-testen af "T · tærskel".

Præregistreret i ``research/prereg/b4_k7_holdout.md``, som også er den frosne hypotese til
``data.holdout.load_holdout``. Strategien, nulmodellen og alle definitioner er
``research/b4_k7_rebalancering.py`` som i commit 4c5cc8e, importeret uændret. Kun serien
skifter. Her ligger alene det præregistreringen tilføjer: den samlede serie, H1, H2,
rækken i §5, E_f og diagnoserne i §7 side om side med in-sample.

    .venv/bin/python -m research.b4_k7_holdout --uro
    .venv/bin/python -m research.b4_k7_holdout --in-sample
    .venv/bin/python -m research.b4_k7_holdout --koer

``--uro`` regner grænsen for urolige måneder på in-sample alene (ingen P&L). ``--in-sample``
kører samme vej på in-sample og må køres når som helst. ``--koer`` åbner holdout (én gang,
ES.v.0 og ZN.v.0) og kræver ejerens godkendelse (§9, trin 2). NQ.v.0's holdout åbnes aldrig
herfra: det er kandidat 6's uåbnede holdout.

## Læsninger

1. **Den samlede serie** er in-sample (``load_in_sample``) efterfulgt af holdout
   (``load_holdout`` med den frosne fil), skåret ved ET-dag < 2026-10-01 (``afskaer``).
   Signaldagene er XNYS-dagene 2016-01-04 → 2026-09-30. ``k7.byg_signal`` og
   ``k7.byg_handel`` køres én gang på den samlede serie, så porteføljerne kører videre fra
   in-sample uden ny start, og forskelsjusteringen dækker begge dele.
2. **Holdout-dagene** er handelsdagene d med 2024-01-02 ≤ d ≤ 2026-09-30, in-sample-dagene
   d ≤ 2023-12-29. ``udsnit`` vælger dagene ud af den samlede ``k7.Handel``; alle per-dag-felter
   skæres, resten deles. Signaldagen for 2024-01-02 er 2023-12-29.
3. **N-retning** er ``k7.nret_gentagelse`` med R = 500 på udsnittet. Fortegnet trækkes pr.
   handelsdag i udsnittet (modulets læsning 10), så in-sample-udsnittet får præcis
   kandidat 7's nulfordeling.
4. **p_H1** = ``(1 + #{nulmodellens middel ≥ T's middel}) / 501``, énsidet, uden korrektion.
5. **H2** er bestået, når den nedre grænse i det tosidede 90%-t-interval over de aktive dage
   er > 0. **E_f** er samme grænse for in-sample og holdout samlet, dag for dag.
6. **Rækken i §5:** 1 = H1 og H2; 2 = H1, ikke H2, middel netto > 0; 3 = H1, middel netto ≤
   0; 4 = alt andet.
7. **Urolige måneder** (§7) [tvivl]: sd (ddof = 1) af ``R^ES_t`` over signaldagene t i
   kalendermåneden, for hver in-sample-måned 2016-01 → 2023-12 (januar 2016 uden første dag,
   som intet afkast har). Grænsen er ``np.percentile(·, 90)`` over de 96 måneder. En måned
   er urolig, hvis dens sd er over grænsen. En handelsdag d udelades i diagnosen, hvis d's
   kalendermåned er urolig. Holdout-månederne vurderes mod samme in-sample-grænse.
8. **Bedste dages andel** (§7): andelen af summen af netto over de aktive dage, som den
   bedste dag og de ⌈5% × n⌉ bedste dage står for. "Uden de 5 bedste dage" er middel netto
   over de øvrige dage.
9. **Publiceringen** deles ved d < 2025-03-01 og d ≥ 2025-03-01.
10. **Resten af §7** er ``k7.diagnoser`` og ``k7.reversal_diagnose`` uændret på udsnittet;
    kun T og T med hele MES rapporteres.
"""
from __future__ import annotations

import argparse
import dataclasses
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data import holdout  # noqa: E402
from research import b4_k1_optaelling as k1  # noqa: E402
from research import b4_k7_rebalancering as k7  # noqa: E402
from research.stats import mean_ci_t  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "output"
FROSSET = ROOT / "research" / "prereg" / "b4_k7_holdout.md"
K7_COMMIT = "4c5cc8e"
K7_STI = "research/b4_k7_rebalancering.py"
COMMITTEDE = (Path(__file__).resolve(), ROOT / "tests" / "test_b4_k7_holdout.py", FROSSET,
              ROOT / "research" / "b4_k7_holdout_data.py", *k7.COMMITTEDE)

SYMBOLER = (k7.ES, k7.ZN)                 # NQ.v.0 åbnes ikke
SIGNAL_FRA = "2016-01-01"
IN_SAMPLE_SLUT = pd.Timestamp("2023-12-29")
HOLDOUT_FRA = pd.Timestamp("2024-01-02")
HOLDOUT_TIL = "2026-10-01"                # til, men ikke med: sidste dag 2026-09-30
PUBLICERET = pd.Timestamp("2025-03-01")
NRET_REPS = k7.NRET_REPS                  # 500
ALFA_H1 = 0.05
ALFA_H2 = 0.10                            # tosidet 90% = énsidet 5%
URO_KVANTIL = 90

TEKST = {1: "Bekræftet", 2: "Retningen er bekræftet, nettogevinsten er ikke bevist",
         3: "Parkeres: retningen virker stadig, men betaler ikke omkostningen efter 2023",
         4: "Parkeres: T holdt ikke uden for artiklens prøve"}

# §9.3 og §9.5: kandidat 7's in-sample-tal.
REGRESSION_T = (1949, 16.42, 3.43, 29.42, 0.006)
REGRESSION_K = (556, 9.40)


# ---------------------------------------------------------------------------
# Serierne
# ---------------------------------------------------------------------------

def afskaer(df: pd.DataFrame, til: str = HOLDOUT_TIL) -> pd.DataFrame:
    """Læsning 1: kun barer hvis ET-dag ligger før ``til``."""
    return df[k1._et_dag(df.index) < pd.Timestamp(til)]


def signal_dage(til: str = HOLDOUT_TIL) -> pd.DatetimeIndex:
    return k1.rth_dage(SIGNAL_FRA, til)


def holdout_serie(symbol: str) -> pd.DataFrame:
    """Holdout åbnes kun her, gennem ``load_holdout`` med den frosne hypotese."""
    if symbol not in SYMBOLER:
        raise PermissionError(f"{symbol}'s holdout åbnes ikke af kandidat 7")
    return afskaer(holdout.load_holdout(FROSSET, symbol=symbol))


def samlet(df_ins: pd.DataFrame, df_hold: pd.DataFrame) -> pd.DataFrame:
    df = pd.concat([df_ins, afskaer(df_hold)]).sort_index()
    if df.index.has_duplicates:
        raise ValueError("in-sample og holdout overlapper")
    return df


def k7_uaendret() -> bool:
    """Kandidat 7's modul er det samme som i commit 4c5cc8e."""
    r = subprocess.run(["git", "--no-optional-locks", "-C", str(ROOT), "diff", "--quiet",
                        K7_COMMIT, "--", K7_STI], capture_output=True)
    return r.returncode == 0


_PR_DAG = ("t_pos", "ind", "f_ind", "ud", "praecis", "f_ud", "midt", "med", "grund")


def udsnit(h: k7.Handel, maske: np.ndarray) -> k7.Handel:
    """Læsning 2: handelsdagene i ``maske``; per-dag-felterne skæres, resten deles."""
    m = np.asarray(maske, bool)
    return dataclasses.replace(h, dage=h.dage[m], info=dict(h.info),
                               **{f: getattr(h, f)[m] for f in _PR_DAG})


def del_op(h: k7.Handel) -> tuple[k7.Handel, k7.Handel]:
    """(in-sample, holdout) ud af den samlede handel."""
    return udsnit(h, h.dage <= IN_SAMPLE_SLUT), udsnit(h, h.dage >= HOLDOUT_FRA)


# ---------------------------------------------------------------------------
# Urolige måneder, §7 og §9.4 — uden P&L
# ---------------------------------------------------------------------------

def maaneds_sd(R: np.ndarray, dage: pd.DatetimeIndex) -> pd.Series:
    """Læsning 7: sd (ddof = 1) af R pr. kalendermåned, nan-dage udeladt."""
    s = pd.Series(np.asarray(R, float), index=pd.DatetimeIndex(dage)).dropna()
    return s.groupby(s.index.to_period("M")).std(ddof=1)


def uro_graense(R_ins: np.ndarray, dage_ins: pd.DatetimeIndex) -> dict:
    sd = maaneds_sd(R_ins, dage_ins)
    g = float(np.percentile(sd.to_numpy(), URO_KVANTIL))
    return {"graense": g, "maaneder_n": len(sd), "sd": sd,
            "urolige": [str(p) for p in sd.index[sd > g]]}


def urolige_dage(dage: pd.DatetimeIndex, R: np.ndarray, sig_dage: pd.DatetimeIndex,
                 graense: float) -> np.ndarray:
    """True for handelsdage d, hvis kalendermåned er urolig mod in-sample-grænsen."""
    sd = maaneds_sd(R, sig_dage)
    urolig = set(sd.index[sd > graense])
    return np.array([p in urolig for p in pd.DatetimeIndex(dage).to_period("M")], bool)


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


def koncentration(netto: np.ndarray) -> dict:
    """Læsning 8."""
    x = np.sort(np.asarray(netto, float))[::-1]
    tot = float(x.sum())
    k = max(1, math.ceil(0.05 * len(x)))
    return {"sum": tot, "bedste_dag_andel": float(x[0] / tot) if tot else float("nan"),
            "bedste_5pct_n": k, "bedste_5pct_andel": float(x[:k].sum() / tot) if tot
            else float("nan"),
            "uden_5_bedste": float(x[5:].mean()) if len(x) > 5 else float("nan")}


def serie_resultat(h: k7.Handel, sig: k7.Signal, uro: float | None = None,
                   n_reps: int = NRET_REPS) -> dict:
    """T på ét udsnit: tallene, nulmodellen og diagnoserne."""
    ws = k7.positioner(sig)
    wT = ws[k7.T_VAR]
    t = k7.variant_tal(h, wT)
    p = t["_p"]
    m = p["aktiv"]
    netto = p["netto"][m]
    null = np.array([k7.nret_gentagelse(h, {k7.T_VAR: wT}, r)[k7.T_VAR]
                     for r in range(n_reps)])
    lo90, hi90 = mean_ci_t(netto, alpha=ALFA_H2)
    diag = k7.diagnoser(h, sig, ws, {k7.T_VAR: t})
    d = h.dage[m]
    aar = []
    for a in sorted(set(d.year.tolist())):
        s = (d.year == a)
        lo, hi = mean_ci_t(netto[s]) if s.sum() >= 2 else (float("nan"), float("nan"))
        aar.append({"aar": a, "n": int(s.sum()), "brutto": float(p["brutto"][m][s].mean()),
                    "netto": float(netto[s].mean()), "lo": lo, "hi": hi})
    ud = {"h": h, "netto": netto, "dage": d, "null": null,
          "aktive_dage_n": t["aktive_dage_n"], "andel_long": t["andel_long"],
          "andel_short": t["andel_short"],
          "brutto_usd_dag": t["middel_brutto_usd"], "netto_usd_dag": t["middel_netto_usd"],
          "ci90_lo": lo90, "ci90_hi": hi90, "ci95_lo": t["ci95_lo"], "ci95_hi": t["ci95_hi"],
          **{f"N_retning_p{q}": float(np.percentile(null, q)) for q in (5, 50, 95)},
          "p_H1": p_h1(t["middel_netto_usd"], null),
          "diag": diag["variant"][k7.T_VAR], "diag_hel": diag["variant"]["T_hel"],
          "lang": diag["lang"], "aar": aar, "koncentration": koncentration(netto),
          "reversal": k7.reversal_diagnose(h, sig),
          "kvalitet": kvalitet(h, sig)}
    for navn, s in (("foer_publ", d < PUBLICERET), ("efter_publ", d >= PUBLICERET)):
        ud[navn] = _seg(netto, s)
    if uro is not None:
        u = urolige_dage(d, sig.R_es, sig.dage, uro)
        ud["uden_uro"] = _seg(netto, ~u)
        ud["kun_uro"] = _seg(netto, u)
    return ud


def _seg(x, s) -> dict:
    s = np.asarray(s, bool)
    lo, hi = mean_ci_t(x[s]) if s.sum() >= 2 else (float("nan"), float("nan"))
    return {"n": int(s.sum()), "netto": float(x[s].mean()) if s.any() else float("nan"),
            "lo": lo, "hi": hi}


def kvalitet(h: k7.Handel, sig: k7.Signal) -> dict:
    """Udelukkede dage, forsinkelser, manglende signalbarer og ruller i vinduet i udsnittet."""
    t_dage = set(sig.dage[h.t_pos].strftime("%Y-%m-%d"))
    ud = {"handelsdage_n": h.n, "udelukket": [f"{d.date()} ({g})" for d, g in
                                             zip(h.dage, h.grund) if g],
          "indgang_forsinket_1_5_n": int((h.med & (h.f_ind > 0)).sum()),
          "udgang_tidligere_bar_n": int((h.med & ~h.praecis).sum()),
          "ruller_i_vinduet_n": int((h.med & (h.iid[h.ind]
                                              != h.iid[np.maximum(h.ud, h.ind)])).sum())}
    for navn in ("ES", "ZN"):
        dd = sig.info.get(f"signalbar_mangler_{navn}_dage", [])
        ud[f"signalbar_mangler_{navn}"] = [x for x in dd if x in t_dage]
    return ud


def afgoerelse(hold: dict, ins: dict) -> dict:
    """§4-§5: H1 og H2 på holdout, rækken og E_f på begge serier samlet."""
    h1 = hold["p_H1"] <= ALFA_H1
    h2 = hold["ci90_lo"] > 0
    nr = raekke(h1, h2, hold["netto_usd_dag"])
    alle = np.concatenate([ins["netto"], hold["netto"]])
    dage = ins["dage"].append(hold["dage"])
    uden_m20 = ~((dage >= k7.MARTS_2020[0]) & (dage < k7.MARTS_2020[1]))
    e_f = nedre_90(alle)
    return {"H1": h1, "H2": h2, "raekke": nr, "tekst": TEKST[nr], "E_f": e_f,
            "E_f_over_0": bool(e_f > 0), "samlet_middel": float(alle.mean()),
            "samlet_dage_n": len(alle), "E_f_uden_marts_2020": nedre_90(alle[uden_m20])}


def analyse(df_es: pd.DataFrame, df_zn: pd.DataFrame, sig_dage: pd.DatetimeIndex,
            uro: float, n_reps: int = NRET_REPS) -> dict:
    """Signal og handel på den samlede serie, så in-sample og holdout hver for sig."""
    sig = k7.byg_signal(df_es, df_zn, sig_dage)
    h_ins, h_hold = del_op(k7.byg_handel(df_es, sig_dage, k7.ES))
    ins = serie_resultat(h_ins, sig, uro, n_reps)
    hold = serie_resultat(h_hold, sig, uro, n_reps)
    return {"holdout": hold, "in_sample": ins, "afgoerelse": afgoerelse(hold, ins),
            "n_reps": n_reps, "uro": uro}


# ---------------------------------------------------------------------------
# Rapporten, §8
# ---------------------------------------------------------------------------

_t = k7._t


def _ci(lo, hi, nd: int = 2) -> str:
    return f"[{_t(lo, nd)}; {_t(hi, nd)}]"


def _seg_txt(s: dict) -> str:
    return f"{_t(s['netto'])} {_ci(s['lo'], s['hi'])} (n {s['n']})"


def skriv_md(res: dict, meta: dict) -> str:
    H, I, A = res["holdout"], res["in_sample"], res["afgoerelse"]
    ja = lambda b: "**bestået**" if b else "**ikke bestået**"
    rk = lambda navn, r: (
        f"| {navn} | {_t(r['aktive_dage_n'], 0)} | {_t(100 * r['andel_long'], 0)}% | "
        f"{_t(r['brutto_usd_dag'])} | **{_t(r['netto_usd_dag'])}** | "
        f"{_ci(r['ci90_lo'], r['ci90_hi'])} | {_ci(r['ci95_lo'], r['ci95_hi'])} | "
        f"{_t(r['N_retning_p5'])}/{_t(r['N_retning_p50'])}/{_t(r['N_retning_p95'])} | "
        f"**{_t(r['p_H1'], 3)}** |")
    dele = [
        "# B4 kandidat 7 — holdout-testen af T · tærskel: resultat", "",
        f"**Kørt:** {meta['koert_utc']} UTC fra `{meta['head'][:12]}`, frosset hypotese "
        f"`research/prereg/b4_k7_holdout.md` (commit `{meta.get('frosset', '—')[:12]}`). "
        f"Kandidat 7's modul uændret fra {K7_COMMIT}. R = {res['n_reps']}. ES (MES-økonomi), "
        "$4,45, dagens niveau.", "",
        "## Hovedtabel", "",
        "| serie | aktive_dage_n | andel_long | brutto_usd_dag | netto_usd_dag | CI90_netto | "
        "CI95_netto | N_retning_p5/p50/p95 | p_H1 |", "|" + "---|" * 9,
        rk("holdout 2024-01-02 → 2026-09-30", H), rk("in-sample 2016-04-01 → 2023-12-29", I),
        "",
        f"- **H1** (p_H1 ≤ 0,05 på holdout): {ja(A['H1'])}, p_H1 = {_t(H['p_H1'], 3)}.",
        f"- **H2** (CI90-nedre > 0 på holdout): {ja(A['H2'])}, CI90-nedre = "
        f"{_t(H['ci90_lo'])}.",
        f"- **§5 anvendt mekanisk:** række {A['raekke']}: {A['tekst']}.",
        f"- **E_f** (énsidet 95%-nedre, in-sample og holdout samlet, n {A['samlet_dage_n']}): "
        f"{_t(A['E_f'])} (middel {_t(A['samlet_middel'])}). E_f > 0: "
        f"{'ja' if A['E_f_over_0'] else 'nej'}. Uden marts 2020: {_t(A['E_f_uden_marts_2020'])}.",
        "", "## Diagnoser (§7, afgør intet)", "",
        f"Grænsen for urolige måneder (in-sample p90 af månedlig sd af R^ES): "
        f"{_t(res['uro'], 5)}.", "",
        "| diagnose | holdout | in-sample |", "|---|---|---|"]
    rows = [
        ("uden urolige måneder", lambda r: _seg_txt(r["uden_uro"])),
        ("kun urolige måneder", lambda r: _seg_txt(r["kun_uro"])),
        ("bedste dags andel af netto i alt", lambda r: f"{_t(100 * r['koncentration']['bedste_dag_andel'], 1)}%"),
        ("de 5% bedste dages andel", lambda r: f"{_t(100 * r['koncentration']['bedste_5pct_andel'], 1)}% "
                                               f"(n {r['koncentration']['bedste_5pct_n']})"),
        ("netto uden de 5 bedste dage", lambda r: _t(r["koncentration"]["uden_5_bedste"])),
        ("før publiceringen (d < 2025-03-01)", lambda r: _seg_txt(r["foer_publ"])),
        ("efter publiceringen", lambda r: _seg_txt(r["efter_publ"])),
        ("andel long / short", lambda r: f"{_t(100 * r['andel_long'], 0)}% / "
                                         f"{_t(100 * r['andel_short'], 0)}%"),
        ("driftjusteret brutto", lambda r: _seg_txt(r["diag"]["driftjusteret"])),
        ("long hele dagen, brutto / netto", lambda r: f"{_t(r['lang']['brutto'])} / "
                                                      f"{_t(r['lang']['netto'])}"),
        ("brutto nat", lambda r: _seg_txt(r["diag"]["brutto_nat"])),
        ("brutto RTH", lambda r: _seg_txt(r["diag"]["brutto_rth"])),
        ("netto ved $5,70", lambda r: _seg_txt(r["diag"]["netto_570"])),
        ("nominelt", lambda r: _seg_txt(r["diag"]["nominelt"])),
        ("break-even pr. round trip, middel / CI-nedre",
         lambda r: f"{_t(r['diag']['breakeven_middel'])} / {_t(r['diag']['breakeven_CI'])}"),
        ("T med hele MES: aktive dage, netto [CI95]",
         lambda r: f"{r['diag_hel']['aktive_dage_n']}, {_t(r['diag_hel']['middel_netto_usd'])} "
                   f"{_ci(r['diag_hel']['ci95_lo'], r['diag_hel']['ci95_hi'])}"),
        ("netto p1/p5/p50/p95/p99", lambda r: "/".join(_t(r["diag"][f"netto_p{q}"], 0)
                                                     for q in (1, 5, 50, 95, 99))),
        ("værste / bedste dag", lambda r: f"{_t(r['diag']['netto_vaerst'], 0)} / "
                                          f"{_t(r['diag']['netto_bedst'], 0)}"),
        ("σ pr. aktiv dag", lambda r: _t(r["diag"]["sd_aktiv"], 0)),
        ("skævhed", lambda r: _t(r["diag"]["skaevhed"], 2)),
        ("største tab i dagen pr. enhed p1/p5/p50/værst",
         lambda r: "/".join(_t(r["diag"][f"tab_i_dagen_{q}"], 0)
                            for q in ("p1", "p5", "p50", "vaerst"))),
        ("reversal: b_T uden kontrol $/sd [95%]",
         lambda r: f"{_t(r['reversal']['T_uden']['b_T'])} "
                   f"{_ci(r['reversal']['T_uden']['b_T_lo'], r['reversal']['T_uden']['b_T_hi'])}"),
        ("reversal: b_T med kontrol $/sd [95%]",
         lambda r: f"{_t(r['reversal']['T_med']['b_T'])} "
                   f"{_ci(r['reversal']['T_med']['b_T_lo'], r['reversal']['T_med']['b_T_hi'])}"),
        ("reversal: b_E (ES' afkast på t) med kontrol",
         lambda r: f"{_t(r['reversal']['T_med']['b_E'])} "
                   f"{_ci(r['reversal']['T_med']['b_E_lo'], r['reversal']['T_med']['b_E_hi'])}"),
        ("handelsdage / udelukkede", lambda r: f"{r['kvalitet']['handelsdage_n']} / "
                                               f"{len(r['kvalitet']['udelukket'])}"),
        ("forsinket indgang 1–5 min / udgang fra tidligere bar",
         lambda r: f"{r['kvalitet']['indgang_forsinket_1_5_n']} / "
                   f"{r['kvalitet']['udgang_tidligere_bar_n']}"),
        ("manglende signalbarer ES / ZN",
         lambda r: f"{len(r['kvalitet']['signalbar_mangler_ES'])} / "
                   f"{len(r['kvalitet']['signalbar_mangler_ZN'])}"),
        ("ruller i vinduet", lambda r: str(r["kvalitet"]["ruller_i_vinduet_n"])),
    ]
    for navn, f in rows:
        dele.append(f"| {navn} | {f(H)} | {f(I)} |")
    dele += ["", "Udelukkede holdout-dage: " + (", ".join(H["kvalitet"]["udelukket"]) or
                                                "ingen") + ".", "",
             "| år | aktive dage | brutto $/dag | netto $/dag [CI95] |", "|---|---|---|---|"]
    for navn, r in (("holdout", H), ("in-sample", I)):
        for a in r["aar"]:
            dele.append(f"| {a['aar']} ({navn}) | {a['n']} | {_t(a['brutto'])} | "
                        f"{_t(a['netto'])} {_ci(a['lo'], a['hi'])} |")
    return "\n".join(dele) + "\n"


def lang_tabel(res: dict) -> pd.DataFrame:
    rows = []
    for navn in ("holdout", "in_sample"):
        r = res[navn]
        flad = {k: v for k, v in r.items() if isinstance(v, (int, float, np.floating))}
        rows.append({"serie": navn, "tabel": "hoved", **flad})
        for k in ("diag", "diag_hel", "koncentration", "foer_publ", "efter_publ", "uden_uro",
                  "kun_uro"):
            d = {}
            for kk, x in r[k].items():
                if isinstance(x, dict):
                    d.update({f"{kk}_{a}": b for a, b in x.items()})
                else:
                    d[kk] = x
            rows.append({"serie": navn, "tabel": k, **d})
        for a in r["aar"]:
            rows.append({"serie": navn, "tabel": "aar", **a})
    rows.append({"serie": "samlet", "tabel": "afgoerelse", **res["afgoerelse"]})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Kørslen
# ---------------------------------------------------------------------------

def uro_in_sample() -> dict:
    """§9.4: grænsen for urolige måneder på in-sample alene. Kun ES' dagsafkast."""
    sig = k7.byg_signal(k7.serie(k7.ES), k7.serie(k7.ZN), k7.signal_dage())
    return uro_graense(sig.R_es, sig.dage)


def in_sample(n_reps: int = NRET_REPS) -> dict:
    """Samme vej på in-sample alene: signal og handel på in-sample-serien."""
    dage = k7.signal_dage()
    df_es = k7.serie(k7.ES)
    sig = k7.byg_signal(df_es, k7.serie(k7.ZN), dage)
    h = k7.byg_handel(df_es, dage, k7.ES)
    uro = uro_graense(sig.R_es, sig.dage)["graense"]
    return {"sig": sig, "h": h, **serie_resultat(h, sig, uro, n_reps)}


def regression_k7() -> dict:
    """§9.5: kandidat 7's T og K på in-sample, med k7's egne funktioner."""
    dage = k7.signal_dage()
    df_es = k7.serie(k7.ES)
    sig = k7.byg_signal(df_es, k7.serie(k7.ZN), dage)
    h = k7.byg_handel(df_es, dage, k7.ES)
    ws = k7.positioner(sig)
    t = {v: k7.variant_tal(h, ws[v]) for v in k7.VARIANTER}
    ok = (t["T"]["aktive_dage_n"] == REGRESSION_T[0]
          and round(t["T"]["middel_netto_usd"], 2) == REGRESSION_T[1]
          and t["K"]["aktive_dage_n"] == REGRESSION_K[0]
          and round(t["K"]["middel_netto_usd"], 2) == REGRESSION_K[1])
    return {"T": (t["T"]["aktive_dage_n"], t["T"]["middel_netto_usd"]),
            "K": (t["K"]["aktive_dage_n"], t["K"]["middel_netto_usd"]), "ok": ok}


def koer(n_reps: int = NRET_REPS) -> dict:
    """§9, trin 2: kandidat 7's modul uændret, regressionstjekket OK, så én åbning."""
    if not k7_uaendret():
        raise RuntimeError(f"{K7_STI} afviger fra {K7_COMMIT}; holdout åbnes ikke")
    reg = regression_k7()
    if not reg["ok"]:
        raise RuntimeError(f"regressionstjekket afveg; holdout åbnes ikke: {reg}")
    uro = uro_in_sample()["graense"]
    df_es = samlet(k7.serie(k7.ES), holdout_serie(k7.ES))
    df_zn = samlet(k7.serie(k7.ZN), holdout_serie(k7.ZN))
    return analyse(df_es, df_zn, signal_dage(), uro, n_reps)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--uro", action="store_true",
                     help="§9.4: grænsen for urolige måneder på in-sample, uden P&L")
    grp.add_argument("--in-sample", action="store_true",
                     help="samme vej på in-sample; åbner ikke holdout")
    grp.add_argument("--regressionstjek", action="store_true",
                     help="§9.5: kandidat 7's T og K på in-sample")
    grp.add_argument("--koer", action="store_true",
                     help="§9 trin 2: åbner holdout én gang. Kræver ejerens godkendelse")
    args = ap.parse_args(argv)
    meta = {"koert_utc": pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M"),
            "head": k7.k4._git("rev-parse", "HEAD").stdout.strip()}
    if args.uro:
        u = uro_in_sample()
        print(f"grænse (p{URO_KVANTIL} af månedlig sd af R^ES over {u['maaneder_n']} "
              f"in-sample-måneder): {u['graense']:.6f}")
        print(f"urolige in-sample-måneder ({len(u['urolige'])}): {', '.join(u['urolige'])}")
        return
    if args.regressionstjek:
        r = regression_k7()
        print(f"Kandidat 7: T {r['T'][0]} / {r['T'][1]:.2f}, K {r['K'][0]} / {r['K'][1]:.2f}: "
              f"{'OK' if r['ok'] else 'AFVIGER'}")
        if not r["ok"]:
            sys.exit(1)
        return
    if args.in_sample:
        r = in_sample()
        print(f"in-sample T: aktive dage {r['aktive_dage_n']}, netto {r['netto_usd_dag']:.2f} "
              f"$/dag, CI95 [{r['ci95_lo']:.2f}; {r['ci95_hi']:.2f}], p_H1 {r['p_H1']:.4f}")
        return
    commits = k1.committede(COMMITTEDE)
    meta["frosset"] = commits[k1._rel(FROSSET)]
    res = koer()
    md = skriv_md(res, meta)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "b4_k7_holdout.md").write_text(md, encoding="utf-8")
    lang_tabel(res).to_csv(OUT / "b4_k7_holdout.csv", index=False)
    print(md)


if __name__ == "__main__":
    main()
