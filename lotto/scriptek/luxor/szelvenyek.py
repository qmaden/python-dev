"""4 Luxor-szelvény összeállítása.

Minden szelvény oszloponként 4 számot tartalmaz (L 1–15, U 16–30, X 31–45,
O 46–60, R 61–75). A kép csak az U, X, O oszlopból áll (oszloponként 2 szám a 4-ből),
ezért a kép esélye azon múlik, hogy ezekben az oszlopokban hány számunkat húzzák ki.

Elv:
  * LEFEDÉS: 4 szelvény × 4 szám = 16 hely oszloponként, de csak 15 szám van ->
    oszloponként mind a 15 számot felhasználjuk, csak egy szerepel kétszer. Így a
    4 szelvény a lehető legkevésbé "fogad ugyanarra", és nő az esélye, hogy
    legalább az egyiken összejön a kép.
  * SORREND: ha a nyertesek számából mérhető a népszerűség, a számokat annak
    sorrendjében, kígyó-sorrendben (1,2,3,4,4,3,2,1,…) osztjuk ki, így minden szelvény
    hasonlóan népszerű. Ha nem mérhető (a jelenlegi adatokon ez a helyzet), akkor a
    számválasztás sem az esélyt, sem a nyereményt nem befolyásolja, ezért rögzített
    véletlenmaggal kevert sorrendet használunk (reprodukálható); óvatosságból
    egy szelvényre sem jut oszlopon belül 3 egymást követő szám.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .tisztitas import JATEKOS_DB_OSZLOPONKENT, OSZLOPOK


def _oszlop_kiosztasa(sorrend: list[int], n_szelveny: int, eltolas: int) -> list[list[int]]:
    """Egy oszlop 15 számának kiosztása kígyó-sorrendben 4×4 helyre (egy szám kétszer)."""
    helyek = []
    for kor in range(JATEKOS_DB_OSZLOPONKENT):
        k = list(range(n_szelveny))
        helyek += k if kor % 2 == 0 else k[::-1]
    helyek = [(h + eltolas) % n_szelveny for h in helyek]
    osztas: list[list[int]] = [[] for _ in range(n_szelveny)]
    kiosztando = list(sorrend)
    for h in helyek:
        # a következő szám, amelyik még nincs a szelvényen (a 16. helyre ismétlés kell)
        if not kiosztando:
            kiosztando = [x for x in sorrend if x not in osztas[h]]
        x = next(x for x in kiosztando if x not in osztas[h])
        kiosztando.remove(x)
        osztas[h].append(x)
    return osztas


def _van_szamsor(szamok: list[int]) -> bool:
    s = sorted(szamok)
    return any(s[i] + 1 == s[i + 1] and s[i + 1] + 1 == s[i + 2] for i in range(len(s) - 2))


def szelvenyek_osszeallitasa(
    nepszeruseg: pd.Series | None = None, n_szelveny: int = 4, seed: int = 2026
) -> list[tuple[int, ...]]:
    rng = np.random.default_rng(seed)
    szelvenyek: list[list[int]] = [[] for _ in range(n_szelveny)]
    for j in range(len(OSZLOPOK)):
        szamok = list(range(15 * j + 1, 15 * j + 16))
        # oszloponként eltoljuk a kígyó kezdőpontját, hogy ne mindig ugyanaz a szelvény kapja az első számot
        eltolas = j % n_szelveny
        if nepszeruseg is not None:
            osztas = _oszlop_kiosztasa(sorted(szamok, key=lambda x: (nepszeruseg.get(x, 0.0), x)), n_szelveny, eltolas)
        else:
            # kevert sorrend; óvatosságból újrakeverünk, ha egy szelvényre 3 egymást követő szám jutna
            while True:
                osztas = _oszlop_kiosztasa([int(x) for x in rng.permutation(szamok)], n_szelveny, eltolas)
                if not any(_van_szamsor(o) for o in osztas):
                    break
        for h in range(n_szelveny):
            szelvenyek[h] += osztas[h]
    return [tuple(sorted(s)) for s in szelvenyek]


def szelveny_tablazat(sz: tuple[int, ...]) -> str:
    """'L: 1 5 9 12 | U: …' formátum."""
    a = np.array(sz)
    return " | ".join(f"{OSZLOPOK[j]}: " + " ".join(f"{x:2d}" for x in a[(a - 1) // 15 == j]) for j in range(5))


def osszehasonlito_keszletek(rng: np.random.Generator, n: int = 4) -> dict[str, list[list[tuple[int, ...]]]]:
    """Összehasonlításhoz: 4 azonos szelvény, illetve 4 egymástól független véletlen szelvény."""

    def veletlen():
        return tuple(sorted(int(x) for j in range(5) for x in rng.choice(np.arange(15 * j + 1, 15 * j + 16), 4, replace=False)))

    return {
        "4 azonos szelvény": [[veletlen()] * n for _ in range(300)],
        "4 független véletlen szelvény": [[veletlen() for _ in range(n)] for _ in range(300)],
    }
