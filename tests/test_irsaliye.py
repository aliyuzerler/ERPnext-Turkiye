"""e-İrsaliye (DespatchAdvice) taslak üretimi testleri — KM-3 şema kanıtı."""

from __future__ import annotations

import pytest

from erpnext_turkiye.turkiye.ebelge.dogrula import DESPATCH_XSD, xsd_ile_dogrula
from erpnext_turkiye.turkiye.ebelge.irsaliye import irsaliye_uret


def ornek_irsaliye() -> str:
    return irsaliye_uret(
        no="IRS-2026-0001",
        uuid="1A2B3C4D-0000-0000-0000-000000000001",
        tarih="2026-11-23",
        gonderen_vkn="0890890895",
        gonderen_ad="Anadolu Makine Sanayi A.Ş.",
        alici_vkn="3456789014",
        alici_ad="Anadolu Ticaret Ltd. Şti.",
        satirlar=[(1, "Montaj Hizmeti", 1)],
    )


def test_irsaliye_yapi() -> None:
    xml = ornek_irsaliye()
    assert "DespatchAdvice" in xml
    assert "<cbc:DeliveredQuantity unitCode=\"C62\">1</cbc:DeliveredQuantity>" in xml
    assert 'schemeID="VKN">0890890895' in xml


@pytest.mark.skipif(not DESPATCH_XSD.exists(), reason="XSD seti repoda yok")
def test_irsaliye_xsd_temiz() -> None:
    assert xsd_ile_dogrula(ornek_irsaliye(), DESPATCH_XSD) == []
