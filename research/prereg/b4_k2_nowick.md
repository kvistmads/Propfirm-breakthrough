# B4 kandidat 2 — præregistrering: Nowick, lys uden væge i trendens retning

**Skrevet:** 2026-10-07 af overblikssessionen, før kørslen. Committes før kørslen.
**Kilde:** `research/kilder/bardfx_nowick_reel_noter.md` (reelen, set 2026-10-07).
**Besluttet af ejeren 2026-10-07:** MNQ 5m. Trenden aflæses på en højere tidsramme. De ni
spørgsmål blev besvaret 1A, 2A, 3A, 4A, 5A, 6B, 7A, 8A og 9A. Hvert svar står ved sin
definition i §4.
**Genbrugt fra kandidat 1:** data, den rettede motor, fyldningsreglerne, sizing,
disciplinreglerne og swing-koden (`research/prereg/b4_k1_trinA.md` §4,
`research/prereg/b4_k1_motorrettelse.md`, `research/b4_k1_filtre.py`).

---

## 1. Hvad testen afgør

1. **Har modellen en handlebar edge på MNQ 5m?** Middel netto-R pr. handel, med
   konfidensinterval og korrektion for 12 varianter.
2. **Er det lysene uden væge, der bærer?** Den samme model køres på almindelige lys med
   væge (§6). Kun hvis lys uden væge klarer sig bedre end dem, er det denne kandidats edge.

Kandidat 2 har én chance: denne test. Viser resultatet noget andet, fx at trend plus retest
virker uanset væge, er det en **ny kandidat** med egen præregistrering og eget N. Det er
ikke et redningsforsøg på denne.

## 2. Mekanismen — skrevet før testen

**Påstanden:** Et lys der åbner og kun bevæger sig én vej, viser ensidigt pres fra
åbningen. Åbningen er et niveau, som prisen ikke har handlet på den anden side af. Når
prisen inden for få lys kommer tilbage dertil, mens den højere tidsramme trender samme vej,
fortsætter bevægelsen.

**Hvad litteraturen siger:**
- Markeder trender på tidsskalaer fra nogle timer til nogle år og vender tilbage på kortere
  skalaer (Safari & Schmidhuber 2025).
- Afkast fortsætter over 1–12 måneder i 58 futures, herunder aktieindeks-futures
  (Moskowitz, Ooi & Pedersen 2012).

Det giver en indirekte begrundelse for en tilbagerekyl på minutskala imod en trend på
daily eller 4H. **Selve niveauet, åbningen af et lys uden væge, har ingen dokumentation.**
Lysmønstre på 5-minutters data overlever sjældent omkostninger (Duvinage, Mazza &
Petitjean, arbejdspapir 2012).

**Hvem taber:** dem der handler imod impulsen ved retesten, og dem hvis stop ligger lige
bag lysets åbning.

## 3. Serie og faste indstillinger

| emne | valg |
|---|---|
| Serie | MNQ.v.0 1m, 2019-05-06 → 2023-12-31, kun gennem `data.holdout.load_in_sample`. Holdout (2024 →) åbnes ikke |
| Handelstidsramme | 5m, bygget af 1m med `data.resample.aggregate` |
| Trendens tidsramme | daily og 4H, bygget af den samme 1m-serie (§4b) |
| Motor | den rettede: rækkefølgen i et 5m-lys afgøres på 1m, og i fyldnings-1m-baren kan kun stoppet rammes |
| Fyldning | regel 1-6 og 8 fra `b4_k1_trinA.md` §4a, uændret. Regel 7 (zonen dør ved berøringen) erstattes af §4c |
| Sizing | `kontrakter = floor(250 / (risiko_pt × 2))`, loftet ved 50. Handel kun ved `kontrakter ≥ 1`, altså `risiko_pt ≤ 125` |
| Omkostning | $2,627 pr. round trip pr. kontrakt. Stoppet fyldes med 0,5417 tick slippage, målet uden |
| R | `R_netto = (pnl_pt × 2 − 2,627) / (risiko_pt × 2)` pr. kontrakt. Uafhængig af antallet af kontrakter |
| Vindue | `fl.vindue_mask(…, 5)`: 08:30 ≤ t < 14:30 CT på RTH-dage og senest 30 min før RTH-luk. Det svarer normalt til 15:30–21:30 dansk tid |
| Fladt | 14:50 CT (normalt 21:50 dansk tid), tidsexit til markedspris |

## 4. Definitionerne

### 4a. Signallyset (svar 1A)

Priser sammenlignes i hele ticks: `round(pris / 0,25)`.

| side | betingelse |
|---|---|
| Short | 5m-lyset er rødt (`close < open`) **og** `high = open`, altså nul ticks topvæge |
| Long | 5m-lyset er grønt (`close > open`) **og** `low = open`, altså nul ticks bundvæge |

Doji (`close = open`) er aldrig et signal. Om lyset har væge i den anden ende, betyder
intet. Signallyset skal ligge i vinduet (§3) og pege i trendens retning (§4b).
**Linjen** er lysets åbning.

### 4b. Trenden (svar 2A og 3A)

**Tidsrammer:** daily er hovedtidsrammen, 4H er en variant.

**Lysene:**
- **Daily** er en CME Globex-handelsdag fra 17:00 CT dagen før til 16:00 CT. Søndag
  aftens handel hører til mandag.
- **4H** starter ved sessionens start kl. 17:00 CT: 17–21, 21–01, 01–05, 05–09, 09–13 og
  13–16 CT. Det sidste lys er afkortet ved 16:00 CT.
- `aggregate` kan kun lave tidsrammer, der går op i en time. Code bygger derfor en ny
  funktion til disse to og rører ikke `aggregate`.

**Swing-punkter:** `fl.swing_punkter` med N = 5, som i kandidat 1. Et swing-punkt er
kendt fra og med lys `i + 5`.

**Tilstanden** (svar 3A) beregnes pr. HTF-lys ved lysets lukning:
- **Op**, når lyset lukker over den seneste kendte swing-top.
- **Ned**, når lyset lukker under den seneste kendte swing-bund.
- **Uændret** ellers.
- Tilstanden er **udefineret**, indtil det første brud er sket. Der handles ikke på
  udefinerede dage, og de tælles.

**Ingen kig frem:** et 5m-signal bruger tilstanden fra det seneste HTF-lys, der er lukket
senest ved 5m-lysets lukning. På daily er det i praksis i går. På 4H kan tilstanden skifte
inden for vinduet, ved 09:00 og 13:00 CT.

**Kontraktskift:** MNQ.v.0 er ikke tilbagejusteret, så en rul giver et prisspring.
- HTF-trenden regnes på en **forskelsjusteret** HTF-serie. Ved hver rul flyttes al
  forudgående historik med springet: første open i den nye kontrakt minus sidste close i
  den gamle.
- Handelspriserne på 5m og 1m justeres ikke.
- Ligger en rul inden for signallysets 10-lys-vindue (§4d), i ordrens levetid eller i
  handlen, springes signalet over og tælles.
- Code rapporterer antallet af ruller, og hvor i døgnet de ligger.

### 4c. Ordren (svar 4A, retest-vinduet 3, 5 og 9 lys)

- En limitordre lægges på linjen ved signallysets lukning. Den er aktiv fra det første
  5m-lys efter signallyset til og med det N'te lys efter det, hvor N ∈ {3, 5, 9}.
- **Fyld** kræver, at prisen handler mindst ét tick igennem linjen (regel 1), set på
  1m-serien. Der fyldes til linjen (regel 2).
- **Et strejf**, hvor prisen rører linjen uden at handle igennem, fylder ikke, men
  **ordren lever videre** til udløb. Strejf tælles (§9).
- **Ordren annulleres**, når:
  1. N lys er gået;
  2. et nyt gyldigt signal kommer (svar 4A: det nyeste signal erstatter den ventende
     ordre);
  3. HTF-trenden skifter væk fra ordrens retning (kun muligt på 4H);
  4. klokken bliver 14:30 CT (regel 8).
- Der kan højst være én ventende ordre ad gangen.

### 4d. Stop (svar 5A)

| side | stop |
|---|---|
| Short | højeste high i de 10 seneste 5m-lys til og med signallyset, **plus 2 ticks** |
| Long | laveste low i de 10 seneste 5m-lys til og med signallyset, **minus 2 ticks** |

- Er signallyset selv det højeste (short) eller laveste (long) af de 10, også ved
  lighed, er der ingen plads til et stop. Signalet springes over og tælles.
- De 10 lys må ligge før vinduets start.
- `risiko_pt = |stop − linje|`. Stoppet ligger fast fra signallysets lukning.

### 4e. Mål (svar 6B)

- Målet ligger **1R** fra linjen. Det er hovedvarianten.
- **2R** er en variant.
- Der er ingen break-even-flytning.

### 4f. Disciplin og rammer (svar 7A og 8A)

- **Én handel om dagen:** den første ordre, der fyldes. Når handlen lukker ved mål, stop
  eller tidsexit, er dagen slut. Dagen er ET-handelsdagen (`k1._et_dag`).
- Reglen om to BE-udgange findes ikke her, fordi der ikke er nogen break-even.
- Vindue, fladning, sizing og omkostning følger §3.

## 5. Varianterne og tælleren

| dimension | værdier |
|---|---|
| HTF | daily, 4H |
| N lys | 3, 5, 9 |
| Mål | 1R, 2R |

**12 varianter.** Hovedvarianten er **daily, 5 lys, 1R**. Den har ingen særstatus i
afgørelsen, men står øverst i rapporten.

| tæller | forsøg |
|---|---|
| Kandidat 1 i alt | 16 |
| Kandidat 2 | 12 |
| **I alt** | **28** |

## 6. Nulmodellen N-alm: almindelige lys med væge (svar 9A)

**Spørgsmålet:** klarer almindelige lys sig lige så godt under præcis de samme regler?

- **Kandidaterne i nulmodellen:** 5m-lys i vinduet, i trendens retning og i den rigtige
  farve. Short-kandidater er røde med `high > open`, long-kandidater grønne med
  `low < open`. Linjen er åbningen. Stoppet regnes som i §4d, og lyset skal have
  `kontrakter ≥ 1`.
- **Matching:** for hver HTF-tidsramme og hver ET-dag tælles de gyldige signaler uden
  væge, k_d. Det er dem, der har plads til stop og `kontrakter ≥ 1`. Derefter trækkes
  k_d lys tilfældigt uden tilbagelægning blandt dagens nulkandidater med samme
  HTF-tilstand. Har dagen færre kandidater end k_d, bruges alle, og det tælles.
- **Alt andet er identisk:** N-vindue, nyeste-erstatter, stop, mål, disciplin, sizing og
  omkostning. N og mål deler signalsæt. Daily og 4H trækkes hver for sig.
- **R = 500 gentagelser.**

Fordi nulmodellen har samme trendfilter, rammer daily-trendens overvægt af long-handler i
2019–21 og 2023 begge sider ens.

**N0, aritmetik, kun som reference:**
- 1R: break-even-vinderrate 50% brutto, `(1 + omk_R) / 2` netto.
- 2R: break-even-vinderrate 33,3% brutto, `(1 + omk_R) / 3` netto.

## 7. Statistik og MDE

**Mål:** middel netto-R pr. handel. Med én handel om dagen ligger handlerne på hver sin
dag, så t-intervallet bruges uden klyngekorrektion.

**Test: Westfall-Young maks-statistik, standardiseret.** Det følger læringen fra kandidat 1:
rå middelværdier på tværs af varianter med forskelligt nulniveau lader varianten med det
højeste nulniveau dominere.

1. For hver variant v beregnes nulmodellens median `med_v` og standardafvigelse `sd_v`
   over de 500 gentagelser.
2. Den observerede statistik er `t_v = (m_v − med_v) / sd_v`.
3. For hver gentagelse r gemmes `max_v (m_v^(r) − med_v) / sd_v`.
4. Den justerede p-værdi pr. variant er
   `p_FWE,v = (1 + #{r: max^(r) ≥ t_v}) / (1 + 500)`.

**MDE**, én-sidet α = 0,05 og 80% styrke:
- σ_R = 1,0 ved 1R og 1,414 ved 2R. Begge er antaget: det er spredningen uden edge.
- "Šidák 12" er en konservativ øvre grænse, der behandler de 12 varianter som
  uafhængige. Westfall-Young ligger mellem de to kolonner.

| handler_n | MDE_R_1R_ukorr | MDE_R_1R_sidak12 | MDE_R_2R_ukorr | MDE_R_2R_sidak12 |
|---|---|---|---|---|
| 400 | 0,124 | 0,174 | 0,176 | 0,245 |
| 600 | 0,102 | 0,142 | 0,144 | 0,200 |
| 800 | 0,088 | 0,123 | 0,124 | 0,174 |
| 1.000 | 0,079 | 0,110 | 0,111 | 0,155 |

Formlen er `(z_α + z_0,20) × σ / √n`. Ukorrigeret er `z_α + z_0,20` = 2,4865, med
Šidák 12 er den 3,4719.

**Økonomisk krav:** +0,20 R pr. handel. Det svarer til 12 R ($3.000 / $250) på cirka 60
handler, som i `b4_k1_trinA.md` §6.

Omregnet til vinderrate ved 1:1 og `omk_R` = 0,10 (antaget fra kandidat 1 spor B, median
0,09–0,12):

| størrelse | værdi |
|---|---|
| Break-even netto | 55% |
| +0,20 R kræver | 65% |
| MDE ved 800 handler (ukorrigeret) | 59% |
| Påstanden 85% svarer til | +0,60 R |

**Betingelse før kørslen:** hver variants `handler_n` skal give MDE (Šidák 12) ≤ 0,20 R.
Det betyder `handler_n ≥ 301` ved 1R og `≥ 603` ved 2R. Ligger en variant under, rapporterer
Code det og stopper, og ejeren beslutter. Intet ændres stiltiende.

## 8. Beslutningsreglen — dækker alle udfald

Rækkerne prøves i rækkefølge, og den første der passer, gælder. "CI" er 95%-t-intervallet
for middel netto-R.

| nr | udfald | handling |
|---|---|---|
| 1 | Mindst én variant har p_FWE ≤ 0,05 **og** middel netto-R ≥ +0,20 R **og** CI-nedre > 0 | **Varianten fryses.** Opfylder flere kravet, fryses den med højeste CI-nedre. Næste skridt: ruinmodellen genkøres med disciplinreglerne, MNQ-holdout købes, og holdout-testen præregistreres |
| 2 | Mindst én variant har p_FWE ≤ 0,05 **og** CI-nedre > 0, men ingen når +0,20 R | **Parkeres som "reel, men under det økonomiske krav".** Tallene skrives ned. En ruinmodel-måling på varianten kan præregistreres som ny måling |
| 3 | Ingen variant har p_FWE ≤ 0,05, men mindst én har CI-nedre > 0 | **Kandidat 2 parkeres:** lys uden væge tilføjer intet målbart. At trend plus retest ser profitabel ud, er et in-sample-fund. Det bliver en mulig ny kandidat med egen præregistrering og fuldt N, og holdout er dens eneste rene test |
| 4 | Alt andet | **Kandidat 2 parkeres** |

Krydser et konfidensinterval en grænse, er betingelsen ikke opfyldt.

## 9. Diagnoser — rapporteres, men afgør intet

**Fyldningsreglen er vigtigere her end i kandidat 1.** Linjen er signallysets egen top
(short) eller bund (long). Reelens "perfekte retest", hvor prisen rører linjen præcis og
vender, er derfor et strejf i vores motor, og vi fylder ikke. Derfor:

- `strejf_n` og `strejf_hvis_fyldt_middel_R_netto` rapporteres pr. variant (§4c i trin A).
- Hele afgørelsen regnes også med **fyld ved berøring**, og nulmodellen behandles på
  samme måde.
- **Afgørelsen tages på gennemhandlingsreglen.** Ville den blive en anden ved berøring,
  skrives resultatet som *afhængigt af køplacering*. Næste skridt er da en særskilt,
  præregistreret måling. Det er ikke en variant.

**Tvetydige minutter** følger regel 4: rammer stop og mål samme 1m-bar, tæller stoppet
først. Antallet rapporteres, og bedste fald regnes som i `b4_k1_trin2.md` §8. Afgørelsen
tages på det forsigtige tal.

| diagnose | hvorfor |
|---|---|
| Long og short hver for sig, med CI på forskellen | trendens overvægt af long |
| Pr. år | koncentration |
| Fyldningsrate pr. N, for model og nulmodel | hvor mange signaler kommer tilbage |
| Andel af dage med op-, ned- og udefineret trend pr. HTF | filterets dækning |
| `sprunget_over_ingen_stopplads_n`, `sprunget_over_rul_n`, `afvist_kontrakter_nul_n` | udfaldne signaler |
| `risiko_pt_p10/p50/p90`, `omk_R_netto_p50/p90`, `be_WR_pct_netto_p50`, `kontrakter_p50/maks`, `kontrakter_loftet_n` | omkostning og størrelse |
| N-alm: dage med for få kandidater | matchingens dækning |

## 10. Rapporten

Filerne er `research/output/b4_k2_nowick.md` og `.csv`. Kompakt hovedtabel i chatten,
brutto og netto side om side, og enheden i kolonnenavnet.

Pr. variant:

| kolonne | formel |
|---|---|
| handler_n · dage_med_handel_n | antal fyldte handler / dage med en handel |
| middel_R_brutto · middel_R_netto · CI95 | sum(R) / handler_n, t-interval |
| win_rate_pct_brutto · _netto + Wilson-CI | mål ramt / handler_n |
| udfald_maal_pct · udfald_stop_pct · udfald_tidsexit_pct | summerer til 100 |
| N_alm_middel_R_netto_p5/p50/p95 · t_v · p_FWE | nulmodellen og testen |
| censureret_n | handler åbne ved in-sample-slut |

Afgørelsen efter §8 anvendes mekanisk og står med den række, der gælder.

## 11. Før kørslen: Code's trin 1, og så stop

1. **Modul og tests:** `research/b4_k2_nowick.py` og `tests/test_b4_k2_nowick.py`.
   - Motoren genbruges via `trinA.simuler_handel`, ikke via `handler_for_variant`
     (berøringsbarens længde er hårdkodet til 15m).
   - `simuler_handel` får målet som parameter. Standardværdien bevarer kandidat 1's 2R.
2. **Syntetiske tests, alle skal bestå:**
   1. Signallys i hele ticks, inklusive lighed og doji.
   2. HTF-tilstanden bruger kun lukkede HTF-lys. Et brud inde i dagens daily-lys må ikke
      påvirke samme dags signaler.
   3. Fyld i lys N, men ikke i lys N+1.
   4. Et strejf fylder ikke, og ordren lever videre.
   5. Nyeste signal erstatter den ventende ordre.
   6. Signallyset som 10-lys-ekstrem springes over.
   7. 1R- og 2R-mål.
   8. Rul inden for 10-lys-vinduet springes over.
   9. 4H-lysenes grænser ved 17:00 CT og afkortningen ved 16:00 CT.
3. **Regressionstjek:** kandidat 1's tre tjek i `b4_k1_trin2.md` §10 holder stadig. Den
   udvidede `simuler_handel` gengiver motorrettelsens tal med 2R: handler_n 1.226 og
   middel_R_netto −0,0115.
4. **Optælling uden udfald:** pr. variant signaler, fyldte handler (`handler_n`), dage med
   handel og de udfaldne signaler i §9. Det samme for N-alm i én gentagelse. **Ingen R,
   ingen vinderrate, intet udfald.** Derefter tjekkes betingelsen i §7.
5. **Tidsmåling:** ét gennemløb og 5 N-alm-gentagelser. Forventet tid for R = 500.
6. **Stop.** Den rigtige kørsel sker først, når ejeren har godkendt optællingen og
   tidsmålingen. R sænkes ikke.

## 12. Forventning, skrevet før kørslen — ikke et kriterium

- **Mest sandsynligt parkeres kandidat 2.** Mit skøn for, hvilken række i §8 der gælder:
  række 1 ca. 5%, række 2 ca. 5%, række 3 ca. 15%, række 4 ca. 75%.
- **Vinderraten i 1R-varianterne ligger omkring 50% brutto, ikke 85%.** Reelens eksempler
  er udvalgt i Replay.
- **Forskellen mellem lys uden og med væge er lille,** under 0,05 R. Kandidat 1's
  retests holdt omkring 50% uanset kriterier.
- **Strejf er hyppige.** "Fyld ved berøring" ser derfor bedre ud end gennemhandling, og
  den forskel er det vigtigste diagnosetal.
- **Daily-varianterne har overvejende long-handler.**

## 13. Efter kørslen

Stop. Tabellerne i chatten. Ingen ændring af definitioner, ingen nye varianter og ingen
forslag. Resultatet læses sammen med ejeren, og §8 anvendes mekanisk.

## Kilder

- Moskowitz, Ooi & Pedersen (2012), *Time Series Momentum*, JFE —
  https://papers.ssrn.com/abstract=2089463
- Safari & Schmidhuber (2025), *Trends and Reversion in Financial Markets on Time Scales
  from Minutes to Decades* — https://arxiv.org/pdf/2501.16772
- Duvinage, Mazza & Petitjean (arbejdspapir 2012), intradag-lysmønstre på Dow 30, 5 min — omtalt hos
  https://cxoadvisory.com/technical-trading/testing-japanese-candlesticks-intraday-on-liquid-stocks
