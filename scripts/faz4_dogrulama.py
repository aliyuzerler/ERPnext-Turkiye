"""Faz 4 site doğrulaması — SAF çekirdek ile site kayıtları çapraz kontrol.

Çalıştırma: stack/frappe-bench/env/bin/python scripts/faz4_dogrulama.py <site>
"""

import os
import sys

import frappe

os.chdir("/home/z/my-project/stack/frappe-bench")
site = sys.argv[1] if len(sys.argv) > 1 else "turkiye.local"
frappe.init(site=site, sites_path="sites")
frappe.connect()

from erpnext_turkiye.turkiye.bordro.izin import RESMI_TATILLER_2026  # noqa: E402
from erpnext_turkiye.turkiye.bordro.sgk import ASGARI_BRUT_UCRET_2026  # noqa: E402
from erpnext_turkiye.turkiye.bordro.vergi import (  # noqa: E402
    GELIR_VERGISI_TARIFESI_2026_UCRET,
)

SONUCLAR: list[tuple[str, bool, str]] = []


def kontrol(ad: str, kosul: bool, detay: str = "") -> None:
    SONUCLAR.append((ad, bool(kosul), detay))


# 1) Salary Component seti ve formüller SAF oranlarıyla uyumlu mu
beklenen = {
    "SGK İşçi Payı": "base * 0.14",
    "İşsizlik Sigortası İşçi Payı": "base * 0.01",
    "Damga Vergisi": "base * 0.00759",
    "SGK İşveren Payı": "base * 0.2075",
    "İşsizlik Sigortası İşveren Payı": "base * 0.02",
}
for ad, formul in beklenen.items():
    ok = frappe.db.get_value("Salary Component", ad, "formula") == formul
    kontrol(f"Bileşen {ad} formülü", ok, formul)

gv = frappe.db.get_value(
    "Salary Component",
    "Gelir Vergisi",
    ["variable_based_on_taxable_salary", "is_income_tax_component"],
    as_dict=True,
)
kontrol(
    "Gelir Vergisi tarifeden hesap",
    bool(gv and gv.variable_based_on_taxable_salary and gv.is_income_tax_component),
)

# 2) Income Tax Slab — SAF tarifesiyle birebir
slab = frappe.get_doc("Income Tax Slab", "Türkiye 2026 (Ücret)")
slap_say = len(slab.slabs)
oranlar_site = [float(d.percent_deduction) for d in slab.slabs]
oranlar_saf = [oran * 100 for _, oran in GELIR_VERGISI_TARIFESI_2026_UCRET]
kontrol("Slab 5 dilim", slap_say == 5, f"{slap_say}")
kontrol("Slab oranları %15/20/27/35/40", oranlar_site == oranlar_saf, str(oranlar_site))
kontrol("Slab para birimi TRY", slab.currency == "TRY", slab.currency)
kontrol(
    "Slab etkin başlangıç 2026-01-01",
    str(slab.effective_from) == "2026-01-01",
    str(slab.effective_from),
)

# 3) Leave Type kanuni sınırlar
izinler = {
    "Doğum İzni": 112,   # 4857 m.74: 8+8 hafta
    "Babalık İzni": 5,   # m.74/6
    "Yıllık Ücretli İzin": 26,  # m.53: en üst kademe
}
for ad, maks in izinler.items():
    gercek = frappe.db.get_value("Leave Type", ad, "max_leaves_allowed")
    kontrol(f"İzin {ad} üst sınırı {maks}", gercek == maks, str(gercek))
kontrol(
    "Ücretsiz İzin LWP", bool(frappe.db.get_value("Leave Type", "Ücretsiz İzin", "is_lwp"))
)

# 4) Holiday List — SAF verisiyle birebir 17 satır
tatil = frappe.get_doc("Holiday List", "Türkiye 2026")
site_tarih = sorted(str(h.holiday_date) for h in tatil.holidays)
saf_tarih = sorted(t.tarih for t in RESMI_TATILLER_2026)
kontrol("Tatil satır sayısı", len(site_tarih) == len(saf_tarih) == 17, str(len(site_tarih)))
kontrol("Tatil tarihleri SAF ile birebir", site_tarih == saf_tarih)
kontrol(
    "Tatil dönem aralığı",
    str(tatil.from_date) == "2026-01-01" and str(tatil.to_date) == "2026-12-31",
)

# 5) Rol profilleri rolleri
for profil, roller in {
    "Türkiye Bordro Yöneticisi": {"HR User", "HR Manager"},
    "Türkiye Muhasebe": {"Accounts User", "Accounts Manager"},
    "Türkiye Satış": {"Sales User", "Sales Manager"},
}.items():
    gercek = {r.role for r in frappe.get_doc("Role Profile", profil).roles}
    kontrol(f"Profil {profil}", gercek == roller, str(sorted(gercek)))

# 6) SAF asgari ücret sabiti — ÇSGB değeri hâlâ 33.030 mu (kanıt satırı)
kontrol(
    "SAF asgari brüt (ÇSGB 2026)",
    ASGARI_BRUT_UCRET_2026 == 33030.00,
    str(ASGARI_BRUT_UCRET_2026),
)

frappe.destroy()
hatasiz = [s for s in SONUCLAR if s[1]]
for ad, ok, detay in SONUCLAR:
    print(("PASS" if ok else "FAIL"), ad, detay)
print(f"\nFaz 4 site doğrulaması: {len(hatasiz)}/{len(SONUCLAR)} geçti")
sys.exit(0 if len(hatasiz) == len(SONUCLAR) else 1)
