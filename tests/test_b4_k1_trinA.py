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

import math
from fractions import Fraction
from pathlib import Path

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


def _flad(h, l, c, entry_i=0, demand=True, be_r=None, cutoff_i=1000, ret_fyldningsbar=True):
    h, l, c = np.asarray(h, float), np.asarray(l, float), np.asarray(c, float)
    return t.simuler_handel(h, l, c, entry_i, ENTRY, demand, RISIKO, be_r, cutoff_i, len(h),
                            ret_fyldningsbar)


class TestSimulerHandelMaalOgStop:
    def test_maal_ramt_efter_fyldningsbaren_giver_plus_2R_brutto_uden_slippage(self):
        udfald, r, i, holder = _flad(h=[105, 121], l=[98, 99], c=[102, 120])
        assert (udfald, r, i, holder) == (t.MAAL, pytest.approx(2.0), 1, True)

    def test_stop_ramt_i_fyldningsbaren_traekker_slippage_fra(self):
        """Motorrettelse 1: stoppet MÅ ramme i selve fyldningsbaren."""
        udfald, r, i, holder = _flad(h=[105], l=[89], c=[90])
        forventet = ((90 - t.SLIP_PT) - ENTRY) / RISIKO
        assert (udfald, i, holder) == (t.STOP, 0, False)
        assert r == pytest.approx(forventet)
        assert r < -1.0        # slippage gør tabet værre end -1R

    def test_regel_4_begge_ramt_samme_bar_stoppet_vinder(self):
        # bar0: fyldningsbaren, neutral. bar1: både stop og mål er ramt.
        udfald, r, i, holder = _flad(h=[105, 125], l=[95, 85], c=[102, 100])
        assert (udfald, i) == (t.STOP, 1)
        assert r == pytest.approx(((90 - t.SLIP_PT) - ENTRY) / RISIKO)

    def test_supply_er_spejlvendt(self):
        udfald, r, i, holder = _flad(h=[105, 110], l=[95, 79], c=[102, 100], demand=False)
        # mål 80 og stop 110 begge ramt i bar1: stoppet vinder (regel 4)
        assert udfald == t.STOP
        assert r == pytest.approx((ENTRY - (110 + t.SLIP_PT)) / RISIKO)

    def test_supply_maal_alene_efter_fyldningsbaren(self):
        udfald, r, i, holder = _flad(h=[105, 102], l=[95, 79], c=[102, 80], demand=False)
        assert (udfald, r, holder) == (t.MAAL, pytest.approx(2.0), True)

    def test_motorrettelse_1_maal_i_fyldningsbaren_taeller_ikke(self):
        """h=121 rammer målet (120) i selve fyldningsbaren — den rettede motor
        (standard) ignorerer det, og handlen løber videre (her: ud i tidsexit)."""
        udfald, r, i, holder = _flad(h=[121], l=[99], c=[120])
        assert udfald != t.MAAL
        assert udfald in (t.TIDSEXIT, t.CENSURERET)

    def test_ret_fyldningsbar_false_er_den_gamle_uden_rettelsen(self):
        """Kun til før/efter-målingen: viser den gamle, ukorrigerede opførsel."""
        udfald, r, i, holder = _flad(h=[121], l=[99], c=[120], ret_fyldningsbar=False)
        assert (udfald, i, holder) == (t.MAAL, 0, True)

    def test_motorrettelse_1_be_trigger_i_fyldningsbaren_armerer_ikke(self):
        """BE-triggeren krydses i fyldningsbaren (h=112 >= 1,0R-trigger 110) — den
        rettede motor ignorerer det, så stoppet i bar 1 er stadig det oprindelige."""
        udfald, r, i, holder = _flad(h=[112, 101], l=[95, 89], c=[105, 90], be_r=1.0)
        assert udfald == t.STOP           # IKKE BE_UDFALD


class TestSimulerHandelBE:
    def test_be_armering_flytter_stoppet_til_E_uden_at_lukke_samme_bar(self):
        """Baren der krydser triggeren rammer ikke den (endnu ikke armerede) BE-stop."""
        # bar0: fyldningsbaren, neutral. be_trigger ved 1,0R = 110.
        # bar1 krydser den (h=112) med l=95: intet ramt endnu.
        udfald, r, i, holder = _flad(h=[105, 112, 101], l=[95, 95, 89],
                                     c=[102, 105, 90], be_r=1.0)
        # bar2: stop nu E=100. low=89 <= 100 → BE-udgang.
        assert udfald == t.BE_UDFALD
        assert r == pytest.approx((ENTRY - t.SLIP_PT - ENTRY) / RISIKO)
        assert r < 0 and r > -0.1          # "BE er ikke nul", men langt fra -1R
        assert holder is True              # BE-triggeren (>= 1,0R) indebærer +1R nået

    def test_be_armeret_men_fortsaetter_til_maal(self):
        udfald, r, i, holder = _flad(h=[105, 112, 125], l=[95, 95, 105],
                                     c=[102, 105, 122], be_r=1.0)
        assert (udfald, r, holder) == (t.MAAL, pytest.approx(2.0), True)

    def test_ingen_be_variant_bruger_aldrig_be_selvom_triggeren_krydses(self):
        """be_r=None: samme priser som armeringstesten, men her lukker det som stop."""
        udfald, r, i, holder = _flad(h=[105, 112, 101], l=[95, 95, 89],
                                     c=[102, 105, 90], be_r=None)
        assert udfald == t.STOP           # ikke BE — variant "ingen" kender ikke BE
        assert r == pytest.approx(((90 - t.SLIP_PT) - ENTRY) / RISIKO)

    def test_be_1_2R_trigger_er_stoerre_end_1_0R(self):
        # h=111 krydser 1,0R (110) men ikke 1,2R (112)
        udfald, r, i, holder = _flad(h=[105, 111, 101], l=[95, 95, 89],
                                     c=[102, 105, 90], be_r=1.2)
        assert udfald == t.STOP           # ikke armeret, så det er det oprindelige stop


class TestHolderPct:
    """Motorrettelse 3: +1R nået før stoppet, fyldningsbaren undtaget."""

    def test_stop_uden_at_naa_1R_er_ikke_holder(self):
        _, _, _, holder = _flad(h=[105, 105], l=[95, 89], c=[102, 90])
        assert holder is False

    def test_1R_naaet_foer_stoppet_er_holder(self):
        # bar1 når +1R (110) uden at ramme noget; bar2 rammer stoppet.
        _, _, _, holder = _flad(h=[105, 111, 105], l=[95, 100, 89], c=[102, 108, 90])
        assert holder is True

    def test_1R_og_stoppet_i_samme_bar_er_ikke_holder(self):
        """Samme worst case som regel 4: nås begge i samme 1m-bar, tæller det ikke
        som holder — stoppet antages ramt først."""
        _, _, _, holder = _flad(h=[105, 111], l=[95, 85], c=[102, 90])
        assert holder is False

    def test_maal_er_altid_holder(self):
        _, _, _, holder = _flad(h=[105, 121], l=[95, 99], c=[102, 120])
        assert holder is True

    def test_tidsexit_er_holder_hvis_1R_blev_naaet_foer_cutoff(self):
        h = [105, 111, 105, 105]
        l = [95, 100, 95, 95]
        c = [101, 108, 103, 103]
        udfald, r, i, holder = _flad(h, l, c, cutoff_i=3)
        assert udfald == t.TIDSEXIT and holder is True

    def test_tidsexit_er_ikke_holder_hvis_1R_aldrig_blev_naaet(self):
        h = [105, 105, 105, 105]
        l = [95, 95, 95, 95]
        c = [101, 102, 103, 103]
        udfald, r, i, holder = _flad(h, l, c, cutoff_i=3)
        assert udfald == t.TIDSEXIT and holder is False

    def test_1R_i_fyldningsbaren_taeller_ikke(self):
        """Fyldningsbaren er undtaget, jf. motorrettelse 1 og 3 — selv med h langt over
        1R-niveauet i bar 0."""
        udfald, r, i, holder = _flad(h=[130], l=[99], c=[105], cutoff_i=1)
        assert holder is False


class TestSimulerHandelTidOgCensurering:
    def test_tidsexit_lukker_til_sidste_lukkekurs_foer_cutoff(self):
        h = [105, 105, 105, 105]
        l = [95, 95, 95, 95]
        c = [101, 102, 103, 104]
        udfald, r, i, holder = _flad(h, l, c, cutoff_i=3)
        assert (udfald, i, holder) == (t.TIDSEXIT, 2, False)
        assert r == pytest.approx((103 - ENTRY) / RISIKO)

    def test_censurering_naar_data_slutter_foer_cutoff(self):
        h = [105, 105, 105]
        l = [95, 95, 95]
        c = [101, 102, 103]
        udfald, r, i, holder = _flad(h, l, c, cutoff_i=1000)   # cutoff langt ude
        assert (udfald, i) == (t.CENSURERET, 2)
        assert r == pytest.approx((103 - ENTRY) / RISIKO)

    def test_cutoff_ved_selve_fyldningsbaren_giver_stadig_et_udfald(self):
        udfald, r, i, holder = _flad(h=[105], l=[95], c=[101], entry_i=0, cutoff_i=0)
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

    def test_kontrakter_loftes_ved_50_men_raa_beholdes(self):
        """§4d, tilføjet 2026-09-23: Topsteps 50-mikro positionsloft. Loftet bider ved
        risiko_pt < 2,5 point — en meget lille, billig 2019-zone; en normal 2023-zone
        (21 point) skal ikke røres."""
        billig = t.sizing_ekte(_zoner_stub(k1.DEMAND, E=8_002.0, zone_low=8_000.0,
                                           zone_high=8_001.0))    # risiko 2 pt -> raa 62
        assert billig["kontrakter_ekte_raa"].iloc[0] > 50
        assert billig["kontrakter_ekte"].iloc[0] == 50.0
        dyr = t.sizing_ekte(_zoner_stub(k1.DEMAND, E=17_021.0, zone_low=17_000.0,
                                        zone_high=17_015.0))      # risiko 21 pt -> raa < 10
        assert dyr["kontrakter_ekte_raa"].iloc[0] < 50
        assert dyr["kontrakter_ekte"].iloc[0] == dyr["kontrakter_ekte_raa"].iloc[0]

    def test_loftet_aendrer_intet_R_tal(self):
        """R er kontraktuafhængigt — loftet må kun ændre kontrakter/omk_R_netto er
        allerede kontraktuafhængig og upåvirket, sizing_ekte rører den slet ikke."""
        z = t.sizing_ekte(_zoner_stub(k1.DEMAND, E=8_009.0, zone_low=8_000.0,
                                      zone_high=8_005.0))
        assert z["risiko_pt_ekte"].iloc[0] == pytest.approx(9.0)
        assert z["omk_R_netto_ekte"].iloc[0] == pytest.approx(2.627 / (2 * 9.0))


class TestSizingTabel:
    def _pop(self) -> pd.DataFrame:
        # 2019: dyr risiko relativt (lav pris), én zone afvist af dollarloftet, én loftet
        # ved 50. 2023: billigere risiko relativt (høj pris), ingen afvist eller loftet.
        return pd.DataFrame([
            {"i_vindue": True, "dag": pd.Timestamp("2019-06-01"),
             "risiko_pt_ekte": 9.0, "kontrakter_ekte": 13.0, "kontrakter_ekte_raa": 13.0,
             "omk_R_netto_ekte": 0.1500},
            {"i_vindue": True, "dag": pd.Timestamp("2019-07-01"),
             "risiko_pt_ekte": 130.0, "kontrakter_ekte": 0.0, "kontrakter_ekte_raa": 0.0,
             "omk_R_netto_ekte": 0.0800},
            {"i_vindue": True, "dag": pd.Timestamp("2019-08-01"),
             "risiko_pt_ekte": 2.0, "kontrakter_ekte": 50.0, "kontrakter_ekte_raa": 62.0,
             "omk_R_netto_ekte": 0.6568},
            {"i_vindue": True, "dag": pd.Timestamp("2023-06-01"),
             "risiko_pt_ekte": 21.0, "kontrakter_ekte": 5.0, "kontrakter_ekte_raa": 5.0,
             "omk_R_netto_ekte": 0.0625},
            {"i_vindue": False, "dag": pd.Timestamp("2023-06-02"),        # ikke i populationen
             "risiko_pt_ekte": 5.0, "kontrakter_ekte": 20.0, "kontrakter_ekte_raa": 20.0,
             "omk_R_netto_ekte": 0.26},
        ])

    def test_population_er_i_vindue_foer_dollarloftet(self):
        tab = t.sizing_tabel(self._pop())
        alle = tab[tab["periode"] == "alle"].iloc[0]
        assert alle["zoner_i_vindue_n"] == 4            # ikke de 5 — den femte er ikke i_vindue
        assert alle["afvist_kontrakter_nul_n"] == 1

    def test_pr_aar_og_konsekvensen_maales_ikke_antages(self):
        tab = t.sizing_tabel(self._pop())
        y19 = tab[tab["periode"] == "2019"].iloc[0]
        y23 = tab[tab["periode"] == "2023"].iloc[0]
        assert (y19["zoner_i_vindue_n"], y23["zoner_i_vindue_n"]) == (3, 1)
        assert y19["afvist_kontrakter_nul_n"] == 1 and y23["afvist_kontrakter_nul_n"] == 0
        # 2019's median omkostning i R er tungere end 2023's — §4d's pointe.
        assert y19["omk_R_netto_p50"] > y23["omk_R_netto_p50"]
        assert y19["kontrakter_maks"] == 50.0 and y23["kontrakter_maks"] == 5.0
        assert y19["be_WR_pct_netto_p50"] > y23["be_WR_pct_netto_p50"]

    def test_kontrakter_loftet_n_og_den_tynde_hale(self):
        """§4d, tilføjet 2026-09-23: positionsloftet på 50 og hvor det bider."""
        tab = t.sizing_tabel(self._pop())
        y19 = tab[tab["periode"] == "2019"].iloc[0]
        y23 = tab[tab["periode"] == "2023"].iloc[0]
        assert y19["kontrakter_loftet_n"] == 1 and y23["kontrakter_loftet_n"] == 0
        assert y19["handler_be_WR_over_50_pct_n"] == 1
        assert y23["handler_be_WR_over_50_pct_n"] == 0
        assert y19["omk_R_netto_p90"] > 0.5

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
        # pr. side og pr. år skal summere til totalen, §8's nedbrydning
        demand = t.noegletal_handler(res, side=t.DEMAND)
        supply = t.noegletal_handler(res, side=t.SUPPLY)
        assert demand["handler_n"] + supply["handler_n"] == row["handler_n"]
        aar2023 = t.noegletal_handler(res, aar=2023)
        assert aar2023["handler_n"] == row["handler_n"]        # al data er i 2023 her
        assert t.noegletal_handler(res, aar=1999)["handler_n"] == 0
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


def test_zone_diagnostik_taeller_status():
    z = pd.DataFrame({"status": ["beroert", "beroert", "ugyldig", "aktiv", "kontraktskift"]})
    d = t.zone_diagnostik(z)
    assert d == {"zoner_n": 5, "beroeringer_n": 2, "ugyldig_foer_aktiv_pct": pytest.approx(20.0)}


def test_zone_diagnostik_tom_zoneliste():
    z = pd.DataFrame({"status": pd.Series(dtype=object)})
    d = t.zone_diagnostik(z)
    assert d["zoner_n"] == 0 and math.isnan(d["ugyldig_foer_aktiv_pct"])


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
        assert row["zoner_n"] == len(ekte)     # N1 bevarer antallet af (forsøgte) zoner


# ===========================================================================
# 6. N2 (FORELØBIG) — E forskydes, §5
# ===========================================================================

class TestFindZonerN2:
    def _ekte_raekke(self, side, E, zone_low, zone_high, basis_i=3, udbrud_i=4):
        return pd.DataFrame([{
            "side": side, "basis_i": basis_i, "udbrud_i": udbrud_i, "E": E,
            "zone_low": zone_low, "zone_high": zone_high, "basis_close": zone_high,
            "hoejde_pct": 1.0, "over_hul": False,
        }])

    def test_dannelseslys_og_tid_bevares_hele_zonen_flyttes(self):
        """Motorrettelse 2: zone_high og zone_low flytter med E, samme forskydning,
        så H og stopafstanden (E - zone_low for demand) bevares."""
        bars = _bars15(10, start_ct="2023-06-05 09:00")
        ekte = self._ekte_raekke(t.DEMAND, E=10_017.0, zone_low=9_995.0, zone_high=10_015.0)
        rng = np.random.default_rng(0)
        z = t.find_zoner_n2(bars, ekte, rng)
        r = z.iloc[0]
        assert (r["basis_i"], r["udbrud_i"]) == (3, 4)
        forskydning = r["E"] - 10_017.0
        assert forskydning != 0.0
        assert r["zone_high"] == pytest.approx(10_015.0 + forskydning)
        assert r["zone_low"] == pytest.approx(9_995.0 + forskydning)
        assert (r["zone_high"] - r["zone_low"]) == pytest.approx(10_015.0 - 9_995.0)   # H bevares
        assert (r["E"] - r["zone_low"]) == pytest.approx(10_017.0 - 9_995.0)  # stopafstand bevares

    def test_stopafstanden_kan_ikke_blive_negativ(self):
        """Før rettelsen kunne et stort negativt skub gøre E - zone_low <= 0. Med hele
        zonen flyttet er stopafstanden altid den oprindelige, uanset forskydning."""
        bars = _bars15(10, start_ct="2023-06-05 09:00")
        ekte = self._ekte_raekke(t.DEMAND, E=10_017.0, zone_low=9_995.0, zone_high=10_015.0)
        for seed in range(50):
            z = t.find_zoner_n2(bars, ekte, np.random.default_rng(seed))
            r = z.iloc[0]
            assert (r["E"] - r["zone_low"]) == pytest.approx(22.0)

    def test_supply_hele_zonen_flyttes(self):
        bars = _bars15(10, start_ct="2023-06-05 09:00")
        ekte = self._ekte_raekke(t.SUPPLY, E=9_983.0, zone_low=9_985.0, zone_high=10_005.0)
        rng = np.random.default_rng(2)
        z = t.find_zoner_n2(bars, ekte, rng)
        r = z.iloc[0]
        forskydning = r["E"] - 9_983.0
        assert r["zone_low"] == pytest.approx(9_985.0 + forskydning)
        assert r["zone_high"] == pytest.approx(10_005.0 + forskydning)
        assert (r["zone_low"] - r["E"]) == pytest.approx(9_985.0 - 9_983.0)  # stopafstand bevares

    def test_forskydningen_er_mellem_0_5H_og_3H_i_begge_retninger(self):
        bars = _bars15(10, start_ct="2023-06-05 09:00")
        H = 20.0
        ekte = self._ekte_raekke(t.DEMAND, E=10_017.0, zone_low=9_995.0, zone_high=10_015.0)
        rng = np.random.default_rng(1)
        forskydninger = []
        for _ in range(200):
            z = t.find_zoner_n2(bars, ekte, rng)
            forskydninger.append(z.iloc[0]["E"] - 10_017.0)
        afstande = np.abs(forskydninger)
        assert (afstande >= 0.5 * H - 1e-9).all() and (afstande <= 3.0 * H + 1e-9).all()
        assert (np.array(forskydninger) > 0).any() and (np.array(forskydninger) < 0).any()

    def test_klassificer_v2_genbruges_uaendret_paa_n2_zoner(self):
        """Smoke-test: uanset den trukne forskydning skal kerne v2's egen mekanik
        (klassificer_v2, urørt) kunne klassificere N2's zoner uden fejl."""
        bars = _bars15(20, start_ct="2023-06-14 09:00")
        b = 3
        bars.loc[bars.index[b], ["open", "high", "low", "close"]] = \
            [10_000.0, 10_020.0, 9_995.0, 10_000.0]
        bars.loc[bars.index[b + 1], ["open", "high", "low", "close"]] = \
            [10_022.0, 10_040.0, 10_022.0, 10_022.0]
        bars.loc[bars.index[b + 2], ["open", "high", "low", "close"]] = \
            [10_015.0, 10_020.0, 9_990.0, 9_995.0]
        ekte = self._ekte_raekke(t.DEMAND, E=10_021.0, zone_low=9_995.0, zone_high=10_020.0,
                                 basis_i=b, udbrud_i=b + 1)
        for seed in range(10):
            z = t.find_zoner_n2(bars, ekte, np.random.default_rng(seed))
            klass = t.k1.klassificer_v2(bars, z, Fraction(0))
            assert klass.iloc[0]["status"] in ("beroert", "ugyldig", "aktiv",
                                               "aldrig_aktiv", "kontraktskift")


def test_n2_gentagelse_koerer_og_har_samme_form_som_n1():
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
    ekte_pr_buffer = {navn: t.k1.find_zoner_v2(bars15, buffer)
                      for navn, buffer in t.BUFFER_VARIANTER.items()}
    ud = t.n2_gentagelse(df_1m, bars15, ekte_pr_buffer, seed=7)
    assert len(ud) == 6
    for navn, row in ud.items():
        assert row["handler_n"] >= 0


# ===========================================================================
# 7. Rapportlaget — Westfall-Young, krydstjek, beslutningsregel, rapport (§6-§8)
# ===========================================================================

def _fake_row(R: float, handler_n: int = 100, zoner_n: int = 200, beroeringer_n: int = 150,
             ugyldig_pct: float = 28.7) -> dict:
    return {"middel_R_netto": R, "middel_R_netto_ci95_lo": R - 0.05,
            "middel_R_netto_ci95_hi": R + 0.05, "handler_n": handler_n,
            "zoner_n": zoner_n, "beroeringer_n": beroeringer_n,
            "ugyldig_foer_aktiv_pct": ugyldig_pct}


VARIANTER_FAKE = [(b, be) for b in ("buffer_10", "buffer_0")
                 for be in ("ingen", "BE_1_0R", "BE_1_2R")]


class TestWestfallYoung:
    def test_finder_bedste_variant_og_p_fwe_matcher_formlen(self):
        virkelig = {v: _fake_row(0.05 * i) for i, v in enumerate(VARIANTER_FAKE)}
        bedste_v = VARIANTER_FAKE[-1]                  # højeste R = 0,25
        rng = np.random.default_rng(0)
        n1_liste = [{v: _fake_row(rng.normal(0, 0.1)) for v in VARIANTER_FAKE}
                   for _ in range(50)]
        wy = t.westfall_young(virkelig, n1_liste)
        assert wy["bedste_variant"] == bedste_v
        assert wy["observeret_bedste_middel_R_netto"] == pytest.approx(0.25)
        maks = np.array([max(rep[v]["middel_R_netto"] for v in VARIANTER_FAKE)
                         for rep in n1_liste])
        forventet_p = (1 + int((maks >= 0.25).sum())) / (1 + 50)
        assert wy["p_fwe"] == pytest.approx(forventet_p)
        assert wy["R"] == 50

    def test_p_fwe_er_naer_1_naar_ingen_edge(self):
        """Kernen er ikke bedre end N1's støj: p_FWE skal være stor, ikke lille."""
        rng = np.random.default_rng(1)
        virkelig = {v: _fake_row(rng.normal(0, 0.1)) for v in VARIANTER_FAKE}
        n1_liste = [{v: _fake_row(rng.normal(0, 0.1)) for v in VARIANTER_FAKE}
                   for _ in range(200)]
        wy = t.westfall_young(virkelig, n1_liste)
        assert wy["p_fwe"] > 0.05


class TestBeslutningTrinA:
    def _wy(self, bedste_R, n1_vaerdier):
        varianter = VARIANTER_FAKE
        virkelig = {v: _fake_row(0.0) for v in varianter}
        virkelig[varianter[0]] = _fake_row(bedste_R)
        n1_pr_variant = {v: np.array(n1_vaerdier if v == varianter[0] else [0.0] * len(n1_vaerdier))
                        for v in varianter}
        wy = {"varianter": varianter, "bedste_variant": varianter[0],
             "observeret_bedste_middel_R_netto": bedste_R, "n1_pr_variant": n1_pr_variant}
        return virkelig, wy

    def test_brugbar_edge(self):
        virkelig, wy = self._wy(0.25, list(np.random.default_rng(0).normal(0, 0.05, 500)))
        wy["p_fwe"] = 0.01
        b = t.beslutning_trin_a(wy, virkelig)
        assert b["kategori_punktestimat"] == "brugbar_edge"

    def test_parkeres_under_n1s_5_pct_fraktil(self):
        n1 = list(np.linspace(-0.5, 0.5, 500))          # 5%-fraktil ≈ -0,45
        virkelig, wy = self._wy(-0.9, n1)
        wy["p_fwe"] = 0.9
        b = t.beslutning_trin_a(wy, virkelig)
        assert b["kategori_punktestimat"] == "parkeres"

    def test_neutral_naar_p_fwe_over_005_og_over_n1_median(self):
        n1 = list(np.linspace(-0.2, 0.2, 500))           # median ≈ 0
        virkelig, wy = self._wy(0.05, n1)
        wy["p_fwe"] = 0.5
        b = t.beslutning_trin_a(wy, virkelig)
        assert b["kategori_punktestimat"] == "neutral"

    def test_uafgjort_naar_ci_krydser_en_graense(self):
        """N1's median er 0: R = 0,03 er 'neutral' (>= median), men R − 0,05 = −0,02 er
        under medianen (0) — CI'et krydser grænsen, og den laveste kategori skal gælde."""
        n1 = list(np.linspace(-0.2, 0.2, 500))            # median ≈ 0
        virkelig, wy = self._wy(0.03, n1)                 # CI [-0,02; 0,08]
        wy["p_fwe"] = 0.5
        b = t.beslutning_trin_a(wy, virkelig)
        assert b["uafgjort"] is True
        assert b["kategori"] == "graenseomraade"          # laveste af neutral/graenseomraade

    def test_afgjort_naar_ci_ikke_krydser_en_graense(self):
        n1 = list(np.linspace(-0.2, 0.2, 500))
        virkelig, wy = self._wy(0.15, n1)                 # CI [0,10; 0,20], langt fra grænserne
        wy["p_fwe"] = 0.5
        b = t.beslutning_trin_a(wy, virkelig)
        assert b["uafgjort"] is False
        assert b["kategori"] == b["kategori_punktestimat"] == "neutral"

    def test_kategori_raekkefoelge_er_konsistent(self):
        assert t._KATEGORI_RAEKKEFOELGE[0] == "parkeres"
        assert t._KATEGORI_RAEKKEFOELGE[-1] == "brugbar_edge"


class TestKrydstjekNQ:
    def test_taeller_begge_veje_separat(self):
        z = pd.DataFrame({
            "signal": [True, True, False, False],
            "i_vindue": [True, True, True, False],
            "kontrakter_ekte": [2.0, 0.0, 3.0, 5.0],
            "dag": pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-02", "2020-01-03"]),
        })
        kryds = t.krydstjek_nq(z)
        assert (kryds["dage_med_signal_procentregel_n"], kryds["signaler_procentregel_n"]) == (2, 2)
        # dollarloft: i_vindue & kontrakter>=1 -> rækker 0 og 2 (række 1 har 0 kontrakter)
        assert (kryds["dage_med_signal_dollarloft_n"], kryds["signaler_dollarloft_n"]) == (2, 2)
        assert kryds["nq_dage_med_signal_n"] == t.NQ_REFERENCE_DAGE_MED_SIGNAL_N


def _byg_lille_koersel(seed_n1=(11, 12), seed_n2=(21,)):
    """Et lille, ægte gennemløb (samme opskrift som andre smoke-tests) plus et par
    rigtige N1/N2-gentagelser — nok til at teste hele rapportlaget uden en time lang
    kørsel. Ikke en statistisk meningsfuld test af selve edge-spørgsmålet."""
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

    df_1m = _1m(_sti([BASIS_D, UDBRUD_D, OVER, GENNEM] + [OVER] * 300),
               start_ct=f"{DAG} 09:00")
    bars15 = resample.aggregate(df_1m, 15)

    virkelig = t.simuler_alle_varianter(df_1m, bars15)
    virkelig_noegletal = {v: t.noegletal_handler(res) for v, res in virkelig.items()}

    ekte_v2 = t.k1.find_zoner_v2(bars15, t.k1.BUFFER_V2)
    ekte_side = ekte_v2["side"].to_numpy()
    ekte_basis_i = ekte_v2["basis_i"].to_numpy()
    ekte_H = (ekte_v2["zone_high"] - ekte_v2["zone_low"]).to_numpy(dtype=float)
    n1_liste = [t.n1_gentagelse(df_1m, bars15, ekte_side, ekte_basis_i, ekte_H, s)
               for s in seed_n1]

    ekte_pr_buffer = {navn: t.k1.find_zoner_v2(bars15, buffer)
                      for navn, buffer in t.BUFFER_VARIANTER.items()}
    n2_liste = [t.n2_gentagelse(df_1m, bars15, ekte_pr_buffer, s) for s in seed_n2]

    return virkelig, virkelig_noegletal, n1_liste, n2_liste


def test_fuld_rapportlag_koerer_uden_fejl_paa_et_lille_ægte_gennemloeb():
    virkelig, virkelig_noegletal, n1_liste, n2_liste = _byg_lille_koersel()

    wy = t.westfall_young(virkelig_noegletal, n1_liste)
    assert set(wy["varianter"]) == set(VARIANTER_FAKE)
    assert wy["bedste_variant"] in wy["varianter"]

    samm, forbehold = t.n1_kerne_sammenligning(virkelig_noegletal, n1_liste, wy)
    assert len(samm) == 6
    assert isinstance(forbehold, list)

    kryds = t.krydstjek_nq(virkelig[("buffer_10", "ingen")]["zoner"])
    assert kryds["dage_med_signal_dollarloft_n"] >= kryds["dage_med_signal_procentregel_n"] - 5

    b = t.beslutning_trin_a(wy, virkelig_noegletal)
    assert b["kategori"] in t._KATEGORI_RAEKKEFOELGE

    tabel = t.fuld_tabel(virkelig, wy, n2_liste)
    assert set(tabel["side"]) == {"alle", "demand", "supply"}
    assert set(tabel["buffer"]) == {"buffer_10", "buffer_0"}
    assert len(tabel) == 6 * 3 * (1 + len(t.AAR_LISTE))     # alle+hvert år, pr. side, pr. variant

    md = t.skriv_trin_a_md(
        {"kryds": kryds, "beslutning": b, "sammenligning": samm, "forbehold": forbehold,
         "tabel": tabel, "n1_reps": len(n1_liste), "n2_reps": len(n2_liste)},
        {"koert_utc": "x", "head": "f" * 40,
         "commits": {t._rel(t.PREREG): "f" * 40, t._rel(Path(t.__file__)): "f" * 40},
         "n_1m": 1000, "n_15m": 100})
    assert "# B4 kandidat 1" in md
    assert wy["bedste_variant"][0] in md


def test_motorrettelse_maaling_og_rapport_koerer_uden_fejl():
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

    foer = t.simuler_alle_varianter(df_1m, bars15, ret_fyldningsbar=False)
    efter = t.simuler_alle_varianter(df_1m, bars15, ret_fyldningsbar=True)
    rows = []
    for v in efter:
        h_foer, h_efter = foer[v]["handler"], efter[v]["handler"]
        nf, ne = t.noegletal_handler(foer[v]), t.noegletal_handler(efter[v])
        rows.append({
            "buffer": v[0], "BE": v[1],
            "handler_n_foer": len(h_foer), "handler_n_efter": len(h_efter),
            "handler_kun_i_foer_n": 0, "handler_kun_i_efter_n": 0,
            "middel_R_netto_foer": nf["middel_R_netto"],
            "middel_R_netto_efter": ne["middel_R_netto"],
            "forskel": ne["middel_R_netto"] - nf["middel_R_netto"],
            "handler_ramt_af_rettelse_1_n": 0,
            "holder_pct": ne["holder_pct"], "holder_ci95_lo_pct": ne["holder_ci95_lo_pct"],
            "holder_ci95_hi_pct": ne["holder_ci95_hi_pct"],
        })
    maaling = {"tabel": pd.DataFrame(rows), "foer": foer, "efter": efter,
              "n_1m": len(df_1m), "n_15m": len(bars15)}
    md = t.skriv_motorrettelse_md(
        maaling, {"koert_utc": "x", "head": "f" * 40,
                 "commits": {t._rel(t.PREREG_MOTOR): "f" * 40,
                            t._rel(Path(t.__file__)): "f" * 40},
                 "n_1m": len(df_1m), "n_15m": len(bars15)})
    assert "# B4 kandidat 1 — motorrettelse" in md
    assert "handler_ramt_af_rettelse_1_n" in md
