# B4 kandidat 5 — præregistrering: VWAP-trend efter Zarattini og Aziz (2023)

**Skrevet:** 2026-10-08 af overblikssessionen, før kørslen. Committes før kørslen.
**Kilde:** `research/kilder/zarattini_aziz_vwap_noter.md` (hele artiklen læst 2026-10-08,
SSRN 4631351). Udkastet med analysen: `research/prereg/b4_k5_vwap_trend_udkast.md`.
**Besluttet af ejeren 2026-10-08:** svar 1A, 2A, 3A, 4A og 5A.

**Svar 1A — fladt-tidspunktet:** ejeren spurgte, om 21:55 er bedre end 21:59 dansk tid.
Overblikssessionen anbefaler **14:55 CT (21:55 dansk tid)**, begrundet i §4d. Det er en
fast regel, ikke en variant. Ejeren retter det før commit, hvis han vil have 14:59 CT.

**To præciseringer fra overblikssessionen** følger anbefalingen, som ejeren gik med. De
står her, fordi de kan afgøre udfaldet. Ejeren retter dem før commit, hvis han er uenig.
- **§4g:** målet i 5A er netto-dollar pr. dag pr. MNQ-kontrakt **ved dagens niveau**
  (NQ 29.138), ikke ved det historiske niveau. Omkostningen er fast i dollar, men
  kursbevægelserne vokser med niveauet. I 2019 (NQ cirka 7.500) vejede $2,627 fire gange
  tungere end i dag. Det nominelle tal rapporteres som diagnose.
- **§4f:** ingen ekstra slippage i prisen ud over de $2,627. Alle ordrer er markedsordrer
  på et lys' åbning, og $2,627 indeholder allerede en hel spread og slippage på begge
  sider. Tallet med kandidat 1–4's ekstra slippage ($3,169) rapporteres som diagnose.

**Genbrugt:** data, omkostningen, kalenderen for RTH (`data.sessions.rth_mask`) og
Westfall-Young standardiseret som i `b4_k2_nowick.md` §7.

---

## 1. Hvad testen afgør

1. **Bærer VWAP-retningen information på MNQ?** Modellen sammenlignes med de samme
   handler med tilfældig retning (N-retning). Korrektion for 4 varianter.
2. **Betaler den omkostningen?** Middel netto-dollar pr. dag pr. MNQ ved dagens niveau,
   med konfidensinterval over dagene.
3. **Hvor meget er der at give af?** Hvor høj omkostningen pr. handel højst må være, før
   strategien går i nul (break-even-omkostningen).

## 2. Mekanismen — skrevet før testen

**Påstanden:** På dage med en trend ligger prisen mest på den ene side af VWAP og bliver
der. Institutionelle, der handler mod VWAP som benchmark, forstærker det:
- Venter de en trend, handler de tidligt og skubber prisen væk fra VWAP.
- Venter de på en bedre pris, der ikke kommer, må de handle i sidste time i trendens
  retning.

Den, der går imod dagens trend, betaler. Strategien taber mange små handler, når prisen
krydser frem og tilbage, og tjener på de få dage, hvor trenden holder.

**Hvad litteraturen siger:**
- **Zarattini og Aziz (2023), QQQ 2018–2023:** Sharpe 2,1 efter kommission. Gevinsten kom
  kl. 9:30–12 og 15–16 New York-tid.
- **Gao, Han, Li og Zhou (2018, JFE):** dagens første halve time forudsiger den sidste
  halve time på S&P 500-ETF'en. Det er dokumenteret momentum inden for dagen.
- **Baltussen, Da, Lammers og Martens (2021, JFE):** momentum sidst på dagen findes i
  aktieindeks-futures på tværs af markeder, også Nasdaq, og forklares delvist med
  optionshandleres afdækning.
- **Vores egne kandidater:** fortsættelse slog tilbageløb i kandidat 1, 2 og 4. Men det
  lå selv omkring 0 netto.

**Det taler imod:**
- Omkostningen er omtrent lige så stor som artiklens gevinst pr. handel (udkastet §2).
- Artiklens periode overlapper vores in-sample. Vi gentager en kendt test på et næsten
  identisk instrument. Det er ikke en uafhængig bekræftelse. Den rene test er holdout
  (2024 →), som ligger efter artiklen.

## 3. Serie og faste indstillinger

| emne | valg |
|---|---|
| Serie | MNQ.v.0 1m, 2019-05-06 → 2023-12-31, kun gennem `data.holdout.load_in_sample`. Holdout åbnes ikke |
| Tidsrammer (svar 3A) | 1m og 5m. 5m bygges af 1m med `data.resample.aggregate`. VWAP regnes altid på 1m |
| RTH | `data.sessions.rth_mask` (XNYS). Kortdage lukker kl. 12:00 CT |
| Ruller | ligger kl. 18–19 CT, uden for RTH. Alt i en handelsdag ligger i samme kontrakt, så der bruges ingen forskelsjustering. Koden tjekker det (§11) |
| Størrelse | **1 MNQ, fast.** Strategien har intet stop og kan ikke måles i R. Hvor mange kontrakter den tåler, afgør ruinmodellen bagefter |
| Omkostning | $2,627 pr. round trip pr. kontrakt. Ingen ekstra slippage i prisen (§4f) |
| Tider | afviger fra den faste ramme (08:30–14:30 CT, fladt 14:50) efter svar 1A: handel hele RTH-dagen og fladt 14:55 CT (§4d) |
| Dansk tid | dansk tid er CT + 7 timer, undtagen i de uger om foråret og efteråret, hvor USA og Europa skifter sommertid på forskellige datoer. Så er det CT + 6. Al kode og en senere bot regner i CT |

## 4. Definitionerne

### 4a. VWAP

- `VWAP_t = Σ(hlc3 × volume) / Σ(volume)` over RTH-1m-barerne fra kl. **08:30 CT** til og
  med bar t. hlc3 = (high + low + close) / 3.
- Kun RTH. Barer før 08:30 CT indgår ikke. VWAP nulstilles hver dag.
- Det er artiklens definition. Den er ikke den samme som kandidat 4's anker kl. 17:00 CT.
- For et 5m-lys bruges VWAP ved lysets sidste minut, regnet på 1m.

### 4b. Signal og position (svar 2A)

- Ved lukningen af hvert lys (1m eller 5m) i RTH:
  - `close > VWAP` → ønsket position **long**;
  - `close < VWAP` → ønsket position **short**;
  - `close = VWAP` → ingen ændring.
- **Dagens første handel:** ved lukningen af dagens første lys (1m: lyset kl. 08:30 CT;
  5m: lyset 08:30–08:35 CT). Er close lig VWAP, ventes til første lys, der lukker over
  eller under.
- **Vending:** afviger den ønskede position fra den nuværende, vendes positionen. Et kryds
  inde i lyset uden en lukning på den anden side udløser intet.
- Der er altid en position fra første handel til fladt-tidspunktet (undtagen pausen i
  §4e).

### 4c. Udførelse

- Handlen sker ved **åbningen af næste lys**. For 5m er det åbningen af det næste 5m-lys'
  første 1m-bar.
- Mangler næste 1m-bar, bruges åbningen af den næste bar, der findes. Det tælles.
- En vending er én handel lukket og én åbnet til samme pris.
- **En handel** går fra en indgang til næste udgang (vending, pause eller fladt).
  `brutto_pt = (udgang − indgang) × retning`, hvor retning er +1 for long og −1 for short.

### 4d. Dagens slut (svar 1A)

- **Fladt kl. 14:55 CT** (21:55 dansk tid de fleste uger): positionen lukkes ved åbningen
  af baren, der starter kl. 14:55 CT.
- Et signal, der skulle udføres kl. 14:55 CT eller senere, bliver ikke til en ny position.
- **Kortdage:** fladt 5 minutter før NYSE lukker, altså kl. 11:55 CT.

**Hvorfor 14:55 og ikke 14:59 CT:**
- **Kø er ikke problemet.** En markedsordre på få micros fyldes med det samme. MNQ er
  mest likvid omkring kontantlukningen. Kø gælder limitordrer, og vi bruger ingen.
- **Teknikken er problemet.** Fejler botten, API'et eller forbindelsen i sidste minut,
  skal der være tid til at prøve igen, før Topstep selv flader kl. 15:08 CT (22:08 dansk
  tid). 14:55 giver 13 minutter, 14:59 giver 9.
- **Prisen er lille.** Vi mister 5 af de sidste 60 minutter. Hvad de 5 minutter ville have
  givet, rapporteres som diagnose (§9), så det kan vurderes bagefter.

### 4e. Pausen midt på dagen (variant, svar 3A)

- **Uden-middag-varianten** lukker positionen ved åbningen af baren kl. **11:00 CT** og
  har ingen position mellem 11:00 og 14:00 CT. Det er 12–15 New York-tid og 18–21 dansk
  tid de fleste uger.
- Kl. **14:00 CT** åbnes en ny position ud fra det sidst lukkede lys: 1m-lyset kl. 13:59
  eller 5m-lyset 13:55–14:00. VWAP er regnet hele dagen, også under pausen.
- Derefter vendes som normalt til fladt kl. 14:55 CT.
- På kortdage lukkes kl. 11:00 CT, og der åbnes ikke igen.

### 4f. Omkostning og slippage

- **$2,627 pr. round trip pr. kontrakt** (`backtest.costs.rundtur_dekomponering`, RTH):
  kommission $1,22, en hel spread $0,865 og slippage 0,5417 tick pr. side ($0,542).
- **Ingen ekstra slippage i prisen.** Hver handel fyldes på et lys' åbning med en
  markedsordre. Spreaden og slippagen er allerede i de $2,627.
- **Afvigelsen fra kandidat 1–4:**
  - Der fik stop-ordrer 0,5417 tick ekstra, fordi en stop-ordre udløses i en pris, der
    bevæger sig, og fyldes dårligere end triggeren.
  - Kandidat 3's markedsordre fik det samme. Det var et forsigtigt valg, mens omkostningen
    var 0,05–0,07 R og ikke afgørende.
  - Her er omkostningen hele spørgsmålet. Dobbelt slippage ville afgøre testen på en
    antagelse.
- **Diagnose:** resultatet ved $3,169 (= $2,627 + 0,5417 tick pr. side) og
  break-even-omkostningen (§9).

### 4g. Målet: netto-dollar pr. dag pr. MNQ ved dagens niveau (svar 5A)

- `L_d` = åbningen af dagens første RTH-1m-bar i den ujusterede MNQ.v.0-serie.
- For hver handel i på dag d:
  `netto_usd_i = brutto_pt_i × (29.138 / L_d) × 2 − 2,627`.
- `dag_netto_usd_d = Σ_i netto_usd_i`.
- **Målet** er middelværdien af `dag_netto_usd_d` over dagene.
- **29.138** er NQ's sidste RTH-luk 2026-09-10. Det er samme referenceniveau som
  ruinmodellen v2, så tallene kan bruges direkte i den.

**Hvorfor ved dagens niveau:**
- Omkostningen er fast i dollar og ticks, men kursbevægelsen i point vokser med niveauet.
- $2,627 er 1,75 basispunkter af positionen ved NQ 7.500, 0,82 bp ved 16.000 og 0,45 bp
  ved 29.138.
- En nominel test ville vægte 2019's dyre handler som om, de var dagens. Det er ikke det,
  botten møder.
- **Antagelsen** er, at bevægelsen i procent og omkostningen i ticks er de samme ved dagens
  niveau som i 2019–2023. Holdout (2024 →, NQ 16.000–29.000) tester det.

### 4h. Huller i data

- En dag udelukkes, hvis første RTH-bar ligger efter 08:35 CT, eller hvis der er et hul
  på mere end 5 minutter mellem to RTH-1m-barer. Det tælles.
- Samme dage udelukkes i alle varianter og i nulmodellen.

## 5. Varianterne og tælleren

| dimension | værdier |
|---|---|
| Tidsramme | 1m, 5m |
| Middag | hele dagen, uden 11:00–14:00 CT |

Der er **4 varianter**. "1m · hele dagen" er artiklens strategi.

| tæller | forsøg |
|---|---|
| Kandidat 1–4 | 37 |
| Kandidat 5 | 4 |
| **I alt** | **41** |

## 6. Nulmodellen (svar 4A)

**N-retning — afgør. Bærer VWAP-retningen noget?**
- Samme handler som modellen: samme dage, samme ind- og udgangstider, samme antal og samme
  omkostning.
- Hver handels retning trækkes tilfældigt, long eller short med 50% hver.
- Retningen trækkes deterministisk pr. (gentagelse, tidsramme, dag, indgangsminut). En
  handel med samme indgangsminut i hele-dagen- og uden-middag-varianten får derfor samme
  tilfældige retning. Så bevares afhængigheden mellem varianterne i maks-statistikken.
- **R = 500.**
- Nulmodellens brutto er 0 i forventning. Forskellen mellem model og nulmodel er altså
  VWAP-retningens bruttogevinst.

**Altid-long — forklarer, ændrer intet.**
- Køb ved åbningen kl. 08:31 CT, sælg ved åbningen kl. 14:55 CT. Én handel om dagen, samme
  omkostning og normering.
- Viser, hvor meget af modellens resultat der kunne komme fra en stigende Nasdaq.

## 7. Statistik og MDE

**Mål:** middel `dag_netto_usd` med t-interval over dagene (95%, tosidet).

**Test:** Westfall-Young maks-statistik mod N-retning, standardiseret præcis som i
`b4_k2_nowick.md` §7:
- `t_v = (m_v − med_v) / sd_v`, hvor m_v er modellens middel `dag_netto_usd`, og med_v og
  sd_v er median og spredning af nulmodellens middel over de 500 gentagelser.
- `p_FWE = (1 + #{gentagelser med max_v' t*_v' ≥ t_v}) / 501`. Énsidet: modellen over
  nulmodellen.

**MDE**, 80% styrke, regnet i optællingen uden udfald:
- σ_dag skønnes fra RTH-markedets egen svingning, ikke fra modellens handler:
  `σ_dag = 2 × √(middel_d[(29.138 / L_d)² × Σ_t Δclose_t²])`. Summen går over variantens
  lys (1m eller 5m) i variantens handelstid.
- Det er spredningen på en dag med tilfældig retning, altså nulmodellens.
- `MDE_sidak4 = 3,0756 × σ_dag / √n_dage` (énsidet α = 0,05 med Šidák 4, z = 2,2340).
- `MDE_CI = 2,8016 × σ_dag / √n_dage`. Det er den nettogevinst, der giver CI-nedre > 0 med
  80% styrke.

| n_dage | σ_dag $600 | $750 | $900 |
|---|---|---|---|
| MDE_sidak4 ved 1.165 | $54 | $68 | $81 |
| MDE_CI ved 1.165 | $49 | $62 | $74 |

**Artiklens effekt ved dagens niveau:** 671% over cirka 1.446 handelsdage er
ln(7,71) / 1.446 = 14,1 bp pr. dag af positionen. Ved NQ 29.138 er 1 MNQ $58.276, så det
er cirka **$82 pr. dag pr. kontrakt** før vores omkostning.

**Betingelse før kørslen:** hver variants `MDE_sidak4` skal være ≤ $82. Testen skal kunne
se artiklens effekt. Ligger en variant over, rapporterer Code det og stopper, og ejeren
beslutter.

**Styrken for netto:** optællingen rapporterer også styrken for CI-nedre > 0, hvis
bruttogevinsten er $82, og omkostningen er variantens egen (handler pr. dag × $2,627).

## 8. Beslutningsreglen — dækker alle udfald

Rækkerne prøves i rækkefølge, og den første, der passer, gælder. Krydser et interval en
grænse, er betingelsen ikke opfyldt.

| nr | udfald | handling |
|---|---|---|
| 1 | Mindst én variant har p_FWE ≤ 0,05 **og** CI-nedre > 0 | **Varianten fryses.** Opfylder flere kravet, fryses den med højeste CI-nedre. Næste skridt: en ruinmodel for daglig P&L (egen præregistrering, for den nuværende er bygget på R og RR 2:1), køb af holdout og præregistrering af holdout-testen |
| 2 | Mindst én variant har p_FWE ≤ 0,05, men ingen har CI-nedre > 0 | **Parkeres som "VWAP-retningen bærer, men betaler ikke omkostningen".** Break-even-omkostningen skrives op. Billigere udførelse kan blive en ny kandidat med egen præregistrering |
| 3 | Ingen variant har p_FWE ≤ 0,05, men mindst én har CI-nedre > 0 | **Parkeres.** Gevinsten kommer ikke fra VWAP-retningen. Det er et in-sample-fund og kan blive en ny kandidat med egen præregistrering |
| 4 | Alt andet | **Kandidat 5 parkeres** |

- Række 3 er næsten umulig, fordi nulmodellens brutto er 0. Den står der, så alle udfald
  er dækket.
- **Afgørelsen tages på $2,627 ved dagens niveau.** Diagnoserne i §9 ændrer ikke rækken.

## 9. Diagnoser — rapporteres, men afgør intet

| diagnose | hvorfor |
|---|---|
| **Break-even-omkostning pr. handel:** den omkostning, hvor middel netto er 0, og den, hvor CI-nedre er 0 | den vigtigste enkeltoplysning: hvor stor er margenen over $2,627 |
| Netto ved $3,169 og den række i §8, det ville give | kandidat 1–4's slippage-konvention |
| **Nominelt:** netto-dollar pr. dag ved det historiske niveau, med CI | hvad der faktisk var tjent dengang |
| Brutto i bp pr. handel og pr. dag | sammenlignes med artiklens cirka 0,93 bp pr. handel og 14,1 bp pr. dag |
| Handler pr. dag (p10/p50/p90) og holdetid | artiklen havde cirka 15 handler om dagen |
| Hit ratio og gevinst/tab-forhold, brutto og netto | artiklen havde 17% og 5,67 |
| Brutto fordelt på halve timer New York-tid (mark-to-market minut for minut) | sammenlignes med artiklens figur 7: gevinst kl. 9:30–12 og 15–16 |
| De sidste 5 minutter: hvad positionen fra 14:55 til 15:00 CT ville have givet brutto | prisen for svar 1A's buffer |
| Dagsfordelingen ved dagens niveau: p1, p5, p50, p95, p99, værste og bedste dag | til ruinmodellen |
| Største tab inden for dagen (mark-to-market på 1m-close), p1, p5 og værste | Topsteps MLL brydes i realtid |
| Bedste dags andel af samlet gevinst og andelen fra de 5% bedste dage | Topsteps konsistensregel på 55% |
| Long mod short, brutto pr. handel, med Welch-CI på forskellen | asymmetri og drift |
| Altid-long (§6) med CI | hvor meget kommer fra drift |
| Pr. år: netto ved dagens niveau og nominelt, handler pr. dag og medianen af L_d | koncentration og niveau |
| Årlig Sharpe af den daglige netto | sammenlignes med artiklens 2,1 |
| Udelukkede dage, manglende minutter og ruller inden for RTH | datakvalitet |

## 10. Rapporten

Filerne er `research/output/b4_k5_vwap_trend.md` og `.csv`.

**Hovedtabellen** har én række pr. variant med kolonnerne:
- `variant`, `dage_n`, `handler_n`, `handler_pr_dag_p50`;
- `middel_brutto_usd_dag`, `middel_netto_usd_dag`, `CI95_netto`;
- `N_retning_p5/p50/p95`, `t_v`, `p_FWE`;
- `breakeven_omk_middel`, `breakeven_omk_CI`;
- `hit_ratio_pct_brutto`, `gevinst_tab_forhold`;
- `netto_usd_dag_nominelt`, `netto_usd_dag_ved_3169`;
- `MDE_sidak4`, `MDE_CI`.

Derefter: afgørelsen efter §8 mekanisk, og diagnoserne fra §9 i hver sin tabel.

## 11. Før kørslen: Code's trin 1, og så stop

1. **Modul og tests:** `research/b4_k5_vwap_trend.py` og `tests/test_b4_k5_vwap_trend.py`.
   Kandidat 1–4's moduler må importeres, men ændres ikke. Westfall-Young genbruges fra
   `b4_k2_nowick.westfall_young`.
2. **Syntetiske tests, alle skal bestå:**
   1. VWAP starter kl. 08:30 CT, bruger kun RTH-barer og hlc3 × volume, og nulstilles hver
      dag.
   2. 5m bruger VWAP ved lysets sidste minut, regnet på 1m.
   3. Første handel besluttes ved første lys' lukning og udføres ved næste lys' åbning.
      Close lig VWAP giver ingen position.
   4. Vending kun ved en lukning på den anden side. Et kryds inde i lyset vender ikke.
   5. Udførelse ved næste lys' åbning. Mangler et minut, bruges næste bar, og det tælles.
   6. Fladt ved åbningen kl. 14:55 CT. Et signal ved lukningen kl. 14:54 giver ingen ny
      position.
   7. Uden middag: fladt kl. 11:00 CT, ingen position til 14:00, ny position kl. 14:00 ud
      fra det sidst lukkede lys og hele dagens VWAP.
   8. Kortdage: fladt kl. 11:55 CT. Uden middag lukker kl. 11:00 og åbner ikke igen.
   9. Normering og omkostning efter §4g, med L_d fra den ujusterede serie.
   10. N-retning: samme handler og antal. Samme indgangsminut giver samme retning i begge
       middagsvarianter. Middel over mange gentagelser er cirka −omkostningen.
   11. Westfall-Young og p_FWE som i kandidat 2.
   12. En rulle inden for RTH får koden til at stoppe med en fejl.
   13. Dage med huller efter §4h udelukkes i alle varianter og i nulmodellen.
3. **Regressionstjek:**
   - Kandidat 1's tre tjek holder.
   - `simuler_handel` gengiver 1.226 handler og −0,0115 R.
   - Kandidat 2's hovedvariant gengiver 611 handler og −0,1430 R.
   - Kandidat 3's k = 1,0 gengiver 1.168 handler og −0,0712 R.
   - Kandidat 4's k = 1,5 · 1/dag gengiver 1.104 handler og −0,0920 R.
4. **Optælling uden udfald, pr. variant:**
   - dage med og uden udelukkelse, manglende minutter og ruller inden for RTH;
   - `handler_n`, handler pr. dag (p10/p50/p90), holdetid (p10/p50/p90);
   - omkostning pr. dag i dollar;
   - medianen af L_d pr. år og omkostningen i bp pr. år;
   - σ_dag, `MDE_sidak4`, `MDE_CI` og betingelsen i §7;
   - styrken for netto ved $82 brutto.
   - **Ingen P&L, ingen hit ratio, ingen andel long eller short, intet udfald.**
5. **Tidsmåling:** ét gennemløb og 5 gentagelser af N-retning.
6. **Stop.** Den rigtige kørsel sker først, når ejeren har godkendt optællingen.

## 12. Forventning, skrevet før kørslen — ikke et kriterium

- **Brutto gentager sig sandsynligvis.** QQQ og MNQ følger samme indeks i samme periode, og
  RTH er den samme. Slår modellen nulmodellen, er det derfor en gentagelse af en kendt
  test, ikke ny viden.
- **Netto afgøres af omkostningen.** Ved dagens niveau giver artiklens tal cirka $82 brutto
  mod cirka $39 i omkostning pr. dag på 1m (15 handler × $2,627). Nominelt, ved 2019–2023's
  niveau, vil 1m sandsynligvis være omkring 0 eller negativ.
- **5m og pausen midt på dagen** sparer omkostning. De kan klare sig bedre netto end 1m,
  hvis bruttogevinsten ikke falder tilsvarende.
- **Mit skøn for rækken i §8:** række 1 ca. 25%, række 2 ca. 35%, række 3 under 5%,
  række 4 ca. 35%.
- **Hit ratio** på 1m: 15–25%, med et gevinst/tab-forhold på 3–6.
- **Store tab inden for dagen:** strategien kan tabe flere hundrede dollar pr. kontrakt på
  en dag med mange krydsninger. Det gør sizingen på Topstep til et problem for sig.

## 13. Efter kørslen

Stop. Tabellerne i chatten. Ingen ændring af definitioner, ingen nye varianter og ingen
forslag. Resultatet læses sammen med ejeren, og §8 anvendes mekanisk.

## Kilder

- Zarattini & Aziz (2023), *Volume Weighted Average Price (VWAP) The Holy Grail for Day
  Trading Systems*, SSRN 4631351 — https://ssrn.com/abstract=4631351
- Gao, Han, Li & Zhou (2018), *Market intraday momentum*, Journal of Financial Economics
  129(2), 394–414.
- Baltussen, Da, Lammers & Martens (2021), *Hedging demand and market intraday momentum*,
  Journal of Financial Economics 142(1), 377–403.
