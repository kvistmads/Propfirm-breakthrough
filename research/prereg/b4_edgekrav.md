# B4 — præregistrering: edge-kravet. Hvor stor skal en edge være, før Topstep giver plus?

**Skrevet:** 2026-10-09 af overblikssessionen, før kørslen. Committes før kørslen.
**Besluttet af ejeren 2026-10-09:** svar A ("regn baglæns").
**Baggrund:** efter seks kandidater og 45 forsøg er den bedste kandidat overnight drift
efter salgsdage, med en Sharpe på cirka 0,6 om året (ikke bevist). Fase 2's ruinmodel
antog en edge svarende til en Sharpe på cirka 1,9. Før vi leder videre, skal vi vide, hvor
stor en edge Topstep kræver.
**Dette er ikke en edge-test.** Der bruges ingen kursdata, og intet tæller i tælleren (45).
Præregistreringen fastlægger modellen og beslutningsreglen, før tallene ses.

---

## 1. Hvad modellen svarer på

For en strategi, der beskrives alene ved sin **årlige Sharpe netto efter
handelsomkostninger** og sin **daglige spredning i dollar**:

1. **Combine:** sandsynligheden for at bestå og tiden til det.
2. **XFA:** forventede udbetalinger, før kontoen lukker.
3. **Økonomien over ét år:** forventet nettoværdi = 90% af udbetalingerne minus alle
   gebyrer.
4. **Kravet:**
   - den mindste Sharpe, hvor den bedste størrelse giver **forventet nettoværdi > 0**;
   - den mindste Sharpe, hvor **første udbetaling kommer inden for 3 måneder (63
     handelsdage) med mindst 50% sandsynlighed**.

## 2. Reglerne i modellen

Alle står i `claude/REGLER_VERIFICERET.md` (verificeret 2026-09-13). Priserne er tjekket
igen 2026-10-09 på help.topstep.com.

| regel | værdi i modellen |
|---|---|
| Combine-mål | saldo ≥ max(3.000, bedste dag / 0,55), og mindst 2 handelsdage |
| Combine-MLL | $2.000 under højeste dagsslutsaldo. Låser ved startsaldoen, når dagsslut når +$2.000. **Brydes i realtid** |
| Combine-brud | Reset til **$49**. Combine starter forfra |
| DLL | **$1.000, slået til**, som ejeren har besluttet. Rammer dagen −$1.000, flades der, og dagen slutter på −$1.000. Det er ikke et brud. Rammes MLL først, er det et brud |
| Abonnement | **$49 pr. påbegyndt måned** (21 handelsdage), mens man er i Combine. Stopper, når man består |
| Aktivering | **$149, når man består** og får en XFA (Standard Path) |
| API | **$14,50 pr. måned** hele året, uanset fase |
| XFA-start | saldo $0 |
| XFA-MLL | $2.000 under højeste dagsslutsaldo. Låser ved $0, når saldoen når $2.000. **Brud lukker kontoen permanent** |
| Udbetaling (Standard) | efter **5 vindende dage à mindst $150 netto** siden sidste udbetaling: halvdelen af saldoen, højst **$4.000** (loftet er fordoblet med DLL), mindst $125. Den tages straks, når den er mulig |
| Efter udbetaling | saldoen falder med beløbet. MLL sættes til $0, og tælleren nulstilles |
| Profitdeling | 90% til ejeren |
| Efter XFA-lukning | et nyt Combine-forløb starter, hvis året ikke er gået |
| Ikke med | konsistensvejen på 40% i XFA (valgfri), LFA (skønsmæssig) og Back2Funded |

## 3. Strategien i modellen

- **Daglig P&L:** `X = μ + σ × Z`, hvor Z er en standardiseret Student-t med 4
  frihedsgrader (fede haler, varians 1).
- **μ** følger af Sharpe: `μ = S / √252 × σ`. Dage uden handel tæller med som 0 i Sharpe.
- **Bevægelsen inden for dagen** (MLL i realtid og DLL) trækkes som minimum af en
  Brownian bridge fra 0 til X med varians σ²:
  `M = (X − √(X² − 2σ² ln U)) / 2`, med U uniform på (0, 1].
- Dagene er uafhængige.
- **Størrelsen** vælges for hver Sharpe som den bedste kombination af σ_C i Combine og
  σ_X i XFA. Begge vælges fra gitteret $100, 150, 200, 250, 300, 400, 500, 600, 800 og
  1.000. **Ejerens disciplinzone**, σ ≤ $400, rapporteres for sig.
- **Sharpe-gitter:** −0,5, 0, 0,25, 0,5, 0,75, 1,0, 1,25, 1,5, 2,0, 2,5 og 3,0.
- **Horisont:** 252 handelsdage (ét år) fra første Combine-dag.
- **Stier:** 20.000 pr. celle, faste frø og common random numbers på tværs af celler.

## 4. Hvad der rapporteres pr. Sharpe

**Ved den bedste størrelse og i disciplinzonen:**
- σ_C og σ_X;
- P(bestå Combine) inden for 63, 126 og 252 dage;
- median dage til bestået;
- antal resets;
- P(mindst én udbetaling inden for 63 og 252 dage);
- forventet udbetaling til ejeren;
- forventede gebyrer;
- **forventet nettoværdi med 95%-interval**;
- P(nettoværdi > 0);
- 10%-fraktilen af nettoværdien.

**Kravet:**
- `S_min_EV` er den laveste Sharpe, hvor forventet nettoværdi er > 0. Det rapporteres både
  som punkt og som det sted, hvor 95%-intervallets nedre grænse er > 0. Der interpoleres
  lineært mellem gitterpunkterne.
- `S_hurtig` er den laveste Sharpe, hvor P(første udbetaling ≤ 63 dage) ≥ 50%.

**Referencepunkter** (placeres på kurven, afgør intet):

| reference | Sharpe | σ pr. dag pr. MNQ |
|---|---|---|
| Fase 2's antagelse (WR 40% ved 2:1, én handel om dagen) | cirka 1,9 | — |
| Kandidat 5 in-sample, 1m · uden middag | 1,17 | $559 |
| Kandidat 5 holdout | −1,04 | $464 |
| Kandidat 6, 07:30–09:30 efter salg (pr. kalenderdag) | 0,64 | $123 |
| Ingen edge, kun omkostning | under 0 | — |

## 5. Følsomhed — rapporteres, men afgør intet

- Normalfordelt Z og Student-t med 3 frihedsgrader;
- DLL slået fra (udbetalingsloftet er så $2.000);
- ingen bevægelse inden for dagen (kun dagsslut);
- horisont 126 dage;
- $95-planen uden aktiveringsgebyr.

## 6. Beslutningsreglen — hvad vi gør bagefter

Afgøres på `S_min_EV` ved punktestimatet, med horisont 252 dage og DLL slået til.

| nr | udfald | handling |
|---|---|---|
| 1 | `S_min_EV` ≤ 0,75 | **Svage edges kan betale sig.** Næste skridt: præregistrering af en holdout-test af overnight drift (NQ 2024–2026 er uåbnet for natten) og en søgning efter svage edges, der kan supplere |
| 2 | 0,75 < `S_min_EV` ≤ 1,5 | **Overnight drift alene er ikke nok.** Der skal en kombination af edges til, eller en stærkere edge. Næste skridt aftales med ejeren |
| 3 | `S_min_EV` > 1,5 | **Offentlige edges på Topstep er næppe vejen.** Næste skridt: undersøg et andet format (spor C: positioner over flere dage) |

**Hvis forventet nettoværdi er positiv allerede ved Sharpe 0**, rapporteres det særskilt:
det vil betyde, at regelgeometrien alene giver plus, og det skal læses sammen med Topsteps
regler om adfærd. Det ændrer ikke rækken.

## 7. Code's opgave: trin 1, og så stop

1. **Modul og tests:** `research/b4_edgekrav.py` og `tests/test_b4_edgekrav.py`.
   - Ingen kursdata, intet fra holdout.
   - `research/mll_ruin.py` må importeres, men ikke ændres.
2. **Tests, alle skal bestå:**
   1. **Brownian bridge-minimum:** den trukne fordeling stemmer med formlen
      (Kolmogorov-Smirnov) og med en finmasket random walk.
   2. **Gambler's ruin:** uden edge, uden trailing og med fine skridt rammer +3.000 før
      −2.000 med sandsynlighed cirka 0,40 (inden for simulationsusikkerheden).
   3. Grænsetilfælde: meget stor positiv edge giver bestået ≈ 1, meget negativ ≈ 0.
   4. **Combine-MLL:** trailing på dagsslut, låsning ved start og brud i realtid. DLL og MLL
      i den rigtige rækkefølge.
   5. **Konsistens:** målet hæves til bedste dag / 0,55.
   6. **XFA:**
      - vindende dage à $150;
      - 50% af saldoen, loft $4.000 og minimum $125;
      - MLL til $0 og ny tæller efter udbetaling;
      - låsning ved $0;
      - permanent lukning.
   7. **Gebyrer:** abonnement pr. påbegyndt 21-dages blok, reset $49, aktivering $149 og
      API $14,50 pr. måned.
   8. **Krydstjek mod `mll_ruin.py`:** med en diskret 2:1-fordeling (+2R / −1R) og
      konstant R skal Combine-beståelsesraten ligge inden for Wilson-intervallet fra
      `mll_ruin.py` ved samme indstilling. Kan `mll_ruin.py` ikke køres med konstant R,
      rapporteres det, og testen springes over.
3. **Regressionstjek:** hele testsuiten.
4. **Tidsmåling:** én celle med 20.000 stier og et skøn for hele gitteret.
5. **Stop.** Kørslen sker, når ejeren har godkendt.

## 8. Efter kørslen

Stop. Tabellerne i chatten: kravet, kurven over Sharpe og referencepunkterne. §6 anvendes
mekanisk og læses sammen med ejeren.

## Kilder

- `claude/REGLER_VERIFICERET.md` §3, §4 og §6
- Topstep, *Pricing and payment questions* (2026-10-09): $49/md, $149 aktivering "charged
  once per Express Funded Account (XFA) earned", reset $49 —
  https://help.topstep.com/en/articles/14289835-topstep-pricing-and-payment-questions
- Topstep, *TopstepX commissions and fees* (2026-10-09): MNQ $1,22 pr. round trip —
  https://help.topstep.com/en/articles/8284213-topstepx-commissions-and-fees
