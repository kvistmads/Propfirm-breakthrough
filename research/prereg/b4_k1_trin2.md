# B4 kandidat 1 — præregistrering: trin 2, videoens kriterier som score

**Skrevet:** 2026-09-24 af overblikssessionen, før kørslen. Committes før kørslen.
**Grundlag:** `research/prereg/b4_k1_trin2_optaelling.md` og tillægget (definitionerne og
de fire præciseringer), `research/output/b4_k1_trin2_optaelling.md` (optællingen),
`research/output/b4_k1_trinA_laest.md` og `research/output/b4_k1_motorrettelse.md`,
`research/kilder/photon_sd_video_noter.md`.
**Aftalt med ejeren:** score som test af videoens påstand, BE og buffer faste, begge spor,
stopreglen (`research/output/b4_hypoteser.md`, "Trin 2 — aftalt").

---

## 1. Hvad trin 2 afgør

Videoen siger at jo flere af de otte kriterier en zone opfylder, jo bedre er den (16:00).
Nr. 8 er i kernen. De øvrige syv giver hver zone en **score**. Trin 2 afgør to ting:

1. **Hovedtesten:** stiger middel netto-R med scoren? Det er videoens påstand, og det er
   stopreglen: stiger den ikke, parkeres kandidat 1.
2. **Varianterne:** findes der en regel — "brud på struktur" eller en tærskel på scoren —
   som kan handles med en brugbar edge?

Kandidat 1 har haft to chancer: kernen alene (trin A) og videoens egne kriterier (trin 2).
Nye idéer — fx videoens indgangsmetode 2, vendelys efter en likvidering — er **nye
kandidater** med egen præregistrering, ikke redningsforsøg på denne.

## 2. Serie, spor og faste indstillinger

| emne | valg |
|---|---|
| Serie | MNQ.v.0 1m, 2019-05-06 → 2023-12-31, kun gennem `data.holdout.load_in_sample` |
| Spor A | handelstimeframe 15m, højere timeframe 1h |
| Spor B | handelstimeframe 5m, højere timeframe 15m. Besluttet af ejeren 2026-09-24 efter optællingen |
| Kerne | v2, buffer 10%, BE +1,2R — fast, én version af hver |
| Motor | den rettede (motorrettelse 1-3): i fyldnings-1m-baren kan kun stoppet rammes |
| Fyldning | de otte regler i `b4_k1_trinA.md` §4a, uændret. Regel 4: stop og mål i samme 1m-bar → stoppet først |
| Sizing | `kontrakter = floor(250 / (risiko_pt × 2))`, loftet ved 50, handel kun ved `kontrakter ≥ 1` |
| Disciplin | én afgjort handel om dagen, to BE-udgange lukker dagen, indgang 15:30-21:30, fladt 21:50 dansk tid |
| Filtre | `research/b4_k1_filtre.py` som committet, med de fire præciseringer |
| Score | antal sande kriterier blandt 1-7. **Score 5, 6 og 7 slås sammen til "5+"**, fordi 6 og 7 næsten ikke findes (spor A: 48 og 4 signaler) |

**Omkostningerne regnes som i backtesten.** At zonerne i point er større ved dagens
prisniveau, og omkostningen i R dermed lavere, bruges **ikke** i afgørelsen.

## 3. Hvordan scoren bruges i en handel

Scoren vurderes ved lukningen af lyset før berøringen, som definitionerne kræver. Live
betyder det: botten vurderer hver aktiv zone ved hvert lys og har kun en hvilende ordre på
zonen, mens den opfylder variantens regel. Backtesten gør det samme: en zone giver kun en
handel, hvis den opfylder reglen ved lyset før berøringen.

## 4. Hovedtesten — stiger middel netto-R med scoren?

**Enheden er skyggehandler.** Hvert signal (berøring i vinduet, `kontrakter ≥ 1`, og
gennemhandling med ét tick) simuleres for sig med den rettede motor, BE +1,2R og fladning
21:50. Disciplinreglerne bruges ikke her, fordi spørgsmålet er om scoren forudsiger
udfaldet, ikke hvilken handel der kommer først på dagen. Strejf uden gennemhandling er
ikke handler.

**Statistikken:** hældningen β i en OLS-regression af `R_netto` på scoren (0, 1, 2, 3, 4,
5+). Standardfejlen er klyngerobust pr. handelsdag, fordi handler samme dag deler marked og
kan overlappe. Én-sidet test, H1: β > 0.

**To spor, to test:** α = 0,025 pr. spor (Bonferroni over 2).

**MDE**, én-sidet α = 0,025 og 80% styrke, σ_R = 1,3 (antaget; BE trækker under 2:1's 1,414),
klyngeeffekt ρ = 0,1 (antaget):

| spor | signaler_n | score_sd | handler_pr_dag | MDE_beta_R_pr_scoretrin |
|---|---|---|---|---|
| A | 3.349 | 1,26 | 3,1 | **0,055** |
| B | 9.273 | 1,23 | 7,9 | **0,040** |

For at gå fra kernens ca. −0,01 R til +0,20 R ved score ≥ 4 kræves en hældning på ca.
**0,13 R pr. scoretrin** (spor A 0,128, spor B 0,123). **MDE ligger under det, så testen
kan se den hældning der betyder noget.**

**Sekundært, afgør intet:** samme hældning i nulmodellen N1 (§5), som p5/p50/p95 over
gentagelserne og andelen af gentagelser med β ≥ den observerede. Den svarer på om
kriterierne virker fordi zonerne er rigtige, eller fordi de ville virke på et hvilket som
helst niveau.

## 5. Varianterne

**Fire pr. spor, otte i alt:**

| variant | regel | dage_med_signal_n spor A / B | MDE_middel_R_netto |
|---|---|---|---|
| Brud alene | kriterium 1 sandt | 914 / 1.139 | 0,13 / 0,12 |
| Score ≥ 2 | | 1.012 / 1.168 | 0,13 / 0,12 |
| Score ≥ 3 | | 883 / 1.127 | 0,14 / 0,12 |
| Score ≥ 4 | | 585 / 942 | 0,17 / 0,13 |

Hver variant handles med disciplinreglerne som i trin A. Målet er **middel netto-R pr.
handel** med t-CI. MDE er regnet på `dage_med_signal_n` som nedre grænse for antallet af
handler, σ = 1,3, én-sidet med Šidák over fire effektive forsøg. **Alle ligger under 0,20
R.**

**Nulmodellen N1** er trin A's: hver zones dannelseslys flyttes til et tilfældigt lys i
samme ISO-uge, side og H bevares. Den flyttede zone får **sine egne filterværdier og sin
egen score**, regnet med samme kode på samme serie, og samme variantregel bruges. Så
svarer N1 på: klarer tilfældigt placerede zoner med samme score sig lige så godt?
**R = 500 gentagelser.**

**Testen:** Westfall-Young maks-statistik over alle otte varianter på tværs af begge spor,
præcis som i trin A: for hver N1-gentagelse gemmes den største middel netto-R blandt de
otte, og den observerede bedste variant holdes op mod den fordeling.

## 6. Tælleren

| trin | forsøg |
|---|---|
| Trin A | 6 |
| Trin 2, hovedtest | 2 |
| Trin 2, varianter | 8 |
| **I alt** | **16** |

## 7. Beslutningsreglen — dækker alle udfald

| udfald | handling |
|---|---|
| Hovedtesten: β er ikke signifikant over 0 på **noget** spor | **Stopreglen: kandidat 1 parkeres.** Varianterne rapporteres, men afgør intet |
| Hovedtesten holder på mindst ét spor, **og** den bedste variant har p_FWE ≤ 0,05, middel netto-R ≥ +0,20 R og CI-nedre > 0 | **Varianten fryses.** Næste skridt: ruinmodellen genkøres med disciplinreglerne, MNQ-holdout købes, og holdout-testen præregistreres |
| Alt andet | **Kandidat 1 parkeres** som "kriterierne hjælper, men ingen variant kan handles". Tallene skrives ned |

Krydser et konfidensinterval en grænse, gælder den laveste kategori.

## 8. Så vi ikke overser en edge — diagnoser der rapporteres, men ikke afgør

**Tvetydige minutter.** Regel 4 antager at stoppet rammes først, når stop og mål — eller
stop og BE-trigger — ligger i samme 1m-bar. Det er forsigtigt, og på spor B's små zoner
sker det oftere. Derfor:

- Antallet af tvetydige handler rapporteres pr. spor og pr. score.
- Hovedtesten og den bedste variant regnes også i **bedste fald**, hvor målet antages ramt
  først. Det giver et interval for hvad data under minutniveau kunne ændre.
- **Afgørelsen i §7 tages på det forsigtige tal.** Ville den blive en anden i bedste fald,
  skrives resultatet som *afhængigt af data under minutniveau*. Næste skridt er da en
  særskilt præregistreret måling med Databento-handelsdata for præcis de tvetydige barer.
  Estimatet hentes gratis først. Det er en måling, ikke en variant.

**Øvrige diagnoser:**

| diagnose | hvorfor |
|---|---|
| Strejf pr. spor, med kontrafaktisk middel-R som i trin A | fyldningsreglens pris |
| `holder_pct` pr. score | ejerens forventning om retesten |
| Middel netto-R når hvert kriterium er sandt mod falsk, pr. spor | beskrivende. **Må ikke bruges til nye varianter uden ny præregistrering, og en sådan brug koster fuldt N** |
| Demand og supply hver for sig, med CI på forskellen | drift |
| Pr. år | koncentration |
| `omk_R_netto_p50/p90` pr. variant | omkostningerne |

## 9. Rapporten

`research/output/b4_k1_trin2.md` og `.csv`. Kompakt hovedtabel i chatten, brutto og netto
side om side, enhed i kolonnenavnet.

| tabel | indhold |
|---|---|
| Hovedtest | pr. spor: β, CI95, p én-sidet, `middel_R_netto` med CI pr. score 0-5+, N1's β p5/p50/p95 |
| Varianter | pr. variant: `handler_n`, `middel_R_brutto`, `middel_R_netto` med CI, `win_rate_pct_netto`, udfaldsandele, N1's p50/p5, p_FWE på den bedste |
| Afgørelsen | §7 anvendt mekanisk, med den kategori der gælder |
| Diagnoserne | §8 |

## 10. Før kørslen: regressionstjek og tidsmåling

**Regressionstjek** — alle skal holde, ellers køres intet:

1. `b4_k1_optaelling.py` gengiver `b4_k1_optaelling_v2.csv` byte for byte.
2. Spor A, variant "score ≥ 0" med buffer 10% og BE +1,2R gengiver motorrettelsens tal
   præcis: `handler_n` 1.226 og `middel_R_netto` −0,0115.
3. Scorefordelingen gengiver `b4_k1_trin2_optaelling.csv`.

**Tidsmåling:** ét gennemløb pr. spor og 5 N1-gentagelser pr. spor. Den forventede tid for R
= 500 rapporteres, og **der stoppes før den rigtige kørsel**, indtil ejeren har godkendt
den. R sænkes ikke.

## 11. Forventning, skrevet før kørslen — ikke et kriterium

- **Mest sandsynligt parkeres kandidat 1.** Kernen var negativ efter motorrettelsen, og
  de to stærkeste sammenhænge mellem kriterierne trækker hver sin vej (6 mod 7) eller
  tæller det samme to gange (1 og 4). Mit skøn: hovedtesten holder på mindst ét spor med
  ca. 35% sandsynlighed, og en variant fryses med ca. 5-10%.
- Kriterium 6 (retning) har den største forskel mellem sand og falsk. Det er markedets
  retning i perioden, ikke zonen.
- Spor B har lavere middel netto-R end spor A ved samme score, fordi omkostningerne er
  højere.
- `holder_pct` stiger svagt med scoren, fra ca. 50%.

## 12. Efter kørslen

Stop. Tabellerne i chatten. Ingen ændring af definitioner, ingen nye varianter, ingen
forslag. Resultatet læses sammen med ejeren, og §7 anvendes mekanisk.
