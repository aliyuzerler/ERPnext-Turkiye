"""İl/ilçe veri seti birim testleri (Faz 2).

Kaynak: volkansenturk/turkiye-iller-ilceler; ilçe sayıları güncel idari
sayımlarla (İstanbul 39, Ankara 25, İzmir 30, toplam 973) çapraz kontrolü.
"""

from __future__ import annotations

import pytest

from erpnext_turkiye.turkiye.veriler.il_ilce import (
    IL_PLAKALARI,
    il_mi,
    ilce_mi,
    ilceler_il,
    iller,
    toplam_ilce,
)


def test_81_il() -> None:
    assert len(iller()) == 81
    assert iller()[0] == "Adana"  # plaka 01
    assert IL_PLAKALARI["İstanbul"] == 34
    assert IL_PLAKALARI["Ankara"] == 6
    assert IL_PLAKALARI["Düzce"] == 81


def test_resmi_ilce_sayilari() -> None:
    assert len(ilceler_il("İstanbul")) == 39
    assert len(ilceler_il("Ankara")) == 25
    assert len(ilceler_il("İzmir")) == 30
    assert toplam_ilce() == 973


def test_ilce_icerigi() -> None:
    istanbul = ilceler_il("İstanbul")
    assert "Kadıköy" in istanbul
    assert "Beşiktaş" in istanbul
    assert "Adalar" in istanbul


def test_il_ilce_ayrimi() -> None:
    assert il_mi("Bursa") is True
    assert il_mi("Kadıköy") is False
    assert ilce_mi("Kadıköy") is True
    assert ilce_mi("Bursa") is False


def test_olmayan_il_key_error() -> None:
    with pytest.raises(KeyError, match="Yokşehir"):
        ilceler_il("Yokşehir")
