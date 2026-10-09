# B4 — screening af mekanismer efter kandidat 1–5

**Skrevet:** 2026-10-08 af overblikssessionen, efter ejerens svar 1A og 2A.
- **1A:** screening af mekanismer, med overnight drift først.
- **2A:** handel uden for RTH er tilladt, så længe Topsteps regler overholdes.

**Formål:** finde den næste kandidat ud fra spørgsmålet "hvem er tvunget til at betale?" og
ikke ud fra et mønster i grafen. Ingen kandidat præregistreres, før ejeren har valgt.

---

## 1. Hvad kandidat 1–5 lærte os

- **Simple prismønstre på MNQ inden for RTH** gav brutto omkring 0 og netto tab
  (kandidat 1–4).
- **En publiceret edge kan forsvinde.** Kandidat 5 (VWAP-trend) gentog artiklen i
  2019–2023. Efter publiceringen, i 2024–2026, faldt bruttogevinsten 95%.
- **Omkostningen vejer mindre ved dagens kursniveau.** $2,627 er 0,45 bp ved NQ 29.138 mod
  1,75 bp ved NQ 7.500.
- **Holdout er brugt** til VWAP og momentum inden for RTH. Andre mekanismer kan stadig
  testes rent på den.

## 2. De fem filtre

| nr | filter | spørgsmål |
|---|---|---|
| F1 | Mekanisme | Hvem betaler, og hvorfor bliver de ved? Uden svar testes intet (PRD §4.1) |
| F2 | Topstep og MNQ | Kan den handles inden for én Topstep-dag (17:00 CT → fladt inden 15:10 CT) med MNQ? |
| F3 | Styrke | Er der handler nok til at se effekten? |
| F4 | Omkostning | Er gevinsten pr. handel klart større end cirka $2,6–3,1 pr. round trip? |
| F5 | Rene data | Findes der data, vi ikke har set? Og hvad siger beviserne efter publiceringen? |

## 3. Screeningen

| mekanisme | F1 | F2 | F3 | F4 | F5 | samlet |
|---|---|---|---|---|---|---|
| **A. Overnight drift ved Europas åbning** | ja: likviditet | ja | middel | ja ved dagens niveau | ja, men ukendt efter 2020 | **anbefales som kandidat 6** |
| B. Stop-kaskader ved runde tal (Osler) | ja: stop-ordrer | ja | høj | tvivlsom | kun FX 1996–98 | lav prioritet |
| C. Turn of the month | nej, ingen forklaring holder | ja, med heldagshold | middel | ja | ukendt efter 2005 | udelukket af F1 |
| D. Pre-FOMC drift | delvist | ja | for få (8 om året) | ja | forsvandt efter 2015 | udelukket |
| E. Momentum sidst på dagen | ja: afdækning | ja | høj | — | forsvundet i 0DTE-tiden, og holdout er brugt | udelukket |
| F. Natrange som kontekst for åbningen | delvist | ja | høj | — | åbningstimen er set i holdout | lav prioritet |

### A. Overnight drift ved Europas åbning — anbefales

**Kilde:** Boyarchenko, Larsen og Whelan, *The Overnight Drift*, Review of Financial
Studies 36(9), 2023. Første udgave var NY Fed Staff Report 917 fra marts 2020.

**Hvad de fandt** på S&P 500 E-mini-futures 1998–2020:
- Det største positive afkast i døgnet ligger **kl. 2–3 New York-tid**, når Europa åbner.
  Det svarer til **kl. 08–09 dansk tid**.
- Afkastet er cirka 3,7% om året, eller 1,48 bp pr. dag. Det var positivt i 20 af 23 år og
  holder efter korrektion for 24 timevinduer.
- **Afkastet er størst efter salg.** Hænger dagens lukning med en salgsubalance, vender
  markedet op om natten. Efter stigninger er effekten lille, og uden ubalance er den nul.
  Den er større, når VIX er høj.

| strategi i artiklen | Sharpe før omkostninger | Sharpe efter omkostninger |
|---|---|---|
| long kl. 2–3 | 1,1 | cirka −0,5 |
| long kl. 1:30–3:30 | 1,3 | cirka 0,3 |
| long kl. 1:30–3:30, kun efter en salgsubalance | 1,8 | cirka 1,1 |

**Hvem betaler (F1):** markedsmagerne har købt det, andre solgte i den amerikanske session.
De tager en lagerrisiko og skal have betaling for det. Når Europa åbner, kommer der nye
købere, og lageret afvikles. Det er betaling for at stille likviditet. Det er ikke et
mønster, nogen kan arbitrere væk uden at tage den samme risiko.

**Topstep (F2):** Topsteps dag starter kl. 17:00 CT (00:00 dansk tid). En position kl.
08–09 dansk tid er én dags handel og ikke en natposition. `STRATEGI_PROPFIRM.md` §3 siger
det samme. Vores egen regel om kun at handle i RTH er løftet for denne kandidat (svar 2A).

**Omkostning (F4), vores egen måling** (`spread_mnq_pr_blok.csv`):
- Spreadet kl. 2:00–3:00 New York-tid er 2,12–2,17 ticks. Det giver cirka **$2,84 pr.
  round trip**.
- Spreadet uden for RTH er steget til 2,44–2,58 ticks i 2025–2026, så en kørsel bør også
  vise resultatet ved cirka $3,10.
- Ved NQ 29.138 er $2,84 cirka 0,49 bp. Artiklens 1,48 bp pr. dag svarer til **cirka $8,6
  brutto pr. MNQ pr. nat**. Netto står der altså cirka en tredjedel mindre tilbage.
- For ES i 1998–2020 var en tick cirka 1 bp. **Det er grunden til, at artiklens
  ubetingede version tabte efter omkostninger, og at vores ikke nødvendigvis gør.**

**Styrke (F3), groft skøn ud fra artiklens Sharpe-tal** (det rigtige tal regnes i
optællingen):

| version | nætter, NQ 2016–2023 | forventet t brutto | forventet t netto |
|---|---|---|---|
| alle nætter | cirka 2.000 | cirka 3,1 | cirka 2,1 |
| kun efter salgsdage | cirka 1.000 | cirka 3,6 | cirka 3,0 |

**Rene data (F5):**
- NQ 1m døgndata 2010–2026 og MNQ 2019–2026 ligger i cachen, så der skal ikke købes noget.
- **Natten er aldrig set.** NQ-holdout 2024–2026 er uåbnet. MNQ-holdout er åbnet én gang,
  men kun RTH blev brugt.
- **Imod:** artiklen kom i 2020. Vi ved ikke, om effekten holdt bagefter. Vores in-sample
  2016–2023 dækker både før og efter, og holdout 2024–2026 ligger helt efter. Kandidat 5
  viste, hvad det kan betyde.

**Andre forbehold:**
- **Vi har ikke artiklens ordreubalance.** "Salgsdag" må erstattes af et prismål, fx et
  negativt afkast i RTH-dagen. Det er en svagere betingelse end artiklens.
- **Artiklen er på S&P 500, ikke Nasdaq.** Effekten kan være en anden på NQ.
- **Gevinsten pr. kontrakt er lille.** Den kan kun betale sig med flere kontrakter. Det
  afgør ruinmodellen.

### B. Stop-kaskader ved runde tal — lav prioritet

**Kilde:** Osler (NY Fed Staff Report 150, 2002), om valuta 1996–1998.

- **Mekanisme:** stop-ordrer samler sig lige over og under runde tal. Når de udløses,
  presser de prisen videre, og take-profit-ordrer på selve tallet giver vendinger.
- **Effekten var lille i valuta:**
  - Efter et kryds af et rundt tal var 15-minutters-bevægelsen 0,061% mod 0,054% efter et
    tilfældigt niveau. Forskellen er cirka 0,7 bp, altså i nærheden af vores omkostning på
    0,45 bp.
  - Vending ved runde tal skete i 59% af tilfældene mod 55% ved tilfældige niveauer.
- **Mod den:**
  - Ingen beviser på indeksfutures fundet.
  - 20 år gammel, og at jage stop er udbredt blandt algoritmer i dag.
  - Mange mulige niveauer og varianter giver mange forsøg.
- Ejeren har selv parkeret idéen "til senere". Den kan blive kandidat 7.

### C. Turn of the month — udelukket af F1

McConnell og Xu (2008) fandt, at afkastet i 1987–2005 lå på den sidste og de tre første
handelsdage i måneden: 0,14% mod −0,01% pr. dag.
- **Forfatterne fandt ingen forklaring, der holder.** Lønudbetaling, risiko og
  pengestrømme i fonde blev forkastet. Uden et svar på "hvem betaler" testes den ikke.
- Den kræver desuden lange positioner hele dagen med fuld eksponering mod MLL.

### D. Pre-FOMC drift — udelukket

Lucca og Moench (2015) fandt, at S&P steg i døgnet før Fed-møder.
- Kurov, Wolfe og Gilbert (2021) forlængede prøven til 2019: **driften forsvandt efter
  2015.**
- Med cirka 8 møder om året er der desuden for få handler.

### E. Momentum sidst på dagen — udelukket

Gao m.fl. (2018) og Baltussen m.fl. (2021) forklarer det med afdækning af optioner og
rebalancering.
- En måling på SPX fra 0DTE-tiden (2022–2026, ikke fagfællebedømt) finder, at den
  ubetingede effekt er væk. Den er kun til stede på de cirka 15% af dagene, hvor
  markedsmagerne er short gamma.
- Vores holdout viste det samme: sidste time gik fra +$27 til −$14 pr. dag.
- **Holdout er brugt til denne type hypoteser.**

### F. Natrange som kontekst for åbningen — lav prioritet

Ejerens egen parkerede idé (PRD §7). Den hører til familien af opening-range-breakouts.
- Den mest kendte artikel om det er af de samme forfattere som kandidat 5.
- Åbningstimen er set i holdout gennem kandidat 5, så den er ikke længere ren.

## 4. Spørgsmål til kandidat 6 — overnight drift

Anbefalingen står først.

**1. Tidsvindue**
- **A: 2:00–3:00 og 1:30–3:30 New York-tid som to varianter, som i artiklen.** Det er kl.
  08:00–09:00 og 07:30–09:30 dansk tid.
- B: kun 2:00–3:00.

**2. Betingelse**
- **A: alle nætter og kun nætter efter en salgsdag, som to varianter.** En salgsdag er en
  dag, hvor RTH-afkastet fra 08:30 til 15:00 CT er negativt. Det er vores erstatning for
  artiklens ordreubalance, som vi ikke har.
- B: kun alle nætter.
- Med 1A og 2A bliver det 4 varianter, og tælleren går fra 41 til 45.

**3. Data**
- **A: NQ 2016–2023 som hovedserie** (cirka 2.000 nætter), med MNQ 2019–2023 som kontrol.
  - NQ og MNQ har samme kurs, og volumen indgår ikke.
  - Holdout bagefter på MNQ 2024–2026. Det bliver anden åbning, men for en ny frossen
    hypotese.
- B: kun MNQ 2019–2023 (cirka 1.170 nætter, mindre styrke).

**4. Nulmodel**
- **A: samme dage og samme længde, men en tilfældig anden time om natten**, mellem 17:00 og
  08:30 CT og uden for vinduet. Den spørger, om Europas åbning er særlig.
  - Som forklaring: long hele natten fra 17:00 til 08:30 CT.
- B: tilfældig retning.

**5. Mål og afgørelse**
- **A: netto-dollar pr. nat pr. MNQ ved dagens niveau, med konfidensinterval over
  nætterne.** Den fryses kun ved p_FWE ≤ 0,05 og CI-nedre > 0, som i kandidat 5.
  - Diagnoser: før og efter marts 2020 (artiklen), nominelt, pr. år og ved $3,10.

**6. Stop**
- **A: intet stop i testen, kun tidsexit, som i artiklen.** Halerisikoen i timen
  rapporteres. Størrelse og et eventuelt nødstop afgøres i ruinmodellen.
- B: et nødstop i testen.

## Kilder

- Boyarchenko, Larsen & Whelan (2023), *The Overnight Drift*, Review of Financial Studies
  36(9), 3502–3547 — https://ideas.repec.org/a/oup/rfinst/v36y2023i9p3502-3547..html
- NY Fed Staff Report 917 (2020), *The Overnight Drift* —
  https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf
- Osler (2002), *Stop-Loss Orders and Price Cascades in Currency Markets*, NY Fed Staff
  Report 150 — https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.html
- McConnell & Xu (2008), *Equity Returns at the Turn of the Month*, Financial Analysts
  Journal 64(2) — https://ideas.repec.org/a/taf/ufajxx/v64y2008i2p49-64.html
- Kurov, Wolfe & Gilbert (2021), *The Disappearing Pre-FOMC Announcement Drift*, Finance
  Research Letters 40 — https://ideas.repec.org/a/eee/finlet/v40y2021ics1544612320315956.html
- Måling af intradag-momentum i 0DTE-tiden (ikke fagfællebedømt) —
  https://dev.to/firmtape/intraday-momentum-is-dead-in-the-0dte-era-we-measured-it-on-1085-spx-sessions-43g0
- Elm Wealth (2022), *Night Moves* — https://elmwealth.com/night-moves-overnight-drift/
- McLean & Pontiff (2016), *Does Academic Research Destroy Stock Return Predictability?*,
  Journal of Finance 71(1)
