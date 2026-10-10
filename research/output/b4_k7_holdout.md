# B4 kandidat 7 — holdout-testen af T · tærskel: resultat

**Kørt:** 2026-10-10 13:57 UTC fra `5dea18898f38`, frosset hypotese `research/prereg/b4_k7_holdout.md` (commit `70cb25ef284e`). Kandidat 7's modul uændret fra 4c5cc8e. R = 500. ES (MES-økonomi), $4,45, dagens niveau.

## Hovedtabel

| serie | aktive_dage_n | andel_long | brutto_usd_dag | netto_usd_dag | CI90_netto | CI95_netto | N_retning_p5/p50/p95 | p_H1 |
|---|---|---|---|---|---|---|---|---|
| holdout 2024-01-02 → 2026-09-30 | 689 | 15% | 1,198 | **-0,083** | [-9,93; 9,76] | [-11,82; 11,65] | -11,046/-1,261/8,887 | **0,429** |
| in-sample 2016-04-01 → 2023-12-29 | 1.949 | 19% | 17,730 | **16,424** | [5,52; 27,33] | [3,43; 29,42] | -11,856/-1,587/10,225 | **0,002** |

- **H1** (p_H1 ≤ 0,05 på holdout): **ikke bestået**, p_H1 = 0,429.
- **H2** (CI90-nedre > 0 på holdout): **ikke bestået**, CI90-nedre = -9,928.
- **§5 anvendt mekanisk:** række 4: Parkeres: T holdt ikke uden for artiklens prøve.
- **E_f** (énsidet 95%-nedre, in-sample og holdout samlet, n 2638): 3,654 (middel 12,113). E_f > 0: ja. Uden marts 2020: -1,982.

## Diagnoser (§7, afgør intet)

Grænsen for urolige måneder (in-sample p90 af månedlig sd af R^ES): 0,01576.

| diagnose | holdout | in-sample |
|---|---|---|
| uden urolige måneder | -2,778 [-9,88; 4,32] (n 668) | 0,377 [-4,08; 4,84] (n 1743) |
| kun urolige måneder | 85,648 [-251,16; 422,45] (n 21) | 152,199 [35,95; 268,45] (n 206) |
| bedste dags andel af netto i alt | -3157,0% | 23,4% |
| de 5% bedste dages andel | -20456,6% (n 35) | 193,8% (n 98) |
| netto uden de 5 bedste dage | -7,095 | 4,683 |
| før publiceringen (d < 2025-03-01) | -1,146 [-11,98; 9,69] (n 291) | 16,424 [3,43; 29,42] (n 1949) |
| efter publiceringen | 0,695 [-18,06; 19,45] (n 398) | — [—; —] (n 0) |
| andel long / short | 15% / 85% | 19% / 81% |
| driftjusteret brutto | 6,473 [-5,30; 18,25] (n 689) | 22,112 [9,14; 35,08] (n 1949) |
| long hele dagen, brutto / netto | 23,705 / 19,255 | 22,448 / 17,998 |
| brutto nat | -3,455 [-10,25; 3,34] (n 689) | 10,797 [1,85; 19,75] (n 1949) |
| brutto RTH | 4,653 [-4,65; 13,96] (n 689) | 6,933 [-0,10; 13,96] (n 1949) |
| netto ved $5,70 | -0,442 [-12,18; 11,29] (n 689) | 16,057 [3,06; 29,05] (n 1949) |
| nominelt | -0,485 [-9,03; 8,06] (n 689) | 5,030 [0,55; 9,51] (n 1949) |
| break-even pr. round trip, middel / CI-nedre | 4,163 / -36,638 | 60,421 / 16,081 |
| T med hele MES: aktive dage, netto [CI95] | 42, 38,848 [-119,63; 197,32] | 168, 212,215 [64,11; 360,32] |
| netto p1/p5/p50/p95/p99 | -278/-137/-4/146/355 | -324/-156/-1/190/618 |
| værste / bedste dag | -2314 / 1796 | -1902 / 7497 |
| σ pr. aktiv dag | 157 | 293 |
| skævhed | -1,50 | 14,92 |
| største tab i dagen pr. enhed p1/p5/p50/værst | -988/-660/-183/-2394 | -1307/-754/-175/-4043 |
| reversal: b_T uden kontrol $/sd [95%] | -26,546 [-82,07; 28,98] | -77,663 [-121,85; -33,48] |
| reversal: b_T med kontrol $/sd [95%] | -10,592 [-58,78; 37,59] | -49,653 [-84,17; -15,13] |
| reversal: b_E (ES' afkast på t) med kontrol | -31,024 [-92,34; 30,29] | -34,000 [-90,24; 22,25] |
| handelsdage / udelukkede | 689 / 0 | 1951 / 2 |
| forsinket indgang 1–5 min / udgang fra tidligere bar | 0 / 0 | 0 / 0 |
| manglende signalbarer ES / ZN | 0 / 0 | 0 / 7 |
| ruller i vinduet | 10 | 31 |

Udelukkede holdout-dage: ingen.

| år | aktive dage | brutto $/dag | netto $/dag [CI95] |
|---|---|---|---|
| 2024 (holdout) | 252 | -0,422 | -1,792 [-13,85; 10,26] |
| 2025 (holdout) | 250 | 4,934 | 3,679 [-24,45; 31,80] |
| 2026 (holdout) | 187 | -1,613 | -2,808 [-17,27; 11,65] |
| 2016 (in-sample) | 191 | 8,501 | 7,229 [-6,02; 20,48] |
| 2017 (in-sample) | 251 | -6,191 | -7,519 [-13,07; -1,96] |
| 2018 (in-sample) | 250 | 0,955 | -0,296 [-20,85; 20,26] |
| 2019 (in-sample) | 252 | 1,451 | 0,142 [-10,91; 11,19] |
| 2020 (in-sample) | 252 | 110,644 | 109,061 [15,39; 202,73] |
| 2021 (in-sample) | 252 | 1,852 | 0,467 [-10,17; 11,10] |
| 2022 (in-sample) | 251 | 18,786 | 17,581 [-2,70; 37,86] |
| 2023 (in-sample) | 250 | 3,267 | 2,164 [-8,14; 12,47] |
