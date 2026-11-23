"""THP tam set birim testleri (Faz 2).

Kaynak çapraz doğrulaması: vergiburosu.com THP sayfası + İSMMMO "Hesap
Planı Açıklamaları" PDF'i; 332 ortak kod iki kaynakta aynıdır.
"""

from __future__ import annotations

import pytest

from erpnext_turkiye.turkiye.hesap_plani import (
    KOKSZ_GRUPLAR,
    THP_TAM,
    ebeveyn_kodu,
    kod_ile,
    thp_dogrula,
)
from erpnext_turkiye.turkiye.veriler.thp_verisi import grup_kodlari


def test_set_temiz() -> None:
    assert thp_dogrula() == []


def test_boyut() -> None:
    # 338 = 333 (vergiburosu sayfası) + 7 (İSMMMO ek hesapları)
    #        - 2 (8 Serbest ve 9 Nazım grupları)
    assert len(THP_TAM) == 338


def test_grup_yaprak_dengesi() -> None:
    gruplar = grup_kodlari()
    assert len(gruplar) == 65
    for hesap in THP_TAM:
        if len(hesap.kod) <= 2:
            assert hesap.kod in gruplar
        else:
            assert hesap.kod not in gruplar


def test_ana_hesaplar() -> None:
    assert kod_ile("100").ad == "Kasa"
    assert kod_ile("100").hesap_turu == "Cash"
    assert kod_ile("102").hesap_turu == "Bank"
    assert kod_ile("120").hesap_turu == "Receivable"
    assert kod_ile("120").kok_tur == "Asset"
    assert kod_ile("320").hesap_turu == "Payable"
    assert kod_ile("320").kok_tur == "Liability"
    assert kod_ile("191").ad == "İndirilecek KDV"
    assert kod_ile("191").hesap_turu == "Tax"
    assert kod_ile("391").ad == "Hesaplanan KDV"
    assert kod_ile("600").ad == "Yurt İçi Satışlar"
    assert kod_ile("600").kok_tur == "Income"


def test_gelir_gider_ayrimi() -> None:
    for kod in ("600", "601", "602", "646", "671", "679"):
        assert kod_ile(kod).kok_tur == "Income", kod
    for kod in ("610", "621", "630", "632", "656", "689", "730", "796"):
        assert kod_ile(kod).kok_tur == "Expense", kod


def test_rapor_turu_eslemesi() -> None:
    for kod in ("100", "191", "320", "500", "570"):
        assert kod_ile(kod).rapor_tur == "Balance Sheet", kod
    for kod in ("600", "621", "730"):
        assert kod_ile(kod).rapor_tur == "Profit and Loss", kod


def test_kdv_hesaplari_taksonomisi() -> None:
    for kod in ("190", "191", "192", "291", "292", "360", "361", "391", "392", "492"):
        assert kod_ile(kod).hesap_turu == "Tax", kod


def test_duran_varlik_eslemeleri() -> None:
    assert kod_ile("257").hesap_turu == "Accumulated Depreciation"
    assert kod_ile("258").hesap_turu == "Capital Work in Progress"
    assert kod_ile("796").hesap_turu == "Depreciation"
    assert kod_ile("153").hesap_turu == "Stock"


def test_ebeveyn_kodu() -> None:
    assert ebeveyn_kodu("1") is None
    assert ebeveyn_kodu("10") == "1"
    assert ebeveyn_kodu("100") == "10"
    assert ebeveyn_kodu("191") == "19"


def test_koksz_gruplar() -> None:
    # 6 grubunun çocukları köklere dağıtılır; 8/9 grubu sette yoktur
    assert frozenset({"6", "8", "9"}) == KOKSZ_GRUPLAR
    with pytest.raises(KeyError, match="9"):
        kod_ile("9")


def test_kod_ile_bulunamayan() -> None:
    with pytest.raises(KeyError, match="999"):
        kod_ile("999")


def test_isim_bicimleri() -> None:
    # Türkçe büyük/küçük harf düzeltmeleri (İSMMMO numaralı listesiyle uyumlu)
    assert kod_ile("372").ad == "Kıdem Tazminatı Karşılığı"
    assert kod_ile("5").ad == "Özkaynaklar"
    assert kod_ile("796").ad == "Amortismanlar ve Tükenme Payları"
    assert kod_ile("630").ad == "Araştırma ve Geliştirme Giderleri(-)"
    assert kod_ile("360").ad == "Ödenecek Vergi ve Fonlar"
