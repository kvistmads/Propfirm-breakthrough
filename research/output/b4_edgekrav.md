# B4 — edge-kravet: resultat

**Kørt:** 2026-10-09 fra commit `e3d0b77619456716960092dd82897403d053679a`
(præregistrering `research/prereg/b4_edgekrav.md` og tillæg
`research/prereg/b4_edgekrav_tillaeg.md`). 20.000 stier pr. celle, 11 Sharpes × 100
størrelser pr. gitter. Valget af størrelse sker på stierne med frø 20261009; tallene i
tabellerne er de valgte celler regnet igen på 20.000 nye stier med frø 20261010
(tillægget §3.1). Ingen kursdata, intet fra holdout, intet tæller i tælleren (45).
Kørselstider: hoved 11,0 min, normal 10,9 min, t3 10,5 min, uden_dll 13,2 min, uden_intradag 9,2 min, horisont_126 6,7 min, plan_95 13,3 min.

## 1. Kravet

| variant | S_min_EV (punkt) | S_min_EV (nedre 95% > 0) | S_min_EV disciplinzone | S_hurtig (bedste EV-størrelse) | S_hurtig (størrelse maks. P) | S_min_EV på valgstierne | EV > 0 ved S = 0 | §6-række |
|---|---|---|---|---|---|---|---|---|
| Hovedmodel (t4, DLL, intradag, 252 dage, $49-plan) | **≤ -0,50 (allerede i første gitterpunkt)** | ≤ -0,50 (allerede i første gitterpunkt) | 0,16 | 1,03 | 0,28 | ≤ -0,50 (allerede i første gitterpunkt) | ja | 1 |
| Normalfordelt Z | **≤ -0,50 (allerede i første gitterpunkt)** | ≤ -0,50 (allerede i første gitterpunkt) | 0,14 | 0,91 | ≤ -0,50 (allerede i første gitterpunkt) | ≤ -0,50 (allerede i første gitterpunkt) | ja | 1 |
| Student-t, 3 frihedsgrader | **-0,35** | -0,33 | 0,25 | 0,98 | 0,74 | -0,35 | ja | 1 |
| DLL slået fra (loft $2.000) | **≤ -0,50 (allerede i første gitterpunkt)** | ≤ -0,50 (allerede i første gitterpunkt) | 0,22 | 0,92 | -0,15 | ≤ -0,50 (allerede i første gitterpunkt) | ja | 1 |
| Ingen bevægelse inden for dagen | **≤ -0,50 (allerede i første gitterpunkt)** | ≤ -0,50 (allerede i første gitterpunkt) | -0,17 | -0,33 | -0,38 | ≤ -0,50 (allerede i første gitterpunkt) | ja | 1 |
| Horisont 126 dage | **-0,48** | -0,45 | 0,41 | 1,03 | 0,28 | -0,48 | ja | 1 |
| $95-planen uden aktivering | **-0,32** | -0,29 | 0,44 | 1,12 | 0,28 | -0,29 | ja | 1 |

S-værdierne er interpoleret lineært mellem gitterpunkterne (−0,5; 0; 0,25; 0,5; 0,75; 1,0;
1,25; 1,5; 2,0; 2,5; 3,0). "Nedre 95% > 0" er det sted, hvor intervallets nedre grænse for
forventet nettoværdi ved den bedste størrelse krydser 0. Kolonnen "på valgstierne" er
S_min_EV regnet på de stier, størrelsen blev valgt på — til sammenligning; den afgør intet.

## 2. §6 anvendt mekanisk

Hovedmodellen, punktestimatet: **S_min_EV = ≤ -0,50 (allerede i første gitterpunkt)** → **række 1**.

Række 1: S_min_EV ≤ 0,75. Svage edges kan betale sig. Næste skridt efter §6: præregistrering af en holdout-test af overnight drift (NQ 2024–2026 er uåbnet for natten) og en søgning efter svage edges, der kan supplere.

Forventet nettoværdi positiv allerede ved Sharpe 0: **ja**.
Det betyder, at regelgeometrien alene giver plus ved den bedste størrelse, og det skal læses sammen med Topsteps regler om adfærd (§6). Det ændrer ikke rækken.

## 3. Kurven ved den bedste størrelse (hovedmodellen)

| Sharpe | σ_C | σ_X | bestå ≤63 | ≤126 | ≤252 | median dage | resets | udbet. ≤63 | ≤252 | til ejer | gebyrer | **EV netto [95%]** | P(netto>0) | p10 | XFA ikke udbetalt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| -0,50 | $800 | $800 | 68% | 90% | 99% | 41 | 17,14 | 24% | 74% | $2.038 | $1.873 | **$165** [$127; $202] | 36% | −$1.944 | $148 |
| 0,00 | $800 | $800 | 74% | 94% | 100% | 35 | 15,09 | 31% | 84% | $2.891 | $1.871 | **$1.020** [$973; $1.067] | 48% | −$1.846 | $201 |
| 0,25 | $1.000 | $800 | 80% | 96% | 100% | 29 | 19,00 | 38% | 89% | $3.708 | $2.146 | **$1.562** [$1.507; $1.617] | 54% | −$1.993 | $259 |
| 0,50 | $1.000 | $800 | 82% | 97% | 100% | 27 | 17,81 | 42% | 92% | $4.367 | $2.130 | **$2.238** [$2.177; $2.299] | 61% | −$1.846 | $297 |
| 0,75 | $1.000 | $800 | 85% | 98% | 100% | 25 | 16,66 | 46% | 94% | $5.117 | $2.112 | **$3.005** [$2.938; $3.072] | 67% | −$1.635 | $348 |
| 1,00 | $1.000 | $800 | 87% | 98% | 100% | 24 | 15,54 | 49% | 96% | $5.989 | $2.095 | **$3.894** [$3.819; $3.968] | 74% | −$1.398 | $401 |
| 1,25 | $1.000 | $800 | 89% | 99% | 100% | 22 | 14,44 | 54% | 97% | $6.961 | $2.072 | **$4.889** [$4.807; $4.971] | 79% | −$1.091 | $465 |
| 1,50 | $1.000 | $800 | 91% | 99% | 100% | 21 | 13,40 | 58% | 98% | $8.093 | $2.048 | **$6.045** [$5.955; $6.135] | 84% | −$742 | $526 |
| 2,00 | $1.000 | $800 | 94% | 99% | 100% | 19 | 11,37 | 66% | 99% | $10.762 | $1.985 | **$8.777** [$8.670; $8.884] | 91% | $253 | $687 |
| 2,50 | $1.000 | $800 | 96% | 100% | 100% | 17 | 9,52 | 73% | 100% | $14.037 | $1.904 | **$12.133** [$12.009; $12.258] | 96% | $1.822 | $890 |
| 3,00 | $1.000 | $1.000 | 97% | 100% | 100% | 15 | 8,71 | 72% | 100% | $18.436 | $1.989 | **$16.447** [$16.287; $16.608] | 97% | $2.933 | $1.167 |

"XFA ikke udbetalt" er diagnosen fra tillægget §2.4: forventet positiv XFA-saldo ved
horisonten. Den indgår ikke i nettoværdien.

## 4. Kurven i disciplinzonen (σ_C og σ_X ≤ $400)

| Sharpe | σ_C | σ_X | bestå ≤63 | ≤126 | ≤252 | median dage | resets | udbet. ≤63 | ≤252 | til ejer | gebyrer | **EV netto [95%]** | P(netto>0) | p10 | XFA ikke udbetalt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| -0,50 | $400 | $400 | 30% | 57% | 84% | 88 | 6,24 | 12% | 58% | $634 | $1.126 | **−$491** [−$507; −$476] | 17% | −$1.158 | $57 |
| 0,00 | $400 | $400 | 37% | 68% | 92% | 77 | 5,18 | 17% | 72% | $997 | $1.138 | **−$141** [−$162; −$120] | 27% | −$1.156 | $88 |
| 0,25 | $400 | $400 | 42% | 73% | 94% | 71 | 4,68 | 20% | 78% | $1.228 | $1.145 | **$83** [$60; $107] | 33% | −$1.109 | $109 |
| 0,50 | $400 | $400 | 46% | 78% | 96% | 66 | 4,21 | 23% | 84% | $1.521 | $1.150 | **$371** [$344; $399] | 40% | −$1.104 | $135 |
| 0,75 | $400 | $400 | 51% | 82% | 98% | 61 | 3,79 | 27% | 88% | $1.866 | $1.155 | **$711** [$680; $742] | 46% | −$1.058 | $159 |
| 1,00 | $400 | $400 | 55% | 86% | 99% | 56 | 3,38 | 31% | 92% | $2.267 | $1.159 | **$1.108** [$1.073; $1.143] | 54% | −$1.009 | $195 |
| 1,25 | $400 | $400 | 60% | 89% | 99% | 52 | 3,00 | 36% | 94% | $2.730 | $1.162 | **$1.568** [$1.528; $1.608] | 61% | −$951 | $232 |
| 1,50 | $400 | $400 | 64% | 92% | 100% | 48 | 2,65 | 40% | 96% | $3.264 | $1.162 | **$2.101** [$2.056; $2.146] | 68% | −$846 | $275 |
| 2,00 | $400 | $400 | 73% | 96% | 100% | 42 | 2,04 | 49% | 99% | $4.564 | $1.153 | **$3.411** [$3.356; $3.466] | 80% | −$569 | $383 |
| 2,50 | $400 | $400 | 80% | 98% | 100% | 37 | 1,54 | 59% | 100% | $6.225 | $1.131 | **$5.094** [$5.028; $5.161] | 89% | −$83 | $512 |
| 3,00 | $400 | $400 | 86% | 99% | 100% | 32 | 1,13 | 68% | 100% | $8.297 | $1.091 | **$7.206** [$7.129; $7.283] | 95% | $714 | $673 |

## 5. S_hurtig, den anden læsning: størrelsen der maksimerer P(første udbetaling ≤ 63 dage)

| Sharpe | σ_C | σ_X | P(udbet. ≤63) | EV netto |
|---|---|---|---|---|
| -0,50 | $1.000 | $400 | 37% | −$377 |
| 0,00 | $1.000 | $400 | 45% | $277 |
| 0,25 | $1.000 | $400 | 49% | $687 |
| 0,50 | $1.000 | $400 | 54% | $1.162 |
| 0,75 | $1.000 | $400 | 58% | $1.685 |
| 1,00 | $1.000 | $400 | 62% | $2.274 |
| 1,25 | $1.000 | $400 | 66% | $2.930 |
| 1,50 | $1.000 | $400 | 70% | $3.668 |
| 2,00 | $1.000 | $400 | 78% | $5.389 |
| 2,50 | $1.000 | $400 | 84% | $7.477 |
| 3,00 | $1.000 | $400 | 89% | $9.912 |

## 6. Valget af størrelse: valgstier mod nye stier (hovedmodellen)

| Sharpe | σ_C | σ_X | EV på valgstierne | EV på nye stier | forskel |
|---|---|---|---|---|---|
| -0,50 | $800 | $800 | $124 | $165 | $41 |
| 0,00 | $800 | $800 | $973 | $1.020 | $47 |
| 0,25 | $1.000 | $800 | $1.516 | $1.562 | $46 |
| 0,50 | $1.000 | $800 | $2.175 | $2.238 | $63 |
| 0,75 | $1.000 | $800 | $2.925 | $3.005 | $79 |
| 1,00 | $1.000 | $800 | $3.799 | $3.894 | $95 |
| 1,25 | $1.000 | $800 | $4.789 | $4.889 | $100 |
| 1,50 | $1.000 | $800 | $5.930 | $6.045 | $115 |
| 2,00 | $1.000 | $800 | $8.615 | $8.777 | $162 |
| 2,50 | $1.000 | $800 | $11.960 | $12.133 | $174 |
| 3,00 | $1.000 | $1.000 | $16.147 | $16.447 | $300 |

## 7. Referencepunkterne (placeres på kurven, afgør intet)

| reference | Sharpe | EV, bedste størrelse | EV, disciplinzone | P(udbet. ≤63) | nærmeste gitterpunkts σ_X | MNQ for den σ_X |
|---|---|---|---|---|---|---|
| Fase 2's antagelse (WR 40% ved 2:1) | 1,90 | $8.231 | $3.149 | 64% | $800 (S = 2,00) | — |
| Kandidat 5 in-sample, 1m · uden middag | 1,17 | $4.570 | $1.421 | 52% | $800 (S = 1,25) | 1,4 |
| Kandidat 5 holdout | -1,04 | under gitteret (−0,5: $165) | under gitteret (−0,5: −$491) | — | $800 (S = -0,50) | 1,7 |
| Kandidat 6, 07:30–09:30 efter salg | 0,64 | $2.667 | $561 | 44% | $800 (S = 0,75) | 6,5 |
| Ingen edge, kun omkostning | under 0 | se S = −0,5 og 0 i kurven | | | | |

"MNQ for den σ_X" er den daglige spredning ved den bedste størrelse i nærmeste
gitterpunkt delt med referencens σ pr. MNQ — hvor mange kontrakter størrelsen svarer til.

## 8. Følsomhed (rapporteres, afgør intet)

| variant | EV ved S = 0,00 | EV ved S = 0,50 | EV ved S = 0,75 | EV ved S = 1,00 | EV ved S = 1,50 | EV ved S = 2,00 |
|---|---|---|---|---|---|---|
| Hovedmodel (t4, DLL, intradag, 252 dage, $49-plan) | $1.020 | $2.238 | $3.005 | $3.894 | $6.045 | $8.777 |
| Normalfordelt Z | $2.450 | $3.983 | $4.924 | $5.948 | $8.390 | $11.309 |
| Student-t, 3 frihedsgrader | $516 | $1.550 | $2.205 | $2.975 | $4.947 | $7.642 |
| DLL slået fra (loft $2.000) | $2.046 | $3.843 | $4.946 | $6.243 | $9.279 | $13.123 |
| Ingen bevægelse inden for dagen | $8.160 | $11.698 | $13.825 | $16.087 | $21.349 | $27.406 |
| Horisont 126 dage | $360 | $912 | $1.259 | $1.658 | $2.616 | $3.821 |
| $95-planen uden aktivering | $631 | $1.959 | $2.766 | $3.677 | $5.936 | $8.792 |

Kravet pr. følsomhed står i tabel 1.

## 9. Hvad der skal læses med tallene (afgør intet, §6 er anvendt ovenfor)

- **Regelgeometrien giver plus uden edge.** Ved den bedste størrelse er forventet
  nettoværdi positiv ved Sharpe 0 ($1.020) og ved −0,5 ($165). Ejerens tab er loftet af
  gebyrerne (cirka $1.900 om året), mens udbetalingerne ikke er loftet. Det er en option, og
  den er mest værd ved stor spredning.
- **Den bedste størrelse er stor og ligger ved gitterets kant.** σ_C er $1.000, gitterets
  største værdi, fra Sharpe 0,25 og op. σ_X er $800. Ved Sharpe −0,5 og 0 er den bedste
  σ_C $800, altså inde i gitteret. En σ på $1.000 svarer til DLL'en på én dags spredning.
- **Prisen er adfærd.** Ved den bedste størrelse er der 15–19 Combine-resets om året ved
  Sharpe ≤ 1, og DLL'en rammes ofte. Det er det mønster, Topstep nævner som grund til nedkald
  og afvisning ("gentagne brud på Daily Loss Limit", "activity that resembles gambling",
  `REGLER_VERIFICERET.md` §5). Modellen kan ikke prissætte den regel.
- **I disciplinzonen** (σ ≤ $400) er S_min_EV 0,16. Forventet nettoværdi er −$141 ved
  Sharpe 0 og −$491 ved −0,5, og der er 3–6 resets om året. Den bedste celle i zonen er
  σ_C = σ_X = $400, zonens kant, ved alle Sharpes.
- **Bevægelsen inden for dagen betyder meget.** Uden den (kun dagsslut) stiger EV ved
  Sharpe 0 fra $1.020 til $8.160. Brud i realtid er altså en stor del af prisen, og
  bridge-antagelsen bærer en stor del af tallet.
- **Genberegningen på nye stier** gav højere EV end valgstierne ved alle Sharpes, med
  $41–$300. Den forventede optimisme ved valget er altså mindre end forskellen mellem de to
  sæt frø. Kravet flytter sig ikke: S_min_EV er ≤ −0,5 på begge.
- **Referencepunkterne:** kandidat 6 (Sharpe 0,64, σ $123 pr. MNQ) skulle handle cirka
  6,5 MNQ for at nå den bedste σ_X på $800, og 3,3 MNQ for disciplinzonens $400.
