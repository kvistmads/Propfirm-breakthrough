# B4 kandidat 3 — vending efter åbningen, læst: kandidat 3 parkeres

**Skrevet:** 2026-10-08 af overblikssessionen, efter kørslen og læst sammen med ejeren.
Tallene står i `b4_k3_vending.md` og `.csv` (commit 77f7621, kørt fra 1dfcbd8 = tillæg
oven på 6f5d4ad). Intet er kørt igen.

## 1. Kan vi stole på tallene?

| tjek | resultat |
|---|---|
| Rækkefølgen af commits | præregistrering 73e9b26 → kode 7b8487d → optælling 6f5d4ad → tillæg 1dfcbd8 → kørsel 77f7621 |
| Koden siden optællingen | uændret. Kørslen tilføjede kun rapporten |
| Regressionstjek, §11.3 | OK |
| Censurerede handler | 0 |
| Tvetydige minutter | 2, kun ved k = 2,0. I bedste fald gælder samme række |

## 2. Afgørelsen efter §8: række 4, kandidat 3 parkeres

| variant | handler_n | middel_R_brutto | middel_R_netto | CI95_netto | win_rate_pct_netto | maal_stop_tid_pct | N_tid_p50_R_netto | t_v | p_FWE |
|---|---|---|---|---|---|---|---|---|---|
| k = 1,0 | 1.168 | −0,012 | −0,071 | [−0,142; −0,001] | 39,7 | 40 / 60 / 0 | −0,080 | 0,40 | 0,70 |
| k = 1,5 | 1.154 | +0,015 | −0,051 | [−0,122; +0,020] | 40,8 | 41 / 59 / 0 | −0,096 | 1,37 | 0,25 |
| k = 2,0 | 688 | +0,012 | −0,062 | [−0,154; +0,031] | 40,7 | 41 / 59 / 0 | −0,045 | −0,41 | 0,97 |

- **Brutto ligger modellen omkring nul.** Med 40% vinderrate ved 1,5R er det præcis
  break-even.
- **Netto taber den cirka 0,05–0,07 R pr. handel,** og det er omkostningen.
- **Volatilitetslyset slår ikke et tilfældigt tidspunkt** (p_FWE 0,25–0,97).

## 3. Vending eller fortsættelse (N-med)

| variant | N_med_middel_R_netto | forskel_N_med_minus_model [Welch-CI95] |
|---|---|---|
| k = 1,0 | −0,083 | −0,012 [−0,111; +0,088] |
| k = 1,5 | −0,011 | +0,040 [−0,061; +0,141] |
| k = 2,0 | −0,065 | −0,004 [−0,137; +0,129] |

**Vending og fortsættelse er lige gode, og begge ligger brutto omkring nul.** Det mønster,
videoen beskriver, kan ikke skelnes fra en mønt mellem 10 og 12.

## 4. Hvad vi lærte — til de næste kandidater, ikke til at redde denne

- **Tre kandidater, samme billede:** brutto omkring nul, netto negativ med omkostningen.

  | kandidat | mekanik | brutto R pr. handel | netto R pr. handel |
  |---|---|---|---|
  | 1 | Retest af en zone, limitordre | omkring 0 | negativ |
  | 2 | Retest af et lys uden væge, limitordre | −0,01 til −0,09 | −0,12 til −0,20 |
  | 3 | Udbrud mod åbningen, markedsordre | −0,01 til +0,02 | −0,05 til −0,07 |

  Simple prismønstre på MNQ inden for dagen giver ikke noget brutto. En ny kandidat skal
  have en grund til at tro på et bruttoafkast, der er større end cirka 0,05–0,10 R, før den
  er værd at bygge.
- **Overnatafkastet** (kun beskrivende): efter en negativ nat ligger modellen på cirka 0
  netto, efter en positiv nat på −0,08 til −0,13. Det peger samme vej som Li (2021), hvor
  vendingen ved åbningen især kommer efter negative nætter. Det er ikke en edge, for 0
  netto er ikke et overskud. Det er et in-sample-fund, som ikke må bruges uden ny
  præregistrering og fuldt N.
- **Omkostningen afgør** med stop på 20–27 point: cirka 0,05–0,06 R i median. Den er
  lavere end på 5m, men stadig hele forskellen mellem nul og tab.
- **Videoens "fundet på 10 minutter"** passer med geometrien, ikke med en edge: 25 point
  stop mod 37 point mål består cirka 40% af gangene uden nogen edge.

## 5. Status

| emne | status |
|---|---|
| Kandidat 3 | **Parkeret** 2026-10-08 |
| Tælleren | 31 forsøg; følger med til næste kandidat |
| Holdout (2024 →) | uåbnet og ukøbt for MNQ |
| Tid fra video til afgørelse | cirka et døgn |
