/**
 * Faz 4 — İK-bordro uyarlamaları ekran görüntüleri (canlı site).
 *
 * Çalışan site gerekir (scripts/site_web.py). Kullanım:
 *   node scripts/site_goruntu_faz4.mjs http://127.0.0.1:8000
 *
 * Çıktı: docs/ekran-goruntuleri/14..16-*.png + PASS/FAIL duman testleri.
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

const tarayici = await chromium.launch({
  headless: true,
  args: ["--host-resolver-rules=MAP turkiye.local 127.0.0.1"],
});
const sayfa = await tarayici.newPage({
  viewport: { width: 1440, height: 900 },
  locale: "tr",
});
sayfa.setDefaultTimeout(60000);

const git = async (adres, bekle = 6000) => {
  await sayfa.goto(`${BASE}${adres}`, { waitUntil: "domcontentloaded" });
  await sayfa.waitForTimeout(bekle);
};

try {
  await sayfa.goto(`${BASE}/api/method/login?usr=Administrator&pwd=admin`, {
    waitUntil: "domcontentloaded",
  });
  await sayfa.waitForTimeout(2000);

  // 14) Salary Component listesi — SGK/GV/Damga seti
  await git("/app/salary-component", 6000);
  await sayfa.screenshot({ path: path.join(CIKTI, "14-bordro-bilesenleri.png") });
  const bilesenler = await sayfa.locator("body").innerText();
  dumanTest("SGK İşçi Payı listede", /SGK İşçi Payı/.test(bilesenler));
  dumanTest("Damga Vergisi listede", /Damga Vergisi/.test(bilesenler));
  dumanTest("Gelir Vergisi listede", /Gelir Vergisi/.test(bilesenler));

  // 15) Leave Type listesi — 4857 izin türleri
  await git("/app/leave-type", 6000);
  await sayfa.screenshot({ path: path.join(CIKTI, "15-izin-turleri.png") });
  const izinler = await sayfa.locator("body").innerText();
  dumanTest("Yıllık Ücretli İzin listede", /Yıllık Ücretli İzin/.test(izinler));
  dumanTest("Doğum İzni listede", /Doğum İzni/.test(izinler));
  dumanTest("Babalık İzni listede", /Babalık İzni/.test(izinler));

  // 16) Holiday List "Türkiye 2026" — 2429 resmî tatiller (17 satır)
  await git("/app/holiday-list/Türkiye 2026", 6000);
  await sayfa.screenshot({ path: path.join(CIKTI, "16-tatil-listesi-2026.png") });
  const tatil = await sayfa.locator("body").innerText();
  dumanTest("tatil listesi başlığı", /Türkiye 2026/.test(tatil));
  dumanTest("Yılbaşı satırı", /Yılbaşı/.test(tatil));
  dumanTest("Ramazan Bayramı satırı", /Ramazan Bayramı/.test(tatil));
  dumanTest("Kurban arifesi yarım gün", /Kurban Bayramı Arifesi \(yarım gün\)/.test(tatil));
  const tatilSatirlari = (tatil.match(/2026-\d\d-\d\d/g) || []).length;
  dumanTest("17 tatil satırı", tatilSatirlari >= 17);
} finally {
  await tarayici.close();
}

const basarisiz = testler.filter((t) => !t.kosul);
console.log(`\nFaz 4 duman testleri: ${testler.length - basarisiz.length}/${testler.length} geçti`);
process.exit(basarisiz.length ? 1 : 0);
