"""Luxor: tisztítás -> tesztek -> játékosfüggés -> 4 szelvény -> jelentés.

    python futtat.py luxor

Kimenet az `eredmenyek/luxor/` mappába:
    luxor_tiszta.csv  – tisztított adat (a kihúzott számok szóközzel elválasztva)
    jelentes.md       – számszerű eredmények
    abra.png          – gyakoriság + számonkénti népszerűségi becslés
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..kozos import ADATOK, EREDMENYEK, SZINEK, abra_cim, abra_stilus
from . import elemzes as e
from . import szelvenyek as s
from .tisztitas import N_SZAM, beolvas, huzott_matrix, tisztitasi_jelentes

KIMENET = EREDMENYEK / "luxor"
SZELVENY_AR = 300  # Ft / alapjáték


def abra(df: pd.DataFrame, becsles: pd.DataFrame, f_p: float, fajl: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    c = SZINEK
    plt.rcParams.update({"font.size": 10, "text.color": c["szoveg"], "axes.labelcolor": c["szoveg2"],
                         "xtick.color": c["szoveg2"], "ytick.color": c["szoveg2"]})
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7.4), facecolor=c["felulet"])

    x = np.arange(1, N_SZAM + 1)
    db = huzott_matrix(df, e.ELSO_N).sum(0)
    p = e.ELSO_N / N_SZAM
    vart, sd = len(df) * p, np.sqrt(len(df) * p * (1 - p))
    ax1.axhspan(vart - 1.96 * sd, vart + 1.96 * sd, color=c["racs"], zorder=0, lw=0)
    ax1.axhline(vart, color=c["szoveg2"], lw=1, ls="--", zorder=1)
    ax1.bar(x, db, width=0.78, color=c["semleges"], zorder=2)
    ax1.set_ylim(0, db.max() * 1.08)
    ax1.set_xticks([15 * k + 8 for k in range(5)])
    ax1.set_xticklabels([f"{b}  {15 * k + 1}–{15 * k + 15}" for k, b in enumerate("LUXOR")])
    ax1.set_xlim(0.3, N_SZAM + 0.7)
    for k in range(1, 5):
        ax1.axvline(15 * k + 0.5, color=c["szoveg2"], lw=0.8, zorder=3)
    abra_cim(ax1, f"Hányszor jöttek ki az egyes számok az első 36 golyóban ({len(df)} húzás, 2001–2026)",
             "Szaggatott vonal = elméleti átlag; szürke sáv = tiszta véletlennél várható 95%-os tartomány")

    xb = np.arange(len(becsles))
    ax2.axhspan(-1.96 * becsles.se.mean() * 100, 1.96 * becsles.se.mean() * 100, color=c["racs"], zorder=0, lw=0)
    szin = [c["piros"] if v > 0 else c["kek"] for v in becsles.hatas]
    ax2.bar(xb, becsles.hatas * 100, width=0.78, color=szin, zorder=2)
    ax2.axhline(0, color=c["szoveg2"], lw=1, zorder=3)
    ax2.set_xticks(xb[::2])
    ax2.set_xticklabels(becsles.index[::2])
    for k in (1, 2):
        ax2.axvline(15 * k - 0.5, color=c["szoveg2"], lw=0.8, zorder=3)
    for k, b in enumerate("UXO"):
        ax2.text(15 * k + 7, 1.0, b, transform=ax2.get_xaxis_transform(), ha="center", va="top",
                 fontsize=11, fontweight="bold", color=c["szoveg2"])
    ax2.set_xlim(-0.7, len(becsles) - 0.3)
    ax2.set_ylabel("%")
    abra_cim(ax2, "Népszerűek-e egyes számok? Hatás a kép-nyertesek számára (U, X, O oszlop, 2015–2026)",
             "+% = ha kihúzzák, ennyivel több a kép-nyertes. Szürke sáv = puszta zajtól várható 95%-os tartomány; "
             f"45 számból néhány kilógó a véletlentől is várható (együttes F-próba: p = {f_p:.2f})")
    for ax in (ax1, ax2):
        abra_stilus(ax)
    fig.tight_layout(h_pad=2.5)
    fig.savefig(fajl, dpi=150, facecolor=c["felulet"])
    plt.close(fig)


def main(csv: Path = ADATOK / "luxor.csv", nyeremenyek: Path = ADATOK / "luxor_nyeremenyek.csv") -> None:
    KIMENET.mkdir(parents=True, exist_ok=True)
    md: list[str] = []

    def ki(szoveg: str = "") -> None:
        print(szoveg)
        md.append(szoveg)

    df = beolvas(csv, nyeremenyek)
    mentes = df.copy()
    mentes["huzott"] = mentes["huzott"].map(lambda sz: " ".join(map(str, sz)))
    mentes.to_csv(KIMENET / "luxor_tiszta.csv", index=False)

    ki("# Luxor elemzés – eredmények\n")
    ki("## 1. Adattisztítás\n")
    ki("```\n" + tisztitasi_jelentes(df) + "\n```\n")

    ki("## 2. A tábla szerkezete az adatokból\n")
    z = e.lezaro_golyok_teszt(df)
    kep_sor = z[z["kategória"] == "elso_kep"].iloc[0]
    keret_sor = z[z["kategória"] == "elso_keret"].iloc[0]
    ki("Melyik oszlopból jött az első képet / első keretet lezáró golyó:\n")
    ki(f"- első kép: {kep_sor['oszloponként']} → a kép **csak az U, X, O oszlopból** áll "
       "(oszloponként 2 szám a játékos 4 számából)")
    ki(f"- első keret: {keret_sor['oszloponként']} → a keretben az L és R oszlop mind a 4 száma benne van, "
       "az U, X, O-ból 2-2\n")
    ki("Ezért a kép esélye: ∏_{U,X,O} C(h, 2) / C(4, 2), ahol h = az oszlopban kihúzott számaink száma; "
       "a keret ehhez még azt is megkívánja, hogy az L és R oszlop mind a 4 száma kint legyen.\n")

    ki("## 3. Véletlenszerűségi tesztek (az első 36 golyón)\n")
    ki("A sorsolás minden héten legalább 36 golyóig tart, ez a rész tehát független attól, "
       "hogy mikor jön ki a Luxor.\n")
    g = e.gyakorisag_teszt(df)
    ki(f"- **Számgyakoriság**: legritkább {g['min'][0]} ({g['min'][1]}×), leggyakoribb {g['max'][0]} "
       f"({g['max'][1]}×), várható {g['vart_db']:.1f}× → p = {g['p']:.2f}")
    for _, r in e.eloszlas_tesztek(df).iterrows():
        ki(f"- **{r.leiras}**: megfigyelt átlag {r.megfigyelt_atlag:.2f}, elméleti {r.elmeleti_atlag:.2f} "
           f"→ p = {r.p_ertek:.3f}")
    ki("\n(Öt teszt mellett egy p ≈ 0,02 még belefér a véletlenbe; a sorrend amúgy sem számít a "
       "nyeréshez, csak az, hogy mely számok jönnek ki a luxorig.)\n")

    ki("## 4. Stratégiák visszatesztelése\n")
    ki(e.strategia_backtest(df).to_markdown(index=False, floatfmt=".3f"))
    ki("")

    ki("## 5. Függ-e a sorsolás és a nyeremény attól, mit játszanak a többiek?\n")
    b = e.befejezo_szakasz_teszt(df)
    ki(f"- **Befejező szakasz** (a 36. golyó után még kijövő számok): a népszerű számoknak gyakrabban "
       f"kellene bekerülniük, ha a megállás érezhetően függne tőlük → p = {b['p']:.2f}")
    for _, r in z.iterrows():
        nev = {"elso_kep": "első kép", "elso_keret": "első keret", "luxor": "luxor"}[r["kategória"]]
        ki(f"- **A(z) {nev} lezáró golyója** (oszlopon belül egyenletes-e): p = {r['p']:.2f}")
    tk = e.nepszeruseg_nyertes_teszt(df, "kep")
    tr = e.nepszeruseg_nyertes_teszt(df, "keret")
    ki(f"- **Kép-nyertesek száma** ({tk['hetek']} hét, 2015-től): számít-e, hogy az U, X, O oszlopon belül "
       f"*melyik* számok jöttek ki? F-próba p = {tk['p']:.2f}")
    ki(f"- **Keret-nyertesek száma**: ugyanez mind az 5 oszlopra → p = {tr['p']:.2f}")
    becsles = e.nepszeruseg_nyertes_becsles(df, "kep")
    van_nepszeruseg = tk["p"] < 0.05
    ki(f"\nA számonkénti becslések szórása {100 * becsles.hatas.std():.1f}%, a puszta zajtól várható "
       f"{100 * becsles.se.mean():.1f}% (egy ±{100 * 2.8 * becsles.se.mean():.0f}%-os népszerűségi "
       "különbséget már ki tudnánk mutatni).\n")
    if van_nepszeruseg:
        ki("**Következtetés:** van mérhető népszerűségi különbség, a szelvények a kevésbé népszerű "
           "számokra épülnek.\n")
    else:
        ki("**Következtetés:** a Luxornál – a Hatoslottóval ellentétben – nem mutatható ki, hogy a "
           "játékosok egyes számokat érezhetően többen játszanának (valószínűleg sokan gépi tippel "
           "játszanak, és 20 szám mellett a kedvenc számok hatása elvész). Így a számválasztás "
           "**sem az esélyt, sem a nyeremény nagyságát** nem befolyásolja mérhetően. "
           "Ami számít: a 4 szelvény közti **lefedés**.\n")

    ki("## 6. Ajánlott 4 szelvény\n")
    sz = s.szelvenyek_osszeallitasa(becsles["hatas"] if van_nepszeruseg else None)
    ki("| # | L (1–15) | U (16–30) | X (31–45) | O (46–60) | R (61–75) |")
    ki("|---|---|---|---|---|---|")
    for i, t in enumerate(sz, 1):
        a = np.array(t)
        ki(f"| {i} | " + " | ".join(" ".join(map(str, a[(a - 1) // 15 == j])) for j in range(5)) + " |")
    ki("")
    ki("Oszloponként mind a 15 számot felhasználjuk (16 helyre 15 szám, egy ismétlődik), így a 4 szelvény "
       "együtt lefedi mind a 75 számot.\n")

    ert = e.szelveny_ertekeles(df, sz)
    rng = np.random.default_rng(7)
    hasonlit = {nev: [e.szelveny_ertekeles(df, k) for k in keszletek[:200]]
                for nev, keszletek in s.osszehasonlito_keszletek(rng).items()}
    ki(f"Ha ezt a 4 szelvényt minden héten megjátszottuk volna ({ert['hetek']} hét, a gép véletlen "
       "elhelyezésére pontosan átlagolva):\n")
    ki("| | ajánlott 4 szelvény | 4 független véletlen | 4 azonos szelvény |")
    ki("|---|---|---|---|")

    def atl(nev, kulcs):
        return np.mean([h[kulcs] for h in hasonlit[nev]])

    for cimke, kulcs, szorzo, fmt in [
        ("kép esélye szelvényenként / hét", "p_kep_szelvenyenkent", 100, "{:.2f}%"),
        ("legalább 1 kép a 4-ből / hét", "p_legalabb_egy_kep", 100, "{:.2f}%"),
        ("legalább 1 keret a 4-ből / hét", "p_legalabb_egy_keret", 100, "{:.3f}%"),
        (f"átlagos nyeremény szelvényenként / hét (2015-től, {SZELVENY_AR} Ft-os tétre)",
         "atl_nyeremeny_ft_szelvenyenkent", 1, "{:.0f} Ft"),
    ]:
        ki(f"| {cimke} | **{fmt.format(ert[kulcs] * szorzo)}** | "
           f"{fmt.format(atl('4 független véletlen szelvény', kulcs) * szorzo)} | "
           f"{fmt.format(atl('4 azonos szelvény', kulcs) * szorzo)} |")
    ki("")
    ki("A szelvényenkénti esély és a várható nyeremény bármilyen számválasztásnál ugyanannyi (a különbségek a "
       "véletlen ingadozás részei); a lefedés azt növeli, hogy **legalább az egyik** szelvény nyerjen.")
    nyd = df[df["ft_kep"].notna()]
    def ezres(x: float) -> str:
        return f"{x:,.0f}".replace(",", " ")

    ki(f"\nÁtlagos nyeremények 2015-től ({len(nyd)} hét): kép {ezres(nyd.ft_kep.mean())} Ft "
       f"(átl. {ezres(nyd.db_kep.mean())} nyertes), keret {ezres(nyd.ft_keret.mean())} Ft "
       f"(átl. {ezres(nyd.db_keret.mean())} nyertes), első kép {ezres(nyd.ft_elso_kep.mean())} Ft, "
       f"Luxor {ezres(nyd.ft_luxor.mean())} Ft. A 4 szelvény ára {4 * SZELVENY_AR} Ft / hét.")

    (KIMENET / "jelentes.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    abra(df, becsles, tk["p"], KIMENET / "abra.png")
    print(f"\nKimenet: {KIMENET}/")
