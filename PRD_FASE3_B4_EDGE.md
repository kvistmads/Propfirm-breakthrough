# PRD — Fase 3: B4, edge-hypotesen (Combine)

**Skrevet:** 2026-09-17 af overblikssessionen, som overdragelse til en ny Cowork-session.
**Besvarer:** åbent spørgsmål **B4** i `STRATEGI_PROPFIRM.md`.
**Afgrænsning:** **kun Combine.** Spor B (XFA/funded) får sin egen session og sin egen fase.

> **Læs først:** `STRATEGI_PROPFIRM.md` (hele), `REGLER_VERIFICERET.md`, `ANTAGELSER.md`,
> `STRATEGI_DAYTRADING.md` (hvad der allerede er afprøvet og forkastet).
> Fase 1 og 2's rapporter ligger i `research/output/`.

---

## 1. Hvorfor denne fase er anderledes end de to før

Fase 1 og 2 målte noget der lå der i forvejen. Svaret var givet på forhånd; vi skulle bare
regne rigtigt. **B4 leder efter noget der måske ikke findes.**

Det ændrer den største risiko. I fase 1 og 2 var risikoen at regne forkert — og det fangede
vi, gentagne gange, med regressionstjek og genberegning. **I B4 er risikoen at finde noget
der ikke er der.** Syv års NQ-data indeholder mønstre nok til at bestå enhver backtest, hvis
man leder længe nok. Nulmodellen fanger held **inden for** én test. Den fanger ikke at man
har kørt to hundrede tests og rapporteret den bedste.

Der er kun ét forsvar mod det, og det er ikke statistisk: **at kunne svare på "hvorfor
betaler nogen mig for det her?" før man måler.** En mekanisme man kan formulere før testen
kan ikke være fundet af testen.

---

## 2. Hvor vi står

**Måleapparatet er færdigt.** Alt hvad en hypotese skal bruge for at blive målt findes:

| | |
|---|---|
| Data | NQ og MNQ fra 2019-05-06, 1m/3m/5m/15m, RTH og døgn adskilt. `data/cache/`, 116 filer |
| Omkostning | $2,627 pr. rundtur i RTH, dekomponeret. Kun slippage er stadig skøn |
| Sizing | Fase 2's bånd **6,4-7,1% af MLL ved p90** med 1 MNQ. **Genåbnet 2026-09-19** af disciplinreglerne: $250 pr. handel, se §3a og §3c |
| Ruinmodel | `research/mll_ruin.py`. Mekanik 1:1 med Combine, R trukket fra ATR-fordelingen |
| Nulmodel | Indbygget. Hver celle har sin egen break-even win rate |
| Regler | Alle verificeret ordret hos primærkilden |
| Tests | 219 passed, 6 skipped |

**Det eneste der mangler er en hypotese.** Alle tal i §5 hviler på en antaget win rate på
**40%** som ingen strategi har leveret. Nulmodellen i den valgte celle består 21,05% ved nul
edge. Forskellen mellem 21% og 80% *er* edgen — og den findes ikke endnu.

**B4 er ikke begyndt.** Ingen hypotese er formuleret, ingen test kørt.

---

## 3. Kravspecifikationen

Det her er fasens vigtigste afsnit. **En hypotese der ikke kan opfylde disse krav, skal
forkastes uden at blive testet** — uanset hvor god den ser ud.

Tider står i dansk tid med Chicago-tid (CT) i parentes. Topstep, CME og koden regner i CT,
som er én time efter New York. **I skifteugerne ligger alt en time tidligere i dansk tid** —
se `STRATEGI_PROPFIRM.md` §3.

| krav | værdi | kilde |
|---|---|---|
| Instrument | MNQ | Besluttet, §2 |
| Kontrakter | **Så mange som kan være inden for $250, rundet ned.** Følger stoppet, se §3c | Besluttet 2026-09-21 |
| Risiko pr. handel | **Højst $250 = 12,5% af MLL.** Rundes ned, aldrig op | Ejerens disciplinregler §3a; afrunding besluttet 2026-09-21 |
| Timeframe | **15m eller lavere** | §5c. 1h og 4h er ude |
| Gevinst/tab | **2:1-bracket som start.** Tidsexit og trailing kan komme senere | Besluttet 2026-09-19 |
| Break-even win rate | 33,33% brutto · **33,68% netto med 1 MNQ, 34,03% med 2** | Omkostning $2,627 pr. rundtur pr. kontrakt |
| Krævet win rate | **åben**, indtil ruinmodellen er kørt med reglerne i §3a-3b | De tidligere ~40% hørte til fase 2's bånd |
| Handler pr. dag | **0-2, højst én afgjort.** Intet signal → ingen handel | §3a |
| Session | **kun US RTH**, 15:30-22:00 dansk tid (08:30-15:00 CT) | §3 |
| Sidste indgang | **21:30 dansk tid** (14:30 CT) | §3 |
| Alt fladt | **21:50 dansk tid** (14:50 CT) | §3 |
| Holde over lukningen | **umuligt** | Topstep kræver fladt 22:10 dansk tid (15:10 CT) |
| Bedste dag | ≤ 55% af samlet profit. **Binder ikke:** bedste dag er højst +2R = $500 | Konsistensreglen |
| Nyheder | ingen maksimal position ind i planlagte større nyheder | Forbudt |
| Frekvensloft | ikke HFT; ikke hundredvis af handler dagligt med varighed i sekunder | SIM-fill-reglerne |
| Adfærd | **skal se disciplineret ud for en menneskelig anmelder** | Op-/nedkaldsprocessen |
| Eksekvering | ordreafsendelse fra Macen. VPS og VPN er forbudt | TopstepX API-vilkår |

**Tre af disse krav dræber flertallet af publicerede edges.** Time-series momentum måles på
månedsafkast. Overnight-anomalien kræver at man holder hen over lukningen. Tværsnitlige
aktieanomalier kan ikke udtrykkes i én kontrakt. **Det er ikke et argument mod litteraturen
— det er en filtrering af den.**

**Frekvensen er nu et statistisk spørgsmål, ikke et regelspørgsmål.** Dage uden handel er
tilladt (§3a), men testens styrke afhænger af det *gennemsnitlige* antal handler. Vejledende
mindste detekterbare win rate ved break-even 33,97%, α = 0,05, 80% styrke og 1.173
in-sample-dage — normalapproksimation, uafhængige handler, før deflation:

| handler_pr_dag, gennemsnit | n_handler | MDE_WR_pct |
|---|---|---|
| 1 | 1.173 | 37,4 |
| 0,5 | 586 | 38,9 |
| 0,2 (én om ugen) | 234 | 41,8 |

En hypotese der fyrer sjældent kan altså ikke skelnes fra nul, selv hvis den er sand. Det
rigtige tal regnes pr. hypotese og præregistreres (metoderegel 3).

---

### 3a. Disciplinreglerne — ejeren, 2026-09-19

Ejerens egne regler. De vurderes efter metoderegel 9 (kan de automatiseres, passer de ind,
hvor omfattende er ændringen), ikke videnskabeligt. Ordret:

> "You're going to buy a 50K account. You're going to risk 250 per trade. […] If you take
> a win, you get off. If you take a loss, you get off. If you take two break evens, you get
> off the charts and you journal every day."

| regel | i botten |
|---|---|
| Risiko $250 pr. handel | Fast dollarrisiko. Kontrakter og stop, se §3c |
| Gevinst → stop for i dag | Første afgjorte handel lukker dagen |
| Tab → stop for i dag | Samme |
| To break-evens → stop for i dag | Højst to handler om dagen. Reglen er kun aktiv hvis stoppet flyttes til BE (§3b) |
| Journal hver dag | Dagsloggen. Hører under `logning` i tjeklisten, §6 |

**Vurdering.** Kan automatiseres uden besvær: en dagstilstand med to tællere. Passer ind:
værste dag er −$250 plus omkostninger, bedste dag +$500, så hverken konsistensreglen eller
DLL'en binder nogensinde, og adfærden ser disciplineret ud for en anmelder. **Omfanget ligger
i fase 2:** båndet 6,4-7,1% af MLL og beståelsesraterne i `STRATEGI_PROPFIRM.md` §5 er
regnet ved 1-3 handler om dagen. Reglerne ændrer frekvensen, og dermed er §5 genåbnet.
Ruinmodellen skal køres med reglerne før dens tal bruges igen.

**Funded:** $250 indtil bufferen er $3.000, derefter $300 ved $3.000, $400 ved $4.000,
$500 ved $5.000 og videre. Hører til spor B (B7), ikke til denne fase.

### 3b. Tradeforvaltning i live — besluttet 2026-09-19

Et selvstændigt punkt: hvad der sker med en åben handel.

**Break-even.** Ejerens regel: når prisen har tilbagelagt 60% af vejen til TP, flyttes stoppet
til indgangen. Ved 2:1 er det +1,2R.

**Det testes om BE overhovedet hjælper**, som tre varianter der alle tæller med i tælleren:
ingen BE · BE ved +1,0R · BE ved +1,2R.

**Falsifikationskriteriet kan formuleres før data.** Flytningen ændrer kun de handler der
når triggeren og derefter vender tilbage til indgangen. Uden BE ville de ende i SL (−1R), i
TP (+2R) eller blive lukket 21:50. BE hjælper hvis de handler i gennemsnit ender under nul
uden BE — groft: hvis mere end dobbelt så mange ender i SL som i TP.

To ting modellen skal have med:

- **BE er ikke 0.** Det er minus omkostning minus slippage på stoppet (C4).
- **Ruinmodellen skal have et tredje udfald.** Den regner i dag binært vind/tab.

Topsteps SIM-fill-regler nævner auto-breakeven, men tærsklen er hundredvis af handler om
dagen. Ved 0-2 handler binder den ikke.

> **Kilde til idéen.** Iagttagelsen om at prisen "lige akkurat ikke rammer TP" stammer fra
> REAL TRADING BOT og hører til det projekt. Den bruges ikke som evidens her. BE testes på
> sine egne præmisser.

**Trailing stop** er en kandidat til samme punkt, ikke besluttet. Den løser ikke problemet
i §3c — trailing styrer udgangen, mens problemet dér er hvor stoppet står ved indgangen.

**Tidsexit.** Udfladningen 21:50 er altid et tredje udfald, også i en ren bracket. Andelen
af handler der lukkes på uret skal måles pr. hypotese.

### 3c. Kontrakter og stop

**Besluttet 2026-09-21:**

- **Indtil der findes en strategi, er stoppet ATR-baseret.** Når en hypotese findes, sætter
  signalet stoppet.
- **Kontrakter = det antal der kan være inden for $250, rundet ned.** $250 er et loft, ikke et
  mål. Handler hvor ét MNQ alene ville risikere mere end $250, tages ikke.
- **Åbent:** ATR-multipel og timeframe for pladsholder-stoppet.

Konsekvens, med 1 × 15m-ATR som eksempel: en typisk dag (ATR 67,6 point) giver 1 MNQ og
$135 i risiko — tæt på fase 2's bånd. Rolige dage med ATR under 62,5 point giver 2 MNQ og op
til $250. Når ATR er over 125 point, gives der ingen handel; det gælder lidt over 10% af
15m-barerne i RTH, da p90 er 133,7 point. Alle pointtal er ved NQ 29.138. **Risikoen bliver altså trinvis og følger volatiliteten, og $250 nås kun
på de rolige dage.** Det skal med i genkørslen af ruinmodellen.

Tabellerne nedenfor er grundlaget for beslutningen.


$250 i risiko kan udtrykkes på to måder indtil signalet selv sætter stoppet. ATR er 15m RTH
ved NQ 29.138: p50 67,6 point, p90 133,7 point.

| | A: 1 MNQ | B: 2 MNQ |
|---|---|---|
| stop_pt | 125 | 62,5 |
| TP_pt ved 2:1 | 250 | 125 |
| stop_ATR, rolig dag (p50) / urolig dag (p90) | 1,85 / 0,93 | 0,92 / 0,47 |
| omk_usd_rundtur | 2,63 | 5,25 |
| omk_R | 0,0105 | 0,0210 |
| be_WR_pct, brutto / netto | 33,33 / 33,68 | 33,33 / 34,03 |

Begge står fast i point uanset dagens volatilitet. Vælges A, skal andelen der lukkes 21:50
måles, fordi målet på 250 point er 3,7 gange median-ATR.

**Når signalet sætter stoppet**, kan $250 kun rammes præcist hvis stoppet passer i hele
kontrakter — 125, 62,5, 41,7, 31,3 … point. Ellers skal der rundes:

| signalets stop_pt | MNQ rundet ned | risiko_usd rundet ned | MNQ rundet op | risiko_usd rundet op |
|---|---|---|---|---|
| 125 | 1 | 250 | 1 | 250 |
| 100 | 1 | 200 | 2 | 400 |
| 80 | 1 | 160 | 2 | 320 |
| 68 (median-ATR) | 1 | 136 | 2 | 272 |
| 55 | 2 | 220 | 3 | 330 |
| 40 | 3 | 240 | 4 | 320 |
| 30 | 4 | 240 | 5 | 300 |

Afrundingen rammer hårdest mellem 62,5 og 125 point — præcis hvor et stop på omkring 1 ATR
ligger. Tre muligheder blev overvejet: ned ($250 er et loft, gennemsnittet ligger under), op
(risikoen overstiger $250 på nogle handler), eller stoppet flyttes ud til nærmeste hele
kontrakt (præcis $250, men så sætter signalet ikke længere stoppet). **Valgt: ned**, fordi
reglen handler om at begrænse tabet.

---

## 4. Den største risiko, og hvordan den holdes nede

**Multiple comparisons.** Vi har én stikprøve på syv år. Hver hypotese vi tester, hvert
parameterinterval vi prøver, hvert instrument vi tilføjer, ganger antallet af chancer for
at finde støj der ligner en edge.

Fire kontroller, som skal besluttes i den nye sessions første samtale og derefter
præregistreres:

1. **Mekanisme før måling.** Hver hypotese skal have et skrevet svar på "hvorfor betaler
   nogen mig for det her?" **før** den kodes. Kan spørgsmålet ikke besvares, testes den ikke.
2. **Få hypoteser, ikke et sweep.** Tre til fem præregistrerede hypoteser. Ikke en
   parametersøgning. **Undtagelse besluttet 2026-09-22:** kandidat 1 (supply og demand) får
   en filtersøgning oven på en fast kerne — på betingelse af at hver kombination tælles,
   at søgningen kun ser in-sample, og at vinderen vurderes med deflateret tærskel og PBO.
   Se `research/output/b4_hypoteser.md`.
3. **Holdout. Besluttet 2026-09-22: in-sample 2016-01-01 til 2023-12-31, holdout fra
   2024-01-01.** In-sample starter samme sted som ATR- og sizing-grundlaget fra fase 1 og
   dækker 2018, covid-krakket og bjørnemarkedet i 2022. Holdout er 676 handelsdage og åbnes
   én gang, for en frosset hypotese. **Forseglingen ligger i koden:** `data/holdout.py`
   åbner aldrig en holdout-fil fra in-sample, og holdout kan kun læses for en committet,
   uændret hypotesefil. Hver åbning logges i `research/output/holdout_log.md`.
   `tests/test_holdout.py` fejler hvis B4-kode læser prisdata uden om modulet.
4. **Tæl hver kørsel.** Antallet af testede varianter rapporteres sammen med resultatet.
   Et p-værdi-agtigt tal uden tælleren er meningsløst.

### Kan vi så bare køre ti tusind strategier?

Ja. Og det er tilladt — **på én betingelse: at tælleren rapporteres og tærsklen hæves
tilsvarende.** Det er ikke en holdning, det er regnestykke.

Den forventede maksimale Sharpe blandt N rene støjstrategier under nulhypotesen er
forventningen til maksimum af N uafhængige standardnormale:

    E[maks] = ∫ x · N · φ(x) · Φ(x)^(N-1) dx

**Definitionen integreres numerisk, og det er den autoritative metode her.**
Implementeringen er `research/maks_sharpe.py`, funktionen `forventet_maks_sharpe`:
Simpsons regel på intervallet ±12, hvor gitteret fordobles indtil to på hinanden
følgende værdier er enige til 1e-11. Konvergensen er altså målt ved kørslen, ikke
antaget. Ingen scipy — `math.erfc` gennem `research/normal.py`.
`tests/test_maks_sharpe.py` fastholder tallene mod referenceværdier beregnet i 50
decimaler med mpmath, så tabellen ikke kun står i et dokument. Den kan genskabes med

    .venv/bin/python -m research.maks_sharpe

| antal testede varianter | E[maks Sharpe] ved sigma_SR = 1 | tærsklen stiger med faktor |
|---|---|---|
| 3 | 0,846 | 1,000× (reference) |
| 10 | 1,539 | 1,818× |
| 100 | 2,508 | 2,963× |
| 1.000 | 3,241 | 3,830× |
| **10.000** | **3,852** | **4,551×** |

**En strategi fundet blandt 10.000 skal have fire en halv gange så høj observeret
Sharpe som en fundet blandt tre, for at være lige troværdig.** Det er den pris man
betaler for at søge bredt, og den er uundgåelig.

> **Rettet 2026-09-17, og igen 2026-09-18.**
>
> Tabellen stod først med `√(2 ln N)` og sluttede på 2,90× ved 10.000. Det var
> forkert. `√(2 ln N)` er kun rækkens førsteled, og ved N = 3 er man ingen steder
> nær det asymptotiske område: leddet overvurderer den absolutte tærskel med 75%
> ved N = 3 og 11% ved N = 10.000, og fordi nævneren rammer mest ved siden af,
> blev hele forholdet 36% for mildt.
>
> Den 17. blev tabellen sat til Bailey og López de Prados lukkede form,
> `(1 - g)·Z⁻¹(1 - 1/N) + g·Z⁻¹(1 - 1/(N·e))`. Den 18. blev den sat til numerisk
> integration af definitionen, som er det den lukkede form approksimerer.
> Forskellen mellem de to er lille, men den er ikke ensrettet: den lukkede form
> ligger **−7,9% ved N = 2, +0,77% ved N = 3, +2,5% ved N = 5** og derefter
> faldende til **+0,24% ved N = 10.000**. Fejlen topper altså midt i det interval
> vi selv bruger, og skifter fortegn under det. En approksimation der opfører sig
> sådan er et dårligt grundlag for et *forhold* mellem to tærskler, og forholdene
> er det denne tabel handler om.
>
> Den lukkede form bliver stående i `research/multipletesting.py`. Det modul er
> lånt uændret og rettes ikke (`research/LAANTE_MODULER.md`) — afvigelsen mellem
> de to er i stedet fastholdt i en test, så ingen senere bytter dem om i den tro
> at de giver det samme.
>
> Værdierne er efterprøvet uafhængigt af implementeringen: mod mpmath i 50
> decimaler (afvigelse under 1e-13 på alle fem rækker), mod den lukkede form for
> N = 2, hvor svaret er 1/√π, og mod Monte Carlo-kørslen fra den 17., der gav
> forholdet 4,551 ved N = 10.000.

Det praktiske problem er ikke at søge. Det er at søge og **ikke tælle**. En bred søgning
hvor tælleren rapporteres er legitim videnskab. En bred søgning hvor man husker vinderen og
glemmer de 9.999 andre er selvbedrag med en pæn graf.

**Metoderne findes og er veludviklede:** Deflated Sharpe Ratio og Probability of Backtest
Overfitting (Bailey & López de Prado), White's Reality Check og Hansens SPA-test, og
purged/embargoed walk-forward. Harvey, Liu og Zhu argumenterede for at en t-værdi på 3 —
ikke 2 — bør være minimum for et nyt faktorfund, netop på grund af den samlede mængde
afprøvninger i litteraturen.

**For vores stikprøve er konklusionen praktisk, ikke principiel.** Med 1-3 handler dagligt
over syv år har vi størrelsesordenen 5.000-10.000 handler. En edge der skal klare en
10.000-forsøgs-deflation på den stikprøve skal være meget stor — større end noget vi
realistisk forventer. **Derfor søger vi smalt: ikke fordi bred søgning er forbudt, men
fordi vores data ikke kan bære regningen.**

### En prøvestand, men ikke endnu

Et værktøj der automatiserer det her er værd at bygge — og dets vigtigste egenskab er ikke
søgningen, det er **bogholderiet**:

- afviser en hypotese der bryder kravspecifikationen i §3, før den overhovedet testes
- **tæller hver eneste kørsel automatisk**, så tælleren ikke afhænger af hukommelse
- håndhæver purged walk-forward, så der ikke lækker information mellem folder
- beregner den deflaterede tærskel ud fra tælleren
- holder holdout-perioden forseglet

**Men byg den ikke først.** Kør to-tre hypoteser i hånden, så vi ved hvad den gentagne del
faktisk er. Bygger vi prøvestanden før vi kender formen, bygger vi den til det forkerte.

**Mindste detekterbare forskel beregnes før testen** — metoderegel 3. Med 1-3 handler om
dagen over syv år har vi størrelsesordenen 5.000-10.000 handler. Hvor lille en edge kan vi
overhovedet skelne fra nul med den stikprøve? **Det tal skal ligge på bordet før første
kørsel**, for det afgør om testen kan svare på spørgsmålet.

---

## 5. Sådan testes en hypotese

Én ad gangen, samme sløjfe hver gang:

1. **Mekanisme** skrives ned. Hvem taber pengene, og hvorfor bliver de ved?
2. **Falsifikationskriteriet præregistreres** i `research/prereg/` og **committes før
   kørslen** — metoderegel 13.
3. **MDE beregnes** og skrives i præregistreringen.
4. **Én kørsel.** Ingen justering undervejs.
5. **Stop.** Resultatet læses i overblikssessionen før noget ændres — metoderegel 8.
6. **Nulmodellen ved siden af**, altid, ved cellens egen break-even win rate — metoderegel 12.

Og den afgørende: **strategien måles ikke på beståelsesrate alene, men på forskellen til
nulmodellen med adskilte konfidensintervaller.** En beståelsesrate på 80% lyder godt, indtil
man opdager at nul edge giver 21% ved samme sizing.

---

## 6. Hvad fase 3 skal levere

Hver hypotese der overlever samtalen, specificeres efter denne tjekliste — lånt fra
AlphaInsiders strategy-creator og udvidet med vores egne krav. **En hypotese er ikke færdig
før alle ti punkter har et svar**, også hvis svaret er "ikke relevant, fordi…":

`instrumenter` · `signaler` · `data` · `timing` · `eksekvering` · `sizing` · `afstemning` ·
`risiko` · `genopretning` · `logning`

De tre der plejer at blive glemt er **afstemning** (stemmer botten sin egen positionsopgørelse
mod brokerens?), **genopretning** (hvad sker der efter et nedbrud midt i en position?) og
**logning** (kan vi bagefter se hvorfor den handlede?). De tre er også dem der afgør om
strategien kan drives, ikke bare om den virker.

| leverance | hvor |
|---|---|
| 3-5 hypoteser med skrevet mekanisme og udfyldt tjekliste | `research/output/b4_hypoteser.md` |
| Beslutning om holdout-periode | Samme dokument, præregistreret |
| MDE for den valgte stikprøve | Samme |
| Præregistrering pr. hypotese | `research/prereg/` |
| Resultat pr. hypotese, med nulmodel og CI | `research/output/` |
| **Kompakt tabel i chatten** | Ved hver kørsel |

**Fasen lykkes hvis mindst én hypotese overlever sit eget præregistrerede kriterium.**
Den lykkes også — på en anden måde — hvis ingen gør det, forudsat at vi kan sige hvorfor.
**En fase der forkaster fem hypoteser ærligt er mere værd end en der accepterer én
uærligt.**

---

## 7. Parkerede kandidater

**Asiatisk og europæisk session som kontekst for US-sessionen.** Ejerens observation; parkeret
2026-09-13 som B4-kandidat. Status efter gennemgang:

- **Målbart og sandt:** volatiliteten er stærkt sessionsafhængig. Vi har målt det selv —
  15m ATR er 0,232% i RTH mod 0,132% over døgnet.
- **Rimeligt understøttet:** foregående sessions high/low fungerer som referenceniveauer, og
  opening-range-breakout-forskning finder at natrangen har informationsværdi.
- **Folklore:** den deterministiske AMD-fortælling (Asien akkumulerer, London manipulerer,
  New York distribuerer) har ingen uafhængig empirisk støtte. Ingredienserne er virkelige,
  tre-akts-strukturen er en efterrationalisering.
- **Testbar formulering:** *bærer den asiatiske sessions range information om US-sessionen ud
  over hvad gårsdagens US-luk og realiseret volatilitet allerede fortæller?*

**Andre indeksfutures (ES, YM, RTY og deres mikroer).** Ejeren vil gerne se om vi går glip af
noget. To forbehold, begge skal håndteres før det køres:

1. **Det ganger multiple-comparison-problemet med fire.** Testes en hypotese på fire
   instrumenter, skal det stå i tælleren, og tærsklen skal justeres. Ellers finder vi en
   "edge" på ét instrument ud af fire, hvilket er hvad ren støj også gør.
2. **Det koster penge.** Databento-udtræk for ES/YM/RTY er nye kontrakter. Estimat hentes
   gratis først, og budgetvagten spørger.

Rækkefølgen bør være: **find noget på MNQ først, brug derefter de andre instrumenter som
uafhængig bekræftelse.** Det er en langt stærkere test end at søge på fire ad gangen.
Besluttet 2026-09-17.

### AlphaInsider — værktøjet nej, arbejdsformen ja

Gennemgået to gange 2026-09-17. Første gennemgang var for overfladisk og afviste for meget.

**Værktøjet kan vi ikke bruge.** Markedspladsen dækker **aktier og krypto, ingen futures**,
og genererede strategier har AlphaInsider som eneste destination for papirordrer. Vi skal
til TopstepX. Broker-tilsluttede bots hos tredjepart passer desuden dårligt med Topsteps
krav om at ordreafsendelse sker fra egen maskine.

**Strategibiblioteket: brug mekanismerne, aldrig tallene.** En offentlig markedsplads
rangeret efter afkast er den reneste multiple-comparison-maskine der findes — tusindvis
publicerer, og de overlevende ser strålende ud af ren konstruktion. Vi kender ikke deres N.
At overtage en strategi *fordi den har klaret sig godt* er at arve en fremmed
selektionsbias. At låne en **idé om en mekanisme** og teste den selv på vores data er
derimod helt legitimt, og biblioteket er gratis at kigge i.

**Arbejdsformen i `alphainsider-strategy-creator` er værd at stjæle fra.** Den er et
interviewdrevet specifikationsværktøj, ikke en edge-finder, og tre ting i den er gode:

1. **"Frontier rounds":** den spørger kun til de beslutninger der er *aktuelt oplåste*, og
   udleder efter hver runde hvilke der så er blevet oplåste. Bedre end et fladt spørgeskema,
   fordi tidlige svar ændrer hvilke senere spørgsmål der overhovedet giver mening.
   **Brug den struktur i hypotesesamtalen.**
2. **Fuldstændighedstjeklisten:** instrumenter · signaler · data · timing · eksekvering ·
   sizing · **afstemning** · risiko · **genopretning** · **logning**. De tre fremhævede har
   vi kun spredt i C-listen. De hører i strategispecifikationen fra starten.
3. **Backtest tilbydes kun når de historiske input kan rekonstrueres uden fremtidig
   information.** Det er en look-ahead-spærre formuleret som en *forudsætning for at køre
   testen*, ikke som et tjek bagefter. Skarpere end vores egen formulering.

To ting gør den allerede som vi gør: den implementerer ikke før planen er bekræftet
(metoderegel 8), og den nedskriver den bekræftede beslutning i en plan-fil (vores
præregistrering). Uafhængig bekræftelse af at formen er rigtig.

**Konklusion: ingen installation, ingen nøgler, intet abonnement. Vi låner tre ting fra
arbejdsformen og ser i biblioteket efter idéer — ikke efter resultater.**

---

## 8. Hvad fase 3 IKKE gør

- Bygger ikke en runner eller en live-bot.
- Optimerer ikke sizing. Risikoen er $250 (§3a); afrundingsreglen og 1 mod 2 MNQ afgøres når signalet sætter stoppet (§3c). Genkørslen af ruinmodellen med disciplinreglerne planlægges for sig.
- Optimerer ikke parametre. En parametersøgning *er* multiple comparisons.
- Modellerer ikke XFA. Det er spor B og en anden fase.
- Åbner ikke holdout-perioden før hypotesen er frosset.

---

## 9. Arbejdsform

Overblikssessionen holder den røde tråd og skriver PRD'er. Denne fase udføres af en ny
Cowork-session med sin egen Code-session til kodearbejdet. Nye branches pr. fase.

De faste regler står i `STRATEGI_PROPFIRM.md` §7 og §8. De fire der oftest glemmes:
`git --no-optional-locks` på alle git-kald · kommandoblokke uden `#`-kommentarer ·
kompakt tabel i chatten ved hvert resultat · aldrig nøgleværdier i chatten.

---

## 10. Første skridt i den nye session

**Ikke kode. En samtale.**

Ejeren vil have en lang drøftelse af hypoteserne før noget skrives. Start der: hvilke
kandidater har han selv, hvad er mekanismen bag hver enkelt, og hvilke overlever
kravspecifikationen i §3.

**Før samtalen i frontier-runder**, ikke som et fladt spørgeskema: stil kun de spørgsmål
der er aktuelt oplåste, og udled efter hvert svar hvilke der så giver mening. Et valg af
mekanisme ændrer hvilke spørgsmål om timing og eksekvering der overhovedet er relevante.

**Hans egne idéer skal ikke valideres videnskabeligt for at komme i betragtning** — de
vurderes på om de kan automatiseres, om de passer ind, og hvor omfattende ændringen er.
Videnskabelig opbakning er et plus, ikke et krav. **Men kravet om en mekanisme gælder
uanset**, for det er ikke et videnskabskrav — det er værnet mod overfitting.

Først når hypoteserne står med hver sin mekanisme, skrives præregistreringen.
