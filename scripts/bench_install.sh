#!/usr/bin/env bash
# Native bench kurulumu — Faz 1'in "Kurulum ve Temel Yapılandırma" çıktısı için hazırlık.
# Yerel bilgisayarda çalıştırılır; bulut gerekmez.
set -euo pipefail

FRAPPE_BRANCH="${FRAPPE_BRANCH:-version-15}"
ERPNEXT_BRANCH="${ERPNEXT_BRANCH:-version-15}"
REPO_URL="https://github.com/aliyuzerler/ERPnext-Turkiye"
SITE_ADI="${SITE_ADI:-turkiye.local}"

bench init frappe-bench --frappe-branch "$FRAPPE_BRANCH"
cd frappe-bench

bench get-app erpnext https://github.com/frappe/erpnext --branch "$ERPNEXT_BRANCH"
bench get-app erpnext_turkiye "$REPO_URL"

bench new-site "$SITE_ADI" \
  --install-app erpnext \
  --install-app erpnext_turkiye \
  --admin-password admin
bench use "$SITE_ADI"

echo "Kurulum tamam: http://$SITE_ADI:8000 (bench start ile)"
