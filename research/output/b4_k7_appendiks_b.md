# B4 kandidat 7: appendiks B læst (§11.7)

**Læst:** 2026-10-10 af Code, før kørslen. Kilden er EDHEC-udgaven af arbejdspapiret
(Fisher College of Business WP 2025-03-001, dateret 14. januar 2026), appendiks B (s. 52–53),
afsnit 1.2 (s. 9–16) og afsnit 4 (s. 37–38). Teksten er trukket ud af PDF'en
maskinelt, så formlernes sænkede tegn og absolutstreger kan være tabt. Koden er ikke rettet.

| punkt i §11.7 | artiklen | præregistreringen | afviger? |
|---|---|---|---|
| s^δ hver dag eller kun ved rebalancering | B.1: `Threshold signal^δ_(t+1) = w̃^T_(t+1)(w^T_t; R^SP, R^10Y) − 60%`, altså vægten efter drift og før en eventuel rebalancering, hver dag | §4c: samme | nej |
| Betingelse for rebalancering | Teksten: "exceed their targets by more than δ". Formlen er udtrukket som "w^T − 60% ≥ δ", og absolutstregerne kan være tabt. Afsnit 1.2 bruger \|Threshold Signal^δ\| ≥ δ om rebalanceringsdagene | §4c: \|s\| ≥ δ | uklart: ≥ eller >, og om der er absolutstreger. Med flydende tal betyder ≥ mod > i praksis intet. Uden absolutstreger ville der kun blive rebalanceret, når aktierne er overvægtede |
| Båndgitteret | "0%–2.5% with increments of 0.1%" (formel 2), altså 26 bånd. 0–2% og 0,1–2,5% er kun robusthed (tabel D.6) | §4c: 0,000–0,025, 26 bånd | nej |
| Kalendersignalet | B.2: rebalancering på månedens sidste hverdag og signalet før rebalanceringen | §4d: samme | nej |
| "Sidste uge" i K | "if t falls within the last week of a month". week4_t = Dummy5Days_t, og R_(t+1) regresseres på signal_t · week4_t, altså signaldagen t og 5 dage | §4e: signaldag t, 5 sidste XNYS-dage | nej |
| "Første dag" i K | "on the first business day of a new month, the modified Calendar signal is set to sign(Calendar Signal_−4)". R^Strategy_(t+1) = (R^S&P − R^10y)_(t+1) · w_t, så positionen sat på den første dag gælder afkastet dagen efter | §4e: t er månedens første XNYS-dag, sign(c_(t−4)) | nej, så vidt teksten rækker. Sænket "−4" er udtrukket uden "t", så "t−4" er en læsning. Teksten siger ikke, hvorfor det er c fra 4 dage før og ikke månedens sidste c |
| Vægtningen i den samlede strategi | w^Strategy er gennemsnittet af −Threshold/1,5% og det modificerede kalendersignal. Begge signaler har cirka 11,6% årlig volatilitet | §4e (diagnose): ½(w^T + w^K) | nej |
| Strategiens ben | Long-short S&P mod 10-årige statsobligationer | Kun aktiebenet (MES) | kendt og præregistreret (§2) |
| Startvægt | 60% ved t = 0 | 0,60 ved første close i 2016 | nej |

**Konklusion:** jeg fandt ingen afvigelse, der kræver et tillæg. To ting er uklare, fordi
teksten er trukket maskinelt ud af PDF'en:

1. om rebalanceringsbetingelsen har absolutstreger (afsnit 1.2 tyder på det);
2. om "Calendar Signal_−4" betyder c_(t−4).

Begge er markeret [tvivl] i modulets docstring (læsning 4 og 6).
