"""B4 kandidat 5 — holdout-testen af "1m · uden middag".

Præregistreret i ``research/prereg/b4_k5_holdout.md``, som også er den frosne hypotese til
``data.holdout.load_holdout``. Strategien, nulmodellen og alle definitioner er
``research/b4_k5_vwap_trend.py`` som i commit 9d4bd2e, importeret uændret. Kun serien
skifter. Her ligger alene det præregistreringen tilføjer: H1, H2, rækken i §5, E_f og
diagnoserne side om side med in-sample.

    .venv/bin/python -m research.b4_k5_holdout --in-sample
    .venv/bin/python -m research.b4_k5_holdout --koer

``--in-sample`` kører samme vej på in-sample og må køres når som helst. ``--koer`` åbner
holdout (én gang) og kræver ejerens godkendelse (§9, trin 2).

## Læsninger

1. **Holdout-dagene** er XNYS-dagene 2024-01-02 → 2026-09-30. Serien skæres ved ET-dagen:
   barer med ET-dato efter 2026-09-30 fjernes, før gitteret bygges (``afskaer``).
2. **N-retning** er ``k5.nret_gentagelse`` med R = 500, samme frø og gitter som i
   kandidat 5. Den regner alle 4 varianter; kun "1m · uden middag" bruges. På in-sample
   giver det præcis kandidat 5's nulfordeling for varianten.
3. **p_H1** = ``(1 + #{nulmodellens middel ≥ modellens middel}) / 501``, énsidet, uden
   korrektion (§4).
4. **H2** er bestået, når den nedre grænse i det tosidede 90%-t-interval over dagene er
   > 0 (§4). **E_f** er samme grænse for in-sample og holdout samlet, dag for dag (§5).
5. **Rækken i §5:** 1 = H1 og H2; 2 = H1, ikke H2, middel netto > 0; 3 = H1, middel netto
   ≤ 0; 4 = alt andet.
6. **Diagnoserne i §7** er kandidat 5's (``k5.diagnoser``, ``k5.udelukkede_dage``,
   ``k5.altid_long``), regnet for begge serier. Opgørelsen pr. år regnes her over de år
   serien har, fordi ``k5.AAR_LISTE`` er 2019-2023.
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
from research import b4_k1_trinA as trinA  # noqa: E402
from research import b4_k2_nowick as k2  # noqa: E402
from research import b4_k5_vwap_trend as k5  # noqa: E402
from research.stats import mean_ci_t  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "output"
FROSSET = ROOT / "research" / "prereg" / "b4_k5_holdout.md"
K5_COMMIT = "9d4bd2e"
K5_STI = "research/b4_k5_vwap_trend.py"
COMMITTEDE = (Path(__file__).resolve(), ROOT / "tests" / "test_b4_k5_holdout.py", FROSSET,
              *k5.COMMITTEDE)

SYMBOL = "MNQ.v.0"
VARIANT = (1, k5.UDEN)                    # frosset, række 1 i kandidat 5
HOLDOUT_FRA = "2024-01-01"                # XNYS-dage fra og med
HOLDOUT_TIL = "2026-10-01"                # til, men ikke med: sidste dag 2026-09-30
NRET_REPS = k5.NRET_REPS                  # 500
ALFA_H1 = 0.05
ALFA_H2 = 0.10                            # tosidet 90% = énsidet 5%

TEKST = {1: "Bekræftet", 2: "Retningen er bekræftet, nettogevinsten er ikke bevist",
         3: "Parkeres: retningen virker stadig, men betaler ikke omkostningen efter 2023",
         4: "Parkeres: VWAP-retningen holdt ikke efter offentliggørelsen"}


# ---------------------------------------------------------------------------
# Serierne
# ---------------------------------------------------------------------------

def afskaer(df: pd.DataFrame, til: str = HOLDOUT_TIL) -> pd.DataFrame:
    """Læsning 1: kun barer hvis ET-dag ligger før ``til``."""
    return df[k1._et_dag(df.index) < pd.Timestamp(til)]


def holdout_dage() -> pd.DatetimeIndex:
    return k1.rth_dage(HOLDOUT_FRA, HOLDOUT_TIL)


def holdout_serie() -> pd.DataFrame:
    """Holdout åbnes kun her, gennem ``load_holdout`` med den frosne hypotese."""
    return afskaer(holdout.load_holdout(FROSSET, symbol=SYMBOL))


def k5_uaendret() -> bool:
    """Kandidat 5's modul er det samme som i commit 9d4bd2e."""
    r = subprocess.run(["git", "--no-optional-locks", "-C", str(ROOT), "diff", "--quiet",
                        K5_COMMIT, "--", K5_STI], capture_output=True)
    return r.returncode == 0


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


def serie_resultat(g: k5.Grundlag, n_reps: int = NRET_REPS) -> dict:
    """Varianten på ét grundlag: tallene, nulmodellen og kandidat 5's diagnoser."""
    hd, fl = k5.forbered(g)
    tal = {v: k5.variant_tal(g, hd[v]) for v in k5.VARIANTER}
    null = np.array([k5.nret_gentagelse(g, fl, rep)[VARIANT] for rep in range(n_reps)])
    t = tal[VARIANT]
    netto = t["_netto_dag"]
    lo95, hi95 = mean_ci_t(netto)
    lo90, hi90 = mean_ci_t(netto, alpha=ALFA_H2)
    p = p_h1(t["middel_netto_usd_dag"], null)
    diag = k5.diagnoser(g, hd, tal)
    aar = []
    for a in sorted(set(g.aar.tolist())):
        s = g.aar == a
        lo, hi = mean_ci_t(netto[s]) if s.sum() >= 2 else (float("nan"), float("nan"))
        aar.append({"aar": a, "dage_n": int(s.sum()), "netto_usd_dag": float(netto[s].mean()),
                    "ci95_lo": lo, "ci95_hi": hi,
                    "nominelt_usd_dag": float(t["_nominelt_dag"][s].mean()),
                    "handler_pr_dag": float(t["_k"][s].mean()),
                    "L_median": float(np.median(g.L[s]))})
    return {"g": g, "h": hd[VARIANT], "tal": t, "null": null,
            "dage_n": g.n, "handler_n": t["handler_n"],
            "brutto_usd_dag": t["middel_brutto_usd_dag"],
            "netto_usd_dag": t["middel_netto_usd_dag"], "ci90_lo": lo90, "ci90_hi": hi90,
            "ci95_lo": lo95, "ci95_hi": hi95,
            **{f"N_retning_p{q}": float(np.percentile(null, q)) for q in (5, 50, 95)},
            "p_H1": p, "diag": diag["variant"][VARIANT], "halvtime": diag["halvtime"][VARIANT],
            "altid_long": diag["altid_long"], "aar": aar,
            "udelukkede": [r for r in k5.udelukkede_dage(g)
                           if (r["tf"], r["middag"]) == VARIANT],
            "info": dict(g.info)}


def afgoerelse(hold: dict, ins: dict) -> dict:
    """§4-§5: H1 og H2 på holdout, rækken og E_f på begge serier samlet."""
    h1 = hold["p_H1"] <= ALFA_H1
    h2 = hold["ci90_lo"] > 0
    samlet = np.concatenate([ins["tal"]["_netto_dag"], hold["tal"]["_netto_dag"]])
    nr = raekke(h1, h2, hold["netto_usd_dag"])
    e_f = nedre_90(samlet)
    return {"H1": h1, "H2": h2, "raekke": nr, "tekst": TEKST[nr], "E_f": e_f,
            "E_f_over_0": bool(e_f > 0), "samlet_middel": float(samlet.mean()),
            "samlet_dage_n": len(samlet)}


def analyse(df_hold: pd.DataFrame, df_ins: pd.DataFrame, n_reps: int = NRET_REPS,
            dage_hold: pd.DatetimeIndex | None = None,
            dage_ins: pd.DatetimeIndex | None = None) -> dict:
    hold = serie_resultat(k5.byg_grundlag(afskaer(df_hold), dage_hold), n_reps)
    ins = serie_resultat(k5.byg_grundlag(df_ins, dage_ins), n_reps)
    return {"holdout": hold, "in_sample": ins, "afgoerelse": afgoerelse(hold, ins),
            "n_reps": n_reps}


# ---------------------------------------------------------------------------
# Rapporten, §8
# ---------------------------------------------------------------------------

def _t(x, nd: int = 2) -> str:
    return k2._t(x, nd)


def _ci(lo, hi, nd: int = 2) -> str:
    return f"[{_t(lo, nd)}; {_t(hi, nd)}]"


def skriv_md(res: dict, meta: dict) -> str:
    H, I, a = res["holdout"], res["in_sample"], res["afgoerelse"]
    par = (("holdout", H), ("in-sample", I))

    def tabel(hoved, celler) -> str:
        linjer = ["| serie | " + " | ".join(hoved) + " |", "|" + "---|" * (1 + len(hoved))]
        linjer += [f"| {n} | " + " | ".join(celler(r)) + " |" for n, r in par]
        return "\n".join(linjer) + "\n"

    d = lambda r, k: r["diag"][k]
    dele = [
        "# B4 kandidat 5 — holdout-testen af \"1m · uden middag\"\n",
        f"Kørt {meta['koert_utc']} UTC fra commit `{meta['head'][:7]}`. Frosset hypotese "
        f"`research/prereg/b4_k5_holdout.md` (commit `{meta.get('frosset', '?')[:7]}`). "
        f"Kandidat 5's modul uændret fra `{K5_COMMIT}`. N-retning: {res['n_reps']} "
        f"gentagelser. $ pr. dag pr. MNQ ved NQ {_t(k5.NQ_NIVEAU, 0)}.\n",
        "## Hovedtabel, §8\n",
        tabel(["dage_n", "handler_n", "brutto_usd_dag", "netto_usd_dag", "CI90_netto",
               "CI95_netto", "N_retning_p5/p50/p95", "p_H1"],
              lambda r: [_t(r["dage_n"]), _t(r["handler_n"]), _t(r["brutto_usd_dag"]),
                         _t(r["netto_usd_dag"]), _ci(r["ci90_lo"], r["ci90_hi"]),
                         _ci(r["ci95_lo"], r["ci95_hi"]),
                         "/".join(_t(r[f"N_retning_p{q}"]) for q in (5, 50, 95)),
                         _t(r["p_H1"], 4)]),
        "## Afgørelsen, §5, mekanisk\n",
        f"- H1 (p_H1 ≤ 0,05): **{'bestået' if a['H1'] else 'ikke bestået'}**",
        f"- H2 (CI90-nedre > 0): **{'bestået' if a['H2'] else 'ikke bestået'}**",
        f"- **Række {a['raekke']}: {a['tekst']}.**",
        f"- E_f (énsidet 95%-nedre grænse, in-sample og holdout samlet, "
        f"{_t(a['samlet_dage_n'])} dage): **{_t(a['E_f'])}**, middel "
        f"{_t(a['samlet_middel'])}. Combine-betingelse 1 (E_f > 0): "
        f"{'opfyldt' if a['E_f_over_0'] else 'ikke opfyldt'}.\n",
        "## Diagnoser, §7\n",
        tabel(["netto ved $3,169 [CI95]", "nominelt [CI95]", "break-even middel",
               "break-even CI"],
              lambda r: [f"{_t(r['tal']['netto_usd_dag_ved_3169'])} "
                         f"{_ci(r['tal']['ved_3169_ci95_lo'], r['tal']['ved_3169_ci95_hi'])}",
                         f"{_t(r['tal']['netto_usd_dag_nominelt'])} "
                         f"{_ci(r['tal']['nominelt_ci95_lo'], r['tal']['nominelt_ci95_hi'])}",
                         _t(r["tal"]["breakeven_omk_middel"], 3),
                         _t(r["tal"]["breakeven_omk_CI"], 3)]),
        tabel(["bp/handel", "bp/dag", "handler pr. dag p10/p50/p90", "hit % brutto",
               "gevinst/tab brutto", "Sharpe/år"],
              lambda r: [_t(d(r, "bp_pr_handel"), 3), _t(d(r, "bp_pr_dag")),
                         "/".join(_t(d(r, f"handler_pr_dag_p{q}"), 0) for q in (10, 50, 90)),
                         _t(r["tal"]["hit_ratio_pct_brutto"], 1),
                         _t(r["tal"]["gevinst_tab_forhold"], 2), _t(d(r, "sharpe_aar"))]),
        "Brutto pr. halve time, New York-tid, $ pr. dag:\n",
        "| halve time NY | holdout | in-sample |\n|---|---|---|\n" +
        "".join(f"| {k5._hhmm_ny(k)} | {_t(H['halvtime'][k])} | {_t(I['halvtime'][k])} |\n"
                for k in range(k5.DAG_MIN // 30)),
        tabel(["sidste 5 min brutto [CI95]", "dag p1/p5/p50/p95/p99", "værste/bedste dag",
               "tab inden for dagen p1/p5/værste"],
              lambda r: [f"{_t(d(r, 'sidste_5_usd_dag'))} "
                         f"{_ci(d(r, 'sidste_5_ci95_lo'), d(r, 'sidste_5_ci95_hi'))}",
                         "/".join(_t(d(r, f"dag_p{q}"), 0) for q in (1, 5, 50, 95, 99)),
                         f"{_t(d(r, 'dag_vaerste'), 0)}/{_t(d(r, 'dag_bedste'), 0)}",
                         f"{_t(d(r, 'intradag_tab_p1'), 0)}/{_t(d(r, 'intradag_tab_p5'), 0)}/"
                         f"{_t(d(r, 'intradag_tab_vaerste'), 0)}"]),
        tabel(["bedste dags andel", "5% bedste dages andel", "long − short brutto [Welch-CI95]",
               "altid-long [CI95]"],
              lambda r: [_t(d(r, "bedste_dag_andel"), 3), _t(d(r, "top5pct_dage_andel"), 3),
                         f"{_t(d(r, 'long_minus_short'))} "
                         f"{_ci(d(r, 'long_minus_short_ci95_lo'), d(r, 'long_minus_short_ci95_hi'))}",
                         f"{_t(r['altid_long']['middel_netto_usd_dag'])} "
                         f"{_ci(r['altid_long']['ci95_lo'], r['altid_long']['ci95_hi'])}"]),
        "Pr. år:\n",
        "| serie | år | dage | netto $/dag [CI95] | nominelt | handler pr. dag | median L_d |\n"
        "|---|---|---|---|---|---|---|\n" +
        "".join(f"| {n} | {x['aar']} | {_t(x['dage_n'])} | {_t(x['netto_usd_dag'])} "
                f"{_ci(x['ci95_lo'], x['ci95_hi'])} | {_t(x['nominelt_usd_dag'])} | "
                f"{_t(x['handler_pr_dag'], 1)} | {_t(x['L_median'])} |\n"
                for n, r in par for x in r["aar"]),
        tabel(["XNYS-dage", "udelukket", "manglende RTH-minutter", "ruller i RTH"],
              lambda r: [_t(r["info"]["rth_dage_n"]), _t(r["info"]["udelukket_n"]),
                         _t(r["info"]["manglende_minutter_n"]),
                         _t(r["info"]["ruller_i_rth_n"])]),
        "Udelukkede dage (diagnose, ikke i middel, CI eller nulmodel):\n",
        "| serie | dag | grund | handler_n | netto $ | nominelt $ | tab inden for dagen $ |\n"
        "|---|---|---|---|---|---|---|\n" +
        "".join(f"| {n} | {x['dag']} | {x['grund']} | {_t(x['handler_n'])} | "
                f"{_t(x['dag_netto_usd'])} | {_t(x['dag_netto_usd_nominelt'])} | "
                f"{_t(x['intradag_tab_vaerste'])} |\n" for n, r in par for x in r["udelukkede"]),
        "## Efter kørslen\n", "Stop. §5 anvendes mekanisk og læses sammen med ejeren.\n",
    ]
    return "\n".join(dele)


def lang_tabel(res: dict) -> pd.DataFrame:
    rows = []
    for navn in ("holdout", "in_sample"):
        r = res[navn]
        rows.append({"tabel": "hoved", "serie": navn,
                     **{k: r[k] for k in ("dage_n", "handler_n", "brutto_usd_dag",
                                          "netto_usd_dag", "ci90_lo", "ci90_hi", "ci95_lo",
                                          "ci95_hi", "N_retning_p5", "N_retning_p50",
                                          "N_retning_p95", "p_H1")},
                     **{k: v for k, v in r["tal"].items() if not k.startswith("_")}})
        rows.append({"tabel": "diagnose", "serie": navn, **r["diag"]})
        rows += [{"tabel": "aar", "serie": navn, **x} for x in r["aar"]]
        rows += [{"tabel": "halvtime", "serie": navn, "halvtime_ny": k5._hhmm_ny(k),
                  "brutto_usd_dag": x} for k, x in enumerate(r["halvtime"])]
        rows += [{"tabel": "udelukket_dag", "serie": navn, **x} for x in r["udelukkede"]]
    rows.append({"tabel": "afgoerelse", **res["afgoerelse"]})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Kørslen
# ---------------------------------------------------------------------------

def in_sample(n_reps: int = NRET_REPS) -> dict:
    g = k5.byg_grundlag(k5.mnq(), k1.rth_dage(trinA.MNQ_START, trinA.TRIN_A_SLUT))
    return serie_resultat(g, n_reps)


def koer(n_reps: int = NRET_REPS) -> dict:
    """§9, trin 2: kandidat 5's modul uændret, regressionstjekket OK, så én åbning."""
    if not k5_uaendret():
        raise RuntimeError(f"{K5_STI} afviger fra {K5_COMMIT}; holdout åbnes ikke")
    df_ins = k5.mnq()
    reg = k5.regressionstjek(df_ins)
    if not reg["ok"]:
        raise RuntimeError(f"regressionstjekket afveg; holdout åbnes ikke: {reg}")
    return analyse(holdout_serie(), df_ins, n_reps, holdout_dage(),
                   k1.rth_dage(trinA.MNQ_START, trinA.TRIN_A_SLUT))


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--in-sample", action="store_true",
                     help="samme vej på in-sample; åbner ikke holdout")
    grp.add_argument("--koer", action="store_true",
                     help="§9 trin 2: åbner holdout én gang. Kræver ejerens godkendelse")
    args = ap.parse_args(argv)
    meta = {"koert_utc": pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M"),
            "head": k5.k4._git("rev-parse", "HEAD").stdout.strip()}
    if args.in_sample:
        r = in_sample()
        print(f"in-sample 1m · uden middag: dage {r['dage_n']}, handler {r['handler_n']}, "
              f"netto {r['netto_usd_dag']:.2f} $/dag, CI95 [{r['ci95_lo']:.2f}; "
              f"{r['ci95_hi']:.2f}], p_H1 {r['p_H1']:.4f}")
        return
    commits = k1.committede(COMMITTEDE)
    meta["frosset"] = commits[k1._rel(FROSSET)]
    res = koer()
    md = skriv_md(res, meta)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "b4_k5_holdout.md").write_text(md, encoding="utf-8")
    lang_tabel(res).to_csv(OUT / "b4_k5_holdout.csv", index=False)
    print(md)


if __name__ == "__main__":
    main()
