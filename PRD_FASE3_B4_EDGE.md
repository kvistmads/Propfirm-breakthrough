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
| Sizing | Risikobåndet **6,4-7,1% af MLL ved p90** med 1 MNQ |
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

| krav | værdi | kilde |
|---|---|---|
| Instrument | MNQ | Besluttet, §2 |
| Kontrakter | **1** | 1 MNQ er udelelig. Sizing er afgjort |
| Risiko pr. handel | så den lander i **6,4-7,1% af MLL ved p90** | Fase 2 |
| R i dollar ved p90 | ~$125-140 | Afledt af ovenstående |
| Timeframe | **15m eller lavere** | §5c. 1h og 4h er ude |
| Gevinst/tab | 2:1 (B5 kan ændre det til 1,5:1) | RR-invarianten |
| Krævet win rate | **≥ ~40%**. Break-even er ~34% | §5 |
| Handler pr. dag | **1-3** | Modelantagelse. Afviger frekvensen, er §5's tal ugyldige |
| Session | **kun US RTH**, 08:30-15:00 CT | §3 |
| Sidste indgang | **14:30 CT** | §3 |
| Alt fladt | **14:50 CT** | §3 |
| Holde over lukningen | **umuligt** | Topstep kræver fladt 15:10 CT |
| Bedste dag | **≤ 55% af samlet profit** | Konsistensreglen |
| Nyheder | ingen maksimal position ind i planlagte større nyheder | Forbudt |
| Frekvensloft | ikke HFT; ikke hundredvis af handler dagligt med varighed i sekunder | SIM-fill-reglerne |
| Adfærd | **skal se disciplineret ud for en menneskelig anmelder** | Op-/nedkaldsprocessen |
| Eksekvering | ordreafsendelse fra Macen. VPS og VPN er forbudt | TopstepX API-vilkår |

**Tre af disse krav dræber flertallet af publicerede edges.** Time-series momentum måles på
månedsafkast. Overnight-anomalien kræver at man holder hen over lukningen. Tværsnitlige
aktieanomalier kan ikke udtrykkes i én kontrakt. **Det er ikke et argument mod litteraturen
— det er en filtrering af den.**

**Og frekvenskravet er strammere end det ser ud.** Én handel om ugen ødelægger spor B, som
kræver fem vindende *dage*. Tyve handler om dagen bryder omkostningsmodellen og nærmer sig
SIM-fill-reglerne. Båndet 1-3 er ikke en bekvemmelighed, det er en betingelse.

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
   parametersøgning.
3. **Holdout.** Forslag: **2019-05 til 2023-12 in-sample, 2024-01 og frem urørt** indtil
   hypotesen er frosset. Det er en beslutning der skal træffes eksplicit — og når den er
   truffet, må holdout-perioden ikke åbnes "bare lige for at se".
4. **Tæl hver kørsel.** Antallet af testede varianter rapporteres sammen med resultatet.
   Et p-værdi-agtigt tal uden tælleren er meningsløst.

### Kan vi så bare køre ti tusind strategier?

Ja. Og det er tilladt — **på én betingelse: at tælleren rapporteres og tærsklen hæves
tilsvarende.** Det er ikke en holdning, det er regnestykke.

Den forventede maksimale Sharpe blandt N rene støjstrategier under nulhypotesen er

    E[maks SR] = sigma_SR · [ (1 - g) · Z^-1(1 - 1/N) + g · Z^-1(1 - 1/(N·e)) ]

hvor `g` er Euler-Mascheronis konstant (0,5772) og `Z^-1` er den inverse
standardnormalfordeling. Formlen er Bailey og López de Prados; den er
implementeret i `research/multipletesting.py` som `expected_maximum_sharpe`.

| antal testede varianter | E[maks Sharpe] ved sigma_SR = 1 | tærsklen stiger med faktor |
|---|---|---|
| 3 | 0,853 | 1,00× (reference) |
| 10 | 1,575 | 1,85× |
| 100 | 2,531 | 2,97× |
| 1.000 | 3,255 | 3,82× |
| **10.000** | **3,861** | **4,53×** |

**En strategi fundet blandt 10.000 skal have fire en halv gange så høj observeret
Sharpe som en fundet blandt tre, for at være lige troværdig.** Det er den pris man
betaler for at søge bredt, og den er uundgåelig.

> **Rettet 2026-09-17.** Tabellen stod tidligere med `√(2 ln N)` og sluttede på
> 2,90× ved 10.000. Det var forkert. `√(2 ln N)` er kun rækkens førsteled, og ved
> N = 3 er man ingen steder nær det asymptotiske område: leddet overvurderer den
> absolutte tærskel med 75% ved N = 3 og 11% ved N = 10.000, og fordi nævneren
> rammer mest ved siden af, blev hele forholdet 36% for mildt. Prisen for bred
> søgning er altså større end PRD'en først skrev, ikke mindre.
>
> Verificeret tre gange uafhængigt af hinanden: numerisk integration af
> E[maks] = ∫ x·N·φ(x)·Φ(x)^(N-1) dx, Monte Carlo med 400.000 trækninger pr. N
> (40.000 ved N = 10.000), og den lukkede form ovenfor. De tre giver forholdet
> 4,551 / 4,551 / 4,527 ved N = 10.000 mod tre. Den gamle approksimation gav 2,895.

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

**Asiatisk og europæisk session som kontekst for US-sessionen.** Mads' observation; parkeret
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

**Andre indeksfutures (ES, YM, RTY og deres mikroer).** Mads vil gerne se om vi går glip af
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
- Rører ikke sizing. Båndet er afgjort.
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

Mads vil have en lang drøftelse af hypoteserne før noget skrives. Start der: hvilke
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
