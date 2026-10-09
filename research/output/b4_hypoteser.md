# B4 — hypoteser

**Skrevet:** 2026-09-22 af overblikssessionen. Leverancen fra `PRD_FASE3_B4_EDGE.md` §6.
**Status:** kandidat 1 er specificeret, og kernen er revideret 2026-09-22 efter den første
signaloptælling (se "Kernens historik"). Ingen edge-test er kørt, intet udfald er set.
Kandidat 2 og frem mangler.

---

## Fælles for alle kandidater

| emne | beslutning | hvor |
|---|---|---|
| In-sample | 2016-01-01 til 2023-12-31, 2.012 handelsdage | PRD §4, besluttet 2026-09-22 |
| Holdout | fra 2024-01-01, 676 handelsdage. Forseglet i `data/holdout.py` | PRD §4 |
| Prisdata | NQ.v.0 1m fra Databento, aggregeret til 15m med `data/resample.py` | fase 1 |
| MNQ mod NQ | MNQ.v.0 ohlcv-1m hentet 2026-09-23, 2019-05-06 til 2024-01-01, $5,98 (forbrug nu $33,29 af $40,00). **Antagelse (A):** et prisniveau i indekspoint er det samme på NQ og MNQ. Krydstjekket: `research/output/b4_mnq_data.md` — dækning, kontraktskift og 15m-vægernes afvigelse i tick. Om afvigelsen er lille nok afgøres når edge-testen præregistreres | fase 2 §1, `research/output/b4_mnq_data.md` |
| Prisniveau | Afstande i point regnes i procent og omregnes ved NQ 29.138 | fase 2 |
| Disciplin, tradeforvaltning, sizing | Højst $250, rundet ned. Én afgjort handel om dagen. BE testes som tre varianter | PRD §3a-3c |
| Tidsvindue | Indgang 15:30-21:30 dansk tid (08:30-14:30 CT), fladt 21:50 | STRATEGI §3 |

---

## Kandidat 1 — supply og demand

**Kilde:** Ejeren. Videoen "Master Institutional Supply and Demand Trading" (Matt Donlevey,
Photon Trading, https://www.youtube.com/watch?v=-RTpm9ZNV-M) og en ven der handler strategien
manuelt og profitabelt, blandt andet på NQ, hovedsageligt på 15m. Vennen kan ikke levere
skærmbilleder.

**Vurderes efter metoderegel 9** (kan den automatiseres, passer den ind, hvor stor er
ændringen), ikke videnskabeligt. Kravet om en mekanisme gælder uanset.

### Mekanisme

Store deltagere kan ikke fylde en ordre på én gang uden at flytte prisen. Et impulsivt
udbrud fra en konsolidering efterlader derfor ufyldte ordrer ved udgangspunktet, og de
samme deltagere har en interesse i at forsvare niveauet når prisen vender tilbage.

- **Hvem sidder på den anden side:** dem der handler ind i zonen fra den forkerte side —
  sene sælgere i en demand-zone, hvis stops ligger lige under den.
- **Hvorfor er den ikke arbitreret væk:** ordreopsplitningen er strukturel. Den forsvinder
  ikke fordi den er kendt, den kan kun konkurreres om.
- Beslægtet med kandidaten "ordrer ved kendte niveauer" (Osler 2003, 2005), som videoens
  likviditetsbegreber (sweep, inducement) også hviler på.

### Kernen — fast, søges ikke

Besluttet 2026-09-22. Rækkefølgen er videoens: range → udbrud → prisen forlader zonen →
prisen vender senere tilbage → handel på retesten. Eksemplet er en demand-zone; supply er
spejlvendt.

| element | regel | kilde |
|---|---|---|
| Timeframe | 15m | vennen |
| **1. Udbrud** | Basislyset er lyset lige før udbrudslyset. Basislyset er rødt (close < open), og udbrudslyset lukker **over** basislysets high. Zonen går fra basislysets high til low, **væger medregnet**. Højden H = high − low. Zonen findes fra udbrudslysets lukning | video 8:47 |
| Buffer | B = 10% af H. Indgangsniveauet er E = high + B | Ejeren, 2026-09-22 |
| **2. Prisen forlader zonen** | Zonen bliver **aktiv** ved det første lys, fra og med udbrudslyset, hvis low ligger over E. Indtil da tæller berøringer ikke. **Lukker et lys under zonens low før aktivering, er zonen ugyldig** | video 7:31; ejeren, 2026-09-22 |
| **3. Retest** | Første lys efter aktiveringen hvis low ≤ E. Det er berøringen. Zonen dør ved den, uanset tidspunkt | video 15:55 |
| Indgang | Limitordre på E. Fyldes ved berøringen | video 9:50, med ejerens buffer |
| Stop | Zonens low | video 9:50 |
| Risiko | E − low = 1,1 × H | — |
| Mål | 2R fra E. Videoen bruger fast R med 3R som eksempel; 2R er vores beslutning | video 16:57, PRD §3 |
| Tidsvindue | Berøringen skal ske 15:30-21:30 dansk tid. Zonen må være dannet og aktiveret når som helst, også om natten | STRATEGI §3 |
| Kontraktskift | Zonen dør ved nyt `instrument_id` | — |
| Stoploft | 1,1 × H ≤ 0,429% af prisen (125 point ved NQ 29.138), altså H ≤ 0,39% (113,6 point) | PRD §3c |
| Kontrakter | `floor(250 / (1,1 × H_pt × 2))` | PRD §3c |

### Kernens historik

| version | forskel | hvorfor den blev ændret |
|---|---|---|
| v1, 2026-09-22 (commit 11d68f2) | Første berøring efter udbrudslyset er signalet. Ingen buffer | Optællingen viste at **55,4% af signalerne var berøringer i lyset lige efter udbruddet** — prisen havde ikke forladt zonen. Det er ikke videoens retest. Ændret før noget udfald er set |
| v2, 2026-09-22 | Trin 2 (zonen skal forlades, ugyldig ved lukning igennem) og bufferen på 10% | — |

### Ejerens forventning, skrevet før edge-testen

**Retesten holder cirka 9 ud af 10 gange**, hvis zonerne er sat rigtigt (ejeren, 2026-09-22).
Edge-testen måler to ting, så forventningen kan efterprøves:

- **holder:** prisen når +1R fra E, før stoppet rammes
- **vinder:** prisen når +2R fra E, før stoppet rammes — det er dette tal der afgør edgen

At zonen holder er ikke det samme som at handlen vinder. En handel kan holde og alligevel
lukkes 21:50 eller i BE uden at nå 2R.

### Varianter — søges og tælles

Hver variant tæller med i N for den deflaterede tærskel.

| variant | alternativer | videoen |
|---|---|---|
| Filter 1: førte til brud på struktur | til / fra | 13:01 |
| Filter 2: flip-zone | til / fra | 13:20 |
| Filter 3: sweep ved dannelsen | til / fra | 14:06 |
| Filter 4: likviditet foran zonen | til / fra | 14:33 |
| Filter 5: stakket med zone på højere timeframe | til / fra | 14:52 |
| Filter 6: retning på højere timeframe | til / fra | 15:13 |
| Filter 7: demand i nederste halvdel, supply i øverste | til / fra | 15:35 |
| Stop | på kanten / med afstand | 9:50 mod 16:57 |
| Buffer | 10% / 0% (videoens kant) | Ejeren mod 9:50 |
| Zonetype | pivot / range | 8:47 |
| Basislysets farve | streng / enhver farve | 9:19 |
| BE | ingen / 1,0R / 1,2R | PRD §3b |

Filter 8 (frisk zone) er i kernen. Filtrene 1-7 alene giver 128 kombinationer, og
tærsklen stiger med 3,07× mod N = 3. Krydses de med alle øvrige varianter, er N = 6.144
(128 × 2 × 2 × 2 × 3 × 2), og faktoren er 4,41×. Hvor mange der faktisk krydses, afgøres når
edge-testen præregistreres — tallet der rapporteres er det faktiske N, ikke dette loft.

### Åbne definitioner — fastlægges før edge-testen præregistreres

- **Swing-punkter:** længde på venstre og højre side. Hvert punkt har to tidsstempler —
  hvornår det skete, og hvornår det blev bekræftet. Backtesten bruger det kun fra
  bekræftelsen.
- **Range for filter 7:** hvilket swing-high og swing-low der afgrænser den.
- **Sweep, likviditet foran, flip:** operationelle definitioner. LuxAlgo's EQH/EQL (lige
  toppe og bunde inden for 0,1 ATR) er inspiration, ikke kode (licensen er CC BY-NC-SA).
- **Højere timeframe:** hvilken — 1h eller 4h — og om den kun bruges som filter.
- **Fyldning:** tæller en berøring af E som fyldt, eller kræves handel gennem E med ét
  tick?
- **Stopafstand i varianten "med afstand":** i tick, i procent af zonen eller i ATR.

### Tjeklisten (PRD §6)

| punkt | svar |
|---|---|
| instrumenter | MNQ. Signaler på NQ-data, se antagelse (A) |
| signaler | Kernen ovenfor, plus de filtre søgningen vælger |
| data | NQ.v.0 1m → 15m. Døgnserie til zoner, RTH-maske til berøringer |
| timing | Indgang 15:30-21:30 dansk tid. Fladt 21:50. Én afgjort handel om dagen |
| eksekvering | Limitordre på E (zonens kant + 10% buffer) med vedhæftet stop og mål (bracket). Lægges når zonen er aktiv. Fyldningsregel åben |
| sizing | Højst $250, kontrakter rundet ned. Zoner over stoploftet handles ikke |
| afstemning | Efter hver ordrehændelse læses position og åbne ordrer fra brokeren og holdes op mod bottens egen. Afvigelse → ingen nye ordrer, alarm |
| risiko | Disciplinreglerne i PRD §3a. BE efter varianten der vinder |
| genopretning | Zoner kan genberegnes fra prisdata. Det eneste der skal gemmes er hvilke zoner der er brugt og dagens tællere. Ved genstart læses det fra disk og afstemmes mod brokeren |
| logning | Hver zone (dannet, berørt, død), hver ordre, og en journal pr. dag — ejerens regel |

### Signaloptællinger

Optællingerne ser ikke på udfald og lægger intet til tælleren.

| optælling | kerne | præregistrering | resultat |
|---|---|---|---|
| 1 | v1 | `research/prereg/b4_k1_optaelling.md` | 1.940 af 2.012 dage med signal, 96,4% (95,5-97,1). Kategori ≥ 590. 55,4% af signalerne i lyset lige efter udbruddet. `research/output/b4_k1_optaelling.md` |
| 2 | v2 | `research/prereg/b4_k1_optaelling_v2.md` | 1.817 af 2.012 dage med signal, 90,3% (88,9-91,5). Kategori ≥ 590. 19,1% berøringer lige efter aktiveringen. 47,2% af signalerne fra zoner dannet uden for RTH. Uden buffer: 1.844 dage, 91,7%. `research/output/b4_k1_optaelling_v2.md` |

### Edge-testens omfang — besluttet 2026-09-22

**Trin A — resultat, 2026-09-23** (`research/output/b4_k1_trinA_laest.md`): bedste variant buffer 0 / ingen BE, middel_R_netto 0,095 [0,010; 0,180], **p_FWE 0,15** mod N1. Ikke skelnelig fra tilfældigt placerede zoner. BE hjælper ikke; bufferen er uafgjort. Handling: trin 2. N = 6. **Efter motorrettelsen** (`research/output/b4_k1_motorrettelse.md`): kernen er **negativ netto i alle 6 varianter** (−0,004 til −0,046 R), og retesten holder **50-51%**, ikke 90%. Fyldningsbaren havde givet 0,06-0,13 R for meget.

**Trin A først:** kernen v2 med BE (ingen / 1,0R / 1,2R) × buffer (10% / 0%) = 6 varianter, faktor 1,50× mod N = 3. Filtersøgningen er et eget, senere trin med egen præregistrering. Præregistreret 2026-09-23 i `research/prereg/b4_k1_trinA.md`: serien er **MNQ.v.0 2019-05-06 til 2023-12-31** (1.173 RTH-dage), nulmodellen er N1 (tilfældig dannelsestid, 500 gentagelser, Westfall-Young maks-statistik), fyldningsreglen er gennemhandling med ét tick med rækkefølgen inde i baren afgjort på 1m-serien, og det afgørende mål er middel netto-R pr. handel, ikke win rate.

### Trin 2 — aftalt 2026-09-23, før optællingen

| emne | beslutning |
|---|---|
| Hvad testes | Videoens egen påstand: jo flere kriterier, jo bedre (16:00). Score 0-7 pr. zone. Hovedtest: stiger middel netto-R med scoren? Varianter: brud på struktur alene og tærskler på scoren, fastlagt efter optællingen |
| BE | +1,2R, fast, én version. Ejerens 60%-regel |
| Buffer | 10%, fast, én version. Ejerens regel |
| Spor | A: 15m med 1h. B: 5m med 15m (videoens eksempel). B går kun videre hvis omkostningerne tillader det, besluttet på udfaldsfri tal |
| Definitioner | `research/prereg/b4_k1_trin2_optaelling.md` §3 |
| **Stopregel** | **Stiger middel netto-R ikke med scoren, parkeres kandidat 1, og kandidat 2 findes.** Ingen redningsforsøg |

**Optællingen, 2026-09-23** (`research/output/b4_k1_trin2_optaelling.md`, udfaldsfri, præciseringer i `research/prereg/b4_k1_trin2_optaelling_tillaeg.md`):

| | spor A, 15m/1h | spor B, 5m/15m |
|---|---|---|
| signaler_n | 3.349 | 9.273 |
| dage_med_signal_n ved score ≥ 2 / ≥ 3 / ≥ 4 | 1.012 / 883 / 585 | 1.168 / 1.127 / 942 |
| dage_med_signal_n, brud alene | 914 | 1.139 |
| omk_R_netto_p50 / p90 | 0,063 / 0,177 | 0,092 / 0,265 |
| be_WR_pct_netto_p50 | 35,4 | 36,4 |

Alle tre tærskler og "brud alene" er testbare på begge spor (§5). Kriterium 6 og 7 trækker mod hinanden (phi −0,48 / −0,53), og kriterium 1 og 4 måler delvis det samme (+0,46 / +0,52). Spor B: **med**, besluttet af ejeren 2026-09-24. Trin 2 præregistreret i `research/prereg/b4_k1_trin2.md`: hovedtest (hældning af middel netto-R på scoren, pr. spor) og otte varianter, N i alt 16.

### Kandidat 1 — PARKERET 2026-09-25

Trin 2 (`research/output/b4_k1_trin2_laest.md`): middel netto-R falder med scoren på begge spor (β −0,034 og −0,029 R pr. trin; spor B med CI under nul). Stopreglen udløst. Alle sikringer mod at overse en edge er brugt, og ingen ændrer afgørelsen. Tælleren står på 16 og følger med. Holdout er uåbnet.

## Kandidat 2 — Nowick: lys uden væge i trendens retning

**Kilde:** bard.fx, Instagram-reel set 2026-10-07 (`research/kilder/bardfx_nowick_reel_noter.md`). Et rødt lys uden topvæge i en nedtrend, eller et grønt uden bundvæge i en optrend. Limitordre på lysets åbning, når prisen inden for få lys kommer tilbage. Stop bag seneste swing, mål cirka 1:1. Påstanden om 85% vinderrate er udokumenteret.

**Besluttet af ejeren 2026-10-07:**
- MNQ 5m med trenden aflæst på daily (hovedtidsramme) og 4H (variant).
- Signallys med nul ticks væge; trenden aflæst ved brud på swing-punkter (N = 5).
- Retest-vindue 3, 5 eller 9 lys; nyeste signal erstatter den ventende ordre.
- Stop bag 10-lys-ekstremen plus 2 ticks; mål 1R og 2R.
- Én handel om dagen; rammerne fra kandidat 1 uændrede.
- Nulmodellen er almindelige lys med væge under samme regler.

12 varianter; tælleren går fra 16 til 28. Præregistreret i `research/prereg/b4_k2_nowick.md`.

### Kandidat 2 — PARKERET 2026-10-07

Kørslen (`research/output/b4_k2_nowick_laest.md`) gav række 4 i §8: alle 12 varianter er negative netto (−0,12 til −0,20 R), og alle konfidensintervaller ligger under nul. Ved 1:1 ramte 40% målet og 45% stoppet. Lys uden væge klarede sig en smule ringere end almindelige lys under samme regler. Fyld ved berøring og bedste fald i de tvetydige minutter giver samme række. Tælleren står på 28, og holdout er uåbnet.

**Læring på tværs af kandidat 1 og 2:** en limitordre tilbage ved udspringet af et stærkt lys, i trendens retning, holder omkring halvdelen af gangene på MNQ og taber netto. Nye kandidater med samme mekanik sammenlignes med disse to resultater, før de bygges.

## Kandidat 3 — vending efter åbningen

**Kilde:** BKTraders, YouTube-video set 2026-10-07 (`research/kilder/bktraders_nasdaq_routine_noter.md`). Den første halve time sætter en retning. Mellem 10 og 12 New York-tid går man ind på et volatilitetslys i modsat retning. Videoens stop og mål var sat efter kontoen; her styrer markedet stop og mål, og kontoen styrer størrelsen. Mekanikken er ny i forhold til kandidat 1 og 2: et udbrud med markedsordre, ikke en limitordre der venter på en retest.

**Besluttet af ejeren 2026-10-07** (svar 5 læst som A):
- 1m, åbningens retning fra 08:30 til 09:00 CT uden tærskel.
- Volatilitetslys med true range > k × ATR(14), hvor k er 1,0, 1,5 eller 2,0.
- Markedsordre ved næste bar, stop 2 × ATR, mål 1,5R, én handel om dagen.
- Nulmodeller: N-tid (tilfældigt tidspunkt) afgør, N-med (åbningens retning) forklarer.

3 varianter; tælleren går fra 28 til 31. Præregistreret i `research/prereg/b4_k3_vending.md`.

### Kandidat 3 — PARKERET 2026-10-08

Kørslen (`research/output/b4_k3_vending_laest.md`) gav række 4 i §8. Brutto ligger modellen omkring nul (−0,01 til +0,02 R), og netto taber den −0,05 til −0,07 R. Ingen variant slår et tilfældigt tidspunkt (p_FWE 0,25–0,97). Fortsættelse i åbningens retning er lige så god eller dårlig som vending. Tælleren står på 31, og holdout er uåbnet.

**Læring på tværs af kandidat 1–3:** simple prismønstre på MNQ inden for dagen har givet brutto omkring nul og netto tab svarende til omkostningen. En ny kandidat skal have en begrundet forventning om et bruttoafkast over cirka 0,05–0,10 R pr. handel, før den bygges.

## Kandidat 4 — EMT: tilbage til VWAP efter et udmattelseslys

**Kilde:** Instagram-reel set 2026-10-08 (`research/kilder/emt_reel_noter.md`). Når prisen er strakt væk fra VWAP og 9 EMA, venter man på et lys med en kraftig væge og går imod strækket på bruddet af lyset. Stoppet sidder bag vægen, målet er VWAP. Ejeren troede først, at der blev brugt EMA 200; reelen siger 9 EMA.

**Besluttet af ejeren 2026-10-08:**
- VWAP med anker kl. 17:00 CT og 9 EMA, 5m.
- Stræk på k × ATR, hvor k er 1,5, 2,0 eller 3,0.
- Væge på mindst 50%. Stop-ordre i næste lys, stop 2 ticks bag vægen.
- Målet er VWAP, opdateret løbende. 1 eller 2 handler om dagen.
- Spring over under 1R (overblikssessionens anbefaling, som ejeren hældede til).

6 varianter; tælleren går fra 31 til 37. Præregistreret i `research/prereg/b4_k4_emt.md`.

### Kandidat 4 — PARKERET 2026-10-08

Kørslen (`research/output/b4_k4_emt_laest.md`) gav række 4 i §8. Alle 6 varianter er negative netto (−0,09 til −0,24 R) og brutto (−0,01 til −0,14 R). Stoppet bag vægen rammes i 69–77% af handlerne. Udmattelseslyset slår ikke et tilfældigt strakt lys i samme time. At handle med strækket (N-mod) er bedre end imod det i alle 6 varianter, men N-mod ligger selv omkring 0. Tælleren står på 37, og holdout er uåbnet.

## Kandidat 5 — VWAP-trend efter Zarattini og Aziz (2023)

**Kilde:** SSRN 4631351, hele artiklen læst 2026-10-08 (`research/kilder/zarattini_aziz_vwap_noter.md`). Long over VWAP og short under, vend ved hver 1m-lukning på den anden side, altid i markedet og fladt ved dagens slut. Artiklen fandt Sharpe 2,1 på QQQ 2018–2023. Udkastet med analysen ligger i `research/prereg/b4_k5_vwap_trend_udkast.md`.

**Besluttet af ejeren 2026-10-08:**
- Handel hele RTH-dagen fra 08:31 CT. Fladt 14:55 CT (21:55 dansk tid), anbefalet af overblikssessionen efter ejerens spørgsmål om 21:55 eller 21:59.
- Alle vendinger, som i artiklen.
- 1m og 5m × hele dagen eller uden 11:00–14:00 CT.
- Nulmodel: samme handler med tilfældig retning.
- Mål: netto-dollar pr. dag pr. MNQ. Fryses kun ved p_FWE ≤ 0,05 og CI-nedre > 0. Bagefter afgør ruinmodellen sizingen.

**Overblikssessionens præciseringer:** målet regnes ved dagens niveau (NQ 29.138), fordi omkostningen er fast i dollar, mens kursbevægelserne vokser med niveauet. Ingen ekstra slippage ud over $2,627, fordi alle ordrer er markedsordrer på et lys' åbning.

4 varianter; tælleren går fra 37 til 41. Præregistreret i `research/prereg/b4_k5_vwap_trend.md`.

**Læring på tværs af kandidat 1–4:** fortsættelse slog tilbageløb i kandidat 1, 2 og 4, men lå selv omkring 0 netto. Kandidat 5 tester fortsættelse med en dokumenteret regel fra litteraturen. Omkostningen er cirka lige så stor som artiklens gevinst pr. handel. Artiklens periode overlapper vores in-sample, så den rene test er holdout.

### Kandidat 5 — FROSSET 2026-10-08: 1m · uden middag

Kørslen (`research/output/b4_k5_vwap_trend_laest.md`) gav række 1 i §8. "1m · uden middag" har netto $41,07 pr. dag pr. MNQ ved dagens niveau, CI95 [9,02; 73,12], og p_FWE 0,0020 mod samme handler med tilfældig retning. Brutto gentager artiklen: cirka 1 bp pr. handel, gevinst kl. 9:30–11:30 og 15–16 New York-tid.

- **Solidt:** VWAP-retningen bærer (t omkring 4 på 1m).
- **Tyndt:** nettogevinsten. Den holder ved $3,169 (CI-nedre +2,01), men nominelt ved det historiske niveau ligger den omkring 0 (−2,64). 2023 var negativt. Gevinsten kommer fra de volatile år og få store dage.
- **Topstep-risiko:** største tab inden for en dag var $2.830 med 1 MNQ, mod en MLL på $2.000.

Tælleren står på 41. Holdout er uåbnet og ukøbt. Næste skridt: præregistrering af holdout-testen, køb af data og en ruinmodel for daglig P&L.

**Holdout-testen, præregistreret 2026-10-08** (`research/prereg/b4_k5_holdout.md`, ejerens svar 1A–4A):
- MNQ 1m fra 2024-01-02 til 2026-09-30 købes for højst $15.
- Retningen (H1) og nettogevinsten (H2, énsidet) testes hver for sig.
- Holder retningen, men nettogevinsten ikke kan bevises, fortsætter vi til ruinmodel og forward-test. En Combine købes kun, hvis den samlede nedre grænse er over 0, ruinmodellen slår nulmodellen ved den, og forward-testen er bestået.
- Holdout åbnes én gang og tæller ikke som nyt forsøg.

### Kandidat 5 — PARKERET 2026-10-08 efter holdout

Holdout-kørslen (`research/output/b4_k5_holdout_laest.md`) gav række 4 i §5:
- Brutto faldt fra $74,40 til $3,65 pr. dag. Netto blev −$30,55 med CI90 [−59,68; −1,42].
- p_H1 var 0,43, så VWAP-retningen er ikke bedre end tilfældig i 2024–2026. Alle tre år var negative.
- Faldet fra in-sample er ikke tilfældigt (z cirka 3,0). Det passer med, at offentliggjorte mønstre svækkes.

Holdout er åbnet én gang og er ikke længere ren for hypoteser om VWAP og momentum inden for dagen. Tælleren står på 41.

## Screening efter kandidat 1–5 (2026-10-08)

Ejerens svar:
- **1A:** screening af mekanismer frem for nye prismønstre.
- **2A:** handel uden for RTH er tilladt inden for Topsteps regler.

Screeningen ligger i `research/output/b4_screening.md`. Hver mekanisme er holdt op mod fem filtre: hvem betaler, Topstep og MNQ, styrke, omkostning og rene data.

| mekanisme | afgørelse |
|---|---|
| Overnight drift ved Europas åbning (Boyarchenko, Larsen og Whelan 2023) | anbefales som kandidat 6 |
| Stop-kaskader ved runde tal (Osler) | lav prioritet |
| Natrange som kontekst for åbningen | lav prioritet |
| Turn of the month | udelukket: ingen mekanisme |
| Pre-FOMC drift | udelukket: forsvandt efter 2015 og har for få handler |
| Momentum sidst på dagen | udelukket: væk i 0DTE-tiden, og holdout er brugt |

## Kandidat 6 — overnight drift ved Europas åbning

**Kilde:** Boyarchenko, Larsen og Whelan (2023, RFS). S&P-futures stiger kl. 2–3 New York-tid (08–09 dansk tid), mest efter salgsdage. Mekanismen er betaling til markedsmagere for at bære lagerrisiko.

**Besluttet af ejeren 2026-10-09** (svar 1A–6A):
- Vinduer: 02:00–03:00 og 01:30–03:30 New York-tid.
- Nætter: alle, og kun efter en salgsdag (RTH-afkast < 0).
- Data: NQ 2016–2023 som hovedserie, MNQ 2019–2023 som kontrol.
- Nulmodel: en tilfældig anden time samme nat.
- Mål: netto-$ pr. nat pr. MNQ ved dagens niveau. Fryses ved p_FWE ≤ 0,05 og CI-nedre > 0.
- Intet stop i testen.

4 varianter; tælleren går fra 41 til 45. Præregistreret i `research/prereg/b4_k6_overnight.md`. Kravet om kun at handle i RTH er løftet for denne kandidat. Topsteps regler gælder.
