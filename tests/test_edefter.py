"""e-Defter SAF modülü testleri — GİB kılavuz kurallarıyla sınama.

Kaynaklar: GİB e-Defter Uygulama Kılavuzu (XBRL-GL zorunluluğu,
yevmiye/kebir ayrı berat, ZIP iki dosya kuralı) + 4857T/VUK çerçevesi.
"""

from __future__ import annotations

import zipfile

import pytest

from erpnext_turkiye.turkiye.edefter.berat import (
    arsivle,
    kebir_berat,
    paket_dogrula,
    paketle,
    yevmiye_berat,
)
from erpnext_turkiye.turkiye.edefter.xbrlgl import (
    YevmiyeKayit,
    YevmiyeSatir,
    kebir_ozeti,
    xbrlgl_yevmiye,
)

VKN = "3456789014"  # demo mükellef (FAZ2 km2 faturasının alıcısıyla uyumlu)
UNVAN = "Anadolu Makine Sanayi A.Ş."

KAYITLAR = [
    YevmiyeKayit(
        tarih="2026-03-15",
        yevmiye_no="2026-001",
        aciklama="Satış faturası ACC-SINV-2026-00001 (KDV %20)",
        kaydi_giren="muhasebe",
        satirlar=(
            YevmiyeSatir("120 01", "Alıcılar", 12000.0, 0.0, "Anadolu Ticaret Ltd. Şti."),
            YevmiyeSatir("600 01", "Yurt İçi Satışlar", 0.0, 10000.0),
            YevmiyeSatir("391 01", "Hesaplanan KDV", 0.0, 2000.0),
        ),
    ),
    YevmiyeKayit(
        tarih="2026-03-16",
        yevmiye_no="2026-002",
        aciklama="Nakit tahsilat",
        kaydi_giren="muhasebe",
        satirlar=(
            YevmiyeSatir("100 01", "Kasa", 5000.0, 0.0),
            YevmiyeSatir("120 01", "Alıcılar", 0.0, 5000.0),
        ),
    ),
]


def test_yevmiye_dengesi_kurali() -> None:
    """Kılavuz kuralı: her yevmiye maddesi borç=alacak; dengesiz reddedilir."""
    assert all(k.dengeli_mi() for k in KAYITLAR)
    dengesiz = YevmiyeKayit(
        tarih="2026-03-17",
        yevmiye_no="2026-003",
        aciklama="hatalı",
        kaydi_giren="muhasebe",
        satirlar=(
            YevmiyeSatir("100 01", "Kasa", 100.0, 0.0),
            YevmiyeSatir("120 01", "Alıcılar", 0.0, 90.0),
        ),
    )
    with pytest.raises(ValueError, match="Dengesiz yevmiye maddesi"):
        xbrlgl_yevmiye([*KAYITLAR, dengesiz], VKN, UNVAN, 2026)


def test_xbrlgl_yapisi() -> None:
    """XBRL-GL instance: kök, namespaces, entriesHeader/entryHeader/entryDetail."""
    xml = xbrlgl_yevmiye(KAYITLAR, VKN, UNVAN, 2026)
    assert xml.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert "<xbrli:xbrl" in xml and "int/gl/cor/2006-10-25" in xml
    assert "gl-cor:entriesHeader" in xml and "gl-cor:entryHeader" in xml
    assert xml.count("<gl-cor:entryDetail>") == 5  # 3+2 madde satırı
    assert "2026-001" in xml and "120 01" in xml
    assert ">12000.00<" in xml and ">10000.00<" in xml and ">2000.00<" in xml
    assert VKN in xml and "entityInformationPeriodCoveredStart>2026-01-01" in xml


def test_tutar_formati_ve_mantigi() -> None:
    """Borç satırı debitAmount, alacak satırı creditAmount; tutarlar 2 hane."""
    xml = xbrlgl_yevmiye(KAYITLAR, VKN, UNVAN, 2026)
    assert "entryDetailDebitAmount" in xml and "entryDetailCreditAmount" in xml
    assert ">12000.00<" in xml  # iki hane sabit
    # borç tutarı alacak alanında yazılmamalı (ayrı elementler)
    assert "<entryDetailCreditAmount>12000.00" not in xml


def test_kebir_ozeti_hesap_bazli() -> None:
    """Kebir görünümü: hesap kodu bazında borç/alacak/net toplamları."""
    ozet = kebir_ozeti(KAYITLAR)
    assert ozet["120 01"] == {"borc": 12000.0, "alacak": 5000.0, "net": 7000.0}
    assert ozet["600 01"] == {"borc": 0.0, "alacak": 10000.0, "net": -10000.0}
    assert ozet["391 01"]["alacak"] == 2000.0
    assert ozet["100 01"]["borc"] == 5000.0


def test_beratlar_ozet_ve_hash() -> None:
    """Berat defter içeriği taşımaz; kayıt sayısı ve hash'i taşır."""
    xml = xbrlgl_yevmiye(KAYITLAR, VKN, UNVAN, 2026)
    h = __import__("hashlib").sha256(xml.encode()).hexdigest()
    yb = yevmiye_berat(KAYITLAR, VKN, UNVAN, 2026, h)
    assert "<kayitSayisi>2</kayitSayisi>" in yb and h in yb
    assert "<defterTuru>Yevmiye</defterTuru>" in yb
    assert "120 01" not in yb  # madde içeriği taşınmaz
    kb = kebir_berat(KAYITLAR, VKN, UNVAN, 2026, h)
    assert "<defterTuru>Kebir</defterTuru>" in kb and 'kodu="120 01"' in kb
    assert "<hesapSayisi>4</hesapSayisi>" in kb
    assert "<zamanDamgasi>" not in yb and "<zamanDamgasi>" not in kb  # damga GİB işlevid
    yb_damgali = yevmiye_berat(KAYITLAR, VKN, UNVAN, 2026, h, "2026-12-31T10:00:00Z")
    assert "<zamanDamgasi>2026-12-31T10:00:00Z</zamanDamgasi>" in yb_damgali


def test_paket_iki_dosya_kurali_ve_arsiv(tmp_path: object) -> None:
    """Kılavuz: ZIP iki dosya (defter + berat); arşiv yil/tür dizini + manifest."""
    xml = xbrlgl_yevmiye(KAYITLAR, VKN, UNVAN, 2026)
    h = __import__("hashlib").sha256(xml.encode()).hexdigest()
    berat = yevmiye_berat(KAYITLAR, VKN, UNVAN, 2026, h)
    paket, manifest = paketle("yevmiye-2026.xml", xml, berat)
    assert len(manifest) == 2 and "yevmiye-2026-berat.xml" in manifest
    yol = arsivle(paket, manifest, str(tmp_path), 2026, "yevmiye")
    assert yol.endswith("2026/yevmiye/paket.zip")
    sonuc = paket_dogrula(yol)
    assert sonuc == {"iki_dosya": True, "hash": True, "mukerrer_degil": True}
    with zipfile.ZipFile(yol) as z:
        assert set(z.namelist()) == {"yevmiye-2026.xml", "yevmiye-2026-berat.xml"}


def test_paket_adi_cakismasi_reddedilir() -> None:
    """Defter adı '-berat.xml' soneki taşıyamaz (berat adı türetilir)."""
    with pytest.raises(ValueError, match="soneki"):
        paketle("berat-berat.xml", "<a/>", "<b/>")
