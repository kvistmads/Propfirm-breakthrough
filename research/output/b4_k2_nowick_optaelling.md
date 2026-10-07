# B4 kandidat 2 — optælling uden udfald (§11.4)

Kørt 2026-10-07 10:07 UTC fra commit `c2de5e5`, kode, tests og præregistrering committet og uændrede. **Ingen handel er simuleret; intet R, ingen vinderrate og intet udfald er regnet.**

Serie: MNQ.v.0 1m gennem `data.holdout.load_in_sample`, 2019-05-06 → 2023-12-31. 1638282 1m-barer → 328638 5m-lys. 1173 RTH-dage. 5m-lys i vinduet uden doji: 83203.

## Kontraktskift, §4b

19 ruller. Tid i CT:

| tid_ct | ugedag | spring_pt |
|---|---|---|
| 2019-06-18 19:00 | Tuesday | 28,50 |
| 2019-09-15 19:00 | Sunday | 22,25 |
| 2019-12-15 18:00 | Sunday | 26,50 |
| 2020-03-15 19:01 | Sunday | -15,00 |
| 2020-06-16 19:00 | Tuesday | -10,00 |
| 2020-09-15 19:00 | Tuesday | -14,00 |
| 2020-12-13 18:00 | Sunday | 0,75 |
| 2021-03-16 19:00 | Tuesday | -10,00 |
| 2021-06-13 19:00 | Sunday | -8,75 |
| 2021-09-12 19:00 | Sunday | -7,25 |
| 2021-12-12 18:00 | Sunday | 1,00 |
| 2022-03-15 19:00 | Tuesday | -2,75 |
| 2022-06-14 19:00 | Tuesday | 33,75 |
| 2022-09-13 19:00 | Tuesday | 80,00 |
| 2022-12-13 18:00 | Tuesday | 120,25 |
| 2023-03-14 19:00 | Tuesday | 129,50 |
| 2023-06-13 19:00 | Tuesday | 184,00 |
| 2023-09-12 19:00 | Tuesday | 195,00 |
| 2023-12-13 18:00 | Wednesday | 210,75 |

## HTF-lys og trenddækning, §4b og §9

| HTF | lys_n | 1m uden for et lys | brud op | brud ned | konflikt (begge) | dage op % | dage ned % | dage udef. % | lys op % | lys ned % | lys udef. % | dage med skift i vinduet |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| daily | 1.205 | 2 | 433 | 170 | 0 | 58,2 | 40,3 | 1,4 | 58,0 | 40,5 | 1,5 | 0 |
| 4H | 7.187 | 2 | 1.989 | 1.214 | 1 | 57,2 | 42,5 | 0,3 | 56,9 | 42,8 | 0,3 | 86 |

## Signaler og udfaldne signaler, §9

Over 5m-lys uden væge i vinduet. Hvert lys tælles ét sted (læsning 15).

| HTF | uden væge | udefineret trend | ikke i trendens retning | ingen stopplads | rul | kontrakter nul | **signaler** | long | short | dage med signal |
|---|---|---|---|---|---|---|---|---|---|---|
| daily | 3.678 | 119 | 1.730 | 8 | 0 | 33 | **1.788** | 1.244 | 544 | 820 |
| 4H | 3.678 | 24 | 1.773 | 9 | 0 | 28 | **1.844** | 1.229 | 615 | 834 |

## Pr. variant — handler og betingelsen i §7

Gennemhandling (§4c regel 1). handler_n = dage med handel, fordi der er én handel om dagen. Mål deler fyldningerne, så 1R og 2R har samme handler_n. MDE i R, Šidák 12.

| variant | signaler | handler_n | dage | strejf_n | skyggefyld % | ordrer | erstattet | udløbet | annull. trend | annull. vindue | MDE Šidák | ≥ krav | betingelse |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| daily · 3 lys · 1R | 1.788 | 533 | 533 | 8 | 45,1 | 1.202 | 65 | 582 | 0 | 22 | 0,150 | 301 | OK |
| daily · 3 lys · 2R | 1.788 | 533 | 533 | 8 | 45,1 | 1.202 | 65 | 582 | 0 | 22 | 0,213 | 603 | **UNDER** |
| daily · 5 lys · 1R | 1.788 | 611 | 611 | 6 | 54,3 | 1.146 | 102 | 404 | 0 | 29 | 0,140 | 301 | OK |
| daily · 5 lys · 2R | 1.788 | 611 | 611 | 6 | 54,3 | 1.146 | 102 | 404 | 0 | 29 | 0,199 | 603 | OK |
| daily · 9 lys · 1R | 1.788 | 659 | 659 | 6 | 61,5 | 1.102 | 144 | 258 | 0 | 41 | 0,135 | 301 | OK |
| daily · 9 lys · 2R | 1.788 | 659 | 659 | 6 | 61,5 | 1.102 | 144 | 258 | 0 | 41 | 0,191 | 603 | OK |
| 4H · 3 lys · 1R | 1.844 | 559 | 559 | 7 | 46,0 | 1.210 | 66 | 568 | 2 | 15 | 0,147 | 301 | OK |
| 4H · 3 lys · 2R | 1.844 | 559 | 559 | 7 | 46,0 | 1.210 | 66 | 568 | 2 | 15 | 0,208 | 603 | **UNDER** |
| 4H · 5 lys · 1R | 1.844 | 634 | 634 | 6 | 55,4 | 1.154 | 99 | 394 | 3 | 24 | 0,138 | 301 | OK |
| 4H · 5 lys · 2R | 1.844 | 634 | 634 | 6 | 55,4 | 1.154 | 99 | 394 | 3 | 24 | 0,195 | 603 | OK |
| 4H · 9 lys · 1R | 1.844 | 684 | 684 | 4 | 63,3 | 1.106 | 141 | 243 | 3 | 35 | 0,133 | 301 | OK |
| 4H · 9 lys · 2R | 1.844 | 684 | 684 | 4 | 63,3 | 1.106 | 141 | 243 | 3 | 35 | 0,188 | 603 | OK |

Fyld ved berøring (§9), samme signaler:

| HTF · N | handler_n | skyggefyld % |
|---|---|---|
| daily · 3 lys | 539 | 46,4 |
| daily · 5 lys | 615 | 55,5 |
| daily · 9 lys | 660 | 62,6 |
| 4H · 3 lys | 565 | 47,3 |
| 4H · 5 lys | 638 | 56,6 |
| 4H · 9 lys | 685 | 64,3 |

## Sizing over signalerne, §9

| HTF | risiko_pt p10/p50/p90 | omk_R_netto p50/p90 | be_WR_pct_netto_p50 1R/2R | kontrakter p50/maks | kontrakter_loftet_n |
|---|---|---|---|---|---|
| daily | 4,25/20,00/66,65 | 0,066/0,309 | 53,3/35,5 | 6/50 | 79 |
| 4H | 4,25/20,12/65,75 | 0,065/0,309 | 53,3/35,5 | 6/50 | 78 |

## N-alm, én gentagelse (seed-strøm 0), §6

| HTF | nulkandidater | celler (dag, tilstand) | celler med for få | dage med for få | trukne | signaler uden væge |
|---|---|---|---|---|---|---|
| daily | 34.620 | 820 | 0 | 0 | 1.788 | 1.788 |
| 4H | 35.005 | 841 | 0 | 0 | 1.844 | 1.844 |

| HTF · N · regel | handler_n | dage | skyggefyld % | ordrer | erstattet |
|---|---|---|---|---|---|
| daily · 3 lys · gennem | 674 | 674 | 63,7 | 1.078 | 45 |
| daily · 3 lys · beroering | 682 | 682 | 65,5 | 1.069 | 41 |
| daily · 5 lys · gennem | 700 | 700 | 69,5 | 1.033 | 60 |
| daily · 5 lys · beroering | 706 | 706 | 70,8 | 1.027 | 55 |
| daily · 9 lys · gennem | 727 | 727 | 74,4 | 998 | 79 |
| daily · 9 lys · beroering | 733 | 733 | 75,8 | 989 | 72 |
| 4H · 3 lys · gennem | 672 | 672 | 64,5 | 1.055 | 32 |
| 4H · 3 lys · beroering | 677 | 677 | 65,9 | 1.044 | 28 |
| 4H · 5 lys · gennem | 713 | 713 | 70,3 | 1.031 | 52 |
| 4H · 5 lys · beroering | 719 | 719 | 71,6 | 1.020 | 47 |
| 4H · 9 lys · gennem | 738 | 738 | 75,4 | 999 | 72 |
| 4H · 9 lys · beroering | 740 | 740 | 76,5 | 988 | 67 |

## Betingelsen i §7

**Mindst én variant ligger under kravet. Code stopper, og ejeren beslutter (§7).**
