# B4 kandidat 4 — præregistrering: EMT, tilbage til VWAP efter et udmattelseslys

**Skrevet:** 2026-10-08 af overblikssessionen, før kørslen. Committes før kørslen.
**Kilde:** `research/kilder/emt_reel_noter.md` (reelen, set 2026-10-08).
**Besluttet af ejeren 2026-10-08:** svar 1A, 2A, 3A, 4A, 5A, 6A, 7A og 8A. Svar 9: A, med
B som variant. Svar 11A.
**Svar 10** er overblikssessionens anbefaling **B**, som ejeren hældede til, men bad om
en vurdering af: spring setuppet over, hvis VWAP ligger under 1R væk. Det er en fast
regel, ikke en variant. Begrundelsen står i §4g. Ejeren retter det før commit, hvis han
er uenig.
**Zarattini og Aziz' trendfølgende VWAP-strategi** er ejerens ønske og bliver kandidat 5
med egen præregistrering, når artiklens præcise regler er læst. Den er ikke en del af
denne test. Den modsatte retning af EMT-setuppet (N-mod, §6) er kun en forklaring.
**Genbrugt:** data, fyldnings- og omkostningsreglerne, sizing, disciplinreglerne,
forskelsjusteringen ved rul (`b4_k2_nowick.py`) og Westfall-Young standardiseret som i
`b4_k2_nowick.md` §7.

---

## 1. Hvad testen afgør

1. **Har EMT en handlebar edge på MNQ 5m?** Modellen går imod et stræk væk fra VWAP efter
   et udmattelseslys, med VWAP som mål. Målet er middel netto-R pr. handel, med
   konfidensinterval og korrektion for 6 varianter.
2. **Er det udmattelseslyset, der bærer?** Sammenlignes med et tilfældigt strakt lys samme
   dag (N-tid, afgør).
3. **Er tilbageløb bedre end fortsættelse?** Sammenlignes med samme setup handlet med
   strækket (N-mod, forklarer).

## 2. Mekanismen — skrevet før testen

**Påstanden:** Når prisen er strakt langt væk fra VWAP og går i stå med et lys med en
kraftig væge, er presset brugt op. Prisen søger tilbage mod dagens gennemsnitspris.

**Hvad litteraturen siger:**
- Den dokumenterede VWAP-strategi går **den modsatte vej**. Zarattini og Aziz (2023,
  QQQ 2018–2023) går long over VWAP og short under, med en Sharpe på 2,1 efter
  kommission. Det peger imod modellen.
- På Nasdaq-100-futures finder Yu, Rentzler og Wolf (2005) både fortsættelse og vending
  inden for dagen, afhængigt af gårsdagens og nattens afkast. Der er ingen simpel regel.
- Kandidat 3 fandt vending og fortsættelse lige gode, begge omkring 0 brutto.

**Hvem taber:** dem der køber toppen af et stræk og først sælger, når prisen er tilbage
ved gennemsnittet.

**Ny mekanik for os:** målet er VWAP, så forholdet mellem gevinst og risiko varierer fra
handel til handel. Stoppet sidder tæt bag vægen. Indgangen er en stop-ordre på bruddet.

## 3. Serie og faste indstillinger

| emne | valg |
|---|---|
| Serie | MNQ.v.0 1m, 2019-05-06 → 2023-12-31, kun gennem `data.holdout.load_in_sample`. Holdout åbnes ikke |
| Tidsramme (svar 3A) | 5m bygget af 1m med `data.resample.aggregate`. Rækkefølgen inde i et 5m-lys afgøres på 1m |
| Indikatorer | regnes på den **forskelsjusterede** 1m-serie (`b4_k2_nowick.forskelsjuster`). Rullerne ligger kl. 18–19 CT, uden for handelstiden, så forskydningen er konstant inden for en RTH-dag. Mål og priser oversættes til handelspris med dagens forskydning |
| Sizing | `kontrakter = floor(250 / (risiko_pt × 2))`, loftet ved 50. Handel kun ved `kontrakter ≥ 1` |
| Omkostning | $2,627 pr. round trip pr. kontrakt. Stop-ordrer (indgang og stop) fyldes med 0,5417 tick slippage imod, målet uden |
| R | `R_netto = (pnl_pt × 2 − 2,627) / (risiko_pt × 2)` |
| Vindue | udmattelseslyset og fyldet skal ligge i `fl.vindue_mask(…, 5)`: 08:30–14:30 CT. Fladt kl. 14:50 CT |
| Motorens regler | i fyldnings-1m-baren kan kun stoppet rammes. Rammer stop og mål samme 1m-bar, tæller stoppet først |

## 4. Definitionerne

### 4a. Indikatorerne (svar 1A og 2A)

| indikator | definition |
|---|---|
| VWAP | `Σ(hlc3 × volume) / Σ(volume)` over 1m-barer fra sessionens start kl. **17:00 CT**. Det er TradingViews standardanker "Session" for CME-futures. Værdien ved et 5m-lys' lukning medtager alle 1m-barer til og med lysets sidste minut |
| EMA9 | eksponentielt gennemsnit af 5m-close med α = 2/10, løbende over alle 5m-lys, også om natten |
| ATR(14) | Wilders ATR på 5m-lys, α = 1/14 |

### 4b. "Strakt" (svar 4A)

5m-lys i er **strakt op**, hvis begge dele gælder:
1. `close_i − VWAP_i ≥ k × ATR_i`;
2. `VWAP_i < EMA9_i < close_i`.

**Strakt ned** er spejlvendt. k ∈ {1,5; 2,0; 3,0}.

### 4c. Udmattelseslyset (svar 5A)

Udmattelseslyset er et strakt lys med en kraftig væge i strækkets retning:
- **Strakt op:** `high − max(open, close) ≥ 0,5 × (high − low)`;
- **strakt ned:** `min(open, close) − low ≥ 0,5 × (high − low)`;
- `high − low > 0`.

### 4d. Indgang (svar 6A)

- **Short efter et stræk op:** sell-stop på `low_i − 1 tick`.
- **Long efter et stræk ned:** buy-stop på `high_i + 1 tick`.
- Ordren er kun aktiv i **det næste 5m-lys** (i+1). Udløses den ikke, er setuppet væk.
- Fyldet sker på triggerprisen med 0,5417 tick slippage imod. Åbner et 1m-lys allerede
  forbi triggeren, fyldes der på det lys' åbning med slippage.
- Opstår et nyt udmattelseslys, mens en ordre venter, erstatter det den gamle.

### 4e. Stop (svar 7A)

- Short: `high_i + 2 ticks`. Long: `low_i − 2 ticks`.
- `risiko_pt = |fyld − stop|`.

### 4f. Mål (svar 8A)

- Målet er **VWAP, opdateret minut for minut**. I 1m-bar j er målet VWAP ved lukningen af
  bar j−1, oversat til handelspris.
- Det fyldes som limit uden slippage, når baren handler til målet.
- **Kodeændring:** målet bevæger sig, så det kan ikke køres gennem `trinA.simuler_handel`.
  Code skriver en ny funktion med samme regler: kun stop i fyldningsbaren, regel 4,
  slippage og fladning. Med et konstant mål skal den give præcis samme resultat som
  `simuler_handel` (test).

### 4g. Mindste afstand til VWAP (svar 10B — anbefalet, fast regel)

Er afstanden fra fyldet til VWAP ved fyldtidspunktet under **1 × risiko_pt**, tages
handlen ikke. Det tælles.

Begrundelse:
- Med omkostning på cirka 0,05–0,10 R kræver et mål under 1R en vinderrate over 55–70%.
- Ejerens egen tanke var: jo længere væk fra VWAP, jo mere skal prisen tilbage. Reglen
  sikrer, at der er mindst lige så langt til målet som til stoppet.
- Reglen er geometrisk og fastlagt før testen, ikke fundet i data.
- Den er ikke en variant, så den koster ikke ekstra i tælleren.
- Prisen er færre handler og en afvigelse fra videoen, som ikke nævner den.

### 4h. Antal handler (svar 9A, 9B som variant)

- **Variant 1/dag:** første fyldte handel. Når den lukker, er dagen slut.
- **Variant 2/dag:** op til to handler. Den anden kan først fyldes, når den første er
  lukket.

## 5. Varianterne og tælleren

| dimension | værdier |
|---|---|
| k | 1,5, 2,0, 3,0 |
| handler pr. dag | 1, 2 |

Der er **6 varianter**.

| tæller | forsøg |
|---|---|
| Kandidat 1–3 | 31 |
| Kandidat 4 | 6 |
| **I alt** | **37** |

## 6. Nulmodellerne (svar 11A)

**N-tid — afgør. Betyder udmattelseslyset noget?**
- **Kandidater i nulmodellen:** strakte lys med samme k og retning i vinduet, hvor næste
  lys bryder lysets bund (short) eller top (long) med 1 tick, og som består 1R-reglen.
  Vægekravet i §4c er fjernet.
- For hver dag med en model-handel trækkes lige så mange kandidater, som modellen havde
  handler den dag, tilfældigt og uden tilbagelægning. Har dagen for få, bruges alle, og
  det tælles.
- Indgang, stop, mål og disciplin er de samme. **R = 500.**
- Både modellen og nulmodellen er betinget af bruddet. Den eneste forskel er vægen.

**N-mod — forklarer. Tilbageløb eller fortsættelse?**
- Samme udmattelsessetups handlet med strækket: buy-stop på `high_i + 1 tick` (efter et
  stræk op) og stop på `low_i − 2 ticks`.
- Målet ligger lige så langt fra indgangen som VWAP, bare den anden vej.
- Det er én deterministisk kørsel pr. variant. Den sammenlignes med modellen ved et
  Welch-interval på forskellen.

## 7. Statistik og MDE

**Mål:** middel netto-R pr. handel med t-interval. Ved 2 handler om dagen regnes
intervallet klyngerobust pr. dag (CR1, som i kandidat 1).

**Test:** Westfall-Young maks-statistik mod N-tid, standardiseret præcis som i
`b4_k2_nowick.md` §7.

**MDE**, én-sidet α = 0,05 og 80% styrke, Šidák 6 (`z_α + z_0,20` = 3,2278):
- Uden edge er `σ_R ≈ √(middel RR)`, fordi målet varierer.
- σ_R regnes pr. variant ud fra **RR-fordelingen i optællingen**. RR kendes ved
  indgangen og er ikke et udfald.
- Ved RR omkring 2 (σ cirka 1,41) kræves cirka 518 handler, ved RR omkring 1,5
  (σ cirka 1,22) cirka 388.

| handler_n | MDE_R_sidak6 ved σ 1,22 | ved σ 1,41 | ved σ 1,73 |
|---|---|---|---|
| 300 | 0,227 | 0,263 | 0,322 |
| 500 | 0,176 | 0,204 | 0,250 |
| 800 | 0,139 | 0,161 | 0,197 |

**Betingelse før kørslen:** hver variants MDE med Šidák 6 skal være ≤ 0,20 R. Ligger en
variant over, rapporterer Code det og stopper, og ejeren beslutter. k = 3,0 er den mest
udsatte.

**Økonomisk krav:** +0,20 R pr. handel.

## 8. Beslutningsreglen — dækker alle udfald

Rækkerne prøves i rækkefølge, og den første der passer, gælder. Krydser et interval en
grænse, er betingelsen ikke opfyldt. +0,20 R gælder punktestimatet.

| nr | udfald | handling |
|---|---|---|
| 1 | Mindst én variant har p_FWE ≤ 0,05 **og** middel netto-R ≥ +0,20 R **og** CI-nedre > 0 | **Varianten fryses.** Opfylder flere kravet, fryses den med højeste CI-nedre. Næste skridt: ruinmodellen, køb af holdout og præregistrering af holdout-testen |
| 2 | Mindst én variant har p_FWE ≤ 0,05 **og** CI-nedre > 0, men ingen når +0,20 R | **Parkeres som "reel, men under det økonomiske krav"** |
| 3 | Ingen variant har p_FWE ≤ 0,05, men mindst én har CI-nedre > 0 | **Parkeres:** udmattelseslyset tilføjer intet ud over et tilfældigt strakt lys. At et tilbageløb fra strækket ser profitabelt ud, er et in-sample-fund. Det bliver en mulig ny kandidat med egen præregistrering og fuldt N |
| 4 | Alt andet | **Kandidat 4 parkeres** |

**N-mod ændrer ikke rækken.** Har N-mod CI-nedre > 0 og ligger over modellen med et
Welch-interval, der ikke rører 0, skrives det som et in-sample-fund om fortsættelse.
Det vedrører kandidat 5.

## 9. Diagnoser — rapporteres, men afgør intet

| diagnose | hvorfor |
|---|---|
| RR-fordeling ved indgang (p10/p50/p90) og `sprunget_over_under_1R_n` | 1R-reglens pris |
| Setups uden brud i næste lys (udløbet) | indgangsreglens pris |
| Tvetydige minutter og bedste fald som i `b4_k1_trin2.md` §8 | afgørelsen tages på det forsigtige tal |
| Long mod short med CI på forskellen | asymmetri |
| Pr. år og signal-tidspunkt p10/p50/p90 | koncentration og tid på dagen |
| Andel af handler i 2/dag-varianten, der er dagens anden handel | hvad variant B tilføjer |
| `risiko_pt` og `omk_R_netto` p10/p50/p90 pr. år, `kontrakter_loftet_n` | stop tæt bag vægen kan være små og dyre |

## 10. Rapporten

Filerne er `research/output/b4_k4_emt.md` og `.csv`. Kolonnerne er de samme som i
`b4_k3_vending.md` §10, med N-mod i stedet for N-med. Desuden kommer `RR_p50`.

## 11. Før kørslen: Code's trin 1, og så stop

1. **Modul og tests:** `research/b4_k4_emt.py` og `tests/test_b4_k4_emt.py`. Kandidat 1–3's
   moduler importeres, men ændres ikke.
2. **Syntetiske tests, alle skal bestå:**
   1. VWAP nulstilles kl. 17:00 CT og regnes med hlc3 × volume.
   2. VWAP på den forskelsjusterede serie, og målet oversættes korrekt til handelspris.
   3. EMA9 og ATR(14) bruger kun lukkede lys.
   4. Stræk op og ned, med EMA-betingelsen.
   5. Vægekravet ved præcis 50%.
   6. Stop-ordren gælder kun i lys i+1, og et gap fyldes på åbningen.
   7. Stop 2 ticks bag vægen.
   8. VWAP-målet bruger forrige minuts VWAP, og i fyldningsbaren rammes kun stoppet.
   9. 1R-reglen.
   10. 1 og 2 handler om dagen.
   11. N-tid kræver brud og trækker pr. dag.
   12. N-mod spejlet.
   13. Den nye motorfunktion giver samme resultat som `simuler_handel` med et konstant
       mål.
3. **Regressionstjek:**
   - Kandidat 1's tre tjek holder.
   - `simuler_handel` gengiver 1.226 handler og −0,0115 R.
   - Kandidat 2's hovedvariant gengiver 611 handler og −0,1430 R.
   - Kandidat 3's k = 1,0 gengiver 1.168 handler og −0,0712 R.
4. **Optælling uden udfald:** pr. variant strakte lys, udmattelseslys, udløste ordrer,
   `sprunget_over_under_1R_n`, `handler_n`, RR p10/p50/p90 og dermed σ_R og MDE. Desuden
   `risiko_pt`, `omk_R` og signaltid. Det samme for N-mod og N-tid's kandidatpulje.
   **Ingen R, ingen vinderrate, intet udfald.**
5. **Tidsmåling:** ét gennemløb og 5 N-tid-gentagelser.
6. **Stop.** Den rigtige kørsel sker først, når ejeren har godkendt optællingen.

## 12. Forventning, skrevet før kørslen — ikke et kriterium

- **Mest sandsynligt parkeres kandidat 4.** Mit skøn for, hvilken række i §8 der gælder:
  række 1 ca. 5%, række 2 ca. 5%, række 3 ca. 10%, række 4 ca. 80%.
- **Vinderraten ligger under 50%,** fordi RR typisk er over 1. Break-even ved RR 2 er
  cirka 35% brutto.
- **N-mod ligger tæt på modellen.** Kandidat 3 fandt ingen forskel på vending og
  fortsættelse.
- **Stop tæt bag vægen er små,** og omkostningen i R bliver derfor højere end i kandidat 3.
- **k = 3,0 har få handler** og klarer måske ikke MDE-betingelsen.

## 13. Efter kørslen

Stop. Tabellerne i chatten. Ingen ændring af definitioner, ingen nye varianter og ingen
forslag. Resultatet læses sammen med ejeren, og §8 anvendes mekanisk.

## Kilder

- Zarattini & Aziz (2023), *Volume Weighted Average Price (VWAP) The Holy Grail for Day
  Trading Systems*, SSRN 4631351 — https://ssrn.com/abstract=4631351
- Yu, Rentzler & Wolf (2005), *NASDAQ-100 Index Futures: Intraday Momentum or Reversal?*,
  JOIM — https://www.joim.com/nasdaq-100-index-futures-intraday-momentum-reversal
- Reelen: https://www.instagram.com/reels/DeM8kyVCdKz/
