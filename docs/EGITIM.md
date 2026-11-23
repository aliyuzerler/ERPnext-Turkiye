# ERPNext Türkiye — Kullanıcı Eğitim Rehberi (kısa metin)

> Bu belge, Faz 5 eğitim çıktısının repo yanmeta metnidir. Görsel ve tablolu
> tam sürüm için `download/ERPNext_Turkiye_Kullanici_Rehberi.docx` (ve PDF) dosyasına
> bakın; ekran görüntüleri `docs/ekran-goruntuleri/` dizinindedir.

Demo ortam: `turkiye.local` — Anadolu Makine Sanayi A.Ş. · Dil: Türkçe · Para birimi: TRY
Giriş: Administrator / `admin` (yalnızca demo; canlı kurulumda hemen değiştirin).

## 1. Sisteme Giriş ve İlk Adımlar

Tarayıcıda `turkiye.local` çözümlenmiyorsa hosts dosyasına `127.0.0.1 turkiye.local`
satırını ekleyin. İlk açılış sihirbazında dil, saat dilimi ve para birimi Faz 1
kurulum fonksiyonlarıyla (`site_tr_ayarlari`) otomatik atandığı için varsayılanları
onaylamak yeterlidir. Yetkilendirmede Rol Profili alanı Faz 4 profilleriyle
(Bordro Yöneticisi, Muhasebe, Satış) tek hamlede tüm izinleri belirler.

## 2. Ana Sayfa ve Arayüzde Gezinme

Masaüstü, yetkiniz olan modüllerin kısayollarını toplar. Sağ üstteki arama kutusu
doküman numarası ve müşteri adıyla tarar (örn. `ACC-SINV`). Liste görünümlerindeki
filtreler kişisel çalışma görünümü olarak kalıcıdır.

## 3. Satış: Müşteri, Fatura ve KDV

Müşteri kartında VKN otomatik doğrulanır; geçersiz VKN ile kayıt açılamaz ve
e-belge üretimi engellenir (Faz 2 kuralı, km2 kanıtı). Bölge alanı Türkiye'nin
81 ili ve 1054 bölge kaydıyla doludur.

| Set | Oran | Kullanım |
| --- | --- | --- |
| KDV %1 Satış / Alış / Kalem | %1 | Temel gıda, kitap vb. |
| KDV %10 Satış / Alış / Kalem | %10 | Belirli tarım ve hizmet kalemleri |
| KDV %20 Satış / Alış / Kalem | %20 | Genel oran — varsayılan satış şablonu |

Fatura adımları: Satış → Satış Faturası → Yeni; müşteri seç; kalem ekle
(demo: HIZ-MLZ-001, HIZ-DAN-001); vergi şablonu seç; Kaydet → Gönder.
Muhasebe fişi THP kodlarıyla oluşur (120 Alıcılar, 600 Yurt İçi Satışlar,
391 Hesaplanan KDV) ve borç-alacak dengesi UAT-MH2'de kanıtlanır.

## 4. e-Dönüşüm: e-Belge Akışı

Gönderilen satış faturası için Faz 3 modülü UBL-TR 2.1 XML üretir; E Belge
Gonderim kaydı durumları: `Uretilmis → Kuyrukta → Gonderildi`. UUID alanı
entegratör sorgularının anahtarıdır. Panoyu Muhasebe workspace'inde
e-Belge Durumu kartında bulursunuz; Yenile eylemi XML'i güncel veriyle
baştan kurar.

## 5. İK ve Bordro

Maaş yapısı **Türkiye Standart** Faz 5'te kurulur: temel ücret üzerinden
SGK %14, işsizlik %1, damga binde 7,59 ve tarifeli gelir vergisi. Gelir
vergisi matrahından SGK primleri mahsuben düşer (GVK m.63; hrms
`allow_tax_exemption` bayrağı faz5_kurulum ile açılır). 2026 asgari ücret
tablosu:

| Kalem | Oran | Tutar (TL/ay) |
| --- | --- | --- |
| Brüt asgari ücret | — | 33.030,00 |
| SGK işçi payı | %14 | 4.624,20 |
| İşsizlik sigortası işçi payı | %1 | 330,30 |
| Net asgari ücret (GV+DV muaf) | — | 28.075,50 |

Bordro: İK → Maaş Yapısı Ataması (çalışan + brüt), sonra İK → Maaş Bordrosu
(dönem seç → oluştur). Brüt 60.000 TL için hrms bordrosu SAF hesabıyla kuruş
düzeyinde eşleşir: SGK 8.400,00 + işsizlik 600,00 + GV 7.650,00 + damga 455,40 =
net **42.894,60 TL** (SAF, GİB/ÇSGB tablosuyla birebir). hrms bordrosu
42.894,52 TL verir; 0,08 TL'lik fark, hrms'in dilim kova uçlarını dahil sayan
konvansiyonundan ((matrah − alt + 1) × oran) kaynaklanan sistematik sapmadır —
UAT-IK2 ±0,10 TL toleransla sınar.

## 6. İzinler ve Resmî Tatiller

İzin türleri 4857 m.53: yıllık ücretli izin 14 / 20 / 26 gün; 18 yaş altı ve
öğrenim çağında en az 20 gün; doğum 8+8 hafta; babalık 5 gün. Türkiye 2026
tatil listesi 2429 sayılı Kanun'a göre **15,5 gün**: bayram arifeleri ve
28 Ekim 13.00 sonrası yarım gün.

## 7. Roller ve Yetkiler

| Profil | Roller | Kapsam |
| --- | --- | --- |
| Türkiye Bordro Yöneticisi | HR User, HR Manager | Özlük, izin, bordro |
| Türkiye Muhasebe | Accounts User, Accounts Manager | Fatura, KDV, THP, e-belge |
| Türkiye Satış | Sales User, Sales Manager | Müşteri, teklif, sipariş, fatura |

Profil değişikliği oturum yeniden açıldığında devreye girer; doküman düzeyi
kıst için Kullanıcı İzinleri bölümünü kullanın.

## 8. e-Defter Arşivleme

Faz 5 modülü fişlerden yevmiye defterini GİB kılavuzunun istediği XBRL-GL
yapısıyla üretir; dengesiz yevmiye maddesi reddedilir (UAT-ED1). ZIP paketi
**iki dosya** taşır: defter + berat (kılavuz kuralı); berat defter içeriğini
taşımaz, dönem özeti ve SHA-256 doğrulaması tutar. Arşiv yolu:
`sites/turkiye.local/private/files/edefter/{yıl}/yevmiye/` + manifest.json.
Zaman damgası ve GİB yükleme gerçek ortam işlevidir (entegratör).

## 9. Sorun Giderme

| Durum | Çözüm |
| --- | --- |
| turkiye.local çözümlenmiyor | hosts kaydı + `bench start` kontrolü |
| Fatura gönderildi, e-belge yok | E Belge Gonderim listesine bak; fatura üzerinde Yenile |
| Bordro neti farklı | Kümülatif matrah: önceki aylar kesilmiş mi |
| Geçersiz VKN ile kayıt açılamıyor | Hata değil — Faz 2 doğrulama kuralı |
| KDV şablonu gelmiyor | Müşteri kartındaki vergi şablonunu kontrol et |

Yedek: `bench --site turkiye.local backup`; çıktı
`sites/turkiye.local/private/backups`. Canlıya alma planı için
`docs/FAZ5.md` bölüm 6'ya bakın.
