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
from typing import Any
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
        # boş elemanlar (yalnızca çapraz kuru olan kayıtlar) None sayılır
        alis = cur.findtext("ForexBuying") or None
        satis = cur.findtext("ForexSelling") or None
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

    Faz 2'de ``scheduler_events`` üzerinden günlük çalıştırılır ve sonuçlar
    Currency Exchange kayıtlarına yazılır.
    """
    istek = Request(url, headers={"User-Agent": "erpnext-turkiye/0.1"})
    with urlopen(istek, timeout=timeout) as yanit:
        veri = yanit.read()
    return parse_kurlar(veri.decode("utf-8"))


# ---------------------------------------------------------------------------
# Site tarafı: Currency Exchange güncelleme (frappe gövde içinde import)
# ---------------------------------------------------------------------------

ONCELI_KURLAR: tuple[str, ...] = ("USD", "EUR", "GBP")
HEDEF_KUR = "TRY"


def kur_guncelle(kodlar: tuple[str, ...] = ONCELI_KURLAR) -> dict[str, float]:
    """TCMB bülteninden kur çekip Currency Exchange kayıtlarını günceller.

    Kullanılan kur: TCMB döviz alış kuru (ForexBuying) — VUK 313'te döviz
    çeviriminde günlük döviz alış kuru referans alınır. Her kod için iki
    yönlü kayıt yazılır (kod->TRY ve TRY->kod); ERPNext get_exchange_rate
    iki yönü de bu kayıtlardan okur.
    """
    import frappe

    tarih, kayitlar = fetch_kurlar()
    sonuc: dict[str, float] = {}
    for kod in kodlar:
        kayit = get_kur(kayitlar, kod)
        if kayit.birim != 1:
            raise ValueError(f"{kod} bülten birimi 1 değil ({kayit.birim}); çeviri desteği gerekli")
        oran = kayit.alis
        ters_oran = round(1 / oran, 6)
        _kayit_yaz(frappe, kod, HEDEF_KUR, oran)
        _kayit_yaz(frappe, HEDEF_KUR, kod, ters_oran)
        sonuc[kod] = oran
    frappe.db.commit()
    frappe.logger("kur_servisi").info({"bulten": tarih, "kurlar": sonuc})
    return sonuc


def _kayit_yaz(frappe_module: Any, kaynak: str, hedef: str, oran: float) -> None:
    """Tek yön için Currency Exchange kaydını ekler ya da günceller."""
    filt = {"from_currency": kaynak, "to_currency": hedef, "for_buying": 1, "for_selling": 1}
    mevcut = frappe_module.db.exists("Currency Exchange", filt)
    if mevcut:
        frappe_module.db.set_value("Currency Exchange", mevcut, "exchange_rate", oran)
    else:
        frappe_module.get_doc(
            {
                "doctype": "Currency Exchange",
                "from_currency": kaynak,
                "to_currency": hedef,
                "exchange_rate": oran,
                "for_buying": 1,
                "for_selling": 1,
            }
        ).insert(ignore_permissions=True)


def gunluk_kur_coz() -> dict[str, float] | str:
    """``scheduler_events.daily`` girişi: ağ hatasında gece işini kilitlememek için kayda alır."""
    try:
        return kur_guncelle()
    except Exception:
        import frappe

        frappe.log_error(title="TCMB kur servisi günlük çekim başarısız")
        return "hata: ayrıntılar hata günlüğünde"
