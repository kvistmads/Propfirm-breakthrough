# B4 kandidat 1 — præregistrering: trin A, edge-test af kernen

**Skrevet:** 2026-09-23 af overblikssessionen, før kørslen. Committes før kørslen (metoderegel 13).
**Grundlag:** kernen v2 i `research/output/b4_hypoteser.md`, og "Edge-testens omfang — besluttet 2026-09-22" samme sted.
**Bygger på:** `research/prereg/b4_k1_optaelling.md` (11d68f2), `b4_k1_optaelling_tillaeg.md` (50a060e), `b4_k1_optaelling_v2.md` (5de6fa1), `b4_k1_optaelling_v2_tillaeg.md` (c18539f). **Alt derfra gælder, medmindre det er ændret her.**

**Det her er den første kørsel der ser på udfald.** De to optællinger så ingen. Fra og med
trin A tæller varianterne med i N for den deflaterede tærskel, og tælleren nulstilles ikke
mellem trin.

---

## 1. Hvad trin A afgør — og hvad den ikke afgør

Kernen er med vilje uselektiv: 90,3% af dagene har et signal, 2,66 signaler pr. dag.
Videoens indhold er de syv filtre; ingen — heller ikke videoen — påstår at den bare kerne
er en edge. **Trin A's opgave er derfor ikke først og fremmest "har kernen en edge", men:**

1. **Hvad er kernens grundlinje?** Middel netto-R pr. handel med konfidensinterval, målt mod
   en nulmodel. Det er det tal filtersøgningen i trin 2 skal slå, og uden det kan trin 2
   ikke fortolkes.
2. **Hjælper break-even-flytningen?** PRD §3b's tre varianter afgøres her, én gang.
3. **Hjælper bufferen?** 10% mod 0%.
4. **Opfører maskineriet sig fornuftigt?** Andel tidsexits, andel handler hvor limitordren
   kun blev strejfet, censurering.

Trin A afgør **ikke** om kandidaten består. Kun den nederste båndgrænse i §7 parkerer den.

Trin A afgør **ikke** ruinrisiko eller beståelsesrate. `STRATEGI_PROPFIRM.md` §5 er genåbnet
og køres igen med disciplinreglerne, når en variant er frosset.

## 2. Serie, periode og hvorfor

| | valg | hvorfor |
|---|---|---|
| Serie | **MNQ.v.0**, 1m → 15m | Det er instrumentet. Antagelse (A) — at et prisniveau er det samme på NQ og MNQ — forsvinder helt ud af beslutningsvejen når zoner og fyldninger begge regnes på MNQ |
| Periode | 2019-05-06 → 2023-12-31, **1.173 RTH-dage** | MNQ's notering til in-sample-grænsen. Hentet 2026-09-23, verificeret i `research/output/b4_mnq_data.md` |
| Adgang | Kun gennem `data.holdout.load_in_sample(symbol="MNQ.v.0")` | Holdout fra 2024-01-01 er forseglet. **MNQ-holdout er ikke købt og findes ikke lokalt** |
| Zoner | Døgnserie | Zonen må dannes og aktiveres når som helst |
| Berøringer | RTH-maske, 15:30-21:30 dansk tid | STRATEGI §3 |

**Hvad vi giver afkald på.** NQ har 2.012 in-sample-dage mod MNQ's 1.173, og MNQ mangler
2016-2018 — herunder det stille 2017. Prisen er en 31% større MDE (§6), og den er stadig
under den effekt vi leder efter. 2019-2023 indeholder til gengæld covid-nedturen, 2021 og
2022-bjørnen.

**Sekundær linje, rapporteres men afgør ikke:** samme frosne varianter kørt på **NQ.v.0
2016-01-01 → 2018-12-31**, 754 dage MNQ aldrig har set. Det er ikke en holdout — datoerne er
in-sample — men det er data denne test ikke er valgt på. Den koster ingen varianter, fordi
det er de samme varianter på andre data.

## 3. Varianterne — N for trin A er 6

| akse | alternativer | kilde |
|---|---|---|
| Break-even | ingen · +1,0R · +1,2R | PRD §3b |
| Buffer | B = 0,10 × H · B = 0 | Mads mod video 9:50 |

6 varianter. Deflationsfaktor mod N = 3: **1,50×** (`research/maks_sharpe.py`).

**Intet andet søges i trin A.** Kernen står fast som beskrevet i `b4_hypoteser.md`. Filtrene
1-7, zonetype, basislysets farve og stopvarianten "med afstand" hører til trin 2 med egen
præregistrering. **Tælleren nulstilles ikke:** N efter trin 2 er 6 × antallet af
filterkombinationer der faktisk køres.

## 4. Handelsmekanikken

### 4a. De otte fyldningsregler

Aftalt med Mads 2026-09-22. Skrevet ud her, så de kan efterprøves.

| nr | regel | bemærkning |
|---|---|---|
| 1 | Limitordren på E fyldes når prisen **handler igennem E med mindst ét tick**, ikke ved berøring af E | Konservativt. Mads accepterede, med det forbehold at en ren berøring i virkeligheden ofte ville fylde |
| 2 | Der fyldes til **E**, aldrig bedre | Ingen positiv slippage, heller ikke ved gap forbi E |
| 3 | Rækkefølgen inde i en 15m-bar afgøres på **1m-serien**, ikke med en antagelse | Vi har 1m-data. Den bruges |
| 4 | Rammes stop og mål inde i **samme 1m-bar**, antages **stoppet ramt først** | Kun her bruges worst case |
| 5 | Stoppet fyldes med **0,5417 tick slippage**; målet fyldes som limit uden slippage | Fase 1's målte tal |
| 6 | **$2,627 pr. rundtur pr. kontrakt** trækkes fra hver handel | Fase 1, RTH. Brutto og netto rapporteres side om side |
| 7 | **Zonen dør ved berøringen**, også hvis ordren ikke fyldes eller handlen ikke tages | Uændret fra optælling 1 |
| 8 | **21:30 dansk tid:** alle hvilende ordrer annulleres, nye signaler ignoreres. **21:50:** åbne handler lukkes til markedspris, uanset niveau | Mads, 2026-09-22 |

### 4b. Ordrer, positioner og dagens tællere

- Alle **aktive** zoner har en hvilende limitordre. Den første gennemhandling der er tilladt
  bliver handlen.
- **Højst én position ad gangen.** Berøringer mens en position er åben springes over og
  **tælles** i rapporten.
- **Afgjort handel** = mål ramt (+2R) eller stop ramt (−1R). Den lukker dagen (PRD §3a).
- **Break-even-udgang** = stoppet er flyttet til E og rammes der. **To af dem lukker dagen.**
  BE er ikke nul: det er minus omkostning minus slippage (PRD §3b).
- **Tidsexit 21:50** afslutter dagen af sig selv.
- I varianten **ingen BE** findes BE-udfaldet ikke, så dagen lukkes ved den første afgjorte
  handel: højst 1 handel pr. dag. I BE-varianterne kan der blive 2. **Antal handler
  rapporteres pr. variant**, fordi n dermed ikke er ens.

### 4c. Sizing, uændret fra PRD §3c

`kontrakter = floor(250 / (risiko_pt × 2))`, rundet ned. Risiko = E − low = 1,1 × H med
buffer, H uden. Stoploft: risiko ≤ 0,429% af prisen. Zoner over loftet handles ikke.
R regnes pr. handel i enheder af den handels egen dollarrisiko, så varierende
kontraktantal ikke forvrider gennemsnittet.

## 5. Nulmodeller

Alle tre kører **samme maskineri, samme sizing, samme omkostninger, samme disciplinregler**
som den rigtige kørsel. Kun zonens placering ændres.

| model | hvad der ændres | hvad den svarer på | rolle |
|---|---|---|---|
| **N0** | intet — ren aritmetik | Hvilken win rate skal 2:1 have for at gå i nul? 33,33% brutto, **34,47% netto** ved medianrisiko | reference |
| **N1** | Zonens **dannelseslys** flyttes til et tilfældigt 15m-lys i **samme kalenderuge**. Side og H bevares; zonen bygges fra det lys' high (demand) eller low (supply) med samme H | Betyder basislys-plus-udbrudslys noget, eller ville et vilkårligt niveau af samme størrelse klare sig lige så godt under samme regler? | **afgør** |
| **N2** | Dannelseslyset og tiden bevares; **E forskydes** med et tilfældigt beløb trukket fra ±[0,5H, 3H] | Er det prisen eller tidspunktet der bærer? | forklarer |

N1 bevarer antal zoner, højdefordeling, side-balance og ugens volatilitetsregime. Den
ødelægger mønsteret. **R = 500 gentagelser.** Kan en gentagelse ikke køres inden for rimelig
tid, rapporteres det og kørslen stoppes — R sænkes ikke stiltiende.

## 6. Den afgørende statistik og MDE

**Primært mål: middel netto-R pr. handel.** Win rate alene holder ikke, så snart BE og
tidsexit findes — der er fire udfald, ikke to. Win rate rapporteres som beskrivelse.

**Test:** Westfall-Young maks-statistik. For hver N1-gentagelse beregnes middel netto-R for
alle 6 varianter, og gentagelsens **maksimum** gemmes. Den observerede bedste variants
middel netto-R holdes op mod den fordeling:

`p_FWE = (1 + antal gentagelser hvor maks ≥ observeret bedste) / (1 + R)`

Det kontrollerer familievis fejlrate eksakt, tager højde for at de 6 varianter er stærkt
korrelerede, og kræver ingen antagelse om normalfordeling. Det er skarpere end Bonferroni,
og det er den deflation der gælder for trin A.

**MDE, én-sidet α = 0,05, 80% styrke.** Ved ~1.056 handler (90,3% signaldage × 1.173) og
σ ≈ 1,414 R (2:1 uden edge):

| størrelse | værdi | formel |
|---|---|---|
| MDE_middel_R | **0,108 R** | (z_0,05 + z_0,20) × σ / √n = 2,4865 × 1,414 / √1056 |
| MDE_win_rate_pct | **37,9** | mod break-even 34,47% netto |
| Økonomisk krav, middel_R | **0,20 R** | 12 R ($3.000 / $250) på ~67 handelsdage ved 0,9 handler pr. dag |

**MDE er mindre end den effekt vi leder efter.** Testen kan altså svare på spørgsmålet
(metoderegel 2). Ved 0,10 R tager Combinen 133 dage, ved 0,30 R tager den 44.

## 7. Beslutningsreglen

Afgøres på den bedste af de 6 varianter, målt på middel netto-R.

| udfald | fortolkning | vi gør |
|---|---|---|
| p_FWE ≤ 0,05 **og** middel netto-R ≥ +0,20 R **og** CI-nedre > 0 | kernen alene har en brugbar edge | Variant fryses, filtersøgning bliver valgfri, holdout-data købes |
| p_FWE ≤ 0,05 **og** middel netto-R i [+0,10; +0,20) | reel, men for lille alene | Trin 2: filtersøgning med trin A som grundlinje |
| p_FWE > 0,05 **og** middel netto-R ≥ N1's median | kernen er neutral — **det forventede** | Trin 2: filtersøgning med trin A som grundlinje |
| bedste middel netto-R **under N1's 5%-fraktil** | kernen er værre end tilfældigt placerede zoner af samme størrelse | **Kandidaten parkeres** |

Krydser konfidensintervallet en grænse, gælder den laveste kategori. Resultatet skrives som
uafgjort, ikke afrundet til en konklusion.

**BE-varianten og buffer-varianten afgøres hver for sig** på samme tal, med CI på
**forskellen** mellem varianterne — ikke ved at se om deres egne intervaller overlapper.

## 8. Rapporten

`research/output/b4_k1_trinA.md` og `.csv`. Kompakt hovedtabel i chatten. Enhed i
kolonnenavnet, brutto og netto side om side, percentiler navngivet efter hvad de er
percentil af.

Pr. variant (6 rækker), plus demand og supply hver for sig, plus pr. år:

| kolonne | formel |
|---|---|
| handler_n | antal fyldte handler |
| middel_R_brutto · middel_R_netto | sum(R) / handler_n |
| middel_R_netto_ci95_lo · _hi | t-interval |
| win_rate_pct_netto + Wilson-CI | mål ramt / handler_n |
| udfald_maal_pct · udfald_stop_pct · udfald_BE_pct · udfald_tidsexit_pct | de fire udfald, summerer til 100 |
| tidsexit_middel_R_netto | hvad uret koster |
| dage_med_handel_n · handler_pr_dag_middel | |
| signaler_sprunget_over_position_n | berøringer afvist fordi en position var åben |
| signaler_sprunget_over_dagslukket_n | berøringer afvist af disciplinreglen |
| strejf_uden_gennemhandling_n | berøringer hvor prisen ramte E men ikke handlede igennem — regel 1's pris |
| risiko_pt_p10/p50/p90 · kontrakter_p10/p50/p90 | som optælling 2 |
| omk_R_netto_p50 · be_WR_pct_netto_p50 | |
| N1_middel_R_netto_p5/p50/p95 · p_FWE | nulmodellen |
| N2_middel_R_netto_p50 | forklaringen |

**Censurering rapporteres som kolonne:** handler der stadig var åbne ved in-sample-slut, og
zoner der aldrig blev berørt.

**Regressionstjek før kørslen:** det udvidede modul skal gengive `b4_k1_optaelling_v2.csv`
(commit c18539f) præcis, når det fodres kerne v2 på NQ. Afviger det, køres trin A ikke.

**Krydstjek mod NQ, rapporteres:** antal signaldage og signaler for kerne v2 på MNQ mod
NQ's 1.817 / 5.350 i samme delperiode (2019-05-06 → 2023-12-31). Det er en regression på
antagelse (A), ikke en variant.

## 9. Forventning, skrevet før kørslen — ikke et kriterium

- **Kernen alene lander på eller lige under N1's median.** Den er uselektiv, og videoens
  påstand ligger i filtrene.
- **Mads' forventning (2026-09-22): retesten holder ca. 9 ud af 10 gange.** Det svarer til
  at +1R nås før stoppet i ~90% af handlerne. Måles som `udfald_maal_pct` plus de handler
  der nåede +1R før stoppet. Det er langt over de 37,9% testen behøver.
- **BE hjælper ikke i gennemsnit.** BE afskærer halen i begge retninger; den hjælper kun
  hvis mere end dobbelt så mange af de udløste handler ender i SL som i TP (PRD §3b).
- **Tidsexit rammer 15-30% af handlerne.** Målet på 2R er langt ved 15m-zoner, og sidste
  indgang er 21:30.

## 10. Efter kørslen

**Stop.** Tabellen i chatten. Ingen ændring af definitioner, ingen forslag til
forbedringer — heller ikke gode. Resultatet læses sammen med Mads, og først derefter
besluttes trin 2.
