# B4 kandidat 6 — overnight drift ved Europas åbning

Kørt 2026-10-09 18:10 UTC fra commit `583dfd9`. Præregistrering: `research/prereg/b4_k6_overnight.md`. R = 500. Afgørelsen tages på NQ.v.0 ved $2,85 og dagens niveau (§8).

## Hovedtabel — NQ.v.0

| variant | naetter_n | middel_brutto_usd | middel_netto_usd | CI95_netto | N_nat_p5/p50/p95 | t_v | p_FWE | netto_usd_pr_kalendernat | MDE_sidak4 | MDE_CI |
|---|---|---|---|---|---|---|---|---|---|---|
| V1 · alle | 2.011 | 5,11 | **2,26** | [-2,70; 7,22] | -6,76/-1,79/2,28 | 1,52 | **0,168** | 2,26 | 8,1 | 7,3 |
| V1 · salg | 902 | 6,60 | **3,75** | [-3,86; 11,36] | -9,51/-1,88/5,26 | 1,30 | **0,228** | 1,68 | 13,0 | 11,8 |
| V2 · alle | 2.011 | 8,08 | **5,23** | [-2,67; 13,13] | -7,05/-1,43/3,54 | 2,01 | **0,072** | 5,22 | 12,2 | 11,1 |
| V2 · salg | 902 | 13,92 | **11,07** | [-0,95; 23,09] | -11,45/-1,72/7,92 | 2,29 | **0,044** | 4,96 | 19,8 | 18,0 |

## §8 anvendt mekanisk

**Række 2: Parkeres som "timen er særlig, men betaler ikke omkostningen".** Varianter: V2 · salg.

## Diagnoser — NQ.v.0 (afgør intet)

### Før og efter 2020-03-01 (artiklen udkom)

| variant | nætter før / efter | netto før | CI | netto efter | CI |
|---|---|---|---|---|---|
| V1 · alle | 1.046 / 965 | 1,72 | [-3,56; 7,00] | 2,84 | [-5,77; 11,46] |
| V1 · salg | 472 / 430 | 6,19 | [-2,10; 14,48] | 1,08 | [-12,07; 14,23] |
| V2 · alle | 1.046 / 965 | 3,97 | [-4,45; 12,39] | 6,59 | [-7,13; 20,30] |
| V2 · salg | 472 / 430 | 2,20 | [-11,47; 15,87] | 20,80 | [0,52; 41,08] |

### Pr. år: netto ved dagens niveau / nominelt

| variant | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|---|---|---|
| V1 · alle | 8,96 / -1,15 | -0,75 / -2,43 | 6,72 / -0,68 | -7,77 / -4,01 | 23,02 / 4,43 | 0,61 / -1,47 | -2,38 / -1,84 | -10,45 / -6,75 |
| V1 · salg | 6,08 / -1,52 | 1,08 / -2,09 | 17,04 / 1,62 | -5,44 / -3,43 | 0,54 / -3,08 | 9,86 / 2,54 | 5,87 / 1,75 | -8,41 / -5,30 |
| V2 · alle | 10,12 / -0,95 | -1,92 / -2,65 | 11,83 / 0,35 | -3,81 / -2,89 | 46,39 / 11,52 | -2,22 / -2,71 | -13,58 / -6,91 | -5,16 / -3,59 |
| V2 · salg | -3,70 / -3,05 | -6,36 / -3,59 | 11,99 / 0,10 | 0,36 / -1,61 | 28,77 / 6,64 | 17,08 / 6,31 | 23,25 / 9,23 | 15,41 / 6,67 |

### Netto ved $3,10, nominelt og break-even

| variant | netto ved $3,10 | CI | nominelt | CI | break-even middel | break-even CI |
|---|---|---|---|---|---|---|
| V1 · alle | 2,01 | [-2,95; 6,97] | -1,73 | [-3,46; -0,01] | 5,11 | 0,15 |
| V1 · salg | 3,50 | [-4,11; 11,11] | -1,03 | [-3,74; 1,69] | 6,60 | -1,01 |
| V2 · alle | 4,98 | [-2,92; 12,88] | -0,97 | [-3,70; 1,75] | 8,08 | 0,18 |
| V2 · salg | 10,82 | [-1,20; 22,84] | 2,65 | [-1,54; 6,83] | 13,92 | 1,90 |

Rækken i §8 ved $3,10 (afgør intet): **Række 2: Parkeres som "timen er særlig, men betaler ikke omkostningen".** Varianter: V2 · salg.

### Brutto efter salgsdagens størrelse (terciler af RTH-afkastet)

| variant | gruppe | nætter | median RTH-afkast | brutto | CI |
|---|---|---|---|---|---|
| V1 · salg | største salg | 301 | -1,52% | 11,02 | [-6,29; 28,32] |
| V1 · salg | mellem | 300 | -0,55% | -1,04 | [-12,69; 10,60] |
| V1 · salg | mindste salg | 301 | -0,15% | 9,81 | [0,39; 19,23] |
| V2 · salg | største salg | 301 | -1,52% | 35,36 | [7,52; 63,21] |
| V2 · salg | mellem | 300 | -0,55% | -5,94 | [-23,23; 11,35] |
| V2 · salg | mindste salg | 301 | -0,15% | 12,26 | [-2,69; 27,22] |

### Long hele natten, 17:00 → 08:30 CT

| nætter | n | brutto | netto | CI |
|---|---|---|---|---|
| alle | 2.009 | 17,82 | 14,97 | [-5,38; 35,31] |
| salg | 901 | 25,70 | 22,85 | [-11,31; 57,02] |

### Profil, natfordeling og største tab i vinduet (netto, $)

| variant | hit netto | gevinst/tab netto | hit brutto | p1/p5/p50/p95/p99 | værst / bedst | tab i vindue p1/p5/p50 | værste tab i vindue |
|---|---|---|---|---|---|---|---|
| V1 · alle | 48,9% | 1,11 | 50,5% | -298/-158/-1/171/342 | -604 / 1252 | -387/-215/-42 | -968 |
| V1 · salg | 51,1% | 1,05 | 52,9% | -316/-176/2/196/330 | -604 / 728 | -446/-237/-43 | -968 |
| V2 · alle | 51,8% | 1,02 | 52,4% | -495/-251/5/261/545 | -938 / 2181 | -584/-325/-64 | -1067 |
| V2 · salg | 53,4% | 1,05 | 53,7% | -525/-258/11/294/639 | -872 / 1154 | -604/-351/-67 | -956 |

## Kontrol — MNQ.v.0 2019-2023 (afgør intet)

| variant | naetter_n | middel_brutto_usd | middel_netto_usd | CI95_netto | N_nat_p5/p50/p95 | t_v | p_FWE | netto_usd_pr_kalendernat | MDE_sidak4 | MDE_CI |
|---|---|---|---|---|---|---|---|---|---|---|
| V1 · alle | 1.171 | 4,88 | **2,03** | [-5,48; 9,54] | -8,43/-1,65/4,49 | 0,91 | **0,461** | 2,03 | 12,1 | 11,0 |
| V1 · salg | 528 | 4,57 | **1,72** | [-9,82; 13,26] | -12,80/-2,36/10,16 | 0,59 | **0,623** | 0,78 | 19,5 | 17,7 |
| V2 · alle | 1.171 | 8,92 | **6,07** | [-5,82; 17,96] | -9,71/-1,83/5,89 | 1,64 | **0,156** | 6,06 | 18,2 | 16,6 |
| V2 · salg | 528 | 23,36 | **20,51** | [2,66; 38,36] | -16,52/-2,49/10,31 | 2,83 | **0,012** | 9,23 | 29,8 | 27,1 |

Rækken i §8 på kontrolserien: **Række 1: Varianten fryses.** Varianter: V2 · salg. Frosset: **V2 · salg**.

### Før og efter 2020-03-01 (artiklen udkom)

| variant | nætter før / efter | netto før | CI | netto efter | CI |
|---|---|---|---|---|---|
| V1 · alle | 207 / 964 | -2,61 | [-16,44; 11,22] | 3,03 | [-5,60; 11,66] |
| V1 · salg | 98 / 430 | 4,12 | [-19,30; 27,53] | 1,18 | [-11,99; 14,34] |
| V2 · alle | 207 / 964 | 3,39 | [-17,82; 24,61] | 6,65 | [-7,08; 20,37] |
| V2 · salg | 98 / 430 | 18,53 | [-18,49; 55,55] | 20,96 | [0,66; 41,25] |

### Pr. år: netto ved dagens niveau / nominelt

| variant | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|
| V1 · alle | -3,31 / -2,95 | 23,49 / 4,54 | 0,72 / -1,42 | -2,10 / -1,71 | -10,48 / -6,76 |
| V1 · salg | -2,42 / -2,75 | 0,89 / -3,03 | 9,84 / 2,52 | 5,94 / 1,79 | -8,41 / -5,30 |
| V2 · alle | 3,61 / -1,10 | 46,47 / 11,53 | -2,14 / -2,66 | -13,18 / -6,73 | -5,24 / -3,63 |
| V2 · salg | 14,98 / 1,82 | 28,59 / 6,56 | 17,29 / 6,42 | 23,80 / 9,48 | 15,53 / 6,74 |

### Netto ved $3,10, nominelt og break-even

| variant | netto ved $3,10 | CI | nominelt | CI | break-even middel | break-even CI |
|---|---|---|---|---|---|---|
| V1 · alle | 1,78 | [-5,73; 9,29] | -1,56 | [-4,41; 1,29] | 4,88 | -2,63 |
| V1 · salg | 1,47 | [-10,07; 13,01] | -1,08 | [-5,54; 3,39] | 4,57 | -6,97 |
| V2 · alle | 5,82 | [-6,07; 17,71] | -0,48 | [-4,98; 4,03] | 8,92 | -2,97 |
| V2 · salg | 20,26 | [2,41; 38,11] | 6,56 | [-0,27; 13,39] | 23,36 | 5,51 |

Rækken i §8 ved $3,10 (afgør intet): **Række 1: Varianten fryses.** Varianter: V2 · salg. Frosset: **V2 · salg**.

### Brutto efter salgsdagens størrelse (terciler af RTH-afkastet)

| variant | gruppe | nætter | median RTH-afkast | brutto | CI |
|---|---|---|---|---|---|
| V1 · salg | største salg | 176 | -1,70% | 8,40 | [-16,22; 33,02] |
| V1 · salg | mellem | 176 | -0,71% | -11,96 | [-29,78; 5,86] |
| V1 · salg | mindste salg | 176 | -0,20% | 17,28 | [0,53; 34,03] |
| V2 · salg | største salg | 176 | -1,70% | 34,98 | [-6,54; 76,51] |
| V2 · salg | mellem | 176 | -0,71% | 0,47 | [-25,63; 26,56] |
| V2 · salg | mindste salg | 176 | -0,20% | 34,63 | [12,64; 56,61] |

### Long hele natten, 17:00 → 08:30 CT

| nætter | n | brutto | netto | CI |
|---|---|---|---|---|
| alle | 1.169 | 19,15 | 16,30 | [-14,23; 46,84] |
| salg | 528 | 30,32 | 27,47 | [-24,31; 79,25] |

### Profil, natfordeling og største tab i vinduet (netto, $)

| variant | hit netto | gevinst/tab netto | hit brutto | p1/p5/p50/p95/p99 | værst / bedst | tab i vindue p1/p5/p50 | værste tab i vindue |
|---|---|---|---|---|---|---|---|
| V1 · alle | 49,9% | 1,05 | 51,3% | -374/-192/-0/183/403 | -604 / 1240 | -510/-265/-51 | -961 |
| V1 · salg | 51,3% | 0,98 | 53,0% | -381/-251/2/210/350 | -604 / 724 | -541/-291/-55 | -961 |
| V2 · alle | 53,8% | 0,94 | 54,1% | -535/-281/11/283/672 | -938 / 2171 | -663/-379/-80 | -1062 |
| V2 · salg | 57,8% | 0,98 | 57,8% | -538/-283/24/328/678 | -653 / 1146 | -671/-439/-79 | -960 |

## Datakvalitet


## NQ.v.0 — hovedserie, afgør

`data.holdout.load_in_sample("NQ.v.0")`: 2.787.275 1m-barer, første bar 2016-01-03 17:00 CT. Nætter for XNYS-dagene 2016-01-01 → 2023-12-29.

| emne | antal |
|---|---|
| nætter i alt (XNYS-dage) | 2.012 |
| udelukket, ingen barer i natten | 0 |
| udelukket, ingen barer i et vindue | 0 |
| udelukket, bar over 5 min forsinket | 1 |
| **nætter der indgår** | **2.011** |
| salgsdag ukendt (forrige RTH-dag uden barer) | 1 |
| salgsdage / kendte | 902 / 2.010 = **44,9%** |
| ruller i serien | 32, kl. 18:00, 19:00 CT |
| long hele natten udførbar (af dem der indgår) | 2.009 |

Udelukkede nætter (dag d):

| dag | grund |
|---|---|
| 2020-03-16 | bar over 5 min forsinket |

N-nat: mulige starter og andelen af dem, der kan udføres pr. nat (p1 / median over nætterne der indgår).

| længde | mulige starter | udførbare p1 | udførbare median |
|---|---|---|---|
| 60 min (V1) | 752 | 99,7% | 100,0% |
| 120 min (V2) | 572 | 99,7% | 100,0% |

Pr. variant. Forsinket = indgangs- eller udgangsbaren startede 1-5 minutter efter det nominelle tidspunkt. σ_nat = 2 × √(middel_n[(29.138 / L_n)² × Σ Δclose²]). MDE_sidak4 = 3,0756 × σ_nat / √n, MDE_CI = 2,8016 × σ_nat / √n. Styrke FWE er testen mod N-nat ved en bruttoeffekt over en tilfældig time; styrke CI er CI-nedre > 0 ved netto = effekt − $2,85 (læsning 13).

| variant | nætter | forsinket ind/ud | ruller i vinduet | σ_nat | MDE_sidak4 | MDE_CI | styrke FWE $8,6 / $17,2 | styrke CI $8,6 / $17,2 |
|---|---|---|---|---|---|---|---|---|
| V1 · alle | 2.011 | 2/2 | 0 | 117,5 | **8,1** | 7,3 | 85% / 100% | 59% / 100% |
| V1 · salg | 902 | 1/1 | 0 | 126,5 | **13,0** | 11,8 | 42% / 97% | 28% / 93% |
| V2 · alle | 2.011 | 28/2 | 0 | 177,3 | **12,2** | 11,1 | 48% / 98% | 31% / 95% |
| V2 · salg | 902 | 11/1 | 0 | 193,2 | **19,8** | 18,0 | 18% / 67% | 14% / 61% |

Median af L_n og omkostningen $2,85 i bp pr. round trip, pr. år. Ved dagens niveau (NQ 29138) er den 0,49 bp.

| variant | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|---|---|---|
| V1 · alle | 4541 / 3,14 bp (252) | 5796 / 2,46 bp (251) | 6966 / 2,05 bp (251) | 7692 / 1,85 bp (252) | 10383 / 1,37 bp (252) | 14563 / 0,98 bp (252) | 12439 / 1,15 bp (251) | 14814 / 0,96 bp (250) |
| V1 · salg | 4513 / 3,16 bp (114) | 5832 / 2,44 bp (104) | 6951 / 2,05 bp (125) | 7705 / 1,85 bp (112) | 9993 / 1,43 bp (107) | 14492 / 0,98 bp (109) | 12334 / 1,16 bp (131) | 14767 / 0,97 bp (100) |
| V2 · alle | 4541 / 3,14 bp (252) | 5798 / 2,46 bp (251) | 6964 / 2,05 bp (251) | 7694 / 1,85 bp (252) | 10386 / 1,37 bp (252) | 14566 / 0,98 bp (252) | 12460 / 1,14 bp (251) | 14820 / 0,96 bp (250) |
| V2 · salg | 4511 / 3,16 bp (114) | 5832 / 2,44 bp (104) | 6949 / 2,05 bp (125) | 7709 / 1,85 bp (112) | 9998 / 1,43 bp (107) | 14504 / 0,98 bp (109) | 12324 / 1,16 bp (131) | 14752 / 0,97 bp (100) |

## MNQ.v.0 — kontrol, afgør intet

`data.holdout.load_in_sample("MNQ.v.0")`: 1.638.282 1m-barer, første bar 2019-05-05 19:00 CT. Nætter for XNYS-dagene 2019-05-06 → 2023-12-29.

| emne | antal |
|---|---|
| nætter i alt (XNYS-dage) | 1.173 |
| udelukket, ingen barer i natten | 0 |
| udelukket, ingen barer i et vindue | 0 |
| udelukket, bar over 5 min forsinket | 2 |
| **nætter der indgår** | **1.171** |
| salgsdag ukendt (forrige RTH-dag uden barer) | 1 |
| salgsdage / kendte | 528 / 1.170 = **45,1%** |
| ruller i serien | 19, kl. 18:00, 19:00, 19:01 CT |
| long hele natten udførbar (af dem der indgår) | 1.169 |

Udelukkede nætter (dag d):

| dag | grund |
|---|---|
| 2020-03-16 | bar over 5 min forsinket |
| 2020-03-18 | bar over 5 min forsinket |

N-nat: mulige starter og andelen af dem, der kan udføres pr. nat (p1 / median over nætterne der indgår).

| længde | mulige starter | udførbare p1 | udførbare median |
|---|---|---|---|
| 60 min (V1) | 752 | 99,7% | 100,0% |
| 120 min (V2) | 572 | 99,8% | 100,0% |

Pr. variant. Forsinket = indgangs- eller udgangsbaren startede 1-5 minutter efter det nominelle tidspunkt. σ_nat = 2 × √(middel_n[(29.138 / L_n)² × Σ Δclose²]). MDE_sidak4 = 3,0756 × σ_nat / √n, MDE_CI = 2,8016 × σ_nat / √n. Styrke FWE er testen mod N-nat ved en bruttoeffekt over en tilfældig time; styrke CI er CI-nedre > 0 ved netto = effekt − $2,85 (læsning 13).

| variant | nætter | forsinket ind/ud | ruller i vinduet | σ_nat | MDE_sidak4 | MDE_CI | styrke FWE $8,6 / $17,2 | styrke CI $8,6 / $17,2 |
|---|---|---|---|---|---|---|---|---|
| V1 · alle | 1.171 | 2/2 | 0 | 134,3 | **12,1** | 11,0 | 48% / 98% | 31% / 96% |
| V1 · salg | 528 | 1/1 | 0 | 145,6 | **19,5** | 17,7 | 19% / 68% | 15% / 62% |
| V2 · alle | 1.171 | 5/0 | 0 | 202,2 | **18,2** | 16,6 | 22% / 75% | 16% / 68% |
| V2 · salg | 528 | 3/0 | 0 | 222,3 | **29,8** | 27,1 | 9% / 32% | 9% / 32% |

Median af L_n og omkostningen $2,85 i bp pr. round trip, pr. år. Ved dagens niveau (NQ 29138) er den 0,49 bp.

| variant | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|
| V1 · alle | 7840 / 1,82 bp (167) | 10478 / 1,36 bp (251) | 14563 / 0,98 bp (252) | 12439 / 1,15 bp (251) | 14815 / 0,96 bp (250) |
| V1 · salg | 7792 / 1,83 bp (81) | 9994 / 1,43 bp (107) | 14492 / 0,98 bp (109) | 12335 / 1,16 bp (131) | 14767 / 0,97 bp (100) |
| V2 · alle | 7842 / 1,82 bp (167) | 10478 / 1,36 bp (251) | 14566 / 0,98 bp (252) | 12459 / 1,14 bp (251) | 14820 / 0,96 bp (250) |
| V2 · salg | 7790 / 1,83 bp (81) | 9999 / 1,43 bp (107) | 14504 / 0,98 bp (109) | 12324 / 1,16 bp (131) | 14752 / 0,97 bp (100) |

## Commits

| fil | commit |
|---|---|
| `research/b4_k6_overnight.py` | `2f48756` |
| `tests/test_b4_k6_overnight.py` | `2f48756` |
| `research/prereg/b4_k6_overnight.md` | `50c03ba` |
| `research/output/b4_screening.md` | `50c03ba` |
| `research/b4_k5_vwap_trend.py` | `9d4bd2e` |
| `research/b4_k4_emt.py` | `3d9c62f` |
| `research/b4_k2_nowick.py` | `f053ece` |
| `research/b4_k1_trinA.py` | `c2de5e5` |
| `research/b4_k1_optaelling.py` | `c18539f` |
| `research/stats.py` | `b273371` |
| `research/normal.py` | `cab3b50` |
| `data/holdout.py` | `feed022` |
| `data/sessions.py` | `753ffd1` |