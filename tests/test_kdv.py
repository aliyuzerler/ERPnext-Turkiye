"""KDV hesap yardımcılarının birim testleri."""

from __future__ import annotations

import pytest

from erpnext_turkiye.turkiye.kdv import kdv_hesapla, tevkifat_hesapla


def test_genel_oranlar() -> None:
    assert kdv_hesapla(1000, 20) == 200.0
    assert kdv_hesapla(1000, 10) == 100.0
    assert kdv_hesapla(1000, 1) == 10.0


def test_yuvarlama() -> None:
    # Beklenen değerler Python round() ile ayrıca hesaplanarak doğrulanmıştır.
    assert kdv_hesapla(33.35, 20) == 6.67
    assert kdv_hesapla(100.125, 10) == 10.01
    assert kdv_hesapla(2.675, 20) == 0.54


def test_gecersiz_oran_hata_verir() -> None:
    with pytest.raises(ValueError, match="Geçersiz KDV oranı"):
        kdv_hesapla(100, 18)


def test_negatif_matrah_hata_verir() -> None:
    with pytest.raises(ValueError, match="negatif"):
        kdv_hesapla(-5, 10)


def test_tevkifat_dokuz_on() -> None:
    yukluluk, tevkif = tevkifat_hesapla(1000, 20, 9, 10)
    assert tevkif == 180.0
    assert yukluluk == 20.0
    assert yukluluk + tevkif == 200.0  # KDV korunur


def test_tevkifat_yedi_on() -> None:
    yukluluk, tevkif = tevkifat_hesapla(100, 10, 7, 10)
    assert tevkif == 7.0
    assert yukluluk == 3.0


def test_tevkifat_gecersiz_kesir_hata_verir() -> None:
    with pytest.raises(ValueError, match="geçersiz"):
        tevkifat_hesapla(100, 10, 0, 10)
    with pytest.raises(ValueError, match="geçersiz"):
        tevkifat_hesapla(100, 10, 11, 10)
