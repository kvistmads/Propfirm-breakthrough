# B4 kandidat 1 — præregistrering: optælling før trin 2

**Skrevet:** 2026-09-23 af overblikssessionen, før kørslen. Committes før kørslen.
**Grundlag:** `research/kilder/photon_sd_video_noter.md` (videoens otte kriterier),
`research/output/b4_k1_trinA_laest.md` og `research/output/b4_k1_motorrettelse.md`.
Definitionerne i §3 er aftalt med ejeren 2026-09-23.

**Kørslen ser ikke på udfald.** Den tæller signaler, filterværdier og scorer. Ingen handel
simuleres, intet R regnes, og intet lægges til tælleren. N står på 6.

---

## 1. Hvorfor

Trin 2 tester videoens egen påstand: jo flere af kriterierne en zone opfylder, jo bedre.
Hver zone får en **score** fra 0 til 7. Hovedtesten er om middel netto-R stiger med
scoren; de handelbare varianter er "brud på struktur alene" og tærskler på scoren.

Hvor tærsklerne kan ligge, afhænger af hvor mange signaler der er tilbage ved hver score.
Det tælles her, før et eneste udfald er set.

## 2. To spor

| spor | handelstimeframe | højere timeframe | hvorfor |
|---|---|---|---|
| **A** | 15m | 1h | Vennens timeframe. Det trin A testede |
| **B** | 5m | 15m | Videoens eget eksempel (14:55: M5 med M15 som højere). Ejeren, 2026-09-23 |

Fælles for begge: kerne v2, buffer 10%, BE +1,2R (fast, én version — ejeren 2026-09-23),
MNQ.v.0 2019-05-06 → 2023-12-31 kun gennem `data.holdout.load_in_sample`, indgangsvindue
15:30-21:30 dansk tid, en handel kræver `kontrakter ≥ 1`, kontrakter loftes ved 50.

**Om spor B går videre til trin 2, besluttes efter denne optælling, på de udfaldsfri tal i
§5, sammen med ejeren og før trin 2 præregistreres.** Grunden: omkostningen i R er omvendt
proportional med stopafstanden, og 5m-zoner er mindre.

## 3. Definitionerne

### 3a. Fælles regler

- **Swing-punkt:** et lys er swing high hvis dets high er højere end de 5 lys før og mindst
  lige så højt som de 5 lys efter. Swing low spejlvendt. **Punktet er kendt først når de 5
  lys efter er lukket**, og bruges aldrig før. N = 5 på alle timeframes (LuxAlgo's standard
  for intern struktur; valgt af andre, før vores data).
- **Brud måles på lukning, sweeps på væge.**
- **Intet kig frem:** hvert filter bruger kun det der var kendt ved lukningen af lyset *før*
  berøringslyset. Filtre der hører til dannelsen, bruger kun det der var kendt ved
  udbrudslysets lukning.
- **Højere timeframe (HTF)** bygges ved at aggregere 1m-serien, og et HTF-lys bruges først
  når det er lukket.
- "Lys" betyder lys på handelstimeframen, medmindre der står HTF.

### 3b. De syv kriterier

Eksemplet er demand; supply er spejlvendt.

| nr | kriterium | definition | vurderes ved |
|---|---|---|---|
| 1 | Brud på struktur | Efter udbrudslyset og før berøringslyset lukker et lys over det seneste swing high, som var kendt ved udbrudslysets lukning og ligger over zonens top. Findes intet sådant swing high: falsk | berøring |
| 2 | Flip | Zonen overlapper prismæssigt en ældre supply-zone S (kerne v2-regler, samme timeframe). S blev berørt for første gang højst 4 lys før demand-zonens basislys. Og før berøringslyset lukker et lys over S's top | berøring |
| 3 | Sweep | Zonens bund ligger under det seneste swing low, som var kendt før basislyset, og udbrudslyset lukker over det swing low | dannelse |
| 4 | Inducement | Mindst ét swing low bliver kendt efter udbrudslyset og før berøringslyset, og ligger over indgangsniveauet E | berøring |
| 5 | Stakket | Zonen overlapper prismæssigt en HTF-zone af samme side (kerne v2-regler på HTF-lys, uden buffer), som er dannet og stadig ikke berørt ved lyset før berøringen | berøring |
| 6 | Retning | Det seneste HTF-strukturbrud var opad: det seneste HTF-lys der lukkede over et kendt HTF-swing high, er nyere end det seneste der lukkede under et kendt HTF-swing low | berøring |
| 7 | Discount | Zonens midtpunkt ligger under midten af HTF-rangen mellem seneste kendte HTF-swing high og HTF-swing low. Ligger swing high under swing low, er rangen udefineret: falsk | berøring |

Kriterium 8 (frisk zone) er i kernen: en zone dør ved første berøring.

**Score = antal sande kriterier blandt 1-7**, uvægtet, som videoen siger.

## 4. Rapport — `research/output/b4_k1_trin2_optaelling.md` og `.csv`

Pr. spor, med Wilson 95%-CI på alle andele:

| tabel | indhold |
|---|---|
| Filtrene | andel signaler hvor hvert af 1-7 er sandt; alle, demand, supply |
| Scorefordeling | `signaler_n` og `dage_med_signal_n` for score 0, 1, …, 7 |
| Kumulativ | `dage_med_signal_n` for score ≥ k, k = 0 … 7 |
| Brud alene | `dage_med_signal_n` hvor kriterium 1 er sandt |
| Samvariation | phi-korrelation mellem hvert par af filtre (21 par) |
| Omkostninger | `risiko_pt_p10/p50/p90`, `omk_R_netto_p10/p50/p90`, `be_WR_pct_netto_p50`, `kontrakter_p50/p90/maks`, `kontrakter_loftet_n` |
| Pr. år | kumulativ tabel og omkostningstabellen pr. år |

`dage_med_signal_n` er antallet af RTH-dage med mindst ét signal. Det er udfaldsfrit og
en nedre grænse for antallet af handler, fordi disciplinreglerne højst giver én afgjort
handel om dagen.

**Regressionstjek før kørslen:** `research/b4_k1_optaelling.py` skal stadig gengive
`b4_k1_optaelling_v2.csv` byte for byte, og spor A's signaler ved score ≥ 0 skal være de
samme som trin A-motorens kandidater for buffer 10%.

## 5. Beslutningsregler — anvendes efter optællingen, før trin 2 præregistreres

| beslutning | regel |
|---|---|
| En tærskel score ≥ k er testbar | `dage_med_signal_n` ved score ≥ k er mindst 310 (MDE 0,20 R) |
| Varianter i trin 2 | "brud alene" og de testbare af score ≥ 2, ≥ 3, ≥ 4. Er ingen tærskel testbar, køres kun hovedtesten |
| Hovedtesten | køres altid; den bruger alle signaler |
| Spor B | besluttes sammen med ejeren på omkostningstabellen. Hvert spor der går videre, lægger sine varianter til N |

## 6. Forventning, skrevet før kørslen — ikke et kriterium

- **Filtre:** 5 og 6 samvarierer mest; de bygger begge på HTF. Nr. 4 er sandt oftest,
  fordi der sjældent går lang tid fra dannelse til berøring uden et swing low.
- **Score:** de fleste signaler har score 1-3. Score ≥ 4 har færre end 310 dage på spor A.
- **Spor B:** median `risiko_pt` omkring 12 point mod 21 på spor A, median `omk_R_netto`
  omkring 0,11 mod 0,063, og break-even-win-rate omkring 37% mod 35%. Den tynde hale bliver
  tykkere: p10-risiko omkring 4 point, hvor omkostningen er over 0,3 R.

## 7. Efter kørslen

Stop. Tabellerne i chatten. Ingen ændring af definitionerne, ingen valg af tærskler —
det gøres sammen med ejeren efter §5.
