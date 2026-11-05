"""Közös segédfüggvények és útvonalak mindkét játékhoz."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import stats

GYOKER = Path(__file__).resolve().parent.parent
ADATOK = GYOKER / "adatok"
EREDMENYEK = GYOKER / "eredmenyek"

# ábrák színei (világos felület)
SZINEK = {
    "felulet": "#fcfcfb",
    "szoveg": "#0b0b0b",
    "szoveg2": "#52514e",
    "racs": "#e4e3df",
    "kek": "#2a78d6",
    "piros": "#e34948",
    "semleges": "#9a9993",
}


def khi2_illeszkedes(megfigyelt: np.ndarray, elmeleti_p: np.ndarray, min_vart: float = 5.0):
    """Khi-négyzet illeszkedésvizsgálat, a kis várható értékű cellákat összevonva."""
    n = megfigyelt.sum()
    vart = elmeleti_p * n
    o, e, acc_o, acc_e = [], [], 0.0, 0.0
    for oi, ei in zip(megfigyelt, vart):
        acc_o += oi
        acc_e += ei
        if acc_e >= min_vart:
            o.append(acc_o)
            e.append(acc_e)
            acc_o = acc_e = 0.0
    if acc_e > 0:
        o[-1] += acc_o
        e[-1] += acc_e
    o, e = np.array(o), np.array(e)
    e *= o.sum() / e.sum()
    return stats.chisquare(o, e)


def veletlen_reszhalmazok(n: int, n_szam: int, k: int, rng: np.random.Generator) -> np.ndarray:
    """n darab véletlen k-elemű részhalmaz 1..n_szam-ból (soronként rendezve)."""
    return np.sort(rng.random((n, n_szam)).argsort(axis=1)[:, :k] + 1, axis=1)


def abra_stilus(ax) -> None:
    ax.set_facecolor(SZINEK["felulet"])
    ax.tick_params(length=0)
    ax.grid(axis="y", color=SZINEK["racs"], lw=0.8, zorder=0)
    for sp in ax.spines.values():
        sp.set_visible(False)


def abra_cim(ax, cim: str, alcim: str) -> None:
    ax.set_title(cim, loc="left", fontsize=12, fontweight="bold", pad=20)
    ax.text(0, 1.02, alcim, transform=ax.transAxes, fontsize=9, color=SZINEK["szoveg2"], va="bottom")
