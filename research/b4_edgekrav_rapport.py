"""B4 edge-kravet — rapporten ud fra ``research/output/b4_edgekrav_<variant>.json``.

Genskaber ``research/output/b4_edgekrav.md`` og ``b4_edgekrav_celler.csv`` fra kørslens
JSON-filer. Kører ingen simulering.

    .venv/bin/python -m research.b4_edgekrav_rapport

Datoen i "Kørt" er commit-datoen for ``b4_edgekrav_hoved.json``, så rapporten kan
genskabes byte for byte.
"""
import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "output"
sys.path.insert(0, str(ROOT))
from research import b4_edgekrav as b  # noqa: E402

V = {v: json.loads((OUT / f"b4_edgekrav_{v}.json").read_text()) for v in b.VARIANTER}
H = V["hoved"]
NAVN = {
    "hoved": "Hovedmodel (t4, DLL, intradag, 252 dage, $49-plan)",
    "normal": "Normalfordelt Z",
    "t3": "Student-t, 3 frihedsgrader",
    "uden_dll": "DLL slået fra (loft $2.000)",
    "uden_intradag": "Ingen bevægelse inden for dagen",
    "horisont_126": "Horisont 126 dage",
    "plan_95": "$95-planen uden aktivering",
}


def tal(x, nd=0):
    if x is None or x != x:
        return "—"
    s = f"{x:,.{nd}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def usd(x):
    if x is None or x != x:
        return "—"
    return ("−$" if x < 0 else "$") + tal(abs(x))


def pct(x, nd=0):
    return tal(100 * x, nd) + "%"


def s_txt(k):
    if k["flag"] == "under_gitter":
        return f"≤ {tal(k['x'], 2)} (allerede i første gitterpunkt)"
    if k["flag"] == "over_gitter":
        return "> 3,0 (ikke nået i gitteret)"
    return tal(k["x"], 2)


def interp(xs, ys, x):
    if x < xs[0] or x > xs[-1]:
        return None
    for x0, x1, y0, y1 in zip(xs, xs[1:], ys, ys[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def kurve(rows, navn):
    hdr = ("| Sharpe | σ_C | σ_X | bestå ≤63 | ≤126 | ≤252 | median dage | resets | "
           "udbet. ≤63 | ≤252 | til ejer | gebyrer | **EV netto [95%]** | P(netto>0) | "
           "p10 | XFA ikke udbetalt |")
    ud = [hdr, "|" + "---|" * 16]
    for r in rows:
        c = r[navn]
        ud.append(
            f"| {tal(r['sharpe'], 2)} | {usd(c['sigma_c'])} | {usd(c['sigma_x'])} | "
            f"{pct(c['P_bestaaet_63'])} | {pct(c['P_bestaaet_126'])} | "
            f"{pct(c.get('P_bestaaet_252', float('nan'))) if 'P_bestaaet_252' in c else '—'} | "
            f"{tal(c['median_dage_bestaaet'])} | {tal(c['resets'], 2)} | "
            f"{pct(c['P_udbetaling_63'])} | "
            f"{pct(c['P_udbetaling_252']) if 'P_udbetaling_252' in c else '—'} | "
            f"{usd(c['til_ejer'])} | {usd(c['gebyr'])} | "
            f"**{usd(c['EV'])}** [{usd(c['EV_lo'])}; {usd(c['EV_hi'])}] | "
            f"{pct(c['P_netto_pos'])} | {usd(c['netto_p10'])} | {usd(c['xfa_ubetalt'])} |")
    return "\n".join(ud)


def krav_tabel():
    ud = ["| variant | S_min_EV (punkt) | S_min_EV (nedre 95% > 0) | S_min_EV disciplinzone | "
          "S_hurtig (bedste EV-størrelse) | S_hurtig (størrelse maks. P) | "
          "S_min_EV på valgstierne | EV > 0 ved S = 0 | §6-række |",
          "|" + "---|" * 9]
    for v, R in V.items():
        k = R["kravet"]
        ud.append(f"| {NAVN[v]} | **{s_txt(k['S_min_EV'])}** | {s_txt(k['S_min_EV_lo'])} | "
                  f"{s_txt(k['S_min_EV_disciplin'])} | {s_txt(k['S_hurtig_bedst'])} | "
                  f"{s_txt(k['S_hurtig_max'])} | {s_txt(k['S_min_EV_valgstier'])} | "
                  f"{'ja' if k['EV_pos_ved_0'] else 'nej'} | {R['beslutning']} |")
    return "\n".join(ud)


def foelsomhed_ev():
    S_vis = (0.0, 0.5, 0.75, 1.0, 1.5, 2.0)
    ud = ["| variant | " + " | ".join(f"EV ved S = {tal(s, 2)}" for s in S_vis) + " |",
          "|" + "---|" * (len(S_vis) + 1)]
    for v, R in V.items():
        m = {r["sharpe"]: r["bedst"]["EV"] for r in R["rows"]}
        ud.append(f"| {NAVN[v]} | " + " | ".join(usd(m[s]) for s in S_vis) + " |")
    return "\n".join(ud)


def hurtigst_tabel():
    ud = ["| Sharpe | σ_C | σ_X | P(udbet. ≤63) | EV netto |", "|---|---|---|---|---|"]
    for r in H["rows"]:
        c = r["hurtigst"]
        ud.append(f"| {tal(r['sharpe'], 2)} | {usd(c['sigma_c'])} | {usd(c['sigma_x'])} | "
                  f"{pct(c['P_udbetaling_63'])} | {usd(c['EV'])} |")
    return "\n".join(ud)


def valg_tabel():
    ud = ["| Sharpe | σ_C | σ_X | EV på valgstierne | EV på nye stier | forskel |",
          "|---|---|---|---|---|---|"]
    for r in H["rows"]:
        a, n = r["bedst_valg"], r["bedst"]
        ud.append(f"| {tal(r['sharpe'], 2)} | {usd(a['sigma_c'])} | {usd(a['sigma_x'])} | "
                  f"{usd(a['EV'])} | {usd(n['EV'])} | {usd(n['EV'] - a['EV'])} |")
    return "\n".join(ud)


REF = [
    ("Fase 2's antagelse (WR 40% ved 2:1)", 1.9, None),
    ("Kandidat 5 in-sample, 1m · uden middag", 1.17, 559.0),
    ("Kandidat 5 holdout", -1.04, 464.0),
    ("Kandidat 6, 07:30–09:30 efter salg", 0.64, 123.0),
]


def ref_tabel():
    S = [r["sharpe"] for r in H["rows"]]
    ev = [r["bedst"]["EV"] for r in H["rows"]]
    evd = [r["disciplin"]["EV"] for r in H["rows"]]
    p63 = [r["bedst"]["P_udbetaling_63"] for r in H["rows"]]
    ud = ["| reference | Sharpe | EV, bedste størrelse | EV, disciplinzone | "
          "P(udbet. ≤63) | nærmeste gitterpunkts σ_X | MNQ for den σ_X |",
          "|---|---|---|---|---|---|---|"]
    for navn, s, sig in REF:
        e, ed, p = interp(S, ev, s), interp(S, evd, s), interp(S, p63, s)
        naer = min(H["rows"], key=lambda r: abs(r["sharpe"] - s))
        sx = naer["bedst"]["sigma_x"]
        mnq = tal(sx / sig, 1) if sig else "—"
        ud.append(f"| {navn} | {tal(s, 2)} | "
                  f"{usd(e) if e is not None else 'under gitteret (−0,5: ' + usd(ev[0]) + ')'} | "
                  f"{usd(ed) if ed is not None else 'under gitteret (−0,5: ' + usd(evd[0]) + ')'} | "
                  f"{pct(p) if p is not None else '—'} | {usd(sx)} (S = {tal(naer['sharpe'], 2)}) "
                  f"| {mnq} |")
    ud.append("| Ingen edge, kun omkostning | under 0 | se S = −0,5 og 0 i kurven | | | | |")
    return "\n".join(ud)


# Afsnit 9 blev skrevet i hånden efter kørslen og står her ordret, så rapporten kan
# genskabes byte for byte. Tallene i det regnes ikke igen.
AFSNIT_9 = '\n## 9. Hvad der skal læses med tallene (afgør intet, §6 er anvendt ovenfor)\n\n- **Regelgeometrien giver plus uden edge.** Ved den bedste størrelse er forventet\n  nettoværdi positiv ved Sharpe 0 ($1.020) og ved −0,5 ($165). Ejerens tab er loftet af\n  gebyrerne (cirka $1.900 om året), mens udbetalingerne ikke er loftet. Det er en option, og\n  den er mest værd ved stor spredning.\n- **Den bedste størrelse er stor og ligger ved gitterets kant.** σ_C er $1.000, gitterets\n  største værdi, fra Sharpe 0,25 og op. σ_X er $800. Ved Sharpe −0,5 og 0 er den bedste\n  σ_C $800, altså inde i gitteret. En σ på $1.000 svarer til DLL\'en på én dags spredning.\n- **Prisen er adfærd.** Ved den bedste størrelse er der 15–19 Combine-resets om året ved\n  Sharpe ≤ 1, og DLL\'en rammes ofte. Det er det mønster, Topstep nævner som grund til nedkald\n  og afvisning ("gentagne brud på Daily Loss Limit", "activity that resembles gambling",\n  `REGLER_VERIFICERET.md` §5). Modellen kan ikke prissætte den regel.\n- **I disciplinzonen** (σ ≤ $400) er S_min_EV 0,16. Forventet nettoværdi er −$141 ved\n  Sharpe 0 og −$491 ved −0,5, og der er 3–6 resets om året. Den bedste celle i zonen er\n  σ_C = σ_X = $400, zonens kant, ved alle Sharpes.\n- **Bevægelsen inden for dagen betyder meget.** Uden den (kun dagsslut) stiger EV ved\n  Sharpe 0 fra $1.020 til $8.160. Brud i realtid er altså en stor del af prisen, og\n  bridge-antagelsen bærer en stor del af tallet.\n- **Genberegningen på nye stier** gav højere EV end valgstierne ved alle Sharpes, med\n  $41–$300. Den forventede optimisme ved valget er altså mindre end forskellen mellem de to\n  sæt frø. Kravet flytter sig ikke: S_min_EV er ≤ −0,5 på begge.\n- **Referencepunkterne:** kandidat 6 (Sharpe 0,64, σ $123 pr. MNQ) skulle handle cirka\n  6,5 MNQ for at nå den bedste σ_X på $800, og 3,3 MNQ for disciplinzonens $400.\n'


def koert_dato() -> str:
    rel = (OUT / "b4_edgekrav_hoved.json").relative_to(ROOT).as_posix()
    return subprocess.run(["git", "--no-optional-locks", "-C", str(ROOT), "log", "-1",
                           "--format=%cs", "--", rel],
                          capture_output=True, text=True, check=True).stdout.strip()


def main():
    k = H["kravet"]
    s_min = k["S_min_EV"]["x"]
    raekke = H["beslutning"]
    tider = ", ".join(f"{v} {tal(R['sekunder'] / 60, 1)} min" for v, R in V.items())
    md = f"""# B4 — edge-kravet: resultat

**Kørt:** {koert_dato()} fra commit `{H['commit']}`
(præregistrering `research/prereg/b4_edgekrav.md` og tillæg
`research/prereg/b4_edgekrav_tillaeg.md`). 20.000 stier pr. celle, 11 Sharpes × 100
størrelser pr. gitter. Valget af størrelse sker på stierne med frø {b.FROE}; tallene i
tabellerne er de valgte celler regnet igen på 20.000 nye stier med frø {b.FROE_NY}
(tillægget §3.1). Ingen kursdata, intet fra holdout, intet tæller i tælleren (45).
Kørselstider: {tider}.

## 1. Kravet

{krav_tabel()}

S-værdierne er interpoleret lineært mellem gitterpunkterne (−0,5; 0; 0,25; 0,5; 0,75; 1,0;
1,25; 1,5; 2,0; 2,5; 3,0). "Nedre 95% > 0" er det sted, hvor intervallets nedre grænse for
forventet nettoværdi ved den bedste størrelse krydser 0. Kolonnen "på valgstierne" er
S_min_EV regnet på de stier, størrelsen blev valgt på — til sammenligning; den afgør intet.

## 2. §6 anvendt mekanisk

Hovedmodellen, punktestimatet: **S_min_EV = {s_txt(k['S_min_EV'])}** → **række {raekke}**.

{ {1: "Række 1: S_min_EV ≤ 0,75. Svage edges kan betale sig. Næste skridt efter §6: præregistrering af en holdout-test af overnight drift (NQ 2024–2026 er uåbnet for natten) og en søgning efter svage edges, der kan supplere.",
   2: "Række 2: 0,75 < S_min_EV ≤ 1,5. Overnight drift alene er ikke nok. Der skal en kombination af edges til, eller en stærkere edge. Næste skridt aftales med ejeren.",
   3: "Række 3: S_min_EV > 1,5. Offentlige edges på Topstep er næppe vejen. Næste skridt efter §6: undersøg et andet format (spor C: positioner over flere dage)."}[raekke] }

Forventet nettoværdi positiv allerede ved Sharpe 0: **{'ja' if k['EV_pos_ved_0'] else 'nej'}**.
{"Det betyder, at regelgeometrien alene giver plus ved den bedste størrelse, og det skal læses sammen med Topsteps regler om adfærd (§6). Det ændrer ikke rækken." if k['EV_pos_ved_0'] else ""}

## 3. Kurven ved den bedste størrelse (hovedmodellen)

{kurve(H['rows'], 'bedst')}

"XFA ikke udbetalt" er diagnosen fra tillægget §2.4: forventet positiv XFA-saldo ved
horisonten. Den indgår ikke i nettoværdien.

## 4. Kurven i disciplinzonen (σ_C og σ_X ≤ $400)

{kurve(H['rows'], 'disciplin')}

## 5. S_hurtig, den anden læsning: størrelsen der maksimerer P(første udbetaling ≤ 63 dage)

{hurtigst_tabel()}

## 6. Valget af størrelse: valgstier mod nye stier (hovedmodellen)

{valg_tabel()}

## 7. Referencepunkterne (placeres på kurven, afgør intet)

{ref_tabel()}

"MNQ for den σ_X" er den daglige spredning ved den bedste størrelse i nærmeste
gitterpunkt delt med referencens σ pr. MNQ — hvor mange kontrakter størrelsen svarer til.

## 8. Følsomhed (rapporteres, afgør intet)

{foelsomhed_ev()}

Kravet pr. følsomhed står i tabel 1.
""" + AFSNIT_9
    (OUT / "b4_edgekrav.md").write_text(md)

    with open(OUT / "b4_edgekrav_celler.csv", "w", newline="") as f:
        felter = None
        for v, R in V.items():
            for r in R["rows"]:
                for c in r["celler"]:
                    row = {"variant": v, **c}
                    if felter is None:
                        felter = list(row)
                        w = csv.DictWriter(f, felter)
                        w.writeheader()
                    w.writerow({kk: row.get(kk, "") for kk in felter})
    print(md)


if __name__ == "__main__":
    main()
