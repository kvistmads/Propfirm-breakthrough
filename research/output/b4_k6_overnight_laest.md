# B4 kandidat 6 — overnight drift, læst: række 2, kandidat 6 parkeres

**Skrevet:** 2026-10-09 af overblikssessionen, efter kørslen og læst sammen med ejeren.
Tallene står i `b4_k6_overnight.md` og `.csv` (commit 2ae6129, kørt fra 583dfd9). Intet
er kørt igen. Alle tal er i $ pr. nat pr. MNQ ved dagens niveau (NQ 29.138), medmindre
andet står.

## 1. Kan vi stole på tallene?

| tjek | resultat |
|---|---|
| Rækkefølgen af commits | præregistrering 50c03ba → kode 2f48756 → optælling a8cd76b → tillæg 583dfd9 → kørsel 2ae6129 |
| Kodeændring efter optællingen | ingen. Modulet er det samme som i a8cd76b, kontrolleret |
| Regressionstjek | OK før kørslen, kandidat 1–5 |
| Data | 2.011 af 2.012 nætter, 0 ruller i vinduerne, som i optællingen |
| Rapportfilen | en tom overskrift under "Datakvalitet", og tillægget mangler i commit-tabellen. Kosmetisk, ændrer intet |

## 2. Afgørelsen efter §8: række 2

| variant | nætter | brutto $ | netto $ | CI95 netto $ | N-nat p50 $ | t_v | p_FWE |
|---|---|---|---|---|---|---|---|
| 08–09 · alle | 2.011 | 5,11 | 2,26 | [−2,70; 7,22] | −1,79 | 1,52 | 0,168 |
| 08–09 · efter salg | 902 | 6,60 | 3,75 | [−3,86; 11,36] | −1,88 | 1,30 | 0,228 |
| 07:30–09:30 · alle | 2.011 | 8,08 | 5,23 | [−2,67; 13,13] | −1,43 | 2,01 | 0,072 |
| **07:30–09:30 · efter salg** | 902 | 13,92 | **11,07** | **[−0,95; 23,09]** | −1,72 | 2,29 | **0,044** |

- **Række 1 gælder ikke.** Ingen variant har både p_FWE ≤ 0,05 og CI-nedre > 0.
- **Række 2 gælder.** 07:30–09:30 · efter salg slår en tilfældig nattetime (p 0,044), men
  dens netto-interval rører 0. **Kandidat 6 parkeres som "timen er særlig, men betaler ikke
  omkostningen".**
- Ingen variant har CI-nedre > 0, så der er ingen in-sample-fund at skrive op.
- **Ved $3,10 er rækken den samme.**

## 3. Hvad tallene viser

- **Retningen er den, artiklen fandt.**
  - Alle fire varianter er positive brutto.
  - Varianten efter salg er stærkest.
  - Tilfældige nattetimer ligger omkring 0 brutto (N-nat p50 cirka −$1,7 netto).
- **Effekten er lille og kan ikke skilles sikkert fra omkostningen.**
  - Hit ratio er 49–53%, og gevinst/tab er 1,0–1,1.
  - Det er en svag skævhed, ikke et tydeligt mønster.
- **Diagnoserne peger i forskellige retninger** (afgør intet):

| diagnose | 07:30–09:30 · efter salg | 08–09 · efter salg |
|---|---|---|
| netto før 2020-03 [CI95] | 2,20 [−11,47; 15,87] | 6,19 [−2,10; 14,48] |
| netto efter 2020-03 [CI95] | 20,80 [0,52; 41,08] | 1,08 [−12,07; 14,23] |
| brutto efter de største salg (−1,5%) [CI95] | 35,36 [7,52; 63,21] | 11,02 [−6,29; 28,32] |
| brutto efter mellemstore salg (−0,55%) [CI95] | −5,94 [−23,23; 11,35] | −1,04 [−12,69; 10,60] |
| brutto efter de mindste salg (−0,15%) [CI95] | 12,26 [−2,69; 27,22] | 9,81 [0,39; 19,23] |

  - Det lange vindue blev stærkere efter publiceringen, og det korte blev svagere. Det
    ligner støj mere end et mønster.
  - **De største salg giver det største bounce** i det lange vindue, som artiklen forudsiger.
    Men det mellemste tercil er negativt, så stigningen er ikke jævn.
- **Kontrolserien MNQ 2019–2023** ville have givet række 1 for 07:30–09:30 · efter salg:
  netto $20,51 [2,66; 38,36] og p 0,012.
  - Det er **ikke uafhængigt bevis.** MNQ og NQ følger samme indeks, og 2019–2023 er den
    del af NQ-perioden, hvor varianten var stærkest.
  - Efter præregistreringen afgør MNQ intet.
- **Hele natten** (17:00 → 08:30 CT) giver $14,97 netto [−5,38; 35,31]. Natten driver
  generelt opad, men med for stor spredning til at være sikker.
- **Risikoen pr. MNQ er lille:** værste nat −$938 og værste tab inden for vinduet −$1.067.
  Det er under halvdelen af Topsteps MLL.

## 4. Hvad det betyder

- **Mekanismen ser ud til at findes på Nasdaq-futures,** men in-sample kan den ikke
  bevises efter omkostning. Tættest på kom 07:30–09:30 efter salg, med en nedre grænse på
  −$0,95.
- **Diagnoserne kan ikke redde den.** Perioden efter 2020 og de største salg er
  delmængder fundet i data. En hypotese bygget på dem ville være valgt på in-sample og
  skulle testes på rene data med egen præregistrering og fuld tæller.
- **Rene data for natten findes stadig:**
  - NQ-holdout 2024–2026 er uåbnet.
  - MNQ-holdout er åbnet én gang, men kun for RTH (kandidat 5).

## 5. Status

| emne | status |
|---|---|
| Kandidat 6 | **Parkeret** 2026-10-09, række 2 |
| Tælleren | 45 forsøg |
| Holdout for natten | uåbnet for NQ. MNQ åbnet én gang, kun RTH set |
| Næste | aftales med ejeren. Ingen forslag, før resultatet er læst |
