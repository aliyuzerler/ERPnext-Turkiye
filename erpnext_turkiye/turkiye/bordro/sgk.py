"""SGK kesinti hesabı (SAF Python) — 2026 yılı parametreleriyle.

Kaynaklar (tutarlar birebir doğrulanmıştır):
- ÇSGB resmî asgari ücret sayfası (csgb.gov.tr/poco-pages/asgari-ucret,
  01.01.2026-31.12.2026): brüt asgari ücret 33.030,00 TL (günlük 1.101,00);
  SGK işçi payı %14 -> 4.624,20; işsizlik sigortası işçi payı %1 -> 330,30;
  kesintiler toplamı 4.954,50; net 28.075,50 (sayfa GV+DV hesaplamaz —
  asgari ücrette gelir ve damga vergisi tam muafiyet düzenlemesiyle
  fiilen elde kalan da 28.075,50'dir).
- İşveren payı (ÇSGB tablosu): indirimsiz %21,75 -> 7.184,03; 2 puan
  indirimli %19,75 -> 6.523,43; 5 puan (imalat) %16,75 -> 5.532,53;
  işsizlik sigortası işveren payı %2 -> 660,60.
- Tablo puan farklarının dayanağı: 5510 s.K. geçici m. 10 (5 puan işveren
  indirimi) ve 7463 s.K. (5 milyar TL üstü net satış ve 100+ çalışan
  işverene +1 puan ek prim). Baz işveren payı %20,75'tir (5510 m. 82
  %20,5 + kısa vadeli kolun 2026'daki %2,25'e yükselmesi).

Hesaplamalar yarım yukarı (half-up) iki haneye yuvarlanır (bordro usulü).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import ROUND_HALF_UP, Decimal

ASGARI_BRUT_UCRET_2026 = 33030.00  # aylık brüt (ÇSGB)
ASGARI_GUNLUK_BRUT_2026 = 1101.00
ASGARI_NET_UCRET_2026 = 28075.50  # brüt - SGK işçi kesintileri (GV+DV muaf)


@dataclass(frozen=True)
class SGKOranlari:
    """2026 SGK oranları; işveren payı puan ayarlamalarıyla türetilebilir."""

    isci_prim: float = 0.14
    isci_isssizlik: float = 0.01
    isveren_prim: float = 0.2075  # baz: %20,5 + kısa vadeli %0,25
    isveren_isssizlik: float = 0.02


def kesinti(tutar: float, oran: float) -> float:
    """``tutar * oran``'ı bordro usulüyle (yarım yukarı, 2 hane) döndürür."""
    ham = Decimal(str(tutar)) * Decimal(str(oran))
    return float(ham.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def isci_kesintileri(brut: float, oranlar: SGKOranlari | None = None) -> dict[str, float]:
    """Çalışan kesintileri: sgk (%14), isssizlik (%1), toplam."""
    o = oranlar or SGKOranlari()
    sgk = kesinti(brut, o.isci_prim)
    isssizlik = kesinti(brut, o.isci_isssizlik)
    toplam = float(
        (Decimal(str(sgk)) + Decimal(str(isssizlik))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    )
    return {"sgk": sgk, "isssizlik": isssizlik, "toplam": toplam}


def isveren_maliyeti(
    brut: float, isveren_prim: float = 0.2075, oranlar: SGKOranlari | None = None
) -> dict[str, float]:
    """İşveren kesintileri ve toplam maliyeti (brüt + işveren payları).

    ``isveren_prim``: baz %20,75; 2 puan indirimli işveren %19,75;
    5 puan (imalat) %16,75; ÇSGB tablosundaki indirimsiz senaryo
    (%21,75) = %20,75 + 7463 s.K. ek 1 puan — ``+0.01`` ile verilir.
    """
    o = oranlar or SGKOranlari()
    sgk = kesinti(brut, isveren_prim)
    isssizlik = kesinti(brut, o.isveren_isssizlik)
    toplam = float(
        (
            Decimal(str(brut)) + Decimal(str(sgk)) + Decimal(str(isssizlik))
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    )
    return {"sgk": sgk, "isssizlik": isssizlik, "toplam_isveren": toplam}


def asgari_tablo_dogrula() -> dict[str, bool]:
    """ÇSGB 2026 asgari ücret tablosunu yeniden hesaplayıp doğrular."""
    k = isci_kesintileri(ASGARI_BRUT_UCRET_2026)
    net = float(
        (Decimal(str(ASGARI_BRUT_UCRET_2026)) - Decimal(str(k["toplam"]))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    )
    return {
        "sgk_i": k["sgk"] == 4624.20,
        "isssizlik_i": k["isssizlik"] == 330.30,
        "kesinti_toplam": k["toplam"] == 4954.50,
        "net": net == ASGARI_NET_UCRET_2026,
        "isveren_indirimsiz": isveren_maliyeti(ASGARI_BRUT_UCRET_2026, 0.2175)["sgk"] == 7184.03,
        "isveren_2_puan": isveren_maliyeti(ASGARI_BRUT_UCRET_2026, 0.1975)["sgk"] == 6523.43,
        "isveren_5_puan": isveren_maliyeti(ASGARI_BRUT_UCRET_2026, 0.1675)["sgk"] == 5532.53,
        "isveren_isssizlik": isveren_maliyeti(ASGARI_BRUT_UCRET_2026, 0.2175)[
            "isssizlik"
        ] == 660.60,
        "isveren_toplam": isveren_maliyeti(ASGARI_BRUT_UCRET_2026, 0.2175)[
            "toplam_isveren"
        ] == 40874.63,
    }


def puan_indirimi(oranda: SGKOranlari, puan: float) -> SGKOranlari:
    """İşveren prim oranını ``puan`` kadar düşürür (geçici m. 10 vb.)."""
    return replace(oranda, isveren_prim=round(oranda.isveren_prim - puan, 4))
