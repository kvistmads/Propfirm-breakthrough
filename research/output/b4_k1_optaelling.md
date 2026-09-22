# B4 kandidat 1 — signaloptælling

Kørt 2026-09-22 12:45 UTC fra commit `50a060e`, med modul, tests, præregistrering, tillæg og datalag committet og uændrede. Præregistrering `research/prereg/b4_k1_optaelling.md` (commit `11d68f2`), tillæg `research/prereg/b4_k1_optaelling_tillaeg.md` (commit `50a060e`). Kode `research/b4_k1_optaelling.py` (commit `50a060e`).

Serie: NQ.v.0 ohlcv-1m gennem `data.holdout.load_in_sample`, 2016-01-03 23:00 → 2023-12-29 21:59 UTC. 2787275 1m-barer → 187558 15m-barer, 32 kontraktskift. RTH-dage in-sample: 2012, heraf uden RTH-barer i data: 0.

**Kørslen tæller signaler og ser ikke på udfald.** Den lægger intet til tælleren for den deflaterede tærskel.

## Hovedtal

Andele i procent med Wilson 95%-CI i parentes. Percentilerne er lineære, tages af hver størrelse for sig og kun over signaler (zonehøjde, kontrakter, omk_R, zonealder). `signaler_pr_dag` er fordelingen over alle RTH-dage, også dage uden signal. `zoner_aldrig_beroert` er zonerne der stadig lever ved in-sample-slut (censurerede). Nævnerne står i tillægget.

| størrelse | alle | demand | supply |
|---|---|---|---|
| RTH_dage_n | 2012 | 2012 | 2012 |
| signaler_n | 6915 | 3605 | 3310 |
| dage_med_signal_n | 1940 | 1693 | 1669 |
| dage_med_signal_pct | 96,4 (95,5–97,1) | 84,1 (82,5–85,7) | 83,0 (81,2–84,5) |
| signaler_pr_dag_p50 | 3,0 | 2,0 | 1,0 |
| signaler_pr_dag_p90 | 6,0 | 3,0 | 3,0 |
| zoner_dannet_n | 26278 | 13368 | 12910 |
| zoner_beroert_n | 25960 | 13160 | 12800 |
| zoner_doede_ved_kontraktskift_n | 314 | 205 | 109 |
| zoner_doede_ved_kontraktskift_pct | 1,2 (1,1–1,3) | 1,5 (1,3–1,8) | 0,8 (0,7–1,0) |
| zoner_aldrig_beroert_n | 4 | 3 | 1 |
| zoner_aldrig_beroert_pct | 0,0 (0,0–0,0) | 0,0 (0,0–0,1) | 0,0 (0,0–0,0) |
| beroeringer_n | 25960 | 13160 | 12800 |
| beroeringer_uden_for_vindue_pct | 71,1 (70,5–71,6) | 70,1 (69,3–70,9) | 72,0 (71,3–72,8) |
| beroeringer_i_vindue_n | 7511 | 3932 | 3579 |
| afvist_af_stoploft_pct | 7,9 (7,3–8,6) | 8,3 (7,5–9,2) | 7,5 (6,7–8,4) |
| zonehoejde_pt_p10 | 16,8 | 16,7 | 17,0 |
| zonehoejde_pt_p50 | 41,4 | 42,5 | 39,8 |
| zonehoejde_pt_p90 | 90,9 | 91,5 | 90,0 |
| kontrakter_p10 | 1,0 | 1,0 | 1,0 |
| kontrakter_p50 | 3,0 | 2,0 | 3,0 |
| kontrakter_p90 | 7,0 | 7,0 | 7,0 |
| omk_R_brutto | 0,0000 | 0,0000 | 0,0000 |
| omk_R_netto_p10 | 0,0144 | 0,0144 | 0,0146 |
| omk_R_netto_p50 | 0,0318 | 0,0309 | 0,0330 |
| omk_R_netto_p90 | 0,0780 | 0,0787 | 0,0772 |
| be_WR_pct_brutto | 33,33 | 33,33 | 33,33 |
| be_WR_pct_netto_p50 | 34,39 | 34,36 | 34,43 |
| be_WR_pct_netto_p90 | 35,93 | 35,96 | 35,91 |
| zonealder_timer_p50 | 0,0 | 0,0 | 0,0 |
| zonealder_timer_p90 | 17,8 | 19,2 | 15,5 |
| dannet_uden_for_RTH_pct | 22,7 (21,7–23,7) | 22,9 (21,6–24,3) | 22,4 (21,0–23,9) |

## Pr. år — dage_med_signal_pct, alle

| aar | RTH_dage_n | signaler_n | dage_med_signal_n | dage_med_signal_pct | ci95_lo_pct | ci95_hi_pct |
|---|---|---|---|---|---|---|
| 2016 | 252 | 883 | 246 | 97,6 | 94,9 | 98,9 |
| 2017 | 251 | 920 | 246 | 98,0 | 95,4 | 99,1 |
| 2018 | 251 | 872 | 244 | 97,2 | 94,4 | 98,6 |
| 2019 | 252 | 931 | 246 | 97,6 | 94,9 | 98,9 |
| 2020 | 253 | 795 | 235 | 92,9 | 89,0 | 95,5 |
| 2021 | 252 | 890 | 246 | 97,6 | 94,9 | 98,9 |
| 2022 | 251 | 732 | 238 | 94,8 | 91,3 | 96,9 |
| 2023 | 250 | 892 | 239 | 95,6 | 92,3 | 97,5 |

Demand og supply pr. år står i `b4_k1_optaelling.csv`.

## Beslutningsreglen, §5, anvendt mekanisk

dage_med_signal_n = 1940 af 2012. Wilson 95%-CI i dage: 1921,8–1954,6. Grænserne er 590 og 390.

CI'et ligger inden for én kategori: **≥ 590: testbar, også med filtersøgning — edge-testen præregistreres**.

## Forventningen, §6 — ikke et kriterium

Forventet over 70% af RTH-dagene. Målt 96,4% (95,5–97,1).

## Gennemsigtighed — erklæret i tillægget før kørslen

- Zoner hvor basis- og udbrudslys er naboer i serien, men med et hul i tid imellem (dagligt stop, weekend, helligdag, manglende bin): 684. Signaler fra dem: 73.
- Zoner hvor basis- og udbrudslys ligger i hver sin kontrakt (døde ved skiftet): 11.
- Signaler hvor formlen giver 0 kontrakter (zonehøjde over 125 point, men højst 0,429%): 0.

Alle tal, også demand og supply pr. år: `b4_k1_optaelling.csv`.
