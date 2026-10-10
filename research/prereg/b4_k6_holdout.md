# B4 kandidat 6 — præregistrering: holdout-testen af overnight drift efter salgsdage

**Skrevet:** 2026-10-10 af overblikssessionen, før data hentes og før kørslen. Committes
før begge dele. Filen er den frosne hypotese, som `data.holdout.load_holdout` kræver.
**Grundlag:** `research/prereg/b4_k6_overnight.md` med tillæg,
`research/output/b4_k6_overnight_laest.md` (række 2), udkastet
`research/prereg/b4_k6_holdout_udkast.md` og holdout-regnskabet
`research/output/holdout_regnskab.md`.
**Besluttet af ejeren 2026-10-10:**
- **1A:** kun V2 · salg.
- **2A:** kun 2024–2026 afgør. Ingen data fra før 2016.
- **3A:** $3,10 pr. round trip afgør. $2,85 rapporteres.
- **4A:** rapporten viser kun V2 · salg og dens nulmodel, så NQ-nætterne kan bruges igen.

**Holdout er ikke et nyt forsøg.** Tælleren forbliver 47.

---

## 1. Hvad testen afgør

NQ-nætterne 2024–2026 har ingen set. Testen spørger om to ting hver for sig:

1. **H1 — timen er særlig:** er long kl. 00:30–02:30 CT efter en salgsdag bedre end en
   tilfældig anden time samme nat?
2. **H2 — netto:** tjener den penge efter omkostning ved dagens niveau?

**Baggrund:** forfatterne skrev i 2026, at den ubetingede drift kl. 2–3 New York-tid har
været cirka 0 siden 2021. In-sample holdt driften efter salgsdage i 2021–2023 ($17,08,
$23,25 og $15,41 pr. nat). Testen viser, om den stadig holder.

## 2. Hvad der testes — intet må ændres

- **Strategien** er V2 · salg, præcis som i `research/prereg/b4_k6_overnight.md` §4:
  - **salgsdag:** forrige XNYS-dags RTH-close er under RTH-open (kortdage: RTH-slut 12:00
    CT);
  - **long 1 MNQ** fra åbningen af 1m-baren kl. 00:30 CT til åbningen af baren kl. 02:30
    CT, dansk tid 07:30–09:30;
  - mangler en bar, bruges den første bar derefter. Er den mere end 5 minutter forsinket,
    udelukkes natten;
  - intet stop;
  - punktforskelle på den forskelsjusterede serie, L_n fra den ujusterede;
  - **netto_usd_n = Δpt × (29.138 / L_n) × 2 − 3,10.**
- **Koden** er `research/b4_k6_overnight.py` som i in-sample-kørslen (kørt fra 583dfd9).
  Den må ikke ændres.
- **Serien bygges på in-sample og holdout samlet,** så salgsdagen for den første holdout-nat
  (2023-12-29) og forskelsjusteringen hænger sammen. Kun nætterne i §3 tæller.
- **Nulmodellen** er N-nat fra `b4_k6_overnight.md` §6: samme nætter, samme længde (120
  minutter), long, tilfældig start i natten 17:00–08:30 CT uden overlap med vinduet. Samme
  omkostning og normering. R = 500.

## 3. Data

| emne | valg |
|---|---|
| Serie | NQ.v.0 ohlcv-1m, Databento GLBX.MDP3. Samme som in-sample |
| Periode | Nætterne før XNYS-dagene **2024-01-02 → 2026-09-30**, fast slutdato |
| Lokalt i dag | NQ.v.0 2024-01-01 → 2026-09-11. Brugt i fase 1 og 2 til ATR og spread, aldrig til signaler eller udfald |
| Køb | Kun det manglende stykke [2026-09-11, 2026-10-01). Estimat først (gratis). Hentes kun, hvis det er højst **$2**. Forbruget er $63,49 af $120 |
| Efter hentningen | Kun antal rækker, første og sidste tidsstempel, som `pull` returnerer |
| Åbning | Kun gennem `data.holdout.load_holdout(frosset=research/prereg/b4_k6_holdout.md, symbol="NQ.v.0")`. **Én åbning.** Intet andet symbol |

## 4. Statistik og styrke — regnet før, uden at se data

- **σ = $190** pr. nat pr. MNQ. Det er in-sample-tallet for V2 · salg.
- **n ≈ 309** salgsnætter (cirka 689 nætter, hvoraf 44,9% følger en salgsdag), så
  standardfejlen er cirka $10,8.

**H1 — timen er særlig.**
- `p_H1 = (1 + #{N-nattens middel netto ≥ variantens middel netto}) / 501`. Énsidet.
  Én variant, så ingen korrektion.
- **H1 er bestået ved p_H1 ≤ 0,05.**

**H2 — netto.**
- Middel `netto_usd` pr. handlet nat ved $3,10, med t-interval over nætterne.
- **H2 er bestået, hvis den nedre grænse i et tosidet 90%-interval er > 0.** Det er en
  énsidet test på 5%.
- MDE ved 80% styrke: cirka $27.

| sand netto $/nat pr. MNQ | styrke H1 | styrke H2 |
|---|---|---|
| 10,82 (in-sample ved $3,10) | cirka 32–38% | cirka 26% |
| 5,4 (det halve) | cirka 13% | cirka 9% |

In-sample-tallet er den bedste af fire varianter og er sandsynligvis for højt. Testen kan
altså kun bekræfte en effekt, der er mindst så stor som in-sample. **Et negativt udfald
beviser ikke, at driften er væk.**

## 5. Beslutningsreglen — dækker alle udfald

**Det forsigtige tal (E_f):** den énsidede 95%-nedre grænse for middel netto ved $3,10 på
in-sample og holdout samlet (902 + cirka 309 nætter).

Rækkerne prøves i rækkefølge. Den første, der passer, gælder.

| nr | udfald | handling |
|---|---|---|
| 1 | H1 bestået **og** H2 bestået | **Bekræftet.** Videre til ruinmodellen og derefter forward-test |
| 2 | H1 bestået, H2 ikke bestået, men middel netto > 0 | **Timen er bekræftet, nettogevinsten er ikke bevist.** Videre som række 1, med samme betingelser |
| 3 | H1 bestået, middel netto ≤ 0 | **Parkeres:** timen er særlig, men betaler ikke omkostningen efter 2023 |
| 4 | Alt andet | **Parkeres for godt:** driften efter salgsdage holdt ikke efter 2023 |

**Betingelser for at handle kandidat 6 på en rigtig konto (række 1 og 2), alle skal være
opfyldt:**
1. E_f > 0.
2. **Ruinmodellen** (egen præregistrering) regner på de faktiske nætter fra in-sample og
   holdout i disciplinzonen. Ved E_f skal resultatet ligge over nulmodellens.
3. **Forward-testen:** 20 salgsnætter på live data uden rigtige penge, med botten og den
   frosne regel. Bestået, hvis mindst 99% af handlerne stemmer med motoren på samme nætters
   data, og den faktiske omkostning højst er $3,50 pr. round trip i middel.

Opfyldes de ikke, handles kandidat 6 ikke. Strategien ændres heller ikke for at opfylde
dem.

## 6. Hvad der ikke kan ske

- Ingen ændring af vinduet, salgsdagen, omkostningen eller normeringen efter, at data er
  hentet.
- Ingen andre varianter eller vinduer på holdout.
- Holdout åbnes én gang.

## 7. Diagnoser — kun for V2 · salg (svar 4A)

For at holde NQ-nætterne brugbare til senere natidéer rapporteres **kun** V2 · salg og
dens nulmodel. **Ikke** long hele natten, ikke de andre vinduer og ikke alle nætter.

| diagnose | hvorfor |
|---|---|
| Netto ved $2,85, nominelt og break-even pr. round trip | omkostning |
| Pr. år (2024, 2025, 2026) | koncentration over tid |
| **Bedste nats andel og de 5% bedste nætters andel** af netto i alt, netto uden de 5 bedste nætter og netto uden den bedste kalendermåned | hvor koncentreret er gevinsten? |
| Hit ratio og gevinst/tab-forhold | profil |
| Natfordeling p1/p5/p50/p95/p99, værste og bedste nat, σ | til ruinmodellen |
| Største tab inden for vinduet (mark-to-market på 1m-close) | Topsteps MLL brydes i realtid |
| Andel salgsnætter, udelukkede nætter, forsinkede udførelser og ruller i vinduet | datakvalitet |
| E_f ved $3,10 og $2,85 | betingelsen i §5 |

## 8. Rapporten

Filerne er `research/output/b4_k6_holdout.md` og `.csv`.

**Hovedtabellen** har én række for holdout og én for in-sample (V2 · salg) med kolonnerne:
- `naetter_n`;
- `brutto_usd_nat`, `netto_usd_nat` (ved $3,10);
- `CI90_netto`, `CI95_netto`;
- `N_nat_p5/p50/p95`, `p_H1`.

Derefter H1, H2, rækken i §5 og E_f. Til sidst diagnoserne i §7.

## 9. Code's opgave

**Trin 1 — og så stop, før holdout åbnes:**
1. **Estimatet** for NQ.v.0 ohlcv-1m [2026-09-11, 2026-10-01). Hent kun, hvis det er højst
   $2. Rapportér pris, brugt budget, antal rækker og første og sidste tidsstempel. Intet
   andet læses. API-nøglen vises aldrig.
2. **Kørslen** `research/b4_k6_holdout.py`. Den importerer kandidat 6's modul uændret og
   kører V2 · salg på en serie bygget af in-sample og holdout samlet. Den skal regne H1, H2,
   rækken i §5, E_f og diagnoserne i §7, **og intet andet fra holdout-nætterne.**

   Kræver det en ændring i kandidat 6's modul, stopper Code og rapporterer.
3. **Tests** i `tests/test_b4_k6_holdout.py`:
   - Kørt på in-sample giver den præcis in-sample-tallene for V2 · salg ved $2,85: 902
     nætter, netto $11,07 og CI95 [−0,95; 23,09].
   - Salgsdagen for den første holdout-nat tages fra 2023-12-29 (syntetisk serie).
   - Syntetiske tests af H2's énsidede grænse, E_f og alle 4 rækker.
   - Afskæringen ved 2026-09-30.
   - Holdout hentes kun gennem `load_holdout` med denne fil og kun for NQ.v.0.
   - Rapporten indeholder ingen andre vinduer, ingen "alle nætter" og ingen long hele
     natten fra holdout.
4. **Regressionstjek:**
   - kandidat 1's tre tjek;
   - `simuler_handel` 1.226 / −0,0115;
   - kandidat 2: 611 / −0,1430;
   - kandidat 3: 1.168 / −0,0712;
   - kandidat 4: 1.104 / −0,0920;
   - kandidat 5: 14.831 / $41,07;
   - kandidat 6: 902 nætter og $11,07;
   - kandidat 7: T 1.949 / $16,42 og K 556 / $9,40;
   - hele testsuiten.
5. **Commit og stop.** Holdout må ikke åbnes, før overblikssessionen har læst trin 1
   igennem, og ejeren har godkendt. Holdout kan kun bruges én gang.

**Trin 2 — efter godkendelse:** én kørsel med `load_holdout`, R = 500. Rapport efter §8,
tabellerne i chatten med brutto og netto, §5 anvendt mekanisk, og stop.
