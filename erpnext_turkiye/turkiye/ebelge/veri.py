"""e-Belge veri sözleşmesi (SAF Python).

Site tarafı (``olaylari.py``) ERPNext Satış Faturası'ndan bu sözleşmeyi
doldurur; UBL üreticisi yalnızca bu sözleşmeye bakar. Böylece ERPNext alan
değişiklikleri yalnızca yapışkan katmanı etkiler, UBL-TR çıktısı kararsız
kalır.

Alan adları GİB e-Fatura UBL-TR 1.2 karşılıklarına denk gelir:
- ``il`` -> cac:PostalAddress/cbc:CityName
- ``ilce`` -> cac:PostalAddress/cbc:CitySubdivisionName
- ``vergi_dairesi`` -> cac:PartyTaxScheme/cac:TaxScheme/cbc:Name
"""

from __future__ import annotations

from dataclasses import dataclass, field

UBL_VERSIYON = "2.1"
UBL_TR_SURUM = "TR1.2"
KDV_TUR_KODU = "0015"  # GİB vergi türü: KDV (resmî örneklerden)


@dataclass(frozen=True)
class Taraf:
    """Fatura tarafı: gönderen (satıcı) ya da alıcı."""

    vkn_tckn: str
    ad: str
    il: str = ""
    ilce: str = ""
    adres: str = ""
    bina_no: str = ""
    posta_kodu: str = ""
    vergi_dairesi: str = ""
    tckn_mi: bool = False  # schemeID: False -> VKN, True -> TCKN


@dataclass(frozen=True)
class FaturaSatiri:
    """InvoiceLine karşılığı."""

    sira: int
    ad: str
    miktar: float
    birim: str = "C62"  # UN/EDIFACT 6411: C62 = adet
    birim_fiyat: float = 0.0
    satir_tutari: float = 0.0


@dataclass(frozen=True)
class KDVGrubu:
    """Bir KDV oranına ait matrah/tutar grubu (cac:TaxSubtotal)."""

    yuzde: float
    matrah: float
    tutar: float


@dataclass(frozen=True)
class TevkifatSatiri:
    """KDV tevkifat satırı (cac:WithholdingTaxTotal içindir).

    ``kod`` GİB tevkifat tür kodudur (resmî örnekten doğrulanmış tek kod:
    606). Katalog Faz 4'te resmî kaynaklardan genişletilir.
    """

    kod: str
    yuzde: float
    tutar: float


@dataclass(frozen=True)
class FaturaVerisi:
    """UBL-TR fatura üretim sözleşmesi (site tarafı doldurur)."""

    fatura_no: str
    uuid: str
    tarih: str  # IssueDate: YYYY-MM-DD
    saat: str  # IssueTime: HH:MM:SS
    gonderen: Taraf
    alici: Taraf
    satirlar: tuple[FaturaSatiri, ...] = ()
    kdv_gruplari: tuple[KDVGrubu, ...] = ()
    tevkifatlar: tuple[TevkifatSatiri, ...] = field(default_factory=tuple)
    profil: str = "TEMELFATURA"  # ProfileID: TEMELFATURA / TICARIFATURA
    tur_kodu: str = "SATIS"  # InvoiceTypeCode
    para_birimi: str = "TRY"
    net_toplam: float = 0.0  # LineExtension / TaxExclusiveAmount
    genel_toplam: float = 0.0  # PayableAmount (alıcının ödediği)

    @property
    def kdv_toplami(self) -> float:
        """Tüm KDV gruplarının tutar toplamı (tam KDV, tevkifat öncesi)."""
        return round(sum(g.tutar for g in self.kdv_gruplari), 2)

    @property
    def tevkifat_toplami(self) -> float:
        """Tüm tevkifat satırlarının tutar toplamı."""
        return round(sum(t.tutar for t in self.tevkifatlar), 2)

    @property
    def odenecek_kdv(self) -> float:
        """Alıcının faturada ödediği KDV: tam KDV − tevkifat (GİB örnek usulü)."""
        return round(self.kdv_toplami - self.tevkifat_toplami, 2)

    @property
    def satir_sayisi(self) -> int:
        """LineCountNumeric değeri."""
        return len(self.satirlar)


def dogrula_veri(veri: FaturaVerisi) -> list[str]:
    """Üretim öncesi tutarlılık denetimi; hata listesi (boş = temiz).

    Kurallar: fatura no/uuid/tarih dolu; gönderen-alıcı dolu; satır sayısı
    > 0; genel toplam = net + odenecek KDV (2 hane hassasiyetle).
    """
    hatalar: list[str] = []
    if not veri.fatura_no:
        hatalar.append("fatura_no boş")
    if not veri.uuid:
        hatalar.append("uuid boş")
    if not veri.tarih:
        hatalar.append("tarih boş")
    if not veri.saat:
        hatalar.append("saat boş")
    if not veri.gonderen.vkn_tckn:
        hatalar.append("gönderen VKN/TCKN boş")
    if not veri.alici.vkn_tckn:
        hatalar.append("alıcı VKN/TCKN boş")
    if not veri.satirlar:
        hatalar.append("fatura satırı yok")
    beklenen = round(veri.net_toplam + veri.odenecek_kdv, 2)
    if round(veri.genel_toplam, 2) != beklenen:
        hatalar.append(
            f"genel_toplam {veri.genel_toplam} != net {veri.net_toplam} + "
            f"odenecek KDV {veri.odenecek_kdv}"
        )
    return hatalar
