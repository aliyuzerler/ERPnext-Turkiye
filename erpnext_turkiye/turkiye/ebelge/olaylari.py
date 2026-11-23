"""e-Belge Frappe kancaları (yapışkan katman, Faz 3).

Sales Invoice ``on_submit``: UBL-TR üretimi + şema doğrulaması + E Belge
Gonderim kaydı (KM-3: şemadan geçmeden kuyruğa girmez). ``on_cancel``:
ilgili kayıtlar Iptal yapılır. ``ebelge_ozeti``: e-belge durum panosunun
canlı veri kaynağı (Faz 0 bileşeni buraya bağlanır).

frappe/erpnext yalnızca fonksiyon gövdelerinde import edilir (Faz 0 kapı
kuralı); çekirdek ``ebelge`` paketi SAF'tır.
"""

from __future__ import annotations

from typing import Any

from erpnext_turkiye.turkiye.ebelge.veri import FaturaVerisi


def fatura_gonderim_kaydet(doc: Any, method: str | None = None) -> None:
    """Sales Invoice on_submit: e-Fatura UBL üret ve kayda al."""
    import frappe

    from erpnext_turkiye.turkiye.ebelge.dogrula import xsd_ile_dogrula
    from erpnext_turkiye.turkiye.ebelge.ubl import fatura_uret
    from erpnext_turkiye.turkiye.ebelge.veri import dogrula_veri

    if frappe.db.exists("E Belge Gonderim", {"fatura": doc.name, "belge_turu": "e-Fatura"}):
        return
    veri = fatura_sozlesmesi(doc.name)
    hatalar = dogrula_veri(veri)
    if hatalar:
        frappe.throw("UBL üretim öncesi sözleşme hataları: " + "; ".join(hatalar))
    xml = fatura_uret(veri)
    xsd_hatalari = xsd_ile_dogrula(xml)
    if xsd_hatalari:
        frappe.throw("UBL-TR şema doğrulaması başarısız (KM-3): " + "; ".join(xsd_hatalari[:3]))
    frappe.get_doc(
        {
            "doctype": "E Belge Gonderim",
            "fatura": doc.name,
            "belge_turu": "e-Fatura",
            "durum": "Uretilmis",
            "uuid": veri.uuid,
            "alici_vkn": veri.alici.vkn_tckn,
            "xml_icerik": xml,
        }
    ).insert(ignore_permissions=True)


def gonderim_iptal(doc: Any, method: str | None = None) -> None:
    """Sales Invoice on_cancel: e-belge kayıtlarını Iptal yapar."""
    import frappe

    kayitlar = frappe.get_all("E Belge Gonderim", filters={"fatura": doc.name}, pluck="name")
    for ad in kayitlar:
        frappe.db.set_value("E Belge Gonderim", ad, "durum", "Iptal")


def fatura_sozlesmesi(fatura_adi: str) -> FaturaVerisi:
    """Satış Faturası → ebelge.veri.FaturaVerisi sözleşmesi (site tarafı)."""
    import uuid as uuid_mod

    import frappe

    from erpnext_turkiye.turkiye.ebelge.veri import (
        FaturaSatiri,
        KDVGrubu,
        Taraf,
    )

    doc = frappe.get_doc("Sales Invoice", fatura_adi)
    sirket_vkn, sirket_adi = frappe.db.get_value(
        "Company", doc.company, ["tax_id", "company_name"]
    )
    musteri_vkn, musteri_adi = frappe.db.get_value(
        "Customer", doc.customer, ["tax_id", "customer_name"]
    )

    satirlar = tuple(
        FaturaSatiri(
            sira=int(kalem.idx),
            ad=kalem.item_name or kalem.item_code,
            miktar=float(kalem.qty or 0),
            birim="C62",
            birim_fiyat=float(kalem.rate or 0),
            satir_tutari=float(kalem.amount or 0),
        )
        for kalem in doc.items
    )

    # fatura düzeyi vergi satırlarından KDV grupları (On Net Total satırları)
    kdv_gruplari: dict[float, list[float]] = {}
    for vergi in doc.taxes or []:
        oran = round(float(vergi.rate or 0), 2)
        if oran <= 0:
            continue
        grup = kdv_gruplari.setdefault(oran, [0.0, 0.0])
        grup[0] += float(vergi.base_net_amount or 0)
        grup[1] += float(vergi.base_tax_amount or 0)

    saat_degeri = doc.posting_time or "00:00:00"
    if hasattr(saat_degeri, "strftime"):
        saat = saat_degeri.strftime("%H:%M:%S")
    elif hasattr(saat_degeri, "total_seconds"):
        # posting_time frappe'de timedelta gelir: str() "5:45:56." gibi
        # geçersiz bir saat üretir (KM-3 şema doğrulaması yakaladı)
        toplam = int(saat_degeri.total_seconds())
        saat = f"{toplam // 3600:02d}:{(toplam % 3600) // 60:02d}:{toplam % 60:02d}"
    else:
        saat = str(saat_degeri)[:8]

    return FaturaVerisi(
        fatura_no=doc.name,
        uuid=str(uuid_mod.uuid4()).upper(),
        tarih=str(doc.posting_date),
        saat=saat,
        gonderen=Taraf(vkn_tckn=sirket_vkn or "", ad=sirket_adi or doc.company),
        alici=Taraf(
            vkn_tckn=musteri_vkn or "",
            ad=musteri_adi or doc.customer,
            tckn_mi=len(musteri_vkn or "") == 11,
        ),
        satirlar=satirlar,
        kdv_gruplari=tuple(
            KDVGrubu(yuzde=oran, matrah=round(m[0], 2), tutar=round(m[1], 2))
            for oran, m in kdv_gruplari.items()
        ),
        profil="TICARIFATURA",
        tur_kodu="SATIS",
        para_birimi=doc.currency or "TRY",
        net_toplam=float(doc.net_total or 0),
        genel_toplam=float(doc.base_grand_total or 0),
    )


def gonderim_xml_yenile(fatura_adi: str) -> str:
    """Kayıtlı e-belge kaydının XML'ini güncel çekirdekten yeniden üretir.

    UUID sabit kalır (ilk kayıtta atanandır); şema doğrulaması yeniden koşar.
    """
    import frappe

    from erpnext_turkiye.turkiye.ebelge.dogrula import xsd_ile_dogrula
    from erpnext_turkiye.turkiye.ebelge.ubl import fatura_uret
    from erpnext_turkiye.turkiye.ebelge.veri import dogrula_veri

    kayit = frappe.db.get_value(
        "E Belge Gonderim",
        {"fatura": fatura_adi, "belge_turu": "e-Fatura"},
        ["name", "uuid"],
        as_dict=True,
    )
    if not kayit:
        frappe.throw(f"{fatura_adi} için e-belge kaydı yok")
    veri = fatura_sozlesmesi(fatura_adi)
    hatalar = dogrula_veri(veri)
    if hatalar:
        frappe.throw("sözleşme hataları: " + "; ".join(hatalar))
    xml = fatura_uret(veri)
    xsd_hatalari = xsd_ile_dogrula(xml)
    if xsd_hatalari:
        frappe.throw("şema doğrulaması başarısız: " + "; ".join(xsd_hatalari[:3]))
    frappe.db.set_value("E Belge Gonderim", kayit.name, "xml_icerik", xml)
    frappe.db.commit()
    return str(kayit.name)


def ebelge_ozeti() -> dict[str, object]:
    """e-belge durum panosu için canlı özet (whitelisted API).

    Dönüş: durum sayaçları + son kayıtlar (pano Faz 0 bileşenine beslenir).
    """
    import frappe

    kayitlar = frappe.get_all(
        "E Belge Gonderim",
        fields=["name", "fatura", "belge_turu", "durum", "alici_vkn", "uuid", "modified"],
        order_by="modified desc",
        limit_page_length=50,
    )
    sayilar: dict[str, int] = {}
    for kayit in frappe.get_all("E Belge Gonderim", fields=["durum"]):
        sayilar[kayit.durum] = sayilar.get(kayit.durum, 0) + 1
    return {"sayilar": sayilar, "kayitlar": kayitlar}
