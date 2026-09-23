# B4 kandidat 1 — trin 2: de syv filtre, optælling

Kørt 2026-09-23 19:40 UTC fra commit `ca80a66`, med modul, tests, præregistrering, kilde og datalag committet og uændrede. Præregistrering `research/prereg/b4_k1_trin2_optaelling.md` (commit `feed022`), kilde `research/kilder/photon_sd_video_noter.md` (commit `feed022`). Kode `research/b4_k1_filtre.py` (commit `ca80a66`), kerne `research/b4_k1_optaelling.py` (commit `c18539f`), motor `research/b4_k1_trinA.py` (commit `feed022`).

Serie: MNQ.v.0 ohlcv-1m gennem `data.holdout.load_in_sample`, 2019-05-06 00:00 → 2023-12-29 21:59 UTC, 1638282 1m-barer. RTH-dage: 1173. Kerne v2 med buffer 10%; et signal er en berøring i indgangsvinduet hvor `kontrakter_ekte ≥ 1`.

**Kørslen ser ikke på udfald.** Ingen handel er simuleret, intet R er regnet, ingen tærskel er valgt, og intet er lagt til tælleren for den deflaterede tærskel. §5's grænse på 310 dage står i tabellerne som en aflæsning, ikke som et valg — varianterne vælges sammen med Mads efter §5.

## Regressionstjek, §4 — før kørslen

- `research/b4_k1_optaelling.py` gengiver `b4_k1_optaelling_v2.csv` byte for byte: **OK**.
- Spor A's signaler ved score ≥ 0 mod trin A-motorens kandidater for buffer 10%: 3349 mod 3349 zoner, **identiske**.

## Fire præciseringer, afklaret med Mads 2026-09-23 før kørslen

§3b's ordlyd er ikke ændret. Fire steder var den ikke entydig, og to steder var den bogstavelige læsning degenereret; andelene nedenfor er målt på MNQ-serien før spørgsmålet blev stillet.

1. **Kriterium 6, "et kendt HTF-swing high":** det *seneste* kendte, som i kriterium 1, 3 og 7. Bogstaveligt har 80,9% af 1h-lysene både et op- og et nedbrud i samme lys, så "nyere end" bliver uafgjort.
2. **Kriterium 2, tredje led:** lyset der lukker over S's top søges fra og med S's berøringslys til, men ikke med, zonens eget berøringslys. Uden nedre grænse er leddet sandt for 98,7% af lysene.
3. **Kriterium 2, vinduet:** S's første berøring ligger i `basis_i − 4 … basis_i`, altså også i selve basislyset.
4. **Kriterium 5:** kun HTF-zoner der stadig lever efter kerne v2 ved skæringen; en zone der er blevet ugyldig eller død ved kontraktskift stakker ikke.

## Spor A — handelstimeframe 15m, højere timeframe 60m

109598 15m-barer og 27551 60m-barer af den samme 1m-serie. 15650 zoner dannet, 3367 berørt i indgangsvinduet, heraf 18 afvist af `kontrakter_ekte ≥ 1`. Signaler: 3349.

### Spor A — filtrene

Antal sande og andel i procent med Wilson 95%-CI.

| kriterium | alle | demand | supply |
|---|---|---|---|
| 1. brud | 2011 — 60,0 (58,4–61,7) | 1067 — 59,7 (57,4–62,0) | 944 — 60,4 (58,0–62,8) |
| 2. flip | 325 — 9,7 (8,7–10,8) | 162 — 9,1 (7,8–10,5) | 163 — 10,4 (9,0–12,0) |
| 3. sweep | 503 — 15,0 (13,8–16,3) | 235 — 13,2 (11,7–14,8) | 268 — 17,2 (15,4–19,1) |
| 4. inducement | 1213 — 36,2 (34,6–37,9) | 680 — 38,1 (35,8–40,3) | 533 — 34,1 (31,8–36,5) |
| 5. stakket | 978 — 29,2 (27,7–30,8) | 512 — 28,7 (26,6–30,8) | 466 — 29,8 (27,6–32,1) |
| 6. retning | 1820 — 54,3 (52,7–56,0) | 1012 — 56,6 (54,3–58,9) | 808 — 51,7 (49,2–54,2) |
| 7. discount | 2241 — 66,9 (65,3–68,5) | 1137 — 63,6 (61,4–65,8) | 1104 — 70,7 (68,4–72,9) |

### Spor A — scorefordeling

| score | signaler_n | dage_med_signal_n | dage_med_signal_pct (CI95) |
|---|---|---|---|
| 0 | 36 | 33 | 2,8 (2,0–3,9) |
| 1 | 662 | 483 | 41,2 (38,4–44,0) |
| 2 | 811 | 576 | 49,1 (46,3–52,0) |
| 3 | 920 | 595 | 50,7 (47,9–53,6) |
| 4 | 609 | 440 | 37,5 (34,8–40,3) |
| 5 | 259 | 215 | 18,3 (16,2–20,6) |
| 6 | 48 | 44 | 3,8 (2,8–5,0) |
| 7 | 4 | 4 | 0,3 (0,1–0,9) |

### Spor A — kumulativt, score ≥ k

| score ≥ k | signaler_n | dage_med_signal_n | dage_med_signal_pct (CI95) | mindst 310 dage |
|---|---|---|---|---|
| ≥ 0 | 3349 | 1097 | 93,5 (92,0–94,8) | ja |
| ≥ 1 | 3313 | 1096 | 93,4 (91,9–94,7) | ja |
| ≥ 2 | 2651 | 1012 | 86,3 (84,2–88,1) | ja |
| ≥ 3 | 1840 | 883 | 75,3 (72,7–77,7) | ja |
| ≥ 4 | 920 | 585 | 49,9 (47,0–52,7) | ja |
| ≥ 5 | 311 | 251 | 21,4 (19,1–23,8) | nej |
| ≥ 6 | 52 | 47 | 4,0 (3,0–5,3) | nej |
| ≥ 7 | 4 | 4 | 0,3 (0,1–0,9) | nej |

### Spor A — brud på struktur alene

Signaler hvor kriterium 1 er sandt: 2011. `dage_med_signal_n`: 914 af 1173 RTH-dage, 77,9 (75,5–80,2)%.

### Spor A — samvariation, phi for alle 21 par

| par | phi |
|---|---|
| retning × discount | -0,479 |
| brud × inducement | 0,464 |
| inducement × discount | 0,296 |
| brud × stakket | 0,135 |
| brud × retning | 0,135 |
| sweep × discount | 0,127 |
| brud × flip | 0,099 |
| flip × discount | -0,082 |
| flip × stakket | 0,045 |
| sweep × stakket | 0,044 |
| flip × inducement | -0,043 |
| flip × retning | 0,043 |
| sweep × inducement | -0,037 |
| brud × sweep | -0,034 |
| stakket × retning | 0,031 |
| flip × sweep | -0,031 |
| inducement × stakket | 0,024 |
| stakket × discount | 0,023 |
| sweep × retning | -0,021 |
| brud × discount | 0,016 |
| inducement × retning | -0,015 |

### Spor A — omkostninger

Populationen er signalerne. `risiko_pt` er E − low (supply: high − E) på zonens rigtige historiske priser, trin A §4d. `zoner_i_vindue_n` og `afvist_kontrakter_nul_n` er før `kontrakter_ekte ≥ 1`.

| størrelse | alle | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|---|
| signaler_n | 3349 | 468 | 755 | 712 | 721 | 693 |
| risiko_pt_p10 | 7,4 | 4,0 | 8,0 | 8,3 | 15,7 | 9,1 |
| risiko_pt_p50 | 20,9 | 8,8 | 20,4 | 20,2 | 34,1 | 21,5 |
| risiko_pt_p90 | 55,3 | 20,6 | 50,8 | 52,2 | 75,1 | 49,8 |
| omk_R_netto_p10 | 0,0238 | 0,0637 | 0,0259 | 0,0252 | 0,0175 | 0,0264 |
| omk_R_netto_p50 | 0,0628 | 0,1493 | 0,0645 | 0,0650 | 0,0385 | 0,0612 |
| omk_R_netto_p90 | 0,1769 | 0,3252 | 0,1647 | 0,1587 | 0,0838 | 0,1447 |
| be_WR_pct_netto_p50 | 35,43 | 38,31 | 35,48 | 35,50 | 34,62 | 35,37 |
| kontrakter_p50 | 5,0 | 14,0 | 6,0 | 6,0 | 3,0 | 5,0 |
| kontrakter_p90 | 16,0 | 30,6 | 15,0 | 14,9 | 7,0 | 13,0 |
| kontrakter_maks | 50 | 50 | 50 | 37 | 34 | 37 |
| kontrakter_loftet_n | 8 | 6 | 2 | 0 | 0 | 0 |
| zoner_i_vindue_n | 3367 | 468 | 759 | 714 | 732 | 694 |
| afvist_kontrakter_nul_n | 18 | 0 | 4 | 2 | 11 | 1 |

### Spor A — kumulativt pr. år, `dage_med_signal_n`

| score ≥ k | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|
| ≥ 0 | 158 | 236 | 236 | 237 | 230 |
| ≥ 1 | 158 | 236 | 236 | 237 | 229 |
| ≥ 2 | 137 | 224 | 211 | 224 | 216 |
| ≥ 3 | 121 | 195 | 187 | 194 | 186 |
| ≥ 4 | 72 | 131 | 124 | 135 | 123 |
| ≥ 5 | 30 | 58 | 58 | 55 | 50 |
| ≥ 6 | 7 | 7 | 11 | 8 | 14 |
| ≥ 7 | 0 | 1 | 1 | 0 | 2 |

## Spor B — handelstimeframe 5m, højere timeframe 15m

328638 5m-barer og 109598 15m-barer af den samme 1m-serie. 45879 zoner dannet, 9277 berørt i indgangsvinduet, heraf 4 afvist af `kontrakter_ekte ≥ 1`. Signaler: 9273.

### Spor B — filtrene

Antal sande og andel i procent med Wilson 95%-CI.

| kriterium | alle | demand | supply |
|---|---|---|---|
| 1. brud | 5156 — 55,6 (54,6–56,6) | 2645 — 54,9 (53,5–56,3) | 2511 — 56,4 (54,9–57,8) |
| 2. flip | 930 — 10,0 (9,4–10,7) | 475 — 9,9 (9,0–10,7) | 455 — 10,2 (9,4–11,1) |
| 3. sweep | 1262 — 13,6 (12,9–14,3) | 631 — 13,1 (12,2–14,1) | 631 — 14,2 (13,2–15,2) |
| 4. inducement | 2994 — 32,3 (31,3–33,2) | 1583 — 32,8 (31,5–34,2) | 1411 — 31,7 (30,3–33,1) |
| 5. stakket | 2802 — 30,2 (29,3–31,2) | 1484 — 30,8 (29,5–32,1) | 1318 — 29,6 (28,3–31,0) |
| 6. retning | 4731 — 51,0 (50,0–52,0) | 2458 — 51,0 (49,6–52,4) | 2273 — 51,0 (49,6–52,5) |
| 7. discount | 6081 — 65,6 (64,6–66,5) | 3039 — 63,0 (61,7–64,4) | 3042 — 68,3 (66,9–69,7) |

### Spor B — scorefordeling

| score | signaler_n | dage_med_signal_n | dage_med_signal_pct (CI95) |
|---|---|---|---|
| 0 | 136 | 122 | 10,4 (8,8–12,3) |
| 1 | 1938 | 939 | 80,1 (77,7–82,2) |
| 2 | 2539 | 1021 | 87,0 (85,0–88,8) |
| 3 | 2430 | 971 | 82,8 (80,5–84,8) |
| 4 | 1590 | 818 | 69,7 (67,0–72,3) |
| 5 | 553 | 395 | 33,7 (31,0–36,4) |
| 6 | 84 | 80 | 6,8 (5,5–8,4) |
| 7 | 3 | 3 | 0,3 (0,1–0,7) |

### Spor B — kumulativt, score ≥ k

| score ≥ k | signaler_n | dage_med_signal_n | dage_med_signal_pct (CI95) | mindst 310 dage |
|---|---|---|---|---|
| ≥ 0 | 9273 | 1173 | 100,0 (99,7–100,0) | ja |
| ≥ 1 | 9137 | 1173 | 100,0 (99,7–100,0) | ja |
| ≥ 2 | 7199 | 1168 | 99,6 (99,0–99,8) | ja |
| ≥ 3 | 4660 | 1127 | 96,1 (94,8–97,0) | ja |
| ≥ 4 | 2230 | 942 | 80,3 (77,9–82,5) | ja |
| ≥ 5 | 640 | 443 | 37,8 (35,0–40,6) | ja |
| ≥ 6 | 87 | 83 | 7,1 (5,7–8,7) | nej |
| ≥ 7 | 3 | 3 | 0,3 (0,1–0,7) | nej |

### Spor B — brud på struktur alene

Signaler hvor kriterium 1 er sandt: 5156. `dage_med_signal_n`: 1139 af 1173 RTH-dage, 97,1 (96,0–97,9)%.

### Spor B — samvariation, phi for alle 21 par

| par | phi |
|---|---|
| retning × discount | -0,527 |
| brud × inducement | 0,520 |
| inducement × discount | 0,365 |
| sweep × discount | 0,177 |
| inducement × retning | -0,135 |
| brud × retning | 0,103 |
| brud × flip | 0,087 |
| sweep × retning | -0,080 |
| flip × discount | -0,074 |
| flip × sweep | -0,052 |
| brud × sweep | -0,051 |
| brud × stakket | 0,047 |
| flip × retning | 0,043 |
| stakket × discount | 0,034 |
| brud × discount | 0,031 |
| flip × stakket | -0,026 |
| sweep × stakket | 0,025 |
| sweep × inducement | -0,007 |
| inducement × stakket | -0,007 |
| flip × inducement | -0,005 |
| stakket × retning | -0,003 |

### Spor B — omkostninger

Populationen er signalerne. `risiko_pt` er E − low (supply: high − E) på zonens rigtige historiske priser, trin A §4d. `zoner_i_vindue_n` og `afvist_kontrakter_nul_n` er før `kontrakter_ekte ≥ 1`.

| størrelse | alle | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|---|
| signaler_n | 9273 | 1278 | 2038 | 2007 | 2056 | 1894 |
| risiko_pt_p10 | 5,0 | 2,5 | 5,8 | 5,5 | 9,9 | 6,6 |
| risiko_pt_p50 | 14,3 | 6,1 | 13,8 | 13,5 | 22,5 | 14,9 |
| risiko_pt_p90 | 35,5 | 14,0 | 35,0 | 32,2 | 47,9 | 31,8 |
| omk_R_netto_p10 | 0,0370 | 0,0937 | 0,0375 | 0,0408 | 0,0275 | 0,0413 |
| omk_R_netto_p50 | 0,0919 | 0,2171 | 0,0955 | 0,0975 | 0,0582 | 0,0885 |
| omk_R_netto_p90 | 0,2654 | 0,5307 | 0,2274 | 0,2388 | 0,1327 | 0,1990 |
| be_WR_pct_netto_p50 | 36,40 | 40,57 | 36,52 | 36,58 | 35,27 | 36,28 |
| kontrakter_p50 | 8,0 | 20,0 | 9,0 | 9,0 | 5,0 | 8,0 |
| kontrakter_p90 | 25,0 | 50,0 | 21,0 | 22,0 | 12,0 | 18,0 |
| kontrakter_maks | 50 | 50 | 50 | 50 | 50 | 50 |
| kontrakter_loftet_n | 152 | 119 | 13 | 9 | 1 | 10 |
| zoner_i_vindue_n | 9277 | 1278 | 2038 | 2007 | 2059 | 1895 |
| afvist_kontrakter_nul_n | 4 | 0 | 0 | 0 | 3 | 1 |

### Spor B — kumulativt pr. år, `dage_med_signal_n`

| score ≥ k | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|
| ≥ 0 | 167 | 253 | 252 | 251 | 250 |
| ≥ 1 | 167 | 253 | 252 | 251 | 250 |
| ≥ 2 | 167 | 252 | 252 | 247 | 250 |
| ≥ 3 | 159 | 245 | 245 | 240 | 238 |
| ≥ 4 | 135 | 206 | 200 | 202 | 199 |
| ≥ 5 | 66 | 100 | 91 | 106 | 80 |
| ≥ 6 | 11 | 17 | 20 | 18 | 17 |
| ≥ 7 | 1 | 0 | 0 | 1 | 1 |

## Forventningen, §6 — ikke et kriterium

§6 forventede at filter 5 og 6 samvarierer mest, at filter 4 er sandt oftest, at de fleste signaler har score 1-3, og at score ≥ 4 har færre end 310 dage på spor A. For spor B forventedes median `risiko_pt` omkring 12 point mod 21 på spor A, median `omk_R_netto` omkring 0,11 mod 0,063 og break-even-win-rate omkring 37% mod 35%.

- **Spor A:** phi(stakket, retning) = 0,031; det hyppigste filter er discount med 66,9%. Median `risiko_pt` 20,9 point, median `omk_R_netto` 0,0628, break-even-win-rate 35,43%, p10 `risiko_pt` 7,4 point med `omk_R_netto` p90 0,1769.
- **Spor B:** phi(stakket, retning) = -0,003; det hyppigste filter er discount med 65,6%. Median `risiko_pt` 14,3 point, median `omk_R_netto` 0,0919, break-even-win-rate 36,40%, p10 `risiko_pt` 5,0 point med `omk_R_netto` p90 0,2654.

## Efter kørslen

Stop. Ingen ændring af definitionerne, ingen valg af tærskler — det gøres sammen med Mads efter §5.

Alle tal, også de 21 phi-værdier og alle årstal: `b4_k1_trin2_optaelling.csv` (langt format: `tabel`, `periode`, `side`, `noegle`, `stoerrelse`, `vaerdi`).
