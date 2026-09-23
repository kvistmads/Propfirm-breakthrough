# B4 kandidat 1 — MNQ-data, verifikation mod NQ

Kørt 2026-09-23 08:35 UTC. Vindue 2019-05-06 → 2024-01-01 (MNQ's notering til holdout-grænsen). Ser ikke på signaler eller udfald og lægger intet til en tærskel.

NQ.v.0: 1642177 1m-barer → 109615 15m-barer. MNQ.v.0: 1638282 1m-barer → 109598 15m-barer. Fælles 15m-tidsstempler: 109589.

## Dækning pr. RTH-dag

1173 RTH-dage i vinduet (NYSE-kalenderen).

| | NQ | MNQ |
|---|---|---|
| dage med 0 manglende minutter | 1169 (99,66%) | 1167 (99,49%) |
| dage uden data overhovedet | 0 | 0 |
| manglende minutter, alle dage, sum | 54,00 | 81,00 |
| manglende minutter, andel af forventet | 0,01% | 0,02% |
| barer pr. dag, p10/p50/p90 | 390,0/390,0/390,0 | 390,0/390,0/390,0 |

Dage hvor MNQ og NQ's barantal afviger: 2 af 1173 (0,17%).

## Kontraktskift

NQ: 19 skift i vinduet. MNQ: 19 skift i vinduet.

### MNQ, alle skift

| tid_utc | fra instrument_id | til instrument_id |
|---|---|---|
| 2019-06-19 00:00:00+00:00 | 8078 | 8084 |
| 2019-09-16 00:00:00+00:00 | 8084 | 8107 |
| 2019-12-16 00:00:00+00:00 | 8107 | 8196 |
| 2020-03-16 00:01:00+00:00 | 8196 | 8204 |
| 2020-06-17 00:00:00+00:00 | 8204 | 13081 |
| 2020-09-16 00:00:00+00:00 | 13081 | 17706 |
| 2020-12-14 00:00:00+00:00 | 17706 | 6227 |
| 2021-03-17 00:00:00+00:00 | 6227 | 9485 |
| 2021-06-14 00:00:00+00:00 | 9485 | 3601 |
| 2021-09-13 00:00:00+00:00 | 3601 | 1447 |
| 2021-12-13 00:00:00+00:00 | 1447 | 7575 |
| 2022-03-16 00:00:00+00:00 | 7575 | 13505 |
| 2022-06-15 00:00:00+00:00 | 13505 | 7688 |
| 2022-09-14 00:00:00+00:00 | 7688 | 20332 |
| 2022-12-14 00:00:00+00:00 | 20332 | 8071 |
| 2023-03-15 00:00:00+00:00 | 8071 | 4973 |
| 2023-06-14 00:00:00+00:00 | 4973 | 9235 |
| 2023-09-13 00:00:00+00:00 | 9235 | 34070 |
| 2023-12-14 00:00:00+00:00 | 34070 | 7101 |

### NQ, alle skift

| tid_utc | fra instrument_id | til instrument_id |
|---|---|---|
| 2019-06-19 00:00:00+00:00 | 9166 | 36742 |
| 2019-09-16 00:00:00+00:00 | 36742 | 15907 |
| 2019-12-16 00:00:00+00:00 | 15907 | 10204 |
| 2020-03-18 00:00:00+00:00 | 10204 | 16908 |
| 2020-06-17 00:00:00+00:00 | 16908 | 14028 |
| 2020-09-16 00:00:00+00:00 | 14028 | 16337 |
| 2020-12-16 00:00:00+00:00 | 16337 | 4378 |
| 2021-03-17 00:00:00+00:00 | 4378 | 2786 |
| 2021-06-16 00:00:00+00:00 | 2786 | 828 |
| 2021-09-15 00:00:00+00:00 | 828 | 2770 |
| 2021-12-13 00:00:00+00:00 | 2770 | 3541 |
| 2022-03-16 00:00:00+00:00 | 3541 | 2895 |
| 2022-06-15 00:00:00+00:00 | 2895 | 10391 |
| 2022-09-14 00:00:00+00:00 | 10391 | 13613 |
| 2022-12-14 00:00:00+00:00 | 13613 | 20631 |
| 2023-03-15 00:00:00+00:00 | 20631 | 3522 |
| 2023-06-14 00:00:00+00:00 | 3522 | 2130 |
| 2023-09-13 00:00:00+00:00 | 2130 | 260937 |
| 2023-12-13 00:00:00+00:00 | 260937 | 750 |

## 15m-vægernes afvigelse, MNQ mod NQ, i tick (0,25 point)

Absolut afvigelse på fælles 15m-tidsstempler. `high` er lysets top, `low` bunden — begge indgår i kandidat 1's zonehøjde ("væger medregnet").

| session | n | high p50 | high p90 | high p99 | high maks | high = 0 tick | high ≤ 1 tick | low p50 | low p90 | low p99 | low maks | low = 0 tick | low ≤ 1 tick |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| alle, ekskl. rullevinduer | 108801 | 1,00 | 2,00 | 8,00 | 423,00 | 38,03% | 79,08% | 1,00 | 2,00 | 8,00 | 422,00 | 37,54% | 78,58% |
| RTH, ekskl. rullevinduer | 30156 | 1,00 | 2,00 | 7,00 | 195,00 | 42,38% | 82,79% | 1,00 | 2,00 | 7,00 | 252,00 | 41,66% | 82,28% |
| ETH, ekskl. rullevinduer | 78645 | 1,00 | 2,00 | 8,00 | 423,00 | 36,37% | 77,66% | 1,00 | 2,00 | 8,00 | 422,00 | 35,96% | 77,16% |
| alle, med rullevinduer | 109589 | 1,00 | 2,00 | 13,00 | 871,00 | 37,76% | 78,51% | 1,00 | 2,00 | 14,00 | 894,00 | 37,27% | 78,01% |

**Rullevinduer:** 788 af 109589 fælles 15m-barer ligger i et vindue hvor NQ og MNQ ikke er på samme kontraktgeneration — de to serier ruller ikke altid samme UTC-dag (datakilder.md §4). Der er forskellen kalenderspread mellem to forskellige kontrakter, ikke et brud på antagelse (A), og de bars er holdt uden for tabellen ovenfor og outlier-listen nedenfor.

### De 10 største afvigelser, uden for rullevinduer
| tid_utc | high_diff_tick | low_diff_tick | NQ high/low | MNQ high/low |
|---|---|---|---|---|
| 2022-02-27 23:00:00+00:00 | 423 | 32 | 13900,25/13683,00 | 14006,00/13691,00 |
| 2022-12-13 13:15:00+00:00 | -148 | -422 | 12000,00/11781,00 | 11963,00/11675,50 |
| 2022-10-13 12:30:00+00:00 | -335 | -1 | 10932,50/10506,50 | 10848,75/10506,25 |
| 2022-07-19 22:00:00+00:00 | 268 | 0 | 12338,00/12317,00 | 12405,00/12317,00 |
| 2022-12-14 18:45:00+00:00 | 0 | -252 | 12069,50/12038,75 | 12069,50/11975,75 |
| 2022-04-28 22:00:00+00:00 | 13 | -243 | 13247,00/13177,75 | 13250,25/13117,00 |
| 2020-03-22 22:00:00+00:00 | 219 | 0 | 6798,00/6628,75 | 6852,75/6628,75 |
| 2022-08-10 12:15:00+00:00 | 2 | -204 | 13146,25/13085,25 | 13146,75/13034,25 |
| 2019-05-12 22:00:00+00:00 | 198 | 15 | 7551,50/7521,50 | 7601,00/7525,25 |
| 2020-03-09 13:30:00+00:00 | 195 | -76 | 7973,50/7820,00 | 8022,25/7801,00 |

Spredt over søndag-genåbningen (18:00 ET), den tynde time før RTH-åbning (07:00-09:00 ET) og markedsuro (marts 2020, december 2022) — øjeblikke hvor de to selvstændigt handlede ordrebøger kan have et enkelt tryk der rammer den ene bog og ikke den anden. Ikke undersøgt pr. bar om close konvergerer bagefter; listen er til gennemsigtighed, ikke en forklaring der er efterprøvet.

## Fortolkning — antagelse (A)
Antagelsen i `research/output/b4_hypoteser.md` er at et prisniveau i indekspoint er det samme på NQ og MNQ. Tabellen ovenfor måler præcis det, på de kanter kandidat 1's zoner bruger. Kørslen tager ikke stilling til om afvigelsen er lille nok — det gøres når edge-testen præregistreres.
