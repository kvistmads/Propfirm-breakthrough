"""Tests for research/b4_k7_rebalancering.py — B4 kandidat 7, rebalancering.

Præregistreringen er ``research/prereg/b4_k7_rebalancering.md``. §11.3's 10 syntetiske tests
står først, i præregistreringens rækkefølge. Derefter det de bygger på:

- RV, σ_v, MDE og styrken i §7;
- beslutningsreglen i §8 og største tab i dagen;
- optællingen regner ingen P&L;
- hele den rigtige kørsel på syntetiske serier, så den ikke fejler første gang den køres.

Alle serier er syntetiske. Ingen test læser prisdata.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from research import b4_k2_nowick as k2
from research import b4_k7_rebalancering as k7

CT = "America/Chicago"
P_ES = 3900.0               # 7.800 / P = 2: dagens niveau er det dobbelte
P_NQ = 14569.0              # 29.138 / P = 2
P_ZN = 120.0


def _ct(dag, hhmm: str) -> pd.Timestamp:
    return pd.Timestamp(f"{pd.Timestamp(dag).date()} {hhmm}").tz_localize(CT).tz_convert("UTC")


def _xnys(fra: str, til: str) -> pd.DatetimeIndex:
    return k7.k1.rth_dage(fra, til)


class Bygger:
    """1m-barer fra 17:00 CT kalenderdagen før til 16:00 CT pr. XNYS-dag, fladt på P."""

    def __init__(self, dage, p: float = P_ES, rng: np.random.Generator | None = None,
                 sd: float = 1.0):
        dele = []
        for d in dage:
            idx = pd.date_range(_ct(pd.Timestamp(d) - pd.Timedelta(days=1), "17:00"),
                                _ct(d, "16:00"), freq="1min", inclusive="left").rename("time")
            dele.append(pd.DataFrame({"open": p, "high": p, "low": p, "close": p,
                                      "volume": 1.0, "instrument_id": np.int64(1)}, index=idx))
        self.df = pd.concat(dele)
        self.dage = pd.DatetimeIndex(list(dage))
        if rng is not None:
            c = p + np.cumsum(rng.normal(0, sd, len(self.df)))
            o = np.r_[p, c[:-1]]
            self.df["open"], self.df["close"] = o, c
            self.df["high"], self.df["low"] = np.maximum(o, c), np.minimum(o, c)

    def saet(self, t: pd.Timestamp, open_=None, close=None) -> "Bygger":
        if open_ is not None:
            self.df.loc[t, "open"] = open_
        if close is not None:
            self.df.loc[t, "close"] = close
        return self

    def flyt(self, fra: pd.Timestamp, delta: float) -> "Bygger":
        s = self.df.index >= fra
        for k in ("open", "high", "low", "close"):
            self.df.loc[s, k] += delta
        return self

    def fjern(self, fra: pd.Timestamp, til: pd.Timestamp) -> "Bygger":
        self.df = self.df[(self.df.index < fra) | (self.df.index >= til)]
        return self

    def rul(self, fra: pd.Timestamp, spring: float) -> "Bygger":
        self.flyt(fra, spring)
        self.df.loc[self.df.index >= fra, "instrument_id"] = 2
        return self


def _dag(h: k7.Handel, d: str) -> int:
    return int(np.flatnonzero(h.dage == pd.Timestamp(d))[0])


# ===========================================================================
# §11.3: de 10 syntetiske tests
# ===========================================================================

def test_1_taerskel_drift_rebalancering_og_middel_af_26_baand():
    R_es = np.array([np.nan, 0.10, 0.0, -0.02, 0.01])
    R_zn = np.array([np.nan, 0.0, 0.0, 0.01, 0.0])
    s = k7.taerskel_signal(R_es, R_zn)
    assert s.shape == (5, 26) and np.isnan(s[0]).all()
    w1 = 0.6 * 1.1 / (0.6 * 1.1 + 0.4)
    assert s[1] == pytest.approx(np.full(26, w1 - 0.6))       # samme drift fra 0,60
    # δ = 0 rebalancerer hver dag: signalet er dagens drift alene
    for t in range(1, 5):
        a = 0.6 * (1 + R_es[t])
        assert s[t, 0] == pytest.approx(a / (a + 0.4 * (1 + R_zn[t])) - 0.6)
    # dag 2 uden afkast: bånd under 0,0226 er rebalanceret (0), de øvrige bærer driften
    assert abs(s[1, 0]) > 0.022 and abs(s[1, -1]) < 0.025
    under = k7.BAAND <= abs(s[1, 0])
    assert s[2][under] == pytest.approx(0.0, abs=1e-15)
    assert s[2][~under] == pytest.approx(np.full((~under).sum(), w1 - 0.6))
    # rebalancering også ved lighed: et bånd præcis på |s|
    lig = np.array([0.5, abs(s[1, 0])])
    s2 = k7.taerskel_signal(R_es, R_zn, baand=lig)
    assert s2[2, 1] == 0.0 and s2[2, 0] == pytest.approx(w1 - 0.6)
    # T er middel af de 26 bånd, positivt når aktierne er overvægtede
    sig = k7.signal_fra_afkast(R_es, R_zn, _xnys("2018-03-01", "2018-03-08"))
    assert sig.T == pytest.approx(s.mean(axis=1), nan_ok=True)
    assert len(k7.BAAND) == 26 and k7.BAAND[-1] == 0.025 and sig.T[1] > 0


def test_2_kalender_drift_siden_maanedsslut_ogsaa_ved_helligdag():
    # Marts 2018: 30. er langfredag, så månedens sidste XNYS-dag er torsdag 29.
    dage = _xnys("2018-03-26", "2018-04-05")
    sidste = k7.maanedsslut(dage)
    assert list(dage[sidste].date.astype(str)) == ["2018-03-29"]
    R_es = np.array([np.nan, 0.01, 0.02, 0.0, 0.01, 0.0, 0.0, 0.0])[:len(dage)]
    R_zn = np.zeros(len(dage))
    c = k7.kalender_signal(R_es, R_zn, sidste)
    w = 0.6
    forventet = [np.nan]
    for t in range(1, len(dage)):
        a = w * (1 + R_es[t])
        wt = a / (a + (1 - w))
        forventet.append(wt - 0.6)                 # før rebalanceringen
        w = 0.6 if sidste[t] else wt
    assert c == pytest.approx(np.array(forventet), nan_ok=True)
    i = int(np.flatnonzero(sidste)[0])
    assert c[i] > 0                                # signalet den dag er før rebalanceringen
    assert c[i + 1] == pytest.approx(0.6 * 1.01 / (0.6 * 1.01 + 0.4) - 0.6)  # kun 3. april


def test_3_k_positioner():
    dage = _xnys("2018-03-01", "2018-05-01")
    efter, foer = k7.maanedens_plads(dage)
    c = np.linspace(-0.01, 0.02, len(dage))
    c[np.flatnonzero(dage == pd.Timestamp("2018-03-27"))[0]] = 0.0     # signal 0
    w = k7.position_K(c, efter, foer)
    marts5 = [str(x.date()) for x in dage[(dage.month == 3)][-5:]]
    assert marts5 == ["2018-03-23", "2018-03-26", "2018-03-27", "2018-03-28", "2018-03-29"]
    for i, d in enumerate(dage):
        ds = str(d.date())
        if ds == "2018-03-27":
            assert w[i] == 0.0
        elif ds in marts5 or ds in [str(x.date()) for x in dage[dage.month == 4][-5:]]:
            assert w[i] == np.sign(-c[i])
        elif ds == "2018-04-02":                    # månedens første: sign(c_(t−4))
            j = int(np.flatnonzero(dage == pd.Timestamp("2018-03-26"))[0])
            assert i - 4 == j and w[i] == np.sign(c[j])
        else:
            assert w[i] == 0.0, ds
    # 1. marts er månedens første, men c_(t−4) ligger før serien: 0
    assert w[0] == 0.0


def test_4_t_position():
    T = np.array([0.015, -0.0075, 0.0, np.nan])
    w = k7.position_T(T)
    assert w[:3] == pytest.approx([-1.0, 0.5, 0.0])
    assert np.isnan(w[3])


def test_5_signalets_tid_kortdag_rulle_og_intet_efter_rth_slut():
    dage = _xnys("2018-11-20", "2018-11-27")      # 23. er kortdag (RTH-slut 12:00 CT)
    assert [str(d.date()) for d in dage] == ["2018-11-20", "2018-11-21", "2018-11-23",
                                             "2018-11-26"]
    es, zn = Bygger(dage), Bygger(dage, P_ZN)
    for b, p in ((es, P_ES), (zn, P_ZN)):
        b.saet(_ct("2018-11-21", "14:59"), close=p * 1.01)
        b.saet(_ct("2018-11-21", "15:00"), close=p * 5)          # efter RTH-slut
        b.saet(_ct("2018-11-23", "11:59"), close=p * 1.02)       # kortdagens signalbar
        b.saet(_ct("2018-11-23", "12:00"), close=p * 7)
    # rul i ES efter signalet 23., så ingen spring i afkastet til 26.
    es.rul(_ct("2018-11-25", "17:00"), 50.0)
    # ZN mangler signalbaren 20.: baren kl. 14:58 bruges og tælles
    zn.fjern(_ct("2018-11-20", "14:59"), _ct("2018-11-20", "15:00"))
    sig = k7.byg_signal(es.df, zn.df, dage)
    assert sig.info["signalbar_mangler_ZN_n"] == 1 and sig.info["signalbar_mangler_ES_n"] == 0
    assert sig.info["signalbar_mangler_ZN_dage"] == ["2018-11-20"]
    assert np.isnan(sig.R_es[0])
    assert sig.R_es[1] == pytest.approx(0.01)
    assert sig.R_es[2] == pytest.approx((1.02 - 1.01) * P_ES / (1.01 * P_ES))
    # 26.: close er P + 50 i ny kontrakt; justeret har 23. close 1,02P + 50
    assert sig.R_es[3] == pytest.approx((P_ES - 1.02 * P_ES) / (1.02 * P_ES))
    assert sig.R_zn[1] == pytest.approx(0.01)
    i, f = k7.signal_close(k7._ns(es.df.index), dage)
    t_ct = es.df.index[i].tz_convert(CT)
    assert [x.strftime("%H:%M") for x in t_ct] == ["14:59", "14:59", "11:59", "14:59"]
    assert (f == 0).all()
    # en ændring efter RTH-slut på t flytter ikke signalet
    es2 = Bygger(dage)
    es2.saet(_ct("2018-11-21", "14:59"), close=P_ES * 1.01)
    es2.saet(_ct("2018-11-21", "15:30"), close=P_ES * 3).saet(_ct("2018-11-21", "16:00"),
                                                              open_=P_ES * 3)
    sig2 = k7.byg_signal(es2.df, Bygger(dage, P_ZN).df, dage)
    assert sig2.R_es[1] == pytest.approx(0.01)


def test_6_topstep_dagen_udfoerelse_og_manglende_barer():
    dage = _xnys("2018-11-15", "2018-11-30")
    b = Bygger(dage)
    # mandag 19.: indgang søndag 17:00, udgang 15:08
    b.saet(_ct("2018-11-18", "17:00"), open_=P_ES + 1).saet(_ct("2018-11-19", "15:08"),
                                                             open_=P_ES + 4)
    # tirsdag 20.: indgang 4 min forsinket (med), udgangsbaren mangler, 15:06 bruges (close)
    b.fjern(_ct("2018-11-19", "17:00"), _ct("2018-11-19", "17:04"))
    b.saet(_ct("2018-11-19", "17:04"), open_=P_ES + 2)
    b.fjern(_ct("2018-11-20", "15:07"), _ct("2018-11-20", "15:09"))
    b.saet(_ct("2018-11-20", "15:06"), close=P_ES + 6)
    # onsdag 21.: indgang 6 min forsinket → udelukket
    b.fjern(_ct("2018-11-20", "17:00"), _ct("2018-11-20", "17:06"))
    # fredag 23. kortdag: udgang 11:58
    b.saet(_ct("2018-11-23", "11:58"), open_=P_ES + 3)
    # mandag 26.: udgangsbar mangler, og seneste bar er over 5 min før → udelukket
    b.fjern(_ct("2018-11-26", "15:02"), _ct("2018-11-26", "15:09"))
    # tirsdag 27.: udgang mangler, seneste bar præcis 5 min før → med
    b.fjern(_ct("2018-11-27", "15:04"), _ct("2018-11-27", "15:09"))
    b.saet(_ct("2018-11-27", "15:03"), close=P_ES - 2)
    h = k7.byg_handel(b.df, dage, k7.ES)
    t = lambda i: pd.Timestamp(h.t_ns[i], tz="UTC").tz_convert(CT).strftime("%Y-%m-%d %H:%M")
    j = _dag(h, "2018-11-19")
    assert t(h.ind[j]) == "2018-11-18 17:00" and t(h.ud[j]) == "2018-11-19 15:08"
    assert h.praecis[j] and h.pt[j] == pytest.approx(3.0) and h.med[j]
    j = _dag(h, "2018-11-20")
    assert h.f_ind[j] == 4 and h.med[j] and not h.praecis[j]
    assert t(h.ud[j]) == "2018-11-20 15:06" and h.pt[j] == pytest.approx(4.0)
    j = _dag(h, "2018-11-21")
    assert not h.med[j] and h.grund[j] == "indgang over 5 min forsinket"
    j = _dag(h, "2018-11-23")
    assert t(h.ud[j]) == "2018-11-23 11:58" and h.pt[j] == pytest.approx(3.0)
    j = _dag(h, "2018-11-26")
    assert not h.med[j] and h.grund[j] == "udgang mangler (over 5 min)"
    j = _dag(h, "2018-11-27")
    assert h.med[j] and h.f_ud[j] == 5 and h.pt[j] == pytest.approx(-2.0)
    assert h.info["indgang_forsinket_1_5_n"] == 1 and h.info["udgang_tidligere_bar_n"] == 2
    # udelukkede dage er udelukket i alle varianter og i N-retning
    w = np.ones(len(dage))
    assert not k7.dag_pnl(h, w)["aktiv"][_dag(h, "2018-11-21")]


def test_7_normering_og_omkostning_ogsaa_nasdaq():
    dage = _xnys("2018-06-11", "2018-06-15")
    b = Bygger(dage)
    b.saet(_ct("2018-06-12", "15:08"), open_=P_ES + 10)       # d = 12.: Δpt = 10
    h = k7.byg_handel(b.df, dage, k7.ES)
    assert (h.L == P_ES).all() and h.skala == pytest.approx(2.0)
    w = np.array([-0.5, 0.0, 0.25, 0.0])                      # signaldag 11. → d 12.
    p = k7.dag_pnl(h, w)
    j = _dag(h, "2018-06-12")
    assert p["brutto"][j] == pytest.approx(-0.5 * 10 * 2 * 5)
    assert p["netto"][j] == pytest.approx(-0.5 * 10 * 2 * 5 - 0.5 * 4.45)
    assert p["nominelt"][j] == pytest.approx(-0.5 * 10 * 5 - 0.5 * 4.45)
    assert not p["aktiv"][_dag(h, "2018-06-13")]
    assert p["netto"][_dag(h, "2018-06-14")] == pytest.approx(-0.25 * 4.45)
    assert 4.45 / (7800 * 5) * 1e4 == pytest.approx(1.14, abs=0.005)       # §4f
    nq = Bygger(dage, P_NQ)
    nq.saet(_ct("2018-06-12", "15:08"), open_=P_NQ + 10)
    hn = k7.byg_handel(nq.df, dage, k7.NQ)
    pn = k7.dag_pnl(hn, w)
    assert pn["netto"][j] == pytest.approx(-0.5 * 10 * 2 * 2 - 0.5 * 2.85)


def test_8_n_retning_samme_abs_w_deterministisk_og_delt():
    dage = _xnys("2018-06-01", "2018-07-10")
    h = k7.byg_handel(Bygger(dage, rng=np.random.default_rng(1)).df, dage, k7.ES)
    s0 = k7.fortegn(3, h.n)
    assert set(np.unique(s0)) <= {-1, 1}
    assert (s0 == k7.fortegn(3, h.n)).all() and not (s0 == k7.fortegn(4, h.n)).all()
    wT = np.linspace(-1, 1, len(dage))
    wK = np.where(np.arange(len(dage)) % 3 == 0, -1.0, 0.0)
    r = k7.nret_gentagelse(h, {"T": wT, "K": wK}, 3)
    G = h.G
    for navn, w in (("T", wT), ("K", wK)):
        a = np.abs(w[h.t_pos])
        m = h.med & (a != 0)
        assert r[navn] == pytest.approx(np.mean((s0 * a * G - a * 4.45)[m]))
    # samme fortegn på de dage T og K deler: K-netto med |w| = 1 læser samme række
    r1 = k7.nret_gentagelse(h, {"a": np.ones(len(dage)), "b": -np.ones(len(dage))}, 3)
    assert r1["a"] == pytest.approx(r1["b"])           # fortegnet afhænger ikke af w's fortegn


def test_9_westfall_young_og_p_fwe_som_kandidat_2():
    rng = np.random.default_rng(5)
    null = {v: rng.normal(0, 1 + i, 500) for i, v in enumerate(k7.VARIANTER)}
    obs = {"T": 3.0, "K": 0.5}
    wy = k2.westfall_young(obs, null)
    M = np.column_stack([null[v] for v in k7.VARIANTER])
    med, sd = np.median(M, axis=0), M.std(axis=0, ddof=1)
    maks = ((M - med) / sd).max(axis=1)
    for i, v in enumerate(k7.VARIANTER):
        t = (obs[v] - med[i]) / sd[i]
        assert wy["pr_variant"][v]["t"] == pytest.approx(t)
        assert wy["pr_variant"][v]["p_FWE"] == pytest.approx((1 + (maks >= t).sum()) / 501)
    # analysen bruger netop den funktion på middel netto mod N-retning
    h, sig = _syntetisk()
    res = k7.analyse(h, sig, n_reps=7)
    ws = k7.positioner(sig)
    null = [k7.nret_gentagelse(h, {v: ws[v] for v in k7.VARIANTER}, r) for r in range(7)]
    wy = k2.westfall_young({v: res["tal"][v]["middel_netto_usd"] for v in k7.VARIANTER},
                           {v: np.array([r[v] for r in null]) for v in k7.VARIANTER})
    for v in k7.VARIANTER:
        assert res["tal"][v]["p_FWE"] == wy["pr_variant"][v]["p_FWE"]
    assert res["wy"]["R"] == 7


def test_10_opvarmning_ingen_handelsdage_foer_2016_04_01():
    dage = _xnys("2016-03-21", "2016-04-12")
    tp = k7.handelsdage(dage)
    assert str(dage[tp[0]].date()) == "2016-03-31"            # t
    assert str(dage[tp[0] + 1].date()) == "2016-04-01"        # d
    assert (dage[tp + 1] >= pd.Timestamp("2016-04-01")).all()
    h = k7.byg_handel(Bygger(dage).df, dage, k7.ES)
    assert h.dage.min() == pd.Timestamp("2016-04-01")
    # hele in-sample: første handelsdag 2016-04-01, sidste 2023-12-29
    alle = k7.signal_dage()
    tp = k7.handelsdage(alle)
    assert str(alle[tp[0] + 1].date()) == "2016-04-01" and str(alle[0].date()) == "2016-01-04"
    assert str(alle[tp[-1] + 1].date()) == "2023-12-29"


# ===========================================================================
# Det testene bygger på
# ===========================================================================

def _syntetisk():
    dage = _xnys("2016-03-21", "2016-05-10")
    rng = np.random.default_rng(11)
    es = Bygger(dage, rng=rng, sd=0.5)
    zn = Bygger(dage, P_ZN, rng=rng, sd=0.01)
    sig = k7.byg_signal(es.df, zn.df, dage)
    return k7.byg_handel(es.df, dage, k7.ES), sig


def test_rv_sigma_mde_og_styrke():
    dage = _xnys("2018-06-11", "2018-06-15")
    h = k7.byg_handel(Bygger(dage, rng=np.random.default_rng(3)).df, dage, k7.ES)
    r = k7.rv(h)
    for j in range(h.n):
        i0, i1 = h.ind[j], h.ud[j]
        sti = np.r_[h.o[i0], h.c[i0:i1], h.o[i1]]
        assert r[j] == pytest.approx((np.diff(sti) ** 2).sum() * (h.skala[j] * 5) ** 2)
    w = np.array([0.5, -1.0, 0.0, 2.0])
    wd = w[h.t_pos]
    m = wd != 0
    assert k7.sigma_v(h, w) == pytest.approx(math.sqrt(np.mean((wd ** 2 * r)[m])))
    assert k7.mde(430.0, 558) == pytest.approx(2.7961 * 430 / math.sqrt(558))
    assert round(k7.mde(430.0, 558)) == 51                     # §7's overslag
    sig, n = 300.0, 1950
    assert k7.styrke_fwe(sig, n, k7.mde(sig, n)) == pytest.approx(0.80, abs=2e-4)
    assert k7.styrke_ci(sig, n, k7.mde(sig, n, k7.Z_CI) + 1.3, 1.3) == pytest.approx(
        0.80, abs=2e-4)


def test_beslutning_alle_raekker():
    def r(p, lo):
        return {"p_FWE": p, "ci95_lo": lo}
    alle = {v: r(0.5, -1.0) for v in k7.VARIANTER}
    assert k7.beslutning(alle)["raekke"] == 4
    assert k7.beslutning({**alle, "T": r(0.5, 0.1)})["raekke"] == 3
    afg = k7.beslutning({"T": r(0.04, -0.1), "K": r(0.5, 0.2)})
    assert afg["raekke"] == 2 and afg["in_sample_fund"] == ["K"]
    afg = k7.beslutning({"T": r(0.01, 0.5), "K": r(0.05, 1.5)})
    assert afg["raekke"] == 1 and afg["variant"] == "K"
    assert k7.beslutning({**alle, "K": r(0.05, 0.0)})["raekke"] == 2


def test_stoerste_tab_i_dagen():
    dage = _xnys("2018-06-11", "2018-06-14")
    b = Bygger(dage)
    b.saet(_ct("2018-06-12", "09:00"), close=P_ES + 4)
    h = k7.byg_handel(b.df, dage, k7.ES)
    wd = np.array([-0.5, 1.0, 1.0])[h.t_pos]
    tab = k7.stoerste_tab(h, wd, h.med)
    assert tab[_dag(h, "2018-06-12")] == pytest.approx(-4 * 2 * 5 - 4.45)   # short pr. enhed
    assert tab[_dag(h, "2018-06-13")] == pytest.approx(-4.45)


def test_optaellingen_regner_ingen_pnl():
    h, sig = _syntetisk()
    o = k7.optaelling(h, sig)
    noegler = set(o) | set(o["serie"]) | {k for r in o["varianter"] for k in r} \
        | {k for r in o["aar"] for k in r}
    for ord_ in ("brutto", "netto", "hit", "pt", "p_FWE", "raekke", "gevinst"):
        assert not any(ord_ in k for k in noegler), ord_
    assert {r["variant"] for r in o["varianter"]} == set(k7.VARIANTER)


def test_hele_koerslen_paa_syntetiske_serier():
    h, sig = _syntetisk()
    dage = sig.dage
    nq = k7.byg_handel(Bygger(dage, P_NQ, rng=np.random.default_rng(12)).df, dage, k7.NQ)
    k6n = pd.Series(np.random.default_rng(13).normal(0, 50, len(h.dage)), index=h.dage)
    res = {k7.ES: k7.analyse(h, sig, 5, k6n), k7.NQ: k7.analyse(nq, sig, 5, k6n)}
    for v in k7.VARIANTER:
        assert res[k7.ES]["tal"][v]["aktive_dage_n"] > 0
        assert np.isfinite(res[k7.ES]["tal"][v]["MDE_sidak2"])
    meta = {"koert_utc": "2026-01-01 00:00", "head": "0" * 40}
    md = k7.skriv_md(res, meta)
    assert "Hovedtabel" in md and "§8 anvendt mekanisk" in md
    df = k7.lang_tabel(res)
    assert {"hoved", "diagnose", "aar", "lang"} <= set(df["tabel"])


def test_reversal_diagnose_ols_hc3_kendt_haeldning():
    """Tillæggets §4: OLS med HC3 genfinder en kendt hældning på syntetiske data."""
    rng = np.random.default_rng(21)
    n = 4000
    x1, x2 = rng.normal(0, 2, n), rng.normal(0, 1, n)
    y = 3.0 - 16.5 * x1 / x1.std(ddof=1) + 4.0 * x2 + rng.normal(0, 1, n) * (1 + np.abs(x1))
    r = k7.ols_hc3(y, np.column_stack([x1 / x1.std(ddof=1), x2]))
    assert r["n"] == n
    assert r["beta"] == pytest.approx([3.0, -16.5, 4.0], abs=0.25)
    assert (r["lo"] < [3.0, -16.5, 4.0]).all() and (r["hi"] > [3.0, -16.5, 4.0]).all()
    # HC3 mod den eksplicitte formel
    X = np.column_stack([np.ones(n), x1 / x1.std(ddof=1), x2])
    B = np.linalg.inv(X.T @ X)
    e = y - X @ (B @ X.T @ y)
    hii = np.array([X[i] @ B @ X[i] for i in range(n)])
    V = B @ (X.T * (e / (1 - hii)) ** 2) @ X @ B
    assert r["se"] == pytest.approx(np.sqrt(np.diag(V)))
    # diagnosen kører på syntetiske serier og giver alle fire regressioner
    h, sig = _syntetisk()
    rd = k7.reversal_diagnose(h, sig)
    assert {"T_uden", "T_med", "c_uden", "c_med", "korr_wK_R_es"} <= set(rd)
    assert rd["T_uden"]["n"] == int(h.med.sum()) and "b_E" in rd["T_med"]
