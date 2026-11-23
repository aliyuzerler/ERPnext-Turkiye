"""KDV oranları ve hesap yardımcıları.

Güncel genel geçer oranlar: %1, %10, %20. Tevkifat kod kataloğu (GİB
e-Fatura kod listesi) Faz 3'te UBL-TR eşleme paketiyle eklenir; burada
yalnızca kesir üzerinden hesap yapan genel fonksiyon bulunur.

Bu modül SAF Python'dur; frappe import etmez.
"""

from __future__ import annotations

ORANLAR: tuple[int, ...] = (1, 10, 20)


def kdv_hesapla(matrah: float, oran: int) -> float:
    """Matrahın KDV tutarını, verilen orana göre 2 hane hassasiyetle döndürür."""
    if oran not in ORANLAR:
        raise ValueError(f"Geçersiz KDV oranı: {oran}. Beklenen: {ORANLAR}")
    if matrah < 0:
        raise ValueError("Matrah negatif olamaz")
    return round(matrah * oran / 100, 2)


def tevkifat_hesapla(matrah: float, oran: int, pay: int, payda: int) -> tuple[float, float]:
    """Tevkifatlı KDV dağılımını döndürür: ``(satici_yuklulugu, tevkif_edilen)``.

    Örnek: ``tevkifat_hesapla(1000, 20, 9, 10)`` -> ``(20.0, 180.0)``
    (200 KDV'nin 9/10'u tevkif edilir).
    """
    if payda <= 0 or pay <= 0 or pay > payda:
        raise ValueError(f"Tevkifat kesri geçersiz: {pay}/{payda}")
    kdv = kdv_hesapla(matrah, oran)
    tevkif_edilen = round(kdv * pay / payda, 2)
    satici_yuklulugu = round(kdv - tevkif_edilen, 2)
    return satici_yuklulugu, tevkif_edilen


# ---------------------------------------------------------------------------
# Site tarafı: KDV setleri (frappe yalnızca fonksiyon gövdelerinde import)
# ---------------------------------------------------------------------------

SATIS_HESABI = "391"  # Hesaplanan KDV
ALIS_HESABI = "191"  # İndirilecek KDV
TEVKIFAT_HESABI = "360"  # Ödenecek Vergi ve Fonlar


def kdv_kur(sirket: str) -> dict[str, object]:
    """KDV setlerini şirkete kurar (idempotent).

    Oluşturulan setler: satış şablonları (391 ile %1/%10/%20), alış
    şablonları (191 ile %1/%10/%20) ve kalem vergi şablonları. KDV %20
    şablonları varsayılan işaretlenir. Dönüş: ``olusan`` (bu çağrıda
    yaratılanlar) + ``docname`` (faturalarda kullanılacak gerçek docname'ler).
    """
    import frappe

    satis_hesabi = frappe.db.get_value(
        "Account", {"account_number": SATIS_HESABI, "company": sirket}
    )
    alis_hesabi = frappe.db.get_value("Account", {"account_number": ALIS_HESABI, "company": sirket})
    if not (satis_hesabi and alis_hesabi):
        frappe.throw(
            f"{sirket} şirketinde {SATIS_HESABI}/{ALIS_HESABI} hesapları yok; "
            "önce hesap_plani.thp_kur çalışmalı"
        )

    olusan: dict[str, list[str]] = {"satis": [], "alis": [], "kalem": []}
    # docname'ler "{başlık} - {şirket kısaltması}" biçiminde üretilir;
    # kesin eşleme için başlık+şirket araması kullanılır
    docname: dict[str, str] = {}
    for oran in ORANLAR:
        satis_adi = f"KDV %{oran} Satış"
        satis_doc = frappe.db.get_value(
            "Sales Taxes and Charges Template", {"title": satis_adi, "company": sirket}
        )
        if satis_doc:
            docname[satis_adi] = satis_doc
        else:
            doc = frappe.get_doc(
                {
                    "doctype": "Sales Taxes and Charges Template",
                    "title": satis_adi,
                    "company": sirket,
                    "is_default": 1 if oran == 20 else 0,
                    "taxes": [
                        {
                            "charge_type": "On Net Total",
                            "account_head": satis_hesabi,
                            "rate": oran,
                            "description": f"KDV %{oran}",
                        }
                    ],
                }
            )
            doc.insert(ignore_permissions=True)
            docname[satis_adi] = doc.name
            olusan["satis"].append(satis_adi)
        alis_adi = f"KDV %{oran} Alış"
        alis_doc = frappe.db.get_value(
            "Purchase Taxes and Charges Template", {"title": alis_adi, "company": sirket}
        )
        if alis_doc:
            docname[alis_adi] = alis_doc
        else:
            doc = frappe.get_doc(
                {
                    "doctype": "Purchase Taxes and Charges Template",
                    "title": alis_adi,
                    "company": sirket,
                    "is_default": 1 if oran == 20 else 0,
                    "taxes": [
                        {
                            "charge_type": "On Net Total",
                            "account_head": alis_hesabi,
                            "rate": oran,
                            "description": f"KDV %{oran}",
                        }
                    ],
                }
            )
            doc.insert(ignore_permissions=True)
            docname[alis_adi] = doc.name
            olusan["alis"].append(alis_adi)
        kalem_adi = f"KDV %{oran}"
        kalem_doc = frappe.db.get_value(
            "Item Tax Template", {"title": kalem_adi, "company": sirket}
        )
        if kalem_doc:
            docname[kalem_adi] = kalem_doc
        else:
            # kalem şablonu satış yönünde 391'e işler; alış faturalarında
            # fatura düzeyi alış şablonu kullanılır
            doc = frappe.get_doc(
                {
                    "doctype": "Item Tax Template",
                    "title": kalem_adi,
                    "company": sirket,
                    "taxes": [{"tax_type": satis_hesabi, "tax_rate": oran}],
                }
            )
            doc.insert(ignore_permissions=True)
            docname[kalem_adi] = doc.name
            olusan["kalem"].append(kalem_adi)
    frappe.db.commit()
    return {"olusan": olusan, "docname": docname}


def tevkifat_kategorisi_olustur(pay: int, payda: int, oran: int = 20) -> str:
    """Parametrik KDV tevkifat kategorisi kurar (ERPNext TDS mekanizması).

    Tevkifat oranı = ``oran x pay / payda`` (net matrah üzerinden); örn.
    %20 KDV'nin 9/10'u -> tax_withholding_rate 18.0. Hesap: 360 Ödenecek
    Vergi ve Fonlar. Resmî GİB tevkifat kod kataloğu Faz 3 UBL-TR paketinde
    eklenir. v15 şeması: rates + accounts iki zorunlu alt tablo.
    """
    import frappe

    sirket = frappe.get_all("Company", pluck="name")[0]
    tevkifat_docname = frappe.db.get_value(
        "Account", {"account_number": TEVKIFAT_HESABI, "company": sirket}
    )
    if not tevkifat_docname:
        frappe.throw(f"{TEVKIFAT_HESABI} hesabı yok; önce hesap_plani.thp_kur çalışmalı")
    kategori = f"KDV Tevkifatı {pay}/{payda} (%{oran})"
    if frappe.db.exists("Tax Withholding Category", kategori):
        return kategori
    frappe.get_doc(
        {
            "doctype": "Tax Withholding Category",
            # autoname Prompt: adı açıkça vermek gerekir
            "name": kategori,
            "category_name": kategori,
            "rates": [
                {
                    "tax_withholding_rate": round(oran * pay / payda, 2),
                    "single_threshold": 0.0,
                    "cumulative_threshold": 0.0,
                    "from_date": "2001-01-01",
                    "to_date": "2099-12-31",
                }
            ],
            "accounts": [{"company": sirket, "account": tevkifat_docname}],
        }
    ).insert(ignore_permissions=True)
    frappe.db.commit()
    return kategori
