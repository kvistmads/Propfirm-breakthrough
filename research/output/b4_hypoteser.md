# B4 — hypoteser

**Skrevet:** 2026-09-22 af overblikssessionen. Leverancen fra `PRD_FASE3_B4_EDGE.md` §6.
**Status:** kandidat 1 er specificeret. Ingen edge-test er kørt. Kandidat 2 og frem mangler.

---

## Fælles for alle kandidater

| emne | beslutning | hvor |
|---|---|---|
| In-sample | 2016-01-01 til 2023-12-31, 2.012 handelsdage | PRD §4, besluttet 2026-09-22 |
| Holdout | fra 2024-01-01, 676 handelsdage. Forseglet i `data/holdout.py` | PRD §4 |
| Prisdata | NQ.v.0 1m fra Databento, aggregeret til 15m med `data/resample.py` | fase 1 |
| MNQ mod NQ | MNQ-OHLCV findes ikke i cachen og ikke før 2019-05-06. **Antagelse (A):** et prisniveau i indekspoint er det samme på NQ og MNQ. Et krydstjek på MNQ-væger (~$9,46, fase 2's estimat) tages op når edge-testen præregistreres | fase 2 §1 |
| Prisniveau | Afstande i point regnes i procent og omregnes ved NQ 29.138 | fase 2 |
| Disciplin, tradeforvaltning, sizing | Højst $250, rundet ned. Én afgjort handel om dagen. BE testes som tre varianter | PRD §3a-3c |
| Tidsvindue | Indgang 15:30-21:30 dansk tid (08:30-14:30 CT), fladt 21:50 | STRATEGI §3 |

---

## Kandidat 1 — supply og demand

**Kilde:** Mads. Videoen "Master Institutional Supply and Demand Trading" (Matt Donlevey,
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

| element | regel | videoen |
|---|---|---|
| Timeframe | 15m | vennen |
| Zone | **Pivot:** basislyset er lyset lige før udbrudslyset. Demand: basislyset er rødt (close < open), udbrudslyset lukker **over** basislysets high. Supply: omvendt. Zonen går fra basislysets high til low, **væger medregnet** | 8:47 |
| Gyldig fra | Udbrudslysets lukning. Før det findes zonen ikke | — |
| Frisk | Kun første berøring efter dannelse | 15:55 |
| Dør | Ved første berøring, uanset tidspunkt. Ved kontraktskift (nyt `instrument_id`) | — |
| Indgang | Limitordre på zonens nære kant — demand: zonens high, supply: zonens low | 9:50 |
| Stop | Zonens fjerne kant | 9:50 |
| Mål | 2R. Videoen bruger fast R med 3R som eksempel; 2R er vores beslutning | 16:57, PRD §3 |
| Tidsvindue | Berøringen skal ske 15:30-21:30 dansk tid. Zonen må være dannet når som helst, også om natten | STRATEGI §3 |
| Stoploft | Zonehøjde ≤ 0,429% af prisen (125 point ved NQ 29.138), så 1 MNQ ≤ $250 | PRD §3c |
| Kontrakter | `floor(250 / (stop_pt × 2))` | PRD §3c |

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
| Zonetype | pivot / range | 8:47 |
| Basislysets farve | streng / enhver farve | 9:19 |
| BE | ingen / 1,0R / 1,2R | PRD §3b |

Filter 8 (frisk zone) er i kernen. Filtrene 1-7 alene giver 128 kombinationer, og
tærsklen stiger med 3,07× mod N = 3. Krydses de med alle øvrige varianter, er N = 3.072
(128 × 2 × 2 × 2 × 3), og faktoren er 4,20×. Hvor mange der faktisk krydses, afgøres når
edge-testen præregistreres — tallet der rapporteres er det faktiske N, ikke dette loft.

### Åbne definitioner — fastlægges før edge-testen præregistreres

- **Swing-punkter:** længde på venstre og højre side. Hvert punkt har to tidsstempler —
  hvornår det skete, og hvornår det blev bekræftet. Backtesten bruger det kun fra
  bekræftelsen.
- **Range for filter 7:** hvilket swing-high og swing-low der afgrænser den.
- **Sweep, likviditet foran, flip:** operationelle definitioner. LuxAlgo's EQH/EQL (lige
  toppe og bunde inden for 0,1 ATR) er inspiration, ikke kode (licensen er CC BY-NC-SA).
- **Højere timeframe:** hvilken — 1h eller 4h — og om den kun bruges som filter.
- **Fyldning:** tæller en berøring af kanten som fyldt, eller kræves handel gennem kanten
  med ét tick?
- **Stopafstand i varianten "med afstand":** i tick, i procent af zonen eller i ATR.

### Tjeklisten (PRD §6)

| punkt | svar |
|---|---|
| instrumenter | MNQ. Signaler på NQ-data, se antagelse (A) |
| signaler | Kernen ovenfor, plus de filtre søgningen vælger |
| data | NQ.v.0 1m → 15m. Døgnserie til zoner, RTH-maske til berøringer |
| timing | Indgang 15:30-21:30 dansk tid. Fladt 21:50. Én afgjort handel om dagen |
| eksekvering | Limitordre på nær kant med vedhæftet stop og mål (bracket). Fyldningsregel åben |
| sizing | Højst $250, kontrakter rundet ned. Zoner over stoploftet handles ikke |
| afstemning | Efter hver ordrehændelse læses position og åbne ordrer fra brokeren og holdes op mod bottens egen. Afvigelse → ingen nye ordrer, alarm |
| risiko | Disciplinreglerne i PRD §3a. BE efter varianten der vinder |
| genopretning | Zoner kan genberegnes fra prisdata. Det eneste der skal gemmes er hvilke zoner der er brugt og dagens tællere. Ved genstart læses det fra disk og afstemmes mod brokeren |
| logning | Hver zone (dannet, berørt, død), hver ordre, og en journal pr. dag — Mads' regel |

### Første skridt

Signaloptællingen: `research/prereg/b4_k1_optaelling.md`. Den ser ikke på udfald og lægger
intet til tælleren.
