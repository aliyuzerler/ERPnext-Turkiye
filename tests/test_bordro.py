"""Bordro çekirdeği birim testleri — 2026 resmî tutarlarla birebir doğrulama.

Kaynak değerler: ÇSGB asgari ücret sayfası (csgb.gov.tr), GİB gelir vergisi
tarifesi 2026 PDF'i, 4857 s.K. m. 53, 2429 s.K. (2026 tatiller).
"""

from __future__ import annotations

from erpnext_turkiye.turkiye.bordro.izin import (
    RESMI_TATILLER_2026,
    toplam_tatil_gunu,
    yillik_izin_suresi,
)
from erpnext_turkiye.turkiye.bordro.sgk import (
    ASGARI_BRUT_UCRET_2026,
    asgari_tablo_dogrula,
    isci_kesintileri,
    isveren_maliyeti,
    kesinti,
)
from erpnext_turkiye.turkiye.bordro.vergi import (
    bordro_hesapla,
    damga_vergisi,
    gelir_vergisi_aylik,
    yillik_gelir_vergisi,
)


def test_csgb_asgari_tablo_birebir() -> None:
    """ÇSGB 2026 tablosundaki tüm tutarlar hesaptan yeniden üretilmeli."""
    dogrulama = asgari_tablo_dogrula()
    hatali = [k for k, ok in dogrulama.items() if not ok]
    assert not hatali, f"ÇSGB tablosuyla tutarsız: {hatali}"


def test_isci_kesintileri_birebir() -> None:
    k = isci_kesintileri(ASGARI_BRUT_UCRET_2026)
    assert k == {"sgk": 4624.20, "isssizlik": 330.30, "toplam": 4954.50}


def test_isveren_uc_senaryo_csgb_tablosu() -> None:
    """ÇSGB tablosundaki üç işveren senaryosu (indirimsiz/2 puan/5 puan)."""
    brut = ASGARI_BRUT_UCRET_2026
    # indirimsiz + 7463 ek puan: %21,75
    m = isveren_maliyeti(brut, 0.2175)
    assert m == {"sgk": 7184.03, "isssizlik": 660.60, "toplam_isveren": 40874.63}
    # 2 puan indirimli: %19,75
    m2 = isveren_maliyeti(brut, 0.1975)
    assert m2["sgk"] == 6523.43 and m2["toplam_isveren"] == 40214.03
    # 5 puan (imalat): %16,75
    m5 = isveren_maliyeti(brut, 0.1675)
    assert m5["sgk"] == 5532.53 and m5["toplam_isveren"] == 39223.13


def test_yarim_yukari_yuvarlama() -> None:
    assert kesinti(5532.525, 1.0) == 5532.53  # yarım yukarı (bordro usulü)
    assert kesinti(0.005, 1.0) == 0.01
    assert kesinti(0.004, 1.0) == 0.00


def test_tarife_dilim_sinirlari() -> None:
    """GİB 2026 ücret tarifesi tutarları: %35 satırı '5.300.000'in
    1.500.000'i için 367.500'le birebir eşleşmeli."""
    assert yillik_gelir_vergisi(190_000) == 28_500.0
    assert yillik_gelir_vergisi(400_000) == 70_500.0  # 28.500 + 210.000*%20
    assert yillik_gelir_vergisi(1_500_000) == 367_500.0  # 70.500 + 1.100.000*%27
    assert yillik_gelir_vergisi(5_300_000) == 1_697_500.0  # 367.500 + 3.800.000*%35
    assert yillik_gelir_vergisi(6_000_000) == 1_977_500.0  # + 700.000*%40
    assert yillik_gelir_vergisi(0) == 0.0


def test_asgari_ucret_gv_dv_muafiyet() -> None:
    """Asgari ücrette GV ve DV sıfır; net = ÇSGB net (28.075,50)."""
    b = bordro_hesapla(ASGARI_BRUT_UCRET_2026)
    assert b["gv"] == 0.0 and b["dv"] == 0.0
    assert b["net"] == 28075.50


def test_60bin_brut_ornek_kod_ile_hesap() -> None:
    """Brüt 60.000 (ay 1): kesintiler, GV, DV, net — kodun çıktısıyla eşleşir."""
    b = bordro_hesapla(60_000.0, kumulatif_matrah=0.0)
    # matrah = 60.000 - 8.400 - 600 = 51.000 -> GV %15 = 7.650
    assert b["sgk"] == 8_400.00 and b["isssizlik"] == 600.00
    assert b["gv"] == 7_650.00
    assert b["dv"] == 455.40  # 60.000 * binde 7,59
    assert b["net"] == 42_894.60


def test_kumulatif_ikinci_ay() -> None:
    """Ay 2: kümülatif matrah 102.000 -> GV farkı 7.650 (aynı dilimde)."""
    ay2 = gelir_vergisi_aylik(60_000.0, kumulatif_matrah=51_000.0)
    assert ay2 == 7_650.00


def test_damga_vergisi_binde_759() -> None:
    assert damga_vergisi(100_000.0) == 759.00
    assert damga_vergisi(60_000.0) == 455.40
    assert damga_vergisi(ASGARI_BRUT_UCRET_2026) == 250.70  # muafiyetsiz hesap


def test_yillik_izin_4857() -> None:
    assert yillik_izin_suresi(0) == 0
    assert yillik_izin_suresi(1) == 14
    assert yillik_izin_suresi(3) == 14
    assert yillik_izin_suresi(5) == 20
    assert yillik_izin_suresi(14) == 20
    assert yillik_izin_suresi(15) == 26
    assert yillik_izin_suresi(2, kucuk_yasli_mi=True) == 20


def test_resmi_tatiller_2026_toplam() -> None:
    """2429 s.K.: 2026 resmî tatil toplamı 15,5 gün (arifeler dahil)."""
    assert toplam_tatil_gunu(2026) == 15.5
    yarim = [t for t in RESMI_TATILLER_2026 if t.yarim_gun]
    assert len(yarim) == 3  # iki bayram arifesi + 28 Ekim 13.00
    tam = toplam_tatil_gunu(2026) - len(yarim) * 0.5
    assert tam == 14.0
    # Ramazan 3 gün, Kurban 4 gün (2429 m. 2/b)
    ramazan = sum(
        1 for t in RESMI_TATILLER_2026 if "Ramazan Bayramı" in t.ad and "Arife" not in t.ad
    )
    kurban = sum(
        1 for t in RESMI_TATILLER_2026 if "Kurban Bayramı" in t.ad and "Arife" not in t.ad
    )
    assert ramazan == 3 and kurban == 4
