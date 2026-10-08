"""Tests for research/b4_k5_vwap_trend.py — B4 kandidat 5, VWAP-trend.

Præregistreringen er ``research/prereg/b4_k5_vwap_trend.md``. §11.2's 13 syntetiske tests
står først, i præregistreringens rækkefølge. Derefter det de bygger på:

- σ_dag, MDE-tabellen og styrken i §7;
- break-even, hit ratio og beslutningsreglen i §8-§9;
- diagnoserne: halve timer, største tab, de sidste 5 minutter og altid-long;
- optællingen regner ingen P&L;
- hele den rigtige kørsel på en syntetisk serie, så den ikke fejler første gang den køres.

Alle serier er syntetiske. Ingen test læser prisdata.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from data import sessions
from research import b4_k2_nowick as k2
from research import b4_k5_vwap_trend as k5
from research.normal import norm
from research.stats import mean_ci_t

CT = "America/Chicago"
DAG = "2023-06-14"          # onsdag, sommertid: CT = UTC − 5
DAG2 = "2023-06-15"
KORT = "2023-11-24"         # fredag efter Thanksgiving: NYSE lukker 12:00 CT
UGE = ("2023-06-12", "2023-06-13", "2023-06-14", "2023-06-15", "2023-06-16")
P = 14569.0                 # 29.138 / P = 2: dagens niveau er det dobbelte
TUNG = 1e6
HELE1, UDEN1, HELE5, UDEN5 = (1, k5.HELE), (1, k5.UDEN), (5, k5.HELE), (5, k5.UDEN)


def _ct(hhmm: str, dag: str = DAG) -> pd.Timestamp:
    return pd.Timestamp(f"{dag} {hhmm}").tz_localize(CT).tz_convert("UTC")


def _plus(hhmm: str, minutter: int) -> str:
    return (pd.Timestamp(f"2000-01-01 {hhmm}") + pd.Timedelta(minutes=minutter)).strftime("%H:%M")


def _g_min(hhmm: str) -> int:
    """Minutter efter 08:30 CT."""
    t = pd.Timestamp(f"2000-01-01 {hhmm}")
    return (t.hour * 60 + t.minute) - (8 * 60 + 30)


# ===========================================================================
# Byggeklodser
# ===========================================================================

class Bygger:
    """1m-barer fra 07:00 til 16:00 CT pr. dag. I RTH fladt på P (open = high = low =
    close), 08:30-baren med volumen 1e6 og resten med 1, så VWAP står på P: et lys der
    lukker over P giver long, under P short, og på P intet. Uden for RTH ligger prisen 500
    point højere med volumen 1e6, så en VWAP der tog de barer med, ville ligge langt fra P.

    Priserne er afstande fra P."""

    def __init__(self, dage=(DAG,), fra: str = "07:00", til: str = "16:00"):
        dele = []
        for d in dage:
            idx = pd.date_range(_ct(fra, d), _ct(til, d), freq="1min",
                                inclusive="left").rename("time")
            rth = sessions.rth_mask(idx, 1)
            px = np.where(rth, P, P + 500.0)
            vol = np.where(rth, 1.0, TUNG)
            vol[idx == _ct("08:30", d)] = TUNG
            dele.append(pd.DataFrame({"open": px, "high": px, "low": px, "close": px,
                                      "volume": vol, "instrument_id": np.int64(1)}, index=idx))
        self.df = pd.concat(dele)
        self.dag0 = dage[0]

    def _d(self, dag):
        return self.dag0 if dag is None else dag

    def bar(self, hhmm, o=0.0, h=None, l=None, c=None, vol=None, dag=None) -> "Bygger":
        c = o if c is None else c
        h = max(o, c) if h is None else h
        l = min(o, c) if l is None else l
        t = _ct(hhmm, self._d(dag))
        self.df.loc[t, ["open", "high", "low", "close"]] = [P + o, P + h, P + l, P + c]
        if vol is not None:
            self.df.loc[t, "volume"] = vol
        return self

    def fra(self, hhmm, x, til: str = "15:00", vol=None, dag=None) -> "Bygger":
        """Barer uden udsving på afstand x fra P, fra ``hhmm`` til (ikke med) ``til``."""
        d = self._d(dag)
        m = (self.df.index >= _ct(hhmm, d)) & (self.df.index < _ct(til, d))
        self.df.loc[m, ["open", "high", "low", "close"]] = P + x
        if vol is not None:
            self.df.loc[m, "volume"] = vol
        return self

    def fjern(self, hhmm, til: str | None = None, dag=None) -> "Bygger":
        d = self._d(dag)
        slut = _ct(til, d) if til else _ct(hhmm, d) + pd.Timedelta(minutes=1)
        self.df = self.df[(self.df.index < _ct(hhmm, d)) | (self.df.index >= slut)]
        return self

    def rul(self, hhmm, dag=None, spring: float = 0.0) -> "Bygger":
        m = self.df.index >= _ct(hhmm, self._d(dag))
        self.df.loc[m, "instrument_id"] = np.int64(2)
        self.df.loc[m, ["open", "high", "low", "close"]] += spring
        return self


def sav(b: Bygger, dag=None, fra: str = "08:40", til: str = "14:40", trin: int = 20,
        x: float = 3.0) -> Bygger:
    """Skiftevis +x og −x hvert ``trin`` minut: en vending ved hvert skift."""
    t, fortegn = fra, 1
    while t < til:
        b.fra(t, fortegn * x, til=_plus(t, trin), dag=dag)
        t, fortegn = _plus(t, trin), -fortegn
    return b


def _g(b: Bygger) -> k5.Grundlag:
    return k5.byg_grundlag(b.df)


def _h(g, v=HELE1) -> k5.Handler:
    return k5.handler(g, v)


def _liste(g, h) -> list[tuple]:
    """(dag, indgang, udgang, retning, udgangstype) pr. handel, tider som HH:MM CT."""
    def hhmm(gm):
        m = 8 * 60 + 30 + int(gm)
        return f"{m // 60:02d}:{m % 60:02d}"
    return [(str(g.dage[g.inkl[r]].date()), hhmm(a), hhmm(b), int(d), k5.UDGANGE[int(u)])
            for r, a, b, d, u in zip(h.rad, h.ind_g, h.ud_g, h.retning, h.udgang)]


# ===========================================================================
# §11.2: de 13 syntetiske tests
# ===========================================================================

class TestVWAP:
    """Test 1: VWAP starter kl. 08:30 CT, bruger kun RTH-barer og hlc3 × volume, og
    nulstilles hver dag."""

    def test_rth_hlc3_volumen_og_nulstilling(self):
        b = Bygger(dage=(DAG, DAG2))
        b.bar("08:30", 0, 4, -2, 1, vol=2.0)                 # hlc3 = 1
        b.bar("08:31", 1, 7, 1, 4, vol=3.0)                  # hlc3 = 4
        b.bar("08:32", 4, 4, -5, -2, vol=5.0)                # hlc3 = −1
        b.bar("08:30", 0, 9, 0, 3, vol=4.0, dag=DAG2)        # hlc3 = 4
        g = _g(b)
        assert g.vwap[0, 0] == pytest.approx(P + 1)
        assert g.vwap[0, 1] == pytest.approx(P + (2 * 1 + 3 * 4) / 5)
        assert g.vwap[0, 2] == pytest.approx(P + (2 * 1 + 3 * 4 - 5 * 1) / 10)
        # Nulstillet næste dag: kun dagens egen 08:30-bar, ikke gårsdagens eller natten.
        assert g.vwap[1, 0] == pytest.approx(P + 4)

    def test_hele_raekken_mod_haandregning(self):
        b = Bygger(dage=(DAG, DAG2))
        rng = np.random.default_rng(5)
        for t in ("08:30", "09:13", "11:40", "14:59"):
            o, c = rng.normal(0, 3, 2)
            b.bar(t, o, max(o, c) + 1, min(o, c) - 1, c, vol=float(rng.integers(1, 9)))
        g = _g(b)
        for r, d in enumerate((DAG, DAG2)):
            x = b.df[sessions.rth_mask(b.df.index, 1)]
            x = x[(x.index >= _ct("08:30", d)) & (x.index < _ct("15:00", d))]
            hlc3 = (x["high"] + x["low"] + x["close"]) / 3
            ventet = (hlc3 * x["volume"]).cumsum() / x["volume"].cumsum()
            assert np.allclose(g.vwap[r], ventet.to_numpy(), rtol=0, atol=1e-9)

    def test_barer_uden_for_rth_bruges_ikke(self):
        b = Bygger()
        g = _g(b)
        # Natten og eftermiddagen ligger 500 point højere med volumen 1e6.
        assert np.allclose(g.vwap[0], P)


class TestFemMinutter:
    """Test 2: 5m bruger VWAP ved lysets sidste minut, regnet på 1m."""

    def test_vwap_ved_sidste_minut(self):
        b = Bygger()
        b.fra("09:00", 2, til="09:04")
        # 09:04: close P+1, men hlc3 = P+4 med tung volumen: VWAP ≈ P+3 ved 09:04, ≈ P før.
        b.bar("09:04", 1, 10, 1, 1, vol=3 * TUNG)
        g = _g(b)
        lys = g.lys[5]
        k = _g_min("09:00") // 5
        assert lys.vwap[0, k] == g.vwap[0, _g_min("09:04")]
        assert lys.close[0, k] == P + 1
        assert g.vwap[0, _g_min("09:03")] < P + 1 < lys.vwap[0, k]
        assert lys.signal[0, k] == -1
        h = _h(g, HELE5)
        assert _liste(g, h) == [(DAG, "09:05", "14:55", -1, "fladt")]

    def test_samme_lys_som_aggregate(self):
        b = sav(Bygger(dage=(DAG, KORT)))
        b.fjern("10:02", dag=DAG)
        g = _g(b)     # byg_grundlag sammenligner selv med data.resample.aggregate
        assert g.info["lys_5m_n"] == 78 + 42


class TestFoersteHandel:
    """Test 3: første handel besluttes ved første lys' lukning og udføres ved næste lys'
    åbning. Close lig VWAP giver ingen position."""

    def test_foerste_lys_lukker_over(self):
        b = Bygger()
        b.bar("08:30", 0, 3, 0, 3, vol=TUNG)         # hlc3 = P+2 = VWAP < close
        b.fra("08:31", 3)
        g = _g(b)
        assert _liste(g, _h(g, HELE1)) == [(DAG, "08:31", "14:55", 1, "fladt")]
        assert _liste(g, _h(g, HELE5)) == [(DAG, "08:35", "14:55", 1, "fladt")]

    def test_close_lig_vwap_venter(self):
        b = Bygger()                                 # 08:30: close = hlc3 = VWAP
        b.fra("09:00", 1)
        g = _g(b)
        assert g.lys[1].signal[0, 0] == 0
        assert _liste(g, _h(g, HELE1)) == [(DAG, "09:01", "14:55", 1, "fladt")]
        assert _liste(g, _h(g, HELE5)) == [(DAG, "09:05", "14:55", 1, "fladt")]

    def test_short_ved_lukning_under(self):
        b = Bygger()
        b.bar("08:30", 0, 0, -3, -3, vol=TUNG)
        b.fra("08:31", -3)
        g = _g(b)
        assert _liste(g, _h(g, HELE1)) == [(DAG, "08:31", "14:55", -1, "fladt")]


class TestVending:
    """Test 4: vending kun ved en lukning på den anden side. Et kryds inde i lyset vender
    ikke."""

    def test_kryds_inde_i_lyset_vender_ikke(self):
        b = Bygger()
        b.fra("09:00", 2)
        b.bar("10:00", 2, 2, -20, 2)                 # handler langt under VWAP, lukker over
        b.bar("10:30", 2, 2, -5, -5)                 # lukker under
        b.fra("10:31", -5)
        g = _g(b)
        h = _h(g, HELE1)
        assert _liste(g, h) == [(DAG, "09:01", "10:31", 1, "vending"),
                                (DAG, "10:31", "14:55", -1, "fladt")]
        # Vendingen lukker og åbner til samme pris.
        assert h.ud_i[0] == h.ind_i[1]

    def test_5m_kryds_i_et_1m_lys_vender_ikke(self):
        b = Bygger()
        b.fra("09:00", 2)
        b.bar("10:01", 2, 2, -5, -5)                 # 1m-lyset lukker under, 5m-lyset over
        g = _g(b)
        assert len(_liste(g, _h(g, HELE1))) == 3
        assert _liste(g, _h(g, HELE5)) == [(DAG, "09:05", "14:55", 1, "fladt")]


class TestUdfoerelse:
    """Test 5: udførelse ved næste lys' åbning. Mangler et minut, bruges næste bar, og det
    tælles."""

    def test_naeste_aabning(self):
        b = Bygger()
        b.fra("09:00", 2)
        b.bar("09:01", 7, 9, 6, 8)
        g = _g(b)
        h = _h(g, HELE1)
        assert g.s_o[h.ind_i[0]] == P + 7
        assert h.tael["udfoert_senere_n"] == 0

    def test_manglende_minut_1m(self):
        b = Bygger()
        b.fra("09:00", 2)
        b.fjern("09:01")
        g = _g(b)
        h = _h(g, HELE1)
        assert _liste(g, h) == [(DAG, "09:02", "14:55", 1, "fladt")]
        assert h.tael["udfoert_senere_n"] == 1

    def test_manglende_minut_5m(self):
        b = Bygger()
        b.fra("09:00", 2)
        b.fjern("09:05")
        g = _g(b)
        h = _h(g, HELE5)
        assert _liste(g, h) == [(DAG, "09:06", "14:55", 1, "fladt")]
        assert h.tael["udfoert_senere_n"] == 1

    def test_manglende_fladt_minut(self):
        b = Bygger()
        b.fra("09:00", 2)
        b.fjern("14:55", "14:57")
        g = _g(b)
        h = _h(g, HELE1)
        assert _liste(g, h) == [(DAG, "09:01", "14:57", 1, "fladt")]
        assert h.tael["udfoert_senere_n"] == 1


class TestFladt:
    """Test 6: fladt ved åbningen kl. 14:55 CT. Et signal ved lukningen kl. 14:54 giver
    ingen ny position."""

    def test_signal_kl_1454_giver_intet(self):
        b = Bygger()
        b.fra("09:00", 2)
        b.fra("14:54", -5)
        g = _g(b)
        h = _h(g, HELE1)
        assert _liste(g, h) == [(DAG, "09:01", "14:55", 1, "fladt")]
        assert g.s_o[h.ud_i[0]] == P - 5

    def test_signal_kl_1453_giver_et_minut(self):
        b = Bygger()
        b.fra("09:00", 2)
        b.fra("14:53", -5)
        g = _g(b)
        assert _liste(g, _h(g, HELE1)) == [(DAG, "09:01", "14:54", 1, "vending"),
                                           (DAG, "14:54", "14:55", -1, "fladt")]

    def test_5m_lyset_1450_giver_intet(self):
        b = Bygger()
        b.fra("09:00", 2)
        b.fra("14:50", -5)                           # 5m-lyset 14:50-14:55 lukker under
        g = _g(b)
        assert _liste(g, _h(g, HELE5)) == [(DAG, "09:05", "14:55", 1, "fladt")]
        b2 = Bygger()
        b2.fra("09:00", 2)
        b2.fra("14:45", -5)
        g2 = _g(b2)
        assert _liste(g2, _h(g2, HELE5)) == [(DAG, "09:05", "14:50", 1, "vending"),
                                             (DAG, "14:50", "14:55", -1, "fladt")]


class TestMiddag:
    """Test 7: uden middag: fladt kl. 11:00 CT, ingen position til 14:00, ny position kl.
    14:00 ud fra det sidst lukkede lys og hele dagens VWAP."""

    def _bygger(self) -> Bygger:
        b = Bygger()
        b.fra("09:00", 2)
        b.fra("11:00", 10, til="13:59", vol=10 * TUNG)   # pausen trækker VWAP op mod P+10
        b.bar("13:59", 5)                                # under hele dagens VWAP
        b.fra("14:00", 5)
        return b

    def test_1m(self):
        g = _g(self._bygger())
        vw = g.vwap[0, _g_min("13:59")]
        assert vw > P + 9.5                              # uden pausen ville den være ≈ P
        assert _liste(g, _h(g, UDEN1)) == [(DAG, "09:01", "11:00", 1, "pause"),
                                           (DAG, "14:00", "14:55", -1, "fladt")]
        assert _liste(g, _h(g, HELE1)) == [(DAG, "09:01", "14:00", 1, "vending"),
                                           (DAG, "14:00", "14:55", -1, "fladt")]

    def test_5m(self):
        g = _g(self._bygger())
        assert _liste(g, _h(g, UDEN5)) == [(DAG, "09:05", "11:00", 1, "pause"),
                                           (DAG, "14:00", "14:55", -1, "fladt")]

    def test_samme_handler_foer_pausen(self):
        g = _g(sav(Bygger()))
        hele, uden = _liste(g, _h(g, HELE1)), _liste(g, _h(g, UDEN1))
        foer = [x for x in hele if x[2] <= "11:00"]
        assert uden[:len(foer)] == foer
        assert all(x[1] >= "14:00" or x[2] <= "11:00" for x in uden)


class TestKortdag:
    """Test 8: kortdage: fladt kl. 11:55 CT. Uden middag lukker kl. 11:00 og åbner ikke
    igen."""

    def test_kortdag(self):
        b = Bygger(dage=(KORT,))
        b.fra("09:00", 2, dag=KORT)
        b.fra("11:30", -5, dag=KORT)
        g = _g(b)
        assert g.n_min[0] == 210 and g.flad[0] == _g_min("11:55")
        assert _liste(g, _h(g, HELE1)) == [(KORT, "09:01", "11:31", 1, "vending"),
                                           (KORT, "11:31", "11:55", -1, "fladt")]
        assert _liste(g, _h(g, UDEN1)) == [(KORT, "09:01", "11:00", 1, "pause")]
        assert _liste(g, _h(g, UDEN5)) == [(KORT, "09:05", "11:00", 1, "pause")]


class TestNormering:
    """Test 9: normering og omkostning efter §4g, med L_d fra den ujusterede serie."""

    def _bygger(self) -> Bygger:
        b = Bygger(dage=(DAG, DAG2))
        b.fra("09:00", 2)
        b.fra("14:30", 12)
        b.rul("18:00", spring=100.0)                 # aftenen efter DAG: ny kontrakt +100
        return b

    def test_L_d_er_ujusteret(self):
        b = self._bygger()
        g = _g(b)
        assert g.L[0] == P and g.L[1] == P + 100
        adj, _ = k2.forskelsjuster(b.df[["open", "high", "low", "close", "instrument_id"]])
        assert adj.loc[_ct("08:30"), "open"] == P + 100   # den justerede ville give P+100

    def test_netto_usd(self):
        g = _g(self._bygger())
        h = _h(g, HELE1)
        res = k5.resultat(g, h)
        i = int(np.flatnonzero(h.rad == 0)[0])
        assert res["pt"][i] == 10.0
        assert res["skala"][i] == 2.0
        assert res["brutto_usd"][i] == pytest.approx(10 * 2 * 2)
        assert res["netto_usd"][i] == pytest.approx(40 - 2.627)
        assert res["nominelt_usd"][i] == pytest.approx(10 * 2 - 2.627)
        assert res["bp"][i] == pytest.approx(10 / P * 1e4)
        dag = k5.pr_dag(g, h, res["netto_usd"])
        assert dag[0] == pytest.approx(res["netto_usd"][h.rad == 0].sum())

    def test_omkostningerne(self):
        assert k5.OMK_USD == 2.627
        assert k5.OMK_DIAGNOSE_USD == pytest.approx(2.627 + 2 * 0.5417 * 0.25 * 2)
        assert round(k5.OMK_DIAGNOSE_USD, 3) == 3.169
        assert k5.NQ_NIVEAU == 29138.0


class TestNRetning:
    """Test 10: N-retning: samme handler og antal. Samme indgangsminut giver samme retning
    i begge middagsvarianter. Middel over mange gentagelser er cirka −omkostningen."""

    def _g(self):
        b = sav(Bygger(dage=(DAG, DAG2)))
        sav(b, dag=DAG2, fra="08:45", trin=15, x=4.0)
        return _g(b)

    def test_samme_handler(self):
        g = self._g()
        hd, fl = k5.forbered(g)
        for v in k5.VARIANTER:
            assert fl[v].n == hd[v].n
            assert np.array_equal(fl[v].ind_g, hd[v].ind_g)
            assert np.array_equal(fl[v].dag, g.inkl[hd[v].rad])
            # Flytningen er handlens brutto uden retning.
            res = k5.resultat(g, hd[v])
            assert np.allclose(fl[v].flyt_usd * hd[v].retning, res["brutto_usd"])

    def test_samme_indgangsminut_samme_retning(self):
        g = self._g()
        hd, fl = k5.forbered(g)
        for tf in k5.TIDSRAMMER:
            a, b = fl[(tf, k5.HELE)], fl[(tf, k5.UDEN)]
            faelles = {(d, m) for d, m in zip(a.dag, a.ind_g)} & {(d, m) for d, m in
                                                                   zip(b.dag, b.ind_g)}
            assert len(faelles) >= 5
            for rep in range(6):
                bits = k5.nret_bits(len(g.dage), rep, tf)
                ra = dict(zip(zip(a.dag, a.ind_g), k5.nret_retning(bits, a)))
                rb = dict(zip(zip(b.dag, b.ind_g), k5.nret_retning(bits, b)))
                assert all(ra[x] == rb[x] for x in faelles)

    def test_deterministisk_og_uafhaengig_af_tidsramme(self):
        a = k5.nret_bits(10, 3, 1)
        assert np.array_equal(a, k5.nret_bits(10, 3, 1))
        assert not np.array_equal(a, k5.nret_bits(10, 3, 5))
        assert not np.array_equal(a, k5.nret_bits(10, 4, 1))
        assert set(np.unique(a)) == {0, 1}

    def test_middel_er_minus_omkostningen(self):
        g = self._g()
        hd, fl = k5.forbered(g)
        R = 3000
        reps = [k5.nret_gentagelse(g, fl, rep) for rep in range(R)]
        for v in k5.VARIANTER:
            m = np.array([r[v] for r in reps])
            ventet = -k5.OMK_USD * hd[v].n / g.n
            se = math.sqrt(float((fl[v].flyt_usd ** 2).sum())) / g.n / math.sqrt(R)
            assert abs(m.mean() - ventet) < 4 * se
            # Hver gentagelse har modellens handler og omkostning.
            assert m.std() > 0


class TestWestfallYoung:
    """Test 11: Westfall-Young og p_FWE som i kandidat 2."""

    def _tal(self, obs: dict) -> dict:
        return {v: {"middel_netto_usd_dag": x, "netto_ci95_lo": x - 10}
                for v, x in obs.items()}

    def test_som_kandidat_2_og_haandregnet(self):
        rng = np.random.default_rng(3)
        null = {v: rng.normal(-30 - 5 * i, 4 + i, 500) for i, v in enumerate(k5.VARIANTER)}
        obs = {v: -30 + 3 * i for i, v in enumerate(k5.VARIANTER)}
        afg = k5.afgoerelse(self._tal(obs), null)
        wy = k2.westfall_young(obs, null)
        M = np.column_stack([null[v] for v in k5.VARIANTER])
        med, sd = np.median(M, axis=0), M.std(axis=0, ddof=1)
        maks = ((M - med) / sd).max(axis=1)
        for i, v in enumerate(k5.VARIANTER):
            t = (obs[v] - med[i]) / sd[i]
            p = (1 + int((maks >= t).sum())) / 501
            r = afg["raekker"][v]
            assert r["t_v"] == pytest.approx(t)
            assert r["p_FWE"] == pytest.approx(p) == wy["pr_variant"][v]["p_FWE"]
            assert r["N_retning_p50"] == pytest.approx(np.percentile(null[v], 50))

    def test_ensidet(self):
        rng = np.random.default_rng(4)
        null = {v: rng.normal(0, 1, 500) for v in k5.VARIANTER}
        lav = k5.afgoerelse(self._tal({v: -10.0 for v in k5.VARIANTER}), null)
        hoej = k5.afgoerelse(self._tal({v: 10.0 for v in k5.VARIANTER}), null)
        assert all(r["p_FWE"] == 1.0 for r in lav["raekker"].values())
        assert all(r["p_FWE"] == 1 / 501 for r in hoej["raekker"].values())


class TestRul:
    """Test 12: en rulle inden for RTH får koden til at stoppe med en fejl."""

    def test_rul_i_rth_stopper(self):
        b = Bygger()
        b.rul("10:00")
        with pytest.raises(ValueError, match="rul inden for RTH"):
            _g(b)

    def test_rul_uden_for_rth_er_i_orden(self):
        b = Bygger(dage=(DAG, DAG2))
        b.rul("18:00")              # serien har ingen aftenbarer: første bar er 07:00 DAG2
        g = _g(b)
        assert g.info["ruller_n"] == 1 and g.info["ruller_i_rth_n"] == 0
        assert g.info["rul_tider_ct"] == "07:00"
        b2 = Bygger()
        b2.rul("15:00")             # lige efter RTH
        assert _g(b2).info["ruller_n"] == 1

    def test_rul_paa_en_udelukket_dag_stopper_ogsaa(self):
        b = Bygger(dage=(DAG, DAG2))
        b.fjern("10:00", "10:10", dag=DAG2)
        b.rul("11:00", dag=DAG2)
        with pytest.raises(ValueError, match="rul inden for RTH"):
            _g(b)


class TestHuller:
    """Test 13: dage med huller efter §4h udelukkes i alle varianter og i nulmodellen."""

    def _g(self):
        b = Bygger(dage=UGE)
        for d in UGE:
            sav(b, dag=d)
        b.fjern("10:00", "10:06", dag=UGE[1])        # 6 manglende minutter: ude
        b.fjern("10:00", "10:05", dag=UGE[2])        # 5: med
        b.fjern("08:30", "08:36", dag=UGE[3])        # første bar 08:36: ude
        b.fjern("08:30", "08:35", dag=UGE[4])        # første bar 08:35: med
        return _g(b)

    def test_udelukkelsen(self):
        g = self._g()
        assert [str(d.date()) for d in g.dage[g.inkl]] == [UGE[0], UGE[2], UGE[4]]
        u = g.udelukket.set_index(g.udelukket["dag"].dt.strftime("%Y-%m-%d"))
        assert u.loc[UGE[1], "grund"] == "hul over 5 min"
        assert u.loc[UGE[1], "maks_hul_min"] == 6
        assert u.loc[UGE[3], "grund"] == "første bar efter 08:35 CT"
        assert g.info["dage_n"] == 3 and g.info["udelukket_n"] == 2
        assert g.info["manglende_minutter_n"] == 10

    def test_ingen_handel_paa_udelukkede_dage(self):
        g = self._g()
        hd, fl = k5.forbered(g)
        ude = {1, 3}                                  # pladserne i ``dage``
        for v in k5.VARIANTER:
            assert hd[v].n > 0
            assert not set(g.inkl[hd[v].rad]) & ude
            assert not set(fl[v].dag) & ude
        # Nulmodellen dividerer med de samme 3 dage.
        r = k5.nret_gentagelse(g, fl, 0)
        for v in k5.VARIANTER:
            d = k5.nret_retning(k5.nret_bits(len(g.dage), 0, v[0]), fl[v])
            assert r[v] == pytest.approx((d @ fl[v].flyt_usd - k5.OMK_USD * fl[v].n) / 3)

    def test_foerste_bar_0835_handler_fra_0836(self):
        g = self._g()
        h = _h(g, HELE1)
        sidste = h.rad == 2
        assert h.ind_g[sidste].min() >= _g_min("08:36")

    def test_ingen_rth_barer(self):
        b = Bygger(dage=(DAG, DAG2))
        b.fjern("08:30", "15:00", dag=DAG2)
        g = _g(b)
        assert g.n == 1 and g.info["udelukket_ingen RTH-barer_n"] == 1


class TestUdelukkedeDageDiagnose:
    """Tillæggets §3: de udelukkede dage rapporteres for sig og indgår ikke i middel, CI,
    nulmodel eller §8."""

    def _bygger(self) -> Bygger:
        b = Bygger(dage=UGE)
        for d in UGE:
            sav(b, dag=d)
        b.fra("09:00", 30, dag=UGE[2])               # stor bevægelse på hul-dagen
        b.fjern("10:00", "10:14", dag=UGE[2])        # 14 manglende minutter: udelukket
        return b

    def test_diagnosen(self):
        b = self._bygger()
        g = _g(b)
        assert g.n == 4 and g.df_1m is not None
        ud = k5.udelukkede_dage(g)
        assert len(ud) == len(k5.VARIANTER)
        r = {(x["tf"], x["middag"]): x for x in ud}[HELE1]
        assert r["dag"] == UGE[2] and r["grund"] == "hul over 5 min" and r["handler_n"] >= 1
        # Positionen holdes gennem stoppet: én long fra 08:41 (P+3) til fladt.
        gu = k5.byg_grundlag(b.df, pd.DatetimeIndex([UGE[2]]), udeluk=False)
        h = k5.handler(gu, HELE1)
        assert _liste(gu, h) == [(UGE[2], "08:41", "14:55", 1, "fladt")]
        assert r["dag_netto_usd"] == pytest.approx(
            (b.df.loc[_ct("14:55", UGE[2]), "open"] - (P + 3)) * 2 * 2 - 2.627)
        assert r["intradag_tab_vaerste"] <= 0

    def test_indgaar_ikke_i_middel_ci_nulmodel_eller_8(self):
        b = self._bygger()
        uden = Bygger(dage=UGE)
        uden.df = b.df[(b.df.index < _ct("08:30", UGE[2])) | (b.df.index >= _ct("15:00", UGE[2]))]
        with np.errstate(all="ignore"):
            a = k5.analyse(_g(b), n_reps=20)
            c = k5.analyse(_g(uden), n_reps=20)
        assert a["udelukkede"] and not c["udelukkede"]
        for v in k5.VARIANTER:
            for x in ("middel_netto_usd_dag", "netto_ci95_lo", "netto_ci95_hi", "handler_n"):
                assert a["tal"][v][x] == c["tal"][v][x]
            assert np.array_equal(a["null"][v], c["null"][v])
            assert (a["afgoerelse"]["hoved"]["raekker"][v]
                    == c["afgoerelse"]["hoved"]["raekker"][v])
        assert a["afgoerelse"]["hoved"]["beslutning"] == c["afgoerelse"]["hoved"]["beslutning"]


# ===========================================================================
# §7: σ_dag, MDE og styrke
# ===========================================================================

class TestSigmaDag:
    def _g(self):
        b = Bygger()
        b.bar("08:30", 0, 1, 0, 1, vol=TUNG)          # Δ(08:31) = −1: kun 1m
        b.bar("12:04", 3)                             # +3 og −3 i pausen
        b.bar("14:54", 4)                             # +4 tæller, −4 kl. 14:55 gør ikke
        return _g(b)

    @pytest.mark.parametrize("v,s", [(HELE1, 1 + 9 + 9 + 16), (UDEN1, 1 + 16),
                                     (HELE5, 9 + 9 + 16), (UDEN5, 16)])
    def test_haandregnet(self, v, s):
        # Én dag med L = P: skala 2, så σ = 2 × √(4 × Σ Δ²).
        assert k5.sigma_dag(self._g(), v) == pytest.approx(2 * math.sqrt(4 * s))

    def test_middel_over_dagene(self):
        b = Bygger(dage=(DAG, DAG2))
        b.bar("09:00", 2)
        g = _g(b)
        assert k5.sigma_dag(g, HELE1) == pytest.approx(2 * math.sqrt(4 * 8 / 2))

    def test_handelstiden(self):
        start = np.arange(78) * 5
        m = k5.i_handelstid(start, 5, np.array([385, 205]), k5.UDEN)
        assert start[m[0]].min() == 5 and start[m[0]].max() == 380
        assert set(start[m[0]]) == set(range(5, 146, 5)) | set(range(330, 381, 5))
        assert start[m[1]].max() == 145


class TestMDE:
    def test_z_vaerdierne(self):
        a = 1 - 0.95 ** (1 / 4)
        assert round(norm.ppf(1 - a), 4) == 2.2340
        assert round(norm.ppf(1 - a) + norm.ppf(0.8), 4) == k5.Z_SIDAK4
        assert round(norm.ppf(0.975) + norm.ppf(0.8), 4) == k5.Z_CI

    @pytest.mark.parametrize("sigma,sidak,ci", [(600, 54, 49), (750, 68, 62), (900, 81, 74)])
    def test_tabellen_i_paragraf_7(self, sigma, sidak, ci):
        assert round(k5.mde(sigma, 1165)) == sidak
        assert round(k5.mde(sigma, 1165, k5.Z_CI)) == ci

    def test_artiklens_effekt(self):
        bp = math.log(7.71) / 1446 * 1e4
        assert round(bp, 1) == 14.1
        assert round(bp / 1e4 * k5.NQ_NIVEAU * 2) == 82 == k5.MDE_GRAENSE_USD

    def test_styrke(self):
        assert k5.styrke(700, 1165, 0.0) == pytest.approx(0.025, abs=1e-4)
        mde_ci = k5.mde(700, 1165, k5.Z_CI)
        assert k5.styrke(700, 1165, mde_ci) == pytest.approx(0.80, abs=1e-3)
        assert k5.styrke(700, 1165, -20) < 0.025


# ===========================================================================
# §8-§9: beslutning, break-even og hit ratio
# ===========================================================================

def _r(p, lo):
    return {"p_FWE": p, "ci95_lo": lo}


class TestBeslutning:
    V = k5.VARIANTER

    def _alle(self):
        return {v: _r(0.5, -5.0) for v in self.V}

    def test_raekke_1_fryser_hoejeste_ci_nedre(self):
        b = k5.beslutning(self._alle() | {self.V[0]: _r(0.01, 3.0), self.V[2]: _r(0.04, 7.0)})
        assert b["raekke"] == 1 and b["variant"] == self.V[2]

    def test_raekke_2(self):
        b = k5.beslutning(self._alle() | {self.V[1]: _r(0.01, -1.0)})
        assert b["raekke"] == 2 and b["kandidater"] == [self.V[1]]

    def test_raekke_3(self):
        b = k5.beslutning(self._alle() | {self.V[3]: _r(0.30, 2.0)})
        assert b["raekke"] == 3 and b["kandidater"] == [self.V[3]]

    def test_raekke_4(self):
        assert k5.beslutning(self._alle())["raekke"] == 4
        # Grænserne: p_FWE = 0,05 er signifikant, CI-nedre = 0 er ikke over 0.
        assert k5.beslutning(self._alle() | {self.V[0]: _r(0.05, 0.0)})["raekke"] == 2
        assert k5.beslutning(self._alle() | {self.V[0]: _r(0.0501, 0.0)})["raekke"] == 4

    def test_tillaeg_2_blandet(self):
        """Tillæggets §2: én variant med p_FWE ≤ 0,05 uden CI-nedre > 0 og en anden med
        CI-nedre > 0 uden p_FWE ≤ 0,05 giver række 2, med den anden som in-sample-fund."""
        b = k5.beslutning(self._alle() | {self.V[0]: _r(0.01, -1.0), self.V[1]: _r(0.5, 1.0)})
        assert b["raekke"] == 2 and b["variant"] is None
        assert b["kandidater"] == [self.V[0]] and b["in_sample_fund"] == [self.V[1]]

    def test_tillaeg_2_raekke_1_uaendret(self):
        b = k5.beslutning(self._alle() | {self.V[0]: _r(0.01, -1.0), self.V[1]: _r(0.5, 1.0),
                                          self.V[2]: _r(0.02, 0.5)})
        assert b["raekke"] == 1 and b["variant"] == self.V[2]


class TestBreakeven:
    def test_middel(self):
        assert k5.breakeven_middel(np.array([10.0, -4.0, 6.0])) == pytest.approx(4.0)

    def test_ci(self):
        rng = np.random.default_rng(7)
        k = rng.integers(5, 20, 400).astype(float)
        b = k * 3.0 + rng.normal(0, 40, 400)
        c = k5.breakeven_ci(b, k)
        assert mean_ci_t(b - c * k)[0] == pytest.approx(0.0, abs=1e-8)
        assert c < b.sum() / k.sum()

    def test_ci_kan_vaere_negativ(self):
        rng = np.random.default_rng(8)
        k = rng.integers(5, 20, 400).astype(float)
        b = k * -1.0 + rng.normal(0, 40, 400)
        c = k5.breakeven_ci(b, k)
        assert c < 0 and mean_ci_t(b - c * k)[0] == pytest.approx(0.0, abs=1e-8)


class TestHit:
    def test_hit_og_forhold(self):
        hr, f = k5.hit([3.0, -1.0, -1.0, 0.0, 6.0])
        assert hr == pytest.approx(40.0) and f == pytest.approx(4.5 / 1.0)

    def test_tom(self):
        assert all(math.isnan(x) for x in k5.hit([]))


# ===========================================================================
# §9: diagnoserne
# ===========================================================================

class TestDiagnoser:
    def _g(self):
        b = Bygger(dage=(DAG, DAG2))
        b.fra("09:00", 2)
        b.fra("10:30", -4)
        b.fra("14:55", -9)                            # efter fladt: de sidste 5 minutter
        sav(b, dag=DAG2)
        return _g(b)

    def test_halve_timer_summer_til_brutto(self):
        g = self._g()
        for v in k5.VARIANTER:
            h = _h(g, v)
            res = k5.resultat(g, h)
            ht = k5.halvtimer(g, h, res["skala"])
            assert len(ht) == 13
            assert ht.sum() == pytest.approx(res["brutto_usd"].sum())

    def test_halve_timer_placering(self):
        b = Bygger()
        b.fra("09:00", 2)
        b.bar("09:40", 2, 7, 2, 7)                    # +5 i 09:40-baren: 10:30-11:00 NY
        b.fra("09:41", 7)
        g = _g(b)
        h = _h(g, HELE1)
        ht = k5.halvtimer(g, h, k5.resultat(g, h)["skala"])
        k = (_g_min("09:40")) // 30
        assert ht[k] == pytest.approx(5 * 2 * 2)
        assert np.delete(ht, k).sum() == pytest.approx(0.0)

    def test_stoerste_tab(self):
        b = Bygger()
        b.fra("09:00", 2)
        b.bar("09:30", 2, 2, -30, 1)                  # long, close P+1: urealiseret −1 pt
        b.fra("09:31", 1)
        g = _g(b)
        h = _h(g, HELE1)
        res = k5.resultat(g, h)
        tab = k5.stoerste_tab(g, h, res)
        # Indgang P+2, værste 1m-close P+1: −1 × 2 × 2 − 2,627.
        assert tab[0] == pytest.approx(-4 - 2.627)

    def test_sidste_5(self):
        g = self._g()
        h = _h(g, HELE1)
        res = k5.resultat(g, h)
        s5 = k5.sidste_5(g, h, res["skala"])
        # DAG: short fra 10:31, fladt på open 14:55 = P−9, close 14:59 = P−9: 0.
        assert s5[0] == pytest.approx(0.0)
        b = Bygger()
        b.fra("09:00", 2)
        b.fra("14:57", 6)
        g2 = _g(b)
        h2 = _h(g2, HELE1)
        s = k5.sidste_5(g2, h2, k5.resultat(g2, h2)["skala"])
        assert s[0] == pytest.approx((6 - 2) * 2 * 2)

    def test_altid_long(self):
        b = Bygger()
        b.bar("08:31", 1)
        b.fra("14:55", 11)
        g = _g(b)
        al = k5.altid_long(g)
        assert al["middel_netto_usd_dag"] == pytest.approx(10 * 2 * 2 - 2.627)

    def test_diagnoserne_regnes(self):
        g = self._g()
        hd, _ = k5.forbered(g)
        tal = {v: k5.variant_tal(g, hd[v]) for v in k5.VARIANTER}
        d = k5.diagnoser(g, hd, tal)
        for v in k5.VARIANTER:
            r = d["variant"][v]
            assert r["long_n"] + r["short_n"] == hd[v].n
            assert r["intradag_tab_vaerste"] <= 0
            assert r["dag_vaerste"] <= r["dag_p50"] <= r["dag_bedste"]
        assert len(d["aar"]) == 4 * len(k5.AAR_LISTE)


class TestVariantTal:
    def test_netto_og_omkostning(self):
        g = TestDiagnoser()._g()
        h = _h(g, HELE1)
        t = k5.variant_tal(g, h)
        res = k5.resultat(g, h)
        assert t["handler_n"] == h.n
        assert t["middel_netto_usd_dag"] == pytest.approx(res["netto_usd"].sum() / g.n)
        assert t["middel_brutto_usd_dag"] - t["middel_netto_usd_dag"] == pytest.approx(
            2.627 * h.n / g.n)
        assert t["middel_netto_usd_dag"] - t["netto_usd_dag_ved_3169"] == pytest.approx(
            (k5.OMK_DIAGNOSE_USD - 2.627) * h.n / g.n)
        assert t["breakeven_omk_middel"] == pytest.approx(res["brutto_usd"].mean())


# ===========================================================================
# §11.4: optællingen regner ingen P&L
# ===========================================================================

class TestOptaelling:
    def test_ingen_pnl(self, monkeypatch):
        g = TestDiagnoser()._g()

        def forbudt(*a, **kw):
            raise AssertionError("optællingen må ikke regne P&L")

        monkeypatch.setattr(k5, "resultat", forbudt)
        monkeypatch.setattr(k5, "flyt", forbudt)
        o = k5.optaelling(g)
        noegler = {x for r in o["varianter"] + o["aar"] + o["L_aar"] for x in r}
        for x in noegler:
            assert not x.startswith(("brutto", "netto_usd", "middel", "hit", "gevinst",
                                     "long", "short", "pnl", "R_", "p_FWE", "t_v")), x
        md = k5.optaelling_md(o, {"koert_utc": "x", "head": "0" * 40})
        for ord_ in ("hit_ratio", "p_FWE", "brutto_usd", "middel_netto", "long_n", "short_n"):
            assert ord_ not in md, ord_
        assert "| 1m · hele dagen |" in md

    def test_raekkerne(self):
        g = TestDiagnoser()._g()
        o = k5.optaelling(g)
        r = {(x["tf"], x["middag"]): x for x in o["varianter"]}
        h = _h(g, HELE1)
        assert r[HELE1]["handler_n"] == h.n
        assert r[HELE1]["omk_usd_dag"] == pytest.approx(h.n * 2.627 / g.n)
        assert r[HELE1]["sigma_dag"] == pytest.approx(k5.sigma_dag(g, HELE1))
        assert r[HELE1]["MDE_sidak4"] == pytest.approx(
            k5.Z_SIDAK4 * r[HELE1]["sigma_dag"] / math.sqrt(g.n))
        assert r[HELE1]["udgang_fladt_n"] == 2
        assert r[UDEN1]["udgang_pause_n"] == 2
        la = {x["aar"]: x for x in o["L_aar"]}[2023]
        assert la["L_median"] == P and la["omk_bp_rundtur"] == pytest.approx(
            2.627 / (2 * P) * 1e4)


# ===========================================================================
# Den rigtige kørsel, på en syntetisk serie
# ===========================================================================

class TestHeleKoerslen:
    def test_analyse_og_rapport(self):
        g = TestDiagnoser()._g()
        with np.errstate(all="ignore"):
            res = k5.analyse(g, n_reps=4)
        assert len(res["null"][HELE1]) == 4
        assert res["afgoerelse"]["hoved"]["beslutning"]["raekke"] in (1, 2, 3, 4)
        meta = {"koert_utc": "x", "head": "0" * 40,
                "commits": {k5._rel(k5.PREREG): "a" * 40,
                            k5._rel(k5.Path(k5.__file__)): "b" * 40}}
        md = k5.skriv_md(res, meta)
        assert "Hovedtabel" in md and "Afgørelsen" in md and "Altid-long" in md
        assert "De udelukkede dage" in md
        tabel = k5.lang_tabel(res)
        assert (tabel["tabel"] == "hoved").sum() == 2 * len(k5.VARIANTER)
        assert not any(c.startswith("_") for c in tabel.columns)


class TestRegression:
    def test_konstanterne(self):
        assert (k5.REGRESSION_K4_HANDLER_N, k5.REGRESSION_K4_MIDDEL_R_NETTO) == (1104, -0.0920)
        assert (k2.REGRESSION_HANDLER_N, k2.REGRESSION_MIDDEL_R_NETTO) == (1226, -0.0115)
        assert len(k5.VARIANTER) == 4 and k5.VARIANTER[0] == k5.ARTIKLENS
