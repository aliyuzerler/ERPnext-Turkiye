# ERPNext Türkiye — Uygulama Yol Haritası (v2.0)

Referans metodoloji: Viva Yazılım'ın kamuya açık hizmet yaklaşımı —
**Denetim → UAT → Kontrollü Canlı Geçiş** ve **dört katmanlı e-Fatura
mimarisi** (Kaynak Veri → Dönüşüm/UBL-TR → İletim → İzleme). Ayrıntılı
karar tabloları proje dokümanında (yol haritası dokümanı v2.0) yer alır.

## Faz çıkış kuralı (değişmez)

> Her faz, `make phase-gate` ve CI kapıları **yeşil olmadan kapanmaz**:
> lint (ruff, eslint, prettier) + tip kontrolü (mypy, tsc) + birim testler
> (pytest) + uçtan uca testler (Playwright). Bir kapı kırmızıysa takip eden
> faz başlatılmaz.

## Faz 0 — Keşif ve Denetim ✅ (tamamlandı)

- İş akışı envanteri, boşluk analizi ve UAT senaryo taslağı hazırlanır (Faz 5'e girdi).
- Depo iskeleti: Frappe uygulaması `erpnext_turkiye`, SAF çekirdek modüller.
- Kalite kapıları: ruff + mypy + pytest + eslint + prettier + tsc + Playwright; Makefile ve CI.
- Çekirdek modüller: TCKN/VKN doğrulama (GİB algoritmaları), KDV oranları ve
  tevkifat hesabı, TCMB kur XML ayrıştırıcı, THP başlangıç seti, e-belge durum
  panosu bileşeni (TS) + e2e.

## Faz 1 — Kurulum ve Temel Yapılandırma ✅ (tamamlandı)

- ERPNext v15 kurulumu (MariaDB 10.6 + Redis, kullanıcı seviyesi yığın) ve
  `erpnext_turkiye` uygulamasının siteye kurulması.
- Türkçe arayüzün devreye alınması (dil tr, dd.MM.yyyy, Europe/Istanbul,
  TRY), şirket kaydı ve demo ana veri (VKN doğrulaması canlı tetiklendi).
- Kurulum yardımcıları `kurulum.py` (kurulum_tamamlandi_isaretle,
  sirket_olustur, demo_verisi_olustur vb.) ve ekran görüntüsü betiği.
- Çıkış kriteri (KM-1) ✅: temel akışlar Türkçe arayüzde gezilebiliyor —
  kanıt: [docs/FAZ1.md](docs/FAZ1.md), duman testleri 7/7 PASS.
- Not: Turkish Delight entegrasyonu Faz 2 kurulum paketiyle değerlendirilecek.

## Faz 2 — Türkiye Lokalizasyon Paketi ✅ (tamamlandı)

- Hesap planı (THP tam set: 338 hesap, iki kaynaklı çapraz doğrulama) ve
  KDV setleri (%1/%10/%20 alış/satış/kalem şablonları + parametrik tevkifat).
- TCKN/VKN doğrulamasının tüm ana veri DocType'larına bağlanması
  (Customer + Supplier + Company; tüzel kişide VKN zorunlu).
- TCMB kur servisinin günlük zamanlayıcıyla devreye alınması
  (`hooks.py` scheduler_events aktivasyonu; canlı çekim doğrulandı).
- İl/ilçe veri yapısı (81 il / 973 ilçe → Territory ağacı 1054 kayıt);
  ana veri doğrulama kuralları (Kaynak Veri katmanı).
- Çıkış kriteri (KM-2) ✅: örnek fatura verisi doğrulama kurallarından
  geçiyor — kanıt: [docs/FAZ2.md](docs/FAZ2.md), duman testleri 11/11 PASS.

## Faz 3 — e-Dönüşüm Entegrasyonu (5 hafta, H8-H12)

Dört katmanlı mimari sırayla:

1. **Dönüşüm:** UBL-TR eşleme modülü (Turkish Delight e-Fatura çekirdeği genişletilir).
2. **İletim:** entegratör bağımsız adaptör + yeniden deneme kuyruğu.
3. **Belge türleri:** e-Fatura → e-Arşiv → e-İrsaliye → e-Defter.
4. **İzleme:** e-belge durum panosu canlı veriye bağlanır (Faz 0 bileşeni).

- Viva'nın beş adımlı yayına çıkış listesi çıkış kriterlerine eklenir.
- Çıkış kriteri (KM-3): test faturaları entegratör test ortamında şema doğrulamasından geçiyor.

## Faz 4 — İK-Bordro ve Kalan Modüller (3 hafta, H13-H15)

- SGK ve izin türü uyarlamaları; yerel bordro rapor beklentileri.
- Üretim iyileştirmeleri (Turkish Delight fonksiyonları), CRM ve Projeler.
- Kullanıcı rolü listesi ve yetkilendirme.

## Faz 5 — UAT, Eğitim ve Canlı Geçiş (3 hafta, H16-H18)

- Faz 0'da taslağı hazırlanan senaryolar gerçekçi verilerle koşulur (UAT 2-3 hafta).
- Rol bazlı eğitim + dokümantasyon paketi.
- Kontrollü canlı geçiş: ilk döngüde yakın izleme, günlük yayınlama pencereleri.
- Çıkış kriteri (KM-4): UAT onayı + ilk döngü izlemesi tamam.

## Sürekli işler (tüm fazlar)

- **Uyumluluk izleme:** mevzuat değişiklikleri takip takvimi; yayına çıkmadan
  önce güncel eşikler GİB resmi kanallarından doğrulanır.
- **Yedekleme ve izleme:** günlük yedekleme + harici kopya, kesintisiz güç
  kaynağı, durum panosu uyarıları (yerel kurulumun SLA eşdeğeri).
- **Çeviri bakımı:** sürüm güncellemelerinde Türkçe çeviri ve uyumluluk birlikte yönetilir.
