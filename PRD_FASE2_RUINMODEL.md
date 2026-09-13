# PRD — Fase 2: Ruinmodel på målt grundlag

**Skrevet:** 2026-09-13 af overblikssessionen.
**Besvarer:** åbent spørgsmål **B6** i `STRATEGI_PROPFIRM.md` — sizing på det målte
grundlag. Lukker §5's genåbnede valg.
**Repo:** `Propfirm-breakthrough`. Arbejdet sker på branchen `fase2-ruinmodel`, ikke på
`main`.
**Kræver ikke:** Topstep-konto, abonnement eller penge. Data ligger allerede i repoet.

---

## Trin 0 — engangsopgaver før fasen begynder

**Slet dette afsnit når det er gjort**, så dokumentet er ren PRD.

### 0.1 `.DS_Store` i `.gitignore`

Der ligger en `.DS_Store` i repoet. macOS laver dem i hver mappe der åbnes i Finder, de
har intet med projektet at gøre, og de skaber støj i hver eneste diff.

Tilføj linjen `.DS_Store` til `.gitignore`. Fjern derefter den der allerede er sporet:

```
git --no-optional-locks rm --cached .DS_Store
```

Findes der flere, tag dem alle:

```
git --no-optional-locks rm --cached -r --ignore-unmatch '*.DS_Store'
```

Verificér bagefter at der ingen er tilbage i indekset:

```
git --no-optional-locks ls-files | grep -c DS_Store
```

Svaret skal være `0`.

Brug `git --no-optional-locks` på **alle** git-kald i dette repo. Uden det efterlades
lockfiler der blokerer GitHub Desktop — det er sket før og kostede en fejlsøgning.

### 0.2 Læg de opdaterede dokumenter på plads

De ligger i `~/Downloads/`:

| fil | hvad |
|---|---|
| `STRATEGI_PROPFIRM.md` | **Erstatter** den eksisterende. §3 har et nyt afsnit om fladningsreglen, §5 er skrevet helt om på fase 1's målte tal, §9 er renummereret |
| `PRD_FASE2_RUINMODEL.md` | Dette dokument. **Ny** |

Kopiér begge til roden af repoet.

**Verificér efter kopieringen** at `STRATEGI_PROPFIRM.md` indeholder afsnittet
`### Handelsdøgnet og fladningsreglen`. Gør den ikke det, er den gamle version stadig på
plads, og resten af fasen bygger på tal der er faldet bort.

`ANTAGELSER.md` skal **ikke** erstattes. Din egen opdatering efter fase 1 er nyere end
overblikssessionens kopi. Opgave 4.6 opdaterer den videre.

### 0.3 Commit på `main` og branch

Dokumenterne er projektbrede referencer og hører hjemme på `main`.

Commit-besked:

```
Fase 2-PRD, opdateret strategidokument efter fase 1, DS_Store i gitignore
```

Push til `origin`. Opret derefter `fase2-ruinmodel` fra `main`.

### 0.4 Tag en kopi af datacachen

`data/cache/` er ~162 MB, git-ignoreret og **eneste kopi**. Yahoo-udtrækket kan ikke hentes
igen fordi Yahoos vindue ruller, så K2 kan kun genkøres herfra. Databento-data igen koster
~$27. Kopiér mappen til et sted uden for repoet — en ekstern disk, en anden mappe, hvad som
helst der ikke ryger med i en `git clean`. Sig hvor den ligger.

Tjek samtidig den faktiske saldo i Databentos portal. Budgetvagten regner på Databentos
*estimater* og er aldrig holdt op mod virkeligheden.

### 0.5 Læs baggrunden

Læs `STRATEGI_PROPFIRM.md` §0 (invarianter), §3's afsnit om fladningsreglen, og hele §5.
Læs `ANTAGELSER.md`. §5 forklarer hvorfor den gamle ruinmodel ikke længere gælder.

---

## 1. Hvorfor denne fase

Ruinmodellen blev kørt 2026-09-09 med **risiko pr. handel som en fast konstant på $102,06**
— afledt af ATR 0,168%, målt over 60 dages Yahoo-historik på hele døgnet.

Fase 1 målte det rigtigt: **15m i US RTH har p50-ATR på 0,232% og p90 på 0,459%.** Den
celle modellen valgte findes ikke. Risikoen pr. handel er $137,79 ved medianen og $270,08
i den høje ende — 6,89% og 13,50% af MLL, mod de 5,10% modellen blev kørt på.

Der er en anden fejl som er mere principiel end niveauet: **modellen trak en konstant.**
ATR svinger dagligt. En model der giver hver handel den samme dollarrisiko kan ikke se den
mekanisme der faktisk slår konti ihjel — at en serie tab rammer i en uge hvor ATR er høj og
hver enkelt taber koster det dobbelte.

**Det er fasens egentlige ændring: fra punktestimat til fordeling.** Estimat-invarianten i
§0 siger at der ikke sizes efter et punktestimat. Modellen gør det stadig. Det rettes her.

---

## 2. Afgrænsning

**Denne fase gør IKKE:**

- leder efter en edge eller et signal
- bygger en strategi eller en runner
- bygger blok-bootstrap — det kræver en strategis egen handelssekvens, og den findes ikke
- optimerer noget

**Den regner sizing-gitteret om på målte input og afgør B6.** Det er alt.

Metoderegel 8 gælder: **stop efter hver kørsel.** Ingen konfigurationsændringer ud over de
to der står eksplicit i 4.1, ingen strategiforslag — heller ikke gode. Resultaterne læses
sammen i overblikssessionen først.

---

## 3. Præregistrerede kriterier

Skrevet før noget køres. Disse afgør fasens udfald, ikke en vurdering bagefter.

| # | kriterium | tærskel | hvis det ikke holder |
|---|---|---|---|
| **K1** | **Regressionstjek.** Fodres modellen med konstant ATR 0,168%, NQ 29.639,50 og omkostning $2,472, reproducerer den gitteret fra 2026-09-09 | **hver celle inden for sit 95%-CI** | Koden har ændret mere end inputtet. **Intet nyt tal er troværdigt før dette holder.** Stop og rapportér |
| **K2** | **Passabilitet.** Findes der mindst én celle med **1 kontrakt** hvor P(ruin) ≤ 20% ved WR 40% under den **pessimistiske** brudmodel | **ja/nej** | Evalueringen er ikke passabel med 1 MNQ på 2:1. B5 (1,5:1) eller en anden kontostørrelse genåbnes |
| **K3** | **Højenderisiko på den valgte celle** | **risiko_pct_af_MLL_p90 ≤ 10** | Cellen kan ikke vælges. Estimat-invarianten: go/no-go vurderes på den ende hvor det gør ondt |
| **K4** | **Brudmodellernes spænd på den valgte celle** | **≤ 5 pp forskel i P(ruin)** | Vejen inde i en handel afgør resultatet, og den er umålt. Modellen kan så ikke vælge celle, og C4 (slippage/sti) bliver blokerende |
| **K5** | **Regimestabilitet.** Samme celle vælges når ATR-fordelingen begrænses til de seneste 12 måneder | **samme celle** | Valget er regimeafhængigt. Rapportér begge og lad overblikssessionen vælge |

K1 er der fordi vi ellers ikke kan skelne "tallet ændrede sig fordi inputtet ændrede sig"
fra "tallet ændrede sig fordi jeg skrev modellen om". Det er billigt at teste og dyrt at
undvære.

---

## 4. Opgaver, i rækkefølge

### 4.0 Fire små rettelser først

Alle fire kommer fra fase 1-sessionens efterskrift. De er små, og to af dem kan ellers
producere et resultat der ser rigtigt ud.

**Import-røgtest.** `research/diagnostics.py` og `research/bias_engine.py` kan ikke
importeres — begge trækker `research/daily_bias.py`, som ikke findes. Testsuiten er grøn
fordi ingen test rører dem. Skriv én test der importerer hvert modul i pakken. Den skal
**fejle** nu, på præcis de to. Marker dem derefter eksplicit som ikke-funktionelle —
`skip` med begrundelse, eller flyt dem til en `attic/`-mappe. **Slet dem ikke** uden at
spørge; de er kopieret fra det gamle repo og kan have værdi senere.

**Kalendervagt.** `exchange_calendars` dækker 20 år tilbage og ét år frem fra
*kørselsdatoen*. Uden for vinduet markerer `rth_mask` alle barer som ETH — tavst. Tilføj
en assertion: dækker kalenderen ikke seriens fulde datointerval, så rejs en fejl med
begge intervaller i beskeden. Tre linjer, og den forhindrer et resultat der ligner et
resultat.

**Lås miljøet.** `requirements.txt` siger Python 3.12; `.venv` kører 3.14.4. Skriv de
faktisk installerede versioner ind (pandas 3.0.5, numpy 2.5.3, pyarrow 25.0.1,
databento 0.86.0, exchange_calendars 4.13.2) og ret Python-versionen. **Der er ingen scipy**
— ruinmodellen skal klare sig med numpy, og det kan den.

**Én NQ-pris, læst fra data.** Der er to i omløb: 29.639,50 og 29.138. De giver 13,72% mod
13,49% for samme ATR. Hardkod ingen af dem — læs **sidste luk i serien** og lad alt regne
på den. Skriv den ind i rapportens hoved med sin dato, så et tal aldrig kan læses uden sit
prisniveau.

### 4.1 To konfigurationsrettelser

Begge er direkte følger af fase 1's målinger og er besluttet. Ikke frie ændringer.

**Spread i `config.yaml` under MNQ:** `spread_ticks` står på `1.50` markeret SKØN. Målt
værdi er **1,73 tick i RTH** og **2,17 tick uden for RTH** (92 dage, 2019-2026). Sæt
RTH-værdien og markér den MÅLT med dato. Kan konfigurationen ikke rumme to værdier, brug
RTH-værdien og notér begrænsningen — botten handler i RTH.

**Omkostningsdekomponeringen skal stå eksplicit i koden**, ikke som ét tal — og med
slippage angivet som den **realiserede** middelværdi, ikke som parameteren:

| led | RTH | uden for RTH | status |
|---|---|---|---|
| Kommission, rundtur | $1,22 | $1,22 | **V** — TopstepX |
| Spread, 1 × fuld spread | $0,865 (1,73 tick) | $1,085 (2,17 tick) | **M** — fase 1, med forbehold |
| Slippage, **0,542** tick pr. side | $0,542 | $0,542 | **S** — ikke målt |
| **I alt rundtur** | **$2,627** | **$2,847** | |

**Hvorfor 0,542 og ikke 0,50.** `costs.py` trækker `max(0, N(0,5; 0,5))` tick pr. side.
Afskæringen ved nul løfter middelværdien til 0,5417. Konfigurationen siger 0,50, koden
leverer 0,542, og differencen har aldrig stået nogen steder. **Konfigurationen skal erklære
det tal koden faktisk realiserer.** Vælger I i stedet at ramme 0,50, skal fordelingens
parametre ændres — men gør ikke begge dele stiltiende.

Tjek: med 1,50 tick spread giver regnestykket $2,512, hvilket er præcis det tal fase
1-sessionen målte i koden. Stemmer jeres tal ikke med det, er modellen af `costs.py`
forkert et sted.

**Fase 1's tabeller er regnet med $2,59 og står ved magt** — differencen flytter
risikokolonnen 0,002 pp og be_WR 0,04 pp i værste række. Men $2,627 er tallet fremadrettet.

**Slippage er nu det største uverificerede led**, og afskæringen ved nul betyder også at
modellen aldrig tillader gunstig slippage. Notér begge dele.

Tests grønne efter ændringen.

### 4.2 R trukket fra den målte ATR-fordeling

Dette er fasens kerne. I `research/mll_ruin.py`:

Erstat den faste `ATR_PCT_15M`-konstant med **et træk pr. handel fra den empiriske
ATR-fordeling** for den timeframe og session cellen kører. Empirisk, ikke en tilpasset
fordeling — resample fra de faktisk målte barer. Fordelingens hale er hele pointen, og en
normalfordeling ville skære den af.

**Prisniveau: brug ét fast, nutidigt niveau (NQ 29.138) for alle træk.** Ikke barens
historiske pris. Begrundelsen skal stå som kommentar i koden: MLL'en er $2.000 i dagens
dollar. NQ gik fra ~8.000 til ~29.000 over stikprøven, så samme ATR i procent er 3,6 gange
flere dollar i dag end i 2019. Trak vi prisen med fra baren, ville modellen blande to
regimer og systematisk undervurdere risikoen.

**Sessionen er RTH.** Døgnserien er fortyndet af stille asiatiske timer og beskriver ikke
den strategi vi bygger.

**Bevar de to brudmodeller** (optimistisk/pessimistisk). Bevar mekanikken 1:1 med Combine:
trailet på dagsslutsaldo, bruddet i realtid på urealiseret P&L, låsning ved startsaldo,
konsistensreglen `profit ≥ max(3000, 2 × bedste_dag)`, minimum 2 handelsdage.

**Én antagelse skifter status fra A til V:** modellen antog at ingen position er åben ved
dagsgrænsen, så trailet regnes på en flad konto. Det er nu **verificeret** — Topstep kræver
alt fladt kl. 15:10 CT hver hverdag. Notér det; antagelsen er blevet en regel.

### 4.3 Gitteret

| akse | værdier |
|---|---|
| timeframe | 15m, 5m, 3m, 1m — alle RTH |
| stop_ATR | 1,00 · 0,75 · 0,50 |
| win_rate | 34 · 37 · 40 · 45 % |
| kontrakter | **1** |
| stier pr. celle | 20.000, samme seed |

48 celler. Kør derudover 2 og 3 kontrakter **kun** på den timeframe der vinder, som
referencerækker — ikke som kandidater. 1 MNQ er gulvet, og gitteret skal vise hvad der sker
over det, ikke tilbyde det.

**Nulmodellen er ikke en ekstra celle — den er hele gitterets målestok.** WR-aksens
nederste værdi skal være **cellens egen break-even win rate**, ikke et fast 34%. Den
varierer med timeframe og stopbredde (33,97% på 15m/1,00 ATR, 38,53% på 1m/0,50 ATR), så
et fast tal ville give 1m en skjult edge og 15m en skjult ulempe. Kør altså **fem**
WR-værdier pr. celle: `be_WR` (nul edge) og derefter be_WR + 3, +6, +11 procentpoint.

Rapportér for hver celle **forskellen** mellem strategiens beståelsesrate og nulmodellens,
med konfidensinterval på forskellen. Det er den kolonne der betyder noget, og den skal
hedde `bestaa_pp_over_nulmodel` med sit CI ved siden af.

Begrundelsen skal stå i rapporten: en beståelsesrate på 88% lyder som en edge, men uden
nulmodellen ved man ikke om den kommer fra strategien eller fra at Topsteps regelgeometri
er mild ved den sizing. **Det er også formen på falsifikationstesten for hver eneste
fremtidig strategi vi bygger** — metoderegel 12.

Kør hele gitteret to gange: én gang på fuld historik og én gang på seneste 12 måneder (K5).

### 4.4 Kolonnedisciplin

Tabellerne fra fase 1 var læsbare. Én kolonne var det ikke: `be_WR_pct_netto_p90` kunne
ikke rekonstrueres fra de øvrige uden at gætte definitionen. **Bekræft eller ret den.**
Overblikssessionens definition er:

`be_WR_pct_pXX = (1 + omk_R_pXX) / 3 × 100`, hvor `omk_R_pXX = omkostning / R_usd_pXX`

Den giver 33,66% for 15m RTH p90 — altså et **lavere** tal end p50, fordi en fast
omkostning fylder mindre i et større R. Stemmer det ikke med din, så sig hvilken formel du
brugte.

Regler for alle tabeller i denne fase:

- **Enheden står i kolonnenavnet.** `risiko_pct_af_MLL_p90`, ikke `risiko`.
- **En percentil siger hvad den er percentil af.** `p90` alene er ikke en kolonne.
- **Hvert tal skal kunne spores til en formel i koden.** Skriv formlen i rapporten ved
  siden af kolonnenavnet, som i §5a.
- **Brutto og netto side om side**, ikke i hver sin tabel.
- **Konfidensinterval på hver andel.** Krydser det nul eller den præregistrerede tærskel,
  er cellen uafgjort og skal skrives som uafgjort — ikke afrundet til en konklusion.

### 4.5 Følsomhed på de tilbageværende skøn

Slippage er det eneste rene skøn tilbage i omkostningen. Kør den valgte celle med en
realiseret middelværdi på 0, 0,542 og 1,0 tick pr. side og rapportér hvad det gør ved
P(ruin). Skifter konklusionen mellem 0,542 og 1,0, er C4 blokerende og skal måles før live.

Kør også den valgte celle med spread sat til 1,50 og 2,17 tick. Det målte 1,73 hviler på to
ubekræftede antagelser om Databentos format (at et bbo-snapshot beskriver intervallet før,
og at en quote fremføres i højst 60 sekunder), og ~7% af sekunderne mangler en bbo-record.
**Vi ved ikke hvilken vej den fejl peger** — derfor begge ender.

### 4.6 Opdatér `ANTAGELSER.md`

Disse rækker skifter status. Ret dem, og ret teksten der begrunder dem:

| række | fra | til |
|---|---|---|
| ATR 15m | M, svagt (60 dage, Yahoo) | **M** — fordeling, MNQ, 2019-2026, RTH og døgn adskilt |
| ATR på 5m/3m/1m | ukendt | **M** |
| Kvadratrods-skalering | A | **M** — holder inden for 5% på MNQ i RTH. Afvigelsen er negativ, ikke positiv |
| Spread | S (1,5 tick) | **M** — 1,73 tick RTH, 2,17 uden for |
| omk_R netto | S | **M** afledt af to M'er og ét S (slippage) |
| NQ-prisniveau | 29.639,50 | 29.138 med dato |
| Fladningsregel / ingen position ved dagsgrænsen | A | **V** — Topstep, 15:10 CT |
| Slippage | S | **stadig S.** Nu det største uverificerede led. Realiseret middelværdi 0,542 tick/side, ikke 0,50, og aldrig gunstig |

Tilføj desuden disse rækker — de findes ikke i registeret i dag:

| ny række | status | note |
|---|---|---|
| Spreadmålingens fortolkning af bbo | **A** | Et snapshot beskriver intervallet før; en quote fremføres højst 60 s. Ubekræftet — Databentos dokumentation kunne ikke hentes. ~7% af sekunderne mangler en record |
| `ts_event` er barens åbning | **M, indirekte** | Bekræftet ved at barerne er identiske med Yahoo, ikke ved dokumentation |
| Apparatet er byte-identisk med det gamle repo | **A** | Kan ikke efterprøves. `REAL TRADING BOT` blev ikke fundet på Macen |
| `data/ohlcv.py` følger `_validate_ohlcv`'s kontrakt | **A** | Skrevet ud fra PRD'ens beskrivelse, ikke fra originalen |
| Kalenderdækning | **A** | `exchange_calendars` dækker kørselsdato ±20/+1 år. Uden for: alt markeres ETH, tavst |

Tilføj en række under afsnit 4: **"Prisniveau i ruinmodellen — fast nutidigt niveau, ikke
barens historiske"**, status **A**, med begrundelsen fra 4.2.

---

## 5. Leverancer

| leverance | hvor |
|---|---|
| Rettet `config.yaml` + omkostningsdekomponering | repoet, tests grønne |
| Ruinmodel v2 | `research/mll_ruin.py` |
| K1-regressionstjek med tal | `research/output/mll_ruin_v2.md` |
| Gitteret, fuld historik og 12 måneder | samme dokument + `.csv` |
| Følsomhed på slippage | samme dokument |
| Opdateret `ANTAGELSER.md` | repoets rod |
| Tests grønne | `.venv/bin/python -m pytest tests/ -q` |
| **Kompakt tabel i chatten** | maks ~15 linjer, enheder i kolonnenavnene, CI med |

Tabellen i chatten er ikke valgfri. Mads er ofte på telefonen og skal kunne læse resultatet
uden at åbne en fil. Vis **kun rækkerne for 1 kontrakt ved WR 40%** i chatten — resten hører
i filen.

---

## 6. Tilbage til overblikssessionen

Når fasen er kørt, rapportér disse seks ting:

1. **Holdt K1?** Med tal. Holdt den ikke, stopper alt andet.
2. **Holdt K2-K5?** Hvilke, med hvilke tal.
3. **Hvilken celle peger gitteret på** — timeframe og stopbredde, med p90-kolonnen og
   P(ruin) under begge brudmodeller som argument.
3b. **Hvad giver nulmodellen i den celle?** Beståelsesrate ved nul edge. Det tal er
   referencepunktet for hver strategi vi senere måler, og det skal stå alene.
4. **Hvor meget flyttede fordelingen resultatet** i forhold til konstanten? Det er fasens
   metodiske pointe og skal stå som ét tal.
5. **Skiftede cellen mellem fuld historik og 12 måneder?**
6. **Hvilke rækker i `ANTAGELSER.md` skiftede status**, og hvilke S'er er tilbage på
   kritisk vej?

**Ingen strategiforslag i rapporten.** Heller ikke gode. Det er metoderegel 8, og den findes
fordi den er blevet brudt før.
