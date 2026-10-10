# B4 kandidat 7 — præregistrering: rebalancering. Presser 60/40-porteføljerne aktierne, når de er overvægtede?

**Skrevet:** 2026-10-10 af overblikssessionen, før kode og kørsel. Committes før kode.
**Kilde:** Harvey, Mazzoleni og Melone, *The Unintended Consequences of Rebalancing*, NBER
w33554 (marts 2025, revideret januar 2026). Det er et arbejdspapir og er ikke
fagfællebedømt. Screeningen står i `research/output/b4_screening_2.md`.
**Besluttet af ejeren:**
- 2026-10-09: disciplinzonen styrer, og der søges svage edges, der kan supplere overnight
  drift (svar 1A og 2A på edge-kravet).
- 2026-10-10: svar 1A–5A på spørgsmålene til kandidat 7 (screening 2 §4).

**Løftede regler for denne kandidat:** `PRD_FASE3_B4_EDGE.md` §3 ("kun US RTH") og
`STRATEGI_PROPFIRM.md` §3 ("ingen markedsordrer uden for RTH"), som for kandidat 6.
Topsteps egne regler gælder uændret. Positionen ligger inden for én Topstep-dag, der starter
kl. 17:00 CT, og er lukket kl. 15:08 CT, før Topsteps grænse kl. 15:10.

**Artiklens appendiks B** (formel B.1 og B.2) kunne ikke læses herfra. §4c–4e er skrevet
ud fra hovedteksten og forfatternes slides (EDHEC 2026). Code læser appendikset i trin 1,
hvis det kan hentes (§11.7). Afviger det, afgør tillægget sagen, før der er set udfald.

---

## 1. Hvad testen afgør

1. **Bærer signalets retning?** Varianten sammenlignes med de samme positioner med
   tilfældigt fortegn (N-retning, afgør). Der korrigeres for 2 varianter.
2. **Betaler den omkostningen?** Middel netto-dollar pr. aktiv dag pr. MES-enhed ved dagens
   niveau, med konfidensinterval over dagene.
3. **Kan den supplere kandidat 6?** Korrelationen med kandidat 6's nætter rapporteres. Den
   afgør intet.

**Om prøven:** vores in-sample (2016–2023) ligger næsten helt inde i artiklens prøve (1997
til marts 2023). Et positivt resultat her er derfor en genskabelse af artiklen med vores
udførelse: kun aktiebenet, Topstep-dagen og vores omkostning. Det er ikke et uafhængigt
bevis. Det kan kun komme fra holdout 2024–2026, som også dækker publiceringen.

## 2. Mekanismen — skrevet før testen

**Påstanden:**
- Pensionskasser, fonde og balancerede fonde holder en fast fordeling, fx 60% aktier og 40%
  obligationer.
- Slår aktierne obligationerne, bliver aktievægten for høj. Så skal de sælge aktier og købe
  obligationer.
- Nogle gør det ved månedens slutning (kalender), andre når vægten er drevet over en grænse
  (tærskel).
- Flowet er stort, tvunget og forudsigeligt. Det presser prisen, og presset vender inden for
  cirka to uger.

**Hvem betaler:** fondene. De handler på et kendt tidspunkt uden hensyn til prisen. Dem, der
tager den anden side eller handler før dem, får betaling.

**Litteraturen** (S&P 500- og 10-årige statsobligationsfutures, 1997-09-10 → 2023-03-17,
6.226 dage):
- 1 standardafvigelse højere signal giver cirka **16–17 bp lavere afkast i S&P-futures
  næste dag** og 2–4 bp højere i obligationsfutures.
- Kalendersignalet virker i månedens sidste dage og mest ved kvartalsslut.
- Tærskelsignalets virkning bunder ud omkring dag 4 og er væk ved dag 9. Kalendersignalets
  bunder ud omkring dag 2 og er væk ved dag 6.
- Long-short-strategien (S&P mod obligationer, vægtet med signalerne):
  - Sharpe 1,11 før omkostninger og cirka 1 efter. Skævhed 5,2.
  - Uden 2008–2009 og marts 2020 er Sharpe 0,90.
- Forudsigelsen var ikke signifikant i 1961–1997, men signifikant i 1997–2023.
- Ifølge en fodnote blev den "endnu stærkere" frem til 2025. Strategiens afkast efter 2023
  er ikke opgjort.

**Det taler imod:**
- **Kun aktiebenet.** Obligationsbenet (ZN) er for stort til disciplinzonen. Aktiebenet
  bar 16–17 af cirka 20 bp i artiklen.
- **Gevinsten kommer i stød**, mest i urolige perioder (skævhed 5,2). Det kræver mange dage
  at se, og tabsdagene imellem trækker i Topsteps MLL.
- **Tærskelsignalet ligner kortsigtet reversal.** Ved δ = 0 er signalet dagens relative
  afkast alene. Artiklen kontrollerer for dagens afkast og finder stadig effekten. Det gør
  vi ikke.
- **Publiceret 2025** med stor omtale (CFA Institute, Duke). Kandidat 5 viste, hvad det kan
  gøre.
- **Vores dag er ikke artiklens.** Artiklen måler close → close. Vi holder fra 17:00 til
  15:08 CT, så vi mangler timen efter signalet (15:00–16:00 CT) og weekendgabet.

## 3. Data og faste indstillinger

| emne | valg |
|---|---|
| Signal (svar 1A) | **ES.v.0 og ZN.v.0 1m**, GLBX.MDP3, 2016-01-01 → 2023-12-31, kun gennem `data.holdout.load_in_sample` |
| Handel (afgør) | ES.v.0 1m som pris for **MES** ($5 pr. punkt). ES og MES har samme kurs. MES er tilladt på Topstep |
| Nasdaq-kontrol | NQ.v.0 1m 2016–2023 med MNQ's økonomi ($2 pr. punkt). Rapporteres, afgør intet |
| Datakøb | ES.v.0 og ZN.v.0 ohlcv-1m for 2016-01-01 → `HOLDOUT_START` (2024-01-01), gennem `data.src_databento.pull` med budgetvagten. Estimat først. **Loft for købet: $30.** Forbruget er $36,84 af $120 |
| Holdout | ES og ZN fra 2024 **købes ikke nu**. Fryses en variant, præregistreres holdout-testen, og først da købes og fryses data |
| Opvarmning | `load_in_sample` starter 2016-01-01. Porteføljerne i §4c–4d starter i 60/40 ved første close i 2016. **Handelsdage tælles fra 2016-04-01** |
| Priser | Punktforskelle og afkast regnes på den **forskelsjusterede** serie (`b4_k2_nowick.forskelsjuster`). Niveauer og nævnere tages fra den ujusterede |
| Omkostning | **$4,45 pr. round trip pr. MES** (§4f) |
| Normering | ES i dag: **7.800** (§4g) |
| Tidszone | CT. Dansk tid er normalt CT + 7 timer, så 17:00–15:08 CT er 00:00–22:08 dansk tid |

## 4. Definitionerne

### 4a. Dagene

- **Signaldag t** er en XNYS-dag (`data.sessions`).
- **Handelsdag d** er den næste XNYS-dag efter t.
- **Topstep-dagen for d** går fra kl. 17:00 CT på kalenderdagen før d til kl. 15:08 CT på d.
  For en mandag starter den søndag kl. 17:00.
- Alt, der bestemmer positionen for d, er kendt ved signalets close på t. Intet fra efter
  RTH-slut på t indgår.

### 4b. Dagsafkast til signalet

- **Close C_t** er close af den sidste 1m-bar, der starter før RTH-slut på t efter
  `data.sessions`. Det er normalt baren kl. 14:59 CT, på kortdage 11:59 CT.
- **Samme tidspunkt for ES og ZN**, så de to afkast er samtidige. ZN's settlement er kl.
  14:00 CT, men ZN handles til 16:00 CT.
- Mangler baren, bruges den seneste bar før RTH-slut samme dag. Ligger den mere end 5
  minutter før, tælles det.
- `R_t = (C^adj_t − C^adj_(t−1)) / C^raw_(t−1)`, hvor t−1 er forrige XNYS-dag, adj er den
  forskelsjusterede serie og raw den ujusterede. En rulle giver altså ikke et spring.

### 4c. Tærskelsignalet

For hvert bånd **δ ∈ {0,000; 0,001; …; 0,025}** (26 bånd) simuleres en portefølje:

1. Startvægten i aktier er w = 0,60 ved første close i 2016.
2. Hver dag t driver vægten:
   `w̃_t = w_(t−1)(1 + R^ES_t) / [w_(t−1)(1 + R^ES_t) + (1 − w_(t−1))(1 + R^ZN_t)]`.
3. Signalet for båndet er afstanden **før** en eventuel rebalancering: `s^δ_t = w̃_t − 0,60`.
4. Er `|s^δ_t| ≥ δ`, rebalanceres der: `w_t = 0,60`. Ellers er `w_t = w̃_t`.
   - Ved δ = 0 rebalanceres hver dag, så `s^0_t` er dagens drift alene.

**Tærskelsignalet** `T_t` er middel af `s^δ_t` over de 26 bånd. Positivt T betyder, at
aktierne er overvægtede.

### 4d. Kalendersignalet

- Én portefølje med startvægt 0,60 og samme drift som i §4c.
- **Signalet** `c_t = w̃_t − 0,60`, afstanden før en eventuel rebalancering.
- På månedens sidste XNYS-dag rebalanceres der: `w_t = 0,60`. Ellers er `w_t = w̃_t`.
- `c_t` er altså driften siden forrige måneds sidste XNYS-dag.

### 4e. Positionerne — de to varianter (svar 2A og 4A)

Positionen `w^v_t` sættes på signaldag t og holdes i Topstep-dagen for d. Positiv betyder
long MES, negativ short. Størrelsen er i MES-enheder.

| variant | position | aktive dage |
|---|---|---|
| **T · tærskel** | `w^T_t = −T_t / 0,015` | alle handelsdage |
| **K · kalender** | t blandt månedens 5 sidste XNYS-dage: `w^K_t = sign(−c_t)`. t er månedens første XNYS-dag: `w^K_t = sign(c_(t−4))`, hvor t−4 er 4 XNYS-dage før t. Ellers 0 | cirka 6 pr. måned |

- **T følger signalets styrke.** Skaleringen med 1,5% er artiklens. Den giver de to signaler
  cirka samme risiko.
- **K bruger kun fortegnet**, som i artiklen.
  - Positionerne ligger i månedens 4 sidste handelsdage og næste måneds første (presset).
  - Næste måneds anden handelsdag tager vendingen efter presset.
- Er signalet præcis 0, er positionen 0.
- **Diagnose, ikke variant:** artiklens samlede strategi, `w^C_t = ½(w^T_t + w^K_t)`.

### 4f. Omkostning

- **$4,45 pr. round trip pr. MES:**
  - kommission $1,22 (TopstepX, tjekket 2026-10-10);
  - spread 1,5 tick = $1,875. Det er antaget, fordi MES' spread ikke er målt. ES og MES har
    normalt 1 tick i RTH, men indgangen ligger ved genåbningen kl. 17:00 og udgangen efter
    RTH-slut;
  - slippage 0,5417 tick pr. side = $1,354 (antagelse C4, som i kandidat 5 og 6).
- **Pr. dag er omkostningen |w| × $4,45.** Positionen lukkes hver dag kl. 15:08 og åbnes
  igen kl. 17:00, så hver aktiv dag er en hel round trip.
- Det er 1,14 bp ved 7.800.
- **Diagnose ved $5,70** (spread 2,5 tick).
- Nasdaq-kontrollen: $2,85 pr. MNQ, som i kandidat 6.
- Fills i Combine og XFA er simulerede, så tallene er nok på den forsigtige side.

### 4g. Indgang, udgang og målet (svar 3A)

- **Indgang:** ved åbningen af den første 1m-bar, der starter kl. 17:00 CT eller senere på
  kalenderdagen før d. Starter den mere end 5 minutter for sent, udelukkes dagen i alle
  varianter og i nulmodellen. Det tælles.
- **Udgang:** ved åbningen af baren, der starter kl. 15:08 CT på d.
  - På kortdage (RTH-slut før 15:00 CT efter `data.sessions`) ved åbningen af baren 2
    minutter før RTH-slut, normalt kl. 11:58 CT.
  - Mangler baren, bruges close af den seneste bar før. Ligger den mere end 5 minutter før,
    udelukkes dagen. Det tælles.
- `L_d` er den ujusterede åbning af indgangsbaren.
- `brutto_usd_d = w × Δpt_d × (7.800 / L_d) × 5`, hvor Δpt er udgang minus indgang på den
  forskelsjusterede serie.
- `netto_usd_d = brutto_usd_d − |w| × 4,45`.
- **Målet** er middel `netto_usd` pr. aktiv dag (w ≠ 0), med t-interval over dagene.
- Middel pr. handelsdag, hvor inaktive dage tæller som 0, rapporteres også, fordi det er
  det, en konto mærker.
- **Normeringen:** S&P 500 lukkede 7.801,77 den 2026-10-07, og ES ligger tæt på. L_ref =
  7.800 ligger fast fra nu. ES lå på cirka 2.000 i 2016, så de første dage skaleres cirka
  3,9 gange op. Antagelsen er som i kandidat 5 og 6: bevægelser i procent og omkostningen i
  ticks er de samme i dag.
- **Nasdaq-kontrollen:** `w × Δpt × (29.138 / L_d) × 2 − |w| × 2,85` på NQ.v.0.

## 5. Varianterne og tælleren

Der er **2 varianter.**

| tæller | forsøg |
|---|---|
| Kandidat 1–6 | 45 |
| Kandidat 7 | 2 |
| **I alt** | **47** |

Edge-kravet tæller ikke.

## 6. Nulmodellen (svar 5A)

**N-retning — afgør. Bærer signalets retning?**
- Samme dage og samme størrelse `|w^v_t|` som varianten, samme omkostning og normering.
- **Fortegnet trækkes tilfældigt**, +1 eller −1 med lige sandsynlighed, for hver dag.
- **Trækningerne deles:** fortegnet trækkes deterministisk pr. (gentagelse, dag). T og K får
  derfor samme tilfældige fortegn på de dage, de deler.
- **R = 500.**

**Markedets drift:** med tilfældigt fortegn er forventet brutto 0. En variant, der mest er
long eller mest er short, kan derfor slå N-retning på driften alene. Derfor rapporteres
andelen long og short og et driftjusteret brutto (§9). T er formentlig oftest short i en
stigende periode, så driften trækker snarere imod.

**Long hele Topstep-dagen — forklarer, ændrer intet.** Long 1 MES hver dag fra indgang til
udgang, med samme omkostning og normering. Viser markedets drift i vinduet.

## 7. Statistik og MDE

**Mål:** middel `netto_usd` pr. aktiv dag, med t-interval over dagene (95%, tosidet).

**Test:** Westfall-Young maks-statistik mod N-retning, standardiseret som i
`b4_k2_nowick.md` §7: `t_v = (m_v − med_v) / sd_v`, `p_FWE = (1 + #{max t* ≥ t_v}) / 501`.
Énsidet.

**MDE**, regnet i optællingen uden udfald:
- `RV_d = Σ_k (Δ_k × (7.800 / L_d) × 5)²`. Summen går over 1m-ændringerne langs stien fra
  indgangens åbning til udgangens åbning, på den forskelsjusterede serie.
- `σ_v = √(middel over aktive dage af w_d² × RV_d)`.
- `MDE_sidak2 = 2,7961 × σ_v / √n_v` og `MDE_CI = 2,8016 × σ_v / √n_v`.

**Overslag før data er hentet.** ES svinger cirka 1,1% om dagen, cirka $430 pr. MES ved
7.800.

| MDE_sidak2 for K (cirka 558 aktive dage, \|w\| = 1) | σ $350 | σ $430 | σ $500 |
|---|---|---|---|
| $ pr. aktiv dag | 41 | 51 | 59 |

For T (cirka 1.950 dage) afhænger σ_T af signalets størrelse. MDE_sidak2 er 0,063 × σ_T.

**Artiklens effekt ved dagens niveau:** 16,5 bp pr. standardafvigelse i signalet svarer til
**$64 brutto pr. MES**. Optællingen regner artiklens forventede brutto pr. aktiv dag ud fra
signalerne alene:
- `E_v = middel over aktive dage af |w_d| × 0,00165 × |z_d| × 7.800 × 5`.
- `z_d` er signalet (T_t for T, c_t for K) divideret med dets standardafvigelse over alle
  in-sample-dage.
- For K sættes E til 0 på dage med vendingen, fordi artiklens hældning ikke gælder dem.

**Ingen fast betingelse før kørslen.** Optællingen viser MDE og styrken mod `E_v` og
`E_v / 2` for hver variant, og **ejeren godkender optællingen, før der køres.** Overslaget
tyder på god styrke for T og middel styrke for K.

## 8. Beslutningsreglen — dækker alle udfald

Rækkerne prøves i rækkefølge, og den første, der passer, gælder. Krydser et interval en
grænse, er betingelsen ikke opfyldt.

| nr | udfald | handling |
|---|---|---|
| 1 | Mindst én variant har p_FWE ≤ 0,05 **og** CI-nedre > 0 | **Varianten fryses.** Opfylder flere kravet, fryses den med højeste CI-nedre. Næste skridt: præregistrering af holdout-testen (ES og ZN 2024–2026 købes og fryses først da), korrelationen med kandidat 6 og ruinmodellen for de to sammen |
| 2 | Mindst én variant har p_FWE ≤ 0,05, men ingen opfylder række 1 | **Parkeres som "retningen bærer, men betaler ikke omkostningen".** Varianter med CI-nedre > 0 uden p_FWE ≤ 0,05 skrives op som in-sample-fund |
| 3 | Ingen variant har p_FWE ≤ 0,05, men mindst én har CI-nedre > 0 | **Parkeres:** gevinsten følger ikke signalets retning, fx markedets drift. In-sample-fund, som kan blive en ny kandidat med egen præregistrering |
| 4 | Alt andet | **Kandidat 7 parkeres** |

**Afgørelsen tages på ES (MES-økonomi) ved $4,45 og dagens niveau.** Diagnoserne i §9
ændrer ikke rækken.

## 9. Diagnoser — rapporteres, men afgør intet

| diagnose | hvorfor |
|---|---|
| **Korrelation med kandidat 6:** dagens netto for T og K mod kandidat 6's netto på NQ-natten før d (07:30–09:30 · efter salg, 0 på nætter uden handel). Samlet Sharpe for de to ved lige risiko | F6: kan den supplere? |
| Korrelation med long hele Topstep-dagen | er det bare markedet? |
| Andel long og short, middel w, og driftjusteret brutto: middel af `brutto_d − w_d × μ`, hvor μ er middel brutto pr. dag for long hele dagen | markedets drift |
| **Inden for og efter artiklens prøve:** 2016-04-01 → 2023-03-17 og 2023-03-18 → 2023-12-31, netto med CI | genskaber vi artiklen, og hvad sker der bagefter (kun 9 måneder) |
| Uden marts 2020 | artiklen fandt gevinsten i urolige perioder |
| Pr. år, netto og nominelt | koncentration |
| K: kvartalsslut mod andre måneder. T: månedens 5 sidste dage mod resten | artiklen fandt mest ved kvartalsslut |
| Brutto for natten (17:00 → 08:30 CT) og RTH (08:30 → 15:08 CT) hver for sig | hvornår kommer gevinsten |
| Brutto close → close (15:00 → 15:00 CT), som i artiklen | koster vores vindue noget? |
| Artiklens samlede strategi, ½(T + K) | sammenligning med artiklen |
| T med hele kontrakter: `round(w^T)` MES | kan T handles med hele MES i disciplinzonen? |
| Netto ved $5,70 og den række i §8, det ville give | spread |
| Break-even-omkostning pr. round trip, middel og CI | margen over $4,45 |
| Nominelt, ved det historiske niveau | hvad der faktisk var tjent |
| Nasdaq-kontrollen, samme 2 varianter | kontrol på instrumentet fra kandidat 5 og 6 |
| Hit ratio, gevinst/tab-forhold og skævhed | artiklens skævhed var 5,2 |
| Dagsfordeling p1/p5/p50/p95/p99, værste og bedste dag, σ pr. aktiv dag og pr. handelsdag | ruinmodel og disciplinzone |
| Største tab inden for dagen (mark-to-market på 1m-close) pr. MES-enhed | Topsteps MLL brydes i realtid |
| Udelukkede dage, forsinkede udførelser, manglende signalbarer og ruller i vinduerne | datakvalitet |

## 10. Rapporten

Filerne er `research/output/b4_k7_rebalancering.md` og `.csv`.

**Hovedtabellen** har én række pr. variant med kolonnerne:
- `variant`, `aktive_dage_n`, `andel_long`;
- `middel_brutto_usd`, `middel_netto_usd`, `CI95_netto`;
- `N_retning_p5/p50/p95`, `t_v`, `p_FWE`;
- `netto_usd_pr_handelsdag`;
- `MDE_sidak2`, `MDE_CI`.

Derefter: §8 anvendt mekanisk, og diagnoserne i hver sin tabel.

## 11. Før kørslen: Code's trin 1, og så stop

1. **Data:** `research/b4_k7_data.py` efter mønstret i `research/b4_mnq_data.py`.
   - Gratis estimat for ES.v.0 og ZN.v.0 ohlcv-1m, 2016-01-01 → `HOLDOUT_START`.
   - **Er det samlede estimat ≤ $30 og inden for budgettet, hentes data.** Commit'en af denne
     præregistrering er ejerens godkendelse af købet inden for loftet. Ellers: stop og
     rapportér.
   - Tjek barer pr. år, rulledatoer for ES og ZN, og at begge kan læses med
     `load_in_sample`.
   - Holdout hentes ikke. API-nøglen vises aldrig, kun maskeret.
2. **Modul og tests:** `research/b4_k7_rebalancering.py` og
   `tests/test_b4_k7_rebalancering.py`. Kandidat 1–6's moduler må importeres, men ikke
   ændres.
   - Westfall-Young genbruges fra `b4_k2_nowick.westfall_young`.
   - Forskelsjusteringen genbruges fra `b4_k2_nowick.forskelsjuster`.
   - Kandidat 6's nætter regnes med `b4_k6_overnight`'s egne funktioner.
3. **Syntetiske tests, alle skal bestå:**
   1. Drift efter §4c. Startvægt 0,60. Ved δ = 0 er signalet dagens drift, og der
      rebalanceres hver dag. Rebalancering ved |s| ≥ δ, også ved lighed. T er middel af 26
      bånd.
   2. Kalender efter §4d: driften siden forrige måneds sidste XNYS-dag, rebalancering ved
      dens close, og signalet den dag er før rebalanceringen. Også når månedens sidste
      hverdag er en helligdag.
   3. K-positioner: de 5 sidste XNYS-dage giver sign(−c_t), første XNYS-dag giver
      sign(c_(t−4)), ellers 0. Signal 0 giver position 0.
   4. T-position = −T / 0,015.
   5. Signalets tid: close af sidste bar før RTH-slut, samme tidspunkt for ES og ZN, også på
      kortdage. Afkast på den forskelsjusterede serie med ujusteret nævner, så en rulle ikke
      giver spring. Intet efter RTH-slut på t indgår i positionen for d.
   6. Topstep-dagen: indgang kl. 17:00 CT på kalenderdagen før d (søndag for mandag), udgang
      kl. 15:08 CT og på kortdage 2 minutter før RTH-slut. Reglerne for manglende barer og 5
      minutters forsinkelse.
   7. Normering og omkostning efter §4f–4g, også for Nasdaq-kontrollen. Omkostningen skalerer
      med |w|.
   8. N-retning: samme |w|, fortegn ±1 deterministisk pr. (gentagelse, dag), delt mellem T og
      K.
   9. Westfall-Young og p_FWE som i kandidat 2.
   10. Opvarmning: ingen handelsdage før 2016-04-01.
4. **Regressionstjek:**
   - kandidat 1's tre tjek;
   - `simuler_handel` 1.226 / −0,0115;
   - kandidat 2: 611 / −0,1430;
   - kandidat 3: 1.168 / −0,0712;
   - kandidat 4: 1.104 / −0,0920;
   - kandidat 5 in-sample, 1m · uden middag: 14.831 handler og $41,07;
   - kandidat 6, NQ, 07:30–09:30 · efter salg: 902 nætter og $11,07 netto;
   - hele testsuiten.
5. **Optælling uden udfald**, for ES og for Nasdaq-kontrollen:
   - handelsdage i alt, udelukkede dage med grund, forsinkede udførelser, manglende
     signalbarer for ES og ZN, og ruller i vinduerne;
   - aktive dage pr. variant, og antal måneds- og kvartalsslut;
   - fordelingen af w^T (p5, p50, p95 og middel |w|), andel long og short for T og K, og
     standardafvigelsen af T og c;
   - korrelationen mellem T med start ved første close i 2016 og med start 2016-02-01, over
     handelsdagene (opvarmningens betydning);
   - korrelationen mellem w^T og ES' afkast på t (ligner det reversal?);
   - medianen af L_d pr. år og omkostningen i bp pr. år;
   - σ_v, `MDE_sidak2`, `MDE_CI`, `E_v` og styrken mod `E_v` og `E_v / 2`, både mod
     N-retning og for CI-nedre > 0.
   - **Ingen P&L, ingen hit ratio, intet udfald.**
6. **Tidsmåling:** ét gennemløb og 5 gentagelser af N-retning.
7. **Appendiks B:** hent artiklen (NBER w33554 eller EDHEC-udgaven), hvis det kan lade sig
   gøre, og læs formel B.1 og B.2 og afsnittet om strategien. Rapportér hver afvigelse fra
   §4c–4e, især:
   - om s^δ er afstanden før rebalancering hver dag, eller kun handelsbeløbet på dage med
     rebalancering;
   - båndgitteret (0–2,5% eller 0–2%);
   - om "sidste uge" og "første dag" i K gælder signaldagen t, som her, eller afkastdagen;
   - hvordan T og K vægtes i den samlede strategi.

   Ret ikke koden efter appendikset. Tillægget afgør det.
8. **Stop.** Den rigtige kørsel sker først, når ejeren har godkendt optællingen.

## 12. Forventning, skrevet før kørslen — ikke et kriterium

- **T har mest styrke.** Den handler hver dag, og artiklens hældning ligger et godt stykke
  over det, testen kan se.
- **Prøven overlapper artiklens.** Findes effekten slet ikke her, er det et stærkt tegn på,
  at aktiebenet alene eller Topstep-dagen ikke kan bære den.
- **Gevinsten kan hænge på få dage.** Marts 2020 kan fylde meget. Diagnosen uden marts 2020
  viser det.
- **Mit skøn for rækken i §8:** række 1 ca. 30%, række 2 ca. 10%, række 3 ca. 10%, række 4
  ca. 50%.

## 13. Efter kørslen

Stop. Tabellerne i chatten. Ingen ændring af definitioner, ingen nye varianter og ingen
forslag. Resultatet læses sammen med ejeren, og §8 anvendes mekanisk.

## Kilder

- Harvey, Mazzoleni & Melone, *The Unintended Consequences of Rebalancing*, NBER w33554 —
  https://www.nber.org/papers/w33554
- Samme, arbejdspapir januar 2026 (EDHEC) —
  https://www.edhec.edu/sites/default/files/2026-03/Scientific%20paper.%20ssrn-5122748.pdf
- Mazzoleni, slides (EDHEC 2026) —
  https://www.edhec.edu/sites/default/files/2026-03/slides_EDHEC_Michele%20Mazzoleni%20%281%29.pdf
- Topstep, *TopstepX commissions and fees* (2026-10-10): MES $1,22 pr. round trip —
  https://help.topstep.com/en/articles/8284213-topstepx-commissions-and-fees
- S&P 500-lukning 2026-10-07: 7.801,77 —
  https://cryptodaily.co.uk/2026/10/sp-500-slips-oil-102-treasury-yield-october-7-2026
- Screeningen: `research/output/b4_screening_2.md`
