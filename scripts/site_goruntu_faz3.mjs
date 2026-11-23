/**
 * Faz 3 — e-belge kayıtları ekran görüntüleri (canlı site).
 *
 * Çalışan site gerekir (scripts/site_web.py). Kullanım:
 *   node scripts/site_goruntu_faz3.mjs http://127.0.0.1:8000
 *
 * Çıktı: docs/ekran-goruntuleri/12..13-*.png + PASS/FAIL duman testleri.
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

const git = async (adres, bekle = 3000) => {
  await sayfa.goto(`${BASE}${adres}`, { waitUntil: "domcontentloaded" });
  await sayfa.waitForTimeout(bekle);
};

try {
  await sayfa.goto(`${BASE}/api/method/login?usr=Administrator&pwd=admin`, {
    waitUntil: "domcontentloaded",
  });
  await sayfa.waitForTimeout(2000);

  // 12) E Belge Gonderim listesi — KM-3 kanıt kaydı (Türkçe arayüz)
  await git("/app/e-belge-gonderim", 4000);
  await sayfa.screenshot({ path: path.join(CIKTI, "12-ebelge-panosu.png"), fullPage: false });
  const listeMetni = await sayfa.locator("body").innerText();
  dumanTest("e-belge listesi Türkçe başlık", /E Belge Gonderim/.test(listeMetni));
  dumanTest("KM-3 kaydı listede", /ACC-SINV/.test(listeMetni));
  dumanTest("durum sütunu (Uretilmis)", /Uretilmis/.test(listeMetni));

  // 13) Kayıt detayı — UUID, alıcı VKN ve UBL-TR XML. Not: desk formu düzenleme
  // modunda render eder; input/textarea değerleri innerText'e girmez — DOM'dan okunur.
  await git("/app/e-belge-gonderim/E-BLG-2026-00001", 8000);
  await sayfa.screenshot({ path: path.join(CIKTI, "13-ebelge-kayit-detay.png"), fullPage: true });
  const detay = await sayfa.evaluate(() => {
    const oku = (alan) => {
      const hucre = document.querySelector(`[data-fieldname="${alan}"]`);
      if (!hucre) return "";
      const kutu = hucre.querySelector("textarea, input");
      if (kutu && kutu.value) return kutu.value; // düzenleme modu: gerçek değer
      const deger = hucre.querySelector(".control-value");
      return deger ? deger.textContent : "";
    };
    return {
      uuid: oku("uuid"),
      vkn: oku("alici_vkn"),
      xml: oku("xml_icerik"),
      durum: oku("durum"),
    };
  });
  dumanTest("kayıt UUID gösteriliyor", detay.uuid.includes("CA9619D2"));
  dumanTest("alıcı VKN gösteriliyor", detay.vkn === "3456789014");
  dumanTest("UBL-TR XML saklı (TR1.2)", detay.xml.includes("CustomizationID"));
  dumanTest("kayıt durumu Uretilmis", detay.durum === "Uretilmis");
  // gönderen (şirket) VKN'si alıcıdan farklı olmalı — demo verisi kusuru düzeltmesi
  dumanTest("gönderen VKN ayrı (5554443334)", detay.xml.includes("5554443334"));
} finally {
  await tarayici.close();
}

const basarisiz = testler.filter((t) => !t.kosul);
console.log(`\nFaz 3 duman testleri: ${testler.length - basarisiz.length}/${testler.length} geçti`);
process.exit(basarisiz.length ? 1 : 0);
