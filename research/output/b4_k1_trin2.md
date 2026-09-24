# B4 kandidat 1 — trin 2: videoens kriterier som score

Kørt 2026-09-24 22:35 UTC fra commit `432d3d9`, med modul, tests, præregistreringer, filtre, kerne, motor og datalag committet og uændrede. Præregistrering `research/prereg/b4_k1_trin2.md` (commit `d35b193`), definitioner `research/prereg/b4_k1_trin2_optaelling.md` (commit `feed022`) med tillæg `research/prereg/b4_k1_trin2_optaelling_tillaeg.md` (commit `fb88274`). Kode `research/b4_k1_trin2.py` (commit `ab05233`), filtre `research/b4_k1_filtre.py` (commit `fb88274`), motor `research/b4_k1_trinA.py` (commit `feed022`), kerne `research/b4_k1_optaelling.py` (commit `c18539f`).

Serie: MNQ.v.0 ohlcv-1m gennem `data.holdout.load_in_sample`, 2019-05-06 00:00 → 2023-12-29 21:59 UTC, 1638282 1m-barer. Kerne v2, buffer 10%, BE +1,2R, den rettede motor. Spor A: 15m med 1h. Spor B: 5m med 15m. N1: 500 gentagelser pr. spor.

## Regressionstjek, §10 — før kørslen

1. `research/b4_k1_optaelling.py` gengiver `b4_k1_optaelling_v2.csv` byte for byte: **OK**.
2. Spor A, score ≥ 0, buffer 10%, BE +1,2R: `handler_n` 1226 og `middel_R_netto` -0,0115 mod motorrettelsens 1226 og -0,0115: **OK**.
3. Scorefordelingen gengiver `b4_k1_trin2_optaelling.csv` (80 rækker): **OK**.

## Hovedtesten, §4 — stiger middel netto-R med scoren?

Enheden er skyggehandler: hvert signal simuleres for sig, uden disciplinregler. β er hældningen i en OLS af `R_netto` på scoren (0, 1, 2, 3, 4, 5+), med klyngerobust standardfejl pr. handelsdag. Én-sidet, H1: β > 0, α = 0,025 pr. spor (Bonferroni over 2). `dage_n` er antallet af klynger.

| spor | skyggehandler_n | dage_n | β_R_pr_scoretrin | CI95 | p_ensidet | α | MDE_β | N1_β p5/p50/p95 | andel_N1_β ≥ obs |
|---|---|---|---|---|---|---|---|---|---|
| A | 3286 | 1095 | -0,0342 | [-0,0719; 0,0035] | 0,9624 | 0,025 | 0,055 | -0,0453/-0,0054/0,0297 | 0,886 |
| B | 8948 | 1173 | -0,0285 | [-0,0524; -0,0047] | 0,9904 | 0,025 | 0,040 | -0,0186/0,0052/0,0316 | 0,988 |

### Middel netto-R pr. score

| spor | score | handler_n | middel_R_brutto | middel_R_netto | CI95 | win_rate_pct_netto | holder_pct | tvetydige_n |
|---|---|---|---|---|---|---|---|---|
| A | 0 | 34 | 0,6243 | 0,5485 | [0,0888; 1,0081] | 38,2 | 67,6 | 0 |
| A | 1 | 649 | 0,0778 | 0,0062 | [-0,0873; 0,0997] | 22,0 | 49,2 | 1 |
| A | 2 | 796 | 0,0273 | -0,0495 | [-0,1349; 0,0359] | 23,5 | 48,1 | 6 |
| A | 3 | 903 | -0,0133 | -0,1063 | [-0,1881; -0,0245] | 23,8 | 45,8 | 6 |
| A | 4 | 599 | -0,0090 | -0,1140 | [-0,2161; -0,0119] | 24,9 | 46,2 | 5 |
| A | 5+ | 305 | 0,0493 | -0,0447 | [-0,1929; 0,1035] | 28,2 | 46,2 | 3 |
| B | 0 | 130 | -0,0082 | -0,1317 | [-0,3607; 0,0972] | 26,9 | 50,0 | 0 |
| B | 1 | 1863 | 0,0020 | -0,1042 | [-0,1626; -0,0457] | 27,0 | 49,9 | 5 |
| B | 2 | 2442 | -0,0132 | -0,1244 | [-0,1757; -0,0731] | 26,7 | 48,2 | 18 |
| B | 3 | 2356 | -0,0282 | -0,1656 | [-0,2181; -0,1132] | 26,1 | 46,7 | 36 |
| B | 4 | 1539 | -0,0347 | -0,1967 | [-0,2622; -0,1313] | 26,6 | 46,3 | 42 |
| B | 5+ | 618 | -0,0464 | -0,2099 | [-0,3127; -0,1070] | 26,4 | 45,0 | 13 |

## Varianterne, §5 — handlet med disciplinreglerne

Westfall-Young maks-statistik over alle otte varianter på tværs af begge spor: for hver N1-gentagelse gemmes den største middel netto-R blandt de otte. `p_FWE` står kun på den observerede bedste variant. `N1_p50`/`N1_p5` er den variants egen fordeling over gentagelserne, ikke maks-fordelingen.

| spor | variant | handler_n | middel_R_brutto | middel_R_netto | CI95 | win_rate_pct_netto | maal/stop/BE/tidsexit_pct | N1_p50 | N1_p5 | p_FWE |
|---|---|---|---|---|---|---|---|---|---|---|
| A | kriterium 1 sandt | 974 | 0,0603 | -0,0376 | [-0,1190; 0,0438] | 27,8 | 27,8/51,1/16,1/4,9 | -0,0833 | -0,1654 | — |
| A | score ≥ 2 | 1104 | 0,0929 | -0,0019 | [-0,0788; 0,0750] | 28,8 | 28,8/50,0/16,0/5,2 | -0,0814 | -0,1533 | 0,1637 |
| A | score ≥ 3 | 937 | 0,0705 | -0,0269 | [-0,1105; 0,0568] | 28,4 | 28,4/51,2/14,9/5,4 | -0,0731 | -0,1551 | — |
| A | score ≥ 4 | 598 | 0,0949 | -0,0029 | [-0,1083; 0,1025] | 28,8 | 28,8/50,3/14,7/6,2 | -0,0781 | -0,1806 | — |
| B | kriterium 1 sandt | 1292 | 0,0702 | -0,0910 | [-0,1644; -0,0176] | 30,3 | 30,3/52,9/16,0/0,8 | -0,2085 | -0,2756 | — |
| B | score ≥ 2 | 1339 | 0,0734 | -0,0844 | [-0,1565; -0,0123] | 30,6 | 30,6/53,0/15,8/0,6 | -0,2040 | -0,2613 | — |
| B | score ≥ 3 | 1274 | 0,0694 | -0,0931 | [-0,1668; -0,0195] | 30,1 | 30,1/52,4/16,6/0,9 | -0,1981 | -0,2689 | — |
| B | score ≥ 4 | 1022 | 0,0400 | -0,1226 | [-0,2037; -0,0416] | 28,5 | 28,5/52,4/17,5/1,6 | -0,1743 | -0,2580 | — |

Bedste variant: **spor A, score ≥ 2** med middel netto-R -0,0019. N1's maks-fordeling: p5 -0,1241, p50 -0,0513, p95 0,0372. `p_FWE` = 0,1637.

## Beslutningsreglen, §7 — anvendt mekanisk

| krav | tal | opfyldt |
|---|---|---|
| Hovedtesten signifikant på spor A (p ≤ 0,025) | p = 0,9624 | nej |
| Hovedtesten signifikant på spor B (p ≤ 0,025) | p = 0,9904 | nej |
| Bedste variant: p_FWE ≤ 0,05 | 0,1637 | nej |
| Bedste variant: middel netto-R ≥ +0,20 R | -0,0019 | nej |
| Bedste variant: CI-nedre > 0 | -0,0788 | nej |

**Kategori: parkeres_stopreglen.** Hovedtesten er ikke signifikant over 0 på noget spor. Stopreglen: kandidat 1 parkeres. Varianterne rapporteres, men afgør intet.

§7's tre rækker er udtømmende — tredje række er "alt andet" — så hvert udfald falder i præcis én. Sætningen om at den laveste kategori gælder når et konfidensinterval krydser en grænse, har derfor intet at afgøre her; intervallet for den bedste variant krydser ikke 0,20 og nul.

## Diagnoserne, §8 — rapporteres, afgør intet

### Tvetydige minutter og bedste fald

En handel er tvetydig når stoppet blev ramt i en 1m-bar hvor **også** målet eller BE-triggeren kunne nås. Regel 4 antager stoppet først; bedste fald vender netop de bar om. Motorrettelse 1 står ved magt begge veje: i fyldningsbaren tjekkes kun stoppet.

| spor | skyggehandler_n | tvetydige_n | tvetydige_pct | β forsigtigt | β bedste fald | p_ensidet bedste fald |
|---|---|---|---|---|---|---|
| A | 3286 | 21 | 0,6 | -0,0342 | -0,0312 | 0,9480 |
| B | 8948 | 114 | 1,3 | -0,0285 | -0,0165 | 0,9133 |

Den bedste variant (spor A, score ≥ 2) i bedste fald: `handler_n` 1104, middel netto-R 0,0212 [-0,0561; 0,0984] mod -0,0019 forsigtigt. **Afgørelsen i §7 er taget på det forsigtige tal.**

### Middel netto-R pr. kriterium, sandt mod falsk

Beskrivende. **Må ikke bruges til nye varianter uden ny præregistrering, og en sådan brug koster fuldt N.**

| spor | kriterium | sand_n | sand_middel_R_netto | falsk_n | falsk_middel_R_netto | forskel | CI95 på forskellen |
|---|---|---|---|---|---|---|---|
| A | brud | 1973 | -0,1038 | 1313 | 0,0078 | -0,1117 | [-0,1985; -0,0249] |
| A | flip | 317 | 0,0142 | 2969 | -0,0671 | 0,0813 | [-0,0669; 0,2295] |
| A | sweep | 494 | -0,0008 | 2792 | -0,0695 | 0,0687 | [-0,0508; 0,1882] |
| A | inducement | 1192 | -0,1435 | 2094 | -0,0112 | -0,1322 | [-0,2221; -0,0424] |
| A | stakket | 960 | -0,0429 | 2326 | -0,0660 | 0,0231 | [-0,0721; 0,1183] |
| A | retning | 1786 | -0,0440 | 1500 | -0,0773 | 0,0333 | [-0,0525; 0,1191] |
| A | discount | 2204 | -0,0960 | 1082 | 0,0158 | -0,1118 | [-0,2028; -0,0208] |
| B | brud | 4983 | -0,1894 | 3965 | -0,0994 | -0,0900 | [-0,1440; -0,0360] |
| B | flip | 896 | -0,1116 | 8052 | -0,1537 | 0,0421 | [-0,0470; 0,1313] |
| B | sweep | 1218 | -0,0665 | 7730 | -0,1626 | 0,0960 | [0,0179; 0,1742] |
| B | inducement | 2899 | -0,2564 | 6049 | -0,0983 | -0,1581 | [-0,2156; -0,1006] |
| B | stakket | 2712 | -0,1240 | 6236 | -0,1606 | 0,0366 | [-0,0221; 0,0952] |
| B | retning | 4569 | -0,1347 | 4379 | -0,1650 | 0,0303 | [-0,0234; 0,0841] |
| B | discount | 5871 | -0,1763 | 3077 | -0,0983 | -0,0781 | [-0,1346; -0,0215] |

### Demand og supply hver for sig

| spor | nøgle | handler_n | middel_R_netto | CI95 |
|---|---|---|---|---|
| A | demand | 1755 | -0,0723 | [-0,1302; -0,0143] |
| A | supply | 1531 | -0,0443 | [-0,1077; 0,0192] |
| A | demand_minus_supply | 3286 | -0,0280 | [-0,1139; 0,0579] |
| B | demand | 4661 | -0,1462 | [-0,1835; -0,1088] |
| B | supply | 4287 | -0,1531 | [-0,1918; -0,1144] |
| B | demand_minus_supply | 8948 | 0,0069 | [-0,0468; 0,0607] |

### Pr. år — middel netto-R på skyggehandlerne

| spor | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|
| A | -0,2860 (n=454) | -0,0665 (n=741) | -0,0476 (n=698) | 0,0255 (n=714) | -0,0006 (n=679) |
| B | -0,3362 (n=1191) | -0,1625 (n=1969) | -0,1379 (n=1955) | -0,1014 (n=2007) | -0,0789 (n=1826) |

### Omkostninger og strejf pr. variant

| spor | variant | signaler_n | omk_R_netto_p50 | omk_R_netto_p90 | strejf_n | strejf_hvis_fyldt_middel_R_netto |
|---|---|---|---|---|---|---|
| A | kriterium 1 sandt | 2011 | 0,0702 | 0,1990 | 17 | 0,9577 |
| A | score ≥ 2 | 2651 | 0,0654 | 0,1911 | 16 | 0,7042 |
| A | score ≥ 3 | 1840 | 0,0713 | 0,1990 | 17 | 0,9744 |
| A | score ≥ 4 | 920 | 0,0746 | 0,2077 | 12 | 0,3225 |
| B | kriterium 1 sandt | 5156 | 0,1038 | 0,2985 | 44 | 0,7151 |
| B | score ≥ 2 | 7199 | 0,0955 | 0,2810 | 42 | 0,7723 |
| B | score ≥ 3 | 4660 | 0,1038 | 0,2985 | 44 | 0,5385 |
| B | score ≥ 4 | 2230 | 0,1194 | 0,3184 | 38 | 0,5888 |

## Efter kørslen — §12

Stop. Ingen ændring af definitioner, ingen nye varianter, ingen forslag. Resultatet læses sammen med ejeren, og §7 anvendes mekanisk.

Alle tal: `research/output/b4_k1_trin2.csv` (langt format: `spor`, `tabel`, `noegle`, `stoerrelse`, `vaerdi`).
