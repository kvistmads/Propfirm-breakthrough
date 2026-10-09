"""Tests for research/b4_k6_overnight.py — B4 kandidat 6, overnight drift.

Præregistreringen er ``research/prereg/b4_k6_overnight.md``. §11.2's 9 syntetiske tests
står først, i præregistreringens rækkefølge. Derefter det de bygger på:

- σ_nat, MDE og styrken i §7;
- beslutningsreglen i §8 og største tab i vinduet;
- optællingen regner ingen P&L;
- hele den rigtige kørsel på en syntetisk serie, så den ikke fejler første gang den køres.

Alle serier er syntetiske. Ingen test læser prisdata.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from research import b4_k2_nowick as k2
from research import b4_k6_overnight as k6

CT = "America/Chicago"
NYZ = "America/New_York"
P = 14569.0                 # 29.138 / P = 2: dagens niveau er det dobbelte
TIR, ONS, TOR = "2023-06-13", "2023-06-14", "2023-06-15"
V1A, V1S, V2A, V2S = k6.VARIANTER


def _ct(dag: str, hhmm: str) -> pd.Timestamp:
    return pd.Timestamp(f"{dag} {hhmm}").tz_localize(CT).tz_convert("UTC")


def _dagen_foer(dag: str) -> str:
    return str((pd.Timestamp(dag) - pd.Timedelta(days=1)).date())


class Bygger:
    """1m-barer fra 17:00 CT dagen før til 15:15 CT pr. dag, fladt på P i kontrakt 1."""

    def __init__(self, dage, rng: np.random.Generator | None = None):
        dele = []
        for d in dage:
            idx = pd.date_range(_ct(_dagen_foer(d), "17:00"), _ct(d, "15:15"), freq="1min",
                                inclusive="left").rename("time")
            dele.append(pd.DataFrame({"open": P, "high": P, "low": P, "close": P,
                                      "volume": 1.0, "instrument_id": np.int64(1)}, index=idx))
        self.df = pd.concat(dele)
        self.dage = pd.DatetimeIndex(list(dage))
        if rng is not None:                   # random walk: open = forrige close
            c = P + np.cumsum(rng.normal(0, 2.0, len(self.df)))
            o = np.r_[P, c[:-1]]
            self.df["open"], self.df["close"] = o, c
            self.df["high"] = np.maximum(o, c)
            self.df["low"] = np.minimum(o, c)

    def saet(self, t: pd.Timestamp, open_=None, close=None) -> "Bygger":
        if open_ is not None:
            self.df.loc[t, "open"] = open_
        if close is not None:
            self.df.loc[t, "close"] = close
        return self

    def fjern(self, fra: pd.Timestamp, til: pd.Timestamp) -> "Bygger":
        """Fjerner barerne i [fra, til)."""
        self.df = self.df[(self.df.index < fra) | (self.df.index >= til)]
        return self

    def rul(self, fra: pd.Timestamp, spring: float) -> "Bygger":
        s = self.df.index >= fra
        for k in ("open", "high", "low", "close"):
            self.df.loc[s, k] += spring
        self.df.loc[s, "instrument_id"] = 2
        return self

    def g(self) -> k6.Grundlag:
        return k6.byg_grundlag(self.df, self.dage, "syntetisk")


def _nat(g: k6.Grundlag, dag: str) -> int:
    return int(g.dage.get_loc(pd.Timestamp(dag)))


def _tid(g: k6.Grundlag, i) -> pd.Timestamp:
    return pd.Timestamp(int(g.t_ns[i]), tz="UTC")


# ===========================================================================
# §11.2: de 9 syntetiske tests
# ===========================================================================

def test_1_natten_og_forrige_rth_dag():
    """Natten før d går fra 17:00 CT dagen før til 08:30 CT på d. Mandagsnatten hører til
    mandag og starter søndag; forrige RTH-dag er fredag. Efter en mandagshelligdag er
    forrige RTH-dag fredagen før."""
    dage = pd.DatetimeIndex(["2023-06-12", "2023-06-14", "2023-05-30", "2023-01-03"])
    nt = k6.naetter(dage)
    start = nt["start"].dt.tz_convert(CT)
    slut = nt["slut"].dt.tz_convert(CT)
    assert list(start.dt.strftime("%Y-%m-%d %H:%M")) == [
        "2023-06-11 17:00", "2023-06-13 17:00", "2023-05-29 17:00", "2023-01-02 17:00"]
    assert list(slut.dt.strftime("%Y-%m-%d %H:%M")) == [
        "2023-06-12 08:30", "2023-06-14 08:30", "2023-05-30 08:30", "2023-01-03 08:30"]
    assert list(nt["forrige"].dt.strftime("%Y-%m-%d")) == [
        "2023-06-09", "2023-06-13", "2023-05-26", "2022-12-30"]
    assert start.iloc[0].day_name() == "Sunday"

    g = Bygger(["2023-06-12"]).g()
    assert _tid(g, g.pkt["nat_ind"][0][0]) == _ct("2023-06-11", "17:00")
    assert _tid(g, g.pkt["nat_ud"][0][0]) == _ct("2023-06-12", "08:30")
    assert g.forrige[0] == pd.Timestamp("2023-06-09")


@pytest.mark.parametrize("dag,dk_offset", [
    ("2023-01-11", 6), ("2023-03-10", 6),      # vinter
    ("2023-03-13", 5), ("2023-03-20", 5),      # USA har skiftet, Europa ikke
    ("2023-03-27", 6), ("2023-07-12", 6),      # begge sommertid
    ("2023-10-30", 5), ("2023-11-03", 5),      # Europa tilbage, USA ikke
    ("2023-11-06", 6),                         # begge vintertid
])
def test_2_vinduerne_i_new_york_tid_hele_aaret(dag, dk_offset):
    """V1 og V2 ligger i New York-tid hele året, også i skifteugerne. CT er altid én time
    før, og dansk tid er New York + 6 timer, i skifteugerne + 5."""
    for w, (a, b) in (("V1", ("02:00", "03:00")), ("V2", ("01:30", "03:30"))):
        ind, ud = k6.vindue_tider(pd.DatetimeIndex([dag]), w)
        for t, hhmm in ((ind[0], a), (ud[0], b)):
            ny = t.tz_convert(NYZ)
            assert ny.strftime("%Y-%m-%d %H:%M") == f"{dag} {hhmm}"
            assert (ny.tz_localize(None) - t.tz_convert(CT).tz_localize(None)) == \
                pd.Timedelta(hours=1)
            assert (t.tz_convert("Europe/Copenhagen").tz_localize(None)
                    - ny.tz_localize(None)) == pd.Timedelta(hours=dk_offset)
    assert k6.vindue_min("V1") == (480, 540)
    assert k6.vindue_min("V2") == (450, 570)


def test_3_indgang_udgang_manglende_bar_og_forsinkelse():
    """Indgang og udgang ved barernes open. Mangler en bar, bruges den næste. Præcis 5
    minutter er med; over 5 udelukker natten i alle varianter og i nulmodellen."""
    b = Bygger([TIR, ONS, TOR])
    b.saet(_ct(ONS, "01:00"), open_=P + 1).saet(_ct(ONS, "02:00"), open_=P + 11)
    g = b.g()
    h = k6.handel(g, "V1")
    n = _nat(g, ONS)
    assert _tid(g, h["ind"][n]) == _ct(ONS, "01:00")
    assert _tid(g, h["ud"][n]) == _ct(ONS, "02:00")
    assert h["pt"][n] == 10.0

    # indgangsbaren mangler 3 minutter: open af 01:03-baren, tælles som forsinket
    b = Bygger([TIR, ONS, TOR]).fjern(_ct(ONS, "01:00"), _ct(ONS, "01:03"))
    b.saet(_ct(ONS, "01:03"), open_=P + 3).saet(_ct(ONS, "02:00"), open_=P + 11)
    g = b.g()
    n = _nat(g, ONS)
    ind, f = g.pkt["V1_ind"]
    assert _tid(g, ind[n]) == _ct(ONS, "01:03") and f[n] == 3.0
    assert k6.handel(g, "V1")["pt"][n] == 8.0
    assert g.med.all()
    o = k6.optaelling(g)
    assert {r["variant"]: r["forsinket_ind_n"] for r in o["varianter"]}["V1 · alle"] == 1

    # præcis 5 minutter er med
    g = Bygger([TIR, ONS, TOR]).fjern(_ct(ONS, "02:00"), _ct(ONS, "02:05")).g()
    assert g.med.all() and g.pkt["V1_ud"][1][_nat(g, ONS)] == 5.0

    # 6 minutter ved V1's udgang udelukker natten i alle 4 varianter og i N-nat
    g = Bygger([TIR, ONS, TOR]).fjern(_ct(ONS, "02:00"), _ct(ONS, "02:06")).g()
    n = _nat(g, ONS)
    assert not g.med[n] and g.grund[n] == "bar over 5 min forsinket"
    g.salg[:] = 1.0
    for v in k6.VARIANTER:
        assert not g.maske(v)[n]
        assert g.maske(v).sum() == 2
    nvs = k6.forbered_nnat(g)
    null = k6.nnat_gentagelse(g, nvs, 0)
    # N-nat regner kun på de nætter, der indgår
    for w, nv in nvs.items():
        valg = k6.nnat_traek(nv, 0, behov=g.med)
        netto = nv.brutto[np.arange(len(valg)), np.maximum(valg, 0)] - k6.OMK_USD
        assert null[(w, k6.ALLE)] == pytest.approx(netto[g.med].mean())

    # et vindue uden barer: grunden skrives
    g = Bygger([TIR, ONS, TOR]).fjern(_ct(ONS, "00:00"), _ct(ONS, "04:00")).g()
    assert g.grund[_nat(g, ONS)] == "ingen barer i et vindue"


def test_4_salgsdag_ogsaa_paa_kortdage():
    """§4c: close af sidste RTH-bar < open af første. Lighed er ikke salg. På en kortdag
    slutter RTH kl. 12:00 CT, og barer efter tæller ikke."""
    b = Bygger([TIR, ONS, TOR])
    b.saet(_ct(TIR, "08:30"), open_=P).saet(_ct(TIR, "14:59"), close=P - 1)   # salg
    b.saet(_ct(ONS, "08:30"), open_=P).saet(_ct(ONS, "14:59"), close=P + 1)   # op
    b.saet(_ct(ONS, "15:10"), close=P - 50)                                   # efter RTH
    g = b.g()
    assert np.isnan(g.salg[_nat(g, TIR)])         # mandag er ikke i serien
    assert g.salg[_nat(g, ONS)] == 1.0            # forrige = tirsdag, salg
    assert g.salg[_nat(g, TOR)] == 0.0            # forrige = onsdag, op
    assert g.rth_afkast_pct[_nat(g, ONS)] == pytest.approx(-1 / P * 100)
    assert g.maske(V1S).tolist() == [False, True, False]
    assert g.maske(V1A).tolist() == [True, True, True]

    # lighed
    g = Bygger([TIR, ONS]).g()
    assert g.salg[_nat(g, ONS)] == 0.0

    # kortdag: fredag efter Thanksgiving lukker 12:00 CT
    KORT, MAN = "2023-11-24", "2023-11-27"
    b = Bygger([KORT, MAN])
    b.saet(_ct(KORT, "11:59"), close=P - 1).saet(_ct(KORT, "12:30"), close=P + 50)
    g = b.g()
    assert g.forrige[_nat(g, MAN)] == pd.Timestamp(KORT)
    assert g.salg[_nat(g, MAN)] == 1.0
    b = Bygger([KORT, MAN])
    b.saet(_ct(KORT, "11:59"), close=P + 1).saet(_ct(KORT, "14:59"), close=P - 50)
    g = b.g()
    assert g.salg[_nat(g, MAN)] == 0.0


def test_5_rulle_i_vinduet_forskelsjusteret_og_L_ujusteret():
    """En rulle inden i vinduet giver ikke springet med. L_n er den ujusterede open."""
    b = Bygger([TIR, ONS, TOR]).rul(_ct(ONS, "01:30"), 100.0)
    b.saet(_ct(ONS, "02:00"), open_=P + 100 + 5)
    g = b.g()
    n = _nat(g, ONS)
    h = k6.handel(g, "V1")
    assert h["pt"][n] == pytest.approx(5.0)
    assert h["L"][n] == P
    o = k6.optaelling(g)
    rul = {r["variant"]: r["ruller_i_vinduet_n"] for r in o["varianter"]}
    assert rul["V1 · alle"] == 1 and rul["V2 · alle"] == 1
    assert g.info["ruller_n"] == 1
    # efter rullen er L den nye kontrakts ujusterede open
    assert h["L"][_nat(g, TOR)] == P + 100


def test_6_normering_og_omkostning():
    """``netto = Δpt × (29.138 / L_n) × 2 − 2,85``. Ved L = 14.569 er skalaen 2."""
    b = Bygger([TIR, ONS])
    b.saet(_ct(ONS, "02:00"), open_=P + 10)
    g = b.g()
    n = _nat(g, ONS)
    h = k6.handel(g, "V1")
    assert h["skala"][n] == pytest.approx(2.0)
    assert h["brutto_usd"][n] == pytest.approx(10 * 2 * 2)
    assert h["netto_usd"][n] == pytest.approx(40 - 2.85)
    assert h["nominelt_usd"][n] == pytest.approx(20 - 2.85)
    t = k6.variant_tal(g, V1A, h)
    assert t["middel_netto_usd"] == pytest.approx(((40 - 2.85) + (0 - 2.85)) / 2)
    assert t["netto_usd_pr_kalendernat"] == pytest.approx(t["middel_netto_usd"])
    assert k6.OMK_USD == 2.85 and k6.NQ_NIVEAU == 29138.0


def test_7_nnat_i_natten_uden_overlap_samme_laengde_og_delt():
    """N-nat: vinduet ligger i natten, overlapper ikke variantens vindue og har samme
    længde. Samme (gentagelse, nat, længde) giver samme start i "alle" og "salg"."""
    for w, antal in (("V1", 752), ("V2", 572)):
        S = k6.nnat_starter(w)
        a, b_ = k6.vindue_min(w)
        L = b_ - a
        assert len(S) == antal
        assert S.min() >= 0 and (S + L).max() <= k6.NAT_MIN
        assert ((S + L <= a) | (S >= b_)).all()

    dage = [TIR, ONS, TOR]
    b = Bygger(dage, rng=np.random.default_rng(1))
    b.fjern(_ct(ONS, "18:00"), _ct(ONS, "23:00"))        # torsdagsnatten har et hul
    g = b.g()
    g.salg[:] = np.array([1.0, 0.0, 1.0])
    nvs = k6.forbered_nnat(g)
    for w, nv in nvs.items():
        L = k6.vindue_laengde(w)
        ind_ny, ud_ny = k6.vindue_tider(g.dage, w)
        for rep in range(5):
            valg = k6.nnat_traek(nv, rep, behov=g.med)
            assert (valg >= 0).all()
            assert (valg == k6.nnat_traek(nv, rep)).all()            # deterministisk
            s = nv.starter[valg]
            start = g.nat_start_ns + s * k6.MIN_NS
            slut = start + L * k6.MIN_NS
            assert (start >= g.nat_start_ns).all() and (slut <= g.nat_slut_ns).all()
            assert ((slut <= k6._ns(ind_ny)) | (start >= k6._ns(ud_ny))).all()
            assert nv.ok[np.arange(len(valg)), valg].all()            # kan udføres
            null = k6.nnat_gentagelse(g, nvs, rep)
            netto = nv.brutto[np.arange(len(valg)), valg] - k6.OMK_USD
            assert null[(w, k6.ALLE)] == pytest.approx(netto.mean())
            assert null[(w, k6.SALG)] == pytest.approx(netto[[0, 2]].mean())
        # hullet: ingen trukket start eller slut i 18:00-23:00 torsdagsnatten
        n = _nat(g, TOR)
        for rep in range(20):
            s = nv.starter[k6.nnat_traek(nv, rep)[n]]
            for m in (s, s + L):
                t = pd.Timestamp(int(g.nat_start_ns[n] + m * k6.MIN_NS), tz="UTC")
                assert not (_ct(ONS, "18:00") < t <= _ct(ONS, "22:55"))
    # gentagelser og længder trækkes forskelligt
    a0 = k6.nnat_traek(nvs["V1"], 0)
    assert any((k6.nnat_traek(nvs["V1"], r) != a0).any() for r in range(1, 5))


def test_8_lang_hele_natten():
    """Long fra open kl. 17:00 CT dagen før til open kl. 08:30 CT."""
    b = Bygger([TIR, ONS])
    b.saet(_ct(TIR, "17:00"), open_=P + 2).saet(_ct(ONS, "08:30"), open_=P + 7)
    g = b.g()
    n = _nat(g, ONS)
    hn = k6.lang_hele_natten(g)
    assert hn["udfoerbar"][n]
    assert hn["brutto_usd"][n] == pytest.approx(5 * (k6.NQ_NIVEAU / (P + 2)) * 2)
    assert hn["netto_usd"][n] == pytest.approx(hn["brutto_usd"][n] - 2.85)
    assert _tid(g, g.pkt["nat_ind"][0][n]) == _ct(TIR, "17:00")
    # 17:00-17:09 mangler: ikke udførbar, men natten indgår stadig i varianterne
    g = Bygger([TIR, ONS]).fjern(_ct(TIR, "17:00"), _ct(TIR, "17:10")).g()
    assert not k6.lang_hele_natten(g)["udfoerbar"][_nat(g, ONS)]
    assert g.med.all()


def test_9_westfall_young_og_p_fwe_som_kandidat_2():
    """Westfall-Young er ``k2.westfall_young`` uændret: t_v = (m_v − med_v) / sd_v og
    p_FWE = (1 + #{max t* ≥ t_v}) / (1 + R), énsidet."""
    rng = np.random.default_rng(5)
    null = {v: rng.normal(0, 1 + i, 500) for i, v in enumerate(k6.VARIANTER)}
    obs = {V1A: 3.0, V1S: 0.5, V2A: -1.0, V2S: 6.0}
    wy = k2.westfall_young(obs, null)
    M = np.column_stack([null[v] for v in k6.VARIANTER])
    med, sd = np.median(M, axis=0), M.std(axis=0, ddof=1)
    maks = ((M - med) / sd).max(axis=1)
    for i, v in enumerate(k6.VARIANTER):
        t = (obs[v] - med[i]) / sd[i]
        assert wy["pr_variant"][v]["t"] == pytest.approx(t)
        assert wy["pr_variant"][v]["p_FWE"] == pytest.approx((1 + (maks >= t).sum()) / 501)

    # analysen bruger netop den funktion på middel netto mod N-nat
    g = Bygger([TIR, ONS, TOR], rng=np.random.default_rng(2)).g()
    g.salg[:] = np.array([1.0, 0.0, 1.0])
    res = k6.analyse(g, n_reps=7)
    nvs = k6.forbered_nnat(g)
    null = [k6.nnat_gentagelse(g, nvs, r) for r in range(7)]
    wy = k2.westfall_young({v: res["tal"][v]["middel_netto_usd"] for v in k6.VARIANTER},
                           {v: np.array([r[v] for r in null]) for v in k6.VARIANTER})
    for v in k6.VARIANTER:
        assert res["tal"][v]["p_FWE"] == wy["pr_variant"][v]["p_FWE"]
        assert res["tal"][v]["t_v"] == wy["pr_variant"][v]["t"]
    assert res["wy"]["R"] == 7


# ===========================================================================
# Det testene bygger på
# ===========================================================================

def test_sigma_nat_mde_og_styrke():
    b = Bygger([TIR, ONS], rng=np.random.default_rng(3))
    g = b.g()
    ind, ud = g.pkt["V1_ind"][0], g.pkt["V1_ud"][0]
    s = []
    for n in range(g.n_alle):
        dc = np.array([g.c[i] - g.c[i - 1] for i in range(ind[n], ud[n])])
        s.append((k6.NQ_NIVEAU / g.o_raa[ind[n]]) ** 2 * (dc ** 2).sum())
    assert k6.sigma_nat(g, V1A) == pytest.approx(2 * math.sqrt(np.mean(s)))
    assert k6.mde(120.0, 2000) == pytest.approx(3.0756 * 120 / math.sqrt(2000))
    assert round(k6.mde(120.0, 2000), 1) == 8.3        # §7's tabel
    assert round(k6.mde(180.0, 1000), 1) == 17.5
    sig, n = 150.0, 2000
    assert k6.styrke_fwe(sig, n, k6.mde(sig, n)) == pytest.approx(0.80, abs=2e-4)
    assert k6.styrke_ci(sig, n, k6.mde(sig, n, k6.Z_CI) + 2.85) == pytest.approx(0.80, abs=2e-4)


def test_beslutning_alle_raekker():
    def r(p, lo):
        return {"p_FWE": p, "ci95_lo": lo}
    alle = {v: r(0.5, -1.0) for v in k6.VARIANTER}
    assert k6.beslutning(alle)["raekke"] == 4
    a = {**alle, V1A: r(0.5, 0.1)}
    assert k6.beslutning(a)["raekke"] == 3
    a = {**alle, V1A: r(0.04, -0.1), V2A: r(0.5, 0.2)}
    afg = k6.beslutning(a)
    assert afg["raekke"] == 2 and afg["in_sample_fund"] == [V2A]
    a = {**alle, V1S: r(0.01, 0.5), V2S: r(0.05, 1.5)}
    afg = k6.beslutning(a)
    assert afg["raekke"] == 1 and afg["variant"] == V2S
    a = {**alle, V1S: r(0.05, 0.0)}          # grænsen: CI-nedre = 0 er ikke > 0
    assert k6.beslutning(a)["raekke"] == 2


def test_stoerste_tab_i_vinduet():
    b = Bygger([TIR, ONS])
    b.saet(_ct(ONS, "01:20"), close=P - 4).saet(_ct(ONS, "02:00"), open_=P + 1)
    g = b.g()
    h = k6.handel(g, "V1")
    tab = k6.stoerste_tab(g, h, g.maske(V1A))
    assert tab[_nat(g, ONS)] == pytest.approx(-4 * 2 * 2 - 2.85)
    assert tab[_nat(g, TIR)] == pytest.approx(-2.85)


def test_optaellingen_regner_ingen_pnl():
    g = Bygger([TIR, ONS, TOR], rng=np.random.default_rng(4)).g()
    o = k6.optaelling(g, k6.forbered_nnat(g))
    noegler = set(o) | set(o["serie"]) | {k for r in o["varianter"] for k in r} \
        | {k for r in o["aar"] for k in r}
    for ord_ in ("brutto", "netto", "hit", "pt", "p_FWE", "raekke", "gevinst"):
        assert not any(ord_ in k for k in noegler), ord_
    assert {r["variant"] for r in o["varianter"]} == {k6._vnavn(v) for v in k6.VARIANTER}


def test_hele_koerslen_paa_syntetisk_serie():
    g = Bygger([TIR, ONS, TOR, "2023-06-16"], rng=np.random.default_rng(6)).g()
    res = k6.analyse(g, n_reps=5)
    for v in k6.VARIANTER:
        t = res["tal"][v]
        assert t["naetter_n"] == g.maske(v).sum()
        assert np.isfinite(t["MDE_sidak4"])
    meta = {"koert_utc": "2026-01-01 00:00", "head": "0" * 40}
    md = k6.skriv_md({k6.HOVED: res, k6.KONTROL: res}, meta)
    assert "Hovedtabel" in md and "§8 anvendt mekanisk" in md
    df = k6.lang_tabel({k6.HOVED: res})
    assert {"hoved", "diagnose", "aar", "hele_natten"} <= set(df["tabel"])
