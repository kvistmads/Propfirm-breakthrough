"""Tests for research/b4_k4_emt.py — B4 kandidat 4, EMT.

Præregistreringen er ``research/prereg/b4_k4_emt.md``. §11.2's 13 syntetiske tests står
først, i præregistreringens rækkefølge. Derefter det de bygger på:

- fladning, rul i handelstiden og halve dage;
- det ublokerede fyld er det samme som dagens forløb giver;
- optællingen regner intet R og simulerer kun hvad 2/dag kræver;
- CR1-intervallet, MDE-tabellen i §7 og beslutningsreglen i §8;
- hele den rigtige kørsel på en syntetisk serie, så den ikke fejler første gang den køres.

Alle serier er syntetiske. Ingen test læser prisdata.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from research import b4_k1_optaelling as k1
from research import b4_k1_trinA as trinA
from research import b4_k4_emt as k4
from research.normal import norm
from research.stats import mean_ci_t

CT = "America/Chicago"
DAG = "2023-06-14"          # onsdag, sommertid: CT = UTC − 5
DAG2 = "2023-06-15"
P = 15000.0
SLIP = trinA.SLIP_PT
NAT_VOL = 1e6               # natten holder VWAP fast på P, til en test flytter den


def _ct(hhmm: str, dag: str = DAG) -> pd.Timestamp:
    return pd.Timestamp(f"{dag} {hhmm}").tz_localize(CT).tz_convert("UTC")


def _plus(hhmm: str, minutter: int) -> str:
    return (pd.Timestamp(f"2000-01-01 {hhmm}") + pd.Timedelta(minutes=minutter)).strftime("%H:%M")


def _foraften(dag: str) -> str:
    return (pd.Timestamp(dag) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")


# ===========================================================================
# Byggeklodser
# ===========================================================================

class Bygger:
    """En 1m-serie pr. dag fra 17:00 CT aftenen før til 15:30 CT. Fladt som standard:
    open = close = P, high/low ± 1, så hvert 5m-lys har TR = 2, ATR = 2, EMA9 = P og VWAP
    = P. Natten har volumen 1e6, dagen 1.

    Priserne i ``bar``, ``lys`` og ``flad`` er afstande fra P. Med ``fortegn = −1`` spejles
    alt omkring P (high og low bytter plads), så samme scenarie giver den modsatte side."""

    def __init__(self, dage=(DAG,), til: str = "15:30", fortegn: int = 1):
        dele = []
        for d in dage:
            idx = pd.date_range(_ct("17:00", _foraften(d)), _ct(til, d), freq="1min",
                                inclusive="left").rename("time")
            vol = np.where(idx < _ct("08:30", d), NAT_VOL, 1.0)
            dele.append(pd.DataFrame({"open": P, "high": P + 1.0, "low": P - 1.0, "close": P,
                                      "volume": vol, "instrument_id": np.int64(1)}, index=idx))
        self.df = pd.concat(dele)
        self.dag0 = dage[0]
        self.f = fortegn

    def _d(self, dag):
        return self.dag0 if dag is None else dag

    def _px(self, o, h, l, c):
        if self.f == 1:
            return [P + o, P + h, P + l, P + c]
        return [P - o, P - l, P - h, P - c]

    def bar(self, hhmm, o, h, l, c, vol=None, dag=None) -> "Bygger":
        t = _ct(hhmm, self._d(dag))
        self.df.loc[t, ["open", "high", "low", "close"]] = self._px(o, h, l, c)
        if vol is not None:
            self.df.loc[t, "volume"] = vol
        return self

    def lys(self, hhmm, o, h, l, c, dag=None) -> "Bygger":
        """Et 5m-lys som fem 1m-barer: high i andet minut, low i tredje, close i femte."""
        m = [_plus(hhmm, x) for x in range(5)]
        self.bar(m[0], o, o, o, o, dag=dag)
        self.bar(m[1], o, max(o, h), o, o, dag=dag)
        self.bar(m[2], o, o, min(o, l), o, dag=dag)
        self.bar(m[3], o, o, o, o, dag=dag)
        self.bar(m[4], o, max(o, c), min(o, c), c, dag=dag)
        return self

    def flad(self, fra, til, x, dag=None) -> "Bygger":
        """Barer uden udsving på afstand x fra P, fra ``fra`` til (ikke med) ``til``."""
        d = self._d(dag)
        m = (self.df.index >= _ct(fra, d)) & (self.df.index < _ct(til, d))
        self.df.loc[m, ["open", "high", "low", "close"]] = self._px(x, x, x, x)
        return self

    def rul(self, hhmm, dag=None) -> "Bygger":
        self.df.loc[self.df.index >= _ct(hhmm, self._d(dag)), "instrument_id"] = np.int64(2)
        return self


LAV = 29.0                  # udmattelseslysets low over P; high = LAV + 11


def udmattelse(b: Bygger, lav: float = LAV, kl: str = "09:15", hoej: float = 11.0,
               close: float = 2.0) -> Bygger:
    """Stræk op i tre lys op til ``lav + 1`` og et udmattelseslys kl. ``kl``: open
    ``lav + 1``, high ``lav + hoej``, low ``lav``, close ``lav + close``. Bagefter fladt på
    close."""
    s = [_plus(kl, -15), _plus(kl, -10), _plus(kl, -5)]
    b.lys(s[0], 0, 4, 0, 4).lys(s[1], 4, 8, 4, 8).lys(s[2], 8, lav + 1, 8, lav + 1)
    b.lys(kl, lav + 1, lav + hoej, lav, lav + close)
    return b.flad(_plus(kl, 5), "15:30", lav + close)


def brud_ned(b: Bygger, kl: str = "09:22", lav: float = LAV, fra: float | None = None
             ) -> Bygger:
    """En 1m-bar der handler 2 ticks under ``lav``, og fladt der bagefter."""
    o = lav + 2 if fra is None else fra
    b.bar(kl, o, o, lav - 0.5, lav - 0.5)
    return b.flad(_plus(kl, 1), "15:30", lav - 0.5)


def til_vwap(b: Bygger, kl: str = "10:00", fra: float = LAV - 0.5) -> Bygger:
    """En 1m-bar der handler ned til P − 1, under VWAP, og fladt der bagefter."""
    b.bar(kl, fra, fra, -1, -1)
    return b.flad(_plus(kl, 1), "15:30", -1)


def hoved(fortegn: int = 1) -> Bygger:
    """Short (eller spejlet long): udmattelseslys 09:15, brud 09:22, tilbage til VWAP
    10:00."""
    return til_vwap(brud_ned(udmattelse(Bygger(fortegn=fortegn))))


FYLD = P + LAV - 0.25 - SLIP          # short: triggeren LAV − 1 tick, slippage imod
STOP = P + LAV + 11 + 0.5             # short: high + 2 ticks
RISIKO = STOP - FYLD


def _dage(*dage: str) -> pd.DatetimeIndex:
    sidste = pd.Timestamp(max(dage)) + pd.Timedelta(days=1)
    return k1.rth_dage(min(dage), sidste)


def _g(b: Bygger, *dage: str) -> k4.Grundlag:
    return k4.byg_grundlag(b.df, _dage(*(dage or (b.dag0,))))


def _r(g: k4.Grundlag, hhmm: str, dag: str = DAG) -> int:
    r = np.flatnonzero(g.lys["tid_ns"].to_numpy() == _ct(hhmm, dag).value)
    assert len(r) == 1, f"intet lys {hhmm} i vinduet"
    return int(r[0])


def _j(g: k4.Grundlag, hhmm: str, dag: str = DAG) -> int:
    j = np.flatnonzero(g.s.tider == _ct(hhmm, dag).value)
    assert len(j) == 1
    return int(j[0])


def _kl(g: k4.Grundlag, raekker) -> list[str]:
    return [pd.Timestamp(int(t), tz="UTC").tz_convert(CT).strftime("%H:%M")
            for t in g.lys["tid_ns"].to_numpy()[np.asarray(raekker, dtype=np.int64)]]


def _forloeb(g, k=1.5, n=1, side=k4.TILBAGE, exit_fn=None) -> k4.Forloeb:
    return k4.dagsforloeb(g, side, k4.setups(g, k), n,
                          k4.exit_fuld(g) if exit_fn is None else exit_fn)


def _handler(g, k=1.5, n=1, side=k4.TILBAGE) -> pd.DataFrame:
    return k4.handelstabel(g, side, _forloeb(g, k, n, side))


# ===========================================================================
# §11.2 test 1 — VWAP nulstilles kl. 17:00 CT og regnes med hlc3 × volume
# ===========================================================================

class TestVWAPSession:
    def _serie(self, dag: str):
        idx = pd.DatetimeIndex([_ct("16:58", dag), _ct("16:59", dag), _ct("17:00", dag),
                                _ct("17:01", dag)])
        h = np.array([110.0, 120.0, 210.0, 230.0])
        l = np.array([100.0, 100.0, 200.0, 200.0])
        c = np.array([101.0, 119.0, 201.0, 229.0])
        v = np.array([1.0, 3.0, 2.0, 6.0])
        return idx, h, l, c, v

    @pytest.mark.parametrize("dag", ["2023-06-14", "2023-01-10"])   # sommer- og vintertid
    def test_nulstilles_17_ct_og_bruger_hlc3(self, dag):
        idx, h, l, c, v = self._serie(dag)
        vw = k4.session_vwap(idx, h, l, c, v)
        hlc3 = (h + l + c) / 3
        # 16:58 og 16:59 hører til sessionen fra 17:00 dagen før.
        assert vw[1] == pytest.approx((hlc3[0] * 1 + hlc3[1] * 3) / 4, abs=1e-12)
        # 17:00 starter en ny session: kun barens egen hlc3, ikke close.
        assert vw[2] == pytest.approx(hlc3[2], abs=1e-12) and vw[2] != c[2]
        assert vw[3] == pytest.approx((hlc3[2] * 2 + hlc3[3] * 6) / 8, abs=1e-12)

    def test_sessionsnoeglen_skifter_ved_17_ct(self):
        idx, *_ = self._serie(DAG)
        n = k4.session_noegle(idx)
        assert n[0] == n[1] != n[2] == n[3]
        vinter = k4.session_noegle(pd.DatetimeIndex([pd.Timestamp("2023-01-10 22:59", tz="UTC"),
                                                     pd.Timestamp("2023-01-10 23:00", tz="UTC")]))
        assert vinter[0] != vinter[1]      # 17:00 CST = 23:00 UTC

    def test_volumen_nul_giver_ingen_vwap(self):
        idx, h, l, c, v = self._serie(DAG)
        v[2] = 0.0
        vw = k4.session_vwap(idx, h, l, c, v)
        assert np.isnan(vw[2]) and np.isfinite(vw[3])

    def test_serien_bruger_sessionens_vwap(self):
        b = Bygger()
        b.bar("09:00", 2, 5, 1, 4, vol=3.0)
        g = _g(b)
        df = b.df
        noegle = k4.session_noegle(df.index)
        m = noegle == noegle[_j(g, "09:00")]
        sub = df[m & (df.index <= _ct("09:00"))]
        ventet = (((sub["high"] + sub["low"] + sub["close"]) / 3 * sub["volume"]).sum()
                  / sub["volume"].sum())
        assert g.s.vwap_adj[_j(g, "09:00")] == pytest.approx(ventet, abs=1e-9)


# ===========================================================================
# §11.2 test 2 — VWAP på den forskelsjusterede serie, målet i handelspris
# ===========================================================================

class TestForskelsjusteretVWAP:
    def _serie(self) -> pd.DataFrame:
        """Kontrakt 1 kl. 17:00-17:59 CT aftenen før på P − 50, rul 18:00 CT til kontrakt 2
        på P (spring 50), og rul 18:00 CT dagen efter til kontrakt 3 på P + 20 (spring 20).
        RTH-dagen ligger i kontrakt 2, hvor forskydningen er 20."""
        idx = pd.date_range(_ct("17:00", _foraften(DAG)), _ct("19:00", DAG), freq="1min",
                            inclusive="left").rename("time")
        idx = idx[(idx < _ct("16:00", DAG)) | (idx >= _ct("17:00", DAG))]
        iid = np.where(idx < _ct("18:00", _foraften(DAG)), 1,
                       np.where(idx >= _ct("18:00", DAG), 3, 2)).astype(np.int64)
        niveau = np.select([iid == 1, iid == 2], [P - 50, P], P + 20)
        df = pd.DataFrame({"open": niveau, "high": niveau + 1, "low": niveau - 1,
                           "close": niveau, "volume": np.where(iid == 1, 20.0, 1.0),
                           "instrument_id": iid}, index=idx)
        df.loc[_ct("09:00"), ["open", "high", "low", "close", "volume"]] = [P, P + 3, P, P + 3, 5]
        return df

    def test_forskydningen(self):
        df = self._serie()
        s = k4.Serie.af(df)
        iid = df["instrument_id"].to_numpy()
        assert set(s.forskyd[iid == 1]) == {70.0}
        assert set(s.forskyd[iid == 2]) == {20.0}
        assert set(s.forskyd[iid == 3]) == {0.0}

    def test_maalet_er_sessionens_vwap_i_kontrakt_2s_priser(self):
        df = self._serie()
        s = k4.Serie.af(df)
        j = int(np.flatnonzero(s.tider == _ct("09:00").value)[0])
        sub = df.iloc[: j + 1]
        hlc3 = (sub["high"] + sub["low"] + sub["close"]) / 3
        # Kontrakt 1's barer flyttes med springet på 50 til kontrakt 2's niveau.
        hlc3 = hlc3 + np.where(sub["instrument_id"] == 1, 50.0, 0.0)
        ventet = float((hlc3 * sub["volume"]).sum() / sub["volume"].sum())
        assert s.vwap_adj[j] == pytest.approx(ventet + 20.0, abs=1e-9)   # justeret
        assert s.maal_vwap[j + 1] == pytest.approx(ventet, abs=1e-9)     # handelspris
        # Uden justering ville kontrakt 1's 1.200 volumen trække VWAP ~28 point ned.
        raa = float(((sub["high"] + sub["low"] + sub["close"]) / 3 * sub["volume"]).sum()
                    / sub["volume"].sum())
        assert ventet - raa > 20

    def test_handlen_ser_maalet_i_handelspris(self):
        """Samme scenarie med og uden en senere rul (spring 300): forskydningen i RTH-dagen
        er 300 vs. 0, men handlen er den samme."""
        uden = hoved()
        med = hoved()
        nat = pd.date_range(_ct("17:00", DAG), _ct("19:00", DAG), freq="1min",
                            inclusive="left").rename("time")
        efter = nat >= _ct("18:00", DAG)
        for b, spring in ((uden, 0.0), (med, 300.0)):
            niveau = P + np.where(efter, spring, 0.0)
            ekstra = pd.DataFrame({"open": niveau, "high": niveau + 1, "low": niveau - 1,
                                   "close": niveau, "volume": 1.0,
                                   "instrument_id": np.where(efter & (spring > 0), 2, 1)
                                   .astype(np.int64)}, index=nat)
            b.df = pd.concat([b.df, ekstra])
        gu, gm = _g(uden), _g(med)
        j = _j(gm, "09:30")
        assert gm.s.forskyd[j] == 300.0 and gu.s.forskyd[j] == 0.0
        assert gm.s.maal_vwap[j] == pytest.approx(gu.s.maal_vwap[j], abs=1e-9)
        hu, hm = _handler(gu), _handler(gm)
        assert len(hu) == len(hm) == 1
        assert hm["R_brutto"].iloc[0] == pytest.approx(hu["R_brutto"].iloc[0], abs=1e-9)
        assert hm["exit_i"].iloc[0] == hu["exit_i"].iloc[0]


# ===========================================================================
# §11.2 test 3 — EMA9 og ATR(14) bruger kun lukkede lys
# ===========================================================================

class TestIndikatorer:
    def test_ema_er_alfa_2_10(self):
        x = np.array([1.0, 5.0, 2.0, 8.0, 8.0, 3.0])
        forventet = pd.Series(x).ewm(alpha=0.2, adjust=False).mean().to_numpy()
        assert np.allclose(k4.ema(x), forventet, atol=1e-12)

    def test_vaerdierne_ved_udmattelseslyset(self):
        g = _g(hoved())
        r = _r(g, "09:15")
        a, e = 2.0, 0.0
        for tr, c in ((4, 4), (4, 8), (22, 30), (11, 31)):   # rallyets tre lys og 09:15
            a += (tr - a) / 14
            e += 0.2 * (c - e)
        assert g.lys["atr"].iloc[r] == pytest.approx(a, abs=1e-9)
        assert g.lys["ema9"].iloc[r] == pytest.approx(P + e, abs=1e-9)
        assert g.lys["vwap"].iloc[r] == g.s.vwap_adj[_j(g, "09:19")]

    def test_senere_lys_aendrer_intet(self):
        g0 = _g(udmattelse(Bygger()))
        b = udmattelse(Bygger())
        b.bar("09:20", 31, 90, -40, 70, vol=1e9)
        g1 = _g(b)
        r = _r(g0, "09:15")
        for kol in ("atr", "ema9", "vwap", "c_adj"):
            assert g1.lys[kol].iloc[r] == g0.lys[kol].iloc[r], kol
        assert g1.lys["atr"].iloc[r + 1] != g0.lys["atr"].iloc[r + 1]

    def test_vwap_medtager_lysets_sidste_minut(self):
        g0 = _g(udmattelse(Bygger()))
        b = udmattelse(Bygger())
        b.bar("09:19", 31, 31, 31, 31, vol=5e8)
        g1 = _g(b)
        r = _r(g0, "09:15")
        assert g1.lys["vwap"].iloc[r] != g0.lys["vwap"].iloc[r]


# ===========================================================================
# §11.2 test 4 — stræk op og ned, med EMA-betingelsen
# ===========================================================================

class TestStraek:
    @pytest.mark.parametrize("c,vwap,ema9,atr,k,ventet", [
        (110.0, 100.0, 105.0, 5.0, 2.0, k4.OP),       # 10 ≥ 2 × 5, VWAP < EMA < close
        (110.0, 100.0, 105.0, 5.0, 3.0, 0),           # 10 < 15
        (110.0, 100.0, 112.0, 5.0, 1.5, 0),           # EMA over close
        (110.0, 100.0, 99.0, 5.0, 1.5, 0),            # EMA under VWAP
        (110.0, 100.0, 110.0, 5.0, 1.5, 0),           # EMA = close er ikke mellem
        (90.0, 100.0, 95.0, 5.0, 2.0, k4.NED),        # spejlvendt
        (90.0, 100.0, 89.0, 5.0, 2.0, 0),             # EMA under close
        (90.0, 100.0, 101.0, 5.0, 2.0, 0),            # EMA over VWAP
        (90.0, 100.0, 95.0, 4.0, 2.5, k4.NED),        # lighed: 10 ≥ 2,5 × 4
    ])
    def test_ren_funktion(self, c, vwap, ema9, atr, k, ventet):
        assert k4.straek_retning([c], [vwap], [ema9], [atr], k)[0] == ventet

    def test_vwap_udefineret_er_ikke_strakt(self):
        assert k4.straek_retning([110.0], [np.nan], [105.0], [1.0], 1.5)[0] == 0

    @pytest.mark.parametrize("fortegn,retning", [(1, k4.OP), (-1, k4.NED)])
    def test_scenariet(self, fortegn, retning):
        g = _g(hoved(fortegn))
        r = _r(g, "09:15")
        for k in k4.K_VAERDIER:
            assert k4.straek(g, k)[r] == retning
        # Før rallyet er intet strakt.
        assert k4.straek(g, 1.5)[_r(g, "08:55")] == 0

    def test_ema_over_close_fjerner_straekket(self):
        """Prisen ligger længe på +60, så EMA9 er ~+60; så lukker et lys på +31. Afstanden
        til VWAP er stor nok, men EMA9 ligger over close."""
        b = Bygger()
        b.flad("09:00", "09:40", 60)
        b.lys("09:40", 60, 60, 31, 31)
        b.flad("09:45", "15:30", 31)
        g = _g(b)
        r = _r(g, "09:40")
        assert g.lys["c_adj"].iloc[r] - g.lys["vwap"].iloc[r] > 3 * g.lys["atr"].iloc[r]
        assert g.lys["ema9"].iloc[r] > g.lys["c_adj"].iloc[r]
        assert k4.straek(g, 1.5)[r] == 0


# ===========================================================================
# §11.2 test 5 — vægekravet ved præcis 50%
# ===========================================================================

class TestVaege:
    def test_praecis_halvdelen_er_nok(self):
        # Ticks: high 10, low 0, open 2, close 5: øvre væge 5 af 10.
        op, ned = k4.vaege([2], [10], [0], [5])
        assert op[0] and not ned[0]
        op, _ = k4.vaege([2], [10], [0], [6])        # 4 af 10
        assert not op[0]
        _, ned = k4.vaege([8], [10], [0], [5])       # nedre væge 5 af 10
        assert ned[0]
        _, ned = k4.vaege([8], [10], [0], [4])
        assert not ned[0]

    def test_lys_uden_laengde(self):
        op, ned = k4.vaege([5], [5], [5], [5])
        assert not op[0] and not ned[0]

    @pytest.mark.parametrize("close,er_setup", [(5.5, True), (5.75, False)])
    def test_i_scenariet(self, close, er_setup):
        """Udmattelseslyset har high LAV + 11 og low LAV: close LAV + 5,5 giver præcis 50%
        øvre væge, close LAV + 5,75 ét tick for lidt."""
        g = _g(udmattelse(Bygger(), close=close))
        r = _r(g, "09:15")
        assert k4.straek(g, 1.5)[r] == k4.OP
        assert (r in k4.setups(g, 1.5)) == er_setup


# ===========================================================================
# §11.2 test 6 — stop-ordren gælder kun i lys i+1, og et gap fyldes på åbningen
# ===========================================================================

class TestIndgang:
    def test_brud_i_naeste_lys_fylder_paa_triggeren(self):
        g = _g(hoved())
        f = _forloeb(g)
        assert f.n == 1 and _kl(g, f.raekke) == ["09:15"]
        assert f.j[0] == _j(g, "09:22")
        assert f.fyld[0] == pytest.approx(FYLD, abs=1e-12)

    def test_brud_foerst_i_lys_i_plus_2_udloeber(self):
        b = til_vwap(brud_ned(udmattelse(Bygger()), kl="09:27"))
        g = _g(b)
        f = _forloeb(g)
        assert f.n == 0
        assert f.tael["udloest_n"] == 0 and f.tael["udloebet_n"] >= 1

    def test_gap_fyldes_paa_aabningen(self):
        b = udmattelse(Bygger())
        b.bar("09:20", 27, 27, 26.5, 26.5)
        b.flad("09:21", "15:30", 26.5)
        til_vwap(b, fra=26.5)
        g = _g(b)
        f = _forloeb(g)
        assert f.j[0] == _j(g, "09:20")
        assert f.fyld[0] == pytest.approx(P + 27 - SLIP, abs=1e-12)
        assert f.risiko[0] == pytest.approx(STOP - (P + 27 - SLIP), abs=1e-12)

    @pytest.mark.parametrize("low,fyldt", [(LAV - 0.25, True), (LAV, False)])
    def test_triggeren_er_et_tick_under_low(self, low, fyldt):
        b = udmattelse(Bygger())
        b.bar("09:22", LAV + 2, LAV + 2, low, low)
        b.flad("09:23", "15:30", LAV + 2)
        g = _g(b)
        assert (_forloeb(g).n == 1) == fyldt

    def test_spejlet_long(self):
        g = _g(hoved(-1))
        f = _forloeb(g)
        assert f.n == 1
        assert bool(g.lys["long_tilbage"].iloc[f.raekke[0]])
        assert f.fyld[0] == pytest.approx(P - (LAV - 0.25) + SLIP, abs=1e-12)

    def test_find_fyld_direkte(self):
        g = _g(hoved())
        r = _r(g, "09:15")
        j, fyld = k4.find_fyld(g.s, _j(g, "09:20"), _j(g, "09:25"),
                               int(g.lys["trigger_t_tilbage"].iloc[r]), False)
        assert j == _j(g, "09:22") and fyld == pytest.approx(FYLD, abs=1e-12)
        assert k4.find_fyld(g.s, _j(g, "09:20"), _j(g, "09:22"),
                            int(g.lys["trigger_t_tilbage"].iloc[r]), False)[0] == -1


# ===========================================================================
# §11.2 test 7 — stop 2 ticks bag vægen
# ===========================================================================

class TestStop:
    def test_stop_og_risiko(self):
        g = _g(hoved())
        r = _r(g, "09:15")
        assert g.lys["stop_t_tilbage"].iloc[r] * 0.25 == STOP
        f = _forloeb(g)
        assert f.risiko[0] == pytest.approx(RISIKO, abs=1e-12)

    @pytest.mark.parametrize("hoej,stoppet", [(LAV + 11.25, False), (LAV + 11.5, True)])
    def test_stoppet_rammes_ved_high_plus_2_ticks(self, hoej, stoppet):
        b = brud_ned(udmattelse(Bygger()))
        b.bar("09:30", LAV - 0.5, hoej, LAV - 0.5, LAV - 0.5)
        g = _g(b)
        h = _handler(g).iloc[0]
        if stoppet:
            assert h["udfald"] == k4.STOP and h["exit_i"] == _j(g, "09:30")
            ventet = (FYLD - (STOP + SLIP)) / RISIKO
            assert h["R_brutto"] == pytest.approx(ventet, abs=1e-12)
        else:
            assert h["udfald"] == k4.TIDSEXIT

    def test_spejlet_long_stop_under_low(self):
        g = _g(hoved(-1))
        r = _r(g, "09:15")
        assert g.lys["stop_t_tilbage"].iloc[r] * 0.25 == P - (LAV + 11.5)


# ===========================================================================
# §11.2 test 8 — målet er forrige minuts VWAP; i fyldningsbaren kun stoppet
# ===========================================================================

class TestMaal:
    def test_maalet_ramt_ved_vwap(self):
        g = _g(hoved())
        h = _handler(g).iloc[0]
        j = _j(g, "10:00")
        assert h["udfald"] == k4.MAAL and h["exit_i"] == j
        assert h["R_brutto"] == pytest.approx((FYLD - g.s.maal_vwap[j]) / RISIKO, abs=1e-12)
        assert h["RR"] == pytest.approx((FYLD - g.s.maal_vwap[_j(g, "09:22")]) / RISIKO,
                                        abs=1e-12)

    def test_forrige_minuts_vwap(self):
        """10:00 har volumen 1e9 og hlc3 ~ +20: VWAP springer til ~+10,5 ved dens lukning.
        10:00's low +10 når den nye VWAP, men ikke målet i 10:00 (VWAP ved 09:59 ~ 0).
        Målet rammes først i 10:01."""
        b = brud_ned(udmattelse(Bygger()))
        b.bar("10:00", 25, 26, 10, 25, vol=1e9)
        b.bar("10:01", 12, 12, 10.25, 11)
        b.flad("10:02", "15:30", 11)
        g = _g(b)
        j = _j(g, "10:00")
        s = g.s
        assert s.l[j] <= s.vwap_adj[j] and s.l[j] > s.maal_vwap[j]
        h = _handler(g).iloc[0]
        assert h["udfald"] == k4.MAAL and h["exit_i"] == j + 1
        assert h["R_brutto"] == pytest.approx((FYLD - s.vwap_adj[j]) / RISIKO, abs=1e-12)

    def test_kun_stoppet_i_fyldningsbaren(self):
        """09:22 handler både under VWAP (målet) og fylder: ikke mål i 09:22, men i 09:23."""
        b = udmattelse(Bygger())
        b.bar("09:22", LAV + 2, LAV + 2, -5, -5)
        b.bar("09:23", -5, -5, -6, -6)
        b.flad("09:24", "15:30", -6)
        g = _g(b)
        h = _handler(g).iloc[0]
        assert h["udfald"] == k4.MAAL and h["exit_i"] == _j(g, "09:23")

    def test_stoppet_kan_rammes_i_fyldningsbaren(self):
        b = udmattelse(Bygger())
        b.bar("09:22", LAV + 2, LAV + 12, LAV - 0.5, LAV)
        b.flad("09:23", "15:30", LAV)
        g = _g(b)
        h = _handler(g).iloc[0]
        assert h["udfald"] == k4.STOP and h["exit_i"] == _j(g, "09:22")
        assert not h["tvetydig"]

    def test_tvetydig_og_bedste_fald(self):
        """09:30 rammer både stop og mål: forsigtigt stop, i bedste fald målet."""
        b = brud_ned(udmattelse(Bygger()))
        b.bar("09:30", LAV - 0.5, LAV + 12, -1, -1)
        b.flad("09:31", "15:30", -1)
        g = _g(b)
        h = _handler(g).iloc[0]
        j = _j(g, "09:30")
        assert h["udfald"] == k4.STOP and h["tvetydig"]
        assert h["udfald_bedste"] == k4.MAAL
        assert h["R_netto_bedste"] == pytest.approx(
            (FYLD - g.s.maal_vwap[j]) / RISIKO - h["omk_R"], abs=1e-12)


# ===========================================================================
# §11.2 test 9 — 1R-reglen
# ===========================================================================

class TestEnR:
    @pytest.mark.parametrize("lav,taget", [(12.5, True), (12.25, False)])
    def test_graensen(self, lav, taget):
        """Udmattelseslys med længde 11: RR ≥ 1 kræver low − VWAP ≥ 11 + 1 + 2 × slip =
        12,27. Low 12,5 klarer det, 12,25 ikke."""
        b = til_vwap(brud_ned(udmattelse(Bygger(), lav=lav), lav=lav), fra=lav - 0.5)
        g = _g(b)
        r = _r(g, "09:15")
        assert r in k4.setups(g, 1.5)
        f = _forloeb(g)
        fyld = P + lav - 0.25 - SLIP
        risiko = P + lav + 11.5 - fyld
        afstand = fyld - g.s.maal_vwap[_j(g, "09:22")]
        assert (afstand >= risiko) == taget
        assert f.tael["udloest_n"] == 1
        assert f.n == int(taget)
        assert f.tael["sprunget_over_under_1R_n"] == int(not taget)
        if taget:
            assert f.rr[0] == pytest.approx(afstand / risiko, abs=1e-12)

    def test_vwap_paa_forkert_side(self):
        assert k4.afstand(100.0, 90.0, False, k4.TILBAGE) < 0   # short med VWAP over fyldet
        assert k4.afstand(100.0, 90.0, True, k4.TILBAGE) == 10.0


# ===========================================================================
# §11.2 test 10 — 1 og 2 handler om dagen
# ===========================================================================

def to_setups() -> Bygger:
    """Handel A: udmattelse 09:15, brud 09:22, mål 10:00. Handel B: nyt rally fra 10:30,
    udmattelse 10:45, brud 10:52, mål 11:30."""
    b = hoved()
    udmattelse(b, kl="10:45")
    brud_ned(b, kl="10:52")
    return til_vwap(b, kl="11:30")


class TestHandlerPrDag:
    def test_en_om_dagen(self):
        g = _g(to_setups())
        assert _kl(g, k4.setups(g, 1.5)) == ["09:15", "10:45"]
        f = _forloeb(g, n=1)
        assert f.n == 1 and _kl(g, f.raekke) == ["09:15"]
        assert f.tael["ignoreret_efter_dagens_sidste_handel_n"] == 1

    def test_to_om_dagen(self):
        g = _g(to_setups())
        f = _forloeb(g, n=2)
        assert f.n == 2 and _kl(g, f.raekke) == ["09:15", "10:45"]
        assert list(f.nr) == [1, 2]
        h = k4.handelstabel(g, k4.TILBAGE, f)
        assert list(h["udfald"]) == [k4.MAAL, k4.MAAL]
        assert h["exit_i"].iloc[0] < h["fyld_j"].iloc[1]

    def _fast_exit(self, g, hhmm):
        kald = []

        def f(side, r, j, fyld, risiko, rr):
            kald.append(r)
            return _j(g, hhmm)
        return f, kald

    def test_blokeret_naar_hele_lys_i_plus_1_ligger_i_handlen(self):
        g = _g(to_setups())
        ex, kald = self._fast_exit(g, "10:55")
        f = _forloeb(g, n=2, exit_fn=ex)
        assert f.n == 1 and f.tael["blokeret_n"] == 1 and len(kald) == 1

    def test_exit_foer_triggeren_giver_samme_fyld(self):
        g = _g(to_setups())
        ex, _ = self._fast_exit(g, "10:51")
        f = _forloeb(g, n=2, exit_fn=ex)
        assert f.n == 2 and f.j[1] == _j(g, "10:52")
        assert f.fyld[1] == pytest.approx(FYLD, abs=1e-12)

    def test_exit_i_triggerbaren_fylder_paa_naeste_aabning(self):
        """Første handel lukker i 10:52: ordren må først fyldes fra 10:53, hvor prisen
        allerede er under triggeren — fyld på åbningen med slippage."""
        g = _g(to_setups())
        ex, _ = self._fast_exit(g, "10:52")
        f = _forloeb(g, n=2, exit_fn=ex)
        assert f.n == 2 and f.j[1] == _j(g, "10:53")
        assert f.fyld[1] == pytest.approx(P + LAV - 0.5 - SLIP, abs=1e-12)

    def test_exit_kaldes_kun_naar_det_betyder_noget(self):
        g = _g(hoved())
        ex, kald = self._fast_exit(g, "10:00")
        assert _forloeb(g, n=2, exit_fn=ex).n == 1 and kald == []   # intet senere setup
        g = _g(to_setups())
        ex, kald = self._fast_exit(g, "10:00")
        _forloeb(g, n=1, exit_fn=ex)
        assert kald == []                                            # 1/dag


# ===========================================================================
# §11.2 test 11 — N-tid kræver brud og trækker pr. dag
# ===========================================================================

class TestNtid:
    def test_puljen_kraever_brud_og_1R(self):
        """Rallyets lys er strakt, men brydes ikke. 09:15 (udmattelse) og 09:55 (strakt uden
        væge, brudt af 10:00) er puljen."""
        g = _g(hoved())
        straekt = np.flatnonzero(k4.straek(g, 1.5) != 0)
        assert {"09:00", "09:05", "09:10", "09:15", "09:55"} <= set(_kl(g, straekt))
        assert _kl(g, k4.ntid_pulje(g, 1.5)) == ["09:15", "09:55"]
        assert "09:55" not in _kl(g, k4.setups(g, 1.5))

    def test_puljen_udelukker_under_1R(self):
        b = til_vwap(brud_ned(udmattelse(Bygger(), lav=12.25), lav=12.25), fra=11.75)
        g = _g(b)
        assert "09:15" not in _kl(g, k4.ntid_pulje(g, 1.5))

    def test_traekker_fra_dagens_celle(self):
        g = _g(hoved())
        model = _forloeb(g)
        nv = k4.ntid_variant(g, 1.5, model)
        assert nv.tael["celler_n"] == 1 and nv.tael["celler_for_faa_n"] == 0
        set_ = set()
        for rep in range(40):
            r = k4.ntid_traek(nv, np.random.default_rng([1, rep]))
            assert len(r) == 1
            set_ |= set(_kl(g, r))
        assert set_ == {"09:15", "09:55"}

    def test_matching_pr_retning_og_for_faa(self):
        """En long modelhandel på en dag hvor puljen kun har shorts: cellen er tom, og det
        tælles."""
        g = _g(hoved())
        r_long = _r(g, "10:05")
        assert bool(g.lys["long_tilbage"].iloc[r_long])
        model = k4.Forloeb(np.array([r_long]), *(np.zeros(1) for _ in range(5)), tael={})
        nv = k4.ntid_variant(g, 1.5, model)
        assert nv.tael["celler_for_faa_n"] == 1 and nv.tael["manglende_n"] == 1
        assert nv.tael["dage_for_faa_n"] == 1
        assert len(k4.ntid_traek(nv, np.random.default_rng(0))) == 0

    def test_dage_uden_modelhandel_traekkes_ikke(self):
        b = hoved()
        b2 = hoved()
        b2.df.index = b2.df.index + pd.Timedelta(days=1)          # samme dag, en dag senere
        b.df = pd.concat([b.df, b2.df])
        g = _g(b, DAG, DAG2)
        model = _forloeb(g)
        assert model.n == 2
        enkelt = k4.Forloeb(model.raekke[:1], model.j[:1], model.fyld[:1], model.risiko[:1],
                            model.rr[:1], model.nr[:1], tael={})
        nv = k4.ntid_variant(g, 1.5, enkelt)
        for rep in range(10):
            r = k4.ntid_traek(nv, np.random.default_rng(rep))
            assert set(g.lys["dag_pos"].to_numpy()[r]) == {0}

    def test_uden_tilbagelaegning_og_alle_ved_for_faa(self):
        nv = k4.NtidVariant(m=np.array([2, 2, 1]), start=np.array([0, 5, 6]),
                            laengde=np.array([5, 1, 3]), pulje=np.arange(9),
                            faste=np.array([5]), tael={})
        for rep in range(200):
            r = k4.ntid_traek(nv, np.random.default_rng(rep))
            celle0 = r[r < 5]
            assert len(celle0) == 2 and celle0[0] != celle0[1]
            assert 5 in r                                  # for få: brugt
            assert ((r >= 6) & (r < 9)).sum() == 1
        a = k4.ntid_traek(nv, k4.ntid_rng(3, (1.5, 2)))
        b = k4.ntid_traek(nv, k4.ntid_rng(3, (1.5, 2)))
        assert np.array_equal(a, b)

    def test_gentagelsen_koerer_disciplinen(self):
        g = _g(hoved())
        _, _, nt = k4.forbered(g)
        rep = k4.ntid_gentagelse(g, nt, 0)
        for v in k4.VARIANTER:
            assert rep[v]["handler_n"] == 1 and rep[v]["udfaldne_n"] == 0
            assert np.isfinite(rep[v]["m"])


# ===========================================================================
# §11.2 test 12 — N-mod spejlet
# ===========================================================================

def nmod_scenarie() -> Bygger:
    """Udmattelse 09:15 (stræk op); 09:21 bryder toppen; bagefter stiger prisen til +90."""
    b = udmattelse(Bygger())
    b.bar("09:21", LAV + 2, LAV + 12, LAV + 2, LAV + 12)
    b.flad("09:22", "10:00", LAV + 12)
    b.bar("10:00", LAV + 12, 90, LAV + 12, 90)
    return b.flad("10:01", "15:30", 90)


class TestNmod:
    def test_ordre_stop_og_risiko(self):
        g = _g(nmod_scenarie())
        r = _r(g, "09:15")
        assert bool(g.lys["long_fortsaet"].iloc[r]) and not bool(g.lys["long_tilbage"].iloc[r])
        assert g.lys["trigger_t_fortsaet"].iloc[r] * 0.25 == P + LAV + 11.25
        assert g.lys["stop_t_fortsaet"].iloc[r] * 0.25 == P + LAV - 0.5
        f = _forloeb(g, side=k4.FORTSAET)
        assert f.n == 1 and f.j[0] == _j(g, "09:21")
        assert f.fyld[0] == pytest.approx(P + LAV + 11.25 + SLIP, abs=1e-12)
        assert f.risiko[0] == pytest.approx(RISIKO, abs=1e-12)    # samme risiko som modellen
        assert _forloeb(g).n == 0                                   # modellen fyldes ikke

    def test_konstant_maal_den_anden_vej(self):
        g = _g(nmod_scenarie())
        f = _forloeb(g, side=k4.FORTSAET)
        vwap = g.s.maal_vwap[f.j[0]]
        afstand = f.fyld[0] - vwap
        assert f.rr[0] == pytest.approx(afstand / f.risiko[0], abs=1e-12)
        h = k4.handelstabel(g, k4.FORTSAET, f).iloc[0]
        assert h["udfald"] == k4.MAAL and h["exit_i"] == _j(g, "10:00")
        assert h["R_brutto"] == f.rr[0]
        # Målet flytter sig ikke med VWAP: 09:30 med enorm volumen ændrer intet.
        b = nmod_scenarie()
        b.bar("09:30", LAV + 12, LAV + 12, LAV + 12, LAV + 12, vol=1e10)
        g2 = _g(b)
        h2 = k4.handelstabel(g2, k4.FORTSAET, _forloeb(g2, side=k4.FORTSAET)).iloc[0]
        assert h2["R_brutto"] == h["R_brutto"] and h2["exit_i"] == h["exit_i"]

    def test_1R_reglen_gaelder_n_mod(self):
        f = _forloeb(_g(nmod_scenarie()), side=k4.FORTSAET)
        assert f.rr[0] >= 1
        assert k4.afstand(100.0, 110.0, True, k4.FORTSAET) == 10.0
        assert k4.afstand(100.0, 95.0, True, k4.FORTSAET) == -5.0

    def test_spejlet_efter_straek_ned(self):
        g = _g(hoved(-1))
        r = _r(g, "09:15")
        assert not bool(g.lys["long_fortsaet"].iloc[r])
        assert g.lys["trigger_t_fortsaet"].iloc[r] * 0.25 == P - (LAV + 11.25)
        assert g.lys["stop_t_fortsaet"].iloc[r] * 0.25 == P - (LAV - 0.5)


# ===========================================================================
# §11.2 test 13 — den nye motor er simuler_handel med et konstant mål
# ===========================================================================

class TestMotor:
    def _sti(self, rng, n=400):
        c = 15000 + np.cumsum(rng.normal(0, 2, n)).round(2)
        h = c + rng.exponential(1.5, n).round(2)
        l = c - rng.exponential(1.5, n).round(2)
        return h, l, c

    def test_bit_for_bit_som_simuler_handel(self):
        rng = np.random.default_rng(4)
        tilfaelde = 0
        for _ in range(60):
            h, l, c = self._sti(rng)
            n = len(c)
            for _ in range(40):
                entry_i = int(rng.integers(0, n - 5))
                long = bool(rng.integers(0, 2))
                risiko = float(rng.choice([0.885425, 2.135425, 5.0, 11.885425, 30.25]))
                maal_r = float(rng.choice([0.5, 1.0, 1.5, 2.0, 3.7, 7.25]))
                entry = float(c[entry_i] + rng.normal(0, 1))
                cutoff = int(rng.choice([n, n + 3, entry_i + int(rng.integers(0, 200))]))
                gammel = trinA.simuler_handel(h, l, c, entry_i, entry, long, risiko, None,
                                              cutoff, n, True, maal_r)
                for m in (maal_r, np.full(max(cutoff, entry_i) - entry_i + 1, maal_r)):
                    ny = k4.simuler_handel_maal(h, l, c, entry_i, entry, long, risiko, m,
                                                cutoff, n)
                    assert ny[0] == gammel[0] and ny[2] == gammel[2]
                    assert ny[1] == gammel[1]            # bit for bit
                tilfaelde += 1
        assert tilfaelde == 2400

    def test_alle_udfald_forekommer(self):
        rng = np.random.default_rng(4)
        set_ = set()
        for _ in range(30):
            h, l, c = self._sti(rng)
            for e in range(0, 300, 7):
                set_.add(k4.simuler_handel_maal(h, l, c, e, float(c[e]), True, 5.0, 2.0,
                                                e + (120 if e % 2 else 3), len(c))[0])
            set_.add(k4.simuler_handel_maal(h, l, c, 390, float(c[390]), True, 50.0, 9.0,
                                            len(c), len(c))[0])
        assert set_ == {k4.MAAL, k4.STOP, k4.TIDSEXIT, k4.CENSURERET}

    def test_tvetydig_som_kandidat_3(self):
        h = np.array([10.0, 10.0, 13.0])
        l = np.array([9.0, 9.0, 4.0])
        c = np.array([10.0, 10.0, 8.0])
        u, r, e, tv, rb = k4.simuler_handel_maal(h, l, c, 0, 10.0, True, 5.0, 0.5, 3, 3)
        assert u == k4.STOP and e == 2 and tv and rb == 0.5


# ===========================================================================
# Fladning, rul og halve dage
# ===========================================================================

class TestRammer:
    def test_tidsexit_1450(self):
        g = _g(brud_ned(udmattelse(Bygger())))
        h = _handler(g).iloc[0]
        assert h["udfald"] == k4.TIDSEXIT
        assert g.s.tider[h["exit_i"]] == _ct("14:49").value

    def test_vinduet_slutter_1430(self):
        g = _g(hoved())
        assert _kl(g, [len(g.lys) - 1]) == ["14:25"]
        assert not bool(g.lys["naeste_ok"].iloc[-1])

    def test_rul_i_handelstiden_springer_dagen_over(self):
        g = _g(hoved().rul("12:00"))
        assert len(g.lys) == 0 and g.info["rul_dage_n"] == 1

    def test_halv_dag(self):
        """2023-11-24: vinduet slutter 11:30 CT; Globex lukker 12:15 CT."""
        halv, soen = "2023-11-24", "2023-11-26"
        b = brud_ned(udmattelse(Bygger(dage=(halv,), til="12:15")))
        nat = pd.date_range(_ct("17:00", soen), _ct("17:30", soen), freq="1min",
                            inclusive="left").rename("time")
        b.df = pd.concat([b.df, pd.DataFrame({"open": P, "high": P + 1, "low": P - 1,
                                              "close": P, "volume": 1.0,
                                              "instrument_id": np.int64(1)}, index=nat)])
        g = _g(b, halv)
        sidste = pd.Timestamp(int(g.lys["tid_ns"].iloc[-1]), tz="UTC").tz_convert(CT)
        assert sidste.strftime("%H:%M") == "11:25"
        h = _handler(g).iloc[0]
        assert h["udfald"] == k4.TIDSEXIT
        assert g.s.tider[h["exit_i"]] == _ct("12:14", halv).value

    def test_ublokeret_fyld_er_dagsforloebets(self):
        g = _g(to_setups())
        f = _forloeb(g, n=2)
        for q in range(f.n):
            r = f.raekke[q]
            assert g.lys["j0_tilbage"].iloc[r] == f.j[q]
            assert g.lys["fyld0_tilbage"].iloc[r] == f.fyld[q]
            assert g.lys["rr0_tilbage"].iloc[r] == f.rr[q]

    def test_handlen_regnes_en_gang(self):
        g = _g(hoved())
        _handler(g)
        n = len(g.cache)
        _handler(g)
        assert len(g.cache) == n == 1


# ===========================================================================
# Optællingen: intet R
# ===========================================================================

class TestOptaelling:
    def test_intet_R_og_kun_noedvendige_exit(self, monkeypatch):
        g = _g(to_setups())
        kald = []
        rigtig = k4.simuler_handel_maal

        def taelle(*a, **kw):
            kald.append(a[3])
            return rigtig(*a, **kw)

        monkeypatch.setattr(k4, "simuler_handel_maal", taelle)
        o = k4.optaelling(g)
        noegler = {x for r in o["varianter"] + o["aar"] + o["ntid"] for x in r}
        for x in noegler:
            assert not x.startswith(("R_", "middel_R", "win_rate", "udfald", "tvetydig",
                                     "maal_R")), x
        assert len(g.cache) == 0
        # 2/dag: kun dagens første handel, og kun når et senere setup venter (modellen og
        # N-mod hver for sig). 1/dag: intet.
        model = {(r["k"], r["pr_dag"]): r for r in o["varianter"] if r["model"] == "EMT"}
        assert model[(1.5, 1)]["handler_n"] == 1 and model[(1.5, 2)]["handler_n"] == 2
        assert set(kald) == {_j(g, "09:22")}

    def test_raekkerne(self):
        g = _g(hoved())
        o = k4.optaelling(g)
        model = {(r["k"], r["pr_dag"]): r for r in o["varianter"] if r["model"] == "EMT"}
        r = model[(1.5, 1)]
        assert r["udmattelseslys_n"] == 1 and r["handler_n"] == 1 and r["short_n"] == 1
        assert r["signaltid_p50"] == 9 * 60 + 15
        assert r["RR_p50"] == pytest.approx((FYLD - g.s.maal_vwap[_j(g, "09:22")]) / RISIKO)
        assert r["sigma_R"] == pytest.approx(math.sqrt(r["RR_middel"]))
        assert r["MDE_R_sidak6"] == pytest.approx(k4.Z_SIDAK6 * r["sigma_R"])
        assert not r["betingelse_ok"]
        nt = {(x["k"], x["pr_dag"]): x for x in o["ntid"]}[(1.5, 1)]
        assert nt["pulje_n"] == 2 and nt["celler_n"] == 1
        md = k4.optaelling_md(o, {"koert_utc": "x", "head": "0" * 40})
        assert "| EMT | k = 1,5 · 1/dag |" in md
        assert "middel_R" not in md and "win_rate" not in md


# ===========================================================================
# §7 og §8
# ===========================================================================

class TestStatistik:
    def test_cr1_er_t_intervallet_ved_en_pr_dag(self):
        rng = np.random.default_rng(1)
        r = rng.normal(0.1, 1.2, 50)
        assert np.allclose(k4.middel_ci_cr1(r, np.arange(50)), mean_ci_t(r), atol=1e-12)

    def test_cr1_er_bredere_ved_korrelerede_dage(self):
        rng = np.random.default_rng(2)
        dag = rng.normal(0, 1, 100)
        r = np.repeat(dag, 2) + rng.normal(0, 0.1, 200)
        lo, hi = k4.middel_ci_cr1(r, np.repeat(np.arange(100), 2))
        lo_t, hi_t = mean_ci_t(r)
        assert hi - lo > 1.3 * (hi_t - lo_t)

    def test_z_vaerdierne(self):
        a = 1 - 0.95 ** (1 / 6)
        assert round(norm.ppf(1 - a) + norm.ppf(0.8), 4) == k4.Z_SIDAK6
        assert round(norm.ppf(0.95) + norm.ppf(0.8), 4) == k4.Z_UKORR

    @pytest.mark.parametrize("n,s122,s141,s173", [(300, 0.227, 0.263, 0.322),
                                                  (500, 0.176, 0.204, 0.250),
                                                  (800, 0.139, 0.161, 0.197)])
    def test_tabellen_i_paragraf_7(self, n, s122, s141, s173):
        assert round(k4.mde(n, 1.22), 3) == s122
        assert round(k4.mde(n, 1.41), 3) == s141
        assert round(k4.mde(n, 1.73), 3) == s173

    def test_handler_der_kraeves(self):
        assert math.ceil((k4.Z_SIDAK6 * 1.41 / 0.20) ** 2) == 518
        assert math.ceil((k4.Z_SIDAK6 * 1.22 / 0.20) ** 2) == 388

    def test_sigma_er_kvadratroden_af_middel_RR(self):
        assert k4.sigma_R([1.0, 3.0]) == pytest.approx(math.sqrt(2.0))


def _b(p, m, lo):
    return {"p_FWE": p, "middel_R_netto": m, "middel_R_netto_ci95_lo": lo}


class TestBeslutning:
    V = k4.VARIANTER

    def _alle(self):
        return {v: _b(0.9, -0.1, -0.2) for v in self.V}

    def test_raekke_1_fryser_hoejeste_ci_nedre(self):
        b = k4.beslutning(self._alle() | {self.V[0]: _b(0.01, 0.25, 0.05),
                                              self.V[3]: _b(0.02, 0.30, 0.10)})
        assert b["raekke"] == 1 and b["variant"] == self.V[3]

    def test_raekke_2(self):
        b = k4.beslutning(self._alle() | {self.V[1]: _b(0.01, 0.15, 0.02)})
        assert b["raekke"] == 2

    def test_raekke_3(self):
        b = k4.beslutning(self._alle() | {self.V[2]: _b(0.30, 0.25, 0.05)})
        assert b["raekke"] == 3 and b["kandidater"] == [self.V[2]]

    def test_raekke_4(self):
        assert k4.beslutning(self._alle())["raekke"] == 4
        b = k4.beslutning(self._alle() | {self.V[0]: _b(0.05, 0.25, 0.0)})
        assert b["raekke"] == 4


# ===========================================================================
# Den rigtige kørsel, på en syntetisk serie
# ===========================================================================

class TestHeleKoerslen:
    def test_analyse_og_rapport(self):
        b = to_setups()
        b2 = hoved(-1)
        b2.df.index = b2.df.index + pd.Timedelta(days=1)
        b.df = pd.concat([b.df, b2.df])
        g = _g(b, DAG, DAG2)
        with np.errstate(all="ignore"):
            res = k4.analyse(g, n_reps=4)
        assert len(res["gentagelser"]) == 4
        r = res["afgoerelse"]["forsigtig"]["raekker"][(1.5, 2)]
        assert r["handler_n"] == 3 and r["ci_metode"] == "CR1 pr. dag"
        assert r["anden_handel_n"] == 1
        meta = {"koert_utc": "x", "head": "0" * 40,
                "commits": {k4._rel(k4.PREREG): "a" * 40,
                            k4._rel(k4.Path(k4.__file__)): "b" * 40}}
        md = k4.skriv_md(res, meta)
        assert "Hovedtabel" in md and "N-mod" in md
        tabel = k4.lang_tabel(res)
        assert (tabel["tabel"] == "hoved").sum() == 2 * len(k4.VARIANTER)


class TestRegression:
    def test_konstanterne(self):
        assert (k4.REGRESSION_K3_HANDLER_N, k4.REGRESSION_K3_MIDDEL_R_NETTO) == (1168, -0.0712)
        assert len(k4.VARIANTER) == 6
