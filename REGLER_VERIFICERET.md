# Verificerede regler — Topstep og CME

**Formål:** ét sted hvor hver regel står med sin **ordrette kilde og sit link**. Dette
dokument indeholder kun ting der er slået op hos primærkilden. Modelantagelser, skøn og
egne målinger hører i `ANTAGELSER.md` — de to må ikke blandes.

**Verificeret:** 2026-09-13 af overblikssessionen. Kun `help.topstep.com`, `topstep.com`
og `cmegroup.com`. Ingen anmeldelsessider, YouTube, Reddit eller affiliate-blogs.
Gennemgået to gange: én bred søgning pr. område, derefter uafhængig genlæsning af de fund
der ændrer et tal i modellen.

> **Regler ændrer sig.** Fem af rækkerne nedenfor var forkerte i vores eget register da
> denne gennemgang begyndte, og to af dem stod som verificerede. **Slå dem op igen før
> første rigtige handel**, og igen før hvert trin. Datoen øverst er dokumentets
> holdbarhedsstempel.

---

## 1. Kontrakten (CME)

| regel | værdi | kilde |
|---|---|---|
| MNQ kontraktenhed | **$2 × Nasdaq-100-indekset** | "CONTRACT UNIT — $2 x Nasdaq-100 Index". Rulebook kap. 361, regel 36101: "Each futures contract shall be valued at $2.00 times the Nasdaq-100 Index" |
| MNQ mindste prisspring | **0,25 indekspoint = $0,50** | "Outright: 0.25 index points = $0.50". Regel 36102.C. Kalenderspread: 0,05 point = $0,10 |
| MNQ første handelsdag | **6. maj 2019** | "The following futures contracts are available to trade starting May 6, 2019". Clearing-advisory Chadv19-118 |
| Maintenance performance bond, sep. 2026 | 4.220 USD long / 3.972 USD short | CME margin-side. **Uden betydning for os** — Combine og XFA er simulerede, og Topsteps egne positionslofter binder i stedet |

CME publicerer **ikke** "initial margin" eller "day-trade margin" — det er broker-begreber.

---

## 2. Handelstider

| | CT | dansk (sommer) | kilde |
|---|---|---|---|
| CME Globex åbner søndag | 17:00 | 00:00 | Contract specs, hentet 13-09-2026 |
| Daglig lukning | **16:00** | 23:00 | "5:00 p.m. - 4:00 p.m. CT" |
| Vedligeholdelse | **16:00–17:00** | 23:00–00:00 | "daily maintenance period from … 4:00 p.m. - 5:00 p.m. CT" |
| Fredag lukker | 16:00 | 23:00 | |
| US RTH | 08:30–15:00 | 15:30–22:00 | |

> **Uafklaret: findes der stadig en 15-minutters pause 15:15–15:30 CT?** CME's egne kilder
> er uenige. De aktuelle contract specs nævner ingen intradag-pause. En ældre Micro
> E-mini-FAQ og SER-8784 (2021) nævner den. Et ældre faktakort angav lukning 16:15 og
> pause 15:15–15:30 — det er hvor tallet i vores tidligere version kom fra.
>
> **Uden betydning for strategien**, fordi vi er flade 14:50 CT. Men kod ikke en
> sessionsfilter på den uden at holde den op mod det faktiske datafeed først.

### Tidsforskellen mellem CT og dansk tid — verificeret 2026-09-19

Tabellen ovenfor viser dansk sommertid. **Forskellen er 7 timer både sommer og vinter**;
kun i de uger hvor USA og EU står på hver sin side af et skift er den 6.

| regel | værdi | ordret kilde |
|---|---|---|
| USA, sommertid begynder | 2. søndag i marts, 02:00 lokal tid | NIST: "begins at 2:00 a.m. on the second Sunday of March". Energy Policy Act of 2005 |
| USA, sommertid slutter | 1. søndag i november, 02:00 lokal tid | NIST: "ends at 2:00 a.m. on the first Sunday of November". For 2026: "from March 8 at 2 a.m. (local time) to November 1 at 2 a.m." |
| EU, sommertid begynder | sidste søndag i marts, 01:00 GMT | Direktiv 2000/84/EF art. 2: "at 1.00 a.m., Greenwich Mean Time, on the last Sunday in March" |
| EU, sommertid slutter | sidste søndag i oktober, 01:00 GMT | Direktiv 2000/84/EF art. 3: "at 1.00 a.m., Greenwich Mean Time, on the last Sunday in October" |
| Danmark, 2026 | 29. marts – 25. oktober 2026 | borger.dk: "Sommertiden begynder søndag den 29. marts 2026 og slutter søndag den 25. oktober 2026". Hjemmel: lov om anvendelse af sommertid og anordning om sommertid fra 2002 |

**Handelsdage med 6 timers forskel:** 26.–30. oktober 2026, 15.–25. marts 2027 (26. marts
er langfredag) og 1.–5. november 2027. Datoerne for 2027 er afledt af reglerne ovenfor og efterprøvet med
IANA-tidszonedatabasen (`America/Chicago` mod `Europe/Copenhagen`) — de står ikke ordret hos
nogen af kilderne.

Kilder: [NIST, Daylight Saving Time Rules](https://www.nist.gov/pml/time-and-frequency-division/popular-links/daylight-saving-time-dst) ·
[EUR-Lex, direktiv 2000/84/EF](https://eur-lex.europa.eu/LexUriServ/LexUriServ.do?uri=CELEX:32000L0084:EN:HTML) ·
[borger.dk, Sommertid](https://www.borger.dk/miljoe-og-energi/Energi/Sommertid)

---

## 3. Trading Combine, $50K

| regel | værdi | ordret kilde |
|---|---|---|
| Profitmål | $3.000 | Prissiden, $50K-rækken |
| Maximum Loss Limit | $2.000 | Tabel: "$50K \| $2,000" |
| MLL trailer på | **dagsslutsaldo, aldrig nedad** | "The MLL is a trailing limit. It rises as your end-of-day balance grows, but never moves down." |
| MLL låser | **ved startsaldo** ($50.000, nås ved dagsslut $52.000) | "Once it reaches your starting balance, it locks permanently." |
| MLL brydes på | **realtid, urealiseret tæller med** | "monitored in real time throughout the session. Both realized and unrealized P&L count toward it. If your Net P&L hits the limit at any point during the day, your account is liquidated immediately." Og: "Final balance above the limit doesn't matter. The breach happened first." |
| **Brud i Combine** | **konto kan ikke fundes før Reset** — ikke permanent | "liquidated for the rest of the trading day and becomes ineligible for funding until you Reset" |
| Daily Loss Limit | $1.000, **valgfri** | "The Daily Loss Limit (DLL) is optional in the Trading Combine® and Express Funded Account® (XFA)." |
| DLL valgt ved køb | **permanent, kan ikke fjernes** | "Daily Loss Limit at checkout is fixed (no changes later)" / "Unlike Daily Loss Limits set at purchase, manual limits can be adjusted or removed at any time." |
| DLL-brud | flader dagen, **ikke** et regelbrud | "Triggering it is not a rule violation — it's a forced break for the rest of that session." Positioner flades, ordrer annulleres, ingen nye handler før 17:00 CT næste session |
| Minimum handelsdage | 2 | "You can pass in as few as two days" |
| **Konsistens** | **55%** | "Best Day Profit ÷ Total Profit = Best Day %" · "If it exceeds that, your Profit Target increases." · "To find your new Profit Target: Best Day ÷ 0.55 = Total Profit Needed." · "55% is a hard line. It is not rounded, and there is no buffer." |
| **Tidsgrænse** | **ingen** | "No time limit for passing." Abonnementet løber til man består eller opsiger |
| Positionsloft, $50K | **5 minis / 50 mikroer** | Combine-parametre. "Micros and minis count at a 10:1 ratio." Fast loft, ingen optrapning |
| Pris | $49/md + $149 aktivering, **eller** $95/md uden aktivering | Prissiden, opdateret 20-07-2026 |
| Refusion | ingen efter 28 dage eller efter nogen handel | "After 28 days or if any trading has occurred, refunds are not available." |

**Konsistensreglen i model-form:** bestået kræver
`samlet profit ≥ max(3.000, bedste_dag / 0,55)`.
Topsteps eget eksempel: "$1,650 best day ÷ 0.55 = a $3,000 Profit Target." En bedste dag
på $1.650 er altså grænsen ved et mål på $3.000.

> **Topstep modsiger sig selv i ordlyden.** Combine-parametersiden og brødteksten i
> konsistensartiklen siger "55% **of your Profit Target**", mens formlen og
> regneeksemplet i samme artikel siger "Best Day ÷ **Total Profit**". Regneeksemplet er
> det operative. **Model efter formlen, ikke efter brødteksten.**

---

## 4. Express Funded Account (XFA)

| regel | værdi | ordret kilde |
|---|---|---|
| Natur | **simuleret, men betaler rigtige penge** | "Topstep pays you real money based on your simulated trading results." |
| Startsaldo | $0 | "Your balance starts at $0 and grows from your trading profits." |
| MLL, $50K | $2.000, trailer på højeste dagsslutsaldo | "This limit is based on your highest end-of-day balance and does not go down if you lose money the next day." |
| MLL låser | **ved $0 når saldoen når $2.000** | "Once your balance reaches $2,000, the MLL locks at $0 permanently." |
| **Brud i XFA** | **kontoen lukkes permanent** | "permanently closed. Back2Funded may be available if you're eligible." |
| Udbetalingsvej 1 — Standard | 5 vindende dage à $150+ net | "5 winning days of $150+ Net P&L" |
| Udbetalingsvej 2 — Konsistens | **3 handelsdage + 40% konsistens** | "3 days with 40% consistency target". Formel: "Largest Winning Day ÷ Total Net Profit" |
| **40%-reglen er valgfri** | **ja — det er en alternativ vej, ikke en spærring** | "2 paths. 1 goal." Overskrides 40%, sker der ingenting ud over at man ikke kan bruge den vej: "keep trading to bring that percentage down." |
| **Udbetalingsloft, $50K** | **$2.000 (Standard) / $3.000 (Konsistens)** | Loftstabel pr. kontostørrelse. $5.000 er **$150K**-kontoens loft |
| **Loftet fordobles med frivillig DLL** | **$4.000 / $6.000** | Payout-politikken |
| Minimum udbetaling | $125 | |
| Profitdeling | 90/10 | |
| Efter hver udbetaling | tælleren nulstilles, MLL sættes til $0, konsistens regnes forfra | "Your MLL is set to $0 regardless of where it was before." · "Payout eligibility must be met again from scratch." |

---

## 5. Live Funded Account (LFA)

| regel | værdi | ordret kilde |
|---|---|---|
| Natur | **rigtige markeder, rigtig kapital** | "Real capital. Real markets." |
| Likvidationsgulv | **$1.000, fast — trailer ikke** | "you will need to make sure your account balance stays above $1,000 (positive)" |
| **Daily Loss Limit, $50K** | **$2.000, skalerer med saldoen** | Hjælpeartiklen om LFA-parametre. **Ikke det samme som gulvet** — bland dem ikke |
| Startkapital | 20% til rådighed straks, minimum $10.000 | |
| Reserven | 80% frigives i **4 trin à 25%**, ved $3.000 nettoprofit pr. trin på $50K | "You cannot unlock multiple tiers with a single large win — each threshold requires net profit since the last expansion." |
| Udbetaling | 5 benchmark-dage à $150+ pr. cyklus → op til 50% af saldoen, **uden dollarloft** | |
| Daglige udbetalinger | efter **30 ikke-sammenhængende** dage à $150+ → **én gang pr. dag**, min. $125 | Bemærk: "once per day", ikke "pr. hverdag" som vi tidligere skrev |
| Konsistensregel | **findes ikke på LFA** | Eneste analoge: samlede udbetalinger må ikke overstige 90% af startsaldo plus nettoprofit |
| **Markedsdata** | **CME er dækket af Topstep — $0 for os** | "Topstep covers 1 exchange for all LFA Traders", CME som standard. CME dækker "ES, MES, NQ, MNQ, RTY, M2K…". Øvrige børser $133/md stykket; alle fire ≈ $540/md, hvoraf $399 af egen lomme. **Handler vi kun MNQ, er datakosten nul på alle tre trin** |
| Platformslicens | **egen regning** på LFA, modsat Combine | |
| Børsgebyr pr. rundtur | ES/NQ $3,80, CL $1,54, GC $4,24 | Bemærk: **højere end i Combine** |

**Rettet 2026-09-17:** de $399 gælder kun hvis man vil handle uden for CME. MNQ ligger på
CME, som Topstep dækker. **Datakosten er altså nul på alle tre trin så længe vi kun handler
MNQ.** Tilbage står platformslicensen, som man selv betaler på LFA, og de højere børsgebyrer
pr. rundtur.

### Op- og nedkald mellem XFA og LFA

Verificeret 2026-09-17. **Dette er den vigtigste regel vi har fundet for en bot, fordi den
ikke er et tal.**

| | |
|---|---|
| Fører fem vindende dage til LFA? | **Nej.** "Do I need 5 payouts to move to Live? No. All decisions are based on overall performance and Risk Team review." De fem dage er et **udbetalingskrav**, ikke en forfremmelse |
| Hvem beslutter | Topsteps risikoafdeling, ud fra konsistens, risikostyring, positionsstørrelse, brug af stops, tidligere opkald og udbetalingshistorik |
| Startsaldo på LFA | 20% af den samlede XFA-saldo, dog højst kontostørrelsen, minimum $10.000 |
| Kan man kaldes ned igen? | **Ja, uden varsel.** "There is no warning before being called down" |

**Grunde til nedkald, ordret:** væsentligt træk på den udlånte kapital · **gentagne brud på
Daily Loss Limit** · "activity that resembles gambling rather than disciplined trading" ·
"continuous over-leveraging, especially during inflection points" · revenge trading.

> **Konsekvensen for en automatiseret strategi.** XFA er ikke en trappe man automatisk går
> op ad — den kan køre i det uendelige med rigtige udbetalinger, og opkald til LFA er en
> skønsmæssig vurdering af **adfærd**. En bot der gentagne gange rammer DLL'en, skalerer op
> efter tab, eller tager maksimal position ind i nyheder, bliver bedømt som udisciplineret
> af et menneske — uanset hvad forventningsværdien siger.
>
> **Det er en bindende designregel vi ikke kan modellere som et tal**, og den skal stå i
> strategiens krav: botten skal ikke bare overholde reglerne, den skal *se* disciplineret ud
> for en anmelder.

---

## 6. Omkostninger i Combine og XFA

| post | værdi | kilde |
|---|---|---|
| **MNQ rundtur, alt inklusive** | **$1,22** | "Micro E-mini NASDAQ 100 (MNQ) — $1.22" under kolonnen "Round-Turn Cost (RT)" |
| Dekomponering | NFA $0,02 + børsgebyr $0,70 + kommission $0,50 | Topstep viser opdelingen for MES, som har samme totale $1,22 og samme CME-mikrogebyr |
| Pr. side | $0,61 | "Each side (Buy or Sell) incurs half the total" |
| **Lægges der noget oveni?** | **Nej.** Børs- og NFA-gebyr er allerede med | "Exchange fees are set by the exchange and do not include the regulatory fee" — men de indgår i totalen |
| API-adgang | $29/md, $14,50 med koden `topstep` | "valid every month with no end date" |
| Level 1-markedsdata | **gratis** i Combine og XFA, alle fire børser | |
| Level 2 | $38/md, **ikke prorata**, gebyres den 28. | |

Dekomponeringen for MNQ specifikt er **udledt** fra MES-rækken; Topstep publicerer kun
opdelingen for MES. Totalen $1,22 er publiceret direkte for MNQ.

---

## 7. Automatiseret handel

| regel | ordret kilde |
|---|---|
| Bots er tilladt | "Custom automated strategies and bots are allowed via the TopstepX / ProjectX API, subject to standard platform rules and our prohibition on high frequency trading (HFT)." |
| **VPS, VPN og fjernservere er forbudt** | "All trading activity must originate from your personal device." · "The use of VPS, VPNs, and remote servers is prohibited by Topstep's Terms of Use." · "Running automation on a VPS can result in account suspension or removal from the program." |
| Hvor grænsen går | "The line is order transmission: your server can watch and record, but it cannot trade." |
| Ansvar | "You remain the owner of your bot and are solely responsible for its design" |
| Ingen fortrydelse | "Orders executed via the API are final — no review, adjustment, or reversal." |

**En egen server må gerne overvåge og logge.** Kun ordreafsendelsen skal komme fra Macen.
Det åbner for at overvågning og alarmering kan ligge et andet sted end eksekveringen.

---

## 8. Forbudt adfærd — relevant for en bot

| forbud | ordret kilde | binder det os? |
|---|---|---|
| Udnyttelse af SIM-fills | "Running 'scalping' algorithms in the SIM environment to take advantage of unrealistic fills" · "Using tight brackets or auto-breakeven to take advantage of favorable fills" | Tærsklen er "hundreds if not thousands, of trades in a day (usually with an average duration measured in seconds, not minutes)". **Vi ligger på 1-3 handler dagligt. Binder ikke** — men auto-breakeven er nævnt eksplicit, og det er en teknik vi har overvejet |
| Maksimal position ind i planlagte nyheder | Forbudt ifølge "Prohibited Trading Strategies" | **Binder.** Botten skal kende økonomiske kalendere og size ned. Nyt C-punkt |
| Handel under nyheder generelt | **tilladt** — "Topstep doesn't require you to flatten positions during economic releases" | Men "Trades impacted by economic releases are not eligible for exceptions or Reset credits" |
| Kryds-konto-hedging, koordineret handel, account stacking | "holding opposite positions across multiple accounts simultaneously" · "repeatedly hitting the Maximum Loss Limit in one account and switching to another" | Binder hvis vi nogensinde kører flere konti. **Én konto ad gangen** |
| "Unfair technology" | "using software, AI, ultra-high speed systems, or mass data entry to gain an unfair advantage" | Bredt formuleret. En 15m-bot på 1-3 handler er ikke det de sigter efter, men formuleringen er elastisk |

Sanktioner spænder fra sletning af en handelsdag til permanent lukning og nægtet udbetaling.

---

## 9. Hvad denne gennemgang rettede

| # | stod i vores register | rigtigt | betydning |
|---|---|---|---|
| 1 | Konsistens 50%, markeret **V** | **55%** | Modellen har regnet strengere end virkeligheden i både v1 og v2. Beståelsesrater er undervurderet |
| 2 | XFA udbetalingsloft $5.000, markeret **V** | **$2.000** på $50K | Vi overvurderede udbetalingskapaciteten med 2,5× |
| 3 | XFA 40% konsistens som krav | **valgfri alternativ vej** med *højere* loft | Ingen spærring at designe udenom. Det er en mulighed, ikke en risiko |
| 4 | LFA-datapris ukendt (C6) | **$133 pr. børs pr. md, ~$399/md** | C6 er lukket. LFA er dyr at holde |
| 5 | LFA udbetaling "én gang pr. hverdag" | "once per day" | Mindre, men forkert |
| 6 | LFA havde kun et gulv på $1.000 | **plus en skalerende DLL på $2.000** | Manglede helt |
| 7 | Børspause 15:15–15:30 CT som faktum | **uafklaret** — CME's egne kilder er uenige | Uden betydning, vi er flade 14:50 |
| 8 | intet om brud-asymmetri | **Combine-brud kræver Reset. XFA-brud lukker kontoen permanent** | Spor B's ruin er terminal. Ruinmodellen for XFA skal se anderledes ud end Combines |
| 9 | intet om positionsloft | 5 minis / 50 mikroer på $50K | Binder ikke ved 1-3 mikroer, men skal stå |
| 10 | intet om DLL ved køb | **permanent hvis valgt ved checkout** | En engangsbeslutning, ikke en indstilling |
| 11 | intet om nyhedsregel | maksimal position ind i planlagte nyheder er forbudt | Nyt C-punkt. Botten skal kende kalenderen |
| 12 | intet om DLL og udbetalingsloft | **frivillig DLL fordobler XFA's loft** til $4.000/$6.000 | Gør DLL til en afvejning, ikke bare en spærring |

**To af de rettede rækker stod som V.** Det er anden og tredje gang et V viser sig ikke at
holde. Konklusionen er ikke at være mindre grundig — det er at **V skal have en ordret
citat og et link, ellers er det ikke et V.** Derfor findes dette dokument.

---

## 10. Hvad der stadig ikke kunne verificeres

| spørgsmål | hvorfor ikke |
|---|---|
| Findes 15:15–15:30-pausen stadig? | CME's aktuelle specs og deres ældre FAQ er uenige. Skal måles i datafeedet |
| MNQ's egen gebyrdekomponering | Topstep publicerer kun opdelingen for MES. Totalen for MNQ er publiceret |
| Databento-saldoen | Portalen kræver login |
| Præcis definition af "high frequency trading" hos Topstep | Ikke kvantificeret nogen steder. Kun SIM-fill-tærsklen giver en indikation |
