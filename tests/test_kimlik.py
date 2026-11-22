"""TCKN/VKN doğrulama birim testleri.

Geçerli vektörlerin kaynağı:
- ``10000000146``: yaygın kullanılan klasik TCKN test numarası.
- ``1234567890``: GİB algoritmasının bilinen özelliği (hane+ofset toplamları
  10'u tamamladığı için kontrol hanesi 0 olur) — elle hesaplanmıştır.
- Üretici (``vkn_uret`` / ``tckn_uret``) ile kurulan vektörler
  öz-tutarlılık denetimidir: formülün kendisi bağımsız kaynaktan (GİB usulü)
  doğrulanmıştır; üretici, doğrulayıcıyla aynı formülü kullandığından bu
  testler yazım/regresyon hatalarını yakalar.
"""

from __future__ import annotations

from erpnext_turkiye.turkiye.kimlik import normalize, validate_tckn, validate_vkn

VALID_TCKN = "10000000146"  # yaygın kullanılan klasik TCKN test numarası


def vkn_uret(ilk_dokuz: str) -> str:
    """GİB usulüyle kontrol hanesi üreterek geçerli biçimli bir VKN kurar."""
    toplam = 0
    for x in range(9):
        tmp1 = (int(ilk_dokuz[x]) + (9 - x)) % 10
        tmp2 = (tmp1 * (2 ** (9 - x))) % 9
        if tmp1 != 0 and tmp2 == 0:
            tmp2 = 9
        toplam += tmp2
    kontrol = 0 if toplam % 10 == 0 else 10 - (toplam % 10)
    return ilk_dokuz + str(kontrol)


def tckn_uret(ilk_dokuz: str) -> str:
    """Klasik TCKN usulüyle son iki hane üretterek geçerli biçimli bir TCKN kurar."""
    d = [int(ch) for ch in ilk_dokuz]  # ilk 9 rakam
    tekler = d[0] + d[2] + d[4] + d[6] + d[8]
    ciftler = d[1] + d[3] + d[5] + d[7]
    onuncu = (tekler * 7 - ciftler) % 10
    onbirinci = (tekler + ciftler + onuncu) % 10
    return ilk_dokuz + str(onuncu) + str(onbirinci)


def test_normalize_ayraclari_temizler() -> None:
    assert normalize("123 45 67") == "1234567"
    assert normalize("123.456.7-8") == "12345678"
    assert normalize(" abc ") == ""
    assert normalize("") == ""


def test_tckn_bilinen_gecerli_numara() -> None:
    assert validate_tckn(VALID_TCKN) is True
    assert validate_tckn("100 000 001 46") is True  # ayraçlı biçim


def test_tckn_uretilen_numaralar_gecerli() -> None:
    for ilk_dokuz in ["112233445", "987654321", "555444333"]:
        assert validate_tckn(tckn_uret(ilk_dokuz)) is True, ilk_dokuz


def test_tckn_gecersiz_durumlar() -> None:
    assert validate_tckn("10000000147") is False  # son hane bozuk
    assert validate_tckn("1000000014") is False  # 10 hane
    assert validate_tckn("100000001467") is False  # 12 hane
    assert validate_tckn("01111111110") is False  # ilk hane sıfır
    assert validate_tckn("abcdefghijk") is False  # rakam değil
    assert validate_tckn("") is False


def test_vkn_bilinen_ozellik_vektoru() -> None:
    # GİB usulünün elle doğrulanmış vektörü (bkz. modül docstring'i).
    assert validate_vkn("1234567890") is True


def test_vkn_uretilen_numaralar_gecerli() -> None:
    for ilk_dokuz in ["345678901", "987654321", "112233445"]:
        assert validate_vkn(vkn_uret(ilk_dokuz)) is True, ilk_dokuz


def test_vkn_basina_sifir_kabul_edilir() -> None:
    assert validate_vkn(vkn_uret("098765432")) is True


def test_vkn_gecersiz_durumlar() -> None:
    gecerli = vkn_uret("345678901")
    bozuk = gecerli[:9] + str((int(gecerli[9]) + 1) % 10)
    assert validate_vkn(bozuk) is False  # kontrol hanesi bozuk
    assert validate_vkn("123456789") is False  # 9 hane
    assert validate_vkn("12345678901") is False  # 11 hane
    assert validate_vkn("0000000000") is False  # tamamen sıfır
    assert validate_vkn("") is False
