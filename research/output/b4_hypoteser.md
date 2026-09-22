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

Besluttet 2026-09-22. Rækkefølgen er videoens: range → udbrud → prisen forlader zonen →
prisen vender senere tilbage → handel på retesten. Eksemplet er en demand-zone; supply er
spejlvendt.

| element | regel | kilde |
|---|---|---|
| Timeframe | 15m | vennen |
| **1. Udbrud** | Basislyset er lyset lige før udbrudslyset. Basislyset er rødt (close < open), og udbrudslyset lukker **over** basislysets high. Zonen går fra basislysets high til low, **væger medregnet**. Højden H = high − low. Zonen findes fra udbrudslysets lukning | video 8:47 |
| Buffer | B = 10% af H. Indgangsniveauet er E = high + B | Mads, 2026-09-22 |
| **2. Prisen forlader zonen** | Zonen bliver **aktiv** ved det første lys, fra og med udbrudslyset, hvis low ligger over E. Indtil da tæller berøringer ikke. **Lukker et lys under zonens low før aktivering, er zonen ugyldig** | video 7:31; Mads, 2026-09-22 |
| **3. Retest** | Første lys efter aktiveringen hvis low ≤ E. Det er berøringen. Zonen dør ved den, uanset tidspunkt | video 15:55 |
| Indgang | Limitordre på E. Fyldes ved berøringen | video 9:50, med Mads' buffer |
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

### Mads' forventning, skrevet før edge-testen

**Retesten holder cirka 9 ud af 10 gange**, hvis zonerne er sat rigtigt (Mads, 2026-09-22).
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
| Buffer | 10% / 0% (videoens kant) | Mads mod 9:50 |
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
| logning | Hver zone (dannet, berørt, død), hver ordre, og en journal pr. dag — Mads' regel |

### Signaloptællinger

Optællingerne ser ikke på udfald og lægger intet til tælleren.

| optælling | kerne | præregistrering | resultat |
|---|---|---|---|
| 1 | v1 | `research/prereg/b4_k1_optaelling.md` | 1.940 af 2.012 dage med signal, 96,4% (95,5-97,1). Kategori ≥ 590. 55,4% af signalerne i lyset lige efter udbruddet. `research/output/b4_k1_optaelling.md` |
| 2 | v2 | `research/prereg/b4_k1_optaelling_v2.md` | endnu ikke kørt |
