# ERPNext Türkiye — kalite kapıları
# Faz çıkış kuralı (ROADMAP.md): her faz yalnızca `make phase-gate` yeşilken kapanır.
PYTHON ?= python3

.PHONY: install install-js lint typecheck unit build e2e phase-gate

install: install-js
	$(PYTHON) -m pip install --quiet ruff mypy pytest

install-js:
	npm install

lint:
	$(PYTHON) -m ruff check .
	npm run --silent lint
	npm run --silent format:check

typecheck:
	$(PYTHON) -m mypy erpnext_turkiye tests
	npm run --silent typecheck

unit:
	$(PYTHON) -m pytest

build:
	npm run --silent build

e2e: build
	npm run --silent e2e

phase-gate: lint typecheck unit e2e
	@echo "==> FAZ KAPISI: lint + typecheck + unit + e2e tumu YESIL"
