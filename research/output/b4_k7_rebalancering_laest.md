# B4 kandidat 7 — rebalancering, læst: række 1, T fryses. Gevinsten er en kriseedge

**Skrevet:** 2026-10-10 af overblikssessionen, efter kørslen og læst sammen med ejeren.
Tallene står i `b4_k7_rebalancering.md` og `.csv` (commit a620e77, kørt fra 4c5cc8e). Intet
er kørt igen. Alle tal er i $ pr. aktiv dag pr. MES-enhed ved dagens niveau (ES 7.800),
medmindre andet står.

## 1. Kan vi stole på tallene?

| tjek | resultat |
|---|---|
| Rækkefølgen af commits | præregistrering 5fb9ba5 → data 4f5c861 → modul e4ec483 → optælling ba3e5bf → tillæg 773c24e → diagnose 4c5cc8e → kørsel a620e77 |
| Kodeændring efter tillægget | kun diagnosen §9a (OLS med HC3) og dens test. Kontrolleret i diff'en |
| Tests og regressionstjek | hele suiten består (1.176). Kandidat 1–6 holder, også kandidat 6 med 902 nætter og $11,07 |
| Data | 1.949 af 1.951 handelsdage, 2 udelukket som i optællingen |

## 2. Afgørelsen efter §8: række 1

| variant | aktive dage | brutto $/dag | netto $/dag | CI95 netto $/dag | t_v | p_FWE |
|---|---|---|---|---|---|---|
| **T · tærskel** | 1.949 | 17,73 | **16,42** | **[3,43; 29,42]** | 2,66 | **0,006** |
| K · kalender | 556 | 13,85 | 9,40 | [−27,02; 45,82] | 0,86 | 0,331 |

- **Række 1 gælder.** T har p_FWE ≤ 0,05 og CI-nedre > 0. **T fryses.** K opfylder ingen
  af kravene og går ikke videre.
- **Ved $5,70 er rækken den samme:** T netto $16,06 [3,06; 29,05].
- Næste skridt efter §8: præregistrering af holdout-testen, korrelationen med kandidat 6 og
  ruinmodellen for de to sammen.

## 3. Hvad tallene viser

**Gevinsten kommer næsten kun fra uro:**

| periode | handelsdage | netto $/dag [CI95] | netto i alt $ |
|---|---|---|---|
| Hele perioden | 1.949 | 16,42 [3,43; 29,42] | cirka 32.000 |
| Marts 2020 | 22 | — | cirka 26.000 (81%) |
| Uden marts 2020 | 1.927 | 3,09 [−2,34; 8,52] | cirka 6.000 |
| 2020 | 252 | 109,06 [15,39; 202,73] | cirka 27.500 |
| 2022 | 251 | 17,58 [−2,70; 37,86] | cirka 4.400 |
| De seks andre år | 1.446 | cirka 0,08 | cirka 100 |

- **Skævheden er 14,9.** Den bedste dag er +$7.497, og den værste er −$1.902.
- **Det passer med mekanismen.** Rebalanceringen er størst, når aktier og obligationer har
  flyttet sig meget fra hinanden, og kvartalsskiftet i marts 2020 var netop sådan et
  tilfælde. Men statistisk er det én episode.
- **Det er ikke kun almindelig reversal.** Med dagens afkast i ES og ZN som kontrol er
  T's hældning −$49,65 pr. standardafvigelse [−84,17; −15,13]. Uden kontrol er den −$77,66.
  Også den regression vejes tungt af de urolige dage.
- **Efter artiklens prøve** (2023-03-18 → 2023-12-29, 198 dage) er netto −$3,04 [−13,46;
  7,38]. Det er for kort til at sige noget.
- **Markedets drift trak imod.** T var short 81% af dagene. Driftjusteret brutto er $22,11
  [9,14; 35,08].
- **Gevinsten kommer både om natten og i RTH:** brutto $10,80 [1,85; 19,75] om natten og
  $6,93 [−0,10; 13,96] i RTH.
- **Omkostningen betyder intet:** break-even er $60,42 pr. round trip i middel og $16,08
  ved CI-nedre, mod $4,45.
- **Nasdaq-kontrollen** viser samme mønster og er stærkere: netto $33,68 [11,70; 55,65] pr.
  MNQ, p 0,002, og uden marts 2020 $10,28 [−0,35; 20,91]. Den er ikke uafhængig: samme
  signal og samme periode.
- **Kandidat 6:** korrelationen er 0,147. Sharpe er 0,89 for T alene, 0,67 for kandidat 6 og
  1,03 for de to sammen ved lige risiko. Begge tal er skrøbelige: T's hviler på marts 2020,
  og kandidat 6 er ikke bevist.
- **Med hele MES** (round(w)) handles kun 168 dage, med netto $212,21 [64,11; 360,32] og
  uden marts 2020 $65,07 [0,43; 129,72]. Det er en diagnose og afgør intet.
- **K** viser intet: netto $9,40 [−27,02; 45,82] og ingen forskel på kvartalsslut og andre
  måneder.

## 4. Hvad det betyder for Topstep

T er en **kriseedge**: tæt på 0 i rolige år og store gevinster, når markedet er i uro. Det
har fire konsekvenser, som ruinmodellen skal regne på:

1. **Gebyrerne løber i de rolige år.** Seks af otte år gav cirka $0, mens gebyrerne i
   disciplinzonen er cirka $1.150 om året (edge-kravet).
2. **Konsistensreglen i Combine straffer store dage.** Målet hæves til bedste dag / 0,55. En
   dag som +$7.497 ville hæve målet til cirka $13.600.
3. **Positionen vokser i uroen.** w følger signalet, så T handler størst, når udsvingene er
   størst. Det største tab inden for dagen pr. MES-enhed var −$4.043. DLL'en på $1.000 kan
   lukke en dag, før gevinsten kommer.
4. **Den positive skævhed passer til XFA.** Udbetalingerne har intet loft over tid, og
   edge-kravet viste, at Topsteps regler belønner spredning. Det taler for T som
   supplement på en kørende konto og ikke som motor til at bestå Combine.

## 5. Næste skridt efter §8

1. **Præregistrering af holdout-testen** af T, uændret som frosset, på ES 2024–2026.
   - Data købes først, når præregistreringen er committet. Estimatet er cirka $7.
   - Holdout indeholder mindst to urolige perioder (august 2024 og april 2025). Testen kan
     altså vise, om T tjener i en krise, den ikke er tilpasset.
   - **Styrken er lav:** med cirka 690 dage og σ $293 er den cirka 45% ved in-sample-effekten
     ($16,42) og under 10%, hvis effekten kun er de $3 uden marts 2020.
   - Også holdout kan blive afgjort af få dage. Bedste dages andel skal rapporteres.
2. **Ruinmodellen** for T og for T + kandidat 6, på de faktiske dage og med Topsteps regler,
   herunder konsistensreglen og DLL'en.

Rækkefølgen og udformningen aftales med ejeren.

## 6. Status

| emne | status |
|---|---|
| Kandidat 7 | **T · tærskel frosset** 2026-10-10, række 1. K går ikke videre |
| Tælleren | 47 forsøg |
| Holdout for ES og ZN | ikke købt, uåbnet |
| Databudget | $56,65 af $120 brugt |
