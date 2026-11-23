/**
 * Faz 2 — THP, KDV setleri, Territory ve kur listesi ekran görüntüleri.
 *
 * Çalışan site gerekir (bench start). Kullanım:
 *   node scripts/site_goruntu_faz2.mjs http://127.0.0.1:8000
 *
 * Çıktı: docs/ekran-goruntuleri/07..11-*.png + PASS/FAIL duman testleri.
 */
import { chromium } from "@playwright/test";
import { mkdirSync } from "node:fs";
import path from "node:path";

const BASE = process.argv[2] || "http://turkiye.local:8000";
const CIKTI = path.resolve("docs/ekran-goruntuleri");
mkdirSync(CIKTI, { recursive: true });

const testler = [];
const dumanTest = (ad, kosul) => {
  testler.push({ ad, kosul });
  console.log(kosul ? `PASS ${ad}` : `FAIL ${ad}`);
};

// turkiye.local DNS kaydı yok: Chromium'a 127.0.0.1'e eşleme kuralı ver
const tarayici = await chromium.launch({
  headless: true,
  args: ["--host-resolver-rules=MAP turkiye.local 127.0.0.1"],
});
const sayfa = await tarayici.newPage({
  viewport: { width: 1440, height: 900 },
  locale: "tr",
});
sayfa.setDefaultTimeout(60000);

const git = async (adres, bekle = 3000) => {
  // socketio (9000) kapalı ortamda networkidle asılı kalabilir: domcontentloaded
  await sayfa.goto(`${BASE}${adres}`, { waitUntil: "domcontentloaded" });
  await sayfa.waitForTimeout(bekle);
};

// ağaç düğümü (.tree-link) hassas tıklama — navbar/breadcrumb karışmaz
const agacTikla = async (metin) => {
  const el = sayfa.locator(".tree-link", { hasText: metin }).first();
  if (await el.isVisible().catch(() => false)) {
    await el.click();
    await sayfa.waitForTimeout(900);
  }
};

// çeviri-bağımsız bölüm açma: başlığı vergi/tax içeren form bölümleri.
// Not: Playwright .click() frappe'in bölüm düğmesini tetiklemiyor; DOM
// click (evaluate) gerekli (gözlemlenmiş davranış, v15.127 desk).
const vergiBolumuAc = async () => {
  await sayfa.evaluate(() => {
    document.querySelectorAll(".section-head").forEach((el) => {
      if (/vergi|tax/i.test(el.textContent || "")) el.click();
    });
  });
  await sayfa.waitForTimeout(1200);
};

try {
  await sayfa.goto(`${BASE}/api/method/login?usr=Administrator&pwd=admin`, {
    waitUntil: "domcontentloaded",
  });
  await sayfa.waitForTimeout(2000);

  // 7) Hesap Planı — THP ağacı (kökleri sırayla aç: 1000 → 1 → 10 ve 19 → yapraklar)
  await git("/app/account/view/tree", 4000);
  await agacTikla("Application of Funds");
  await agacTikla("Dönen Varlıklar");
  await agacTikla("Hazır Değerler");
  await agacTikla("Diğer Dönen Varlıklar");
  await sayfa.screenshot({ path: path.join(CIKTI, "07-hesap-plani-thp.png"), fullPage: false });
  const thpMetni = await sayfa.locator("body").innerText();
  dumanTest("THP kök grubu (Dönen Varlıklar)", /Dönen Varlıklar/.test(thpMetni));
  dumanTest("THP KDV hesabı (İndirilecek KDV)", /İndirilecek KDV/.test(thpMetni));
  dumanTest("THP yaprak hesabı (100 - Kasa)", /100 - Kasa/.test(thpMetni));

  // 8) KM-2 örnek satış faturası — vergi bölümünü aç, KDV %20 satırı ve toplamlar
  // en son taslak faturayı API'den bul (naming serisi koşudan koşuya ilerler);
  // fetch sayfa bağlamında koşar (tarayıcı DNS kuralı + oturum çerezi geçerli)
  const faturaAdi = await sayfa.evaluate(async () => {
    const yanit = await fetch(
      "/api/resource/Sales%20Invoice?fields=[%22name%22]&order_by=creation%20desc&limit_page_length=1",
    );
    const veri = await yanit.json();
    return veri.data[0].name;
  });
  await git(`/app/sales-invoice/${encodeURIComponent(faturaAdi)}`, 5000);
  await vergiBolumuAc();
  await sayfa.screenshot({ path: path.join(CIKTI, "08-ornek-fatura-kdv.png"), fullPage: true });
  const faturaMetni = await sayfa.locator("body").innerText();
  dumanTest("KM-2 faturası KDV %20 satırı", /KDV %20/.test(faturaMetni));
  dumanTest("KM-2 faturası müşteri (geçerli VKN)", /Anadolu Ticaret/.test(faturaMetni));

  // 9) Territory ağacı — Türkiye > il > ilçe
  await git("/app/territory/view/tree", 4000);
  await agacTikla("Türkiye");
  await agacTikla("Ankara");
  await sayfa.screenshot({ path: path.join(CIKTI, "09-territory-il-ilce.png"), fullPage: false });
  const terMetni = await sayfa.locator("body").innerText();
  dumanTest("Territory Türkiye kökü", /Türkiye/.test(terMetni));
  dumanTest("Territory ilçe düzeyi (Çankaya)", /Çankaya/.test(terMetni));

  // 10) TCMB kur listesi (Currency Exchange — çift yönlü kayıtlar)
  await git("/app/currency-exchange", 3000);
  await sayfa.screenshot({ path: path.join(CIKTI, "10-tcmb-kur-listesi.png"), fullPage: false });
  const kurMetni = await sayfa.locator("body").innerText();
  dumanTest("Kur listesi USD", /USD/.test(kurMetni));
  dumanTest("Kur listesi EUR", /EUR/.test(kurMetni));

  // 11) Satış vergi şablonları (KDV %1/%10/%20 Satış)
  await git("/app/sales-taxes-and-charges-template", 3000);
  await sayfa.screenshot({ path: path.join(CIKTI, "11-kdv-sablonlari.png"), fullPage: false });
  const kdvMetni = await sayfa.locator("body").innerText();
  dumanTest("KDV %20 Satış şablonu", /KDV %20 Satış/.test(kdvMetni));
  dumanTest("KDV %1 Satış şablonu", /KDV %1 Satış/.test(kdvMetni));
} finally {
  await tarayici.close();
}

const basarisiz = testler.filter((t) => !t.kosul);
console.log(`\nFaz 2 duman testleri: ${testler.length - basarisiz.length}/${testler.length} geçti`);
process.exit(basarisiz.length ? 1 : 0);
