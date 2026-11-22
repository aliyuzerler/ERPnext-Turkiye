"""TCKN ve VKN doğrulama (Kaynak Veri katmanı, Faz 0-2).

Algoritmalar, GİB'in yayımlanmış kontrol usullerine dayanır:

- **TCKN (11 hane):** ilk hane sıfır olamaz; 10. hane = (1,3,5,7,9. hanelerin
  toplamının 7 katından 2,4,6,8. hanelerin toplamı çıkarıldıktan sonra mod 10);
  11. hane = ilk 10 hanelerin toplamının mod 10'u.
- **VKN (10 hane):** her hane için ``tmp1 = (hane + ofset) mod 10``,
  ``tmp2 = tmp1 x 2**(9-x) mod 9``; ``tmp1 != 0`` iken ``tmp2 == 0`` çıkarsa
  ``tmp2 = 9`` alınır. Toplamın mod 10'u sıfır ise kontrol hanesi 0, değilse
  ``10 - (toplam mod 10)`` olur.

Bilinen özellik (GİB usulünün doğal sonucu): her ``(hane + ofset)`` toplamı
10'a tamamlanan diziler — örneğin ``1234567890`` — kontrol hanesi 0 üretir.

Bu modül SAF Python'dur; frappe import etmez, birim testleri sitesiz koşar.
"""

from __future__ import annotations

import re

_TCKN_RE = re.compile(r"^[1-9][0-9]{10}$")
_VKN_RE = re.compile(r"^[0-9]{10}$")


def normalize(numara: str) -> str:
    """Ayraçları temizler: yalnızca rakamları sırayla bırakır.

    ``"123 45 67"`` -> ``"1234567"``; boşluk, nokta, tire ve boş olmayan diğer
    karakterler yok sayılır.
    """
    return "".join(ch for ch in (numara or "") if ch.isdigit())


def validate_tckn(value: str) -> bool:
    """11 haneli T.C. Kimlik Numarası doğrulaması."""
    tckn = normalize(value)
    if not _TCKN_RE.match(tckn):
        return False
    digits = [int(ch) for ch in tckn]
    tekler = digits[0] + digits[2] + digits[4] + digits[6] + digits[8]
    ciftler = digits[1] + digits[3] + digits[5] + digits[7]
    onuncu = (tekler * 7 - ciftler) % 10
    onbirinci = (tekler + ciftler + digits[9]) % 10
    return digits[9] == onuncu and digits[10] == onbirinci


def validate_vkn(value: str) -> bool:
    """10 haneli Vergi Kimlik Numarası doğrulaması."""
    vkn = normalize(value)
    if not _VKN_RE.match(vkn) or vkn == "0000000000":
        return False
    toplam = 0
    for x in range(9):
        tmp1 = (int(vkn[x]) + (9 - x)) % 10
        tmp2 = (tmp1 * (2 ** (9 - x))) % 9
        if tmp1 != 0 and tmp2 == 0:
            tmp2 = 9
        toplam += tmp2
    kontrol = 0 if toplam % 10 == 0 else 10 - (toplam % 10)
    return int(vkn[9]) == kontrol
