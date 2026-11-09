# Hatoslottó elemzés – eredmények

## 1. Adattisztítás

```
Húzások száma: 1863  (1988–2026)
Dátummal rendelkező sorok: 1211 (első: 2004-11-07)
Nyertes-darabszám ismert: 1568 húzás (1998-tól)
Pótszámos húzások: 794 (–2007)
Csütörtöki húzások: 62 (első: 2025-09-04)
Hiányos évek (<50 húzás): 1988:2, 1989:8, 1990:12, 1991:12, 1992:24, 1993:29
```

## 2. Véletlenszerűségi tesztek

Ha a húzásokban lenne kihasználható mintázat, ezek közül valamelyik kimutatná (p < 0,05).

- **Számgyakoriság (teljes időszak)**: legritkább 31 (217×), leggyakoribb 41 (268×), várható 248.4× → p = 0.78
- **Számgyakoriság (utolsó 104 húzás)**: legritkább 45 (6×), leggyakoribb 34 (23×), várható 13.9× → p = 0.50
- **Számpárok**: leggyakoribb pár 32–41 (46×, várható 28.2×), a párok szórása → p = 0.63
- **6 szám összege (elmélet: 138)**: megfigyelt átlag 138.86, elméleti 138.00 → p = 0.34
- **páratlan számok darabszáma**: megfigyelt átlag 3.01, elméleti 3.07 → p = 0.33
- **egymást követő számpárok (pl. 12-13)**: megfigyelt átlag 0.67, elméleti 0.67 → p = 0.58
- **1–31 közötti számok darabszáma**: megfigyelt átlag 4.08, elméleti 4.13 → p = 0.17
- **hány szám ismétlődik az előző húzásból**: megfigyelt átlag 0.80, elméleti 0.80 → p = 0.85
- **két megjelenés közti húzások száma (geometriai eloszlás)**: megfigyelt átlag 7.47, elméleti 7.50 → p = 0.44

**Következtetés:** minden teszt a tiszta véletlennel konzisztens.

## 3. Stratégiák visszatesztelése

Minden húzás előtt csak a múltbeli adatok alapján választunk 6 számot.

| strategia                      |   huzasok |   atlag_talalat |   3+_talalat_arany_% |   p_ertek_vs_0.8 |
|:-------------------------------|----------:|----------------:|---------------------:|-----------------:|
| forro (utolso 50 leggyakoribb) |  1813.000 |           0.809 |                2.151 |            0.616 |
| hideg (utolso 50 legritkabb)   |  1813.000 |           0.760 |                2.041 |            0.025 |
| esedekes (legregebben huzott)  |  1813.000 |           0.780 |                2.206 |            0.280 |
| veletlen                       |  1813.000 |           0.832 |                2.923 |            0.093 |
| ELMELET (barmely 6 szam)       |   nan     |           0.800 |                2.383 |          nan     |

(4 stratégia tesztelése mellett egy p ≈ 0,02 még bőven a véletlen ingadozás része; a „véletlen” sor mutatja, mekkora a zaj.)

## 4. Játékos-népszerűség számonként (nyertesek számából)

- Konzisztencia: 3-as vs 4-es modell r = 0.995, 3-as vs 5-ös r = 0.975
- Mintán kívüli teszt (2016 előtti becslés → 628 későbbi húzás): Spearman r = -0.79 a népszerűségi pontszám és a 3-as nyeremény között (p = 3.2e-133); kalibrált meredekség = -0.71
- 3-as nyeremény a mintán kívüli húzásokon, népszerűségi negyedenként (átlaghoz képest):
  - legkevésbé népszerű: ×1.16
  - 2.: ×1.04
  - 3.: ×0.96
  - legnépszerűbb: ×0.87
- Legkevésbé játszott: 36 (-13%), 15 (-11%), 1 (-10%), 29 (-8%), 35 (-8%), 40 (-7%), 38 (-7%), 22 (-6%)
- Legnépszerűbb: 9 (+13%), 7 (+12%), 13 (+11%), 3 (+10%), 17 (+8%), 11 (+7%), 19 (+7%), 24 (+6%)
- 1–31 átlag: +1.8%, 32–45 átlag: -3.9%

## 5. Ellenőrzés és bővített modell

**a) Mintázat-hatás.** A nyertesek száma nemcsak attól függ, *mely* számokat húzzák ki, hanem attól is, hogyan helyezkednek el egymáshoz képest. Hatás a nyertesek számára (± standard hiba):

| mintázat a kihúzott számok között | 3-as | 4-es | 5-ös |
|---|---|---|---|
| szomszédos számpár (különbség 1) | -6.4% (±0.5) | -14.7% (±0.6) | -24.4% (±1.3) |
| 2-vel eltérő számpár | -2.6% (±0.5) | -5.4% (±0.6) | -6.5% (±1.3) |
| 7-tel eltérő számpár | -2.9% (±0.4) | -6.6% (±0.6) | -9.8% (±1.3) |
| azonos tízesbe eső számpár | -0.6% (±0.3) | -2.0% (±0.4) | -4.2% (±0.8) |
| azonos végződésű számpár | +0.1% (±0.3) | +1.1% (±0.4) | +3.1% (±0.9) |
| terjedelem (legnagyobb − legkisebb, tízesekben) | -2.7% (±0.7) | -7.6% (±1.0) | -15.7% (±2.1) |

A játékosok tehát **kerülik a szomszédos számokat**: ha a húzásban van ilyen pár, érezhetően kevesebb a nyertes. (A korábbi szelvény-szűrő épp fordítva, a szomszédos párokat tiltotta.)

**b) Mintán kívüli ellenőrzés** – minden évre csak a korábbi évekből becsülve (2008-tól, 1046 húzás): a nyertesszám ingadozásának mekkora részét jelzi előre a modell.

| | 3-as | 4-es | 5-ös |
|---|---|---|---|
| csak számonkénti népszerűség (eredeti modell) | 53% | 45% | 27% |
| + mintázat, + friss adatok nagyobb súlya | **63%** | **68%** | **51%** |
| kalibráció (1 = pontos; <1 = a modell túloz) | 0.83 | 0.86 | 0.81 |

A szelvények szorzóit a kalibrációval visszahúzva számoljuk.

**c) Időbeli stabilitás.** A 2012 előtti és utáni becslés korrelációja r = 0.93: a sorrend nagyjából állandó, de lassan változik (legtöbbet nőtt: 45 (+6%), 40 (+6%), 43 (+5%); csökkent: 21 (-6%), 9 (-6%), 5 (-4%)). Ezért a friss húzások nagyobb súlyt kapnak (felezési idő 8 év).

**d) A korábbi „nyeremény-szorzó” túlbecslés volt.** A 4. pont pontszáma azt mutatja, mi történik, ha a szelvény *mind a 6* számát kihúzzák. 3 találatnál viszont a húzás másik 3 száma nem a miénk, így a tényleges szorzó kisebb. A helyes érték: átlag mindazon húzásokra, amelyek a szelvényt pontosan 3 (4, 5) számban találják el. A korábbi 4 szelvényre így:

| # | Számok | 3-as | 4-es | 5-ös | várható 3–5 találatos nyeremény / szelvény |
|---|---|---|---|---|---|
| 1 | 15 – 16 – 28 – 38 – 43 – 45 | ×1.09 | ×1.20 | ×1.36 | 109 Ft |
| 2 | 2 – 8 – 29 – 30 – 35 – 37 | ×1.10 | ×1.27 | ×1.61 | 114 Ft |
| 3 | 1 – 20 – 39 – 40 – 42 – 44 | ×1.11 | ×1.29 | ×1.50 | 113 Ft |
| 4 | 14 – 22 – 32 – 34 – 36 – 41 | ×1.09 | ×1.21 | ×1.33 | 108 Ft |

(Véletlen számokkal: ×1,00 és 96 Ft. A korábban közölt ×1,23–1,26 helyett a 3-as szorzó valójában kb. ×1,1.)

## 6. Ajánlott 4 szelvény

4 egymást nem fedő szelvény, amelyek együttes várható 3–5 találatos nyereménye a legnagyobb (megkötés: nincs 3 egymást követő szám, legfeljebb 2 szomszédos pár, nincs 4 hosszú számtani sor, nem korábbi nyerőszámsor – ezeken túl a modellnek nincs tapasztalata).

| # | Számok | 3-as | 4-es | 5-ös | várható 3–5 találatos nyeremény / szelvény |
|---|---|---|---|---|---|
| 1 | 1 – 28 – 29 – 35 – 36 – 43 | ×1.19 | ×1.57 | ×2.50 | 135 Ft |
| 2 | 14 – 15 – 20 – 22 – 39 – 40 | ×1.14 | ×1.38 | ×1.68 | 119 Ft |
| 3 | 2 – 30 – 31 – 34 – 37 – 38 | ×1.08 | ×1.30 | ×1.87 | 116 Ft |
| 4 | 8 – 16 – 41 – 42 – 44 – 45 | ×1.03 | ×1.11 | ×1.43 | 104 Ft |

| # | Számok | 3-as | 4-es | 5-ös | várható 3–5 találatos nyeremény / szelvény |
|---|---|---|---|---|---|
| „szerencseszámok” | 3 – 7 – 9 – 13 – 17 – 21 | ×0.82 | ×0.62 | ×0.42 | 71 Ft |

Szelvényenként átlagosan 119 Ft várható 3–5 találatos nyeremény (korábbi szelvények: 111 Ft, véletlen számok: 96 Ft). Az 5-ös szorzók a legbizonytalanabbak (kevés adat).

Pontos esélyek (mind a 8 145 060 lehetséges húzás végigszámolásával) – ezek a számválasztástól nem, csak attól függnek, hogy a 4 szelvény nem fedi egymást:

- Legalább egy szelvényen 3+ találat: **9.50%** (4 független véletlen szelvény: 9.20%, 4 erősen átfedő szelvény: 5.25%)
- Legalább egy 4+ találat: 0.557%
- Legalább egy 5+ találat: 0.0115% (≈ 1 : 8,665)
- Telitalálat: 1 : 2,036,265

## 7. Próba a múlton: mi lett volna 2019-től?

A szelvényeket csak a 2019 előtti adatokból állítjuk össze, majd megnézzük a 2019–2026 közötti húzásokat: amikor a szelvényen pontosan 3 találat volt, mekkora volt a tényleges nyeremény az adott negyedév átlagához képest.

| szelvények | húzások | 3 találatos esetek | tényleges 3-as nyeremény az átlaghoz képest |
|---|---|---|---|
| bővített módszer (4 szelvény) | 472 | 36 | ×1.12 (±0.02) |
| eredeti módszer (4 szelvény) | 472 | 40 | ×1.11 (±0.02) |
| „szerencseszámok” 3-7-9-13-17-21 | 472 | 9 | ×0.83 (±0.02) |
| 200 véletlen szelvény | 472 | 2159 | ×1.01 (±0.00) |

A kevéssé népszerű számokkal tehát a valóságban is kb. 10%-kal nagyobb volt a 3-as nyeremény, a népszerű számokkal jóval kisebb. A két módszer közti különbség a 3-asoknál kicsi, és ennyi esetből nem mérhető; a bővített módszer előnye főleg a 4-es és 5-ös találatnál várható, amiből túl kevés van a közvetlen méréshez. A találatok *száma* a számválasztástól nem függ.

## 8. Megtérülés és időzítés

Az utolsó 104 húzáson egy szelvényre átlagosan 186 Ft nyeremény jutott: 3-as 70 Ft, 4-es 13 Ft, 5-ös 13 Ft, telitalálat 90 Ft (ez utóbbi szinte mind ritka, nagy nyeremény). A főnyeremény halmozódik, ezért a megtérülés attól függ, mióta nincs telitalálat (utolsó 10 év):

| húzások telitalálat nélkül | húzások | telitalálatos húzás | főnyeremény Ft / szelvény |
|---|---|---|---|
| 0–4 | 301 | 40 | 27 |
| 5–9 | 146 | 18 | 61 |
| 10–19 | 105 | 17 | 143 |
| 20+ | 24 | 3 | 182 |

Jelenleg **7** húzás óta nincs telitalálat. A várható érték így is a szelvény ára alatt marad; a táblázat csak azt mutatja, hogy a hosszan halmozódó főnyereménynél ugyanannyi pénzért több jár vissza.
