# B4 kandidat 1 — signaloptælling 2, kerne v2

Kørt 2026-09-22 15:24 UTC fra commit `c18539f`, med modul, tests, præregistreringer, tillæg og datalag committet og uændrede. Præregistrering `research/prereg/b4_k1_optaelling_v2.md` (commit `5de6fa1`), tillæg `research/prereg/b4_k1_optaelling_v2_tillaeg.md` (commit `c18539f`). Bygger på `research/prereg/b4_k1_optaelling.md` (commit `11d68f2`) og `research/prereg/b4_k1_optaelling_tillaeg.md` (commit `50a060e`), som gælder medmindre v2 ændrer dem. Kode `research/b4_k1_optaelling.py` (commit `c18539f`).

Serie: NQ.v.0 ohlcv-1m gennem `data.holdout.load_in_sample`, 2016-01-03 23:00 → 2023-12-29 21:59 UTC. 2787275 1m-barer → 187558 15m-barer, 32 kontraktskift. RTH-dage in-sample: 2012, heraf uden RTH-barer i data: 0.

**Kørslen tæller signaler og ser ikke på udfald.** Den lægger intet til tælleren for den deflaterede tærskel.

## Hovedtal, kerne v2 (buffer 10%)

Andele i procent med Wilson 95%-CI i parentes. Percentilerne er lineære, tages af hver størrelse for sig og kun over signaler. `signaler_pr_dag` er fordelingen over alle RTH-dage, også dage uden signal. `risiko_pt` er 1,1 × H, og stoploft, kontrakter og omk_R regnes på den; `zonehoejde_pt` er H. `zoner_aldrig_beroert` er de to censurerede forløb tilsammen. `tid_til_aktiv_timer` er −0,25 når udbrudslyset selv er aktiveringslyset. Nævnerne står i tillæggene.

| størrelse | alle | demand | supply |
|---|---|---|---|
| RTH_dage_n | 2012 | 2012 | 2012 |
| signaler_n | 5350 | 2873 | 2477 |
| dage_med_signal_n | 1817 | 1413 | 1370 |
| dage_med_signal_pct | 90,3 (88,9–91,5) | 70,2 (68,2–72,2) | 68,1 (66,0–70,1) |
| signaler_pr_dag_p50 | 2,0 | 1,0 | 1,0 |
| signaler_pr_dag_p90 | 5,0 | 3,0 | 3,0 |
| zoner_dannet_n | 26278 | 13368 | 12910 |
| zoner_beroert_n | 18200 | 9403 | 8797 |
| zoner_ugyldige_foer_aktiv_n | 7551 | 3619 | 3932 |
| zoner_ugyldige_foer_aktiv_pct | 28,7 (28,2–29,3) | 27,1 (26,3–27,8) | 30,5 (29,7–31,3) |
| zoner_doede_ved_kontraktskift_n | 521 | 341 | 180 |
| zoner_doede_ved_kontraktskift_pct | 2,0 (1,8–2,2) | 2,6 (2,3–2,8) | 1,4 (1,2–1,6) |
| zoner_aktive_ikke_beroert_n | 5 | 5 | 0 |
| zoner_aktive_ikke_beroert_pct | 0,0 (0,0–0,0) | 0,0 (0,0–0,1) | 0,0 (0,0–0,0) |
| zoner_aldrig_aktive_n | 1 | 0 | 1 |
| zoner_aldrig_aktive_pct | 0,0 (0,0–0,0) | 0,0 (0,0–0,0) | 0,0 (0,0–0,0) |
| zoner_aldrig_beroert_pct | 0,0 (0,0–0,0) | 0,0 (0,0–0,1) | 0,0 (0,0–0,0) |
| beroeringer_n | 18200 | 9403 | 8797 |
| beroeringer_uden_for_vindue_pct | 67,9 (67,2–68,6) | 66,8 (65,8–67,8) | 69,1 (68,1–70,0) |
| beroeringer_i_vindue_n | 5842 | 3121 | 2721 |
| afvist_af_stoploft_pct | 8,4 (7,7–9,2) | 7,9 (7,0–8,9) | 9,0 (8,0–10,1) |
| zonehoejde_pt_p10 | 14,0 | 13,7 | 14,4 |
| zonehoejde_pt_p50 | 35,1 | 36,1 | 34,5 |
| zonehoejde_pt_p90 | 82,1 | 82,9 | 81,1 |
| risiko_pt_p10 | 15,4 | 15,1 | 15,8 |
| risiko_pt_p50 | 38,6 | 39,7 | 37,9 |
| risiko_pt_p90 | 90,3 | 91,1 | 89,3 |
| kontrakter_p10 | 1,0 | 1,0 | 1,0 |
| kontrakter_p50 | 3,0 | 3,0 | 3,0 |
| kontrakter_p90 | 8,0 | 8,0 | 7,0 |
| omk_R_brutto | 0,0000 | 0,0000 | 0,0000 |
| omk_R_netto_p10 | 0,0145 | 0,0144 | 0,0147 |
| omk_R_netto_p50 | 0,0340 | 0,0331 | 0,0346 |
| omk_R_netto_p90 | 0,0854 | 0,0870 | 0,0830 |
| be_WR_pct_brutto | 33,33 | 33,33 | 33,33 |
| be_WR_pct_netto_p50 | 34,47 | 34,44 | 34,49 |
| be_WR_pct_netto_p90 | 36,18 | 36,23 | 36,10 |
| zonealder_timer_p50 | 2,5 | 3,0 | 2,2 |
| zonealder_timer_p90 | 76,8 | 92,2 | 68,5 |
| tid_til_aktiv_timer_p50 | 0,25 | 0,25 | 0,25 |
| tid_til_aktiv_timer_p90 | 1,00 | 1,25 | 1,00 |
| tid_efter_aktiv_timer_p50 | 1,75 | 2,25 | 1,50 |
| tid_efter_aktiv_timer_p90 | 74,75 | 91,85 | 67,75 |
| beroering_lige_efter_aktivering_pct | 19,1 (18,1–20,2) | 17,8 (16,5–19,3) | 20,6 (19,1–22,3) |
| dannet_uden_for_RTH_pct | 47,2 (45,9–48,6) | 46,7 (44,9–48,5) | 47,8 (45,8–49,8) |

De fem forløb: 18200 berørt + 7551 ugyldig + 521 kontraktskift + 5 aktiv, ikke berørt + 1 aldrig aktiv = 26278 zoner dannet.

## Pr. år — dage_med_signal_pct, alle, kerne v2

| aar | RTH_dage_n | signaler_n | dage_med_signal_n | dage_med_signal_pct | ci95_lo_pct | ci95_hi_pct |
|---|---|---|---|---|---|---|
| 2016 | 252 | 664 | 233 | 92,5 | 88,5 | 95,1 |
| 2017 | 251 | 646 | 226 | 90,0 | 85,7 | 93,2 |
| 2018 | 251 | 727 | 232 | 92,4 | 88,5 | 95,1 |
| 2019 | 252 | 730 | 235 | 93,3 | 89,5 | 95,7 |
| 2020 | 253 | 640 | 212 | 83,8 | 78,8 | 87,8 |
| 2021 | 252 | 678 | 229 | 90,9 | 86,7 | 93,8 |
| 2022 | 251 | 572 | 219 | 87,3 | 82,6 | 90,8 |
| 2023 | 250 | 693 | 231 | 92,4 | 88,4 | 95,1 |

Demand og supply pr. år står i `b4_k1_optaelling_v2.csv`.

## Varianten uden buffer, §3 — B = 0

Kun til at kunne regne MDE for varianten senere. Beslutningsreglen gælder den ikke.

| side | signaler_n | dage_med_signal_n | dage_med_signal_pct |
|---|---|---|---|
| alle | 5615 | 1844 | 91,7 (90,4–92,8) |
| demand | 3023 | 1470 | 73,1 (71,1–75,0) |
| supply | 2592 | 1413 | 70,2 (68,2–72,2) |

## Beslutningsreglen, §5, anvendt mekanisk — kerne v2

dage_med_signal_n = 1817 af 2012. Wilson 95%-CI i dage: 1789,4–1841,5. Grænserne er 590 og 390.

CI'et ligger inden for én kategori: **≥ 590: testbar, også med filtersøgning — edge-testen præregistreres**.

## Forventningen, §7 — ikke et kriterium

- Forventet mellem 60% og 90% af RTH-dagene med signal. Målt 90,3% (88,9–91,5).
- Andelen af signaler med berøringen i lyset lige efter aktiveringslyset forventet langt under v1's 55,4%. Målt 19,1% (18,1–20,2).

## Gennemsigtighed — erklæret i tillæggene før kørslen

- Zoner hvor basis- og udbrudslys er naboer i serien, men med et hul i tid imellem: 684. Signaler fra dem: 84.
- Zoner hvor basis- og udbrudslys ligger i hver sin kontrakt (døde ved skiftet): 11.
- Signaler hvor formlen giver 0 kontrakter (risiko over 125 point, men højst 0,429%): 0.
- Signaler hvor udbrudslyset selv er aktiveringslyset: 30.

Alle tal, også hele tabellen for varianten og demand og supply pr. år: `b4_k1_optaelling_v2.csv`, kolonnen `kerne`.
