# B4 kandidat 1 — tillæg til præregistreringen af signaloptælling 2, kerne v2

**Skrevet:** 2026-09-22, før kørslen. Committes før kørslen, sammen med koden.
**Hører til:** `research/prereg/b4_k1_optaelling_v2.md` (commit 5de6fa1). Tillægget til
optælling 1, `b4_k1_optaelling_tillaeg.md` (commit 50a060e), gælder stadig, medmindre det er
ændret her.

Tillægget ændrer ingen definition, og intet punkt ændrer hvad der tælles. Det fastlægger
implementeringsdetaljer, som præregistreringen ikke nævner.

---

## 1. Strukturtjek før kørslen, uden signaler

Serien er den samme som i optælling 1 (tillæg 1, §1). Ét nyt tjek, uden zoner og signaler:
alle open, high, low og close i 15m-serien er hele multipla af 0,25 point, altså hele tick.
Den højeste pris er 17.165,25. Det er det der gør sammenligningerne i §3 eksakte.

## 2. Koden, og regressionstjekket

- **v1 står uændret.** `find_zoner`, `klassificer`, `noegletal`, `tabel` og `skriv_md` gør
  det samme som i 50a060e. Kerne v2 er en selvstændig funktion, `find_zoner_v2`, med egne
  tests. Kun fundet af basislys, udbrudslys og næste kontraktskift er fælles, i `_kandidater`.
  `klassificer` har fået en risikofaktor, som er 1 i v1.
- **Kørslen vælger kerne:** `--kerne v1` eller `--kerne v2` er påkrævet, så ingen af dem
  køres ved et uheld. `--ud` angiver outputmappen.
- **Regressionstjekket (præregistreringen v2 §6):** Når koden er committet, køres
  `--kerne v1 --ud <scratchpad>` fra den committede kode. Den csv der kommer ud, skal være
  byte for byte identisk (`cmp`) med `research/output/b4_k1_optaelling.csv` fra 43c5182.
  Afviger den, køres v2 ikke, og det rapporteres.
- Inden da er det tjekket på 40 tilfældige syntetiske serier (7.669 zoner, 1.275 signaler) at
  v1-vejen giver samme zonetabel og samme csv-tekst som modulet fra 50a060e. En test låser
  at v1-tabellens kolonner og deres rækkefølge er dem i den committede csv.

## 3. E og sammenligningerne

- Bufferen er brøken 1/10. Sammenligningerne med E regnes i skaleret form:

  | | demand | supply |
  |---|---|---|
  | aktivering | 10·low > 10·zonens high + H | 10·high < 10·zonens low − H |
  | berøring | 10·low ≤ 10·zonens high + H | 10·high ≥ 10·zonens low − H |

  Med priser i hele tick er hvert led eksakt i float64.
- Den naive form, high + 0,1 × H, giver de samme sammenligninger ved in-sample-niveauerne.
  Det er tjekket på 200.000 tilfældige zoner mellem 4.000 og 17.200 point. Ligger E på
  tick-gitteret, runder den naive sum til præcis gitterværdien. Ligger E uden for gitteret,
  er afstanden til nærmeste pris mindst 0,025 point. Den skalerede form ændrer altså intet
  resultat; den er eksakt pr. konstruktion.
- Varianten uden buffer er brøken 0: E er zonens high (supply: low) eksakt.
- Kolonnen `E` i zonelisten er et float og bruges kun til visning.

## 4. De fem forløb

- Statusværdierne i zonelisten er `beroert`, `ugyldig`, `kontraktskift`, `aktiv` og
  `aldrig_aktiv`. De to sidste er de censurerede: `aktiv` er aktiv, men ikke berørt ved
  in-sample-slut, og `aldrig_aktiv` er aldrig aktiveret ved in-sample-slut. De erstatter
  v1's `aaben`.
- **Kontraktskift i alle faser:** skiftelyset vurderes ikke for noget, hverken aktivering,
  ugyldighed eller berøring. Zonen dør dér.
- **Ugyldighed og aktivering** kan ikke ske i samme lys. Aktivering kræver low > E > zonens
  low, og så er close > zonens low.
- **Udbrudslyset** kan aktivere ("fra og med"). Det kan ikke gøre zonen ugyldig ("efter
  udbrudslyset"), og det kunne heller ikke, for dets close ligger over zonens high.
- **Aktiveringslyset** kan ikke være berøringen, for dets low ligger over E. Berøringen er
  første lys efter det.
- **Efter aktiveringen** gælder ugyldigheden ikke længere. Et lys der lukker gennem zonen
  efter aktiveringen, har low ≤ E og er berøringen.
- **Basislys og udbrudslys i hver sin kontrakt:** som tillæg 1, §2. Zonen tælles som dannet
  og dør ved udbrudslyset, før den bliver gyldig. Den kan heller ikke aktiveres i det lys.
- Dør en aktiv zone ved kontraktskift, beholder zonelisten `aktiv_i`. Zonen tælles i
  `zoner_doede_ved_kontraktskift_n`.

## 5. Risiko, stoploft og sizing

- `risiko_pct` = zonehøjde_pct × 1,1, altså 1,1 × H / basislysets close × 100. Det er
  basislysets close, for v2 ændrer ikke den del af v1-definitionen.
- Stoploftet er afrundet `risiko_pct` ≤ 0,429, med 10 decimaler som i tillæg 1, §5.
- `zonehoejde_pt` er stadig H_pt. Den nye `risiko_pt` er 1,1 × H_pt.
- `kontrakter` = floor(250 / (risiko_pt × 2)), med samme afrunding før floor som i v1.
  `omk_R_netto` = 2,627 / (2 × risiko_pt), og `be_WR` regnes som i tillæg 1.
- Formlen giver 0 kontrakter når risikoen ligger mellem 125/29.138 og 0,429%. Antallet
  rapporteres.
- For varianten uden buffer er risikoen H, så alt regnes som i v1.

## 6. Tiderne og de nye rækker

- `tid_til_aktiv_timer` = aktiveringslysets åbning − udbrudslysets lukning (åbning + 15 min).
  Er udbrudslyset selv aktiveringslyset, giver formlen −0,25 timer. Formlen bruges som
  skrevet, og antallet af den slags signaler rapporteres.
- `tid_efter_aktiv_timer` = berøringslysets åbning − aktiveringslysets lukning (åbning + 15
  min). Den er aldrig negativ.
- `zonealder_timer` er som i v1, berøringslysets åbning − udbrudslysets lukning. For hvert
  signal er zonealder = tid_til_aktiv + 0,25 + tid_efter_aktiv.
- `beroering_lige_efter_aktivering`: berøringslyset er det næste lys i serien efter
  aktiveringslyset. "Lige efter" betyder nabolys i serien, som i tillæg 1, §2. Et hul i tid
  imellem ændrer det ikke.
- Alle tre regnes kun over signaler, med percentilerne som i tillæg 1, §7.

## 7. Nævnere, de nye rækker

| andel | tæller | nævner |
|---|---|---|
| `zoner_ugyldige_foer_aktiv_pct` | ugyldige før aktivering | `zoner_dannet_n` |
| `zoner_aktive_ikke_beroert_pct` | aktive, ikke berørt ved in-sample-slut | `zoner_dannet_n` |
| `zoner_aldrig_aktive_pct` | aldrig aktiveret ved in-sample-slut | `zoner_dannet_n` |
| `beroering_lige_efter_aktivering_pct` | signaler med berøringen i lyset lige efter aktiveringslyset | signaler |

v1-rækkerne står der stadig, og tre af dem læses sådan i v2:

- `zoner_aldrig_beroert_pct` er de to censurerede forløb tilsammen, altså zonerne der
  stadig lever ved in-sample-slut. Det er samme betydning som i v1.
- `beroeringer_*` tæller kun berøringer efter aktiveringen. Et lys før aktiveringen der når
  E, er ikke en berøring.
- `afvist_af_stoploft_pct` regnes på risikoen.

Hver andel får Wilson 95%-CI.

## 8. Varianten uden buffer

Den tælles i samme kørsel, med samme kode og bufferen 0. CSV'en har hele tabellen for begge,
og kolonnen `kerne` er `v2` eller `v2_uden_buffer`. Rapporten viser den korte tabel fra
præregistreringen v2 §4. Beslutningsreglen gælder kun v2.

## 9. Kørslen

- **Kun fra committet kode**, som i tillæg 1, §10. Kontrollen dækker nu også
  præregistreringen v2 og dette tillæg.
- Først regressionstjekket (§2). Derefter én kørsel:
  `.venv/bin/python -m research.b4_k1_optaelling --kerne v2 --zoner <scratchpad>/b4_k1_v2_zoner.parquet`.
- **Output:** `research/output/b4_k1_optaelling_v2.md` og `.csv`. Optælling 1's filer
  røres ikke.
- **Zonelisten** har begge kerner med kolonnen `kerne` og skrives uden for repoet, som i
  tillæg 1.

## 10. Gennemgang efter kørslen

Som tillæg 1, §11, og desuden:

- De fem forløb skal summe til `zoner_dannet_n` for hver side.
- For hvert signal skal zonealder = tid_til_aktiv + 0,25 + tid_efter_aktiv.
- Stikprøven holdes op mod 15m-lysene fra basislyset til og med slutlyset, og aktiveringslyset
  tjekkes med.
