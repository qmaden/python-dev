"""Statisztikai elemzések a Hatoslottó húzásaira.

1. Véletlenszerűségi tesztek  -> van-e bármi kihasználható mintázat a húzásokban?
2. Stratégiák visszatesztelése (forró / hideg / "esedékes" számok)
3. Játékos-népszerűségi modell -> mely számokat játsszák meg sokan?
   (a nyertesek számából becsülve; ez az egyetlen tényező, ami a nyeremény
   *nagyságát* befolyásolja, mert a nyereményalapot a nyertesek osztják el)
"""

from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from math import comb

import numpy as np
import pandas as pd
from scipy import stats

from ..kozos import khi2_illeszkedes as _khi2_illeszkedes
from ..kozos import veletlen_reszhalmazok
from .tisztitas import SZAM_OSZLOPOK

N_SZAM, K = 45, 6
P_SZAM = K / N_SZAM  # egy adott szám esélye egy húzáson: 6/45 = 13,3%


# ---------------------------------------------------------------------------
# Segédfüggvények
# ---------------------------------------------------------------------------
def szam_matrix(df: pd.DataFrame) -> np.ndarray:
    """(húzások × 45) 0/1 mátrix: az i-edik szám kihúzták-e."""
    m = np.zeros((len(df), N_SZAM), dtype=np.int8)
    sz = df[SZAM_OSZLOPOK].to_numpy() - 1
    m[np.arange(len(df))[:, None], sz] = 1
    return m


@lru_cache(maxsize=1)
def osszes_kombinacio() -> np.ndarray:
    """Mind a C(45,6) = 8 145 060 lehetséges húzás (int8, 1-től számozva)."""
    it = combinations(range(1, N_SZAM + 1), K)
    return np.fromiter(it, dtype=np.dtype((np.int8, K)), count=comb(N_SZAM, K))


def veletlen_huzasok(n: int, rng: np.random.Generator) -> np.ndarray:
    return veletlen_reszhalmazok(n, N_SZAM, K, rng)




# ---------------------------------------------------------------------------
# 1. Véletlenszerűségi tesztek
# ---------------------------------------------------------------------------
def gyakorisag_teszt(df: pd.DataFrame, n_szim: int = 4000, seed: int = 1) -> dict:
    """Egyenletes-e a számok gyakorisága? Monte-Carlo p-érték, mert egy húzáson
    belül a számok nem függetlenek (visszatevés nélküli húzás)."""
    m = szam_matrix(df)
    db = m.sum(axis=0)
    vart = len(df) * P_SZAM
    stat = ((db - vart) ** 2 / vart).sum()
    rng = np.random.default_rng(seed)
    szim = np.empty(n_szim)
    for i in range(n_szim):
        h = veletlen_huzasok(len(df), rng)
        c = np.bincount(h.ravel(), minlength=N_SZAM + 1)[1:]
        szim[i] = ((c - vart) ** 2 / vart).sum()
    return {
        "huzasok": len(df),
        "vart_db": vart,
        "min": (int(db.argmin()) + 1, int(db.min())),
        "max": (int(db.argmax()) + 1, int(db.max())),
        "khi2": stat,
        "p": (szim >= stat).mean(),
    }


def eloszlas_tesztek(df: pd.DataFrame) -> pd.DataFrame:
    """Összeg, páratlanok száma, szomszédos párok, ismétlés az előző húzásból,
    1–31 közötti számok aránya: mindet a pontos elméleti eloszláshoz hasonlítjuk."""
    h = df[SZAM_OSZLOPOK].to_numpy()
    osszes = osszes_kombinacio().astype(np.int16)
    eredmeny = []

    def teszt(nev, megf_ertek, elm_ertek, leiras):
        lo = min(megf_ertek.min(), elm_ertek.min())
        hi = max(megf_ertek.max(), elm_ertek.max())
        bins = np.arange(lo, hi + 2)
        o = np.histogram(megf_ertek, bins)[0].astype(float)
        p = np.histogram(elm_ertek, bins)[0] / len(elm_ertek)
        r = _khi2_illeszkedes(o, p)
        eredmeny.append(
            {
                "teszt": nev,
                "leiras": leiras,
                "megfigyelt_atlag": megf_ertek.mean(),
                "elmeleti_atlag": elm_ertek.mean(),
                "p_ertek": r.pvalue,
            }
        )

    teszt("szamok_osszege", h.sum(1), osszes.sum(1), "6 szám összege (elmélet: 138)")
    teszt("paratlanok", (h % 2).sum(1), (osszes % 2).sum(1), "páratlan számok darabszáma")
    teszt(
        "szomszedos_parok",
        (np.diff(h, axis=1) == 1).sum(1),
        (np.diff(osszes, axis=1) == 1).sum(1),
        "egymást követő számpárok (pl. 12-13)",
    )
    teszt("szuletesnap_1_31", (h <= 31).sum(1), (osszes <= 31).sum(1), "1–31 közötti számok darabszáma")

    # ismétlődés az előző húzásból: hipergeometrikus(45, 6, 6)
    m = szam_matrix(df)
    ism = (m[1:] & m[:-1]).sum(1)
    k = np.arange(7)
    p = stats.hypergeom.pmf(k, N_SZAM, K, K)
    o = np.bincount(ism, minlength=7).astype(float)
    r = _khi2_illeszkedes(o, p)
    eredmeny.append(
        {
            "teszt": "ismetles_elozobol",
            "leiras": "hány szám ismétlődik az előző húzásból",
            "megfigyelt_atlag": ism.mean(),
            "elmeleti_atlag": K * K / N_SZAM,
            "p_ertek": r.pvalue,
        }
    )

    # kimaradási hossz (gap): geometriai eloszlás p = 6/45
    gaps = []
    for i in range(N_SZAM):
        idx = np.flatnonzero(m[:, i])
        gaps.extend(np.diff(idx))
    gaps = np.array(gaps)
    g_max = 60
    o = np.bincount(np.minimum(gaps, g_max), minlength=g_max + 1)[1:].astype(float)
    kk = np.arange(1, g_max + 1)
    p = stats.geom.pmf(kk, P_SZAM)
    p[-1] = stats.geom.sf(g_max - 1, P_SZAM)
    r = _khi2_illeszkedes(o, p)
    eredmeny.append(
        {
            "teszt": "kimaradas_hossza",
            "leiras": "két megjelenés közti húzások száma (geometriai eloszlás)",
            "megfigyelt_atlag": gaps.mean(),
            "elmeleti_atlag": 1 / P_SZAM,
            "p_ertek": r.pvalue,
        }
    )
    return pd.DataFrame(eredmeny)


def par_teszt(df: pd.DataFrame, n_szim: int = 300, seed: int = 2) -> dict:
    """Vannak-e "összetartó" számpárok? A 990 pár gyakoriságának szórását
    hasonlítjuk szimulált véletlen lottókhoz."""
    m = szam_matrix(df).astype(np.int32)
    iu = np.triu_indices(N_SZAM, 1)
    megf = (m.T @ m)[iu]
    rng = np.random.default_rng(seed)
    szim = np.empty(n_szim)
    for i in range(n_szim):
        h = veletlen_huzasok(len(df), rng)
        mm = np.zeros((len(df), N_SZAM), dtype=np.int32)
        mm[np.arange(len(df))[:, None], h - 1] = 1
        szim[i] = (mm.T @ mm)[iu].var()
    leggyakoribb = np.argmax(megf)
    return {
        "par_db_szoras": megf.var(),
        "p": (szim >= megf.var()).mean(),
        "leggyakoribb_par": (iu[0][leggyakoribb] + 1, iu[1][leggyakoribb] + 1, int(megf.max())),
        "vart_par_db": len(df) * comb(N_SZAM - 2, K - 2) / comb(N_SZAM, K),
    }


# ---------------------------------------------------------------------------
# 2. Stratégiák visszatesztelése
# ---------------------------------------------------------------------------
def strategia_backtest(df: pd.DataFrame, ablak: int = 50) -> pd.DataFrame:
    """Minden húzás előtt kiválasztunk 6 számot csak a korábbi húzások alapján,
    és megnézzük, átlagosan hány találatunk lett. Elmélet: 6*6/45 = 0,8."""
    m = szam_matrix(df)
    rng = np.random.default_rng(3)
    talalat = {"forro (utolso 50 leggyakoribb)": [], "hideg (utolso 50 legritkabb)": [],
               "esedekes (legregebben huzott)": [], "veletlen": []}
    utolso = np.full(N_SZAM, -1)
    for t in range(len(df)):
        if t >= ablak:
            gy = m[t - ablak:t].sum(0) + rng.random(N_SZAM) * 1e-3  # döntetlen véletlen bontása
            valaszt = {
                "forro (utolso 50 leggyakoribb)": np.argsort(-gy)[:K],
                "hideg (utolso 50 legritkabb)": np.argsort(gy)[:K],
                "esedekes (legregebben huzott)": np.argsort(utolso + rng.random(N_SZAM) * 1e-3)[:K],
                "veletlen": rng.choice(N_SZAM, K, replace=False),
            }
            for nev, v in valaszt.items():
                talalat[nev].append(m[t, v].sum())
        utolso[m[t] == 1] = t
    sorok = []
    for nev, t in talalat.items():
        t = np.array(t)
        sorok.append({
            "strategia": nev,
            "huzasok": len(t),
            "atlag_talalat": t.mean(),
            "3+_talalat_arany_%": 100 * (t >= 3).mean(),
            "p_ertek_vs_0.8": stats.ttest_1samp(t, K * K / N_SZAM).pvalue,
        })
    sorok.append({"strategia": "ELMELET (barmely 6 szam)", "huzasok": np.nan,
                  "atlag_talalat": K * K / N_SZAM,
                  "3+_talalat_arany_%": 100 * stats.hypergeom.sf(2, N_SZAM, K, K),
                  "p_ertek_vs_0.8": np.nan})
    return pd.DataFrame(sorok)


# ---------------------------------------------------------------------------
# 3. Játékos-népszerűség becslése a nyertesek számából
# ---------------------------------------------------------------------------
def _nepszeruseg_design(df: pd.DataFrame):
    d = df[df["db_3"].notna() & (df["db_3"] > 0)].copy()
    # halmozódás: hány húzás óta nem volt telitalálat (nagyobb főnyeremény -> több szelvény)
    streak, s = [], 0
    for _, r in df.iterrows():
        streak.append(s)
        s = 0 if (r["db_6"] or 0) > 0 else s + 1
    df_streak = pd.Series(streak, index=df.index)
    d["halmozodas"] = np.log1p(df_streak.loc[d.index])
    d["periodus"] = d["ev"].astype(str) + "_" + d["nap"].where(d["nap"] == "Csütörtök", "V")
    X_per = pd.get_dummies(d["periodus"], dtype=float)
    X_szam = pd.DataFrame(szam_matrix(d), index=d.index, columns=range(1, N_SZAM + 1), dtype=float)
    return d, X_per, X_szam


def nepszeruseg_modell(df: pd.DataFrame, kategoria: str = "3", tanito_maszk=None) -> pd.Series:
    """log(nyertesek száma) = periódus-hatás (év × nap, ~ eladott szelvények)
                              + β·log(1 + halmozódó hetek)
                              + Σ_{kihúzott számok} népszerűség_i

    A népszerűség_i ≈ log-arányban mennyivel több nyertes van, ha az i-t kihúzzák.
    Pozitív = sokan játsszák, negatív = kevesen. (Nulla összegűre centrálva.)"""
    d, X_per, X_szam = _nepszeruseg_design(df)
    y = np.log(d[f"db_{kategoria}"].clip(lower=0.5))
    if tanito_maszk is not None:
        sel = tanito_maszk.loc[d.index].to_numpy()
        d, X_per, X_szam, y = d[sel], X_per[sel], X_szam[sel], y[sel]
        X_per = X_per.loc[:, X_per.sum() > 0]
    # A 45 szám-dummy összege mindig 6 -> 1 szabadsági fok elvész; az utolsót elhagyjuk,
    # majd centrálunk.
    X = np.hstack([X_per.to_numpy(), d[["halmozodas"]].to_numpy(), X_szam.to_numpy()[:, :-1]])
    beta, *_ = np.linalg.lstsq(X, y.to_numpy(), rcond=None)
    nep = np.append(beta[-(N_SZAM - 1):], 0.0)
    nep -= nep.mean()
    return pd.Series(nep, index=range(1, N_SZAM + 1), name=f"nepszeruseg_{kategoria}")


def nepszeruseg_validacio(df: pd.DataFrame, hatar_ev: int = 2016) -> dict:
    """Mintán kívüli ellenőrzés: a hatar_ev előtti adatokon becsült népszerűség
    előrejelzi-e a későbbi húzásoknál a 3-as nyeremény összegét?"""
    tanito = df["ev"] < hatar_ev
    nep = nepszeruseg_modell(df, "3", tanito_maszk=tanito)
    teszt = df[(~tanito) & df["ft_3"].notna() & (df["ft_3"] > 0)].copy()
    m = szam_matrix(teszt)
    teszt["pontszam"] = m @ nep.to_numpy()
    # az év × nap átlagos nyereményszinttől való eltérés
    teszt["periodus"] = teszt["ev"].astype(str) + teszt["nap"]
    teszt["log_ft3_elteres"] = np.log(teszt["ft_3"]) - np.log(teszt["ft_3"]).groupby(teszt["periodus"]).transform("mean")
    r, p = stats.spearmanr(teszt["pontszam"], teszt["log_ft3_elteres"])
    # log(nyeremény) ≈ meredekség × pontszám  -> a becsült nyeremény-szorzó exp(meredekség × pontszám)
    meredekseg = stats.linregress(teszt["pontszam"], teszt["log_ft3_elteres"]).slope
    q = pd.qcut(teszt["pontszam"], 4, labels=["legkevésbé népszerű", "2.", "3.", "legnépszerűbb"])
    kvart = np.exp(teszt.groupby(q, observed=True)["log_ft3_elteres"].mean())
    return {
        "teszt_huzasok": len(teszt),
        "spearman_r": r,
        "p": p,
        "meredekseg": meredekseg,
        "kvartilis_ft3_szorzo": kvart,
    }
