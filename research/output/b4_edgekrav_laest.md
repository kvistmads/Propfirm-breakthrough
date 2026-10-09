# B4 — edge-kravet, læst: række 1, og en opdagelse om reglerne selv

**Skrevet:** 2026-10-09 af overblikssessionen, efter kørslen og læst sammen med ejeren.
Tallene står i `b4_edgekrav.md`, `b4_edgekrav_celler.csv` og JSON-filerne (commit e59b92a,
kørt fra e3d0b77). Intet er kørt igen.

## 1. Kan vi stole på tallene?

| tjek | resultat |
|---|---|
| Rækkefølgen af commits | præregistrering 9c085c6 → trin 1 8774973 → tillæg 63dd222 → kode e3d0b77 → kørsel e59b92a |
| Tests | alle består (1.157), også betalingsreglen og interpolationen |
| Krydstjek | gambler's ruin 0,4004 mod 0,40, og `mll_ruin.py` inden for Wilson-intervallet |
| Bedste celle på nye stier | $41–$300 *mere* end på valgstierne. Optimismen fra at vælge den bedste af 100 celler er altså mindre end forskellen mellem to sæt frø |
| Rapportscriptet | ligger stadig i Code's scratchpad. De rå resultater (CSV og JSON) er committet, så tallene kan genskabes. Scriptet bør committes |

## 2. Afgørelsen efter §6: række 1

| kurve | S_min_EV | række |
|---|---|---|
| Bedste størrelse | ≤ −0,50 | 1 |
| Disciplinzonen (σ ≤ $400) | 0,16 | 1 |

**Række 1 gælder begge veje: svage edges kan betale sig.** Næste skridt efter §6 er en
præregistreret holdout-test af overnight drift og en søgning efter svage edges, der kan
supplere.

## 3. Opdagelsen: reglerne giver plus i forventning uden edge

Ved den bedste størrelse er forventet nettoværdi positiv allerede ved Sharpe 0 ($1.020) og
−0,5 ($165).

**Hvorfor:**
- Tabet er loftet af gebyrerne, cirka $1.900 om året.
- Gevinsterne tages ud løbende som udbetalinger og har intet loft.
- Det virker som en option, og en option er mest værd ved stor spredning. Derfor ligger den
  bedste størrelse på kanten af gitteret: σ_C = $1.000, lige så stor som DLL'en.

**Det er ikke en plan:**

| forbehold | tal |
|---|---|
| Det mest sandsynlige udfald er et tab | ved Sharpe 0 er P(netto > 0) 48%. 10%-fraktilen er −$1.846 |
| Adfærden kan straffes | 15–19 resets om året, og DLL'en rammes ofte. Topstep nævner "gentagne brud på DLL" og "activity that resembles gambling", og sanktionerne går til nægtet udbetaling. Modellen kan ikke prissætte den regel |
| Tallet er skrøbeligt | uden bevægelse inden for dagen: $8.160. Med fede haler (t3): $516. Uafhængige dage uden klynger af dårlige dage er en optimistisk antagelse |
| Ingen grænse opad | optimum ligger på gitterets kant. Modellen belønner mere risiko, end vi har testet |

**Konklusion:** plusset er en egenskab ved Topsteps regler, ikke en edge. Det bruges ikke
som strategi.

## 4. Hvilken kurve skal styre: disciplinzonen

**Anbefaling: disciplinzonen** (σ ≤ $400 pr. dag). Tre grunde:
1. **Ejerens egne regler:** $250 risiko pr. handel og "skal se disciplineret ud".
2. **Topsteps adfærdsregler:** den store størrelse giver præcis det mønster, der kan koste
   udbetalinger.
3. **Robusthed:** tallene ved den store størrelse afhænger mest af de antagelser, vi er
   mindst sikre på.

**Hvad disciplinzonen siger om økonomien (1 konto, 1 år):**

| Sharpe | eksempel | EV netto $ | P(netto > 0) | første udbetaling ≤ 63 dage | gebyrer $ |
|---|---|---|---|---|---|
| 0 | ingen edge | −141 | 27% | 17% | 1.138 |
| 0,64 | kandidat 6 (punkt) | cirka 560 | cirka 43% | cirka 25% | cirka 1.150 |
| 1,0 | — | 1.108 | 54% | 31% | 1.159 |
| 1,17 | kandidat 5 in-sample | 1.421 | cirka 58% | cirka 34% | cirka 1.160 |
| 2,0 | fase 2's antagelse | 3.411 | 80% | 49% | 1.153 |

- **En svag edge giver beskedne penge,** og et tabsår er stadig sandsynligt.
- **For hurtige penge skal Sharpe op omkring 2.** Så er der cirka 50% chance for første
  udbetaling inden for 3 måneder.
- **Svage edges kan lægges sammen.** Flere uafhængige edges med Sharpe 0,64 giver cirka
  0,90 (2 edges), 1,11 (3) og 1,28 (4), hvis de er lige store og ukorrelerede. Det er
  grunden til, at §6 peger på at søge edges, der kan supplere.

## 5. Næste skridt efter §6 række 1

1. **Præregistrering af holdout-testen af overnight drift** (NQ 2024–2026, natten
   uåbnet).
   - **Forbehold:** testen har lav styrke. Med cirka 305 salgsnætter og en sand gevinst på
     $11 pr. nat er styrken cirka 25–30% for netto over 0.
   - Præregistreringen skal tage stilling til det, som ved kandidat 5's holdout.
2. **Søgning efter svage edges, der kan supplere**, med mekanisme først som i screeningen.

Rækkefølgen aftales med ejeren.

## 6. Status

| emne | status |
|---|---|
| Edge-kravet | **Række 1**, 2026-10-09. Disciplinzonen anbefales som styrende kurve |
| Tælleren | 45 (edge-kravet tæller ikke) |
| Rapportscriptet | bør committes af Code |
