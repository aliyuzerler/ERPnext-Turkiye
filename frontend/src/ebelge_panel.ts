/**
 * e-Belge Durum Panosu — Faz 0 iskelet bileşeni (Faz 3: canlı veri modu).
 *
 * Bekleyen, hatalı ve tamamlanan e-belgeleri tek ekranda gösterir; durum
 * filtreleri tabloyu anında daraltır. Tarayıcıda `window.EBelgePanel.create`
 * sabit veriyle, `window.EBelgePanel.canliOlustur` ise sitenin
 * `ebelge_ozeti` API'sinden (Frappe whitelisted) canlı veriyle çalışır
 * (tsc, modulsuz betik üretir — bkz. tsconfig.json).
 */

type Durum = "bekleyen" | "hatali" | "tamamlanan";

interface Belge {
  belgeNo: string;
  tip: string;
  durum: Durum;
}

interface PanelVerisi {
  belgeler: Belge[];
}

interface EBelgePanelApi {
  create(alan: HTMLElement, veri: PanelVerisi): void;
  canliOlustur(alan: HTMLElement): Promise<void>;
}

const DURUM_SIRASI: Durum[] = ["bekleyen", "hatali", "tamamlanan"];

const DURUM_ETIKETLERI: Record<Durum, string> = {
  bekleyen: "Bekleyen",
  hatali: "Hatalı",
  tamamlanan: "Tamamlanan",
};

function sayaciOlustur(durum: Durum, adet: number): HTMLDivElement {
  const kart = document.createElement("div");
  kart.className = "ebelge-kart";
  kart.setAttribute("data-durum", durum);
  const sayi = document.createElement("span");
  sayi.className = "ebelge-sayi";
  sayi.textContent = String(adet);
  const etiket = document.createElement("span");
  etiket.className = "ebelge-etiket";
  etiket.textContent = DURUM_ETIKETLERI[durum];
  kart.append(sayi, etiket);
  return kart;
}

function tabloyuDoldur(govde: HTMLTableSectionElement, belgeler: Belge[]): void {
  govde.replaceChildren();
  for (const belge of belgeler) {
    const satir = document.createElement("tr");
    satir.setAttribute("data-durum", belge.durum);
    const hucreBelgeNo = document.createElement("td");
    hucreBelgeNo.textContent = belge.belgeNo;
    const hucreTip = document.createElement("td");
    hucreTip.textContent = belge.tip;
    const hucreDurum = document.createElement("td");
    hucreDurum.textContent = DURUM_ETIKETLERI[belge.durum];
    satir.append(hucreBelgeNo, hucreTip, hucreDurum);
    govde.appendChild(satir);
  }
}

function create(alan: HTMLElement, veri: PanelVerisi): void {
  alan.replaceChildren();

  const kok = document.createElement("div");
  kok.className = "ebelge-panel";

  const baslik = document.createElement("h3");
  baslik.textContent = "e-Belge Durum Panosu";
  kok.appendChild(baslik);

  const adetler = new Map<Durum, number>(DURUM_SIRASI.map((d): [Durum, number] => [d, 0]));
  for (const belge of veri.belgeler) {
    adetler.set(belge.durum, (adetler.get(belge.durum) ?? 0) + 1);
  }

  const kartlar = document.createElement("div");
  kartlar.className = "ebelge-kartlar";
  for (const durum of DURUM_SIRASI) {
    kartlar.appendChild(sayaciOlustur(durum, adetler.get(durum) ?? 0));
  }
  kok.appendChild(kartlar);

  const govde = document.createElement("tbody");
  const tabloyuGoster = (filtre: Durum | "tumu"): void => {
    const secili =
      filtre === "tumu" ? veri.belgeler : veri.belgeler.filter((b) => b.durum === filtre);
    tabloyuDoldur(govde, secili);
  };

  const filtreKutusu = document.createElement("div");
  filtreKutusu.className = "ebelge-filtre";
  for (const secenek of ["tumu", ...DURUM_SIRASI] as (Durum | "tumu")[]) {
    const dugme = document.createElement("button");
    dugme.type = "button";
    dugme.textContent = secenek === "tumu" ? "Tümü" : DURUM_ETIKETLERI[secenek];
    dugme.setAttribute("data-filtre", secenek);
    dugme.addEventListener("click", () => tabloyuGoster(secenek));
    filtreKutusu.appendChild(dugme);
  }
  kok.appendChild(filtreKutusu);

  const tablo = document.createElement("table");
  tablo.className = "ebelge-tablo";
  const basliklar = document.createElement("thead");
  const baslikSatiri = document.createElement("tr");
  for (const metin of ["Belge No", "Belge Tipi", "Durum"]) {
    const th = document.createElement("th");
    th.textContent = metin;
    baslikSatiri.appendChild(th);
  }
  basliklar.appendChild(baslikSatiri);
  tablo.append(basliklar, govde);
  kok.appendChild(tablo);

  alan.appendChild(kok);
  tabloyuGoster("tumu");
}

const hedef: unknown = typeof window !== "undefined" ? window : globalThis;

async function canliVeriAl(): Promise<PanelVerisi> {
  const yanit = await fetch("/api/method/erpnext_turkiye.turkiye.ebelge.api.ebelge_ozeti");
  const govde = (await yanit.json()) as {
    message: { kayitlar: { fatura: string; belge_turu: string; durum: string }[] };
  };
  const durum_esle: Record<string, Durum> = {
    Gonderildi: "tamamlanan",
    Hata: "hatali",
  };
  const belgeler = govde.message.kayitlar.map((kayit): Belge => ({
    belgeNo: kayit.fatura,
    tip: kayit.belge_turu,
    durum: durum_esle[kayit.durum] ?? "bekleyen",
  }));
  return { belgeler };
}

async function canliOlustur(alan: HTMLElement): Promise<void> {
  const veri = await canliVeriAl();
  create(alan, veri);
}

(hedef as { EBelgePanel: EBelgePanelApi }).EBelgePanel = { create, canliOlustur };
