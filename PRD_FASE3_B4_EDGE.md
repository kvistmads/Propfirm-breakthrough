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

| leverance | hvor |
|---|---|
| 3-5 hypoteser med skrevet mekanisme | `research/output/b4_hypoteser.md` |
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

**Hans egne idéer skal ikke valideres videnskabeligt for at komme i betragtning** — de
vurderes på om de kan automatiseres, om de passer ind, og hvor omfattende ændringen er.
Videnskabelig opbakning er et plus, ikke et krav. **Men kravet om en mekanisme gælder
uanset**, for det er ikke et videnskabskrav — det er værnet mod overfitting.

Først når hypoteserne står med hver sin mekanisme, skrives præregistreringen.
