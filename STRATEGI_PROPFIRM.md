# Propfirm-sporet

**Status:** 2026-09-13. **Fase 1 og 2 er kørt og lukket.** Der er NQ- og MNQ-data i repoet
fra 2019-05-06, ATR er målt som fordeling, spread er målt, ruinmodellen kører på
fordelingen i stedet for et punktestimat, og alle Topstep-regler er verificeret ordret hos
primærkilden. **A1-A7, B1-B3 og B6 er besvaret.**

**Sizing var afgjort som et bånd: 6,4-7,1% af MLL ved p90 med 1 MNQ** (§5). **Genåbnet
2026-09-19** af Mads' disciplinregler — $250 pr. handel, højst én afgjort handel om dagen.
Timeframen afgøres i B4 på edge-grunde.

**Næste fase er B4 — edge-hypotesen.** Det er projektets egentlige opgave, og alt hidtil
har bygget måleapparatet til den. Ingen konto åbnet, ingen strategi bygget, ingen edge
fundet.

Søsterdokumenter: **`REGLER_VERIFICERET.md`** (hver regel med ordret citat og link — går
forud for dette dokument ved uenighed), `ANTAGELSER.md` (målinger, skøn og
modelantagelser), `PRD_FASE1_DATAGRUNDLAG.md` og `PRD_FASE2_RUINMODEL.md` (kørt),
`STRATEGI_TSMOM.md`, `STRATEGI_DAYTRADING.md`.

---

## Faseoversigt

Hvor vi står, og hvad der mangler. **Kørte faser er faktuelle; kommende faser er skitser**
— de får først en PRD når vi når dertil, én ad gangen (§7).

| fase | indhold | status |
|---|---|---|
| **0. Repo og apparat** | Eget repo, apparatet kopieret fra det gamle, arbejdsform og metoderegler | **Kørt** 09-10/09 |
| **1. Datagrundlag** | Datakilder, MNQ/NQ fra 2019, ATR som fordeling, spread målt. K1-K4 holdt | **Kørt** 11-13/09 |
| **2. Ruinmodel og sizing** | R trukket fra fordelingen, nulmodel, låsekriterium. K1-K5 holdt | **Kørt** 13/09 |
| **3. Edge-hypotese (B4)** | Findes der en edge på indeksfutures? **Projektets egentlige opgave** | **Næste** |
| 4. Strategi og backtest | Hypotesen bygget som kode, målt mod nulmodellen. B5 (2:1 mod 1,5:1) afgøres her. **MNQ-runneren bygges, og de fire skippede ende-til-ende-tests genaktiveres** | Skitse |
| 5. Spor B: XFA-model | Egen ruinmodel for XFA — terminal ruin, udbetalingsloft, "fem dage à $150+" | Skitse |
| 6. Live-klargøring | C-listen: fladningsregel i kode, slippage målt (C4), tilstandsgenopretning, feed-afvigelse | Skitse |
| 7. Combine købt og kørt | Først når 1-6 er lukket. $49-95/md begynder at løbe her | Skitse |

### Hvad der er afgjort

- **Instrument og konto:** MNQ, Topstep $50K.
- **Omkostning:** $2,627 pr. rundtur i RTH, dekomponeret og verificeret. Kun slippage er
  stadig et skøn.
- **Sizing:** risikobåndet **6,4-7,1% af MLL ved p90** med 1 MNQ. Ikke én celle — tre
  timeframes rammer båndet og er uadskillelige. **Genåbnet 2026-09-19:** Mads'
  disciplinregler sætter risikoen til $250 pr. handel og højst én afgjort handel om dagen.
  Se `PRD_FASE3_B4_EDGE.md` §3a-3c.
- **Timeframe-vindue:** 15m og nedad. 1h og 4h er ude.
- **Handelsvindue og fladning:** kun US RTH, sidste indgang 14:30 CT, hård udfladning
  14:50 CT.
- **Alle Topstep-regler** verificeret ordret hos primærkilden (`REGLER_VERIFICERET.md`).

### Hvad der mangler, i rækkefølge

1. **B4 — en edge-hypotese.** Uden den er alt ovenstående et måleapparat uden noget at
   måle. Alle tal i §5 hviler på en antaget win rate på 40% som ingen strategi har leveret.
2. **B5 — understøtter MNQ 2:1?** Afgøres når en strategi findes. Ved 1,5:1 springer
   break-even fra ~34% til ~40% og hele §5 skal regnes om.
3. **B7 — spor B's egen model.** XFA har terminal ruin, et udbetalingsloft på $2.000 og en
   anden målfunktion end Combine.
4. **C4 — slippage målt.** Blokerende: ved 1,0 tick pr. side krydser ruin K2's grænse.
5. **C-listen i øvrigt** før første live-handel.
6. **De fire skippede ende-til-ende-tests** i `test_paired.py` genaktiveres når
   MNQ-runneren findes. Det er apparatets eneste samlede dækning.

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

> **Reglerne står i `REGLER_VERIFICERET.md`, ikke her.** Det dokument har hver regel med
> ordret citat og link, verificeret hos primærkilden 2026-09-13. Dette afsnit er et
> sammendrag til læsning — **er de to uenige, gælder `REGLER_VERIFICERET.md`.**
> Gennemgangen 2026-09-13 rettede tolv fejl, hvoraf to stod som verificerede her.

**Vi talte hidtil om "eval" og "funded" som to trin. Der er tre, og de har fundamentalt
forskellig risikogeometri.**

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
| Combine | Nå $3.000. **Bedste dag ≤ 55% af samlet profit**, ellers hæves målet til `bedste_dag / 0,55`. Min. 2 handelsdage. **Ingen tidsgrænse** |
| XFA | **5 vindende dage à $150+ net.** Payout op til 50% af saldo, **maks $2.000 på $50K** (min $125). En frivillig DLL fordobler loftet til $4.000. Efter hver payout nulstilles tælleren og MLL låses på $0 |
| LFA | 5 benchmark-dage à $150+ pr. cyklus → 50% af saldo, uden dollarloft. Efter 30 dage: **én gang pr. dag** |

**Brud er ikke det samme på de to trin.** Et MLL-brud i Combine gør kontoen ufundérbar
indtil man betaler for en Reset. **Et MLL-brud på XFA lukker kontoen permanent.** Spor B's
ruin er terminal, og det gør spor B til et andet modelleringsproblem end Combine — ikke et
mildere.

**Og XFA's 40%-konsistensregel er ikke en spærring.** Den er en *alternativ* udbetalingsvej
— 3 handelsdage i stedet for 5 vindende, mod et højere loft. Overskrides de 40%, sker der
ingenting ud over at man tager Standard-vejen i stedet.

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

**Handelsdagen i dansk tid — referencetabellen.** Godkendt af Mads 2026-09-21. Dansk tid står
først; New York-tid er børsens egen tid; Chicago-tid (CT) er den Topstep, CME og koden regner i,
og den ligger altid en time efter New York.

| hvad | dansk tid, normalt | dansk tid, i skifteugerne | New York-tid | CT |
|---|---|---|---|---|
| Handelsdøgnet åbner (CME) | 00:00 | 23:00 | 18:00 | 17:00 |
| US-børsen åbner | 15:30 | 14:30 | 09:30 | 08:30 |
| **Sidste indgang** (vores regel) | **21:30** | 20:30 | 15:30 | 14:30 |
| **Alt fladt** (vores regel) | **21:50** | 20:50 | 15:50 | 14:50 |
| US-børsen lukker | 22:00 | 21:00 | 16:00 | 15:00 |
| Topstep begynder at flade | 22:08 | 21:08 | 16:08 | 15:08 |
| Topsteps deadline | 22:10 | 21:10 | 16:10 | 15:10 |

"Normalt" er hele året undtagen skifteugerne. **I skifteugerne ligger alt en time tidligere i
dansk tid** — både i oktober og i marts, aldrig senere.

**Forskydningen er 7 timer både sommer og vinter.** Chicago og København skifter begge
tid, med samme ene time, så forskellen er den samme når begge har sommertid og når ingen
af dem har. De 6 timer opstår kun i de uger hvor USA og EU står på hver sin side af et
skift — **to til tre uger i marts og én uge omkring 1. november**:

| periode | USA | EU | handelsdage med 6 timers forskel |
|---|---|---|---|
| efterår 2026 | sommertid slutter søn. 1. nov. | sommertid slutter søn. 25. okt. | **man. 26. – fre. 30. okt. 2026** |
| forår 2027 | sommertid begynder søn. 14. mar. | sommertid begynder søn. 28. mar. | **man. 15. – tor. 25. mar. 2027** (26. marts er langfredag, NYSE lukket) |
| efterår 2027 | sommertid slutter søn. 7. nov. | sommertid slutter søn. 31. okt. | **man. 1. – fre. 5. nov. 2027** |

Reglerne bag datoerne står med kilde i `REGLER_VERIFICERET.md` §2. **Rettet 2026-09-19:**
kolonnen hed før "vinter, 6t", og teksten nævnte kun oktober. Om vinteren er forskellen
7 timer, og martsskiftet manglede. Tallene i 6-timers-kolonnen var rigtige, kun
overskriften og forklaringen var forkerte.

**Koden skal regne i America/Chicago og konvertere, ikke hardkode 22:10.** Rettelsen her
viser hvorfor: en hardkodet dansk tid ville ramme forkert fem handelsdage i oktober 2026 og
ni i marts 2027, og det er de dage hvor fladningen skal ske en time tidligere end normalt i
dansk tid.

**Børsen selv er åben ~23 timer i døgnet** (CME Globex, verificeret hos CME 2026-09-13).
Det er to forskellige ting: børsens åbningstid og Topsteps regel. Topsteps deadline ligger
fem minutter før børsens eftermiddagspause:

| CME Globex, aktieindeks | CT | dansk tid (sommer) |
|---|---|---|
| Åbner | 17:00 | 00:00 |
| US RTH | 08:30–15:00 | 15:30–22:00 |
| **Topstep: alt fladt** | **15:10** | **22:10** |
| Børsen lukker | **16:00** | 23:00 |
| Vedligeholdelse | **16:00–17:00** | 23:00–00:00 |

Topstep spærrer 1t50m, og børsen er selv lukket i den sidste time af det.

> **En 15-minutters pause 15:15–15:30 CT er uafklaret.** CME's aktuelle contract specs
> nævner ingen intradag-pause; en ældre FAQ gør. Uden betydning for os — vi er flade 14:50
> — men kod ikke et sessionsfilter på den uden at måle den i datafeedet først.

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

## 5. Positionsstørrelse og timeframe — GENÅBNET 2026-09-19

> **Genåbnet af disciplinreglerne** (`PRD_FASE3_B4_EDGE.md` §3a): $250 pr. handel (12,5% af
> MLL), højst én afgjort handel om dagen, dage uden handel tilladt, og BE-flyt ved +1,2R.
> Alt nedenfor er regnet ved 1-3 handler dagligt, binært vind/tab og risiko som ATR-multipel.
> **Tallene er rigtige for de antagelser, men antagelserne gælder ikke længere.** Ruinmodellen
> skal køres med reglerne før båndet eller beståelsesraterne bruges igen.

**Fase 2 kørt 2026-09-13.** Rapport: `research/output/mll_ruin_v2_k55.md`. Præregistrering:
`research/prereg/fase2_valgregel.md`. Alle fem kriterier K1–K5 holdt.

### 5a. Svaret er et bånd, ikke en celle

> **Risikobåndet: 6,4–7,1% af MLL ved p90, med 1 MNQ.**
>
> Timeframen afgøres ikke her. Den afgøres i **B4** på edge-grunde, hvorefter stopbredden
> sættes så risikoen lander i båndet.

Det præregistrerede låsekriterium krævede at én celle var øverst på **begge** WR-akser.
Den fejlede, og det var det rigtige udfald.

| celle | risiko_p90 | bestaa_pct, absolut akse | bestaa_pct, relativ akse |
|---|---|---|---|
| **5m/0,75** | **6,4** | 78,4 | **82,43** |
| **3m/1,00** | **6,6** | 78,2 | 82,03 |
| **15m/0,50** | **7,1** | **79,6** | 82,00 |

På den absolutte akse (WR 40% overalt) fører 15m/0,50 med 1,16 [0,81; 1,52] pp. På den
relative akse (be_WR + 6 pp) fører 5m/0,75, og 15m/0,50 er ikke engang forrest på
punktestimatet — den ligger −0,43 [−0,76; −0,09] pp efter.

**Begge forskelle er statistisk afgjorte og økonomisk ligegyldige.** 20.000 parrede stier
giver konfidensintervaller på ±0,3 pp, så en forskel på 0,4 pp er "signifikant". Den er
bare ikke vigtig. Hele toppen af feltet ligger inden for 0,43 pp på den ene akse og
1,4 pp på den anden.

**Hvorfor akserne vender hver sin vej** — og det er ikke støj, det er mekanik. På den
relative akse har hver celle per konstruktion samme forventning: ved gevinst/tab `r` og win
rate `be_WR + δ` er forventningen `δ(r+1)` i R, altså 0,18 R i alle celler ved 2:1 og
δ = 6 pp. Cellerne med høj omkostning i R får derfor et større WR-løft når man går fra
absolut til relativ, og de indhenter. **Ingen af akserne er "den rigtige"** — den ene
antager at win rate er en egenskab ved signalet, den anden at edgen over break-even er
det. Hvilken der gælder afhænger af hvordan win rate reagerer på stopbredde, og **det er
vej 2, som er åben.**

### 5b. Beståelsesraten er en funktion af risikoniveau

Dette er fasens vigtigste fund, og det er større end cellevalget.

| risiko_p90 | celle | bestaa_pct | ruin_pct_pess | uafgjort_pct | dage_til_bestaa_p50 |
|---|---|---|---|---|---|
| 2,0 | 1m/0,50 | 0,2 | 0,1 | **99,6** | 180 |
| 3,0 | 1m/0,75 | 14,4 | 1,2 | **84,4** | 164 |
| 3,4 | 3m/0,50 | 28,3 | 2,1 | **69,7** | 155 |
| 3,9 | 1m/1,00 | 43,0 | 3,9 | **53,1** | 144 |
| 4,3 | 5m/0,50 | 56,6 | 5,3 | **38,1** | 133 |
| 5,0 | 3m/0,75 | 67,8 | 8,6 | 23,6 | 118 |
| **6,4** | **5m/0,75** | **78,4** | 15,2 | 6,4 | 90 |
| **6,6** | **3m/1,00** | **78,2** | 16,5 | 5,3 | 87 |
| **7,1** | **15m/0,50** | **79,6** | 18,1 | 2,3 | 76 |
| 8,4 | 5m/1,00 | 75,0 | 24,4 | 0,6 | 60 |
| 10,6 | 15m/0,75 | 67,9 | 32,1 | 0,0 | 40 |
| 14,0 | 15m/1,00 | 58,9 | 41,1 | 0,0 | 25 |

Sorteret efter risiko er kurven enkelttoppet og næsten monoton på begge sider. **Tre
forskellige timeframes lander inden for 1,4 pp af hinanden når de rammer samme
risikoniveau.** Risikoen forklarer stort set alt; timeframen næsten intet.

Og symmetrien: 5,0% giver 67,8 og 10,6% giver 67,9. Halv og halvanden gang det optimale
koster det samme.

**Grunden til at kurven falder i begge ender er forskellig.** Til højre dør man — ruin
41% ved 14,0%. Til venstre når man aldrig frem: 1m/0,50 er stadig uafgjort i 99,6% af
stierne efter 200 handelsdage.

### 5c. Tid er ikke gratis, men den adskiller heller ikke

Combine har **ingen tidsgrænse** (verificeret), så uafgjort er ikke "ikke bestået" — det er
"ikke bestået endnu", til $49–95 om måneden. Blandt de tre plateau-celler:

| celle | median dage | ved $49/md | ved $95/md |
|---|---|---|---|
| 15m/0,50 | 76 | ~$177 | ~$344 |
| 3m/1,00 | 87 | ~$203 | ~$394 |
| 5m/0,75 | 90 | ~$210 | ~$407 |

15m/0,50 er 14 handelsdage hurtigere end 5m/0,75 ved medianen. **Det er ~$33 i sparet
abonnement mod et mål på $3.000.** Tid adskiller altså heller ikke cellerne. Det er en
legitim input til B4's valg, men det er ikke et argument der vejer noget alene.

### 5d. Hvad der ellers blev afgjort

**Konsistensrettelsen 50 → 55% flyttede næsten ingenting med 1 kontrakt.** Kun 15m/1,00
(+0,16 pp) og 15m/0,75 (+0,04 pp) rykkede synligt, ingen rangering skiftede. Forklaringen
er mekanisk: reglen binder først når bedste dag overstiger $1.500, og med 1 MNQ og højst
tre handler dagligt kan kun de bredeste celler nå dertil, og kun i ATR-fordelingens hale.
**Ved 2-3 kontrakter betyder rettelsen op til +0,8 pp** — hvis vi nogensinde skalerer, skal
den regnes med.

**Fordelingen mod punktestimatet: P(ruin) stiger 8,52 [8,05; 8,98] pp** mod en konstant ved
E[R], og 11,68 pp mod en konstant ved R_p50 — som er den gamle models metode. Det er
fasens metodiske resultat. Den gamle §5 sagde 10,09% ruin for 15m/1-ATR; det rigtige tal er
34,5% optimistisk og 41,1% pessimistisk. **Vi tog fejl med en faktor tre og et halvt.**

**Monotoni-selvtjekket holdt.** Ruin stiger monotont med risiko på den relative akse — 0
afgjorte brud ud af 66 par, ved både 200 og 500 dages horisont. Mekanikken opfører sig som
gambler's ruin forudsiger.

**500-dages-diagnosen bekræftede at horisonten former rangeringen.** Ved 500 dage er
5m/0,50 øverst på den absolutte akse (91,6%) og 15m/0,50 falder til 7. plads.
Beståelsesrangeringen er ikke monoton i risiko, fordi de mindste celler stadig ikke er
færdige. **Konklusionen af det er ikke "vælg småt"** — det er at horisonten er et budget,
ikke en modelparameter, og at 200 handelsdage er valgt af os.

### 5e. Hvad der stadig ikke er afgjort

- **C4 er blokerende.** Ved 1,0 tick slippage pr. side når ruin 19,51 [18,97; 20,07] og
  krydser K2's grænse på 20%. Slippage er det eneste rene skøn tilbage i omkostningen og
  skal måles før live. Spread på 1,50 eller 2,17 tick ændrer derimod ingenting.
- **Vej 2.** Hvordan win rate reagerer på stopbredde er umålt. Det afgør hvilken WR-akse
  der er den rigtige, og dermed hvor i båndet man bør ligge.
- **Klyngede tab.** Handlerne trækkes stadig uafhængigt. Når der findes en strategi, skal
  modellen blok-bootstrappe fra strategiens egen handelssekvens.
- **Spor B.** Målfunktionen her er Combine. XFA har en anden — fem dage à $150+, terminal
  ruin, og et loft på $2.000. Egen model, egen fase.
- **Den bindende antagelse:** alt ovenstående forudsætter en win rate på 40% som **ingen
  strategi har leveret.** Nulmodellen i 15m/0,50 består 21,05% ved nul edge. Forskellen
  mellem 21% og 80% er edgen, og den findes ikke endnu.

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
| ~~B6~~ | ~~Sizing på det målte grundlag~~ | B2 | **Besvaret.** Risikobåndet 6,4-7,1% af MLL ved p90. §5 |
| **B4** | **Edge-hypotese til indeksfutures** | — | Uden den har vi et måleapparat uden noget at måle. **Det egentlige projekt, og næste fase.** Eget dokument |
| **B5** | **Understøtter MNQ 2:1, eller skal vi til 1,5:1?** | B4 | Ved 1,5:1 springer be_WR fra ~34% til ~40% og hele §5 er ugyldig |
| **B7** | **Spor B's egen ruinmodel.** XFA har terminal ruin, et udbetalingsloft på $2.000 og en helt anden målfunktion end Combine | B4 | Vi har hidtil kaldt XFA "et mildere regime". Det holder ikke. Egen fase |

### C. Før live

| # | spørgsmål |
|---|---|
| C1 | **Tilstandsgenopretning ved opstart.** Uden den er `KeepAlive` en risiko frem for en sikkerhed |
| C2 | Netværkstab midt i en åben position |
| C3 | Fallback når Telegram er nede |
| C4 | Slippage på stops, målt |
| C5 | Eksplicit regel i koden når MLL nærmer sig |
| ~~C6~~ | ~~Hvad koster markedsdata på LFA?~~ **Besvaret: $133 pr. børs pr. måned, professionel takst. ~$399/md for alle fire** |
| C7 | **Afvigelse mellem backtest-serien og TopstepX' feed**, målt (§7) |
| C8 | **Fladningsreglen i kode.** Reglen er besluttet (§3): sidste indgang 14:30 CT, hård udfladning 14:50 CT, genforsøg, alarm 15:00 CT, alt regnet i America/Chicago, fladt bekræftet mod brokerens positionsopgørelse. **Implementeringen mangler**, og det gør adfærden når Macen er offline på fladningstidspunktet |
| C10 | **Hvad koster indgangsstoppet 14:30 CT?** 7,7% af RTH-sessionen fravælges. Måles mod en rigtig strategi, ikke besluttet på forhånd |
| ~~C9~~ | ~~Opdatér `config.yaml` med målt spread~~ — **gjort i fase 2** |
| C11 | **Nyhedsfilter.** Maksimal position ind i planlagte større nyheder er forbudt. Botten skal kende den økonomiske kalender og size ned. Handel *under* nyheder er tilladt |
| C12 | **Én konto ad gangen.** Kryds-konto-hedging, koordineret handel og account stacking er forbudt |
| C13 | **Auto-breakeven er nævnt eksplicit** i Topsteps SIM-fill-regler. Vores frekvens er langt under tærsklen, men teknikken skal ikke bruges blindt |

---

## 10. Definition af "klar til at bygge"

Vi bygger ikke fordi det føles som næste skridt. Vi er klar når **alle fem** holder:

1. ~~**B1-B3 er besvaret**~~ — **opfyldt 2026-09-13.** Der findes data, ATR er målt som
   fordeling, spread er målt.
   ~~**1b. B6 er afgjort**~~ — **opfyldt 2026-09-13.** Sizingen står på den målte fordeling
   som et bånd, ikke et punktestimat.
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
