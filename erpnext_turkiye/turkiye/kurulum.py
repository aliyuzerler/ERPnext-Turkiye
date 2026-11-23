"""Faz 1 kurulum yardımcıları (site içi çalışır).

Bu fonksiyonlar bench üzerinden çağrılır::

    bench --site turkiye.local execute \\
        erpnext_turkiye.turkiye.kurulum.site_tr_ayarlari
    bench --site turkiye.local execute \\
        erpnext_turkiye.turkiye.kurulum.demo_verisi_olustur

Tasarım kuralı gereği frappe yalnızca fonksiyon gövdesinde import edilir;
modül düzeyinde bağımlılık yoktur (Faz 0 kapı kuralı korunur).
"""

from __future__ import annotations


def site_tr_ayarlari() -> dict[str, str]:
    """Siteyi Türkiye profiline ayarlar: dil, saat dilimi, ülke, tarih biçimi.

    Dönüş değeri uygulanan ayarların özeti; bench çıktısında görünür.
    """
    import frappe

    frappe.db.set_single_value(
        "System Settings",
        {
            "language": "tr",
            "time_zone": "Europe/Istanbul",
            "country": "Turkey",
            "date_format": "dd.MM.yyyy",
            "first_day_of_the_week": "Monday",
        },
    )
    frappe.db.commit()
    frappe.clear_cache()
    return {"dil": "tr", "saat_dilimi": "Europe/Istanbul", "ulke": "Turkey"}


def sirket_olustur(
    ad: str = "Anadolu Makine Sanayi A.Ş.",
    kisaltma: str = "AMS",
) -> dict[str, str | None]:
    """TRY para birimi ve Türkiye ülkesiyle örnek şirketi kurar.

    Hesap planı Faz 2'de THP tam setiyle değiştirilecektir; Faz 1'de
    "Standard with Numbers" ile başlar (numerik kodlu, THP'ye geçişe uygun).
    """
    import frappe

    mevcut = frappe.db.exists("Company", ad)
    if mevcut:
        return {"company": ad, "durum": "zaten var"}

    doc = frappe.get_doc(
        {
            "doctype": "Company",
            "company_name": ad,
            "abbr": kisaltma,
            "country": "Turkey",
            "default_currency": "TRY",
            "chart_of_accounts": "Standard with Numbers",
            "company_email": "info@ornek.local",
            "tax_id": "3456789016",  # test vektörü (geçerli VKN algoritması)
        }
    )
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"company": ad, "durum": "oluşturuldu"}


def demo_verisi_olustur() -> list[str]:
    """Faz 1 ekran görüntüleri için örnek ana veri (müşteri, tedarikçi, kalem)."""
    import frappe

    olusturulanlar: list[str] = []

    def musteri_ekle(adi: str, tax_id: str) -> None:
        if frappe.db.exists("Customer", adi):
            return
        frappe.get_doc(
            {
                "doctype": "Customer",
                "customer_name": adi,
                "customer_type": "Company",
                "customer_group": "All Customer Groups",
                "territory": "All Territories",
                "tax_id": tax_id,
            }
        ).insert(ignore_permissions=True)
        olusturulanlar.append(f"Müşteri: {adi}")

    def tedarikci_ekle(adi: str, tax_id: str) -> None:
        if frappe.db.exists("Supplier", adi):
            return
        frappe.get_doc(
            {
                "doctype": "Supplier",
                "supplier_name": adi,
                "supplier_group": "All Supplier Groups",
                "tax_id": tax_id,
            }
        ).insert(ignore_permissions=True)
        olusturulanlar.append(f"Tedarikçi: {adi}")

    def kalem_ekle(kodu: str, adi: str) -> None:
        if frappe.db.exists("Item", kodu):
            return
        frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": kodu,
                "item_name": adi,
                "item_group": "All Item Groups",
                "stock_uom": "Nos",
                "is_stock_item": 0,
            }
        ).insert(ignore_permissions=True)
        olusturulanlar.append(f"Kalem: {kodu}")

    # tax_id değerleri test paketindeki geçerli algoritma vektörleridir
    musteri_ekle("Anadolu Ticaret Ltd. Şti.", "3456789016")
    musteri_ekle("Marmara Endüstri A.Ş.", "1122334459")
    tedarikci_ekle("Ege Hammadde San. Tic.", "9876543217")
    kalem_ekle("HIZ-MLZ-001", "Montaj Hizmeti")
    kalem_ekle("HIZ-DAN-001", "Danışmanlık Hizmeti")

    frappe.db.commit()
    return olusturulanlar
