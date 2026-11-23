"""Tek Düzen Hesap Planı (THP) yardımcıları — tam set (Faz 2).

SAF katman: tam set verisi ``veriler.thp_verisi``'den dışa aktarılır.
Site tarafı (frappe) yalnızca fonksiyon gövdelerinde import edilir
(Faz 0 kapı kuralı: çekirdek kod sitesiz birim test edilebilir).

bench kullanımı::

    bench --site turkiye.local execute \\
        erpnext_turkiye.turkiye.hesap_plani.thp_kur \\
        --kwargs '{"sirket": "Anadolu Makine Sanayi A.Ş."}'

Kaynaklar: vergiburosu.com THP sayfası + İSMMMO "Hesap Planı Açıklamaları"
(kod ve adlar çapraz doğrulanmıştır; ayrıntı bkz. veriler.thp_verisi).
"""

from __future__ import annotations

from typing import Any

from erpnext_turkiye.turkiye.veriler.thp_verisi import (
    THP,
    HesapKaydi,
    ebeveyn_kodu,
    grup_kodlari,
    kod_ile,
    thp_dogrula,
)

THP_TAM: tuple[HesapKaydi, ...] = THP

__all__ = [
    "KOKSZ_GRUPLAR",
    "THP",
    "THP_TAM",
    "VARSAYILAN_HESAPLAR",
    "HesapKaydi",
    "ebeveyn_kodu",
    "grup_kodlari",
    "kod_ile",
    "kok_hesaplarini_bul",
    "sirket_hesap_varsayilanlari",
    "thp_dogrula",
    "thp_kur",
]

# 6 Gelir Tablosu grubu ERPNext'te fiziksel grup değildir: gelir çocukları
# Income, gider çocukları Expense köküne bağlanır. 8 Serbest ve 9 Nazım
# grupları tohum setinde yoktur (bkz. veriler.thp_verisi docstring'i).
KOKSZ_GRUPLAR: frozenset[str] = frozenset({"6", "8", "9"})

# Şirket varsayılan hesap alanı -> THP hesap kodu
VARSAYILAN_HESAPLAR: dict[str, str] = {
    "default_receivable_account": "120",
    "default_payable_account": "320",
    "default_cash_account": "100",
    "default_bank_account": "102",
    "default_income_account": "600",
    "default_expense_account": "621",
    "write_off_account": "689",
    # ERPNext tek alan kullanır: kambiyo kârları 646; zararlar 656'ya
    # dönem sonunda aktarılabilir (e-defter kapanış pratiği)
    "exchange_gain_loss_account": "646",
    "unrealized_exchange_gain_loss_account": "646",
    "capital_work_in_progress_account": "258",
    "accumulated_depreciation_account": "257",
    "depreciation_expense_account": "796",
}


def kok_hesaplarini_bul(frappe_module: Any, sirket: str) -> dict[str, str]:
    """Şirketin kök hesaplarını kök türüne göre döndürür (site tarafı yardımcısı).

    frappe_module parametresi testlerde sahte (fake) modülle çağrılabilir;
    üretimde frappe modülü geçirilir.
    """
    kokler: dict[str, str] = {}
    for kok_tur in ("Asset", "Liability", "Equity", "Income", "Expense"):
        adaylar = frappe_module.get_all(
            "Account",
            filters={"company": sirket, "root_type": kok_tur, "is_group": 1},
            fields=["name", "parent_account"],
        )
        kokler[kok_tur] = next((a["name"] for a in adaylar if not a["parent_account"]), "")
    return kokler


def thp_kur(sirket: str) -> dict[str, int]:
    """THP tam setini şirkete kurar; var olan kodlar atlanır (idempotent).

    Grup hesapları (1-2 haneli kodlar) is_group=1; yapraklar is_group=0
    eklenir. Ebeveyn her zaman çocuklardan önce gelir (kod uzunluğu sırası).
    """
    import frappe

    kokler = kok_hesaplarini_bul(frappe, sirket)
    eksik = [tur for tur, ad in kokler.items() if not ad]
    if eksik:
        frappe.throw(f"{sirket} şirketinde kök hesapları eksik: {', '.join(eksik)}")

    sonuc = {"olusturulan": 0, "atlanan": 0}
    for hesap in THP_TAM:
        if hesap.kod in KOKSZ_GRUPLAR:
            continue
        if frappe.db.exists("Account", {"account_number": hesap.kod, "company": sirket}):
            sonuc["atlanan"] += 1
            continue
        if len(hesap.kod) == 1:
            ebeveyn_docname = kokler[hesap.kok_tur]
        else:
            ebeveyn = ebeveyn_kodu(hesap.kod)
            if ebeveyn in KOKSZ_GRUPLAR:
                # 6 grubunun çocukları: gelir/gider köklerine bağlanır
                ebeveyn_docname = kokler[hesap.kok_tur]
            else:
                ebeveyn_docname = frappe.db.get_value(
                    "Account", {"account_number": ebeveyn, "company": sirket}
                )
                if not ebeveyn_docname:
                    frappe.throw(f"Ebeveyn hesap bulunamadı ({hesap.kod} -> {ebeveyn})")
        frappe.get_doc(
            {
                "doctype": "Account",
                "company": sirket,
                "account_number": hesap.kod,
                "account_name": hesap.ad,
                "parent_account": ebeveyn_docname,
                "is_group": 1 if len(hesap.kod) <= 2 else 0,
                "root_type": hesap.kok_tur,
                "report_type": hesap.rapor_tur,
                "account_type": hesap.hesap_turu or "",
            }
        ).insert(ignore_permissions=True)
        sonuc["olusturulan"] += 1
    frappe.db.commit()
    return sonuc


def sirket_hesap_varsayilanlari(sirket: str) -> dict[str, str]:
    """Şirket varsayılan hesaplarını THP hesaplarına bağlar.

    ERPNext sürümünde olmayan alanlar sessizce atlanır (get_meta denetimi).
    """
    import frappe

    meta = frappe.get_meta("Company")
    guncellenecek: dict[str, str] = {}
    for alan, kod in VARSAYILAN_HESAPLAR.items():
        if not meta.get_field(alan):
            continue
        docname = frappe.db.get_value("Account", {"account_number": kod, "company": sirket})
        if docname:
            guncellenecek[alan] = docname
    if guncellenecek:
        frappe.db.set_value("Company", sirket, guncellenecek, update_modified=False)
        frappe.db.commit()
    return guncellenecek
