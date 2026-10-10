# B4 kandidat 7 — præregistrering: holdout-testen af "T · tærskel"

**Skrevet:** 2026-10-10 af overblikssessionen, før data hentes og før kørslen. Committes
før begge dele. Filen er den frosne hypotese, som `data.holdout.load_holdout` kræver.
**Grundlag:** `research/output/b4_k7_rebalancering_laest.md` (T frosset, række 1) og
mønstret fra kandidat 5's holdout (`research/prereg/b4_k5_holdout.md`).
**Besluttet af ejeren 2026-10-10:**
- **1A:** T testes uændret som frosset, med retningen og netto som to hypoteser.
- **2A:** hele perioden afgør. Tal uden de urolige perioder og de bedste dages andel
  rapporteres, men afgør intet.
- **3A:** ruinmodellen kommer efter holdout, på de faktiske dage.

**Holdout er ikke et nyt forsøg.** Tælleren forbliver 47.

---

## 1. Hvad testen afgør

Testen bruger data, som ingen kandidat er valgt på, fra en periode efter artiklens prøve
(marts 2023) og hen over publiceringen (NBER, marts 2025). To spørgsmål testes hver for sig:

1. **H1 — retningen:** bærer rebalanceringssignalets retning stadig information?
2. **H2 — netto:** tjener T penge efter omkostning, ved dagens niveau?

**Det vigtigste forbehold:** in-sample kom 81% af gevinsten fra marts 2020. Holdout
indeholder mindst to urolige perioder (august 2024 og april 2025). Testen viser derfor
især, om T tjener i uro, den ikke er tilpasset. Også her kan få dage afgøre udfaldet, så
diagnoserne i §7 viser, hvor koncentreret gevinsten er.

## 2. Hvad der testes — intet må ændres

- **Strategien** er den frosne variant "T · tærskel", præcis som i
  `research/prereg/b4_k7_rebalancering.md` §4 med tillæg:
  - signalet fra ES og ZN ved RTH-slut, 26 bånd fra 0 til 2,5%, |s| ≥ δ;
  - position `w = −T / 0,015` MES-enheder;
  - Topstep-dagen fra 17:00 CT dagen før til 15:08 CT;
  - $4,45 pr. round trip pr. MES, skaleret med |w|;
  - normering til ES 7.800.
- **Koden** er `research/b4_k7_rebalancering.py` som i commit 4c5cc8e. Den må ikke ændres.
  Kun dataserien skifter.
- **Signalets porteføljer kører videre** fra in-sample uden ny start. Holdout-dagenes signal
  bygges på den samlede serie, så tilstanden ved 2023-12-29 er præcis den samme som i
  in-sample-kørslen.
- **Nulmodellen** er N-retning med modulets egen funktion og R = 500.
- **Udelukkelser og rultjek** (§4b og §4g i præregistreringen) gælder uændret.
- **K · kalender** og **Nasdaq-kontrollen** er ikke med.

## 3. Data

| emne | valg |
|---|---|
| Serier | ES.v.0 og ZN.v.0 ohlcv-1m, Databento GLBX.MDP3. Samme som in-sample |
| Periode | Handelsdage d fra **2024-01-02 → 2026-09-30**, fast slutdato. Udtrækket er [2024-01-01, 2026-10-01). Signaldagen for 2024-01-02 er 2023-12-29, som ligger i in-sample |
| Lokalt i dag | Ingen ES eller ZN efter 2023 |
| Køb | Estimat først (gratis) med `data.src_databento.plan`. Der hentes kun, hvis det samlede estimat er højst **$15**. Budgetvagten gælder. Forbruget er $56,65 af $120 |
| Efter hentningen | Kun antal rækker, første og sidste tidsstempel pr. fil, som `pull` returnerer. Ingen priser, signaler eller udfald |
| Åbning | Kun gennem `data.holdout.load_holdout(frosset=research/prereg/b4_k7_holdout.md, symbol=...)`, én gang for ES.v.0 og én for ZN.v.0. De to linjer i `research/output/holdout_log.md` er **én åbning** |
| **NQ holdes uden for** | NQ.v.0 2024–2026 åbnes ikke. Det er kandidat 6's uåbnede holdout for natten. Derfor er der ingen Nasdaq-kontrol og ingen korrelation med kandidat 6 i holdout |

## 4. Statistik og styrke — regnet før, uden at se data

- **σ_dag = $293** pr. aktiv dag pr. MES-enhed. Det er in-sample-tallet for T, inklusive
  marts 2020. Vi kigger ikke i holdout for at skønne den.
- **n ≈ 689** handelsdage, så standardfejlen er cirka $11,1.

**H1 — retningen.**
- T's middel `netto_usd` sammenlignes med N-retning:
  `p = (1 + #{nulmodellens middel ≥ T's middel}) / 501`.
- Énsidet. Der er én variant, så der korrigeres ikke.
- **H1 er bestået ved p ≤ 0,05.**

| brutto over nulmodellen, $/dag | styrke |
|---|---|
| 18,0 (in-sample) | 49% |
| 10 | 23% |
| 5 | 12% |

**H2 — netto (énsidet).**
- Middel `netto_usd` pr. aktiv dag ved dagens niveau, med t-interval over dagene.
- **H2 er bestået, hvis den nedre grænse i et tosidet 90%-interval er > 0.** Det er en
  énsidet test på 5%.
- MDE ved 80% styrke er cirka $27,7.

| sand netto $/dag | styrke |
|---|---|
| 16,42 (in-sample) | 43% |
| 10 | 23% |
| 3,09 (in-sample uden marts 2020) | 9% |

Styrken er lav. Er holdout roligere end in-sample, er σ mindre og styrken lidt højere. Er
gevinsten koncentreret i få dage, er den lavere.

## 5. Beslutningsreglen — dækker alle udfald

**Det forsigtige tal (E_f):** den énsidede 95%-nedre grænse for middel `netto_usd` på
in-sample og holdout samlet (1.949 + cirka 689 dage). Det bruges i række 1 og 2.

Rækkerne prøves i rækkefølge. Den første, der passer, gælder.

| nr | udfald | handling |
|---|---|---|
| 1 | H1 bestået **og** H2 bestået | **Bekræftet.** Videre til ruinmodellen (svar 3A), og derefter bot og forward-test |
| 2 | H1 bestået, H2 ikke bestået, men middel netto > 0 | **Retningen er bekræftet, nettogevinsten er ikke bevist.** Videre som i række 1, med samme betingelser |
| 3 | H1 bestået, middel netto ≤ 0 | **Parkeres:** retningen virker stadig, men betaler ikke omkostningen efter 2023 |
| 4 | Alt andet | **Parkeres:** T holdt ikke uden for artiklens prøve |

**Betingelser for at handle T på en rigtig konto (række 1 og 2), alle skal være opfyldt:**
1. E_f > 0.
2. **Ruinmodellen** (egen præregistrering, svar 3A) regner på de faktiske dage fra
   in-sample og holdout, med Topsteps regler inklusive konsistensreglen og DLL'en, for T
   alene og T + kandidat 6. Den afgør også, hvordan T's brøkdele af en MES bliver til hele
   kontrakter. Ved E_f skal resultatet ligge over nulmodellens.
3. **Forward-testen:** 20 handelsdage på live data uden rigtige penge, med botten og den
   frosne regel. Bestået, hvis mindst 99% af positionerne stemmer med motoren på samme
   dages data, og den faktiske omkostning højst er $5,70 pr. round trip i middel.

Opfyldes de ikke, handles T ikke. Strategien ændres heller ikke for at opfylde dem.

## 6. Hvad der ikke kan ske

- Ingen ændring af T, signalet, vinduet, omkostningen eller normeringen efter, at data er
  hentet.
- Ingen ny variant på holdout. Udfaldet af diagnoserne i §7 kan blive til nye hypoteser,
  men kun med egen præregistrering og rene data.
- Holdout åbnes én gang.

## 7. Diagnoser — rapporteres, men afgør intet (svar 2A)

For T, side om side med in-sample:

| diagnose | hvorfor |
|---|---|
| **Uden de urolige måneder:** en kalendermåned er urolig, hvis sd af ES' dagsafkast R^ES_t i måneden er over in-sample-p90 af samme mål (2016–2023). Grænsen regnes i trin 1 alene på in-sample | tjener T noget uden for uro? |
| **Bedste dags andel og de 5% bedste dages andel** af netto i alt, og netto uden de 5 bedste dage | hvor koncentreret er gevinsten? |
| Pr. år (2024, 2025, 2026) | koncentration |
| Før og efter publiceringen (2025-03-01) | publiceringseffekt |
| E_f uden marts 2020 | hvor meget hviler E_f på én måned? |
| Reversal-regressionen fra tillæggets §4 (OLS med HC3) | er det stadig mere end reversal? |
| Driftjusteret brutto og andel long og short | markedets drift |
| Brutto nat og RTH | hvornår kommer gevinsten |
| Netto ved $5,70, nominelt og break-even pr. round trip | omkostning |
| T med hele MES: round(w) | kan den handles med hele kontrakter? |
| Dagsfordeling p1/p5/p50/p95/p99, værste og bedste dag, σ pr. dag, største tab inden for dagen og skævhed | til ruinmodellen |
| Udelukkede dage, forsinkede udførelser, manglende signalbarer og ruller i vinduerne | datakvalitet |

## 8. Rapporten

Filerne er `research/output/b4_k7_holdout.md` og `.csv`.

**Hovedtabellen** har én række for holdout og én for in-sample med kolonnerne:
- `aktive_dage_n`, `andel_long`;
- `brutto_usd_dag`, `netto_usd_dag`;
- `CI90_netto`, `CI95_netto`;
- `N_retning_p5/p50/p95`, `p_H1`.

Derefter H1, H2, rækken i §5 og E_f. Til sidst diagnoserne.

## 9. Code's opgave

**Trin 1 — og så stop, før holdout åbnes:**
1. **Estimatet** for ES.v.0 og ZN.v.0 ohlcv-1m [2024-01-01, 2026-10-01). Hent kun, hvis det
   samlede estimat er højst $15. Rapportér pris, brugt budget, antal rækker og første og
   sidste tidsstempel pr. fil. Intet andet læses. API-nøglen vises aldrig.
2. **Kørslen** `research/b4_k7_holdout.py`. Den importerer kandidat 7's modul uændret og
   kører T på en given serie, hvor signalet bygges på in-sample og holdout samlet. Den skal
   regne:
   - H1 og H2;
   - rækken i §5;
   - E_f;
   - diagnoserne i §7.

   Kræver det en ændring i kandidat 7's modul, stopper Code og rapporterer.
3. **Tests** i `tests/test_b4_k7_holdout.py`:
   - Kørt på in-sample giver den præcis in-sample-tallene for T: 1.949 aktive dage, netto
     $16,42, CI95 [3,43; 29,42] og p_FWE 0,006.
   - Signalets tilstand ved 2023-12-29 er den samme, uanset om serien slutter dér eller
     fortsætter (syntetisk serie).
   - Syntetiske tests af H2's énsidede grænse, E_f og alle 4 rækker.
   - Afskæringen ved 2026-09-30.
   - Definitionen af urolige måneder.
   - Holdout hentes kun gennem `load_holdout` med denne fil, og NQ.v.0's holdout åbnes ikke.
4. **Grænsen for urolige måneder** regnes på in-sample alene og rapporteres: tallet og
   hvilke in-sample-måneder der er urolige. Ingen P&L.
5. **Regressionstjek:**
   - kandidat 1's tre tjek;
   - `simuler_handel` 1.226 / −0,0115;
   - kandidat 2: 611 / −0,1430;
   - kandidat 3: 1.168 / −0,0712;
   - kandidat 4: 1.104 / −0,0920;
   - kandidat 5: 14.831 / $41,07;
   - kandidat 6: 902 nætter og $11,07;
   - kandidat 7: T 1.949 / $16,42 og K 556 / $9,40;
   - hele testsuiten.
6. **Commit og stop.** Holdout må ikke åbnes, før overblikssessionen har læst trin 1
   igennem, og ejeren har godkendt. Holdout kan kun bruges én gang.

**Trin 2 — efter godkendelse:** én kørsel med `load_holdout`, R = 500. Rapport efter §8,
tabellerne i chatten med brutto og netto, §5 anvendt mekanisk, og stop.
