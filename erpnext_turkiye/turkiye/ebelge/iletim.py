"""Entegratör bağımsız iletim çekirdeği (SAF Python).

Adaptör sözleşmesi: herhangi bir entegratör (Foriba, Uyumsoft, Veriban,
Logo, GİB portal aracısı) UBL XML'i alır, entegratör cevabını döndürür.
Kuyruk çekirdeği entegratörden bağımsızdır: başarısız denemeleri **üstel
geri çekilme** (exponential backoff) ile yeniler; her kayıt için nihai
sonucu raporlar. Site tarafı (``olaylari.py``) Frappe kuyruğunu buraya
bağlar; çekirdek hiçbir kuyruk teknolojisine bağımlı değildir.

Bu modül SAF Python'dur; frappe import etmez.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol


class EntegratorAdaptoru(Protocol):
    """Adaptör sözleşmesi: bir UBL XML'i gönderip cevap metni döndürür.

    Gönderim hatası ``Exception`` (tercihen ``RuntimeError``) olarak
    fırlatılır; kuyruk çekirdeği bunu yeniden deneme sinyali sayar.
    """

    def gonder(self, xml: str) -> str: ...


@dataclass(frozen=True)
class KuyrukKaydi:
    """Gönderim kuyruğundaki tek kayıt."""

    kimlik: str
    xml: str


@dataclass(frozen=True)
class Sonuc:
    """Tek kaydın nihai iletim sonucu."""

    kimlik: str
    durum: str  # "Gonderildi" | "Hata"
    cevap: str = ""
    hata: str = ""
    deneme_sayisi: int = 0


def bekleme_suresi(deneme: int, taban: float = 2.0, ust_limit: float = 60.0) -> float:
    """Üstel geri çekilme: ``taban ** deneme``, ``ust_limit`` ile sınırlı.

    ``deneme`` 1'den başlar: 1. yeniden deneme öncesi taban, 2. öncesi
    taban² vb. beklenir.
    """
    return min(taban**deneme, ust_limit)


def kuyruk_isle(
    kayitlar: list[KuyrukKaydi],
    gonder: Callable[[str], str],
    max_deneme: int = 3,
    taban: float = 2.0,
    saat: Callable[[float], None] = time.sleep,
) -> list[Sonuc]:
    """Kayıtları sırayla gönderir; hatalarda üstel geri çekilmeyle yeniler.

    ``saat`` testlerde sahte (fake) saatle değiştirilir; gerçek koşumda
    ``time.sleep`` kullanılır. Aynı kayıt için ``max_deneme`` kez denenir;
    tüm denemeler başarısızsa son hata kaydıyla "Hata" sonucu döner.
    """
    sonuclar: list[Sonuc] = []
    for kayit in kayitlar:
        son_sonuc: Sonuc | None = None
        for deneme in range(1, max_deneme + 1):
            try:
                cevap = gonder(kayit.xml)
                son_sonuc = Sonuc(
                    kayit.kimlik, "Gonderildi", cevap=cevap, deneme_sayisi=deneme
                )
                break
            except Exception as hata:
                son_sonuc = Sonuc(kayit.kimlik, "Hata", hata=str(hata), deneme_sayisi=deneme)
                if deneme < max_deneme:
                    saat(bekleme_suresi(deneme, taban))
        if son_sonuc is not None:
            sonuclar.append(son_sonuc)
    return sonuclar
