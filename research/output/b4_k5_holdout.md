# B4 kandidat 5 — holdout-testen af "1m · uden middag"

Kørt 2026-10-08 19:40 UTC fra commit `eb1189c`. Frosset hypotese `research/prereg/b4_k5_holdout.md` (commit `ef4af79`). Kandidat 5's modul uændret fra `9d4bd2e`. N-retning: 500 gentagelser. $ pr. dag pr. MNQ ved NQ 29138.

## Hovedtabel, §8

| serie | dage_n | handler_n | brutto_usd_dag | netto_usd_dag | CI90_netto | CI95_netto | N_retning_p5/p50/p95 | p_H1 |
|---|---|---|---|---|---|---|---|---|
| holdout | 689 | 8.970 | 3,65 | -30,55 | [-59,68; -1,42] | [-65,28; 4,17] | -63,86/-34,74/-6,18 | 0,4291 |
| in-sample | 1.169 | 14.831 | 74,40 | 41,07 | [14,18; 67,96] | [9,02; 73,12] | -64,82/-32,65/-6,09 | 0,0020 |

## Afgørelsen, §5, mekanisk

- H1 (p_H1 ≤ 0,05): **ikke bestået**
- H2 (CI90-nedre > 0): **ikke bestået**
- **Række 4: Parkeres: VWAP-retningen holdt ikke efter offentliggørelsen.**
- E_f (énsidet 95%-nedre grænse, in-sample og holdout samlet, 1.858 dage): **-5,59**, middel 14,51. Combine-betingelse 1 (E_f > 0): ikke opfyldt.

## Diagnoser, §7

| serie | netto ved $3,169 [CI95] | nominelt [CI95] | break-even middel | break-even CI |
|---|---|---|---|---|
| holdout | -37,60 [-72,52; -2,69] | -30,43 [-57,44; -3,41] | 0,280 | -2,259 |
| in-sample | 34,20 [2,01; 66,38] | -2,64 [-16,44; 11,16] | 5,864 | 3,324 |

| serie | bp/handel | bp/dag | handler pr. dag p10/p50/p90 | hit % brutto | gevinst/tab brutto | Sharpe/år |
|---|---|---|---|---|---|---|
| holdout | 0,048 | 0,63 | 5/12/22 | 22,5 | 3,47 | -1,04 |
| in-sample | 1,006 | 12,77 | 5/12/21 | 23,9 | 3,67 | 1,17 |

Brutto pr. halve time, New York-tid, $ pr. dag:

| halve time NY | holdout | in-sample |
|---|---|---|
| 09:30-10:00 | 10,13 | 12,08 |
| 10:00-10:30 | 10,47 | 10,75 |
| 10:30-11:00 | -1,67 | 11,43 |
| 11:00-11:30 | -3,86 | 9,92 |
| 11:30-12:00 | 2,17 | 2,87 |
| 12:00-12:30 | 0,00 | 0,00 |
| 12:30-13:00 | 0,00 | 0,00 |
| 13:00-13:30 | 0,00 | 0,00 |
| 13:30-14:00 | 0,00 | 0,00 |
| 14:00-14:30 | 0,00 | 0,00 |
| 14:30-15:00 | 0,00 | 0,00 |
| 15:00-15:30 | -1,20 | 15,96 |
| 15:30-16:00 | -12,39 | 11,39 |

| serie | sidste 5 min brutto [CI95] | dag p1/p5/p50/p95/p99 | værste/bedste dag | tab inden for dagen p1/p5/værste |
|---|---|---|---|---|
| holdout | -2,65 [-7,74; 2,44] | -1174/-778/-38/734/1111 | -2504/1715 | -1491/-968/-3068 |
| in-sample | 6,99 [1,65; 12,33] | -1424/-837/36/950/1658 | -2329/2477 | -1842/-1064/-2830 |

| serie | bedste dags andel | 5% bedste dages andel | long − short brutto [Welch-CI95] | altid-long [CI95] |
|---|---|---|---|---|
| holdout | — | — | 0,77 [-4,51; 6,04] | 12,22 [-33,11; 57,55] |
| in-sample | 0,052 | 1,665 | 0,43 [-4,67; 5,53] | 14,44 [-25,72; 54,59] |

Pr. år:

| serie | år | dage | netto $/dag [CI95] | nominelt | handler pr. dag | median L_d |
|---|---|---|---|---|---|---|
| holdout | 2024 | 252 | -9,69 [-63,46; 44,09] | -17,49 | 13,1 | 19120,00 |
| holdout | 2025 | 250 | -52,18 [-115,23; 10,86] | -42,95 | 13,1 | 22923,62 |
| holdout | 2026 | 187 | -29,75 [-94,18; 34,69] | -31,10 | 12,8 | 28606,75 |
| in-sample | 2019 | 167 | -1,65 [-55,67; 52,38] | -25,10 | 12,9 | 7842,75 |
| in-sample | 2020 | 249 | 86,89 [8,17; 165,60] | 6,67 | 12,5 | 10470,00 |
| in-sample | 2021 | 252 | 52,67 [-2,03; 107,37] | 10,23 | 12,4 | 14528,12 |
| in-sample | 2022 | 251 | 64,38 [-29,54; 158,30] | 12,25 | 12,3 | 12448,75 |
| in-sample | 2023 | 250 | -11,12 [-67,93; 45,70] | -24,82 | 13,4 | 14816,75 |

| serie | XNYS-dage | udelukket | manglende RTH-minutter | ruller i RTH |
|---|---|---|---|---|
| holdout | 689 | 0 | 0 | 0 |
| in-sample | 1.173 | 4 | 27 | 0 |

Udelukkede dage (diagnose, ikke i middel, CI eller nulmodel):

| serie | dag | grund | handler_n | netto $ | nominelt $ | tab inden for dagen $ |
|---|---|---|---|---|---|---|
| in-sample | 2020-03-09 | hul over 5 min | 11 | 1146,14 | 294,60 | -0,81 |
| in-sample | 2020-03-12 | hul over 5 min | 9 | 1254,21 | 306,36 | -180,75 |
| in-sample | 2020-03-16 | hul over 5 min | 9 | 2927,17 | 723,86 | -516,45 |
| in-sample | 2020-03-18 | hul over 5 min | 13 | -357,21 | -111,15 | -369,79 |

## Efter kørslen

Stop. §5 anvendes mekanisk og læses sammen med ejeren.
