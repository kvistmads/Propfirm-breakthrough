# B4 kandidat 3 — optælling uden udfald (§11.4)

Kørt 2026-10-07 18:56 UTC fra commit `7b8487d`, kode, tests og præregistrering committet og uændrede. **Ingen handel er simuleret; intet R, ingen vinderrate og intet udfald er regnet.**

Serie: MNQ.v.0 1m gennem `data.holdout.load_in_sample`, 2019-05-06 → 2023-12-31, 1.638.282 1m-barer. 1.173 RTH-dage. 1m-barer i [09:00, 11:00) CT: 140.760, heraf uden en bar i næste minut: 0.

## Åbningens retning, §4a

| RTH-dage | med retning | ned (long) | op (short) | r_aabning = 0 | manglende bar | rul 08:30-14:50 CT |
|---|---|---|---|---|---|---|
| 1.173 | 1.168 | 531 | 637 | 5 | 0 | 0 |

## Pr. variant — dækning og handler, §9 og §11.4

Én handel om dagen, så handler_n = dage med handel. Signaler er alle 1m-barer i vinduet der opfylder §4b, også dem efter dagens handel.

| model | variant | dage med retning | signaler | dage med signal | dage uden signal | sprunget over (hul) | afvist (kontrakter 0) | **handler_n** | long | short | signalminut p10/p50/p90 CT |
|---|---|---|---|---|---|---|---|---|---|---|---|
| vending | k = 1,0 | 1.168 | 24.918 | 1.168 | 0 | 0 | 0 | **1.168** | 531 | 637 | 09:00/09:01/09:09 |
| vending | k = 1,5 | 1.168 | 5.162 | 1.154 | 14 | 0 | 0 | **1.154** | 522 | 632 | 09:00/09:14/10:02 |
| vending | k = 2,0 | 1.168 | 1.109 | 688 | 480 | 0 | 0 | **688** | 266 | 422 | 09:00/09:45/10:41 |
| N_med | k = 1,0 | 1.168 | 24.639 | 1.168 | 0 | 0 | 0 | **1.168** | 637 | 531 | 09:00/09:01/09:10 |
| N_med | k = 1,5 | 1.168 | 4.851 | 1.145 | 23 | 0 | 0 | **1.145** | 620 | 525 | 09:00/09:15/10:01 |
| N_med | k = 2,0 | 1.168 | 1.002 | 639 | 529 | 0 | 0 | **639** | 306 | 333 | 09:00/09:45/10:40 |

## Pr. variant — risiko, omkostning og størrelse, §9

Over de valgte barer. be_WR_pct_netto_p50 = (1 + omk_R_netto_p50) / 2,5 (§6, N0).

| model | variant | risiko_pt p10/p50/p90 | omk_R_netto p50/p90 | be_WR_pct_netto_p50 | kontrakter p50/maks | kontrakter_loftet_n |
|---|---|---|---|---|---|---|
| vending | k = 1,0 | 12,39/26,64/46,14 | 0,049/0,106 | 42,0 | 4/28 | 0 |
| vending | k = 1,5 | 10,64/24,89/43,81 | 0,053/0,124 | 42,1 | 5/39 | 0 |
| vending | k = 2,0 | 9,64/22,64/41,46 | 0,058/0,136 | 42,3 | 5/39 | 0 |
| N_med | k = 1,0 | 11,89/26,89/45,39 | 0,049/0,111 | 42,0 | 4/26 | 0 |
| N_med | k = 1,5 | 10,74/24,64/43,54 | 0,053/0,122 | 42,1 | 5/32 | 0 |
| N_med | k = 2,0 | 9,39/22,14/40,69 | 0,059/0,140 | 42,4 | 5/39 | 0 |

## Pr. år — risiko og omkostning, §9

| model | variant | år | handler_n | risiko_pt p10/p50/p90 | omk_R_netto p50/p90 | kontrakter_loftet_n |
|---|---|---|---|---|---|---|
| vending | k = 1,0 | 2019 | 165 | 7,39/11,39/17,99 | 0,115/0,178 | 0 |
| vending | k = 1,0 | 2020 | 251 | 14,14/23,89/43,14 | 0,055/0,093 | 0 |
| vending | k = 1,0 | 2021 | 252 | 17,64/25,26/41,86 | 0,052/0,074 | 0 |
| vending | k = 1,0 | 2022 | 251 | 29,89/40,14/57,64 | 0,033/0,044 | 0 |
| vending | k = 1,0 | 2023 | 249 | 19,89/27,64/38,14 | 0,048/0,066 | 0 |
| vending | k = 1,5 | 2019 | 165 | 6,14/9,89/18,04 | 0,133/0,214 | 0 |
| vending | k = 1,5 | 2020 | 241 | 11,89/22,14/41,14 | 0,059/0,111 | 0 |
| vending | k = 1,5 | 2021 | 251 | 14,64/22,39/38,89 | 0,059/0,090 | 0 |
| vending | k = 1,5 | 2022 | 250 | 26,34/37,64/57,64 | 0,035/0,050 | 0 |
| vending | k = 1,5 | 2023 | 247 | 18,14/25,64/35,39 | 0,051/0,072 | 0 |
| vending | k = 2,0 | 2019 | 107 | 5,64/9,64/17,49 | 0,136/0,233 | 0 |
| vending | k = 2,0 | 2020 | 133 | 9,89/18,64/38,89 | 0,070/0,133 | 0 |
| vending | k = 2,0 | 2021 | 154 | 13,96/21,14/36,56 | 0,062/0,094 | 0 |
| vending | k = 2,0 | 2022 | 147 | 24,59/35,64/57,49 | 0,037/0,054 | 0 |
| vending | k = 2,0 | 2023 | 147 | 15,29/24,39/34,34 | 0,054/0,086 | 0 |
| N_med | k = 1,0 | 2019 | 165 | 7,14/10,89/18,14 | 0,121/0,184 | 0 |
| N_med | k = 1,0 | 2020 | 251 | 14,39/23,89/42,89 | 0,055/0,091 | 0 |
| N_med | k = 1,0 | 2021 | 252 | 17,64/24,26/40,89 | 0,054/0,074 | 0 |
| N_med | k = 1,0 | 2022 | 251 | 29,14/40,14/57,64 | 0,033/0,045 | 0 |
| N_med | k = 1,0 | 2023 | 249 | 19,64/27,89/38,44 | 0,047/0,067 | 0 |
| N_med | k = 1,5 | 2019 | 164 | 6,64/10,39/17,39 | 0,126/0,198 | 0 |
| N_med | k = 1,5 | 2020 | 249 | 11,64/22,14/39,69 | 0,059/0,113 | 0 |
| N_med | k = 1,5 | 2021 | 246 | 16,01/23,39/37,64 | 0,056/0,082 | 0 |
| N_med | k = 1,5 | 2022 | 244 | 26,71/38,26/54,34 | 0,034/0,049 | 0 |
| N_med | k = 1,5 | 2023 | 242 | 17,89/26,26/34,89 | 0,050/0,073 | 0 |
| N_med | k = 2,0 | 2019 | 109 | 6,14/9,89/16,89 | 0,133/0,214 | 0 |
| N_med | k = 2,0 | 2020 | 132 | 9,41/20,14/32,56 | 0,065/0,140 | 0 |
| N_med | k = 2,0 | 2021 | 141 | 14,39/22,89/37,14 | 0,057/0,091 | 0 |
| N_med | k = 2,0 | 2022 | 118 | 23,89/36,51/52,89 | 0,036/0,055 | 0 |
| N_med | k = 2,0 | 2023 | 139 | 15,64/24,39/35,34 | 0,054/0,084 | 0 |

## N-tid's opslag, §6

Pr. variant: modellens handelsdage, hvor mange forskellige minutter puljen har, og hvor mange (dag, puljeminut)-celler der ikke kan handles (læsning 10).

| variant | modeldage | minutter i puljen | celler uden handlebar bar |
|---|---|---|---|
| k = 1,0 | 1.168 | 30 | 0 |
| k = 1,5 | 1.154 | 108 | 0 |
| k = 2,0 | 688 | 120 | 0 |

## Betingelsen i §7

| variant | handler_n | MDE_R_ukorr | MDE_R_sidak3 | ≥ 330 |
|---|---|---|---|---|
| k = 1,0 | 1.168 | 0,089 | 0,106 | OK |
| k = 1,5 | 1.154 | 0,090 | 0,107 | OK |
| k = 2,0 | 688 | 0,116 | 0,138 | OK |

Alle 3 varianter har `handler_n ≥ 330`, så MDE (Šidák 3) ≤ 0,20 R.
