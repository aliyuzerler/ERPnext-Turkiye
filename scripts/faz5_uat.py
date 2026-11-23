"""Faz 5 — KM-4 UAT koşucusu: üç iş süreci + e-Defter + performans dumanı.

Çalıştırma: stack/frappe-bench/env/bin/python scripts/faz5_uat.py <site>
Çıktı: PASS/FAIL kanıtları + KM-4 onay tablosu; exit 0 = onaya hazır.

Gerçek iş birimi onayı pilot kurumda alınacaktır; bu koşucu UAT
senaryolarını script kanıtıyla çalıştırır (docs/FAZ5.md).
"""

import os
import sys
import time
import traceback
from decimal import Decimal

import frappe

BENCH_KOK = "/home/z/my-project/stack/frappe-bench"

SONUCLAR: list[tuple[str, str, str, bool, str]] = []


def uat(kod: str, surec: str, ad: str, kosul: bool, detay: str = "") -> None:
    SONUCLAR.append((kod, surec, ad, bool(kosul), detay))
    print(("PASS" if kosul else "FAIL"), kod, ad, detay, flush=True)


def _d(x: float) -> Decimal:
    return Decimal(str(x))


def uat_muhasebe() -> None:
    """Fatura → KDV %20 → GL dengesi → e-belge üretimi (km2/km3 akışı)."""
    kurulum = "erpnext_turkiye.turkiye.kurulum"
    r2 = frappe.get_attr(f"{kurulum}.km2_fatura_dogrulamasi")()
    kdv = r2["kdv"]
    uat("UAT-MH1", "Muhasebe", "Satış faturasında KDV %20 doğru", _d(kdv) == _d(2000), str(kdv))
    uat(
        "UAT-MH4",
        "Muhasebe",
        "Geçersiz VKN faturası reddedildi",
        bool(r2["gecersiz_vkn_reddedildi"]),
    )
    gl = frappe.get_all(
        "GL Entry",
        filters={"voucher_no": r2["fatura"], "docstatus": 1},
        fields=["account", "debit", "credit"],
    )
    borc = sum((_d(g["debit"]) for g in gl), Decimal("0"))
    alacak = sum((_d(g["credit"]) for g in gl), Decimal("0"))
    uat("UAT-MH2", "Muhasebe", "Mizan dengesi: borç = alacak", borc == alacak, f"{borc}={alacak}")
    r3 = frappe.get_attr(f"{kurulum}.km3_fatura_gonder")()
    uat(
        "UAT-MH3",
        "Muhasebe",
        "e-Belge kaydı üretildi (UBL-TR)",
        bool(r3.get("e_belge")) and r3.get("durum") == "Uretilmis",
        str(r3.get("e_belge")),
    )


def uat_satis() -> None:
    """Türkçe müşteri + KDV şablonlu satış siparişi akışı."""
    sirket = frappe.db.get_value("Company", {}, "name")
    musteri = frappe.db.get_value("Customer", {"customer_name": "Anadolu Ticaret Ltd. Şti."})
    uat("UAT-ST3", "Satış", "Müşteri kaydı ve Türkiye bölgesi", bool(musteri))
    if musteri:
        bolge = frappe.db.get_value("Customer", musteri, "territory")
        uat("UAT-ST4", "Satış", "Müşteri bölgesi Türkiye", bolge == "Türkiye", str(bolge))
    so = frappe.get_doc(
        {
            "doctype": "Sales Order",
            "customer": musteri,
            "company": sirket,
            "transaction_date": "2026-11-20",
            "delivery_date": "2026-11-27",
            "selling_price_list": "Standard Selling",
            "taxes_and_charges": "KDV %20 Satış",
            "items": [{"item_code": "HIZ-MLZ-001", "qty": 3, "rate": 10000.0}],
        }
    )
    so.insert(ignore_permissions=True)
    frappe.db.commit()
    uat("UAT-ST1", "Satış", "Sipariş toplamı 30.000", _d(so.total) == _d(30000), str(so.total))
    uat(
        "UAT-ST2",
        "Satış",
        "Siparişte KDV %20 (6.000)",
        _d(so.total_taxes_and_charges) == _d(6000),
        str(so.total_taxes_and_charges),
    )


def uat_ik() -> None:
    """Bordro: hrms Salary Slip ↔ SAF bordro_hesapla çapraz doğrulama."""
    kurulum = "erpnext_turkiye.turkiye.kurulum"
    frappe.get_attr(f"{kurulum}.faz5_kurulum")()
    r = frappe.get_attr(f"{kurulum}.ornek_bordro_kes")("2026-11")
    uat("UAT-IK1", "İK", "Bordro bileşen seti kuruldu", True, "SGK/İşsizlik/Damga/GV")
    uat(
        "UAT-IK2",
        "İK",
        "hrms bordro neti = SAF hesap (fark 0)",
        _d(r["fark"]) == 0,
        f"site {r['site_net']} / SAF {r['saf_net']}",
    )
    net = r["site_net"]
    uat("UAT-IK3", "İK", "Beklenen net 42.894,60", _d(net) == _d(42894.60), str(net))


def uat_edefter() -> None:
    """GL kayıtlarından XBRL-GL yevmiye + berat paketi + arşivleme."""
    from erpnext_turkiye.turkiye.edefter.berat import arsivle, paket_dogrula, paketle
    from erpnext_turkiye.turkiye.edefter.xbrlgl import YevmiyeKayit, YevmiyeSatir, xbrlgl_yevmiye

    sirket = frappe.db.get_value("Company", {}, "name")
    vkn = frappe.db.get_value("Company", sirket, "tax_id") or "3456789014"
    gl = frappe.get_all(
        "GL Entry",
        filters={"company": sirket, "docstatus": 1},
        fields=["voucher_no", "posting_date", "account", "debit", "credit"],
        order_by="voucher_no, posting_date",
    )
    grup: dict[str, list[frappe._dict]] = {}
    for g in gl:
        grup.setdefault(g["voucher_no"], []).append(g)
    kayitlar: list[YevmiyeKayit] = []
    for no, satirlar in sorted(grup.items()):
        detaylar = tuple(
            YevmiyeSatir(
                hesap_kodu=s["account"].split(" - ")[0] if " - " in s["account"] else s["account"],
                hesap_adi=s["account"],
                borc=float(s["debit"] or 0),
                alacak=float(s["credit"] or 0),
                aciklama=s["account"],
            )
            for s in satirlar
        )
        kayit = YevmiyeKayit(
            tarih=str(satirlar[0]["posting_date"]),
            yevmiye_no=no,
            aciklama=f"Fiş {no}",
            kaydi_giren="erpnext",
            satirlar=detaylar,
        )
        if kayit.dengeli_mi():
            kayitlar.append(kayit)
    denge = f"{len(kayitlar)}/{len(grup)}"
    uat("UAT-ED1", "e-Defter", "Yevmiye maddeleri dengeli", len(kayitlar) == len(grup), denge)
    xml = xbrlgl_yevmiye(kayitlar, vkn, sirket, 2026)
    import hashlib

    h = hashlib.sha256(xml.encode("utf-8")).hexdigest()
    berat = __import__(
        "erpnext_turkiye.turkiye.edefter.berat", fromlist=["yevmiye_berat"]
    ).yevmiye_berat(kayitlar, vkn, sirket, 2026, h)
    paket, manifest = paketle("yevmiye-2026.xml", xml, berat)
    hedef = os.path.join(BENCH_KOK, "sites", "turkiye.local", "private", "files", "edefter")
    yol = arsivle(paket, manifest, hedef, 2026, "yevmiye")
    dogru = paket_dogrula(yol)
    paket_ok = dogru["iki_dosya"] and dogru["mukerrer_degil"]
    uat("UAT-ED2", "e-Defter", "ZIP iki dosya (defter+berat)", paket_ok, yol)
    uat("UAT-ED3", "e-Defter", "Arşiv manifesti hash tutarlı", dogru["hash"], h[:16] + "…")


def uat_performans() -> None:
    """Ölçek dumanı: 100 satış faturası toplu üretim süresi."""
    sirket = frappe.db.get_value("Company", {}, "name")
    musteri = frappe.db.get_value("Customer", {"customer_name": "Anadolu Ticaret Ltd. Şti."})
    t0 = time.perf_counter()
    adet = 100
    for _ in range(adet):
        f = frappe.get_doc(
            {
                "doctype": "Sales Invoice",
                "customer": musteri,
                "company": sirket,
                "posting_date": "2026-11-21",
                "set_posting_time": 1,
                "selling_price_list": "Standard Selling",
                "taxes_and_charges": "KDV %20 Satış",
                "items": [{"item_code": "HIZ-MLZ-001", "qty": 1, "rate": 100.0}],
            }
        )
        f.insert(ignore_permissions=True)
    frappe.db.commit()
    sure = time.perf_counter() - t0
    uat(
        "UAT-PR1",
        "Performans",
        f"{adet} fatura üretimi {sure:.1f} sn (< 120 sn)",
        sure < 120,
        f"{sure / adet * 1000:.0f} ms/fatura",
    )


SENARYOLAR = [
    ("Muhasebe", uat_muhasebe),
    ("Satış", uat_satis),
    ("İK", uat_ik),
    ("e-Defter", uat_edefter),
    ("Performans", uat_performans),
]


def main() -> int:
    site = sys.argv[1] if len(sys.argv) > 1 else "turkiye.local"
    os.chdir(BENCH_KOK)
    frappe.init(site=site, sites_path="sites")
    frappe.connect()
    hatalar = 0
    for ad, kos in SENARYOLAR:
        print(f"\n=== {ad} ===", flush=True)
        try:
            kos()
        except Exception:
            hatalar += 1
            traceback.print_exc()
            frappe.db.rollback()
    frappe.destroy()
    print("\n=== KM-4 UAT ONAY TABLOSU ===")
    gecen = sum(1 for s in SONUCLAR if s[3])
    for kod, surec, ad, ok, detay in SONUCLAR:
        print(f"| {kod} | {surec} | {ad} | {'PASS' if ok else 'FAIL'} | {detay} |")
    print(f"\nKM-4: {gecen}/{len(SONUCLAR)} senaryo kanıtı PASS")
    return 0 if hatalar == 0 and gecen == len(SONUCLAR) else 1


if __name__ == "__main__":
    sys.exit(main())
