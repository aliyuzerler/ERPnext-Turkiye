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


def warehouse_turleri_tamamla() -> list[str]:
    """ERPNext v15'te site kurulumu sırasında atlanan Warehouse Type kaydını tamamlar.

    Şirketin varsayılan depolarını oluştururken ERPNext "Transit" türünü ister;
    yeni kurulan sitelerde bazen eksik kalır (gözlemlenen kurulum sırası sorunu).
    """
    import frappe

    eklenen: list[str] = []
    for tur in ["Transit"]:
        if frappe.db.exists("Warehouse Type", tur):
            continue
        # Warehouse Type "prompt" autoname kullanır: adı açıkça vermek gerekir
        frappe.get_doc({"doctype": "Warehouse Type", "name": tur, "warehouse_type": tur}).insert(
            ignore_permissions=True
        )
        eklenen.append(tur)
    frappe.db.commit()
    return eklenen


def kurulum_tamamlandi_isaretle() -> dict[str, bool]:
    """Sihirbazsız kurulumda "kurulum tamamlandı" bayraklarını kapatır.

    frappe.is_setup_complete() System Settings.setup_complete yerine
    "Installed Application" kayıtlarındaki is_setup_complete alanını okur;
    bench get-app + install-app ile kurulan sitelerde bu alanlar 0 kalır ve
    masaüstü her açılışta kurulum sihirbazına yönlendirir.
    """
    import frappe

    sonuc: dict[str, bool] = {}
    for app_adi in ["frappe", "erpnext", "erpnext_turkiye"]:
        name = frappe.db.get_value("Installed Application", {"app_name": app_adi})
        if not name:
            continue
        mevcut = frappe.db.get_value("Installed Application", name, "is_setup_complete")
        if not mevcut:
            frappe.db.set_value("Installed Application", name, "is_setup_complete", 1)
        sonuc[app_adi] = True
    frappe.db.set_single_value("System Settings", "setup_complete", 1)
    frappe.db.commit()
    frappe.clear_cache()
    return sonuc


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
            "tax_id": "3456789014",  # test vektörü (geçerli VKN algoritması)
        }
    )
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"company": ad, "durum": "oluşturuldu"}


def demo_verisi_olustur() -> list[str]:
    """Faz 1 ekran görüntüleri için örnek ana veri (müşteri, tedarikçi, kalem).

    Ağaç doctype varsayılanları (Customer Group, Territory, Supplier Group,
    Item Group) normalde kurulum sihirbazında oluşur; sihirbazsız kurulumda
    burada garanti edilir.
    """
    import frappe

    olusturulanlar: list[str] = []

    def grub_olustur(doctype: str, ad_alani: str, ad: str) -> None:
        if frappe.db.exists(doctype, ad):
            return
        frappe.get_doc({"doctype": doctype, ad_alani: ad, "is_group": 1}).insert(
            ignore_permissions=True
        )
        olusturulanlar.append(f"{doctype}: {ad}")

    grub_olustur("Customer Group", "customer_group_name", "All Customer Groups")
    grub_olustur("Territory", "territory_name", "All Territories")
    grub_olustur("Supplier Group", "supplier_group_name", "All Supplier Groups")
    grub_olustur("Item Group", "item_group_name", "All Item Groups")

    # Kayıt ekleme Group türlerine izin vermez: kök altına alt grup (is_group=0) kur
    def alt_grub_olustur(
        doctype: str,
        ad_alani: str,
        ebeveyn_alani: str,
        ad: str,
        ebeveyn: str,
    ) -> None:
        if frappe.db.exists(doctype, ad):
            return
        frappe.get_doc(
            {
                "doctype": doctype,
                ad_alani: ad,
                ebeveyn_alani: ebeveyn,
                "is_group": 0,
            }
        ).insert(ignore_permissions=True)
        olusturulanlar.append(f"{doctype}: {ad}")

    alt_grub_olustur(
        "Customer Group",
        "customer_group_name",
        "parent_customer_group",
        "Yerel Müşteriler",
        "All Customer Groups",
    )
    alt_grub_olustur(
        "Territory", "territory_name", "parent_territory", "Türkiye", "All Territories"
    )
    alt_grub_olustur(
        "Supplier Group",
        "supplier_group_name",
        "parent_supplier_group",
        "Onaylı Tedarikçiler",
        "All Supplier Groups",
    )
    alt_grub_olustur(
        "Item Group", "item_group_name", "parent_item_group", "Hizmetler", "All Item Groups"
    )

    if not frappe.db.exists("UOM", "Nos"):
        frappe.get_doc({"doctype": "UOM", "uom_name": "Nos", "must_be_whole_number": 1}).insert(
            ignore_permissions=True
        )
        olusturulanlar.append("UOM: Nos")

    def musteri_ekle(adi: str, tax_id: str) -> None:
        if frappe.db.exists("Customer", adi):
            return
        frappe.get_doc(
            {
                "doctype": "Customer",
                "customer_name": adi,
                "customer_type": "Company",
                "customer_group": "Yerel Müşteriler",
                "territory": "Türkiye",
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
                "supplier_group": "Onaylı Tedarikçiler",
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
                "item_group": "Hizmetler",
                "stock_uom": "Nos",
                "is_stock_item": 0,
            }
        ).insert(ignore_permissions=True)
        olusturulanlar.append(f"Kalem: {kodu}")

    # tax_id değerleri test paketindeki geçerli algoritma vektörleridir
    musteri_ekle("Anadolu Ticaret Ltd. Şti.", "3456789014")
    musteri_ekle("Marmara Endüstri A.Ş.", "1122334455")
    tedarikci_ekle("Ege Hammadde San. Tic.", "9876543217")
    kalem_ekle("HIZ-MLZ-001", "Montaj Hizmeti")
    kalem_ekle("HIZ-DAN-001", "Danışmanlık Hizmeti")

    frappe.db.commit()
    return olusturulanlar
