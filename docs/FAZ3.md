# Faz 3 — e-Dönüşüm Entegrasyonu (Çekirdek Tamamlandı)

**Tarih:** 23 Kasım 2026 · **Durum:** ✅ Çekirdek tamamlandı · **Çıkış kriteri (KM-3):** ✅ şema doğrulaması
**Kalite kapısı:** `make phase-gate` yeşil (lint + typecheck + **53** birim test + 3 e2e)
**Site duman testleri:** Faz 3 seti **8/8 PASS**

Faz 3, ROADMAP'teki dört katmanlı e-Fatura mimarisinin **Dönüşüm, İletim ve
İzleme** katmanlarını kurar. Üretim XML'i **GİB'in resmî örnek
faturalarından** (fatıhaslamaci/GIBFramework `SampleApp/OrnekFaturalar/` —
TEVKIFAT, 01-TemelFaturaOrnegi) birebir yapıyla üretilir ve **OASIS UBL 2.1
XSD setiyle** şema doğrulamasından geçmeden kayda alınmaz.

---

## 1. Kaynaklar ve şema seti (kod hafızadan yazılmaz)

| Kaynak                                                                       | Kullanım                                                                                                                            |
| ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| GIBFramework resmî örnek faturaları (TEVKIFAT.xml, 01-TemelFaturaOrnegi.xml) | UBL-TR 1.2 yapı: CustomizationID `TR1.2`, KDV TaxTypeCode `0015`, tevkifat `cac:WithholdingTaxTotal` (ör. kod 606), Signature bloğu |
| OASIS UBL 2.1 XSD seti (21 dosya, repoya tedarik: `ebelge/xsd/UBL-2.1/`)     | KM-3 şema doğrulaması (Invoice + DespatchAdvice)                                                                                    |
| Turkish Delight (logedosoft)                                                 | Referans olarak incelendi: SOAP veri taşır, dönüşümü entegratör yapar — biz XML'i kendi SAF çekirdeğimizle üretiyoruz               |

Not: vefa-validator XSD'lerindeki mutlak `schemaLocation` yolları repoya
göreli yollara çevrildi; `ext:ExtensionContent` OASIS şeması tam bir çocuk
ister (GİB xsdrt boş izin verir) — üretimde şema-düzeyinde serbest bir
`ebelge:ImzaYerTutucu` düğümü konur, entegratör imzayı buraya yazar.

## 2. Dönüşüm katmanı — `turkiye/ebelge/` (SAF)

- `veri.py` — ERPNext'ten bağımsız veri sözleşmesi (Taraf, FaturaSatiri,
  KDVGrubu, TevkifatSatiri, FaturaVerisi + `dogrula_veri` tutarlılık
  denetimi: genel toplam = net + ödenecek KDV).
- `ubl.py` — UBL-TR 1.2 Invoice üretici. Tevkifat usulü resmî örnekle
  birebir: `TaxTotal/TaxAmount` = alıcının ödediği KDV (tam − tevkifat),
  `TaxSubtotal` = tam KDV (matrah + oran), `WithholdingTaxTotal` = tevkif
  edilen toplam; `LegalMonetaryTotal` (PayableAmount = net + ödenen KDV).
- `irsaliye.py` — e-İrsaliye (DespatchAdvice) taslak üreticisi; OASIS XSD'den
  geçer (DespatchAdviceType'ta `cac:Delivery` bulunmadığından teslim
  ayrıntısı Shipment'e bırakılır — bilinçli kapsam kararı).
- `dogrula.py` — `xmlschema` ile XSD doğrulama (hata listesi döner).

## 3. İletim katmanı — `iletim.py` (SAF)

`EntegratorAdaptoru` sözleşmesi (Protocol: `gonder(xml) -> cevap`) + entegratör
bağımsız **yeniden deneme kuyruğu**: üstel geri çekilme (`2^deneme`, 60 sn üst
limit), kayıt başına `max_deneme`, sahte saat/göndericiyle hermetik testler
(uyku zinciri [2, 4] doğrulanır). Frappe tarafı kuyruk teknolojisini
buraya bağlar; çekirdek kuyruk teknolojisine bağımlı değildir.

## 4. KM-3 kanıtı: şema doğrulaması iki düzeyde kanıtlandı

1. **Hermetik birim testleri:** üretilen fatura + irsaliye XML'leri OASIS
   UBL 2.1 XSD'sinden geçer; bozuk XML hata listesi üretir (ters kanıt).
2. **Site kanıt kaydı:** `kurulum.km3_fatura_gonder` — KM-2 taslak faturası
   (ACC-SINV-2026-00002) submit edildi; `on_submit` kancası UBL-TR üretti,
   şema doğrulamasından geçirdi ve **E-BLG-2026-00001** kaydını açtı
   (durum `Uretilmis`, UUID atandı, alıcı VKN 3456789014; gönderen VKN
   5554443334 — demo gönderen/alıcı çakışması giderildi,
   `kimlik.vkn_uret` ile üretilen geçerli vektör).

**Bulgular (şema doğrulamasının gerçek değeri):** KM-3 ilk koşumda hatalı
üretimi reddetti — `posting_time` timedelta'dan gelen `5:45:56.` geçersiz
saati kancada biçimlendirdik; `ns0:` önekli serileştirme standart dışıydı,
varsayılan isim alanı kaydıyla `Invoice` kökü düzeltildi. İkisi de test
paketiyle sabitlendi.

## 5. Site entegrasyonu

- **E Belge Gonderim** DocType (Faz 3'te eklenen tek doctype): fatura linki,
  belge türü (e-Fatura/e-Arşiv/e-İrsaliye), durum
  (Uretilmis→Kuyrukta→Gonderildi/Hata/Iptal), UUID, alıcı VKN, XML içeriği,
  deneme sayısı, hata mesajı.
- **Kancalar:** `hooks.doc_events` Sales Invoice `on_submit` →
  `ebelge.olaylari.fatura_gonderim_kaydet` (üretim + doğrulama + kayıt),
  `on_cancel` → `gonderim_iptal`.
- **Panosu API:** `ebelge.api.ebelge_ozeti` (whitelisted) — durum sayaçları +
  son 50 kayıt; **e-belge durum panosu (Faz 0 bileşeni) canlı veriye
  bağlandı**: `window.EBelgePanel.canliOlustur(alan)` artık API'den çekip
  render eder (Faz 0 sabit-veri yolu korunur).
- Kurulum sırasında giderilen sihirbazsız kurulum eksikleri:
  `kurulum.party_turleri_tamamla` (Party Type kayıtları — `party_type`
  alanı DocType'a Link olduğu için kurulu olmayan modül doctype'ları
  atlanır) ve açık mali yıl garantisi (GL kaydı için).

## 6. Ekran görüntüleri (docs/ekran-goruntuleri/)

| Dosya                       | İçerik                                                          |
| --------------------------- | --------------------------------------------------------------- |
| `12-ebelge-panosu.png`      | E Belge Gonderim listesi (Türkçe): kanıt kaydı                  |
| `13-ebelge-kayit-detay.png` | Kayıt detayı: UUID, alıcı VKN, UBL-TR XML (TR1.2, TICARIFATURA) |

## 7. Kalite kapısı ve duman testleri

- `make phase-gate` yeşil: ruff + eslint + prettier, mypy (34 kaynak), **53
  pytest** (Faz 2'de 39 idi: UBL 7 + iletim 5 + irsaliye 2 yeni), Playwright 3/3.
- Faz 3 duman testleri (`scripts/site_goruntu_faz3.mjs`): **8/8 PASS** — liste,
  UUID, alıcı VKN, XML (TR1.2), durum, gönderen VKN ayrılığı.
- Notlar: `xmlschema` hem dev hem çalışma-zamanı bağımlılığıdır (pyproject
  dependencies; CI araç kurulum satırına eklendi). bench env'e de kuruldu.

## 8. Yeniden kurulum (tekrarlanabilirlik)

```bash
bench --site turkiye.local migrate            # E Belge Gonderim doctype
bench --site turkiye.local execute erpnext_turkiye.turkiye.kurulum.km3_fatura_gonder
# taslak fatura -> submit -> UBL-TR üretimi + XSD doğrulaması + kayıt
node scripts/site_goruntu_faz3.mjs http://127.0.0.1:8000
```

Ortam notları: web sunucusu `scripts/site_web.py` — **cwd bench `sites/`
dizini olmalıdır** (`frappe.read_file("assets/assets.json")` cwd-göreli; aksi
halde desk sayfaları NoneType.get ile çöker). rsync senkronu
`public/dist` silmemeli — bench build çıktısı bench tarafında kalır.

## 9. Bilinen notlar ve kalan kapsam

- **Gerçek entegratör iletimi:** adaptör sözleşmesi + kuyruk hazır; Foriba/
  Uyumsoft/Veriban hesap anahtarı sağlanınca tek yapılacak: adaptör
  sınıfının `gonder()`'ini entegratör REST/SOAP çağrısıyla doldurmak
  (Faz 4 kurulum paketi). GİB portal doğrudan iletiyi imza altyapısı
  gerektirir.
- **Zarf (Envelope):** entegratörler zarfı kendi tarafında sarmalar; GİB
  portal zarf şeması temin edildiğinde `zarf_sar()` eklenebilir.
- **e-Defter:** ayrı XSLT/GlCor format ailesi — Faz 4 kapsamı.
- **GİB tevkifat kod kataloğu:** resmî örnekte doğrulanmış tek kod (606)
  kullanılıyor; katalog genişletmesi resmî kod listesi kaynağıyla yapılır.
- Per-line vergi alt toplamları v1'de fatura düzeyinde gruplandırılır
  (şema-geçer); GİB detay kural seti Faz 4'te CIUS düzeyinde eklenir.
