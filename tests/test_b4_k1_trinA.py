"""Tests for research/b4_k1_trinA.py — handelsmodulet for B4 kandidat 1, trin A.

To lag testes hver for sig:

1. ``simuler_handel`` — selve handelens gang på rene numpy-arrays: mål, stop, regel 4's
   tie-break, BE-armering og -udgang, "ingen"-variantens manglende BE, tidsexit 14:50 CT,
   censurering ved in-sample-slut. Ingen zoner eller data involveret.
2. ``sizing_ekte`` — den ægte punktrisiko (E − low / high − E), IKKE k1's NQ 29.138-
   normerede tal. Det er den vigtigste enkeltstående ting at få ret i modulet.
3. ``handler_for_variant`` — fyldningsreglen (gennemhandling, ikke berøring), strejf og
   dens kontrafaktiske gennemkøring, og disciplinreglerne: position åben, dagen lukket,
   to BE'er lukker dagen, "ingen"-varianten giver højst 1 handel/dag.
4. Et lille endt-til-anden smoke-test af ``simuler_alle_varianter``/``noegletal_handler``.
"""
from __future__ import annotations

from fractions import Fraction

import numpy as np
import pandas as pd
import pytest

from research import b4_k1_optaelling as k1
from research import b4_k1_trinA as t

CT = "America/Chicago"


def _ct(s) -> pd.Timestamp:
    ts = pd.Timestamp(s)
    return ts.tz_localize(CT) if ts.tzinfo is None else ts.tz_convert(CT)


# ===========================================================================
# 1. simuler_handel — rene arrays, ingen zoner
# ===========================================================================

ENTRY = 100.0
RISIKO = 10.0            # stop 90, mål 120 for demand; stop 110, mål 80 for supply


def _flad(h, l, c, entry_i=0, demand=True, be_r=None, cutoff_i=1000):
    h, l, c = np.asarray(h, float), np.asarray(l, float), np.asarray(c, float)
    return t.simuler_handel(h, l, c, entry_i, ENTRY, demand, RISIKO, be_r, cutoff_i, len(h))


class TestSimulerHandelMaalOgStop:
    def test_maal_ramt_giver_plus_2R_brutto_uden_slippage(self):
        udfald, r, i = _flad(h=[105, 121], l=[98, 99], c=[102, 120])
        assert (udfald, r, i) == (t.MAAL, pytest.approx(2.0), 1)

    def test_stop_ramt_traekker_slippage_fra(self):
        udfald, r, i = _flad(h=[105], l=[89], c=[90])
        forventet = ((90 - t.SLIP_PT) - ENTRY) / RISIKO
        assert (udfald, i) == (t.STOP, 0)
        assert r == pytest.approx(forventet)
        assert r < -1.0        # slippage gør tabet værre end -1R

    def test_regel_4_begge_ramt_samme_bar_stoppet_vinder(self):
        udfald, r, i = _flad(h=[125], l=[85], c=[100])
        assert udfald == t.STOP
        assert r == pytest.approx(((90 - t.SLIP_PT) - ENTRY) / RISIKO)

    def test_supply_er_spejlvendt(self):
        udfald, r, i = _flad(h=[110], l=[79], c=[100], demand=False)
        # mål 80 og stop 110 begge ramt: stoppet vinder (regel 4)
        assert udfald == t.STOP
        assert r == pytest.approx((ENTRY - (110 + t.SLIP_PT)) / RISIKO)

    def test_supply_maal_alene(self):
        udfald, r, i = _flad(h=[102], l=[79], c=[80], demand=False)
        assert (udfald, r) == (t.MAAL, pytest.approx(2.0))

    def test_fyldningsbaren_selv_kan_afgoere_handlen(self):
        """entry_i er selve fyldningsbaren — den skal også tjekkes."""
        udfald, r, i = _flad(h=[121], l=[99], c=[120])
        assert (udfald, i) == (t.MAAL, 0)


class TestSimulerHandelBE:
    def test_be_armering_flytter_stoppet_til_E_uden_at_lukke_samme_bar(self):
        """Baren der krydser triggeren rammer ikke den (endnu ikke armerede) BE-stop."""
        # be_trigger ved 1,0R = 110. Bar0 krydser den (h=112) med l=95: intet ramt.
        udfald, r, i = _flad(h=[112, 101], l=[95, 89], c=[105, 90], be_r=1.0)
        # Bar1: stop nu E=100. low=89 <= 100 → BE-udgang.
        assert udfald == t.BE_UDFALD
        assert r == pytest.approx((ENTRY - t.SLIP_PT - ENTRY) / RISIKO)
        assert r < 0 and r > -0.1          # "BE er ikke nul", men langt fra -1R

    def test_be_armeret_men_fortsaetter_til_maal(self):
        udfald, r, i = _flad(h=[112, 125], l=[95, 105], c=[105, 122], be_r=1.0)
        assert (udfald, r) == (t.MAAL, pytest.approx(2.0))

    def test_ingen_be_variant_bruger_aldrig_be_selvom_triggeren_krydses(self):
        """be_r=None: samme priser som armeringstesten, men her lukker det som stop."""
        udfald, r, i = _flad(h=[112], l=[89], c=[90], be_r=None)
        assert udfald == t.STOP           # ikke BE — variant "ingen" kender ikke BE
        assert r == pytest.approx(((90 - t.SLIP_PT) - ENTRY) / RISIKO)

    def test_be_1_2R_trigger_er_stoerre_end_1_0R(self):
        # h=111 krydser 1,0R (110) men ikke 1,2R (112)
        udfald, r, i = _flad(h=[111, 101], l=[95, 89], c=[105, 90], be_r=1.2)
        assert udfald == t.STOP           # ikke armeret, så det er det oprindelige stop


class TestSimulerHandelTidOgCensurering:
    def test_tidsexit_lukker_til_sidste_lukkekurs_foer_cutoff(self):
        h = [105, 105, 105, 105]
        l = [95, 95, 95, 95]
        c = [101, 102, 103, 104]
        udfald, r, i = _flad(h, l, c, cutoff_i=3)
        assert (udfald, i) == (t.TIDSEXIT, 2)
        assert r == pytest.approx((103 - ENTRY) / RISIKO)

    def test_censurering_naar_data_slutter_foer_cutoff(self):
        h = [105, 105, 105]
        l = [95, 95, 95]
        c = [101, 102, 103]
        udfald, r, i = _flad(h, l, c, cutoff_i=1000)   # cutoff langt ude, data slutter først
        assert (udfald, i) == (t.CENSURERET, 2)
        assert r == pytest.approx((103 - ENTRY) / RISIKO)

    def test_cutoff_ved_selve_fyldningsbaren_giver_stadig_et_udfald(self):
        udfald, r, i = _flad(h=[105], l=[95], c=[101], entry_i=0, cutoff_i=0)
        assert i == 0 and udfald in (t.TIDSEXIT, t.CENSURERET)


class TestFladTidUtc:
    def test_1450_ct_alle_ugedage_ingen_halv_dags_undtagelse(self):
        """Fladt-reglen er et fast klokkeslæt, uafhængigt af RTH-kalenderens halve dage."""
        for dag in ("2023-06-14", "2023-11-24", "2023-07-03"):   # sidste to: halve dage
            fyld = _ct(f"{dag} 09:03").tz_convert("UTC")
            graense = t.flad_tid_utc(fyld)
            assert graense.tz_convert(CT).strftime("%H:%M") == "14:50"
            assert graense.date() == _ct(f"{dag} 00:00").date()

    def test_virker_over_sommertidsskiftet(self):
        for dag in ("2023-01-11", "2023-06-14"):     # CST og CDT
            fyld = _ct(f"{dag} 09:00").tz_convert("UTC")
            assert t.flad_tid_utc(fyld).tz_convert(CT).strftime("%H:%M") == "14:50"


# ===========================================================================
# 2. sizing_ekte — den ægte punktrisiko, ikke k1's NQ 29.138-normering
# ===========================================================================

def _zoner_stub(side, E, zone_low, zone_high) -> pd.DataFrame:
    return pd.DataFrame({"side": [side], "E": [E], "zone_low": [zone_low],
                         "zone_high": [zone_high]})


class TestSizingEkte:
    def test_demand_risiko_er_E_minus_low(self):
        z = t.sizing_ekte(_zoner_stub(k1.DEMAND, E=10_017.0, zone_low=9_995.0, zone_high=10_015.0))
        assert z["risiko_pt_ekte"].iloc[0] == pytest.approx(22.0)
        assert z["kontrakter_ekte"].iloc[0] == np.floor(250 / (22.0 * 2))
        assert z["omk_R_netto_ekte"].iloc[0] == pytest.approx(2.627 / (22.0 * 2))

    def test_supply_risiko_er_high_minus_E(self):
        z = t.sizing_ekte(_zoner_stub(k1.SUPPLY, E=9_983.0, zone_low=9_985.0, zone_high=10_005.0))
        assert z["risiko_pt_ekte"].iloc[0] == pytest.approx(22.0)

    def test_risikoen_er_uafhaengig_af_nq_niveau_29138(self):
        """En lav historisk pris (2019-MNQ) skal give langt flere kontrakter end k1's
        NQ 29.138-normerede sizing ville — det er netop pointen med §4d."""
        z = t.sizing_ekte(_zoner_stub(k1.DEMAND, E=8_020.0, zone_low=8_000.0, zone_high=8_015.0))
        assert z["risiko_pt_ekte"].iloc[0] == pytest.approx(20.0)
        assert z["kontrakter_ekte"].iloc[0] == np.floor(250 / (20.0 * 2))     # 6, ikke 1-2
        assert z["kontrakter_ekte"].iloc[0] >= 5

    def test_reelt_stoploft_grebet_giver_ikke_0_kontrakter_i_2019_2023_vinduet(self):
        """0,429% er kalibreret ved NQ 29.138 = præcis $250 for 1 kontrakt der. Ved
        lavere reelle priser (MNQ 2019-2023) giver loftet aldrig 0 ægte kontrakter."""
        pris = 8_000.0
        risiko_pt = 0.00429 * pris          # lige på loftet
        z = t.sizing_ekte(_zoner_stub(k1.DEMAND, E=pris + risiko_pt, zone_low=pris,
                                       zone_high=pris + risiko_pt))
        assert z["kontrakter_ekte"].iloc[0] >= 1


class TestSizingTabel:
    def _pop(self) -> pd.DataFrame:
        # 2019: dyr risiko relativt (lav pris), én zone afvist af dollarloftet.
        # 2023: billigere risiko relativt (høj pris), ingen afvist.
        return pd.DataFrame([
            {"i_vindue": True, "dag": pd.Timestamp("2019-06-01"),
             "risiko_pt_ekte": 9.0, "kontrakter_ekte": 13.0, "omk_R_netto_ekte": 0.1500},
            {"i_vindue": True, "dag": pd.Timestamp("2019-07-01"),
             "risiko_pt_ekte": 130.0, "kontrakter_ekte": 0.0, "omk_R_netto_ekte": 0.0800},
            {"i_vindue": True, "dag": pd.Timestamp("2023-06-01"),
             "risiko_pt_ekte": 21.0, "kontrakter_ekte": 5.0, "omk_R_netto_ekte": 0.0625},
            {"i_vindue": False, "dag": pd.Timestamp("2023-06-02"),        # ikke i populationen
             "risiko_pt_ekte": 5.0, "kontrakter_ekte": 20.0, "omk_R_netto_ekte": 0.26},
        ])

    def test_population_er_i_vindue_foer_dollarloftet(self):
        tab = t.sizing_tabel(self._pop())
        alle = tab[tab["periode"] == "alle"].iloc[0]
        assert alle["zoner_i_vindue_n"] == 3            # ikke de 4 — den fjerde er ikke i_vindue
        assert alle["afvist_kontrakter_nul_n"] == 1

    def test_pr_aar_og_konsekvensen_maales_ikke_antages(self):
        tab = t.sizing_tabel(self._pop())
        y19 = tab[tab["periode"] == "2019"].iloc[0]
        y23 = tab[tab["periode"] == "2023"].iloc[0]
        assert (y19["zoner_i_vindue_n"], y23["zoner_i_vindue_n"]) == (2, 1)
        assert y19["afvist_kontrakter_nul_n"] == 1 and y23["afvist_kontrakter_nul_n"] == 0
        # 2019's median omkostning i R er tungere end 2023's — §4d's pointe.
        assert y19["omk_R_netto_p50"] > y23["omk_R_netto_p50"]
        assert y19["kontrakter_maks"] == 13.0 and y23["kontrakter_maks"] == 5.0
        assert y19["be_WR_pct_netto_p50"] > y23["be_WR_pct_netto_p50"]

    def test_tom_population_giver_ingen_fejl(self):
        tom = pd.DataFrame(columns=["i_vindue", "dag", "risiko_pt_ekte", "kontrakter_ekte",
                                    "omk_R_netto_ekte"])
        tab = t.sizing_tabel(tom)
        assert len(tab) == 1 and tab.iloc[0]["periode"] == "alle"
        assert tab.iloc[0]["zoner_i_vindue_n"] == 0


# ===========================================================================
# 3. handler_for_variant — fyldning, strejf og disciplinreglerne
# ===========================================================================

def _1m(rows, start_ct="2023-06-14 09:00") -> pd.DataFrame:
    """Sammenhængende 1m-barer fra ``start_ct`` (CT), én pr. minut."""
    a = np.asarray(rows, dtype=float)
    idx = pd.date_range(_ct(start_ct), periods=len(a), freq="1min").tz_convert("UTC")
    return pd.DataFrame({"open": a[:, 0], "high": a[:, 1], "low": a[:, 2], "close": a[:, 3],
                         "volume": 1.0}, index=idx.rename("time"))


def _zone(side, E, risiko_pt, dag, slut_tid, basis_i=0, kontrakter=2, omk_R=0.01,
         i_vindue=True) -> dict:
    return {"side": side, "E": E, "risiko_pt_ekte": risiko_pt, "kontrakter_ekte": kontrakter,
            "omk_R_netto_ekte": omk_R, "i_vindue": i_vindue, "dag": pd.Timestamp(dag),
            "slut_tid": _ct(slut_tid).tz_convert("UTC"), "basis_i": basis_i}


FLAT = (10_022.0, 10_022.0, 10_022.0, 10_022.0)     # ingen touch, intet ramt


def _serie(n_minutter, start_ct="2023-06-14 09:00", flad_ved=None):
    """``n_minutter`` flade barer med værdien FLAT, undtagen dem der overskrives."""
    rows = [FLAT] * n_minutter
    if flad_ved:
        for i, bar in flad_ved.items():
            rows[i] = bar
    return _1m(rows, start_ct)


class TestFyldning:
    def test_gennemhandling_kraeves_beroering_alene_er_strejf(self):
        """low = E (berøring) uden at gå ét tick igennem: ingen handel, tælles som strejf."""
        zone = _zone(k1.DEMAND, E=10_020.0, risiko_pt=20.0, dag="2023-06-14",
                     slut_tid="2023-06-14 09:00")
        df = _serie(20, flad_ved={3: (10_020.0, 10_020.0, 10_020.0, 10_020.0)})   # low == E
        handler, tael, strejf = t.handler_for_variant(df, pd.DataFrame([zone]), be_r=None)
        assert len(handler) == 0
        assert len(strejf) == 1

    def test_et_tick_igennem_fylder_ordren(self):
        zone = _zone(k1.DEMAND, E=10_020.0, risiko_pt=20.0, dag="2023-06-14",
                     slut_tid="2023-06-14 09:00")
        df = _serie(60, flad_ved={3: (10_020.0, 10_020.0, 10_019.75, 10_020.0),
                                  30: (10_060.0, 10_061.0, 10_060.0, 10_060.0)})
        handler, tael, strejf = t.handler_for_variant(df, pd.DataFrame([zone]), be_r=None)
        assert len(handler) == 1 and len(strejf) == 0
        r = handler.iloc[0]
        assert r["fyld_tid"] == df.index[3]
        assert r["udfald"] == t.MAAL

    def test_fyldes_altid_til_E_aldrig_bedre_selv_ved_gap(self):
        zone = _zone(k1.DEMAND, E=10_020.0, risiko_pt=20.0, dag="2023-06-14",
                     slut_tid="2023-06-14 09:00")
        # gap: lyset åbner og lukker langt under E, low 10.000 (10 point igennem)
        df = _serie(20, flad_ved={2: (10_005.0, 10_006.0, 10_000.0, 10_003.0)})
        handler, _, _ = t.handler_for_variant(df, pd.DataFrame([zone]), be_r=None)
        # målet er E+2*risiko = 10.060, stoppet E-risiko = 10.000 — fyldningskursen er E,
        # så gap-baren rammer også stoppet (low 10.000 <= 10.000): R skal regnes fra E.
        assert handler.iloc[0]["udfald"] == t.STOP
        forventet = ((10_000.0 - t.SLIP_PT) - 10_020.0) / 20.0
        assert handler.iloc[0]["R_brutto"] == pytest.approx(forventet)

    def test_strejf_kontrafaktisk_koeres_gennem_samme_maskineri(self):
        zone = _zone(k1.DEMAND, E=10_020.0, risiko_pt=20.0, dag="2023-06-14",
                     slut_tid="2023-06-14 09:00")
        df = _serie(60, flad_ved={
            3: (10_020.0, 10_020.0, 10_020.0, 10_020.0),      # berøring, ikke gennemhandlet
            30: (10_060.0, 10_061.0, 10_060.0, 10_060.0),     # ville have ramt målet
        })
        handler, tael, strejf = t.handler_for_variant(df, pd.DataFrame([zone]), be_r=None)
        assert len(handler) == 0 and len(strejf) == 1
        assert strejf.iloc[0]["udfald"] == t.MAAL
        assert strejf.iloc[0]["R_brutto"] == pytest.approx(2.0)


class TestDisciplin:
    def _to_kandidater(self, dag="2023-06-14"):
        z1 = _zone(k1.DEMAND, E=10_020.0, risiko_pt=20.0, dag=dag,
                  slut_tid=f"{dag} 09:00", basis_i=0)
        z2 = _zone(k1.SUPPLY, E=9_980.0, risiko_pt=20.0, dag=dag,
                  slut_tid=f"{dag} 09:15", basis_i=1)
        return z1, z2

    def test_beroering_mens_position_er_aaben_springes_over_og_taelles(self):
        z1, z2 = self._to_kandidater()
        # z1 fyldes 09:03, armerer BE ved bar 50 og lukker der (BE alene lukker ikke
        # dagen) — z2's berøring 09:15 falder inden for den åbne handels levetid, så
        # den skal springes over som "position åben", ikke "dagen lukket" (den er ikke).
        df = _serie(120, flad_ved={
            3: (10_020.0, 10_020.0, 10_019.75, 10_020.0),       # z1 fyldes, stop 10.000
            50: (10_041.0, 10_041.0, 10_030.0, 10_035.0),        # krydser BE-triggeren 10.040
            80: (10_022.0, 10_022.0, 10_019.9, 10_020.0),        # BE-stop (10.020) ramt
        })
        handler, tael, strejf = t.handler_for_variant(
            df, pd.DataFrame([z1, z2]), be_r=1.0)
        assert len(handler) == 1                       # kun z1 blev handlet
        assert handler.iloc[0]["udfald"] == t.BE_UDFALD
        assert tael["signaler_sprunget_over_position_n"] == 1
        assert tael["signaler_sprunget_over_dagslukket_n"] == 0
        assert len(strejf) == 0                          # z2 blev aldrig fyldnings-tjekket

    def test_dagen_lukker_efter_foerste_afgjorte_handel_ingen_be(self):
        z1, z2 = self._to_kandidater()
        df = _serie(60, flad_ved={
            3: (10_020.0, 10_020.0, 10_019.75, 10_020.0),
            5: (10_060.0, 10_061.0, 10_060.0, 10_060.0),            # z1 rammer mål tidligt
            30: (9_980.0, 9_980.0, 9_979.75, 9_980.0),               # z2's berøring, senere
        })
        handler, tael, strejf = t.handler_for_variant(
            df, pd.DataFrame([z1, z2]), be_r=None)
        assert len(handler) == 1
        assert tael["signaler_sprunget_over_dagslukket_n"] == 1

    def test_to_be_udgange_lukker_dagen_men_en_alene_goer_ikke(self):
        z1, z2 = self._to_kandidater()
        # be_r=1,0R: trigger for z1 (demand, E=10.020, risiko 20) er 10.040, BE-stoppet
        # er E=10.020. For z2 (supply, E=9.980) er triggeren 9.960, BE-stoppet 9.980.
        # Efter z1 er lukket (bar 5) skal fyld-barerne være "sikre" for z2's stop/mål —
        # de globale FLAT-barer (10.022) er kun sikre for demand-zonen z1.
        flad_ved = {i: (9_990.0, 9_990.0, 9_990.0, 9_990.0) for i in range(6, 60)}
        flad_ved.update({
            3: (10_020.0, 10_020.0, 10_019.75, 10_020.0),        # z1 fyldes
            4: (10_041.0, 10_041.0, 10_030.0, 10_035.0),          # z1 krydser BE-triggeren
            5: (10_022.0, 10_022.0, 10_019.9, 10_020.0),          # z1's BE-stop ramt
            20: (9_980.0, 9_980.0, 9_979.75, 9_980.0),            # z2 fyldes (position var fri)
            25: (9_961.0, 9_961.0, 9_959.0, 9_960.0),              # z2 krydser BE-triggeren
            26: (9_980.1, 9_980.1, 9_980.0, 9_980.0),              # z2's BE-stop ramt
        })
        df = _serie(60, flad_ved=flad_ved)
        handler, tael, strejf = t.handler_for_variant(
            df, pd.DataFrame([z1, z2]), be_r=1.0)
        assert len(handler) == 2
        assert (handler.iloc[0]["udfald"], handler.iloc[1]["udfald"]) == (t.BE_UDFALD, t.BE_UDFALD)
        assert tael["signaler_sprunget_over_dagslukket_n"] == 0   # begge blev handlet

    def test_kontrakter_nul_udelukker_kandidaten(self):
        zone = _zone(k1.DEMAND, E=10_020.0, risiko_pt=20.0, dag="2023-06-14",
                     slut_tid="2023-06-14 09:00", kontrakter=0)
        df = _serie(20, flad_ved={3: (10_020.0, 10_020.0, 10_019.75, 10_020.0)})
        handler, tael, strejf = t.handler_for_variant(df, pd.DataFrame([zone]), be_r=None)
        assert len(handler) == 0 and len(strejf) == 0

    def test_kun_i_vindue_zoner_er_kandidater(self):
        """IKKE k1's ``signal`` — den bærer stadig den droppede procentregel, §4d."""
        zone = _zone(k1.DEMAND, E=10_020.0, risiko_pt=20.0, dag="2023-06-14",
                     slut_tid="2023-06-14 09:00", i_vindue=False)
        df = _serie(20, flad_ved={3: (10_020.0, 10_020.0, 10_019.75, 10_020.0)})
        handler, tael, strejf = t.handler_for_variant(df, pd.DataFrame([zone]), be_r=None)
        assert len(handler) == 0 and len(strejf) == 0

    def test_hoej_risiko_afvist_selvom_under_0429_pct_ikke_er_sat(self):
        """§4d: kontrakter_ekte >= 1 er det ENESTE loft — der er ingen procenttest her.
        En zone med kontrakter_ekte = 0 (for stor dollarrisiko) udelukkes uanset."""
        zone = _zone(k1.DEMAND, E=10_020.0, risiko_pt=130.0, dag="2023-06-14",
                     slut_tid="2023-06-14 09:00", kontrakter=0, i_vindue=True)
        df = _serie(20, flad_ved={3: (10_020.0, 10_020.0, 10_019.75, 10_020.0)})
        handler, tael, strejf = t.handler_for_variant(df, pd.DataFrame([zone]), be_r=None)
        assert len(handler) == 0 and len(strejf) == 0


# ===========================================================================
# 4. Smoke-test — simuler_alle_varianter / noegletal_handler
# ===========================================================================

def test_seks_varianter_koerer_og_giver_fornuftige_noegletal():
    """Endt-til-anden: 1m → 15m → zoner (kerne v2) → 6 varianters handler. En demand-zone
    med udbrud der handler klart igennem E, så mindst én variant får en rigtig handel."""
    from data import resample

    DAG = "2023-06-14"
    BASIS_D = (10_010, 10_015, 9_995, 10_000)
    UDBRUD_D = (10_000, 10_030, 9_998, 10_020)
    OVER = (10_022, 10_025, 10_020, 10_022)
    GENNEM = (10_005, 10_006, 9_990, 9_991)      # handler klart igennem E (10.017 m. buffer)

    def _sti(lys15):
        rows = []
        for o, h, l, c in lys15:
            path = np.linspace(o, c, 15)
            for i, p in enumerate(path):
                rows.append((p, h if i == 5 else p, l if i == 10 else p, p))
        return rows

    df_1m = _1m(_sti([BASIS_D, UDBRUD_D, OVER, GENNEM] + [OVER] * 10),
               start_ct=f"{DAG} 09:00")
    bars15 = resample.aggregate(df_1m, 15)

    ud = t.simuler_alle_varianter(df_1m, bars15)
    assert len(ud) == 6
    handler_i_alt = 0
    for navn, res in ud.items():
        row = t.noegletal_handler(res)
        assert row["handler_n"] >= 0
        assert set(res["handler"]["udfald"]).issubset(set(t.UDFALD))
        assert set(res["strejf"]["udfald"]).issubset(set(t.UDFALD))
        handler_i_alt += row["handler_n"]
    assert handler_i_alt > 0


# ===========================================================================
# 5. N1 (FORELØBIG — kun til punkt 4's tidsmåling) — dannelseslyset, §5
# ===========================================================================

def _bars15(n, start_ct="2023-06-05 09:00") -> pd.DataFrame:
    """n sammenhængende 15m-barer, flade OHLC — til at teste ugegrænser og geometri."""
    idx = pd.date_range(_ct(start_ct), periods=n, freq="15min").tz_convert("UTC")
    return pd.DataFrame({"open": 10_000.0, "high": 10_000.0, "low": 10_000.0,
                         "close": 10_000.0}, index=idx.rename("time"))


class TestUgeId:
    def test_samme_iso_uge_faar_samme_id(self):
        idx = pd.DatetimeIndex([_ct("2023-06-05 09:00"),
                                _ct("2023-06-09 15:00")]).tz_convert("UTC")
        ud = t._uge_id(idx)
        assert ud[0] == ud[1]           # mandag og fredag, samme ISO-uge

    def test_naeste_uge_faar_andet_id(self):
        idx = pd.DatetimeIndex([_ct("2023-06-09 15:00"),
                                _ct("2023-06-12 09:00")]).tz_convert("UTC")
        ud = t._uge_id(idx)
        assert ud[0] != ud[1]


class TestN1Dannelseslys:
    def test_trukket_lys_er_i_samme_uge_som_basislys_og_efterlader_plads(self):
        bars = _bars15(4 * 96, start_ct="2023-06-05 00:00")     # fire hele uger
        uge = t._uge_id(bars.index)
        rng = np.random.default_rng(0)
        basis_i = np.array([10, 300])
        b_n1 = t.n1_dannelseslys(bars, basis_i, rng)
        assert (b_n1 >= 0).all()
        assert uge[b_n1[0]] == uge[basis_i[0]]
        assert uge[b_n1[1]] == uge[basis_i[1]]
        graenser = np.flatnonzero(np.r_[True, uge[1:] != uge[:-1]])
        graenser = np.r_[graenser, len(bars)]
        for b in b_n1:
            gi = np.searchsorted(graenser, b, side="right") - 1
            assert b + 1 < graenser[gi + 1]      # et "udbrudslys" findes i samme uge

    def test_minus1_naar_ugen_ikke_har_plads_til_endnu_et_lys(self):
        bars = _bars15(1)                          # basislyset er selv sidste i ugen
        b_n1 = t.n1_dannelseslys(bars, np.array([0]), np.random.default_rng(0))
        assert b_n1[0] == -1

    def test_reproducerbar_med_samme_seed(self):
        bars = _bars15(200, start_ct="2023-06-05 00:00")
        basis_i = np.array([5, 50, 150])
        a = t.n1_dannelseslys(bars, basis_i, np.random.default_rng(42))
        b = t.n1_dannelseslys(bars, basis_i, np.random.default_rng(42))
        assert (a == b).all()


class TestFindZonerN1:
    def test_demand_bygges_fra_det_trukne_lys_high_med_rigtig_H(self):
        bars = _bars15(10, start_ct="2023-06-05 09:00")
        bars.loc[bars.index[3], ["open", "high", "low", "close"]] = \
            [10_050.0, 10_060.0, 10_045.0, 10_050.0]
        z = t.find_zoner_n1(bars, side=np.array([t.DEMAND]), H=np.array([20.0]),
                            b_n1=np.array([3]), buffer=Fraction(0))
        assert len(z) == 1
        r = z.iloc[0]
        assert (r["zone_high"], r["zone_low"]) == (10_060.0, 10_040.0)   # high, high − H
        assert r["side"] == t.DEMAND and r["basis_i"] == 3

    def test_supply_bygges_fra_det_trukne_lys_low_med_rigtig_H(self):
        bars = _bars15(10, start_ct="2023-06-05 09:00")
        bars.loc[bars.index[3], ["open", "high", "low", "close"]] = \
            [9_950.0, 9_955.0, 9_940.0, 9_950.0]
        z = t.find_zoner_n1(bars, side=np.array([t.SUPPLY]), H=np.array([20.0]),
                            b_n1=np.array([3]), buffer=Fraction(0))
        r = z.iloc[0]
        assert (r["zone_high"], r["zone_low"]) == (9_960.0, 9_940.0)     # low + H, low

    def test_minus1_springes_over(self):
        bars = _bars15(10)
        z = t.find_zoner_n1(bars, side=np.array([t.DEMAND, t.SUPPLY]),
                            H=np.array([20.0, 20.0]), b_n1=np.array([-1, 3]),
                            buffer=Fraction(0))
        assert len(z) == 1 and z.iloc[0]["basis_i"] == 3

    def test_klassificer_v2_genbruges_uaendret_paa_n1_zoner(self):
        """Kerne v2's egen forløbslogik (afprøvet i test_b4_k1_optaelling.py) skal
        virke uændret på N1's zoner — den kaldes direkte, ikke genskrevet her."""
        bars = _bars15(20, start_ct="2023-06-14 09:00")
        b = 3
        bars.loc[bars.index[b], ["open", "high", "low", "close"]] = \
            [10_000.0, 10_020.0, 9_995.0, 10_000.0]
        bars.loc[bars.index[b + 1], ["open", "high", "low", "close"]] = \
            [10_022.0, 10_025.0, 10_021.0, 10_022.0]      # aktiverer: low (10.021) > E (10.020)
        bars.loc[bars.index[b + 2], ["open", "high", "low", "close"]] = \
            [10_019.0, 10_020.0, 10_018.0, 10_019.0]      # berører: low (10.018) <= E
        z = t.find_zoner_n1(bars, side=np.array([t.DEMAND]), H=np.array([25.0]),
                            b_n1=np.array([b]), buffer=Fraction(0))
        klass = t.k1.klassificer_v2(bars, z, Fraction(0))
        assert (klass.iloc[0]["status"], klass.iloc[0]["slut_i"]) == ("beroert", b + 2)


def test_n1_gentagelse_koerer_og_har_samme_form_som_simuler_alle_varianter():
    from data import resample

    DAG = "2023-06-14"
    BASIS_D = (10_010, 10_015, 9_995, 10_000)
    UDBRUD_D = (10_000, 10_030, 9_998, 10_020)
    OVER = (10_022, 10_025, 10_020, 10_022)
    GENNEM = (10_005, 10_006, 9_990, 9_991)

    def _sti(lys15):
        rows = []
        for o, h, l, c in lys15:
            path = np.linspace(o, c, 15)
            for i, p in enumerate(path):
                rows.append((p, h if i == 5 else p, l if i == 10 else p, p))
        return rows

    df_1m = _1m(_sti([BASIS_D, UDBRUD_D, OVER, GENNEM] + [OVER] * 200),
               start_ct=f"{DAG} 09:00")
    bars15 = resample.aggregate(df_1m, 15)
    ekte = t.k1.find_zoner_v2(bars15, t.k1.BUFFER_V2)
    ud = t.n1_gentagelse(df_1m, bars15, ekte["side"].to_numpy(), ekte["basis_i"].to_numpy(),
                         (ekte["zone_high"] - ekte["zone_low"]).to_numpy(dtype=float), seed=7)
    assert len(ud) == 6
    for navn, row in ud.items():
        assert row["handler_n"] >= 0
