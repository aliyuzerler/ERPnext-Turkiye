"""THP başlangıç veri seti birim testleri."""

from __future__ import annotations

import pytest

from erpnext_turkiye.turkiye.hesap_plani import (
    BASLANGIC_THP,
    Hesap,
    kod_ile,
    validate_thp,
)


def test_baslangic_seti_temiz() -> None:
    assert validate_thp(BASLANGIC_THP) == []


def test_kod_ile_bulma() -> None:
    assert kod_ile(BASLANGIC_THP, "391").ad == "Hesaplanan KDV"
    assert kod_ile(BASLANGIC_THP, "600").tur == "Gelir"
    assert kod_ile(BASLANGIC_THP, "191").tur == "Varlık"


def test_kod_ile_bulunamayan_hata_verir() -> None:
    with pytest.raises(KeyError, match="999"):
        kod_ile(BASLANGIC_THP, "999")


def test_kod_tekrarı_yakalanir() -> None:
    bozuk = (*BASLANGIC_THP, Hesap("100", "İkinci Kasa", "Varlık"))
    hatalar = validate_thp(bozuk)
    assert any("Kod tekrarı: 100" in h for h in hatalar)


def test_gecersiz_kod_ve_tur_yakalanir() -> None:
    bozuk = [Hesap("19", "Kısa Kod", "Varlık"), Hesap("900", "Yanlış Tür", "Üçüncü")]
    hatalar = validate_thp(bozuk)
    assert any("3 rakam olmalı: 19" in h for h in hatalar)
    assert any("Geçersiz tür (900)" in h for h in hatalar)
