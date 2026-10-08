# B4 kandidat 5 — UDKAST: VWAP-trend efter Zarattini og Aziz (2023)

**Status: udkast, ikke en præregistrering.** Skrevet 2026-10-08 af overblikssessionen og
gemt efter ejerens ønske, så det er klar, når kandidat 4 er læst. Spørgsmålene i §3 skal
besvares, og præregistreringen skal skrives og committes, før Code bygger noget.
**Kilde:** `research/kilder/zarattini_aziz_vwap_noter.md` (hele artiklen læst 2026-10-08,
SSRN 4631351).
**Baggrund:** ejeren ønskede 2026-10-08 at teste den dokumenterede, trendfølgende VWAP-
strategi ved siden af EMT (kandidat 4). Så får vi svar på både tilbageløbet mod VWAP og
trenden væk fra den.

---

## 1. Strategien, som artiklen beskriver den

| emne | regel |
|---|---|
| VWAP | Regnes kun på børsens åbningstid fra 9:30 New York-tid, med (high+low+close)/3 × volumen pr. minut |
| Første handel | Når første 1m-lys er lukket kl. 9:31, går man long over VWAP og short under |
| Vending | Lukker et 1m-lys på den anden side af VWAP, vender man positionen. Et kryds inde i lyset uden lukning udløser intet |
| Altid i markedet | Der er altid en position, og det giver cirka 15 handler om dagen (21.967 på 5¾ år) |
| Slut | Alt lukkes kl. 16:00 New York-tid. Intet natten over |
| Resultat på QQQ | Sharpe 2,1, største drawdown 9,4%, kun 17% vindere, men gevinsterne er 5,7 gange større end tabene. VWAP slog SMA 9, 20, 100 og 200 |
| Tid på dagen | Gevinsten kom fra 9:30–12:00 og 15:00–16:00 New York-tid. Midt på dagen var der intet |

## 2. Fire ting, der betyder noget for os

1. **Omkostningen er cirka lige så stor som gevinsten.** Artiklens egne tal giver cirka
   0,93 basispunkter af positionens værdi pr. handel. På MNQ koster vores $2,627 pr. handel
   cirka 0,9 bp ved NQ 15.000 og 1,7 bp ved NQ 7.500.
   - Artiklen regnede med næsten gratis handel på ETF'en og ingen slippage.
   - På 1m med rigtige futures-omkostninger skal vi derfor forvente omkring break-even.
     5m-udgaven, som forfatterne selv nævner, handler sjældnere og kan klare sig bedre.
2. **Den passer ikke til "én handel om dagen".** Pointen er netop at være i markedet hele
   dagen og vende ved hver krydsning. Den har heller intet fast stop, så den kan ikke måles
   i R.
3. **Risikoen pr. dag:** værste dag var −5,1% af positionens værdi. 1 MNQ er cirka
   $58.000 ved NQ 29.000, så en dårlig dag med bare én kontrakt kan komme tæt på Topsteps
   grænse på $2.000. Hvor stor positionen må være, afgør ruinmodellen bagefter.
4. **Vores test er en gentagelse, ikke en uafhængig bekræftelse.** Artiklen dækker
   2018–2023, og vores in-sample er 2019–2023. Til gengæld ligger vores holdout fra 2024
   efter artiklen kom ud. Holder strategien på MNQ, er holdout en ren test af, om den også
   virker efter offentliggørelsen.

## 3. Spørgsmålene til kandidat 5 (ubesvarede)

Anbefalingen står først.

**1. Handelstider**
- **A: som artiklen, så tæt som Topstep tillader.** Første handel kl. 15:31 dansk tid,
  vendinger hele dagen og fladt kl. 21:59. Topstep flader selv kl. 22:08. Det afviger fra
  vores regel om fladt 21:50, men artiklens bedste time er den sidste.
- B: vores faste regler, altså ingen nye handler efter 21:30 og fladt 21:50. Så mister vi
  en del af den sidste time.

**2. Antal handler**
- **A: alle vendinger, som i artiklen.**
- B: kun den første handel.

**3. Varianter**
- **A: 1m og 5m × hele dagen eller uden 18:00–21:00 dansk tid (12–15 New York-tid) = 4
  varianter.** Tælleren går fra 37 til 41. Pausen midt på dagen er forfatternes forslag ud
  fra deres egne data, så den tæller som variant.
- B: kun 1m, hele dagen, præcis som artiklen. Det er 1 variant.

**4. Nulmodel**
- **A: samme handelstidspunkter, men med tilfældig retning pr. handel.** Den har samme
  antal handler og samme omkostning, men ingen VWAP-information. Den svarer på, om VWAP's
  retning bærer noget.

**5. Mål og afgørelse**
- **A: netto-dollar pr. dag pr. MNQ-kontrakt, med konfidensinterval over dagene.** Fryses
  kun, hvis den slår nulmodellen (p_FWE ≤ 0,05), og intervallets nedre grænse er over 0.
  Bagefter afgør ruinmodellen, om og med hvor mange kontrakter den kan bestå Combinen.

Rapporten skal også vise, hvad omkostningen pr. handel højst må være, før strategien går i
nul. Det er det tal, der fortæller mest om den.

## 4. Noter til præregistreringen, når spørgsmålene er besvaret

- **Omkostning:** $2,627 pr. round trip dækker kommission, en hel spread og slippage
  0,5417 tick pr. side (fase 1's dekomponering). Alle ordrer er markedsordrer, så der
  lægges ingen ekstra slippage på. Det skal begrundes i præregistreringen, fordi kandidat
  1–4 lagde stop-slippage oveni.
- **Udførelse:** et lys lukker over eller under VWAP, og handlen sker ved næste lys'
  åbning.
- **VWAP:** regnes fra 08:30 CT, kun på RTH-barer, med hlc3 × volumen. Det er artiklens
  definition og ikke den samme som kandidat 4's anker kl. 17:00 CT.
- **Tidsserien:** rullerne ligger kl. 18–19 CT, uden for RTH, så RTH-VWAP påvirkes ikke.
- **Diagnoser:**
  - break-even-omkostning pr. handel;
  - handler pr. dag;
  - hit ratio og gevinst/tab-forhold sammenlignet med artiklens 17% og 5,7;
  - fortjeneste fordelt på tid på dagen sammenlignet med artiklens figur 7;
  - værste dag i dollar pr. kontrakt (til ruinmodellen);
  - pr. år.
