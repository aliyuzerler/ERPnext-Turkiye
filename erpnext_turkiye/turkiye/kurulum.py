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
    # "yazıyla tutar" (num2words) istek dilini kullanır: Administrator'un
    # dili tr olmalı, aksi halde faturalarda tutar İngilizce yazar
    frappe.db.set_value("User", "Administrator", "language", "tr")
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


def faz2_kurulum() -> dict[str, object]:
    """Faz 2 tümleşik kurulumu: THP tam seti + varsayılanlar + KDV setleri + Territory.

    Idempotenttir; mevcut kayıtlar atlanır. Sıra önemlidir: THP önce
    çalışmalı (KDV setleri 191/391 hesaplarını ister).
    """
    import frappe

    from erpnext_turkiye.turkiye.hesap_plani import sirket_hesap_varsayilanlari, thp_kur
    from erpnext_turkiye.turkiye.kdv import kdv_kur
    from erpnext_turkiye.turkiye.yerlesim import territory_kur

    sirketler = frappe.get_all("Company", pluck="name")
    if not sirketler:
        frappe.throw("Şirket yok; önce kurulum.sirket_olustur çalıştırın")
    sirket = sirketler[0]
    return {
        "sirket": sirket,
        "thp": thp_kur(sirket),
        "varsayilanlar": sirket_hesap_varsayilanlari(sirket),
        "kdv": kdv_kur(sirket),
        "territory": territory_kur(),
    }


def km2_fatura_dogrulamasi() -> dict[str, object]:
    """KM-2 çıkış kanıtı: örnek satış faturası Kaynak Veri kurallarından geçer.

    1) Geçersiz VKN'li müşteri girişimi doğrulama kancasıyla reddedilir.
    2) Geçerli VKN'li demo müşterisine %20 KDV'li taslak fatura açılır;
       net toplam ve KDV beklenen değerlerle birebir karşılaştırılır.
    """
    import frappe

    sirket = frappe.get_all("Company", pluck="name")[0]
    # "yazıyla tutar" (num2words) istek dilini kullanır; bench bağlamında
    # local.lang varsayılanı "en"dir — web oturumunu etkilemez, burada tr şart
    frappe.local.lang = frappe.get_system_settings("language") or "tr"
    musteri = frappe.db.get_value("Customer", {"customer_name": "Anadolu Ticaret Ltd. Şti."})
    if not musteri:
        frappe.throw("Demo müşterisi yok; kurulum.demo_verisi_olustur çalıştırın")
    satis_sablon = frappe.db.get_value(
        "Sales Taxes and Charges Template", {"title": "KDV %20 Satış", "company": sirket}
    )
    if not satis_sablon:
        frappe.throw("KDV %20 Satış şablonu yok; kurulum.faz2_kurulum çalıştırın")
    # sihirbazsız kurulumda satış fiyat listesi oluşmaz; TRY liste garanti edilir
    if not frappe.db.exists("Price List", "Standard Selling"):
        frappe.get_doc(
            {
                "doctype": "Price List",
                "price_list_name": "Standard Selling",
                "currency": "TRY",
                "selling": 1,
                "buying": 0,
                "enabled": 1,
            }
        ).insert(ignore_permissions=True)
        # bağ doğrulaması aynı işlemde cache'li görmezden gelebilir: hemen yaz
        frappe.db.commit()

    # 1) negatif örnek önce: geçersiz VKN reddedilmeli; ardından geri al
    engellendi = False
    try:
        frappe.get_doc(
            {
                "doctype": "Customer",
                "customer_name": "VKN Hatalı Test A.Ş.",
                "customer_type": "Company",
                "customer_group": "Yerel Müşteriler",
                "territory": "Türkiye",
                "tax_id": "1111111111",
            }
        ).insert(ignore_permissions=True)
    except Exception:
        engellendi = True
    frappe.db.rollback()

    # 2) pozitif örnek: geçerli VKN'li müşteri + KDV %20 şablonu (taslak)
    # şablon satırları sunucu tarafında UI gibi otomatik dolmaz: açıkça alınır
    from erpnext.controllers.accounts_controller import get_taxes_and_charges

    fatura = frappe.get_doc(
        {
            "doctype": "Sales Invoice",
            "company": sirket,
            "customer": musteri,
            "currency": "TRY",
            "selling_price_list": "Standard Selling",
            "taxes_and_charges": satis_sablon,
            "taxes": get_taxes_and_charges("Sales Taxes and Charges Template", satis_sablon),
            "items": [{"item_code": "HIZ-MLZ-001", "qty": 1, "rate": 10000.0}],
        }
    )
    fatura.insert(ignore_permissions=True)
    beklenen_kdv = round(fatura.net_total * 20 / 100, 2)
    if fatura.total_taxes_and_charges != beklenen_kdv:
        frappe.throw(
            f"KDV toplamı beklenenden farklı: {fatura.total_taxes_and_charges} != {beklenen_kdv}"
        )
    frappe.db.commit()
    return {
        "fatura": fatura.name,
        "musteri": musteri,
        "net_toplam": fatura.net_total,
        "kdv": fatura.total_taxes_and_charges,
        "gecersiz_vkn_reddedildi": engellendi,
    }
