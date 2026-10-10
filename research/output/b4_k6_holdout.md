# B4 kandidat 6 — holdout-testen af V2 · salg: resultat

**Kørt:** 2026-10-10 20:59 UTC fra `c4cf0c705d05`, frosset hypotese `research/prereg/b4_k6_holdout.md` (commit `d4b4c4c12128`). Kandidat 6's modul uændret fra 583dfd9. R = 500. NQ.v.0, MNQ-økonomi, $3,10 pr. round trip, dagens niveau. Kun V2 · salg og dens N-nat (§7).

## Hovedtabel

| serie | naetter_n | brutto_usd_nat | netto_usd_nat | CI90_netto | CI95_netto | N_nat_p5/p50/p95 | p_H1 |
|---|---|---|---|---|---|---|---|
| holdout 2024-01-02 → 2026-09-30 | 324 | 9,672 | **6,572** | [-9,56; 22,70] | [-12,67; 25,81] | -11,673/2,078/16,526 | **0,325** |
| in-sample 2016-01-04 → 2023-12-29 | 902 | 13,918 | **10,818** | [0,73; 20,90] | [-1,20; 22,84] | -11,698/-1,968/7,666 | **0,020** |

- **H1** (p_H1 ≤ 0,05 på holdout): **ikke bestået**, p_H1 = 0,325.
- **H2** (CI90-nedre > 0 på holdout): **ikke bestået**, CI90-nedre = -9,558.
- **§5 anvendt mekanisk:** række 4: Parkeres for godt: driften efter salgsdage holdt ikke efter 2023.
- **E_f** (énsidet 95%-nedre, in-sample og holdout samlet, n 1226): 1,149 ved $3,10 (middel 9,696), 1,399 ved $2,85. E_f > 0: ja.

## Diagnoser (§7, afgør intet)

| diagnose | holdout | in-sample |
|---|---|---|
| netto ved $2,85 | 6,822 [-12,42; 26,06] (n 324) | 11,068 [-0,95; 23,09] (n 902) |
| nominelt ved $3,10 | 4,966 [-9,46; 19,39] (n 324) | 2,396 [-1,79; 6,58] (n 902) |
| break-even pr. round trip, middel / CI-nedre | 9,672 / -9,565 | 13,918 / 1,899 |
| bedste nats andel af netto i alt | 67,0% | 11,8% |
| de 5% bedste nætters andel | 355,1% (n 17) | 227,5% (n 46) |
| netto uden de 5 bedste nætter | -5,732 | 5,337 |
| netto uden den bedste kalendermåned | 0,987 (uden 2025-04) | 9,221 (uden 2021-03) |
| hit ratio / gevinst-tab | 51,2% / 1,07 | 53,3% / 1,05 |
| netto p1/p5/p50/p95/p99 | -446/-214/3/232/423 | -525/-259/11/294/639 |
| værste / bedste nat | -684 / 1426 | -872 / 1154 |
| σ pr. nat | 176 | 184 |
| største tab i vinduet p1/p5/p50/værst | -553/-298/-72/-1294 | -605/-351/-68/-956 |
| andel salgsnætter | 47,1% (324 / 688) | 44,9% (902 / 2010) |
| nætter / udelukkede | 689 / 1 | 2012 / 1 |
| forsinkede udførelser (ind / ud) | 0 (0 / 0) | 11 (11 / 1) |
| ruller i vinduet | 0 | 0 |

Udelukkede holdout-nætter: 2025-11-28 (ingen barer i et vindue).

| år | nætter | brutto $/nat | netto $/nat [CI95] |
|---|---|---|---|
| 2024 (holdout) | 118 | -8,263 | -11,363 [-33,19; 10,46] |
| 2025 (holdout) | 112 | 20,300 | 17,200 [-24,75; 59,15] |
| 2026 (holdout) | 94 | 19,524 | 16,424 [-18,47; 51,32] |
| 2016 (in-sample) | 114 | -0,854 | -3,954 [-29,36; 21,45] |
| 2017 (in-sample) | 104 | -3,507 | -6,607 [-20,84; 7,62] |
| 2018 (in-sample) | 125 | 14,843 | 11,743 [-19,17; 42,66] |
| 2019 (in-sample) | 112 | 3,212 | 0,112 [-28,92; 29,15] |
| 2020 (in-sample) | 107 | 31,623 | 28,523 [-28,48; 85,53] |
| 2021 (in-sample) | 109 | 19,933 | 16,833 [-13,00; 46,67] |
| 2022 (in-sample) | 131 | 26,103 | 23,003 [-18,81; 64,81] |
| 2023 (in-sample) | 100 | 18,256 | 15,156 [-9,94; 40,25] |
