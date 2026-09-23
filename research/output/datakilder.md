# Datakilder — fase 1

Kortlagt og verificeret 2026-09-11. Besvarer B1 (kilder, dybde, pris, overensstemmelse) og
første del af B3 (kan spread måles, og hvorfra). PRD: `PRD_FASE1_DATAGRUNDLAG.md`.

## Konklusion

| spørgsmål | svar |
|---|---|
| Kilde | **Databento GLBX.MDP3** — CME's egen Globex-feed — via gratis kredit. Ingen nøglefri kilde har ≥ 3 år NQ intradag; Yahoo har 60 dage på 15m |
| K1 dybde | **Holder.** 16,26 år NQ 1m; 10,69 år i de år der også består K3 (2016-2026) |
| K2 to kilder | **Holder.** Yahoo og Databento er identiske bar for bar: samme bar-grænser, samme tidszone, median afvigelse i dagligt range 0,00% |
| K3 dækning | **Holder for 2016-2026** (0,00-0,05% manglende RTH-minutter pr. år). **Ikke for 2010-2015** (11-79%) |
| K4 degeneration | **Holder i alle RTH-celler** (≤ 0,02% flade barer). Fejler for 1m døgn (2,02% i 2016-2026) |
| Rullen | 65 skift, 4 om året, ingen frem-og-tilbage. Flytter p90 i ATR-fordelingen under 0,5% |
| Spread | **Kan måles, og er målt** på MNQ fra Databentos bid/ask (92 dage 2019-2026): **RTH 1,73 tick, uden for RTH 2,17 tick** i snit mod skønnet 1,5. Rundturen bliver $2,59 i RTH og $2,80 uden for RTH mod $2,47 |
| Forbrug | $27,31 af $40 |

---

## 1. Kildeoversigt (§4.1)

"Målt" betyder hentet og talt af os. "Oplyst" betyder udbyderens egen side.

| kilde | NQ / MNQ | opløsninger | dybde | pris | må vi handle på det? |
|---|---|---|---|---|---|
| **Databento GLBX.MDP3** | begge, CME-primærdata | 1s/1m/1h/1d OHLCV, trades, bid/ask | **målt:** 1m fra 2010-06-07; komplet RTH fra 2016 | $125 gratis kredit | ja, intern kommerciel brug |
| **Yahoo NQ=F** | NQ, kontinuerlig | 1m/2m/5m/15m/30m/1h… (ingen 3m) | **målt:** 1m 30 d, 15m 60 d, 1h 730 d | gratis | nej — personlig brug |
| London Strategic Edge | **sandsynligvis ingen** — "futures" = Eurex | 14, inkl. 1m/3m/5m/15m | futures ikke oplyst | gratis nøgle | ja, ikke videresalg |
| FirstRate Data | NQ, kontinuerlig + enkeltmåneder | 1m/5m/30m/1h (ingen 15m) | oplyst fra 2008-01-02 | betalt, 2 ugers prøve | ikke oplyst |
| Dukascopy | **nej** — CFD på Nasdaq-100 | tick/1s/1m… | 1m fra 2011 (tredjepart) | gratis | **nej** — ikke-kommerciel, ingen database |
| Barchart | NQ | 1m intraday ~10 år | kun Premier | betalt | ikke oplyst |
| TopstepX / ProjectX | begge | sekund…måned | ikke oplyst | Topstep-konto + $14,50/md | — (det er venuet) |

**Ingen kilde uden konto har ≥ 3 år NQ 15m.** Den eneste nøglefri kilde er Yahoo, og den
rækker 60 dage på 15m — samme cap som §5's 0,168% blev målt under.

### Databento — GLBX.MDP3 (valgt)

| felt | |
|---|---|
| Instrumenter | NQ og MNQ som enkeltkontrakter. Kontinuerlig via symbologi: `NQ.v.0` (størst volumen), `.c.0` (nærmeste udløb), `.n.0` (open interest). Rå priser, ingen tilbagejustering |
| Opløsninger | ohlcv-1s/-1m/-1h/-1d, trades, mbp-1/-10, mbo, bbo-1s/-1m, tbbo. **Ingen 3m/5m/15m** — aggregeres fra 1m |
| Dybde | oplyst fra 2010-06-06. **Målt:** første 1m-bar 2010-06-07 00:00 UTC, sidste 2026-09-10 23:59 UTC (4.818.677 barer). RTH er komplet fra 2016 — se §3 og §6 |
| Pris | usage-based, estimeres gratis før hvert udtræk. $125 kredit ved oprettelse, udløber efter 6 md. Fase 1-loft $40 (hævet fra $25); brugt $27,31 |
| Licens | intern kommerciel brug tilladt på alle planer. Cachen og prisdetaljer er git-ignoreret |
| Format | DBN/CSV/JSON over HTTP. Python-klient `databento` 0.86 |
| Sessioner / tidszone | **UTC**, nanosekunder. Hele Globex-døgnet, ingen RTH-markering — den lægger datalaget på efter NYSE-kalenderen |
| Quotes | **ja** — bbo-1s, bbo-1m, mbp-1, tbbo |

### Yahoo Finance — NQ=F (anden kilde til K2)

| felt | |
|---|---|
| Instrumenter | NQ som Yahoos egen kontinuerlige front-kontrakt. Rulledato udokumenteret |
| Opløsninger | 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 4h, 1d og op. **3m afvises** af API'et |
| Dybde (målt 2026-09-11) | 1m: 30 dage, højst 7 pr. kald. 5m/15m: fra 2026-07-01. 1h: fra 2024-04-18 |
| Pris | gratis, ingen nøgle |
| Licens | yfinance er uofficiel; Yahoos data er til personlig brug. Egnet til krydstjek, ikke som grundlag |
| Format | uofficielt JSON-API via yfinance 1.7. Ingen dokumenterede rate limits |
| Sessioner / tidszone | **America/New_York**, tz-aware. `prepost=True` giver hele døgnet |
| Quotes | nej |

### London Strategic Edge (droppet 2026-09-11)

| felt | |
|---|---|
| Instrumenter | "54 futures" uden symbolliste. Den officielle klient (`lse-data`, `client.py`) mapper kategorien *Futures* til datasættet **`eurex`**. NQ/MNQ nævnes ingen steder. Kataloget kræver nøgle (HTTP 401 uden), så det kunne ikke efterprøves |
| Opløsninger | 1s, 5s, 15s, 30s, 1m, 3m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1mo |
| Dybde | aktier 2003, FX 2009, krypto 2017. Futures ikke oplyst |
| Pris | gratis nøgle |
| Licens | egen research, trading og modeltræning, også kommercielt. Ikke videresalg eller redistribution |
| Format | REST, maks 5.000 rækker pr. kald, plus asynkron Parquet-eksport. Streaming og download deler én kvote |
| Tidszone | UTC |
| Quotes | ikke dokumenteret for futures |

### De øvrige

- **FirstRate Data** — NQ kontinuerlig fra 2008-01-02 i tre justeringsvarianter, enkeltkontrakter
  fra NQZ08. 1m/5m/30m/1h/1d, CSV i zip, US/Eastern. Betalt; to ugers gratis prøve. Ingen quotes.
- **Dukascopy** — `USATECHIDXUSD` er en CFD, ikke NQ. Gratis og dyb, med bid/ask — men
  CFD'ens spread, ikke CME's. Vilkårene tillader kun personlig, ikke-kommerciel brug og
  forbyder at opbygge en database af indholdet. Uegnet.
- **Barchart** — 1m intraday ~10 år tilbage kræver Premier. Gratis: daglige priser 2 år.
  Maks 10.000 rækker pr. download.
- **TopstepX / ProjectX Gateway** — historik via `POST /api/History/retrieveBars` (sekund til
  måned, maks 20.000 barer pr. kald, dybde ikke oplyst). Realtid via market hub:
  `GatewayQuote` med `bestBid`/`bestAsk`, `GatewayTrade`, `GatewayDepth`. Kræver
  Topstep-konto og API-abonnement — uden for fase 1, men det er serien botten handler i (C7).
- **Portara (CQG), Kibot** — betalte. Level 1-tick med bid/ask for NQ; Portara fra 1999.

---

## 2. Valg

**Databento**, besluttet af ejeren 2026-09-11, med disse betingelser:

1. Budget for fase 1: $40 af kreditten (hævet fra $25, så spread kan måles). Prisestimat før hvert udtræk.
2. Kun 1m OHLCV. 3m/5m/15m aggregeres, så alle timeframes deler bar-grænser.
3. ATR måles på NQ, spread på MNQ — og MNQ først fra noteringen 2019-05-06.
4. Spread på en stikprøve af rolige og volatile dage, RTH og uden for RTH hver for sig.
5. Rullemetoden dokumenteres og antallet af spring rapporteres.

Yahoo er anden kilde til K2. LSE droppes. Budgetloft og MNQ-notering håndhæves i
`data/src_databento.py`.

---

## 3. Verifikation (§4.2) — K1-K4

Operationaliseringen er præregistreret i `research/fase1_verifikation.py`. Tal fra
`research/output/fase1_verifikation.json`.

| # | kriterium | tærskel | målt | holder |
|---|---|---|---|---|
| **K1** | dybde på NQ 15m | ≥ 3 år | **16,26 år** (2010-06-07 → 2026-09-10). I K3-beståede år: **10,69 år** (2016 → 2026-09-10) | **ja** — via gratis kredit, ikke nøglefrit |
| **K2** | median abs. afvigelse i dagligt high-low-range, Yahoo mod Databento | < 5% | **0,00%** pr. CME-handelsdag (48 dage); **0,00%** i RTH (48 dage); maks 2,93% | **ja** |
| **K3** | manglende RTH-barer | < 2% | **2016-2026: 0,00-0,05%** pr. år · 2010-2015: 11,0-79,0% · hele perioden 13,6% | **ja for 2016-2026**, nej for 2010-2015 |
| **K4** | flade barer · ikke-monotone timestamps | < 1% · 0 | RTH: **≤ 0,02%** i alle timeframes · døgn 1m: 2,02% (2016-2026), 5,41% (hele) · ikke-monotone: **0** | **ja i RTH**; nej for 1m døgn |

K3 er gjort op pr. år mod NYSE-kalenderen, og **ATR-fordelingens go/no-go-tabel bruger kun
de år der består** (`atr_fordeling.md`). Helhistorik-tabellen står uændret ved siden af.

### K2 — Yahoo mod Databento

| måling | resultat |
|---|---|
| Overlap | Yahoos 15m-øjebliksbillede 2026-07-01 → 2026-09-10: 50 CME-handelsdage uden de delvise ender |
| Udeladt (barantal > 10% fra hinanden) | 2026-07-03 (Yahoo 24 barer mod 76, halv helligdag) og 2026-09-08 (68 mod 92; range alligevel identisk) |
| Dagligt range, CME-handelsdag | median **0,00%**, p90 0,00%, én dag over 0,5% (2026-08-31: 2,93%) |
| Dagligt range, RTH | 0,00% alle 48 dage |
| Bar for bar, 2026-08-26 RTH | **26 af 26 15m-barer og 390 af 390 1m-barer har identisk open/high/low/close til tick** |
| Tidsforskydning | Spearman-korrelation af 1m-afkast topper ved **0 minutter** (0,9986) |
| ATR 15m over samme 60 dage | RTH p50 0,2267% i begge kilder; døgn 0,1654% (Yahoo) mod 0,1625% |

Samme bar-grænser og samme tidszone. **Barerne er ikke bare statistisk ens — de er identiske;**
Yahoo aggregerer tydeligvis de samme CME-handler. K2 bekræfter dermed bar-grænser og tidszone,
men er ikke et uafhængigt prisestimat. På syv fredage afviger Globex-dagens sidste luk
(−36 til +117 point), mens dagens range er identisk — den sidste bar før weekenden er
forskellig hos de to kilder.

### K3 — manglende RTH-minutter pr. år

| år | sessioner | forventede minutter | manglende | mangler_pct | sessioner uden RTH-data |
|---|---|---|---|---|---|
| 2010 | 146 | 56.760 | 44.850 | **79,0** | 115 |
| 2011 | 252 | 98.100 | 71.760 | **73,1** | 184 |
| 2012 | 250 | 96.960 | 55.594 | **57,3** | 143 |
| 2013 | 252 | 97.740 | 15.803 | **16,2** | 40 |
| 2014 | 252 | 97.740 | 17.550 | **18,0** | 45 |
| 2015 | 252 | 97.920 | 10.759 | **11,0** | 27 |
| 2016 | 252 | 98.100 | 0 | 0,00 | 0 |
| 2017 | 251 | 97.530 | 0 | 0,00 | 0 |
| 2018 | 251 | 97.350 | 0 | 0,00 | 0 |
| 2019 | 252 | 97.740 | 0 | 0,00 | 0 |
| 2020 | 253 | 98.310 | 54 | 0,05 | 0 |
| 2021 | 252 | 98.100 | 0 | 0,00 | 0 |
| 2022 | 251 | 97.710 | 0 | 0,00 | 0 |
| 2023 | 250 | 97.140 | 0 | 0,00 | 0 |
| 2024 | 252 | 97.740 | 0 | 0,00 | 0 |
| 2025 | 250 | 96.960 | 0 | 0,00 | 0 |
| 2026 | 173 | 67.470 | 0 | 0,00 | 0 |
| **hele** | 4.091 | 1.589.370 | 216.370 | **13,6** | 554 |

Yahoo: 1m 0,08% (19 sessioner), 5m og 15m 0,00% (50 sessioner). 3m/5m/15m fra Databento arver
1m-dækningen — de er bygget af samme serie.

### K4 — flade barer (H = L)

| timeframe | RTH, hele | RTH, 2016-2026 | døgn, hele | døgn, 2016-2026 |
|---|---|---|---|---|
| 1m | 0,024% | 0,002% | **5,41%** | **2,02%** |
| 3m | 0,000% | 0,000% | **1,69%** | 0,36% |
| 5m | 0,000% | 0,000% | 0,71% | 0,13% |
| 15m | 0,001% | 0,001% | 0,10% | 0,07% |

Flade 1m-barer i døgnserien pr. år: 28,2% (2010) · 21,2 · 20,3 · 18,4 · 16,6 · 11,4 · 9,3 (2016) ·
10,1 (2017) · 1,3 (2018) · 0,65 · 0,39 · 0,16 · 0,04 · 0,11 · 0,12 · 0,07 · 0,05% (2026). Det er
tynde natminutter med én handel, ikke fejl — men de trækker 1m-døgn-ATR ned i de tidlige år.

**Ikke-monotone timestamps: 0.** Valideringen afviser ethvert udtræk der har dem, og alle 17
årsbidder passerede.

### Supplement — uforklarede spring

Præregistreret: |open − forrige close| ≥ 1 × ATR14 (1m) inden for samme kontrakt og uden brud.

- **2010-2017:** 2.000-7.400 pr. 100.000 barer. Tærsklen er for lav når natten er så tynd at
  ATR nærmer sig nul.
- **2018-2026:** 7-160 pr. 100.000 barer.
- **De største:** RTH-åbningen 09:30 ET den 9., 12., 13., 16. og 18. marts 2020 (op til 639
  ticks) — markedet stod limit-down om natten, 1m-barerne var flade og ATR ≈ 0. Markedshændelser,
  ikke datafejl.

---

## 4. Rullemetode

**Serie:** `NQ.v.0` — Databentos kontinuerlige symbologi, rangeret efter volumen. Rå priser, ingen
tilbagejustering. Kontraktskiftet sker ved UTC-midnat — 20:00 ET (49 gange) eller 19:00 ET (16) —
midt i Globex-natten, 1-5 minutter efter forrige bar. Det ses i data som skift i `instrument_id`.

**Håndtering i målingen:** true range bruger ikke forrige luk over et kontraktskift
(`data.sessions.break_mask`). En 3m/5m/15m-bar kan ikke blande to kontrakter —
`data.resample.aggregate` afviser det — og UTC-midnat er en grænse for alle timeframes.

**Antal spring: 65** fra 2010-06-14 til 2026-06-17 — 3 i 2010, 4 om året 2011-2025, 2 i 2026.
Ingen frem-og-tilbage-skift. Symbologien giver de samme 66 kontraktintervaller.

**Springets størrelse** (open i ny kontrakt − close i gammel) er kalenderspread og følger renten:

| år | 2010-2017 | 2018-2019 | 2020-2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|
| median \|spring\|, point | 2-8 | 26-27 | 7-14 | 57 | 189 | 260 | 231 | 268 |

Et 2026-spring på 268 point er ca. 4 × median-ATR på 15m i RTH. Uden brudhåndtering ville hver
rulle ligne en voldsom bar.

### Tidspunktet — `.v.0` halter 1-2 handelsdage

Dagsvolumen pr. kontrakt (Databento ohlcv-1d, $0,01):

| rulle | udløb | volumenskift (ny > gammel) | `.v.0` skifter | gammel kontrakts andel imellem |
|---|---|---|---|---|
| NQZ5 → NQH6 | fre 2025-12-19 | man 12-15 (305k mod 237k) | ons 12-17 | tir 12-16: 17% |
| NQH6 → NQM6 | fre 2026-03-20 | man 03-16 (279k mod 238k) | ons 03-18 | tir 03-17: 18% |
| NQM6 → NQU6 | fre 2026-06-19 | man 06-15 (338k mod 140k) | ons 06-17 | tir 06-16: 13% |
| MNQZ5 → MNQH6 | fre 2025-12-19 | tir 12-16 (1,71M mod 0,53M) | tor 12-18 | tir 24%, ons 12-17: 14% |
| MNQH6 → MNQM6 | fre 2026-03-20 | man 03-16 (0,97M mod 0,91M) | tor 03-19 | tir 18%, ons 03-18: 11% |
| MNQM6 → MNQU6 | fre 2026-06-19 | man 06-15 (1,66M mod 0,55M) | ons 06-17 | tir 06-16: 12% |

`.n.0` (open interest) skifter samme dag eller senere; `.c.0` først ved udløb. Ingen af de
færdige varianter følger volumenskiftet præcist. Den udløbende NQ-kontrakt handler stadig 70.000+
kontrakter om dagen i vinduet.

**Effekt på ATR-fordelingen** (følsomhed, 15m, hele perioden — præregistreret før NQ-data):

| variant | risiko_pct_af_MLL_netto_p90 RTH | risiko_pct_af_MLL_netto_p90 døgn |
|---|---|---|
| præregistreret | 12,63 | 8,28 |
| uden rullevinduer (5 handelsdage før skift) | 12,57 | 8,26 |
| helt uden brudhåndtering (`calculate_atr`) | — | 8,39 |

**Rullen forgifter ikke fordelingen:** brudhåndteringen fjerner springet, og dagene omkring
skiftet er ikke mere volatile end resten.

---

## 5. Spread (§4.5, B3)

### Kan spread udledes af OHLC-barer?

Nej. En bars high-low blander prisbevægelse og spread uadskilleligt. Der findes estimatorer der
forsøger (Roll 1984, Corwin & Schultz 2012, Abdi & Ranaldo 2017), men de estimerer i
basispunkter med en støj der er større end hele signalet her: ét MNQ-tick er 0,86 bp ved NQ
29.000. Spread skal måles på quotes.

### Hvilke kilder har quotes?

| kilde | quotes | bemærkning |
|---|---|---|
| **Databento** | **ja** | bbo-1s, bbo-1m, mbp-1, tbbo — CME's egen top of book |
| Yahoo, FirstRate, Barchart | nej | kun handler/OHLCV |
| London Strategic Edge | ikke dokumenteret | for futures |
| Dukascopy | ja, men CFD | ikke CME-spread |
| TopstepX / ProjectX | ja, realtid | `GatewayQuote.bestBid/bestAsk`. Venuets egen feed — relevant for C7. Kræver konto |
| Portara, Kibot | ja, betalt | Level 1-tick |

### Målt: MNQ, stratificeret stikprøve

Designet er præregistreret i `research/spread_stikproeve.py` før udtrækket. 92 Globex-handelsdage
2019-2026, trukket fra 1.659 sessioner: 4 pr. år × tercil af NQ's RTH-range (rolig ≤ 1,094% <
mellem ≤ 1,746% < volatil). 2022 har ingen rolige dage. Halve dage og rullevinduer er udeladt.
MNQ.v.0 bbo-1s lagt på et 1-sekunds gitter: 7,6 mio. sekunder, 11.001 låste eller krydsede
udeladt, ingen dag med to kontrakter. Fuld rapport: `research/output/spread_mnq.md`.

| mål | session | n_sekunder | gns_ticks | p10_ticks | p50_ticks | p90_ticks | andel_1_tick_pct |
|---|---|---|---|---|---|---|---|
| tidsvægtet | **RTH** | 2.152.676 | **1,73** | 1 | 2 | 2 | 34,4 |
| tidsvægtet | **ETH** | 5.441.191 | **2,17** | 1 | 2 | 3 | 15,6 |
| ved minutgrænse | RTH | 35.879 | 1,73 | 1 | 2 | 2 | 35,1 |
| ved minutgrænse | ETH | 90.589 | 2,16 | 1 | 2 | 3 | 15,7 |

**Pr. regime** (gns_ticks, tidsvægtet):

| session | rolig | mellem | volatil |
|---|---|---|---|
| RTH | 1,55 | 1,69 | 1,94 |
| ETH | 1,95 | 2,14 | 2,38 |

**Pr. år** (gns_ticks, tidsvægtet):

| session | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|
| RTH | 1,65 | 1,83 | 1,77 | 1,81 | 1,44 | 1,73 | 1,85 | 1,81 |
| ETH | 1,99 | 2,07 | 2,15 | 2,06 | 1,74 | 2,26 | 2,44 | 2,58 |

**Pr. tidsblok (ET):** RTH er bredest ved åbningen (09:30-10:00: 1,93; 10:00-10:30: 1,87) og
ligger derefter på 1,68-1,75 resten af dagen. Uden for RTH er genåbningen 18:00-18:30 bredest
(2,91, p90 4 tick), natten 00:00-01:30 smallest (2,00-2,06), 03:00-05:00 omkring 2,2, halvtimen
før åbning 1,95, og efter lukning 16:00-17:00 2,30-2,32.

**Omkostning pr. rundtur** — gebyr ($1,22) og slippage (0,5 tick pr. side) uændret; kun
spread-leddet skifter. R ved målt 15m RTH-ATR 2016-2026 og §5's NQ-niveau:

| variant | spread_ticks_gns | spread_usd_rundtur | omk_usd_rundtur | omk_R_netto_p50 (15m RTH) | be_WR_pct_netto_p90 (15m RTH) |
|---|---|---|---|---|---|
| skøn i `config.yaml` | 1,50 | 0,75 | 2,47 | 0,0180 | 34,40 |
| **målt RTH** | **1,73** | 0,87 | **2,59** | 0,0188 | 34,46 |
| målt uden for RTH | 2,17 | 1,08 | 2,80 | — | — |

- **Skønnet på 1,5 tick er for lavt i begge sessioner:** RTH-spreadet er 16% bredere, uden for
  RTH 44% bredere. I dollar er det $0,12 pr. rundtur i RTH og $0,33 uden for RTH.
- **Spreadet ved minutgrænsen er det samme som tidsvægtet** (1,73 mod 1,73 i RTH). Der er ingen
  ekstra udvidelse i det sekund en bar lukker.
- **Volatile dage er bredere:** RTH 1,94 tick mod 1,55 på rolige dage.
- **Uden for RTH er spreadet steget hvert år siden 2023** (1,74 → 2,58 tick).
- **`config.yaml` er ikke ændret.** Alle omkostningstal i projektet bruger stadig 1,5 tick.

### Krydstjek: sammenhængende 182 døgn, bbo-1m

Første udtræk, før ejeren bad om en stikprøve: MNQ.v.0 bbo-1m 2026-03-13 → 2026-09-10, ét snapshot
pr. minut (ved minutgrænsen), 179.155 snapshots, 953 låste/krydsede udeladt.

| session | n | gns_ticks | p10_ticks | p50_ticks | p90_ticks | andel_1_tick_pct |
|---|---|---|---|---|---|---|
| RTH | 48.747 | 1,87 | 1 | 2 | 2 | 26,3 |
| ETH | 129.455 | 2,66 | 2 | 2 | 3 | 3,2 |
| RTH uden rullevinduer | 45.627 | 1,79 | 1 | 2 | 2 | 27,9 |
| ETH uden rullevinduer | 121.636 | 2,58 | 2 | 2 | 3 | 3,4 |

Stemmer med stikprøvens 2026-dage (RTH 1,81, ETH 2,58). RTH er bredest ved åbningen
(09:30-10:00: 2,31 tick) og smallest om eftermiddagen (1,77-1,83). Uden for RTH er
genåbningen 18:00-18:30 bredest (3,53), fulgt af 08:00-08:30 (3,16).

### Hvad der stadig ikke er målt

- **Slippage på stops (C4).** bbo giver det stillede spread, ikke fyldet i en hurtig bevægelse.
- **TopstepX' egen feed (C7).** Spread og barer hos venuet er ikke sammenlignet med CME-data.
  En fremtidig måling kan tage `GatewayQuote.bestBid/bestAsk` direkte fra TopstepX.
- **Ingen optager er bygget** — PRD'en udelukker det i denne fase.

---

## 6. Fund om kilden

- **Databento 2010-2015 har huller.** 11-79% af RTH-minutterne mangler pr. år, og 554 sessioner
  har slet ingen RTH-data. Dækningen er ujævn over døgnet: i 2011 findes i snit 14 af 60
  minutter pr. RTH-time, men 37 i timen 18-19 ET. Databentos katalog oplyser at data før
  2017-05-21 er hentet fra FIX-filer uden capture-tidsstempler.
- **To nedbrud midt i ugen i 2014:** 94,0 timer uden data efter 2014-06-11 19:59 ET og 83,4 timer
  efter 2014-09-22 19:56 ET. Hverken weekend eller helligdag.
- **Tynde nætter 2010-2017:** 9-28% flade 1m-barer i døgnserien pr. år (2018: 1,3%; 2019 og frem
  < 0,7%).
- **Fra 2016 er RTH komplet** (0-54 manglende minutter pr. år).
- **`.v.0` halter volumenskiftet** med 1-2 handelsdage (§4).
- **Yahoo NQ=F er identisk med CME-data** bar for bar, men mangler barer på halve helligdage
  (2026-07-03) og dagen efter Labor Day (2026-09-08).

---

## 7. Forbrug af Databento-kredit

Estimeret og bogført før hvert udtræk (`data/cache/databento/udtraek.jsonl`).

| udtræk | schema | periode | rækker | estimat_usd |
|---|---|---|---|---|
| NQ.v.0 | ohlcv-1m | 2010-06-06 → 2026-09-11 | 4.818.677 | 17,60 |
| 8 NQ/MNQ-kontrakter (rulletjek) | ohlcv-1d | 2025-12-01 → 2026-09-11 | 990 | 0,01 |
| MNQ.v.0 (krydstjek) | bbo-1m | 2026-03-13 → 2026-09-11 | 179.155 | 0,24 |
| MNQ.v.0 (stikprøve, 92 dage) | bbo-1s | 2019-05 → 2026-09 | 7.056.604 | 9,46 |
| **i alt** | | | | **27,31 af 40,00** |

---

## Kilder

- databento.com: catalog/cme/GLBX.MDP3/futures/NQ, pricing; Databento Historical API
  (metadata.get_dataset_range, metadata.get_cost, symbology.resolve)
- yfinance 1.7.0 mod NQ=F, målt 2026-09-11
- londonstrategicedge.com (forside, /data, /api-documentation); github.com/londonstrategicedge/lse-data
  (`README.md`, `lse/client.py`, `lse/vault.py`); api.londonstrategicedge.com/vault (401 uden nøgle)
- firstratedata.com/i/futures/NQ og forsiden
- dukascopy-node.app/instrument/usatechidxusd; dukascopy.com Terms of Use
- help.barchart.com: "How can I download historical data"
- gateway.docs.projectx.com: retrieve-bars, realtime
- portaracqg.com/futures/int/enq; kibot.com
- exchange_calendars 4.13 (XNYS) for NYSE-sessioner, halve dage og helligdage
- Roll (1984), Corwin & Schultz (2012), Abdi & Ranaldo (2017) — spread-estimatorer fra prisdata
