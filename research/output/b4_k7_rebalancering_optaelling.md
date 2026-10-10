# B4 kandidat 7 — optælling uden udfald (§11.5)

**Kørt:** 2026-10-10 11:26 UTC fra `e4ec483b5b42` (arbejdskopien kan indeholde ucommittet modul og tests). Præregistrering `research/prereg/b4_k7_rebalancering.md`. Ingen P&L, ingen hit ratio, intet udfald.

## ES (MES-økonomi, afgør)

| emne | antal |
|---|---|
| 1m-barer | 2.803.331 |
| handelsdage i alt (d 2016-04-01 → 2023-12-29) | 1.951 |
| udelukket: indgang over 5 min forsinket | 2 |
| udelukket: udgang mangler (over 5 min) | 0 |
| udelukket: ingen barer i Topstep-dagen | 0 |
| handelsdage med | 1.949 |
| indgang forsinket 1–5 min | 0 |
| udgang fra tidligere bar (≤ 5 min) | 0 |
| kortdage | 15 |
| ruller i serien / i vinduet | 32 / 31 |
| manglende signalbarer ES (heraf over 5 min) | 0 (0) |
| manglende signalbarer ZN (heraf over 5 min) | 7 (2) |
| månedsslut / kvartalsslut blandt signaldagene | 92 / 30 |

Udelukkede dage: 2018-04-30 (indgang over 5 min forsinket), 2020-07-01 (indgang over 5 min forsinket)

Ruller i vinduet: 2016-06-13, 2016-09-12, 2016-12-13, 2017-03-13, 2017-06-12, 2017-09-11, 2017-12-11, 2018-03-14, 2018-06-13, 2018-09-17, 2018-12-17, 2019-03-11, 2019-06-17, 2019-09-16, 2019-12-16, 2020-03-18, 2020-06-17, 2020-09-14, 2020-12-14, 2021-03-15, 2021-06-14, 2021-09-13, 2021-12-13, 2022-03-14, 2022-06-15, 2022-09-14, 2022-12-14, 2023-03-15, 2023-06-14, 2023-09-13, 2023-12-13

| variant | aktive dage | andel long | andel short | middel \|w\| | omk. pr. aktiv dag | σ_v | MDE_sidak2 | MDE_CI | E_v | styrke FWE mod E_v | mod E_v/2 | styrke CI mod E_v | mod E_v/2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T · tærskel | 1.949 | 19% | 81% | 0,293 | 1,31 | 315,2 | **20,0** | 20,0 | **26,5** | 96% | 46% | 94% | 39% |
| K · kalender | 556 | 39% | 61% | 1,000 | 4,45 | 431,1 | **51,1** | 51,2 | **51,0** | 80% | 29% | 72% | 21% |

w^T: p5 -0,518, p50 -0,261, p95 0,349, middel |w| 0,293. sd(T) 0,00434, sd(c) 0,00917.
Korrelation T (start første close 2016) mod T (start 2016-02-01) over handelsdagene: 0,9649. Korrelation w^T mod ES' afkast på t: -0,644.

| år | handelsdage | median L_d | omkostning i bp (historisk niveau) |
|---|---|---|---|
| 2016 | 191 | 2137,00 | 4,16 |
| 2017 | 251 | 2432,00 | 3,66 |
| 2018 | 250 | 2745,62 | 3,24 |
| 2019 | 252 | 2917,12 | 3,05 |
| 2020 | 252 | 3271,50 | 2,72 |
| 2021 | 252 | 4295,00 | 2,07 |
| 2022 | 251 | 4037,00 | 2,20 |
| 2023 | 250 | 4317,62 | 2,06 |

## Nasdaq-kontrol (NQ, MNQ-økonomi)

| emne | antal |
|---|---|
| 1m-barer | 2.787.275 |
| handelsdage i alt (d 2016-04-01 → 2023-12-29) | 1.951 |
| udelukket: indgang over 5 min forsinket | 2 |
| udelukket: udgang mangler (over 5 min) | 0 |
| udelukket: ingen barer i Topstep-dagen | 0 |
| handelsdage med | 1.949 |
| indgang forsinket 1–5 min | 0 |
| udgang fra tidligere bar (≤ 5 min) | 0 |
| kortdage | 15 |
| ruller i serien / i vinduet | 32 / 31 |
| manglende signalbarer ES (heraf over 5 min) | 0 (0) |
| manglende signalbarer ZN (heraf over 5 min) | 7 (2) |
| månedsslut / kvartalsslut blandt signaldagene | 92 / 30 |

Udelukkede dage: 2018-04-30 (indgang over 5 min forsinket), 2020-07-01 (indgang over 5 min forsinket)

Ruller i vinduet: 2016-06-13, 2016-09-12, 2016-12-13, 2017-03-13, 2017-06-12, 2017-09-11, 2017-12-11, 2018-03-12, 2018-06-11, 2018-09-17, 2018-12-17, 2019-03-11, 2019-06-19, 2019-09-16, 2019-12-16, 2020-03-18, 2020-06-17, 2020-09-16, 2020-12-16, 2021-03-17, 2021-06-16, 2021-09-15, 2021-12-13, 2022-03-16, 2022-06-15, 2022-09-14, 2022-12-14, 2023-03-15, 2023-06-14, 2023-09-13, 2023-12-13

| variant | aktive dage | andel long | andel short | middel \|w\| | omk. pr. aktiv dag | σ_v | MDE_sidak2 | MDE_CI | E_v | styrke FWE mod E_v | mod E_v/2 | styrke CI mod E_v | mod E_v/2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T · tærskel | 1.949 | 19% | 81% | 0,293 | 0,84 | 475,5 | **30,1** | 30,2 | **39,7** | 96% | 45% | 95% | 42% |
| K · kalender | 556 | 39% | 61% | 1,000 | 2,85 | 780,8 | **92,6** | 92,8 | **76,2** | 64% | 21% | 60% | 19% |

w^T: p5 -0,518, p50 -0,261, p95 0,349, middel |w| 0,293. sd(T) 0,00434, sd(c) 0,00917.
Korrelation T (start første close 2016) mod T (start 2016-02-01) over handelsdagene: 0,9649. Korrelation w^T mod ES' afkast på t: -0,644.

| år | handelsdage | median L_d | omkostning i bp (historisk niveau) |
|---|---|---|---|
| 2016 | 191 | 4737,50 | 3,01 |
| 2017 | 251 | 5793,25 | 2,46 |
| 2018 | 250 | 6959,12 | 2,05 |
| 2019 | 252 | 7693,88 | 1,85 |
| 2020 | 252 | 10302,88 | 1,38 |
| 2021 | 252 | 14571,62 | 0,98 |
| 2022 | 251 | 12440,00 | 1,15 |
| 2023 | 250 | 14826,00 | 0,96 |
