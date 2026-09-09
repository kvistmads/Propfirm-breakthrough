# MLL-ruinmodel — Topstep $50K Trading Combine

Aabent spoergsmaal 1. Koert 2026-09-09. 20.000 stier pr. celle, horisont 200 handelsdage.
Alle sandsynligheder med Wilson-95%-interval. Netto = efter $2,472 pr. rundtur.

## Praeregistreret kriterium

> Vej 3 ("acceptér 5% pr. handel") forkastes hvis P(ruin foer profitmaal) > 50% ved
> WR 40%, 1 MNQ og 1-ATR-stop.

**Resultat: P(ruin) = 10.09% [9.7, 10.5]** (pessimistisk brudmodel 11.84% [11.4, 12.3]). P(bestaa) = 88.61% [88.2, 89.0].

**Kriteriet er ikke opfyldt. Vej 3 er ikke falsificeret.**

## Gitteret ved WR 40% (netto)

| kontrakter | stop_ATR | risiko_pr_handel_usd | risiko_pct_af_MLL | be_WR_pct | bestaa_pct | bestaa_CI_95 | ruin_pct_opt | ruin_pct_pess | uafgjort_pct | median_dage_til_bestaa |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.5 | 52.27 | 2.61 | 34.99 | 57.27 | [56.6, 58.0] | 1.11 | 1.31 | 41.61 | 141.0 |
| 1 | 0.75 | 77.16 | 3.86 | 34.44 | 86.02 | [85.5, 86.5] | 5.28 | 6.18 | 8.71 | 99.0 |
| 1 | 1.0 | 102.06 | 5.1 | 34.16 | 88.61 | [88.2, 89.0] | 10.09 | 11.84 | 1.3 | 69.0 |
| 2 | 0.5 | 104.53 | 5.23 | 34.99 | 82.53 | [82.0, 83.1] | 15.16 | 17.69 | 2.3 | 74.0 |
| 2 | 0.75 | 154.33 | 7.72 | 34.44 | 73.83 | [73.2, 74.4] | 26.13 | 30.46 | 0.04 | 40.0 |
| 2 | 1.0 | 204.12 | 10.21 | 34.16 | 67.65 | [67.0, 68.3] | 32.35 | 37.97 | 0.0 | 25.0 |
| 3 | 0.5 | 156.8 | 7.84 | 34.99 | 70.89 | [70.3, 71.5] | 29.09 | 33.2 | 0.03 | 41.0 |
| 3 | 0.75 | 231.49 | 11.57 | 34.44 | 63.03 | [62.4, 63.7] | 36.97 | 43.2 | 0.0 | 21.0 |
| 3 | 1.0 | 306.18 | 15.31 | 34.16 | 57.67 | [57.0, 58.4] | 42.33 | 50.28 | 0.0 | 14.0 |

## WR-foelsomhed, 1 kontrakt (netto)

| stop_ATR | antaget_WR_pct | edge_pp | bestaa_pct | ruin_pct_opt | uafgjort_pct |
|---|---|---|---|---|---|
| 0.5 | 34.0 | -0.99 | 1.44 | 41.49 | 57.08 |
| 0.5 | 37.0 | 2.01 | 15.85 | 9.67 | 74.48 |
| 0.5 | 40.0 | 5.01 | 57.27 | 1.11 | 41.61 |
| 0.5 | 45.0 | 10.01 | 98.53 | 0.0 | 1.48 |
| 0.75 | 34.0 | -0.44 | 10.69 | 63.85 | 25.45 |
| 0.75 | 37.0 | 2.56 | 47.23 | 24.53 | 28.24 |
| 0.75 | 40.0 | 5.56 | 86.02 | 5.28 | 8.71 |
| 0.75 | 45.0 | 10.56 | 99.72 | 0.2 | 0.08 |
| 1.0 | 34.0 | -0.16 | 21.27 | 72.08 | 6.65 |
| 1.0 | 37.0 | 2.84 | 59.38 | 34.55 | 6.07 |
| 1.0 | 40.0 | 5.84 | 88.61 | 10.09 | 1.3 |
| 1.0 | 45.0 | 10.84 | 99.08 | 0.9 | 0.01 |

## Brutto mod netto (WR 40%, optimistisk brudmodel)

| kontrakter | stop_ATR | bestaa_pct_brutto | bestaa_pct_netto | delta_pp | ruin_pct_brutto | ruin_pct_netto | delta_pp |
|---|---|---|---|---|---|---|---|
| 1 | 0.5 | 79.5 | 57.3 | -22.2 | 0.2 | 1.1 | +0.9 |
| 1 | 0.75 | 93.2 | 86.0 | -7.2 | 2.6 | 5.3 | +2.7 |
| 1 | 1.0 | 92.8 | 88.6 | -4.2 | 6.4 | 10.1 | +3.7 |
| 2 | 0.5 | 92.7 | 82.5 | -10.1 | 6.6 | 15.2 | +8.6 |
| 2 | 0.75 | 81.3 | 73.8 | -7.5 | 18.7 | 26.1 | +7.4 |
| 2 | 1.0 | 74.2 | 67.7 | -6.5 | 25.8 | 32.4 | +6.5 |
| 3 | 0.5 | 81.6 | 70.9 | -10.7 | 18.4 | 29.1 | +10.7 |
| 3 | 0.75 | 67.1 | 63.0 | -4.1 | 32.9 | 37.0 | +4.1 |
| 3 | 1.0 | 59.1 | 57.7 | -1.4 | 40.9 | 42.3 | +1.4 |

## Hvad modellen IKKE svarer paa

- **Hvordan win rate aendrer sig med stopbredden.** Modellen holder WR fast og varierer
  stoppet. I virkeligheden falder WR naar stoppet strammes. Vej 2 kan derfor ikke afgoeres
  her — det kraever maalte data.
- **Den funded konto.** Maalfunktionen der er implementeret er "naa $3.000 foer ruin",
  altsaa evalueringen. Konto-strategien har en anden maalfunktion (overlev og tag payouts)
  og kraever payout-reglerne verificeret foerst.
- **Vejen inde i en handel.** Derfor to brudmodeller frem for ét tal.
- **ATR paa andre timeframes end 15m.** Hele gitteret staar paa ATR_15m = 0,168%.

## Kilder

- help.topstep.com: Trading Combine Parameters, Maximum Loss Limit, Daily Loss Limit,
  Consistency Target, TopstepX Commissions and Fees (alle hentet 2026-09-09)
- cmegroup.com: Micro E-mini Nasdaq-100 contract specifications
- NQ-niveau 29.639,50 pr. 2026-09-07
