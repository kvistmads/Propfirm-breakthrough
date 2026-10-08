# B4 kandidat 5 — tillæg: beslutninger efter optællingen, før kørslen

**Skrevet:** 2026-10-08 af overblikssessionen. Det er skrevet efter Code's trin 1 (kode
7506775, optælling 4f43209) og **før** den rigtige kørsel. Der er ikke set P&L, hit ratio
eller udfald.

**Gyldighed:** tillægget gælder, når ejeren committer det. Commit'en er ejerens
godkendelse af beslutningerne nedenfor, som følger overblikssessionens anbefaling. Vil
ejeren noget andet, rettes tillægget før commit. `b4_k5_vwap_trend.md` gælder uændret,
undtagen hvor dette tillæg siger andet.

**Bekræftet af ejeren 2026-10-08:**
- Målet regnes ved dagens niveau (§4g). Det nominelle tal er en diagnose.
- Der lægges ingen ekstra slippage på ud over de $2,627 (§4f).

## 1. Optællingen er godkendt

| variant | handler_n | handler pr. dag (middel) | omk. $/dag | σ_dag $ | MDE_sidak4 $ | styrke for netto ved artiklens $82 |
|---|---|---|---|---|---|---|
| 1m · hele dagen | 19.151 | 16,4 | 43,04 | 685 | 61,6 | 49% |
| 1m · uden middag | 14.831 | 12,7 | 33,33 | 561 | 50,4 | 84% |
| 5m · hele dagen | 8.734 | 7,5 | 19,63 | 680 | 61,2 | 88% |
| 5m · uden middag | 7.387 | 6,3 | 16,60 | 554 | 49,8 | 98% |

- **§7's betingelse holder for alle 4 varianter.** Hver variant kan se artiklens effekt
  mod nulmodellen. **Tælleren forbliver 41.**
- **Artiklens egen strategi (1m · hele dagen) har kun 49% styrke for netto.** Selv hvis
  artiklens effekt holder fuldt ud på MNQ, er det cirka plat eller krone, om dens
  netto-interval kommer over 0. Det skyldes omkostningen på $43 om dagen. Det ændrer
  intet i testen, men står her, så det ikke overrasker bagefter.
- **Handler pr. dag** på 1m (16,4) ligger tæt på artiklens cirka 15. Det tyder på, at
  reglerne er bygget som i artiklen.
- **Omkostningen pr. round trip** var 1,67 bp i 2019 og 0,89–1,25 bp i 2020–2023 mod
  0,45 bp ved dagens niveau. Det bekræfter, at valget i §4g betyder noget.

## 2. §8's række 2 omskrives (læsning 30)

Code gjorde opmærksom på et hul i §8. Har én variant p_FWE ≤ 0,05 uden CI-nedre > 0, og
en anden variant CI-nedre > 0 uden p_FWE ≤ 0,05, passer hverken række 1, 2 eller 3. Så
ville række 4 gælde, og det beviste om VWAP-retningen ville gå tabt.

**Ny række 2**, som erstatter den gamle:

| nr | udfald | handling |
|---|---|---|
| 2 | Mindst én variant har p_FWE ≤ 0,05, men ingen variant opfylder række 1 | **Parkeres som "VWAP-retningen bærer, men betaler ikke omkostningen".** Har en anden variant CI-nedre > 0 uden p_FWE ≤ 0,05, skrives den op som et in-sample-fund, som i række 3 |

- Række 1, 3 og 4 er uændrede. **Kravet for at fryse er det samme:** én og samme variant
  skal have både p_FWE ≤ 0,05 og CI-nedre > 0.
- Handlingen er "parkér" i alle tilfælde. Rettelsen sikrer kun, at teksten passer til
  beviset.
- Rettelsen er besluttet før udfaldene, ud fra Code's læsning alene.

## 3. De 4 udelukkede dage — ny diagnose

De 4 dage, som §4h udelukker (9., 12., 16. og 18. marts 2020), er de dage, hvor
markedsbredde circuit breakers stoppede handlen i cirka 15 minutter efter et fald på 7%
i S&P 500.

- **De forbliver udelukket**, som §4h foreskriver. Middel, CI, nulmodel og §8 ændres
  ikke.
- **Ny diagnose:** de 4 dage rapporteres for sig pr. variant med `dag_netto_usd` ved
  dagens niveau og nominelt, og med største tab inden for dagen.
  - Positionen holdes gennem stoppet.
  - Udførelsen sker ved første bar efter stoppet (læsning 12).
- **Hvorfor:** en trendstrategi kan tjene eller tabe meget på netop de dage. En bot på
  Topstep kan sidde med en position, når handlen stopper. Ruinmodellen skal kende
  størrelsen.

## 4. Code's læsninger — godkendt

Alle 31 i docstringen i `research/b4_k5_vwap_trend.py` er godkendt. Læsning 30 erstattes
af §2 ovenfor. De seks markerede:

| nr | læsning | hvorfor den er rigtig |
|---|---|---|
| 3 | Et hul er antallet af manglende minutter. Mere end 5 udelukker | Begge læsninger udelukker de samme 4 dage. Den valgte passer med grænsen for første bar kl. 08:35 |
| 10 | Kl. 14:00 åbnes efter det seneste signal ≠ 0, også hvis lyset kl. 13:59 lukker præcis på VWAP | Det er §4b's princip om, at close = VWAP ikke ændrer noget. §4b's regel om at vente gælder kun dagens første handel, hvor der ikke findes et tidligere signal |
| 17 | σ_dag regnes over variantens handelstid fra første mulige udførelse, med Δclose mod forrige lys | σ_dag skal være markedets svingning, ikke modellens handler. Så holder den sig fri af udfald |
| 18 | Styrken bruger middel handler pr. dag og en normalapproksimation | Omkostningen pr. dag er et middel. Styrken er kun en oplysning, ikke et krav |
| 25 | Hele omkostningen trækkes ved indgangen i det største tab inden for dagen | Den forsigtige side. Topsteps MLL brydes i realtid, og forskellen er højst $2,627 |
| 30 | §8 læst bogstaveligt | Erstattet af §2 |

**Bemærk læsning 29:** nulmodellen har de samme handler som modellen og flyttes derfor med
præcis samme omkostning. p_FWE afhænger altså ikke af omkostningen. Kun netto-intervallet
gør.

## 5. Betingelser for den rigtige kørsel

1. **De eneste tilladte kodeændringer:**
   - `beslutning` efter §2, med en test af det blandede tilfælde;
   - diagnosen i §3, med en test der viser, at de 4 dage ikke indgår i middel, CI,
     nulmodel eller §8.
2. Derefter køres regressionstjekkene i `b4_k5_vwap_trend.md` §11.3 og hele testsuiten
   igen. De skal holde. Optællingen køres igen og skal give de samme tal.
3. **Koden står derefter fast.** Kørslen sker fra den commit, og rapporten oplyser dens
   hash.
4. **R = 500.**
5. **Rapport efter §10 og §9**, plus §3 her. Bagefter: stop. §8 anvendes mekanisk og
   læses sammen med ejeren.
