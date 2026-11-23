"""e-Belge panosu API köprüsü (Faz 3).

`frappe.whitelist` dekoratörü frappe'yi modül düzeyinde şart koştuğu için
bu ince köprü modülü istisnadır; iş mantığı ``olaylari``/SAF çekirdekte
durur (Faz 0 kapı kuralının amacı çekirdeğin sitesiz test edilebilirliği
olduğundan, yalnızca delegasyon içeren bu dosya istisna olarak
belgelenmiştir).
"""

import frappe


@frappe.whitelist()
def ebelge_ozeti() -> dict[str, object]:
    """Durum panosu canlı verisi: durum sayaçları + son kayıtlar."""
    from erpnext_turkiye.turkiye.ebelge.olaylari import ebelge_ozeti as ozet

    return ozet()
