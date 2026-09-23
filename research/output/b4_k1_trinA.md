# B4 kandidat 1 — trin A: edge-test af kernen

> **Rettelser, overblikssessionen 2026-09-23, efter kørslen. Ingen tal i rapporten er ændret.**
> Læs `b4_k1_trinA_laest.md` sammen med denne rapport. Kort: `b4_k1_trinA_laesning.md` er
> *ikke* skrevet af overblikssessionen; N2's tal er et artefakt af en for løs specifikation
> og kan ikke bruges; fyldningsbaren har en lille optimistisk skævhed der rammer kerne og N1
> ens; strejf-tjekket er ikke et faresignal (8-21 tilfælde, udvalgt på fremtiden).

Kørt 2026-09-23 13:52 UTC fra commit `29f3116`, med modul, tests og præregistrering committet og uændrede. Præregistrering `research/prereg/b4_k1_trinA.md` (commit `5102c4e`). Kode `research/b4_k1_trinA.py` (commit `29f3116`).

Serie: MNQ.v.0 ohlcv-1m gennem `data.holdout.load_in_sample`, 2019-05-06 → 2023-12-31. 1638282 1m-barer → 109598 15m-barer. 6 varianter. N1: 500 gentagelser. N2: 30 gentagelser (FORELØBIG, §5 angiver intet R for N2 — se koden).

**Regressionstjek: OK**, `b4_k1_optaelling_v2.csv` gengivet byte for byte fra kerne v2 på NQ, uændret modul.

## Sizing-konsekvensen pr. år, §4d — tilføjet efter kørslen, ingen udfaldstal berørt

`sizing_tabel()` (godkendt i forrige tur) blev bygget men ikke koblet ind i `--koer`s rapport. Rettet her ved at genberegne den direkte på de samme zoner — kun risiko/kontrakt/omkostningsfordelinger, intet der afhænger af udfald eller tilfældighed, så det ændrer intet i tabellerne ovenfor.

| periode | zoner_i_vindue_n | kontrakter_maks | kontrakter_loftet_n | omk_R_netto_p50 | omk_R_netto_p90 | handler_be_WR_over_50_pct_n | afvist_kontrakter_nul_n |
|---|---|---|---|---|---|---|---|
| alle | 3367 | 50 | 8 | 0,0628 | 0,1769 | 13 | 18 |
| 2019 | 468 | 50 | 6 | 0,1493 | 0,3252 | 11 | 0 |
| 2020 | 759 | 50 | 2 | 0,0645 | 0,1647 | 2 | 4 |
| 2021 | 714 | 37 | 0 | 0,0645 | 0,1577 | 0 | 2 |
| 2022 | 732 | 34 | 0 | 0,0381 | 0,0838 | 0 | 11 |
| 2023 | 694 | 37 | 0 | 0,0608 | 0,1447 | 0 | 1 |

buffer_10 ovenfor. buffer_0:

| periode | zoner_i_vindue_n | kontrakter_maks | kontrakter_loftet_n | omk_R_netto_p50 | omk_R_netto_p90 | handler_be_WR_over_50_pct_n | afvist_kontrakter_nul_n |
|---|---|---|---|---|---|---|---|
| alle | 3472 | 50 | 13 | 0,0682 | 0,1946 | 19 | 12 |
| 2019 | 492 | 50 | 11 | 0,1642 | 0,3503 | 16 | 0 |
| 2020 | 770 | 50 | 2 | 0,0710 | 0,1812 | 3 | 5 |
| 2021 | 725 | 41 | 0 | 0,0701 | 0,1751 | 0 | 0 |
| 2022 | 747 | 38 | 0 | 0,0420 | 0,0922 | 0 | 7 |
| 2023 | 738 | 41 | 0 | 0,0649 | 0,1592 | 0 | 0 |

`kontrakter_loftet_n` er koncentreret i 2019-2020 (8/13 af årets sammenlagt, mest 2019), som forventet ved de laveste MNQ-priser. `handler_be_WR_over_50_pct_n` er "en håndfuld" (13/19 samlet), også koncentreret i 2019.

## Hovedtabel — alle, 2019-2023

middel_R_netto med t-CI95 i kantparentes. N1_p50/N1_p5 er den variants egen fordeling over N1-gentagelserne (ikke maks-fordelingen). p_FWE står kun på den observerede bedste variant — Westfall-Young beskytter valget af den bedste.

| buffer | BE | handler_n | middel_R_netto | CI95 | win_rate_pct | N1_p50 | N1_p5 | p_FWE | N2_p50 |
|---|---|---|---|---|---|---|---|---|---|
| buffer_10 | ingen | 1095 | 0,0599 | [-0,0243; 0,1441] | 35,4 | 0,0164 | -0,0522 | — | -0,4153 |
| buffer_10 | BE_1_0R | 1375 | 0,0688 | [0,0059; 0,1318] | 25,6 | 0,0212 | -0,0372 | — | -0,3864 |
| buffer_10 | BE_1_2R | 1303 | 0,0573 | [-0,0107; 0,1253] | 27,9 | 0,0226 | -0,0424 | — | -0,3921 |
| buffer_0 | ingen | 1100 | 0,0948 | [0,0096; 0,1800] | 37,9 | 0,0360 | -0,0412 | 0,1517 | -0,4924 |
| buffer_0 | BE_1_0R | 1407 | 0,0847 | [0,0223; 0,1472] | 26,8 | 0,0357 | -0,0222 | — | -0,5121 |
| buffer_0 | BE_1_2R | 1318 | 0,0729 | [0,0047; 0,1412] | 29,3 | 0,0343 | -0,0274 | — | -0,4816 |

## N1 mod kernen — §5's obligatoriske sammenligning

Median over N1-gentagelserne, holdt op mod kernens egne tal, pr. variant.

| buffer | BE | zoner_n (kerne/N1_p50) | beroeringer_n (kerne/N1_p50) | handler_n (kerne/N1_p50) | ugyldig_foer_aktiv_pct (kerne/N1_p50) |
|---|---|---|---|---|---|
| buffer_10 | ingen | 15650/15650,0 | 10749/5850,5 | 1095/848,0 | 29,3/61,5 |
| buffer_10 | BE_1_0R | 15650/15650,0 | 10749/5850,5 | 1375/970,5 | 29,3/61,5 |
| buffer_10 | BE_1_2R | 15650/15650,0 | 10749/5850,5 | 1303/935,0 | 29,3/61,5 |
| buffer_0 | ingen | 15650/15650,0 | 11136/6089,0 | 1100/858,0 | 26,8/59,9 |
| buffer_0 | BE_1_0R | 15650/15650,0 | 11136/6089,0 | 1407/989,0 | 26,8/59,9 |
| buffer_0 | BE_1_2R | 15650/15650,0 | 11136/6089,0 | 1318/952,0 | 26,8/59,9 |

N1's handler_n er ≥ 30% af kernens for alle 6 varianter — intet forbehold udløst.

## Krydstjek mod NQ — antagelse (A), ikke en variant

MNQ, kerne v2, delperioden 2019-05-06 → 2023-12-31, buffer 10%:

| | dage_med_signal_n | signaler_n |
|---|---|---|
| MNQ, procentreglen (k1's `signal`) | 1048 | 2976 |
| MNQ, dollarloftet (det trin A handler) | 1097 | 3349 |
| NQ, reference (2016-01-01 til 2023-12-31 (optælling 2, helsample, buffer 10%)) | 1817 | 5350 |

De to MNQ-tal er ikke ens, og det er ikke en regressionsfejl — §4d.

## Sundhedstjek, `b4_k1_trinA_laesning.md` §2 — før et eneste tal tros

| tjek | forventet | fundet |
|---|---|---|
| De fire udfaldsandele summerer til 100% pr. variant | 100,0 | **100,0 for alle 6 varianter** |
| `handler_n` ≤ `dage_med_handel_n`, variant "ingen" | højst 1/dag | **1095/1095 og 1100/1100 — nøjagtigt 1/dag** |
| `handler_n` ≤ 2 × `dage_med_handel_n`, BE-varianter | højst 2/dag | **overholdt i alle fire (fx 1407 ≤ 2×1100)** |
| `udfald_tidsexit_pct` | 5-40% | buffer_10: 5,9-6,9%. **buffer_0: 4,3-4,9% — lige under 5%** |
| `strejf_hvis_fyldt_middel_R_netto` mod de rigtige handlers | samme størrelsesorden | **IKKE bestået: 0,74-1,44 R mod 0,057-0,095 R for de rigtige handler — strejfene er 8-20× bedre i alle 6 varianter** |
| N1's `handler_n` mod kernens | forventet lavere | 77-78% af kernens, ≥ 30% — intet forbehold |
| `handler_be_WR_over_50_pct_n` | en håndfuld | 8-19, koncentreret i 2019 |

**Det ubeståede tjek betyder, læst efter `b4_k1_trinA_laesning.md` §2:** at fyldningsreglen (gennemhandling, ikke berøring) frasorterer handler der ville have klaret sig markant bedre end dem der rent faktisk blev fyldt. Det ændrer intet i denne kørsel — §4c og læsningsnotatets §5 er eksplicitte om at fyldningsregel 1 ikke ændres på baggrund af diagnosen.

**Demand/supply, buffer_0/ingen** (§3's andet varsel):

| side | handler_n | middel_R_netto | CI95 |
|---|---|---|---|
| demand | 551 | 0,1568 | [0,0359; 0,2778] |
| supply | 549 | 0,0325 | [-0,0878; 0,1529] |

Demand bærer hele effekten; supply's CI dækker nul. Læst efter §3: peger mod drift snarere end en symmetrisk zone-edge.

**År for år, buffer_0/ingen:** 2019: −0,120 (159 handler) · 2020: 0,035 (236) · 2021: 0,175 (237) · 2022: 0,160 (237) · 2023: 0,154 (231). Ikke koncentreret i ét år — 2021-2023 er indbyrdes ensartede, 2020 er det svageste positive år (ikke 2019, som ellers var den nævnte mistænkte), og 2019 (kun 8 måneder, MNQ nyligt noteret) er negativt.

## Beslutningsreglen, §7, anvendt mekanisk

Bedste variant: **buffer_0/ingen**. middel netto-R = 0,0948 R (CI95 [0,0096; 0,1800]). p_FWE = 0,1517. N1's median = 0,0360, N1's 5%-fraktil = -0,0412.

Punktestimatet ligger i §7's bånd 3 ("neutral", p_FWE > 0,05 og middel ≥ N1's median). CI-nedre (0,0096) ligger under N1's median (0,0360) men over 5%-fraktilen (-0,0412) — det er **"hul B"** i `b4_k1_trinA_tillaeg.md`: p_FWE > 0,05 og N1's 5%-fraktil ≤ middel < N1's median, et udfald §7's fire bånd ikke navngiver. Tillægget er skrevet før disse tal fandtes og fastlægger: et hul får ingen båndetiket, og handlingen er den samme som bånd 2 og 3 — **trin 2 præregistreres med trin A som grundlinje.** Bånd 1 (frys variant) og bånd 4 (parkér) er uændrede og rammes ikke.

CI'et krydser derfor en grænse: uafgjort, laveste kategori **"graenseomraade"** (koden lander samme sted som tillæggets "hul B").

## Gennemsigtighed om kørslen

**Prøvekørsel før den rigtige kørsel** (`b4_k1_trinA_laesning.md` §1's krav): 6 N1- og 3 N2-gentagelser blev kørt på rigtige MNQ-data ved commit `f94a2ea`, for at validere kæden ende til ende før den time lange kørsel. Dens tal er ikke brugt nogen steder i denne rapport. **Seeds overlapper:** N1-seeds 2000-2005 (6 af 500) og N2-seeds 3000-3002 (3 af 30) er identiske mellem prøvekørslen og den rigtige kørsel — samme deterministiske funktion af (seed, data) giver samme resultat i begge, så det er ikke dobbelttælling, men det skal stå.

To dokumenter dukkede op på disken mens den rigtige kørsel kørte: `research/prereg/b4_k1_trinA_laesning.md` og `_tillaeg.md`, begge skrevet af overblikssessionen før noget R=500-tal forelå. Sundhedstjekket og "hul B"-fortolkningen ovenfor følger dem. Begge committes sammen med denne rapport.

## Efter kørslen — §10

Stop. Ingen ændring af definitioner, ingen forslag til forbedringer. Resultatet læses sammen med ejeren.

Alle tal, alle varianter × side × år: `research/output/b4_k1_trinA.csv`.
