# Faz 2 — Türkiye Lokalizasyon Paketi (Tamamlandı)

**Tarih:** 23 Kasım 2026 · **Durum:** ✅ Tamamlandı · **Çıkış kriteri (KM-2):** ✅
**Kalite kapısı:** `make phase-gate` yeşil (lint + typecheck + 39 birim test + 3 e2e)
**Site duman testleri:** Faz 2 seti **11/11 PASS**

Faz 2, ROADMAP.md'de tanımlı "Türkiye Lokalizasyon Paketi"nin tamamını kurar:
THP tam hesap planı, KDV setleri, TCKN/VKN doğrulamasının tüm ana veri
DocType'larına bağlanması, TCMB kur servisinin günlük zamanlayıcıyla devreye
alınması ve il/ilçe veri yapısı. Tüm kurulum idempotenttir
(`kurulum.faz2_kurulum` tek komutla yeniden çalıştırılabilir).

---

## 1. Tek Düzen Hesap Planı (THP tam set)

### Veri kaynakları ve çapraz doğrulama

Hesap kodları ve adları hafızadan değil, iki bağımsız kaynaktan çıkarılıp
çapraz doğrulanarak yazıldı (`scripts/thp_cikar.py`, `scripts/thp_uret.py`):

| Kaynak                                                                                                            | İçerik                               | Sonuç     |
| ----------------------------------------------------------------------------------------------------------------- | ------------------------------------ | --------- |
| [vergiburosu.com — Tekdüzen Hesap Planı](https://www.vergiburosu.com/pratik-bilgiler/tekduzen-hesap-plani)        | VUK 1 No.lu Genel Tebliği planı      | 333 hesap |
| [İSMMMO — Hesap Planı Açıklamaları (PDF)](https://www.ismmmo.org.tr/dosya/415/Mevzuat-Dosya/tekduzhesapplani.pdf) | Numaralı hesap listesi + açıklamalar | 341 hesap |

- **332 kod iki kaynakta birebir aynıdır**; isim farkları yazım biçimi
  düzeyindedir (büyük/küçük harf, boşluk) ve Türkçe büyük/küçük harf
  kurallarıyla (İ/I dönüşümü korunarak) tek biçime getirildi.
- İSMMMO'da fazladan bulunan 7 hesap (178, 350, 358, 339, 439, 502, 503) eklendi.
- İSMMMO gövde/başlık numaralandırması 23x aralığında çelişkili olduğundan
  238 "Şüpheli Diğer Alacaklar" iki bağımsız kaynakla doğrulanamadı ve sete
  alınmadı (belgelenmiş istisna).
- 8 Serbest Hesaplar ve 9 Nazım Hesaplar grupları ERPNext kök türü alamayacağı
  için tohum setinde yoktur.
- 6 Gelir Tablosu grubu ERPNext'te fiziksel grup değildir: gelir çocukları
  (600, 601, 602, 640-649, 671, 679) Income köküne, gider çocukları
  (610-612, 620-623, 630-632, 653-659, 660-661, 680-689, 690-698) Expense
  köküne bağlanır. 7 Maliyet grubu ortak bağlantı setiyle yüklenir.

**Set istatistikleri:** 338 hesap (65 grup + 273 yaprak); `thp_dogrula()` temiz.
Siteye **337 hesap** yüklendi (338 − köksüz "6" grubu).

### ERPNext eşlemeleri

Kritik hesaplar `account_type` ile işaretlendi (Asset modülü, mutabakat ve
KDV otomasyonları bu tipleri ister): 100 Cash, 102 Bank, 120 Receivable,
320 Payable, 150-153/157 Stock, 190-193/291/292/360/361/391/392/492 Tax,
257 Accumulated Depreciation, 258 Capital Work in Progress, 796 Depreciation.

### Şirket varsayılan hesapları (12 alan)

`hesap_plani.sirket_hesap_varsayilanlari` şirketi THP'ye bağladı —
"Anadolu Makine Sanayi A.Ş." için: 120 Alıcılar (alacak), 320 Satıcılar
(borç), 100 Kasa, 102 Bankalar, 600 Yurt İçi Satışlar, 621 Satılan Ticari
Mallar Maliyeti, 689 (write-off), 646 Kambiyo Kârları (kur farkı — zararlar
656'ya dönem sonunda aktarılabilir), 258 (CWIP), 257 (birikmiş amortisman),
796 (amortisman gideri). Alan ERPNext sürümünde yoksa sessizce atlanır.

---

## 2. KDV setleri

`kdv.kdv_kur(sirket)` dokuz şablon kurdu (idempotent; docname'ler
"başlık - AMS" biçiminde olduğu için başlık+şirket araması kullanılır):

- **Satış** (391 Hesaplanan KDV): KDV %1/%10/%20 Satış — %20 varsayılan
- **Alış** (191 İndirilecek KDV): KDV %1/%10/%20 Alış — %20 varsayılan
- **Kalem vergi şablonları**: KDV %1/%10/%20 (satış yönü 391'e işler)

**Tevkifat:** çekirdek `tevkifat_hesapla(matrah, oran, pay, payda)` Faz 0'dan
beri SAF'tır; Faz 2'de site tarafı eklendi — `tevkifat_kategorisi_olustur(pay,
payda, oran)` ERPNext TDS mekanizmasıyla **Tax Withholding Category** kurar
(v15 şeması: `rates` + `accounts` iki zorunlu alt tablo; tarih aralığı geniş
verilir). Örnek kurulum: **KDV Tevkifatı 9/10 (%20)** → tax_withholding_rate
18.0, hesap 360 Ödenecek Vergi ve Fonlar. Resmî GİB tevkifat kod kataloğu
UBL-TR eşleme paketiyle Faz 3'te eklenir (kod listesi hafızadan yazılmaz).

---

## 3. TCKN/VKN doğrulaması — tüm ana veri DocType'ları

`hooks.doc_events` artık üç DocType'a bağlıdır: **Customer**, **Supplier**,
**Company** (`frappe_olaylari.validate_tax_id`).

- Customer/Supplier: 11 hane TCKN **veya** 10 hane VKN (GİB algoritmaları,
  `kimlik.py` — sitesiz birim testli).
- Company: tüzel kişi olduğundan **yalnızca 10 haneli VKN kabul edilir**;
  ayrı hata mesajı verir. (Şahıs şirketlerinin GİB VKN'leri de VKN
  algoritmasından geçer.)

---

## 4. TCMB kur servisi — canlı devrede

- **Kaynak:** `https://www.tcmb.gov.tr/kurlar/today.xml` (günlük bülten XML'i)
- **Kullanılan kur:** TCMB döviz alış kuru (`ForexBuying`) — VUK 313'te döviz
  çeviriminde günlük döviz alış kuru referans alınır.
- **Sağlamlık:** bülten içinde yalnızca çapraz kuru olan kayıtlar boş
  `ForexBuying/ForexSelling` gelir; ayrıştırıcı bunları atlar (canlı bülten
  üzerinde bulunan gerçek bir uç durumu; fixture testi eklendi).
- **Currency Exchange:** her kod için çift yönlü kayıt (kod→TRY ve TRY→kod)
  yazılır/güncellenir; ERPNext `get_exchange_rate` iki yönü de okur.
- **Zamanlayıcı:** `hooks.scheduler_events.daily` →
  `kur_servisi.gunluk_kur_coz` (ağ hatasında siteyi kilitlemez; hata günlüğe
  yazılır). `bench start` çalışırken otomatik tetiklenir.

**Canlı çekim sonucu (23.11.2026):** USD 50.4028 · EUR 55.2974 · GBP 65.9363
→ 6 çift yönlü Currency Exchange kaydı doğrulandı.

---

## 5. İl/ilçe veri yapısı

- **Kaynak:** [volkansenturk/turkiye-iller-ilceler](https://github.com/volkansenturk/turkiye-iller-ilceler)
  (il.json + ilce.json). Veri setindeki KKTC kayıtları (plaka 501-503)
  filtrelenir; **81 il / 973 ilçe** kalır — İstanbul 39, Ankara 25, İzmir 30
  (güncel idari sayımlarla birebir; testlerde sabitlenir).
- Adlar Türkçe büyük/küçük harf kurallarıyla yazılır (İ/I korunur,
  "ve/ile" bağlaçları küçük kalır, KDV gibi kısaltmalar büyük).
- **Territory ağacı:** `yerlesim.territory_kur()` — Türkiye > 81 il > 973
  ilçe = **1054 kayıt** oluşturuldu. İlçe adları iller arası çakışabilen
  adlar için `<ilçe> (<il>)` biçiminde yazılır (ör. Gölbaşı (Ankara)).
- Faz 1'de yapraksız kalan "Türkiye" territory'si gruba çevrildi.

---

## 6. KM-2 çıkış kanıtı: örnek fatura doğrulama kurallarından geçer

`kurulum.km2_fatura_dogrulamasi()` iki yönlü kanıt üretir:

| Kanıt                                                           | Sonuç                                                                                                              |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Geçersiz VKN (1111111111) ile müşteri girişimi                  | ✅ doğrulama kancasıyla reddedildi                                                                                 |
| Geçerli VKN'li müşteri (Anadolu Ticaret Ltd. Şti. — 3456789014) | ✅ kabul                                                                                                           |
| Taslak satış faturası: 10.000 TL × KDV %20 Satış şablonu        | ✅ **ACC-SINV-2026-00002** — net 10.000,00 TL, **KDV 2.000,00 TL** (391 Hesaplanan KDV), genel toplam 12.000,00 TL |
| Toplamlar beklenenle birebir                                    | ✅ `total_taxes_and_charges == 2000.0`                                                                             |

Kurulum sırasında giderilen pürüzler (belgelendirme amacıyla kayıtlı):
şablon docname'leri `{başlık} - {şirket kısaltması}` biçiminde üretilir
(başlık+şirket aramasına geçildi); şablon vergi satırları sunucu tarafında
otomatik dolmaz (`erpnext.controllers.accounts_controller.get_taxes_and_charges`
ile açıkça alınır); sihirbazsız kurulumda "Standard Selling" fiyat listesi
oluşmaz (km2 garanti eder); bench (istek dışı) bağlamında `frappe.local.lang`
"en" varsayılandır ve "yazıyla tutar" Türkçe yazılması için
`frappe.local.lang` tr'ye çekilir + Administrator kullanıcısının dili tr
yapılır.

---

## 7. Kalite kapısı ve duman testleri

- `make phase-gate` **yeşil**: ruff + eslint + prettier, mypy (21 kaynak
  dosya), **39 pytest** (Faz 1'de 27 idi: THP seti 12 + il/ilçe 5 yeni test),
  Playwright e2e 3/3 (fixture tabanlı; site gerekmez).
- Faz 2 duman testleri `scripts/site_goruntu_faz2.mjs` — **11/11 PASS**:
  THP ağacı (1 Dönen Varlıklar > 10 Hazır Değerler > 100 Kasa; 19 grubunda
  190 Devreden KDV, 191 İndirilecek KDV), KM-2 faturası (KDV %20 satırı,
  geçerli VKN), Territory ağacı (Türkiye > Ankara > Çankaya), kur listesi
  (USD/EUR), KDV şablonları (%1/%20 Satış).
- mypy: frappe/erpnext bench çalışma zamanı tarafından sağlandığından
  `pyproject.toml` override'ı iki paketi de kapsar.

## 8. Ekran görüntüleri (docs/ekran-goruntuleri/)

| Dosya                      | İçerik                                                         |
| -------------------------- | -------------------------------------------------------------- |
| `07-hesap-plani-thp.png`   | Hesap Planı ağacı: THP grupları ve KDV hesapları               |
| `08-ornek-fatura-kdv.png`  | KM-2 faturası: KDV %20 satırı, 391 hesabı, Türkçe tutar yazımı |
| `09-territory-il-ilce.png` | Territory ağacı: Türkiye > il > ilçe                           |
| `10-tcmb-kur-listesi.png`  | Currency Exchange: çift yönlü canlı TCMB kurları               |
| `11-kdv-sablonlari.png`    | Satış vergi şablonları: KDV %1/%10/%20 Satış                   |

## 9. Ortam ve sürüm pinleri

| Bileşen            | Sürüm    | Pin                                                 |
| ------------------ | -------- | --------------------------------------------------- |
| Frappe             | 15.127.1 | dal `version-15`, commit `0f31ab0`                  |
| ERPNext            | 15.126.0 | dal `version-15`, commit `a6f54f9`                  |
| MariaDB            | 10.6.18  | kullanıcı seviyesi yığın (`scripts/mariadb_kur.sh`) |
| Redis              | 8.0.2    | 11000 (cache) / 13000 (queue)                       |
| Python (bench env) | 3.12     | bench env; uygulama Python >= 3.10 hedefli          |

Sandbox notları: `bench start`'ın honcho ağacı bu ortamda arka planda
hayatta kalmadığından web sunucusu tek süreç olarak
`scripts/site_web.py` (frappe.app.serve) ile ayakta tutulur; site bağlamlı
komutlar için `scripts/site_komut.py <module.fn>` (bench env python'u ile,
host venv gölgesi olmadan) kullanılır.

## 10. Yeniden kurulum (tekrarlanabilirlik)

Faz 1 adımlarından sonra:

```bash
bench --site turkiye.local execute erpnext_turkiye.turkiye.kurulum.faz2_kurulum
# THP tam seti + şirket varsayılanları + KDV setleri + Territory ağacı

bench --site turkiye.local execute erpnext_turkiye.turkiye.kur_servisi.kur_guncelle
# TCMB bültenini çekip Currency Exchange kayıtlarını günceller

bench --site turkiye.local execute erpnext_turkiye.turkiye.kurulum.km2_fatura_dogrulamasi
# KM-2 kanıt faturası (taslak) ve geçersiz VKN reddi

node scripts/site_goruntu_faz2.mjs http://127.0.0.1:8000   # görüntüler + duman testleri
```

## 11. Bilinen notlar ve istisnalar

- THP 238 "Şüpheli Diğer Alacaklar" kaynak çelişkisi nedeniyle sette yok;
  teyit kaynağı bulunursa `scripts/thp_uret.py` üzerinden eklenebilir.
- Kambiyo kâr/zararı ERPNext tek alandadır (646); e-defter kapanışında
  zararlar 656'ya aktarılabilir — Faz 3 e-Defter modülünde otomatikleştirilir.
- Tevkifat kategorileri parametriktir; resmî GİB tevkifat kod kataloğu
  (601 vb.) Faz 3 UBL-TR paketinde gelir.
- num2words Türkçe çıktısı title-case sonrası "Onikibin" gibi bitişik yazım
  üretebilir (frappe `money_in_words` .title() davranışı); Faz 3 e-belge
  yazı alanında UBL-TR metin üretimiyle ele alınır.
- Zamanlayıcı, `bench start` süreçleri çalışırken tetiklenir; sandbox
  recycle'ları sonrası `scripts/site_web.py` + redis/mariadb betikleriyle
  yeniden başlatılır.
