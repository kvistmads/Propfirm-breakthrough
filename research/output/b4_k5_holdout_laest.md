# B4 kandidat 5 — holdout, læst: række 4, kandidat 5 parkeres

**Skrevet:** 2026-10-08 af overblikssessionen, efter kørslen og læst sammen med ejeren.
Tallene står i `b4_k5_holdout.md` og `.csv` (commit ea30391, kørt fra eb1189c). Intet er
kørt igen. Alle tal er i $ pr. dag pr. MNQ ved dagens niveau (NQ 29.138), medmindre andet
står.

## 1. Kan vi stole på tallene?

| tjek | resultat |
|---|---|
| Rækkefølgen af commits | præregistrering ef4af79 → data og kørsel eb1189c → kørsel ea30391 |
| Antal åbninger af holdout | én. Loggen har én linje: 2026-10-08 19:41:33 UTC, `b4_k5_holdout.md`, ef4af79, MNQ.v.0 |
| Kandidat 5's modul | uændret siden 9d4bd2e. Kørslen tjekker det, før holdout åbnes |
| Regressionstjek | OK før åbningen |
| Samme mekanik som in-sample | ja: 13 handler om dagen mod 12,7, samme spredning i handler pr. dag |
| Data | 689 dage, 0 udelukket, 0 manglende minutter i RTH og 0 ruller i RTH. De 7 dage, Databento markerede som "degraded", havde ingen huller i RTH |

## 2. Afgørelsen efter §5: række 4

| serie | dage | brutto $/dag | netto $/dag | CI90 netto $ | p_H1 |
|---|---|---|---|---|---|
| **holdout 2024–2026** | 689 | **3,65** | **−30,55** | [−59,68; −1,42] | **0,43** |
| in-sample 2019–2023 | 1.169 | 74,40 | 41,07 | [14,18; 67,96] | 0,002 |

- **H1 er ikke bestået** (p 0,43). VWAP-retningen er ikke bedre end tilfældig efter 2023.
- **H2 er ikke bestået.** Hele 90%-intervallet ligger under 0.
- **Række 4: kandidat 5 parkeres.**
- **E_f = −5,59** (in-sample og holdout samlet, 1.858 dage, middel $14,51). Betingelsen for
  en Combine er ikke opfyldt.

## 3. Hvad der skete

- **Bruttogevinsten forsvandt.** Den faldt fra $74 til $4 pr. dag, eller 95%. Pr. handel
  faldt den fra 1,0 til 0,05 bp. Handlerne og omkostningen er de samme, men retningen
  rammer ikke længere.
- **Faldet er ikke tilfældigt.** Forskellen i netto mellem in-sample og holdout er $72 pr.
  dag, med z cirka 3,0 og p cirka 0,003 (overblikssessionens beregning).
- **Alle tre år i holdout er negative:** 2024 −9,69, 2025 −52,18 og 2026 −29,75.
- **Tid på dagen:**

| halve time NY | holdout brutto $/dag | in-sample brutto $/dag |
|---|---|---|
| 9:30–10:30 | 20,60 | 22,83 |
| 10:30–12:00 | −3,36 | 24,22 |
| 15:00–16:00 | −13,59 | 27,35 |

  - Den første time ser ud som før.
  - Resten af formiddagen og især sidste time er vendt. Sidste time var artiklens og
    litteraturens stærkeste del.
  - **Det er en iagttagelse, ikke et fund.** Den er set på holdout og kan ikke testes på
    holdout igen.
- **Det passer med litteraturen om offentliggjorte mønstre:** McLean og Pontiff (2016)
  fandt, at afkastet fra publicerede anomalier i gennemsnit falder cirka 58% efter
  offentliggørelsen. Her faldt det 95%.
- **Risikoen var der stadig:** værste dag var −$2.504, og største tab inden for en dag var
  −$3.068 med 1 MNQ. Begge er over Topsteps MLL på $2.000.

## 4. Hvad metoden gjorde

- In-sample sagde "frys", fordi vi havde besluttet at frygte netop dette. Artiklens periode
  overlappede vores, og vi kaldte testen en gentagelse.
- Holdout blev købt for $3,55 og åbnet én gang. Den sagde nej, før der blev købt en Combine,
  bygget en bot eller sat penge på spil.
- **Vinderens forbandelse og offentliggørelsen** var de to risici, præregistreringen pegede
  på. Det var den anden, der slog igennem.

## 5. Holdout er nu brugt

- **Til VWAP og momentum inden for dagen er den ikke længere ren.** Vi har set tidsprofilen
  for 2024–2026. En ny hypotese om fx "kun første time" ville være valgt på holdout-data og
  kan ikke testes på dem.
- **Til hypoteser uden forbindelse** kan den stadig bruges. Det skal vurderes og skrives i
  hver præregistrering.
- **Rene data** for VWAP og intradag-momentum findes nu kun fremad, fra oktober 2026.

## 6. Status for B4

| kandidat | idé | afgørelse |
|---|---|---|
| 1 | supply og demand | parkeret i in-sample |
| 2 | Nowick, lys uden væge | parkeret i in-sample |
| 3 | vending efter åbningen | parkeret i in-sample |
| 4 | EMT, tilbage til VWAP | parkeret i in-sample |
| 5 | VWAP-trend (Zarattini og Aziz) | frosset i in-sample, **parkeret i holdout** |

| emne | status |
|---|---|
| Tælleren | 41 forsøg. Holdout-testen tæller ikke som forsøg |
| Holdout MNQ 2024-01-02 → 2026-09-30 | købt og åbnet én gang for kandidat 5 |
| Budget hos Databento | $36,84 af $120 brugt |
| Næste | aftales med ejeren. Ingen forslag før resultatet er læst |

## Kilder

- McLean & Pontiff (2016), *Does Academic Research Destroy Stock Return Predictability?*,
  Journal of Finance 71(1), 5–32.
