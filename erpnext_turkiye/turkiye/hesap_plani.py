"""Tek Düzen Hesap Planı (THP) başlangıç veri seti (Faz 2 çekirdeği).

Faz 0'da yaygın hesapların çekirdek seti tanımlıdır; Faz 2'de tam plan,
hiyerarşi ve ERPNext hesap eşlemesiyle genişletilir.

Bu modül SAF Python'dur; frappe import etmez.
"""

from __future__ import annotations

from dataclasses import dataclass

TURLER: tuple[str, ...] = ("Varlık", "Yükümlülük", "Özkaynak", "Gelir", "Gider")


@dataclass(frozen=True)
class Hesap:
    """Tek Düzen hesap kaydı."""

    kod: str
    ad: str
    tur: str


BASLANGIC_THP: tuple[Hesap, ...] = (
    Hesap("100", "Hazır Değerler", "Varlık"),
    Hesap("102", "Bankalar", "Varlık"),
    Hesap("120", "Alıcılar", "Varlık"),
    Hesap("153", "Ticari Mallar", "Varlık"),
    Hesap("191", "İndirilecek KDV", "Varlık"),
    Hesap("213", "Borçlar", "Yükümlülük"),
    Hesap("320", "Satıcılar", "Yükümlülük"),
    Hesap("391", "Hesaplanan KDV", "Yükümlülük"),
    Hesap("500", "Sermaye", "Özkaynak"),
    Hesap("570", "Geçmiş Yıllar Kârları", "Özkaynak"),
    Hesap("600", "Yurt İçi Satışlar", "Gelir"),
    Hesap("610", "Yurt Dışı Satışlar", "Gelir"),
    Hesap("621", "Satış İndirimleri", "Gider"),
    Hesap("770", "Genel Yönetim Giderleri", "Gider"),
)


def validate_thp(hesaplar: tuple[Hesap, ...] | list[Hesap]) -> list[str]:
    """Veri seti tutarlılık denetimi: hata mesajları listesi (boş = temiz).

    Kurallar: kod benzersiz; kod tam 3 rakam; ad boş değil; tur geçerli bir
    mali tablo türü.
    """
    hatalar: list[str] = []
    gorulen: set[str] = set()
    for hesap in hesaplar:
        if hesap.kod in gorulen:
            hatalar.append(f"Kod tekrarı: {hesap.kod}")
        gorulen.add(hesap.kod)
        if not (len(hesap.kod) == 3 and hesap.kod.isdigit()):
            hatalar.append(f"Kod 3 rakam olmalı: {hesap.kod}")
        if not hesap.ad:
            hatalar.append(f"Ad boş olamaz: {hesap.kod}")
        if hesap.tur not in TURLER:
            hatalar.append(f"Geçersiz tür ({hesap.kod}): {hesap.tur}")
    return hatalar


def kod_ile(hesaplar: tuple[Hesap, ...] | list[Hesap], kod: str) -> Hesap:
    """Koduna göre hesabı bulur; yoksa KeyError fırlatır."""
    for hesap in hesaplar:
        if hesap.kod == kod:
            return hesap
    raise KeyError(f"{kod} kodlu hesap bulunamadı")
