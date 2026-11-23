// ESLint 9 flat config — Faz 0 kapı kuralı: `npm run lint` yeşil olmalı.
import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  {
    ignores: [
      "node_modules/**",
      "erpnext_turkiye/public/js/**", // tsc çıktısı (üretilmiş)
      "playwright-report/**",
      "test-results/**",
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["**/*.ts"],
    rules: {
      // TS derleyicisi tanımsız adları zaten yakalar; DOM/node genel adları için kapalı.
      "no-undef": "off",
      "@typescript-eslint/no-explicit-any": "error",
    },
  },
  {
    // Node betikleri (site ekran görüntüleri/duman testleri)
    files: ["scripts/**/*.mjs"],
    languageOptions: {
      globals: {
        console: "readonly",
        process: "readonly",
        setTimeout: "readonly",
        clearTimeout: "readonly",
        // Playwright sayfa.evaluate gövdesinde tarayıcı globali kullanılır
        document: "readonly",
        window: "readonly",
        fetch: "readonly",
      },
    },
  },
);
