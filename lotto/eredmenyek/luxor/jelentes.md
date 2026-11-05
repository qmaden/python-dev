# Luxor elemzés – eredmények

## 1. Adattisztítás

```
Húzások száma: 1310  (2001/39 – 2026/44)
Dátummal rendelkező sorok: 1148 (első: 2004-11-06)
Határszámok ismertek: 1164 húzás (2004/29-től)
Hiányos számsor: 2004/32 (39 szám a 43 helyett)
Kihúzott golyók száma a luxorig: 36–51 (átlag 43.9)
Jackpot-nyerések: 99
Szabálytól eltérő jackpot-határ: 2016/51, 2017/35, 2018/2, 2018/15
Nyereménytábla ismert: 611 húzás (2015/5-tól), az oldalon hiányzik: 2016/51, 2016/52, 2022/52
CSV és nyereménytábla határszámai egyeznek: 611 hét
```

## 2. A tábla szerkezete az adatokból

Melyik oszlopból jött az első képet / első keretet lezáró golyó:

- első kép: L:0 U:403 X:377 O:383 R:0 → a kép **csak az U, X, O oszlopból** áll (oszloponként 2 szám a játékos 4 számából)
- első keret: L:367 U:135 X:142 O:152 R:367 → a keretben az L és R oszlop mind a 4 száma benne van, az U, X, O-ból 2-2

Ezért a kép esélye: ∏_{U,X,O} C(h, 2) / C(4, 2), ahol h = az oszlopban kihúzott számaink száma; a keret ehhez még azt is megkívánja, hogy az L és R oszlop mind a 4 száma kint legyen.

## 3. Véletlenszerűségi tesztek (az első 36 golyón)

A sorsolás minden héten legalább 36 golyóig tart, ez a rész tehát független attól, hogy mikor jön ki a Luxor.

- **Számgyakoriság**: legritkább 68 (580×), leggyakoribb 9 (673×), várható 628.8× → p = 0.53
- **az első kihúzott golyó (1–75 egyenletes?)**: megfigyelt átlag 37.81, elméleti 38.00 → p = 0.084
- **oszloponkénti darabszám az első 36-ban**: megfigyelt átlag 7.20, elméleti 7.20 → p = 0.687
- **ismétlődés az előző hétből (első 36)**: megfigyelt átlag 17.22, elméleti 17.28 → p = 0.778
- **a szám értéke vs. hányadikként húzták**: megfigyelt átlag 37.86, elméleti 38.00 → p = 0.018

(Öt teszt mellett egy p ≈ 0,02 még belefér a véletlenbe; a sorrend amúgy sem számít a nyeréshez, csak az, hogy mely számok jönnek ki a luxorig.)

## 4. Stratégiák visszatesztelése

| stratégia                     |    hetek |   átlag találat az első 36-ban |   p (vs 9,6) |
|:------------------------------|---------:|-------------------------------:|-------------:|
| forró (utolsó 50 hét)         | 1260.000 |                          9.634 |        0.535 |
| hideg (utolsó 50 hét)         | 1260.000 |                          9.525 |        0.161 |
| esedékes (legrégebben húzott) | 1260.000 |                          9.583 |        0.741 |
| véletlen                      | 1260.000 |                          9.584 |        0.775 |
| ELMÉLET (bármely 20 szám)     |  nan     |                          9.600 |      nan     |

## 5. Függ-e a sorsolás és a nyeremény attól, mit játszanak a többiek?

- **Befejező szakasz** (a 36. golyó után még kijövő számok): a népszerű számoknak gyakrabban kellene bekerülniük, ha a megállás érezhetően függne tőlük → p = 0.72
- **A(z) első kép lezáró golyója** (oszlopon belül egyenletes-e): p = 0.69
- **A(z) első keret lezáró golyója** (oszlopon belül egyenletes-e): p = 0.10
- **A(z) luxor lezáró golyója** (oszlopon belül egyenletes-e): p = 0.23
- **Kép-nyertesek száma** (611 hét, 2015-től): számít-e, hogy az U, X, O oszlopon belül *melyik* számok jöttek ki? F-próba p = 0.12
- **Keret-nyertesek száma**: ugyanez mind az 5 oszlopra → p = 0.76

A számonkénti becslések szórása 1.4%, a puszta zajtól várható 1.2% (egy ±3%-os népszerűségi különbséget már ki tudnánk mutatni).

**Következtetés:** a Luxornál – a Hatoslottóval ellentétben – nem mutatható ki, hogy a játékosok egyes számokat érezhetően többen játszanának (valószínűleg sokan gépi tippel játszanak, és 20 szám mellett a kedvenc számok hatása elvész). Így a számválasztás **sem az esélyt, sem a nyeremény nagyságát** nem befolyásolja mérhetően. Ami számít: a 4 szelvény közti **lefedés**.

## 6. Ajánlott 4 szelvény

| # | L (1–15) | U (16–30) | X (31–45) | O (46–60) | R (61–75) |
|---|---|---|---|---|---|
| 1 | 1 5 6 13 | 18 24 25 27 | 31 35 36 44 | 47 52 53 60 | 61 64 67 68 |
| 2 | 3 9 12 13 | 19 21 28 29 | 33 34 38 39 | 51 55 57 59 | 61 70 71 75 |
| 3 | 8 11 14 15 | 17 20 23 29 | 37 41 43 45 | 46 49 50 58 | 62 63 66 73 |
| 4 | 2 4 7 10 | 16 22 26 30 | 32 40 42 45 | 48 54 56 60 | 65 69 72 74 |

Oszloponként mind a 15 számot felhasználjuk (16 helyre 15 szám, egy ismétlődik), így a 4 szelvény együtt lefedi mind a 75 számot.

Ha ezt a 4 szelvényt minden héten megjátszottuk volna (1309 hét, a gép véletlen elhelyezésére pontosan átlagolva):

| | ajánlott 4 szelvény | 4 független véletlen | 4 azonos szelvény |
|---|---|---|---|
| kép esélye szelvényenként / hét | **3.63%** | 3.59% | 3.59% |
| legalább 1 kép a 4-ből / hét | **13.87%** | 13.28% | 10.96% |
| legalább 1 keret a 4-ből / hét | **0.127%** | 0.110% | 0.086% |
| átlagos nyeremény szelvényenként / hét (2015-től, 300 Ft-os tétre) | **58 Ft** | 60 Ft | 61 Ft |

A szelvényenkénti esély és a várható nyeremény bármilyen számválasztásnál ugyanannyi (a különbségek a véletlen ingadozás részei); a lefedés azt növeli, hogy **legalább az egyik** szelvény nyerjen.

Átlagos nyeremények 2015-től (611 hét): kép 1 776 Ft (átl. 12 555 nyertes), keret 83 111 Ft (átl. 110 nyertes), első kép 399 693 Ft, Luxor 6 933 157 Ft. A 4 szelvény ára 1200 Ft / hét.
