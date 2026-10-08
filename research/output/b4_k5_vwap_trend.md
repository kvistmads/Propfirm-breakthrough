# B4 kandidat 5 — VWAP-trend efter Zarattini og Aziz (2023)

Kørt 2026-10-08 17:37 UTC fra commit `9d4bd2e`. Præregistrering `research/prereg/b4_k5_vwap_trend.md` (commit `1a515ea`). Kode `research/b4_k5_vwap_trend.py` (commit `9d4bd2e`).

Serie: MNQ.v.0 1m, 2019-05-06 → 2023-12-31, 1.169 dage. 4 varianter. N-retning: 500 gentagelser. Netto-dollar pr. dag pr. MNQ ved NQ 29138, omkostning $2,627 pr. round trip.

**Regressionstjek: OK.**

## Hovedtabel, §10

| variant | dage_n | handler_n | handler_pr_dag_p50 | middel_brutto_usd_dag | middel_netto_usd_dag | CI95_netto | N_retning_p5/p50/p95 | t_v | p_FWE | breakeven_omk_middel | breakeven_omk_CI | hit_ratio_pct_brutto | gevinst_tab_forhold | netto_usd_dag_nominelt | netto_usd_dag_ved_3169 | MDE_sidak4 | MDE_CI |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1m · hele dagen | 1.169 | 19.151 | 15 | 81,95 | 38,92 | [-0,30; 78,14] | -78,64/-44,06/-8,18 | 3,85 | 0,0020 | 5,003 | 2,609 | 17,5 | 5,38 | -9,09 | 30,04 | 61,6 | 56,1 |
| 1m · uden middag | 1.169 | 14.831 | 12 | 74,40 | 41,07 | [9,02; 73,12] | -64,82/-32,65/-6,09 | 4,26 | 0,0020 | 5,864 | 3,324 | 23,9 | 3,67 | -2,64 | 34,20 | 50,4 | 45,9 |
| 5m · hele dagen | 1.169 | 8.734 | 7 | 43,60 | 23,98 | [-14,44; 62,39] | -54,53/-17,73/13,69 | 2,08 | 0,0559 | 5,836 | 0,738 | 23,8 | 3,48 | -1,20 | 19,93 | 61,2 | 55,8 |
| 5m · uden middag | 1.169 | 7.387 | 6 | 38,40 | 21,80 | [-10,04; 53,65] | -45,18/-16,00/9,98 | 2,30 | 0,0299 | 6,077 | 1,063 | 32,7 | 2,25 | -0,07 | 18,38 | 49,8 | 45,4 |

## Afgørelsen, §8, mekanisk

**Ved $2,627: række 1: Varianten fryses.** Frosset variant: **1m · uden middag**.

**Ved $3,169 (diagnose, ændrer ikke rækken): række 1: Varianten fryses.** Frosset variant: **1m · uden middag**.

## Omkostningen, §9

| variant | break-even, middel = 0 | break-even, CI-nedre = 0 | netto ved $3,169 [CI95] | nominelt [CI95] |
|---|---|---|---|---|
| 1m · hele dagen | 5,003 | 2,609 | 30,04 [-9,40; 69,49] | -9,09 [-26,08; 7,91] |
| 1m · uden middag | 5,864 | 3,324 | 34,20 [2,01; 66,38] | -2,64 [-16,44; 11,16] |
| 5m · hele dagen | 5,836 | 0,738 | 19,93 [-18,58; 58,44] | -1,20 [-17,38; 14,98] |
| 5m · uden middag | 6,077 | 1,063 | 18,38 [-13,52; 50,28] | -0,07 [-13,39; 13,25] |

## Brutto i bp, handler og holdetid, §9

Artiklen: cirka 0,93 bp pr. handel og 14,1 bp pr. dag, cirka 15 handler om dagen.

| variant | bp pr. handel | bp pr. dag | handler pr. dag p10/p50/p90 | holdetid min p10/p50/p90 |
|---|---|---|---|---|
| 1m · hele dagen | 0,858 | 14,06 | 5/15/30 | 1/3/57 |
| 1m · uden middag | 1,006 | 12,77 | 5/12/21 | 1/4/55 |
| 5m · hele dagen | 1,001 | 7,48 | 2/7/13 | 5/15/160 |
| 5m · uden middag | 1,043 | 6,59 | 3/6/10 | 5/15/75 |

## Hit ratio og gevinst/tab-forhold, §9

Artiklen: 17% og 5,67.

| variant | hit ratio brutto % | gevinst/tab brutto | hit ratio netto % | gevinst/tab netto |
|---|---|---|---|---|
| 1m · hele dagen | 17,5 | 5,38 | 16,8 | 5,27 |
| 1m · uden middag | 23,9 | 3,67 | 23,2 | 3,60 |
| 5m · hele dagen | 23,8 | 3,48 | 23,4 | 3,44 |
| 5m · uden middag | 32,7 | 2,25 | 32,2 | 2,22 |

## Brutto pr. halve time, New York-tid, $ pr. dag, §9

Mark-to-market minut for minut. Artiklens figur 7: gevinst kl. 9:30-12 og 15-16.

| halve time NY | 1m · hele dagen | 1m · uden middag | 5m · hele dagen | 5m · uden middag |
|---|---|---|---|---|
| 09:30-10:00 | 12,08 | 12,08 | -7,14 | -7,14 |
| 10:00-10:30 | 10,75 | 10,75 | 3,34 | 3,34 |
| 10:30-11:00 | 11,43 | 11,43 | 3,94 | 3,94 |
| 11:00-11:30 | 9,92 | 9,92 | 8,65 | 8,65 |
| 11:30-12:00 | 2,87 | 2,87 | 1,48 | 1,48 |
| 12:00-12:30 | -3,66 | 0,00 | -4,29 | 0,00 |
| 12:30-13:00 | 2,44 | 0,00 | 1,12 | 0,00 |
| 13:00-13:30 | -1,94 | 0,00 | -4,52 | 0,00 |
| 13:30-14:00 | 12,96 | 0,00 | 14,03 | 0,00 |
| 14:00-14:30 | -3,02 | 0,00 | -0,60 | 0,00 |
| 14:30-15:00 | 0,78 | 0,00 | -0,54 | 0,00 |
| 15:00-15:30 | 15,96 | 15,96 | 15,59 | 15,59 |
| 15:30-16:00 | 11,39 | 11,39 | 12,54 | 12,54 |

## De sidste 5 minutter, §9

| variant | dage med position ved fladt | brutto $/dag 14:55-15:00 CT [CI95] |
|---|---|---|
| 1m · hele dagen | 1.169 | 6,96 [1,61; 12,31] |
| 1m · uden middag | 1.160 | 6,99 [1,65; 12,33] |
| 5m · hele dagen | 1.169 | 4,34 [-1,02; 9,70] |
| 5m · uden middag | 1.160 | 4,37 [-0,98; 9,72] |

## Dagsfordelingen ved dagens niveau, $ netto, §9

| variant | p1 | p5 | p50 | p95 | p99 | værste | bedste |
|---|---|---|---|---|---|---|---|
| 1m · hele dagen | -1845,5 | -1014,2 | 32,0 | 1113,5 | 1840,1 | -4076,4 | 3510,2 |
| 1m · uden middag | -1423,9 | -836,9 | 35,6 | 950,2 | 1658,1 | -2328,8 | 2476,8 |
| 5m · hele dagen | -1742,5 | -1044,8 | 5,7 | 1093,5 | 1746,9 | -3682,3 | 3564,9 |
| 5m · uden middag | -1548,6 | -784,8 | 12,2 | 889,9 | 1491,2 | -2809,0 | 3564,4 |

## Største tab inden for dagen, $ netto, mark-to-market på 1m-close, §9

| variant | p1 | p5 | værste |
|---|---|---|---|
| 1m · hele dagen | -2148,4 | -1310,5 | -4374,1 |
| 1m · uden middag | -1841,9 | -1063,7 | -2829,7 |
| 5m · hele dagen | -2172,3 | -1327,2 | -3864,8 |
| 5m · uden middag | -1926,0 | -1054,9 | -3239,2 |

## Konsistens, §9

| variant | bedste dags andel af samlet netto | de 5% bedste dages andel |
|---|---|---|
| 1m · hele dagen | 0,077 | 1,985 |
| 1m · uden middag | 0,052 | 1,665 |
| 5m · hele dagen | 0,127 | 3,260 |
| 5m · uden middag | 0,140 | 3,042 |

## Long mod short, brutto $ pr. handel, §9

| variant | long_n | short_n | long | short | long − short [Welch-CI95] |
|---|---|---|---|---|---|
| 1m · hele dagen | 9.643 | 9.508 | 6,01 | 3,98 | 2,02 [-2,90; 6,95] |
| 1m · uden middag | 7.575 | 7.256 | 6,08 | 5,64 | 0,43 [-4,67; 5,53] |
| 5m · hele dagen | 4.404 | 4.330 | 8,72 | 2,90 | 5,82 [-4,78; 16,42] |
| 5m · uden middag | 3.825 | 3.562 | 7,29 | 4,78 | 2,51 [-7,46; 12,48] |

## De udelukkede dage, tillæggets §3 (diagnose, ændrer intet)

Circuit breaker-dagene i marts 2020, udelukket efter §4h. Regnet med samme motor; positionen holdes gennem stoppet og udføres ved første bar efter det. Ikke med i middel, CI, nulmodel eller §8.

| variant | dag | handler_n | netto $ ved dagens niveau | nominelt $ | største tab inden for dagen $ |
|---|---|---|---|---|---|
| 1m · hele dagen | 2020-03-09 | 21 | 315,32 | 46,83 | -0,81 |
| 1m · hele dagen | 2020-03-12 | 18 | -502,28 | -164,79 | -1501,33 |
| 1m · hele dagen | 2020-03-16 | 15 | 1946,22 | 463,59 | -516,45 |
| 1m · hele dagen | 2020-03-18 | 14 | 466,69 | 83,22 | -229,77 |
| 1m · uden middag | 2020-03-09 | 11 | 1146,14 | 294,60 | -0,81 |
| 1m · uden middag | 2020-03-12 | 9 | 1254,21 | 306,36 | -180,75 |
| 1m · uden middag | 2020-03-16 | 9 | 2927,17 | 723,86 | -516,45 |
| 1m · uden middag | 2020-03-18 | 13 | -357,21 | -111,15 | -369,79 |
| 5m · hele dagen | 2020-03-09 | 9 | -995,27 | -291,14 | -1539,30 |
| 5m · hele dagen | 2020-03-12 | 11 | -2658,18 | -707,90 | -3892,75 |
| 5m · hele dagen | 2020-03-16 | 8 | 1818,55 | 444,98 | -1284,25 |
| 5m · hele dagen | 2020-03-18 | 4 | 10,47 | -5,51 | -809,76 |
| 5m · uden middag | 2020-03-09 | 7 | -635,87 | -188,39 | -1447,26 |
| 5m · uden middag | 2020-03-12 | 6 | -788,28 | -215,26 | -1843,35 |
| 5m · uden middag | 2020-03-16 | 6 | 2354,75 | 584,74 | -1284,25 |
| 5m · uden middag | 2020-03-18 | 5 | -1259,21 | -310,14 | -1271,80 |

## Altid-long, §6 (forklarer, ændrer intet)

Køb 08:31 CT, sælg ved fladt, 1.169 dage: middel netto 14,44 $/dag [-25,72; 54,59].

## Årlig Sharpe af den daglige netto, §9

Artiklen: 2,1.

| variant | Sharpe |
|---|---|
| 1m · hele dagen | 0,90 |
| 1m · uden middag | 1,17 |
| 5m · hele dagen | 0,57 |
| 5m · uden middag | 0,62 |

## Pr. år, §9

| variant | år | dage | netto $/dag [CI95] | nominelt $/dag | handler pr. dag | median L_d |
|---|---|---|---|---|---|---|
| 1m · hele dagen | 2019 | 167 | -12,53 [-79,17; 54,12] | -35,65 | 16,8 | 7842,75 |
| 1m · hele dagen | 2020 | 249 | 96,52 [0,66; 192,38] | 5,29 | 16,1 | 10470,00 |
| 1m · hele dagen | 2021 | 252 | 38,97 [-25,74; 103,69] | -1,92 | 16,0 | 14528,12 |
| 1m · hele dagen | 2022 | 251 | 75,22 [-41,34; 191,79] | 12,49 | 15,9 | 12448,75 |
| 1m · hele dagen | 2023 | 250 | -20,60 [-89,92; 48,72] | -34,55 | 17,2 | 14816,75 |
| 1m · uden middag | 2019 | 167 | -1,65 [-55,67; 52,38] | -25,10 | 12,9 | 7842,75 |
| 1m · uden middag | 2020 | 249 | 86,89 [8,17; 165,60] | 6,67 | 12,5 | 10470,00 |
| 1m · uden middag | 2021 | 252 | 52,67 [-2,03; 107,37] | 10,23 | 12,4 | 14528,12 |
| 1m · uden middag | 2022 | 251 | 64,38 [-29,54; 158,30] | 12,25 | 12,3 | 12448,75 |
| 1m · uden middag | 2023 | 250 | -11,12 [-67,93; 45,70] | -24,82 | 13,4 | 14816,75 |
| 5m · hele dagen | 2019 | 167 | -6,52 [-69,06; 56,03] | -16,08 | 7,3 | 7842,75 |
| 5m · hele dagen | 2020 | 249 | 25,46 [-74,82; 125,73] | -7,62 | 7,7 | 10470,00 |
| 5m · hele dagen | 2021 | 252 | 39,28 [-26,59; 105,14] | 9,55 | 7,5 | 14528,12 |
| 5m · hele dagen | 2022 | 251 | 73,28 [-35,35; 181,91] | 24,59 | 7,1 | 12448,75 |
| 5m · hele dagen | 2023 | 250 | -22,05 [-89,32; 45,21] | -21,60 | 7,6 | 14816,75 |
| 5m · uden middag | 2019 | 167 | -15,48 [-69,85; 38,89] | -16,35 | 6,3 | 7842,75 |
| 5m · uden middag | 2020 | 249 | 17,81 [-66,09; 101,72] | -9,79 | 6,5 | 10470,00 |
| 5m · uden middag | 2021 | 252 | 46,24 [-9,61; 102,09] | 14,69 | 6,4 | 14528,12 |
| 5m · uden middag | 2022 | 251 | 63,72 [-25,76; 153,20] | 21,79 | 6,1 | 12448,75 |
| 5m · uden middag | 2023 | 250 | -16,05 [-69,04; 36,94] | -16,34 | 6,4 | 14816,75 |

## Optælling og datakvalitet

## Serie og dage, §3 og §4h

MNQ.v.0 1m gennem `data.holdout.load_in_sample`, 2019-05-06 → 2023-12-31: 1.638.282 1m-barer. 1.173 XNYS-dage, heraf 9 kortdage blandt dem der indgår.

| emne | antal |
|---|---|
| XNYS-dage | 1.173 |
| udelukket, hul over 5 min | 4 |
| udelukket, første bar efter 08:35 CT | 0 |
| udelukket, ingen RTH-barer | 0 |
| **dage der indgår (n_dage)** | **1.169** |
| manglende RTH-minutter på dagene der indgår | 27 (på 2 dage) |
| ruller i serien | 19, kl. 18:00, 19:00, 19:01 CT |
| ruller inden for RTH | 0 |
| RTH-barer uden VWAP | 0 |
| 1m-lys / heraf close = VWAP | 454.263 / 7 |
| 5m-lys / heraf close = VWAP | 90.858 / 0 |

Udelukkede dage:

| dag | grund | største hul, min | første bar, min efter 08:30 |
|---|---|---|---|
| 2020-03-09 | hul over 5 min | 13 | 0 |
| 2020-03-12 | hul over 5 min | 13 | 0 |
| 2020-03-16 | hul over 5 min | 14 | 0 |
| 2020-03-18 | hul over 5 min | 13 | 0 |

## Pr. variant — handler og holdetid, §11.4

Handler pr. dag er over alle n_dage, også dage uden handel. Holdetid i minutter fra indgangsbar til udgangsbar. `udført senere` er ændringer der faldt i et manglende minut og blev udført på næste bar (§4c).

| variant | handler_n | handler pr. dag p10/p50/p90 | middel | dage uden handel | holdetid p10/p50/p90 | omk. $/dag | udgang vending/pause/fladt/efter RTH | udført senere |
|---|---|---|---|---|---|---|---|---|
| 1m · hele dagen | 19.151 | 5/15/30 | 16,38 | 0 | 1/3/57 | 43,04 | 17.982/0/1.169/0 | 2 |
| 1m · uden middag | 14.831 | 5/12/21 | 12,69 | 0 | 1/4/55 | 33,33 | 12.502/1.169/1.160/0 | 0 |
| 5m · hele dagen | 8.734 | 2/7/13 | 7,47 | 0 | 5/15/160 | 19,63 | 7.565/0/1.169/0 | 0 |
| 5m · uden middag | 7.387 | 3/6/10 | 6,32 | 0 | 5/15/75 | 16,60 | 5.058/1.169/1.160/0 | 0 |

## Pr. variant — σ_dag, MDE og styrke, §7

σ_dag = 2 × √(middel_d[(29.138 / L_d)² × Σ Δclose²]) over variantens lys i handelstiden. MDE_sidak4 = 3,0756 × σ_dag / √n_dage, MDE_CI = 2,8016 × σ_dag / √n_dage. Styrken er for CI-nedre > 0, hvis bruttogevinsten er $82 pr. dag og omkostningen variantens egen.

| variant | n_dage | σ_dag | MDE_sidak4 | MDE_CI | MDE_sidak4 ≤ $82 | omk. $/dag | netto ved $82 brutto | styrke |
|---|---|---|---|---|---|---|---|---|
| 1m · hele dagen | 1.169 | 685,0 | **61,6** | 56,1 | OK | 43,04 | 38,96 | 49,4% |
| 1m · uden middag | 1.169 | 560,5 | **50,4** | 45,9 | OK | 33,33 | 48,67 | 84,4% |
| 5m · hele dagen | 1.169 | 680,4 | **61,2** | 55,8 | OK | 19,63 | 62,37 | 88,0% |
| 5m · uden middag | 1.169 | 553,6 | **49,8** | 45,4 | OK | 16,60 | 65,40 | 98,1% |

## L_d og omkostningen pr. år, §4g

Omkostningen i bp er $2,627 / (2 × L) × 10⁴ pr. round trip ved årets median af L_d. Ved dagens niveau (NQ 29138) er den 0,45 bp.

| år | dage | median L_d | omk. bp pr. round trip |
|---|---|---|---|
| 2019 | 167 | 7842,75 | 1,67 |
| 2020 | 249 | 10470,00 | 1,25 |
| 2021 | 252 | 14528,12 | 0,90 |
| 2022 | 251 | 12448,75 | 1,06 |
| 2023 | 250 | 14816,75 | 0,89 |

Pr. variant og år: handler pr. dag (middel) og omkostning pr. dag i bp af positionen, middel over dagene.

| variant | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|
| 1m · hele dagen | 16,8 / 28,1 bp | 16,1 / 20,9 bp | 16,0 / 14,6 bp | 15,9 / 16,6 bp | 17,2 / 16,0 bp |
| 1m · uden middag | 12,9 / 21,5 bp | 12,5 / 16,3 bp | 12,4 / 11,3 bp | 12,3 / 12,8 bp | 13,4 / 12,4 bp |
| 5m · hele dagen | 7,3 / 12,3 bp | 7,7 / 10,0 bp | 7,5 / 6,9 bp | 7,1 / 7,4 bp | 7,6 / 7,1 bp |
| 5m · uden middag | 6,3 / 10,5 bp | 6,5 / 8,3 bp | 6,4 / 5,8 bp | 6,1 / 6,3 bp | 6,4 / 6,0 bp |

## Betingelsen i §7

Alle 4 varianter har MDE_sidak4 ≤ $82.

## Efter kørslen, §13

Stop. Ingen ændring af definitioner, ingen nye varianter og ingen forslag.

Alle tal: `research/output/b4_k5_vwap_trend.csv`.
