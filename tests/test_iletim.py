"""İletim kuyruğu birim testleri (SAF, sahte saat ve sahte gönderici ile)."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from erpnext_turkiye.turkiye.ebelge.iletim import (
    KuyrukKaydi,
    bekleme_suresi,
    kuyruk_isle,
)


def test_bekleme_suresi_ustel_ve_sinirli() -> None:
    assert bekleme_suresi(1) == 2.0
    assert bekleme_suresi(2) == 4.0
    assert bekleme_suresi(3) == 8.0
    assert bekleme_suresi(10) == 60.0  # üst limit
    assert bekleme_suresi(5, taban=1.5) == pytest.approx(1.5**5)  # 7.59375


def test_ilk_denemede_basarili() -> None:
    uykular: list[float] = []
    kayit = KuyrukKaydi("f-1", "<Invoice/>")
    sonuclar = kuyruk_isle([kayit], lambda _x: "OK", saat=uykular.append)
    assert len(sonuclar) == 1
    s = sonuclar[0]
    assert s.durum == "Gonderildi"
    assert s.deneme_sayisi == 1
    assert s.cevap == "OK"
    assert uykular == []


def test_ustel_geri_cekilme_ile_basarili() -> None:
    """İki kez hata veren gönderici 3. denemede başarılı: uyku [2, 4]."""
    uykular: list[float] = []
    denemeler: list[str] = []

    def tereddutlu_gonderici(xml: str) -> str:
        denemeler.append(xml)
        if len(denemeler) < 3:
            raise RuntimeError("entegratör 503")
        return "KABUL: f-1"

    sonuclar = kuyruk_isle(
        [KuyrukKaydi("f-1", "<Invoice/>")],
        tereddutlu_gonderici,
        saat=uykular.append,
    )
    s = sonuclar[0]
    assert s.durum == "Gonderildi"
    assert s.deneme_sayisi == 3
    assert s.cevap == "KABUL: f-1"
    assert uykular == [2.0, 4.0]
    assert len(denemeler) == 3


def test_tum_denemeler_basarısızsa_hata() -> None:
    uykular: list[float] = []

    def her_zaman_hata(_xml: str) -> str:
        raise RuntimeError("kalıcı hata")

    sonuclar = kuyruk_isle(
        [KuyrukKaydi("f-9", "<Invoice/>")],
        her_zaman_hata,
        saat=uykular.append,
    )
    s = sonuclar[0]
    assert s.durum == "Hata"
    assert s.deneme_sayisi == 3
    assert "kalıcı hata" in s.hata
    assert uykular == [2.0, 4.0]


def test_kuyruk_sirali_isler() -> None:
    gonderilen: list[str] = []

    def kaydedici(xml: str) -> str:
        gonderilen.append(xml)
        return "ok"

    kayitlar = [KuyrukKaydi(f"f-{i}", f"<Invoice id='{i}'/>") for i in range(1, 4)]
    sonuclar = kuyruk_isle(kayitlar, kaydedici, saat=_sart_siz_saat())
    assert [s.kimlik for s in sonuclar] == ["f-1", "f-2", "f-3"]
    assert gonderilen == [k.xml for k in kayitlar]


def _sart_siz_saat() -> Callable[[float], None]:
    def _bekle(_sn: float) -> None:
        return None

    return _bekle
