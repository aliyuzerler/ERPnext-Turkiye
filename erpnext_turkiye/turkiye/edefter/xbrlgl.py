"""Yevmiye defteri — XBRL-GL instance üretimi (SAF Python).

GİB e-Defter Uygulama Kılavuzu uyarınca yevmiye defteri XBRL-GL
taksonomisiyle üretilir. Bu modül gl-cor elementlerini kullanır:
``entriesHeader`` (dönem + mükellef), ``entryHeader`` (yevmiye
maddesi: numara, tarih, kaydı giren) ve ``entryDetail`` (madde
satırı: hesap kodu, borç/alacak tutarı, açıklama).

Standart: XBRL-GL (gl-cor 2006-10-25 core taxonomy, xbrli 2.1).
Kılavuz kuralı: her yevmiye maddesinde borç toplamı alacak toplamına
eşit olmalıdır — ``dengeli_mi`` bunu sınar; dengesiz madde reddedilir.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from xml.sax.saxutils import escape

GL_COR_NS = "http://www.xbrl.org/int/gl/cor/2006-10-25"
XBRLI_NS = "http://www.xbrl.org/2003/instance"
GL_COR_PREFIX = "gl-cor"


@dataclass(frozen=True)
class YevmiyeSatir:
    """Bir yevmiye madde satırı (entryDetail)."""

    hesap_kodu: str
    hesap_adi: str
    borc: float
    alacak: float
    aciklama: str = ""


@dataclass(frozen=True)
class YevmiyeKayit:
    """Bir yevmiye maddesi (entryHeader + entryDetail'ler)."""

    tarih: str  # YYYY-MM-DD
    yevmiye_no: str
    aciklama: str
    kaydi_giren: str
    satirlar: tuple[YevmiyeSatir, ...] = field(default_factory=tuple)

    def dengeli_mi(self) -> bool:
        """Borç toplamı == alacak toplamı (kılavuz kuralı)."""
        borc = sum((Decimal(str(s.borc)) for s in self.satirlar), Decimal("0"))
        alacak = sum((Decimal(str(s.alacak)) for s in self.satirlar), Decimal("0"))
        return borc == alacak and borc > 0

    def toplam_borc(self) -> float:
        return float(sum((Decimal(str(s.borc)) for s in self.satirlar), Decimal("0")))

    def toplam_alacak(self) -> float:
        return float(sum((Decimal(str(s.alacak)) for s in self.satirlar), Decimal("0")))


def _tutar(x: float) -> str:
    return str(Decimal(str(x)).quantize(Decimal("0.01")))


def _eleman(name: str, deger: str, context: str | None = None, girinti: str = "      ") -> str:
    ref = f' contextRef="{context}"' if context else ""
    return f'{girinti}<{GL_COR_PREFIX}:{name}{ref}>{escape(deger)}</{GL_COR_PREFIX}:{name}>'


def xbrlgl_yevmiye(
    kayitlar: list[YevmiyeKayit],
    vkn: str,
    unvan: str,
    yil: int,
) -> str:
    """Yevmiye defteri XBRL-GL instance'ı üretir (kayak: GİB e-Defter kılavuzu).

    Dengesiz yevmiye maddesi `ValueError` ile reddedilir (kılavuz kuralı).
    """
    for k in kayitlar:
        if not k.dengeli_mi():
            raise ValueError(
                f"Dengesiz yevmiye maddesi {k.yevmiye_no}: "
                f"borç {k.toplam_borc()} != alacak {k.toplam_alacak()}"
            )
    tarihler = sorted({k.tarih for k in kayitlar})
    context_etiketleri = {tarih: f"d-{tarih.replace('-', '')}" for tarih in tarihler}
    satirlar: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<xbrli:xbrl xmlns:xbrli="{XBRLI_NS}" xmlns:{GL_COR_PREFIX}="{GL_COR_NS}">',
        "  <xbrli:contexts>",
    ]
    for tarih in tarihler:
        etiket = context_etiketleri[tarih]
        satirlar += [
            f'    <xbrli:context id="{etiket}">',
            "      <xbrli:entity>",
            "        <xbrli:identifier scheme='http://www.edefter.gov.tr/defterbelge'>"
            + escape(vkn)
            + "</xbrli:identifier>",
            "      </xbrli:entity>",
            "      <xbrli:period>",
            f"        <xbrli:instant>{tarih}</xbrli:instant>",
            "      </xbrli:period>",
            "    </xbrli:context>",
        ]
    satirlar += [
        "  </xbrli:contexts>",
        "  <gl-cor:accountingEntries>",
        "    <gl-cor:entriesHeader>",
        "      <gl-cor:entityInformation>",
        _eleman("entityInformationOrganizationType", "SA"),
        _eleman("entityInformationOrganizationIdent", vkn),
        _eleman("entityInformationOrganizationTypeScheme", "GIBVKN"),
        _eleman("entityInformationOrganizationShortName", unvan[:40]),
        _eleman("entityInformationPeriodCoveredStart", f"{yil}-01-01"),
        _eleman("entityInformationPeriodCoveredEnd", f"{yil}-12-31"),
        "      </gl-cor:entityInformation>",
        "      <gl-cor:documentInfo>",
        _eleman("documentInfoDocumentType", "YN"),
        _eleman("documentInfoDocumentNumber", str(yil)),
        "      </gl-cor:documentInfo>",
        _eleman("entriesHeaderCreatedBy", unvan[:40]),
        _eleman("entriesHeaderEntryDataCorrection", "0"),
        "    </gl-cor:entriesHeader>",
    ]
    for k in kayitlar:
        ctx = context_etiketleri[k.tarih]
        satirlar += [
            "    <gl-cor:entryHeader>",
            _eleman("entryHeaderEnteredBy", k.kaydi_giren),
            _eleman("entryHeaderEnteredDate", k.tarih, ctx),
            _eleman("entryHeaderEntryNumber", k.yevmiye_no),
            _eleman("entryHeaderEntryComment", k.aciklama),
        ]
        for i, s in enumerate(k.satirlar, start=1):
            tutar = s.borc if s.borc else s.alacak
            borc_mu = bool(s.borc)
            satirlar += [
                "      <gl-cor:entryDetail>",
                _eleman("entryDetailLineNumber", str(i)),
                _eleman("entryDetailAccountNumber", s.hesap_kodu),
                _eleman("entryDetailAccountDescription", s.hesap_adi),
                _eleman("entryDetailComment", s.aciklama or k.aciklama),
                (
                    _eleman("entryDetailDebitAmount", _tutar(tutar), ctx)
                    if borc_mu
                    else _eleman("entryDetailCreditAmount", _tutar(tutar), ctx)
                ),
                "      </gl-cor:entryDetail>",
            ]
        satirlar.append("    </gl-cor:entryHeader>")
    satirlar += ["  </gl-cor:accountingEntries>", "</xbrli:xbrl>", ""]
    return "\n".join(satirlar)


def kebir_ozeti(kayitlar: list[YevmiyeKayit]) -> dict[str, dict[str, float]]:
    """Hesap kodu bazında dönem toplamları (büyük defter görünümü).

    Dönüş: {hesap_kodu: {"borc": x, "alacak": y, "net": borc-alacak}}.
    """
    ozet: dict[str, dict[str, float]] = {}
    for k in kayitlar:
        for s in k.satirlar:
            d = ozet.setdefault(s.hesap_kodu, {"borc": 0.0, "alacak": 0.0})
            d["borc"] = float(Decimal(str(d["borc"])) + Decimal(str(s.borc)))
            d["alacak"] = float(Decimal(str(d["alacak"])) + Decimal(str(s.alacak)))
    for d in ozet.values():
        d["net"] = float(Decimal(str(d["borc"])) - Decimal(str(d["alacak"])))
    return dict(sorted(ozet.items()))
