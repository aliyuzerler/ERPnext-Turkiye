"""e-Defter berat üretimi + paketleme + arşivleme (SAF Python).

GİB e-Defter kılavuzu kuralları:
- Yevmiye defteri için ayrı, büyük defter için ayrı berat oluşturulmalıdır.
- Yüklenen ZIP paketi **iki dosya** içermelidir (defter + berat).
- Berat, defter içeriğini taşımaz (özet + doğrulama verisidir) ve
  zaman damgası ile saklanır; damga GİB/MB kaynaklıdır — burada damga
  alanı entegratör adımı için boş bırakılır (``zaman_damgasi=None``).

Arşivleme: ``{yil}/{defter_turu}/`` dizini + SHA-256 manifest.json.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import zipfile
from decimal import Decimal
from xml.sax.saxutils import escape

from erpnext_turkiye.turkiye.edefter.xbrlgl import YevmiyeKayit, kebir_ozeti


def _sha256(veri: bytes) -> str:
    return hashlib.sha256(veri).hexdigest()


def _yuvarla(x: float) -> str:
    return str(Decimal(str(x)).quantize(Decimal("0.01")))


def yevmiye_berat(
    kayitlar: list[YevmiyeKayit],
    vkn: str,
    unvan: str,
    yil: int,
    defter_hash: str,
    zaman_damgasi: str | None = None,
) -> str:
    """Yevmiye defteri beratı (özet XML; defter içeriği taşımaz)."""
    toplam_borc = sum((k.toplam_borc() for k in kayitlar), 0.0)
    toplam_alacak = sum((k.toplam_alacak() for k in kayitlar), 0.0)
    damga = (
        f"    <zamanDamgasi>{escape(zaman_damgasi)}</zamanDamgasi>\n" if zaman_damgasi else ""
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<defterBerat>\n"
        f"  <defterTuru>Yevmiye</defterTuru>\n"
        f"  <mukellefVKN>{escape(vkn)}</mukellefVKN>\n"
        f"  <mukellefUnvan>{escape(unvan)}</mukellefUnvan>\n"
        f"  <donemYili>{yil}</donemYili>\n"
        f"  <kayitSayisi>{len(kayitlar)}</kayitSayisi>\n"
        f"  <toplamBorc>{_yuvarla(toplam_borc)}</toplamBorc>\n"
        f"  <toplamAlacak>{_yuvarla(toplam_alacak)}</toplamAlacak>\n"
        f"  <defterDosyaSHA256>{defter_hash}</defterDosyaSHA256>\n"
        f"{damga}"
        "</defterBerat>\n"
    )


def kebir_berat(
    kayitlar: list[YevmiyeKayit],
    vkn: str,
    unvan: str,
    yil: int,
    defter_hash: str,
    zaman_damgasi: str | None = None,
) -> str:
    """Büyük defter beratı: hesap bazlı dönem toplamları (kebir_ozeti)."""
    ozet = kebir_ozeti(kayitlar)
    satirlar = "".join(
        f"    <hesap kodu=\"{escape(kod)}\" borc=\"{_yuvarla(v['borc'])}\" "
        f"alacak=\"{_yuvarla(v['alacak'])}\" net=\"{_yuvarla(v['net'])}\"/>\n"
        for kod, v in ozet.items()
    )
    damga = (
        f"    <zamanDamgasi>{escape(zaman_damgasi)}</zamanDamgasi>\n" if zaman_damgasi else ""
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<defterBerat>\n"
        "  <defterTuru>Kebir</defterTuru>\n"
        f"  <mukellefVKN>{escape(vkn)}</mukellefVKN>\n"
        f"  <mukellefUnvan>{escape(unvan)}</mukellefUnvan>\n"
        f"  <donemYili>{yil}</donemYili>\n"
        f"  <hesapSayisi>{len(ozet)}</hesapSayisi>\n"
        "  <hesaplar>\n"
        f"{satirlar}"
        "  </hesaplar>\n"
        f"  <defterDosyaSHA256>{defter_hash}</defterDosyaSHA256>\n"
        f"{damga}"
        "</defterBerat>\n"
    )


def paketle(
    defter_adi: str,
    defter_xml: str,
    berat_xml: str,
) -> tuple[bytes, dict[str, str]]:
    """ZIP paketi (kılavuz: iki dosya — defter + berat) + SHA-256 manifesti.

    ``defter_adi`` örnek: "yevmiye-2026.xml" (berat adı türetilir).
    """
    berat_adi = defter_adi.replace(".xml", "-berat.xml")
    if defter_adi.endswith("-berat.xml"):
        raise ValueError("defter dosya adı '-berat.xml' soneki taşıyamaz")
    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(defter_adi, defter_xml)
        z.writestr(berat_adi, berat_xml)
    isimler = zipfile.ZipFile(tampon).namelist()
    if len(isimler) != 2:
        raise AssertionError(f"ZIP iki dosya içermeli; içerik: {isimler}")
    manifest = {
        defter_adi: _sha256(defter_xml.encode("utf-8")),
        berat_adi: _sha256(berat_xml.encode("utf-8")),
    }
    return tampon.getvalue(), manifest


def arsivle(
    paket: bytes,
    manifest: dict[str, str],
    arsiv_dizini: str,
    yil: int,
    defter_turu: str,
) -> str:
    """Paketi ``{dizin}/{yil}/{defter_turu}/`` altına manifestle arşivler."""
    hedef = os.path.join(arsiv_dizini, str(yil), defter_turu)
    os.makedirs(hedef, exist_ok=True)
    yol = os.path.join(hedef, "paket.zip")
    with open(yol, "wb") as f:
        f.write(paket)
    with open(os.path.join(hedef, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return yol


def paket_dogrula(yol: str) -> dict[str, bool]:
    """Arşivlenen paketi sınar: iki dosya + hash tutarlılığı."""
    with zipfile.ZipFile(yol) as z:
        isimler = z.namelist()
        iki_dosya = len(isimler) == 2
        dizin = os.path.dirname(yol)
        with open(os.path.join(dizin, "manifest.json"), encoding="utf-8") as mf:
            m = json.load(mf)
        hash_ok = all(
            _sha256(z.read(ad)) == hashim for ad, hashim in m.items() if ad in isimler
        )
        mukerrer = len(set(isimler)) == len(isimler)
    return {"iki_dosya": iki_dosya, "hash": hash_ok, "mukerrer_degil": mukerrer}
