# ERPNext Türkiye

Türkiye lokalizasyonu için ERPNext/Frappe uygulaması: e-belge (e-Fatura, e-Arşiv,
e-İrsaliye, e-Defter), TCMB döviz kuru servisi, Tek Düzen Hesap Planı (THP) ve
TCKN/VKN doğrulama. Yol haritası, Viva Yazılım'ın kamuya açık e-Dönüşüm ve
ERPNext hizmet yaklaşımı temel alınarak hazırlanmıştır (bkz. ROADMAP.md).

## Proje durumu — Faz 5 tamamlandı (UAT 15/15 PASS)

| Faz   | Kapsam                                                       | Durum                                     |
| ----- | ------------------------------------------------------------ | ----------------------------------------- |
| Faz 0 | Keşif, iskelet, kalite kapıları                              | ✅ Tamamlandı                             |
| Faz 1 | Kurulum ve temel yapılandırma (Türkçe arayüz)                | ✅ Tamamlandı                             |
| Faz 2 | Türkiye lokalizasyon paketi (THP, KDV, TCKN/VKN, TCMB)       | ✅ Tamamlandı                             |
| Faz 3 | e-Dönüşüm entegrasyonu (UBL-TR, iletim, panosu)              | ✅ Çekirdek tamamlandı                    |
| Faz 4 | İK-Bordro ve kalan modüller (SAF bordro + hrms seti)         | ✅ Çekirdek tamamlandı                    |
| Faz 5 | UAT, eğitim ve kontrollü canlıya alma (e-Defter BG/YB, KM-4) | ✅ Tamamlandı (GİB yükleme pilot kurumda) |

Faz 1 çıktıları ve Türkçe arayüz ekran görüntüleri: [docs/FAZ1.md](docs/FAZ1.md)
Faz 2 çıktıları (THP tam set, KDV setleri, TCMB, il/ilçe, KM-2 kanıtı):
[docs/FAZ2.md](docs/FAZ2.md)
Faz 3 çıktıları (UBL-TR üretimi, XSD doğrulaması/KM-3, iletim kuyruğu, e-belge
panosu): [docs/FAZ3.md](docs/FAZ3.md)
Faz 4 çıktıları (SAF bordro çekirdeği, hrms bileşen seti, GİB 2026 tarifesi,
izin türleri, resmî tatiller, rol profilleri): [docs/FAZ4.md](docs/FAZ4.md)
Faz 5 çıktıları (e-Defter XBRL-GL çekirdeği, KM-4 UAT 15/15 PASS, eğitim
rehberi, geri alma + canlıya alma planı): [docs/FAZ5.md](docs/FAZ5.md)
Kullanıcı eğitim rehberi (görsel): `download/ERPNext_Turkiye_Kullanici_Rehberi.docx`

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
  hooks.py                Kanca yapılandırması (doc_events, scheduler_events)
  turkiye/                Çekirdek iş mantığı (SAF Python, frappe'siz)
    veriler/              Veri setleri (SAF): thp_verisi.py (338 hesap),
                          il_ilce.py (81 il / 973 ilçe)
    kimlik.py             TCKN/VKN doğrulama (GİB algoritmaları)
    kdv.py                KDV oranları/tevkifat + site KDV setleri
    kur_servisi.py        TCMB günlük kur XML + Currency Exchange + scheduler
    hesap_plani.py        THP tam set + şirket THP kurulumu/varsayılanları
    yerlesim.py           İl/ilçe Territory kurulumu (site tarafı)
    kurulum.py            Site kurulum yardımcıları (faz2/3, KM-2/KM-3 kanıtları)
    frappe_olaylari.py    Frappe doc_event yapışkan katmanı
    ebelge/               e-Dönüşüm (SAF): UBL-TR üretici + irsaliye taslağı,
                          XSD seti (OASIS UBL 2.1), iletim kuyruğu;
                          olaylari.py = fatura kancaları, api.py = panosu API
    doctype/e_belge_gonderim/  E-belge kayıtları (durum takibi + XML saklama)
frontend/src/             TypeScript kaynakları (e-belge durum panosu — canlı API modu)
erpnext_turkiye/public/js/  tsc çıktısı (üretilmiş, depoya girmez... girmezse CI derler)
tests/                    Birim testler (hermetik; ağ/site gerekmez)
e2e/                      Playwright uçtan uca testler + önizleme sayfası
docker/                   Yerel geliştirme ortamı (compose)
scripts/                  bench kurulum betiği + site görüntü betikleri
```

> Not: `erpnext_turkiye/public/js/` derleme çıktısıdır ve `.gitignore` ile
> dışlanmıştır; CI ve `make phase-gate` her koşumda yeniden derler.

## Çekirdek tasarım kuralı

`erpnext_turkiye/turkiye/` paketi **SAF Python**'dur: frappe import etmez
(site tarafı fonksiyonları yalnızca gövde içinde frappe/erpnext import eder).
Birim testleri bir Frappe sitesi olmadan koşar (39 test, saniyeler altında).
Bu sayede kalite kapıları her ortamda aynıdır.

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
