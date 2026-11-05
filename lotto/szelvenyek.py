"""4 szelvény összeállítása és pontos valószínűség-számítás.

Mivel minden 6-os kombináció pontosan ugyanakkora eséllyel jön ki (1 : 8 145 060),
két dolgon lehet javítani:

  1. LEFEDÉS: a 4 szelvény ne fedje át egymást (24 különböző szám). Így a
     szelvények nem "ugyanarra fogadnak", és nő az esélye, hogy legalább egy nyer.
  2. NYEREMÉNY NAGYSÁGA: a nyereményalapot a nyertesek osztják el, ezért a
     kevesek által játszott számokkal ugyanakkora esély mellett nagyobb a
     várható nyeremény. Ehhez a népszerűségi modellt (elemzes.py) használjuk,
     plusz kerüljük a tipikus emberi mintákat (sorozatok, számtani sorok,
     korábbi nyerőszámok).
"""

from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats

from elemzes import K, N_SZAM, osszes_kombinacio
from tisztitas import SZAM_OSZLOPOK


# ---------------------------------------------------------------------------
# Mintázat-szűrők (az emberek által gyakran választott alakzatok kerülése)
# ---------------------------------------------------------------------------
def _leghosszabb_szamtani_sor(sz: tuple[int, ...]) -> int:
    s, halmaz, best = sorted(sz), set(sz), 2
    for a, b in combinations(s, 2):
        d, n, x = b - a, 2, b
        while x + d in halmaz:
            x += d
            n += 1
        best = max(best, n)
    return best


def mintazat_hibak(sz: tuple[int, ...], multbeli: set[tuple[int, ...]], friss: np.ndarray) -> list[str]:
    s = sorted(sz)
    hibak = []
    kul = np.diff(s)
    if any(kul[i] == 1 and kul[i + 1] == 1 for i in range(len(kul) - 1)):
        hibak.append("3 egymást követő szám")
    if (kul == 1).sum() > 1:
        hibak.append("1-nél több szomszédos pár")
    if _leghosszabb_szamtani_sor(sz) >= 4:
        hibak.append("4+ hosszú számtani sor")
    if max(np.bincount(np.array(s) % 10)) >= 3:
        hibak.append("3+ azonos végződés")
    if max(np.bincount(np.array(s) // 10)) >= 4:
        hibak.append("4+ ugyanabból a tízesből")
    if tuple(s) in multbeli:
        hibak.append("korábbi nyerőszámsor")
    if len(friss) and (np.isin(friss, s).sum(1) >= 4).any():
        hibak.append("4+ egyezés az elmúlt 1 év valamelyik húzásával")
    return hibak


# ---------------------------------------------------------------------------
# Szelvények kiválasztása
# ---------------------------------------------------------------------------
def szelvenyek_osszeallitasa(
    df: pd.DataFrame,
    nepszeruseg: pd.Series,
    n_szelveny: int = 4,
    n_proba: int = 200_000,
    seed: int = 2026,
) -> list[tuple[int, ...]]:
    """24 legkevésbé népszerű szám szétosztása 4 egymást nem fedő szelvényre úgy,
    hogy mindegyik átmenjen a mintázat-szűrőn, és a szelvények népszerűsége
    kiegyensúlyozott legyen. Ha nincs érvényes felosztás, a következő
    legkevésbé népszerű számmal cserél."""
    multbeli = {tuple(r) for r in df[SZAM_OSZLOPOK].to_numpy()}
    friss = df[SZAM_OSZLOPOK].to_numpy()[-104:]
    sorrend = nepszeruseg.sort_values().index.to_list()
    rng = np.random.default_rng(seed)
    nep = nepszeruseg.to_dict()

    for extra in range(0, N_SZAM - n_szelveny * K + 1):
        # a "határon" lévő számok közül cserélgetünk, ha kell
        jeloltek = sorrend[: n_szelveny * K + extra]
        legjobb, legjobb_ertek = None, np.inf
        for _ in range(n_proba // (extra + 1)):
            valasztott = rng.choice(jeloltek, n_szelveny * K, replace=False) if extra else rng.permutation(jeloltek)
            sz = [tuple(sorted(int(x) for x in valasztott[i * K:(i + 1) * K])) for i in range(n_szelveny)]
            if any(mintazat_hibak(s, multbeli, friss) for s in sz):
                continue
            pont = [sum(nep[x] for x in s) for s in sz]
            ertek = sum(pont) + 0.5 * (max(pont) - min(pont))  # alacsony + kiegyensúlyozott
            if ertek < legjobb_ertek:
                legjobb, legjobb_ertek = sz, ertek
        if legjobb is not None:
            return sorted(legjobb, key=lambda s: sum(nep[x] for x in s))
    raise RuntimeError("Nem található érvényes szelvénykészlet")


# ---------------------------------------------------------------------------
# Pontos valószínűségek (mind a 8 145 060 lehetséges húzás végigszámolásával)
# ---------------------------------------------------------------------------
def pontos_eselyek(szelvenyek: list[tuple[int, ...]]) -> dict:
    osszes = osszes_kombinacio()
    talalat = np.empty((len(osszes), len(szelvenyek)), dtype=np.int8)
    for j, s in enumerate(szelvenyek):
        tag = np.zeros(N_SZAM + 1, dtype=np.int8)
        tag[list(s)] = 1
        talalat[:, j] = tag[osszes].sum(1)
    legjobb = talalat.max(1)
    n = len(osszes)
    egy = {k: stats.hypergeom.sf(k - 1, N_SZAM, K, K) for k in (3, 4, 5, 6)}
    return {
        "legalabb_egy_3+": (legjobb >= 3).sum() / n,
        "legalabb_egy_4+": (legjobb >= 4).sum() / n,
        "legalabb_egy_5+": (legjobb >= 5).sum() / n,
        "telitalalat": (legjobb == 6).sum() / n,
        "fuggetlen_4_veletlen_3+": 1 - (1 - egy[3]) ** len(szelvenyek),
        "egy_szelveny_3+": egy[3],
        "egy_szelveny_6": egy[6],
    }


def atfedo_pelda_eselye(n_szelveny: int = 4) -> float:
    """Összehasonlításképp: 4 szelvény, amelyek 5 számban egyeznek
    (pl. valaki a "kedvenc" számaihoz mindig egy mást ír)."""
    alap = (1, 2, 3, 4, 5)
    sz = [alap + (6 + i,) for i in range(n_szelveny)]
    return pontos_eselyek(sz)["legalabb_egy_3+"]
