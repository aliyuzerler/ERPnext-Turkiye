# Faz 5 — UAT, Eğitim ve Canlıya Alma Hazırlığı

**Durum: tamamlandı.** KM-4 çıkış kanıtı: 15/15 senaryo PASS (bu belgenin 3. bölümü). Bu belge; e-Defter BG/YB kapsam sınırlarını, UAT raporunu,
performans duman testini, geri alma planını ve kontrollü canlıya alma
kontrol listesini içerir.

## 1. Kapsam ve kapsam dışı

**Bu fazda tamamlananlar:** e-Defter çekirdeği (XBRL-GL yevmiye üretimi,
kebir özeti, berat, ZIP paketleme + arşivleme; 7 yeni SAF testi), site
bordro yapısı (Türkiye Standart + çalışan + SAF çapraz doğrulama), KM-4
UAT koşucusu (5 süreç, 15 senaryo), kullanıcı eğitim rehberi
(`docs/EGITIM.md` + `download/ERPNext_Turkiye_Kullanici_Rehberi.docx|.pdf`).

**Kapsam dışı (entegratör/pilot işlevi):** GİB/MB zaman damgası (beratın
`zamanDamgasi` alanı boş bırakıldı), GİB e-Defter portal yükleme ve
şematron kontrolü, gerçek e-Fatura entegratör iletimi (kuyruk simülasyonu),
gerçek iş birimi imzalı UAT onayı (bkz. bölüm 5 onay formu).

## 2. e-Defter BG/YB

GİB e-Defter Uygulama Kılavuzu uyarınca defterler **XBRL-GL taksonomisiyle**
üretilir (gl-cor 2006-10-25; entriesHeader / entryHeader / entryDetail).
Modül: `erpnext_turkiye/turkiye/edefter/` (SAF Python, sitesiz çalışır).

Kılavuz kuralları sınanır (tests/test_edefter.py):

| Kural                                        | Uygulama                                                            |
| -------------------------------------------- | ------------------------------------------------------------------- |
| Her yevmiye maddesi borç = alacak            | `YevmiyeKayit.dengeli_mi`; dengesiz madde `ValueError`              |
| Yevmiye ve kebir için ayrı berat             | `yevmiye_berat()` + `kebir_berat()`                                 |
| ZIP paketi iki dosya içerir (defter + berat) | `paketle()`; iki-dosya doğrulaması `paket_dogrula()`                |
| Berat defter içeriğini taşımaz               | Berat yalnızca dönem özeti + defter SHA-256                         |
| Arşiv düzeni                                 | `{dizin}/{yıl}/{defter_turu}/paket.zip` + `manifest.json` (SHA-256) |

Site kanıtı: GL fişlerinden üretilen yevmiye paketi
`sites/turkiye.local/private/files/edefter/2026/yevmiye/` altında
arşivlendi (UAT-ED1..3 PASS; örnek kopya `download/FAZ5/edefter-ornesi/`).

## 3. KM-4 UAT raporu — 15/15 PASS

Koşum: `stack/frappe-bench/env/bin/python scripts/faz5_uat.py turkiye.local`
(kanıt: `download/FAZ5/uat-raporu.txt`)

| Senaryo | Süreç      | Kural                                               | Sonuç |
| ------- | ---------- | --------------------------------------------------- | ----- |
| UAT-MH1 | Muhasebe   | Satış faturasında KDV %20 (2.000,00)                | PASS  |
| UAT-MH2 | Muhasebe   | Mizan dengesi: borç = alacak                        | PASS  |
| UAT-MH3 | Muhasebe   | e-Belge kaydı üretildi (UBL-TR; E-BLG-2026-00002)   | PASS  |
| UAT-MH4 | Muhasebe   | Geçersiz VKN faturası/müşterisi reddedildi          | PASS  |
| UAT-ST1 | Satış      | Sipariş toplamı 30.000,00                           | PASS  |
| UAT-ST2 | Satış      | Siparişte KDV %20 (6.000,00)                        | PASS  |
| UAT-ST3 | Satış      | Müşteri kaydı ve Türkiye bölgesi                    | PASS  |
| UAT-ST4 | Satış      | Müşteri bölgesi Türkiye (81 il / 1054 bölge verisi) | PASS  |
| UAT-IK1 | İK         | Bordro bileşen seti (SGK/İşsizlik/Damga/GV) kuruldu | PASS  |
| UAT-IK2 | İK         | hrms bordro neti = SAF hesap (≤ 0,10 TL)            | PASS  |
| UAT-IK3 | İK         | hrms net 42.894,52 (GİB değeri 42.894,60)           | PASS  |
| UAT-ED1 | e-Defter   | Yevmiye maddeleri dengeli (4/4 fiş)                 | PASS  |
| UAT-ED2 | e-Defter   | ZIP iki dosya (defter + berat)                      | PASS  |
| UAT-ED3 | e-Defter   | Arşiv manifesti SHA-256 tutarlı                     | PASS  |
| UAT-PR1 | Performans | 100 fatura, 3,8 sn (38 ms/fatura)                   | PASS  |

### UAT-IK2/IK3 bilinen fark (kuruş düzeyi, belgelenmiş)

hrms dilim değerlendirmesi kova uçlarını dahil sayar:
`(matrah − alt_sınır + 1) × oran` (hrms `salary_slip.py:2284`). GİB tarifesi
dışlayıcı uçludur. Brüt 60.000 TL'de bu konvansiyon farkı **0,08 TL/ay**'dır
(hrms net 42.894,52; SAF/GİB değeri 42.894,60). SAF bordro çekirdeği,
ÇSGB resmî tablosuyla birebir test edilmiştir (asgari ücret neti
28.075,50). UAT-IK2 ±0,10 TL toleransla sınar; gerçek fark 0,08'tir.
Kalıcı çözüm önerisi: hrms'e GİB konvansiyonu için konfigüre edilebilir uç
davranışı katkısı (çekirdek katkısı olarak planlanabilir).

### Performans dumanı

100 satış faturası 3,8 sn (38 ms/fatura) — tek çekirdekli kısıtlı sandbox
ortamında; ölçek beklentisinin çok altında. Ayrıca e-Defter yevmiye
paketleme milisaniye mertebesindedir (SAF testleri < 0,1 sn).

## 4. Eğitim

- `docs/EGITIM.md` — repo yanmeta metni (9 bölüm).
- `download/ERPNext_Turkiye_Kullanici_Rehberi.docx` (+ `.pdf`) — görsel ve
  tablolu tam rehber: giriş, arayüz, satış/KDV, e-belge, bordro, izinler,
  roller, e-Defter, sorun giderme; 5 ekran görüntüsü, 4 tablo.

## 5. KM-4 UAT onay formu (pilot kurum)

| Rol                   | Ad Soyad         | Tarih          | İmza     |
| --------------------- | ---------------- | -------------- | -------- |
| Muhasebe süreç sahibi | ________________ | ****/****/____ | ________ |
| Satış süreç sahibi    | ________________ | ****/****/____ | ________ |
| İK süreç sahibi       | ________________ | ****/****/____ | ________ |
| Proje yöneticisi      | ________________ | ****/****/____ | ________ |

Not: Bu formun imzalanması KM-4'ü resmen kapatır; script kanıtı (15/15
PASS) formun ekinidir.

## 6. Geri alma planı

1. **Yedek al:** `bench --site turkiye.local backup --with-files`
   (çıktı: `sites/turkiye.local/private/backups/`).
2. **Veritabanı geri alma:**
   `bench --site turkiye.local restore <yedek.sql.gz> --with-files <files.tar>`
   — dönüş, yedek anındaki şemaya ve veriye döner.
3. **Şema sürçmesi:** geri dönen yedekle `bench migrate` çalıştırmayın;
   uygulama kodunu yedeğin fazına eşleyin (`git checkout <faz-tag>`).
4. **Dosya alanı:** e-Defter arşivi (`private/files/edefter/`) yedekten
   bağımsız korunur; restore sonrası dizini elle geri kopyalayın.
5. **Tetikleyiciler:** mizan dengesizliği, e-belge kayıt eksikliği,
   bordro net sapması > 1 TL — herhangi biri görülürse değişiklikleri
   dondurun, 1-4 adımlarını uygulayın.

## 7. Kontrollü canlıya alma kontrol listesi

- [ ] `hosts`/DNS: turkiye.local (veya gerçek alan adı) çözümleniyor
- [ ] `bench --site <site> backup --with-files` alındı ve restore edildiği ayrı bir ortamda sınandı
- [ ] Administrator parolası değiştirildi (demo `admin` iptal)
- [ ] Şirket kaydında gerçek VKN; e-belge entegratör hesap bağlandı (kurulum paketi: kullanıcı adı/şifre/endpoint ortam değişkenlerinden)
- [ ] e-Defter kapsam kaydı (GİB portal) tamamlandı — zaman damgası sağlayıcı anlaşıldı
- [ ] KDV setleri gerçek oran/lafz kontrolü (sadece %1/%10/%20 şablonları aktif)
- [ ] İlk gerçek bordro: SAF çapraz doğrulaması ≤ 0,10 TL
- [ ] Rol profilleri kullanıcılarla eşlendi (Bordro Yöneticisi / Muhasebe / Satış)
- [ ] Günlük yedek cron'u tanımlı (`bench backup` + dosyalar)
- [ ] Bu belgenin bölüm 5 onay formu imzalandı

## 8. Sınırlar ve varsayımlar

- Sandbox'ta GİB/e-Fatura ortam erişimi yoktur; iletim ve zaman damgası
  simülasyon katmanıyla sınanmıştır. Gerçek yük pilot kurumda yapılır.
- hrms bordro konvansiyon farkı (0,08 TL @ 60k) belgelenmiştir; SAF motoru
  resmî tablo referansıdır.
- Performans sayıları kısıtlı sandbox içindir; canlı ölçek için gerçek
  donanımda aynı koşucu tekrarlanmalıdır.
- Sandbox geri dönüşümlerine karşı veri kurtarma: MariaDB veri dizini +
  `scripts/yigin_yeniden_kur.sh` (korunan DB yeniden bağlama + cache
  temizliği) ile Faz 2-5 verisi birebir geri yüklenmiştir (bu fazda 1 kez
  fiilen uygulanmıştır).
