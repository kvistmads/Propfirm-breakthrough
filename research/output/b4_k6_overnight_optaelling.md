# B4 kandidat 6 — optælling uden udfald (§11.4)

Kørt 2026-10-09 16:37 UTC fra commit `2f48756`, kode, tests og præregistrering committet og uændrede. **Ingen P&L, ingen hit ratio og intet udfald er regnet.** Nætterne og udførelsespunkterne er bestemt af kalenderen og barernes tider alene. σ_nat er markedets egen svingning i vinduet (§7), og salgsdagen er forrige RTH-dags fortegn (§4c).

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
