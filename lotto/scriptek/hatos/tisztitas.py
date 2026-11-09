"""Hatoslottó CSV beolvasása és tisztítása.

A szerencsejatek.hu-ról letölthető `hatos.csv` nyers formátuma:
    év; hét; nap; dátum;
    6-os db; 6-os nyeremény; 5+1-es db; 5+1-es nyeremény;
    5-ös db; 5-ös nyeremény; 4-es db; 4-es nyeremény; 3-as db; 3-as nyeremény;
    sz1; sz2; sz3; sz4; sz5; sz6; [pótszám]

Talált problémák, amiket itt kezelünk:
  * UTF-8 BOM a fájl elején
  * nincs fejléc
  * vegyes mezőszám: 2007-ig van 7. szám (pótszám az 5+1-es találathoz),
    utána egy darabig üres 21. mező (záró ';'), később csak 20 mező
  * a nyeremények szövegként, ezres szóközzel és "Ft" utótaggal ("1 152 640 105 Ft"),
    az 5+1-es oszlopban néha csak "0"
  * a dátum 2004 novembere előtt hiányzik
  * 1988–1997 között a nyertesszámok mind 0 -> ez hiányzó adat, nem valódi nulla
  * 1988–1993 hiányos / ritkább húzások (évente 2–29 sor)
  * 2025 szeptemberétől csütörtökön is van húzás, így (év, hét) már nem egyedi kulcs
  * a nap megnevezése a forrásban utólag változott: a 2004 előtti húzások a korábbi
    letöltésben "Csütörtök", a mostaniban "Hétfő" címkével szerepelnek (az elemzést nem
    érinti: a csütörtöki húzásokat csak 2025-től kezeljük külön)
  * év-forduló: a "játékév" (pl. 2022/52. hét) dátuma lehet már a következő naptári év
  * 1998/3. hét: 0 db telitalálat, de "1 Ft" nyeremény -> hibás érték
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SZAM_OSZLOPOK = [f"sz{i}" for i in range(1, 7)]
KATEGORIAK = ["6", "5p1", "5", "4", "3"]  # 5p1 = 5 + pótszám


def _ft_to_int(s: str) -> int:
    s = s.replace("Ft", "").replace(" ", "").replace(" ", "").strip()
    return int(s) if s else 0


def beolvas(utvonal: str | Path) -> pd.DataFrame:
    """Nyers CSV -> tiszta, időrendbe (régi -> új) rendezett DataFrame."""
    sorok = Path(utvonal).read_text(encoding="utf-8-sig").splitlines()
    rekordok = []
    for sor in sorok:
        if not sor.strip():
            continue
        m = sor.split(";")
        if len(m) not in (20, 21):
            raise ValueError(f"Váratlan mezőszám ({len(m)}): {sor!r}")
        rek = {
            "ev": int(m[0]),
            "het": int(m[1]),
            "nap": m[2].strip(),
            "datum": m[3].strip().rstrip(".") or None,
        }
        for i, kat in enumerate(KATEGORIAK):
            rek[f"db_{kat}"] = int(m[4 + 2 * i].strip() or 0)
            rek[f"ft_{kat}"] = _ft_to_int(m[5 + 2 * i])
        szamok = [int(x) for x in m[14:20]]
        for j, sz in enumerate(sorted(szamok)):
            rek[SZAM_OSZLOPOK[j]] = sz
        rek["potszam"] = int(m[20]) if len(m) == 21 and m[20].strip() else np.nan
        rekordok.append(rek)

    df = pd.DataFrame(rekordok)
    df["datum"] = pd.to_datetime(df["datum"], format="%Y.%m.%d", errors="coerce")

    # --- érvényesség-ellenőrzés -------------------------------------------
    szamok = df[SZAM_OSZLOPOK].to_numpy()
    if szamok.min() < 1 or szamok.max() > 45:
        raise ValueError("1..45 tartományon kívüli szám")
    if any(len(set(r)) != 6 for r in szamok):
        raise ValueError("Ismétlődő szám egy húzáson belül")
    if df.duplicated(["ev", "het", "nap"]).any():
        raise ValueError("Duplikált húzás (év, hét, nap)")

    # --- hiányzó adatok jelölése --------------------------------------------
    # 1998 előtt a nyertes-darabszámok és nyeremények hiányoznak (mind 0).
    nincs_nyertes_adat = df[[f"db_{k}" for k in ("5", "4", "3")]].sum(axis=1) == 0
    for kat in KATEGORIAK:
        df.loc[nincs_nyertes_adat, [f"db_{kat}", f"ft_{kat}"]] = np.nan
    # 0 nyertes mellett nem lehet nyeremény (pl. 1998/3: "1 Ft")
    for kat in KATEGORIAK:
        df.loc[df[f"db_{kat}"] == 0, f"ft_{kat}"] = 0

    # --- időrend + segédoszlopok -----------------------------------------
    nap_sorrend = {"Hétfő": 0, "Csütörtök": 3, "Szombat": 5, "Vasárnap": 6}
    df["_nap_rend"] = df["nap"].map(nap_sorrend)
    df = df.sort_values(["ev", "het", "_nap_rend"]).drop(columns="_nap_rend")
    df = df.reset_index(drop=True)
    df.insert(0, "huzas_id", np.arange(1, len(df) + 1))
    df["csutortok"] = (df["nap"] == "Csütörtök").astype(int)
    df["szamok_osszege"] = df[SZAM_OSZLOPOK].sum(axis=1)
    return df


def tisztitasi_jelentes(df: pd.DataFrame) -> str:
    sor = []
    sor.append(f"Húzások száma: {len(df)}  ({df.ev.min()}–{df.ev.max()})")
    sor.append(f"Dátummal rendelkező sorok: {df.datum.notna().sum()} (első: {df.datum.min():%Y-%m-%d})")
    sor.append(f"Nyertes-darabszám ismert: {df.db_3.notna().sum()} húzás (1998-tól)")
    sor.append(f"Pótszámos húzások: {df.potszam.notna().sum()} (–{int(df[df.potszam.notna()].ev.max())})")
    sor.append(f"Csütörtöki húzások: {int(df.csutortok.sum())} (első: {df[df.csutortok == 1].datum.min():%Y-%m-%d})")
    evente = df.groupby("ev").size()
    hianyos = evente[evente < 50]
    sor.append("Hiányos évek (<50 húzás): " + ", ".join(f"{e}:{n}" for e, n in hianyos.items() if e < 2026))
    return "\n".join(sor)


if __name__ == "__main__":
    import sys

    from ..kozos import ADATOK

    adat = beolvas(sys.argv[1] if len(sys.argv) > 1 else ADATOK / "hatos.csv")
    print(tisztitasi_jelentes(adat))
