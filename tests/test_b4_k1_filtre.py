"""Tests for research/b4_k1_filtre.py — de syv filtre til B4 kandidat 1, trin 2.

Præregistreringen er ``research/prereg/b4_k1_trin2_optaelling.md``. Fem lag testes:

1. **Swing-punkter, §3a.** Strengt højere end de 5 lys før, mindst lige så højt som de 5
   efter, kendt først når det femte lys efter er lukket.
2. **Hvert af de syv kriterier, §3b**, låst med syntetiske lys: én serie hvor kriteriet er
   sandt, og de mindste ændringer der gør det falsk. De fire præciseringer fra
   2026-09-23 har hver sin test.
3. **Intet filter kigger frem.** 1m-serien skæres af ved lukningen af lyset før
   berøringen, begge timeframes bygges forfra af den afskårne serie, og de syv værdier
   skal være uændrede. Det er den vigtigste test i modulet, og den er kun noget værd hvis
   filtrene faktisk varierer og faktisk afhænger af skæringen — begge dele hævdes.
4. **Signalet** er trin A-motorens kandidatregel, ikke k1's procentregel.
5. **Optællingen og rapporten:** scorefordeling, kumulativ, phi, omkostninger, markdown og
   hele ``main`` med datavejen og git skiftet ud.
"""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from data import resample
from research import b4_k1_filtre as f
from research import b4_k1_optaelling as k1
from research import b4_k1_trinA as trinA

CT = "America/Chicago"
START_UTC = "2023-06-14 14:00"      # 09:00 CT, midt i indgangsvinduet og på alle bar-grænser


# ===========================================================================
# Byggeklodser
# ===========================================================================

def _bars(rows, tf: int = 15, start: str = START_UTC, iid: int = 1) -> pd.DataFrame:
    """Sammenhængende lys på ``tf`` minutter af (open, high, low, close)."""
    a = np.asarray(rows, dtype=float)
    idx = pd.date_range(pd.Timestamp(start, tz="UTC"), periods=len(a), freq=f"{tf}min")
    return pd.DataFrame({"open": a[:, 0], "high": a[:, 1], "low": a[:, 2], "close": a[:, 3],
                         "volume": 1.0, "instrument_id": np.int64(iid)},
                        index=idx.rename("time"))


FLAD = (155.0, 160.0, 150.0, 155.0)      # doji: hverken rødt eller grønt, danner ingen zone


def _flad_serie(n: int, aendringer: dict | None = None, tf: int = 15,
                start: str = START_UTC) -> pd.DataFrame:
    rows = [FLAD] * n
    for i, lys in (aendringer or {}).items():
        rows[i] = lys
    return _bars(rows, tf, start)


def _zone(side: str, basis_i: int, udbrud_i: int, slut_i: int, zone_high: float,
          zone_low: float, buffer: float = 0.1) -> pd.DataFrame:
    """Én zonerække med præcis de kolonner ``beregn_filtre`` læser."""
    H = zone_high - zone_low
    E = zone_high + buffer * H if side == f.DEMAND else zone_low - buffer * H
    return pd.DataFrame([{"side": side, "basis_i": basis_i, "udbrud_i": udbrud_i,
                          "slut_i": slut_i, "zone_high": zone_high, "zone_low": zone_low,
                          "E": E}])


def _f(zone: pd.DataFrame, bars: pd.DataFrame, htf: pd.DataFrame | None = None,
       tf: int = 15, htf_min: int = 15) -> pd.Series:
    """De syv værdier for én zone. Uden ``htf`` bruges handelsserien selv."""
    return f.beregn_filtre(zone, bars, bars if htf is None else htf, tf, htf_min).iloc[0]


# ===========================================================================
# 1. Swing-punkter, §3a
# ===========================================================================

class TestSwingPunkter:
    def test_toppen_er_swing_high_naar_de_fem_foer_er_lavere_og_de_fem_efter_ikke_hoejere(self):
        h = np.array([1, 2, 3, 4, 5, 10, 5, 4, 3, 2, 1], dtype=float)
        sh, sl = f.swing_punkter(h, h - 1)
        assert list(np.flatnonzero(sh)) == [5]

    def test_foer_er_streng_lighed_med_et_af_de_fem_foer_er_ikke_et_swing_high(self):
        h = np.array([1, 2, 3, 4, 10, 10, 5, 4, 3, 2, 1], dtype=float)
        sh, _ = f.swing_punkter(h, h - 1)
        assert not sh.any()

    def test_efter_er_ikke_streng_lighed_med_et_af_de_fem_efter_er_stadig_swing_high(self):
        h = np.array([1, 2, 3, 4, 5, 10, 10, 4, 3, 2, 1], dtype=float)
        sh, _ = f.swing_punkter(h, h - 1)
        assert list(np.flatnonzero(sh)) == [5]

    def test_swing_low_er_spejlvendt(self):
        l = np.array([9, 8, 7, 6, 5, 1, 5, 6, 7, 8, 9], dtype=float)
        _, sl = f.swing_punkter(l + 1, l)
        assert list(np.flatnonzero(sl)) == [5]
        l_lig_efter = np.array([9, 8, 7, 6, 5, 1, 1, 6, 7, 8, 9], dtype=float)
        _, sl2 = f.swing_punkter(l_lig_efter + 1, l_lig_efter)
        assert list(np.flatnonzero(sl2)) == [5]

    def test_de_fem_foerste_og_sidste_lys_kan_aldrig_vaere_swing_punkter(self):
        h = np.arange(20, dtype=float)[::-1]          # strengt faldende: kun kant-kandidater
        sh, _ = f.swing_punkter(h, h - 1)
        assert not sh[:5].any() and not sh[-5:].any()

    def test_for_kort_serie_giver_ingen_swing_punkter(self):
        sh, sl = f.swing_punkter(np.arange(10.0), np.arange(10.0))
        assert not sh.any() and not sl.any()

    def test_punktet_er_kendt_foerst_naar_de_fem_lys_efter_er_lukket(self):
        h = np.array([1, 2, 3, 4, 5, 10, 5, 4, 3, 2, 1], dtype=float)
        sh, _ = f.swing_punkter(h, h - 1)
        conf, idx = f._kendt(sh)
        assert (list(idx), list(conf)) == ([5], [10])
        seneste = f._seneste_niveau(h, sh)
        assert np.isnan(seneste[9]) and seneste[10] == 10.0


# ===========================================================================
# 2. De syv kriterier, §3b
# ===========================================================================

# Kriterium 1: swing high ved lys 5 (niveau 200), kendt ved lys 10. Zonen er 100-90, så
# 200 ligger over zonens top. Udbrudslyset er 12, berøringen 18.
TOP = (155.0, 200.0, 150.0, 155.0)


class TestKriterium1Brud:
    def _serie(self, brud_lys, brud_i=14, n=20):
        return _flad_serie(n, {5: TOP, brud_i: brud_lys})

    def test_lukning_over_seneste_kendte_swing_high_over_zonens_top_er_brud(self):
        bars = self._serie((155.0, 210.0, 150.0, 205.0))
        assert bool(_f(_zone(f.DEMAND, 11, 12, 18, 100.0, 90.0), bars)[f.KOL[0]])

    def test_lukning_paa_niveauet_er_ikke_brud(self):
        bars = self._serie((155.0, 210.0, 150.0, 200.0))
        assert not bool(_f(_zone(f.DEMAND, 11, 12, 18, 100.0, 90.0), bars)[f.KOL[0]])

    def test_bruddet_skal_ligge_efter_udbrudslyset_og_foer_beroeringslyset(self):
        bars = self._serie((155.0, 210.0, 150.0, 205.0), brud_i=12)      # i udbrudslyset
        assert not bool(_f(_zone(f.DEMAND, 11, 12, 18, 100.0, 90.0), bars)[f.KOL[0]])
        bars = self._serie((155.0, 210.0, 150.0, 205.0), brud_i=18)      # i berøringslyset
        assert not bool(_f(_zone(f.DEMAND, 11, 12, 18, 100.0, 90.0), bars)[f.KOL[0]])

    def test_swing_high_skal_vaere_kendt_ved_udbrudslysets_lukning(self):
        bars = self._serie((155.0, 210.0, 150.0, 205.0))
        # udbrud ved lys 9: swing high'et ved lys 5 er først kendt ved lys 10.
        assert not bool(_f(_zone(f.DEMAND, 8, 9, 18, 100.0, 90.0), bars)[f.KOL[0]])

    def test_swing_high_under_zonens_top_taeller_ikke(self):
        bars = self._serie((155.0, 210.0, 150.0, 205.0))
        assert not bool(_f(_zone(f.DEMAND, 11, 12, 18, 250.0, 240.0), bars)[f.KOL[0]])

    def test_supply_er_spejlvendt(self):
        bars = _flad_serie(20, {5: (155.0, 160.0, 100.0, 155.0),
                                14: (155.0, 160.0, 90.0, 95.0)})
        assert bool(_f(_zone(f.SUPPLY, 11, 12, 18, 210.0, 200.0), bars)[f.KOL[1 - 1]])


# Kriterium 2: en rigtig supply-zone S i serien, berørt tæt på demand-zonens basislys.
S_BASIS = (9_990.0, 10_010.0, 9_990.0, 10_000.0)      # grøn, zone 9.990-10.010, E = 9.988
S_UDBRUD = (9_995.0, 9_996.0, 9_975.0, 9_980.0)       # lukker under zonens bund
S_AKTIV = (9_980.0, 9_985.0, 9_970.0, 9_975.0)        # high 9.985 < E: aktiverer
S_BEROER = (9_985.0, 9_990.0, 9_978.0, 9_980.0)       # high 9.990 ≥ E: berøring
LAV = (9_950.0, 9_955.0, 9_945.0, 9_950.0)            # doji langt under S, lukker ikke over
OVER_S = (9_990.0, 10_020.0, 9_985.0, 10_012.0)       # close 10.012 > S's top 10.010


class TestKriterium2Flip:
    def _serie(self, over_i=8, n=24, ekstra=None):
        rows = [LAV] * n
        for i, lys in ((1, S_BASIS), (2, S_UDBRUD), (3, S_AKTIV), (4, S_BEROER)):
            rows[i] = lys
        if over_i is not None:
            rows[over_i] = OVER_S
        for i, lys in (ekstra or {}).items():
            rows[i] = lys
        return _bars(rows)

    def _s_beroering(self, bars):
        z = k1.find_zoner_v2(bars, f.BUFFER)
        s = z[(z["side"] == f.SUPPLY) & (z["basis_i"] == 1)]
        assert len(s) == 1 and s.iloc[0]["status"] == k1.BEROERT
        return int(s.iloc[0]["slut_i"])

    def test_serien_indeholder_praecis_en_beroert_supply_zone_ved_lys_4(self):
        bars = self._serie()
        assert self._s_beroering(bars) == 4
        z = k1.find_zoner_v2(bars, f.BUFFER)
        assert list(z.loc[z["status"] == k1.BEROERT, "basis_i"]) == [1]

    def test_overlappende_zone_med_lukning_over_S_efter_S_blev_beroert_er_flip(self):
        bars = self._serie(over_i=8)
        zone = _zone(f.DEMAND, 6, 7, 20, 10_005.0, 9_995.0)    # overlapper 9.990-10.010
        assert bool(_f(zone, bars)[f.KOL[1]])

    def test_uden_prisoverlapning_er_det_ikke_et_flip(self):
        bars = self._serie(over_i=8)
        zone = _zone(f.DEMAND, 6, 7, 20, 9_900.0, 9_890.0)
        assert not bool(_f(zone, bars)[f.KOL[1]])

    def test_uden_en_lukning_over_S_top_er_det_ikke_et_flip(self):
        bars = self._serie(over_i=None)
        zone = _zone(f.DEMAND, 6, 7, 20, 10_005.0, 9_995.0)
        assert not bool(_f(zone, bars)[f.KOL[1]])

    def test_praecisering_2_lukningen_skal_ligge_efter_S_egen_beroering(self):
        """En lukning over S's top FØR S blev berørt tæller ikke — §3b's tredje led måles
        fra og med S's berøringslys."""
        bars = self._serie(over_i=None, ekstra={0: OVER_S})
        zone = _zone(f.DEMAND, 6, 7, 20, 10_005.0, 9_995.0)
        assert not bool(_f(zone, bars)[f.KOL[1]])

    def test_lukningen_skal_ligge_foer_zonens_egen_beroering(self):
        bars = self._serie(over_i=20)          # præcis i berøringslyset
        zone = _zone(f.DEMAND, 6, 7, 20, 10_005.0, 9_995.0)
        assert not bool(_f(zone, bars)[f.KOL[1]])

    @pytest.mark.parametrize("basis_i,forventet", [(4, True), (8, True), (9, False)])
    def test_praecisering_3_vinduet_er_basis_minus_4_til_og_med_basislyset(self, basis_i,
                                                                          forventet):
        """S blev berørt ved lys 4. Basislyset må ligge fra lys 4 (afstand 0) til lys 8."""
        bars = self._serie(over_i=9)
        zone = _zone(f.DEMAND, basis_i, basis_i + 1, 20, 10_005.0, 9_995.0)
        assert bool(_f(zone, bars)[f.KOL[1]]) is forventet


class TestKriterium3Sweep:
    """Swing low ved lys 5 (niveau 80), kendt ved lys 10. Basislyset er 11, udbruddet 12."""

    BUND = (155.0, 160.0, 80.0, 155.0)

    def _serie(self, udbrud_close, n=20, bund_i=5):
        return _flad_serie(n, {bund_i: self.BUND,
                               12: (155.0, 160.0, 150.0, udbrud_close)})

    def test_zonens_bund_under_seneste_kendte_swing_low_og_udbrud_over_det(self):
        bars = self._serie(udbrud_close=90.0)
        assert bool(_f(_zone(f.DEMAND, 11, 12, 18, 78.0, 70.0), bars)[f.KOL[2]])

    def test_zonens_bund_over_swing_low_er_ikke_et_sweep(self):
        bars = self._serie(udbrud_close=90.0)
        assert not bool(_f(_zone(f.DEMAND, 11, 12, 18, 95.0, 85.0), bars)[f.KOL[2]])

    def test_udbrudslyset_skal_lukke_over_swing_low(self):
        bars = self._serie(udbrud_close=75.0)
        assert not bool(_f(_zone(f.DEMAND, 11, 12, 18, 78.0, 70.0), bars)[f.KOL[2]])

    def test_swing_low_skal_vaere_kendt_FOER_basislyset(self):
        """Kendt ved lys 10; med basislys 10 er det ikke kendt før basislyset."""
        bars = self._serie(udbrud_close=90.0)
        assert not bool(_f(_zone(f.DEMAND, 10, 12, 18, 78.0, 70.0), bars)[f.KOL[2]])
        assert bool(_f(_zone(f.DEMAND, 11, 12, 18, 78.0, 70.0), bars)[f.KOL[2]])

    def test_supply_er_spejlvendt(self):
        bars = _flad_serie(20, {5: (155.0, 230.0, 150.0, 155.0),
                                12: (155.0, 160.0, 150.0, 220.0)})
        assert bool(_f(_zone(f.SUPPLY, 11, 12, 18, 240.0, 232.0), bars)[f.KOL[2]])


class TestKriterium4Inducement:
    """Swing low ved lys 8 (kendt ved lys 13). E for zonen 100-90 er 101."""

    def _serie(self, bund, n=24, bund_i=8):
        return _flad_serie(n, {bund_i: (155.0, 160.0, bund, 155.0)})

    def test_swing_low_over_E_kendt_mellem_udbrud_og_beroering(self):
        bars = self._serie(bund=110.0)
        assert bool(_f(_zone(f.DEMAND, 1, 2, 20, 100.0, 90.0), bars)[f.KOL[3]])

    def test_swing_low_under_E_taeller_ikke(self):
        bars = self._serie(bund=95.0)
        assert not bool(_f(_zone(f.DEMAND, 1, 2, 20, 100.0, 90.0), bars)[f.KOL[3]])

    def test_swing_low_kendt_foer_udbrudslyset_taeller_ikke(self):
        bars = self._serie(bund=110.0)
        assert not bool(_f(_zone(f.DEMAND, 12, 13, 20, 100.0, 90.0), bars)[f.KOL[3]])

    def test_swing_low_kendt_i_beroeringslyset_taeller_ikke(self):
        bars = self._serie(bund=110.0)
        assert not bool(_f(_zone(f.DEMAND, 1, 2, 13, 100.0, 90.0), bars)[f.KOL[3]])
        assert bool(_f(_zone(f.DEMAND, 1, 2, 14, 100.0, 90.0), bars)[f.KOL[3]])

    def test_supply_er_spejlvendt(self):
        bars = _flad_serie(24, {8: (155.0, 200.0, 150.0, 155.0)})
        # supply-zone 220-210, E = 209: swing high 200 ligger under E.
        assert bool(_f(_zone(f.SUPPLY, 1, 2, 20, 220.0, 210.0), bars)[f.KOL[3]])
        assert not bool(_f(_zone(f.SUPPLY, 1, 2, 20, 195.0, 185.0), bars)[f.KOL[3]])


# Kriterium 5: HTF-demand-zone 150-160 ved lys 3-4, aktiveret ved lys 5 og derefter i live.
H_BASIS = (158.0, 160.0, 150.0, 152.0)          # rødt basislys, zone 150-160, E = 160
H_UDBRUD = (155.0, 170.0, 154.0, 165.0)         # lukker over zonens top
H_OVER = (165.0, 170.0, 162.0, 166.0)           # low 162 > E: aktiverer og holder sig over
H_BEROER = (165.0, 170.0, 158.0, 166.0)         # low 158 ≤ E: berøring
H_GENNEM = (152.0, 153.0, 140.0, 145.0)         # close 145 < zonens bund: ugyldig


class TestKriterium5Stakket:
    def _htf(self, n=20, ekstra=None):
        aendringer = {3: H_BASIS, 4: H_UDBRUD}
        aendringer.update({i: H_OVER for i in range(5, n)})
        aendringer.update(ekstra or {})
        return _flad_serie(n, aendringer)

    def _flade_handelsbarer(self, n=20):
        return _flad_serie(n)

    def test_overlappende_htf_zone_der_lever_og_er_dannet_stakker(self):
        zone = _zone(f.DEMAND, 0, 1, 12, 165.0, 155.0)
        assert bool(_f(zone, self._flade_handelsbarer(), self._htf())[f.KOL[4]])

    def test_uden_prisoverlapning_stakker_den_ikke(self):
        zone = _zone(f.DEMAND, 0, 1, 12, 210.0, 200.0)
        assert not bool(_f(zone, self._flade_handelsbarer(), self._htf())[f.KOL[4]])

    def test_htf_zone_af_modsat_side_stakker_ikke(self):
        zone = _zone(f.SUPPLY, 0, 1, 12, 165.0, 155.0)
        assert not bool(_f(zone, self._flade_handelsbarer(), self._htf())[f.KOL[4]])

    def test_htf_zonen_skal_vaere_dannet_ved_skaeringen(self):
        """Skæringen er lukningen af HTF-lys 3; udbrudslyset er 4, så zonen er ikke gyldig."""
        zone = _zone(f.DEMAND, 0, 1, 4, 165.0, 155.0)
        assert not bool(_f(zone, self._flade_handelsbarer(), self._htf())[f.KOL[4]])
        assert bool(_f(_zone(f.DEMAND, 0, 1, 6, 165.0, 155.0),
                       self._flade_handelsbarer(), self._htf())[f.KOL[4]])

    def test_htf_zone_beroert_foer_skaeringen_stakker_ikke(self):
        htf = self._htf(ekstra={8: H_BEROER})
        assert bool(_f(_zone(f.DEMAND, 0, 1, 8, 165.0, 155.0),
                       self._flade_handelsbarer(), htf)[f.KOL[4]])      # skæring ved lys 7
        assert not bool(_f(_zone(f.DEMAND, 0, 1, 12, 165.0, 155.0),
                           self._flade_handelsbarer(), htf)[f.KOL[4]])

    def test_praecisering_4_en_ugyldig_htf_zone_stakker_ikke(self):
        """Lys 5 lukker gennem zonen før aktiveringen: zonen dør uden nogensinde at være
        berørt. Efter skæringen ved lys 5 stakker den ikke."""
        htf = self._htf(ekstra={5: H_GENNEM})
        z = k1.find_zoner_v2(htf, Fraction(0))
        z = z[(z["side"] == f.DEMAND) & (z["basis_i"] == 3)]
        assert (z.iloc[0]["status"], z.iloc[0]["slut_i"]) == (k1.UGYLDIG, 5)
        assert bool(_f(_zone(f.DEMAND, 0, 1, 5, 165.0, 155.0),
                       self._flade_handelsbarer(), htf)[f.KOL[4]])      # skæring ved lys 4
        assert not bool(_f(_zone(f.DEMAND, 0, 1, 12, 165.0, 155.0),
                           self._flade_handelsbarer(), htf)[f.KOL[4]])


class TestKriterium6Retning:
    """HTF: swing high ved lys 5 (200), swing low ved lys 6 (100), opbrud ved lys 13
    (close 250) og nedbrud ved lys 20 (close 50)."""

    def _htf(self, n=28):
        return _flad_serie(n, {5: (155.0, 200.0, 150.0, 155.0),
                               6: (155.0, 160.0, 100.0, 155.0),
                               13: (155.0, 250.0, 150.0, 250.0),
                               20: (155.0, 160.0, 50.0, 50.0)})

    def test_serien_har_de_forventede_swing_punkter(self):
        htf = self._htf()
        sh, sl = f.swing_punkter(htf["high"].to_numpy(), htf["low"].to_numpy())
        assert list(np.flatnonzero(sh)) == [5, 13]
        assert list(np.flatnonzero(sl)) == [6, 20]

    @pytest.mark.parametrize("ber_i,demand_op", [(12, False), (16, True), (25, False)])
    def test_retningen_er_det_seneste_HTF_strukturbrud(self, ber_i, demand_op):
        bars, htf = _flad_serie(28), self._htf()
        d = _f(_zone(f.DEMAND, 0, 1, ber_i, 165.0, 155.0), bars, htf)[f.KOL[5]]
        s = _f(_zone(f.SUPPLY, 0, 1, ber_i, 165.0, 155.0), bars, htf)[f.KOL[5]]
        assert bool(d) is demand_op
        # Uafgjort (intet brud endnu) er falsk for begge sider; ellers er de hinandens
        # modsætning.
        assert bool(s) is (False if ber_i == 12 else not demand_op)

    def test_intet_brud_endnu_giver_falsk_for_begge_sider(self):
        bars, htf = _flad_serie(28), self._htf()
        for side in (f.DEMAND, f.SUPPLY):
            assert not bool(_f(_zone(side, 0, 1, 8, 165.0, 155.0), bars, htf)[f.KOL[5]])


class TestKriterium7Discount:
    """HTF: swing high 200 ved lys 5 (kendt ved 10), swing low 100 ved lys 16 (kendt ved
    21). Rangens midte er 150."""

    def _htf(self, n=28):
        return _flad_serie(n, {5: (155.0, 200.0, 150.0, 155.0),
                               16: (155.0, 160.0, 100.0, 155.0)})

    def test_zonens_midtpunkt_under_rangens_midte_er_discount(self):
        bars, htf = _flad_serie(28), self._htf()
        assert bool(_f(_zone(f.DEMAND, 0, 1, 25, 125.0, 115.0), bars, htf)[f.KOL[6]])

    def test_zonens_midtpunkt_over_rangens_midte_er_ikke_discount(self):
        bars, htf = _flad_serie(28), self._htf()
        assert not bool(_f(_zone(f.DEMAND, 0, 1, 25, 185.0, 175.0), bars, htf)[f.KOL[6]])

    def test_supply_er_spejlvendt_premium(self):
        bars, htf = _flad_serie(28), self._htf()
        assert bool(_f(_zone(f.SUPPLY, 0, 1, 25, 185.0, 175.0), bars, htf)[f.KOL[6]])
        assert not bool(_f(_zone(f.SUPPLY, 0, 1, 25, 125.0, 115.0), bars, htf)[f.KOL[6]])

    def test_uden_baade_swing_high_og_swing_low_er_rangen_udefineret(self):
        bars, htf = _flad_serie(28), self._htf()
        # Skæring ved lys 14: kun swing high'et er kendt.
        assert not bool(_f(_zone(f.DEMAND, 0, 1, 15, 125.0, 115.0), bars, htf)[f.KOL[6]])

    def test_swing_high_under_swing_low_giver_falsk(self):
        """To regimer: swing high 120 i det lave, swing low 250 i det høje. Højderne er
        strengt stigende i det høje regime, så der opstår intet nyt swing high."""
        rows = [(100.0, 105.0, 95.0, 100.0)] * 11
        for i in range(11, 28):
            p = 295.0 + (i - 11)
            rows.append((p, p + 5, p - 5, p))
        rows[5] = (100.0, 120.0, 95.0, 100.0)
        rows[16] = (rows[16][0], rows[16][1], 250.0, rows[16][3])
        htf = _bars(rows)
        sh, sl = f.swing_punkter(htf["high"].to_numpy(), htf["low"].to_numpy())
        assert (list(np.flatnonzero(sh)), list(np.flatnonzero(sl))) == ([5], [16])
        bars = _flad_serie(28)
        assert not bool(_f(_zone(f.DEMAND, 0, 1, 25, 125.0, 115.0), bars, htf)[f.KOL[6]])


def test_scoren_er_antallet_af_sande_kriterier():
    bars, htf = _flad_serie(28), TestKriterium7Discount()._htf()
    r = _f(_zone(f.DEMAND, 0, 1, 25, 125.0, 115.0), bars, htf)
    assert int(r["score"]) == int(sum(bool(r[k]) for k in f.KOL))
    assert 0 <= r["score"] <= f.MAKS_SCORE


# ===========================================================================
# 3. Intet filter kigger frem — modulets vigtigste test
# ===========================================================================

def _tilfaeldig_1m(n: int, seed: int, tick: float = 0.25,
                   start: str = "2023-03-01 00:00") -> pd.DataFrame:
    """Sammenhængende 1m-vandring i hele tick med to kontraktblokke.

    Kontraktskiftet lægges på en hel time, så ingen bin på 5m, 15m eller 1h blander to
    kontrakter (``resample.aggregate`` afviser det).
    """
    rng = np.random.default_rng(seed)
    idx = pd.date_range(pd.Timestamp(start, tz="UTC"), periods=n, freq="1min")
    close = 10_000 + np.cumsum(rng.normal(0, 1.5, n))
    open_ = np.r_[close[0], close[:-1]] + rng.normal(0, 0.5, n)
    doji = rng.random(n) < 0.05
    open_[doji] = close[doji]
    kvant = lambda x, fn: fn(np.asarray(x) / tick) * tick
    skift = (n // 2) // 60 * 60
    return pd.DataFrame({
        "open": kvant(open_, np.round), "close": kvant(close, np.round),
        "high": kvant(np.maximum(open_, close) + rng.exponential(1.2, n), np.ceil),
        "low": kvant(np.minimum(open_, close) - rng.exponential(1.2, n), np.floor),
        "volume": 1.0,
        "instrument_id": np.where(np.arange(n) < skift, 1, 2).astype(np.int64),
    }, index=idx.rename("time"))


def _beroerte_zoner(bars: pd.DataFrame) -> pd.DataFrame:
    z = k1.find_zoner_v2(bars, f.BUFFER)
    return z[z["status"] == k1.BEROERT]


LOOKAHEAD_1M = 30_000
PR_FILTER = 3
TILFAELDIGE = 15


def _stikproeve(z: pd.DataFrame, fuld: pd.DataFrame, seed: int = 0) -> list:
    """Zonerne der skæres af: for hvert filter nogle hvor det er sandt og nogle hvor det
    er falsk, plus en tilfældig håndfuld. §3a's krav gælder pr. filter, så stikprøven
    skal ramme hvert filter i begge tilstande, ikke bare tilfældigt."""
    valgt = []
    for kol in f.KOL:
        for vaerdi in (True, False):
            traef = fuld.index[fuld[kol] == vaerdi]
            valgt += list(traef[:: max(1, len(traef) // PR_FILTER)][:PR_FILTER])
    rng = np.random.default_rng(seed)
    valgt += list(rng.choice(z.index.to_numpy(), min(TILFAELDIGE, len(z)), replace=False))
    return list(dict.fromkeys(valgt))


@pytest.mark.parametrize("spor", ["A", "B"])
def test_intet_filter_kigger_frem(spor):
    """§3a: hvert filter bruger kun det der var kendt ved lukningen af lyset før
    berøringen. 1m-serien skæres af dér, begge timeframes bygges forfra af den afskårne
    serie — også det HTF-lys der så bliver halvt — og alle syv værdier skal være uændrede.
    """
    tf_min, htf_min = f.SPOR[spor]
    df = _tilfaeldig_1m(LOOKAHEAD_1M, seed=7)
    bars = resample.aggregate(df, tf_min)
    htf = resample.aggregate(df, htf_min)
    z = _beroerte_zoner(bars)
    fuld = f.beregn_filtre(z, bars, htf, tf_min, htf_min)

    # Testen er kun noget værd hvis filtrene faktisk varierer på serien.
    for kol in f.KOL:
        assert set(fuld[kol].tolist()) == {True, False}, f"{kol} varierer ikke"
    stik = _stikproeve(z, fuld)
    for kol in f.KOL:
        assert set(fuld.loc[stik, kol].tolist()) == {True, False}, \
            f"{kol} prøves kun i én tilstand"

    tf_luk = bars.index + pd.Timedelta(minutes=tf_min)
    for navn in stik:
        ber_i = int(z.loc[navn, "slut_i"])
        t_snit = tf_luk[ber_i - 1]
        kort = df[df.index < t_snit]
        b2 = resample.aggregate(kort, tf_min)
        h2 = resample.aggregate(kort, htf_min)
        assert len(b2) == ber_i                    # afskæringen rammer præcis lyset før
        kortere = f.beregn_filtre(z.loc[[navn]], b2, h2, tf_min, htf_min)
        assert (list(kortere.iloc[0][list(f.KOL)]) == list(fuld.loc[navn, list(f.KOL)])), \
            f"{spor}: zone {navn} ændrede sig da fremtiden blev fjernet"


@pytest.mark.parametrize("spor", ["A", "B"])
def test_filtrene_afhaenger_faktisk_af_skaeringen(spor):
    """Modstykket til testen ovenfor: rykkes skæringen frem, ændrer mindst ét filter sig
    for en betydelig del af zonerne. Ellers ville uændretheden være triviel."""
    tf_min, htf_min = f.SPOR[spor]
    df = _tilfaeldig_1m(LOOKAHEAD_1M, seed=7)
    bars = resample.aggregate(df, tf_min)
    htf = resample.aggregate(df, htf_min)
    z = _beroerte_zoner(bars)
    z = z[z["slut_i"] + 40 < len(bars)]
    fuld = f.beregn_filtre(z, bars, htf, tf_min, htf_min)
    senere = f.beregn_filtre(z.assign(slut_i=z["slut_i"] + 40), bars, htf, tf_min, htf_min)
    aendret = (fuld[list(f.KOL)].to_numpy() != senere[list(f.KOL)].to_numpy()).any(axis=1)
    assert aendret.mean() > 0.10


# ===========================================================================
# 4. Vindue, signal og regressionstjek
# ===========================================================================

def test_vindue_mask_er_k1s_paa_15m():
    idx = pd.date_range(pd.Timestamp("2023-06-12 10:00", tz="UTC"), periods=400, freq="15min")
    assert np.array_equal(f.vindue_mask(idx, 15), k1.vindue_mask(idx))


def test_vindue_mask_paa_5m_har_samme_graenser_i_CT():
    idx = pd.date_range(pd.Timestamp("2023-06-14 12:00", tz="UTC"), periods=200, freq="5min")
    m = f.vindue_mask(idx, 5)
    ct = idx[m].tz_convert(CT)
    minut = ct.hour * 60 + ct.minute
    assert minut.min() >= 8 * 60 + 30 and minut.max() < 14 * 60 + 30


def _to_dages_serie() -> pd.DataFrame:
    """Rigtige 1m-lys på to RTH-dage: en demand-zone der dannes og berøres i vinduet."""
    lys15 = [(10_010, 10_015, 9_995, 10_000),      # rødt basislys, zone 9.995-10.015
             (10_000, 10_030, 9_998, 10_020),      # udbrud, lukker over
             (10_022, 10_025, 10_020, 10_022),     # low 10.020 > E = 10.017: aktiverer
             (10_022, 10_025, 10_014, 10_022)]     # low 10.014 ≤ E: berøring
    lys15 += [(10_022, 10_025, 10_020, 10_022)] * 12
    rows = []
    for o, h, l, c in lys15:
        sti = np.linspace(o, c, 15)
        rows += [(p, h if i == 5 else p, l if i == 10 else p, p) for i, p in enumerate(sti)]
    a = np.asarray(rows, dtype=float)
    idx = pd.date_range(pd.Timestamp("2023-06-14 13:30", tz="UTC"), periods=len(a),
                        freq="1min")
    return pd.DataFrame({"open": a[:, 0], "high": a[:, 1], "low": a[:, 2], "close": a[:, 3],
                         "volume": 1.0, "instrument_id": np.int64(1)}, index=idx.rename("time"))


def test_signalet_er_trin_A_motorens_kandidatregel():
    df = _to_dages_serie()
    bars, _, z = f.spor_data(df, 15, 60)
    mine = np.sort(z.loc[z["signal"].to_numpy(dtype=bool), "basis_i"].to_numpy())
    assert len(mine) >= 1
    assert np.array_equal(mine, f.trin_a_kandidater(bars))


def test_signalet_kraever_mindst_en_kontrakt_og_ikke_k1s_procentregel():
    df = _to_dages_serie()
    _, _, z = f.spor_data(df, 15, 60)
    sig = z[z["signal"].to_numpy(dtype=bool)]
    assert (sig["kontrakter_ekte"] >= 1).all()
    assert "under_stoploft" not in z.columns


# ===========================================================================
# 5. Optællingen og rapporten
# ===========================================================================

def _kunstige_signaler(n: int = 40, dage_n: int = 5, seed: int = 3):
    rng = np.random.default_rng(seed)
    dage = pd.DatetimeIndex(pd.date_range("2023-06-12", periods=dage_n, freq="D")).as_unit("ns")
    sig = pd.DataFrame({
        "side": rng.choice([f.DEMAND, f.SUPPLY], n),
        "dag": rng.choice(dage, n),
        "risiko_pt_ekte": rng.uniform(5, 40, n),
        "omk_R_netto_ekte": rng.uniform(0.02, 0.3, n),
        "kontrakter_ekte": rng.integers(1, 51, n).astype(float),
        "kontrakter_ekte_raa": rng.integers(1, 80, n).astype(float),
    })
    for kol in f.KOL:
        sig[kol] = rng.random(n) < 0.5
    sig["score"] = sig[list(f.KOL)].sum(axis=1).astype(np.int64)
    return sig, dage


def test_scorefordeling_og_kumulativ_haenger_sammen():
    sig, dage = _kunstige_signaler()
    o = f._opslag(pd.DataFrame(f.scoretabel(sig, dage) + f.kumulativtabel(sig, dage)))
    sum_pr_score = sum(o[("score", "alle", f.ALLE, str(s), "signaler_n")]
                       for s in range(f.MAKS_SCORE + 1))
    assert sum_pr_score == len(sig)
    assert o[("kumulativ", "alle", f.ALLE, ">=0", "signaler_n")] == len(sig)
    # Kumulativt er aftagende i k, både i signaler og i dage.
    for s in range(f.MAKS_SCORE):
        for maal in ("signaler_n", "dage_med_signal_n"):
            assert (o[("kumulativ", "alle", f.ALLE, f">={s}", maal)]
                    >= o[("kumulativ", "alle", f.ALLE, f">={s + 1}", maal)])


def test_dage_med_signal_er_antal_forskellige_dage():
    sig, dage = _kunstige_signaler()
    o = f._opslag(pd.DataFrame(f.kumulativtabel(sig, dage)))
    assert o[("kumulativ", "alle", f.ALLE, ">=0", "dage_med_signal_n")] == len(set(sig["dag"]))


def test_signal_paa_en_dag_uden_for_RTH_dagene_afvises():
    sig, dage = _kunstige_signaler()
    sig.loc[0, "dag"] = pd.Timestamp("2022-01-03")
    with pytest.raises(ValueError, match="uden for RTH-dagene"):
        f.kumulativtabel(sig, dage)


def test_filtertabellen_har_alle_syv_filtre_paa_tre_sider():
    sig, _ = _kunstige_signaler()
    tab = pd.DataFrame(f.filtertabel(sig))
    assert set(tab["noegle"]) == set(f.KOL)
    assert set(tab["side"]) == {f.ALLE, f.DEMAND, f.SUPPLY}
    o = f._opslag(tab)
    for kol in f.KOL:
        assert (o[("filtre", "alle", f.DEMAND, kol, "sande_n")]
                + o[("filtre", "alle", f.SUPPLY, kol, "sande_n")]
                == o[("filtre", "alle", f.ALLE, kol, "sande_n")])


class TestPhi:
    def test_ens_variable_giver_en(self):
        a = np.array([True, False, True, True, False])
        assert f.phi(a, a) == pytest.approx(1.0)

    def test_modsatte_variable_giver_minus_en(self):
        a = np.array([True, False, True, True, False])
        assert f.phi(a, ~a) == pytest.approx(-1.0)

    def test_konstant_variabel_giver_nan(self):
        a = np.array([True, True, True, True])
        assert np.isnan(f.phi(a, np.array([True, False, True, False])))

    def test_samvariation_har_alle_21_par(self):
        sig, _ = _kunstige_signaler()
        tab = pd.DataFrame(f.samvariation(sig))
        assert len(tab[tab["stoerrelse"] == "phi"]) == 21


def test_omkostningstabellen_har_de_praeregistrerede_stoerrelser():
    sig, _ = _kunstige_signaler()
    meta = {"zoner_i_vindue_n": 60, "afvist_kontrakter_nul_n": 20}
    o = f._opslag(pd.DataFrame(f.omkostningstabel(sig, meta)))
    n = ("omkostninger", "alle", f.ALLE, "signaler")
    for navn in ("risiko_pt_p10", "risiko_pt_p50", "risiko_pt_p90", "omk_R_netto_p10",
                 "omk_R_netto_p50", "omk_R_netto_p90", "be_WR_pct_netto_p50",
                 "kontrakter_p50", "kontrakter_p90", "kontrakter_maks",
                 "kontrakter_loftet_n"):
        assert np.isfinite(o[n + (navn,)])
    assert o[n + ("kontrakter_loftet_n",)] == (sig["kontrakter_ekte_raa"]
                                               > trinA.KONTRAKTER_LOFT).sum()
    assert o[n + ("afvist_kontrakter_nul_n",)] == 20


def test_be_WR_stiger_med_omkostningen():
    sig, _ = _kunstige_signaler()
    meta = {"zoner_i_vindue_n": 0, "afvist_kontrakter_nul_n": 0}
    n = ("omkostninger", "alle", f.ALLE, "signaler")
    lav = f._opslag(pd.DataFrame(f.omkostningstabel(sig, meta)))[n + ("be_WR_pct_netto_p50",)]
    dyr = sig.assign(omk_R_netto_ekte=sig["omk_R_netto_ekte"] + 0.1)
    hoej = f._opslag(pd.DataFrame(f.omkostningstabel(dyr, meta)))[n + ("be_WR_pct_netto_p50",)]
    assert hoej > lav


def test_hele_optaellingen_og_rapporten_paa_en_lille_aegte_serie(tmp_path):
    df = _to_dages_serie()
    dage = k1.rth_dage(pd.Timestamp("2023-06-14", tz="UTC"), pd.Timestamp("2023-06-16", tz="UTC"))
    z, sig, meta = f.signaler_med_filtre(df, 15, 60)
    assert len(sig) >= 1 and set(f.KOL) <= set(sig.columns)
    tab = f.optael(sig, z, dage, meta)
    tab.insert(0, "spor", "A")
    res = {"A": {"tabel": tab, "opslag": f._opslag(tab), "meta": meta, "signaler": sig}}
    md = f.skriv_md(res, {
        "koert_utc": "x", "head": "f" * 40,
        "commits": {f._rel(p): "f" * 40 for p in f.COMMITTEDE},
        "foerste_bar_utc": "a", "sidste_bar_utc": "b", "n_1m": len(df),
        "rth_dage_n": len(dage), "dage": dage, "csv_navn": "x.csv",
        "regression": {"csv_byte_for_byte": True, "spor_a_signaler_n": 1,
                       "trin_a_kandidater_n": 1, "identiske": True},
        "forventning": f.forventning_md(res),
    })
    assert "# B4 kandidat 1 — trin 2" in md
    assert "Spor A — handelstimeframe 15m, højere timeframe 60m" in md
    for kol in f.KOL:
        assert kol.split("_", 1)[1] in md
    assert "Ingen handel er simuleret" in md


def test_main_fra_ende_til_anden_med_datavejen_og_git_skiftet_ud(monkeypatch, tmp_path):
    df = _to_dages_serie()
    monkeypatch.setattr(f.holdout, "load_in_sample", lambda s: df)
    monkeypatch.setattr(f, "START", pd.Timestamp("2023-06-14", tz="UTC"))
    monkeypatch.setattr(f, "SLUT", pd.Timestamp("2023-06-16", tz="UTC"))
    monkeypatch.setattr(k1, "committede", lambda stier: {f._rel(s): "f" * 40 for s in stier})
    monkeypatch.setattr(f, "_git", lambda *a: type("Svar", (), {"stdout": "e" * 40})())
    monkeypatch.setattr(f, "regressionstjek", lambda df_1m=None: {
        "csv_byte_for_byte": True, "spor_a_signaler_n": 1, "trin_a_kandidater_n": 1,
        "identiske": True})

    f.main(["--koer", "--spor", "A", "--ud", str(tmp_path)])
    md = (tmp_path / "b4_k1_trin2_optaelling.md").read_text(encoding="utf-8")
    csv = pd.read_csv(tmp_path / "b4_k1_trin2_optaelling.csv")
    assert "Kørslen ser ikke på udfald" in md
    assert set(csv["tabel"]) == {"filtre", "score", "kumulativ", "brud_alene",
                                 "samvariation", "omkostninger"}
    assert set(csv["spor"]) == {"A"}


def test_koerslen_stopper_hvis_regressionstjekket_fejler(monkeypatch, tmp_path):
    monkeypatch.setattr(f.holdout, "load_in_sample", lambda s: _to_dages_serie())
    monkeypatch.setattr(f, "START", pd.Timestamp("2023-06-14", tz="UTC"))
    monkeypatch.setattr(f, "SLUT", pd.Timestamp("2023-06-16", tz="UTC"))
    monkeypatch.setattr(k1, "committede", lambda stier: {f._rel(s): "f" * 40 for s in stier})
    monkeypatch.setattr(f, "_git", lambda *a: type("Svar", (), {"stdout": "e" * 40})())
    monkeypatch.setattr(f, "regressionstjek", lambda df_1m=None: {
        "csv_byte_for_byte": False, "spor_a_signaler_n": 1, "trin_a_kandidater_n": 2,
        "identiske": False})
    with pytest.raises(RuntimeError, match="regressionstjekket fejler"):
        f.main(["--koer", "--ud", str(tmp_path)])


def test_pris_hentes_kun_gennem_load_in_sample():
    kilde = Path(f.__file__).read_text(encoding="utf-8")
    assert "holdout.load_in_sample(" in kilde
    assert "load_holdout" not in kilde


def test_praeregistreringen_og_kilden_staar_paa_listen_over_committede_filer():
    assert f.PREREG in f.COMMITTEDE and f.KILDE in f.COMMITTEDE
    assert Path(f.__file__).resolve() in f.COMMITTEDE
