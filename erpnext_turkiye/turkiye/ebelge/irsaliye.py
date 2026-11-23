"""UBL DespatchAdvice (e-İrsaliye) taslak üreticisi (SAF Python).

GİB e-İrsaliye UBL-TR eşlemesinin iskeletidir: OASIS UBL 2.1
``UBL-DespatchAdvice-2.1.xsd`` ile şema doğrulamasından geçecek minimum
yapı (ID, UUID, IssueDate, taraflar, shipment, despatch satırları).
GİB-özel alanlar (zrf/gönderim şekli, üst yazı kodları) entegratör
doğrulamasıyla Faz 4'te tamamlanır; bu modül şema düzeyinde kanıt üretir.

Bu modül SAF Python'dur; frappe import etmez.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

NS_DESPATCH = "urn:oasis:names:specification:ubl:schema:xsd:DespatchAdvice-2"

_NAMESPACES: dict[str, str] = {
    "": NS_DESPATCH,
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
}


def _ele(
    parent: ET.Element | None,
    ad: str,
    metin: str | None = None,
    **nitelik: str,
) -> ET.Element:
    """``ubl._ele`` ile aynı sözleşme; DespatchAdvice isim alanıyla."""
    on, _, yerel = ad.partition(":")
    if on and on in _NAMESPACES and yerel:
        q = f"{{{_NAMESPACES[on]}}}{yerel}"
    else:
        q = f"{{{_NAMESPACES['']}}}{ad}"
    el = ET.SubElement(parent, q, nitelik) if parent is not None else ET.Element(q, nitelik)
    if metin is not None:
        el.text = metin
    return el


def _taraf_blok(ana: ET.Element, etiket: str, vkn: str, ad: str) -> None:
    """DespatchSupplier/DeliveryCustomerParty minimum bloğu."""
    blok = _ele(ana, f"cac:{etiket}")
    party = _ele(blok, "cac:Party")
    kimlik = _ele(party, "cac:PartyIdentification")
    _ele(kimlik, "cbc:ID", vkn, schemeID="VKN")
    _ele(_ele(party, "cac:PartyName"), "cbc:Name", ad)


def irsaliye_uret(
    no: str,
    uuid: str,
    tarih: str,
    gonderen_vkn: str,
    gonderen_ad: str,
    alici_vkn: str,
    alici_ad: str,
    satirlar: list[tuple[int, str, float]],
    sevk_id: str = "SEVK-1",
) -> str:
    """Minimum DespatchAdvice XML'i üretir.

    ``satirlar``: (sıra, ürün adı, teslim edilen miktar) üçlüleri.
    Not: OASIS DespatchAdviceType'da cac:Delivery çocuğu yoktur; teslim
    ayrıntısı Shipment içi aşamalarla taşınır (Faz 4 kapsam).
    """
    for onek, uri in _NAMESPACES.items():
        # boş önek dahil: DespatchAdvice kökü varsayılan isim alanında kalmalı
        ET.register_namespace(onek, uri)
    kok = _ele(None, "DespatchAdvice")
    _ele(kok, "cbc:ID", no)
    _ele(kok, "cbc:UUID", uuid)
    _ele(kok, "cbc:IssueDate", tarih)
    _taraf_blok(kok, "DespatchSupplierParty", gonderen_vkn, gonderen_ad)
    _taraf_blok(kok, "DeliveryCustomerParty", alici_vkn, alici_ad)
    sevk = _ele(kok, "cac:Shipment")
    _ele(sevk, "cbc:ID", sevk_id)
    for sira, ad, miktar in satirlar:
        satir = _ele(kok, "cac:DespatchLine")
        _ele(satir, "cbc:ID", str(sira))
        _ele(satir, "cbc:DeliveredQuantity", f"{miktar:g}", unitCode="C62")
        # DespatchLineType dizisinde Item'dan önce zorunlu OrderLineReference
        referans = _ele(satir, "cac:OrderLineReference")
        _ele(referans, "cbc:LineID", str(sira))
        _ele(_ele(satir, "cac:Item"), "cbc:Name", ad)
    return ET.tostring(kok, encoding="unicode", xml_declaration=False)
