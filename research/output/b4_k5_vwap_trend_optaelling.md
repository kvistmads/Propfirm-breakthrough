# B4 kandidat 5 — optælling uden udfald (§11.4)

Kørt 2026-10-08 17:08 UTC fra commit `7506775`, kode, tests og præregistrering committet og uændrede. **Ingen P&L, ingen hit ratio, ingen andel long eller short og intet udfald er regnet.** Handlerne er bestemt af signalerne og handelstiden alene; ingen pris i en handel indgår. σ_dag er markedets egen svingning i handelstiden (§7).

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
