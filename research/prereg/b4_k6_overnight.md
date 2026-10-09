# B4 kandidat 6 — præregistrering: overnight drift ved Europas åbning

**Skrevet:** 2026-10-09 af overblikssessionen, før kørslen. Committes før kørslen.
**Kilde:** Boyarchenko, Larsen og Whelan (2023), *The Overnight Drift*, Review of
Financial Studies 36(9). Første udgave var NY Fed Staff Report 917 fra marts 2020.
Screeningen står i `research/output/b4_screening.md`.
**Besluttet af ejeren:**
- 2026-10-08, svar 1A og 2A på screeningen. Handel uden for RTH er tilladt inden for
  Topsteps regler.
- 2026-10-09, svar 1A–6A på spørgsmålene til kandidat 6 (screeningen §4).

**Løftede regler for denne kandidat:** `PRD_FASE3_B4_EDGE.md` §3 ("kun US RTH") og
`STRATEGI_PROPFIRM.md` §3 ("ingen markedsordrer uden for RTH"). Topsteps egne regler
gælder uændret. Positionen ligger inden for én Topstep-dag, som starter kl. 17:00 CT.

---

## 1. Hvad testen afgør

1. **Er timen omkring Europas åbning særlig på Nasdaq-futures?** Long i vinduet sammenlignes
   med long i en tilfældig anden time samme nat (N-nat, afgør). Korrektion for 4 varianter.
2. **Betaler den omkostningen?** Middel netto-dollar pr. nat pr. MNQ ved dagens niveau, med
   konfidensinterval over nætterne.
3. **Er den større efter en salgsdag**, som artiklen fandt?

## 2. Mekanismen — skrevet før testen

**Påstanden:** når investorer sælger i den amerikanske session, køber markedsmagerne og
sidder med et lager, de ikke ønsker. Når Europa åbner, kommer der nye købere, og lageret
afvikles med en gevinst. Det er betaling for at stille likviditet og bære lagerrisiko.
Derfor er effekten størst efter dage med salg og nul, når der ikke var en ubalance.

**Hvem betaler:** de investorer, der skulle sælge i den amerikanske session og ikke kunne
vente.

**Litteraturen (ES 1998–2020):**
- Det største positive afkast i døgnet ligger kl. 2:00–3:00 New York-tid, cirka 1,48 bp pr.
  dag. Det var positivt i 20 af 23 år.
- Long 2:00–3:00 havde Sharpe 1,1 før og −0,5 efter omkostninger.
- Long 1:30–3:30 havde Sharpe 1,3 før og 0,3 efter.
- Long 1:30–3:30 kun efter en salgsubalance havde Sharpe 1,8 før og 1,1 efter.

**Det taler imod:**
- Artiklen kom i 2020. Om effekten holdt bagefter, er ukendt, og kandidat 5 viste, hvad
  publicering kan gøre.
- Den er målt på S&P og ikke på Nasdaq.
- Vi har ikke artiklens ordreubalance, kun en erstatning bygget på prisen (§4c).

## 3. Serie og faste indstillinger

| emne | valg |
|---|---|
| Hovedserie (svar 3A) | **NQ.v.0 1m, 2016-01-01 → 2023-12-31**, kun gennem `data.holdout.load_in_sample(symbol="NQ.v.0")`. NQ og MNQ har samme kurs, og volumen indgår ikke |
| Kontrolserie | MNQ.v.0 1m, 2019-05-06 → 2023-12-31, samme vej. Den rapporteres, men afgør intet |
| Holdout | Åbnes ikke. Hvis kandidaten fryses, præregistreres holdout-testen for sig (§8) |
| Priser | Alle punktforskelle regnes på den **forskelsjusterede** serie (`b4_k2_nowick.forskelsjuster`), så et vindue hen over en rulle ikke får springet med. L_d tages fra den ujusterede serie |
| Størrelse | 1 MNQ fast. Hvor mange kontrakter, og om der skal et nødstop på, afgør ruinmodellen |
| Omkostning | **$2,85 pr. round trip** (§4e). Ingen ekstra slippage |
| Tidszone | Vinduerne står i New York-tid som i artiklen. CT er altid én time før New York. Dansk tid er normalt New York + 6 timer, i skifteugerne + 5 |

## 4. Definitionerne

### 4a. Natten

- **Natten før RTH-dag d** er Globex-sessionen fra kl. 17:00 CT dagen før til kl. 08:30 CT
  på dag d. Dag d er en XNYS-dag (`data.sessions`).
- **Forrige RTH-dag** er XNYS-dagen før d. For mandagsnætter er det fredagen.
- Nætter, hvor Globex ikke handler i vinduet, findes ikke og tælles som udelukkede.

### 4b. Vinduerne (svar 1A)

| vindue | New York-tid | CT | dansk tid, normalt |
|---|---|---|---|
| **V1** | 02:00–03:00 | 01:00–02:00 | 08:00–09:00 |
| **V2** | 01:30–03:30 | 00:30–02:30 | 07:30–09:30 |

- **Indgang:** long ved åbningen af 1m-baren, der starter ved vinduets start.
- **Udgang:** ved åbningen af 1m-baren, der starter ved vinduets slutning.
- **Mangler baren,** bruges åbningen af den første bar, der starter på eller efter det
  nominelle tidspunkt. Det tælles.
- **Starter den bar mere end 5 minutter for sent**, ved indgang eller udgang, udelukkes
  natten i alle varianter og i nulmodellen. Det tælles.
- Én handel pr. nat pr. variant. Intet stop (svar 6A).

### 4c. Salgsdag (svar 2A)

- **Forrige RTH-dag er en salgsdag,** hvis `close(sidste RTH-bar) < open(første RTH-bar)`,
  altså afkastet fra 08:30 CT til RTH-slut er negativt. På kortdage slutter RTH kl. 12:00 CT.
- Det er vores erstatning for artiklens negative ordreubalance ved lukningen. Den er
  svagere, fordi en dag kan falde uden en stor ubalance ved lukningen.

### 4d. Varianterne

| variant | vindue | nætter |
|---|---|---|
| V1 · alle | 02:00–03:00 NY | alle |
| V1 · salg | 02:00–03:00 NY | kun efter en salgsdag |
| V2 · alle | 01:30–03:30 NY | alle |
| V2 · salg | 01:30–03:30 NY | kun efter en salgsdag |

### 4e. Omkostning

- **$2,85 pr. round trip:** kommission $1,22 + spread + slippage $0,54.
- Spreadet er målt i fase 1 (`spread_mnq_pr_blok.csv`): cirka 2,1–2,2 ticks i timerne
  omkring vinduerne. V1 giver $2,85 og V2 $2,83. Der bruges $2,85 for begge.
- **Ingen ekstra slippage i prisen**, af samme grund som i kandidat 5 §4f: begge ordrer er
  markedsordrer på en bars åbning.
- **Diagnose ved $3,10:** spreadet uden for RTH var 2,44–2,58 ticks i 2025–2026.

### 4f. Målet (svar 5A)

- `L_n` er den ujusterede åbning af indgangsbaren.
- `netto_usd_n = Δpt_n × (29.138 / L_n) × 2 − 2,85`, hvor Δpt er udgang minus indgang på
  den forskelsjusterede serie.
- **Målet** er middel `netto_usd` pr. handlet nat pr. MNQ, med t-interval over nætterne.
- Middel pr. kalendernat (= middel × andel handlede nætter) rapporteres også, fordi det er
  det, en Combine mærker.
- Normeringen til dagens niveau følger kandidat 5 §4g. NQ lå på cirka 4.000–5.000 i 2016,
  så nætterne fra 2016 skaleres op til cirka 6–7 gange. Antagelsen er, at bevægelser i
  procent og omkostningen i ticks er de samme i dag.

## 5. Varianterne og tælleren

Der er **4 varianter.**

| tæller | forsøg |
|---|---|
| Kandidat 1–5 | 41 |
| Kandidat 6 | 4 |
| **I alt** | **45** |

## 6. Nulmodellerne (svar 4A)

**N-nat — afgør. Er timen omkring Europas åbning særlig?**
- Samme nætter og samme længde som varianten (60 eller 120 minutter), long, samme
  omkostning og normering.
- **Starten trækkes tilfældigt** på minutgitteret, så vinduet ligger helt mellem 17:00 og
  08:30 CT og ikke overlapper variantens vindue.
- Ved udførelse gælder samme regel om manglende barer og 5 minutters forsinkelse som i
  §4b. Kan en trukket start ikke udføres, trækkes der igen.
- **Trækningerne deles:** starten trækkes deterministisk pr. (gentagelse, nat,
  vindueslængde). "Alle" og "salg" med samme vindue får derfor samme tilfældige time på de
  nætter, de deler.
- **R = 500.**

**Long hele natten — forklarer, ændrer intet.** Long fra åbningen kl. 17:00 CT til
åbningen kl. 08:30 CT, samme omkostning og normering. Viser, om hele natten driver, eller
kun timen omkring Europas åbning.

## 7. Statistik og MDE

**Mål:** middel `netto_usd` pr. handlet nat, med t-interval over nætterne (95%, tosidet).

**Test:** Westfall-Young maks-statistik mod N-nat, standardiseret som i `b4_k2_nowick.md`
§7: `t_v = (m_v − med_v) / sd_v`, `p_FWE = (1 + #{max t* ≥ t_v}) / 501`. Énsidet.

**MDE**, regnet i optællingen uden udfald:
- `σ_nat = 2 × √(middel_n[(29.138 / L_n)² × Σ_t Δclose_t²])`. Summen går over vinduets
  1m-barer, på den forskelsjusterede serie.
- `MDE_sidak4 = 3,0756 × σ_nat / √n` og `MDE_CI = 2,8016 × σ_nat / √n`.

| nætter | σ_nat $120 | $150 | $180 |
|---|---|---|---|
| MDE_sidak4 ved 2.000 (alle) | $8,3 | $10,3 | $12,4 |
| MDE_sidak4 ved 1.000 (salg) | $11,7 | $14,6 | $17,5 |

**Artiklens effekt ved dagens niveau:** 1,48 bp pr. dag i V1 svarer til **$8,6 brutto pr.
MNQ**. Effekten efter salg er større, men artiklen opgiver den ikke i bp.

**Ingen fast betingelse før kørslen.** V1 · alle ligger tæt på det, testen kan se. I
stedet viser optællingen MDE og styrken mod $8,6 og $17,2 (det dobbelte) for hver
variant, og **ejeren godkender optællingen, før der køres.**

## 8. Beslutningsreglen — dækker alle udfald

Rækkerne prøves i rækkefølge, og den første, der passer, gælder. Krydser et interval en
grænse, er betingelsen ikke opfyldt.

| nr | udfald | handling |
|---|---|---|
| 1 | Mindst én variant har p_FWE ≤ 0,05 **og** CI-nedre > 0 | **Varianten fryses.** Opfylder flere kravet, fryses den med højeste CI-nedre. Næste skridt: præregistrering af holdout-testen på MNQ 2024–2026 og ruinmodellen |
| 2 | Mindst én variant har p_FWE ≤ 0,05, men ingen opfylder række 1 | **Parkeres som "timen er særlig, men betaler ikke omkostningen".** Varianter med CI-nedre > 0 uden p_FWE ≤ 0,05 skrives op som in-sample-fund |
| 3 | Ingen variant har p_FWE ≤ 0,05, men mindst én har CI-nedre > 0 | **Parkeres:** gevinsten er ikke knyttet til Europas åbning. Det er et in-sample-fund, fx at hele natten driver. Det kan blive en ny kandidat med egen præregistrering |
| 4 | Alt andet | **Kandidat 6 parkeres** |

**Afgørelsen tages på NQ ved $2,85 og dagens niveau.** Diagnoserne i §9 ændrer ikke
rækken.

## 9. Diagnoser — rapporteres, men afgør intet

| diagnose | hvorfor |
|---|---|
| **Før og efter 2020-03-01** (artiklen udkom), middel netto med CI pr. periode | holder den efter publiceringen? |
| Pr. år, netto og nominelt | koncentration |
| Netto ved $3,10 og den række i §8, det ville give | nyere spread uden for RTH |
| Nominelt, ved det historiske niveau | hvad der faktisk var tjent |
| Break-even-omkostning pr. handel, middel og CI | margen over $2,85 |
| **MNQ 2019–2023**, samme 4 varianter | kontrol på det instrument, der handles |
| Brutto efter salgsdagens størrelse (terciler af RTH-afkastet) | er effekten større efter større salg, som artiklen fandt? |
| Long hele natten (§6) | driver hele natten? |
| Hit ratio og gevinst/tab-forhold | profil |
| Natfordeling p1/p5/p50/p95/p99, værste og bedste nat | til ruinmodellen |
| Største tab inden for vinduet (mark-to-market på 1m-close) | Topsteps MLL brydes i realtid |
| Andel salgsdage, udelukkede nætter, forsinkede udførelser og ruller i vinduerne | datakvalitet |

## 10. Rapporten

Filerne er `research/output/b4_k6_overnight.md` og `.csv`.

**Hovedtabellen** har én række pr. variant med kolonnerne:
- `variant`, `naetter_n`;
- `middel_brutto_usd`, `middel_netto_usd`, `CI95_netto`;
- `N_nat_p5/p50/p95`, `t_v`, `p_FWE`;
- `netto_usd_pr_kalendernat`;
- `MDE_sidak4`, `MDE_CI`.

Derefter: §8 anvendt mekanisk, og diagnoserne i hver sin tabel.

## 11. Før kørslen: Code's trin 1, og så stop

1. **Modul og tests:** `research/b4_k6_overnight.py` og `tests/test_b4_k6_overnight.py`.
   Kandidat 1–5's moduler må importeres, men ikke ændres.
   - Westfall-Young genbruges fra `b4_k2_nowick.westfall_young`.
   - Forskelsjusteringen genbruges fra `b4_k2_nowick.forskelsjuster`.
2. **Syntetiske tests, alle skal bestå:**
   1. Natten før dag d går fra 17:00 CT dagen før til 08:30 CT på dag d. Mandagsnatten
      hører til mandag, og forrige RTH-dag er fredag.
   2. V1 og V2 ligger rigtigt i New York-tid hele året, også i skifteugerne.
   3. Indgang og udgang ved barernes åbning. Mangler en bar, bruges den næste.
      Forsinkelse over 5 minutter udelukker natten.
   4. Salgsdag efter §4c, også på kortdage.
   5. Punktforskelle på den forskelsjusterede serie. En rulle inden i et vindue giver ikke
      springet med. L_n er ujusteret.
   6. Normering og omkostning efter §4f.
   7. N-nat: vinduet ligger i natten, overlapper ikke variantens vindue og har samme
      længde. Samme (gentagelse, nat, længde) giver samme start i "alle" og "salg".
   8. Long hele natten fra 17:00 til 08:30 CT.
   9. Westfall-Young og p_FWE som i kandidat 2.
3. **Regressionstjek:**
   - kandidat 1's tre tjek;
   - `simuler_handel` 1.226 / −0,0115;
   - kandidat 2: 611 / −0,1430;
   - kandidat 3: 1.168 / −0,0712;
   - kandidat 4: 1.104 / −0,0920;
   - kandidat 5 in-sample, 1m · uden middag: 14.831 handler og $41,07;
   - hele testsuiten.
4. **Optælling uden udfald,** pr. variant og for både NQ og MNQ:
   - nætter i alt, udelukkede nætter med grund, forsinkede udførelser og ruller i
     vinduerne;
   - andel salgsdage;
   - medianen af L_n pr. år og omkostningen i bp pr. år;
   - σ_nat, `MDE_sidak4`, `MDE_CI` og styrken mod $8,6 og $17,2.
   - **Ingen P&L, ingen hit ratio, intet udfald.**
5. **Tidsmåling:** ét gennemløb og 5 gentagelser af N-nat.
6. **Stop.** Den rigtige kørsel sker først, når ejeren har godkendt optællingen.

## 12. Forventning, skrevet før kørslen — ikke et kriterium

- **Salgsvarianterne er de mest lovende.** Det var den eneste version, der klarede
  omkostningerne i artiklen.
- **V1 · alle er svær at skelne fra nul.** Artiklens effekt på $8,6 ligger omkring MDE.
- **Publiceringen er den største risiko.** Jeg forventer et svagere resultat efter 2020
  end før.
- **Mit skøn for rækken i §8:** række 1 ca. 20%, række 2 ca. 15%, række 3 ca. 10%,
  række 4 ca. 55%.

## 13. Efter kørslen

Stop. Tabellerne i chatten. Ingen ændring af definitioner, ingen nye varianter og ingen
forslag. Resultatet læses sammen med ejeren, og §8 anvendes mekanisk.

## Kilder

- Boyarchenko, Larsen & Whelan (2023), *The Overnight Drift*, Review of Financial Studies
  36(9), 3502–3547 — https://ideas.repec.org/a/oup/rfinst/v36y2023i9p3502-3547..html
- NY Fed Staff Report 917 (2020) —
  https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf
- Screeningen: `research/output/b4_screening.md`
