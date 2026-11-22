"""TCMB kur servisi birim testleri (hermetik — ağ erişimi yok)."""

from __future__ import annotations

from pathlib import Path

import pytest

from erpnext_turkiye.turkiye.kur_servisi import fetch_kurlar, get_kur, parse_kurlar

FIXTURE = Path(__file__).parent / "fixtures" / "tcmb_today.xml"


@pytest.fixture()
def bulten_xml() -> str:
    return FIXTURE.read_text(encoding="utf-8")


def test_parse_tarih_ve_kayitlar(bulten_xml: str) -> None:
    tarih, kayitlar = parse_kurlar(bulten_xml)
    assert tarih == "20.11.2026"
    kodlar = [k.kod for k in kayitlar]
    assert kodlar == ["USD", "EUR"]


def test_usd_kaydi_alanlari(bulten_xml: str) -> None:
    _, kayitlar = parse_kurlar(bulten_xml)
    usd = get_kur(kayitlar, "USD")
    assert usd.isim == "ABD DOLARI"
    assert usd.birim == 1
    assert usd.alis == pytest.approx(50.4028)
    assert usd.satis == pytest.approx(50.4936)


def test_eur_kaydi_alanlari(bulten_xml: str) -> None:
    _, kayitlar = parse_kurlar(bulten_xml)
    eur = get_kur(kayitlar, "EUR")
    assert eur.alis == pytest.approx(54.1234)
    assert eur.satis == pytest.approx(54.2234)


def test_bultende_olmayan_kur_key_error(bulten_xml: str) -> None:
    _, kayitlar = parse_kurlar(bulten_xml)
    with pytest.raises(KeyError, match="GBP"):
        get_kur(kayitlar, "GBP")


def test_fetch_kurlar_sahte_opener_ile(bulten_xml: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Ağ erişimi sahte (fake) opener ile eslenir: test dış ortama bağlı değil."""

    class SahteYanit:
        def read(self) -> bytes:
            return bulten_xml.encode("utf-8")

        def __enter__(self) -> SahteYanit:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

    def sahte_urlopen(_istek: object, timeout: int = 30) -> SahteYanit:
        return SahteYanit()

    monkeypatch.setattr("erpnext_turkiye.turkiye.kur_servisi.urlopen", sahte_urlopen)
    tarih, kayitlar = fetch_kurlar(url="http://ornek.local/today.xml", timeout=1)
    assert tarih == "20.11.2026"
    assert len(kayitlar) == 2
