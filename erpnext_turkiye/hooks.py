"""ERPNext Türkiye uygulama kancaları (hooks).

Frappe dokümantasyonu: https://docs.frappe.io/framework/user/en/dynamic-links
Kaynak Veri katmanı: Customer/Supplier/Company.tax_id alanlarına TCKN/VKN
doğrulaması bağlanır (Faz 2: tüm ana veri DocType'ları).
"""

app_name = "erpnext_turkiye"
app_title = "ERPNext Türkiye"
app_publisher = "aliyuzerler"
app_description = "Türkiye lokalizasyonu: e-belge, TCMB kur servisi, THP, TCKN/VKN doğrulama"
app_license = "mit"
required_apps = ["erpnext"]

# Kaynak Veri katmanı: ana veri doğrulama kuralları (Tablo 3 / Bölüm 5)
# e-Dönüşüm: satış faturası on_submit -> UBL-TR üretimi + şema doğrulaması (KM-3)
doc_events = {
    "Customer": {
        "validate": "erpnext_turkiye.turkiye.frappe_olaylari.validate_tax_id",
    },
    "Supplier": {
        "validate": "erpnext_turkiye.turkiye.frappe_olaylari.validate_tax_id",
    },
    "Company": {
        "validate": "erpnext_turkiye.turkiye.frappe_olaylari.validate_tax_id",
    },
    "Sales Invoice": {
        "on_submit": "erpnext_turkiye.turkiye.ebelge.olaylari.fatura_gonderim_kaydet",
        "on_cancel": "erpnext_turkiye.turkiye.ebelge.olaylari.gonderim_iptal",
    },
}

# TCMB kur servisi: her gün bülteni çekip Currency Exchange kayıtlarını günceller
scheduler_events = {
    "daily": ["erpnext_turkiye.turkiye.kur_servisi.gunluk_kur_coz"],
}
