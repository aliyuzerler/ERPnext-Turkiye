"""UBL-TR 1.2 fatura XML üreticisi (SAF Python).

Yapı, GİB'in resmî örnek faturalarından birebir alınmıştır
(fatihaslamaci/GIBFramework deposundaki ``SampleApp/OrnekFaturalar/`` —
TEVKIFAT.xml, 01-TemelFaturaOrnegi.xml; CustomizationID ``TR1.2``,
KDV TaxTypeCode ``0015``, tevkifat ``cac:WithholdingTaxTotal``).

Tevkifat usulü (resmî TEVKIFAT örneğinden):
- ``cac:TaxTotal/cbc:TaxAmount``          = alıcının ödediği KDV (tam KDV − tevkifat)
- ``cac:TaxTotal/cac:TaxSubtotal``        = tam KDV (matrah + oran)
- ``cac:WithholdingTaxTotal/cbc:TaxAmount`` = tevkif edilen toplam

Bu modül SAF Python'dur; frappe import etmez. Doğrulama ``dogrula.py``'de
OASIS UBL 2.1 XSD setiyle (``xsd/``) yapılır.
"""

from __future__ import annotations

import uuid as uuid_mod
import xml.etree.ElementTree as ET

from erpnext_turkiye.turkiye.ebelge.veri import (
    KDV_TUR_KODU,
    UBL_TR_SURUM,
    UBL_VERSIYON,
    FaturaVerisi,
    Taraf,
)

NS_INVOICE = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
NS_CAC = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
NS_CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
NS_EXT = "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
# imza yer tutucusu: özel isim alanı (şemada tanımsız -> lax ile geçer)
NS_EBELGE = "urn:erpnext-turkiye:ebelge:yer-tutucu"

_NAMESPACES: dict[str, str] = {
    "": NS_INVOICE,
    "cac": NS_CAC,
    "cbc": NS_CBC,
    "ext": NS_EXT,
    "ebelge": NS_EBELGE,
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}


def _para(x: float) -> str:
    """Tutarı GİB biçiminde yazar: iki hane, nokta ondalık ayracı."""
    return f"{x:.2f}"


def _yuzde(x: float) -> str:
    """Oranı gereksiz sıfırlardan arındırır: 18 -> '18', 18.5 -> '18.5'."""
    return format(x, "g")


def _ele(
    parent: ET.Element | None,
    ad: str,
    metin: str | None = None,
    **nitelik: str,
) -> ET.Element:
    """Uygun isim alanıyla alt eleman kurar; metin verilirse yazar.

    ``ad`` "cac:Party" / "cbc:ID" biçiminde önekli gelir; öneksiz adlar
    fatura varsayılan isim alanına gider.
    """
    on, _, yerel = ad.partition(":")
    if on and on in _NAMESPACES and yerel:
        q = f"{{{_NAMESPACES[on]}}}{yerel}"
    else:
        q = f"{{{_NAMESPACES['']}}}{ad}"
    el = ET.SubElement(parent, q, nitelik) if parent is not None else ET.Element(q, nitelik)
    if metin is not None:
        el.text = metin
    return el


def _taraf_blok(ana: ET.Element, etiket: str, taraf: Taraf) -> None:
    """AccountingSupplier/CustomerParty bloğu (resmî örnek dizilimiyle)."""
    blok = _ele(ana, f"cac:{etiket}")
    party = _ele(blok, "cac:Party")
    kimlik = _ele(party, "cac:PartyIdentification")
    _ele(kimlik, "cbc:ID", taraf.vkn_tckn, schemeID="TCKN" if taraf.tckn_mi else "VKN")
    _ele(_ele(party, "cac:PartyName"), "cbc:Name", taraf.ad)
    adres = _ele(party, "cac:PostalAddress")
    if taraf.adres:
        _ele(adres, "cbc:StreetName", taraf.adres)
    if taraf.bina_no:
        _ele(adres, "cbc:BuildingNumber", taraf.bina_no)
    if taraf.ilce:
        _ele(adres, "cbc:CitySubdivisionName", taraf.ilce)
    if taraf.il:
        _ele(adres, "cbc:CityName", taraf.il)
    if taraf.posta_kodu:
        _ele(adres, "cbc:PostalZone", taraf.posta_kodu)
    ulke = _ele(adres, "cac:Country")
    _ele(ulke, "cbc:Name", "Türkiye")
    if taraf.vergi_dairesi:
        vergi = _ele(party, "cac:PartyTaxScheme")
        _ele(_ele(vergi, "cac:TaxScheme"), "cbc:Name", taraf.vergi_dairesi)


def _imza_blok(ana: ET.Element, gonderen: Taraf) -> None:
    """cac:Signature: entegratör imza ekleyene kadar URI #Signature yer tutucu."""
    imza = _ele(ana, "cac:Signature")
    _ele(imza, "cbc:ID", gonderen.vkn_tckn, schemeID="VKN_TCKN")
    taraf = _ele(imza, "cac:SignatoryParty")
    kimlik = _ele(taraf, "cac:PartyIdentification")
    _ele(kimlik, "cbc:ID", gonderen.vkn_tckn, schemeID="TCKN" if gonderen.tckn_mi else "VKN")
    ek = _ele(imza, "cac:DigitalSignatureAttachment")
    ref = _ele(ek, "cac:ExternalReference")
    _ele(ref, "cbc:URI", "#Signature")


def fatura_uret(veri: FaturaVerisi, yeni_uuid: bool = False) -> str:
    """UBL-TR 1.2 Invoice XML'i üretir; boş hata listesiyle çağrılmalı.

    ``yeni_uuid`` doğrulanmışsa (fatura_no boşsa) yeni UUID üretir; diğer
    hallerde veri içindeki UUID kullanılır.
    """
    if yeni_uuid and not veri.uuid:
        veri = FaturaVerisi(
            fatura_no=veri.fatura_no,
            uuid=str(uuid_mod.uuid4()).upper(),
            tarih=veri.tarih,
            saat=veri.saat,
            gonderen=veri.gonderen,
            alici=veri.alici,
            satirlar=veri.satirlar,
            kdv_gruplari=veri.kdv_gruplari,
            tevkifatlar=veri.tevkifatlar,
            profil=veri.profil,
            tur_kodu=veri.tur_kodu,
            para_birimi=veri.para_birimi,
            net_toplam=veri.net_toplam,
            genel_toplam=veri.genel_toplam,
        )

    for ns_onek, uri in _NAMESPACES.items():
        # boş önek dahil: Invoice kökü varsayılan isim alanında kalmalı
        # (aksinde ns0:Invoice ürer — entegratör şeması standardı bozar)
        ET.register_namespace(ns_onek, uri)
    kok = _ele(None, "Invoice")

    uzantilar = _ele(kok, "ext:UBLExtensions")
    uzanti = _ele(uzantilar, "ext:UBLExtension")
    icerik = _ele(uzanti, "ext:ExtensionContent")
    # GİB akışında imzayı entegratör yazar; şema (OASIS) ExtensionContent
    # içinde tam bir çocuk ister — serbest (lax anyType) yer tutucu düğüm.
    # GİB xsdrt boş içeriğe izin verdiğinden entegratör boş alır.
    _ele(icerik, "ebelge:ImzaYerTutucu")

    _ele(kok, "cbc:UBLVersionID", UBL_VERSIYON)
    _ele(kok, "cbc:CustomizationID", UBL_TR_SURUM)
    _ele(kok, "cbc:ProfileID", veri.profil)
    _ele(kok, "cbc:ID", veri.fatura_no)
    _ele(kok, "cbc:CopyIndicator", "false")
    _ele(kok, "cbc:UUID", veri.uuid)
    _ele(kok, "cbc:IssueDate", veri.tarih)
    _ele(kok, "cbc:IssueTime", veri.saat)
    _ele(kok, "cbc:InvoiceTypeCode", veri.tur_kodu)
    _ele(kok, "cbc:DocumentCurrencyCode", veri.para_birimi)
    _ele(kok, "cbc:LineCountNumeric", str(veri.satir_sayisi))

    _imza_blok(kok, veri.gonderen)
    _taraf_blok(kok, "AccountingSupplierParty", veri.gonderen)
    _taraf_blok(kok, "AccountingCustomerParty", veri.alici)

    if veri.kdv_gruplari:
        kdv = _ele(kok, "cac:TaxTotal")
        _ele(kdv, "cbc:TaxAmount", _para(veri.odenecek_kdv), currencyID=veri.para_birimi)
        for grup in veri.kdv_gruplari:
            alt = _ele(kdv, "cac:TaxSubtotal")
            _ele(alt, "cbc:TaxableAmount", _para(grup.matrah), currencyID=veri.para_birimi)
            _ele(alt, "cbc:TaxAmount", _para(grup.tutar), currencyID=veri.para_birimi)
            _ele(alt, "cbc:Percent", _yuzde(grup.yuzde))
            kategori = _ele(alt, "cac:TaxCategory")
            sema = _ele(kategori, "cac:TaxScheme")
            _ele(sema, "cbc:Name", "KDV")
            _ele(sema, "cbc:TaxTypeCode", KDV_TUR_KODU)
    if veri.tevkifatlar:
        tevkif = _ele(kok, "cac:WithholdingTaxTotal")
        _ele(tevkif, "cbc:TaxAmount", _para(veri.tevkifat_toplami), currencyID=veri.para_birimi)
        for tevkifat_kaydi in veri.tevkifatlar:
            alt = _ele(tevkif, "cac:TaxSubtotal")
            _ele(alt, "cbc:TaxAmount", _para(tevkifat_kaydi.tutar), currencyID=veri.para_birimi)
            _ele(alt, "cbc:Percent", _yuzde(tevkifat_kaydi.yuzde))
            kategori = _ele(alt, "cac:TaxCategory")
            sema = _ele(kategori, "cac:TaxScheme")
            _ele(sema, "cbc:TaxTypeCode", tevkifat_kaydi.kod)

    para = _ele(kok, "cac:LegalMonetaryTotal")
    _ele(para, "cbc:LineExtensionAmount", _para(veri.net_toplam), currencyID=veri.para_birimi)
    _ele(para, "cbc:TaxExclusiveAmount", _para(veri.net_toplam), currencyID=veri.para_birimi)
    _ele(
        para,
        "cbc:TaxInclusiveAmount",
        _para(veri.net_toplam + veri.odenecek_kdv),
        currencyID=veri.para_birimi,
    )
    _ele(para, "cbc:PayableAmount", _para(veri.genel_toplam), currencyID=veri.para_birimi)

    for satir in veri.satirlar:
        il = _ele(kok, "cac:InvoiceLine")
        _ele(il, "cbc:ID", str(satir.sira))
        _ele(il, "cbc:InvoicedQuantity", _para(satir.miktar), unitCode=satir.birim)
        _ele(il, "cbc:LineExtensionAmount", _para(satir.satir_tutari), currencyID=veri.para_birimi)
        _ele(_ele(il, "cac:Item"), "cbc:Name", satir.ad)
        fiyat = _ele(il, "cac:Price")
        _ele(fiyat, "cbc:PriceAmount", _para(satir.birim_fiyat), currencyID=veri.para_birimi)

    return ET.tostring(kok, encoding="unicode", xml_declaration=False)
