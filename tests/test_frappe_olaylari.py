"""Frappe yapışkan katmanı testleri (sitesiz ortam)."""

from __future__ import annotations

from types import SimpleNamespace

from erpnext_turkiye.turkiye.frappe_olaylari import validate_tax_id


def test_sitesiz_ortamda_exception_firlatmaz() -> None:
    """frappe kurulu değilken işleyici sessizce geçer (ImportError yolu)."""
    doc = SimpleNamespace(tax_id="10000000146")
    validate_tax_id(doc, "validate")  # hata fırlatmamalı


def test_bos_tax_id_islenmez() -> None:
    doc = SimpleNamespace(tax_id=None)
    validate_tax_id(doc, "validate")  # hata fırlatmamalı
