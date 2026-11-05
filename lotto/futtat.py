"""Lottó-elemzések futtatása.

    python futtat.py                 # mindkét játék
    python futtat.py hatos           # csak Hatoslottó
    python futtat.py luxor           # csak Luxor
    python futtat.py mind --letolt   # előtte friss húzási adatok letöltése

Bemenet:  adatok/      (húzási eredmények)
Kimenet:  eredmenyek/  (tisztított adat, jelentés, ábra játékonként)
"""

from __future__ import annotations

import argparse

from scriptek import letoltes


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("jatek", nargs="?", default="mind", choices=["hatos", "luxor", "mind"])
    ap.add_argument("--letolt", action="store_true",
                    help="friss CSV-k (és Luxor heti nyeremények) letöltése a szerencsejatek.hu-ról")
    a = ap.parse_args()

    if a.letolt:
        for j in ("hatos", "luxor") if a.jatek == "mind" else (a.jatek,):
            print("letöltve:", letoltes.letolt_csv(j))
        if a.jatek in ("luxor", "mind"):
            print("frissítve:", letoltes.luxor_nyeremenyek_frissitese())

    if a.jatek in ("hatos", "mind"):
        from scriptek.hatos import jelentes as hatos

        hatos.main()
    if a.jatek in ("luxor", "mind"):
        from scriptek.luxor import jelentes as luxor

        luxor.main()


if __name__ == "__main__":
    main()
