# B4 — screening 3: planlagte begivenheder, som kan lægges sammen

**Skrevet:** 2026-10-10 af overblikssessionen, som aftalt efter kandidat 6.
**Grundlag:** litteraturscanningen (`research/output/b4_litteraturscan_2026_10.md`).
Nøgletallene er tjekket i forfatternes egne versioner, se kilderne. Holdout-regnskabet ligger
i `research/output/holdout_regnskab.md`.

---

## 1. Hvorfor begivenheder

Kandidat 1–7 er parkeret, og alle tre holdout-tests gav række 4. Litteraturen siger det
samme: de kendte mønstre i indeksfutures (intradag-trend, natdrift, driften før FOMC inden for
dagen) er svundet ind efter publicering.

**Det, der stadig ser levende ud, er planlagte begivenheder:** en kendt dato og et kendt
klokkeslæt, hvor nogen enten er tvunget til at handle (optionsudløb) eller får betaling for
at bære usikkerheden op til en offentliggørelse (FOMC, beskæftigelsestal).

**Tre egenskaber gør dem interessante for os:**
- De handler sjældent, så de fylder ikke meget i disciplinzonen.
- De ligger på forskellige dage, så de burde være næsten ukorrelerede.
- Kun de dage, hvor man handler, tæller med i risikoen. En lille edge pr. begivenhed kan
  derfor give en pæn Sharpe over et år.

## 2. Filtrene

F1–F7 fra screening 1 og 2 gælder: hvem betaler, Topstep og instrument, styrke, omkostning,
rene data, diversificering og disciplinzonen. To nye:

| nr | filter | spørgsmål |
|---|---|---|
| F8 | Forfald | Er effekten målt efter publiceringen eller efter 2016, og holdt den? |
| F9 | Styrke | Hvor mange begivenheder om året, og kan testen se papirets effekt? |

## 3. Kandidaterne

Tal i bp af ES. 1 bp er cirka $3,90 pr. MES ved 7.800. Omkostningen er cirka 1,1 bp pr. round
trip på MES.

| begivenhed | kilde | vindue (CT) | brutto bp pr. begivenhed | pr. år | forfald (F8) | t in-sample 2016–2023 ved papirets effekt | samlet |
|---|---|---|---|---|---|---|---|
| **A. Natten før månedligt optionsudløb** | Baltussen, Terstegge og Whelan | torsdag 17:00 → fredag 08:30, long | +14 (kvartalsudløb +27) | 12 | holdt i 16 af 19 år til 2021. En praktiker fandt den svagere i ES efter 2023 | cirka 2,3 | **med** |
| **A'. Vending fredag efter udløb** | samme | fredag 08:30 → cirka 11:00, short | −6 (kvartalsudløb −37) | 12 | som A | lav, mest kvartalsudløb | **med, som variant** |
| **C. Natten før FOMC** | Song (2026), Hu m.fl. (2022) | 17:00 → 08:30 på FOMC-dagen, long | +19 i natgabet (2016–2023) | 8 | Hu m.fl. fandt kun 4 bp i 2012–2018 for hele vinduet. Song finder natgabet signifikant i 2016–2023 | cirka 0,6–3,0 | **med, usikker** |
| **E. Natten før beskæftigelsestal** | Hu, Pan, Wang og Zhu (JFE 2022) | 17:00 → 07:25 på udgivelsesdagen, long | +10 (σ 43 pr. gang) | 12 | ikke opgjort for NFP alene. Samlet for NFP, ISM og BNP: 7 bp i 2012–2018 | cirka 1,6–2,3 | **med** |
| B. Store udbyttedage | Hartzmark og Solomon (AER 2025) | dagen før og på betalingsdagen, long | +7 (øverste kvartil) | cirka 63 | ingen tal efter 2018 | cirka 1,5 | lav. Kræver udbyttedata, vi ikke har, og er mest markedets eget afkast |
| Valutafixing (M6E) | Krohn, Mueller og Whelan (JF 2024) | omkring Tokyo-, ECB- og London-fixing | cirka 2,5 pr. ben | cirka 250 | svagere efter 2013 | — | lav. Omkostningen spiser den |

**Fælles mekanisme for A, C og E:** natten før en planlagt begivenhed stiger aktier i snit.
For FOMC og NFP forklares det som betaling for at bære usikkerheden (VIX stiger op til og
falder ved offentliggørelsen). For optionsudløbet forklares det som market makeres afdækning
op til afregningen kl. 08:30 CT.

## 4. Anbefaling: kandidat 8, en "begivenhedsbog"

**Long MES natten før de tre begivenheder, samlet i én bog**, med hver begivenhed rapporteret
for sig. Fredagsvendingen ved optionsudløb er en variant ved siden af.

- **Cirka 32 nætter om året.** Mindre end 2,5% af tiden i markedet.
- **Styrken samlet,** σ cirka 50 bp pr. nat:

| sand effekt bp pr. nat | t in-sample (cirka 256 nætter) | styrke holdout (cirka 88 nætter) |
|---|---|---|
| 12 (som i artiklerne) | cirka 3,8 | cirka 73% |
| 6 (det halve) | cirka 1,9 | cirka 30% |

- **Hvis den holder på artiklernes niveau:** cirka 0,24 i Sharpe pr. nat, eller cirka 1,3 om
  året, fordi der kun er risiko på de 32 nætter. Det er netop idéen om små edges, der lægges
  sammen.
- **Pengene:** cirka $47 pr. nat pr. MES ved 12 bp, cirka $1.500 om året pr. MES før
  omkostning. I disciplinzonen er der plads til cirka 2 MES pr. nat. Det er en langsom edge,
  ikke en motor til at bestå Combine hurtigt.

**Nulmodellen skal være andre nætter, ikke tilfældigt fortegn.** Natten steg generelt i
2024–2026 (kandidat 6's nulmodel gav +$2,08 pr. nat). Spørgsmålet er, om nætterne før
begivenheder er bedre end almindelige nætter. Nulmodellen er derfor tilfældige
ikke-begivenhedsnætter med samme vindue.

**Data:**
- ES 2016–2023 ligger klar. Intet datakøb.
- ES 2024–2026 er åbnet én gang for kandidat 7, men kun for aggregater over alle dage.
  Begivenhedsnætterne er ikke set hver for sig. Holdout-regnskabet tillader det med en note.
- Begivenhedskalenderen (tredje fredag, FOMC-datoer fra Fed og NFP-datoer fra BLS) bygges fra
  offentlige kilder og committes, før der ses på priser.

**Forbehold:**
- **FOMC er den mest usikre.** Hu m.fl. fandt den væk i 2012–2018, mens Song finder natgabet
  signifikant i 2016–2023. Song's prøve er den samme som vores in-sample, så et fund her
  er ikke uafhængigt.
- **Optionsudløbet blev lagt ud i 2023,** og en praktiker fandt det svagere i ES bagefter.
- **Optionsimplicitte præmier er små.** Knox m.fl. (2026) finder cirka 3–8 bp pr. begivenhed
  (ikke tjekket i PDF'en). Artiklernes realiserede tal kan være for høje.
- **Få begivenheder pr. år** betyder, at holdout kun har cirka 88 nætter.

## 5. Spørgsmål til kandidat 8

Anbefalingen står først.

**1. Hvad testes?**
- **A: begivenhedsbogen** (optionsudløb, FOMC og NFP samlet), hver rapporteret for sig.
- B: kun optionsudløbet, den stærkeste enkelt.

**2. Fredagsvendingen ved optionsudløb (short 08:30–11:00 CT)**
- **A: med som variant 2.**
- B: ikke med.

**3. Instrument**
- **A: MES** (ES-data, artiklernes instrument). MNQ som kontrol.
- B: MNQ.

**4. Nulmodel**
- **A: tilfældige ikke-begivenhedsnætter, samme vindue.** Den fjerner den generelle natdrift.
- B: samme nætter med tilfældigt fortegn.

## Kilder

- Baltussen, Terstegge & Whelan, *The Derivative Payoff Bias* (januar 2024-version) —
  https://afajof.org/management/viewp.php?n=98196
- Song, *Pre-FOMC Uncertainty Accumulation: Evidence from 0DTE Options* (15. sept. 2026) —
  https://afajof.org/management/viewp.php?n=260400
- Hu, Pan, Wang & Zhu, *Premium for Heightened Uncertainty: Explaining Pre-Announcement
  Market Returns*, JFE 2022 — https://en.saif.sjtu.edu.cn/junpan/PreAnn_20210728.pdf og
  https://www.nber.org/papers/w25817
- Hartzmark & Solomon, *Market-Wide Predictable Price Pressure*, AER 115(9), 2025
- Krohn, Mueller & Whelan, *Foreign Exchange Fixings and Returns around the Clock*, JF 2024
- Litteraturscanningen: `research/output/b4_litteraturscan_2026_10.md`
