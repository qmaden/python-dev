# Lottó-elemzések: Hatoslottó és Luxor

A szerencsejatek.hu nyilvános húzási adataiból: adattisztítás, véletlenszerűségi
tesztek, stratégiák visszatesztelése, a játékosok számválasztásának becslése, és ez
alapján 4-4 ajánlott szelvény.

```bash
pip install -r requirements.txt
python futtat.py                 # mindkét játék (a Hatoslottó kb. 1 perc)
python futtat.py luxor           # csak az egyik
python futtat.py mind --letolt   # előtte friss adatok letöltése
python -m pytest                 # ellenőrzések
```

## Mappaszerkezet

```
lotto/
├── futtat.py                  belépési pont (hatos | luxor | mind, --letolt)
├── adatok/                    húzási eredmények (nyers, ahogy letöltöttük)
│   ├── hatos.csv              Hatoslottó 1988–
│   ├── luxor.csv              Luxor 2001– (kihúzott számok sorrendben + határszámok)
│   └── luxor_nyeremenyek.csv  Luxor heti nyertesszámok és nyeremények 2015–
├── scriptek/
│   ├── letoltes.py            CSV-k és Luxor nyereménytáblák letöltése
│   ├── kozos.py               útvonalak, statisztikai és ábra-segédfüggvények
│   ├── hatos/                 tisztitas.py · elemzes.py · mintazat.py · szelvenyek.py · jelentes.py
│   └── luxor/                 tisztitas.py · elemzes.py · megterules.py · szelvenyek.py · jelentes.py
├── eredmenyek/
│   ├── hatos/                 hatos_tiszta.csv · jelentes.md · abra.png
│   └── luxor/                 luxor_tiszta.csv · jelentes.md · abra.png
└── tesztek/test_lotto.py      tisztítás, képletek, szelvény-szabályok ellenőrzése
```

Minden szám és teszt részletesen: [`eredmenyek/hatos/jelentes.md`](eredmenyek/hatos/jelentes.md),
[`eredmenyek/luxor/jelentes.md`](eredmenyek/luxor/jelentes.md).

---

## Hatoslottó (6/45)

**Adattisztítás:** UTF-8 BOM, nincs fejléc, vegyes mezőszám (2007-ig pótszám), szöveges
összegek („1 152 640 105 Ft”), 2004 előtt nincs dátum, 1998 előtt a nyertesek száma 0
(ez hiányzó adat, nem valódi nulla), 1988–93 hiányos évek, 2025 szept. óta csütörtöki
húzás is van (az (év, hét) már nem egyedi), egy hibás érték (1998/3: 0 telitalálat, de „1 Ft”).

**Eredmények:**
- A húzások tisztán véletlenek: gyakoriság, párok, összeg, páros/páratlan, szomszédos
  számok, ismétlődés, kimaradás – minden p > 0,15. A forró/hideg/esedékes számok
  visszatesztelve pontosan a véletlen szintjén teljesítenek.
- **A játékosok viszont nem véletlenül választanak.** A 3-as nyertesek számából becsülve
  a 9, 7, 13, 3, 17 kb. 10–13%-kal népszerűbb, az 1, 15, 36, 29, 35 és a legtöbb 32 feletti
  szám kevésbé. Mintán kívüli teszten (2016 előtti adatból becsülve, 2016–2026-on mérve)
  ez erősen előre jelzi a 3-as nyeremény összegét (r = −0,79): a legkevésbé népszerű
  negyedben 16%-kal több, a legnépszerűbbben 13%-kal kevesebb volt a nyeremény.
- Vagyis: **az esélyen nem lehet javítani, a nyeremény nagyságán igen.**

**Utólagos ellenőrzés (2026. november)** – részletek a jelentés 5–8. pontjában:
- A korábbi számok reprodukálhatók, a véletlenszerűségi tesztek és a 9,50%-os lefedési esély helyesek.
- **Hiba volt a „nyeremény-szorzóban”:** a közölt ×1,23–1,26 azt az esetet írta le, amikor a szelvény
  mind a 6 számát kihúzzák. 3 találatnál a húzás másik 3 száma nem a miénk, így a valódi szorzó kb. ×1,1.
  Most minden szelvényre pontosan számoljuk (átlag az összes olyan húzásra, amelyik pontosan 3/4/5
  számát találja el).
- **Új: mintázat-hatás.** A játékosok kerülik a szomszédos számokat: ha a húzásban van szomszédos pár,
  6%-kal kevesebb a 3-as, 15%-kal a 4-es, 24%-kal az 5-ös nyertes (kisebb hatás a 2-vel és 7-tel eltérő
  pároknál is). A korábbi szűrő épp tiltotta a szomszédos párokat. A bővített modell mintán kívül a
  nyertesszám ingadozásának 63 / 68 / 51%-át jelzi előre (3-as / 4-es / 5-ös) a korábbi 53 / 45 / 27% helyett.
- **Új: időbeli súlyozás.** A népszerűség lassan változik (2012 előtt/után r = 0,93), ezért a friss
  húzások nagyobb súlyt kapnak.
- **Próba a múlton:** csak 2019 előtti adatból választott szelvényekkel 2019–2026 között a tényleges
  3-as nyeremény ×1,12 volt az átlaghoz képest (36 eset), a „szerencseszámokkal” ×0,83.

**4 szelvény** – egymást nem fedik, együttes várható 3–5 találatos nyereményük a legnagyobb
(megkötés: nincs 3 egymást követő szám, legfeljebb 2 szomszédos pár, nincs számtani sor, nem korábbi nyerőszámsor):

| # | Számok | 3-as szorzó | 4-es | 5-ös | várható 3–5 találatos nyeremény |
|---|---|---|---|---|---|
| 1 | **1 – 28 – 29 – 35 – 36 – 43** | ×1,19 | ×1,57 | ×2,50 | 135 Ft |
| 2 | **14 – 15 – 20 – 22 – 39 – 40** | ×1,14 | ×1,38 | ×1,68 | 119 Ft |
| 3 | **2 – 30 – 31 – 34 – 37 – 38** | ×1,08 | ×1,30 | ×1,87 | 116 Ft |
| 4 | **8 – 16 – 41 – 42 – 44 – 45** | ×1,03 | ×1,11 | ×1,43 | 104 Ft |
| – | véletlen számok | ×1,00 | ×1,00 | ×1,00 | 96 Ft |
| – | korábbi 4 szelvény (átlag) | ×1,10 | ×1,24 | ×1,45 | 111 Ft |
| – | 3 – 7 – 9 – 13 – 17 – 21 | ×0,82 | ×0,62 | ×0,42 | 71 Ft |

Legalább egy 3+ találat esélye a 4 szelvénnyel **9,50%** (4 független véletlen
szelvény: 9,20%; 4 erősen átfedő: 5,25%), telitalálat 1 : 2 036 265. A 4-es és főleg az 5-ös szorzók
modellbecslések, közvetlenül nem mérhetők vissza (túl ritka esemény).

Az utolsó 104 húzáson egy szelvényre átlagosan kb. 186 Ft nyeremény jutott (ennek fele a ritka
telitalálat). A főnyeremény-rész a halmozódással nő: 0–4 telitalálat nélküli húzás után 27 Ft,
10–19 után 143 Ft szelvényenként.

---

## Luxor (75 szám, oszloponként 4)

**A játék:** oszloponként (L 1–15, U 16–30, X 31–45, O 46–60, R 61–75) 4 számot jelölünk,
a gép véletlenszerűen rakja őket egy 5×5-ös táblára. **Kép** = belső 3×3 (6 szám),
**Keret** = külső gyűrű (14 szám), **Luxor** = mind a 20. A sorsolás addig tart, amíg
valakinek össze nem jön a Luxor (36–51 golyó).

**Adattisztítás:** BOM, CRLF, változó hosszú számsorok, 2001–2004/28 a határszámok 0-k
(hiányzó adat), 2004/32 hiányos számsor (39 szám 43 helyett), 4 szabálytól eltérő
jackpot-határ (valószínűleg akciós hetek). A CSV-ben nincs nyeremény, ezért a heti
nyereménytáblákat külön letöltjük (`scriptek/letoltes.py`; 2015/5-től érhetők el, 611 hét,
3 hétnek nincs oldala), és a két forrás határszámait egymással is ellenőrizzük (mind a 611
hét egyezik; jackpot-nyerésnél az oldal a határ helyett a tényleges golyószámot mutatja).

**Eredmények:**
- **A tábla szerkezete az adatokból:** az első képet lezáró golyó mindig az U, X vagy O
  oszlopból jön → a kép oszloponként 2 számból áll ebből a 3 oszlopból; a keretben az
  L és R mind a 4 száma + U, X, O 2-2 száma van. Ebből pontos képlet adódik a kép és a
  keret esélyére.
- A húzás tisztán véletlen (az első 36 golyón, ami minden héten kijön); forró/hideg/
  esedékes stratégiák itt sem működnek.
- **Népszerűségi hatás itt nem mutatható ki:** sem a húzási sorrendből (befejező szakasz
  p = 0,72; lezáró golyók p = 0,69 / 0,10 / 0,23), sem a kép- és keret-nyertesek számából
  (611 hét, F-próba p = 0,12 és 0,76; egy kb. ±3%-os különbséget már kimutatnánk).
  Valószínűleg sokan gépi tippel
  játszanak, és 20 szám mellett a kedvenc számok hatása elvész. Ezért a Luxornál a
  számválasztás sem az esélyt, sem a nyeremény nagyságát nem befolyásolja mérhetően.
- **Ami számít: a lefedés.** A 4 szelvény együtt mind a 75 számot lefedi (oszloponként
  16 helyre 15 szám).

**Utólagos ellenőrzés (2026. november)** – a jelentés 2. és 7. pontja:
- **A tábla-képlet független próbája:** a kép-nyertesekből visszaszámolt szelvényszámmal a képlet
  68 023 keret-nyertest jósol 2015 óta, a tényleges 67 237 (99%); az első kép 8 306 vs. 8 355.
- **Javítás:** a korábbi „kb. 60 Ft nyeremény szelvényenként” alulbecslés volt, mert a ritka nyeremények
  (luxor, jackpot, első kép/keret) egyetlen szelvény múltjából nem mérhetők. Az összes kifizetésből
  számolva az utolsó 52 héten **144 Ft** jutott egy szelvényre (kép 73, luxor 34, jackpot 16, keret 12 Ft).
- **Új: időzítés.** A megtérülés a jackpot-határtól függ: 32–38-as határnál kb. 129 Ft, 42–43-nál 169 Ft,
  44 felett 254 Ft jut egy szelvényre (ekkor a jackpotot a hetek 55%-ában elvitték). Az ár alatt marad
  mindig, de alkalmi játékhoz a magas határú hetek a jobbak.
- A 4 szelvény és a lefedési számok változatlanok.

**4 szelvény:**

| # | L (1–15) | U (16–30) | X (31–45) | O (46–60) | R (61–75) |
|---|---|---|---|---|---|
| 1 | 1 5 6 13 | 18 24 25 27 | 31 35 36 44 | 47 52 53 60 | 61 64 67 68 |
| 2 | 3 9 12 13 | 19 21 28 29 | 33 34 38 39 | 51 55 57 59 | 61 70 71 75 |
| 3 | 8 11 14 15 | 17 20 23 29 | 37 41 43 45 | 46 49 50 58 | 62 63 66 73 |
| 4 | 2 4 7 10 | 16 22 26 30 | 32 40 42 45 | 48 54 56 60 | 65 69 72 74 |

Ha ezt minden héten megjátszottuk volna (1310 hét, a gép véletlen elhelyezésére pontosan átlagolva):

| | ajánlott | 4 független véletlen | 4 azonos |
|---|---|---|---|
| kép esélye szelvényenként | 3,63% | 3,59% | 3,59% |
| legalább 1 kép a 4-ből | **13,9%** | 13,3% | 11,0% |
| legalább 1 keret a 4-ből | **0,13%** | 0,11% | 0,09% |

---

## Fontos

- Egyik módszer sem növeli a főnyeremény esélyét; a lottó várható értéke negatív
  (a befizetések kb. fele megy vissza nyereményként, bármilyen számokkal). Csak annyit
  érdemes rá költeni, amennyit szórakozásra szánnál.
- Ha mindenki ugyanezt a módszert használná, a Hatoslottós előny eltűnne. :)
