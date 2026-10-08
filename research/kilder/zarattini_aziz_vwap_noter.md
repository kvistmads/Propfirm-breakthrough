# Kilde: Zarattini & Aziz (2023), "Volume Weighted Average Price (VWAP) The Holy Grail for Day Trading Systems"

**Link:** https://ssrn.com/abstract=4631351 (26 sider, skrevet 13. november 2023, revideret
29. april 2025)
**Læst:** 2026-10-08 af overblikssessionen. Hele artiklen er læst. PDF'en ligger ikke i
repoet, fordi SSRN-licensen ikke tillader genbrug. Noterne her er en sammenfatning med egne
ord.
**Status:** et arbejdspapir, ikke fagfællebedømt. Forfatterne kalder det selv udforskende
og "ikke et fuldt udviklet handelssystem".

## Data

- QQQ og TQQQ, 1-minutsbarer med volumen, 2. januar 2018 – 28. september 2023.
- Data fra IQFeed og Interactive Brokers. Backtest i MATLAB.

## VWAP

`VWAP = Σ(HLC_t × Volume_t) / Σ Volume_t`, hvor HLC_t er gennemsnittet af high, low og close
i minut t. **Kun RTH-data:** VWAP regnes fra 9:30 ET og uden handel før og efter børsen.

## Reglerne (§3)

| emne | regel |
|---|---|
| Første handel | Vent til første 1m-lys efter 9:30 ET er lukket. Kl. 9:31:00 ET: ligger prisen over VWAP, gå long; ligger den under, gå short ved starten af næste lys |
| Exit og vending | Lukker et 1m-lys på den anden side af VWAP, lukkes positionen, og den vendes. Et kryds inde i lyset uden lukning udløser intet (s. 11) |
| Altid i markedet | Bortset fra første minut har systemet altid en position, long eller short. Det giver flere handler pr. dag (§3.2) |
| Dagens slut | Positionen lukkes til markedets lukkekurs kl. 16:00 ET. Ingen positioner natten over |
| Størrelse | 100% af kapitalen pr. handel uden gearing (QQQ). TQQQ giver 3x |
| Omkostning | $0,0005 pr. aktie i kommission, ingen slippage antaget (§3.4). Højere kommission kan skade strategien (fodnote 6) |
| Tidsramme | 1m. Forfatterne nævner, at den kan laves på 5m (s. 10) |

## Resultater (QQQ, efter kommission)

| mål | VWAP-strategien | køb og hold |
|---|---|---|
| Samlet afkast | 671% | 126% |
| Årligt afkast | 43% | 15% |
| Volatilitet | 18% | 25% |
| Sharpe | 2,1 | 0,7 |
| Største drawdown | 9,4% | 35,6% |
| Handler | 21.967 (cirka 15 pr. dag) | 1 |
| Hit ratio | 17% | — |
| Gevinst/tab-forhold | 5,67 | — |
| Værste dag | −5,1% | −12,3% |

- Alfa 38% om året (t > 5), beta ikke signifikant forskellig fra 0.
- Med SMA 9/20/100/200 i stedet for VWAP blev Sharpe 1,3, 0,5, 0,7 og 0,9. VWAP var bedst.

## Tid på dagen (§5)

Næsten hele gevinsten kom mellem 9:30 og 12:00 ET og i sidste time, 15:00–16:00 ET.
Midt på dagen var der ingen trend. Forfatterne foreslår, at en billigere udgave kunne
undlade at handle mellem 12 og 15. **Det er et fund i deres egne data.**

## Mekanismen, som forfatterne foreslår

Institutionelle handler mod VWAP som benchmark:
- Tidligt på dagen køber eller sælger de med det samme, hvis de forventer en trend. Det
  forstærker bevægelsen.
- Venter de på en bedre pris, og kommer den ikke, presses de til at handle i sidste time i
  VWAP's retning.

## Det er vigtigt for os

- **Prøven overlapper vores.** Artiklens periode er 2018–2023, vores in-sample er
  2019–2023. En test på MNQ i in-sample er derfor en **gentagelse** på et andet instrument
  med rigtige futures-omkostninger. Det er ikke en uafhængig bekræftelse.
- **Holdout er rent.** Vores holdout (2024 →) ligger efter artiklen (november 2023) og er
  dermed en ren test efter offentliggørelsen.
- **Omkostningen er næsten lige så stor som gevinsten pr. handel.**
  - 671% over 21.967 handler giver cirka ln(7,71) / 21.967 ≈ 0,93 basispunkter af
    positionens værdi pr. handel efter kommission.
  - På MNQ koster $2,627 pr. round trip cirka 0,9 bp ved NQ 15.000 og cirka 1,7 bp ved
    NQ 7.500.
  - Forventningen på 1m er derfor omkring break-even efter rigtige futures-omkostninger.
- **Risikoen pr. dag:** værste dag var −5,1% af positionens værdi. 1 MNQ er cirka $58.000
  ved NQ 29.000. Sizing på Topstep ($2.000 MLL) hører til ruinmodellen.
