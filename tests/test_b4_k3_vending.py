"""Tests for research/b4_k3_vending.py — B4 kandidat 3, vending efter åbningen.

Præregistreringen er ``research/prereg/b4_k3_vending.md``. §11.2's ti syntetiske tests står
først, i præregistreringens rækkefølge. Derefter det de bygger på:

- TR og Wilders ATR, også hen over et hul i serien;
- de forudregnede handler er de samme som direkte simulering med ``simuler_handel``;
- stoppets afrunding, sizing og loftet;
- ruller, halve dage og overnatafkastets fortegn;
- optællingen simulerer ingen handel;
- beslutningsreglen i §8 og MDE-tabellen i §7.

Alle serier er syntetiske. Ingen test læser prisdata.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from research import b4_k1_trinA as trinA
from research import b4_k3_vending as k3

CT = "America/Chicago"
DAG = "2023-06-14"          # onsdag, sommertid: CT = UTC − 5
DAG2 = "2023-06-15"
P = 15000.0
SLIP = trinA.SLIP_PT


def _ct(hhmm: str, dag: str = DAG) -> pd.Timestamp:
    return pd.Timestamp(f"{dag} {hhmm}").tz_localize(CT).tz_convert("UTC")


def _plus(hhmm: str, minutter: int) -> str:
    return (pd.Timestamp(f"2000-01-01 {hhmm}") + pd.Timedelta(minutes=minutter)).strftime("%H:%M")


# ===========================================================================
# Byggeklodser
# ===========================================================================

class Bygger:
    """En 1m-serie over en eller flere dage. Flad som standard: doji-barer med high/low
    ±1 point, så TR = 2 og ATR = 2 præcist. Åbningen sættes med 08:59-barens close ét tick
    under (``NED``) eller over (``OP``) 08:30-barens open; TR ændres ikke af det."""

    def __init__(self, dage=(DAG,), fra: str = "07:00", til: str = "15:30", pris: float = P,
                 aabning: int | None = k3.NED):
        dele = []
        for d in dage:
            idx = pd.date_range(_ct(fra, d), _ct(til, d), freq="1min", inclusive="left")
            dele.append(pd.DataFrame({"open": pris, "high": pris + 1.0, "low": pris - 1.0,
                                      "close": pris, "volume": 1.0,
                                      "instrument_id": np.int64(1)}, index=idx.rename("time")))
        self.df = pd.concat(dele)
        self.dag0 = dage[0]
        if aabning is not None:
            for d in dage:
                self.df.loc[_ct("08:59", d), "close"] = pris + 0.25 * aabning

    def _d(self, dag):
        return self.dag0 if dag is None else dag

    def minut(self, hhmm: str, o: float, h: float, l: float, c: float, dag=None) -> "Bygger":
        self.df.loc[_ct(hhmm, self._d(dag)), ["open", "high", "low", "close"]] = [o, h, l, c]
        return self

    def flad_fra(self, hhmm: str, pris: float, dag=None) -> "Bygger":
        d = self._d(dag)
        m = (self.df.index >= _ct(hhmm, d)) & (self.df.index < _ct("23:59", d))
        self.df.loc[m, ["open", "close"]] = pris
        self.df.loc[m, "high"] = pris + 1.0
        self.df.loc[m, "low"] = pris - 1.0
        return self

    def lys(self, hhmm: str, o: float, h: float, l: float, c: float, dag=None) -> "Bygger":
        """Én bar, og resten af dagen fladt på dens close."""
        self.flad_fra(_plus(hhmm, 1), c, dag)
        return self.minut(hhmm, o, h, l, c, dag)

    def groent(self, hhmm: str, niveau: float, tr: float = 4.25, dag=None) -> "Bygger":
        """Grønt lys fra ``niveau`` med præcis denne TR: low = niveau − 1, close = high − 0,25."""
        return self.lys(hhmm, niveau, niveau + tr - 1, niveau - 1, niveau + tr - 1.25, dag)

    def roedt(self, hhmm: str, niveau: float, tr: float = 4.25, dag=None) -> "Bygger":
        return self.lys(hhmm, niveau, niveau + 1, niveau - tr + 1, niveau - tr + 1.25, dag)

    def fjern(self, hhmm: str, dag=None) -> "Bygger":
        self.df = self.df.drop(_ct(hhmm, self._d(dag)))
        return self

    def rul(self, hhmm: str, dag=None) -> "Bygger":
        self.df.loc[self.df.index >= _ct(hhmm, self._d(dag)), "instrument_id"] = np.int64(2)
        return self


def _g(b: Bygger, forudregn: bool = True) -> k3.Grundlag:
    g = k3.byg_grundlag(b.df)
    if forudregn:
        k3.forbered(g)
    return g


def _raekke(g: k3.Grundlag, hhmm: str, dag: str = DAG) -> int:
    r = np.flatnonzero(g.bar["tid_ns"].to_numpy() == _ct(hhmm, dag).value)
    assert len(r) == 1, f"ingen vinduesbar {hhmm}"
    return int(r[0])


def _valgt(g: k3.Grundlag, side: str = k3.MOD, k: float = 1.0) -> list[str]:
    """De valgte signalbarer som "HH:MM"."""
    v = k3.foerste_signal(g, side, k)
    return [(pd.Timestamp(int(t), tz="UTC").tz_convert(CT)).strftime("%H:%M")
            for t in g.bar["tid_ns"].to_numpy()[v.raekker]]


def _handel(g: k3.Grundlag, side: str = k3.MOD, k: float = 1.0) -> pd.Series:
    v = k3.foerste_signal(g, side, k)
    assert len(v.raekker) == 1
    return k3.handelstabel(g, v.raekker, side).iloc[0]


def _long_scenarie() -> Bygger:
    """Åbning ned, grønt lys kl. 09:10 med TR 4,25 fra 15000. Signal for alle tre k:
    4,25 > 2 × ATR_{i−1} = 4. Bagefter fladt på 15003 (close)."""
    return Bygger().groent("09:10", P)


# Tallene i scenariet, regnet i hånden.
ATR_I = 2.0 + (4.25 - 2.0) / 14
FYLD_LONG = 15003.0 + SLIP
STOP_LONG = 14998.75            # floor((15003,135425 − 4,3214…) / 0,25) × 0,25
RISIKO_LONG = FYLD_LONG - STOP_LONG
MAAL_LONG = FYLD_LONG + 1.5 * RISIKO_LONG


# ===========================================================================
# §11.2 test 1 — åbningens retning, retning 0 og manglende barer
# ===========================================================================

class TestAabningensRetning:
    def test_ned_og_op(self):
        for aab, ventet in ((k3.NED, k3.NED), (k3.OP, k3.OP)):
            g = _g(Bygger(aabning=aab), forudregn=False)
            assert g.dage["status"].iloc[0] == "ok"
            assert g.dage["retning"].iloc[0] == ventet
            assert g.dage["r_aabning_t"].iloc[0] == aab

    def test_bruger_0830_open_og_0859_close(self):
        """08:30 åbner 0,5 over niveauet, 08:59 lukker 0,25 over: r = −1 tick, åbningen er
        ned. Med 08:29's close eller 09:00's close ville den være op eller nul."""
        b = Bygger(aabning=None)
        b.minut("08:30", P + 0.5, P + 1, P - 1, P)
        b.minut("08:59", P, P + 1, P - 1, P + 0.25)
        g = _g(b, forudregn=False)
        assert g.dage["r_aabning_t"].iloc[0] == -1
        assert g.dage["retning"].iloc[0] == k3.NED

    def test_retning_nul_giver_ingen_handel_og_taelles(self):
        g = _g(Bygger(aabning=None).groent("09:10", P), forudregn=False)
        assert g.dage["status"].iloc[0] == "nul"
        assert g.dage["retning"].iloc[0] == k3.INGEN
        for side in k3.SIDER:
            assert _valgt(g, side) == []
        assert k3.optaelling(g)["dage"]["r_aabning_nul_n"] == 1

    @pytest.mark.parametrize("mangler", ["08:30", "08:59"])
    def test_manglende_bar_giver_ingen_handel_og_taelles(self, mangler):
        g = _g(_long_scenarie().fjern(mangler), forudregn=False)
        assert g.dage["status"].iloc[0] == "mangler"
        assert _valgt(g) == [] and _valgt(g, k3.MED) == []
        o = k3.optaelling(g)
        assert o["dage"]["mangler_bar_n"] == 1
        assert o["dage"]["dage_med_aabningsretning_n"] == 0


# ===========================================================================
# §11.2 test 2 — signalet bruger ATR_{i−1}, stoppet ATR_i
# ===========================================================================

class TestATRTidspunkt:
    def test_signalet_bruger_atr_foer_signalbaren(self):
        """TR 4,25 > 2 × ATR_{i−1} = 4,0, men ≤ 2 × ATR_i = 4,32. Med ATR_i var der intet
        signal ved k = 2."""
        g = _g(_long_scenarie(), forudregn=False)
        r = _raekke(g, "09:10")
        assert g.bar["atr_foer"].iloc[r] == 2.0
        assert g.bar["atr_i"].iloc[r] == pytest.approx(ATR_I, abs=1e-12)
        assert 4.25 <= 2.0 * g.bar["atr_i"].iloc[r]
        assert k3.signal_maske(g, k3.MOD, 2.0)[r]
        assert _valgt(g, k=2.0) == ["09:10"]

    def test_signalet_bruger_ikke_atr_to_barer_tilbage(self):
        """En doji med TR 16 kl. 09:09 løfter ATR til 3. Lyset 09:10 har TR 5: over
        2 × ATR_{i−2} = 4, men ikke over 2 × ATR_{i−1} = 6."""
        b = Bygger()
        b.minut("09:09", P, P + 8, P - 8, P)
        b.lys("09:10", P, P + 4, P - 1, P + 3.5)
        g = _g(b, forudregn=False)
        r = _raekke(g, "09:10")
        assert g.bar["atr_foer"].iloc[r] == pytest.approx(3.0)
        assert g.bar["tr"].iloc[r] == 5.0
        assert not k3.signal_maske(g, k3.MOD, 2.0)[r]
        assert k3.signal_maske(g, k3.MOD, 1.5)[r]          # 5 > 4,5

    def test_stoppet_bruger_atr_i(self):
        g = _g(_long_scenarie(), forudregn=False)
        r = _raekke(g, "09:10")
        assert g.bar["fyld_mod"].iloc[r] == pytest.approx(FYLD_LONG, abs=1e-9)
        assert g.bar["stop_mod"].iloc[r] == STOP_LONG
        assert g.bar["risiko_pt_mod"].iloc[r] == pytest.approx(RISIKO_LONG, abs=1e-9)
        # Med ATR_{i−1} ville stoppet ligge på 14999,00.
        med_foer = math.floor(round((FYLD_LONG - 4.0) / 0.25, 9)) * 0.25
        assert med_foer == 14999.0 != STOP_LONG

    def test_atr_er_kendt_ved_lukningen(self):
        """Ingen kig frem: ATR_i ændres ikke af barer efter i."""
        b1 = _long_scenarie()
        b2 = _long_scenarie().minut("09:11", 15003, 15040, 14990, 15003)
        g1, g2 = _g(b1, forudregn=False), _g(b2, forudregn=False)
        r = _raekke(g1, "09:10")
        for kol in ("atr_foer", "atr_i", "stop_mod", "risiko_pt_mod"):
            assert g1.bar[kol].iloc[r] == g2.bar[kol].iloc[r]


# ===========================================================================
# §11.2 test 3 — kun signalbarer der starter i [09:00, 11:00) CT
# ===========================================================================

class TestVindue:
    def _b(self) -> Bygger:
        """Rødt lys 08:40 og grønt 08:45 sætter en åbning ned (r = −20 point). Det grønne
        lys kl. 08:45 ville være et signal i vinduet."""
        b = Bygger(aabning=None)
        b.roedt("08:40", P, tr=30)
        b.groent("08:45", P - 28.75, tr=10)
        return b

    def test_vinduet_har_120_barer(self):
        g = _g(Bygger(), forudregn=False)
        assert len(g.bar) == 120
        assert g.bar["minut_off"].tolist() == list(range(120))

    def test_lys_foer_0900_og_fra_1100_er_ikke_signaler(self):
        b = self._b()
        b.groent("11:00", P - 20, tr=10)
        g = _g(b, forudregn=False)
        assert g.dage["retning"].iloc[0] == k3.NED
        for k in k3.K_VAERDIER:
            assert _valgt(g, k=k) == []

    def test_lys_kl_1059_er_et_signal_og_handles_fra_1100(self):
        b = self._b()
        b.groent("10:59", P - 20, tr=10)
        b.groent("11:00", P - 11.25, tr=10)
        g = _g(b)
        assert _valgt(g) == ["10:59"]
        h = _handel(g)
        r = int(h["raekke"])
        assert g.bar["entry_i"].iloc[r] == g.bar["i"].iloc[r] + 1
        assert g.bar["aabning_naeste"].iloc[r] == P - 11.25


# ===========================================================================
# §11.2 test 4 — lysets farve skal være modsat åbningen
# ===========================================================================

class TestFarve:
    def test_aabning_ned_groent_lys_er_long(self):
        g = _g(Bygger(aabning=k3.NED).groent("09:10", P), forudregn=False)
        assert _valgt(g) == ["09:10"]
        assert bool(g.bar["long_mod"].iloc[_raekke(g, "09:10")])

    def test_aabning_ned_roedt_lys_er_ikke_et_signal(self):
        g = _g(Bygger(aabning=k3.NED).roedt("09:10", P), forudregn=False)
        assert _valgt(g) == []

    def test_aabning_op_roedt_lys_er_short(self):
        g = _g(Bygger(aabning=k3.OP).roedt("09:10", P), forudregn=False)
        assert _valgt(g) == ["09:10"]
        assert not bool(g.bar["long_mod"].iloc[_raekke(g, "09:10")])

    def test_aabning_op_groent_lys_er_ikke_et_signal(self):
        g = _g(Bygger(aabning=k3.OP).groent("09:10", P), forudregn=False)
        assert _valgt(g) == []

    def test_doji_er_aldrig_et_signal(self):
        b = Bygger(aabning=k3.NED).minut("09:10", P, P + 10, P - 10, P)
        g = _g(b, forudregn=False)
        assert _valgt(g) == [] and _valgt(g, k3.MED) == []

    def test_farven_i_hele_ticks(self):
        """Close en milliontedel over open er ikke grønt."""
        b = Bygger(aabning=k3.NED).minut("09:10", P, P + 5, P - 1, P + 1e-6)
        g = _g(b, forudregn=False)
        assert _valgt(g) == []


# ===========================================================================
# §11.2 test 5 — indgang ved næste bars åbning plus slippage; hul over 1 minut
# ===========================================================================

class TestIndgang:
    def test_long_fylder_naeste_aabning_plus_slippage(self):
        b = _long_scenarie().minut("09:11", 15003.5, 15004.5, 15002.5, 15003)
        g = _g(b)
        h = _handel(g)
        r = int(h["raekke"])
        assert g.bar["fyld_mod"].iloc[r] == pytest.approx(15003.5 + SLIP, abs=1e-9)
        assert g.bar["entry_i"].iloc[r] == g.bar["i"].iloc[r] + 1

    def test_short_fylder_naeste_aabning_minus_slippage(self):
        b = Bygger(aabning=k3.OP).roedt("09:10", P)
        g = _g(b)
        r = _raekke(g, "09:10")
        fyld = 14997.0 - SLIP
        assert g.bar["fyld_mod"].iloc[r] == pytest.approx(fyld, abs=1e-9)
        # Stoppet rundes op, væk fra indgangen.
        stop = math.ceil(round((fyld + 2 * ATR_I) / 0.25, 9)) * 0.25
        assert stop == 15001.25
        assert g.bar["stop_mod"].iloc[r] == stop
        assert g.bar["risiko_pt_mod"].iloc[r] == pytest.approx(stop - fyld, abs=1e-9)

    def test_hul_over_et_minut_springes_over_og_taelles(self):
        b = _long_scenarie().fjern("09:11")
        g = _g(b, forudregn=False)
        v = k3.foerste_signal(g, k3.MOD, 1.0)
        assert len(v.raekker) == 0
        assert v.tael["sprunget_over_hul_n"] == 1
        assert v.tael["dage_med_signal_n"] == 1

    def test_efter_et_hul_proeves_naeste_signal(self):
        b = _long_scenarie().groent("09:30", 15003.0, tr=10).fjern("09:11")
        g = _g(b)
        assert _valgt(g) == ["09:30"]
        v = k3.foerste_signal(g, k3.MOD, 1.0)
        assert v.tael["sprunget_over_hul_n"] == 1

    def test_hul_efter_dagens_handel_taelles_ikke(self):
        b = _long_scenarie().groent("09:30", 15003.0, tr=10).fjern("09:31")
        g = _g(b, forudregn=False)
        v = k3.foerste_signal(g, k3.MOD, 1.0)
        assert _valgt(g) == ["09:10"]
        assert v.tael["sprunget_over_hul_n"] == 0


# ===========================================================================
# §11.2 test 6 — i indgangsbaren kan kun stoppet rammes
# ===========================================================================

class TestIndgangsbaren:
    def test_maal_i_indgangsbaren_taeller_ikke(self):
        b = _long_scenarie().minut("09:11", 15003, MAAL_LONG + 1, 15002, 15003)
        h = _handel(_g(b))
        assert h["udfald"] == k3.TIDSEXIT

    def test_maal_naeste_bar_tæller(self):
        b = (_long_scenarie().minut("09:11", 15003, MAAL_LONG + 1, 15002, 15003)
             .minut("09:12", 15003, MAAL_LONG + 1, 15002, 15003))
        g = _g(b)
        h = _handel(g)
        assert h["udfald"] == k3.MAAL
        r = int(h["raekke"])
        assert g.bar["exit_i_mod"].iloc[r] == g.bar["entry_i"].iloc[r] + 1

    def test_stop_i_indgangsbaren_rammes_ogsaa_med_maal(self):
        b = _long_scenarie().minut("09:11", 15003, MAAL_LONG + 1, STOP_LONG - 0.25, 15003)
        g = _g(b)
        h = _handel(g)
        assert h["udfald"] == k3.STOP
        assert not h["tvetydig"]                       # indgangsbaren er aldrig tvetydig
        r = int(h["raekke"])
        assert g.bar["exit_i_mod"].iloc[r] == g.bar["entry_i"].iloc[r]
        assert h["R_brutto"] == pytest.approx(-(RISIKO_LONG + SLIP) / RISIKO_LONG)


# ===========================================================================
# §11.2 test 7 — målet er 1,5R
# ===========================================================================

class TestMaal:
    def test_maalet_ligger_1_5R_fra_fyldet(self):
        under = math.floor(MAAL_LONG / 0.25) * 0.25
        over = math.ceil(MAAL_LONG / 0.25) * 0.25
        assert under < MAAL_LONG < over
        g = _g(_long_scenarie().minut("09:20", 15003, under, 15002, 15003))
        assert _handel(g)["udfald"] == k3.TIDSEXIT
        g = _g(_long_scenarie().minut("09:20", 15003, over, 15002, 15003))
        h = _handel(g)
        assert h["udfald"] == k3.MAAL
        assert h["R_brutto"] == 1.5
        assert h["R_netto"] == pytest.approx(1.5 - k3.OMK_USD_RUNDTUR / (RISIKO_LONG * 2))

    def test_short_maal(self):
        fyld = 14997.0 - SLIP
        risiko = 15001.25 - fyld
        maal = fyld - 1.5 * risiko
        b = Bygger(aabning=k3.OP).roedt("09:10", P).minut(
            "09:20", 14997, 14998, math.floor(maal / 0.25) * 0.25, 14997)
        h = _handel(_g(b))
        assert h["udfald"] == k3.MAAL and h["R_brutto"] == 1.5

    def test_motoren_kaldes_med_be_none_og_maal_1_5(self, monkeypatch):
        kald = []
        oprindelig = trinA.simuler_handel

        def spion(*a, **kw):
            kald.append(kw)
            return oprindelig(*a, **kw)

        monkeypatch.setattr(trinA, "simuler_handel", spion)
        _g(_long_scenarie())
        assert kald and all(kw["be_r"] is None and kw["maal_r"] == 1.5
                            and kw["ret_fyldningsbar"] is True for kw in kald)


# ===========================================================================
# §11.2 test 8 — kun den første handel om dagen
# ===========================================================================

class TestEnHandelOmDagen:
    def test_andet_signal_handles_ikke_efter_stop(self):
        b = (_long_scenarie().minut("09:15", 15003, 15004, STOP_LONG - 1, 15003)
             .groent("09:30", 15003.0, tr=10))
        g = _g(b)
        assert k3.signal_maske(g, k3.MOD, 1.0)[_raekke(g, "09:30")]
        assert _valgt(g) == ["09:10"]
        assert _handel(g)["udfald"] == k3.STOP

    def test_foerste_signal_der_kan_sizes(self):
        """Kan det første signal ikke sizes, er dagens handel det næste, og det første
        tælles. Kontrakterne sættes direkte; sizing testes for sig nedenfor."""
        g = _g(_long_scenarie().groent("09:30", 15003.0, tr=10), forudregn=False)
        g.bar.loc[_raekke(g, "09:10"), "kontrakter_mod"] = 0.0
        v = k3.foerste_signal(g, k3.MOD, 1.0)
        assert _valgt(g) == ["09:30"]
        assert v.tael["afvist_kontrakter_nul_n"] == 1

    def test_en_handel_pr_dag_over_to_dage(self):
        b = Bygger(dage=(DAG, DAG2))
        b.groent("09:10", P).groent("09:40", 15003.0, tr=10)
        b.groent("09:20", P, dag=DAG2)
        g = _g(b, forudregn=False)
        v = k3.foerste_signal(g, k3.MOD, 1.0)
        assert v.tael["handler_n"] == 2
        assert g.bar["dag_pos"].to_numpy()[v.raekker].tolist() == [0, 1]
        assert g.bar["minut_off"].to_numpy()[v.raekker].tolist() == [10, 20]


# ===========================================================================
# §11.2 test 9 — N-tid trækker fra variantens egen minutfordeling
# ===========================================================================

class TestNtid:
    def _nt(self, puljer: dict, n_dage: int = 400) -> k3.NtidGrundlag:
        opslag = np.arange(n_dage * k3.VINDUE_N, dtype=np.int64).reshape(n_dage, k3.VINDUE_N)
        return k3.NtidGrundlag(dage={k: np.arange(n_dage) for k in puljer},
                               pulje={k: np.asarray(p) for k, p in puljer.items()},
                               opslag=opslag)

    def test_kun_puljens_minutter_og_i_dens_forhold(self):
        nt = self._nt({1.0: [5, 5, 5, 40]}, n_dage=4000)
        r, udf = k3.ntid_traek(nt, 1.0, np.random.default_rng(1))
        minut = r % k3.VINDUE_N
        assert udf == 0 and len(r) == 4000
        assert set(minut.tolist()) == {5, 40}
        assert (minut == 5).mean() == pytest.approx(0.75, abs=0.03)
        assert (r // k3.VINDUE_N).tolist() == list(range(4000))   # én pr. modeldag

    def test_hver_variant_har_sin_egen_pulje(self):
        nt = self._nt({1.0: [3], 1.5: [17], 2.0: [90]})
        for k, m in ((1.0, 3), (1.5, 17), (2.0, 90)):
            r, _ = k3.ntid_traek(nt, k, k3.ntid_rng(0, k))
            assert set((r % k3.VINDUE_N).tolist()) == {m}

    def test_celle_uden_handlebar_bar_giver_ingen_handel_og_taelles(self):
        nt = self._nt({1.0: [5]}, n_dage=10)
        nt.opslag[3, 5] = -1
        r, udf = k3.ntid_traek(nt, 1.0, np.random.default_rng(0))
        assert udf == 1 and len(r) == 9

    def test_strømmene(self):
        nt = self._nt({1.0: list(range(120)), 2.0: list(range(120))})
        a, _ = k3.ntid_traek(nt, 1.0, k3.ntid_rng(7, 1.0))
        b, _ = k3.ntid_traek(nt, 1.0, k3.ntid_rng(7, 1.0))
        c, _ = k3.ntid_traek(nt, 1.0, k3.ntid_rng(8, 1.0))
        d, _ = k3.ntid_traek(nt, 2.0, k3.ntid_rng(7, 2.0))
        assert (a == b).all() and not (a == c).all() and not (a == d).all()

    def test_paa_serien_puljen_er_modellens_minutter_og_retningen_modellens(self):
        """Dag 1 åbner ned (signal 09:10), dag 2 op (signal 09:40). Puljen er {10, 40};
        hver trukken handel er long på dag 1 og short på dag 2, fra den trukne bar."""
        b = Bygger(dage=(DAG, DAG2))
        b.groent("09:10", P)
        b.df.loc[_ct("08:59", DAG2), "close"] = P + 0.25
        b.roedt("09:40", P, dag=DAG2)
        g = _g(b)
        valg = k3.alle_valg(g)
        nt = k3.ntid_grundlag(g, {k: valg[(k3.MOD, k)] for k in k3.K_VAERDIER})
        assert sorted(nt.pulje[1.0].tolist()) == [10, 40]
        set_minut = set()
        for rep in range(40):
            r, udf = k3.ntid_traek(nt, 1.0, k3.ntid_rng(rep, 1.0))
            assert udf == 0 and len(r) == 2
            dp = g.bar["dag_pos"].to_numpy()[r]
            assert dp.tolist() == [0, 1]
            assert g.bar["long_mod"].to_numpy()[r].tolist() == [True, False]
            set_minut |= set(g.bar["minut_off"].to_numpy()[r].tolist())
            for rr in r:
                assert g.bar["udfald_mod"].iloc[rr] > 0          # forudregnet
        assert set_minut == {10, 40}

    def test_gentagelsen_er_middel_af_opslaget(self):
        b = Bygger(dage=(DAG, DAG2)).groent("09:10", P).groent("09:40", P, dag=DAG2)
        g = _g(b)
        valg = k3.alle_valg(g)
        nt = k3.ntid_grundlag(g, {k: valg[(k3.MOD, k)] for k in k3.K_VAERDIER})
        rep = k3.ntid_gentagelse(g, nt, 3)
        r, _ = k3.ntid_traek(nt, 1.0, k3.ntid_rng(3, 1.0))
        h = k3.handelstabel(g, r, k3.MOD)
        assert rep[1.0]["m"] == pytest.approx(h["R_netto"].mean())
        assert rep[1.0]["m_bedste"] == pytest.approx(h["R_netto_bedste"].mean())
        assert rep[1.0]["handler_n"] == 2


# ===========================================================================
# §11.2 test 10 — N-med bruger lys i åbningens retning
# ===========================================================================

class TestNmed:
    def test_aabning_ned_roedt_lys_er_short_for_nmed(self):
        b = Bygger(aabning=k3.NED).roedt("09:10", P).groent("09:20", 14997.0)
        g = _g(b)
        assert _valgt(g, k3.MED) == ["09:10"]
        assert _valgt(g, k3.MOD) == ["09:20"]
        h = _handel(g, k3.MED)
        assert h["side"] == "short"
        r = int(h["raekke"])
        assert g.bar["fyld_med"].iloc[r] == pytest.approx(14997.0 - SLIP, abs=1e-9)

    def test_aabning_op_groent_lys_er_long_for_nmed(self):
        b = Bygger(aabning=k3.OP).groent("09:10", P)
        g = _g(b)
        assert _valgt(g, k3.MED) == ["09:10"] and _valgt(g, k3.MOD) == []
        assert _handel(g, k3.MED)["side"] == "long"

    def test_nmed_og_model_paa_samme_bar_har_hver_sin_side(self):
        """Samme bar set fra begge sider: fyld, stop og risiko spejler hinanden."""
        g = _g(Bygger(aabning=k3.NED), forudregn=False)
        r = _raekke(g, "09:30")
        assert bool(g.bar["long_mod"].iloc[r]) and not bool(g.bar["long_med"].iloc[r])
        assert g.bar["fyld_mod"].iloc[r] - P == pytest.approx(P - g.bar["fyld_med"].iloc[r])
        assert g.bar["risiko_pt_mod"].iloc[r] == pytest.approx(g.bar["risiko_pt_med"].iloc[r])


# ===========================================================================
# TR og ATR
# ===========================================================================

class TestATR:
    def test_true_range_med_forrige_close(self):
        tr = k3.true_range([10, 12, 9], [8, 11, 7], [9, 11.5, 8])
        assert tr.tolist() == [2.0, 3.0, 4.5]          # 12 − 9; 11,5 − 7

    def test_wilder_rekursion(self):
        rng = np.random.default_rng(3)
        tr = rng.uniform(0.5, 5, 500)
        a = tr[0]
        forventet = [a]
        for x in tr[1:]:
            a = a + (x - a) / 14
            forventet.append(a)
        assert np.allclose(k3.wilder_atr(tr), forventet, rtol=0, atol=1e-12)

    def test_konstant_tr_giver_praecis_konstant_atr(self):
        assert (k3.wilder_atr(np.full(1000, 2.0)) == 2.0).all()

    def test_atr_paa_hele_serien_ogsaa_over_huller(self):
        """Et hul i serien (en manglende bar) springes ikke over: TR bruger den forrige
        bar i serien, uanset tid."""
        b = Bygger().fjern("09:05")
        b.minut("09:06", P + 3, P + 4, P + 2, P + 3)
        s = k3.Serie.af(b.df)
        i = int(np.flatnonzero(s.tider == _ct("09:06").value)[0])
        assert s.tider[i] - s.tider[i - 1] == 2 * k3.MIN_NS
        assert s.tr[i] == 4.0                          # max(P + 4, P) − min(P + 2, P)


# ===========================================================================
# Motoren: forudregnet = direkte simulering, og tvetydige minutter
# ===========================================================================

def _tilfaeldig_dag(seed: int, aabning: int) -> Bygger:
    """En tilfældig gang i hele ticks fra 07:00 til 15:30 CT."""
    rng = np.random.default_rng(seed)
    b = Bygger(aabning=None)
    n = len(b.df)
    c = P + 0.25 * np.cumsum(rng.integers(-6, 7, n))
    o = np.r_[P, c[:-1]]
    h = np.maximum(o, c) + 0.25 * rng.integers(0, 5, n)
    l = np.minimum(o, c) - 0.25 * rng.integers(0, 5, n)
    b.df[["open", "high", "low", "close"]] = np.column_stack([o, h, l, c])
    i0830 = b.df.index.get_loc(_ct("08:30"))
    i0859 = b.df.index.get_loc(_ct("08:59"))
    # Tving åbningens retning: 08:59 lukker 2 point på den rigtige side af 08:30's open.
    c0859 = o[i0830] + 2.0 * aabning
    b.df.iloc[i0859, b.df.columns.get_loc("close")] = c0859
    b.df.iloc[i0859, b.df.columns.get_loc("high")] = max(h[i0859], c0859)
    b.df.iloc[i0859, b.df.columns.get_loc("low")] = min(l[i0859], c0859)
    return b


class TestForudregnet:
    @pytest.mark.parametrize("seed,aabning", [(1, k3.NED), (2, k3.OP), (3, k3.NED)])
    def test_hver_bar_er_som_direkte_simulering(self, seed, aabning):
        g = _g(_tilfaeldig_dag(seed, aabning))
        b = g.bar
        rows = np.flatnonzero(b["handlebar_mod"].to_numpy())
        assert len(rows) == 120
        for r in rows:
            u, rr, e, _ = trinA.simuler_handel(
                g.s.h, g.s.l, g.s.c, int(b["entry_i"].iloc[r]), float(b["fyld_mod"].iloc[r]),
                bool(b["long_mod"].iloc[r]), float(b["risiko_pt_mod"].iloc[r]), None,
                int(b["cutoff_i"].iloc[r]), g.s.n, True, 1.5)
            assert k3.KODE_UDFALD[int(b["udfald_mod"].iloc[r])] == u
            assert b["R_brutto_mod"].iloc[r] == rr
            assert b["exit_i_mod"].iloc[r] == e

    def test_valgte_handler_er_opslag_i_tabellen(self):
        g = _g(_tilfaeldig_dag(4, k3.NED))
        for k in k3.K_VAERDIER:
            v = k3.foerste_signal(g, k3.MOD, k)
            h = k3.handelstabel(g, v.raekker, k3.MOD)
            for _, x in h.iterrows():
                r = int(x["raekke"])
                u, rr, _, tv = k3.simuler(g.s, int(g.bar["entry_i"].iloc[r]),
                                          float(g.bar["fyld_mod"].iloc[r]), True,
                                          float(g.bar["risiko_pt_mod"].iloc[r]),
                                          int(g.bar["cutoff_i"].iloc[r]))
                assert (x["udfald"], x["R_brutto"], x["tvetydig"]) == (u, rr, tv)

    def test_tvetydig_og_bedste_fald(self):
        """Stop og mål i samme bar efter indgangsbaren: stoppet tæller, tvetydig, og i
        bedste fald er det målet."""
        b = _long_scenarie().minut("09:14", 15003, MAAL_LONG + 1, STOP_LONG - 1, 15003)
        h = _handel(_g(b))
        assert h["udfald"] == k3.STOP and h["tvetydig"]
        assert h["udfald_bedste"] == k3.MAAL
        assert h["R_netto_bedste"] == pytest.approx(1.5 - h["omk_R"])

    def test_handelstabel_kraever_forudregning(self):
        g = _g(_long_scenarie(), forudregn=False)
        v = k3.foerste_signal(g, k3.MOD, 1.0)
        with pytest.raises(RuntimeError):
            k3.handelstabel(g, v.raekker, k3.MOD)


# ===========================================================================
# Stop, sizing og omkostning
# ===========================================================================

class TestSizing:
    def test_stop_rundes_vaek_fra_indgangen(self):
        ind = k3.indgang_og_stop([100.0, 100.0], [1.1, 1.1], [True, False])
        # long: 100,135425 − 2,2 = 97,935… → 97,75; short: 99,864575 + 2,2 = 102,06… → 102,25
        assert ind["stop"].tolist() == [97.75, 102.25]

    def test_stop_praecis_paa_et_tick_flyttes_ikke(self):
        fyld = 100.0 + SLIP
        atr = (fyld - 98.0) / 2                       # stoppet lander præcis på 98,00
        ind = k3.indgang_og_stop([100.0], [atr], [True])
        assert ind["stop"][0] == 98.0

    def test_kontrakter_loft_og_nul(self):
        sz = k3.sizing([2.4, 2.5, 5.0, 125.0, 125.25])
        assert sz["kontrakter_raa"].tolist() == [52, 50, 25, 1, 0]
        assert sz["kontrakter"].tolist() == [50, 50, 25, 1, 0]
        assert sz["omk_R"][2] == pytest.approx(2.627 / 10)

    def test_R_netto_er_uafhaengigt_af_kontrakterne(self):
        """R_netto = (pnl_pt × 2 − 2,627) / (risiko_pt × 2), §3."""
        b = _long_scenarie().minut("09:20", 15003, MAAL_LONG + 1, 15002, 15003)
        h = _handel(_g(b))
        pnl_pt = 1.5 * RISIKO_LONG
        assert h["R_netto"] == pytest.approx((pnl_pt * 2 - 2.627) / (RISIKO_LONG * 2))


# ===========================================================================
# Ruller, halve dage og overnatafkastet
# ===========================================================================

class TestDagen:
    def test_rul_mellem_0830_og_1450_springer_dagen_over(self):
        g = _g(_long_scenarie().rul("12:00"), forudregn=False)
        assert g.dage["status"].iloc[0] == "rul"
        assert _valgt(g) == []
        assert k3.optaelling(g)["dage"]["rul_n"] == 1

    def test_rul_efter_1450_paavirker_ikke_dagen(self):
        g = _g(_long_scenarie().rul("15:00"), forudregn=False)
        assert g.dage["status"].iloc[0] == "ok"
        assert _valgt(g) == ["09:10"]

    def test_fladning_1450_ct(self):
        g = _g(_long_scenarie(), forudregn=False)
        assert g.dage["flad_ns"].iloc[0] == _ct("14:50").value
        h = _handel(_g(_long_scenarie()))
        assert h["udfald"] == k3.TIDSEXIT
        g = _g(_long_scenarie())
        r = int(h["raekke"])
        assert g.s.tider[g.bar["exit_i_mod"].iloc[r]] == _ct("14:49").value

    def test_halv_dag_vinduet_gaelder_og_handlen_lukker_ved_sidste_bar(self):
        """2023-11-24 lukker NYSE 12:00 CT og Globex 12:15 CT. Næste bar er søndag 17:00
        CT. Fladningen er 14:50 CT, så handlen lukker til close i 12:14-baren."""
        halv, soen = "2023-11-24", "2023-11-26"
        b = Bygger(dage=(halv,), til="12:15").groent("09:10", P, dag=halv)
        nat = pd.date_range(_ct("17:00", soen), _ct("17:30", soen), freq="1min",
                            inclusive="left")
        b.df = pd.concat([b.df, pd.DataFrame({"open": P, "high": P + 1, "low": P - 1,
                                              "close": P, "volume": 1.0,
                                              "instrument_id": np.int64(1)}, index=nat)])
        g = _g(b)
        assert len(g.dage) == 1
        assert g.dage["flad_ns"].iloc[0] == _ct("14:50", halv).value
        h = _handel(g)
        assert h["udfald"] == k3.TIDSEXIT
        r = int(h["raekke"])
        assert g.s.tider[g.bar["exit_i_mod"].iloc[r]] == _ct("12:14", halv).value

    def test_overnatafkastets_fortegn(self):
        b = Bygger(dage=(DAG, DAG2))
        b.flad_fra("07:00", P + 10, dag=DAG2)
        b.df.loc[_ct("08:59", DAG2), "close"] = P + 10 - 0.25
        g = _g(b, forudregn=False)
        f = g.dage["overnat_fortegn"].to_numpy()
        assert np.isnan(f[0]) and f[1] == 1.0

    def test_overnatafkastet_trækker_rulspringet_fra(self):
        b = Bygger(dage=(DAG, DAG2))
        b.flad_fra("07:00", P + 10, dag=DAG2)
        b.df.loc[_ct("08:59", DAG2), "close"] = P + 10 - 0.25
        b.rul("07:00", dag=DAG2)                      # springet er hele de 10 point
        g = _g(b, forudregn=False)
        assert g.dage["overnat_fortegn"].iloc[1] == 0.0
        assert g.dage["status"].iloc[1] == "ok"       # rullen ligger før 08:30


# ===========================================================================
# Optællingen simulerer ingen handel
# ===========================================================================

class TestOptaelling:
    def test_ingen_simulering_og_intet_R(self, monkeypatch):
        def forbudt(*a, **kw):
            raise AssertionError("optællingen må ikke simulere en handel")

        monkeypatch.setattr(trinA, "simuler_handel", forbudt)
        b = Bygger(dage=(DAG, DAG2)).groent("09:10", P).roedt("09:15", P, dag=DAG2)
        g = _g(b, forudregn=False)
        o = k3.optaelling(g)
        noegler = set(o["dage"]) | {x for r in o["varianter"] + o["aar"] for x in r}
        # omk_R_netto_p50/p90 er omkostningen i R og hører til optællingen (§11.4).
        for x in noegler:
            assert not x.startswith(("R_", "middel_R", "win_rate", "udfald", "tvetydig")), x
        model = {r["k"]: r for r in o["varianter"] if r["model"] == "vending"}
        assert model[1.0]["handler_n"] == 1
        assert model[1.0]["signalminut_p50"] == 9 * 60 + 10
        assert not model[1.0]["betingelse_ok"]
        # Begge dage åbner ned: dag 1's grønne lys er modellens, dag 2's røde er N-med's.
        nmed = {r["k"]: r for r in o["varianter"] if r["model"] == "N_med"}
        assert nmed[1.0]["handler_n"] == 1
        assert nmed[1.0]["signalminut_p50"] == 9 * 60 + 15

    def test_dage_med_og_uden_signal(self):
        b = Bygger(dage=(DAG, DAG2)).groent("09:10", P)
        g = _g(b, forudregn=False)
        o = k3.optaelling(g)
        model = {r["k"]: r for r in o["varianter"] if r["model"] == "vending"}[1.0]
        assert model["dage_med_aabningsretning_n"] == 2
        assert model["dage_med_signal_n"] == 1 and model["dage_uden_signal_n"] == 1


# ===========================================================================
# §7 og §8
# ===========================================================================

def _r(p, m, lo):
    return {"p_FWE": p, "middel_R_netto": m, "middel_R_netto_ci95_lo": lo}


class TestBeslutning:
    def test_raekke_1_fryser_hoejeste_ci_nedre(self):
        b = k3.beslutning({1.0: _r(0.01, 0.25, 0.05), 1.5: _r(0.02, 0.30, 0.10),
                           2.0: _r(0.20, 0.40, 0.20)})
        assert b["raekke"] == 1 and b["variant"] == 1.5

    def test_raekke_2(self):
        b = k3.beslutning({1.0: _r(0.01, 0.15, 0.02), 1.5: _r(0.5, 0.0, -0.1),
                           2.0: _r(0.5, 0.0, -0.1)})
        assert b["raekke"] == 2

    def test_raekke_3(self):
        b = k3.beslutning({1.0: _r(0.30, 0.25, 0.05), 1.5: _r(0.5, 0.0, -0.1),
                           2.0: _r(0.5, 0.0, -0.1)})
        assert b["raekke"] == 3 and b["kandidater"] == [1.0]

    def test_raekke_4(self):
        b = k3.beslutning({1.0: _r(0.01, 0.25, -0.01), 1.5: _r(0.5, 0.0, -0.1),
                           2.0: _r(0.5, 0.0, -0.1)})
        assert b["raekke"] == 4
        b = k3.beslutning({k: _r(0.9, -0.1, -0.2) for k in k3.K_VAERDIER})
        assert b["raekke"] == 4

    def test_signifikant_og_ci_nedre_paa_graensen_er_ikke_opfyldt(self):
        b = k3.beslutning({1.0: _r(0.05, 0.25, 0.0), 1.5: _r(0.5, 0.0, -0.1),
                           2.0: _r(0.5, 0.0, -0.1)})
        assert b["raekke"] == 4


class TestMDE:
    @pytest.mark.parametrize("n,ukorr,sidak", [(400, 0.152, 0.181), (600, 0.124, 0.148),
                                               (800, 0.108, 0.128), (1000, 0.096, 0.115)])
    def test_tabellen_i_paragraf_7(self, n, ukorr, sidak):
        assert round(k3.mde(n, k3.Z_UKORR), 3) == ukorr
        assert round(k3.mde(n), 3) == sidak

    def test_minimum_330(self):
        assert k3.MIN_HANDLER == math.ceil((k3.Z_SIDAK3 * k3.SIGMA_R / 0.20) ** 2)
        assert k3.mde(330) <= 0.20 < k3.mde(329)
