"""Frappe doc_event işleyicileri (yapışkan katman).

Çekirdek mantık ``turkiye`` paketindeki SAF modüllerde tutulur; frappe
buraya yalnızca işleyici gövdesi içinde import edilir. Bu sayede çekirdek
kod bir Frappe sitesi olmadan birim test edilebilir (Faz 0 kapı kuralı).

Kancalar ``hooks.py`` üzerinden Customer/Supplier.validate'ye bağlıdır.
"""

from __future__ import annotations


def validate_tax_id(doc: object, method: str | None = None) -> None:
    """``tax_id`` alanı doluysa TCKN (11 hane) ya da VKN (10 hane) doğrula.

    Kaynak Veri katmanı kuralı (Tablo 3): iletime çıkmadan önce vergi
    numaralarının güvenilir olması. Company DocType'ı tüzel kişilere
    aittir: yalnızca 10 haneli VKN kabul edilir (şahıs şirketlerinin GİB
    VKN'si de VKN algoritmasından geçer).
    """
    try:
        import frappe
    except ImportError:  # sitesiz ortam (test/araç zinciri): sessiz geç
        return

    from erpnext_turkiye.turkiye.kimlik import normalize, validate_tckn, validate_vkn

    tax_id = getattr(doc, "tax_id", None) or ""
    if not tax_id:
        return
    temiz = normalize(tax_id)
    if getattr(doc, "doctype", "") == "Company":
        if len(temiz) == 10 and validate_vkn(temiz):
            return
        frappe.throw(f"Şirket için geçerli bir VKN gerekli (10 hane): {tax_id}")
    if len(temiz) == 11 and validate_tckn(temiz):
        return
    if len(temiz) == 10 and validate_vkn(temiz):
        return
    frappe.throw(f"Geçersiz Vergi/T.C. Kimlik Numarası: {tax_id}")
