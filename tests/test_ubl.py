"""UBL-TR fatura üretimi birim testleri (hermetik; ağ/site gerekmez).

Referans değerler GİB'in resmî TEVKIFAT.xml örneğinden alınmıştır:
matrah 20.000, KDV %18 -> 3.600, tevkifat kod 606 %90 -> 3.240,
alıcının ödediği KDV 360. KM-3 kanıtı: üretilen XML resmî OASIS UBL 2.1
XSD'sinden geçer (xsd/UBL-2.1/, repoya tedarik edilmiş).
"""

from __future__ import annotations

from typing import Any

import pytest

from erpnext_turkiye.turkiye.ebelge.dogrula import INVOICE_XSD, xsd_ile_dogrula
from erpnext_turkiye.turkiye.ebelge.ubl import fatura_uret
from erpnext_turkiye.turkiye.ebelge.veri import (
    FaturaSatiri,
    FaturaVerisi,
    KDVGrubu,
    Taraf,
    TevkifatSatiri,
    dogrula_veri,
)


def tevkifat_faturasi(**degistir: Any) -> FaturaVerisi:
    """Resmî TEVKIFAT örnek değerleriyle sözleşme kurar (anahtar=alan adı)."""
    oz: dict[str, Any] = dict(
        fatura_no="SRM2012000086985",
        uuid="F47AC10B-58CC-4372-A567-0E02B2C3D479",
        tarih="2012-08-04",
        saat="07:47:00",
        gonderen=Taraf(
            vkn_tckn="0890890895",
            ad="Örnek İnşaat San. ve Tic. Ltd. Şti.",
            il="Adana",
            ilce="Seyhan",
            vergi_dairesi="Ziyapaşa",
        ),
        alici=Taraf(vkn_tckn="1870200192", ad="Alıcı Sanayi A.Ş.", il="İstanbul", ilce="Maslak"),
        satirlar=(FaturaSatiri(1, "Hafriyat Hizmeti", 1, "C62", 20000.0, 20000.0),),
        kdv_gruplari=(KDVGrubu(18, 20000.0, 3600.0),),
        tevkifatlar=(TevkifatSatiri("606", 90.0, 3240.0),),
        profil="TICARIFATURA",
        tur_kodu="TEVKIFAT",
        net_toplam=20000.0,
        genel_toplam=20360.0,
    )
    oz.update(degistir)
    return FaturaVerisi(**oz)


def test_tevkifat_usulu_resmi_ornek_degerleriyle() -> None:
    xml = fatura_uret(tevkifat_faturasi())
    # resmî örnek: TaxTotal 360 (ödenen), subtotal 3600 (tam), tevkifat 3240
    assert "<cbc:TaxAmount currencyID=\"TRY\">360.00</cbc:TaxAmount>" in xml
    assert "<cbc:TaxableAmount currencyID=\"TRY\">20000.00</cbc:TaxableAmount>" in xml
    assert "<cbc:TaxAmount currencyID=\"TRY\">3600.00</cbc:TaxAmount>" in xml
    assert "<cbc:Percent>18</cbc:Percent>" in xml
    assert "WithholdingTaxTotal" in xml
    assert "<cbc:TaxAmount currencyID=\"TRY\">3240.00</cbc:TaxAmount>" in xml
    assert "<cbc:Percent>90</cbc:Percent>" in xml
    assert "<cbc:TaxTypeCode>606</cbc:TaxTypeCode>" in xml
    assert "<cbc:PayableAmount currencyID=\"TRY\">20360.00</cbc:PayableAmount>" in xml


def test_temel_yapi_tr12() -> None:
    xml = fatura_uret(tevkifat_faturasi())
    assert "<cbc:UBLVersionID>2.1</cbc:UBLVersionID>" in xml
    assert "<cbc:CustomizationID>TR1.2</cbc:CustomizationID>" in xml
    assert "<cbc:ProfileID>TICARIFATURA</cbc:ProfileID>" in xml
    assert "<cbc:InvoiceTypeCode>TEVKIFAT</cbc:InvoiceTypeCode>" in xml
    assert 'schemeID="VKN">0890890895' in xml
    assert "InvoiceLine" in xml
    assert "<cbc:LineCountNumeric>1</cbc:LineCountNumeric>" in xml


def test_tevkifatsiz_faturada_withholding_yok() -> None:
    temiz = tevkifat_faturasi(
        tevkifatlar=(),
        profil="TEMELFATURA",
        tur_kodu="SATIS",
        genel_toplam=23600.0,  # 20000 + tam KDV 3600
    )
    xml = fatura_uret(temiz)
    assert "WithholdingTaxTotal" not in xml
    assert "<cbc:TaxAmount currencyID=\"TRY\">3600.00</cbc:TaxAmount>" in xml
    assert "<cbc:PayableAmount currencyID=\"TRY\">23600.00</cbc:PayableAmount>" in xml


def test_veri_dogrulama_hatalari() -> None:
    hatalar = dogrula_veri(
        tevkifat_faturasi(fatura_no="", uuid="", tarih="", saat="", genel_toplam=1.0)
    )
    assert any("fatura_no" in h for h in hatalar)
    assert any("uuid" in h for h in hatalar)
    assert any("genel_toplam" in h for h in hatalar)
    assert dogrula_veri(tevkifat_faturasi()) == []


def test_uuid_uretim() -> None:
    bos_uuid = tevkifat_faturasi(uuid="")
    xml = fatura_uret(bos_uuid, yeni_uuid=True)
    assert "<cbc:UUID>" in xml and "F47AC10B" not in xml


@pytest.mark.skipif(not INVOICE_XSD.exists(), reason="XSD seti repoda yok")
def test_xsd_dogrulama_temiz() -> None:
    xml = fatura_uret(tevkifat_faturasi())
    assert xsd_ile_dogrula(xml) == []


def test_xsd_gecersiz_xml_hata_uretir() -> None:
    # IssueDate geçersiz biçim: şema hata verir (KM-3 doğrulama ters kanıt)
    bozuk = fatura_uret(tevkifat_faturasi(tarih="32.13.2026"))
    hatalar = xsd_ile_dogrula(bozuk)
    assert hatalar
