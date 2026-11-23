"""E Belge Gonderim — üretilen/gönderilen e-belge kaydı (Faz 3).

Satış Faturası on_submit kancasıyla doldurulur: UBL-TR XML şema
doğrulamasından geçmeden kayıt açılmaz (KM-3). İletim durumları: Uretilmis
-> Kuyrukta -> Gonderildi / Hata / Iptal.
"""

from __future__ import annotations

from frappe.model.document import Document


class EBelgeGonderim(Document):
    """E Belge Gonderim controller — iş mantığı SAF ebelge paketinde."""
