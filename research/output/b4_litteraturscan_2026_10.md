# B4 — litteraturscanning oktober 2026: nye papers og tegn på forfald

**Skrevet:** 2026-10-10 af overblikssessionen, efter ejerens ønske om at søge på SSRN efter
de nyeste papers med små edges, der kan lægges sammen.
**Status:** råmateriale til screening 3. **Ikke verificeret.** Tallene kommer fra
automatiske resuméer af forfatternes egne versioner (NBER, Fed, arXiv, forfattersider).
SSRN blokerede direkte læsning. Hvert tal skal tjekkes i PDF'en, før det bruges i en
præregistrering.

## 1. Hovedfundet: litteraturen dokumenterer selv forfaldet

| kilde | hvad den viser | betydning for os |
|---|---|---|
| Boyarchenko, Larsen og Whelan, "The Disappearing Overnight Drift" (NY Fed-blog, 2026) | Driften kl. 2–3 New York-tid har været cirka 0 siden 2021, mod cirka 3,7% om året før | Forklarer, at den ubetingede natdrift er væk hos os. Driften efter salgsdage holdt in-sample i 2021–2023 |
| Kurth, Eisler, Rej og Bouchaud, "Is Trend Still Your Friend?" (arXiv, juli 2026) | Kortsigtet trend i indeks- og valutafutures døde efter 2009, mest i kontrakter med små ticks som MES og MNQ | Passer med, at kandidat 5 (VWAP-trend) faldt på holdout |
| Song, "Pre-FOMC Uncertainty Accumulation" (sept. 2026) | Driften før FOMC inden for dagen forsvandt efter 2016, da optioner med onsdagsudløb kom. Kun natgabet før mødet er tilbage | Kun natdelen er værd at se på |
| Mesfin, MNQ-studie (arXiv, maj 2026, uafhængig forfatter) | 14 signalfamilier på 5m-barer i MNQ 2021–2025. Ingen slog omkostningen | Støtter vores resultater med kandidat 1–4 |

## 2. Kandidater med en tvungen betaler og en fast kalender

| # | paper | handel | vindue (CT) | brutto bp pr. handel | handler pr. år | status | foreløbig vurdering |
|---|---|---|---|---|---|---|---|
| A | Baltussen, Terstegge og Whelan, "The Derivative Payoff Bias" (RFS, revision) | MES/MNQ | torsdag 17:00 → fredag 08:30 long ved månedligt optionsudløb, fredag 08:30 → cirka 11:00 short | ES +14 nat og −13 fredag. NQ cirka +14 og så vending | cirka 12 | arbejdspapir | middel–høj. En praktiker fandt ES svækket efter 2023, NQ uafklaret |
| B | Hartzmark og Solomon, "Market-Wide Predictable Price Pressure" (AER 2025) | MES | dagen før og på dage med store udbytteudbetalinger | +7 (øverste kvartil), +12 (top 10) | 10–63 | fagfællebedømt | middel–høj. Kun long, så delvis bare markedets afkast. Kræver udbyttedata |
| C | Song (sept. 2026) | MES | 17:00 dagen før FOMC → 08:30 FOMC-dagen | cirka +19 (2016–2023) | 8 | arbejdspapir | middel |
| D | Pan og Peng (juni 2026) | signal til C | obligationsrenten natten før FOMC | 1 bp rentefald → +1,7 bp i S&P | 8 | arbejdspapir | middel–lav, kun som filter til C |

**Lavere:** valutafixing for M6E (cirka 2,5 bp pr. ben, cirka lig omkostningen, svækket
efter 2013), døgnmønstre i EUR/USD, vending efter FOMC i valuta, kryptoweekend før Nasdaq
mandag, 0DTE-gamma som filter, EIA-dage i olie, overnight-mod-dag-vending på tværs af
futures.

**Ikke læst, kun titlen fundet:** fire nye single-author-papers på SSRN om bl.a. Dow-futures
efter 0DTE, guld og sølv fordelt på sessioner og regimeskift i Nasdaq-futures.

## 3. Hvad det betyder for idéen om mange små edges

- **De overlevende kandidater er sjældne begivenheder:** 8–63 handler om året hver. Alene
  har hver især lav styrke. A har fx cirka 96 begivenheder i 2016–2023.
- **De ligger på forskellige dage** (optionsudløb, udbyttedage, FOMC), så de burde være
  næsten ukorrelerede. Det er netop ejerens idé om at lægge små edges sammen.
- **Styrken skal regnes for porteføljen**, ikke kun for hver enkelt, hvis de skal testes
  samlet. Det er et designspørgsmål til screening 3.
- **Data:** ES og MNQ i 2024–2026 er delvist set (holdout-regnskabet). Dage med optionsudløb,
  udbytte og FOMC er ikke set hver for sig.

## Kilder

- Boyarchenko, Larsen & Whelan, "The Disappearing Overnight Drift", Liberty Street
  Economics (2026). Den oprindelige blogpost fra 2021:
  https://libertystreeteconomics.newyorkfed.org/2021/05/the-overnight-drift-in-us-equity-returns
- Baltussen, Terstegge & Whelan, "The Derivative Payoff Bias" —
  https://afajof.org/management/viewp.php?n=98196
- Hartzmark & Solomon, "Market-Wide Predictable Price Pressure", AER 115(9), 2025 —
  doi 10.1257/aer.20231725
- Song, "Pre-FOMC Uncertainty Accumulation: Evidence from 0DTE Options" —
  https://afajof.org/management/viewp.php?n=260400
- Pan & Peng, "The Pre-FOMC Drift in Long-Term Treasury Bonds" —
  https://en.saif.sjtu.edu.cn/junpan/FOMC_new.pdf
- Kurth, Eisler, Rej & Bouchaud, "Is Trend Still Your Friend?", arXiv 2607.01550
- Mesfin, "Structural Limits of OHLCV-Based Intraday Signals in MNQ Futures", arXiv
  2605.04004
