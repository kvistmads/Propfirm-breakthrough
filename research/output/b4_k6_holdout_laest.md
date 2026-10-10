# B4 kandidat 6 — holdout-testen af overnight drift, læst: række 4, parkeret for godt

**Skrevet:** 2026-10-10 af overblikssessionen, efter kørslen og læst sammen med ejeren.
Tallene står i `b4_k6_holdout.md` og `.csv` (commit 0a37449, kørt fra c4cf0c7). Intet er
kørt igen. Alle tal er i $ pr. nat pr. MNQ ved dagens niveau (NQ 29.138) og $3,10 pr.
round trip, medmindre andet står.

## 1. Kan vi stole på tallene?

| tjek | resultat |
|---|---|
| Rækkefølgen | præregistrering d4b4c4c → data, modul og tests c4cf0c7 → kørsel 0a37449 |
| Kodeændring efter trin 1 | ingen. Kørsel-commit'en indeholder kun rapporten og loggen |
| Holdout-loggen | én linje: 2026-10-10 20:59:42, `b4_k6_holdout.md`, NQ.v.0 |
| Beskyttelsen | kun V2 · salg og dens nulmodel er rapporteret |
| Data | 689 nætter, 1 udelukket (2025-11-28), ingen forsinkelser, ingen ruller i vinduet |

## 2. Afgørelsen efter §5: række 4

| serie | nætter | brutto $/nat | netto $/nat | CI90 netto $/nat | N-nat p50 $/nat | p_H1 |
|---|---|---|---|---|---|---|
| **holdout** 2024–2026 | 324 | 9,67 | **6,57** | [−9,56; 22,70] | 2,08 | **0,325** |
| in-sample 2016–2023 | 902 | 13,92 | 10,82 | [0,73; 20,90] | −1,97 | 0,020 |

- **H1 (timen er særlig): ikke bestået.** p 0,325.
- **H2 (netto): ikke bestået.** CI90-nedre −$9,56.
- **Række 4: kandidat 6 parkeres for godt.** Driften efter salgsdage holdt ikke efter 2023.

## 3. Hvad tallene viser

- **Punktestimatet er positivt, men det er én måned.**
  - Den bedste nat står for 67% af nettosummen.
  - Uden de 5 bedste nætter er netto −$5,73.
  - Uden april 2025 (toldchokket) er netto $0,99.
- **Timen er ikke længere særlig.** En tilfældig anden time samme nat gav i middel +$2,08 på
  holdout mod −$1,97 in-sample. Natten steg generelt, og vinduet slog den ikke.
- **Pr. år:** 2024 −$11,36, 2025 +$17,20, 2026 +$16,42. Alle intervaller krydser 0.
- **Profilen er den samme som in-sample:** hit ratio 51%, gevinst/tab 1,07, σ $176.
- **Det passer med forfatterne,** som skrev i 2026, at driften kl. 2–3 New York-tid har været
  cirka 0 siden 2021. Driften efter salgsdage holdt in-sample i 2021–2023, men ikke
  bagefter.
- **Styrken var lav** (cirka 26–38%). Et svagt positivt punktestimat kan stadig skjule en lille
  effekt, men den kan ikke skilles fra en tilfældig nattetime eller fra april 2025.

## 4. Hvad det betyder

- **Alle syv kandidater er nu parkeret.** Tre holdouts er brugt, og alle tre gav række 4.
- **Mønstret er det samme hver gang:** in-sample ser lovende ud, og holdout giver cirka 0, ofte
  med én urolig måned som den eneste gevinst.
- **Litteraturen siger det samme:** de kendte mønstre i indeksfutures er svundet ind efter
  publicering (litteraturscanningen).

## 5. Holdout-data, der nu er set

NQ-nætterne 2024–2026 er set for V2 · salg og for tilfældige 2-timersvinduer på salgsnætter
(nulmodellen). Andre vinduer, nætter uden salg og long hele natten er ikke rapporteret.
Holdout-regnskabet er opdateret.

## 6. Status

| emne | status |
|---|---|
| Kandidat 6 | **Parkeret for godt** 2026-10-10, holdout række 4 |
| Tælleren | 47 forsøg. Holdout tæller ikke |
| Databudget | $63,56 af $120 brugt |
| Næste | screening 3, som aftalt. Udformningen aftales med ejeren |
