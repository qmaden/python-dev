# Hatoslottó elemzés – eredmények

## 1. Adattisztítás

```
Húzások száma: 1860  (1988–2026)
Dátummal rendelkező sorok: 1208 (első: 2004-11-07)
Nyertes-darabszám ismert: 1565 húzás (1998-tól)
Pótszámos húzások: 794 (–2007)
Csütörtöki húzások: 61 (első: 2025-09-04)
Hiányos évek (<50 húzás): 1988:2, 1989:8, 1990:12, 1991:12, 1992:24, 1993:29
```

## 2. Véletlenszerűségi tesztek

Ha a húzásokban lenne kihasználható mintázat, ezek közül valamelyik kimutatná (p < 0,05).

- **Számgyakoriság (teljes időszak)**: legritkább 31 (216×), leggyakoribb 41 (268×), várható 248.0× → p = 0.75
- **Számgyakoriság (utolsó 104 húzás)**: legritkább 45 (6×), leggyakoribb 34 (23×), várható 13.9× → p = 0.44
- **Számpárok**: leggyakoribb pár 32–41 (46×, várható 28.2×), a párok szórása → p = 0.60
- **6 szám összege (elmélet: 138)**: megfigyelt átlag 138.87, elméleti 138.00 → p = 0.33
- **páratlan számok darabszáma**: megfigyelt átlag 3.01, elméleti 3.07 → p = 0.31
- **egymást követő számpárok (pl. 12-13)**: megfigyelt átlag 0.67, elméleti 0.67 → p = 0.60
- **1–31 közötti számok darabszáma**: megfigyelt átlag 4.08, elméleti 4.13 → p = 0.16
- **hány szám ismétlődik az előző húzásból**: megfigyelt átlag 0.80, elméleti 0.80 → p = 0.85
- **két megjelenés közti húzások száma (geometriai eloszlás)**: megfigyelt átlag 7.47, elméleti 7.50 → p = 0.41

**Következtetés:** minden teszt a tiszta véletlennel konzisztens.

## 3. Stratégiák visszatesztelése

Minden húzás előtt csak a múltbeli adatok alapján választunk 6 számot.

| strategia                      |   huzasok |   atlag_talalat |   3+_talalat_arany_% |   p_ertek_vs_0.8 |
|:-------------------------------|----------:|----------------:|---------------------:|-----------------:|
| forro (utolso 50 leggyakoribb) |  1810.000 |           0.810 |                2.155 |            0.587 |
| hideg (utolso 50 legritkabb)   |  1810.000 |           0.759 |                2.044 |            0.024 |
| esedekes (legregebben huzott)  |  1810.000 |           0.780 |                2.210 |            0.272 |
| veletlen                       |  1810.000 |           0.833 |                2.928 |            0.085 |
| ELMELET (barmely 6 szam)       |   nan     |           0.800 |                2.383 |          nan     |

(4 stratégia tesztelése mellett egy p ≈ 0,02 még bőven a véletlen ingadozás része; a „véletlen” sor mutatja, mekkora a zaj.)

## 4. Játékos-népszerűség (nyertesek számából)

- Konzisztencia: 3-as vs 4-es modell r = 0.995, 3-as vs 5-ös r = 0.975
- Mintán kívüli teszt (2016 előtti becslés → 625 későbbi húzás): Spearman r = -0.79 a népszerűségi pontszám és a 3-as nyeremény között (p = 1.6e-136); kalibrált meredekség = -0.71
- 3-as nyeremény a mintán kívüli húzásokon, népszerűségi negyedenként (átlaghoz képest):
  - legkevésbé népszerű: ×1.16
  - 2.: ×1.04
  - 3.: ×0.95
  - legnépszerűbb: ×0.87
- Legkevésbé játszott: 36 (-13%), 15 (-11%), 1 (-10%), 29 (-8%), 35 (-8%), 40 (-7%), 38 (-7%), 22 (-6%)
- Legnépszerűbb: 9 (+13%), 7 (+12%), 13 (+10%), 3 (+10%), 17 (+8%), 11 (+7%), 19 (+7%), 24 (+6%)
- 1–31 átlag: +1.8%, 32–45 átlag: -3.9%

## 5. Ajánlott 4 szelvény

| # | Számok | Népszerűségi pontszám | Becsült 3-as nyeremény-szorzó |
|---|---|---|---|
| 1 | 2 – 29 – 32 – 35 – 36 – 45 | -0.313 | ×1.25 |
| 2 | 1 – 8 – 20 – 28 – 30 – 34 | -0.309 | ×1.25 |
| 3 | 14 – 16 – 38 – 40 – 43 – 44 | -0.307 | ×1.25 |
| 4 | 15 – 22 – 37 – 39 – 41 – 42 | -0.306 | ×1.24 |
| – | összehasonlítás: „szerencseszámok” 3 – 7 – 9 – 13 – 17 – 21 | +0.576 | ×0.66 |

Pontos esélyek (mind a 8 145 060 lehetséges húzás végigszámolásával):

- Legalább egy szelvényen 3+ találat: **9.50%** (4 független véletlen szelvény: 9.20%, 4 erősen átfedő szelvény: 5.25%)
- Legalább egy 4+ találat: 0.557%
- Legalább egy 5+ találat: 0.0115% (≈ 1 : 8,665)
- Telitalálat: 1 : 2,036,265
