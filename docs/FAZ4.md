# Faz 4 — İK-Bordro ve Kalan Modüller (Çekirdek Tamamlandı)

**Tarih:** 23 Kasım 2026 · **Durum:** ✅ SAF bordro çekirdeği + site uyarlamaları
**Kalite kapısı:** `make phase-gate` yeşil (**64** birim test, faz3'te 53 idi)
**Not:** Bu fazda ROADMAP'te ayrı KM çıkış kriteri yoktur (KM-4 Faz 5 UAT'tadır).

## 1. Kaynak tablosu — tüm rakamlar resmî kaynaklardan birebir

| Parametre | Değer (2026) | Kaynak |
| --- | --- | --- |
| Brüt asgari ücret | 33.030,00 TL/ay (günlük 1.101,00) | ÇSGB resmî sayfası (csgb.gov.tr/poco-pages/asgari-ucret) |
| SGK işçi payı | %14 → 4.624,20 TL | ÇSGB tablosu; 5510 s.K. m. 82 |
| İşsizlik sig. işçi | %1 → 330,30 TL | ÇSGB tablosu |
| Kesintiler toplamı / net | 4.954,50 / 28.075,50 TL | ÇSGB tablosu (GV+DV asgari ücrette tam muafiyet) |
| SGK işveren payı | baz %20,75; ÇSGB senaryoları %21,75 (indirimsiz+ek 1 puan) / %19,75 / %16,75 → 7.184,03 / 6.523,43 / 5.532,53 TL | ÇSGB tablosu; 5510 geçici m. 10 (5 puan); 7463 s.K. (ek prim) |
| İşsizlik sig. işveren | %2 → 660,60 TL | ÇSGB tablosu |
| Gelir vergisi tarifesi (ücret) | 190.000'e kadar %15 → 400.000'e %20 (28.500) → 1.500.000'e %27 (367.500) → 5.300.000'e %35 (1.697.500) → %40 | GİB resmî PDF (gelir-vergisi-tarifesi-2026) |
| Damga vergisi | binde 7,59 | 488 s.K.; 2026 ücret oranları |
| Yıllık izin | 1 yıl→14; 5 yıl→20; 15 yıl→26; 18 yaş altı/öğrenim→20 | 4857 s.K. m. 53 |
| Resmî tatiller 2026 | 15,5 gün (Ramazan 3+arife; Kurban 4+arife; 28 Ekim 13.00'ten sonra yarım) | 2429 s.K.; 2026 takvim |

Kanıt: `tests/test_bordro.py` ÇSGB tablosunun **her tutarını** hesaptan yeniden
üreterek birebir karşılaştırır (`asgari_tablo_dogrula`).

## 2. SAF bordro çekirdeği — `turkiye/bordro/`

- `sgk.py` — işçi kesintileri + işveren maliyeti (üç senaryo), yarım-yukarı
  (half-up) bordro yuvarlaması, `asgari_tablo_dogrula` (ÇSGB ile birebir).
- `vergi.py` — GİB 2026 ücret tarifesi, **kümülatif bordro usulü**
  (ay vergisi = yıllık(kümülatif+ay) − yıllık(kümülatif)), damga vergisi,
  asgari ücret GV+DV tam muafiyeti; `bordro_hesapla(brüt, kümülatif)`.
- `izin.py` — 4857 yıllık izin süreleri + 2429 s.K. 2026 resmî tatilleri.

Örnek (testten): brüt 60.000 TL, 1. ay → SGK 8.400,00 + İşsizlik 600,00 +
GV 7.650,00 (matrah 51.000 × %15) + Damga 455,40 → **net 42.894,60**.
İkinci ayda kümülatif 102.000 olduğundan ay vergisi yine 7.650,00.

## 3. Site uyarlamaları — `kurulum.faz4_kurulum()` (hrms ister)

`bench get-app hrms` sonrası tek komutla kurulur:

| Kurulum | İçerik |
| --- | --- |
| `bordro_bilesenleri_kur` | Salary Component: SGK İşçi Payı (%14), İşsizlik İşçi (%1), Damga Vergisi (binde 7,59), Gelir Vergisi (tarifeden — `variable_based_on_taxable_salary`), SGK İşveren Payı (%20,75, toplama dahil değil), İşsizlik İşveren (%2, dahil değil) |
| `gelir_vergisi_dilimleri_kur` | Income Tax Slab "Türkiye 2026 (Ücret)" — GİB tarifesi 5 dilim (SAF sabitinden döker) |
| `izin_turleri_kur` | Yıllık Ücretli İzin (devri + max 26), Mazeret, Hastalık, Ücretsiz (LWP), Doğum (112 gün — 4857 m.74), Babalık (5 gün — m.74/6) |
| `tatil_listesi_kur` | Holiday List "Türkiye 2026" — 17 satır (15,5 gün; yarım günler açıklamada) |
| `rol_profilleri_kur` | Role Profile: Türkiye Bordro Yöneticisi (HR User/Manager), Türkiye Muhasebe (Accounts User/Manager), Türkiye Satış (Sales User/Manager) |
| `crm_proje_tanimlari_kur` | Project Type: Sözleşmeli Proje, Dahili Ar-Ge, Bakım Hizmeti (CRM ayrıntısı Faz 5 UAT kapsamı) |

## 4. Rol matrisi ve yetkilendirme

| Rol profili | Standart roller | Kapsam |
| --- | --- | --- |
| Türkiye Bordro Yöneticisi | HR User, HR Manager | Bordro/izin/özlük işlemleri; hrms raporları |
| Türkiye Muhasebe | Accounts User, Accounts Manager | Fatura-KDV-THP, e-belge kayıtları |
| Türkiye Satış | Sales User, Sales Manager | Satış ve müşteri süreçleri |

Doctype düzeyi izinler Faz 1'den beri tek tek ayarlıdır (E Belge Gonderim:
System Manager + Accounts User). Kullanıcıya profil atamak:
`Kullanıcı → Role Profile` alanı; izinler frappe Role Profile mekanizmasıyla
kalıtılır.

## 5. Ortam notu — yığın yeniden kurulumu

Sandbox geri dönüşümü yerel yığını (venv, site, MariaDB veri dizini) temizledi;
**kod uzakta güvende** olduğundan kurtarma tamamen GitHub klonu + `scripts/
yigin_yeniden_kur.sh` ile yapıldı: MariaDB 10.6 bintar (TCP 3306, root/admin,
devam-etmeli indirme), redis (cache 11311 / queue 11000), `bench init` (frappe
version-15), get-app erpnext + **hrms** + erpnext_turkiye, site `turkiye.local`.
Faz 1-3 site verisi kurulum fonksiyonlarıyla (kod-dan) yeniden üretilir:
`site_tr_ayarlari → sirket_olustur → demo_verisi_olustur → faz2_kurulum →
km2_fatura_dogrulamasi → km3_fatura_gonder → faz4_kurulum`.

## 6. Bilinen notlar

- Bordro v1: brüt→net döngüsü ve bileşen seti SAF+site ile tutarlı; hrms
  Salary Structure assignment/işletme senaryoları (SGK indirim koşulları,
  nakit ücret istisnaları) Faz 5 UAT'ta gerçek bordro senaryolarıyla sınanır.
- GV bordro hesabı hrms'in Income Tax Slab mekanizmasına dökülmüştür;
  kesinti içi istisnalar (özel avantajlar) ayrı bileşen olarak eklenir.
- CI notu: `26c1473` push'unda mypy kapısı gerçek hatayı yakaladı
  (Decimal→float dönüşümü); `a11211c` ile düzeltildi — kapı çalışıyor.
