"""Alapvető ellenőrzések:  python -m pytest tesztek"""

import numpy as np
import pytest

from scriptek.hatos import elemzes as he
from scriptek.hatos import mintazat as hm
from scriptek.hatos import szelvenyek as hs
from scriptek.hatos.tisztitas import _ft_to_int
from scriptek.hatos.tisztitas import beolvas as hatos_beolvas
from scriptek.kozos import ADATOK
from scriptek.luxor import elemzes as le
from scriptek.luxor import megterules as lm
from scriptek.luxor import szelvenyek as ls
from scriptek.luxor.tisztitas import beolvas as luxor_beolvas


@pytest.fixture(scope="module")
def hatos():
    return hatos_beolvas(ADATOK / "hatos.csv")


@pytest.fixture(scope="module")
def luxor():
    return luxor_beolvas(ADATOK / "luxor.csv", ADATOK / "luxor_nyeremenyek.csv")


def test_ft_atalakitas():
    assert _ft_to_int("1 152 640 105 Ft") == 1_152_640_105
    assert _ft_to_int("0") == 0


def test_hatos_tisztitas(hatos):
    sz = hatos[["sz1", "sz2", "sz3", "sz4", "sz5", "sz6"]].to_numpy()
    assert sz.min() >= 1 and sz.max() <= 45
    assert (np.diff(sz, axis=1) > 0).all()  # rendezett, nincs ismétlődés
    assert hatos["huzas_id"].is_monotonic_increasing
    assert hatos.loc[hatos.ev < 1998, "db_3"].isna().all()  # 1998 előtt hiányzó adat, nem 0


def test_hatos_szelvenyek(hatos):
    nep = he.nepszeruseg_modell(hatos, "3")
    sz = hs.szelvenyek_osszeallitasa(hatos, nep)
    assert len(sz) == 4 and all(len(t) == 6 for t in sz)
    assert len({x for t in sz for x in t}) == 24  # nincs átfedés
    multbeli = {tuple(r) for r in hatos[["sz1", "sz2", "sz3", "sz4", "sz5", "sz6"]].to_numpy()}
    assert not any(hs.mintazat_hibak(t, multbeli, hatos[["sz1", "sz2", "sz3", "sz4", "sz5", "sz6"]].to_numpy()[-104:])
                   for t in sz)


def test_luxor_tisztitas(luxor):
    assert all(1 <= min(s) and max(s) <= 75 and len(set(s)) == len(s) for s in luxor["huzott"])
    hianyos = luxor[~luxor["teljes_sorozat"]]
    assert list(zip(hianyos.ev, hianyos.het)) == [(2004, 32)]
    if "forras_egyezik" in luxor:
        assert (luxor["forras_egyezik"].dropna() == 1).all()


def test_kep_keret_keplet():
    h = np.array([[4, 4, 4, 4, 4], [0, 2, 4, 4, 0], [4, 1, 4, 4, 4], [4, 3, 3, 3, 4]])
    kep, keret, lux = le.esely_kep_keret(h)
    assert kep.tolist() == pytest.approx([1.0, 1 / 6, 0.0, 0.125])
    assert keret.tolist() == pytest.approx([1.0, 0.0, 0.0, 0.125])
    assert lux.tolist() == [1.0, 0.0, 0.0, 0.0]


def test_luxor_szelvenyek():
    sz = ls.szelvenyek_osszeallitasa()
    assert len(sz) == 4
    for t in sz:
        a = np.array(t)
        assert len(set(t)) == 20 and np.bincount((a - 1) // 15, minlength=5).tolist() == [4] * 5
    assert len({x for t in sz for x in t}) == 75  # együtt lefedik mind a 75 számot


def test_hatos_bovitett_modell(hatos):
    # a kombinációk sorszámozása egyértelmű
    osszes = he.osszes_kombinacio()
    rang = hm._rang(osszes[::9973])
    assert len(set(rang.tolist())) == len(rang) and rang.max() < len(osszes)
    assert hm._rang(np.array([[1, 2, 3, 4, 5, 6]]))[0] == 0
    assert hm._rang(np.array([[40, 41, 42, 43, 44, 45]]))[0] == len(osszes) - 1

    modellek = {m: hm.illeszt(hatos, m) for m in hm.SZINTEK}
    assert modellek[3].minta[0] < -0.03  # szomszédos számpár -> kevesebb nyertes
    meredekseg = {m: 0.8 for m in hm.SZINTEK}
    szorzok = hm.huzas_szorzok(modellek, meredekseg)
    assert all(abs(f.mean() - 1) < 1e-3 for f in szorzok.values())
    # a pontos szorzó megegyezik a közvetlen (lassú) számolással
    t = (1, 28, 29, 35, 36, 43)
    kozvetlen = np.exp(-0.8 * modellek[5].pontszam(osszes))
    kozvetlen /= kozvetlen.mean()
    tag = np.zeros(46, dtype=np.int8)
    tag[list(t)] = 1
    assert hm.szelveny_szorzo(t, szorzok)[5] == pytest.approx(kozvetlen[tag[osszes].sum(1) == 5].mean(), rel=1e-4)

    sulyok = hm.szint_sulyok(hatos)
    sz = hs.optimalis_szelvenyek(hatos, modellek, meredekseg, szorzok, sulyok)
    multbeli = {tuple(r) for r in hatos[["sz1", "sz2", "sz3", "sz4", "sz5", "sz6"]].to_numpy()}
    assert len(sz) == 4 and len({x for t in sz for x in t}) == 24
    assert all(hs.megengedett(t, multbeli) for t in sz)
    assert all(hm.szelveny_ertek(t, szorzok, sulyok) > sum(sulyok[m] for m in hm.SZINTEK) for t in sz)


def test_luxor_szerkezet_a_nyertesszamokbol(luxor):
    e = lm.szerkezet_ellenorzes(lm.heti_tabla(luxor)).set_index("kategória")["arány"]
    assert e["keret"] == pytest.approx(1, abs=0.05) and e["első kép"] == pytest.approx(1, abs=0.05)
    assert e["luxor"] == pytest.approx(1, abs=0.12)
