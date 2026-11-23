"""Tek Düzen Hesap Planı tam seti (SAF veri modülü).

Kaynaklar (kod + ad çapraz doğrulanmıştır):
- vergiburosu.com "Tekdüzen Hesap Planı" sayfası (VUK 1 No.lu Genel Tebliği
  planı; https://www.vergiburosu.com/pratik-bilgiler/tekduzen-hesap-plani)
- İSMMMO "Hesap Planı Açıklamaları" (https://www.ismmmo.org.tr/dosya/415/
  Mevzuat-Dosya/tekduzhesapplani.pdf) — ek hesaplar (178, 350, 358, 339, 439,
  502, 503) bu kaynaktan tamamlanmıştır.

Notlar:
- Kodlar resmi plan kodlarıdır; şirket altı alt hesaplar (ör. 120.01) site
  kurulumunda şirkete göre açılabilir (thp_kur).
- 7. grup 7/A ve 7/B seçeneklerinin ortak bağlantı setidir; seçenek
  ayrımı Faz 4 üretim modülünde değerlendirilir.
- 8 Serbest Hesaplar ve 9 Nazım Hesaplar grupları köksüz ERPNext kaydına
  açılamayacağından tohum setinde yer almaz (belgelenmiş istisna).
- 238 "Şüpheli Diğer Alacaklar" iki bağımsız kaynaktan doğrulanamadığı
  (İSMMMO gövde/başlık numaralandırması çelişkili) için sete alınmadı.
- 690/691/692/697/698 dönemi kapanış ve enflasyon düzeltme hesaplarıdır;
  ERPNext P&L kapanışını otomatik yapar, bu hesaplar tam set bütünlüğü
  için Gider kök türüyle eklenir.

Bu modül SAF Python'dur; frappe import etmez.
"""

from __future__ import annotations

# ruff: noqa: E501  (veri tablosu satırları resmi hesap adlarıyla uzundur)
from dataclasses import dataclass

TURLER: tuple[str, ...] = ("Asset", "Liability", "Equity", "Income", "Expense")
RAPOR_TURLERI: tuple[str, ...] = ("Balance Sheet", "Profit and Loss")


@dataclass(frozen=True)
class HesapKaydi:
    """THP hesap kaydı (kod, ad, ERPNext eşlemeleri)."""

    kod: str
    ad: str
    kok_tur: str
    rapor_tur: str
    hesap_turu: str | None


# (kod, ad, kok_tur, rapor_tur, hesap_turu)
_HAM: tuple[tuple[str, str, str, str, str | None], ...] = (
    ("1", "Dönen Varlıklar", "Asset", "Balance Sheet", None),
    ("10", "Hazır Değerler", "Asset", "Balance Sheet", None),
    ("100", "Kasa", "Asset", "Balance Sheet", "Cash"),
    ("101", "Alınan Çekler", "Asset", "Balance Sheet", None),
    ("102", "Bankalar", "Asset", "Balance Sheet", "Bank"),
    ("103", "Verilen Çekler ve Ödeme Emirleri(-)", "Asset", "Balance Sheet", None),
    ("108", "Diğer Hazır Değerler", "Asset", "Balance Sheet", None),
    ("11", "Menkul Kıymetler", "Asset", "Balance Sheet", None),
    ("110", "Hisse Senetleri", "Asset", "Balance Sheet", None),
    ("111", "Özel Kesim Tahvil Senet ve Bonoları", "Asset", "Balance Sheet", None),
    ("112", "Kamu Kesimi Tahvil, Senet ve Bonoları", "Asset", "Balance Sheet", None),
    ("118", "Diğer Menkul Kıymetler", "Asset", "Balance Sheet", None),
    ("119", "Menkul Kıymetler Değer Düşüklüğü Karşılığı(-)", "Asset", "Balance Sheet", None),
    ("12", "Ticari Alacaklar", "Asset", "Balance Sheet", None),
    ("120", "Alıcılar", "Asset", "Balance Sheet", "Receivable"),
    ("121", "Alacak Senetleri", "Asset", "Balance Sheet", None),
    ("122", "Alacak Senetleri Reeskontu(-)", "Asset", "Balance Sheet", None),
    ("124", "Kazanılmamış Finansal Kiralama Faiz Gelirleri(-)", "Asset", "Balance Sheet", None),
    ("126", "Verilen Depozito ve Teminatlar", "Asset", "Balance Sheet", None),
    ("127", "Diğer Ticari Alacaklar", "Asset", "Balance Sheet", None),
    ("128", "Şüpheli Ticari Alacaklar", "Asset", "Balance Sheet", None),
    ("129", "Şüpheli Ticari Alacaklar Karşılığı(-)", "Asset", "Balance Sheet", None),
    ("13", "Diğer Alacaklar", "Asset", "Balance Sheet", None),
    ("131", "Ortaklardan Alacaklar", "Asset", "Balance Sheet", None),
    ("132", "İştiraklerden Alacaklar", "Asset", "Balance Sheet", None),
    ("133", "Bağlı Ortaklıklardan Alacaklar", "Asset", "Balance Sheet", None),
    ("135", "Personelden Alacaklar", "Asset", "Balance Sheet", None),
    ("136", "Diğer Çeşitli Alacaklar", "Asset", "Balance Sheet", None),
    ("137", "Diğer Alacak Senetleri Reeskontu(-)", "Asset", "Balance Sheet", None),
    ("138", "Şüpheli Diğer Alacaklar", "Asset", "Balance Sheet", None),
    ("139", "Şüpheli Diğer Alacaklar Karşılığı(-)", "Asset", "Balance Sheet", None),
    ("15", "Stoklar", "Asset", "Balance Sheet", None),
    ("150", "İlk Madde Malzeme", "Asset", "Balance Sheet", "Stock"),
    ("151", "Yarı Mamuller", "Asset", "Balance Sheet", "Stock"),
    ("152", "Mamuller", "Asset", "Balance Sheet", "Stock"),
    ("153", "Ticari Mallar", "Asset", "Balance Sheet", "Stock"),
    ("157", "Diğer Stoklar", "Asset", "Balance Sheet", "Stock"),
    ("158", "Stok Değer Düşüklüğü Karşılığı(-)", "Asset", "Balance Sheet", None),
    ("159", "Verilen Sipariş Avansları", "Asset", "Balance Sheet", None),
    ("17", "Yıllara Yaygın İnşaat ve Onarım Maliyetleri", "Asset", "Balance Sheet", None),
    ("170", "Yıllara Yaygın İnşaat ve Onarım Maliyetleri", "Asset", "Balance Sheet", None),
    ("178", "Yıllara Yaygın İnşaat Enflasyon Düzeltme", "Asset", "Balance Sheet", None),
    ("179", "Taşeronlara Verilen Avanslar", "Asset", "Balance Sheet", None),
    ("18", "Gelecek Aylara Ait Giderler ve Gelir Tahakkukları", "Asset", "Balance Sheet", None),
    ("180", "Gelecek Aylara Ait Giderler", "Asset", "Balance Sheet", None),
    ("181", "Gelir Tahakkukları", "Asset", "Balance Sheet", None),
    ("19", "Diğer Dönen Varlıklar", "Asset", "Balance Sheet", None),
    ("190", "Devreden KDV", "Asset", "Balance Sheet", "Tax"),
    ("191", "İndirilecek KDV", "Asset", "Balance Sheet", "Tax"),
    ("192", "Diğer KDV", "Asset", "Balance Sheet", "Tax"),
    ("193", "Peşin Ödenen Vergiler ve Fonlar", "Asset", "Balance Sheet", "Tax"),
    ("195", "İş Avansları", "Asset", "Balance Sheet", None),
    ("196", "Personel Avansları", "Asset", "Balance Sheet", None),
    ("197", "Sayım ve Tesellüm Noksanları", "Asset", "Balance Sheet", None),
    ("198", "Diğer Çeşitli Dönen Varlıklar", "Asset", "Balance Sheet", None),
    ("199", "Diğer Dönen Varlıklar Karşılığı(-)", "Asset", "Balance Sheet", None),
    ("2", "Duran Varlıklar", "Asset", "Balance Sheet", None),
    ("22", "Ticari Alacaklar", "Asset", "Balance Sheet", None),
    ("220", "Alıcılar", "Asset", "Balance Sheet", None),
    ("221", "Alacak Senetleri", "Asset", "Balance Sheet", None),
    ("222", "Alacak Senetleri Reeskontu(-)", "Asset", "Balance Sheet", None),
    ("224", "Kazanılmamış Finansal Kiralama Faiz Gelirleri(-)", "Asset", "Balance Sheet", None),
    ("226", "Verilen Depozito ve Teminatlar", "Asset", "Balance Sheet", None),
    ("229", "Şüpheli Ticari Alacaklar Karşılığı(-)", "Asset", "Balance Sheet", None),
    ("23", "Diğer Alacaklar", "Asset", "Balance Sheet", None),
    ("231", "Ortaklardan Alacaklar", "Asset", "Balance Sheet", None),
    ("232", "İştiraklerden Alacaklar", "Asset", "Balance Sheet", None),
    ("233", "Bağlı Ortaklıklardan Alacaklar", "Asset", "Balance Sheet", None),
    ("235", "Personelden Alacaklar", "Asset", "Balance Sheet", None),
    ("236", "Diğer Çeşitli Alacaklar", "Asset", "Balance Sheet", None),
    ("237", "Diğer Alacak Senetleri Reeskontu(-)", "Asset", "Balance Sheet", None),
    ("239", "Şüpheli Diğer Alacaklar Karşılığı(-)", "Asset", "Balance Sheet", None),
    ("24", "Mali Duran Varlıklar", "Asset", "Balance Sheet", None),
    ("240", "Bağlı Menkul Kıymetler", "Asset", "Balance Sheet", None),
    ("241", "Bağlı Menkul Kıymetler Değer Düşüklüğü Karşılığı(-)", "Asset", "Balance Sheet", None),
    ("242", "İştirakler", "Asset", "Balance Sheet", None),
    ("243", "İştiraklere Sermaye Taahhütleri(-)", "Asset", "Balance Sheet", None),
    ("244", "İştirakler Sermaye Payları Değer Düşüklüğü Karşılığı(-)", "Asset", "Balance Sheet", None),
    ("245", "Bağlı Ortaklıklar", "Asset", "Balance Sheet", None),
    ("246", "Bağlı Ortaklıklara Sermaye Taahhütleri(-)", "Asset", "Balance Sheet", None),
    ("247", "Bağlı Ortaklıklar Sermaye Payları Değer Düşüklüğü Karşılığı(-)", "Asset", "Balance Sheet", None),
    ("248", "Diğer Mali Duran Varlıklar", "Asset", "Balance Sheet", None),
    ("249", "Diğer Mali Duran Varlıklar Karşılığı(-)", "Asset", "Balance Sheet", None),
    ("25", "Maddi Duran Varlıklar", "Asset", "Balance Sheet", None),
    ("250", "Arazi ve Arsalar", "Asset", "Balance Sheet", None),
    ("251", "Yer Altı ve Yer Üstü Düzenleri", "Asset", "Balance Sheet", None),
    ("252", "Binalar", "Asset", "Balance Sheet", None),
    ("253", "Tesis, Makine ve Cihazlar", "Asset", "Balance Sheet", None),
    ("254", "Taşıtlar", "Asset", "Balance Sheet", None),
    ("255", "Demirbaşlar", "Asset", "Balance Sheet", None),
    ("256", "Diğer Maddi Duran Varlıklar", "Asset", "Balance Sheet", None),
    ("257", "Birikmiş Amortismanlar(-)", "Asset", "Balance Sheet", "Accumulated Depreciation"),
    ("258", "Yapılmakta Olan Yatırımlar", "Asset", "Balance Sheet", "Capital Work in Progress"),
    ("259", "Verilen Avanslar", "Asset", "Balance Sheet", None),
    ("26", "Maddi Olmayan Duran Varlıklar", "Asset", "Balance Sheet", None),
    ("260", "Haklar", "Asset", "Balance Sheet", None),
    ("261", "Şerefiye", "Asset", "Balance Sheet", None),
    ("262", "Kuruluş ve Örgütlenme Giderleri", "Asset", "Balance Sheet", None),
    ("263", "Araştırma ve Geliştirme Giderleri", "Asset", "Balance Sheet", None),
    ("264", "Özel Maliyetler", "Asset", "Balance Sheet", None),
    ("267", "Diğer Maddi Olmayan Duran Varlıklar", "Asset", "Balance Sheet", None),
    ("268", "Birikmiş Amortismanlar(-)", "Asset", "Balance Sheet", "Accumulated Depreciation"),
    ("269", "Verilen Avanslar", "Asset", "Balance Sheet", None),
    ("27", "Özel Tükenmeye Tabi Varlıklar", "Asset", "Balance Sheet", None),
    ("271", "Arama Giderleri", "Asset", "Balance Sheet", None),
    ("272", "Hazırlık ve Geliştirme Giderleri", "Asset", "Balance Sheet", None),
    ("277", "Diğer Özel Tükenmeye Tabi Varlıklar", "Asset", "Balance Sheet", None),
    ("278", "Birikmiş Tükenme Payları(-)", "Asset", "Balance Sheet", "Accumulated Depreciation"),
    ("279", "Verilen Avanslar", "Asset", "Balance Sheet", None),
    ("28", "Gelecek Yıllara Ait Giderler ve Gelir Tahakkukları", "Asset", "Balance Sheet", None),
    ("280", "Gelecek Yıllara Ait Giderler", "Asset", "Balance Sheet", None),
    ("281", "Gelir Tahakkukları", "Asset", "Balance Sheet", None),
    ("29", "Diğer Duran Varlıklar", "Asset", "Balance Sheet", None),
    ("291", "Gelecek Yıllarda İndirilecek KDV", "Asset", "Balance Sheet", "Tax"),
    ("292", "Diğer KDV", "Asset", "Balance Sheet", "Tax"),
    ("293", "Gelecek Yıllar İhtiyacı Stoklar", "Asset", "Balance Sheet", None),
    ("294", "Elden Çıkarılacak Stoklar ve Maddi Duran Varlıklar", "Asset", "Balance Sheet", None),
    ("295", "Peşin Ödenen Vergi ve Fonlar", "Asset", "Balance Sheet", None),
    ("297", "Diğer Çeşitli Duran Varlıklar", "Asset", "Balance Sheet", None),
    ("298", "Stok Değer Düşüklüğü Karşılığı(-)", "Asset", "Balance Sheet", None),
    ("299", "Birikmiş Amortismanlar(-)", "Asset", "Balance Sheet", "Accumulated Depreciation"),
    ("3", "Kısa Vadeli Yabancı Kaynaklar", "Liability", "Balance Sheet", None),
    ("30", "Mali Borçlar", "Liability", "Balance Sheet", None),
    ("300", "Banka Kredileri", "Liability", "Balance Sheet", None),
    ("301", "Finansal Kiralama İşlemlerinden Borçlar", "Liability", "Balance Sheet", None),
    ("302", "Ertelenmiş Finansal Kiralama Borçlanma Maliyetleri(-)", "Liability", "Balance Sheet", None),
    ("303", "Uzun Vadeli Kredilerin Anapara Taksitleri ve Faizleri", "Liability", "Balance Sheet", None),
    ("304", "Tahvil Anapara Borç, Taksit ve Faizleri", "Liability", "Balance Sheet", None),
    ("305", "Çıkarılan Bonolar ve Senetler", "Liability", "Balance Sheet", None),
    ("306", "Çıkarılmış Diğer Menkul Kıymetler", "Liability", "Balance Sheet", None),
    ("308", "Menkul Kıymetler İhraç Farkı(-)", "Liability", "Balance Sheet", None),
    ("309", "Diğer Mali Borçlar", "Liability", "Balance Sheet", None),
    ("32", "Ticari Borçlar", "Liability", "Balance Sheet", None),
    ("320", "Satıcılar", "Liability", "Balance Sheet", "Payable"),
    ("321", "Borç Senetleri", "Liability", "Balance Sheet", None),
    ("322", "Borç Senetleri Reeskontu(-)", "Liability", "Balance Sheet", None),
    ("326", "Alınan Depozito ve Teminatlar", "Liability", "Balance Sheet", None),
    ("329", "Diğer Ticari Borçlar", "Liability", "Balance Sheet", None),
    ("33", "Diğer Borçlar", "Liability", "Balance Sheet", None),
    ("331", "Ortaklara Borçlar", "Liability", "Balance Sheet", None),
    ("332", "İştiraklere Borçlar", "Liability", "Balance Sheet", None),
    ("333", "Bağlı Ortaklıklara Borçlar", "Liability", "Balance Sheet", None),
    ("335", "Personele Borçlar", "Liability", "Balance Sheet", None),
    ("336", "Diğer Çeşitli Borçlar", "Liability", "Balance Sheet", None),
    ("337", "Diğer Borç Senetleri Reeskontu(-)", "Liability", "Balance Sheet", None),
    ("339", "Diğer Çeşitli Borçlar", "Liability", "Balance Sheet", None),
    ("34", "Alınan Avanslar", "Liability", "Balance Sheet", None),
    ("340", "Alınan Sipariş Avansları", "Liability", "Balance Sheet", None),
    ("349", "Alınan Diğer Avanslar", "Liability", "Balance Sheet", None),
    ("35", "Yıllara Yaygın İnşaat ve Onarım Hakedişleri", "Liability", "Balance Sheet", None),
    ("350", "Yıllara Yaygın İnşaat ve Onarım Hakedişleri", "Liability", "Balance Sheet", None),
    ("358", "Yıllara Yaygın İnşaat Enflasyon Düzeltme", "Liability", "Balance Sheet", None),
    ("36", "Ödenecek Vergi ve Diğer Yükümlülükler", "Liability", "Balance Sheet", None),
    ("360", "Ödenecek Vergi ve Fonlar", "Liability", "Balance Sheet", "Tax"),
    ("361", "Ödenecek Sosyal Güvenlik Kesintileri", "Liability", "Balance Sheet", "Tax"),
    ("368", "Vadesi Geçmiş, Ertelenmiş Veya Taksitlendirilmiş Vergi ve Diğer Yükümlülükler", "Liability", "Balance Sheet", None),
    ("369", "Ödenecek Diğer Yükümlülükler", "Liability", "Balance Sheet", None),
    ("37", "Borç ve Gider Karşılıkları", "Liability", "Balance Sheet", None),
    ("370", "Dönem Kârı Vergi ve Diğer Yasal Yükümlülük Karşılıkları", "Liability", "Balance Sheet", None),
    ("371", "Dönem Kârının Peşin Ödenen Vergi ve Diğer Yükümlülükleri(-)", "Liability", "Balance Sheet", None),
    ("372", "Kıdem Tazminatı Karşılığı", "Liability", "Balance Sheet", None),
    ("373", "Maliyet Giderleri Karşılığı", "Liability", "Balance Sheet", None),
    ("379", "Diğer Borç ve Gider Karşılıkları", "Liability", "Balance Sheet", None),
    ("38", "Gelecek Aylara Ait Gelirler ve Gider Tahakkukları", "Liability", "Balance Sheet", None),
    ("380", "Gelecek Aylara Ait Gelirler", "Liability", "Balance Sheet", None),
    ("381", "Gider Tahakkukları", "Liability", "Balance Sheet", None),
    ("39", "Diğer Kısa Vadeli Yabancı Kaynaklar", "Liability", "Balance Sheet", None),
    ("391", "Hesaplanan KDV", "Liability", "Balance Sheet", "Tax"),
    ("392", "Diğer KDV", "Liability", "Balance Sheet", "Tax"),
    ("393", "Merkez ve Şubeler Cari Hesabı", "Liability", "Balance Sheet", None),
    ("397", "Sayım ve Tesellüm Fazlaları", "Liability", "Balance Sheet", None),
    ("399", "Diğer Çeşitli Yabancı Kaynaklar", "Liability", "Balance Sheet", None),
    ("4", "Uzun Vadeli Yabancı Kaynaklar", "Liability", "Balance Sheet", None),
    ("40", "Mali Borçlar", "Liability", "Balance Sheet", None),
    ("400", "Banka Kredileri", "Liability", "Balance Sheet", None),
    ("401", "Finansal Kiralama İşlemlerinden Borçlar", "Liability", "Balance Sheet", None),
    ("402", "Ertelenmiş Finansal Kiralama Borçlanma Maliyetleri(-)", "Liability", "Balance Sheet", None),
    ("405", "Çıkarılmış Tahviller", "Liability", "Balance Sheet", None),
    ("407", "Çıkarılmış Diğer Menkul Kıymetler", "Liability", "Balance Sheet", None),
    ("408", "Menkul Kıymetler İhraç Farkı(-)", "Liability", "Balance Sheet", None),
    ("409", "Diğer Mali Borçlar", "Liability", "Balance Sheet", None),
    ("42", "Ticari Borçlar", "Liability", "Balance Sheet", None),
    ("420", "Satıcılar", "Liability", "Balance Sheet", None),
    ("421", "Borç Senetleri", "Liability", "Balance Sheet", None),
    ("422", "Borç Senetleri Reeskontu(-)", "Liability", "Balance Sheet", None),
    ("426", "Alınan Depozito ve Teminatlar", "Liability", "Balance Sheet", None),
    ("429", "Diğer Ticari Borçlar", "Liability", "Balance Sheet", None),
    ("43", "Diğer Borçlar", "Liability", "Balance Sheet", None),
    ("431", "Ortaklara Borçlar", "Liability", "Balance Sheet", None),
    ("432", "İştiraklere Borçlar", "Liability", "Balance Sheet", None),
    ("433", "Bağlı Ortaklıklara Borçlar", "Liability", "Balance Sheet", None),
    ("436", "Diğer Çeşitli Borçlar", "Liability", "Balance Sheet", None),
    ("437", "Diğer Borç Senetleri Reeskontu(-)", "Liability", "Balance Sheet", None),
    ("438", "Kamuya Olan Ertelenmiş Veya Taksitlendirilmiş Borçlar", "Liability", "Balance Sheet", None),
    ("439", "Diğer Çeşitli Borçlar", "Liability", "Balance Sheet", None),
    ("44", "Alınan Avanslar", "Liability", "Balance Sheet", None),
    ("440", "Alınan Sipariş Avansları", "Liability", "Balance Sheet", None),
    ("449", "Alınan Diğer Avanslar", "Liability", "Balance Sheet", None),
    ("47", "Borç ve Gider Karşılıkları", "Liability", "Balance Sheet", None),
    ("472", "Kıdem Tazminatı Karşılığı", "Liability", "Balance Sheet", None),
    ("479", "Diğer Borç ve Gider Karşılıkları", "Liability", "Balance Sheet", None),
    ("48", "Gelecek Yıllara Ait Gelirler ve Gider Tahakkukları", "Liability", "Balance Sheet", None),
    ("480", "Gelecek Yıllara Ait Gelirler", "Liability", "Balance Sheet", None),
    ("481", "Gider Tahakkukları", "Liability", "Balance Sheet", None),
    ("49", "Diğer Uzun Vadeli Yabancı Kaynaklar", "Liability", "Balance Sheet", None),
    ("492", "Gelecek Yıllara Ertelenmiş Veya Terkin Edilecek KDV", "Liability", "Balance Sheet", "Tax"),
    ("493", "Tesise Katılma Payları", "Liability", "Balance Sheet", None),
    ("499", "Diğer Çeşitli Uzun Vadeli Yabancı Kaynaklar", "Liability", "Balance Sheet", None),
    ("5", "Özkaynaklar", "Equity", "Balance Sheet", None),
    ("50", "Ödenmiş Sermaye", "Equity", "Balance Sheet", None),
    ("500", "Sermaye", "Equity", "Balance Sheet", None),
    ("501", "Ödenmemiş Sermaye(-)", "Equity", "Balance Sheet", None),
    ("502", "Sermaye Düzeltmesi Olumlu Farkları", "Equity", "Balance Sheet", None),
    ("503", "Sermaye Düzeltmesi Olumsuz Farkları(-)", "Equity", "Balance Sheet", None),
    ("52", "Sermaye Yedekleri", "Equity", "Balance Sheet", None),
    ("520", "Hisse Senetleri İhraç Primleri", "Equity", "Balance Sheet", None),
    ("521", "Hisse Senedi İptal Kârları", "Equity", "Balance Sheet", None),
    ("522", "Maddi Duran Varlık Yeniden Değerleme Artışları", "Equity", "Balance Sheet", None),
    ("523", "İştirakler Yeniden Değerleme Artışları", "Equity", "Balance Sheet", None),
    ("524", "Maliyet Artışları Fonu", "Equity", "Balance Sheet", None),
    ("529", "Diğer Sermaye Yedekleri", "Equity", "Balance Sheet", None),
    ("54", "Kâr Yedekleri", "Equity", "Balance Sheet", None),
    ("540", "Yasal Yedekler", "Equity", "Balance Sheet", None),
    ("541", "Statü Yedekleri", "Equity", "Balance Sheet", None),
    ("542", "Olağanüstü Yedekler", "Equity", "Balance Sheet", None),
    ("548", "Diğer Kâr Yedekleri", "Equity", "Balance Sheet", None),
    ("549", "Özel Fonlar", "Equity", "Balance Sheet", None),
    ("57", "Geçmiş Yıllar Kârları", "Equity", "Balance Sheet", None),
    ("570", "Geçmiş Yıllar Kârları", "Equity", "Balance Sheet", None),
    ("58", "Geçmiş Yıllar Zararları(-)", "Equity", "Balance Sheet", None),
    ("580", "Geçmiş Yıllar Zararları(-)", "Equity", "Balance Sheet", None),
    ("59", "Dönem Net Kârı (Zararı)", "Equity", "Balance Sheet", None),
    ("590", "Dönem Net Kârı", "Equity", "Balance Sheet", None),
    ("591", "Dönem Net Zararı(-)", "Equity", "Balance Sheet", None),
    ("6", "Gelir Tablosu Hesapları", "Income", "Balance Sheet", None),
    ("60", "Brüt Satışlar", "Expense", "Profit and Loss", None),
    ("600", "Yurt İçi Satışlar", "Income", "Profit and Loss", None),
    ("601", "Yurt Dışı Satışlar", "Income", "Profit and Loss", None),
    ("602", "Diğer Gelirler", "Income", "Profit and Loss", None),
    ("61", "Satış İndirimleri(-)", "Expense", "Profit and Loss", None),
    ("610", "Satıştan İadeler(-)", "Expense", "Profit and Loss", None),
    ("611", "Satış İndirimleri(-)", "Expense", "Profit and Loss", None),
    ("612", "Diğer İndirimler(-)", "Expense", "Profit and Loss", None),
    ("62", "Satışların Maliyeti(-)", "Expense", "Profit and Loss", None),
    ("620", "Satılan Mamuller Maliyeti(-)", "Expense", "Profit and Loss", None),
    ("621", "Satılan Ticari Mallar Maliyeti(-)", "Expense", "Profit and Loss", None),
    ("622", "Satılan Hizmet Maliyeti(-)", "Expense", "Profit and Loss", None),
    ("623", "Diğer Satışların Maliyeti(-)", "Expense", "Profit and Loss", None),
    ("63", "Faaliyet Giderleri(-)", "Expense", "Profit and Loss", None),
    ("630", "Araştırma ve Geliştirme Giderleri(-)", "Expense", "Profit and Loss", None),
    ("631", "Pazarlama Satış ve Dağıtım Giderleri(-)", "Expense", "Profit and Loss", None),
    ("632", "Genel Yönetim Giderleri(-)", "Expense", "Profit and Loss", None),
    ("64", "Diğer Faaliyetlerden Olağan Gelir ve Kârlar", "Expense", "Profit and Loss", None),
    ("640", "İştiraklerden Temettü Gelirleri", "Income", "Profit and Loss", None),
    ("641", "Bağlı Ortaklıklardan Temettü Gelirleri", "Income", "Profit and Loss", None),
    ("642", "Faiz Gelirleri", "Income", "Profit and Loss", None),
    ("643", "Komisyon Gelirleri", "Income", "Profit and Loss", None),
    ("644", "Konusu Kalmayan Karşılıklar", "Income", "Profit and Loss", None),
    ("645", "Menkul Kıymet Satış Kârları", "Income", "Profit and Loss", None),
    ("646", "Kambiyo Kârları", "Income", "Profit and Loss", None),
    ("647", "Reeskont Faiz Gelirleri", "Income", "Profit and Loss", None),
    ("648", "Enflasyon Düzeltme Kârları", "Income", "Profit and Loss", None),
    ("649", "Diğer Olağan Gelir ve Kârlar", "Income", "Profit and Loss", None),
    ("65", "Diğer Faaliyetlerden Olağan Gider ve Zararlar(-)", "Expense", "Profit and Loss", None),
    ("653", "Komisyon Giderleri(-)", "Expense", "Profit and Loss", None),
    ("654", "Karşılık Giderleri(-)", "Expense", "Profit and Loss", None),
    ("655", "Menkul Kıymet Satış Zararları(-)", "Expense", "Profit and Loss", None),
    ("656", "Kambiyo Zararları(-)", "Expense", "Profit and Loss", None),
    ("657", "Reeskont Faiz Giderleri(-)", "Expense", "Profit and Loss", None),
    ("658", "Enflasyon Düzeltmesi Zararları(-)", "Expense", "Profit and Loss", None),
    ("659", "Diğer Olağan Gider ve Zararlar(-)", "Expense", "Profit and Loss", None),
    ("66", "Finansman Giderleri(-)", "Expense", "Profit and Loss", None),
    ("660", "Kısa Vadeli Borçlanma Giderleri(-)", "Expense", "Profit and Loss", None),
    ("661", "Uzun Vadeli Borçlanma Giderleri(-)", "Expense", "Profit and Loss", None),
    ("67", "Olağan Dışı Gelir ve Kârlar", "Expense", "Profit and Loss", None),
    ("671", "Önceki Dönem Gelir ve Kârları", "Income", "Profit and Loss", None),
    ("679", "Diğer Olağan Dışı Gelir ve Kârlar", "Income", "Profit and Loss", None),
    ("68", "Olağan Dışı Gider ve Zararlar(-)", "Expense", "Profit and Loss", None),
    ("680", "Çalışmayan Kısım Gider ve Zararları(-)", "Expense", "Profit and Loss", None),
    ("681", "Önceki Dönem Gider ve Zararları(-)", "Expense", "Profit and Loss", None),
    ("689", "Diğer Olağan Dışı Gider ve Zararlar(-)", "Expense", "Profit and Loss", None),
    ("69", "Dönem Net Kârı Veya Zararı", "Expense", "Profit and Loss", None),
    ("690", "Dönem Kârı Veya Zararı", "Expense", "Profit and Loss", None),
    ("691", "Dönem Kârı Vergi ve Diğer Yasal Yükümlülük Karşılıkları(-)", "Expense", "Profit and Loss", None),
    ("692", "Dönem Net Kârı Veya Zararı", "Expense", "Profit and Loss", None),
    ("697", "Yıllara Yaygın İnşaat ve Enflasyon Düzeltme Hesabı", "Expense", "Profit and Loss", None),
    ("698", "Enflasyon Düzeltme Hesabı", "Expense", "Profit and Loss", None),
    ("7", "Maliyet Hesapları", "Expense", "Balance Sheet", None),
    ("70", "Maliyet Muhasebesi Bağlantı Hesapları", "Expense", "Profit and Loss", None),
    ("700", "Maliyet Muhasebesi Bağlantı Hesabı", "Expense", "Profit and Loss", None),
    ("701", "Maliyet Muhasebesi Yansıtma Hesabı", "Expense", "Profit and Loss", None),
    ("71", "Direkt İlk Madde ve Malzeme Giderleri", "Expense", "Profit and Loss", None),
    ("710", "Direkt İlk Madde ve Malzeme Giderleri Hesabı", "Expense", "Profit and Loss", None),
    ("711", "Direkt İlk Madde ve Malzeme Yansıtma Hesabı", "Expense", "Profit and Loss", None),
    ("712", "Direkt İlk Madde ve Malzeme Fiyat Farkı", "Expense", "Profit and Loss", None),
    ("713", "Direkt İlk Madde ve Malzeme Miktar Farkı", "Expense", "Profit and Loss", None),
    ("72", "Direkt İşçilik Giderleri", "Expense", "Profit and Loss", None),
    ("720", "Direkt İşçilik Giderleri", "Expense", "Profit and Loss", None),
    ("721", "Direkt İşçilik Giderleri Yansıtma Hesabı", "Expense", "Profit and Loss", None),
    ("722", "Direkt İşçilik Ücret Farkları", "Expense", "Profit and Loss", None),
    ("723", "Direkt İşçilik Süre Farkları", "Expense", "Profit and Loss", None),
    ("73", "Genel Üretim Giderleri", "Expense", "Profit and Loss", None),
    ("730", "Genel Üretim Giderleri", "Expense", "Profit and Loss", None),
    ("731", "Genel Üretim Giderleri Yansıtma Hesabı", "Expense", "Profit and Loss", None),
    ("732", "Genel Üretim Giderleri Bütçe Farkları", "Expense", "Profit and Loss", None),
    ("733", "Genel Üretim Giderleri Verimlilik Giderleri", "Expense", "Profit and Loss", None),
    ("734", "Genel Üretim Giderleri Kapasite Farkları", "Expense", "Profit and Loss", None),
    ("74", "Hizmet Üretim Maliyeti", "Expense", "Profit and Loss", None),
    ("740", "Hizmet Üretim Maliyeti", "Expense", "Profit and Loss", None),
    ("741", "Hizmet Üretim Maliyeti Yansıtma Hesabı", "Expense", "Profit and Loss", None),
    ("742", "Hizmet Üretim Maliyeti Fark Hesapları", "Expense", "Profit and Loss", None),
    ("75", "Araştırma ve Geliştirme Giderleri", "Expense", "Profit and Loss", None),
    ("750", "Araştırma ve Geliştirme Giderleri", "Expense", "Profit and Loss", None),
    ("751", "Araştırma ve Geliştirme Giderleri Yansıtma Hesabı", "Expense", "Profit and Loss", None),
    ("752", "Araştırma ve Geliştirme Gider Farkları", "Expense", "Profit and Loss", None),
    ("76", "Pazarlama Satış ve Dağıtım Giderleri", "Expense", "Profit and Loss", None),
    ("760", "Pazarlama Satış ve Dağıtım Giderleri", "Expense", "Profit and Loss", None),
    ("761", "Pazarlama Satış ve Dağıtım Giderleri Yansıtma Hesabı", "Expense", "Profit and Loss", None),
    ("762", "Pazarlama Satış ve Dağıtım Giderleri Fark Hesabı", "Expense", "Profit and Loss", None),
    ("77", "Genel Yönetim Giderleri", "Expense", "Profit and Loss", None),
    ("770", "Genel Yönetim Giderleri", "Expense", "Profit and Loss", None),
    ("771", "Genel Yönetim Giderleri Yansıtma Hesabı", "Expense", "Profit and Loss", None),
    ("772", "Genel Yönetim Gider Farkları Hesabı", "Expense", "Profit and Loss", None),
    ("78", "Finansman Giderleri", "Expense", "Profit and Loss", None),
    ("780", "Finansman Giderleri", "Expense", "Profit and Loss", None),
    ("781", "Finansman Giderleri Yansıtma Hesabı", "Expense", "Profit and Loss", None),
    ("782", "Finansman Giderleri Fark Hesabı", "Expense", "Profit and Loss", None),
    ("79", "Gider Çeşitleri", "Expense", "Profit and Loss", None),
    ("790", "İlk Madde ve Malzeme Giderleri", "Expense", "Profit and Loss", None),
    ("791", "İşçi Ücret ve Giderleri", "Expense", "Profit and Loss", None),
    ("792", "Memur Ücret ve Giderleri", "Expense", "Profit and Loss", None),
    ("793", "Dışarıdan Sağlanan Fayda ve Hizmetler", "Expense", "Profit and Loss", None),
    ("794", "Çeşitli Giderler", "Expense", "Profit and Loss", None),
    ("795", "Vergi, Resim ve Harçlar", "Expense", "Profit and Loss", None),
    ("796", "Amortismanlar ve Tükenme Payları", "Expense", "Profit and Loss", "Depreciation"),
    ("797", "Finansman Giderleri", "Expense", "Profit and Loss", None),
    ("798", "Gider Çeşitleri Yansıtma Hesabı", "Expense", "Profit and Loss", None),
    ("799", "Üretim Maliyet Hesabı", "Expense", "Profit and Loss", None),
)

THP: tuple[HesapKaydi, ...] = tuple(HesapKaydi(*kayit) for kayit in _HAM)

_GRUP_KODLARI: frozenset[str] = frozenset(k.kod for k in THP if len(k.kod) <= 2)


def thp_dogrula() -> list[str]:
    """Set tutarlılık denetimi: hata listesi (boş liste = temiz)."""
    hatalar: list[str] = []
    gorulen: set[str] = set()
    for hesap in THP:
        if hesap.kod in gorulen:
            hatalar.append(f"Kod tekrarı: {hesap.kod}")
        gorulen.add(hesap.kod)
        if hesap.kok_tur not in TURLER:
            hatalar.append(f"Geçersiz kök türü ({hesap.kod}): {hesap.kok_tur}")
        if hesap.rapor_tur not in RAPOR_TURLERI:
            hatalar.append(f"Geçersiz rapor türü ({hesap.kod}): {hesap.rapor_tur}")
        if len(hesap.kod) > 1:
            ebeveyn = hesap.kod[: len(hesap.kod) - 1]
            if ebeveyn not in _GRUP_KODLARI:
                hatalar.append(f"Ebeveyn bulunamadı ({hesap.kod} -> {ebeveyn})")
    return hatalar


def grup_kodlari() -> frozenset[str]:
    """Grup (1-2 haneli) hesap kodlarını döndürür."""
    return _GRUP_KODLARI


def ebeveyn_kodu(kod: str) -> str | None:
    """Hesabın THP ebeveyn kodu; 1 haneli köklerde None."""
    return kod[: len(kod) - 1] if len(kod) > 1 else None


def kod_ile(kod: str) -> HesapKaydi:
    """Koda göre hesabı bulur; yoksa KeyError fırlatır."""
    for hesap in THP:
        if hesap.kod == kod:
            return hesap
    raise KeyError(f"{kod} kodlu THP hesabı bulunamadı")
