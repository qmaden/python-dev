"""Statisztikai elemzések a Luxor húzásaira.

A Luxor egy fontos ponton különbözik a Hatoslottótól: a sorsolás addig tart,
amíg *valamelyik játékos* szelvényén össze nem jön a Luxor. A megállás tehát
függ attól, hogy a játékosok milyen számokat játszanak meg. Ezért:

  * az első 36 golyó (ennyi minden héten kijön) tisztán véletlen minta ->
    ezen végezzük a véletlenszerűségi teszteket;
  * az első képet / első keretet lezáró golyó viszont elárulja, mely számokat
    játsszák sokan (amikor sok szelvényen ugyanaz a szám hiányzik, nagyobb az esély,
    hogy épp az zárja le) -> népszerűségi index;
  * a tábla szerkezete: a Kép csak az U, X, O oszlopból áll (oszloponként 2 szám
    a játékos 4 számából, a gép választja ki véletlenszerűen), a Keret az L és R
    oszlop mind a 4 számából + az U, X, O másik 2-2 számából áll.
  * 2015-től a nyertesek száma is ismert -> a népszerűség a kép-nyertesek
    számából is becsülhető, és ellenőrizhető, hogy a két becslés egyezik-e.
"""

from __future__ import annotations

from math import comb

import numpy as np
import pandas as pd
from scipy import stats

from ..kozos import khi2_illeszkedes, veletlen_reszhalmazok
from .tisztitas import JATEKOS_DB, N_SZAM, huzott_matrix, oszlop, pozicio_matrix

ELSO_N = 36  # ennyi golyót minden héten kihúznak -> torzítatlan minta


# ---------------------------------------------------------------------------
# 1. Véletlenszerűségi tesztek az első 36 golyón
# ---------------------------------------------------------------------------
def gyakorisag_teszt(df: pd.DataFrame, n_szim: int = 4000, seed: int = 11) -> dict:
    m = huzott_matrix(df, ELSO_N)
    db = m.sum(0)
    vart = len(df) * ELSO_N / N_SZAM
    stat = ((db - vart) ** 2 / vart).sum()
    rng = np.random.default_rng(seed)
    szim = np.empty(n_szim)
    for i in range(n_szim):
        h = veletlen_reszhalmazok(len(df), N_SZAM, ELSO_N, rng)
        c = np.bincount(h.ravel(), minlength=N_SZAM + 1)[1:]
        szim[i] = ((c - vart) ** 2 / vart).sum()
    return {
        "huzasok": len(df),
        "vart_db": vart,
        "min": (int(db.argmin()) + 1, int(db.min())),
        "max": (int(db.argmax()) + 1, int(db.max())),
        "p": float((szim >= stat).mean()),
    }


def eloszlas_tesztek(df: pd.DataFrame) -> pd.DataFrame:
    sor = []
    m = huzott_matrix(df, ELSO_N)

    # első golyó egyenletes-e 1..75-ön
    elso = np.array([sz[0] for sz in df["huzott"]])
    o = np.bincount(elso, minlength=N_SZAM + 1)[1:].astype(float)
    r = khi2_illeszkedes(o, np.full(N_SZAM, 1 / N_SZAM))
    sor.append({"leiras": "az első kihúzott golyó (1–75 egyenletes?)", "megfigyelt_atlag": elso.mean(),
                "elmeleti_atlag": 38.0, "p_ertek": r.pvalue})

    # oszlopok: az első 36-ból hány esik az L oszlopba (hipergeometrikus 75/15/36), mind az 5 oszlopra összesítve
    osz = np.stack([m[:, j * 15:(j + 1) * 15].sum(1) for j in range(5)], axis=1)
    k = np.arange(16)
    p = stats.hypergeom.pmf(k, N_SZAM, 15, ELSO_N)
    o = sum(np.bincount(osz[:, j], minlength=16) for j in range(5)).astype(float)
    r = khi2_illeszkedes(o, p)
    sor.append({"leiras": "oszloponkénti darabszám az első 36-ban", "megfigyelt_atlag": osz.mean(),
                "elmeleti_atlag": ELSO_N / 5, "p_ertek": r.pvalue})

    # ismétlődés: az előző hét első 36 számából hány jön ki újra az első 36-ban
    ism = (m[1:] & m[:-1]).sum(1)
    k = np.arange(ELSO_N + 1)
    p = stats.hypergeom.pmf(k, N_SZAM, ELSO_N, ELSO_N)
    r = khi2_illeszkedes(np.bincount(ism, minlength=ELSO_N + 1).astype(float), p)
    sor.append({"leiras": "ismétlődés az előző hétből (első 36)", "megfigyelt_atlag": ism.mean(),
                "elmeleti_atlag": ELSO_N * ELSO_N / N_SZAM, "p_ertek": r.pvalue})

    # sorrend: a golyó értéke független-e attól, hányadikként húzták
    poz = np.array([sz[:ELSO_N] for sz in df["huzott"]])
    r = stats.kruskal(*[poz[:, j] for j in range(ELSO_N)])
    sor.append({"leiras": "a szám értéke vs. hányadikként húzták", "megfigyelt_atlag": poz.mean(),
                "elmeleti_atlag": 38.0, "p_ertek": r.pvalue})
    return pd.DataFrame(sor)


def strategia_backtest(df: pd.DataFrame, ablak: int = 50, seed: int = 12) -> pd.DataFrame:
    """20 szám (oszloponként 4) a múltbeli első-36 gyakoriságok alapján; mérjük a
    találatokat a következő hét első 36 golyójában. Elmélet: 20*36/75 = 9,6."""
    m = huzott_matrix(df, ELSO_N)
    rng = np.random.default_rng(seed)
    osz = oszlop(np.arange(1, N_SZAM + 1))

    def oszloponkent(pont):
        return np.concatenate([np.flatnonzero(osz == j)[np.argsort(pont[osz == j])[:4]] for j in range(5)])

    eredm = {"forró (utolsó 50 hét)": [], "hideg (utolsó 50 hét)": [], "esedékes (legrégebben húzott)": [],
             "véletlen": []}
    utolso = np.full(N_SZAM, -1.0)
    for t in range(len(df)):
        if t >= ablak:
            gy = m[t - ablak:t].sum(0) + rng.random(N_SZAM) * 1e-3
            v = {
                "forró (utolsó 50 hét)": oszloponkent(-gy),
                "hideg (utolsó 50 hét)": oszloponkent(gy),
                "esedékes (legrégebben húzott)": oszloponkent(utolso + rng.random(N_SZAM) * 1e-3),
                "véletlen": oszloponkent(rng.random(N_SZAM)),
            }
            for nev, sz in v.items():
                eredm[nev].append(m[t, sz].sum())
        utolso[m[t] == 1] = t
    sor = []
    for nev, t in eredm.items():
        t = np.array(t)
        sor.append({"stratégia": nev, "hetek": len(t), "átlag találat az első 36-ban": t.mean(),
                    "p (vs 9,6)": stats.ttest_1samp(t, JATEKOS_DB * ELSO_N / N_SZAM).pvalue})
    sor.append({"stratégia": "ELMÉLET (bármely 20 szám)", "hetek": np.nan,
                "átlag találat az első 36-ban": JATEKOS_DB * ELSO_N / N_SZAM, "p (vs 9,6)": np.nan})
    return pd.DataFrame(sor)


# ---------------------------------------------------------------------------
# 2. A megállási szabály nyoma: népszerűség a húzási sorrendből
# ---------------------------------------------------------------------------
def befejezo_szakasz(df: pd.DataFrame, maszk: np.ndarray | None = None) -> pd.DataFrame:
    """A 36. golyó után még kint lévő 39 szám közül melyek jönnek ki a luxorig?

    Ha a megállás független lenne a játékosoktól, a maradék számok mindegyike
    ugyanakkora eséllyel (|befejező szakasz| / 39) kerülne be. A népszerű számok
    viszont gyakrabban kerülnek be, mert a sorsolás addig megy, amíg egy
    (jellemzően népszerű számokból álló) szelvény be nem telik."""
    d = df[df["teljes_sorozat"]] if maszk is None else df[df["teljes_sorozat"] & maszk]
    elso = huzott_matrix(d, ELSO_N).astype(bool)
    osszes = huzott_matrix(d).astype(bool)
    maradek = ~elso
    befejezo = osszes & ~elso
    arany = befejezo.sum(1, keepdims=True) / maradek.sum(1, keepdims=True)
    megf = befejezo.sum(0)
    vart = (maradek * arany).sum(0)
    return pd.DataFrame({"megfigyelt": megf, "vart": vart, "arany": megf / vart}, index=range(1, N_SZAM + 1))


def befejezo_szakasz_teszt(df: pd.DataFrame, n_szim: int = 2000, seed: int = 13) -> dict:
    """Permutációs teszt: hetente véletlenszerűen választjuk ki a befejező szakaszt a maradékból."""
    d = df[df["teljes_sorozat"]]
    t = befejezo_szakasz(df)
    stat = ((t.megfigyelt - t.vart) ** 2 / t.vart).sum()
    elso = huzott_matrix(d, ELSO_N).astype(bool)
    n_bef = d["n_huzott"].to_numpy() - ELSO_N
    rng = np.random.default_rng(seed)
    szim = np.empty(n_szim)
    for s in range(n_szim):
        r = rng.random(elso.shape)
        r[elso] = 2.0  # az első 36 nem választható
        rang = r.argsort(1).argsort(1)
        bef = rang < n_bef[:, None]
        c = bef.sum(0)
        szim[s] = ((c - t.vart.to_numpy()) ** 2 / t.vart.to_numpy()).sum()
    return {"khi2": stat, "p": float((szim >= stat).mean()), "szim_atlag": szim.mean()}


def lezaro_golyok(df: pd.DataFrame, maszk: np.ndarray | None = None) -> pd.DataFrame:
    """Melyik szám "zárta le" az első képet, az első keretet és a luxort?
    Ha minden számot egyformán játszanának, egy oszlopon belül mindegyik szám
    ugyanakkora eséllyel lenne a záró golyó."""
    d = df[df["elso_kep"].notna() & df["teljes_sorozat"]]
    if maszk is not None:
        d = d[maszk[d.index]]
    ki = {}
    for kat in ("elso_kep", "elso_keret", "luxor"):
        golyo = [sz[int(p) - 1] for sz, p in zip(d["huzott"], d[kat])]
        ki[kat] = np.bincount(golyo, minlength=N_SZAM + 1)[1:]
    t = pd.DataFrame(ki, index=range(1, N_SZAM + 1))
    # azonos népszerűség mellett egy oszlopon belül mindegyik szám egyforma eséllyel zár
    # (az oszlopok között nem: a képet csak U, X, O oszlopbeli szám zárhatja le)
    osz = oszlop(t.index.to_numpy())
    for kat in ki:
        t[f"vart_{kat}"] = t[kat].groupby(osz).transform("mean")
    t["osszes"] = t[list(ki)].sum(1)
    t["vart"] = t[[f"vart_{k}" for k in ki]].sum(1)
    return t


def lezaro_golyok_teszt(df: pd.DataFrame) -> pd.DataFrame:
    t = lezaro_golyok(df)
    sor = []
    osz = oszlop(t.index.to_numpy())
    for kat in ("elso_kep", "elso_keret", "luxor"):
        o = t[kat].to_numpy().astype(float)
        e = t[f"vart_{kat}"].to_numpy()
        hasznalt = e > 0
        stat = ((o[hasznalt] - e[hasznalt]) ** 2 / e[hasznalt]).sum()
        df_ = hasznalt.sum() - len(np.unique(osz[hasznalt]))  # oszloponként 1 szabadsági fok elvész
        oszl = " ".join(f"{'LUXOR'[j]}:{int(o[osz == j].sum())}" for j in range(5))
        sor.append({"kategória": kat, "események": int(o.sum()), "oszloponként": oszl,
                    "khi2": stat, "szabadsági fok": int(df_), "p": stats.chi2.sf(stat, df_)})
    return pd.DataFrame(sor)


def nepszeruseg_sorrendbol(df: pd.DataFrame, maszk: np.ndarray | None = None) -> pd.Series:
    """Népszerűségi index a húzási sorrendből (csak a CSV kell hozzá): hányszor
    zárta le a szám az első képet / első keretet a várthoz képest (log-arány).
    A luxort lezáró golyó és a befejező szakasz nem hordoz mérhető jelet, ezért kimarad."""
    z = lezaro_golyok(df, maszk)
    megf = z["elso_kep"] + z["elso_keret"]
    vart = z["vart_elso_kep"] + z["vart_elso_keret"]
    idx = np.log((megf + 2) / (vart + 2))
    return (idx - idx.mean()).rename("nepszeruseg_sorrend")


# ---------------------------------------------------------------------------
# 3. Népszerűség a kép-nyertesek számából (2015-től)
# ---------------------------------------------------------------------------
def nepszeruseg_kep_modell(df: pd.DataFrame, maszk: np.ndarray | None = None) -> pd.Series:
    """log(kép-nyertesek) = év-hatás (~ eladott szelvények) + hossz-hatás (hány golyót húztak)
                            + Σ_{kihúzott számok} népszerűség_i
    A húzás véletlen, így ez lényegében randomizált kísérlet."""
    sel = df["db_kep"].notna() & (df["db_kep"] > 0) & df["teljes_sorozat"]
    if maszk is not None:
        sel &= maszk
    d = df[sel]
    y = np.log(d["db_kep"].to_numpy())
    X_ev = pd.get_dummies(d["ev"].astype(str), dtype=float).to_numpy()
    X_hossz = pd.get_dummies(d["n_huzott"].clip(39, 49).astype(str), dtype=float).to_numpy()[:, 1:]
    X_szam = huzott_matrix(d).astype(float)
    # a kihúzott számok száma = n_huzott, ami a hossz-dummykban már benne van -> 1 szám elhagyva, majd centrálás
    X = np.hstack([X_ev, X_hossz, X_szam[:, :-1]])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    nep = np.append(beta[-(N_SZAM - 1):], 0.0)
    return pd.Series(nep - nep.mean(), index=range(1, N_SZAM + 1), name="nepszeruseg_kep")


# ---------------------------------------------------------------------------
# 4. Szelvények értékelése a múltbeli húzásokon (pontos várható érték)
# ---------------------------------------------------------------------------
_PAR_P = np.array([comb(h, 2) / comb(4, 2) for h in range(5)])  # 2 adott szám a 4-ből mind kint van


def oszlop_talalatok(huzott: np.ndarray, szelvenyek: list[tuple[int, ...]]) -> np.ndarray:
    """(húzások × szelvények × 5): oszloponként a szelvény 4 számából hány van kint."""
    osz = oszlop(np.arange(1, N_SZAM + 1))
    tag = np.zeros((N_SZAM, len(szelvenyek), 5), dtype=np.int16)
    for j, s in enumerate(szelvenyek):
        s = np.array(s)
        tag[s - 1, j, osz[s - 1]] = 1
    return np.einsum("dn,ntc->dtc", huzott.astype(np.int16), tag)


def esely_kep_keret(h: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Oszloponkénti találatokból (…×5) a kép / keret / luxor esélye, a gép véletlen
    elhelyezésére átlagolva. U, X, O oszlopban a 4 számból 2 kerül a képbe, 2 a keretbe;
    L és R mind a 4 száma a keretben van."""
    uxo = _PAR_P[h[..., 1]] * _PAR_P[h[..., 2]] * _PAR_P[h[..., 3]]
    lr = (h[..., 0] == 4) & (h[..., 4] == 4)
    luxor = (h == 4).all(-1)
    return uxo, uxo * lr, luxor.astype(float)


def szelveny_ertekeles(df: pd.DataFrame, szelvenyek: list[tuple[int, ...]]) -> dict:
    """Ha az adott szelvényeket minden héten megjátszottuk volna: pontosan mekkora
    eséllyel lett volna kép / keret, és (ahol a nyeremény ismert) mennyit nyertünk
    volna átlagosan. Az első kép / első keret nyereményt is beszámítjuk: ehhez a
    szelvény számainak a lezáró golyóig kint kell lenniük."""
    d = df[df["teljes_sorozat"]]
    h = oszlop_talalatok(huzott_matrix(d), szelvenyek)
    p_kep, p_keret, p_luxor = esely_kep_keret(h)
    ki = {
        "hetek": len(d),
        "atl_talalat": h.sum(-1).mean(),
        "p_kep_szelvenyenkent": p_kep.mean(),
        "p_keret_szelvenyenkent": p_keret.mean(),
        "p_legalabb_egy_kep": (1 - np.prod(1 - p_kep, axis=1)).mean(),
        "p_legalabb_egy_keret": (1 - np.prod(1 - p_keret, axis=1)).mean(),
    }
    if "ft_kep" in d:
        van = d["ft_kep"].notna().to_numpy()
        if van.any():
            dv = d[van]
            poz = pozicio_matrix(dv)
            elso_kep = (poz > 0) & (poz <= dv["elso_kep"].to_numpy()[:, None])
            elso_keret = (poz > 0) & (poz <= dv["elso_keret"].to_numpy()[:, None])
            p_ek, _, _ = esely_kep_keret(oszlop_talalatok(elso_kep, szelvenyek))
            _, p_er, _ = esely_kep_keret(oszlop_talalatok(elso_keret, szelvenyek))

            def ft(oszl):
                return dv[oszl].fillna(0).to_numpy()[:, None]

            nyer = (p_kep[van] * ft("ft_kep") + p_keret[van] * ft("ft_keret")
                    + p_ek * ft("ft_elso_kep") + p_er * ft("ft_elso_keret")
                    + p_luxor[van] * (ft("ft_luxor") + ft("ft_jackpot")))
            ki["nyeremeny_hetek"] = int(van.sum())
            ki["atl_nyeremeny_ft_szelvenyenkent"] = nyer.mean()
            ki["atl_kep_ft_szelvenyenkent"] = (p_kep[van] * ft("ft_kep")).mean()
    return ki


def strategia_osszehasonlitas(df: pd.DataFrame, hatar_ev: int = 2021, n_veletlen: int = 2000,
                              seed: int = 14) -> pd.DataFrame:
    """Mintán kívüli összehasonlítás: a hatar_ev előtti húzásokból becsült
    népszerűség alapján választunk számokat, és a hatar_ev utáni heteken mérjük."""
    tanito = (df["ev"] < hatar_ev).to_numpy()
    teszt = df[~tanito]
    nep = nepszeruseg_sorrendbol(df, tanito)
    osz = oszlop(np.arange(1, N_SZAM + 1))
    rng = np.random.default_rng(seed)

    def oszloponkent(pont: np.ndarray, honnan: int = 0) -> tuple[int, ...]:
        return tuple(sorted(int(x) + 1 for j in range(5)
                            for x in np.flatnonzero(osz == j)[np.argsort(pont[osz == j])[honnan:honnan + 4]]))

    p = nep.to_numpy()
    szabalyok = {
        "legnépszerűbb 4 / oszlop": [oszloponkent(-p)],
        "legkevésbé népszerű 4 / oszlop": [oszloponkent(p)],
        "véletlen szelvények (átlag)": [oszloponkent(rng.random(N_SZAM)) for _ in range(n_veletlen)],
    }
    sor = []
    for nev, sz in szabalyok.items():
        e = szelveny_ertekeles(teszt, sz)
        sor.append({
            "szabály": nev,
            "átl. kihúzott a 20-ból": e["atl_talalat"],
            "kép esély / hét": e["p_kep_szelvenyenkent"],
            "keret esély / hét": e["p_keret_szelvenyenkent"],
            "átl. nyeremény (Ft) / hét": e.get("atl_nyeremeny_ft_szelvenyenkent", np.nan),
        })
    return pd.DataFrame(sor)


# ---------------------------------------------------------------------------
# 5. Van-e egyáltalán mérhető népszerűségi különbség a kép-nyertesek számában?
# ---------------------------------------------------------------------------
def _nyertes_design(d: pd.DataFrame, oszlopok: tuple[int, ...], egyedi: bool) -> np.ndarray:
    X_ev = pd.get_dummies(d["ev"].astype(str), dtype=float).to_numpy()
    X_hossz = pd.get_dummies(d["n_huzott"].clip(39, 49).astype(str), dtype=float).to_numpy()[:, 1:]
    m = huzott_matrix(d).astype(float)
    osz = oszlop(np.arange(1, N_SZAM + 1))
    # oszloponként hány szám jött ki (a hossz mellett ez is számít)
    X_osz = np.stack([m[:, osz == j].sum(1) for j in oszlopok], axis=1)
    reszek = [X_ev, X_hossz, X_osz]
    if egyedi:
        # számonkénti hatás; oszloponként egyet elhagyunk (az oszlopösszeg már benne van)
        reszek.append(np.hstack([m[:, (osz == j)][:, 1:] for j in oszlopok]))
    return np.hstack(reszek)


KATEGORIA_OSZLOPOK = {"kep": (1, 2, 3), "keret": (0, 1, 2, 3, 4)}


def nepszeruseg_nyertes_teszt(df: pd.DataFrame, kategoria: str = "kep") -> dict:
    """Beágyazott modellek F-próbája: ad-e hozzá a nyertesek számának magyarázatához,
    hogy egy oszlopon belül *melyik* számokat húzták, azon túl, hogy hányat?
    Ha a játékosok egyes számokat jóval többen játszanának, igen kellene legyen.
    (Kép: csak az U, X, O oszlop számít; keret: mind az 5.)"""
    oszlopok = KATEGORIA_OSZLOPOK[kategoria]
    d = df[df[f"db_{kategoria}"].notna() & (df[f"db_{kategoria}"] > 0) & df["teljes_sorozat"]]
    y = np.log(d[f"db_{kategoria}"].to_numpy())
    eredm = {}
    for nev, egyedi in (("szukitett", False), ("teljes", True)):
        X = _nyertes_design(d, oszlopok, egyedi)
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        r = y - X @ beta
        eredm[nev] = (r @ r, np.linalg.matrix_rank(X), beta)
    (rss0, k0, _), (rss1, k1, beta1) = eredm["szukitett"], eredm["teljes"]
    n = len(y)
    F = ((rss0 - rss1) / (k1 - k0)) / (rss1 / (n - k1))
    return {
        "kategoria": kategoria,
        "hetek": n,
        "F": F,
        "df": (int(k1 - k0), int(n - k1)),
        "p": float(stats.f.sf(F, k1 - k0, n - k1)),
        "rezidualis_szoras": float(np.sqrt(rss1 / (n - k1))),
    }


def nepszeruseg_nyertes_becsles(df: pd.DataFrame, kategoria: str = "kep") -> pd.DataFrame:
    """Számonkénti hatás a nyertesek számára (log-skála, oszlopon belül 0 átlagra
    centrálva) standard hibával. Pozitív = ha kihúzzák, több a nyertes (népszerű szám)."""
    oszlopok = KATEGORIA_OSZLOPOK[kategoria]
    d = df[df[f"db_{kategoria}"].notna() & (df[f"db_{kategoria}"] > 0) & df["teljes_sorozat"]]
    y = np.log(d[f"db_{kategoria}"].to_numpy())
    X = _nyertes_design(d, oszlopok, True)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ beta
    s2 = r @ r / (len(y) - np.linalg.matrix_rank(X))
    cov = s2 * np.linalg.pinv(X.T @ X)
    n_egyedi = 14 * len(oszlopok)
    b, C = beta[-n_egyedi:], cov[-n_egyedi:, -n_egyedi:]
    # 14 együttható/oszlop -> 15 szám (az első 0), majd oszlopon belüli centrálás
    M = np.zeros((15 * len(oszlopok), n_egyedi))
    for k in range(len(oszlopok)):
        M[15 * k + 1:15 * k + 15, 14 * k:14 * k + 14] = np.eye(14)
    Kc = np.kron(np.eye(len(oszlopok)), np.eye(15) - np.ones((15, 15)) / 15)
    T = Kc @ M
    ertek, se = T @ b, np.sqrt(np.diag(T @ C @ T.T))
    idx = [x for j in oszlopok for x in range(15 * j + 1, 15 * j + 16)]
    return pd.DataFrame({"hatas": ertek, "se": se}, index=idx)
