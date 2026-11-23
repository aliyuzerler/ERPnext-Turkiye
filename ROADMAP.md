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

## Faz 3 — e-Dönüşüm Entegrasyonu ✅ (çekirdek tamamlandı)

1. **Dönüşüm:** UBL-TR 1.2 eşleme modülü (SAF `ebelge/`) — yapı GİB resmî
   örnek faturalarından, şema seti OASIS UBL 2.1'den (repoya tedarik).
2. **İletim:** entegratör bağımsız adaptör sözleşmesi + üstel geri çekilme
   ile yeniden deneme kuyruğu (SAF, hermetik testli); entegratör hesap
   anahtarının bağlanması Faz 4 kurulum paketinde.
3. **Belge türleri:** e-Fatura ✅ (tam eşleme) · e-İrsaliye ✅ (taslak,
   XSD-geçer) · e-Arşiv (aynı UBL, kapsam kaydı) · e-Defter (Faz 4).
4. **İzleme:** e-belge durum panosu canlı veriye bağlandı
   (`ebelge.api.ebelge_ozeti` + `EBelgePanel.canliOlustur`); E Belge
   Gonderim doctype + Sales Invoice on_submit kancası (şemadan geçmeyen
   fatura kuyruğa girmez).

- Viva'nın beş adımlı yayına çıkış listesi çıkış kriterlerine eklenir.
- Çıkış kriteri (KM-3) ✅: fatura XML'leri UBL 2.1 şema doğrulamasından
  geçiyor — kanıt: [docs/FAZ3.md](docs/FAZ3.md), duman testleri 8/8 PASS.

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
