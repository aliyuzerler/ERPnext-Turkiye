"""Yıllık izin süreleri (4857 s.K. m. 53) + 2026 resmî tatiller (SAF Python).

Kaynaklar:
- 4857 s.K. m. 53: bir yılı dolduran işçiye 14 gün; 5 yılı dolduranlara
  20 gün; 15 yılı dolduranlara 26 gün. On sekiz yaşından küçük ve öğrenim
  çağında olan işçilere en az 20 gün (m. 53/5).
- Ulusal Bayram ve Genel Tatiller Hakkında Kanun (2429 s.K.) uyarınca
  2026 resmî tatilleri: toplam 15,5 gün (arifeler dahil; 28 Ekim 13.00
  itibarıyla yarım gün). Ramazan Bayramı 3 gün (20-22 Mart, arife 19 Mart
  yarım gün), Kurban Bayramı 4 gün (27-30 Mayıs, arife 26 Mayıs yarım gün).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResmiTatil:
    tarih: str  # YYYY-MM-DD
    ad: str
    yarim_gun: bool = False


RESMI_TATILLER_2026: tuple[ResmiTatil, ...] = (
    ResmiTatil("2026-01-01", "Yılbaşı"),
    ResmiTatil("2026-03-19", "Ramazan Bayramı Arifesi", yarim_gun=True),
    ResmiTatil("2026-03-20", "Ramazan Bayramı 1. Gün"),
    ResmiTatil("2026-03-21", "Ramazan Bayramı 2. Gün"),
    ResmiTatil("2026-03-22", "Ramazan Bayramı 3. Gün"),
    ResmiTatil("2026-04-23", "Ulusal Egemenlik ve Çocuk Bayramı"),
    ResmiTatil("2026-05-01", "Emek ve Dayanışma Günü"),
    ResmiTatil("2026-05-19", "Atatürk'ü Anma, Gençlik ve Spor Bayramı"),
    ResmiTatil("2026-05-26", "Kurban Bayramı Arifesi", yarim_gun=True),
    ResmiTatil("2026-05-27", "Kurban Bayramı 1. Gün"),
    ResmiTatil("2026-05-28", "Kurban Bayramı 2. Gün"),
    ResmiTatil("2026-05-29", "Kurban Bayramı 3. Gün"),
    ResmiTatil("2026-05-30", "Kurban Bayramı 4. Gün"),
    ResmiTatil("2026-07-15", "Demokrasi ve Millî Birlik Günü"),
    ResmiTatil("2026-08-30", "Zafer Bayramı"),
    ResmiTatil("2026-10-28", "Cumhuriyet Bayramı Arifesi (13.00 itibarıyla)", yarim_gun=True),
    ResmiTatil("2026-10-29", "Cumhuriyet Bayramı"),
)


def toplam_tatil_gunu(yil: int = 2026) -> float:
    """Resmî tatil toplamı (yarım günler 0,5 sayılır; kanuni usul)."""
    toplam = sum(0.5 if t.yarim_gun else 1.0 for t in RESMI_TATILLER_2026)
    return float(toplam) if yil == 2026 else 0.0


def yillik_izin_suresi(hizmet_yili: int, kucuk_yasli_mi: bool = False) -> int:
    """4857 m. 53'e göre yıllık ücretli izin günü.

    ``kucuk_yasli_mi``: 18 yaşından küçük ve öğrenim çağında olan işçi
    (kanun: en az 20 gün).
    """
    if hizmet_yili < 1:
        return 0
    if kucuk_yasli_mi:
        return 20
    if hizmet_yili >= 15:
        return 26
    if hizmet_yili >= 5:
        return 20
    return 14
