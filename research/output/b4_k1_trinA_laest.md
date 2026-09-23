# B4 kandidat 1 — trin A, læst

> **RETTET 2026-09-23 efter motorrettelsen** (`research/output/b4_k1_motorrettelse.md`).
> To af læsningens påstande holdt ikke:
>
> | påstand nedenfor | virkelighed efter rettelsen |
> |---|---|
> | Fyldningsbarens skævhed er "formentlig lille" | **Stor.** Middel netto-R faldt 0,06-0,13 R. Overblikssessionens forventning var under 0,02 R — den tog fejl med en faktor 3-6 |
> | Kernen tjener lidt: 0,06-0,09 R | **Kernen taber lidt: −0,00 til −0,05 R** netto i alle 6 varianter |
> | Retesten holder 59-64% | **50-51%** — et møntkast |
>
> Årsagen: i tynde zoner er 2R mindre end et almindeligt 1m-udsving, så fyldningsbarens high lå
> over målet, *før* ordren blev fyldt. 23-41 handler i varianterne uden BE blev registreret som
> +2R i stedet for −1R. Trin A's afgørelse står som kørt, men N1 havde samme fejl og er ikke kørt
> igen. Om den rettede kerne ville have ramt bånd 4 (parkér), er derfor ukendt; trin 2 kører
> kerne og N1 med den rettede motor og svarer på det.

**Skrevet:** 2026-09-23 af overblikssessionen, **efter** kørslen, sammen med Mads. Det her
er læsningen, ikke præregistreringen. Tallene står i `b4_k1_trinA.md` og `.csv` (committet
i 29d34f6, kørt fra 29f3116). Alt nedenfor er regnet fra de filer; intet er kørt igen.

---

## 1. Afgørelsen, mekanisk

| størrelse | værdi |
|---|---|
| Bedste variant | buffer 0 / ingen BE |
| middel_R_netto, CI95 | 0,095 [0,010; 0,180] |
| p_FWE, Westfall-Young over 6 varianter, R = 500 | **0,15** |
| N1_middel_R_netto median / 5%-fraktil | 0,036 / −0,041 |

Ikke bånd 1 (middel under 0,20, p_FWE over 0,05). Ikke bånd 4 (middel over N1's
5%-fraktil). Punktestimatet ligger i bånd 3, og CI'et krydser N1's median ned i tillæggets
hul B. Handlingen er den samme uanset etiket: **trin 2 præregistreres med trin A som
grundlinje.** Tælleren står på N = 6 og nulstilles ikke.

**I klart sprog:** kernen tjener lidt. Tilfældigt placerede zoner af samme størrelse, under
præcis samme regler, tjener også lidt. Forskellen er ikke større end hvad held giver, når
man vælger den bedste af seks. **Der er intet bevis for at basislys-plus-udbrudslys gør
noget af sig selv.**

## 2. Hvad der er efterprøvet, og hvad der ikke holder

| punkt | status |
|---|---|
| Udfaldsandele summerer til 100; højst 1 handel pr. dag uden BE, 2 med | bestået |
| Regressionstjek mod optælling 2 | bestået, byte for byte |
| R er kontraktuafhængigt | bestået, i formel og kode |
| **N2** | **ubrugelig.** E forskydes, men stoppet — zonens kant — bliver stående. Forskydes E nedad i en demand-zone, skrumper risikoen mod nul eller bliver negativ, og omkostningen i R eksploderer. N2's −0,39 til −0,51 R er et artefakt af det. §5 sagde ikke at hele zonen skulle flyttes med; **det er overblikssessionens fejl i specifikationen**, ikke Code's. N2 indgår ikke i afgørelsen |
| **Fyldningsbaren** | **optimistisk skævhed.** `simuler_handel` tjekker mål og BE-trigger mod hele fyldnings-1m-barens high, også den del der lå før fyldningen. Det kræver en 1m-bar med et udsving over 2R, så det er sjældent, men hyppigst i de tynde zoner. N1 bruger samme funktion og har samme skævhed, så p_FWE er stort set upåvirket. Middel-R's niveau er overvurderet med et ukendt, formentlig lille beløb |
| **Strejf-diagnosen** | **ikke et faresignal**, selv om rapporten kalder den "ikke bestået". Der er kun 8-21 strejf mod 1.095-1.407 handler. De er udvalgt på fremtiden: prisen gik ikke én tick under E resten af baren, så de første op til 15 minutter er risikofri pr. definition. Selv hvis alle var blevet fyldt, ville middel-R højst stige med ca. 0,015 R. Fyldningsregel 1 koster næsten intet her |

## 3. Tallene

| buffer | BE | handler_n | middel_R_brutto | middel_R_netto | CI95_netto | win_rate_pct_netto | N1_middel_R_netto_p50 |
|---|---|---|---|---|---|---|---|
| 0% | ingen | 1.100 | 0,199 | **0,095** | [0,010; 0,180] | 37,9 | 0,036 |
| 0% | +1,0R | 1.407 | 0,185 | 0,085 | [0,022; 0,147] | 26,8 | 0,036 |
| 0% | +1,2R | 1.318 | 0,174 | 0,073 | [0,005; 0,141] | 29,3 | 0,034 |
| 10% | ingen | 1.095 | 0,155 | 0,060 | [−0,024; 0,144] | 35,4 | 0,016 |
| 10% | +1,0R | 1.375 | 0,161 | 0,069 | [0,006; 0,132] | 25,6 | 0,021 |
| 10% | +1,2R | 1.303 | 0,150 | 0,057 | [−0,011; 0,125] | 27,9 | 0,023 |

**Omkostningerne tager halvdelen.** Brutto 0,20 R, netto 0,09 R for den bedste variant.
Den gennemsnitlige omk_R på 0,10 ligger over medianen på 0,07, fordi den tynde hale — mest
2019 — koster op til 0,3 R pr. handel.

## 4. Mads' forventning: retesten holder 9 ud af 10

| mål | forventet | målt |
|---|---|---|
| holder: +1R nået før stoppet | ca. 90% | **59-64%** |
| vinder: +2R nået før stoppet | — | 37,9% [35,0; 40,8] |
| break-even win rate netto, ved median omk_R | — | 35,6% |

"Holder" aflæses i varianten BE +1,0R, buffer 0: mål 26,8% og BE-udgang 32,6% nåede begge
+1R; stop 36,3% gjorde ikke; tidsexit 4,3% er ukendt. Deraf 59,4-63,7%.

Det er den **ufiltrerede** kerne. Vennens 9 ud af 10 gælder zoner han selv udvælger, og det
afviser tallet ikke. Det viser at kernen alene ikke er dér.

+1R før −1R er et symmetrisk kapløb, hvor en ren tilfældig bevægelse giver 50%. 59-64%
ligger over det, men den rigtige sammenligning er N1's andel, og den er ikke regnet.

**Hvorfor BE ikke hjælper**, beskrivende: af de handler der når +1R, når 60-64% også +2R.
En ren tilfældig bevægelse fra +1R, med −1R og +2R som grænser, giver 67%. Efter +1R
opfører prisen sig altså højst som et møntkast, og så kan en BE-flytning hverken tilføje
eller fjerne noget i gennemsnit.

## 5. Retning, ikke zoner

| side | handler_n | middel_R_netto | CI95 |
|---|---|---|---|
| demand | 551 | 0,157 | [0,036; 0,278] |
| supply | 549 | 0,033 | [−0,088; 0,153] |
| **forskel** | | **0,124** | **ca. [−0,05; 0,30]** |

Forskellens CI krydser nul: **uafgjort.** Rapportens "demand bærer hele effekten" er for
stærkt.

Pr. år, buffer 0 / ingen BE:

| år | NQ's retning | demand_R_netto | supply_R_netto |
|---|---|---|---|
| 2019 (fra maj) | op | 0,03 | −0,28 |
| 2020 | op | 0,07 | −0,01 |
| 2021 | op | 0,22 | 0,13 |
| 2022 | **ned** | 0,12 | **0,20** |
| 2023 | op | 0,34 | 0,01 |

Den side der vinder, skifter med årets retning. I 2022 slår supply demand. Alle celler
krydser nul undtagen demand 2023, så **mønsteret er et hint, ikke et fund.** Det peger
mod markedsretning snarere end zonestruktur — præcis det N1 fanger, og det forklarer hvorfor
N1 også tjener penge.

**Det er samtidig en fælde for trin 2.** Filter 6, retning på højere timeframe, stod på
listen i `b4_hypoteser.md` før i dag. Nu har vi set et mønster der ligner det. Trin 2's
præregistrering skal derfor holde hele filterlisten og tælle alle kombinationer; den må
ikke snævres ind til de filtre dette mønster peger på.

## 6. De tre spørgsmål trin A skulle svare på

| spørgsmål | svar |
|---|---|
| Grundlinjen | middel_R_netto 0,06-0,09 R, ikke skelnelig fra N1's 0,02-0,04 R |
| Hjælper BE? | **Nej.** Forskellene er 0,01-0,02 R, langt inde i støjen. Uafgjort; ved buffer 0 er punktestimaterne let negative |
| Hjælper bufferen? | **Uafgjort.** Punktestimaterne favoriserer 0% — videoens egen kant — i alle tre BE-varianter med 0,016-0,035 R. Men de tre sammenligninger deler zoner og er næsten én sammenligning |

## 7. Forventningerne fra §9, holdt op mod udfaldet

| forventning | udfald |
|---|---|
| Kernen lander på eller lige under N1's median | over N1's median, men ikke skelnelig fra den. Rigtig i substansen |
| Retesten holder ca. 9 ud af 10 | 59-64% |
| BE hjælper ikke i gennemsnit | rigtig |
| Tidsexit 15-30% | **forkert:** 4-7% |

## 8. Rettelser til rapporten

- Rapporten siger at `b4_k1_trinA_laesning.md` er skrevet af overblikssessionen. **Det er
  forkert.** Code-sessionen skrev den selv (bekræftet af Mads); se noten øverst i den fil.
- Rapporten aflæser hul B på CI'ets nedre grænse. Hul B er defineret på punktestimatet.
  Konklusionen bliver den samme gennem §7's CI-klausul.
- Rapporten mangler "holder"-målet og CI på forskellen mellem demand og supply. Begge er
  regnet her ud fra `.csv`.

## 9. Før trin 2 kan præregistreres

Ikke forslag til strategien. Forudsætninger for at trin 2's tal kan troes:

1. **Fyldningsbaren:** mål og BE-trigger må ikke kunne rammes i fyldnings-1m-baren. Antallet
   af berørte handler i trin A tælles og rapporteres. Trin A's afgørelse står som kørt; trin
   2's grundlinje regnes med den rettede motor, og forskellen til trin A oplyses.
2. **N2** flytter hele zonen, så stopafstanden bevares.
3. **"Holder"** præregistreres som mål for både kernen og N1.
4. **Code:** `git add` kun med filnavne og kun på egne filer. Skriver aldrig i
   `research/prereg/` og aldrig i en anden sessions navn.
