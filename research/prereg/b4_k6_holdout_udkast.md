# B4 kandidat 6 — udkast: holdout-testen af overnight drift efter salgsdage

**Skrevet:** 2026-10-10 af overblikssessionen. Det er et udkast med spørgsmål til ejeren.
Den endelige præregistrering skrives efter svarene og committes, før data hentes eller
åbnes.
**Grundlag:** `research/prereg/b4_k6_overnight.md` med tillæg,
`research/output/b4_k6_overnight_laest.md` (række 2), edge-kravets §6 række 1 og ejerens
svar 1A (2026-10-10). Holdout-regnskabet: `research/output/holdout_regnskab.md`.

**Holdout er ikke et nyt forsøg.** Tælleren forbliver 47.

---

## 1. Hvorfor testen, og hvad der er nyt siden kandidat 6

Kandidat 6 blev parkeret i række 2: timen omkring Europas åbning var særlig efter
salgsdage, men nettogevinsten var ikke bevist. Edge-kravet pegede på en holdout-test som
næste skridt. NQ-nætterne 2024–2026 er det eneste holdout, ingen har set.

**Ny viden fra forfatterne selv.** Boyarchenko, Larsen og Whelan skrev i 2026 på New York
Feds blog ("The Disappearing Overnight Drift"), at drift kl. 2–3 New York-tid har været
cirka 0 siden 2021. Før var den cirka 3,7% om året.

**Vores egne in-sample-tal peger samme vej, men kun for den ubetingede drift.**

| variant, netto $/nat pr. MNQ | 2021 | 2022 | 2023 |
|---|---|---|---|
| V1 · alle | 0,61 | −2,38 | −10,45 |
| V2 · alle | −2,22 | −13,58 | −5,16 |
| **V2 · salg** | **17,08** | **23,25** | **15,41** |

- Driften på alle nætter forsvandt hos os også efter 2020.
- **Driften efter salgsdage holdt i 2021–2023.** Det passer med forfatternes mekanisme:
  forhandlerne bærer et lager efter salg ved lukningen. Bliver de store ubalancer
  sjældnere, falder den gennemsnitlige drift, men driften efter et salg kan godt bestå.
- Tallene er in-sample og allerede set. De afgør intet, men de forklarer, hvorfor testen
  stadig giver mening.

## 2. Hvad der testes

- **Strategien:** long MNQ 07:30–09:30 dansk tid (00:30–02:30 CT) efter en salgsdag, som i
  `b4_k6_overnight.md` §4. Koden er `research/b4_k6_overnight.py` som i in-sample-kørslen
  (kørt fra 583dfd9). Den må ikke ændres.
- **Nulmodellen:** N-nat (en tilfældig anden time samme nat, samme længde), R = 500.
- **Data:** NQ.v.0 1m, nætterne før XNYS-dagene 2024-01-02 → 2026-09-30.
  - Lokalt findes NQ til 2026-09-11. De sidste tre uger købes (estimat først, loft $2).
  - Åbnes kun gennem `load_holdout` med den frosne fil.

**In-sample-tallene for V2 · salg:** 902 nætter, netto $11,07 [−0,95; 23,09], p_FWE 0,044.
Det er den bedste af fire varianter, så den sande effekt ligger sandsynligvis lavere.

## 3. Styrken

Cirka 309 salgsnætter i 2024–2026 og σ cirka $190 pr. nat:

| sand netto $/nat pr. MNQ | styrke "timen er særlig" (mod N-nat) | styrke "netto > 0" |
|---|---|---|
| 11 (in-sample) | cirka 32–38% | cirka 26% |
| 5,5 (det halve) | cirka 13% | cirka 9% |

Testen kan altså kun bekræfte en effekt, der er mindst så stor som in-sample. Et negativt
udfald beviser ikke, at effekten er væk.

## 4. Beslutningsreglen (skitse, som ved kandidat 5 og 7)

| nr | udfald | handling |
|---|---|---|
| 1 | Timen er særlig (p ≤ 0,05) **og** netto > 0 (90%-nedre grænse > 0) | **Bekræftet.** Ruinmodellen på de faktiske nætter i disciplinzonen, derefter forward-test |
| 2 | Timen er særlig, netto ikke bevist, men middel > 0 | **Retningen er bekræftet.** Videre som række 1 med samme betingelser |
| 3 | Timen er særlig, middel netto ≤ 0 | **Parkeres:** timen er særlig, men betaler ikke |
| 4 | Alt andet | **Parkeres for godt:** driften efter salg er forsvundet, som forfatterne fandt for den ubetingede |

## 5. Spørgsmål til ejeren

Anbefalingen står først.

**1. Hvilken variant?**
- **A: kun V2 · salg.** Den var stærkest in-sample, holdt i 2021–2023 og er den version,
  artiklen fandt stærkest efter omkostninger. Én variant giver mest styrke.
- B: alle fire med korrektion. Det giver mindre styrke, og de ubetingede er sandsynligvis
  væk.

**2. Skal NQ fra før 2016 med?**
- **A: nej, kun 2024–2026 afgør.** Spørgsmålet er, om driften findes i dag. Data fra
  2010–2015 er fra før forfatternes fald og kunne få testen til at bestå på gamle data.
  Det fordobler styrken, men på det forkerte spørgsmål.
- B: ja, samlet med 2024–2026. Styrken bliver cirka 55%, men et bestået kan skyldes
  2010–2015.

**3. Omkostning**
- **A: $3,10 afgør.** Det er det målte spread om natten i 2025–2026. $2,85 rapporteres.
- B: $2,85 som in-sample.

**4. Skal holdout-natten beskyttes til senere kandidater?**
- **A: ja.** Rapporten viser kun V2 · salg og dens nulmodel, ikke "long hele natten" og
  ikke de andre vinduer. Så kan NQ-nætterne stadig bruges til en anden natidé, fx
  driften før optionsudløb (litteraturscanningen), med en note.
- B: nej, alle diagnoser som in-sample.
