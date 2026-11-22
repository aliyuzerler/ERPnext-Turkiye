"""ERPNext Türkiye uygulama kancaları (hooks).

Frappe dokümantasyonu: https://docs.frappe.io/framework/user/en/dynamic-links
Faz 0 kapsamı: Kaynak Veri katmanının ilk kuralı — Customer/Supplier.tax_id
alanına TCKN/VKN doğrulaması bağlanır (Faz 2'de genişletilir).
"""

app_name = "erpnext_turkiye"
app_title = "ERPNext Türkiye"
app_publisher = "aliyuzerler"
app_description = "Türkiye lokalizasyonu: e-belge, TCMB kur servisi, THP, TCKN/VKN doğrulama"
app_license = "mit"
required_apps = ["erpnext"]

# Kaynak Veri katmanı: ana veri doğrulama kuralları (Tablo 3 / Bölüm 5, Faz 2)
doc_events = {
    "Customer": {
        "validate": "erpnext_turkiye.turkiye.frappe_olaylari.validate_tax_id",
    },
    "Supplier": {
        "validate": "erpnext_turkiye.turkiye.frappe_olaylari.validate_tax_id",
    },
}

# TCMB kur servisi: günlük otomatik çekim Faz 2'de devreye alınır.
# scheduler_events = {
#     "daily": ["erpnext_turkiye.turkiye.kur_servisi.gunluk_kur_coz"],
# }
