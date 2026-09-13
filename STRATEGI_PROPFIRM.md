# Propfirm-sporet

**Status:** 2026-09-13. **Fase 1 er kørt.** Der er MNQ-data i repoet fra 2019-05-06,
ATR er målt som fordeling pr. timeframe og session, spread er målt, og K1-K4 holdt.
**A1-A6 og B1-B3 er besvaret.** §5 er skrevet om på de målte tal og **sizing-valget er
genåbnet** — det gamle valg stod på et ATR-tal der var for lavt. Ingen konto åbnet, ingen
strategi bygget, ingen edge fundet.

Søsterdokumenter: `ANTAGELSER.md` (hvilke tal er verificeret og hvilke er gæt),
`PRD_FASE2_RUINMODEL.md` (næste fase), `PRD_FASE1_DATAGRUNDLAG.md` (kørt),
`STRATEGI_TSMOM.md`, `STRATEGI_DAYTRADING.md`.

---

## 0. Invarianter

Regler der gør alle tabeller i dokumentet forkerte hvis de brydes. De står her og ikke i
en fodnote, fordi de er stille fejl — man ser dem ikke i et resultat.

> **RR-invarianten.** Alt i dette dokument regner med **2:1**. Ved 2:1 og målt omkostning
> 0,0192 R på 15m RTH er break-even 33,97%. Ved 1,5:1 er den ~40%. **Tal fra en 2:1-tabel
> må aldrig læses sammen med tal fra en 1,5:1-tabel.** Ændres RR, skal hver eneste tabel
> regnes om — ikke justeres.

> **Kanal-invarianten.** En gebyrsats tæller først når den er verificeret for den kanal
> botten faktisk bruger. Fanget to gange: MEXC (web mod API) og MNQ (Tradovate Free mod
> TopstepX).

> **Enheds-invarianten.** Enheden står i kolonnenavnet. `omk_R_netto`, ikke `omk`.

> **Estimat-invarianten.** Et punktestimat sizes der ikke efter. Fordelinger rapporteres
> som 10./50./90. percentil, og go/no-go vurderes på den ende hvor det gør ondt.

---

## 1. Hvad sporet er

Et handelssystem der skal igennem Topsteps tre trin og derefter tjene penge på
propfirmaets kapital.

**To strategier, tre konfigurationer.** Antallet af strategier følger antallet af
*målfunktioner*, ikke antallet af konti:

| spor | konti | målfunktion | tabsfunktion |
|---|---|---|---|
| **A — eval** | Combine | Nå +$3.000 før −$2.000 (trailende gulv) | Fejl koster et gebyr. Må være aggressiv |
| **B — indtjening** | XFA, derefter LFA | Producér vindende dage à $150+ og tag payouts | Fejl koster kontoen. Skal være defensiv |

XFA og LFA deler målfunktion — vindende dage → payout. De adskiller sig kun på gulvet
($2.000 trailende der låser ved $0, mod $1.000 fast) og på om markedet er rigtigt. **Det
er en risikoparameter, ikke en strategi.** Derfor to strategier med tre
risikokonfigurationer, ikke tre strategier.

**A optimerer en strækning. B optimerer en gentagen daglig tærskel.** Det er den
væsentlige forskel, og den har konsekvenser helt ned i valget af timeframe (§5).

### Afgrænsning

- **Nyt repo.** Begrundelsen er Mads' egen: "knald eller fald, en forkert fejl på det
  forkerte tidspunkt, konto død."
- **Apparatet kopieres, deles ikke.** Gennemført — se §6.
- **De 5-10K egen kapital er ikke en del af dette spor.**

---

## 2. Beslutninger truffet

| Spørgsmål | Valg |
|---|---|
| Kapital | Udelukkende propfirm-kapital |
| Firma | Topstep er førstevalg, ikke låst |
| Kontostørrelse | **$50K** |
| Instrument | **MNQ** (mikro Nasdaq) |
| Antal strategier | **To** (spor A og B), tre risikokonfigurationer |
| Sizing, spor A | **1 MNQ, 1-ATR-stop** (§5) |
| Timeframe | **15m eller lavere.** 1h og 4h er udelukket — se §5 |
| Daily Loss Limit | Slået til ($1.000 i Combine) |
| Ruinmål | Drawdown, 1:1 med Topsteps egen mekanik |
| Autonomi | Backtest og paper-forward **fuldauto**; funded live **semi**. Combine-fasen ikke afgjort |
| Session | US RTH som udgangspunkt; døgndrift skal måles før den vurderes |
| RR | 2:1 — **antaget, ikke målt.** Se B5 |

---

## 3. Topsteps tre trin

Verificeret 2026-09-09/10. **Vi talte hidtil om "eval" og "funded" som to trin. Der er
tre, og de har fundamentalt forskellig risikogeometri.**

| trin | konto | penge | startsaldo | MLL | trailer MLL? |
|---|---|---|---|---|---|
| **1. Trading Combine** | simuleret | abonnement, ingen udbetaling | $50.000 | $2.000 | Ja — på dagsslutsaldo, låser ved startsaldo |
| **2. Express Funded (XFA)** | **simuleret, men rigtige udbetalinger** | 90% til dig | $0 | $2.000 | Ja — låser permanent ved $0 når saldo når $2.000 |
| **3. Live Funded (LFA)** | **rigtige markeder** | 90% + bonusser | 20% af samlet saldo, resten frigives i trin | **$1.000** | **Nej. Fast gulv** |

**Trin 2 er hvor pengene begynder, og den er stadig simuleret.** Man kan tjene rigtige
penge uden nogensinde at røre et live-marked.

### Hvad hvert trin kræver

| trin | krav |
|---|---|
| Combine | Nå $3.000. Bedste dag ≤ 50% af profitmålet, ellers **hæves** målet. Min. 2 handelsdage |
| XFA | **5 vindende dage à $150+ net.** Derefter payout på op til 50% af saldo, maks $5.000, min $125. Efter hver payout nulstilles tælleren og MLL låses på $0 |
| LFA | 5 benchmark-dage à $150+ pr. cyklus. 50% af saldo indtil 30 benchmark-dage, derefter 100% én gang pr. hverdag |

### Konsekvensen for strategidesign

**Combine belønner en strækning. XFA og LFA belønner en tærskel.**

På Combine skal man samle $3.000 op mod et gulv der følger med op. På XFA skal man lave
**fem dage med mindst $150 net** — og med 1 MNQ på 2:1 er én vinder $199. Én ren vinder på
en dag *er* en vindende dag. Markant lavere barre, og den favoriserer en anden adfærd:
tag gevinsten, luk dagen, gentag.

Efter første payout er XFA-gulvet $0. Man kan derefter aldrig tabe mere end det der står
på kontoen. **Trin 2 er et mildere regime end evalueringen, ikke et hårdere.**

**Og spor B har en nedre grænse for handelsfrekvens som spor A ikke har.** Fem vindende
*dage* kan ikke produceres af en strategi der handler én gang om ugen. Det binder
timeframe-valget — se §5.

### Automatisering og hvor koden kører

> "Custom automated strategies and bots are allowed via the TopstepX / ProjectX API,
> subject to standard platform rules and our prohibition on high-frequency trading (HFT)."

> "All trading activity must originate from your personal device. The use of VPS, VPNs,
> and remote servers is prohibited by Topstep's Terms of Use."

Ingen sandbox — "API orders are final". Ingen support på implementeringen. Macens oppetid
er en del af strategien og skal løses før første live-handel.

### MLL-mekanikken på de trailende trin

| | |
|---|---|
| MLL **trailer** på | **dagsslutsaldo**. Aldrig nedad |
| MLL **låser** | Combine: ved startsaldo ($50.000, dvs. dagsslut $52.000). XFA: ved $0 |
| MLL **brydes** på | **net P&L i realtid, urealiseret tæller med** → øjeblikkelig likvidering |
| Intradag give-back | tæller **ikke** mod trailet. Kun mod bruddet |

**Trailet er dagsslut, bruddet er realtid.** Topstep er ikke intraday-trailing: et løb til
+$800 der gives tilbage til +$300 koster ingenting i gulv.

Risikoen er ikke jævnt fordelt over de $3.000 i Combine:

| fase | saldo_$ | luft_til_MLL_$ |
|---|---|---|
| start | 50.000 | 2.000 |
| under opbygning | 50.000–52.000 | altid ~2.000 — gulvet følger med op |
| efter lås | > 52.000 | saldo − 50.000, vokser frit |
| profitmål nået | 53.000 | 3.000 |

To tredjedele af eval-løbet ligger i det stramme felt.

### Daily Loss Limit — ikke det samme som MLL

| grænse | Combine $50K | LFA | konsekvens ved brud |
|---|---|---|---|
| Maximum Loss Limit | 2.000, trailende | 1.000, fast | konto død |
| Daily Loss Limit | 1.000, **valgfri** | dynamisk med saldo | positioner flades, pause til næste dag. **Ikke** et regelbrud |

**Ved 1-3 mikroer binder DLL'en aldrig.** Værste dag ved 3 kontrakter × 3 handler er $918.

### Handelsdøgnet og fladningsreglen

Verificeret hos Topstep 2026-09-12. **Dette er en hård regel, ikke en anbefaling, og den
skal ligge i koden.**

> "All positions must be closed by 3:10 PM CT every weekday." Risikoafdelingen begynder at
> flade konti kl. **15:08 CT**. Handel genoptages kl. **17:00 CT**.
> "Topstep is a day trading program" — swingpositioner findes ikke.

| | CT | dansk tid (sommer, 7t) | dansk tid (vinter, 6t) |
|---|---|---|---|
| Handelsdøgnet åbner | 17:00 | 00:00 | 23:00 |
| US RTH åbner | 08:30 | 15:30 | 14:30 |
| US RTH lukker | 15:00 | 22:00 | 21:00 |
| Topstep begynder at flade | 15:08 | 22:08 | 21:08 |
| **Alt skal være fladt** | **15:10** | **22:10** | **21:10** |

Forskydningen er 7 timer det meste af året og 6 timer i den uge omkring slutningen af
oktober hvor USA og EU skifter sommertid på forskellige datoer. **Koden skal regne i
America/Chicago og konvertere, ikke hardkode 22:10.**

**Børsen selv er åben ~23 timer i døgnet** (CME Globex, verificeret hos CME 2026-09-13).
Det er to forskellige ting: børsens åbningstid og Topsteps regel. Topsteps deadline ligger
fem minutter før børsens eftermiddagspause:

| CME Globex, aktieindeks | CT | dansk tid (sommer) |
|---|---|---|
| Åbner | 17:00 | 00:00 |
| US RTH | 08:30–15:00 | 15:30–22:00 |
| **Topstep: alt fladt** | **15:10** | **22:10** |
| 15-minutters handelspause | 15:15–15:30 | 22:15–22:30 |
| Handler igen, samme handelsdag | 15:30–16:15 | 22:30–23:15 |
| Vedligeholdelseslukning | 16:15–17:00 | 23:15–00:00 |

Topstep spærrer altså kun 1t50m, og børsen er selv lukket eller i pause i en stor del af
det. **Reelt forbudt handelstid vi ellers kunne bruge: ~50 minutter i døgnet.**

**Fladt betyder nul åbne positioner.** Ikke reducerede, ikke hedgede. Åbne ordrer bør også
annulleres, så intet fyldes ind i fladningsvinduet.

Tre konsekvenser der ikke er indlysende:

1. **Vinduet uden handel er ~1t50m, ikke et døgn.** Fra 22:10 til 00:00 dansk tid. Resten
   af døgnet må der handles.
2. **Topsteps handelsdøgn starter kl. 17:00 CT, ikke ved midnat.** En position åbnet
   kl. 02:00 dansk tid og lukket kl. 20:00 samme dag er **én intradag-handel** i Topsteps
   regnskab — ikke en overnight-position. Der er ingen regel om at natpositioner skal
   lukkes ved RTH-åbning. Reglen er kun deadline'en kl. 15:10 CT.
3. **Men vores egen regel bliver strammere.** En position der holdes fra natten og ind
   over RTH-åbningen er eksponeret mod døgnets kraftigste bevægelse med et gulv der
   brydes på urealiseret P&L i realtid. Det er ikke forbudt af Topstep; det er bare en
   dårlig idé, og det skal afgøres af måling og ikke af mavefornemmelse (C8).

### Vores egen dagsafslutningsregel — besluttet 2026-09-13

Strammere end Topsteps, og med lag frem for én timer. **Alle klokkeslæt regnes i
America/Chicago og konverteres. Intet hardkodes i dansk tid.**

| lag | CT | dansk (sommer) | hvad |
|---|---|---|---|
| Handelsvindue | 08:30–15:00 | 15:30–22:00 | **Kun US RTH.** Ingen indgange uden for |
| Sidste indgang | **14:30** | **21:30** | Ingen nye positioner efter dette. Åbne må løbe |
| **Hård udfladning** | **14:50** | **21:50** | Markedsordre på alt åbent. Annullér alle hvilende ordrer |
| Genforsøg | 14:53 og 14:56 | 21:53 og 21:56 | Hvis positionen stadig står åben |
| Alarm | 15:00 | 22:00 | Telegram. Herefter er det manuelt |
| Topstep flader selv | 15:08 | 22:08 | **Har vi nået hertil, er noget gået galt** |
| Topsteps deadline | 15:10 | 22:10 | |

**Hvorfor 14:50 CT og ikke 15:05.** Tre grunde, og kun den første handler om reglen:

1. **20 minutters margin til deadline.** En markedsordre kan afvises, forsinkes eller
   fyldes delvist. Bliver vi fladet af Topsteps risikoafdeling, er det systemet der greb
   ind — ikke en ren dag.
2. **Vi er inde i RTH.** 14:50 CT er fuld likviditet og målt spread på 1,73 tick. Fem
   minutter senere er vi tættere på lukkeauktionen, og efter 15:00 CT er spreadet 2,17
   tick. **Ingen markedsordrer uden for RTH** — besluttet.
3. **Vi undgår lukkespidsen.** De sidste minutter før cash-luk bærer ofte en skarp
   retningsbevægelse. Vi vil ikke sidde i den med et gulv der brydes på urealiseret P&L.

**Fladt bekræftes, ikke antages.** Reglen er ikke "send en lukkeordre 14:50". Den er
"positionsopgørelsen hos brokeren viser nul 14:50". En afsendt ordre er ikke en lukket
position. Koden skal spørge og læse svaret.

**Konsekvensen er at Topsteps regel aldrig binder.** Handler vi kun RTH og flader 14:50,
er vi allerede flade 20 minutter før deadline hver eneste dag. Reglen er et sikkerhedsnet,
ikke en begrænsning på strategien.

**To ting reglen ikke løser:**

- **Macen er offline 14:50.** Så flader ingenting. Et serverside-stop hos brokeren beskytter
  prisen, men ikke tiden — der findes ingen tidsbaseret exit hos brokeren. Residualrisiko,
  hører i C1/C2.
- **Hvad reglen koster.** 14:30–15:00 CT er 30 af RTH-sessionens 390 minutter, altså 7,7%
  af handelstiden, og det er en periode med høj volumen. Det er formentlig billig
  forsikring, men **det er en antagelse, ikke en måling.** Skal måles når der findes en
  strategi: hvad sker der med resultatet hvis sidste indgang flyttes til 14:00 eller 15:00
  CT?

### Omkostninger og data

| post | $/md |
|---|---|
| Combine $50K, standard-spor | 49,00 |
| API med koden `topstep` | 14,50 |
| Level 1-markedsdata (Combine + XFA) | 0 |
| **i alt under evaluering** | **63,50** |

Level 2 koster $38/md og er unødvendig på 15m. Historiske data til backtest er en anden
sag og forventes gratis — se B1. **LFA-datapris er ukendt (C6).**

---

## 4. Omkostningsgrundlaget

Kontrakten (CME): MNQ er **$2 pr. indekspoint, tick 0,25 = $0,50**.
Gebyret (TopstepX): **$1,22 rundtur** = $0,50 kurtage + $0,71 børs + $0,01 NFA. Samme sats
på alle tre trin.

Ved NQ 29.639,50 og ATR_15m 0,168% er 1 ATR = 49,79 point = **R = $99,59** pr. kontrakt:

| grundlag | gebyr_$ | spread_$ | slippage_$ | i_alt_$ | omk_R | be_WR_pct ved 2:1 |
|---|---|---|---|---|---|---|
| gammelt tal (Tradovate Free) | 1,50 | 0,75 | — | 2,25 | 0,023 | 34,1 |
| verificeret, gebyr + spread | **1,22** | 0,75 | — | **1,97** | **0,0198** | **33,99** |
| **som koden faktisk regner** | 1,22 | 0,75 | 0,50 | **2,47** | **0,0248** | **34,16** |

**Tredje række gælder.** Det gamle 0,023 R var uden slippage; modellen i repoet trækker
0,5 tick pr. side.

**To af tre led er skøn.** Kun gebyret er verificeret. Spread (1,5 tick) og slippage
(0,5 tick/side) er gæt — se `claude/ANTAGELSER.md`.

**Omkostningsspørgsmålet er lukket.** Det der mangler er en edge.

---

## 5. Positionsstørrelse og timeframe

> **Status 2026-09-13: §5's konklusion er faldet bort.** Fase 1 målte ATR på rigtige
> MNQ-data i stedet for på 60 dages Yahoo-historik. Tallet er markant højere i US RTH end
> det §5 stod på, og **valget "1 MNQ, 1-ATR-stop, 15m" er dermed ikke længere begrundet.**
> Ruingitteret i 5b er regnet på det gamle tal og gælder ikke. Fase 2 regner det om.
> Afsnittet er skrevet om så det viser hvad der **er** målt, og hvad der ikke er afgjort.

### 5a. Det målte grundlag

Fase 1, MNQ, 2019-05-06 til 2026-09, Databento. Verificeret ved uafhængig genberegning i
overblikssessionen (afvigelse < 0,01 pp).

**Basis:** NQ 29.138 · MNQ $2/point · MLL $2.000 · rundturomkostning $2,59 i RTH og $2,80
uden for RTH (målt spread, ikke skøn) · gevinst/tab 2:1 · 1 kontrakt · 1-ATR-stop.

> **Én uoverensstemmelse, og den er uden betydning.** Tabellen er regnet med $2,59, men
> `backtest/costs.py` trækker slippage som `max(0, N(0,5; 0,5))` tick, og afskæringen ved
> nul løfter middelværdien til **0,542 tick pr. side**, ikke 0,50. Kodens faktiske
> rundturomkostning i RTH er derfor **$2,627**. Forskellen flytter risikokolonnen med
> 0,002 pp og be_WR med 0,04 pp i værste række. **Tabellen står.** Men $2,627 er tallet
> der skal bruges fremadrettet, og konfigurationen skal erklære den *realiserede*
> middelværdi, ikke parameteren. Fanget i fase 1-sessionens efterskrift.

| timeframe | session | ATR_pct_p50 | ATR_pct_p90 | R_usd_p50 | R_usd_p90 | **risiko_pct_af_MLL_p50** | **risiko_pct_af_MLL_p90** | omk_R_p50 | be_WR_pct_p50 |
|---|---|---|---|---|---|---|---|---|---|
| 1m | RTH | 0,057 | 0,123 | 33,22 | 71,68 | **1,79** | **3,71** | 0,0780 | 35,93 |
| 3m | RTH | 0,101 | 0,210 | 58,86 | 122,38 | **3,07** | **6,25** | 0,0440 | 34,80 |
| 5m | RTH | 0,132 | 0,271 | 76,92 | 157,93 | **3,98** | **8,03** | 0,0337 | 34,46 |
| 15m | RTH | 0,232 | 0,459 | 135,20 | 267,49 | **6,89** | **13,50** | 0,0192 | 33,97 |
| 15m | døgn | 0,132 | 0,296 | 76,92 | 172,50 | **3,99** | **8,76** | 0,0364 | 34,55 |

**Kolonnedefinitioner** — så tabellen kan læses uden at gætte:

- `ATR_pct_pXX` = XX. percentil af ATR målt som procent af prisen, over alle barer i
  sessionen. Ikke et gennemsnit.
- `R_usd_pXX` = 1 ATR ved den percentil, omregnet til dollar for **én** MNQ:
  `NQ × ATR_pct/100 × 2 × stop_ATR`.
- `risiko_pct_af_MLL_pXX` = `(R_usd_pXX + rundturomkostning) / 2.000 × 100`.
  **Det er go/no-go-kolonnen, og den vurderes på p90.**
- `omk_R_pXX` = `rundturomkostning / R_usd_pXX`. Omkostningen målt i R.
- `be_WR_pct_pXX` = break-even win rate ved 2:1 = `(1 + omk_R_pXX) / 3 × 100`.
  Bemærk at den **falder** med percentilen, fordi den faste omkostning fylder mindre i et
  større R. `be_WR_pct_p90` er derfor det *mildeste* tal i rækken, ikke det værste.

### 5b. Hvad målingen ændrer

**1. RTH er ikke det samme som døgnet, og forskellen er stor.** 15m i RTH har p50-ATR på
0,232% mod 0,132% over hele døgnet — næsten det dobbelte. Døgnserien er fortyndet af
stille asiatiske timer. **Al tidligere regning brugte reelt et døgntal på en RTH-strategi.**

**2. Det gamle grundlag var for lavt.** ATR 0,168% gav $99,59 i R og 5,10% af MLL. Målt
RTH-tal giver $135,20 og **6,89%**. Ved p90 **13,50%** — mere end en fordobling af den
risiko §5 blev skrevet på.

**3. Ruingitteret i den gamle §5a gælder ikke.** Det blev kørt med risiko_pr_handel =
$102,06 fast. Den celle findes ikke længere: 1 MNQ med 1-ATR-stop på 15m RTH ligger på
$137,79. Konklusionerne der ikke afhænger af niveauet står stadig — *sizing er andenordens,
edge er førsteordens*, og *den forsigtige og den aggressive ende havner samme sted af
modsatte grunde* — men **alle tal i gitteret skal regnes om.** Det er fase 2.

**4. Min forudsigelse om kvadratrods-skalering var forkert.** Jeg skrev at lave timeframes
formentlig ville have **højere** ATR end kvadratroden forudsiger. Målingen siger det
modsatte, og afvigelsen er lille:

| timeframe | forudsagt af √ fra 15m | målt | afvigelse |
|---|---|---|---|
| 1m | 0,0599% | 0,057% | **−4,8%** |
| 3m | 0,1038% | 0,101% | **−2,7%** |
| 5m | 0,1339% | 0,132% | **−1,5%** |

Kvadratrods-skalering holder inden for 5% på MNQ i RTH. Antagelsen var god; min korrektion
af den var ikke. Den skifter status fra **A** til **M** i `ANTAGELSER.md`.

**5. Spread er målt og var undervurderet.** 92 dage, 2019-2026: **1,73 tick i RTH** og
**2,17 tick uden for RTH**. Skønnet i `config.yaml` er 1,50 tick. Retningen er som
forventet — uden for RTH er dyrere — men RTH er også dyrere end antaget.
**Konfigurationen skal opdateres, og det er en fase 2-opgave, ikke en fri ændring.**

> **Målingen har en antagelse inden i sig.** Tallet hviler på at et bbo-snapshot beskriver
> intervallet før det, og at en quote fremføres i højst 60 sekunder. Ingen af delene er
> bekræftet mod Databentos dokumentation — den kunne ikke hentes. Omkring 7% af sekunderne
> mangler en bbo-record, og hvad det betyder, vides ikke. **Status er M med et A indeni.**
> Det er stadig langt bedre end et gæt, men det er ikke det samme som et verificeret tal,
> og det skal stå sådan i `ANTAGELSER.md`.

### 5c. Timeframe-vinduet

Kræfterne er uændrede — det er kun tallene der er nye.

**Nedefra af omkostningen.** Omkostningen er fast pr. handel. Falder timeframen, skrumper
1R, og gebyret fylder mere i R. På 1m er `omk_R` 0,078 og break-even win rate 35,9%.

**Ovenfra af MLL'en, og af at 1 MNQ er udelelig.** Der findes ingen halv kontrakt. På 15m
RTH lægger den mindst mulige position 13,50% af hele risikobudgettet på spil i en p90-bar.
**Syv sådanne handler i træk og kontoen er død** — og syv tab i træk ved 34% win rate sker
i omtrent 5% af alle sekvenser på 20 handler.

**1h og 4h er stadig ude**, og nu med bedre margin. Kvadratrods-opskalering fra det målte
15m RTH-tal giver 0,464% på 1h og 0,928% på 4h, altså ~27% og ~54% af MLL pr. handel ved
1 ATR. Der er ingen vej udenom ved at size ned.

**Spor B lukker døren yderligere.** XFA kræver fem vindende *dage*. Kravet om dage sætter
en nedre grænse på handelsfrekvensen.

**Stopbredde som håndtag.** Da kontraktantallet ikke kan sænkes under 1, er stopafstanden
det eneste andet håndtag på dollarrisikoen. Prisen betales i break-even win rate:

| timeframe | stop_ATR | risiko_pct_af_MLL_p50 | risiko_pct_af_MLL_p90 | be_WR_pct_p50 |
|---|---|---|---|---|
| 15m | 1,00 | 6,89 | 13,50 | 33,97 |
| 15m | 0,75 | 5,20 | 10,16 | 34,18 |
| 15m | 0,50 | 3,51 | 6,82 | 34,61 |
| 5m | 1,00 | 3,98 | 8,03 | 34,46 |
| 5m | 0,75 | 3,01 | 6,05 | 34,83 |
| 3m | 1,00 | 3,07 | 6,25 | 34,80 |
| 3m | 0,75 | 2,34 | 4,72 | 35,29 |
| 1m | 1,00 | 1,79 | 3,71 | 35,93 |
| 1m | 0,50 | 0,96 | 1,92 | 38,53 |

**At halvere risikoen koster omkring 0,6 pp i break-even win rate.** Det er billigt på
papiret, og det er derfor tabellen er farlig at læse alene: den viser kun
omkostningseffekten af et strammere stop. **Den viser ikke at et strammere stop rammes
oftere.** Den effekt er ukendt og kan være mange gange større end 0,6 pp. Den kan kun
måles mod en rigtig strategi.

**Søgefeltet er 15m og nedad**, og 15m er nu den dyre ende frem for det oplagte valg.

### 5d. De fire veje

| vej | idé | status |
|---|---|---|
| 1 | Lavere timeframe | **Åben og nu mere attraktiv.** 3m og 5m koster 3-4% af MLL mod 15m's 6,9% |
| 2 | Sub-ATR stop | **Åben.** Kostsiden er kvantificeret (0,6 pp pr. halvering); win rate-siden er det ikke |
| 3 | Acceptér ~5% pr. handel | **Skal genprøves.** Cellen er nu 6,89% ved p50 og 13,50% ved p90 |
| 4 | Større konto | Bortfaldet — $50K valgt |

**De fire veje er ikke valgmuligheder man vælger imellem. De er akser i ét sweep**, der
køres én gang mod en rigtig strategi på rigtige data. Vej 1 og 2 virker begge gennem win
rate, og win rate kommer fra en strategi.

### 5e. Hvad modellen ikke svarer på

- **Hvordan win rate ændrer sig med stopbredden.** Vej 2's dyre side er stadig umålt.
- **Spor B.** Målfunktionen er "nå $3.000 før ruin" — altså Combine. XFA og LFA har en
  anden målfunktion: fem dage à $150+.
- **Klyngede tab.** Handlerne trækkes uafhængigt. Når der findes en strategi, skal modellen
  **blok-bootstrappe fra strategiens egen handelssekvens**.
- **Vejen inde i en handel.** Derfor to brudmodeller frem for ét tal.
- **Prisniveauets vandring.** ATR i procent er målt over syv år hvor NQ gik fra ~8.000 til
  ~29.000. Samme ATR i procent er 3,6× flere dollar i dag. En ruinmodel der trækker fra
  hele historikken og regner i dollar mod et fast gulv på $2.000 blander to regimer.
  Håndteres i fase 2.

---

## 6. Repoets tilstand

**94 passed, 4 skipped.** Committet og pushet (`6a5cd46`, 34 filer).

Apparatet er kopieret fra det gamle repo: `backtest/` (costs, rnorm, paired, metrics,
report), `research/` (stats, portfolio, venues, diagnostics, tsmom, daily_series,
bias_engine), `data/indicators.py`, `strategies/base.py`, `config.yaml`.

> **"Byte-identisk" kan ikke længere efterprøves.** Påstanden stammer fra en session der
> kunne se det gamle repo. `REAL TRADING BOT` ligger ikke under `~/Documents/GitHub`, og
> fase 1-sessionen kunne ikke finde det. Det samme gælder docstringen i `data/ohlcv.py`,
> der påstår at valideringen følger "samme kontrakt som `data/fetcher._validate_ohlcv`" —
> den blev skrevet ud fra PRD'ens *beskrivelse* af kontrakten, ikke fra originalen.
> Formentlig rigtigt. **Ikke verificeret.**

**Tre moduler kan ikke importeres.** `research/diagnostics.py` og `research/bias_engine.py`
importerer begge `research/daily_bias.py`, som ikke findes i repoet. `diagnostics.py` og
`daily_series.py` peger desuden på `data/historical/*.csv`, som heller ikke findes.
**Testene er grønne, fordi ingen test rører de filer.** Det er den egentlige lærdom: en
grøn testsuite der ikke kan skelne "modulet virker" fra "modulet blev aldrig indlæst".
Fase 2 tilføjer en import-røgtest over hele pakken.

**Kopien var ufuldstændig første gang.** Afhængighedsanalysen scannede toplinje-imports og
konkluderede "tre ekstra filer, ikke en kaskade". Den ramte forbi, fordi `paired.py:58` er
en **doven import inde i en funktion** — indrykket, og usynlig for et scan efter linjer
der begynder med `from` eller `import`.

**Runner-beslutningen:** `backtest/runner.py` er ikke kopieret og skal ikke kopieres. Den
trækker ccxt, yfinance, `data/fetcher.py`, `strategies/registry.py` og de tre
krypto-composites med sig. Propfirm-sporet bygger sin egen MNQ-runner, og `paired.py:58`
pointes mod den. `tests/test_paired.py::TestEndToEnd` er markeret `skip` med den
begrundelse i koden.

**Én kodeafvigelse:** `BaseStrategy.get_asset_class()` faldt tilbage på `"crypto"` for alt
ukendt — MNQ ville have fået den proportionale 0,20%-model. Den har nu `MNQ → index`.
Fallbacken er stadig en fælde for ethvert fremtidigt futures-symbol.

---

## 7. Arbejdsform og sessioner

Besluttet 2026-09-10.

| rolle | hvor | opgave |
|---|---|---|
| **Overblikssession** (denne) | Cowork | Holder den røde tråd, fælles forståelse af mål og midler. Sparring, idéer, verifikation af regler og tal. **Skriver PRD til hver fase — én ad gangen, når vi når dertil.** Vedligeholder `STRATEGI_PROPFIRM.md` og `claude/ANTAGELSER.md` |
| **Fasesession** | Cowork eller Code, én pr. fase | Udfører fasens PRD. Arbejder på egen branch |
| **Claude Code på Macen** | lokalt | Bygger og backtester |

Reglen der gør det til andet end en arbejdsdeling: **PRD'er skrives én ad gangen.** Skrev
vi alle faser nu, ville vi låse beslutninger vi endnu ikke har grundlag for — og fase 3's
PRD skal skrives med fase 2's resultater i hånden, ikke uden.

Git: nye branches pr. fase, ikke arbejde direkte på `main`. **Commit ikke i repoet mens
en session arbejder i det** — det skete 2026-09-11 kl. 02:09 og gav to aktører på samme
branch. Det gik godt, men det var held.

**En fasesession er ny hver gang.** Den forrige fases session bærer forældede tal i sin
kontekst — fase 1's session tror stadig at ATR er 0,168% og at sizingen er afgjort. En
frisk session der læser den opdaterede PRD har ikke det problem. Derfor er hver PRD skrevet
selvbærende, med et trin 0 der peger på præcis hvad der skal læses.

Før en fasesession lukkes: spørg den **"hvad ved du om repoet som ikke står i nogen fil?"**
og skriv svaret ind. Tavs viden om apparatets fælder er dyrere at genopdage end at nedskrive.

### Regler for enhver session der arbejder i dette repo

Disse er ikke stilpræferencer. Hver enkelt er skrevet efter at være gået galt.

| regel | hvorfor |
|---|---|
| **Kommandoblokke uden `#`-kommentarer** | Mads' zsh fejler på dem. Forklaringen står i teksten over blokken, ikke inde i den |
| **`git --no-optional-locks` på alle git-kald** | Uden det efterlades lockfiler der blokerer GitHub Desktop. Kørt to gange, kostede fejlsøgning begge gange |
| **`git add` køres ikke af en Cowork-session** | `--no-optional-locks` dæmper kun den opportunistiske lås fra læsekommandoer som `status`. `git add` tager den rigtige lås uanset |
| **Kompakt tabel i chatten ved hvert resultat** | Mads er ofte på telefonen og skal kunne læse resultatet uden at åbne en fil |
| **Aldrig API-nøgleværdier i chatten** | En nøgle er allerede lækket i et skærmbillede og måtte roteres. Verificér kun maskeret: `sed 's/\(=db-....\).*/\1…/' .env` |
| **`.env` i `.gitignore`, aldrig committet** | Verifikation: `grep -c "^\.env$" .gitignore` → mindst 1, og `git --no-optional-locks status --porcelain=v1 \| grep -c "env"` → 0 |
| **Nøgler roteres aldrig midt i en kørsel** | Gjort én gang. Gav 401 og dræbte et MNQ-udtræk halvvejs |
| **`REAL TRADING BOT` er kun læsekilde** | Slå op frit. Ingen kode her må importere derfra, og der skrives aldrig tilbage |

### Testning kræver ikke Topstep

Backtest og paper-forward kører udelukkende på Macen med egne data. **Topstep-konto og
API-abonnement er først nødvendigt når evalueringen faktisk skal købes.** Det betyder at
alt frem til og med et validt paper-resultat kan bygges uden at betale noget.

Ét forbehold, og det er den samme fælde som på guld: **backtest på én kilde og live på
TopstepX' feed er to forskellige serier.** Vi så 20% forskel i ATR mellem to kilder for
samme instrument og periode, formentlig fordi bar-grænserne lå forskelligt. Før første
live-handel skal de to serier holdes op mod hinanden — det er ikke en detalje, det er
forskellen på om backtesten beskriver det marked botten handler i.

---

## 8. Metoderegler

1. **Præregistrér kriteriet før kørslen.**
2. **Konfidensinterval på alt.** Krydser det nul, er resultatet uafgjort.
3. **Mindste detekterbare forskel beregnes før testen.**
4. **Gates hører til i live, aldrig i backtesten.**
5. **Alle tal både brutto og netto.**
6. **Enheden står i kolonnenavnet.**
7. **En gebyrsats tæller først når den er verificeret for den kanal botten bruger.**
8. **Stop efter hver kørsel.** Ingen konfigurationsændringer, ingen strategiforslag.
9. **Egne idéer valideres ikke videnskabeligt** — de vurderes på: kan den automatiseres,
   passer den ind, hvor omfattende er ændringen.
10. **Alt andet sammenlignes mod nyeste litteratur.**
11. **Der sizes ikke efter punktestimater.** Percentiler, og go/no-go på den ende hvor det
    gør ondt.
13. **Præregistreringen committes før kørslen.** Rækkefølgen i en session kan ikke
    efterprøves bagefter — fase 1's præregistrering var reel, men kunne kun dokumenteres
    ved at nogen huskede rækkefølgen. Fra nu af: kriteriet skrives i en dateret fil under
    `research/prereg/`, committes, og *derefter* køres. Så er metoderegel 1 revisérbar i
    stedet for tillidsbaseret.
12. **Nulmodellen kører altid ved siden af.** Hver gang en strategi måles, køres den samme
    måling med **win rate sat til break-even** — altså nul edge — ved samme sizing, samme
    omkostning, samme mekanik. Strategiens tal må kun kaldes en edge hvis det ligger over
    nulmodellens **med adskilte konfidensintervaller**. Uden referencerækken ved man ikke
    om 88% beståelse er en edge eller bare en gunstig regelgeometri.

---

## 9. Åbne spørgsmål

Bogstavet er fasen, tallet er rækkefølgen inden for fasen.

### A. Besvaret

| # | spørgsmål | svar |
|---|---|---|
| A1 | Positionsstørrelse mod MLL | **Genåbnet.** Svaret "1 MNQ, 1-ATR, 15m" stod på et ATR-tal der var for lavt. Grundlaget er nu målt (§5a); valget træffes i fase 2 |
| A2 | Profitmål og priser pr. kontostørrelse | §3. $3.000 / $2.000 / $49-95 md |
| A3 | Følger markedsdata med API-adgangen? | §3. Level 1 gratis i Combine og XFA. Level 2 $38/md, unødvendig |
| A4 | Tæller en ordre fra telefonen som "personal device"? | Bortfaldet. Ordren afsendes fra Macen |
| A5 | Hvordan ser Topsteps trin faktisk ud? | §3. Tre trin, ikke to. XFA er simuleret men betaler |
| A6 | Kan 1h/4h bruges? | §5c. **Nej**, og nu med bedre margin: ~27% og ~54% af MLL pr. handel ved 1 ATR |
| A7 | Hvornår skal botten være fladt ude? | §3. **15:10 CT hver hverdag**, hård regel. Handel genoptages 17:00 CT |

### B. Før kode — blokerende, i rækkefølge

| # | spørgsmål | afhænger af | hvorfor den blokerer |
|---|---|---|---|
| ~~B1~~ | ~~Datagrundlag~~ | — | **Besvaret.** Databento, MNQ fra 2019-05-06. K1-K4 holdt |
| ~~B2~~ | ~~ATR-fordeling pr. timeframe~~ | B1 | **Besvaret.** §5a |
| ~~B3~~ | ~~Reelt spread pr. tidsblok~~ | B1 | **Besvaret.** Målt: 1,73 tick i RTH, 2,17 uden for. §5b |
| **B6** | **Sizing på det målte grundlag.** Hvilken kombination af timeframe og stopbredde overlever ruinmodellen med R trukket fra den målte ATR-fordeling? | B2 | §5's konklusion er faldet. Se `PRD_FASE2_RUINMODEL.md` |
| **B4** | **Edge-hypotese til indeksfutures** | — | Uden den har vi et måleapparat uden noget at måle. **Det egentlige projekt.** Eget dokument |
| **B5** | **Understøtter MNQ 2:1, eller skal vi til 1,5:1?** | B4 | Ved 1,5:1 springer be_WR fra ~34% til ~40% og hele §5 er ugyldig |

### C. Før live

| # | spørgsmål |
|---|---|
| C1 | **Tilstandsgenopretning ved opstart.** Uden den er `KeepAlive` en risiko frem for en sikkerhed |
| C2 | Netværkstab midt i en åben position |
| C3 | Fallback når Telegram er nede |
| C4 | Slippage på stops, målt |
| C5 | Eksplicit regel i koden når MLL nærmer sig |
| C6 | Hvad koster markedsdata på LFA? |
| C7 | **Afvigelse mellem backtest-serien og TopstepX' feed**, målt (§7) |
| C8 | **Fladningsreglen i kode.** Reglen er besluttet (§3): sidste indgang 14:30 CT, hård udfladning 14:50 CT, genforsøg, alarm 15:00 CT, alt regnet i America/Chicago, fladt bekræftet mod brokerens positionsopgørelse. **Implementeringen mangler**, og det gør adfærden når Macen er offline på fladningstidspunktet |
| C10 | **Hvad koster indgangsstoppet 14:30 CT?** 7,7% af RTH-sessionen fravælges. Måles mod en rigtig strategi, ikke besluttet på forhånd |
| C9 | **Opdatér `config.yaml` med målt spread** — 1,73 tick i RTH, 2,17 uden for. Skønnet 1,50 står der stadig |

---

## 10. Definition af "klar til at bygge"

Vi bygger ikke fordi det føles som næste skridt. Vi er klar når **alle fem** holder:

1. ~~**B1-B3 er besvaret**~~ — **opfyldt 2026-09-13.** Der findes data, ATR er målt som
   fordeling, spread er målt.
   **1b. B6 er afgjort** — sizingen står på den målte fordeling, ikke på et punktestimat.
2. **B4 har mindst én kandidat** med et svar på "hvorfor betaler nogen mig for det her?"
3. **B5 er afgjort** — vi ved hvilket RR instrumentet understøtter.
4. **`claude/ANTAGELSER.md` har ingen S'er på kritisk vej** — eller de tilbageværende skøn
   har en følsomhedskolonne der viser at konklusionen holder i begge ender.
5. **Fælles forståelse af mål og midler.** Begge parter kan gengive hvad vi bygger, hvorfor,
   og hvad der ville få os til at stoppe.

---

## 11. Hvad der IKKE er en del af dette spor

- **TSMOM.** Ude. Dokumenteret i `STRATEGI_TSMOM.md` som reference.
- **Krypto.** Omkostningen på 15m gør sporet dødt for daytrading. Bemærk at
  `STRATEGI_DAYTRADING.md` §6's edge-kandidater alle er krypto-specifikke og **ikke**
  overføres — se B4. Det dokument er en historisk protokol og rettes ikke bagud.
- **De 5-10K egen kapital.**
- **Aktie-execution.** Udskudt.

---

## 12. Åbne observationer fra det eksisterende projekt

- **Break-even-stop og trailing stop fungerer muligvis ikke som håbet.** Mads' observation
  fra live paper-handler. Ikke målt. Kandidat til en falsifikationstest.
- **Prisen rammer ofte lige akkurat ikke TP**, hvorefter den går mod SL eller lukkes af
  tidsstop. Det var begrundelsen for `tp_rr_ratio` 1,5 i det gamle projekt — og præcis
  grunden til at B5 findes.

### Fra fase 1-sessionens efterskrift, 2026-09-13

Ting der ikke stod nogen steder. De to første kan bide.

- **NYSE-kalenderen følger kørselsdatoen.** `exchange_calendars` dækker 20 år tilbage og ét
  år frem. Uden for vinduet markerer `rth_mask` **alle** barer som ETH — uden at fejle.
  Rammer live-brug efter september 2027 og historik før 2006. **En stille fejl der ligner
  et resultat.** Fase 2 gør den støjende.
- **Budgetvagten kan nulstilles ved et uheld.** Den læser `data/cache/udtraek.jsonl`, som er
  git-ignoreret. Slettes cachen eller klones repoet, starter forbruget forfra på $0. Tallene
  er desuden Databentos *estimater* — den faktiske saldo i portalen er aldrig tjekket.
- **Datacachen er eneste kopi.** 162 MB, ikke i git. Yahoo-udtrækket kan ikke hentes igen
  (rullende vindue), så K2 kan kun genkøres herfra. Databento-data igen koster ~$27. **Tag
  en kopi uden for repoet.**
- **Cachen er delt i kalenderår.** Forlænges 2026 med en ny slutdato, betales hele
  årsbidden igen (~$0,90), ikke kun det nye stykke.
- **Miljøet er ikke låst.** `.venv` kører Python 3.14.4 med pandas 3.0.5, numpy 2.5.3,
  pyarrow 25.0.1, databento 0.86.0, exchange_calendars 4.13.2. **Ingen scipy.**
  `requirements.txt` siger stadig 3.12. Macen har hverken brew, uv, pyenv eller gh — derfor
  kan ingen session pushe selv; det gør Mads i GitHub Desktop.
- **To NQ-niveauer i omløb.** 29.639,50 (2026-09-07) og 29.138 (seriens sidste luk) giver
  13,72% mod 13,49% for samme ATR på 15m RTH p90. **Dette dokument bruger 29.138
  gennemgående.** Fase 2 holder op med at hardkode prisen og læser den fra sidste bar.
- **Én regel er aldrig kørt.** Reglen der rykker NQ's startår frem ved et estimat over $20
  blev ikke udløst (estimatet var $17,83) og har ingen test.

---

## Kilder

- help.topstep.com: TopstepX API Access, Trading Combine Parameters, Live Funded Account
  Parameters, Maximum Loss Limit, Daily Loss Limit, Consistency Target, TopstepX
  Commissions and Fees, Payout Policy, Level 1 and Level 2 Market Data, Pricing
- topstep.com: how-it-works, express-funded-account-rules, live-funded-account-rules,
  blog/prop-firm-drawdown-rules
- cmegroup.com — Micro E-mini Nasdaq-100 contract specifications
- NQ-niveau 29.639,50 pr. 2026-09-07
- `research/output/venue_costs.md` — gammelt repo, læst. Tradovate-baseret
- `research/output/mll_ruin.md` — dette repo, §5a
