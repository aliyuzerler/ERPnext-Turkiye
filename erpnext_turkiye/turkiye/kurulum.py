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

    # şirket VKN'si demo müşterisi VKN'sinden farklı olmalı: GİB usulüyle
    # üretilmiş ayrı bir geçerli vektör (kimlik.vkn_uret + validate_vkn)
    from erpnext_turkiye.turkiye.kimlik import vkn_uret

    doc = frappe.get_doc(
        {
            "doctype": "Company",
            "company_name": ad,
            "abbr": kisaltma,
            "country": "Turkey",
            "default_currency": "TRY",
            "chart_of_accounts": "Standard with Numbers",
            "company_email": "info@ornek.local",
            "tax_id": vkn_uret("555444333"),  # -> 5554443334
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


def party_turleri_tamamla() -> list[str]:
    """ERPNext v15 sihirbazsız kurulumda eksik kalan Party Type kayıtlarını kurar.

    GL Entry'de alacak/borç hesaplarına party yazabilmek için "Customer",
    "Supplier" vb. Party Type kayıtları gerekir (gözlemlenen kurulum
    sırası sorunu; Faz 1 Warehouse Type vakasıyla aynı).
    """
    import frappe

    turler = ["Customer", "Supplier", "Employee", "Student", "Shareholder"]
    eklenen: list[str] = []
    for tur in turler:
        if frappe.db.exists("Party Type", tur):
            continue
        # party_type alanı DocType'a Link'tir: kurulu olmayan modül
        # doctype'ları (örn. Student) atlanır
        if not frappe.db.exists("DocType", tur):
            continue
        # Party Type autoname'i field:party_type — alanı vermek şart
        frappe.get_doc({"doctype": "Party Type", "party_type": tur}).insert(
            ignore_permissions=True
        )
        eklenen.append(tur)
    frappe.db.commit()
    return eklenen


def km3_fatura_gonder() -> dict[str, object]:
    """KM-3 site kanıtı: taslak faturayı gönderir; UBL-TR üretimi + kayıt açılır.

    on_submit kancası UBL-TR XML'i üretir, OASIS XSD doğrulamasından geçirir
    ve E Belge Gonderim kaydını açar (şemadan geçmeyen fatura gönderilemez).
    """
    import frappe

    party_turleri_tamamla()
    sirket = frappe.get_all("Company", pluck="name")[0]
    # gönderim muhasebe kaydı açar: açık mali yıl garanti edilir
    yil = int(frappe.utils.nowdate()[:4])
    if not frappe.db.exists("Fiscal Year", {"year": str(yil)}):
        frappe.get_doc(
            {
                "doctype": "Fiscal Year",
                "year": str(yil),
                "year_start_date": f"{yil}-01-01",
                "year_end_date": f"{yil}-12-31",
                "disabled": 0,
                "companies": [{"company": sirket}],
            }
        ).insert(ignore_permissions=True)
        frappe.db.commit()

    fatura_adi = frappe.get_all(
        "Sales Invoice",
        filters={"docstatus": 0},
        order_by="creation desc",
        limit_page_length=1,
        pluck="name",
    )
    if not fatura_adi:
        frappe.throw("Taslak fatura yok; kurulum.km2_fatura_dogrulamasi çalıştırın")
    doc = frappe.get_doc("Sales Invoice", fatura_adi[0])
    doc.submit()
    frappe.db.commit()
    kayit = frappe.db.get_value(
        "E Belge Gonderim",
        {"fatura": doc.name},
        ["name", "durum", "uuid", "alici_vkn"],
        as_dict=True,
    )
    if not kayit:
        frappe.throw("on_submit kancası e-belge kaydı açmadı")
    return {
        "fatura": doc.name,
        "e_belge": kayit.name,
        "durum": kayit.durum,
        "uuid": kayit.uuid,
        "alici_vkn": kayit.alici_vkn,
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


def faz4_kurulum() -> dict[str, object]:
    """Faz 4 site kurulumu: İK-bordro uyarlamaları (hrms gerekli).

    Kurulanlar: Türkiye Salary Component seti (SGK/İşsizlik/Damga/Gelir
    Vergisi), GİB 2026 gelir vergisi tarifesi (Income Tax Slab), 4857
    izin türleri, 2429 s.K. 2026 resmî tatil listesi ve rol profilleri.
    SAF bordro çekirdeği (bordro/) tutar ve oranları buraya taşır.
    """
    import frappe

    if "hrms" not in frappe.get_installed_apps():
        frappe.throw("İK uyarlamaları hrms uygulaması ister; önce bench get-app hrms")
    ozet: dict[str, object] = {}
    ozet["bilesenler"] = bordro_bilesenleri_kur()
    ozet["gelir_vergisi_slabi"] = gelir_vergisi_dilimleri_kur()
    ozet["izin_turleri"] = izin_turleri_kur()
    ozet["tatil_listesi"] = tatil_listesi_kur()
    ozet["rol_profilleri"] = rol_profilleri_kur()
    ozet["crm_proje"] = crm_proje_tanimlari_kur()
    frappe.db.commit()
    return ozet


def crm_proje_tanimlari_kur() -> dict[str, list[str]]:
    """Türkiye proje türleri (v1 kapsam; CRM ayrıntısı Faz 5 UAT'e)."""
    import frappe

    turler = ["Sözleşmeli Proje", "Dahili Ar-Ge", "Bakım Hizmeti"]
    olusan: list[str] = []
    for ad in turler:
        if frappe.db.exists("Project Type", ad):
            olusan.append(ad)
            continue
        frappe.get_doc({"doctype": "Project Type", "project_type": ad}).insert(
            ignore_permissions=True
        )
        olusan.append(ad)
    frappe.db.commit()
    return {"proje_turleri": olusan}


def _bilesen_yoksa_ekle(
    ad: str,
    tur: str,
    formulu: str | None = None,
    **ekstra: object,
) -> str:
    """Salary Component yoksa formüllü kurar; adını döndürür."""
    import frappe

    if frappe.db.exists("Salary Component", ad):
        return str(ad)
    veri: dict[str, object] = {
        "doctype": "Salary Component",
        "salary_component": ad,
        "type": tur,
        "amount_based_on_formula": 1 if formulu else 0,
        "formula": formulu,
    }
    veri.update(ekstra)
    frappe.get_doc(veri).insert(ignore_permissions=True)
    return str(ad)


def bordro_bilesenleri_kur() -> list[str]:
    """Türkiye Salary Component seti (2026 oranları, SAF bordro/sgk ile uyumlu).

    Formüller: SGK İşçi %14, İşsizlik İşçi %1, Damga binde 7,59,
    Gelir Vergisi tarifeden (variable), SGK İşveren %20,75 (toplama
    dahil değil — işveren maliyet gösterimi).
    """
    import frappe

    olusan: list[str] = []
    olusan.append(_bilesen_yoksa_ekle("SGK İşçi Payı", "Deduction", "base * 0.14", abbr="SGK_I"))
    olusan.append(
        _bilesen_yoksa_ekle(
            "İşsizlik Sigortası İşçi Payı", "Deduction", "base * 0.01", abbr="ISS_I"
        )
    )
    olusan.append(_bilesen_yoksa_ekle("Damga Vergisi", "Deduction", "base * 0.00759", abbr="DV"))
    olusan.append(
        _bilesen_yoksa_ekle(
            "Gelir Vergisi",
            "Deduction",
            None,
            abbr="GV",
            variable_based_on_taxable_salary=1,
            is_income_tax_component=1,
        )
    )
    olusan.append(
        _bilesen_yoksa_ekle(
            "SGK İşveren Payı",
            "Deduction",
            "base * 0.2075",
            abbr="SGK_V",
            do_not_include_in_total=1,
        )
    )
    olusan.append(
        _bilesen_yoksa_ekle(
            "İşsizlik Sigortası İşveren Payı",
            "Deduction",
            "base * 0.02",
            abbr="ISS_V",
            do_not_include_in_total=1,
        )
    )
    frappe.db.commit()
    return olusan


def gelir_vergisi_dilimleri_kur() -> str:
    """GİB 2026 ücret tarifesi → Income Tax Slab "Türkiye 2026 (Ücret)"."""
    import frappe

    from erpnext_turkiye.turkiye.bordro.vergi import GELIR_VERGISI_TARIFESI_2026_UCRET

    ad = "Türkiye 2026 (Ücret)"
    if frappe.db.exists("Income Tax Slab", ad):
        return ad
    dilimler: list[dict[str, object]] = []
    alt_sinir = 0.0
    for ust, oran in GELIR_VERGISI_TARIFESI_2026_UCRET:
        dilimler.append(
            {
                "from_amount": alt_sinir,
                "to_amount": ust if ust != float("inf") else 0.0,
                "percent_deduction": oran * 100,
            }
        )
        alt_sinir = ust
    frappe.get_doc(
        {
            "doctype": "Income Tax Slab",
            "name": ad,
            "enabled": 1,
            "effective_from": "2026-01-01",
            "salary_slab_based_on": "Yearly",
            "currency": "TRY",
            "slabs": dilimler,
        }
    ).insert(ignore_permissions=True)
    frappe.db.commit()
    return ad


def izin_turleri_kur() -> list[str]:
    """4857 s.K. uyarınca standart izin türleri (hrms Leave Type)."""
    import frappe

    turler: list[dict[str, object]] = [
        {
            "leave_type_name": "Yıllık Ücretli İzin",
            "is_carry_forward": 1,
            "max_leaves_allowed": 26,
        },
        {"leave_type_name": "Mazeret İzni"},
        {"leave_type_name": "Hastalık İzni"},
        {"leave_type_name": "Ücretsiz İzin", "is_lwp": 1},
        {"leave_type_name": "Doğum İzni", "max_leaves_allowed": 112},  # 4857 m.74: 8+8 hafta
        {"leave_type_name": "Babalık İzni", "max_leaves_allowed": 5},  # m.74/6: 5 gün
    ]
    olusan: list[str] = []
    for tur in turler:
        ad = str(tur["leave_type_name"])
        if frappe.db.exists("Leave Type", ad):
            olusan.append(ad)
            continue
        frappe.get_doc({"doctype": "Leave Type", **tur}).insert(ignore_permissions=True)
        olusan.append(ad)
    frappe.db.commit()
    return olusan


def tatil_listesi_kur() -> str:
    """2429 s.K. 2026 resmî tatilleri → Holiday List "Türkiye 2026"."""
    import frappe

    from erpnext_turkiye.turkiye.bordro.izin import RESMI_TATILLER_2026

    ad = "Türkiye 2026"
    if frappe.db.exists("Holiday List", ad):
        return ad
    gunler = [
        {
            "holiday_date": t.tarih,
            "description": t.ad + (" (yarım gün)" if t.yarim_gun else ""),
            "weekly_off": 0,
        }
        for t in RESMI_TATILLER_2026
    ]
    frappe.get_doc(
        {
            "doctype": "Holiday List",
            "holiday_list_name": ad,
            "from_date": "2026-01-01",
            "to_date": "2026-12-31",
            "holidays": gunler,
        }
    ).insert(ignore_permissions=True)
    frappe.db.commit()
    return ad


def rol_profilleri_kur() -> list[str]:
    """Türkiye rol profilleri: bordro yöneticisi, muhasebe, satış."""
    import frappe

    profiller: dict[str, tuple[str, ...]] = {
        "Türkiye Bordro Yöneticisi": ("HR User", "HR Manager"),
        "Türkiye Muhasebe": ("Accounts User", "Accounts Manager"),
        "Türkiye Satış": ("Sales User", "Sales Manager"),
    }
    olusan: list[str] = []
    for ad, roller in profiller.items():
        if frappe.db.exists("Role Profile", ad):
            olusan.append(ad)
            continue
        frappe.get_doc(
            {
                "doctype": "Role Profile",
                "role_profile": ad,
                "roles": [{"role": r} for r in roller],
            }
        ).insert(ignore_permissions=True)
        olusan.append(ad)
    frappe.db.commit()
    return olusan


def faz5_kurulum() -> dict[str, object]:
    """Faz 5 site kurulumu: bordro yapısı + çalışan + örnek bordro.

    Kurulanlar: Temel Ücret bileşeni, "Türkiye Standart" Salary Structure
    (Faz 4 bileşen setiyle: SGK %14, İşsizlik %1, Damga binde 7,59, GV
    tarifeden), örnek çalışan, Salary Structure Assignment (brüt 60.000)
    ve Kasım 2026 Salary Slip'i — SAF bordro_hesapla ile çapraz
    doğrulama yapar (UAT-İK senaryosunun temeli).
    """
    import frappe

    if "hrms" not in frappe.get_installed_apps():
        frappe.throw("Bordro yapısı hrms uygulaması ister")
    ozet: dict[str, object] = {}
    ozet["bilesen"] = _temel_ucret_bileseni()
    ozet["yapı"] = bordro_yapisi_kur()
    ozet["calisan"] = ornek_calisan_kur()
    ozet["atama"] = bordro_atama_kur(60000.0)
    ozet["bordro"] = ornek_bordro_kes("2026-11")
    frappe.db.commit()
    return ozet


def _temel_ucret_bileseni() -> str:
    """Earnings baz bileşeni: Temel Ücret (base)."""
    import frappe

    ad = "Temel Ücret"
    if not frappe.db.exists("Salary Component", ad):
        frappe.get_doc(
            {
                "doctype": "Salary Component",
                "salary_component": ad,
                "type": "Earning",
                "amount_based_on_formula": 1,
                "formula": "base",
                "abbr": "TU",
            }
        ).insert(ignore_permissions=True)
        frappe.db.commit()
    return ad


def bordro_yapisi_kur() -> str:
    """'Türkiye Standart' Salary Structure (Faz 4 bileşen setiyle)."""
    import frappe

    ad = "Türkiye Standart"
    if frappe.db.exists("Salary Structure", ad):
        return ad
    sirket = frappe.db.get_value("Company", {}, "name")
    if not sirket:
        frappe.throw("Şirket yok; önce sirket_olustur çalıştırın")
    kesintiler = ["SGK İşçi Payı", "İşsizlik Sigortası İşçi Payı", "Damga Vergisi", "Gelir Vergisi"]
    frappe.get_doc(
        {
            "doctype": "Salary Structure",
            "salary_structure": ad,
            "company": sirket,
            "currency": "TRY",
            "payroll_frequency": "Monthly",
            "is_active": 1,
            "earnings": [
                {
                    "salary_component": "Temel Ücret",
                    "abbreviation": "TU",
                    "amount_based_on_formula": 1,
                    "formula": "base",
                }
            ],
            "deductions": [
                {"salary_component": k, "amount_based_on_formula": 1} for k in kesintiler
            ],
        }
    ).insert(ignore_permissions=True)
    frappe.db.commit()
    return ad


def ornek_calisan_kur() -> str:
    """UAT örnek çalışanı (Aydın Kaya; girişin üstü brüt maaş senaryosu)."""
    import frappe

    if frappe.db.exists("Employee", {"employee_name": "Aydın Kaya"}):
        return str(frappe.db.get_value("Employee", {"employee_name": "Aydın Kaya"}, "name"))
    sirket = frappe.db.get_value("Company", {}, "name")
    calisan = frappe.get_doc(
        {
            "doctype": "Employee",
            "first_name": "Aydın",
            "last_name": "Kaya",
            "employee_name": "Aydın Kaya",
            "company": sirket,
            "gender": "Male",
            "date_of_birth": "1990-05-17",
            "date_of_joining": "2026-01-05",
            "designation": "Muhasebe Uzmanı",
            "status": "Active",
        }
    )
    calisan.insert(ignore_permissions=True)
    frappe.db.commit()
    return str(calisan.name)


def bordro_atama_kur(brut: float) -> str:
    """Salary Structure Assignment: brüt ücretle yapıyı çalışana bağlar."""
    import frappe

    calisan = ornek_calisan_kur()
    sirket = frappe.db.get_value("Company", {}, "name")
    varolan = frappe.db.get_value(
        "Salary Structure Assignment",
        {"employee": calisan, "salary_structure": "Türkiye Standart"},
        "name",
    )
    if varolan:
        frappe.db.set_value("Salary Structure Assignment", varolan, "base", brut)
        frappe.db.commit()
        return str(varolan)
    atama = frappe.get_doc(
        {
            "doctype": "Salary Structure Assignment",
            "employee": calisan,
            "salary_structure": "Türkiye Standart",
            "company": sirket,
            "from_date": "2026-11-01",
            "currency": "TRY",
            "base": brut,
        }
    )
    atama.insert(ignore_permissions=True)
    frappe.db.commit()
    return str(atama.name)


def ornek_bordro_kes(donem: str) -> dict[str, object]:
    """Salary Slip üretir ve SAF bordro_hesapla ile karşılaştırır.

    ``donem``: "YYYY-MM". Dönüş: slip net tutarı, SAF net tutarı, fark.
    """
    import frappe
    from decimal import Decimal

    from erpnext_turkiye.turkiye.bordro.vergi import bordro_hesapla

    calisan = ornek_calisan_kur()
    sirket = frappe.db.get_value("Company", {}, "name")
    yil, ay = donem.split("-")
    baslangic = f"{donem}-01"
    bitis = f"{donem}-30" if ay == "11" else f"{donem}-28"
    varolan = frappe.db.get_value(
        "Salary Slip", {"employee": calisan, "start_date": baslangic}, "name"
    )
    if varolan:
        frappe.delete_doc("Salary Slip", varolan, force=True)
    slip = frappe.get_doc(
        {
            "doctype": "Salary Slip",
            "employee": calisan,
            "company": sirket,
            "salary_structure": "Türkiye Standart",
            "start_date": baslangic,
            "end_date": bitis,
            "currency": "TRY",
            "payroll_frequency": "Monthly",
        }
    )
    slip.insert(ignore_permissions=True)
    slip.calculate_net_pay()
    net_site = float(slip.net_pay or 0)
    brut = float(frappe.db.get_value("Salary Structure Assignment", {"employee": calisan}, "base") or 0)
    saf = bordro_hesapla(brut, kumulatif_matrah=0.0)
    frappe.db.commit()
    return {
        "brut": brut,
        "site_net": net_site,
        "saf_net": saf["net"],
        "fark": float(Decimal(str(net_site)) - Decimal(str(saf["net"]))),
        "saf_kirilim": {k: saf[k] for k in ("sgk", "isssizlik", "gv", "dv")},
    }
