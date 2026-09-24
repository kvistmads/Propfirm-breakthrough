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
