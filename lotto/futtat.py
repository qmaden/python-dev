"""Teljes elemzés futtatása: tisztítás -> tesztek -> népszerűség -> 4 szelvény.

    python futtat.py [hatos.csv]

Kimenet az `eredmenyek/` mappába:
    hatos_tiszta.csv  – tisztított adat
    jelentes.md       – számszerű eredmények
    abra.png          – gyakoriság vs. játékos-népszerűség
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

import elemzes as e
import szelvenyek as s
from tisztitas import beolvas, tisztitasi_jelentes

ITT = Path(__file__).parent
KIMENET = ITT / "eredmenyek"


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


def main(csv: Path) -> None:
    KIMENET.mkdir(exist_ok=True)
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

    ki("## 4. Játékos-népszerűség (nyertesek számából)\n")
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

    ki("## 5. Ajánlott 4 szelvény\n")
    sz = s.szelvenyek_osszeallitasa(df, nep)
    ki("| # | Számok | Népszerűségi pontszám | Becsült 3-as nyeremény-szorzó |")
    ki("|---|---|---|---|")
    for i, t_ in enumerate(sz, 1):
        pont = sum(nep[x] for x in t_)
        ki(f"| {i} | {' – '.join(map(str, t_))} | {pont:+.3f} | ×{np.exp(v['meredekseg'] * pont):.2f} |")
    pelda = (3, 7, 9, 13, 17, 21)
    pp = sum(nep[x] for x in pelda)
    ki(f"| – | összehasonlítás: „szerencseszámok” {' – '.join(map(str, pelda))} | {pp:+.3f} | "
       f"×{np.exp(v['meredekseg'] * pp):.2f} |\n")

    es = s.pontos_eselyek(sz)
    atf = s.atfedo_pelda_eselye()
    ki("Pontos esélyek (mind a 8 145 060 lehetséges húzás végigszámolásával):\n")
    ki(f"- Legalább egy szelvényen 3+ találat: **{100 * es['legalabb_egy_3+']:.2f}%** "
       f"(4 független véletlen szelvény: {100 * es['fuggetlen_4_veletlen_3+']:.2f}%, "
       f"4 erősen átfedő szelvény: {100 * atf:.2f}%)")
    ki(f"- Legalább egy 4+ találat: {100 * es['legalabb_egy_4+']:.3f}%")
    ki(f"- Legalább egy 5+ találat: {100 * es['legalabb_egy_5+']:.4f}% (≈ 1 : {1 / es['legalabb_egy_5+']:,.0f})")
    ki(f"- Telitalálat: 1 : {1 / es['telitalalat']:,.0f}")

    (KIMENET / "jelentes.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    abra(df, nep, {x for t_ in sz for x in t_}, KIMENET / "abra.png")
    print(f"\nKimenet: {KIMENET}/")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ITT / "data" / "hatos.csv")
