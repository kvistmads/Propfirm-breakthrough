# B4 kandidat 5 — UDKAST: holdout-testen af "1m · uden middag"

**Status: udkast, ikke en præregistrering.** Skrevet 2026-10-08 af overblikssessionen
efter ejerens svar 1A og 2A på næste skridt. Spørgsmålene i §8 skal besvares, og
præregistreringen skal skrives og committes, før data hentes, og før noget køres.
**Grundlag:** `research/output/b4_k5_vwap_trend_laest.md` (kandidat 5 frosset, række 1).

---

## 1. Hvad testen afgør

Holdout er data, ingen af kandidaterne er valgt på. Perioden ligger efter artiklen
(november 2023). Testen svarer på to spørgsmål **hver for sig**, fordi de har meget
forskellig styrke:

| spørgsmål | hvad det betyder | styrke ved in-sample-effekten |
|---|---|---|
| **H1 — retningen** | Bærer VWAP-retningen stadig information efter offentliggørelsen? | cirka 97% |
| **H2 — netto** | Tjener den penge efter omkostning, ved dagens niveau? | cirka 49–61% |

H1 kan testen næsten sikkert afgøre. H2 kan den kun lige se, selv hvis edgen er ægte.
Derfor skal det besluttes på forhånd, hvad der sker, hvis H1 holder, men H2 ikke kan
bevises (§5, række 2).

## 2. Hvad der testes — intet må ændres

- **Strategien:** præcis den frosne variant "1m · uden middag", som i
  `research/prereg/b4_k5_vwap_trend.md` §4 med tillæg:
  - VWAP fra 08:30 CT;
  - vending ved hver 1m-lukning på den anden side;
  - pause 11:00–14:00 CT;
  - fladt 14:55 CT;
  - $2,627 pr. round trip;
  - normering til NQ 29.138.
- **Koden:** `research/b4_k5_vwap_trend.py` som i commit 9d4bd2e, uændret. Kun dataserien
  skifter.
- **Nulmodellen:** N-retning som i in-sample, med R = 500.
- **Udelukkelser:** §4h gælder uændret.

## 3. Data

| emne | valg |
|---|---|
| Serie | MNQ.v.0 ohlcv-1m, Databento GLBX.MDP3 — samme instrument som in-sample |
| Periode | 2024-01-01 → 2026-09-30 (forslag, se spørgsmål 2). Cirka 689 handelsdage |
| Status i dag | **MNQ-holdout findes ikke lokalt** (cachen slutter 2023-12-31). NQ.v.0 for 2024–2026 findes, købt til ruinmodellen og kun brugt til ATR. Den bruges ikke her: in-sample er MNQ, og VWAP vægtes med volumen, som er forskellig på NQ og MNQ |
| Køb | prisen estimeres først (gratis). Hentes kun, hvis estimatet er højst $15 — ejeren har godkendt cirka $10. Budgetvagten i `data.src_databento` gælder |
| Tjek efter hentning | kun dækning: antal barer pr. dag, manglende minutter og ruller inden for RTH. Ingen priser, signaler eller udfald |
| Åbning | kun gennem `data.holdout.load_holdout`, med den committede præregistrering som frossen fil. Åbningen logges i `research/output/holdout_log.md`. **Én åbning** |

## 4. Statistik og MDE — regnet før, uden at se data

- **σ_dag** tages fra in-sample: $559 pr. dag pr. MNQ for "1m · uden middag". Vi kigger
  ikke i holdout for at skønne den.
- **n** er cirka 689 dage.

**H1 — retningen:** modellens middel mod N-retning, énsidet. `p = (1 + #{nulmodellens
middel ≥ modellens}) / 501`. Bestået ved p ≤ 0,05. Der er én variant, så der korrigeres
ikke.

| brutto over nulmodellen | styrke |
|---|---|
| $74 (in-sample) | 97% |
| $50 | 76% |
| $40 | 59% |

**H2 — netto:** middel `dag_netto_usd` ved dagens niveau, t-interval over dagene.

| test | MDE | styrke ved $41 | ved $30 | ved $20 |
|---|---|---|---|---|
| énsidet 95% (nedre grænse af 90%-interval > 0) | $53 | 61% | 41% | 24% |
| tosidet 95% (nedre grænse af 95%-interval > 0) | $60 | 49% | 29% | 15% |

**Vinderens forbandelse:** $41 var den bedste af 4 varianter. Den sande værdi ligger
sandsynligvis lavere, og så er styrken også lavere. Det er derfor, række 2 i §5 betyder
noget.

## 5. Beslutningsreglen — udkast

| nr | udfald | handling |
|---|---|---|
| 1 | H1 bestået **og** H2 bestået | **Bekræftet.** Ruinmodel for daglig P&L, bygning af botten, forward-test (§6), derefter Combine |
| 2 | H1 bestået, H2 ikke bestået, men middel netto > 0 | **Retningen er bekræftet, nettogevinsten er ikke bevist.** Handlingen afhænger af spørgsmål 3 |
| 3 | H1 bestået, middel netto ≤ 0 | **Parkeres:** retningen virker stadig, men betaler ikke omkostningen efter 2023 |
| 4 | Alt andet | **Parkeres:** VWAP-retningen holdt ikke efter offentliggørelsen |

## 6. Forward-testen — et tjek af udførelsen, ikke en statistisk test

Holdout afgør, om der er en edge. En forward-test på få uger kan ikke ændre det: 20 dage
lægger næsten intet til de 689. Forward-testen skal i stedet vise, at **botten handler som
backtesten**, før der står rigtige penge på spil:

- signalerne stemmer overens med motoren kørt på de samme dage;
- den faktiske omkostning pr. round trip, inklusive slippage, sammenlignet med $2,627;
- Topsteps regler: fladt 14:55 CT, pausen og kontraktskift.

Forslag: 20 handelsdage på live data uden rigtige penge. Bestået, hvis mindst 99% af
signalerne stemmer, og den faktiske omkostning er højst $3,17 pr. round trip (kandidat
1–4's slippage-konvention). In-sample var break-even-omkostningen $3,32 ved CI-nedre.

## 7. Diagnoser — rapporteres, men afgør intet

Samme som `b4_k5_vwap_trend.md` §9, for "1m · uden middag":
- brutto og netto, nominelt og ved $3,169;
- break-even-omkostningen;
- pr. år (2024, 2025, 2026);
- brutto pr. halve time;
- de sidste 5 minutter;
- dagsfordelingen og største tab inden for dagen;
- konsistensen;
- long mod short;
- altid-long.

Desuden: holdout-tallene side om side med in-sample-tallene.

## 8. Spørgsmål til ejeren

Anbefalingen står først.

**1. Netto-testen (H2)**
- **A: énsidet 95%.** Vi tester kun, om gevinsten er over 0, ikke om den kunne være
  negativ. Retningen er givet fra in-sample. Styrken ved $41 er 61%.
- B: tosidet 95%, som in-sample. Styrken er 49%.

**2. Holdout-periodens slutning**
- **A: fast slutdato 2026-09-30,** sat nu. Så kan ingen vælge en slutdato, der passer.
- B: til nyeste data på kørselsdagen.

**3. Hvis retningen holder, men nettogevinsten ikke kan bevises (række 2)**
- **A: videre til ruinmodel og forward-test.** Ruinmodellen regner både på holdout'ens
  punktestimat og på den nedre grænse. En Combine købes kun, hvis ruinmodellen viser en
  beståelsesrate klart over nulmodellen ved den nedre grænse.
- B: parkér som række 3. Ingen Combine uden bevist nettogevinst.

**4. Forward-testen (§6)**
- **A: 20 handelsdage uden rigtige penge før den første Combine,** med kriterierne i §6.
- B: spring den over og gå til Combine, når ruinmodellen er klar.

## 9. Code's opgave, når præregistreringen er committet

1. **Kør estimatet** for MNQ.v.0 ohlcv-1m 2024-01-01 → 2026-10-01. Hent kun, hvis det er
   højst $15. Lav kun tjekket af dækningen fra §3.
2. **Skriv en lille kørsel,** `research/b4_k5_holdout.py`, der kalder kandidat 5's modul
   uændret for "1m · uden middag".
   - Test: kørt på in-sample skal den give præcis in-sample-tallene: 14.831 handler,
     $41,07 og [9,02; 73,12].
3. **Commit kørslen og testene**, før holdout åbnes.
4. **Én kørsel** med `load_holdout`, R = 500. Rapport, og stop.
