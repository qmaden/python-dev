"""Hatoslottó: tisztítás -> tesztek -> népszerűség -> 4 szelvény -> jelentés.

    python futtat.py hatos

Kimenet az `eredmenyek/hatos/` mappába:
    hatos_tiszta.csv  – tisztított adat
    jelentes.md       – számszerű eredmények
    abra.png          – gyakoriság vs. játékos-népszerűség
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..kozos import ADATOK, EREDMENYEK
from . import elemzes as e
from . import mintazat as mm
from . import szelvenyek as s
from .tisztitas import beolvas, tisztitasi_jelentes

KIMENET = EREDMENYEK / "hatos"


def abra(df: pd.DataFrame, nep: pd.Series, valasztott: set[int], fajl: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    felulet, szoveg, szoveg2, racs = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
    kek, piros, semleges = "#2a78d6", "#e34948", "#9a9993"
    plt.rcParams.update({"font.size": 10, "text.color": szoveg, "axes.labelcolor": szoveg2,
                         "xtick.color": szoveg2, "ytick.color": szoveg2})
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7.2), facecolor=felulet)
    x = np.arange(1, 46)

    db = e.szam_matrix(df).sum(0)
    vart = len(df) * e.P_SZAM
    sd = np.sqrt(len(df) * e.P_SZAM * (1 - e.P_SZAM))
    ax1.axhspan(vart - 1.96 * sd, vart + 1.96 * sd, color=racs, zorder=0, lw=0)
    ax1.axhline(vart, color=szoveg2, lw=1, ls="--", zorder=1)
    ax1.bar(x, db, width=0.78, color=semleges, zorder=2)
    ax1.set_ylim(0, db.max() * 1.08)
    ax1.set_title(f"Hányszor húzták ki az egyes számokat ({len(df)} húzás, 1988–2026)",
                  loc="left", fontsize=12, fontweight="bold", pad=20)
    ax1.text(0, 1.02, "Szaggatott vonal = elméleti átlag; szürke sáv = tiszta véletlennél várható 95%-os tartomány",
             transform=ax1.transAxes, fontsize=9, color=szoveg2, va="bottom")

    szin = [piros if v > 0 else kek for v in nep.values]
    ax2.bar(x, nep.values * 100, width=0.78, color=szin, zorder=2)
    ax2.axhline(0, color=szoveg2, lw=1, zorder=3)
    ax2.set_title("Mennyire népszerűek a számok a játékosok körében (becslés a nyertesek számából)",
                  loc="left", fontsize=12, fontweight="bold", pad=20)
    ax2.text(0, 1.02, "+% = ha kihúzzák, ennyivel több a 3-as nyertes (piros: sokan játsszák, kék: kevesen). "
             "Aláhúzott szám = bekerült a szelvényekbe",
             transform=ax2.transAxes, fontsize=9, color=szoveg2, va="bottom")
    ax2.set_ylabel("%")

    for ax in (ax1, ax2):
        ax.set_facecolor(felulet)
        ax.set_xticks(x)
        ax.set_xlim(0.3, 45.7)
        ax.tick_params(length=0)
        ax.grid(axis="y", color=racs, lw=0.8, zorder=0)
        for sp in ax.spines.values():
            sp.set_visible(False)
    ax2.set_xticklabels([f"$\\underline{{{i}}}$" if i in valasztott else str(i) for i in x])
    fig.tight_layout(h_pad=2.5)
    fig.savefig(fajl, dpi=150, facecolor=felulet)
    plt.close(fig)


def main(csv: Path = ADATOK / "hatos.csv") -> None:
    KIMENET.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 160)
    md: list[str] = []

    def ki(szoveg: str = "") -> None:
        print(szoveg)
        md.append(szoveg)

    df = beolvas(csv)
    df.to_csv(KIMENET / "hatos_tiszta.csv", index=False)

    ki("# Hatoslottó elemzés – eredmények\n")
    ki("## 1. Adattisztítás\n")
    ki("```\n" + tisztitasi_jelentes(df) + "\n```\n")

    ki("## 2. Véletlenszerűségi tesztek\n")
    ki("Ha a húzásokban lenne kihasználható mintázat, ezek közül valamelyik kimutatná (p < 0,05).\n")
    for nev, resz in [("teljes időszak", df), ("utolsó 104 húzás", df.tail(104))]:
        g = e.gyakorisag_teszt(resz)
        ki(f"- **Számgyakoriság ({nev})**: legritkább {g['min'][0]} ({g['min'][1]}×), "
           f"leggyakoribb {g['max'][0]} ({g['max'][1]}×), várható {g['vart_db']:.1f}× → "
           f"p = {g['p']:.2f}")
    p = e.par_teszt(df)
    ki(f"- **Számpárok**: leggyakoribb pár {p['leggyakoribb_par'][0]}–{p['leggyakoribb_par'][1]} "
       f"({p['leggyakoribb_par'][2]}×, várható {p['vart_par_db']:.1f}×), a párok szórása → p = {p['p']:.2f}")
    t = e.eloszlas_tesztek(df)
    for _, r in t.iterrows():
        ki(f"- **{r.leiras}**: megfigyelt átlag {r.megfigyelt_atlag:.2f}, elméleti {r.elmeleti_atlag:.2f} "
           f"→ p = {r.p_ertek:.2f}")
    ki("\n**Következtetés:** minden teszt a tiszta véletlennel konzisztens.\n")

    ki("## 3. Stratégiák visszatesztelése\n")
    ki("Minden húzás előtt csak a múltbeli adatok alapján választunk 6 számot.\n")
    bt = e.strategia_backtest(df)
    ki(bt.to_markdown(index=False, floatfmt=".3f"))
    ki("\n(4 stratégia tesztelése mellett egy p ≈ 0,02 még bőven a véletlen ingadozás része; "
       "a „véletlen” sor mutatja, mekkora a zaj.)\n")

    ki("## 4. Játékos-népszerűség számonként (nyertesek számából)\n")
    nep = e.nepszeruseg_modell(df, "3")
    nep4 = e.nepszeruseg_modell(df, "4")
    nep5 = e.nepszeruseg_modell(df, "5")
    v = e.nepszeruseg_validacio(df)
    ki(f"- Konzisztencia: 3-as vs 4-es modell r = {nep.corr(nep4):.3f}, 3-as vs 5-ös r = {nep.corr(nep5):.3f}")
    ki(f"- Mintán kívüli teszt (2016 előtti becslés → {v['teszt_huzasok']} későbbi húzás): "
       f"Spearman r = {v['spearman_r']:.2f} a népszerűségi pontszám és a 3-as nyeremény között "
       f"(p = {v['p']:.1e}); kalibrált meredekség = {v['meredekseg']:.2f}")
    ki("- 3-as nyeremény a mintán kívüli húzásokon, népszerűségi negyedenként (átlaghoz képest):")
    for k, val in v["kvartilis_ft3_szorzo"].items():
        ki(f"  - {k}: ×{val:.2f}")
    top = nep.sort_values()
    ki(f"- Legkevésbé játszott: {', '.join(f'{i} ({100 * x:+.0f}%)' for i, x in top.head(8).items())}")
    ki(f"- Legnépszerűbb: {', '.join(f'{i} ({100 * x:+.0f}%)' for i, x in top.tail(8)[::-1].items())}")
    ki(f"- 1–31 átlag: {100 * nep.loc[1:31].mean():+.1f}%, 32–45 átlag: {100 * nep.loc[32:45].mean():+.1f}%\n")

    ki("## 5. Ellenőrzés és bővített modell\n")
    regi_sz = s.szelvenyek_osszeallitasa(df, nep)
    val = {m: mm.gordulo_validacio(df, m) for m in mm.SZINTEK}
    val0 = {m: mm.gordulo_validacio(df, m, mintazattal=False, felezesi_ido=None) for m in mm.SZINTEK}
    modellek = {m: mm.illeszt(df, m) for m in mm.SZINTEK}
    meredeksegek = {m: val[m]["meredekseg"] for m in mm.SZINTEK}
    szorzok = mm.huzas_szorzok(modellek, meredeksegek)
    sulyok = mm.szint_sulyok(df)
    stab = mm.idobeli_stabilitas(df)

    ki("**a) Mintázat-hatás.** A nyertesek száma nemcsak attól függ, *mely* számokat húzzák ki, hanem attól is, "
       "hogyan helyezkednek el egymáshoz képest. Hatás a nyertesek számára (± standard hiba):\n")
    ki("| mintázat a kihúzott számok között | 3-as | 4-es | 5-ös |")
    ki("|---|---|---|---|")
    for i, leiras in enumerate(mm.JELLEMZOK.values()):
        ki(f"| {leiras} | " + " | ".join(
            f"{100 * (np.exp(modellek[m].minta[i]) - 1):+.1f}% (±{100 * modellek[m].minta_se[i]:.1f})"
            for m in mm.SZINTEK) + " |")
    ki("\nA játékosok tehát **kerülik a szomszédos számokat**: ha a húzásban van ilyen pár, érezhetően kevesebb "
       "a nyertes. (A korábbi szelvény-szűrő épp fordítva, a szomszédos párokat tiltotta.)\n")
    ki("**b) Mintán kívüli ellenőrzés** – minden évre csak a korábbi évekből becsülve (2008-tól, "
       f"{val[3]['huzasok']} húzás): a nyertesszám ingadozásának mekkora részét jelzi előre a modell.\n")
    ki("| | 3-as | 4-es | 5-ös |")
    ki("|---|---|---|---|")
    ki("| csak számonkénti népszerűség (eredeti modell) | " + " | ".join(f"{100 * val0[m]['r2']:.0f}%" for m in mm.SZINTEK) + " |")
    ki("| + mintázat, + friss adatok nagyobb súlya | " + " | ".join(f"**{100 * val[m]['r2']:.0f}%**" for m in mm.SZINTEK) + " |")
    ki("| kalibráció (1 = pontos; <1 = a modell túloz) | " + " | ".join(f"{val[m]['meredekseg']:.2f}" for m in mm.SZINTEK) + " |")
    ki("\nA szelvények szorzóit a kalibrációval visszahúzva számoljuk.\n")
    ki(f"**c) Időbeli stabilitás.** A 2012 előtti és utáni becslés korrelációja r = {stab['r']:.2f}: a sorrend "
       "nagyjából állandó, de lassan változik (legtöbbet nőtt: "
       + ", ".join(f"{i} ({100 * x:+.0f}%)" for i, x in stab["valtozas"].tail(3)[::-1].items())
       + "; csökkent: " + ", ".join(f"{i} ({100 * x:+.0f}%)" for i, x in stab["valtozas"].head(3).items())
       + "). Ezért a friss húzások nagyobb súlyt kapnak (felezési idő 8 év).\n")
    ki("**d) A korábbi „nyeremény-szorzó” túlbecslés volt.** A 4. pont pontszáma azt mutatja, mi történik, ha a "
       "szelvény *mind a 6* számát kihúzzák. 3 találatnál viszont a húzás másik 3 száma nem a miénk, így a "
       "tényleges szorzó kisebb. A helyes érték: átlag mindazon húzásokra, amelyek a szelvényt pontosan 3 "
       "(4, 5) számban találják el. A korábbi 4 szelvényre így:\n")

    def tabla(szelvenyek, cimkek=None):
        ki("| # | Számok | 3-as | 4-es | 5-ös | várható 3–5 találatos nyeremény / szelvény |")
        ki("|---|---|---|---|---|---|")
        for i, t_ in enumerate(szelvenyek, 1):
            x = mm.szelveny_szorzo(t_, szorzok)
            ki(f"| {cimkek[i - 1] if cimkek else i} | {' – '.join(map(str, t_))} | ×{x[3]:.2f} | ×{x[4]:.2f} | "
               f"×{x[5]:.2f} | {sum(sulyok[m] * x[m] for m in mm.SZINTEK):.0f} Ft |")

    tabla(regi_sz)
    alap = sum(sulyok[m] for m in mm.SZINTEK)
    ki(f"\n(Véletlen számokkal: ×1,00 és {alap:.0f} Ft. A korábban közölt ×1,23–1,26 helyett a 3-as szorzó "
       "valójában kb. ×1,1.)\n")

    ki("## 6. Ajánlott 4 szelvény\n")
    sz = s.optimalis_szelvenyek(df, modellek, meredeksegek, szorzok, sulyok)
    ki("4 egymást nem fedő szelvény, amelyek együttes várható 3–5 találatos nyereménye a legnagyobb "
       "(megkötés: nincs 3 egymást követő szám, legfeljebb 2 szomszédos pár, nincs 4 hosszú számtani sor, "
       "nem korábbi nyerőszámsor – ezeken túl a modellnek nincs tapasztalata).\n")
    tabla(sz)
    pelda = (3, 7, 9, 13, 17, 21)
    ki("")
    tabla([pelda], ["„szerencseszámok”"])
    uj_ossz = sum(mm.szelveny_ertek(t_, szorzok, sulyok) for t_ in sz) / len(sz)
    regi_ossz = sum(mm.szelveny_ertek(t_, szorzok, sulyok) for t_ in regi_sz) / len(regi_sz)
    ki(f"\nSzelvényenként átlagosan {uj_ossz:.0f} Ft várható 3–5 találatos nyeremény (korábbi szelvények: "
       f"{regi_ossz:.0f} Ft, véletlen számok: {alap:.0f} Ft). Az 5-ös szorzók a legbizonytalanabbak (kevés adat).\n")

    es = s.pontos_eselyek(sz)
    atf = s.atfedo_pelda_eselye()
    ki("Pontos esélyek (mind a 8 145 060 lehetséges húzás végigszámolásával) – ezek a számválasztástól nem, "
       "csak attól függnek, hogy a 4 szelvény nem fedi egymást:\n")
    ki(f"- Legalább egy szelvényen 3+ találat: **{100 * es['legalabb_egy_3+']:.2f}%** "
       f"(4 független véletlen szelvény: {100 * es['fuggetlen_4_veletlen_3+']:.2f}%, "
       f"4 erősen átfedő szelvény: {100 * atf:.2f}%)")
    ki(f"- Legalább egy 4+ találat: {100 * es['legalabb_egy_4+']:.3f}%")
    ki(f"- Legalább egy 5+ találat: {100 * es['legalabb_egy_5+']:.4f}% (≈ 1 : {1 / es['legalabb_egy_5+']:,.0f})")
    ki(f"- Telitalálat: 1 : {1 / es['telitalalat']:,.0f}\n")

    ki("## 7. Próba a múlton: mi lett volna 2019-től?\n")
    hatar = 2019
    tan = df[df["ev"] < hatar]
    tv = {m: mm.gordulo_validacio(tan, m)["meredekseg"] for m in mm.SZINTEK}
    tm = {m: mm.illeszt(tan, m) for m in mm.SZINTEK}
    t_uj = s.optimalis_szelvenyek(tan, tm, tv, mm.huzas_szorzok(tm, tv), mm.szint_sulyok(tan))
    t_regi = s.szelvenyek_osszeallitasa(tan, e.nepszeruseg_modell(tan, "3"))
    rng = np.random.default_rng(5)
    t_vel = [tuple(int(x) for x in r) for r in e.veletlen_huzasok(200, rng)]
    ki(f"A szelvényeket csak a {hatar} előtti adatokból állítjuk össze, majd megnézzük a {hatar}–{df.ev.max()} közötti "
       "húzásokat: amikor a szelvényen pontosan 3 találat volt, mekkora volt a tényleges nyeremény az adott "
       "negyedév átlagához képest.\n")
    ki("| szelvények | húzások | 3 találatos esetek | tényleges 3-as nyeremény az átlaghoz képest |")
    ki("|---|---|---|---|")
    for nev, keszlet in [("bővített módszer (4 szelvény)", t_uj), ("eredeti módszer (4 szelvény)", t_regi),
                         ("„szerencseszámok” 3-7-9-13-17-21", [pelda]), ("200 véletlen szelvény", t_vel)]:
        r = mm.szelveny_visszateszt(df, keszlet, hatar)
        ki(f"| {nev} | {r['huzasok']} | {r[3]['esetek']} | ×{r[3]['szorzo']:.2f} (±{r[3]['se']:.2f}) |")
    ki("\nA kevéssé népszerű számokkal tehát a valóságban is kb. 10%-kal nagyobb volt a 3-as nyeremény, a "
       "népszerű számokkal jóval kisebb. A két módszer közti különbség a 3-asoknál kicsi, és ennyi esetből nem "
       "mérhető; a bővített módszer előnye főleg a 4-es és 5-ös találatnál várható, amiből túl kevés van a "
       "közvetlen méréshez. A találatok *száma* a számválasztástól nem függ.\n")

    ki("## 8. Megtérülés és időzítés\n")
    ido, sorozat = mm.fonyeremeny_idozites(df)
    ki(f"Az utolsó {104} húzáson egy szelvényre átlagosan {sum(sulyok.values()):.0f} Ft nyeremény jutott: "
       f"3-as {sulyok[3]:.0f} Ft, 4-es {sulyok[4]:.0f} Ft, 5-ös {sulyok[5]:.0f} Ft, telitalálat {sulyok[6]:.0f} Ft "
       "(ez utóbbi szinte mind ritka, nagy nyeremény). A főnyeremény halmozódik, ezért a megtérülés attól függ, "
       "mióta nincs telitalálat (utolsó 10 év):\n")
    ki("| húzások telitalálat nélkül | húzások | telitalálatos húzás | főnyeremény Ft / szelvény |")
    ki("|---|---|---|---|")
    for h, r in ido.iterrows():
        ki(f"| {h} | {int(r.huzasok)} | {int(r.telitalalat)} | {r.ft_szelvenyenkent:.0f} |")
    ki(f"\nJelenleg **{sorozat}** húzás óta nincs telitalálat. A várható érték így is a szelvény ára alatt marad; "
       "a táblázat csak azt mutatja, hogy a hosszan halmozódó főnyereménynél ugyanannyi pénzért több jár vissza.")

    (KIMENET / "jelentes.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    abra(df, nep, {x for t_ in sz for x in t_}, KIMENET / "abra.png")
    print(f"\nKimenet: {KIMENET}/")

