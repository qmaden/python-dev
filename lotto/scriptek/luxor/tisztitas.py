"""Luxor CSV (+ heti nyeremények) beolvasása és tisztítása.

A játék röviden: 75 szám 5 oszlopban (L 1–15, U 16–30, X 31–45, O 46–60, R 61–75).
A játékos oszloponként 4 számot jelöl (összesen 20), a gép ezeket véletlenszerűen
rakja ki egy 5×5-ös táblára oszloponként 1-1 lóherével. Kép = a belső 3×3 (6 szám),
Keret = a külső gyűrű (14 szám), Luxor = mind a 20. A sorsolás addig tart, amíg
legalább egy szelvényen össze nem jön a Luxor. Jackpot: ha ez a határszámon belül
történik (a határ 32-ről indul, és hetente eggyel nő, amíg valaki el nem viszi).

A szerencsejatek.hu `luxor.csv` nyers formátuma:
    év; hét; dátum; jackpot-határ; első kép (hányadik golyónál); első keret; luxor;
    kihúzott számok húzási sorrendben (36–51 db, a luxorig)

Talált problémák:
  * UTF-8 BOM, CRLF sorvégek, nincs fejléc, változó mezőszám
  * 2001–2004/28: a négy határszám-mező 0 (hiányzó adat), a dátum 2004 végéig hiányzik
  * 2004/32: a luxor a 43. golyónál jött, de csak 39 szám szerepel -> hiányos sorozat
  * 4 hétnél a jackpot-határ eltér a "+1 vagy vissza 32-re" szabálytól
    (2016/51, 2017/35, 2018/2, 2018/15) – valószínűleg akciós hetek; csak jelöljük
  * a nyereménytáblák (darabszám, Ft) csak 2015/5-től érhetők el, külön fájlban;
    3 hétnek nincs oldala (2016/51, 2016/52, 2022/52); jackpot-nyerésnél az oldal a
    határszám helyett a tényleges golyószámot mutatja (2015/23, 2015/49, 2016/19)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

N_SZAM = 75
OSZLOPOK = "LUXOR"
JATEKOS_DB_OSZLOPONKENT = 4
JATEKOS_DB = 20
KEP_DB, KERET_DB = 6, 14
JACKPOT_KEZDO_HATAR = 32


def oszlop(szam: int | np.ndarray):
    """1..75 -> 0..4 (L, U, X, O, R)."""
    return (np.asarray(szam) - 1) // 15


def beolvas(utvonal: str | Path, nyeremenyek: str | Path | None = None) -> pd.DataFrame:
    sorok = Path(utvonal).read_text(encoding="utf-8-sig").splitlines()
    rek = []
    for sor in sorok:
        if not sor.strip():
            continue
        m = sor.strip().split(";")
        szamok = [int(x) for x in m[7:] if x.strip()]
        rek.append(
            {
                "ev": int(m[0]),
                "het": int(m[1]),
                "datum": m[2].strip().rstrip(".") or None,
                "jackpot_hatar": int(m[3]),
                "elso_kep": int(m[4]),
                "elso_keret": int(m[5]),
                "luxor": int(m[6]),
                "huzott": szamok,
            }
        )
    df = pd.DataFrame(rek)
    df["datum"] = pd.to_datetime(df["datum"], format="%Y.%m.%d", errors="coerce")
    df["n_huzott"] = df["huzott"].map(len)

    # --- érvényesség -------------------------------------------------------
    for sz in df["huzott"]:
        if min(sz) < 1 or max(sz) > N_SZAM or len(set(sz)) != len(sz):
            raise ValueError(f"Hibás számsor: {sz}")
    if df.duplicated(["ev", "het"]).any():
        raise ValueError("Duplikált hét")

    # --- hiányzó adatok -----------------------------------------------------
    hatar_oszlopok = ["jackpot_hatar", "elso_kep", "elso_keret", "luxor"]
    hianyzik = (df[hatar_oszlopok] == 0).all(axis=1)
    df[hatar_oszlopok] = df[hatar_oszlopok].astype(float)
    df.loc[hianyzik, hatar_oszlopok] = np.nan
    # ahol nincs adat, a luxor = a kihúzott számok száma (a sorozat a luxorig tart)
    df["luxor"] = df["luxor"].fillna(df["n_huzott"].astype(float))
    df["teljes_sorozat"] = df["luxor"] == df["n_huzott"]

    if not ((df["elso_kep"] <= df["elso_keret"]) & (df["elso_keret"] <= df["luxor"]) | hianyzik).all():
        raise ValueError("elso_kep <= elso_keret <= luxor sérül")

    # --- időrend + származtatott oszlopok --------------------------------
    df = df.sort_values(["ev", "het"]).reset_index(drop=True)
    df.insert(0, "huzas_id", np.arange(1, len(df) + 1))
    df["jackpot"] = (df["luxor"] <= df["jackpot_hatar"]).where(df["jackpot_hatar"].notna())
    elozo_jp = df["jackpot"].shift(1)
    vart_hatar = np.where(elozo_jp == True, JACKPOT_KEZDO_HATAR, df["jackpot_hatar"].shift(1) + 1)  # noqa: E712
    df["hatar_szabalytalan"] = df["jackpot_hatar"].notna() & df["jackpot_hatar"].shift(1).notna() & (
        df["jackpot_hatar"] != vart_hatar
    )

    if nyeremenyek is not None and Path(nyeremenyek).exists():
        ny = pd.read_csv(nyeremenyek)
        df = df.merge(ny, on=["ev", "het"], how="left")
        # kereszt-ellenőrzés a két forrás között
        van = df["hatar_luxor"].notna()
        df["forras_egyezik"] = np.where(
            van,
            (df["hatar_luxor"] == df["luxor"])
            & (df["hatar_elso_kep"] == df["elso_kep"])
            & (df["hatar_elso_keret"] == df["elso_keret"])
            # jackpot-nyerésnél az oldal a határ helyett a tényleges golyószámot írja ki
            & ((df["hatar_jackpot"] == df["jackpot_hatar"])
               | ((df["db_jackpot"] > 0) & (df["hatar_jackpot"] == df["luxor"]))),
            np.nan,
        )
    return df


def huzott_matrix(df: pd.DataFrame, elso: int | None = None) -> np.ndarray:
    """(húzások × 75) 0/1 mátrix. `elso`: csak az első ennyi golyó számít."""
    m = np.zeros((len(df), N_SZAM), dtype=np.int8)
    for i, sz in enumerate(df["huzott"]):
        sz = sz[:elso] if elso else sz
        m[i, np.array(sz) - 1] = 1
    return m


def pozicio_matrix(df: pd.DataFrame) -> np.ndarray:
    """(húzások × 75): hányadik golyóként húzták a számot (0 = nem húzták a luxorig)."""
    p = np.zeros((len(df), N_SZAM), dtype=np.int16)
    for i, sz in enumerate(df["huzott"]):
        p[i, np.array(sz) - 1] = np.arange(1, len(sz) + 1)
    return p


def tisztitasi_jelentes(df: pd.DataFrame) -> str:
    s = []
    s.append(f"Húzások száma: {len(df)}  ({df.ev.min()}/{df.het.iloc[0]} – {df.ev.max()}/{df.het.iloc[-1]})")
    s.append(f"Dátummal rendelkező sorok: {df.datum.notna().sum()} (első: {df.datum.min():%Y-%m-%d})")
    s.append(f"Határszámok ismertek: {df.elso_kep.notna().sum()} húzás (2004/29-től)")
    hiany = df[~df.teljes_sorozat]
    s.append("Hiányos számsor: " + (", ".join(f"{r.ev}/{r.het} ({r.n_huzott} szám a {int(r.luxor)} helyett)"
                                            for r in hiany.itertuples()) or "nincs"))
    s.append(f"Kihúzott golyók száma a luxorig: {df.n_huzott.min()}–{df.n_huzott.max()} (átlag {df.luxor.mean():.1f})")
    s.append(f"Jackpot-nyerések: {int(df.jackpot.sum())}")
    s.append("Szabálytól eltérő jackpot-határ: "
             + ", ".join(f"{r.ev}/{r.het}" for r in df[df.hatar_szabalytalan].itertuples()))
    if "db_kep" in df:
        van = df[df.db_kep.notna()]
        hianyzik = df[(df.ev >= van.ev.min()) & df.db_kep.isna() & (df.huzas_id > van.huzas_id.min())]
        s.append(f"Nyereménytábla ismert: {len(van)} húzás ({van.ev.iloc[0]}/{van.het.iloc[0]}-tól)"
                 + (f", az oldalon hiányzik: {', '.join(f'{r.ev}/{r.het}' for r in hianyzik.itertuples())}"
                    if len(hianyzik) else ""))
        if "forras_egyezik" in df:
            nem = df[df.forras_egyezik == 0]
            s.append(f"CSV és nyereménytábla határszámai egyeznek: {int((df.forras_egyezik == 1).sum())} hét"
                     + (f", eltér: {', '.join(f'{r.ev}/{r.het}' for r in nem.itertuples())}" if len(nem) else ""))
    return "\n".join(s)


if __name__ == "__main__":
    from ..kozos import ADATOK

    print(tisztitasi_jelentes(beolvas(ADATOK / "luxor.csv", ADATOK / "luxor_nyeremenyek.csv")))
