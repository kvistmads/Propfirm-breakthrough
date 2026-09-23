"""B4 kandidat 1 — trin 2: de syv filtre og scorefordelingen.

Præregistreret i ``research/prereg/b4_k1_trin2_optaelling.md``. Kilden til kriterierne er
``research/kilder/photon_sd_video_noter.md``. Kernen er ``research/b4_k1_optaelling.py``
(kerne v2, ``zoner_v2``) og signalbegrebet er trin A-motorens kandidatregel
(``research/b4_k1_trinA.py``, ``sizing_ekte``) — begge står uændrede.

    .venv/bin/python -m research.b4_k1_filtre --regressionstjek
    .venv/bin/python -m research.b4_k1_filtre --koer

**Kørslen ser ikke på udfald.** Den tæller signaler, filterværdier og scorer. Ingen handel
simuleres, intet R regnes, intet lægges til tælleren for den deflaterede tærskel. Pris
hentes kun gennem ``data.holdout.load_in_sample``; holdout åbnes ikke.

## To spor, præregistreringen §2

    A   handelstimeframe 15m, højere timeframe 1h   (vennens timeframe, det trin A testede)
    B   handelstimeframe  5m, højere timeframe 15m  (videoens eget eksempel, 14:55)

Fælles: kerne v2 med buffer 10%, MNQ.v.0 2019-05-06 → 2023-12-31, indgangsvinduet
08:30-14:30 CT på en RTH-dag og før RTH-luk − 30 min, og **et signal er en berøring i
vinduet hvor ``kontrakter_ekte ≥ 1``** — nøjagtig trin A-motorens kandidatregel, med
kontrakter loftet ved 50. Den procentbaserede ``under_stoploft`` fra optællingsmodulet
bruges ikke, af samme grund som i trin A §4d.

## Signalet og de to skæringer, §3a

Hvert filter bruger kun det der var kendt ved lukningen af lyset **før** berøringslyset;
filtre der hører til dannelsen, kun det der var kendt ved udbrudslysets lukning. Derfor
læser ``beregn_filtre`` aldrig en pris med indeks ≥ berøringslysets: skæringstidspunktet
er ``t_snit`` = lukningen af lyset før berøringen, og et HTF-lys tælles med først når det
er lukket senest ``t_snit``. Det er testet ved at skære 1m-serien af ved ``t_snit``,
bygge begge timeframes forfra og kræve samme syv værdier — ``tests/test_b4_k1_filtre.py``.

Swing-punkter: N = 5 på alle timeframes. Et lys er swing high hvis dets high er højere end
de 5 lys før og mindst lige så højt som de 5 lys efter; swing low spejlvendt. Punktet er
kendt fra og med lukningen af det femte lys efter, jf. §3a.

## Fire præciseringer, afklaret med Mads 2026-09-23 før kørslen

§3b's ordlyd er ikke ændret; fire steder var den ikke entydig, og den bogstavelige læsning
var to steder degenereret. Målingerne står i rapporten.

1. **Kriterium 6, "et kendt HTF-swing high":** det *seneste* kendte, som i kriterium 1, 3
   og 7. Bogstaveligt ("et hvilket som helst kendt") har 80,9% af 1h-lysene både et op- og
   et nedbrud i samme lys, så "nyere end" bliver uafgjort og kriteriet reelt kun måler om
   prisen ligger under det højeste swing low i hele historikken.
2. **Kriterium 2, tredje led:** lyset der lukker over S's top søges fra og med S's
   berøringslys til, men ikke med, demand-zonens berøringslys. Uden nedre grænse er leddet
   sandt for 98,7% af lysene, fordi præfiks-maks af close næsten altid ligger over det
   aktuelle niveau.
3. **Kriterium 2, vinduet:** S's første berøring ligger i ``basis_i − 4 … basis_i``, altså
   også i selve basislyset.
4. **Kriterium 5:** kun HTF-zoner der stadig lever efter kerne v2 ved skæringen. En zone
   der er blevet ugyldig eller død ved kontraktskift stakker ikke, selv om den aldrig blev
   berørt.
"""
from __future__ import annotations

import argparse
import itertools
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data import holdout, resample, sessions  # noqa: E402
from research import b4_k1_optaelling as k1  # noqa: E402
from research import b4_k1_trinA as trinA  # noqa: E402
from research.stats import breakeven_win_rate, wilson_interval  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "output"
PREREG = ROOT / "research" / "prereg" / "b4_k1_trin2_optaelling.md"
KILDE = ROOT / "research" / "kilder" / "photon_sd_video_noter.md"
# Kørslen sker kun når disse er committet og uændrede.
COMMITTEDE = (
    Path(__file__).resolve(), ROOT / "tests" / "test_b4_k1_filtre.py", PREREG, KILDE,
    ROOT / "research" / "b4_k1_optaelling.py", ROOT / "research" / "b4_k1_trinA.py",
    ROOT / "data" / "holdout.py", ROOT / "data" / "resample.py",
    ROOT / "data" / "sessions.py", ROOT / "research" / "stats.py",
)

SYMBOL = trinA.MNQ
START = trinA.MNQ_START
SLUT = trinA.TRIN_A_SLUT
BUFFER = k1.BUFFER_V2
SWING_N = 5                                  # §3a, LuxAlgo's standard for intern struktur
SPOR = {"A": (15, 60), "B": (5, 15)}         # spor: (handelstimeframe, højere timeframe)
DEMAND, SUPPLY, ALLE = k1.DEMAND, k1.SUPPLY, k1.ALLE
RR = k1.RR
MDE_DAGE = 310                               # §5's grænse for en testbar tærskel
EVIG = np.iinfo(np.int64).max                # dødstidspunkt for en zone der aldrig dør

FILTRE = ("brud", "flip", "sweep", "inducement", "stakket", "retning", "discount")
KOL = tuple(f"f{nr}_{navn}" for nr, navn in enumerate(FILTRE, 1))
MAKS_SCORE = len(FILTRE)


# ---------------------------------------------------------------------------
# Swing-punkter, §3a
# ---------------------------------------------------------------------------

def swing_punkter(high, low, n: int = SWING_N) -> tuple[np.ndarray, np.ndarray]:
    """(swing_high, swing_low) som boolske masker over lysene.

    Swing high: strengt højere high end de ``n`` lys før, og mindst lige så højt som de
    ``n`` lys efter. Swing low spejlvendt. De ``n`` første og sidste lys kan aldrig være
    swing-punkter. Punktet er kendt fra og med lys ``i + n`` — se ``_kendt``.
    """
    h, l = np.asarray(high, dtype=float), np.asarray(low, dtype=float)
    m = len(h)
    sh, sl = np.zeros(m, dtype=bool), np.zeros(m, dtype=bool)
    if m < 2 * n + 1:
        return sh, sl
    vh = np.lib.stride_tricks.sliding_window_view(h, 2 * n + 1)
    vl = np.lib.stride_tricks.sliding_window_view(l, 2 * n + 1)
    sh[n:m - n] = (vh[:, n] > vh[:, :n].max(axis=1)) & (vh[:, n] >= vh[:, n + 1:].max(axis=1))
    sl[n:m - n] = (vl[:, n] < vl[:, :n].min(axis=1)) & (vl[:, n] <= vl[:, n + 1:].min(axis=1))
    return sh, sl


def _kendt(er_swing: np.ndarray, n: int = SWING_N) -> tuple[np.ndarray, np.ndarray]:
    """(bekræftelsesindeks, swing-indeks) for hvert swing-punkt, sorteret stigende.

    Bekræftelsen er lys ``i + n``: først dér er de ``n`` lys efter lukket, §3a.
    """
    idx = np.flatnonzero(er_swing)
    return idx + n, idx


def _seneste_niveau(niveau: np.ndarray, er_swing: np.ndarray,
                    n: int = SWING_N) -> np.ndarray:
    """``ud[m]`` = niveauet for det seneste swing-punkt der er kendt ved lys ``m``'s
    lukning, NaN hvor intet er kendt endnu."""
    conf, idx = _kendt(er_swing, n)
    ud = np.full(len(niveau), np.nan)
    if len(idx) == 0:
        return ud
    pos = np.searchsorted(conf, np.arange(len(niveau)), side="right") - 1
    ok = pos >= 0
    ud[ok] = niveau[idx[pos[ok]]]
    return ud


# ---------------------------------------------------------------------------
# Vindue og signal — k1's regler, men med timeframen som parameter
# ---------------------------------------------------------------------------

def vindue_mask(index: pd.DatetimeIndex, bar_min: int) -> np.ndarray:
    """Som ``k1.vindue_mask``, men for en vilkårlig timeframe.

    08:30 ≤ t < 14:30 CT på en RTH-dag og t < RTH-luk − 30 min (halve dage: 11:30 CT).
    ``rth_mask`` kræver desuden at lyset ligger helt i NYSE-sessionen.
    """
    if len(index) == 0:
        return np.zeros(0, dtype=bool)
    rth = sessions.rth_mask(index, bar_min)
    ct = index.tz_convert(k1.CT)
    minut = np.asarray(ct.hour * 60 + ct.minute)
    luk = pd.DatetimeIndex(sessions._xnys().schedule["close"].reindex(k1._et_dag(index)))
    foer_luk = np.asarray(index < luk - k1.LUK_MARGIN, dtype=bool)   # NaT → False
    return rth & (minut >= k1.VINDUE_CT[0]) & (minut < k1.VINDUE_CT[1]) & foer_luk


def klassificer(bars: pd.DataFrame, zoner: pd.DataFrame, bar_min: int) -> pd.DataFrame:
    """``i_vindue`` og ``dag`` pr. zone — samme to kolonner som ``k1.klassificer``.

    Stoploftet i procent og k1's NQ-normerede sizing indgår ikke: signalet her er trin
    A-motorens kandidatregel, hvor dollarloftet alene håndhæves af ``kontrakter_ekte``.
    """
    z = zoner.copy()
    vindue = vindue_mask(bars.index, bar_min)
    beroert = (z["status"] == k1.BEROERT).to_numpy()
    slut = z["slut_i"].to_numpy(dtype=np.int64)
    z["i_vindue"] = beroert & vindue[np.where(beroert, slut, 0)]
    z["dag"] = pd.Series(k1._et_dag(pd.DatetimeIndex(z["slut_tid"])),
                         index=z.index).where(beroert)
    return z


def spor_data(df_1m: pd.DataFrame, tf_min: int, htf_min: int,
              buffer: Fraction = BUFFER) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """(handelsbarer, HTF-barer, zoner med signal). Begge timeframes bygges af den samme
    1m-serie, §3a."""
    bars = resample.aggregate(df_1m, tf_min)
    htf = resample.aggregate(df_1m, htf_min)
    z = trinA.sizing_ekte(klassificer(bars, k1.find_zoner_v2(bars, buffer), tf_min))
    z["signal"] = (z["i_vindue"].to_numpy(dtype=bool)
                   & (z["kontrakter_ekte"].to_numpy(dtype=float) >= 1))
    return bars, htf, z


# ---------------------------------------------------------------------------
# De syv filtre, §3b
# ---------------------------------------------------------------------------

def _luk(index: pd.DatetimeIndex, bar_min: int) -> np.ndarray:
    """Lukketidspunktet for hvert lys, i nanosekunder siden epoken. Heltal, ikke float:
    ns-tal i 2020'erne er for store til float64's 53 bit mantisse."""
    return (index + pd.Timedelta(minutes=bar_min)).astype("int64").to_numpy()


def _htf_zoner(htf: pd.DataFrame, htf_luk: np.ndarray) -> dict:
    """HTF-zonerne efter kerne v2 UDEN buffer, pr. side, sorteret efter dødstidspunkt.

    ``dannet`` er udbrudslysets lukning (zonen er gyldig derfra), ``doed`` lukningen af
    det lys hvor zonen døde — berørt, ugyldig eller kontraktskift — og +∞ for de zoner
    der stadig lever ved seriens slut. Kriterium 5 kræver ``dannet ≤ t_snit < doed``.
    """
    z = k1.find_zoner_v2(htf, Fraction(0))
    ud = {}
    for side in (DEMAND, SUPPLY):
        s = z[z["side"] == side]
        slut = s["slut_i"].to_numpy(dtype=np.int64)
        doed = np.where(slut >= 0, htf_luk[np.where(slut >= 0, slut, 0)], EVIG)
        orden = np.argsort(doed, kind="stable")
        ud[side] = {
            "dannet": htf_luk[s["udbrud_i"].to_numpy(dtype=np.int64)][orden],
            "doed": doed[orden],
            "high": s["zone_high"].to_numpy(dtype=float)[orden],
            "low": s["zone_low"].to_numpy(dtype=float)[orden],
        }
    return ud


def _modzoner(bars: pd.DataFrame, buffer: Fraction) -> dict:
    """De berørte kerne v2-zoner pr. side, sorteret efter berøringslysets indeks.

    Kriterium 2 slår her op: for en demand-zone er S en supply-zone fra samme liste.
    """
    z = k1.find_zoner_v2(bars, buffer)
    z = z[z["status"] == k1.BEROERT]
    ud = {}
    for side in (DEMAND, SUPPLY):
        s = z[z["side"] == side]
        beroering = s["slut_i"].to_numpy(dtype=np.int64)
        orden = np.argsort(beroering, kind="stable")
        ud[side] = {
            "beroering": beroering[orden],
            "high": s["zone_high"].to_numpy(dtype=float)[orden],
            "low": s["zone_low"].to_numpy(dtype=float)[orden],
        }
    return ud


def beregn_filtre(zoner: pd.DataFrame, bars: pd.DataFrame, htf: pd.DataFrame,
                  tf_min: int, htf_min: int, buffer: Fraction = BUFFER,
                  swing_n: int = SWING_N) -> pd.DataFrame:
    """De syv kriterier og scoren for hver zone i ``zoner``. §3b.

    ``zoner`` skal være berørte kerne v2-zoner fra netop ``bars`` (``side``, ``basis_i``,
    ``udbrud_i``, ``slut_i``, ``zone_high``, ``zone_low``, ``E``). ``htf`` er den højere
    timeframe, bygget af den samme 1m-serie.

    **Intet kig frem.** Skæringen er ``t_snit`` = lukningen af lyset før berøringen. Ingen
    pris med indeks ≥ ``slut_i`` læses, hverken på handelstimeframen eller på HTF, hvor
    kun lys der er lukket senest ``t_snit`` tælles med. Funktionen bygger selv både
    zonelisten til kriterium 2 og HTF-zonelisten til kriterium 5 ud af de serier den får,
    så en afskåret serie giver de samme syv værdier — det er testens hele pointe.
    """
    h = bars["high"].to_numpy(dtype=float)
    l = bars["low"].to_numpy(dtype=float)
    c = bars["close"].to_numpy(dtype=float)
    tf_luk = _luk(bars.index, tf_min)
    hh = htf["high"].to_numpy(dtype=float)
    hl = htf["low"].to_numpy(dtype=float)
    hc = htf["close"].to_numpy(dtype=float)
    htf_luk = _luk(htf.index, htf_min)

    sh, sl = swing_punkter(h, l, swing_n)
    sh_conf, sh_idx = _kendt(sh, swing_n)
    sl_conf, sl_idx = _kendt(sl, swing_n)
    sh_niv, sl_niv = h[sh_idx], l[sl_idx]

    htf_sh, htf_sl = swing_punkter(hh, hl, swing_n)
    sen_sh = _seneste_niveau(hh, htf_sh, swing_n)
    sen_sl = _seneste_niveau(hl, htf_sl, swing_n)
    # Kriterium 6: for hvert HTF-lys, om det lukkede over/under det swing-punkt der var
    # kendt dér. Det seneste brud af hver slags sammenlignes ved skæringen.
    m_idx = np.arange(len(hc))
    sidste_op = np.maximum.accumulate(np.where(hc > sen_sh, m_idx, -1))
    sidste_ned = np.maximum.accumulate(np.where(hc < sen_sl, m_idx, -1))
    retning_op, retning_ned = sidste_op > sidste_ned, sidste_ned > sidste_op

    mod = _modzoner(bars, buffer)
    stak = _htf_zoner(htf, htf_luk)

    side_arr = zoner["side"].to_numpy()
    basis_arr = zoner["basis_i"].to_numpy(dtype=np.int64)
    udbrud_arr = zoner["udbrud_i"].to_numpy(dtype=np.int64)
    slut_arr = zoner["slut_i"].to_numpy(dtype=np.int64)
    high_arr = zoner["zone_high"].to_numpy(dtype=float)
    low_arr = zoner["zone_low"].to_numpy(dtype=float)
    e_arr = zoner["E"].to_numpy(dtype=float)

    ud = np.zeros((len(zoner), MAKS_SCORE), dtype=bool)
    for r in range(len(zoner)):
        demand = side_arr[r] == DEMAND
        basis_i, udbrud_i, ber_i = int(basis_arr[r]), int(udbrud_arr[r]), int(slut_arr[r])
        zone_high, zone_low, E = high_arr[r], low_arr[r], e_arr[r]
        t_snit = tf_luk[ber_i - 1]
        m_snit = int(np.searchsorted(htf_luk, t_snit, side="right")) - 1

        # 1 Brud på struktur: det seneste swing high over zonens top, kendt ved
        #   udbrudslysets lukning, brudt på lukning efter udbrudslyset og før berøringen.
        conf, niv = (sh_conf, sh_niv) if demand else (sl_conf, sl_niv)
        kendt = int(np.searchsorted(conf, udbrud_i, side="right"))
        over = (np.flatnonzero(niv[:kendt] > zone_high) if demand
                else np.flatnonzero(niv[:kendt] < zone_low))
        if len(over):
            graense = niv[over[-1]]
            seg = c[udbrud_i + 1:ber_i]
            if len(seg):
                ud[r, 0] = bool(seg.max() > graense) if demand else bool(seg.min() < graense)

        # 2 Flip: en overlappende modsat zone, berørt i basis_i − 4 … basis_i, hvis top
        #   (bund) blev lukket igennem mellem dens egen berøring og vores.
        m = mod[SUPPLY if demand else DEMAND]
        lo = int(np.searchsorted(m["beroering"], basis_i - 4, side="left"))
        hi = int(np.searchsorted(m["beroering"], basis_i, side="right"))
        for p in range(lo, hi):
            s_high, s_low = m["high"][p], m["low"][p]
            if zone_low > s_high or s_low > zone_high:      # ingen prisoverlapning
                continue
            seg = c[int(m["beroering"][p]):ber_i]
            if len(seg) and (seg.max() > s_high if demand else seg.min() < s_low):
                ud[r, 1] = True
                break

        # 3 Sweep: zonens bund under det seneste swing low kendt FØR basislyset, og
        #   udbrudslyset lukker over det. Vurderes ved dannelsen.
        conf3, niv3 = (sl_conf, sl_niv) if demand else (sh_conf, sh_niv)
        kendt3 = int(np.searchsorted(conf3, basis_i - 1, side="right"))
        if kendt3:
            n3 = niv3[kendt3 - 1]
            ud[r, 2] = (bool(zone_low < n3 and c[udbrud_i] > n3) if demand
                        else bool(zone_high > n3 and c[udbrud_i] < n3))

        # 4 Inducement: mindst ét swing low bliver kendt efter udbrudslyset og før
        #   berøringslyset, og ligger over indgangsniveauet E.
        conf4, niv4 = (sl_conf, sl_niv) if demand else (sh_conf, sh_niv)
        a = int(np.searchsorted(conf4, udbrud_i, side="right"))
        b = int(np.searchsorted(conf4, ber_i - 1, side="right"))
        seg4 = niv4[a:b]
        if len(seg4):
            ud[r, 3] = bool(seg4.max() > E) if demand else bool(seg4.min() < E)

        # 5 Stakket: en HTF-zone af samme side, dannet og stadig i live ved skæringen,
        #   som overlapper zonen prismæssigt.
        s5 = stak[DEMAND if demand else SUPPLY]
        lev = int(np.searchsorted(s5["doed"], t_snit, side="right"))
        ud[r, 4] = bool(((s5["dannet"][lev:] <= t_snit)
                         & (zone_low <= s5["high"][lev:])
                         & (s5["low"][lev:] <= zone_high)).any())

        if m_snit >= 0:
            # 6 Retning: det seneste HTF-strukturbrud peger samme vej som zonen.
            ud[r, 5] = bool(retning_op[m_snit]) if demand else bool(retning_ned[m_snit])

            # 7 Discount: zonens midtpunkt i den rigtige halvdel af HTF-rangen mellem de
            #   seneste kendte HTF-swings. Swing high under swing low: rangen udefineret.
            top, bund = sen_sh[m_snit], sen_sl[m_snit]
            if np.isfinite(top) and np.isfinite(bund) and top >= bund:
                midt, zone_midt = (top + bund) / 2, (zone_high + zone_low) / 2
                ud[r, 6] = bool(zone_midt < midt) if demand else bool(zone_midt > midt)

    tabel = pd.DataFrame(ud, columns=list(KOL), index=zoner.index)
    tabel["score"] = ud.sum(axis=1).astype(np.int64)
    return tabel


def signaler_med_filtre(df_1m: pd.DataFrame, tf_min: int, htf_min: int,
                        buffer: Fraction = BUFFER) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """(alle zoner, signalerne med filtre og score, metadata) for ét spor."""
    bars, htf, z = spor_data(df_1m, tf_min, htf_min, buffer)
    sig = z[z["signal"].to_numpy(dtype=bool)].copy()
    sig = pd.concat([sig, beregn_filtre(sig, bars, htf, tf_min, htf_min, buffer)], axis=1)
    meta = {"n_tf": len(bars), "n_htf": len(htf), "zoner_n": len(z),
            "zoner_i_vindue_n": int(z["i_vindue"].sum()),
            "afvist_kontrakter_nul_n": int((z["i_vindue"].to_numpy(dtype=bool)
                                            & (z["kontrakter_ekte"] < 1)).sum())}
    return z, sig, meta


# ---------------------------------------------------------------------------
# Optællingen, §4
# ---------------------------------------------------------------------------

def _dage_med_signal(sig: pd.DataFrame, dage: pd.DatetimeIndex) -> tuple[int, float, float]:
    """(antal RTH-dage med mindst ét signal, Wilson-CI's nedre og øvre grænse i procent)."""
    s = pd.DatetimeIndex(sig["dag"]).as_unit("ns")
    if not s.isin(dage).all():
        raise ValueError("signaler på dage uden for RTH-dagene")
    n = int(len(set(s)))
    lo, hi = wilson_interval(n, len(dage))
    return n, 100 * lo, 100 * hi


def _raekke(tabel: str, periode: str, side: str, noegle: str, **maal) -> list[dict]:
    return [{"tabel": tabel, "periode": periode, "side": side, "noegle": noegle,
             "stoerrelse": k, "vaerdi": float(v)} for k, v in maal.items()]


def filtertabel(sig: pd.DataFrame, periode: str = "alle") -> list[dict]:
    """Andel signaler hvor hvert af de syv kriterier er sandt. Alle, demand, supply."""
    rows = []
    for side, sub in ((ALLE, sig), (DEMAND, sig[sig["side"] == DEMAND]),
                      (SUPPLY, sig[sig["side"] == SUPPLY])):
        for kol in KOL:
            k, n = int(sub[kol].sum()), len(sub)
            lo, hi = wilson_interval(k, n)
            rows += _raekke("filtre", periode, side, kol, signaler_n=n, sande_n=k,
                            pct=100 * k / n if n else float("nan"),
                            ci95_lo_pct=100 * lo if n else float("nan"),
                            ci95_hi_pct=100 * hi if n else float("nan"))
    return rows


def scoretabel(sig: pd.DataFrame, dage: pd.DatetimeIndex, periode: str = "alle") -> list[dict]:
    """Scorefordelingen: signaler_n og dage_med_signal_n for score 0, 1, … 7."""
    rows = []
    for s in range(MAKS_SCORE + 1):
        sub = sig[sig["score"] == s]
        dage_n, lo, hi = _dage_med_signal(sub, dage)
        rows += _raekke("score", periode, ALLE, str(s), signaler_n=len(sub),
                        dage_med_signal_n=dage_n,
                        dage_med_signal_pct=100 * dage_n / len(dage),
                        ci95_lo_pct=lo, ci95_hi_pct=hi)
    return rows


def kumulativtabel(sig: pd.DataFrame, dage: pd.DatetimeIndex,
                   periode: str = "alle") -> list[dict]:
    """dage_med_signal_n for score ≥ k, k = 0 … 7. §5's grænse er 310 dage."""
    rows = []
    for s in range(MAKS_SCORE + 1):
        sub = sig[sig["score"] >= s]
        dage_n, lo, hi = _dage_med_signal(sub, dage)
        rows += _raekke("kumulativ", periode, ALLE, f">={s}", signaler_n=len(sub),
                        dage_med_signal_n=dage_n,
                        dage_med_signal_pct=100 * dage_n / len(dage),
                        ci95_lo_pct=lo, ci95_hi_pct=hi)
    return rows


def brud_alene(sig: pd.DataFrame, dage: pd.DatetimeIndex, periode: str = "alle") -> list[dict]:
    """Varianten "brud på struktur alene": dage_med_signal_n hvor kriterium 1 er sandt."""
    sub = sig[sig[KOL[0]]]
    dage_n, lo, hi = _dage_med_signal(sub, dage)
    return _raekke("brud_alene", periode, ALLE, KOL[0], signaler_n=len(sub),
                   dage_med_signal_n=dage_n, dage_med_signal_pct=100 * dage_n / len(dage),
                   ci95_lo_pct=lo, ci95_hi_pct=hi)


def phi(a: np.ndarray, b: np.ndarray) -> float:
    """Phi-koefficienten for to binære variable — Pearsons r på 0/1. NaN hvis den ene er
    konstant, for så er variansen nul og korrelationen udefineret."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if len(a) < 2 or a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def samvariation(sig: pd.DataFrame, periode: str = "alle") -> list[dict]:
    """Phi mellem hvert par af filtre — 21 par."""
    rows = []
    for x, y in itertools.combinations(KOL, 2):
        rows += _raekke("samvariation", periode, ALLE, f"{x}|{y}",
                        phi=phi(sig[x].to_numpy(), sig[y].to_numpy()),
                        signaler_n=len(sig))
    return rows


def omkostningstabel(sig: pd.DataFrame, meta: dict, periode: str = "alle") -> list[dict]:
    """Risiko, kontrakter og omkostning over signalerne. Udfaldsfrit.

    ``risiko_pt`` er E − low (supply: high − E) på zonens rigtige historiske priser, som
    trin A §4d — ikke k1's NQ 29.138-normerede tal. Populationen er signalerne, altså
    efter ``kontrakter_ekte ≥ 1``; hvor mange berøringer i vinduet den regel afviser,
    står som ``afvist_kontrakter_nul_n``.
    """
    maal = {"signaler_n": len(sig)}
    for q in (10, 50, 90):
        maal[f"risiko_pt_p{q}"] = k1._p(sig["risiko_pt_ekte"], q)
    for q in (10, 50, 90):
        maal[f"omk_R_netto_p{q}"] = k1._p(sig["omk_R_netto_ekte"], q)
    maal["be_WR_pct_netto_p50"] = (100 * breakeven_win_rate(RR, 1.0, maal["omk_R_netto_p50"])
                                   if len(sig) else float("nan"))
    for q in (50, 90):
        maal[f"kontrakter_p{q}"] = k1._p(sig["kontrakter_ekte"], q)
    maal["kontrakter_maks"] = (float(sig["kontrakter_ekte"].max()) if len(sig)
                               else float("nan"))
    maal["kontrakter_loftet_n"] = float((sig["kontrakter_ekte_raa"]
                                         > trinA.KONTRAKTER_LOFT).sum())
    maal["zoner_i_vindue_n"] = float(meta["zoner_i_vindue_n"])
    maal["afvist_kontrakter_nul_n"] = float(meta["afvist_kontrakter_nul_n"])
    return _raekke("omkostninger", periode, ALLE, "signaler", **maal)


def _aar_meta(z: pd.DataFrame, aar: int) -> dict:
    i_vindue = z[z["i_vindue"].to_numpy(dtype=bool)]
    i_vindue = i_vindue[pd.DatetimeIndex(i_vindue["dag"]).year == aar]
    return {"zoner_i_vindue_n": len(i_vindue),
            "afvist_kontrakter_nul_n": int((i_vindue["kontrakter_ekte"] < 1).sum())}


def optael(sig: pd.DataFrame, z: pd.DataFrame, dage: pd.DatetimeIndex,
           meta: dict) -> pd.DataFrame:
    """Alle §4's tabeller for ét spor, i langt format: én række pr. (tabel, periode, side,
    nøgle, størrelse)."""
    rows = (filtertabel(sig) + scoretabel(sig, dage) + kumulativtabel(sig, dage)
            + brud_alene(sig, dage) + samvariation(sig) + omkostningstabel(sig, meta))
    for aar in sorted(set(dage.year)):
        d = dage[dage.year == aar]
        s = sig[pd.DatetimeIndex(sig["dag"]).year == aar]
        rows += kumulativtabel(s, d, str(aar))
        rows += omkostningstabel(s, _aar_meta(z, aar), str(aar))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Regressionstjek, §4
# ---------------------------------------------------------------------------

def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "--no-optional-locks", "-C", str(ROOT), *args],
                          capture_output=True, text=True)


def trin_a_kandidater(bars_15m: pd.DataFrame, buffer: Fraction = BUFFER) -> np.ndarray:
    """Trin A-motorens kandidater: ``i_vindue`` og ``kontrakter_ekte ≥ 1``, k1's egen
    ``klassificer_v2``. Returnerer basislysenes indeks, sorteret."""
    z = trinA.sizing_ekte(k1.klassificer_v2(bars_15m, k1.find_zoner_v2(bars_15m, buffer),
                                            buffer))
    kand = z[z["i_vindue"].to_numpy(dtype=bool) & (z["kontrakter_ekte"] >= 1)]
    return np.sort(kand["basis_i"].to_numpy(dtype=np.int64))


def regressionstjek(df_1m: pd.DataFrame | None = None) -> dict:
    """§4's to tjek, begge før kørslen.

    1. ``research/b4_k1_optaelling.py`` gengiver stadig ``b4_k1_optaelling_v2.csv`` byte
       for byte — trin A's egen ``regressionstjek``, uændret.
    2. Spor A's signaler ved score ≥ 0 er de samme zoner som trin A-motorens kandidater
       for buffer 10%.
    """
    csv_ok = trinA.regressionstjek()
    df = _mnq() if df_1m is None else df_1m
    tf_min, htf_min = SPOR["A"]
    bars, _, z = spor_data(df, tf_min, htf_min)
    mine = np.sort(z.loc[z["signal"].to_numpy(dtype=bool), "basis_i"].to_numpy(dtype=np.int64))
    trin_a = trin_a_kandidater(bars)
    return {"csv_byte_for_byte": bool(csv_ok),
            "spor_a_signaler_n": int(len(mine)),
            "trin_a_kandidater_n": int(len(trin_a)),
            "identiske": bool(len(mine) == len(trin_a) and np.array_equal(mine, trin_a))}


# ---------------------------------------------------------------------------
# Rapport, §4
# ---------------------------------------------------------------------------

def _tal(v, nd: int = 1) -> str:
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "—"
    return f"{float(v):.{nd}f}".replace(".", ",")


def _n(v) -> str:
    return "—" if v is None or not np.isfinite(v) else str(int(round(float(v))))


def _opslag(tab: pd.DataFrame) -> dict:
    return {(r.tabel, r.periode, r.side, r.noegle, r.stoerrelse): r.vaerdi
            for r in tab.itertuples()}


def _andel(o: dict, noegle: tuple, stam: str = "pct") -> str:
    p = o.get(noegle + (stam,), float("nan"))
    lo = o.get(noegle + ("ci95_lo_pct",), float("nan"))
    hi = o.get(noegle + ("ci95_hi_pct",), float("nan"))
    return f"{_tal(p)} ({_tal(lo)}–{_tal(hi)})"


def filtertabel_md(o: dict) -> str:
    linjer = ["| kriterium | alle | demand | supply |", "|---|---|---|---|"]
    for nr, kol in enumerate(KOL, 1):
        celler = " | ".join(
            f"{_n(o[('filtre', 'alle', s, kol, 'sande_n')])} — "
            f"{_andel(o, ('filtre', 'alle', s, kol))}"
            for s in (ALLE, DEMAND, SUPPLY))
        linjer.append(f"| {nr}. {kol.split('_', 1)[1]} | {celler} |")
    return "\n".join(linjer) + "\n"


def scoretabel_md(o: dict) -> str:
    linjer = ["| score | signaler_n | dage_med_signal_n | dage_med_signal_pct (CI95) |",
              "|---|---|---|---|"]
    for s in range(MAKS_SCORE + 1):
        n = ("score", "alle", ALLE, str(s))
        linjer.append(f"| {s} | {_n(o[n + ('signaler_n',)])} | "
                      f"{_n(o[n + ('dage_med_signal_n',)])} | "
                      f"{_andel(o, n, 'dage_med_signal_pct')} |")
    return "\n".join(linjer) + "\n"


def kumulativtabel_md(o: dict, periode: str = "alle") -> str:
    linjer = ["| score ≥ k | signaler_n | dage_med_signal_n | dage_med_signal_pct (CI95) "
              "| mindst 310 dage |", "|---|---|---|---|---|"]
    for s in range(MAKS_SCORE + 1):
        n = ("kumulativ", periode, ALLE, f">={s}")
        dage_n = o[n + ("dage_med_signal_n",)]
        linjer.append(f"| ≥ {s} | {_n(o[n + ('signaler_n',)])} | {_n(dage_n)} | "
                      f"{_andel(o, n, 'dage_med_signal_pct')} | "
                      f"{'ja' if dage_n >= MDE_DAGE else 'nej'} |")
    return "\n".join(linjer) + "\n"


def kumulativ_aar_md(o: dict, aar: list[int]) -> str:
    linjer = ["| score ≥ k | " + " | ".join(str(a) for a in aar) + " |",
              "|---" * (len(aar) + 1) + "|"]
    for s in range(MAKS_SCORE + 1):
        celler = " | ".join(
            _n(o[("kumulativ", str(a), ALLE, f">={s}", "dage_med_signal_n")]) for a in aar)
        linjer.append(f"| ≥ {s} | {celler} |")
    return "\n".join(linjer) + "\n"


SAMVARIATION_TOP = 8


def samvariation_md(tab: pd.DataFrame) -> str:
    p = tab[(tab["tabel"] == "samvariation") & (tab["stoerrelse"] == "phi")
            & (tab["periode"] == "alle")]
    p = p.assign(abs_phi=p["vaerdi"].abs()).sort_values("abs_phi", ascending=False)
    linjer = ["| par | phi |", "|---|---|"]
    for _, r in p.iterrows():
        a, b = r["noegle"].split("|")
        linjer.append(f"| {a.split('_', 1)[1]} × {b.split('_', 1)[1]} | "
                      f"{_tal(r['vaerdi'], 3)} |")
    return "\n".join(linjer) + "\n"


OMK_RAEKKER = (("signaler_n", 0), ("risiko_pt_p10", 1), ("risiko_pt_p50", 1),
               ("risiko_pt_p90", 1), ("omk_R_netto_p10", 4), ("omk_R_netto_p50", 4),
               ("omk_R_netto_p90", 4), ("be_WR_pct_netto_p50", 2), ("kontrakter_p50", 1),
               ("kontrakter_p90", 1), ("kontrakter_maks", 0), ("kontrakter_loftet_n", 0),
               ("zoner_i_vindue_n", 0), ("afvist_kontrakter_nul_n", 0))


def omkostningstabel_md(o: dict, perioder: list[str]) -> str:
    linjer = ["| størrelse | " + " | ".join(perioder) + " |",
              "|---" * (len(perioder) + 1) + "|"]
    for navn, nd in OMK_RAEKKER:
        celler = " | ".join(
            _n(o[("omkostninger", p, ALLE, "signaler", navn)]) if nd == 0
            else _tal(o[("omkostninger", p, ALLE, "signaler", navn)], nd)
            for p in perioder)
        linjer.append(f"| {navn} | {celler} |")
    return "\n".join(linjer) + "\n"


def _rel(sti: Path) -> str:
    return Path(sti).resolve().relative_to(ROOT.resolve()).as_posix()


PRAECISERINGER = [
    "**Kriterium 6, \"et kendt HTF-swing high\":** det *seneste* kendte, som i kriterium "
    "1, 3 og 7. Bogstaveligt har 80,9% af 1h-lysene både et op- og et nedbrud i samme lys, "
    "så \"nyere end\" bliver uafgjort.",
    "**Kriterium 2, tredje led:** lyset der lukker over S's top søges fra og med S's "
    "berøringslys til, men ikke med, zonens eget berøringslys. Uden nedre grænse er leddet "
    "sandt for 98,7% af lysene.",
    "**Kriterium 2, vinduet:** S's første berøring ligger i `basis_i − 4 … basis_i`, altså "
    "også i selve basislyset.",
    "**Kriterium 5:** kun HTF-zoner der stadig lever efter kerne v2 ved skæringen; en zone "
    "der er blevet ugyldig eller død ved kontraktskift stakker ikke.",
]


def skriv_md(resultater: dict, meta: dict) -> str:
    c = meta["commits"]
    dele = [
        "# B4 kandidat 1 — trin 2: de syv filtre, optælling\n",
        f"Kørt {meta['koert_utc']} UTC fra commit `{meta['head'][:7]}`, med modul, tests, "
        f"præregistrering, kilde og datalag committet og uændrede. Præregistrering "
        f"`{_rel(PREREG)}` (commit `{c[_rel(PREREG)][:7]}`), kilde `{_rel(KILDE)}` "
        f"(commit `{c[_rel(KILDE)][:7]}`). Kode `{_rel(Path(__file__))}` "
        f"(commit `{c[_rel(Path(__file__))][:7]}`), kerne `{_rel(ROOT / 'research' / 'b4_k1_optaelling.py')}` "
        f"(commit `{c[_rel(ROOT / 'research' / 'b4_k1_optaelling.py')][:7]}`), motor "
        f"`{_rel(ROOT / 'research' / 'b4_k1_trinA.py')}` "
        f"(commit `{c[_rel(ROOT / 'research' / 'b4_k1_trinA.py')][:7]}`).\n",
        f"Serie: {SYMBOL} ohlcv-1m gennem `data.holdout.load_in_sample`, "
        f"{meta['foerste_bar_utc']} → {meta['sidste_bar_utc']} UTC, {meta['n_1m']} "
        f"1m-barer. RTH-dage: {meta['rth_dage_n']}. Kerne v2 med buffer 10%; et signal er "
        f"en berøring i indgangsvinduet hvor `kontrakter_ekte ≥ 1`.\n",
        "**Kørslen ser ikke på udfald.** Ingen handel er simuleret, intet R er regnet, "
        "ingen tærskel er valgt, og intet er lagt til tælleren for den deflaterede "
        "tærskel. §5's grænse på 310 dage står i tabellerne som en aflæsning, ikke som et "
        "valg — varianterne vælges sammen med Mads efter §5.\n",
        "## Regressionstjek, §4 — før kørslen\n",
        f"- `research/b4_k1_optaelling.py` gengiver `b4_k1_optaelling_v2.csv` byte for "
        f"byte: **{'OK' if meta['regression']['csv_byte_for_byte'] else 'AFVIGER'}**.\n"
        f"- Spor A's signaler ved score ≥ 0 mod trin A-motorens kandidater for buffer 10%: "
        f"{meta['regression']['spor_a_signaler_n']} mod "
        f"{meta['regression']['trin_a_kandidater_n']} zoner, "
        f"**{'identiske' if meta['regression']['identiske'] else 'FORSKELLIGE'}**.\n",
        "## Fire præciseringer, afklaret med Mads 2026-09-23 før kørslen\n",
        "§3b's ordlyd er ikke ændret. Fire steder var den ikke entydig, og to steder var "
        "den bogstavelige læsning degenereret; andelene nedenfor er målt på MNQ-serien før "
        "spørgsmålet blev stillet.\n",
        "\n".join(f"{i}. {t}" for i, t in enumerate(PRAECISERINGER, 1)) + "\n",
    ]
    for spor, res in resultater.items():
        tf_min, htf_min = SPOR[spor]
        o, tab = res["opslag"], res["tabel"]
        m = res["meta"]
        aar = sorted(set(meta["dage"].year))
        dele += [
            f"## Spor {spor} — handelstimeframe {tf_min}m, højere timeframe {htf_min}m\n",
            f"{m['n_tf']} {tf_min}m-barer og {m['n_htf']} {htf_min}m-barer af den samme "
            f"1m-serie. {m['zoner_n']} zoner dannet, {m['zoner_i_vindue_n']} berørt i "
            f"indgangsvinduet, heraf {m['afvist_kontrakter_nul_n']} afvist af "
            f"`kontrakter_ekte ≥ 1`. Signaler: "
            f"{_n(o[('omkostninger', 'alle', ALLE, 'signaler', 'signaler_n')])}.\n",
            f"### Spor {spor} — filtrene\n",
            "Antal sande og andel i procent med Wilson 95%-CI.\n",
            filtertabel_md(o),
            f"### Spor {spor} — scorefordeling\n",
            scoretabel_md(o),
            f"### Spor {spor} — kumulativt, score ≥ k\n",
            kumulativtabel_md(o),
            f"### Spor {spor} — brud på struktur alene\n",
            f"Signaler hvor kriterium 1 er sandt: "
            f"{_n(o[('brud_alene', 'alle', ALLE, KOL[0], 'signaler_n')])}. "
            f"`dage_med_signal_n`: "
            f"{_n(o[('brud_alene', 'alle', ALLE, KOL[0], 'dage_med_signal_n')])} af "
            f"{meta['rth_dage_n']} RTH-dage, "
            f"{_andel(o, ('brud_alene', 'alle', ALLE, KOL[0]), 'dage_med_signal_pct')}%.\n",
            f"### Spor {spor} — samvariation, phi for alle 21 par\n",
            samvariation_md(tab),
            f"### Spor {spor} — omkostninger\n",
            "Populationen er signalerne. `risiko_pt` er E − low (supply: high − E) på "
            "zonens rigtige historiske priser, trin A §4d. `zoner_i_vindue_n` og "
            "`afvist_kontrakter_nul_n` er før `kontrakter_ekte ≥ 1`.\n",
            omkostningstabel_md(o, ["alle"] + [str(a) for a in aar]),
            f"### Spor {spor} — kumulativt pr. år, `dage_med_signal_n`\n",
            kumulativ_aar_md(o, aar),
        ]
    dele += [
        "## Forventningen, §6 — ikke et kriterium\n",
        meta["forventning"],
        "## Efter kørslen\n",
        "Stop. Ingen ændring af definitionerne, ingen valg af tærskler — det gøres sammen "
        "med Mads efter §5.\n",
        f"Alle tal, også de 21 phi-værdier og alle årstal: `{meta['csv_navn']}` "
        "(langt format: `tabel`, `periode`, `side`, `noegle`, `stoerrelse`, `vaerdi`).\n",
    ]
    return "\n".join(dele)


def forventning_md(resultater: dict) -> str:
    """§6's forventninger holdt op mod de målte tal. Beskrivende, ikke et kriterium."""
    linjer = []
    for spor, res in resultater.items():
        o = res["opslag"]
        p = o.get(("samvariation", "alle", ALLE, "f5_stakket|f6_retning", "phi"),
                  float("nan"))
        stoerst = max(KOL, key=lambda k: o[("filtre", "alle", ALLE, k, "pct")])
        linjer.append(
            f"- **Spor {spor}:** phi(stakket, retning) = {_tal(p, 3)}; det hyppigste "
            f"filter er {stoerst.split('_', 1)[1]} med "
            f"{_tal(o[('filtre', 'alle', ALLE, stoerst, 'pct')])}%. Median `risiko_pt` "
            f"{_tal(o[('omkostninger', 'alle', ALLE, 'signaler', 'risiko_pt_p50')])} point, "
            f"median `omk_R_netto` "
            f"{_tal(o[('omkostninger', 'alle', ALLE, 'signaler', 'omk_R_netto_p50')], 4)}, "
            f"break-even-win-rate "
            f"{_tal(o[('omkostninger', 'alle', ALLE, 'signaler', 'be_WR_pct_netto_p50')], 2)}%, "
            f"p10 `risiko_pt` "
            f"{_tal(o[('omkostninger', 'alle', ALLE, 'signaler', 'risiko_pt_p10')])} point "
            f"med `omk_R_netto` p90 "
            f"{_tal(o[('omkostninger', 'alle', ALLE, 'signaler', 'omk_R_netto_p90')], 4)}.")
    return ("§6 forventede at filter 5 og 6 samvarierer mest, at filter 4 er sandt oftest, "
            "at de fleste signaler har score 1-3, og at score ≥ 4 har færre end 310 dage "
            "på spor A. For spor B forventedes median `risiko_pt` omkring 12 point mod 21 "
            "på spor A, median `omk_R_netto` omkring 0,11 mod 0,063 og break-even-win-rate "
            "omkring 37% mod 35%.\n\n" + "\n".join(linjer) + "\n")


# ---------------------------------------------------------------------------
# Kørslen
# ---------------------------------------------------------------------------

def _mnq() -> pd.DataFrame:
    """MNQ.v.0 1m, 2019-05-06 → 2023-12-31, kun gennem holdout-modulet."""
    df = holdout.load_in_sample(SYMBOL)
    return df[(df.index >= START) & (df.index < SLUT)]


def koer(df_1m: pd.DataFrame, dage: pd.DatetimeIndex, spor: tuple[str, ...]) -> dict:
    ud = {}
    for navn in spor:
        tf_min, htf_min = SPOR[navn]
        z, sig, meta = signaler_med_filtre(df_1m, tf_min, htf_min)
        tab = optael(sig, z, dage, meta)
        tab.insert(0, "spor", navn)
        ud[navn] = {"tabel": tab, "opslag": _opslag(tab), "meta": meta, "signaler": sig}
    return ud


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--regressionstjek", action="store_true",
                     help="§4's to tjek. Kører ikke optællingen")
    grp.add_argument("--koer", action="store_true",
                     help="§4: optællingen for begge spor. Skriver md og csv")
    ap.add_argument("--spor", choices=("A", "B", "begge"), default="begge")
    ap.add_argument("--ud", type=Path, default=None,
                    help="mappe til md og csv, standard research/output")
    args = ap.parse_args(argv)

    if args.regressionstjek:
        r = regressionstjek()
        print(f"1. b4_k1_optaelling_v2.csv byte for byte: "
              f"{'OK' if r['csv_byte_for_byte'] else 'AFVIGER'}")
        print(f"2. spor A's signaler {r['spor_a_signaler_n']} mod trin A's kandidater "
              f"{r['trin_a_kandidater_n']}: "
              f"{'identiske' if r['identiske'] else 'FORSKELLIGE'}")
        if not (r["csv_byte_for_byte"] and r["identiske"]):
            sys.exit(1)
        return

    commits = k1.committede(COMMITTEDE)
    head = _git("rev-parse", "HEAD").stdout.strip()
    df = _mnq()
    dage = k1.rth_dage(START, SLUT)
    regression = regressionstjek(df)
    if not (regression["csv_byte_for_byte"] and regression["identiske"]):
        raise RuntimeError(f"regressionstjekket fejler, optællingen køres ikke: {regression}")

    navne = ("A", "B") if args.spor == "begge" else (args.spor,)
    resultater = koer(df, dage, navne)
    tab = pd.concat([r["tabel"] for r in resultater.values()], ignore_index=True)

    ud = args.ud if args.ud is not None else OUT
    navn = "b4_k1_trin2_optaelling"
    meta = {
        "koert_utc": pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M"),
        "head": head, "commits": commits,
        "foerste_bar_utc": df.index[0].strftime("%Y-%m-%d %H:%M"),
        "sidste_bar_utc": df.index[-1].strftime("%Y-%m-%d %H:%M"),
        "n_1m": len(df), "rth_dage_n": len(dage), "dage": dage,
        "regression": regression, "csv_navn": f"{navn}.csv",
        "forventning": forventning_md(resultater),
    }
    ud.mkdir(parents=True, exist_ok=True)
    tab.to_csv(ud / f"{navn}.csv", index=False)
    md = skriv_md(resultater, meta)
    (ud / f"{navn}.md").write_text(md, encoding="utf-8")
    print(md)
    print(f"skrev {ud / navn}.md og .csv")


if __name__ == "__main__":
    main()
