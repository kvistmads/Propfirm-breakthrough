# B4 kandidat 3 — præregistrering: vending efter åbningen, volatilitetslys i modsat retning

**Skrevet:** 2026-10-07 af overblikssessionen, før kørslen. Committes før kørslen.
**Kilde:** `research/kilder/bktraders_nasdaq_routine_noter.md` (videoen, set 2026-10-07).
**Besluttet af ejeren 2026-10-07:** svar 1A, 2A, 3A, 4A, 5A, 6A, 7A og 8A. Svar 5 blev
transskriberet som "vi tager os af". Det er læst som **5A**, fordi alle de øvrige svar er A.
Ejeren retter det før commit, hvis det er forkert.
**Om stop og mål:** kontoen styrer positionens størrelse ($250 pr. handel). Markedet styrer,
hvor stop og mål ligger. Videoens stop og mål var sat efter Apex-kontoen og bruges ikke.
**Genbrugt fra kandidat 1 og 2:** data, den rettede motor (`trinA.simuler_handel` med
`maal_r`), sizing, disciplinreglerne og Westfall-Young standardiseret som i
`b4_k2_nowick.md` §7.

---

## 1. Hvad testen afgør

1. **Har modellen en handlebar edge på MNQ?** Når åbningens første halve time har sat en
   retning, går man ind på det første volatilitetslys i modsat retning mellem 10 og 12
   New York-tid. Målet er middel netto-R pr. handel, med konfidensinterval og korrektion
   for 3 varianter.
2. **Er det volatilitetslyset, der bærer?** Den samme vending sammenlignes med en indgang
   på et tilfældigt tidspunkt (N-tid, afgør).
3. **Er vending bedre end fortsættelse?** Samme lys i åbningens retning (N-med, forklarer).

Kandidat 3 har én chance: denne test.

## 2. Mekanismen — skrevet før testen

**Påstanden:** I den første halve time lægger alle deres åbningsordrer. Market makerne
optager presset og forventer, at bevægelsen vender. Mellem 10 og 12 kommer modbevægelsen,
og et volatilitetslys i modsat retning markerer, at den er begyndt.

**Hvad litteraturen siger:**
- Afkastet i første halve time forudsiger afkastet i **sidste** halve time i **samme**
  retning (Gao, Han, Li & Zhou; SPY/QQQ 1999–2012, R² cirka 2%). Det er fortsættelse og
  peger mod modellen. Det siger dog intet om tidsrummet 10–12.
- I 16 markeder er der en vending ved åbningen, især efter negative overnatafkast, og
  fortsættelse ind mod lukningen (Li 2021).
- Der er altså et delvist grundlag for en tidlig vending, men ingen dokumentation for
  netop 10–12 eller for signalet.

**Hvem taber:** dem der køber eller sælger åbningens bevægelse for sent, i retning af den.

**Ny mekanik:** dette er ikke en limitordre ved udspringet af et stærkt lys, som kandidat
1 og 2 var. Man følger et udbrud ind med en markedsordre.

## 3. Serie og faste indstillinger

| emne | valg |
|---|---|
| Serie | MNQ.v.0 1m, 2019-05-06 → 2023-12-31, kun gennem `data.holdout.load_in_sample`. Holdout (2024 →) åbnes ikke |
| Tidsramme (svar 1A) | 1m, både signal og handel |
| Motor | den rettede: i fyldnings-1m-baren kan kun stoppet rammes. Målet tjekkes fra næste bar |
| Indgang | markedsordre. Se §4c |
| Sizing | `kontrakter = floor(250 / (risiko_pt × 2))`, loftet ved 50. Handel kun ved `kontrakter ≥ 1` |
| Omkostning | $2,627 pr. round trip pr. kontrakt. Stoppet fyldes med 0,5417 tick slippage, målet uden (regel 5–6 i `b4_k1_trinA.md` §4a) |
| R | `R_netto = (pnl_pt × 2 − 2,627) / (risiko_pt × 2)`, uafhængig af antallet af kontrakter |
| Fladt | 14:50 CT (normalt 21:50 dansk tid), tidsexit til markedspris |
| Halve dage | vinduet 09:00–11:00 CT gælder også. Fladning efter `trinA.flad_tid_utc` |

## 4. Definitionerne

Alle tider er CT, som koden regner i. 08:30 CT = 09:30 ET = 15:30 dansk tid i normale uger.

### 4a. Åbningens retning (svar 2A)

- `r_aabning = close(08:59-baren) − open(08:30-baren)` på RTH-dagen.
- Er den under 0, er åbningen **ned**, og modellen handler long. Er den over 0, er den
  **op**, og modellen handler short.
- `r_aabning = 0` giver ingen handel. Mangler en af de to barer, handles der heller ikke.
  Begge dele tælles.
- Der er ingen tærskel for bevægelsens størrelse.

### 4b. Volatilitetslyset (svar 3A)

- `TR_i = max(high_i, close_{i−1}) − min(low_i, close_{i−1})`.
- ATR(14) er Wilders ATR med α = 1/14 på hele den kontinuerlige 1m-serie.
- `ATR_{i−1}` er ATR kendt ved lukningen af bar i−1, altså uden signalbaren.

**Signalet** er 1m-bar i, der starter i [09:00, 11:00) CT og opfylder:
1. lyset har modsat farve af åbningen: grønt (`close > open`) efter en åbning ned, rødt
   (`close < open`) efter en åbning op;
2. `TR_i > k × ATR_{i−1}`, hvor k ∈ {1,0; 1,5; 2,0}.

### 4c. Indgang (svar 4A)

- Indgangen sker ved åbningen af den næste tilgængelige 1m-bar efter signalbaren.
- Markedsordren får **0,5417 tick slippage** imod sig, samme tal som stoppets.
- Er der mere end 1 minut til næste bar, springes signalet over, og det tælles.

### 4d. Stop (svar 5A)

- Stoppet ligger **2 × ATR_i** fra indgangen. `ATR_i` er ATR kendt ved signalbarens
  lukning, altså inklusive signalbaren.
- Stopprisen rundes til helt tick, væk fra indgangen.
- `risiko_pt = |indgang − stop|`.
- Faktoren 2 er et skøn ud fra videoens 25 point. Den er ikke kalibreret, fordi det ville
  kræve data fra holdout-perioden.

### 4e. Mål (svar 6A)

- Målet ligger **1,5R** fra indgangen og fyldes som limit uden slippage.
- Der er ingen break-even-flytning.

### 4f. Disciplin (svar 7A)

- **Én handel om dagen.** Det er det første signal i vinduet, der kan sizes
  (`kontrakter ≥ 1`).
- Handlen lukker ved mål, stop eller tidsexit kl. 14:50 CT. Derefter er dagen slut.
- Rammerne fra kandidat 1 og 2 gælder i øvrigt. Signalvinduet ligger inden for
  `fl.vindue_mask`'s 08:30–14:30 CT.

## 5. Varianterne og tælleren

Der er 3 varianter: k = 1,0, 1,5 og 2,0. Ingen af dem er hovedvariant.

| tæller | forsøg |
|---|---|
| Kandidat 1 og 2 | 28 |
| Kandidat 3 | 3 |
| **I alt** | **31** |

## 6. Nulmodellerne (svar 8A)

**N-tid — afgør. Betyder volatilitetslyset noget?**
- For hver variant v og hver dag, hvor modellen har en handel, trækkes et tilfældigt
  signalminut fra variantens egen fordeling af signalminutter. Fordelingen samles over
  alle dage, så nulmodellen får samme tidsprofil.
- Indgang ved næste bar i **samme retning som modellen**, altså mod åbningen. Stop, mål,
  disciplin og omkostning er de samme.
- **R = 500 gentagelser.**

**N-med — forklarer. Vending eller fortsættelse?**
- Samme regler, men det første volatilitetslys i **åbningens retning**, og handlen går i
  åbningens retning. Det er én deterministisk kørsel pr. variant.
- Sammenlignes med modellen ved et Welch-interval på forskellen i middel netto-R.

**N0, aritmetik:** ved 1,5R er break-even-vinderraten 40% brutto og `(1 + omk_R) / 2,5`
netto.

## 7. Statistik og MDE

**Mål:** middel netto-R pr. handel med t-interval. Der er én handel om dagen.

**Test:** Westfall-Young maks-statistik mod N-tid, standardiseret præcis som i
`b4_k2_nowick.md` §7:
- `t_v = (m_v − med_v) / sd_v`, hvor `med_v` og `sd_v` (ddof = 1) regnes over N-tid's
  gentagelser;
- `p_FWE,v = (1 + #{r: max_v^(r) ≥ t_v}) / 501`.

**MDE**, én-sidet α = 0,05 og 80% styrke. σ_R = 1,225 er antaget: det er 1,5R uden edge
(+1,5 med 40%, −1 med 60%). Šidák 3 er den forsigtige grænse.

| handler_n | MDE_R_ukorr | MDE_R_sidak3 |
|---|---|---|
| 400 | 0,152 | 0,181 |
| 600 | 0,124 | 0,148 |
| 800 | 0,108 | 0,128 |
| 1.000 | 0,096 | 0,115 |

Formlen er `(z_α + z_0,20) × σ / √n`. Ukorrigeret er `z_α + z_0,20` = 2,4865, med
Šidák 3 er den 2,9628.

**Økonomisk krav:** +0,20 R pr. handel, som for kandidat 1 og 2.

Omregnet til vinderrate ved 1,5R og `omk_R` = 0,10 (antaget):

| størrelse | værdi |
|---|---|
| Break-even netto | 44% |
| +0,20 R kræver | 52% |
| MDE ved 800 handler (ukorrigeret) | 48% |

**Betingelse før kørslen:** hver variant skal have `handler_n ≥ 330`. Så er MDE med
Šidák 3 ≤ 0,20 R. Ligger en variant under, rapporterer Code det og stopper, og ejeren
beslutter.

## 8. Beslutningsreglen — dækker alle udfald

Rækkerne prøves i rækkefølge, og den første der passer, gælder. Krydser et interval en
grænse, er betingelsen ikke opfyldt. +0,20 R gælder punktestimatet.

| nr | udfald | handling |
|---|---|---|
| 1 | Mindst én variant har p_FWE ≤ 0,05 **og** middel netto-R ≥ +0,20 R **og** CI-nedre > 0 | **Varianten fryses.** Opfylder flere kravet, fryses den med højeste CI-nedre. Næste skridt: ruinmodellen med disciplinreglerne, køb af MNQ-holdout og præregistrering af holdout-testen |
| 2 | Mindst én variant har p_FWE ≤ 0,05 **og** CI-nedre > 0, men ingen når +0,20 R | **Parkeres som "reel, men under det økonomiske krav"** |
| 3 | Ingen variant har p_FWE ≤ 0,05, men mindst én har CI-nedre > 0 | **Kandidat 3 parkeres:** volatilitetslyset tilføjer intet ud over tidspunktet. At vending mellem 10 og 12 ser profitabel ud, er et in-sample-fund. Det bliver en mulig ny kandidat med egen præregistrering og fuldt N |
| 4 | Alt andet | **Kandidat 3 parkeres** |

**N-med ændrer ikke rækken.** Har N-med for en variant CI-nedre > 0 og ligger over
modellen med et Welch-interval på forskellen, der ikke rører 0, skrives det som et
in-sample-fund om fortsættelse. Det kan blive en ny kandidat med egen præregistrering og
fuldt N.

## 9. Diagnoser — rapporteres, men afgør intet

| diagnose | hvorfor |
|---|---|
| Tvetydige minutter, hvor stop og mål kan nås i samme 1m-bar, og bedste fald som i `b4_k1_trin2.md` §8 | 1m-stop er små. Afgørelsen tages på det forsigtige tal. Ville bedste fald give en anden række, skrives resultatet som *afhængigt af data under minutniveau* |
| Long mod short (åbning ned mod op), med CI på forskellen | asymmetri |
| Efter fortegnet på overnatafkastet (16:00 CT dagen før → 08:30 CT) | Li (2021). Beskrivende, må ikke bruges til nye varianter uden ny præregistrering |
| Pr. år | koncentration |
| Signalminut: p10/p50/p90 pr. variant | hvornår i vinduet |
| Dage med åbningsretning, dage med signal, dage uden signal | dækning |
| `risiko_pt_p10/p50/p90` og `omk_R_netto_p50/p90` pr. år | 1m-stop er små i 2019–20 |
| `kontrakter_p50/maks`, `kontrakter_loftet_n` | loftet på 50 binder ved risiko under 2,5 point |

## 10. Rapporten

Filerne er `research/output/b4_k3_vending.md` og `.csv`. Kompakt hovedtabel i chatten,
brutto og netto side om side, og enheden i kolonnenavnet.

Pr. variant:

| kolonne | formel |
|---|---|
| handler_n · dage_med_handel_n | antal fyldte handler / dage med en handel |
| middel_R_brutto · middel_R_netto · CI95 | sum(R) / handler_n, t-interval |
| win_rate_pct_brutto · _netto + Wilson-CI | andel med R > 0, brutto og netto |
| udfald_maal_pct · udfald_stop_pct · udfald_tidsexit_pct | summerer til 100 |
| N_tid_middel_R_netto_p5/p50/p95 · t_v · p_FWE | afgørende nulmodel |
| N_med_handler_n · N_med_middel_R_netto · forskel med Welch-CI95 | forklarende nulmodel |
| tvetydig_n · censureret_n | |

## 11. Før kørslen: Code's trin 1, og så stop

1. **Modul og tests:** `research/b4_k3_vending.py` og `tests/test_b4_k3_vending.py`. Motoren
   bruges via `trinA.simuler_handel(..., be_r=None, maal_r=1.5)`. Kandidat 1's og 2's
   moduler røres ikke.
2. **Syntetiske tests, alle skal bestå:**
   1. Åbningens retning fra 08:30-open og 08:59-close, inklusive retning 0 og manglende
      barer.
   2. Signalet bruger `ATR_{i−1}`, og stoppet bruger `ATR_i`.
   3. Kun signalbarer, der starter i [09:00, 11:00) CT.
   4. Lysets farve skal være modsat åbningen.
   5. Indgang ved næste bars åbning plus slippage, og et hul over 1 minut springes over.
   6. I indgangsbaren kan kun stoppet rammes.
   7. Målet er 1,5R.
   8. Kun den første handel om dagen.
   9. N-tid trækker fra variantens egen minutfordeling.
   10. N-med bruger lys i åbningens retning.
3. **Regressionstjek:**
   - Kandidat 1's tre tjek holder.
   - `simuler_handel` gengiver 1.226 handler og −0,0115 R.
   - Kandidat 2's hovedvariant gengiver 611 handler og −0,1430 R (commit f053ece).
4. **Optælling uden udfald:** pr. variant dage med åbningsretning, dage med signal,
   `handler_n`, signalminuttets p10/p50/p90, `risiko_pt_p10/p50/p90` og
   `omk_R_netto_p50/p90`. Det samme for N-med. **Ingen R, ingen vinderrate, intet
   udfald.** Derefter tjekkes betingelsen i §7.
5. **Tidsmåling:** ét gennemløb og 5 N-tid-gentagelser. Forventet tid for R = 500.
6. **Stop.** Den rigtige kørsel sker først, når ejeren har godkendt optællingen.

## 12. Forventning, skrevet før kørslen — ikke et kriterium

- **Mest sandsynligt parkeres kandidat 3.** Mit skøn for, hvilken række i §8 der gælder:
  række 1 ca. 5%, række 2 ca. 5%, række 3 ca. 10%, række 4 ca. 80%.
- **Ved k = 1,0 har næsten hver dag et signal i de første minutter efter kl. 9:00 CT.**
  Signalet er da næsten betingelsesløst, og modellen ligger tæt på N-tid.
- **N-med klarer sig mindst lige så godt som modellen.** Det skyldes litteraturens
  fortsættelse fra åbningen.
- **Omkostningen er tungest i 2019–20,** hvor 1m-ATR er lille.
- **Vinderraten ved 1,5R ligger omkring 40% brutto.**

## 13. Efter kørslen

Stop. Tabellerne i chatten. Ingen ændring af definitioner, ingen nye varianter og ingen
forslag. Resultatet læses sammen med ejeren, og §8 anvendes mekanisk.

## Kilder

- Gao, Han, Li & Zhou, *Market Intraday Momentum*, JFE — omtalt hos
  https://www.cxoadvisory.com/?p=25481
- Li (2021), *Essays on Intraday Stock Return Predictability*, University of Southampton —
  https://eprints.soton.ac.uk/452387
- Videoen: https://www.youtube.com/watch?v=LDmV1KpUiWo
