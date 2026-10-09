"""B4 — edge-kravet: hvor stor skal en edge være, før Topstep giver plus?

Præregistreret i ``research/prereg/b4_edgekrav.md``. Reglerne er §2, strategien §3, det
der rapporteres §4. Modellen bruger **ingen kursdata og intet fra holdout**: en strategi er
kun sin årlige Sharpe netto og sin daglige spredning i dollar. ``research/mll_ruin.py``
importeres kun i testen (krydstjekket, §7.2.8) og røres ikke.

    .venv/bin/python -m research.b4_edgekrav tid       én celle à 20.000 stier og et skøn
    .venv/bin/python -m research.b4_edgekrav gitter    hele gitteret. Kræver ejerens godkendelse

## Vejen gennem modulet

1. ``Regler`` (§2) og ``regler_uden_dll`` / ``regler_95`` til følsomheden (§5).
2. ``traek_stoej``: Z (standardiseret Student-t eller normal) og U pr. sti og dag, med fast
   frø. Samme træk i alle celler: common random numbers.
3. ``bridge_minimum``: dagens laveste punkt givet dagsslut X (§3).
4. ``dagens_udfald``: realtidsbrud og DLL i den rigtige rækkefølge. Fælles for Combine og
   XFA. ``combine_dagsslut`` og ``xfa_dagsslut``: trailing, konsistensmål og udbetaling.
5. ``simuler_aar``: ét år for én celle (Sharpe, σ_C, σ_X). ``combine_alene``: kun Combine,
   uden reset — bruges af gambler's ruin-testen og krydstjekket mod ``mll_ruin.py``.
6. ``opsummer`` (§4), ``koer_sharpe`` (bedste størrelse og disciplinzonen), ``kravet``
   (S_min_EV og S_hurtig) og ``tidsmaaling`` (§7.4).

## Læsninger — valgt af Code, skrevet op før kørslen

Præregistreringen fastlægger ikke disse detaljer. De er valgt her og skal bekræftes. Dem,
der kan flytte resultatet, eller hvor reglen kan læses på to måder, er mærket **[tvivl]**.

1. **DLL og MLL i samme dag.** Begge er nedre grænser for dagens P&L i realtid. Afstanden
   til MLL er ``d = MLL − saldo ved dagens start``. Ligger MLL nærmere end DLL
   (``d ≥ −1.000``), er dagen et brud, hvis minimum når ``d``. Ellers flades dagen på
   −$1.000, hvis minimum når −$1.000, og dagen er ikke et brud.
2. **[tvivl] Lige langt til DLL og MLL** (``d = −1.000``) tælles som **brud**. Det er ikke
   et kanttilfælde: start på $0 med MLL −$2.000, en DLL-dag giver saldo −$1.000 med MLL
   uændret på −$2.000, og næste DLL-dag rammer begge på én gang. Topstep: rammer net P&L
   grænsen, likvideres kontoen. Den anden læsning (DLL vinder) giver færre brud.
3. **Dagen efter brud eller beståelse.** Reset efter Combine-brud gælder fra næste
   handelsdag; brud-dagen er brugt. En XFA starter dagen efter beståelse, og et nyt
   Combine-forløb dagen efter XFA-lukning. Ingen ventedage imellem. [tvivl] I praksis går
   der nogle dage fra beståelse til XFA; det gør modellen en smule optimistisk.
4. **[tvivl] Abonnementet** tælles pr. Combine-forløb: $49 betales på forløbets dag 1, 22,
   43 … (påbegyndte 21-dages blokke af Combine-dage). Et reset nulstiller ikke tælleren.
   Et nyt forløb efter XFA-lukning starter en ny tæller. Den anden læsning — at et reset
   også starter en ny abonnementsmåned, eller at månederne er faste kalenderblokke — giver
   andre gebyrer ved lave Sharpes, hvor der er mange resets.
5. **API** er $14,50 × påbegyndte 21-dages blokke af horisonten, ens for alle stier:
   12 × 14,50 = $174 ved 252 dage.
6. **Konsistensmålet** bruger bedste dag i det igangværende forsøg; et reset starter
   bedste dag, saldo, MLL og dagstæller forfra. Bestået kræver mindst 2 handelsdage i
   forsøget. Målet tjekkes ved dagsslut.
7. **Vindende dag i XFA** er dags-P&L ≥ $150 (``$150+``). En DLL-dag er aldrig vindende.
   Tælleren tæller dage, ikke sammenhængende dage.
8. **Udbetaling** tjekkes ved dagsslut, når tælleren er ≥ 5: beløbet er
   ``min(loft, saldo / 2)`` og tages kun, hvis det er ≥ $125. Er det under (saldo < $250),
   tages intet, og tælleren beholdes, til beløbet er stort nok.
9. **Efter udbetaling** er MLL $0 (låst), saldoen falder med beløbet, tælleren er 0.
10. **[tvivl] Nettoværdien** er 90% af udbetalingerne inden for horisonten minus gebyrerne.
    En XFA-saldo, der står ved horisonten uden at være udbetalt, tæller **ikke** med (§1.3:
    "90% af udbetalingerne"). Det gør tallet konservativt for stier, der lige er bestået.
11. **Tider** regnes i handelsdage fra første Combine-dag (dag 1). "Inden for 63 dage" er
    dag ≤ 63. **Median dage til bestået** er medianen blandt de stier, der består inden for
    horisonten (første beståelse); andelen står ved siden af.
12. **Antal resets** er det forventede antal Combine-brud pr. år (hvert koster $49).
13. **95%-intervallet** for forventet nettoværdi er ``middel ± 1,96 · sd / √n`` for den
    valgte celle. Det tager ikke højde for, at cellen er valgt som den bedste af 100; ved
    lav Sharpe er punktet derfor lidt optimistisk.
14. **[tvivl] S_hurtig** (§1.4 og §4) siger ikke ved hvilken størrelse. Hovedlæsningen er
    **ved den størrelse, der er bedst på forventet nettoværdi** (§4: "Ved den bedste
    størrelse"). Den anden læsning er den størrelse, der maksimerer P(første udbetaling ≤
    63 dage). ``kravet`` regner begge.
15. **Interpolation** (§4): S_min_EV er det første nulpunkt for EV(S) mellem to
    gitterpunkter, hvor EV skifter fra ≤ 0 til > 0, lineært. Er EV > 0 allerede i første
    gitterpunkt, rapporteres gitterpunktet og et flag. Samme for intervallets nedre grænse
    og for S_hurtig (med 0,5 som tærskel).
16. **Uden bevægelse inden for dagen** (følsomhed §5) er minimum ``min(0, X)``: brud og DLL
    tjekkes kun på dagsslut.
17. **Brownian bridge** bruger cellens σ som bridgens varians, også når X er trukket fra
    Student-t (§3 ordret).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from dataclasses import dataclass, field, replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "output"

HANDELSDAGE_AAR = 252
HORISONT = 252
DAGE_MAANED = 21
N_STIER = 20_000
FROE = 20261009
DF = 4

SHARPE_GITTER = (-0.5, 0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0)
SIGMA_GITTER = (100.0, 150.0, 200.0, 250.0, 300.0, 400.0, 500.0, 600.0, 800.0, 1000.0)
DISCIPLIN_MAX = 400.0
VINDUER = (63, 126, 252)
HURTIG_DAGE = 63
HURTIG_P = 0.5
Z95 = 1.959963984540054

COMBINE, XFA = 0, 1


@dataclass(frozen=True)
class Regler:
    """§2. Beløb i dollar, saldo regnet fra startsaldoen (Combine $0 = $50.000)."""
    combine_maal: float = 3_000.0
    mll_rum: float = 2_000.0
    mll_laas: float = 0.0
    dll: float | None = 1_000.0
    konsistens: float | None = 0.55
    min_dage: int = 2
    trailing: bool = True
    reset: float = 49.0
    abonnement: float = 49.0
    aktivering: float = 149.0
    api: float = 14.50
    vinderdag: float = 150.0
    vinderdage: int = 5
    udbetaling_andel: float = 0.5
    udbetaling_loft: float = 4_000.0
    udbetaling_min: float = 125.0
    profitdeling: float = 0.90


def regler_uden_dll(r: Regler = Regler()) -> Regler:
    """§5: DLL slået fra. Udbetalingsloftet er så $2.000."""
    return replace(r, dll=None, udbetaling_loft=2_000.0)


def regler_95(r: Regler = Regler()) -> Regler:
    """§5: $95-planen uden aktiveringsgebyr."""
    return replace(r, abonnement=95.0, aktivering=0.0)


def abonnement_blokke(combine_dage: int) -> int:
    """Påbegyndte 21-dages blokke for et Combine-forløb på ``combine_dage`` dage."""
    return -(-int(combine_dage) // DAGE_MAANED)


def api_gebyr(horisont: int, r: Regler = Regler()) -> float:
    return r.api * abonnement_blokke(horisont)


def mu_fra_sharpe(sharpe: float, sigma: float) -> float:
    """§3: μ = S / √252 · σ."""
    return sharpe / math.sqrt(HANDELSDAGE_AAR) * sigma


# ---------------------------------------------------------------------------
# Tilfældigheden
# ---------------------------------------------------------------------------

def standard_t(rng: np.random.Generator, df: int | None, size) -> np.ndarray:
    """Student-t med ``df`` frihedsgrader skaleret til varians 1. ``None`` er normal."""
    if df is None:
        return rng.standard_normal(size)
    if df <= 2:
        raise ValueError("varians findes kun for df > 2")
    return rng.standard_t(df, size) / math.sqrt(df / (df - 2.0))


@dataclass
class Stoej:
    """Z og U pr. (sti, dag). U er uniform på (0, 1]."""
    Z: np.ndarray
    U: np.ndarray
    df: int | None
    froe: int


def traek_stoej(n: int = N_STIER, dage: int = HORISONT, df: int | None = DF,
                froe: int = FROE) -> Stoej:
    rng = np.random.default_rng(froe)
    Z = standard_t(rng, df, (n, dage))
    U = 1.0 - np.random.default_rng([froe, 1]).random((n, dage))
    return Stoej(Z=Z, U=U, df=df, froe=froe)


def bridge_minimum(X, sigma, U):
    """Minimum af en Brownian bridge fra 0 til X med varians σ² over dagen.

    P(M ≤ m | X) = exp(−2 m (m − X) / σ²) for m ≤ min(0, X). Invers:
    M = (X − √(X² − 2σ² ln U)) / 2.
    """
    X = np.asarray(X, dtype=float)
    return 0.5 * (X - np.sqrt(X * X - 2.0 * np.square(sigma) * np.log(U)))


# ---------------------------------------------------------------------------
# Én dag
# ---------------------------------------------------------------------------

def dagens_udfald(saldo, mll, X, M, r: Regler):
    """(dags-P&L, brud, dll_ramt). Realtidsbrud og DLL i den rigtige rækkefølge.

    Læsning 1 og 2: ``d = mll − saldo``. Ligger MLL nærmere end eller lige så nær som DLL,
    er dagen et brud, når M ≤ d. Ellers flades dagen på −DLL, når M ≤ −DLL.
    """
    d = np.asarray(mll, dtype=float) - np.asarray(saldo, dtype=float)
    M = np.asarray(M, dtype=float)
    X = np.asarray(X, dtype=float)
    if r.dll is None:
        brud = M <= d
        dll_ramt = np.zeros_like(brud)
    else:
        mll_foerst = d >= -r.dll
        brud = mll_foerst & (M <= d)
        dll_ramt = ~mll_foerst & (M <= -r.dll)
    pnl = np.where(dll_ramt, -(r.dll or 0.0), X)
    return pnl, brud, dll_ramt


def trail(mll, saldo, r: Regler):
    """MLL efter dagsslut: følger højeste dagsslutsaldo − rum, låser ved ``mll_laas``."""
    if not r.trailing:
        return mll
    return np.minimum(r.mll_laas, np.maximum(mll, saldo - r.mll_rum))


def combine_maal(bedste_dag, r: Regler):
    """§2: saldo ≥ max(3.000, bedste dag / 0,55)."""
    if r.konsistens is None:
        return np.full_like(np.asarray(bedste_dag, dtype=float), r.combine_maal)
    return np.maximum(r.combine_maal, np.asarray(bedste_dag, dtype=float) / r.konsistens)


def combine_dagsslut(saldo, mll, bedste, dage, pnl, r: Regler):
    """Ikke-brudte stier: (saldo, mll, bedste, dage, bestået)."""
    saldo = saldo + pnl
    bedste = np.maximum(bedste, pnl)
    mll = trail(mll, saldo, r)
    dage = dage + 1
    bestaaet = (dage >= r.min_dage) & (saldo >= combine_maal(bedste, r))
    return saldo, mll, bedste, dage, bestaaet


def xfa_dagsslut(saldo, mll, vinder, pnl, r: Regler):
    """Ikke-brudte stier: (saldo, mll, vinder, udbetaling)."""
    saldo = saldo + pnl
    mll = trail(mll, saldo, r)
    vinder = vinder + (pnl >= r.vinderdag)
    beloeb = np.minimum(r.udbetaling_loft, r.udbetaling_andel * saldo)
    ud = (vinder >= r.vinderdage) & (beloeb >= r.udbetaling_min)
    beloeb = np.where(ud, beloeb, 0.0)
    saldo = saldo - beloeb
    mll = np.where(ud, 0.0, mll)
    vinder = np.where(ud, 0, vinder)
    return saldo, mll, vinder, beloeb


# ---------------------------------------------------------------------------
# Ét år
# ---------------------------------------------------------------------------

def simuler_aar(sharpe: float, sigma_c: float, sigma_x: float, stoej: Stoej,
                r: Regler = Regler(), horisont: int = HORISONT, intradag: bool = True,
                X_fast: np.ndarray | None = None, M_fast: np.ndarray | None = None) -> dict:
    """Ét år for én celle. Returnerer per-sti-arrays.

    ``X_fast``/``M_fast`` (n, dage) overstyrer trækket helt — kun til deterministiske tests.
    """
    if X_fast is not None:
        n = X_fast.shape[0]
    else:
        n = stoej.Z.shape[0]
        if stoej.Z.shape[1] < horisont:
            raise ValueError("støjen er kortere end horisonten")
    mu_c, mu_x = mu_fra_sharpe(sharpe, sigma_c), mu_fra_sharpe(sharpe, sigma_x)

    fase = np.full(n, COMBINE, dtype=np.int8)
    saldo = np.zeros(n)
    mll = np.full(n, -r.mll_rum)
    bedste = np.zeros(n)
    dage = np.zeros(n, dtype=np.int32)
    blok = np.zeros(n, dtype=np.int32)
    vinder = np.zeros(n, dtype=np.int32)

    gebyr = np.zeros(n)
    udbetalt = np.zeros(n)
    resets = np.zeros(n, dtype=np.int32)
    lukninger = np.zeros(n, dtype=np.int32)
    n_bestaaet = np.zeros(n, dtype=np.int32)
    n_udbetalinger = np.zeros(n, dtype=np.int32)
    foerste_bestaaet = np.full(n, np.inf)
    foerste_udbetaling = np.full(n, np.inf)

    for t in range(horisont):
        dag = t + 1
        i_c = fase == COMBINE
        if X_fast is not None:
            X, M = X_fast[:, t], M_fast[:, t]
        else:
            sigma = np.where(i_c, sigma_c, sigma_x)
            X = np.where(i_c, mu_c, mu_x) + sigma * stoej.Z[:, t]
            M = bridge_minimum(X, sigma, stoej.U[:, t]) if intradag else np.minimum(0.0, X)

        ny_blok = i_c & (blok % DAGE_MAANED == 0)
        gebyr += np.where(ny_blok, r.abonnement, 0.0)
        blok += i_c

        pnl, brud, _ = dagens_udfald(saldo, mll, X, M, r)

        # Combine
        c_ok = i_c & ~brud
        s2, m2, b2, d2, bestaar = combine_dagsslut(saldo, mll, bedste, dage, pnl, r)
        x_ok = ~i_c & ~brud
        s3, m3, v3, ud = xfa_dagsslut(saldo, mll, vinder, pnl, r)

        saldo = np.where(c_ok, s2, np.where(x_ok, s3, saldo))
        mll = np.where(c_ok, m2, np.where(x_ok, m3, mll))
        bedste = np.where(c_ok, b2, bedste)
        dage = np.where(c_ok, d2, dage)
        vinder = np.where(x_ok, v3, vinder)
        ud = np.where(x_ok, ud, 0.0)
        udbetalt += ud
        n_udbetalinger += ud > 0
        foerste_udbetaling = np.where((ud > 0) & np.isinf(foerste_udbetaling), dag,
                                      foerste_udbetaling)

        c_brud = i_c & brud
        resets += c_brud
        gebyr += np.where(c_brud, r.reset, 0.0)

        bestod = c_ok & bestaar
        gebyr += np.where(bestod, r.aktivering, 0.0)
        n_bestaaet += bestod
        foerste_bestaaet = np.where(bestod & np.isinf(foerste_bestaaet), dag, foerste_bestaaet)

        x_brud = ~i_c & brud
        lukninger += x_brud

        # Overgange. Nyt Combine-forsøg efter Combine-brud og XFA-lukning, XFA efter bestået.
        ny_c = c_brud | x_brud
        ny_x = bestod
        nul = ny_c | ny_x
        saldo = np.where(nul, 0.0, saldo)
        mll = np.where(nul, -r.mll_rum, mll)
        bedste = np.where(nul, 0.0, bedste)
        dage = np.where(nul, 0, dage)
        vinder = np.where(nul, 0, vinder)
        blok = np.where(x_brud | ny_x, 0, blok)
        fase = np.where(ny_x, XFA, np.where(x_brud, COMBINE, fase)).astype(np.int8)

    gebyr += api_gebyr(horisont, r)
    netto = r.profitdeling * udbetalt - gebyr
    return {
        "n": n,
        "horisont": horisont,
        "netto": netto,
        "gebyr": gebyr,
        "udbetalt": udbetalt,
        "til_ejer": r.profitdeling * udbetalt,
        "resets": resets,
        "lukninger": lukninger,
        "n_bestaaet": n_bestaaet,
        "n_udbetalinger": n_udbetalinger,
        "foerste_bestaaet": foerste_bestaaet,
        "foerste_udbetaling": foerste_udbetaling,
        "slut_fase": fase,
        "slut_saldo": saldo,
    }


def combine_alene(n: int, horisont: int, dag_traek, r: Regler = Regler(),
                  froe: int = FROE) -> dict:
    """Ét Combine-forsøg uden reset: bestået, ruin eller uafgjort ved horisonten.

    ``dag_traek(rng, k)`` giver (X, M) for k levende stier. Kun de levende stier trækkes,
    så lange horisonter er billige. Bruges af gambler's ruin og krydstjekket.
    """
    rng = np.random.default_rng(froe)
    idx = np.arange(n)
    saldo = np.zeros(n)
    mll = np.full(n, -r.mll_rum)
    bedste = np.zeros(n)
    dage = np.zeros(n, dtype=np.int32)
    bestaaet = np.zeros(n, dtype=bool)
    ruin = np.zeros(n, dtype=bool)
    dag_slut = np.zeros(n, dtype=np.int32)
    for t in range(horisont):
        if idx.size == 0:
            break
        X, M = dag_traek(rng, idx.size)
        pnl, brud, _ = dagens_udfald(saldo, mll, X, M, r)
        s, m_, b, d, best = combine_dagsslut(saldo, mll, bedste, dage, pnl, r)
        best &= ~brud
        ruin[idx[brud]] = True
        bestaaet[idx[best]] = True
        dag_slut[idx[brud | best]] = t + 1
        hold = ~(brud | best)
        idx, saldo, mll, bedste, dage = idx[hold], s[hold], m_[hold], b[hold], d[hold]
    return {"n": n, "bestaaet": int(bestaaet.sum()), "ruin": int(ruin.sum()),
            "uafgjort": int(n - bestaaet.sum() - ruin.sum()), "bestaaet_sti": bestaaet,
            "dag_slut": dag_slut}


def brownian_dag(mu: float, sigma: float, df: int | None = None):
    """Dagstræk til ``combine_alene``: X = μ + σZ og bridge-minimum."""
    def traek(rng, k):
        X = mu + sigma * standard_t(rng, df, k)
        U = 1.0 - rng.random(k)
        return X, bridge_minimum(X, sigma, U)
    return traek


def diskret_2til1_dag(wr: float, R: float, omk: float, maks_handler: int = 3):
    """Dagstræk som ``mll_ruin.simulate`` (optimistisk brud, én kontrakt, konstant R).

    1-``maks_handler`` handler om dagen, hver +2R − c eller −R − c. M er minimum af den
    kumulerede dags-P&L efter hver handel (og 0): kontoen dør kun, når et stop rammes.
    """
    def traek(rng, k):
        n_h = rng.integers(1, maks_handler + 1, k)
        kum = np.zeros(k)
        M = np.zeros(k)
        for slot in range(maks_handler):
            vind = rng.random(k) < wr
            delta = np.where(vind, 2.0 * R - omk, -R - omk)
            kum = np.where(slot < n_h, kum + delta, kum)
            M = np.minimum(M, kum)
        return kum, M
    return traek


# ---------------------------------------------------------------------------
# §4: opsummering, størrelse og kravet
# ---------------------------------------------------------------------------

def opsummer(res: dict) -> dict:
    n = res["n"]
    netto = res["netto"]
    sd = float(netto.std(ddof=1))
    ev = float(netto.mean())
    fb, fu = res["foerste_bestaaet"], res["foerste_udbetaling"]
    ud = {
        "n": n,
        "EV": ev,
        "EV_lo": ev - Z95 * sd / math.sqrt(n),
        "EV_hi": ev + Z95 * sd / math.sqrt(n),
        "P_netto_pos": float((netto > 0).mean()),
        "netto_p10": float(np.percentile(netto, 10)),
        "til_ejer": float(res["til_ejer"].mean()),
        "gebyr": float(res["gebyr"].mean()),
        "resets": float(res["resets"].mean()),
        "median_dage_bestaaet": float(np.median(fb[np.isfinite(fb)])) if np.isfinite(fb).any()
        else float("nan"),
    }
    for v in VINDUER:
        if v <= res["horisont"]:
            ud[f"P_bestaaet_{v}"] = float((fb <= v).mean())
            ud[f"P_udbetaling_{v}"] = float((fu <= v).mean())
    return ud


def koer_sharpe(sharpe: float, stoej: Stoej, r: Regler = Regler(), horisont: int = HORISONT,
                intradag: bool = True, sigmaer=SIGMA_GITTER) -> dict:
    """Alle (σ_C, σ_X) for én Sharpe. Bedste størrelse er højeste forventede nettoværdi."""
    celler = []
    for sc in sigmaer:
        for sx in sigmaer:
            o = opsummer(simuler_aar(sharpe, sc, sx, stoej, r, horisont, intradag))
            celler.append({"sharpe": sharpe, "sigma_c": sc, "sigma_x": sx, **o})
    bedst = max(celler, key=lambda c: c["EV"])
    zone = [c for c in celler if c["sigma_c"] <= DISCIPLIN_MAX and c["sigma_x"] <= DISCIPLIN_MAX]
    bedst_zone = max(zone, key=lambda c: c["EV"])
    hurtig_key = f"P_udbetaling_{HURTIG_DAGE}"
    hurtigst = max(celler, key=lambda c: c.get(hurtig_key, -1.0))
    return {"sharpe": sharpe, "bedst": bedst, "disciplin": bedst_zone, "hurtigst": hurtigst,
            "celler": celler}


def foerste_krydsning(xs, ys, taerskel: float) -> dict:
    """Laveste x hvor y > taerskel, lineært mellem gitterpunkter (læsning 15).

    Returnerer {'x': værdi eller None, 'flag': 'under_gitter' | 'over_gitter' | None}.
    "≥ 0,5" regnes som "> 0,5 − ε".
    """
    xs, ys = list(xs), list(ys)
    if ys[0] > taerskel:
        return {"x": xs[0], "flag": "under_gitter"}
    for (x0, y0), (x1, y1) in zip(zip(xs, ys), zip(xs[1:], ys[1:])):
        if y0 <= taerskel < y1:
            return {"x": x0 + (taerskel - y0) * (x1 - x0) / (y1 - y0), "flag": None}
    return {"x": None, "flag": "over_gitter"}


def kravet(rows: list[dict]) -> dict:
    """§4: S_min_EV (punkt og nedre 95%-grænse) og S_hurtig (begge læsninger, nr. 14)."""
    rows = sorted(rows, key=lambda r: r["sharpe"])
    S = [r["sharpe"] for r in rows]
    k = f"P_udbetaling_{HURTIG_DAGE}"
    eps = 1e-12
    return {
        "S_min_EV": foerste_krydsning(S, [r["bedst"]["EV"] for r in rows], 0.0),
        "S_min_EV_lo": foerste_krydsning(S, [r["bedst"]["EV_lo"] for r in rows], 0.0),
        "S_min_EV_disciplin": foerste_krydsning(S, [r["disciplin"]["EV"] for r in rows], 0.0),
        "S_hurtig_bedst": foerste_krydsning(S, [r["bedst"][k] for r in rows], HURTIG_P - eps),
        "S_hurtig_max": foerste_krydsning(S, [r["hurtigst"][k] for r in rows], HURTIG_P - eps),
        "EV_pos_ved_0": any(r["sharpe"] == 0.0 and r["bedst"]["EV"] > 0 for r in rows),
    }


def beslutning(s_min_ev: float | None) -> int:
    """§6, mekanisk: 1 (≤ 0,75), 2 (≤ 1,5) eller 3."""
    if s_min_ev is None or s_min_ev > 1.5:
        return 3
    return 1 if s_min_ev <= 0.75 else 2


# ---------------------------------------------------------------------------
# §7.4 tidsmåling og kørsel
# ---------------------------------------------------------------------------

def tidsmaaling(n: int = N_STIER, sharpe: float = 1.0, sigma_c: float = 300.0,
                sigma_x: float = 300.0, gentagelser: int = 3) -> dict:
    t0 = time.perf_counter()
    stoej = traek_stoej(n)
    t_stoej = time.perf_counter() - t0
    tider = []
    for _ in range(gentagelser):
        t0 = time.perf_counter()
        simuler_aar(sharpe, sigma_c, sigma_x, stoej)
        tider.append(time.perf_counter() - t0)
    celle = min(tider)
    n_celler = len(SHARPE_GITTER) * len(SIGMA_GITTER) ** 2
    # §5: fem følsomheder. Fordelingerne (normal, t3) kræver hver sin støj.
    n_foelsomhed = 5
    return {
        "n_stier": n,
        "sekunder_stoej": t_stoej,
        "sekunder_celle_min": celle,
        "sekunder_celle_alle": tider,
        "celler_hovedgitter": n_celler,
        "skoen_hovedgitter_min": n_celler * celle / 60.0,
        "skoen_med_foelsomhed_min": (1 + n_foelsomhed + 1) * n_celler * celle / 60.0,
        "note": "følsomhedens fordelinger tælles som to gitre (normal og t3); "
                "de tre andre følsomheder som ét gitter hver",
    }


def gitter(n: int = N_STIER) -> dict:  # pragma: no cover - kørslen kræver godkendelse
    stoej = traek_stoej(n)
    rows = [koer_sharpe(S, stoej) for S in SHARPE_GITTER]
    krav = kravet(rows)
    return {"rows": rows, "kravet": krav, "beslutning": beslutning(krav["S_min_EV"]["x"])}


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("kommando", choices=("tid", "gitter"))
    a = p.parse_args(argv)
    if a.kommando == "tid":
        print(json.dumps(tidsmaaling(), indent=2, ensure_ascii=False))
    else:
        raise SystemExit("Hele gitteret kører først, når ejeren har godkendt (§7.5).")


if __name__ == "__main__":
    main()
