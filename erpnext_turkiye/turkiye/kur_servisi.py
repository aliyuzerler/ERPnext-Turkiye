"""TCMB günlük döviz kuru servisi (yeni özellik 4, Faz 2).

Kaynak: ``https://www.tcmb.gov.tr/kurlar/today.xml`` — günlük bülten XML'i;
kök ``<Tarih_Date Tarih="..." Date="..." Bulten_No="...">`` ve altında
``<Currency Kod="USD" CurrencyCode="USD">`` kayıtları; döviz alış/satış
``ForexBuying`` / ``ForexSelling`` alt elemanlarında tutulur.

``parse_kurlar`` SAF fonksiyondur; ağ erişimi yalnızca ``fetch_kurlar``'dadır
ve birim testlerinde sahte (fake) opener ile hermetik koşar.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from urllib.request import Request, urlopen

TCMB_URL = "https://www.tcmb.gov.tr/kurlar/today.xml"


@dataclass(frozen=True)
class KurKaydi:
    """Bülten içindeki tek döviz kaydı."""

    kod: str
    isim: str
    birim: int
    alis: float
    satis: float


def parse_kurlar(xml_metni: str) -> tuple[str, list[KurKaydi]]:
    """Bülten XML'ini ayrıştırır: ``(bulten_tarihi, kayitlar)`` döndürür.

    Döviz alış/satış değeri bulunmayan kayıtlar (yalnızca çapraz kuru olanlar)
    atlanır.
    """
    kok = ET.fromstring(xml_metni)
    tarih = kok.get("Tarih") or kok.get("Date") or ""
    kayitlar: list[KurKaydi] = []
    for cur in kok.findall("Currency"):
        kod = cur.get("Kod") or ""
        alis = cur.findtext("ForexBuying")
        satis = cur.findtext("ForexSelling")
        if not kod or alis is None or satis is None:
            continue
        birim_metni = cur.findtext("Unit") or "1"
        kayitlar.append(
            KurKaydi(
                kod=kod,
                isim=(cur.findtext("Isim") or "").strip(),
                birim=int(birim_metni),
                alis=float(alis),
                satis=float(satis),
            )
        )
    return tarih, kayitlar


def get_kur(kayitlar: list[KurKaydi], kod: str) -> KurKaydi:
    """Kayıtlar içinde istenen para birimini bulur; yoksa KeyError fırlatır."""
    for kayit in kayitlar:
        if kayit.kod == kod:
            return kayit
    raise KeyError(f"{kod} kuru bu bültende bulunamadı")


def fetch_kurlar(url: str = TCMB_URL, timeout: int = 30) -> tuple[str, list[KurKaydi]]:
    """TCMB günlük bültenini indirir ve ayrıştırır.

    Faz 2'de ``scheduler_events`` üzerinden günlük çalıştırılacak ve sonuçlar
    Currency Exchange kayıtlarına yazılacaktır.
    """
    istek = Request(url, headers={"User-Agent": "erpnext-turkiye/0.1"})
    with urlopen(istek, timeout=timeout) as yanit:
        veri = yanit.read()
    return parse_kurlar(veri.decode("utf-8"))
