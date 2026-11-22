/**
 * e-Belge Durum Panosu e2e testleri (Faz 0).
 *
 * Faz 0 kapsamında pano bileşeni statik önizleme sayfası üzerinde koşulur;
 * Faz 1'de çalışan Frappe sitesi üzerindeki gerçek uçtan uca senaryolarla
 * genişletilir (bkz. ROADMAP.md, Faz çıkış kuralı).
 */
import { expect, test } from "@playwright/test";
import path from "node:path";

const onizlemeYolu = "file://" + path.resolve(__dirname, "preview.html");

test("pano render ediliyor ve sayaçlar doğru", async ({ page }) => {
  await page.goto(onizlemeYolu);
  await expect(page.locator(".ebelge-panel")).toBeVisible();
  await expect(page.locator(".ebelge-kart[data-durum='bekleyen'] .ebelge-sayi")).toHaveText("1");
  await expect(page.locator(".ebelge-kart[data-durum='hatali'] .ebelge-sayi")).toHaveText("1");
  await expect(page.locator(".ebelge-kart[data-durum='tamamlanan'] .ebelge-sayi")).toHaveText("2");
  await expect(page.locator(".ebelge-tablo tbody tr")).toHaveCount(4);
});

test("hata filtresi tabloyu daraltıyor", async ({ page }) => {
  await page.goto(onizlemeYolu);
  await page.click("button[data-filtre='hatali']");
  await expect(page.locator(".ebelge-tablo tbody tr")).toHaveCount(1);
  await expect(page.locator(".ebelge-tablo tbody tr").first()).toContainText("EFT-0002");
});

test("tamamlanan filtresi tüm tamamlananları listeliyor", async ({ page }) => {
  await page.goto(onizlemeYolu);
  await page.click("button[data-filtre='tamamlanan']");
  await expect(page.locator(".ebelge-tablo tbody tr")).toHaveCount(2);
  await expect(page.locator(".ebelge-tablo tbody tr")).toContainText(["EFT-0003", "EFT-0004"]);
});
