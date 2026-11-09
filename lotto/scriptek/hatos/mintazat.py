"""Hatoslottó: bővített nyertesszám-modell és a szelvények pontos értékelése.

Az `elemzes.nepszeruseg_modell` csak számonkénti hatást becsül. Az utólagos
ellenőrzés három dolgot mutatott ki, amit ez a modul kezel:

  1. MINTÁZAT-HATÁS: a nyertesek száma attól is függ, hogyan helyezkednek el a
     kihúzott számok egymáshoz képest. Ha két szomszédos szám (pl. 23–24) is kijön,
     kb. 7%-kal kevesebb a 3-as és 16%-kal kevesebb a 4-es nyertes: a játékosok
     kerülik az egymás melletti számokat (és kisebb mértékben a 2-vel, 7-tel
     eltérőket, illetve az egy tízesbe esőket). Mintán kívül is igazolódik.
  2. IDŐBELI ELTOLÓDÁS: a számok népszerűsége lassan változik (a régi és az új
     időszak becslése r ≈ 0,94, a különbség szignifikáns), ezért a friss húzások
     nagyobb súlyt kapnak (felezési idő: 8 év), és az időszak-hatás negyedéves.
  3. A SZELVÉNY TÉNYLEGES SZORZÓJA: ha a szelvényünkön 3 találat van, a húzás
     másik 3 száma nem a miénk. A nyeremény-szorzót ezért nem a 6 számunk
     pontszámának összegéből, hanem az összes olyan húzásra átlagolva kell
     számolni, amelyik a szelvényt pontosan 3 (4, 5) számban találja el.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations
from math import comb

import numpy as np
import pandas as pd
from scipy import stats

from .elemzes import K, N_SZAM, osszes_kombinacio, szam_matrix
from .tisztitas import SZAM_OSZLOPOK

SZINTEK = (3, 4, 5)
JELLEMZOK = {
    "d1": "szomszédos számpár (különbség 1)",
    "d2": "2-vel eltérő számpár",
    "d7": "7-tel eltérő számpár",
    "tizes": "azonos tízesbe eső számpár",
    "vegz": "azonos végződésű számpár",
    "terj": "terjedelem (legnagyobb − legkisebb, tízesekben)",
}
FELEZESI_IDO = 8.0  # év
_IU = np.triu_indices(K, 1)
P_TALALAT = {m: stats.hypergeom.pmf(m, N_SZAM, K, K) for m in (3, 4, 5, 6)}


def jellemzok(h: np.ndarray) -> np.ndarray:
    """(n × 6) számsorokból (n × len(JELLEMZOK)) mintázat-jellemzők."""
    h = np.asarray(h, dtype=np.int16)
    kul = np.abs(h[:, :, None] - h[:, None, :])[:, _IU[0], _IU[1]]
    tizes = (h[:, :, None] // 10 == h[:, None, :] // 10)[:, _IU[0], _IU[1]]
    vegz = (h[:, :, None] % 10 == h[:, None, :] % 10)[:, _IU[0], _IU[1]]
    return np.stack([
        (kul == 1).sum(1), (kul == 2).sum(1), (kul == 7).sum(1),
        tizes.sum(1), vegz.sum(1), (h.max(1) - h.min(1)) / 10,
    ], axis=1).astype(np.float32)


def _ido(d: pd.DataFrame) -> np.ndarray:
    return d["ev"].to_numpy() + (d["het"].to_numpy() - 1) / 53


def _periodus(d: pd.DataFrame) -> pd.Series:
    negyed = ((d["het"] - 1) // 13).clip(0, 3).astype(str)
    return d["ev"].astype(str) + "_" + negyed + "_" + d["nap"].where(d["nap"] == "Csütörtök", "V")


def _ervenyes(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["db_3"].notna() & (df["db_3"] > 0)]


@dataclass
class Modell:
    szint: int
    szam: np.ndarray      # 45 számonkénti hatás (log-skála, 0 átlagra centrálva)
    minta: np.ndarray     # a JELLEMZOK együtthatói
    minta_se: np.ndarray
    rezidualis_szoras: float

    def pontszam(self, h: np.ndarray) -> np.ndarray:
        """Várható log-eltérés a nyertesek számában, ha a `h` számsort húzzák ki."""
        h = np.asarray(h)
        return self.szam[h - 1].sum(1) + jellemzok(h) @ self.minta


def illeszt(df: pd.DataFrame, szint: int = 3, maszk: pd.Series | None = None,
            felezesi_ido: float | None = FELEZESI_IDO, mintazattal: bool = True) -> Modell:
    """log(nyertesek) = negyedév × nap hatás + Σ szám-hatás + mintázat-jellemzők.
    Súlyozott legkisebb négyzetek; a súly a húzás korával feleződik."""
    d = _ervenyes(df)
    if maszk is not None:
        d = d[maszk.loc[d.index]]
    y = np.log(d[f"db_{szint}"].clip(lower=0.5).to_numpy())
    t = _ido(d)
    w = np.ones(len(d)) if felezesi_ido is None else 0.5 ** ((t.max() - t) / felezesi_ido)
    X_per = pd.get_dummies(_periodus(d), dtype=float).to_numpy()
    X_szam = szam_matrix(d).astype(float)[:, :-1]  # a 45 dummy összege 6 -> egyet elhagyunk
    F = jellemzok(d[SZAM_OSZLOPOK].to_numpy()).astype(float) if mintazattal else np.zeros((len(d), 0))
    X = np.hstack([X_per, X_szam, F])
    sw = np.sqrt(w)
    beta, *_ = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)
    r = (y - X @ beta) * sw
    s2 = r @ r / (len(y) - np.linalg.matrix_rank(X))
    nf = F.shape[1]
    se = np.sqrt(np.diag(s2 * np.linalg.pinv((X * w[:, None]).T @ X)))[len(beta) - nf:]
    szam = np.append(beta[len(beta) - nf - (N_SZAM - 1):len(beta) - nf], 0.0)
    minta = beta[len(beta) - nf:] if nf else np.zeros(len(JELLEMZOK))
    return Modell(szint, szam - szam.mean(), minta, se if nf else np.zeros(len(JELLEMZOK)), float(np.sqrt(s2)))


def gordulo_validacio(df: pd.DataFrame, szint: int = 3, elso_ev: int = 2008, mintazattal: bool = True,
                      felezesi_ido: float | None = FELEZESI_IDO) -> dict:
    """Minden évre csak a korábbi évek adataiból becslünk, és az adott év húzásain
    mérjük, mennyire jelzi előre a modell a nyertesek számát (negyedéven belüli eltérés)."""
    d = _ervenyes(df)
    sorok = []
    for ev in range(elso_ev, int(d["ev"].max()) + 1):
        m = illeszt(df, szint, maszk=df["ev"] < ev, mintazattal=mintazattal, felezesi_ido=felezesi_ido)
        te = d[d["ev"] == ev]
        per = _periodus(te).to_numpy()
        y = pd.Series(np.log(te[f"db_{szint}"].clip(lower=0.5).to_numpy()))
        s = pd.Series(m.pontszam(te[SZAM_OSZLOPOK].to_numpy()))
        ft = pd.Series(np.log(te[f"ft_{szint}"].where(te[f"ft_{szint}"] > 0).to_numpy()))
        sorok.append(pd.DataFrame({
            "tenyleges": (y - y.groupby(per).transform("mean")).to_numpy(),
            "becsult": (s - s.groupby(per).transform("mean")).to_numpy(),
            "nyeremeny": (ft - ft.groupby(per).transform("mean")).to_numpy(),
        }))
    r = pd.concat(sorok, ignore_index=True)
    lin = stats.linregress(r["becsult"], r["tenyleges"])
    rn = r.dropna()
    tized = r.groupby(pd.qcut(r["becsult"], 10, labels=False))[["becsult", "tenyleges"]].mean()
    return {
        "huzasok": len(r),
        "meredekseg": float(lin.slope),
        "r2": float(lin.rvalue ** 2),
        "nyeremeny_meredekseg": float(stats.linregress(rn["becsult"], rn["nyeremeny"]).slope),
        "tizedek": tized,
    }


def idobeli_stabilitas(df: pd.DataFrame, hatar_ev: int = 2012) -> dict:
    """Ugyanazok-e a népszerű számok a régi és az új időszakban?"""
    a = illeszt(df, 3, maszk=df["ev"] < hatar_ev, felezesi_ido=None)
    b = illeszt(df, 3, maszk=df["ev"] >= hatar_ev, felezesi_ido=None)
    kul = pd.Series(b.szam - a.szam, index=range(1, N_SZAM + 1))
    return {"r": float(np.corrcoef(a.szam, b.szam)[0, 1]), "valtozas": kul.sort_values()}


# ---------------------------------------------------------------------------
# A szelvény pontos nyeremény-szorzója
# ---------------------------------------------------------------------------
_BINOM = np.array([[comb(n, k) for k in range(K + 1)] for n in range(N_SZAM + 1)], dtype=np.int64)


def _rang(h: np.ndarray) -> np.ndarray:
    """Rendezett (n × 6) számsorok sorszáma (kolexikografikus rend, 0-tól)."""
    return sum(_BINOM[h[:, i].astype(np.int64) - 1, i + 1] for i in range(K))


@lru_cache(maxsize=1)
def _osszes_jellemzo() -> tuple[np.ndarray, np.ndarray]:
    osszes = osszes_kombinacio()
    return _rang(osszes), np.concatenate([jellemzok(osszes[i:i + 500_000]) for i in range(0, len(osszes), 500_000)])


def huzas_szorzok(modellek: dict[int, Modell], meredeksegek: dict[int, float]) -> dict[int, np.ndarray]:
    """Mind a 8 145 060 lehetséges húzásra a becsült nyeremény-szorzó szintenként
    (1 = átlagos húzás). A `meredeksegek` a mintán kívül mért kalibráció (< 1: a modell
    a jövőbeli eltéréseket kissé túlbecsüli, ezért visszahúzzuk)."""
    osszes = osszes_kombinacio()
    rang, jell = _osszes_jellemzo()
    ki = {}
    for szint, m in modellek.items():
        pont = m.szam.astype(np.float32)[osszes - 1].sum(1) + jell @ m.minta.astype(np.float32)
        f = np.exp(-meredeksegek[szint] * pont)
        tomb = np.empty(len(osszes), dtype=np.float32)
        tomb[rang] = f / f.mean()
        ki[szint] = tomb
    return ki


def kozelito_pontszam(modell: Modell, szelvenyek: np.ndarray) -> np.ndarray:
    """Gyors közelítés a kereséshez: a nyertesszám várható log-eltérése azokon a húzásokon,
    amelyek a szelvényt pontosan `modell.szint` számban találják el (a terjedelem nélkül).
    szelvenyek: (n × 6) -> (n,)"""
    m = modell.szint
    x = np.arange(1, N_SZAM + 1)
    kul = np.abs(x[:, None] - x[None, :])
    c = modell.minta
    P = (c[0] * (kul == 1) + c[1] * (kul == 2) + c[2] * (kul == 7)
         + c[3] * ((x[:, None] // 10 == x[None, :] // 10) & (kul > 0))
         + c[4] * ((x[:, None] % 10 == x[None, :] % 10) & (kul > 0)))
    tag = np.zeros((len(szelvenyek), N_SZAM))
    tag[np.arange(len(szelvenyek))[:, None], np.asarray(szelvenyek) - 1] = 1
    kint = 1 - tag
    n_kint = N_SZAM - K
    bb = np.einsum("ni,ij,nj->n", tag, P, tag) / 2
    bk = np.einsum("ni,ij,nj->n", tag, P, kint)
    kk = np.einsum("ni,ij,nj->n", kint, P, kint) / 2
    return (m / K * (tag @ modell.szam) + (K - m) / n_kint * (kint @ modell.szam)
            + m * (m - 1) / (K * (K - 1)) * bb + m / K * (K - m) / n_kint * bk
            + (K - m) * (K - m - 1) / (n_kint * (n_kint - 1)) * kk)


@lru_cache(maxsize=None)
def _reszhalmazok(n: int, k: int) -> np.ndarray:
    return np.array(list(combinations(range(n), k)), dtype=np.int16).reshape(-1, k)


def szelveny_szorzo(szelveny: tuple[int, ...], szorzok: dict[int, np.ndarray]) -> dict[int, float]:
    """A szelvény várható nyeremény-szorzója szintenként: átlag mindazon húzásokra,
    amelyek a szelvényt pontosan `szint` számban találják el."""
    sajat = np.array(sorted(szelveny), dtype=np.int16)
    tobbi = np.array([x for x in range(1, N_SZAM + 1) if x not in szelveny], dtype=np.int16)
    ki = {}
    for szint, f in szorzok.items():
        a = sajat[_reszhalmazok(K, szint)]
        b = tobbi[_reszhalmazok(len(tobbi), K - szint)]
        h = np.concatenate([np.repeat(a, len(b), axis=0), np.tile(b, (len(a), 1))], axis=1)
        h.sort(axis=1)
        ki[szint] = float(f[_rang(h)].mean())
    return ki


def szint_sulyok(df: pd.DataFrame, utolso: int = 104) -> dict[int, float]:
    """Egy szelvényre jutó átlagos nyeremény szintenként (Ft) az utolsó `utolso` húzáson.
    Az eladott szelvények száma a 3-as nyertesek számából: db_3 / P(pontosan 3 találat)."""
    d = _ervenyes(df).tail(utolso)
    n = d["db_3"].sum() / P_TALALAT[3]
    ki = {m: float((d[f"db_{m}"] * d[f"ft_{m}"]).sum() / n) for m in SZINTEK}
    ki[6] = float((d["db_6"].fillna(0) * d["ft_6"].fillna(0)).sum() / n)
    return ki


def szelveny_ertek(szelveny: tuple[int, ...], szorzok: dict[int, np.ndarray], sulyok: dict[int, float]) -> float:
    """Várható 3–5 találatos nyeremény szelvényenként (Ft)."""
    sz = szelveny_szorzo(szelveny, szorzok)
    return sum(sulyok[m] * sz[m] for m in szorzok)


# ---------------------------------------------------------------------------
# Tényleges eredmény, ha a múltban ezekkel a szelvényekkel játszottunk volna
# ---------------------------------------------------------------------------
def szelveny_visszateszt(df: pd.DataFrame, szelvenyek: list[tuple[int, ...]], tol_ev: int) -> dict:
    """A `tol_ev`-től kezdődő húzásokon: amikor valamelyik szelvényen 3 (4) találat volt,
    mekkora volt a tényleges nyeremény az adott negyedév átlagához képest."""
    d = _ervenyes(df)
    d = d[d["ev"] >= tol_ev]
    per = _periodus(d).to_numpy()
    m = szam_matrix(d)
    ki = {"huzasok": len(d)}
    for szint in (3, 4):
        ft = d[f"ft_{szint}"].where(d[f"ft_{szint}"] > 0)
        elt = (np.log(ft) - np.log(ft).groupby(per).transform("mean")).to_numpy()
        ertekek = []
        for s in szelvenyek:
            tal = m[:, np.array(s) - 1].sum(1)
            ertekek.extend(elt[(tal == szint) & ~np.isnan(elt)])
        e = np.array(ertekek)
        ki[szint] = {"esetek": len(e),
                     "szorzo": float(np.exp(e.mean())) if len(e) else np.nan,
                     "se": float(e.std(ddof=1) / np.sqrt(len(e))) if len(e) > 1 else np.nan}
    return ki


def fonyeremeny_idozites(df: pd.DataFrame) -> pd.DataFrame:
    """Hány húzás óta nincs telitalálat -> mennyi főnyeremény jutott egy szelvényre."""
    d = df[df["db_3"].notna()].copy()
    sorozat, s = [], 0
    for db in d["db_6"].fillna(0):
        sorozat.append(s)
        s = 0 if db > 0 else s + 1
    d["sorozat"] = sorozat
    d["n"] = d["db_3"] / P_TALALAT[3]
    d["fo"] = d["db_6"].fillna(0) * d["ft_6"].fillna(0)
    d = d[d["ev"] >= d["ev"].max() - 9]
    cs = pd.cut(d["sorozat"], [-1, 4, 9, 19, 1000], labels=["0–4", "5–9", "10–19", "20+"])
    g = d.groupby(cs, observed=True).agg(huzasok=("fo", "size"), telitalalat=("db_6", lambda x: int((x > 0).sum())),
                                         fo=("fo", "sum"), n=("n", "sum"))
    g["ft_szelvenyenkent"] = g["fo"] / g["n"]
    return g[["huzasok", "telitalalat", "ft_szelvenyenkent"]], int(sorozat[-1] + (0 if d["db_6"].iloc[-1] > 0 else 1))
