# B4 kandidat 7 — tillæg: optællingen godkendt, før kørslen

**Skrevet:** 2026-10-10 af overblikssessionen, efter Code's trin 1 og **før** den rigtige
kørsel. Trin 1 er data 4f5c861, modul og tests e4ec483, optælling og appendiks B ba3e5bf.
Der er ikke set P&L, hit ratio eller udfald.

**Gyldighed:** tillægget gælder, når ejeren committer det. Commit'en er ejerens
godkendelse. `b4_k7_rebalancering.md` gælder uændret, bortset fra én ny diagnose i §4.
Diagnosen afgør intet og ændrer ikke beslutningsreglen i §8.

## 1. Trin 1 er godkendt

- **Data:** ES $10,23 og ZN $9,57, i alt $19,81, under loftet på $30.
  - Forbruget er nu $56,65 af $120.
  - Holdout er ikke hentet.
- **Tests:** kandidat 7's 15 tests består. Hele suiten: 1.175 bestået, 6 sprunget over.
- **Regressionstjek:** alle holder, kandidat 1–6.
- **Edge-kravets rapportscript** er committet (721efda) og genskaber `b4_edgekrav.md` og
  `b4_edgekrav_celler.csv` byte for byte. Afsnit 9 står ordret i scriptet og regnes ikke
  igen. Det noteres og godkendes.

**Optællingen på ES (afgør):**

| variant | aktive dage | long / short | middel \|w\| | σ_v $/dag | MDE_sidak2 $/dag | E_v $/dag | styrke mod N-retning ved E_v / E_v/2 | styrke for CI-nedre > 0 ved E_v / E_v/2 |
|---|---|---|---|---|---|---|---|---|
| T · tærskel | 1.949 | 19% / 81% | 0,293 | 315 | 20,0 | 26,5 | 96% / 46% | 94% / 39% |
| K · kalender | 556 | 39% / 61% | 1,000 | 431 | 51,1 | 51,0 | 80% / 29% | 72% / 21% |

- **Data:**
  - 1.951 handelsdage, hvoraf 2 er udelukket, fordi indgangen kom over 5 minutter for sent
    (2018-04-30 og 2020-07-01).
  - 15 kortdage. Ingen forsinkede udførelser på 1–5 minutter.
  - 31 ruller ligger inde i Topstep-dagen. Den forskelsjusterede serie tager springet ud.
  - ES mangler ingen signalbarer. ZN mangler 7, heraf 2 over 5 minutter.
- **Opvarmningen** betyder lidt: T med start i januar og i februar 2016 korrelerer 0,965.
- **Styrken:**
  - T kan se artiklens effekt med 96%, men det halve kun med 46%.
  - K kan se artiklens effekt med 80% og det halve med 29%.
  - **Kørslen godkendes.** Præregistreringen satte ingen fast grænse, og varianterne er
    bestemt på forhånd.
- **Omkostningen** var 4,16 bp i 2016 og 2,06 bp i 2023 ved det historiske niveau, mod
  1,14 bp ved dagens niveau.
- **Tælleren forbliver 47.**

## 2. Appendiks B: ingen afvigelse

Code læste EDHEC-udgaven (14. januar 2026, appendiks B s. 52–53) og fandt ingen afvigelse
fra §4c–4e. De to uklare punkter afgøres sådan:

| punkt | afgørelse |
|---|---|
| Absolutstreger og ≥ i rebalanceringen | **\|s\| ≥ δ står.** Afsnit 1.2 bruger selv absolutstreger. Uden dem ville en undervægt aldrig udløse køb af aktier, og det modsiger mekanismen. ≥ mod > betyder intet med flydende tal |
| c_(t−4) i K's vending | **Står som skrevet.** Det er præregistreringens tekst, og det rammer kun de cirka 92 vendingsdage |

## 3. Code's læsninger — godkendt

Alle 27 i docstringen i `research/b4_k7_rebalancering.py` er godkendt. De syv markerede:

| nr | læsning | svar |
|---|---|---|
| 2 | ES og ZN slår signalbaren op hver for sig | Godkendt. Det rammer kun ZN's 7 manglende barer |
| 4 | Rebalancering ved \|s\| ≥ δ | Godkendt, se §2 |
| 6 | Vendingen bruger c_(t−4) | Godkendt, se §2 |
| 7 | 5 minutter ved manglende udgangsbar måles fra barens start | Godkendt. Ingen dage rammes |
| 9 | Udelukkede dage tæller ikke med i nævneren for netto pr. handelsdag | Godkendt. Det er 2 dage |
| 13 | sd for z tages over alle signaldage | Godkendt. Det er §7's "alle in-sample-dage", og E_v afgør intet |
| 14 | Styrken ved normalapproksimation | Godkendt, som i kandidat 6 |

## 4. Hvad optællingen viser — og én ny diagnose

Tre ting fra optællingen. De er ikke udfald, men de ændrer, hvordan resultatet skal læses.

1. **T ligner i høj grad kortsigtet reversal.** w^T korrelerer −0,644 med ES' afkast på
   signaldagen: stiger ES en dag, er T oftest short dagen efter.
   - §2 advarede om det. Artiklen kontrollerer for dagens afkast, men vores test gør ikke.
   - Vinder T, ved vi altså ikke, om det er rebalancering eller almindelig reversal.
   - Det ændrer ikke rækken. Men det afgør, hvad der i givet fald fryses og testes på
     holdout. Derfor den nye diagnose nedenfor.
2. **T tager de største positioner på de mest urolige dage.**
   - Med middel |w| på 0,293 er σ_v $315 pr. dag. Det er cirka det dobbelte af, hvad man
     ville vente, hvis størrelse og uro var uafhængige.
   - Det passer med artiklens gevinster i stød, men det trækker i MLL'en.
   - Dagsfordelingen og største tab inden for dagen (§9) viser, hvor meget.
3. **T er short 81% af dagene.** I en stigende periode trækker markedets drift imod T.
   Det driftjusterede brutto i §9 viser hvor meget.

**Ny diagnose, §9a — T og K mod kortsigtet reversal:**
- **Data:** de ikke-udelukkede handelsdage på ES.
  `y_d = Δpt_d × (7.800 / L_d) × 5`, altså brutto pr. MES ved w = +1.
- **Regressioner (OLS med HC3-robuste standardfejl):**
  1. Uden kontrol: `y_d = a + b_T × z(T_t)`.
  2. Med kontrol, som artiklens dagsafkast:
     `y_d = a + b_T × z(T_t) + b_E × z(R^ES_t) + b_Z × z(R^ZN_t)`.
  3. Det samme for K på de dage, hvor t er blandt månedens 5 sidste XNYS-dage, med z(c_t) i
     stedet for z(T_t).
- **Standardisering:** z er værdien divideret med dens sd over de samme dage (ddof = 1).
- **Rapportér** koefficienterne i $ pr. standardafvigelse med 95%-interval og n, samt
  korrelationen mellem w^K og ES' afkast på t.
- **Sådan læses den:**
  - Rebalancering forudsiger b_T < 0 og b_c < 0, også med kontrol.
  - Forsvinder b_T, når dagsafkastet er med, er T mest reversal.
- **Den afgør intet** og ændrer ikke rækken i §8.

## 5. Betingelser for den rigtige kørsel

1. **Den eneste tilladte kodeændring** er diagnosen i §4, med en test på syntetiske data med
   kendt hældning.
2. Hele testsuiten og regressionstjekket i §11.4 skal bestå igen. Koden committes, og
   kørslen sker fra den commit. Rapporten oplyser commit-hash.
3. **R = 500** for både ES og Nasdaq-kontrollen.
4. **Afgørelsen efter §8 tages på ES** ved $4,45 og dagens niveau. Nasdaq-kontrollen
   rapporteres og afgør intet.
5. **Rapport efter §10 og §9**, med diagnosen i §4. Alle tal brutto og netto.
6. Bagefter: stop. §8 anvendes mekanisk og læses sammen med ejeren.
