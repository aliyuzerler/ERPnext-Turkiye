"""e-Defter paketi (SAF Python) — Faz 5 çekirdeği.

GİB e-Defter Uygulama Kılavuzu uyarınca yevmiye ve büyük defter
**XBRL-GL taksonomisine göre** üretilmelidir (kılavuz V_1.12; GİB).
``xbrlgl`` modülü yevmiye kayıtlarından XBRL-GL instance'ı (gl-cor
elementleri: entriesHeader / entryHeader / entryDetail) üretir;
``berat`` modülü defter özeti (berat) + paketleme + arşivleme yapar.

Kılavuz kuralları burada sınanır:
- ZIP paketi iki dosya içermelidir (defter + berat).
- Yevmiye defteri için ayrı, büyük defter için ayrı berat oluşturulmalıdır.
- Yevmiye madde dengesi: her yevmiye kaydında borç toplamı = alacak toplamı.
GİB şematron/yükleme adımı gerçek ortam işlevid (zaman damgası GİB/MB
kaynaklıdır) — bkz. docs/FAZ5.md sınırlar bölümü.
"""
