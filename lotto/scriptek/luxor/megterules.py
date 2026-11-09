"""Luxor: eladott szelvények, megtérülés és a jackpot-határ szerepe.

A nyertesek számából visszaszámolható, hány szelvény volt játékban: egy véletlen
szelvényen a kép esélye pontosan ismert (oszloponként a kihúzott számok számából),
így   eladott szelvények ≈ kép-nyertesek / P(kép).

Ezzel két dolog ellenőrizhető / számolható, ami egyetlen szelvény múltbeli
találataiból nem (a ritka nyeremények – luxor, jackpot, első kép – egy adott
szelvénnyel a múltban szinte sosem jöttek volna ki, ezért azok átlaga torz):

  * a tábla szerkezetére felírt képlet független ellenőrzése: a keret-, első kép-,
    első keret- és luxor-nyertesek várt száma egyezik-e a ténylegessel;
  * a szelvényenkénti tényleges megtérülés (összes kifizetés / eladott szelvény),
    és hogy ez hogyan függ a jackpot-határszámtól.
"""

from __future__ import annotations

from math import comb

import numpy as np
import pandas as pd

from .tisztitas import JACKPOT_KEZDO_HATAR, huzott_matrix, pozicio_matrix

KATEGORIAK = {"kep": "kép", "keret": "keret", "elso_kep": "első kép", "elso_keret": "első keret",
              "luxor": "luxor", "jackpot": "jackpot"}
_C2 = np.array([comb(k, 2) / comb(15, 2) for k in range(16)])  # egy oszlop 2 adott helye kint van
_C4 = np.array([comb(k, 4) / comb(15, 4) for k in range(16)])  # egy oszlop mind a 4 száma kint van


def _oszlop_db(m: np.ndarray) -> np.ndarray:
    return np.stack([m[:, j * 15:(j + 1) * 15].sum(1) for j in range(5)], axis=1)


def _p_kep(c: np.ndarray) -> np.ndarray:
    return _C2[c[:, 1]] * _C2[c[:, 2]] * _C2[c[:, 3]]


def _p_keret(c: np.ndarray) -> np.ndarray:
    return _C4[c[:, 0]] * _C4[c[:, 4]] * _p_kep(c)


def heti_tabla(df: pd.DataFrame) -> pd.DataFrame:
    """Hetente: becsült eladott szelvényszám, várt nyertesszámok, kifizetés kategóriánként."""
    d = df[df["db_kep"].notna() & (df["db_kep"] > 0) & df["teljes_sorozat"]].copy()
    c = _oszlop_db(huzott_matrix(d))
    d["szelvenyek"] = d["db_kep"] / _p_kep(c)
    d["vart_keret"] = d["szelvenyek"] * _p_keret(c)
    d["vart_luxor"] = d["szelvenyek"] * np.prod(_C4[c], axis=1)
    poz = pozicio_matrix(d)
    for kat, p in (("elso_kep", _p_kep), ("elso_keret", _p_keret)):
        kint = (poz > 0) & (poz <= d[kat].to_numpy()[:, None])
        d[f"vart_{kat}"] = d["szelvenyek"] * p(_oszlop_db(kint))
    for kat in KATEGORIAK:
        d[f"kif_{kat}"] = d[f"db_{kat}"].fillna(0) * d[f"ft_{kat}"].fillna(0)
    d["kif"] = d[[f"kif_{k}" for k in KATEGORIAK]].sum(axis=1)
    return d


def szerkezet_ellenorzes(t: pd.DataFrame) -> pd.DataFrame:
    """A képletből várt és a tényleges nyertesszám (a szelvényszámot a kép-nyertesekből becsülve)."""
    sor = [{"kategória": KATEGORIAK[k], "tényleges": int(t[f"db_{k}"].sum()), "várt": float(t[f"vart_{k}"].sum())}
           for k in ("keret", "elso_kep", "elso_keret", "luxor")]
    ki = pd.DataFrame(sor)
    ki["arány"] = ki["tényleges"] / ki["várt"]
    return ki


def megterules(t: pd.DataFrame, utolso: int = 52) -> dict:
    """Egy szelvényre jutó átlagos kifizetés (Ft) kategóriánként az utolsó `utolso` héten."""
    d = t.tail(utolso)
    n = d["szelvenyek"].sum()
    ki = {KATEGORIAK[k]: float(d[f"kif_{k}"].sum() / n) for k in KATEGORIAK}
    ki["összesen"] = float(d["kif"].sum() / n)
    ki["szelvények / hét"] = float(d["szelvenyek"].mean())
    return ki


def jackpot_idozites(df: pd.DataFrame, t: pd.DataFrame, utolso: int = 260) -> tuple[pd.DataFrame, int]:
    """A jackpot-határ szerint: milyen gyakran vitték el a jackpotot, és mennyi jutott belőle
    egy szelvényre (mai nyereményszinten). Visszaadja a következő heti határszámot is."""
    d = t.tail(utolso)
    cs = pd.cut(d["jackpot_hatar"], [0, 38, 41, 43, 99], labels=["32–38", "39–41", "42–43", "44+"])
    g = d.groupby(cs, observed=True).agg(hetek=("kif", "size"), jackpot_nyeres=("db_jackpot", lambda x: int((x > 0).sum())),
                                         jp=("kif_jackpot", "sum"), kif=("kif", "sum"), n=("szelvenyek", "sum"))
    g["jackpot_esely_%"] = 100 * g["jackpot_nyeres"] / g["hetek"]
    # az árak változása miatt a jackpotot a többi nyereményhez viszonyítjuk, és a mai szintre vetítjük
    alap = megterules(t)
    alap = alap["összesen"] - alap["jackpot"]
    g["jackpot_ft_szelvenyenkent"] = alap * g["jp"] / (g["kif"] - g["jp"])
    g["osszes_ft_szelvenyenkent"] = alap + g["jackpot_ft_szelvenyenkent"]
    u = df.iloc[-1]
    kovetkezo = JACKPOT_KEZDO_HATAR if u["jackpot"] == True else int(u["jackpot_hatar"]) + 1  # noqa: E712
    return g[["hetek", "jackpot_nyeres", "jackpot_esely_%", "jackpot_ft_szelvenyenkent",
              "osszes_ft_szelvenyenkent"]], kovetkezo
