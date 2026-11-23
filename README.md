# ERPNext Türkiye

Türkiye lokalizasyonu için ERPNext/Frappe uygulaması: e-belge (e-Fatura, e-Arşiv,
e-İrsaliye, e-Defter), TCMB döviz kuru servisi, Tek Düzen Hesap Planı (THP) ve
TCKN/VKN doğrulama. Yol haritası, Viva Yazılım'ın kamuya açık e-Dönüşüm ve
ERPNext hizmet yaklaşımı temel alınarak hazırlanmıştır (bkz. ROADMAP.md).

## Proje durumu — Faz 1 tamamlandı

| Faz   | Kapsam                                                 | Durum         |
| ----- | ------------------------------------------------------ | ------------- |
| Faz 0 | Keşif, iskelet, kalite kapıları                        | ✅ Tamamlandı |
| Faz 1 | Kurulum ve temel yapılandırma (Türkçe arayüz)          | ✅ Tamamlandı |
| Faz 2 | Türkiye lokalizasyon paketi (THP, KDV, TCKN/VKN, TCMB) | Beklemede     |
| Faz 3 | e-Dönüşüm entegrasyonu (4 katmanlı mimari)             | Beklemede     |
| Faz 4 | İK-Bordro ve kalan modüller                            | Beklemede     |
| Faz 5 | UAT, eğitim ve kontrollü canlı geçiş                   | Beklemede     |

Faz 1 çıktıları ve Türkçe arayüz ekran görüntüleri: [docs/FAZ1.md](docs/FAZ1.md)

## Faz çıkış kuralı

Her faz, **tüm kalite kapıları yeşil olmadan kapanmaz**: lint (ruff + eslint +
prettier), tip kontrolü (mypy + tsc), birim testler (pytest) ve uçtan uca
testler (Playwright). Tek komutla:

```bash
make phase-gate
```

CI (`.github/workflows/ci.yml`) aynı kapıları her push ve PR'da koşar.

## Depo yapısı

```
erpnext_turkiye/          Frappe uygulaması
  hooks.py                Kanca yapılandırması (doc_events vb.)
  turkiye/                Çekirdek iş mantığı (SAF Python, frappe'siz)
    kimlik.py             TCKN/VKN doğrulama (GİB algoritmaları)
    kdv.py                KDV oranları ve tevkifat hesabı
    kur_servisi.py        TCMB günlük kur XML ayrıştırıcı + fetch
    hesap_plani.py        THP başlangıç veri seti ve doğrulama
    frappe_olaylari.py    Frappe doc_event yapışkan katmanı
frontend/src/             TypeScript kaynakları (e-belge durum panosu)
erpnext_turkiye/public/js/  tsc çıktısı (üretilmiş, depoya girmez... girmezse CI derler)
tests/                    Birim testler (hermetik; ağ/site gerekmez)
e2e/                      Playwright uçtan uca testler + önizleme sayfası
docker/                   Yerel geliştirme ortamı (compose)
scripts/                  bench kurulum betiği
```

> Not: `erpnext_turkiye/public/js/` derleme çıktısıdır ve `.gitignore` ile
> dışlanmıştır; CI ve `make phase-gate` her koşumda yeniden derler.

## Çekirdek tasarım kuralı

`erpnext_turkiye/turkiye/` paketi **SAF Python**'dur: frappe import etmez.
Birim testleri bir Frappe sitesi olmadan koşar (27 test, saniyeler altında).
Frappe bağlamı yalnızca `frappe_olaylari.py` içinde geciktirilmiş import ile
tutulur. Bu sayede kalite kapıları her ortamda aynıdır.

## Geliştirme ortamı

### Yerel (bench)

```bash
bash scripts/bench_install.sh   # bench init + get-app + new-site (Faz 1)
```

### Docker

```bash
docker compose -f docker/compose.yaml up -d
# http://localhost:8080 — admin/admin
```

`apps.json`, frappe_docker'in özel imaj akışıyla (`APPS_JSON_BASE64`) da
kullanılabilir; bkz. https://github.com/frappe/frappe_docker.

## Kalite kapıları (tek tek)

```bash
make lint        # ruff + eslint + prettier --check
make typecheck   # mypy + tsc
make unit        # pytest
make e2e         # tsc build + Playwright
make phase-gate  # hepsi
```

## Lisans

MIT — bkz. [LICENSE](LICENSE). Temel alınan açık kaynak proje
[ERPNext-Turkish-Delight](https://github.com/logedosoft/ERPNext-Turkish-Delight)
(MIT) ile referans yaklaşım [Viva Yazılım](https://vivayazilim.com/) hizmet
sayfalarından derlenmiştir; kod düzeyinde bir devralma yoktur.
