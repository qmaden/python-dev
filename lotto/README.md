# Hatoslottó: elemzés és szelvényajánlás

```bash
pip install -r requirements.txt
python futtat.py            # vagy: python futtat.py másik/hatos.csv
```

A szkript kiírja az eredményeket, és az `eredmenyek/` mappába menti a tisztított
adatot (`hatos_tiszta.csv`), a részletes jelentést (`jelentes.md`) és az ábrát (`abra.png`).

| Fájl | Feladat |
|---|---|
| `tisztitas.py` | beolvasás, tisztítás, érvényesség-ellenőrzés |
| `elemzes.py` | véletlenszerűségi tesztek, stratégiák visszatesztelése, népszerűségi modell |
| `szelvenyek.py` | a 4 szelvény kiválasztása, pontos esélyek (mind a 8 145 060 kombinációval) |
| `futtat.py` | az egész folyamat egyben + jelentés + ábra |

## Ötletek: mit lehet egyáltalán kezdeni a lottóadatokkal?

1. **Adattisztítás** – BOM, nincs fejléc, vegyes mezőszám (2007-ig pótszám), szöveges
   összegek („1 152 640 105 Ft”), hiányzó dátumok (2004 előtt), 1998 előtt a nyertesek
   száma 0 (ez hiányzó adat, nem valódi nulla), 1988–93 hiányos évek, 2025 szept. óta
   csütörtöki húzás is van (így az (év, hét) már nem egyedi), és egy hibás érték
   (1998/3: 0 telitalálat, mégis „1 Ft” nyeremény).
2. **Véletlenszerűségi tesztek** – számgyakoriság, számpárok, összeg, páros/páratlan,
   szomszédos számok, ismétlés az előző húzásból, kimaradási hossz. Mindet a *pontos*
   elméleti eloszláshoz hasonlítjuk (khi-négyzet, Monte-Carlo).
3. **Stratégiák visszatesztelése** – forró / hideg / „esedékes” számok: ha működnének,
   a múltban több találatot hoztak volna a várt 0,8-nál.
4. **Játékos-népszerűség** – az adatban benne van, hány nyertes volt az egyes
   kategóriákban. Mivel a nyereményalapot a nyertesek osztják el, abból, hogy egy szám
   kihúzásakor mennyivel több a 3-as nyertes, megbecsülhető, mennyire szeretik a
   játékosok az adott számot. A húzás véletlen, ezért ez gyakorlatilag egy randomizált
   kísérlet, tiszta becsléssel.
5. **Lefedés** – a 4 szelvény ne fedje át egymást, így nő az esély, hogy legalább egy nyer.

## Fő eredmények

- **A húzások tisztán véletlenek.** Egyik teszt sem mutat eltérést (minden p > 0,15),
  a forró/hideg/esedékes stratégiák pontosan a véletlen szintjén teljesítenek. A múltbeli
  húzásokból **nem** lehet megjósolni a következőt, és egyik 6-os kombináció sem
  valószínűbb a másiknál (mindegyik 1 : 8 145 060).
- **A játékosok viszont nem véletlenszerűen játszanak.** A 3, 7, 9, 13, 17 (szerencseszámok)
  kb. 10–13%-kal több nyertest „hoz”, az 1, 15, 36, 29, 35 és a legtöbb 32 feletti szám
  kevesebbet. Mintán kívüli teszten (2016 előtti adatból becsülve, a 2016–2026-os
  húzásokon ellenőrizve) a népszerűségi pontszám erősen előre jelzi a 3-as nyeremény
  összegét (Spearman r = −0,79): a legkevésbé népszerű negyedben átlagosan 16%-kal
  több volt a 3-as nyeremény, a legnépszerűbb negyedben 13%-kal kevesebb.

Vagyis **nyerési esélyt javítani nem lehet, a várható nyeremény nagyságát viszont igen**:
ha a kevésbé játszott számokra teszünk, nyerés esetén kevesebben osztoznak velünk.

## A 4 ajánlott szelvény

| # | Számok | Becsült 3-as nyeremény-szorzó |
|---|---|---|
| 1 | **2 – 29 – 32 – 35 – 36 – 45** | ×1,25 |
| 2 | **1 – 8 – 20 – 28 – 30 – 34** | ×1,25 |
| 3 | **14 – 16 – 38 – 40 – 43 – 44** | ×1,25 |
| 4 | **15 – 22 – 37 – 39 – 41 – 42** | ×1,24 |
| – | összehasonlításképp: 3 – 7 – 9 – 13 – 17 – 21 | ×0,66 |

Kiválasztás menete:
- a **24 legkevésbé népszerű** számot osztjuk el 4 **egymást nem fedő** szelvényre;
- kiszűrjük a tipikus emberi mintákat: 3 egymást követő szám, 1-nél több szomszédos pár,
  4+ hosszú számtani sor, 3+ azonos végződés, 4+ szám ugyanabból a tízesből, korábbi
  nyerőszámsor, 4+ egyezés az elmúlt 1 év bármelyik húzásával;
- a 4 szelvény népszerűsége kiegyensúlyozott (rögzített véletlenmaggal, reprodukálható).

Pontos esélyek a 4 szelvénnyel (a 8 145 060 lehetséges húzás végigszámolásával):

| | Esély |
|---|---|
| legalább egy 3+ találat | **9,50%** (4 független véletlen szelvény: 9,20%; 4 erősen átfedő: 5,25%) |
| legalább egy 4+ találat | 0,56% |
| legalább egy 5+ találat | ≈ 1 : 8 665 |
| telitalálat | 1 : 2 036 265 |

## Fontos

- Ez a nyerési esélyt **nem** növeli; a lottó várható értéke negatív (a befizetések kb.
  fele megy vissza nyereményként). Csak annyit érdemes rá költeni, amennyit szórakozásra
  szánnál.
- A „nyeremény-szorzó” a 3-as kategóriára becsült átlagos hatás; a magasabb kategóriákban
  (4-es, 5-ös, telitalálat) a népszerűség hatása a modell szerint még erősebb.
- Ha mindenki ugyanezt a módszert használná, az előny eltűnne. :)
