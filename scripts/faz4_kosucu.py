"""Site kurulum zinciri koşucusu — tam traceback ile (bench execute izleri maskeliyor).

Çalıştırma: stack/frappe-bench/env/bin/python scripts/faz4_kosucu.py <site>
"""
import os
import sys
import traceback

import frappe

BENCH_KOK = "/home/z/my-project/stack/frappe-bench"

ADIMLAR = [
    "erpnext_turkiye.turkiye.kurulum.site_tr_ayarlari",
    "erpnext_turkiye.turkiye.kurulum.warehouse_turleri_tamamla",
    "erpnext_turkiye.turkiye.kurulum.kurulum_tamamlandi_isaretle",
    "erpnext_turkiye.turkiye.kurulum.sirket_olustur",
    "erpnext_turkiye.turkiye.kurulum.demo_verisi_olustur",
    "erpnext_turkiye.turkiye.kurulum.faz2_kurulum",
    "erpnext_turkiye.turkiye.kurulum.km2_fatura_dogrulamasi",
    "erpnext_turkiye.turkiye.kurulum.km3_fatura_gonder",
    "erpnext_turkiye.turkiye.kurulum.faz4_kurulum",
]


def main() -> int:
    site = sys.argv[1] if len(sys.argv) > 1 else "turkiye.local"
    filtre = sys.argv[2] if len(sys.argv) > 2 else ""
    os.chdir(BENCH_KOK)  # frappe, göreli "sites" yolunu cwd'den çözer
    frappe.init(site=site, sites_path="sites")
    frappe.connect()
    hatalar = 0
    for metot in ADIMLAR:
        if filtre and filtre not in metot:
            continue
        print(f"\n=== {metot} ===", flush=True)
        try:
            sonuc = frappe.get_attr(metot)()
            frappe.db.commit()
            print("OK:", sonuc, flush=True)
        except Exception:
            hatalar += 1
            traceback.print_exc()
            frappe.db.rollback()
            print("HATA", flush=True)
    frappe.destroy()
    return 1 if hatalar else 0


if __name__ == "__main__":
    sys.exit(main())
