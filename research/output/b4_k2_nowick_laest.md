# B4 kandidat 2 — Nowick, læst: kandidat 2 parkeres

**Skrevet:** 2026-10-07 af overblikssessionen, efter kørslen og læst sammen med ejeren.
Tallene står i `b4_k2_nowick.md` og `.csv` (commit 19039f4, kørt fra f053ece). Intet er
kørt igen.

## 1. Kan vi stole på tallene?

| tjek | resultat |
|---|---|
| Rækkefølgen af commits | præregistrering 0fc9d4f → kode c2de5e5 → optælling 7263fc6 → tillæg ef71355 → vinderrate f053ece → kørsel 19039f4 |
| Regressionstjek, §11.3 | OK. Hele testsuiten: 861 bestået, 6 sprunget over |
| Censurerede handler | 0 i alle varianter |
| Tvetydige minutter | 1–7 pr. variant. I bedste fald gælder samme række |
| Fyld ved berøring | samme række. Resultatet afhænger ikke af køplacering |
| Forældet tekst i rapporten | optællingsafsnittets "Code stopper" og kravet 301 i stedet for 302. Begge er afgjort i tillægget, og ingen af dem ændrer noget |

## 2. Afgørelsen efter §8: række 4, kandidat 2 parkeres

| variant | handler_n | middel_R_brutto | middel_R_netto | CI95_netto | maal_stop_tid_pct | N_alm_p50_R_netto | t_v |
|---|---|---|---|---|---|---|---|
| daily · 5 lys · 1R (hovedvariant) | 611 | −0,032 | −0,143 | [−0,222; −0,064] | 40 / 45 / 15 | −0,065 | −2,37 |
| bedste brutto: daily · 3 lys · 1R | 533 | −0,010 | −0,122 | [−0,207; −0,037] | 41 / 44 / 15 | −0,063 | −1,73 |
| værste: 4H · 3 lys · 2R | 559 | −0,090 | −0,197 | [−0,296; −0,097] | 16 / 54 / 30 | −0,084 | −2,73 |

- **Alle 12 varianter er negative netto, og alle konfidensintervaller ligger helt under
  nul.**
- Brutto ligger varianterne mellem −0,01 og −0,09 R.
- p_FWE er 1,000 for alle.

## 3. Det reelen påstod, mod det vi målte

| påstand | målt |
|---|---|
| 85% vinderrate ved cirka 1:1 | **Mål 40%, stop 45%, tidsexit 15%.** Andelen med R > 0 er cirka 50%. Stoppet rammes oftere end målet |
| Lys uden væge er særlige | **De er en smule ringere end almindelige lys under samme regler** (t_v fra −1,6 til −3,3) |
| Virker hver gang | Alle fem år er negative, undtagen 2021, som ligger omkring nul |

## 4. Hvad vi lærte — til de næste kandidater, ikke til at redde denne

- **To kandidater med samme mekanik har givet samme svar.** Kandidat 1 og 2 lagde begge
  en limitordre tilbage ved udspringet af et stærkt lys, i trendens retning, på MNQ.
  Retesten holder omkring halvdelen af gangene brutto og taber netto. Fremtidige kandidater
  med samme mekanik (order blocks, FVG-retests, supply/demand-retests) bør sorteres fra
  eller sammenlignes med disse to resultater, før de bygges.
- **Når prisen kommer tilbage til et urørt niveau, går den lidt oftere igennem end tilbage.**
  Det gælder både lys uden væge og kandidat 1's strukturbrud. Det ligner momentum på
  minutskala. Det er en iagttagelse fra in-sample-data, ikke et fund man kan bygge på.
- **5m med stop omkring 20 point er dyrt.** Omkostningen kostede cirka 0,11 R pr. handel.
  Ved 1:1 kræver det en vinderrate over cirka 55% blot for at gå i nul.
- **Long var lidt bedre end short** (0,05–0,14 R), men alle intervaller krydser nul, og
  begge sider er negative.
- **De 4–8 strejf** ville have tjent penge, hvis de var fyldt. De er for få til at betyde
  noget, og fyld ved berøring giver samme afgørelse.

## 5. Status

| emne | status |
|---|---|
| Kandidat 2 | **Parkeret** 2026-10-07 |
| Tælleren | 28 forsøg; følger med til næste kandidat |
| Holdout (2024 →) | uåbnet og ukøbt for MNQ |
| Tid fra video til afgørelse | én dag |
| Genbrugeligt | det samme som efter kandidat 1. Desuden daily- og 4H-lys med forskelsjustering ved rul, mål som parameter og en standardiseret Westfall-Young |
