# B4 — screening 2: edges der kan supplere overnight drift

**Skrevet:** 2026-10-09 af overblikssessionen, efter ejerens svar på edge-kravet:
- **1A:** disciplinzonen (σ ≤ $400 pr. dag) styrer.
- **2A:** søg først efter svage edges, der kan supplere overnight drift.

**Ejerens mål:** en samlet Sharpe på mindst 1, gerne 2.

---

## 1. Hvad der skal til

Uafhængige edges lægges sammen omtrent som Sharpe × √antal, hvis de er lige store og
ukorrelerede. Kandidat 6 (overnight drift) ligger på cirka 0,64.

| samlet Sharpe | antal edges à 0,64 | eller fx |
|---|---|---|
| cirka 1,0 | 2–3 | overnight drift + én edge på cirka 0,8 |
| cirka 1,3 | 4 | — |
| cirka 2,0 | cirka 10 | eller 2–3 edges på hver cirka 1,2 |

**Ærligt:** Sharpe 1 er et realistisk mål med 2–3 gode, uafhængige edges. Sharpe 2 kræver
enten mange edges eller nogle, der er markant stærkere end dem, vi har fundet.

## 2. Filtrene

Filtrene fra screening 1 (F1–F5) gælder stadig: hvem betaler, Topstep og instrument,
styrke, omkostning og rene data. Der kommer to nye til:

| nr | filter | spørgsmål |
|---|---|---|
| F6 | Diversificering | Handler den på andre tider, dage eller markeder end overnight drift, så gevinsterne ikke kommer på samme dage? |
| F7 | Disciplinzonen | Kan den handles i små nok størrelser til, at den samlede σ holder sig under $400 pr. dag? |

Topstep tillader blandt andet MES, MNQ, MGC (mikroguld), M6E (mikroeuro), MCL og ZN
(10-årig statsobligation, kun fuld størrelse). Kontrakter markeret med * har særlige
restriktioner (help.topstep.com, "When and what products can I trade").

## 3. Screeningen

| mekanisme | F1 hvem betaler | F2 Topstep | F3 styrke | F4 omkostning | F5 rene data | F6 | F7 | samlet |
|---|---|---|---|---|---|---|---|---|
| **A. Rebalancering (Harvey, Mazzoleni og Melone 2025)** | ja: pensionskasser og fonde, der skal rebalancere | ja, aktiebenet via MES/MNQ inden for én Topstep-dag | middel–høj | ja: cirka 16 bp mod cirka 0,5–1 bp | ja, men prøven overlapper artiklens | ja, andre dage og en anden betingelse | ja | **anbefales som kandidat 7** |
| B. Auktionscyklus i statsobligationer (Lou, Yan og Zhang 2013) | ja: primary dealers med begrænset balance | delvis: kun ZN i fuld størrelse, og mønsteret varer flere dage | middel | tvivlsom: cirka 1,8 bp pr. handel | ukendt efter 2013 | ja | svær: 1 ZN fylder cirka hele zonen | lav, kræver mere research |
| C. Valuta svækkes i egen handelstid (Breedon og Ranaldo) | ja: lokale nettokøbere af fremmed valuta | ja, M6E | middel | **nej:** én tick på M6E er cirka 0,86 bp, så en round trip koster cirka 2 bp mod en effekt på få bp | ukendt | ja | ja | lav, omkostningen dræber den formentlig |
| D. Guld stiger om natten | svag: ingen klar betaler, og det er mest guldets egen stigning | ja, MGC | middel | ja | kun praktikere og kinesiske data | ja | ja | lav |
| E. Overnight drift på ES | samme som kandidat 6 | ja | — | — | — | **nej:** ES og NQ følges for tæt | — | lav som supplement |
| F. Intradag-momentum i obligationer og råvarer (Baltussen m.fl. 2021) | ja: afdækning | ja | middel | ukendt | publiceret 2021, og aktiedelen er væk | ja | ja | lav–middel, kræver mere research |

### A. Rebalancering — anbefales som kandidat 7

**Kilde:** Harvey, Mazzoleni og Melone, *The Unintended Consequences of Rebalancing*
(NBER w33554, 2025; arbejdspapir dateret januar 2026, præsenteret ved AFA 2026). Ikke
fagfællebedømt endnu.

**Mekanismen (F1):**
- Pensionskasser og fonde holder fx 60% aktier og 40% obligationer.
- Har aktierne klaret sig bedre end obligationerne, skal de sælge aktier og købe
  obligationer for at komme tilbage til målet.
- Det sker enten ved månedens slutning (kalender) eller, når vægten driver for langt
  (tærskel).
- Flowet er **tvunget og forudsigeligt**. Dem, der handler før det, får betaling.

**Hvad de fandt** (S&P 500- og 10-årige statsobligationsfutures, 1997–2023):
- En stigning på 1 standardafvigelse i signalet giver **cirka 16–17 bp lavere afkast i
  aktier næste dag**, og 2–4 bp højere i obligationer.
- **Kalendersignalet** virker i månedens sidste fire dage og mest ved kvartalsslut.
  Presset vender inden for cirka to uger.
- **Long-short-strategien:** Sharpe 1,11 før og cirka 1 efter omkostninger.
  - Skævhed 5,2: gevinsten kommer i stød, mest i urolige perioder.
  - Uden 2008–2009 og marts 2020 er Sharpe 0,90.
- Ifølge en fodnote blev effekten "endnu stærkere", da testen blev forlænget til 2025.

**Hvorfor den passer:**
- **F2:** aktiebenet kan handles med MES eller MNQ inden for én Topstep-dag (17:00 → 15:10
  CT). Obligationsbenet (ZN) er for stort til disciplinzonen og droppes.
- **F4:** 16 bp ved NQ 29.138 er cirka $93 pr. MNQ pr. signal-standardafvigelse, mod cirka
  $2,6–2,9 i omkostning.
- **F6:** signalet bygger på aktier mod obligationer og handler især omkring månedens
  slut. Overnight drift handler efter salgsdage i timen omkring Europas åbning. De to
  burde kun overlappe lidt. Korrelationen måles i testen.

**Forbehold:**
- **Prøven overlapper artiklens.** Vores in-sample er 2016–2023, artiklens prøve går til
  marts 2023. Holdout 2024–2026 ligger omkring publiceringen (2025).
- **Data skal købes:**
  - S&P 500-futures (ES) og 10-årige statsobligationsfutures (ZN) til signalet;
  - ES 1m til handlen, hvis vi følger artiklen.
  - Det er sandsynligvis et mindre beløb, og estimatet tjekkes først.
- **Gevinsten kommer i stød.** Det betyder noget for Topsteps MLL og skal med i
  ruinmodellen.
- **Kun aktiebenet:** artiklens Sharpe gælder for long-short. Aktiebenet alene er
  formentlig svagere, og det skal testen vise.

### Hvorfor de andre ikke anbefales nu

- **B (auktioner):** mekanismen er god, men mønsteret varer flere dage, og ZN fylder hele
  disciplinzonen. Mere research før en test.
- **C (valuta):** omkostningen i bp er for høj på M6E til en effekt på få bp.
- **D (guld):** ingen klar betaler. Det ligner mest guldets egen stigning de seneste år.
- **E (ES-overnight):** følges for tæt med kandidat 6 til at sprede risikoen.
- **F (momentum i andre markeder):** muligt, men publiceret 2021 og forsvundet i aktier.
  Mere research.

## 4. Spørgsmål til kandidat 7 — rebalancering

Anbefalingen står først.

**1. Instrument**
- **A: signal og handel som i artiklen.**
  - Signalet bygges af ES og ZN.
  - Der handles på ES (MES på Topstep).
  - MNQ køres som kontrol.
  - Kræver køb af ES- og ZN-data (estimat først).
- B: kun NQ/MNQ, som vi har. Signalet kan så ikke bygges som i artiklen.

**2. Signaler**
- **A: kalender og tærskel som to varianter, som i artiklen.**
- B: kun kalender (månedens sidste dage).

**3. Holdeperiode**
- **A: hele Topstep-dagen efter signalet**, fra kl. 17:00 til 15:08 CT. Det er tættest på
  artiklens "næste dag".
- B: kun RTH.

**4. Retning**
- **A: kun short aktier, når aktierne er overvægtede, og long, når de er undervægtede**,
  vægtet efter signalets styrke som i artiklen.
- B: kun handel, når signalet er stærkt (over en grænse sat på forhånd).

**5. Nulmodel**
- **A: samme dage og samme størrelse, men med tilfældigt fortegn (N-retning).** Den
  spørger, om signalets retning bærer.
- B: tilfældige dage.

## Kilder

- Harvey, Mazzoleni & Melone, *The Unintended Consequences of Rebalancing*, NBER w33554 —
  https://www.nber.org/papers/w33554 · arbejdspapir (jan. 2026) —
  https://www.edhec.edu/sites/default/files/2026-03/Scientific%20paper.%20ssrn-5122748.pdf
- Lou, Yan & Zhang (2013), *Anticipated and Repeated Shocks in Liquid Markets*, Review of
  Financial Studies — https://researchonline.lse.ac.uk/id/eprint/43120
- Breedon & Ranaldo, *Intraday Patterns in FX Returns and Order Flow*, SNB Working Paper
  2011-04 — https://www.snb.ch/en/publications/research/working-papers/2011/working_paper_2011_04
- Baltussen, Da, Lammers & Martens (2021), *Hedging Demand and Market Intraday Momentum*,
  JFE — https://academicweb.nd.edu/~zda/intramom.pdf
- Quantified Strategies, *A Quantitative Look at the Gold Overnight Strategy* (praktiker) —
  https://quantifiedstrategies.substack.com/p/a-quantitative-look-at-the-gold-overnight
- Topstep, *When and what products can I trade* —
  https://help.topstep.com/en/articles/8284206-when-and-what-products-can-i-trade
