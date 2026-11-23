"""UBL XML şema doğrulama (OASIS UBL 2.1 XSD seti ile).

XSD seti repoya tedarik edilmiştir: ``xsd/UBL-2.1/`` (21 dosya; maindoc +
common; OASIS UBL 2.1 resmî şemaları). KM-3 kanıtı bu doğrulamaya dayanır:
üretilen fatura/irsaliye XML'leri şemadan geçmeden kuyruğa alınmaz.

``xmlschema`` geliştirme bağımlılığıdır (pyproject [dev]); fonksiyon gövdesi
içinde import edilir — paket çalışma zamanında bu bağımlılığı zorlamaz.
"""

from __future__ import annotations

from pathlib import Path

XSD_KOK = Path(__file__).parent / "xsd" / "UBL-2.1"
INVOICE_XSD = XSD_KOK / "maindoc" / "UBL-Invoice-2.1.xsd"
DESPATCH_XSD = XSD_KOK / "maindoc" / "UBL-DespatchAdvice-2.1.xsd"


def xsd_ile_dogrula(xml_metni: str, xsd_yolu: Path = INVOICE_XSD) -> list[str]:
    """XML'i verilen XSD'ye göre doğrular; hata listesi (boş = geçti).

    xmlschema kütüphanesi gerekir: ``pip install xmlschema`` (dev).
    """
    import xmlschema

    sema = xmlschema.XMLSchema(str(xsd_yolu))
    hatalar: list[str] = []
    for hata in sema.iter_errors(xml_metni):
        satir = getattr(hata, "line", None)
        neden = getattr(hata, "reason", None) or str(hata)
        yer = f"satır {satir}: " if satir else ""
        hatalar.append(f"{yer}{neden}")
    return hatalar
