"""Turkiye modülü: Türkiye lokalizasyonunun çekirdek mantığı.

Tasarım kuralı: bu paketin içindeki modüller (kimlik, kdv, kur_servisi,
hesap_plani) SAF Python'dur — frappe import etmez. Bu sayede birim testleri
bir Frappe sitesi olmadan koşar. Frappe bağlamı yalnızca
``erpnext_turkiye.turkiye.frappe_olaylari`` içinde, fonksiyon gövdesinde
geciktirilmiş (lazy) import ile tutulur.
"""
