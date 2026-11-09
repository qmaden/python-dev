"""Húzási adatok letöltése a Szerencsejáték Zrt. oldaláról.

    python -m scriptek.letoltes                 # hatos.csv + luxor.csv frissítése
    python -m scriptek.letoltes --luxor-nyeremenyek   # + Luxor heti nyeremények (lassú)

A Luxor CSV csak a kihúzott számokat és a határszámokat tartalmazza, a nyertesek
számát és a nyereményeket nem. Ezeket a heti sorsolási oldalakból gyűjtjük ki
(2015-től érhetők el),
hetente egy kéréssel, kíméletes tempóban; a már letöltött heteket nem kéri újra.
"""

from __future__ import annotations

import argparse
import csv
import html
import re
import time
import urllib.request
from pathlib import Path

ADATOK = Path(__file__).resolve().parent.parent / "adatok"
CSV_URL = "https://bet.szerencsejatek.hu/cmsfiles/{jatek}.csv"
LUXOR_HET_URL = "https://bet.szerencsejatek.hu/mobil/jatekok/luxor/sorsolasok?year={ev}&week={het}"
USER_AGENT = "Mozilla/5.0 (lotto-elemzes; adatgyujtes heti egy keressel)"

LUXOR_KATEGORIAK = {
    "Jackpot": "jackpot",
    "Luxor": "luxor",
    "Első keret": "elso_keret",
    "Első kép": "elso_kep",
    "Összes keret": "keret",
    "Összes kép": "kep",
}
LUXOR_NYEREMENY_OSZLOPOK = ["ev", "het"] + [
    f"{elotag}_{k}" for k in LUXOR_KATEGORIAK.values() for elotag in ("hatar", "db", "ft")
]


def _get(url: str, timeout: float = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def letolt_csv(jatek: str, cel: Path | None = None) -> Path:
    """`hatos` vagy `luxor` teljes húzási CSV letöltése (a meglévő fájl felülírásával)."""
    cel = cel or ADATOK / f"{jatek}.csv"
    adat = _get(CSV_URL.format(jatek=jatek))
    cel.write_bytes(adat.replace(b"\r\n", b"\n"))
    return cel


_SOR = re.compile(
    r"<tr>\s*<td[^>]*>\s*([^<]+?)\s*</td>\s*<td>([^<]*)</td>\s*<td>([^<]*)</td>\s*<td>([^<]*)</td>\s*</tr>",
    re.S,
)


def _szam(s: str) -> int | None:
    s = html.unescape(s).replace("Ft", "").replace(" ", "").replace(" ", "").strip()
    return int(s) if s.lstrip("-").isdigit() else None


def luxor_het_nyeremenyei(ev: int, het: int) -> dict | None:
    """Egy hét nyereménytáblája: kategóriánként határszám, darabszám, nyeremény (Ft)."""
    oldal = _get(LUXOR_HET_URL.format(ev=ev, het=het)).decode("utf-8", "replace")
    # ellenőrzés: tényleg a kért hét jött-e vissza
    if not re.search(rf"{ev}\.\s*{het}\.\s*hét", oldal):
        return None
    sor = {"ev": ev, "het": het}
    for nev, hatar, db, ft in _SOR.findall(oldal):
        kulcs = LUXOR_KATEGORIAK.get(html.unescape(nev).strip())
        if kulcs:
            sor[f"hatar_{kulcs}"] = _szam(hatar)
            sor[f"db_{kulcs}"] = _szam(db)
            sor[f"ft_{kulcs}"] = _szam(ft)
    return sor if len(sor) > 2 else None


def luxor_nyeremenyek_frissitese(
    luxor_csv: Path = ADATOK / "luxor.csv",
    cel: Path = ADATOK / "luxor_nyeremenyek.csv",
    kesleltetes: float = 0.6,
    tol_ev: int = 2015,
) -> Path:
    """A heti nyereménytáblák az oldalon 2015-től érhetők el."""
    hetek = []
    for sor in luxor_csv.read_text(encoding="utf-8-sig").splitlines():
        if sor.strip():
            m = sor.split(";")
            if int(m[0]) >= tol_ev:
                hetek.append((int(m[0]), int(m[1])))
    meglevo: set[tuple[int, int]] = set()
    if cel.exists():
        with cel.open(encoding="utf-8") as f:
            meglevo = {(int(r["ev"]), int(r["het"])) for r in csv.DictReader(f)}
    hianyzo = [h for h in hetek if h not in meglevo]
    uj_fajl = not cel.exists()
    with cel.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LUXOR_NYEREMENY_OSZLOPOK)
        if uj_fajl:
            w.writeheader()
        for i, (ev, het) in enumerate(hianyzo, 1):
            for proba in range(4):
                try:
                    sor = luxor_het_nyeremenyei(ev, het)
                    break
                except Exception as hiba:  # hálózati hiba -> visszalépéses újrapróbálás
                    print(f"  {ev}/{het}: {hiba} – újrapróbálás")
                    time.sleep(2 ** (proba + 1))
            else:
                sor = None
            if sor:
                w.writerow(sor)
                f.flush()
            else:
                print(f"  {ev}/{het}: nincs nyereménytábla")
            if i % 50 == 0:
                print(f"  {i}/{len(hianyzo)} hét kész")
            time.sleep(kesleltetes)
    return cel


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--luxor-nyeremenyek", action="store_true", help="Luxor heti nyeremények letöltése is")
    ap.add_argument("--csak-nyeremenyek", action="store_true", help="a CSV-ket ne töltse le újra")
    a = ap.parse_args()
    if not a.csak_nyeremenyek:
        for j in ("hatos", "luxor"):
            print("letöltve:", letolt_csv(j))
    if a.luxor_nyeremenyek or a.csak_nyeremenyek:
        print("letöltve:", luxor_nyeremenyek_frissitese())
