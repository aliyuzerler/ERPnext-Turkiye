"""Bordro vergileri: gelir vergisi tarifesi + damga vergisi (SAF Python).

Kaynaklar:
- Gelir vergisi tarifesi 2026 (GİB resmî PDF: gelir-vergisi-tarifesi-2026):
  ücret gelirlerinde 190.000 TL'ye kadar %15; 400.000 TL'nin 190.000 TL'si
  için 28.500 TL, fazlası %20; 1.500.000 TL'nin 400.000 TL'si için
  325.500 TL, fazlası %35; 5.300.000 TL'nin 1.500.000 TL'si için
  1.655.500 TL, fazlası %40.
- Damga vergisi: ücret ödemelerinde binde 7,59 (2026'da da geçerli).

Bordro usulü: gelir vergisi kümülatif matrah üzerinden yıllık tarifeyle
hesaplanır; ay vergisi = yıllık(kümülatif + bu ay) - yıllık(kümülatif).
Asgari ücret brütü ve altındaki ücretlerde GV ve DV tam muafiyet
uygulanır (asgari ücret istisnası, 2022'den bu yana ve 2026'da da).
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from erpnext_turkiye.turkiye.bordro.sgk import ASGARI_BRUT_UCRET_2026

DAMGA_ORANI = 0.00759  # binde 7,59

# (üst sınır, oran) — ücret gelirleri tarifesı 2026; üst sınır sonsuz = son dilim
GELIR_VERGISI_TARIFESI_2026_UCRET: tuple[tuple[float, float], ...] = (
    (190_000.0, 0.15),
    (400_000.0, 0.20),
    (1_500_000.0, 0.27),
    (5_300_000.0, 0.35),
    (float("inf"), 0.40),
)


def _yuvarla(x: float) -> float:
    return float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def yillik_gelir_vergisi(matrah: float) -> float:
    """Yıllık tarifeyle gelir vergisi (dilimler üzerinden)."""
    if matrah <= 0:
        return 0.0
    vergi = Decimal("0")
    onceki = Decimal("0")
    for ust, oran in GELIR_VERGISI_TARIFESI_2026_UCRET:
        dilim = Decimal(str(min(matrah, ust))) - onceki
        if dilim <= 0:
            break
        vergi += dilim * Decimal(str(oran))
        onceki = Decimal(str(ust))
    return _yuvarla(float(vergi))


def gelir_vergisi_aylik(brut: float, kumulatif_matrah: float) -> float:
    """Ayın gelir vergisi: kümülatif fark yöntemi (bordro usulü).

    Vergiye tabi matrah = brüt - SGK işçi kesintileri (kümülatife eklemeden
    önce kesintiler düşülür).
    """
    from erpnext_turkiye.turkiye.bordro.sgk import isci_kesintileri

    ay_matrahi = brut - isci_kesintileri(brut)["toplam"]
    if ay_matrahi <= 0:
        return 0.0
    yeni_kumulatif = kumulatif_matrah + ay_matrahi
    fark = yillik_gelir_vergisi(yeni_kumulatif) - yillik_gelir_vergisi(kumulatif_matrah)
    return _yuvarla(max(fark, 0.0))


def damga_vergisi(brut: float) -> float:
    """Damga vergisi: brüt ücret üzerinden binde 7,59 (yarım yukarı)."""
    return _yuvarla(float(Decimal(str(brut)) * Decimal(str(DAMGA_ORANI))))


def bordro_hesapla(brut: float, kumulatif_matrah: float = 0.0) -> dict[str, float]:
    """Tek ay bordro özeti (2026 parametreleriyle).

    Asgari ücret brütü ve altındaki ücretlerde GV ve DV sıfırdır
    (tam muafiyet). Dönüş: sgk, isssizlik, gv, dv, kesinti_toplam, net.
    """
    from erpnext_turkiye.turkiye.bordro.sgk import isci_kesintileri

    kesintiler = isci_kesintileri(brut)
    muaf = brut <= ASGARI_BRUT_UCRET_2026
    gv = 0.0 if muaf else gelir_vergisi_aylik(brut, kumulatif_matrah)
    dv = 0.0 if muaf else damga_vergisi(brut)
    toplam = float(
        (
            Decimal(str(kesintiler["toplam"])) + Decimal(str(gv)) + Decimal(str(dv))
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    )
    net = _yuvarla(float(Decimal(str(brut)) - Decimal(str(toplam))))
    return {
        "sgk": kesintiler["sgk"],
        "isssizlik": kesintiler["isssizlik"],
        "gv": gv,
        "dv": dv,
        "kesinti_toplam": toplam,
        "net": net,
    }
