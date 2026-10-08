# B4 kandidat 5 — VWAP-trend, læst: række 1, "1m · uden middag" fryses

**Skrevet:** 2026-10-08 af overblikssessionen, efter kørslen og læst sammen med ejeren.
Tallene står i `b4_k5_vwap_trend.md` og `.csv` (commit aaa87bd, kørt fra 9d4bd2e). Intet
er kørt igen. Tallene nedenfor er i $ pr. dag pr. MNQ ved dagens niveau (NQ 29.138),
medmindre andet står.

## 1. Kan vi stole på tallene?

| tjek | resultat |
|---|---|
| Rækkefølgen af commits | præregistrering 1a515ea → kode 7506775 → optælling 4f43209 → tillæg 053e48b → tillæggets kodeændringer 9d4bd2e → kørsel aaa87bd |
| Kodeændring efter optællingen | kun tillæggets to: ny række 2 i `beslutning` og diagnosen for de udelukkede dage, med tests. Kontrolleret i diff'en |
| Regressionstjek | OK. Hele testsuiten: 1.106 bestået, 6 sprunget over |
| Optællingen efter kodeændringen | CSV'en er byte for byte uændret |
| Uafhængigt krydstjek | Code's separate simulator, der går bar for bar, gav samme handler på alle 1.169 dage i alle 4 varianter |
| Handler pr. dag mod artiklen | 1m · hele dagen: 16,4 mod artiklens cirka 15. Hit ratio 17,5% og gevinst/tab 5,38 mod artiklens 17% og 5,67 |

Reglerne er bygget som i artiklen, og den rækkefølge, metoden kræver, er overholdt.

## 2. Afgørelsen efter §8: række 1

| variant | handler_n | brutto $/dag | netto $/dag | CI95 netto $ | N-retning p50 $ | t_v | p_FWE |
|---|---|---|---|---|---|---|---|
| 1m · hele dagen | 19.151 | 81,95 | 38,92 | [−0,30; 78,14] | −44,1 | 3,85 | 0,0020 |
| **1m · uden middag** | 14.831 | 74,40 | **41,07** | **[9,02; 73,12]** | −32,7 | 4,26 | **0,0020** |
| 5m · hele dagen | 8.734 | 43,60 | 23,98 | [−14,44; 62,39] | −17,7 | 2,08 | 0,0559 |
| 5m · uden middag | 7.387 | 38,40 | 21,80 | [−10,04; 53,65] | −16,0 | 2,30 | 0,0299 |

- **Kun "1m · uden middag" har både p_FWE ≤ 0,05 og CI-nedre > 0. Den fryses**, præcis som
  præregistreret i §4 med tillæg: 1m-lys, VWAP fra 08:30 CT, vending ved hver lukning på den
  anden side, pause 11:00–14:00 CT, fladt 14:55 CT og $2,627 pr. round trip.
- **VWAP-retningen bærer klart.** Begge 1m-varianter slår nulmodellen med t omkring 4.
  p_FWE = 0,0020 er det laveste, 500 gentagelser kan give.
- **Brutto gentager artiklen:** 0,86–1,01 bp pr. handel og 14,1 bp pr. dag på 1m · hele
  dagen. Artiklen havde cirka 0,93 bp og 14,1 bp.
- **Gevinsten kom på de tider, artiklen fandt:** kl. 9:30–11:30 New York-tid (cirka $44 pr.
  dag) og kl. 15:00–16:00 (cirka $27). Midt på dagen ligger brutto omkring 0. Derfor
  klarer pausen sig bedst: den sparer $10 om dagen i omkostning og mister kun lidt brutto.

## 3. Hvor solidt er det?

| prøve | 1m · uden middag | holder? |
|---|---|---|
| CI-nedre ved $2,627 | +9,02 | ja |
| CI-nedre ved $3,169 (kandidat 1–4's slippage) | +2,01 | ja, med lille margen |
| CI-nedre korrigeret for 4 varianter (Šidák, tosidet), overblikssessionens beregning | +0,32 | lige akkurat |
| Break-even-omkostning pr. handel, middel / CI | $5,86 / $3,32 | margen $0,70 pr. handel over $2,627 |
| Nominelt, ved det historiske niveau | −2,64 [−16,44; 11,16] | **nej**, omkring 0 |
| Pr. år | 2019 −1,65 · 2020 +86,89 · 2021 +52,67 · 2022 +64,38 · 2023 −11,12 | 3 af 5 år positive |
| Altid-long (drift) | 14,44 [−25,72; 54,59] | drift forklarer det ikke |
| Long mod short, brutto pr. handel | +0,43 [−4,67; 5,53] | ingen skævhed |
| Circuit breaker-dagene i marts 2020 (ikke med i testen) | +1.146, +1.254, +2.927, −357 | trenddage hjælper |

**Hvad det betyder:**
- **At VWAP-retningen virker, er solidt.** Det holder på tværs af varianter og efter
  korrektion. Det holder også mod de 41 forsøg, vi har brugt i alt.
- **At den tjener penge efter omkostning, er tyndt.** Det holder ved dagens niveau og ved
  den dyrere slippage. Korrigeret for 4 varianter er det lige akkurat. Nominelt, ved de
  priser vi faktisk havde dengang, ligger det omkring 0.
- **Gevinsten kommer fra de volatile år** (2020 og 2022) og fra få store dage: de 5% bedste
  dage står for 167% af den samlede gevinst. Resten af dagene taber samlet set lidt. Sådan
  ser en trendstrategi ud.
- **2023, sidste år i in-sample, er negativt** i alle 4 varianter.

## 4. Hvad testen ikke viser

- **Det er en gentagelse, ikke en uafhængig bekræftelse.** Artiklen dækker QQQ 2018–2023,
  og vi har testet samme indeks i samme periode. Den rene test er holdout (2024 →), som
  ligger efter artiklen.
- **Om den kan bestå en Combine.** Det afgør ruinmodellen. Tallene, den skal arbejde med:
  - Med 1 MNQ tager $3.000 cirka 73 handelsdage ved $41 pr. dag.
  - Dagens spredning er cirka $560 med 1 MNQ. Største tab inden for en dag var $2.830, og
    1% af dagene tabte $1.842 eller mere. **Topsteps MLL er $2.000**, og 1 MNQ er den
    mindste størrelse. Det kan blive det afgørende problem.
  - Konsistensreglen er ikke et problem: bedste dag er 5% af den samlede gevinst, langt
    under 55%.
- **De sidste 5 minutter** (14:55–15:00 CT) ville have givet $6,99 [1,65; 12,33] brutto om
  dagen. Det er prisen for bufferen før Topsteps fladning. Den frosne regel er uændret.
  En ændring nu ville være at tilpasse reglen til de data, den er testet på.

## 5. Næste skridt efter §8 række 1

1. **Præregistrering af holdout-testen**, før data købes. Holdout (2024-01 → i dag) er
   cirka 690 handelsdage:
   - Om VWAP-retningen slår nulmodellen, kan den se med cirka 97% styrke.
   - Om nettogevinsten på $41 pr. dag er over 0, kan den kun se med cirka 49–61% styrke,
     afhængigt af om testen er tosidet eller énsidet.
   - Det skal præregistreringen tage stilling til. Ellers kan en rigtig edge dumpe på
     uheld.
2. **Køb af holdout-data** (MNQ 1m fra 2024). Det kræver ejerens godkendelse af prisen.
   Data åbnes kun til den præregistrerede kørsel.
3. **Ruinmodel for daglig P&L**, med egen præregistrering. Den nuværende ruinmodel bygger
   på R og RR 2:1 og passer ikke til en strategi uden stop.

## 6. Status

| emne | status |
|---|---|
| Kandidat 5 | **Frosset** 2026-10-08: 1m · uden middag |
| Tælleren | 41 forsøg |
| Holdout (2024 →) | uåbnet og ukøbt for MNQ |
| Næste | holdout-præregistrering, køb af data og ruinmodel for daglig P&L |
