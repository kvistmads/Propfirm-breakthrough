# B4 kandidat 5 — præregistrering: holdout-testen af "1m · uden middag"

**Skrevet:** 2026-10-08 af overblikssessionen, før data hentes og før kørslen. Committes
før begge dele. Filen er den frosne hypotese, som `data.holdout.load_holdout` kræver.
**Grundlag:** `research/output/b4_k5_vwap_trend_laest.md` (kandidat 5 frosset, række 1)
og udkastet `research/prereg/b4_k5_holdout_udkast.md`.
**Besluttet af ejeren 2026-10-08:** svar 1A, 2A, 3A og 4A, og køb af MNQ-holdout for
cirka $10.

**Én rettelse af overblikssessionens egen formulering i svar 3A.** Udkastet sagde, at
ruinmodellen skulle regne på "den nedre grænse". I række 2 er holdout'ens nedre grænse
pr. definition ≤ 0, så betingelsen kunne aldrig opfyldes. Det forsigtige tal er derfor
den nedre grænse for **in-sample og holdout samlet** (§5). Ejeren retter det før commit,
hvis han er uenig.

**Holdout er ikke et nyt forsøg.** Tælleren forbliver 41.

---

## 1. Hvad testen afgør

Testen bruger data, som ingen kandidat er valgt på, fra en periode efter artiklen
(november 2023). To spørgsmål testes hver for sig:

1. **H1 — retningen:** bærer VWAP-retningen stadig information efter offentliggørelsen?
2. **H2 — netto:** tjener strategien penge efter omkostning, ved dagens niveau?

## 2. Hvad der testes — intet må ændres

- **Strategien** er den frosne variant "1m · uden middag", præcis som i
  `research/prereg/b4_k5_vwap_trend.md` §4 med tillæg:
  - VWAP fra 08:30 CT;
  - vending ved hver 1m-lukning på den anden side;
  - pause 11:00–14:00 CT;
  - fladt 14:55 CT;
  - $2,627 pr. round trip;
  - normering til NQ 29.138.
- **Koden** er `research/b4_k5_vwap_trend.py` som i commit 9d4bd2e. Den må ikke ændres.
  Kun dataserien skifter.
- **Nulmodellen** er N-retning med modulets egen funktion og R = 500.
- **Udelukkelser og rultjek** (§4h og §3 i kandidat 5's præregistrering) gælder uændret.

## 3. Data

| emne | valg |
|---|---|
| Serie | MNQ.v.0 ohlcv-1m, Databento GLBX.MDP3. Samme instrument som in-sample |
| Periode (svar 2A) | ET-dagene 2024-01-02 → **2026-09-30**, fast slutdato. Udtrækket er [2024-01-01, 2026-10-01) |
| Lokalt i dag | Ingen MNQ ohlcv-1m efter 2023. NQ.v.0 for 2024–2026 findes (købt til ruinmodellen), og MNQ-spreadstikprøver findes (bbo). **Ingen af dem bruges** |
| Køb | Estimat først (gratis) med `data.src_databento.plan`. Der hentes kun, hvis estimatet er højst **$15**. Budgetvagten gælder |
| Efter hentningen | Kun antal rækker, første og sidste tidsstempel pr. fil, som `pull` returnerer. Ingen priser, signaler eller udfald |
| Åbning | Kun gennem `data.holdout.load_holdout(frosset=research/prereg/b4_k5_holdout.md, symbol="MNQ.v.0")`. Åbningen logges i `research/output/holdout_log.md`. **Én åbning** |

## 4. Statistik og MDE — regnet før, uden at se data

- **σ_dag = $559** pr. dag pr. MNQ. Det er in-sample-tallet for "1m · uden middag". Vi
  kigger ikke i holdout for at skønne den.
- **n ≈ 689** handelsdage.

**H1 — retningen.**
- Modellens middel `dag_netto_usd` sammenlignes med N-retning: `p = (1 + #{nulmodellens
  middel ≥ modellens middel}) / 501`.
- Énsidet. Der er én variant, så der korrigeres ikke.
- **H1 er bestået ved p ≤ 0,05.**

| brutto over nulmodellen | styrke |
|---|---|
| $74 (in-sample) | 97% |
| $50 | 76% |
| $40 | 59% |

**H2 — netto (svar 1A, énsidet).**
- Middel `dag_netto_usd` ved dagens niveau, med t-interval over dagene.
- **H2 er bestået, hvis den nedre grænse i et tosidet 90%-interval er > 0.** Det er en
  énsidet test på 5%.
- MDE er $53.

| sand nettogevinst pr. dag | styrke |
|---|---|
| $41 (in-sample) | 61% |
| $30 | 41% |
| $20 | 24% |

$41 var den bedste af 4 varianter. Den sande værdi ligger sandsynligvis lavere. Derfor er
række 2 i §5 bestemt på forhånd.

## 5. Beslutningsreglen — dækker alle udfald

**Det forsigtige tal (E_f):** den énsidede 95%-nedre grænse for middel `dag_netto_usd` på
in-sample og holdout samlet: 1.169 + cirka 689 dage, "1m · uden middag". Det bruges i
række 1 og 2.

Rækkerne prøves i rækkefølge. Den første, der passer, gælder.

| nr | udfald | handling |
|---|---|---|
| 1 | H1 bestået **og** H2 bestået | **Bekræftet.** Videre til ruinmodel, bot og forward-test (§6). En Combine købes, når betingelserne nedenfor er opfyldt |
| 2 | H1 bestået, H2 ikke bestået, men middel netto > 0 (svar 3A) | **Retningen er bekræftet, nettogevinsten er ikke bevist.** Videre til ruinmodel, bot og forward-test som i række 1, med samme betingelser for en Combine |
| 3 | H1 bestået, middel netto ≤ 0 | **Parkeres:** retningen virker stadig, men betaler ikke omkostningen efter 2023 |
| 4 | Alt andet | **Parkeres:** VWAP-retningen holdt ikke efter offentliggørelsen |

**Betingelser for at købe den første Combine (række 1 og 2), alle skal være opfyldt:**
1. E_f > 0.
2. Ruinmodellen for daglig P&L (egen præregistrering) regner ved både holdout'ens
   punktestimat og E_f. **Ved E_f** skal beståelsesraten ligge over nulmodellens, og
   intervallet på forskellen skal ligge over 0, som i ruinmodel v2.
3. Forward-testen i §6 er bestået.

Opfyldes de ikke, købes der ingen Combine. Strategien ændres heller ikke for at opfylde
dem.

## 6. Forward-testen (svar 4A) — tjek af udførelsen

Holdout afgør, om der er en edge. Forward-testen skal vise, at botten handler som
backtesten, før der står rigtige penge på spil.

- **20 handelsdage** på live data uden rigtige penge, med botten og den frosne regel.
- **Bestået, hvis begge dele holder:**
  1. Mindst 99% af signalerne stemmer med motoren, kørt på de samme dages data.
  2. Den faktiske omkostning er højst **$3,17 pr. round trip** i middel. Den regnes som
     kommission plus afvigelsen mellem fyldprisen og 1m-barens åbning, på begge sider.
- **Dumper den,** rettes botten, og testen køres igen. Strategien ændres ikke.

## 7. Diagnoser — rapporteres, men afgør intet

For "1m · uden middag", side om side med in-sample:
- brutto og netto, nominelt og ved $3,169;
- break-even-omkostningen;
- pr. år (2024, 2025, 2026);
- brutto pr. halve time New York-tid;
- de sidste 5 minutter;
- dagsfordelingen og største tab inden for dagen;
- bedste dags andel og de 5% bedste dages andel;
- long mod short og altid-long;
- udelukkede dage og manglende minutter;
- E_f og middel for in-sample og holdout samlet.

## 8. Rapporten

Filerne er `research/output/b4_k5_holdout.md` og `.csv`.

**Hovedtabellen** har én række for holdout og én for in-sample med kolonnerne:
- `dage_n`, `handler_n`;
- `brutto_usd_dag`, `netto_usd_dag`;
- `CI90_netto`, `CI95_netto`;
- `N_retning_p5/p50/p95`, `p_H1`.

Derefter H1, H2, rækken i §5 og E_f. Til sidst diagnoserne.

## 9. Code's opgave

**Trin 1 — og så stop, før holdout åbnes:**
1. **Estimatet** for MNQ.v.0 ohlcv-1m [2024-01-01, 2026-10-01). Hent kun, hvis det er
   højst $15. Rapportér pris, brugt budget, antal rækker og første og sidste tidsstempel
   pr. fil. Intet andet læses. API-nøglen vises aldrig.
2. **Kørslen** `research/b4_k5_holdout.py`. Den importerer kandidat 5's modul uændret og
   kører "1m · uden middag" på en given serie. Den skal regne:
   - H1 og H2;
   - rækken i §5;
   - E_f;
   - diagnoserne i §7.
3. **Tests** i `tests/test_b4_k5_holdout.py`:
   - Kørt på in-sample giver den præcis in-sample-tallene: 14.831 handler, $41,07,
     CI95 [9,02; 73,12] og p_FWE 0,0020.
   - Syntetiske tests af H2's énsidede grænse, E_f og alle 4 rækker.
   - Afskæringen ved 2026-09-30.
   - Holdout hentes kun gennem `load_holdout` med denne fil.
4. **Regressionstjek:**
   - kandidat 1's tre tjek;
   - `simuler_handel` 1.226 / −0,0115;
   - kandidat 2: 611 / −0,1430;
   - kandidat 3: 1.168 / −0,0712;
   - kandidat 4: 1.104 / −0,0920;
   - hele testsuiten.
5. **Commit og stop.** Holdout må ikke åbnes, før overblikssessionen har læst kørslen
   igennem, og ejeren har godkendt. Holdout kan kun bruges én gang.

**Trin 2 — efter godkendelse:** én kørsel med `load_holdout`, R = 500. Rapport efter §8,
tabellerne i chatten, §5 anvendt mekanisk, og stop.
