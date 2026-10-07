"""Tests for research/b4_k2_nowick.py — B4 kandidat 2, Nowick.

Præregistreringen er ``research/prereg/b4_k2_nowick.md``. §11.2's ni syntetiske tests står
først, i præregistreringens rækkefølge. Derefter det de bygger på:

- motoren: ``simuler_handel`` med målet som parameter gengiver kandidat 1's 2R, og de
  forudregnede handler er de samme som direkte simulering;
- dagens ordrer: én handel om dagen, den gamle ordre kan fyldes inde i det nye signallys,
  annullering ved trendskift og ved vinduets slutning;
- HTF: forskelsjusteringen, swing-tilstanden og konfliktreglen (læsning 5);
- nulmodellen: trækningen pr. (dag, tilstand), uden tilbagelægning, alle ved for få;
- statistikken: Westfall-Young standardiseret, beslutningsreglen i §8, MDE-tabellen i §7.

Alle serier er syntetiske. Ingen test læser prisdata.
"""
from __future__ import annotations

import warnings
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from research import b4_k1_trinA as trinA
from research import b4_k2_nowick as k2

CT = "America/Chicago"
DAG = "2023-06-14"          # onsdag, sommertid: CT = UTC − 5


def _ct(hhmm: str, dag: str = DAG) -> pd.Timestamp:
    return pd.Timestamp(f"{dag} {hhmm}").tz_localize(CT).tz_convert("UTC")


# ===========================================================================
# Byggeklodser
# ===========================================================================

class Bygger:
    """En 1m-serie på én dag. Flad som standard (doji-lys, ingen signaler), hvor enkelte
    minutter og 5m-lys sættes."""

    def __init__(self, fra: str = "07:00", til: str = "15:30", pris: float = 14998.0,
                 dag: str = DAG):
        self.dag = dag
        idx = pd.date_range(_ct(fra, dag), _ct(til, dag), freq="1min", inclusive="left")
        self.df = pd.DataFrame({"open": pris, "high": pris + 0.5, "low": pris - 0.5,
                                "close": pris, "volume": 1.0,
                                "instrument_id": np.int64(1)}, index=idx.rename("time"))

    def _maske(self, fra: str, til: str):
        return (self.df.index >= _ct(fra, self.dag)) & (self.df.index < _ct(til, self.dag))

    def flad(self, fra: str, til: str, pris: float) -> "Bygger":
        m = self._maske(fra, til)
        self.df.loc[m, ["open", "close"]] = pris
        self.df.loc[m, "high"] = pris + 0.5
        self.df.loc[m, "low"] = pris - 0.5
        return self

    def minut(self, hhmm: str, o: float, h: float, l: float, c: float) -> "Bygger":
        self.df.loc[_ct(hhmm, self.dag), ["open", "high", "low", "close"]] = [o, h, l, c]
        return self

    def lys(self, hhmm: str, o: float, h: float, l: float, c: float) -> "Bygger":
        """Et 5m-lys med præcis denne OHLC: første minut bærer høj og lav, resten står på
        lukkekursen."""
        start = _ct(hhmm, self.dag)
        self.df.loc[start, ["open", "high", "low", "close"]] = [o, h, l, c]
        for k in range(1, 5):
            self.df.loc[start + pd.Timedelta(minutes=k),
                        ["open", "high", "low", "close"]] = [c, c, c, c]
        return self

    def rul(self, hhmm: str) -> "Bygger":
        self.df.loc[self.df.index >= _ct(hhmm, self.dag), "instrument_id"] = np.int64(2)
        return self


def _fast_htf(tilstand: int) -> pd.DataFrame:
    return pd.DataFrame({"luk": [pd.Timestamp("2000-01-03 22:00", tz="UTC")],
                         "tilstand": np.array([tilstand], dtype=np.int8)})


def _g(b: Bygger, tilstand: int = k2.NED, htf: dict | None = None,
       med_handler: bool = True) -> k2.Grundlag:
    if htf is None:
        htf = {n: _fast_htf(tilstand) for n in k2.HTF_NAVNE}
    return k2.byg_grundlag(b.df, med_handler=med_handler, htf=htf)


def _signaler(g: k2.Grundlag, htf: str = "daily") -> np.ndarray:
    return np.flatnonzero(g.gyldig[htf]["gyldig"] & g.lys["uden_vaege"].to_numpy(dtype=bool))


def _short_scenarie() -> Bygger:
    """Ét short-signal kl. 08:30 CT: rødt, åbner 15000 = high. Spidsen 07:55 (high 15010)
    giver plads til stoppet: 15010 + 2 ticks, risiko 10,5 pt. Efter signalet står prisen
    fladt på 14995 (doji, ingen nye signaler) — linjen 15000 nås ikke af sig selv."""
    b = Bygger()
    b.minut("07:55", 14998, 15010, 14997.5, 14998)
    b.lys("08:30", 15000, 15000, 14990, 14992)
    b.flad("08:35", "15:30", 14995)
    return b


def _lys_start(n_efter: int) -> str:
    """Starten på det n'te 5m-lys efter signallyset 08:30, som "HH:MM"."""
    t = pd.Timestamp(f"{DAG} 08:30") + pd.Timedelta(minutes=5 * n_efter)
    return t.strftime("%H:%M")


def _plus(hhmm: str, minutter: int) -> str:
    return (pd.Timestamp(f"{DAG} {hhmm}") + pd.Timedelta(minutes=minutter)).strftime("%H:%M")


GENNEM = 15000.25           # ét tick over linjen
BEROER = 15000.0            # præcis linjen


# ===========================================================================
# §11.2 test 1 — signallyset i hele ticks, lighed og doji
# ===========================================================================

class TestSignallys:
    def test_short_uden_topvaege_ogsaa_med_flydende_stoej(self):
        f = k2.lys_flag([15000.0], [15000.0 + 1e-9], [14990.0], [14992.0])
        assert f["short_uden_vaege"][0] and not f["short_med_vaege"][0]

    def test_et_tick_topvaege_er_ikke_et_signal(self):
        f = k2.lys_flag([15000.0], [15000.25], [14990.0], [14992.0])
        assert not f["short_uden_vaege"][0] and f["short_med_vaege"][0]

    def test_long_uden_bundvaege_lighed(self):
        f = k2.lys_flag([15000.0], [15010.0], [15000.0 - 1e-9], [15008.0])
        assert f["long_uden_vaege"][0] and not f["long_med_vaege"][0]

    def test_vaege_i_den_anden_ende_betyder_intet(self):
        """Rødt uden topvæge men med lang bundvæge: stadig et short-signal."""
        f = k2.lys_flag([15000.0], [15000.0], [14950.0], [14992.0])
        assert f["short_uden_vaege"][0]

    def test_doji_er_aldrig_et_signal_heller_ikke_uden_vaege(self):
        f = k2.lys_flag([15000.0, 15000.0], [15000.0, 15005.0], [14995.0, 15000.0],
                        [15000.0, 15000.0 + 1e-9])
        for navn in ("short_uden_vaege", "long_uden_vaege", "short_med_vaege",
                     "long_med_vaege"):
            assert not f[navn].any()

    def test_signallyset_i_scenariet_er_et_gyldigt_short_signal(self):
        g = _g(_short_scenarie(), med_handler=False)
        sig = _signaler(g)
        assert len(sig) == 1
        r = g.lys.iloc[sig[0]]
        assert not r["long"] and r["linje"] == 15000.0
        assert r["stop_t"] == k2.tick([15010.0])[0] + 2
        assert r["risiko_pt"] == 10.5 and r["kontrakter"] == 11


# ===========================================================================
# §11.2 test 2 — HTF-tilstanden bruger kun lukkede HTF-lys
# ===========================================================================

def _globex_serie(n_dage: int, seed: int, rul_dag: int | None = None,
                  drift: float = 0.1, regime: int = 4) -> pd.DataFrame:
    """1m-serie over ``n_dage`` Globex-dage (man-fre), hver 17:00 CT dagen før til 16:00
    CT. Random walk i hele ticks med trend der skifter, så swing-brud opstår. Ved
    ``rul_dag`` skifter kontrakten kl. 18:00 CT med et spring på 40 pt."""
    rng = np.random.default_rng(seed)
    dage = pd.bdate_range("2023-05-08", periods=n_dage)
    dele = []
    pris = 15000.0
    for d_i, d in enumerate(dage):
        start = (pd.Timestamp(d) - pd.Timedelta(days=1)).replace(hour=17)   # mandag: søndag
        idx = pd.date_range(start, periods=1380, freq="1min").tz_localize(CT).tz_convert("UTC")
        d_drift = drift if (d_i // regime) % 2 == 0 else -drift
        skridt = np.round(rng.normal(d_drift, 3.0, len(idx)) / 0.25) * 0.25
        c = pris + np.cumsum(skridt)
        o = np.r_[pris, c[:-1]]
        h = np.maximum(o, c) + 0.25 * rng.integers(0, 4, len(idx))
        l = np.minimum(o, c) - 0.25 * rng.integers(0, 4, len(idx))
        ny = rul_dag is not None and d_i >= rul_dag
        iid = np.full(len(idx), 2 if ny else 1, dtype=np.int64)
        if rul_dag is not None and d_i == rul_dag:
            efter = idx >= pd.Timestamp(start + pd.Timedelta(hours=1)).tz_localize(CT)
            iid = np.where(efter, 2, 1).astype(np.int64)
            o, h, l, c = (np.where(efter, x + 40.0, x) for x in (o, h, l, c))
        dele.append(pd.DataFrame({"open": o, "high": h, "low": l, "close": c,
                                  "volume": 1.0, "instrument_id": iid}, index=idx))
        pris = float(c[-1])
    df = pd.concat(dele)
    df.index = df.index.rename("time")
    return df


def _tilstand_paa(df: pd.DataFrame, htf: str, t: pd.Timestamp) -> int:
    bars, _ = k2.byg_htf(df, htf)
    st, _ = k2.htf_tilstand(bars)
    s, _ = k2.tilstand_ved(np.array([t.value], dtype=np.int64), k2._ns(bars["luk"]), st)
    return int(s[0])


class TestHTFIngenKigFrem:
    @pytest.mark.parametrize("htf", k2.HTF_NAVNE)
    def test_afskaaret_serie_giver_samme_tilstand(self, htf):
        """Skær 1m-serien af ved T, byg HTF forfra, og kræv samme tilstand ved T. Serien
        har en rul, så også forskelsjusteringen er med."""
        df = _globex_serie(40, seed=5, rul_dag=20)
        fuld_bars, _ = k2.byg_htf(df, htf)
        fuld_st, _ = k2.htf_tilstand(fuld_bars)
        assert len(set(fuld_st.tolist()) - {k2.UDEF}) == 2      # både op og ned forekommer
        dage = pd.bdate_range("2023-05-08", periods=40)[14:40:2]
        for d in dage:
            for hhmm in ("08:35", "10:40", "13:05", "14:30"):
                t = _ct(hhmm, d.strftime("%Y-%m-%d"))
                fuld, _ = k2.tilstand_ved(np.array([t.value]), k2._ns(fuld_bars["luk"]),
                                          fuld_st)
                assert _tilstand_paa(df[df.index < t], htf, t) == int(fuld[0]), (d, hhmm)

    def test_brud_inde_i_dagens_daily_lys_paavirker_ikke_samme_dags_signaler(self):
        df = _globex_serie(40, seed=5)
        bars, _ = k2.byg_htf(df, "daily")
        st, _ = k2.htf_tilstand(bars)
        skift = np.flatnonzero(st[1:] != st[:-1]) + 1
        skift = skift[st[skift - 1] != k2.UDEF]
        assert len(skift)                                    # mindst ét rigtigt skift
        luk = k2._ns(bars["luk"])
        for j in skift:
            dag = pd.Timestamp(bars["luk"].iloc[j]).tz_convert(CT).strftime("%Y-%m-%d")
            inde = np.array([_ct(x, dag).value for x in ("08:35", "11:00", "14:30")])
            s, _ = k2.tilstand_ved(inde, luk, st)
            assert (s == st[j - 1]).all() and (s != st[j]).all()
            naeste = pd.Timestamp(bars["luk"].iloc[j + 1]).tz_convert(CT).strftime("%Y-%m-%d")
            s2, _ = k2.tilstand_ved(np.array([_ct("08:35", naeste).value]), luk, st)
            assert s2[0] == st[j]

    def test_htf_lys_der_lukker_samtidig_med_5m_lyset_taeller_med(self):
        """"Lukket senest ved 5m-lysets lukning": 4H-lyset 05-09 lukker 09:00 CT, og
        5m-lyset 08:55-09:00 bruger det."""
        luk = np.array([_ct("05:00").value, _ct("09:00").value])
        st = np.array([k2.NED, k2.OP], dtype=np.int8)
        s, slut = k2.tilstand_ved(np.array([_ct("08:55").value, _ct("09:00").value]), luk, st)
        assert s.tolist() == [k2.NED, k2.OP]
        assert slut[0] == _ct("09:00").value and slut[1] == k2.EVIG


# ===========================================================================
# §11.2 test 3 — fyld i lys N, ikke i lys N+1
# ===========================================================================

class TestFyldILysN:
    @pytest.mark.parametrize("n_lys", k2.N_LYS)
    def test_gennemhandling_i_lys_N_fylder(self, n_lys):
        b = _short_scenarie()
        b.minut(_plus(_lys_start(n_lys), 2), 14995, GENNEM, 14994.5, 14995)
        g = _g(b)
        res = k2.koer_signalsaet(g, "daily", _signaler(g))
        assert len(res[(n_lys, "gennem")].fyldt) == 1
        fyld_i = int(g.lys["gennem_i"].iloc[res[(n_lys, "gennem")].fyldt[0]])
        assert g.lys["gennem_tid"].iloc[res[(n_lys, "gennem")].fyldt[0]] == \
            _ct(_plus(_lys_start(n_lys), 2)).value
        assert b.df.index[fyld_i] == _ct(_plus(_lys_start(n_lys), 2))

    @pytest.mark.parametrize("n_lys", k2.N_LYS)
    def test_gennemhandling_i_lys_N_plus_1_fylder_ikke(self, n_lys):
        b = _short_scenarie()
        b.minut(_lys_start(n_lys + 1), 14995, GENNEM, 14994.5, 14995)   # første minut
        g = _g(b)
        res = k2.koer_signalsaet(g, "daily", _signaler(g))
        assert len(res[(n_lys, "gennem")].fyldt) == 0
        assert res[(n_lys, "gennem")].tael["udloebet_n"] == 1
        for stoerre in (n for n in k2.N_LYS if n > n_lys):
            assert len(res[(stoerre, "gennem")].fyldt) == 1

    def test_sidste_minut_af_lys_N_fylder(self):
        b = _short_scenarie()
        b.minut(_plus(_lys_start(3), 4), 14995, GENNEM, 14994.5, 14995)
        g = _g(b)
        assert len(k2.koer_signalsaet(g, "daily", _signaler(g))[(3, "gennem")].fyldt) == 1

    def test_signallysets_egne_minutter_fylder_ikke(self):
        """Ordren lægges ved signallysets lukning. Signallyset handler selv på linjen i
        sit første minut (åbningen), men det tæller hverken som berøring eller fyld."""
        b = _short_scenarie()
        g = _g(b)
        r = g.lys.iloc[_signaler(g)[0]]
        assert r["gennem_tid"] == k2.EVIG and r["beroering_tid"] == k2.EVIG


# ===========================================================================
# §11.2 test 4 — et strejf fylder ikke, og ordren lever videre
# ===========================================================================

class TestStrejf:
    def test_strejf_fylder_ikke_men_ordren_lever_og_fyldes_senere(self):
        b = _short_scenarie()
        b.minut(_plus(_lys_start(1), 2), 14995, BEROER, 14994.5, 14995)
        b.minut(_plus(_lys_start(3), 1), 14995, GENNEM, 14994.5, 14995)
        g = _g(b)
        res = k2.koer_signalsaet(g, "daily", _signaler(g))
        r = res[(3, "gennem")]
        assert len(r.fyldt) == 1 and len(r.strejf) == 0
        assert g.lys["gennem_tid"].iloc[r.fyldt[0]] == _ct(_plus(_lys_start(3), 1)).value

    def test_strejf_alene_taelles_og_fyldes_ved_beroering(self):
        b = _short_scenarie()
        b.minut(_plus(_lys_start(1), 2), 14995, BEROER, 14994.5, 14995)
        g = _g(b)
        res = k2.koer_signalsaet(g, "daily", _signaler(g))
        assert len(res[(5, "gennem")].fyldt) == 0
        assert len(res[(5, "gennem")].strejf) == 1
        assert len(res[(5, "beroering")].fyldt) == 1
        assert len(res[(5, "beroering")].strejf) == 0
        rk = res[(5, "beroering")].fyldt[0]
        assert g.lys["beroering_tid"].iloc[rk] == _ct(_plus(_lys_start(1), 2)).value

    def test_strejfets_kontrafaktiske_handel_er_berøringsreglens(self):
        b = _short_scenarie()
        b.minut(_plus(_lys_start(1), 2), 14995, BEROER, 14994.5, 14995)
        b.flad(_lys_start(4), "15:30", 14980)            # 1R = 14989,5 nås
        g = _g(b)
        res = k2.koer_signalsaet(g, "daily", _signaler(g))
        s = k2.handelstabel(g, res[(5, "gennem")].strejf, "beroering", 1.0)
        f = k2.handelstabel(g, res[(5, "beroering")].fyldt, "beroering", 1.0)
        pd.testing.assert_frame_equal(s, f)
        assert s["udfald"].iloc[0] == k2.MAAL


# ===========================================================================
# §11.2 test 5 — nyeste signal erstatter den ventende ordre
# ===========================================================================

class TestNyesteErstatter:
    def _to_signaler(self) -> Bygger:
        """A 08:30 (linje 15000), B 08:40 (linje 14996). Efter B står prisen på 14995."""
        b = _short_scenarie()
        b.lys("08:40", 14996, 14996, 14992, 14993)
        return b

    def test_det_nye_signal_er_ordren_i_markedet(self):
        b = self._to_signaler()
        b.minut("08:52", 14995, 14996.25, 14994.5, 14995)   # gennem B, ikke A
        g = _g(b)
        sig = _signaler(g)
        assert len(sig) == 2
        res = k2.koer_signalsaet(g, "daily", sig)
        for n_lys in k2.N_LYS:
            r = res[(n_lys, "gennem")]
            assert r.fyldt.tolist() == [sig[1]]
            assert r.tael["erstattet_n"] == 1 and r.tael["ordrer_n"] == 2

    def test_den_erstattede_ordre_fyldes_ikke_bagefter(self):
        """Dagsgennemløbet på rene arrays: A ville blive fyldt efter B's lukning, men er
        erstattet; B fyldes aldrig."""
        d = np.array([1, 1])
        luk = np.array([0, 50])
        n_slut = np.array([100, 150])
        fyld = np.array([60, k2.EVIG])
        r = k2.dagsgennemloeb(np.array([0, 1]), d, luk, n_slut, fyld, fyld,
                              np.array([10**6, 10**6]), np.array([k2.EVIG, k2.EVIG]), 5)
        assert len(r.fyldt) == 0
        assert r.tael["erstattet_n"] == 1 and r.tael["udloebet_n"] == 0

    def test_den_gamle_ordre_kan_fyldes_inde_i_det_nye_signallys(self):
        d = np.array([1, 1])
        luk = np.array([0, 50])
        r = k2.dagsgennemloeb(np.array([0, 1]), d, luk, np.array([100, 150]),
                              np.array([45, 60]), np.array([45, 60]),
                              np.array([10**6, 10**6]), np.array([k2.EVIG, k2.EVIG]), 5)
        assert r.fyldt.tolist() == [0]
        assert r.tael["ignoreret_dagslukket_n"] == 1


# ===========================================================================
# §11.2 test 6 — signallyset som 10-lys-ekstrem springes over
# ===========================================================================

class TestStopplads:
    def test_short_lighed_med_hoejeste_er_ingen_plads(self):
        h = np.array([10] * 9 + [10] + [0], dtype=np.int64)
        l = np.zeros(11, dtype=np.int64)
        stop, ingen = k2.stop_og_plads(h, l, h.copy(), np.array([9]), np.array([False]))
        assert ingen[0] and stop[0] == 12

    def test_short_lavere_end_hoejeste_har_plads(self):
        h = np.array([10, 20] + [10] * 7 + [15], dtype=np.int64)
        stop, ingen = k2.stop_og_plads(h, np.zeros(10, dtype=np.int64), h.copy(),
                                       np.array([9]), np.array([False]))
        assert not ingen[0] and stop[0] == 22

    def test_long_lighed_med_laveste_er_ingen_plads(self):
        l = np.array([5] * 10, dtype=np.int64)
        _, ingen = k2.stop_og_plads(np.zeros(10, dtype=np.int64), l, l.copy(),
                                    np.array([9]), np.array([True]))
        assert ingen[0]

    def test_long_stop_er_laveste_minus_to_ticks(self):
        l = np.array([7, 3] + [8] * 7 + [9], dtype=np.int64)
        stop, ingen = k2.stop_og_plads(np.zeros(10, dtype=np.int64), l, l.copy(),
                                       np.array([9]), np.array([True]))
        assert not ingen[0] and stop[0] == 1

    def test_scenarie_uden_spids_springes_over_og_taelles(self):
        b = Bygger()
        b.lys("08:30", 15000, 15000, 14990, 14992)          # det højeste af de 10
        b.flad("08:35", "15:30", 14995)
        g = _g(b, med_handler=False)
        assert len(_signaler(g)) == 0
        assert k2.tael_signaler(g, "daily")["sprunget_over_ingen_stopplads_n"] == 1

    def test_de_10_lys_maa_ligge_foer_vinduet(self):
        """Signallyset 08:30 er vinduets første; spidsen 07:55 ligger før vinduet."""
        g = _g(_short_scenarie(), med_handler=False)
        assert len(_signaler(g)) == 1


# ===========================================================================
# §11.2 test 7 — 1R- og 2R-mål
# ===========================================================================

def _serie(h, l, c) -> k2.Serie1m:
    h, l, c = (np.asarray(x, dtype=float) for x in (h, l, c))
    return k2.Serie1m(tider=np.arange(len(h), dtype=np.int64), h=h, l=l, c=c,
                      h_t=k2.tick(h), l_t=k2.tick(l))


class TestMaal:
    def test_1R_ramt_giver_plus_1R(self):
        s = _serie(h=[101, 110, 105], l=[99, 101, 101], c=[100, 109, 104])
        u, r, i, tv = k2.simuler(s, 0, 100.0, True, 10.0, 1.0, 3)
        assert (u, r, i, tv) == (k2.MAAL, 1.0, 1, False)

    def test_2R_ikke_ramt_ved_1R_alene(self):
        """Bar 3 ligger efter 14:50-grænsen (cutoff 3): handlen lukker på bar 2's close."""
        s = _serie(h=[101, 110, 105, 130], l=[99, 101, 101, 101], c=[100, 109, 104, 125])
        u, r, i, tv = k2.simuler(s, 0, 100.0, True, 10.0, 2.0, 3)
        assert u == k2.TIDSEXIT and r == pytest.approx(0.4)

    def test_2R_ramt_giver_plus_2R(self):
        s = _serie(h=[101, 110, 121], l=[99, 101, 105], c=[100, 109, 120])
        assert k2.simuler(s, 0, 100.0, True, 10.0, 2.0, 3)[:2] == (k2.MAAL, 2.0)
        assert k2.simuler(s, 0, 100.0, True, 10.0, 1.0, 3)[:3] == (k2.MAAL, 1.0, 1)

    def test_short_spejlvendt(self):
        s = _serie(h=[101, 99, 95], l=[99, 90, 79], c=[100, 91, 80])
        assert k2.simuler(s, 0, 100.0, False, 10.0, 1.0, 3)[:3] == (k2.MAAL, 1.0, 1)
        assert k2.simuler(s, 0, 100.0, False, 10.0, 2.0, 3)[:3] == (k2.MAAL, 2.0, 2)

    def test_maal_i_fyldningsbaren_taeller_ikke(self):
        """Motorrettelse 1, uændret: i fyldningsbaren kan kun stoppet rammes."""
        s = _serie(h=[115, 102, 102], l=[99, 99, 99], c=[100, 101, 101])
        assert k2.simuler(s, 0, 100.0, True, 10.0, 1.0, 2)[0] == k2.TIDSEXIT

    def test_scenariet_1R_og_2R(self):
        b = _short_scenarie()
        b.minut(_plus(_lys_start(1), 1), 14995, GENNEM, 14994.5, 14995)
        b.flad(_lys_start(3), _lys_start(5), 14989)          # 1R = 14989,5
        b.flad(_lys_start(5), "15:30", 14978)                # 2R = 14979
        g = _g(b)
        res = k2.koer_signalsaet(g, "daily", _signaler(g))
        fyldt = res[(5, "gennem")].fyldt
        h1 = k2.handelstabel(g, fyldt, "gennem", 1.0)
        h2 = k2.handelstabel(g, fyldt, "gennem", 2.0)
        assert h1["udfald"].iloc[0] == k2.MAAL and h1["R_brutto"].iloc[0] == 1.0
        assert h2["udfald"].iloc[0] == k2.MAAL and h2["R_brutto"].iloc[0] == 2.0
        omk = 2.627 / (10.5 * 2)
        assert h1["R_netto"].iloc[0] == pytest.approx(1.0 - omk)


class TestMotorErKandidat1s:
    @pytest.mark.parametrize("seed", range(4))
    def test_standardvaerdien_er_2R(self, seed):
        rng = np.random.default_rng(seed)
        c = 15000 + np.cumsum(rng.normal(0, 2, 400))
        c = np.round(c / 0.25) * 0.25
        sp = np.round(np.abs(rng.normal(0, 2, 400)) / 0.25) * 0.25
        h, l = c + sp, c - sp
        for _ in range(30):
            e = int(rng.integers(0, 350))
            demand = bool(rng.integers(0, 2))
            risiko = float(rng.choice([2.0, 5.0, 10.0]))
            for be in (None, 1.0):
                a = trinA.simuler_handel(h, l, c, e, c[e], demand, risiko, be, 400, 400)
                b = trinA.simuler_handel(h, l, c, e, c[e], demand, risiko, be, 400, 400,
                                         True, 2.0)
                assert a == b

    def test_forudregnede_handler_er_direkte_simulering(self):
        b = _short_scenarie()
        b.minut(_plus(_lys_start(2), 3), 14995, GENNEM, 14994.5, 14995)
        rng = np.random.default_rng(5)
        efter = b.df.index >= _ct(_lys_start(3))
        n = int(efter.sum())
        c = 14995 + np.round(np.cumsum(rng.normal(0, 1.5, n)) / 0.25) * 0.25
        b.df.loc[efter, ["open", "close"]] = np.c_[c, c]
        b.df.loc[efter, "high"] = c + 0.5
        b.df.loc[efter, "low"] = c - 0.5
        g = _g(b)
        s = k2.Serie1m.af(b.df)
        gyldig = np.logical_or.reduce([g.gyldig[n]["gyldig"] for n in k2.HTF_NAVNE])
        for regel in k2.REGLER:
            rk = np.flatnonzero((g.lys[f"{regel}_i"].to_numpy() >= 0) & gyldig)
            assert len(rk) >= 5
            for m in k2.MAAL_R:
                t = k2.handelstabel(g, rk, regel, m)
                for j, k in enumerate(rk):
                    r = g.lys.iloc[k]
                    cutoff = int(np.searchsorted(s.tider, r["flad_ns"]))
                    u, rb, _, tv = k2.simuler(s, int(r[f"{regel}_i"]), r["linje"],
                                              bool(r["long"]), r["risiko_pt"], m, cutoff)
                    assert (t["udfald"].iloc[j], t["R_brutto"].iloc[j],
                            t["tvetydig"].iloc[j]) == (u, rb, tv)


# ===========================================================================
# §11.2 test 8 — rul inden for 10-lys-vinduet springes over
# ===========================================================================

class TestRul:
    def test_rul_i_stopvinduet_springes_over_og_taelles(self):
        b = _short_scenarie().rul("08:10")
        g = _g(b, med_handler=False)
        assert len(_signaler(g)) == 0
        assert k2.tael_signaler(g, "daily")["sprunget_over_rul_n"] == 1

    def test_rul_foer_stopvinduet_springes_ikke_over(self):
        b = Bygger(fra="06:00")
        b.minut("07:55", 14998, 15010, 14997.5, 14998)
        b.lys("08:30", 15000, 15000, 14990, 14992)
        b.flad("08:35", "15:30", 14995)
        b.rul("07:00")
        g = _g(b, med_handler=False)
        assert len(_signaler(g)) == 1

    def test_rul_efter_signalet_samme_dag_springes_over(self):
        """Læsning 8: en rul i ordrens liv eller handlen — her 14:40 CT — springer
        signalet over."""
        b = _short_scenarie().rul("14:40")
        g = _g(b, med_handler=False)
        assert len(_signaler(g)) == 0


# ===========================================================================
# §11.2 test 9 — 4H-lysenes grænser ved 17:00 CT og afkortningen ved 16:00 CT
# ===========================================================================

def _dagsserie(fra_ct: str, til_ct: str) -> pd.DataFrame:
    idx = pd.date_range(pd.Timestamp(fra_ct), pd.Timestamp(til_ct), freq="1min",
                        inclusive="left").tz_localize(CT).tz_convert("UTC")
    p = 15000 + 0.25 * np.arange(len(idx))
    return pd.DataFrame({"open": p, "high": p + 1, "low": p - 1, "close": p, "volume": 1.0,
                         "instrument_id": np.int64(1)}, index=idx.rename("time"))


class TestHTFLys:
    @pytest.mark.parametrize("dag", ["2023-06-13", "2023-01-10"])   # sommer- og vintertid
    def test_4H_graenser_og_afkortning(self, dag):
        d = pd.Timestamp(dag)
        df = _dagsserie(f"{(d - pd.Timedelta(days=1)).date()} 17:00", f"{d.date()} 18:00")
        bars, udenfor = k2.byg_htf(df, "4H")
        start = bars.index.tz_convert(CT)
        luk = pd.DatetimeIndex(bars["luk"]).tz_convert(CT)
        assert start.strftime("%H:%M").tolist() == ["17:00", "21:00", "01:00", "05:00",
                                                    "09:00", "13:00", "17:00"]
        assert luk.strftime("%H:%M").tolist() == ["21:00", "01:00", "05:00", "09:00",
                                                  "13:00", "16:00", "21:00"]
        assert bars["n_1m"].tolist() == [240, 240, 240, 240, 240, 180, 60]
        assert udenfor == 60                                  # 16:00-16:59 CT
        assert start[0].date() == (d - pd.Timedelta(days=1)).date()
        assert start[-1].date() == d.date()                   # næste Globex-dag

    def test_daily_er_globex_dagen_og_soendag_hoerer_til_mandag(self):
        df = _dagsserie("2023-06-11 17:00", "2023-06-12 16:00")   # søndag 17 → mandag 16
        bars, _ = k2.byg_htf(df, "daily")
        assert len(bars) == 1 and bars["n_1m"].iloc[0] == 1380
        luk = pd.Timestamp(bars["luk"].iloc[0]).tz_convert(CT)
        assert (luk.day_name(), luk.strftime("%H:%M")) == ("Monday", "16:00")
        assert bars["open"].iloc[0] == df["open"].iloc[0]
        assert bars["close"].iloc[0] == df["close"].iloc[-1]

    def test_lukketiden_er_nominel_ikke_sidste_bar(self):
        """Læsning 1: 09-13-lyset lukker 13:00 CT, også hvis handlen stopper 12:15."""
        df = _dagsserie("2023-06-12 17:00", "2023-06-13 12:15")
        bars, _ = k2.byg_htf(df, "4H")
        assert pd.Timestamp(bars["luk"].iloc[-1]).tz_convert(CT).strftime("%H:%M") == "13:00"


class TestForskelsjustering:
    def test_historikken_flyttes_med_springet(self):
        df = _dagsserie("2023-06-12 17:00", "2023-06-12 21:00")
        rul = df.index >= _ct("19:00", "2023-06-12")
        df.loc[rul, ["open", "high", "low", "close"]] += 30.0
        df.loc[rul, "instrument_id"] = np.int64(2)
        adj, ruller = k2.forskelsjuster(df)
        i = int(np.argmax(rul))
        spring = df["open"].iloc[i] - df["close"].iloc[i - 1]
        assert len(ruller) == 1 and ruller["spring_pt"].iloc[0] == spring
        assert np.allclose(adj.loc[~rul, "close"], df.loc[~rul, "close"] + spring)
        assert np.allclose(adj.loc[rul, "close"], df.loc[rul, "close"])
        # justeret: sidste close i den gamle kontrakt = første open i den nye
        assert adj["close"].iloc[i - 1] == adj["open"].iloc[i]


class TestHTFTilstand:
    def _htf(self, h, l, c) -> pd.DataFrame:
        return pd.DataFrame({"high": np.asarray(h, float), "low": np.asarray(l, float),
                             "close": np.asarray(c, float)})

    def test_udefineret_op_og_ned(self):
        h = [100, 101, 102, 103, 104, 110, 104, 103, 102, 101, 100, 100,
             115, 116, 117, 118, 119, 120, 100]
        l = [x - 5 for x in h[:12]] + [110, 111, 112, 113, 114, 115, 90]
        c = [x - 2 for x in h[:12]] + [112, 113, 114, 115, 116, 117, 92]
        st, t = k2.htf_tilstand(self._htf(h, l, c))
        assert (st[:12] == k2.UDEF).all()
        assert (st[12:18] == k2.OP).all()
        assert st[18] == k2.NED
        assert t["konflikt_n"] == 0

    def test_konflikt_er_uaendret(self):
        """Læsning 5: den seneste swing-bund (140) ligger over den seneste swing-top (100);
        lys 22 lukker på 120, over toppen og under bunden. Tilstanden er uændret op."""
        h = [90, 91, 92, 93, 94, 100, 95, 96, 97, 98, 99,
             150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 150]
        l = [85, 86, 87, 88, 89, 95, 90, 91, 92, 93, 94,
             145, 146, 147, 148, 149, 140, 141, 142, 143, 144, 145, 115]
        c = [x - 2 for x in h[:22]] + [120]
        st, t = k2.htf_tilstand(self._htf(h, l, c))
        assert t["konflikt_n"] == 1
        assert st[21] == k2.OP and st[22] == k2.OP


# ===========================================================================
# Dagens ordrer, §4c og §4f
# ===========================================================================

class TestDagensOrdrer:
    def test_en_handel_om_dagen(self):
        d = np.array([1, 1, 2])
        luk = np.array([0, 200, 0])
        r = k2.dagsgennemloeb(np.array([0, 1, 2]), d, luk, np.array([100, 300, 100]),
                              np.array([50, 250, 50]), np.array([50, 250, 50]),
                              np.full(3, 10**6), np.full(3, k2.EVIG), 5)
        assert r.fyldt.tolist() == [0, 2]
        assert r.tael["ignoreret_dagslukket_n"] == 1

    def test_trendskift_annullerer(self):
        luk = np.array([0])
        r = k2.dagsgennemloeb(np.array([0]), np.array([1]), luk, np.array([30]),
                              np.array([40]), np.array([40]), np.array([10**6]),
                              np.array([30]), 5)
        assert len(r.fyldt) == 0 and r.tael["annulleret_trend_n"] == 1

    def test_trendskift_paa_4H_annullerer_i_scenariet(self):
        b = _short_scenarie()
        b.minut("08:47", 14995, GENNEM, 14994.5, 14995)
        htf = {"daily": _fast_htf(k2.NED),
               "4H": pd.DataFrame({"luk": [pd.Timestamp("2000-01-03 22:00", tz="UTC"),
                                           _ct("08:45")],
                                   "tilstand": np.array([k2.NED, k2.OP], dtype=np.int8)})}
        g = _g(b, htf=htf)
        res_d = k2.koer_signalsaet(g, "daily", _signaler(g, "daily"))
        res_4 = k2.koer_signalsaet(g, "4H", _signaler(g, "4H"))
        assert len(res_d[(5, "gennem")].fyldt) == 1
        assert len(res_4[(5, "gennem")].fyldt) == 0
        assert res_4[(5, "gennem")].tael["annulleret_trend_n"] == 1

    def test_vinduets_slutning_annullerer(self):
        """Signal i vinduets sidste lys (14:25-14:30 CT): ordren dør ved lukningen."""
        b = Bygger()
        b.minut("13:50", 14998, 15010, 14997.5, 14998)
        b.lys("14:25", 15000, 15000, 14990, 14992)
        b.flad("14:30", "15:30", 14995)
        b.minut("14:31", 14995, GENNEM, 14994.5, 14995)
        g = _g(b)
        sig = _signaler(g)
        assert len(sig) == 1
        res = k2.koer_signalsaet(g, "daily", sig)
        assert len(res[(3, "gennem")].fyldt) == 0
        assert res[(3, "gennem")].tael["annulleret_vindue_n"] == 1

    def test_vinduet_slutter_1130_paa_en_halv_dag(self):
        """Læsning 7: 2023-11-24 (dagen efter Thanksgiving) lukker RTH 12:00 CT."""
        b = Bygger(dag="2023-11-24", fra="07:00", til="12:00")
        b.minut("10:55", 14998, 15010, 14997.5, 14998)
        b.lys("11:25", 15000, 15000, 14990, 14992)
        b.flad("11:30", "12:00", 14995)
        b.minut("11:32", 14995, GENNEM, 14994.5, 14995)
        g = _g(b)
        sig = _signaler(g)
        assert len(sig) == 1
        assert g.lys["vindue_slut_ns"].iloc[sig[0]] == _ct("11:30", "2023-11-24").value
        assert len(k2.koer_signalsaet(g, "daily", sig)[(5, "gennem")].fyldt) == 0

    def test_ingen_trend_ingen_handel(self):
        g = _g(_short_scenarie(), tilstand=k2.UDEF, med_handler=False)
        assert len(_signaler(g)) == 0
        assert k2.tael_signaler(g, "daily")["sprunget_over_udefineret_n"] == 1

    def test_mod_trenden_er_intet_signal(self):
        g = _g(_short_scenarie(), tilstand=k2.OP, med_handler=False)
        assert len(_signaler(g)) == 0
        assert k2.tael_signaler(g, "daily")["ikke_i_trendens_retning_n"] == 1


class TestSizing:
    def test_dollarloftet_og_positionsloftet(self):
        z = k2.sizing(np.array([500, 501, 4], dtype=np.int64))
        assert z["kontrakter"].tolist() == [1.0, 0.0, 50.0]
        assert z["kontrakter_raa"][2] == 125.0

    def test_tvetydig_og_bedste_fald(self):
        s = _serie(h=[101, 115], l=[99, 85], c=[100, 100])
        u, r, i, tv = k2.simuler(s, 0, 100.0, True, 10.0, 1.0, 2)
        assert (u, i, tv) == (k2.STOP, 1, True)
        # i fyldningsbaren er der ingen tvetydighed: kun stoppet kan rammes dér
        s2 = _serie(h=[115], l=[85], c=[100])
        assert k2.simuler(s2, 0, 100.0, True, 10.0, 1.0, 1)[3] is False


# ===========================================================================
# Nulmodellen, §6
# ===========================================================================

class TestNalm:
    def test_traek_uden_tilbagelaegning_og_alle_ved_for_faa(self):
        mt = k2.Matching(k=np.array([2, 3]), kandidater=[np.arange(5), np.array([10, 11])],
                         celler_for_faa_n=1, dage_for_faa_n=1, dage_n=2)
        a = k2.nalm_traek(mt, np.random.default_rng(1))
        assert len(a) == 4 and set(a[-2:]) == {10, 11}
        assert len(set(a[:2])) == 2 and set(a[:2]) <= set(range(5))
        assert (k2.nalm_traek(mt, np.random.default_rng(1)) == a).all()

    def test_matching_pr_dag_og_tilstand(self):
        dag = pd.to_datetime(["2023-06-14"] * 6 + ["2023-06-15"] * 3).to_numpy()
        st = np.array([k2.NED, k2.NED, k2.NED, k2.OP, k2.OP, k2.OP, k2.NED, k2.NED, k2.NED],
                      dtype=np.int8)
        uden = np.array([1, 0, 0, 1, 0, 0, 1, 1, 0], dtype=bool)
        lys = pd.DataFrame({"dag": dag, "tilstand_4H": st, "uden_vaege": uden})
        g = SimpleNamespace(lys=lys, gyldig={"4H": {"gyldig": np.ones(9, dtype=bool)}})
        mt = k2.matching(g, "4H")
        celler = {(int(k), tuple(c.tolist())) for k, c in zip(mt.k, mt.kandidater)}
        assert celler == {(1, (1, 2)), (1, (4, 5)), (2, (8,))}
        assert mt.celler_for_faa_n == 1 and mt.dage_for_faa_n == 1 and mt.dage_n == 2

    def test_daily_og_4H_trækkes_hver_for_sig(self):
        a = k2.nalm_rng(0, "daily").integers(0, 10**9, 5)
        b = k2.nalm_rng(0, "4H").integers(0, 10**9, 5)
        c = k2.nalm_rng(1, "daily").integers(0, 10**9, 5)
        assert not (a == b).all() and not (a == c).all()

    def test_nulkandidat_er_lys_med_vaege_med_samme_regler(self):
        b = _short_scenarie()
        b.lys("09:00", 14996, 14997, 14990, 14991)            # rødt med topvæge
        g = _g(b, med_handler=False)
        gy = g.gyldig["daily"]["gyldig"]
        uden = g.lys["uden_vaege"].to_numpy(dtype=bool)
        assert int((gy & uden).sum()) == 1 and int((gy & ~uden).sum()) == 1


# ===========================================================================
# Statistikken, §7 og §8
# ===========================================================================

class TestWestfallYoung:
    def test_standardiseret_maks(self):
        obs = {"a": 5.0, "b": 15.0}
        null = {"a": np.array([0.0, 1, 2, 3]), "b": np.array([10.0, 10, 20, 20])}
        wy = k2.westfall_young(obs, null)
        assert wy["pr_variant"]["a"]["p_FWE"] == pytest.approx(1 / 5)
        assert wy["pr_variant"]["b"]["p_FWE"] == pytest.approx(3 / 5)
        sd_a = np.std([0, 1, 2, 3], ddof=1)
        assert wy["pr_variant"]["a"]["t"] == pytest.approx((5 - 1.5) / sd_a)

    def test_hoejt_nulniveau_dominerer_ikke(self):
        """Lektien fra kandidat 1: en variant med højere nulniveau må ikke vinde alene på
        niveauet. b ligger på sin egen median og får ingen signifikans."""
        rng = np.random.default_rng(0)
        null = {"a": rng.normal(0, 0.05, 500), "b": rng.normal(0.3, 0.05, 500)}
        wy = k2.westfall_young({"a": 0.0, "b": 0.3}, null)
        assert wy["pr_variant"]["b"]["p_FWE"] > 0.3


class TestBeslutning:
    def _r(self, p, m, lo):
        return {"p_FWE": p, "middel_R_netto": m, "middel_R_netto_ci95_lo": lo}

    def test_raekke_1_fryser_hoejeste_ci_nedre(self):
        b = k2.beslutning({"x": self._r(0.01, 0.25, 0.05), "y": self._r(0.02, 0.30, 0.08),
                           "z": self._r(0.5, 0.0, -0.1)})
        assert b["raekke"] == 1 and b["variant"] == "y"

    def test_raekke_1_graenser(self):
        """p = 0,05 og +0,20 R består; CI-nedre = 0 består ikke."""
        assert k2.beslutning({"x": self._r(0.05, 0.20, 0.01)})["raekke"] == 1
        assert k2.beslutning({"x": self._r(0.05, 0.20, 0.0)})["raekke"] == 4

    def test_raekke_2(self):
        assert k2.beslutning({"x": self._r(0.01, 0.10, 0.02)})["raekke"] == 2

    def test_raekke_3(self):
        assert k2.beslutning({"x": self._r(0.2, 0.10, 0.02),
                              "y": self._r(0.3, 0.0, -0.1)})["raekke"] == 3

    def test_raekke_4_naar_signifikans_og_ci_ligger_paa_hver_sin_variant(self):
        assert k2.beslutning({"x": self._r(0.01, 0.10, -0.01),
                              "y": self._r(0.3, 0.10, 0.02)})["raekke"] == 4


class TestMDE:
    @pytest.mark.parametrize("n, m, ukorr, sidak", [
        (400, 1.0, 0.124, 0.174), (600, 1.0, 0.102, 0.142), (800, 1.0, 0.088, 0.123),
        (1000, 1.0, 0.079, 0.110), (400, 2.0, 0.176, 0.245), (600, 2.0, 0.144, 0.200),
        (800, 2.0, 0.124, 0.174), (1000, 2.0, 0.111, 0.155)])
    def test_tabellen_i_paragraf_7(self, n, m, ukorr, sidak):
        assert round(k2.mde(n, m, k2.Z_UKORR), 3) == ukorr
        assert round(k2.mde(n, m), 3) == sidak

    def test_graensen(self):
        assert k2.mde(603, 2.0) <= 0.20 < k2.mde(602, 2.0)
        assert k2.mde(302, 1.0) <= 0.20 < k2.mde(301, 1.0)


# ===========================================================================
# Rapportlaget — hele kørslens vej på en syntetisk serie
# ===========================================================================

def test_rapporten_kan_skrives_paa_en_syntetisk_koersel():
    """``koer`` læser rigtige data og må ikke køres før godkendelsen. Her køres resten af
    vejen — varianter, N-alm, Westfall-Young, §8, diagnoser, md og csv — på en syntetisk
    serie med ét signal og mange nulkandidater."""
    b = _short_scenarie()
    b.minut(_plus(_lys_start(2), 3), 14995, GENNEM, 14994.5, 14995)
    rng = np.random.default_rng(5)
    efter = b.df.index >= _ct(_lys_start(3))
    c = 14995 + np.round(np.cumsum(rng.normal(0, 1.5, int(efter.sum()))) / 0.25) * 0.25
    b.df.loc[efter, ["open", "close"]] = np.c_[c, c]
    b.df.loc[efter, "high"] = c + 0.5
    b.df.loc[efter, "low"] = c - 0.5
    g = _g(b)
    mt = {htf: k2.matching(g, htf) for htf in k2.HTF_NAVNE}
    gentagelser = [k2.nalm_gentagelse(r, g, mt) for r in range(6)]
    virkelig = k2.koer_virkelig(g)
    with np.errstate(all="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)   # alle-NaN i nulmodellen
        afg = {navn: k2.afgoerelse(virkelig, gentagelser, regel, bedste)
               for navn, regel, bedste in (("gennem", "gennem", False),
                                           ("beroering", "beroering", False),
                                           ("gennem_bedste_fald", "gennem", True))}
        res = {"g": g, "virkelig": virkelig, "gentagelser": gentagelser, "afgoerelse": afg,
               "diagnoser": k2.diagnoser(g, virkelig, gentagelser),
               "optaelling": k2.optaelling(g), "n_reps": 6, "n_1m": len(b.df)}
        meta = {"koert_utc": "2026-01-01 00:00", "head": "0" * 40,
                "commits": {k2._rel(k2.PREREG): "1" * 40,
                            k2._rel(k2.Path(k2.__file__)): "2" * 40}}
        md = k2.skriv_md(res, meta)
        tabel = k2.lang_tabel(res)
    assert "række" in md and k2._vnavn(k2.HOVEDVARIANT) in md
    assert md.index(k2._vnavn(k2.HOVEDVARIANT)) < md.index(k2._vnavn(("daily", 3, 1.0)))
    assert {"gennem", "beroering", "gennem_bedste_fald", "optaelling"} <= set(tabel["afgoerelse"])
    assert len(tabel[(tabel["afgoerelse"] == "gennem") & (tabel["side"] == "alle")
                     & (tabel["periode"] == "2019-2023")]) == 12
    for v in k2.VARIANTER:
        assert afg["gennem"]["raekker"][v]["handler_n"] == len(virkelig[(v, "gennem")]["handler"])
