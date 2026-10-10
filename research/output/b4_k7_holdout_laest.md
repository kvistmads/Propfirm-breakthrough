# B4 kandidat 7 — holdout-testen af T, læst: række 4, T parkeres

**Skrevet:** 2026-10-10 af overblikssessionen, efter kørslen og læst sammen med ejeren.
Tallene står i `b4_k7_holdout.md` og `.csv` (commit c67119d, kørt fra 5dea188). Intet er
kørt igen. Alle tal er i $ pr. aktiv dag pr. MES-enhed ved dagens niveau (ES 7.800),
medmindre andet står.

## 1. Kan vi stole på tallene?

| tjek | resultat |
|---|---|
| Rækkefølgen | præregistrering 70cb25e → data, modul og tests 5dea188 → kørsel c67119d |
| Kodeændring efter trin 1 | ingen. Kørsel-commit'en indeholder kun rapporten og loggen |
| Holdout-loggen | to linjer for `b4_k7_holdout.md` (ES og ZN, 13:58:05 og 13:58:07). Det er én åbning |
| NQ | urørt. Kandidat 6's natholdout er stadig uåbnet |
| Data | 689 handelsdage, ingen udelukket, ingen manglende signalbarer, 10 ruller i vinduet |

## 2. Afgørelsen efter §5: række 4

| serie | aktive dage | brutto $/dag | netto $/dag | CI90 netto $/dag | p_H1 |
|---|---|---|---|---|---|
| **holdout** 2024-01-02 → 2026-09-30 | 689 | 1,20 | **−0,08** | [−9,93; 9,76] | **0,429** |
| in-sample 2016-04-01 → 2023-12-29 | 1.949 | 17,73 | 16,42 | [5,52; 27,33] | 0,002 |

- **H1 (retningen): ikke bestået.** p 0,429.
- **H2 (netto): ikke bestået.** CI90-nedre −$9,93.
- **Række 4: T parkeres.** T holdt ikke uden for artiklens prøve.
- E_f for de to samlet er $3,65, men uden marts 2020 −$1,98. Den ændrer ikke rækken.

## 3. Hvad tallene viser

**Uden for uro tjener T ingenting, hverken in-sample eller på holdout:**

| periode | holdout netto $/dag [CI95] | in-sample netto $/dag [CI95] |
|---|---|---|
| uden urolige måneder | −2,78 [−9,88; 4,32] (n 668) | 0,38 [−4,08; 4,84] (n 1.743) |
| kun urolige måneder | 85,65 [−251,16; 422,45] (n 21) | 152,20 [35,95; 268,45] (n 206) |

- **In-sample kom hele gevinsten fra 10 urolige måneder.** Holdout havde kun én urolig
  måned. Den gav plus, men med et interval fra −$251 til +$422 pr. dag. Den kan hverken
  bekræfte eller afvise.
- **Profilen vendte.** In-sample var skævheden +14,9, og den bedste dag var +$7.497.
  På holdout er skævheden −1,50, den værste dag er −$2.314, og den bedste er +$1.796.
  Gevinsten i stød, som var hele idéen, kom ikke.
- **Signalet mistede sin forudsigelse.** Med dagsafkastet som kontrol er hældningen
  −$10,59 pr. sd [−58,78; 37,59] mod −$49,65 [−84,17; −15,13] in-sample.
- **Publiceringen forklarer det ikke:** −$1,15 før marts 2025 og +$0,70 efter.
- **Markedets drift trak imod.** T var short 85% af dagene i et stigende marked. Long hele
  dagen gav $19,26 netto. Men også driftjusteret er brutto kun $6,47 [−5,30; 18,25].
- **Pr. år:** 2024 −$1,79, 2025 +$3,68, 2026 −$2,81. Alle intervaller krydser 0.

## 4. Hvad det betyder

- **Rebalanceringseffekten kan ikke bruges på Topstep i vores form.** Med kun aktiebenet i
  Topstep-dagen er der ingen effekt på almindelige dage, og effekten i uro er én episode
  in-sample og ubekræftet bagefter.
- **In-sample-fund, skrevet op:** in-sample tjente T i urolige måneder ($152,20 pr. dag
  [35,95; 268,45]). Det er valgt på data og kan kun testes med egen præregistrering og rene
  data. Der er ingen rene ES-data tilbage, og urolige måneder er sjældne. Det er derfor ikke
  testbart inden for en rimelig tid.
- **Mønstret fra kandidat 5 gentager sig:** to publicerede edges klarede in-sample og faldt
  på holdout.

## 5. To ting at tage stilling til senere

1. **Beslutningsreglen kan udløses af én episode.** Kandidat 7 nåede række 1 på marts 2020.
   "Uden marts 2020" stod i præregistreringen, men kun som diagnose. Om fremtidige
   præregistreringer skal kræve, at resultatet også holder uden den bedste måned, aftales
   med ejeren.
2. **Holdout-data, der nu er set:**
   - ES og ZN 2024–2026 er ikke længere rene for rebalancering, reversal og drift over
     hele dagen på ES. Long hele dagen og de urolige måneder er rapporteret.
   - MNQ 2024–2026 er set for VWAP-retningen i RTH (kandidat 5).
   - NQ 2024–2026 er uåbnet.

## 6. Status

| emne | status |
|---|---|
| Kandidat 7 | **Parkeret** 2026-10-10, holdout række 4. K gik ikke videre in-sample |
| Tælleren | 47 forsøg. Holdout tæller ikke |
| Databudget | $63,49 af $120 brugt |
| Næste | aftales med ejeren. Ingen forslag, før resultatet er læst |
