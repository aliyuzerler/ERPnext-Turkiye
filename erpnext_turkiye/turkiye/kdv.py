"""KDV oranları ve hesap yardımcıları.

Güncel genel geçer oranlar: %1, %10, %20. Tevkifat kod kataloğu (GİB
e-Fatura kod listesi) Faz 3'te UBL-TR eşleme paketiyle eklenir; burada
yalnızca kesir üzerinden hesap yapan genel fonksiyon bulunur.

Bu modül SAF Python'dur; frappe import etmez.
"""

from __future__ import annotations

ORANLAR: tuple[int, ...] = (1, 10, 20)


def kdv_hesapla(matrah: float, oran: int) -> float:
    """Matrahın KDV tutarını, verilen orana göre 2 hane hassasiyetle döndürür."""
    if oran not in ORANLAR:
        raise ValueError(f"Geçersiz KDV oranı: {oran}. Beklenen: {ORANLAR}")
    if matrah < 0:
        raise ValueError("Matrah negatif olamaz")
    return round(matrah * oran / 100, 2)


def tevkifat_hesapla(matrah: float, oran: int, pay: int, payda: int) -> tuple[float, float]:
    """Tevkifatlı KDV dağılımını döndürür: ``(satici_yuklulugu, tevkif_edilen)``.

    Örnek: ``tevkifat_hesapla(1000, 20, 9, 10)`` -> ``(20.0, 180.0)``
    (200 KDV'nin 9/10'u tevkif edilir).
    """
    if payda <= 0 or pay <= 0 or pay > payda:
        raise ValueError(f"Tevkifat kesri geçersiz: {pay}/{payda}")
    kdv = kdv_hesapla(matrah, oran)
    tevkif_edilen = round(kdv * pay / payda, 2)
    satici_yuklulugu = round(kdv - tevkif_edilen, 2)
    return satici_yuklulugu, tevkif_edilen
