/**
 * Faz 1 — Türkçe arayüz ekran görüntüleri ve site duman testleri.
 *
 * Çalışan site gerekir (bench start). Kullanım:
 *   node scripts/site_goruntu.mjs http://127.0.0.1:8000
 *
 * Çıktı: docs/ekran-goruntuleri/*.png + PASS/FAIL duman testleri.
 * Bu betik CI'ye dahil değildir; site-bağımlı olduğu için faz çıkış kapısı
 * ayrıca (make phase-gate) fixture tabanlı e2e ile koşulur.
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
  locale: "tr", // konuk sayfalar için Accept-Language: tr
});
sayfa.setDefaultTimeout(60000);

try {
  // 1) Giriş ekranı (Türkçe)
  await sayfa.goto(`${BASE}/login`, { waitUntil: "networkidle" });
  await sayfa.screenshot({ path: path.join(CIKTI, "01-giris-ekrani.png"), fullPage: true });
  const girisMetni = await sayfa.locator("body").innerText();
  dumanTest("giriş ekranı Türkçe", /Giriş|giriş/.test(girisMetni));

  // 2) Giriş (tarayıcı içi API çağrısı; --host-resolver-rules yalnızca tarayıcıyı etkiler)
  await sayfa.goto(`${BASE}/api/method/login?usr=Administrator&pwd=admin`, {
    waitUntil: "networkidle",
  });
  const girisGovde = await sayfa.locator("body").innerText();
  dumanTest("API girişi başarılı", /Logged In|home_page/.test(girisGovde));

  // 3) Masaüstü ana sayfa
  await sayfa.goto(`${BASE}/app`, { waitUntil: "networkidle" });
  await sayfa.waitForTimeout(3000);
  await sayfa.screenshot({ path: path.join(CIKTI, "02-masaustu.png"), fullPage: false });
  const govdeMetni = await sayfa.locator("body").innerText();
  dumanTest("masaüstü Türkçe (Türkçe modül adları)", /Fatura|Stok|Muhasebe/.test(govdeMetni));

  // 4) Yeni Satış Faturası formu
  await sayfa.goto(`${BASE}/app/sales-invoice/new`, { waitUntil: "networkidle" });
  await sayfa.waitForTimeout(4000);
  await sayfa.screenshot({ path: path.join(CIKTI, "03-satis-faturasi-formu.png"), fullPage: true });
  const faturaMetni = await sayfa.locator("body").innerText();
  dumanTest("fatura formu Türkçe alan", /Müşteri/.test(faturaMetni));

  // 5) Müşteri listesi
  await sayfa.goto(`${BASE}/app/customer`, { waitUntil: "networkidle" });
  await sayfa.waitForTimeout(3000);
  await sayfa.screenshot({ path: path.join(CIKTI, "04-musteri-listesi.png"), fullPage: false });
  const musteriMetni = await sayfa.locator("body").innerText();
  dumanTest("müşteri listesi Türkçe", /Müşteri/.test(musteriMetni));

  // 6) Hesap Planı (ağaç görünümü — v15'te doğrudan doctype rotası)
  await sayfa.goto(`${BASE}/app/account`, { waitUntil: "networkidle" });
  await sayfa.waitForTimeout(3000);
  await sayfa.screenshot({ path: path.join(CIKTI, "05-hesap-plani.png"), fullPage: false });
  const hesapMetni = await sayfa.locator("body").innerText();
  dumanTest(
    "hesap planı listesi Türkçe (numerik COA)",
    /Hesap Numarası|Hesap Adı/.test(hesapMetni),
  );

  // 7) Şirket sayfası
  await sayfa.goto(`${BASE}/app/company`, { waitUntil: "networkidle" });
  await sayfa.waitForTimeout(3000);
  await sayfa.screenshot({ path: path.join(CIKTI, "06-sirket.png"), fullPage: false });
  const sirketMetni = await sayfa.locator("body").innerText();
  dumanTest("şirket sayfası TRY", /Anadolu Makine/.test(sirketMetni));
} finally {
  await tarayici.close();
}

const basarisiz = testler.filter((t) => !t.kosul);
console.log(`\nDuman testleri: ${testler.length - basarisiz.length}/${testler.length} geçti`);
process.exit(basarisiz.length ? 1 : 0);
