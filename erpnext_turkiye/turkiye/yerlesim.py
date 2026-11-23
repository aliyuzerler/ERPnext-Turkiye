"""İl/ilçe Territory yapısı (Faz 2) — site tarafı.

Veri: ``veriler.il_ilce`` (81 il, 973 ilçe; kaynak: volkansenturk/
turkiye-iller-ilceler GitHub veri seti). Territory global bir ağaçtır
(şirket bazlı değildir).

bench kullanımı::

    bench --site turkiye.local execute \\
        erpnext_turkiye.turkiye.yerlesim.territory_kur

İlçeler iller arasında aynı ada sahip olabildiği için (örn. Gölbaşı,
Ereğli) adları ``<ilçe> (<il>)`` biçiminde yazılır; il adları benzersizdir.
"""

from __future__ import annotations


def territory_kur() -> dict[str, int]:
    """Territory ağacını kurar: Türkiye > 81 il > 973 ilçe (idempotent)."""
    import frappe

    from erpnext_turkiye.turkiye.veriler.il_ilce import ilceler_il, iller

    olusturulan = 0

    def ekle(ad: str, ebeveyn: str, grup: bool) -> None:
        nonlocal olusturulan
        if frappe.db.exists("Territory", ad):
            return
        frappe.get_doc(
            {
                "doctype": "Territory",
                "territory_name": ad,
                "parent_territory": ebeveyn,
                "is_group": 1 if grup else 0,
            }
        ).insert(ignore_permissions=True)
        olusturulan += 1

    if not frappe.db.exists("Territory", "All Territories"):
        frappe.get_doc(
            {"doctype": "Territory", "territory_name": "All Territories", "is_group": 1}
        ).insert(ignore_permissions=True)
        olusturulan += 1
    ekle("Türkiye", "All Territories", grup=True)
    for il in iller():
        ekle(il, "Türkiye", grup=True)
        for isim in ilceler_il(il):
            ekle(f"{isim} ({il})", il, grup=False)
        frappe.db.commit()  # il başına commit: uzun işte ilerleme korunur
    return {"olusturulan": olusturulan, "il": len(iller())}
