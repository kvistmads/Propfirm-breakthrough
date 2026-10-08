# B4 kandidat 3 — tillæg: læsninger og optælling, før kørslen

**Skrevet:** 2026-10-08 af overblikssessionen. Det er skrevet efter Code's trin 1 (kode
7b8487d, optælling 6f5d4ad) og **før** den rigtige kørsel. Ingen R, vinderrate eller
udfald er set.

**Gyldighed:** tillægget gælder, når ejeren committer det. Commit'en er ejerens
godkendelse. `b4_k3_vending.md` gælder uændret, undtagen hvor dette tillæg siger andet.

## 1. Svar 5

Ejeren committede præregistreringen uden at rette læsningen af svar 5 (73e9b26).
**5A gælder:** stoppet ligger 2 × ATR fra indgangen.

## 2. Code's læsninger — godkendt

Alle 20 i docstringen i `research/b4_k3_vending.py` er godkendt uden ændringer. De tre,
der kan flytte noget:

| nr | læsning | hvorfor den er rigtig |
|---|---|---|
| 7 | Stoppet måles fra fyldprisen: næste bars åbning med 0,5417 tick slippage imod. Det ligger 2 × ATR_i derfra, rundet væk fra fyldet, og `risiko_pt = \|fyld − stop\|` | Det er den pris handlen faktisk har. R regnes fra den, som `simuler_handel` gør |
| 9 | N-tid trækker fra modellens egne signalminutter, ét pr. handelsdag, med tilbagelægning | Det er §6's "variantens egen fordeling, samlet over alle dage". Alle signalbarer, også senere på dagen, ville give nulmodellen en senere tidsprofil end modellen og blande tidspunkt ind i sammenligningen |
| 11 | Hver variant trækker uafhængigt i hver gentagelse | Det gør Westfall-Young lidt forsigtigere. Det er den rigtige side at fejle på |

Læsning 6 og 10 sker 0 gange i data.

## 3. Det optællingen viser — skrevet ned før udfaldene

- **Ved k = 1,0 er signalet næsten betingelsesløst.**
  - Der er et signal på alle 1.168 dage med retning, og medianen er kl. 09:01 CT.
  - N-tid's pulje har kun 30 forskellige minutter (09:00–09:29).
  - k = 1,0 kan derfor næsten ikke skilles fra N-tid. Det var forventet i §12.
  - k = 2,0 (688 handler, median kl. 09:45) er den variant, hvor lyset reelt vælger.
- **Stoppets størrelse:** `risiko_pt` har median 23–27 point. Det ligner videoens 25
  point, selv om prisniveauet i 2019–23 var lavere. Det er en tilfældighed i målestokken,
  ikke en kalibrering.
- **Omkostning:** `omk_R` har median 0,05–0,06 og p90 0,11–0,14. Den er tungest i 2019.
- **Retning:** der er flere short- end long-handler, fordi 637 dage åbner op og 531 ned.
- **Ingen handel er udfaldet:** loftet på 50 kontrakter binder aldrig, der er ingen huller
  i næste minut, ingen ruller i handelstiden og ingen manglende barer.
- **MDE (Šidák 3):** 0,106, 0,107 og 0,138 R. Alle ligger under 0,20, så betingelsen i
  §7 er opfyldt.

## 4. Betingelser for den rigtige kørsel

1. **Koden står fast.** Kørslen sker fra commit 6f5d4ad uden ændringer i `research/*.py`.
   Ændres noget, køres regressionstjekkene i §11.3 igen, og ændringen oplyses.
2. **R = 500.** Tidsmålingen forventer cirka 1¾ minut inklusive regressionstjekket.
3. **Rapport efter §10.** Bagefter: stop. §8 anvendes mekanisk og læses sammen med ejeren.
