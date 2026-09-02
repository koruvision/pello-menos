export type ProductCategory =
  | "axilas"
  | "virilha"
  | "pernas"
  | "rosto"
  | "bracos"
  | "corpo"
  | "produtos";

export type ProductMethod =
  | "cera"
  | "laser"
  | "linha"
  | "esfoliacao"
  | "produto";

export type ProductAudience = "feminino" | "masculino";

export type StoreUnit = {
  id: string;
  name: string;
  city: string;
  state: "RJ" | "SP";
  address: string;
  hours: string;
};

export type Product = {
  id: string;
  name: string;
  duration: string;
  priceCents: number;
  oldPriceCents?: number;
  badge?: string;
  highlight?: boolean;
  image: string;
  imageAlt: string;
  category: ProductCategory;
  method: ProductMethod;
  audience: ProductAudience;
  sku: string;
  code: string;
  description: string;
};

type ProductSeed = Omit<
  Product,
  "sku" | "code" | "description" | "method" | "audience" | "priceCents" | "oldPriceCents"
> & {
  originalCents: number;
  method?: ProductMethod;
  audience?: ProductAudience;
};

export type HeroLayout = "split" | "copy-right" | "copy-left" | "copy-top";

export type HeroSlide = {
  id: string;
  badge: string;
  title: string;
  priceReais: string;
  priceCents: string;
  cta: string;
  ctaHref: string;
  image: string;
  imageMobile?: string;
  imagePosition?: string;
  imagePositionMobile?: string;
  imageAlt: string;
  layout: HeroLayout;
};

export type Category = {
  id: string;
  label: string;
  image: string;
  href: string;
};

export type PromoBannerData = {
  id: string;
  badge: string;
  title: string;
  subtitle: string;
  image: string;
  imageMobile?: string;
  imagePosition?: string;
  imagePositionMobile?: string;
  imageAlt: string;
  textSide?: "left" | "right";
  overlay?: "black" | "purple";
};

export type SquareBannerData = {
  id: string;
  title: string;
  subtitle: string;
  badge?: string;
  image: string;
  imagePosition?: string;
  imageAlt: string;
};

export type Review = {
  id: string;
  name: string;
  rating: number;
  text: string;
  time: string;
};

export const ECOMMERCE_DISCOUNT = 0.05;

export function withEcommercePrice(originalCents: number) {
  return {
    oldPriceCents: originalCents,
    priceCents: Math.round(originalCents * (1 - ECOMMERCE_DISCOUNT)),
  };
}

export function formatBRL(cents: number) {
  return (cents / 100).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

export function formatHeroPrice(cents: number) {
  const sale = withEcommercePrice(cents).priceCents;
  const reais = Math.floor(sale / 100);
  const cc = sale % 100;
  return {
    priceReais: reais.toLocaleString("pt-BR"),
    priceCents: String(cc).padStart(2, "0"),
  };
}

export function audienceFromPath(pathname: string): ProductAudience {
  return pathname.startsWith("/masculino") ? "masculino" : "feminino";
}

export function homeHref(audience: ProductAudience) {
  return audience === "masculino" ? "/masculino" : "/";
}

export function productsHref(audience: ProductAudience) {
  return audience === "masculino" ? "/masculino#produtos" : "/#produtos";
}

export const MIN_INSTALLMENT_CENTS = 5000;
export const WAX_TEN_X_MIN_CENTS = 18000;

export function inferMethod(id: string, explicit?: ProductMethod): ProductMethod {
  if (explicit) return explicit;
  if (id.includes("linha")) return "linha";
  if (id.includes("esfolia")) return "esfoliacao";
  if (id.includes("splash") || id.includes("body")) return "produto";
  if (id.includes("laser")) return "laser";
  if (
    id.includes("cera") ||
    id.includes("sobrancelha") ||
    id.includes("henna") ||
    id.includes("realce") ||
    id.includes("tintura") ||
    id.includes("design")
  ) {
    return "cera";
  }
  return "produto";
}

export function getInstallment(
  priceCents: number,
  method: ProductMethod = "laser",
) {
  let maxTimes = 10;
  if (method === "cera" && priceCents < WAX_TEN_X_MIN_CENTS) {
    maxTimes = Math.max(1, Math.floor(priceCents / MIN_INSTALLMENT_CENTS));
  }
  const byFloor = Math.max(1, Math.floor(priceCents / MIN_INSTALLMENT_CENTS));
  const times = Math.min(10, maxTimes, byFloor);
  const installmentCents = Math.ceil(priceCents / times);
  return { times, installmentCents };
}

export function installmentHint(method: ProductMethod) {
  if (method === "cera") {
    return "Em cera, 10x só acima de R$ 180. Parcela mínima de R$ 50.";
  }
  return "Parcele em até 10x, com parcela mínima de R$ 50.";
}

const I = {
  axilasLaser: "/images/products/axilas-laser-v3.png",
  axilaCera: "/images/products/axila-cera-v3.png",
  bucoLaser: "/images/products/buco-laser-v3.png",
  bucoCera: "/images/products/buco-cera-v3.png",
  virilhaLaser: "/images/products/virilha-laser-v3.png",
  virilhaCera: "/images/products/virilha-cera-v3.png",
  virilhaComum: "/images/products/virilha-comum-laser-v3.png",
  pernaLaser: "/images/products/perna-laser-v3.png",
  pernaCera: "/images/products/perna-cera-v3.png",
  meiaPernaLaser: "/images/products/meia-perna-laser-v3.png",
  meiaPernaCera: "/images/products/meia-perna-cera-v3.png",
  coxasLaser: "/images/products/coxas-laser-v3.png",
  coxaCera: "/images/products/coxa-cera-v3.png",
  bracosLaser: "/images/products/bracos-laser-v3.png",
  bracosCera: "/images/products/bracos-cera-v3.png",
  antebracoLaser: "/images/products/antebraco-laser-v3.png",
  antebracoCera: "/images/products/antebraco-cera-v3.png",
  abdomenLaser: "/images/products/abdomen-laser-v3.png",
  abdomenCera: "/images/products/abdomen-cera-v3.png",
  costasLaser: "/images/products/costas-laser-v3.png",
  queixoLaser: "/images/products/queixo-laser-v3.png",
  pescocoLaser: "/images/products/pescoco-laser-v3.png",
  rostoLaser: "/images/products/rosto-inteiro-laser-v3.png",
  design: "/images/products/design-sobrancelha-v3.png",
  henna: "/images/products/sobrancelha-henna-v3.png",
  kits: "/images/hero/destaque-kits.png",
  verao: "/images/hero/destaque-verao.png",
};

const M = {
  heroPeito: "/images/hero/male/hero-peito.jpg",
  heroPeitoM: "/images/hero/male/hero-peito-m.jpg",
  heroCostas: "/images/hero/male/hero-costas.jpg",
  heroCostasM: "/images/hero/male/hero-costas-m.jpg",
  heroAxilas: "/images/hero/male/hero-axilas.jpg",
  heroAxilasM: "/images/hero/male/hero-axilas-m.jpg",
  heroBarba: "/images/hero/male/hero-barba.jpg",
  heroBarbaM: "/images/hero/male/hero-barba-m.jpg",
  promoLaser: "/images/hero/male/promo-laser.jpg",
  promoLaserM: "/images/hero/male/promo-laser-m.jpg",
  promoCorpo: "/images/hero/male/promo-corpo.jpg",
  promoCorpoM: "/images/hero/male/promo-corpo-m.jpg",
  destaquePeito: "/images/hero/male/destaque-peito.jpg",
  destaqueVerao: "/images/hero/male/destaque-verao.jpg",
  destaqueBarba: "/images/hero/male/destaque-barba.jpg",
  destaqueSplash: "/images/hero/male/destaque-splash.jpg",
  catLaser: "/images/categories/male/cat-laser.jpg",
  catCera: "/images/categories/male/cat-cera.jpg",
  catEsfoliacao: "/images/categories/male/cat-esfoliacao.jpg",
  catAxilas: "/images/categories/male/cat-axilas.jpg",
  catCorpo: "/images/categories/male/cat-corpo.jpg",
  catRosto: "/images/categories/male/cat-rosto.jpg",
  catPernas: "/images/categories/male/cat-pernas.jpg",
  assinaturaCera: "/images/hero/male/assinatura-cera.jpg",
  peito: "/images/products/male/peito.jpg",
  costas: "/images/products/male/costas.jpg",
  barba: "/images/products/male/barba.jpg",
  axilas: "/images/products/male/axilas.jpg",
  abdomen: "/images/products/male/abdomen.jpg",
  bracos: "/images/products/male/bracos.jpg",
  pernas: "/images/products/male/pernas.jpg",
  nuca: "/images/products/male/nuca.jpg",
  virilha: "/images/products/male/virilha.jpg",
  pescoco: "/images/products/male/pescoco.jpg",
  antebraco: "/images/products/male/antebraco.jpg",
};

const catalogItems: ProductSeed[] = [
  // Cera feminino — preço cartão da tabela RJ-SP (original)
  { id: "abdomen-cera", name: "Abdômen – Cera", duration: "15 min • Avulso", originalCents: 5990, category: "corpo", image: I.abdomenCera, imageAlt: "Abdômen após cera" },
  { id: "axila-cera", name: "Axila – Cera", duration: "15 min • Avulso", originalCents: 3500, badge: "Cera", highlight: true, category: "axilas", image: I.axilaCera, imageAlt: "Axila lisa após cera" },
  { id: "antebraco-cera", name: "Antebraço – Cera", duration: "15 min • Avulso", originalCents: 5190, category: "bracos", image: I.antebracoCera, imageAlt: "Antebraço após cera" },
  { id: "bracos-cera", name: "Braços – Cera", duration: "20 min • Avulso", originalCents: 7190, category: "bracos", image: I.bracosCera, imageAlt: "Braços lisos após cera" },
  { id: "buco-cera", name: "Buço – Cera", duration: "10 min • Avulso", originalCents: 2800, highlight: true, category: "rosto", image: I.bucoCera, imageAlt: "Buço após cera" },
  { id: "costas-cera", name: "Costas – Cera", duration: "25 min • Avulso", originalCents: 5800, category: "corpo", image: I.costasLaser, imageAlt: "Costas após cera" },
  { id: "coxa-cera", name: "Coxa – Cera", duration: "20 min • Avulso", originalCents: 5190, category: "pernas", image: I.coxaCera, imageAlt: "Coxa após cera" },
  { id: "faixa-cera", name: "Faixa – Cera", duration: "10 min • Avulso", originalCents: 2800, category: "corpo", image: I.abdomenCera, imageAlt: "Faixa de cera no corpo" },
  { id: "intergluteos-cera", name: "Interglúteos – Cera", duration: "15 min • Avulso", originalCents: 3390, category: "corpo", image: I.virilhaCera, imageAlt: "Cera na região dos interglúteos" },
  { id: "nariz-cera", name: "Nariz – Cera", duration: "10 min • Avulso", originalCents: 3000, category: "rosto", image: I.queixoLaser, imageAlt: "Nariz após cera" },
  { id: "nadegas-cera", name: "Nádegas – Cera", duration: "20 min • Avulso", originalCents: 5190, category: "corpo", image: I.virilhaCera, imageAlt: "Nádegas após cera" },
  { id: "meia-nadega-cera", name: "Meia nádega – Cera", duration: "15 min • Avulso", originalCents: 2600, badge: "Cera", category: "corpo", image: I.virilhaCera, imageAlt: "Meia nádega após cera" },
  { id: "perna-cera", name: "Perna Inteira – Cera", duration: "40 min • Avulso", originalCents: 8700, badge: "5% OFF", highlight: true, category: "pernas", image: I.pernaCera, imageAlt: "Perna inteira após cera" },
  { id: "meia-perna-cera", name: "Meia Perna – Cera", duration: "20 min • Avulso", originalCents: 5190, category: "pernas", image: I.meiaPernaCera, imageAlt: "Meia perna após cera" },
  { id: "queixo-cera", name: "Queixo – Cera", duration: "10 min • Avulso", originalCents: 2800, badge: "Cera", category: "rosto", image: I.queixoLaser, imageAlt: "Queixo após cera" },
  { id: "seios-cera", name: "Seios – Cera", duration: "10 min • Avulso", originalCents: 2900, category: "corpo", image: I.abdomenCera, imageAlt: "Seios após cera" },
  { id: "virilha-comum-cera", name: "Virilha comum – Cera", duration: "15 min • Avulso", originalCents: 3999, badge: "Cera", category: "virilha", image: I.virilhaComum, imageAlt: "Virilha comum após cera" },
  { id: "virilha-comum-faixa-cera", name: "Virilha comum + faixa – Cera", duration: "20 min • Avulso", originalCents: 5399, category: "virilha", image: I.virilhaComum, imageAlt: "Virilha comum com faixa após cera" },
  { id: "virilha-cavada-cera", name: "Virilha cavada – Cera", duration: "20 min • Avulso", originalCents: 7390, category: "virilha", image: I.virilhaCera, imageAlt: "Virilha cavada após cera" },
  { id: "virilha-cavada-faixa-cera", name: "Virilha cavada + faixa – Cera", duration: "25 min • Avulso", originalCents: 8790, category: "virilha", image: I.virilhaCera, imageAlt: "Virilha cavada com faixa após cera" },
  { id: "virilha-modelada-cera", name: "Virilha modelada – Cera", duration: "25 min • Avulso", originalCents: 8700, category: "virilha", image: I.virilhaCera, imageAlt: "Virilha modelada após cera" },
  { id: "virilha-cera", name: "Virilha Total – Cera", duration: "25 min • Avulso", originalCents: 8890, highlight: true, category: "virilha", image: I.virilhaCera, imageAlt: "Virilha total após cera" },
  { id: "labios-genitais-cera", name: "Lábios genitais – Cera", duration: "15 min • Avulso", originalCents: 3990, category: "virilha", image: I.virilhaCera, imageAlt: "Cera nos lábios genitais" },
  { id: "tintura-pelos-pubianos", name: "Tintura dos pelos pubianos", duration: "20 min • Avulso", originalCents: 4600, category: "virilha", method: "cera", image: I.virilhaCera, imageAlt: "Tintura dos pelos pubianos" },
  { id: "sobrancelha-cera", name: "Sobrancelha – Cera", duration: "15 min • Avulso", originalCents: 4990, category: "rosto", image: I.design, imageAlt: "Sobrancelha com cera" },
  { id: "sobrancelha-realce-cera", name: "Sobrancelha + realce – Cera", duration: "25 min • Avulso", originalCents: 7790, category: "rosto", image: I.henna, imageAlt: "Sobrancelha com realce" },
  { id: "sobrancelha-henna-simples", name: "Sobrancelha simples + henna", duration: "25 min • Avulso", originalCents: 8590, category: "rosto", image: I.henna, imageAlt: "Sobrancelha simples com henna" },
  { id: "design-sobrancelha", name: "Design de Sobrancelha", duration: "20 min • Avulso", originalCents: 6000, badge: "Olhar", highlight: true, category: "rosto", image: I.design, imageAlt: "Design de sobrancelha" },
  { id: "design-sobrancelha-realce", name: "Design de sobrancelha + realce", duration: "30 min • Avulso", originalCents: 7990, category: "rosto", image: I.henna, imageAlt: "Design de sobrancelha com realce" },
  { id: "sobrancelha-henna", name: "Design de sobrancelha + henna", duration: "30 min • Avulso", originalCents: 8790, badge: "Combo", category: "rosto", image: I.henna, imageAlt: "Design de sobrancelha com henna" },
  { id: "realce", name: "Realce", duration: "15 min • Avulso", originalCents: 3390, category: "rosto", method: "cera", image: I.henna, imageAlt: "Realce de sobrancelha" },
  { id: "henna", name: "Henna", duration: "20 min • Avulso", originalCents: 4290, category: "rosto", method: "cera", image: I.henna, imageAlt: "Henna nas sobrancelhas" },

  // Linha feminino — tabela RJ-SP
  { id: "buco-linha", name: "Buço – Linha", duration: "10 min • Avulso", originalCents: 3190, badge: "Linha", category: "rosto", method: "linha", image: I.bucoCera, imageAlt: "Buço após linha" },
  { id: "queixo-linha", name: "Queixo – Linha", duration: "10 min • Avulso", originalCents: 3190, badge: "Linha", category: "rosto", method: "linha", image: I.queixoLaser, imageAlt: "Queixo após linha" },
  { id: "faixa-linha", name: "Faixa – Linha", duration: "10 min • Avulso", originalCents: 2950, badge: "Linha", category: "rosto", method: "linha", image: I.rostoLaser, imageAlt: "Faixa após linha" },

  // Esfoliação feminino — tabela RJ-SP
  { id: "esfoliacao-faixa", name: "Esfoliação de faixa", duration: "10 min • Avulso", originalCents: 1400, category: "corpo", method: "esfoliacao", image: I.abdomenCera, imageAlt: "Esfoliação de faixa" },
  { id: "esfoliacao-meio-braco", name: "Esfoliação de meio braço", duration: "15 min • Avulso", originalCents: 2595, category: "bracos", method: "esfoliacao", image: I.antebracoCera, imageAlt: "Esfoliação de meio braço" },
  { id: "esfoliacao-braco", name: "Esfoliação de braço", duration: "20 min • Avulso", originalCents: 3595, category: "bracos", method: "esfoliacao", image: I.bracosCera, imageAlt: "Esfoliação de braço" },
  { id: "esfoliacao-meia-perna", name: "Esfoliação de meia perna", duration: "20 min • Avulso", originalCents: 2595, category: "pernas", method: "esfoliacao", image: I.meiaPernaCera, imageAlt: "Esfoliação de meia perna" },
  { id: "esfoliacao-abdomen", name: "Esfoliação de abdômen", duration: "15 min • Avulso", originalCents: 2995, category: "corpo", method: "esfoliacao", image: I.abdomenCera, imageAlt: "Esfoliação de abdômen" },
  { id: "esfoliacao-axilas", name: "Esfoliação de axilas", duration: "15 min • Avulso", originalCents: 1750, badge: "Pele", category: "axilas", method: "esfoliacao", image: I.axilaCera, imageAlt: "Esfoliação de axilas" },
  { id: "esfoliacao-nadegas", name: "Esfoliação de nádegas", duration: "15 min • Avulso", originalCents: 2595, category: "corpo", method: "esfoliacao", image: I.virilhaCera, imageAlt: "Esfoliação de nádegas" },
  { id: "esfoliacao-meia-nadega", name: "Esfoliação de meia nádega", duration: "10 min • Avulso", originalCents: 1300, category: "corpo", method: "esfoliacao", image: I.virilhaCera, imageAlt: "Esfoliação de meia nádega" },
  { id: "esfoliacao-coxa", name: "Esfoliação de coxa", duration: "20 min • Avulso", originalCents: 2595, category: "pernas", method: "esfoliacao", image: I.coxaCera, imageAlt: "Esfoliação de coxa" },
  { id: "esfoliacao-costas", name: "Esfoliação de costas", duration: "20 min • Avulso", originalCents: 2900, category: "corpo", method: "esfoliacao", image: I.costasLaser, imageAlt: "Esfoliação de costas" },
  { id: "esfoliacao-perna", name: "Esfoliação de perna inteira", duration: "25 min • Avulso", originalCents: 4350, badge: "Pele", highlight: true, category: "pernas", method: "esfoliacao", image: I.pernaCera, imageAlt: "Esfoliação de perna inteira" },
  { id: "esfoliacao-virilha", name: "Esfoliação de virilha", duration: "15 min • Avulso", originalCents: 2000, category: "virilha", method: "esfoliacao", image: I.virilhaCera, imageAlt: "Esfoliação de virilha" },
  { id: "esfoliacao-virilha-faixa", name: "Esfoliação de virilha + faixa", duration: "20 min • Avulso", originalCents: 2699, category: "virilha", method: "esfoliacao", image: I.virilhaCera, imageAlt: "Esfoliação de virilha com faixa" },
  { id: "esfoliacao-seios", name: "Esfoliação de seios", duration: "10 min • Avulso", originalCents: 1450, category: "corpo", method: "esfoliacao", image: I.abdomenCera, imageAlt: "Esfoliação de seios" },

  // Laser feminino — preço riscado da loja oficial (pacote original)
  { id: "axilas-laser", name: "Axilas Laser", duration: "15 min • até 10 sessões", originalCents: 89990, badge: "5% OFF", highlight: true, category: "axilas", image: I.axilasLaser, imageAlt: "Axilas após laser" },
  { id: "areola-laser", name: "Aréola Laser", duration: "10 min • até 10 sessões", originalCents: 38090, category: "corpo", image: I.abdomenLaser, imageAlt: "Aréola após laser" },
  { id: "buco-laser", name: "Buço Laser", duration: "10 min • até 10 sessões", originalCents: 42590, category: "rosto", image: I.bucoLaser, imageAlt: "Buço após laser" },
  { id: "virilha-laser", name: "Virilha Total Laser", duration: "20 min • até 10 sessões", originalCents: 209000, badge: "Mais vendido", highlight: true, category: "virilha", image: I.virilhaLaser, imageAlt: "Virilha total após laser" },
  { id: "virilha-comum-laser", name: "Virilha Comum Laser", duration: "15 min • até 10 sessões", originalCents: 132000, category: "virilha", image: I.virilhaComum, imageAlt: "Virilha comum após laser" },
  { id: "virilha-cavada-laser", name: "Virilha Cavada Laser", duration: "20 min • até 10 sessões", originalCents: 179000, category: "virilha", image: I.virilhaLaser, imageAlt: "Virilha cavada após laser" },
  { id: "virilha-cavada-faixa-laser", name: "Virilha Cavada c/ Faixa Laser", duration: "20 min • até 10 sessões", originalCents: 203500, category: "virilha", image: I.virilhaLaser, imageAlt: "Virilha cavada com faixa após laser" },
  { id: "virilha-faixa-laser", name: "Virilha c/ Faixa Laser", duration: "15 min • até 10 sessões", originalCents: 156000, category: "virilha", image: I.virilhaComum, imageAlt: "Virilha com faixa após laser" },
  { id: "perna-laser", name: "Perna Inteira Laser", duration: "40 min • até 10 sessões", originalCents: 423500, badge: "Verão", category: "pernas", image: I.pernaLaser, imageAlt: "Perna inteira após laser" },
  { id: "meia-perna-laser", name: "Meia Perna Laser", duration: "20 min • até 10 sessões", originalCents: 203000, badge: "Verão", highlight: true, category: "pernas", image: I.meiaPernaLaser, imageAlt: "Meia perna após laser" },
  { id: "coxas-laser", name: "Coxas Laser", duration: "25 min • até 10 sessões", originalCents: 219990, category: "pernas", image: I.coxasLaser, imageAlt: "Coxas após laser" },
  { id: "bracos-laser", name: "Braços Inteiros Laser", duration: "20 min • até 10 sessões", originalCents: 144000, badge: "Novo", highlight: true, category: "bracos", image: I.bracosLaser, imageAlt: "Braços após laser" },
  { id: "antebraco-laser", name: "Antebraço Laser", duration: "15 min • até 10 sessões", originalCents: 108000, category: "bracos", image: I.antebracoLaser, imageAlt: "Antebraço após laser" },
  { id: "abdomen-laser", name: "Abdômen Laser", duration: "20 min • até 10 sessões", originalCents: 102000, badge: "Corpo", category: "corpo", image: I.abdomenLaser, imageAlt: "Abdômen após laser" },
  { id: "costas-laser", name: "Costas Laser", duration: "25 min • até 10 sessões", originalCents: 149500, category: "corpo", image: I.costasLaser, imageAlt: "Costas após laser" },
  { id: "queixo-laser", name: "Queixo Laser", duration: "10 min • até 10 sessões", originalCents: 73300, category: "rosto", image: I.queixoLaser, imageAlt: "Queixo após laser" },
  { id: "pescoco-laser", name: "Pescoço Laser", duration: "10 min • até 10 sessões", originalCents: 70300, category: "rosto", image: I.pescocoLaser, imageAlt: "Pescoço após laser" },
  { id: "nariz-laser", name: "Nariz Laser", duration: "10 min • até 10 sessões", originalCents: 34000, category: "rosto", image: I.queixoLaser, imageAlt: "Nariz após laser" },
  { id: "orelhas-laser", name: "Orelhas Laser", duration: "10 min • até 10 sessões", originalCents: 43990, category: "rosto", image: I.pescocoLaser, imageAlt: "Orelhas após laser" },
  { id: "rosto-inteiro-laser", name: "Rosto Inteiro Laser", duration: "20 min • até 10 sessões", originalCents: 144500, badge: "Combo", highlight: true, category: "rosto", image: I.rostoLaser, imageAlt: "Rosto inteiro após laser" },
  { id: "intergluteos-laser", name: "Interglúteos Laser", duration: "15 min • até 10 sessões", originalCents: 47000, category: "corpo", image: I.virilhaLaser, imageAlt: "Interglúteos após laser" },
  { id: "meia-nadega-laser", name: "Meia Nádega Laser", duration: "15 min • até 10 sessões", originalCents: 70300, category: "corpo", image: I.virilhaLaser, imageAlt: "Meia nádega após laser" },
  { id: "nadegas-laser", name: "Nádegas Laser", duration: "20 min • até 10 sessões", originalCents: 123090, category: "corpo", image: I.virilhaLaser, imageAlt: "Nádegas após laser" },
  { id: "psd-p-laser", name: "PSD P Laser", duration: "10 min • até 10 sessões", originalCents: 43000, category: "corpo", image: I.abdomenLaser, imageAlt: "Área sem definição P após laser" },
  { id: "psd-m-laser", name: "PSD M Laser", duration: "15 min • até 10 sessões", originalCents: 49500, category: "corpo", image: I.abdomenLaser, imageAlt: "Área sem definição M após laser" },
  { id: "psd-g-laser", name: "PSD G Laser", duration: "20 min • até 10 sessões", originalCents: 76900, category: "corpo", image: I.abdomenLaser, imageAlt: "Área sem definição G após laser" },

  // Produto oficial
  { id: "body-splash", name: "Body Splash Pello Menos", duration: "Uso diário", originalCents: 6900, badge: "Oficial", category: "produtos", method: "produto", image: I.kits, imageAlt: "Body Splash oficial Pello Menos" },

  // Cera masculino — áreas da tabela RJ-SP para homem; preço cartão + 5% OFF no site
  { id: "peito-cera-masc", name: "Peito – Cera", duration: "20 min • Avulso", originalCents: 5990, badge: "Cera", highlight: true, category: "corpo", method: "cera", audience: "masculino", image: M.peito, imageAlt: "Homem após cera no peito Pello Menos" },
  { id: "abdomen-cera-masc", name: "Abdômen – Cera", duration: "15 min • Avulso", originalCents: 5990, category: "corpo", method: "cera", audience: "masculino", image: M.abdomen, imageAlt: "Homem após cera no abdômen Pello Menos" },
  { id: "axila-cera-masc", name: "Axila – Cera", duration: "15 min • Avulso", originalCents: 3500, badge: "Cera", highlight: true, category: "axilas", method: "cera", audience: "masculino", image: M.axilas, imageAlt: "Homem após cera nas axilas Pello Menos" },
  { id: "antebraco-cera-masc", name: "Antebraço – Cera", duration: "15 min • Avulso", originalCents: 5190, category: "bracos", method: "cera", audience: "masculino", image: M.antebraco, imageAlt: "Homem após cera no antebraço Pello Menos" },
  { id: "bracos-cera-masc", name: "Braços – Cera", duration: "20 min • Avulso", originalCents: 7190, category: "bracos", method: "cera", audience: "masculino", image: M.bracos, imageAlt: "Homem após cera nos braços Pello Menos" },
  { id: "costas-cera-masc", name: "Costas – Cera", duration: "25 min • Avulso", originalCents: 5800, highlight: true, category: "corpo", method: "cera", audience: "masculino", image: M.costas, imageAlt: "Homem após cera nas costas Pello Menos" },
  { id: "coxa-cera-masc", name: "Coxa – Cera", duration: "20 min • Avulso", originalCents: 5190, category: "pernas", method: "cera", audience: "masculino", image: M.pernas, imageAlt: "Homem após cera na coxa Pello Menos" },
  { id: "faixa-cera-masc", name: "Faixa – Cera", duration: "10 min • Avulso", originalCents: 2800, category: "corpo", method: "cera", audience: "masculino", image: M.abdomen, imageAlt: "Homem após cera na faixa Pello Menos" },
  { id: "intergluteos-cera-masc", name: "Interglúteos – Cera", duration: "15 min • Avulso", originalCents: 3390, category: "corpo", method: "cera", audience: "masculino", image: M.virilha, imageAlt: "Homem após cera nos interglúteos Pello Menos" },
  { id: "nariz-cera-masc", name: "Nariz – Cera", duration: "10 min • Avulso", originalCents: 3000, category: "rosto", method: "cera", audience: "masculino", image: M.pescoco, imageAlt: "Homem após cera no nariz Pello Menos" },
  { id: "nadegas-cera-masc", name: "Nádegas – Cera", duration: "20 min • Avulso", originalCents: 5190, category: "corpo", method: "cera", audience: "masculino", image: M.virilha, imageAlt: "Homem após cera nas nádegas Pello Menos" },
  { id: "meia-nadega-cera-masc", name: "Meia nádega – Cera", duration: "15 min • Avulso", originalCents: 2600, badge: "Cera", category: "corpo", method: "cera", audience: "masculino", image: M.virilha, imageAlt: "Homem após cera na meia nádega Pello Menos" },
  { id: "perna-cera-masc", name: "Perna Inteira – Cera", duration: "40 min • Avulso", originalCents: 8700, badge: "5% OFF", highlight: true, category: "pernas", method: "cera", audience: "masculino", image: M.pernas, imageAlt: "Homem após cera na perna inteira Pello Menos" },
  { id: "meia-perna-cera-masc", name: "Meia Perna – Cera", duration: "20 min • Avulso", originalCents: 5190, category: "pernas", method: "cera", audience: "masculino", image: M.pernas, imageAlt: "Homem após cera na meia perna Pello Menos" },
  { id: "queixo-cera-masc", name: "Queixo – Cera", duration: "10 min • Avulso", originalCents: 2800, badge: "Cera", category: "rosto", method: "cera", audience: "masculino", image: M.barba, imageAlt: "Homem após cera no queixo Pello Menos" },
  { id: "virilha-comum-cera-masc", name: "Virilha comum – Cera", duration: "15 min • Avulso", originalCents: 3999, badge: "Cera", category: "virilha", method: "cera", audience: "masculino", image: M.virilha, imageAlt: "Homem após cera na virilha comum Pello Menos" },
  { id: "virilha-cera-masc", name: "Virilha Total – Cera", duration: "25 min • Avulso", originalCents: 8890, highlight: true, category: "virilha", method: "cera", audience: "masculino", image: M.virilha, imageAlt: "Homem após cera na virilha total Pello Menos" },

  // Esfoliação masculino — áreas equivalentes da tabela, sem seios
  { id: "esfoliacao-faixa-masc", name: "Esfoliação de faixa", duration: "10 min • Avulso", originalCents: 1400, category: "corpo", method: "esfoliacao", audience: "masculino", image: M.abdomen, imageAlt: "Esfoliação de faixa masculina Pello Menos" },
  { id: "esfoliacao-meio-braco-masc", name: "Esfoliação de meio braço", duration: "15 min • Avulso", originalCents: 2595, category: "bracos", method: "esfoliacao", audience: "masculino", image: M.antebraco, imageAlt: "Esfoliação de meio braço masculina Pello Menos" },
  { id: "esfoliacao-braco-masc", name: "Esfoliação de braço", duration: "20 min • Avulso", originalCents: 3595, category: "bracos", method: "esfoliacao", audience: "masculino", image: M.bracos, imageAlt: "Esfoliação de braço masculina Pello Menos" },
  { id: "esfoliacao-meia-perna-masc", name: "Esfoliação de meia perna", duration: "20 min • Avulso", originalCents: 2595, category: "pernas", method: "esfoliacao", audience: "masculino", image: M.pernas, imageAlt: "Esfoliação de meia perna masculina Pello Menos" },
  { id: "esfoliacao-abdomen-masc", name: "Esfoliação de abdômen", duration: "15 min • Avulso", originalCents: 2995, category: "corpo", method: "esfoliacao", audience: "masculino", image: M.abdomen, imageAlt: "Esfoliação de abdômen masculina Pello Menos" },
  { id: "esfoliacao-axilas-masc", name: "Esfoliação de axilas", duration: "15 min • Avulso", originalCents: 1750, badge: "Pele", category: "axilas", method: "esfoliacao", audience: "masculino", image: M.axilas, imageAlt: "Esfoliação de axilas masculina Pello Menos" },
  { id: "esfoliacao-nadegas-masc", name: "Esfoliação de nádegas", duration: "15 min • Avulso", originalCents: 2595, category: "corpo", method: "esfoliacao", audience: "masculino", image: M.virilha, imageAlt: "Esfoliação de nádegas masculina Pello Menos" },
  { id: "esfoliacao-meia-nadega-masc", name: "Esfoliação de meia nádega", duration: "10 min • Avulso", originalCents: 1300, category: "corpo", method: "esfoliacao", audience: "masculino", image: M.virilha, imageAlt: "Esfoliação de meia nádega masculina Pello Menos" },
  { id: "esfoliacao-coxa-masc", name: "Esfoliação de coxa", duration: "20 min • Avulso", originalCents: 2595, category: "pernas", method: "esfoliacao", audience: "masculino", image: M.pernas, imageAlt: "Esfoliação de coxa masculina Pello Menos" },
  { id: "esfoliacao-costas-masc", name: "Esfoliação de costas", duration: "20 min • Avulso", originalCents: 2900, category: "corpo", method: "esfoliacao", audience: "masculino", image: M.costas, imageAlt: "Esfoliação de costas masculina Pello Menos" },
  { id: "esfoliacao-perna-masc", name: "Esfoliação de perna inteira", duration: "25 min • Avulso", originalCents: 4350, badge: "Pele", highlight: true, category: "pernas", method: "esfoliacao", audience: "masculino", image: M.pernas, imageAlt: "Esfoliação de perna inteira masculina Pello Menos" },
  { id: "esfoliacao-virilha-masc", name: "Esfoliação de virilha", duration: "15 min • Avulso", originalCents: 2000, category: "virilha", method: "esfoliacao", audience: "masculino", image: M.virilha, imageAlt: "Esfoliação de virilha masculina Pello Menos" },
  { id: "esfoliacao-virilha-faixa-masc", name: "Esfoliação de virilha + faixa", duration: "20 min • Avulso", originalCents: 2699, category: "virilha", method: "esfoliacao", audience: "masculino", image: M.virilha, imageAlt: "Esfoliação de virilha com faixa masculina Pello Menos" },

  // Laser masculino — original da tabela/loja para a área equivalente
  { id: "axilas-laser-masc", name: "Axilas Laser", duration: "15 min • até 10 sessões", originalCents: 89990, badge: "5% OFF", highlight: true, category: "axilas", method: "laser", audience: "masculino", image: M.axilas, imageAlt: "Homem em campanha de laser nas axilas Pello Menos" },
  { id: "peito-laser-masc", name: "Peito Laser", duration: "25 min • até 10 sessões", originalCents: 149500, badge: "Masculino", highlight: true, category: "corpo", method: "laser", audience: "masculino", image: M.peito, imageAlt: "Homem em campanha de laser no peito Pello Menos" },
  { id: "costas-laser-masc", name: "Costas Laser", duration: "30 min • até 10 sessões", originalCents: 149500, badge: "Masculino", highlight: true, category: "corpo", method: "laser", audience: "masculino", image: M.costas, imageAlt: "Homem em campanha de laser nas costas Pello Menos" },
  { id: "abdomen-laser-masc", name: "Abdômen Laser", duration: "20 min • até 10 sessões", originalCents: 102000, category: "corpo", method: "laser", audience: "masculino", image: M.abdomen, imageAlt: "Homem em campanha de laser no abdômen Pello Menos" },
  { id: "barba-laser-masc", name: "Barba Laser", duration: "15 min • até 10 sessões", originalCents: 99000, badge: "Rosto", highlight: true, category: "rosto", method: "laser", audience: "masculino", image: M.barba, imageAlt: "Homem em campanha de laser na barba Pello Menos" },
  { id: "nuca-laser-masc", name: "Nuca Laser", duration: "10 min • até 10 sessões", originalCents: 70300, category: "rosto", method: "laser", audience: "masculino", image: M.nuca, imageAlt: "Homem em campanha de laser na nuca Pello Menos" },
  { id: "pescoco-laser-masc", name: "Pescoço Laser", duration: "10 min • até 10 sessões", originalCents: 70300, category: "rosto", method: "laser", audience: "masculino", image: M.pescoco, imageAlt: "Homem em campanha de laser no pescoço Pello Menos" },
  { id: "orelhas-laser-masc", name: "Orelhas Laser", duration: "10 min • até 10 sessões", originalCents: 43990, category: "rosto", method: "laser", audience: "masculino", image: M.barba, imageAlt: "Homem em campanha de laser nas orelhas Pello Menos" },
  { id: "nariz-laser-masc", name: "Nariz Laser", duration: "10 min • até 10 sessões", originalCents: 34000, category: "rosto", method: "laser", audience: "masculino", image: M.pescoco, imageAlt: "Homem em campanha de laser no nariz Pello Menos" },
  { id: "bracos-laser-masc", name: "Braços Inteiros Laser", duration: "20 min • até 10 sessões", originalCents: 144000, category: "bracos", method: "laser", audience: "masculino", image: M.bracos, imageAlt: "Homem em campanha de laser nos braços Pello Menos" },
  { id: "antebraco-laser-masc", name: "Antebraço Laser", duration: "15 min • até 10 sessões", originalCents: 108000, category: "bracos", method: "laser", audience: "masculino", image: M.antebraco, imageAlt: "Homem em campanha de laser no antebraço Pello Menos" },
  { id: "perna-laser-masc", name: "Perna Inteira Laser", duration: "40 min • até 10 sessões", originalCents: 423500, badge: "Verão", category: "pernas", method: "laser", audience: "masculino", image: M.pernas, imageAlt: "Homem em campanha de laser nas pernas Pello Menos" },
  { id: "meia-perna-laser-masc", name: "Meia Perna Laser", duration: "20 min • até 10 sessões", originalCents: 203000, category: "pernas", method: "laser", audience: "masculino", image: M.pernas, imageAlt: "Homem em campanha de laser na meia perna Pello Menos" },
  { id: "virilha-laser-masc", name: "Virilha Laser", duration: "20 min • até 10 sessões", originalCents: 209000, category: "virilha", method: "laser", audience: "masculino", image: M.virilha, imageAlt: "Homem em campanha de laser na virilha Pello Menos" },
];

function defaultDescription(item: ProductSeed, method: ProductMethod, audience: ProductAudience) {
  const who =
    audience === "masculino"
      ? "Atendimento masculino, por ordem de chegada."
      : "Atendimento feminino, por ordem de chegada.";
  if (method === "laser") {
    return `${item.name} em pacote de até 10 sessões na Pello Menos. ${who} Informe a unidade no pedido: o pacote só pode ser usado na loja escolhida.`;
  }
  if (method === "cera") {
    return `${item.name} em sessão avulsa na Pello Menos. Resultado no mesmo dia. ${who} Escolha a unidade obrigatória no pedido.`;
  }
  if (method === "linha") {
    return `${item.name} com precisão no contorno. Sessão avulsa. ${who} Selecione a loja no pedido.`;
  }
  if (method === "esfoliacao") {
    return `${item.name} para renovar a pele e potencializar a cera. Sessão avulsa. ${who} Selecione a unidade no pedido.`;
  }
  return "Body Splash oficial da linha Pello Menos para o cuidado em casa após a depilação.";
}

function catalogSku(index: number) {
  return `PM-${String(index + 1).padStart(4, "0")}`;
}

function catalogCode(id: string) {
  return `PEL-${id.replace(/-/g, "").toUpperCase()}`;
}

export const products: Product[] = catalogItems.map((item, index) => {
  const { originalCents, method: explicitMethod, audience: explicitAudience, ...rest } = item;
  const method = inferMethod(item.id, explicitMethod);
  const audience = explicitAudience ?? "feminino";
  return {
    ...rest,
    ...withEcommercePrice(originalCents),
    duration: item.duration.replace(/^(\d+)/, "~$1"),
    method,
    audience,
    sku: catalogSku(index),
    code: catalogCode(item.id),
    description: defaultDescription(item, method, audience),
  };
});

export function getProductById(id: string) {
  return products.find((item) => item.id === id);
}

export function productsForAudience(audience: ProductAudience) {
  return products.filter(
    (item) => item.audience === audience || item.method === "produto",
  );
}

export const storeUnits: StoreUnit[] = [
  {
    id: "copacabana",
    name: "Copacabana",
    city: "Rio de Janeiro",
    state: "RJ",
    address: "Av. Nossa Senhora de Copacabana, 680 — loja 12",
    hours: "Seg a sáb, 9h às 20h",
  },
  {
    id: "tijuca",
    name: "Tijuca",
    city: "Rio de Janeiro",
    state: "RJ",
    address: "Rua Conde de Bonfim, 318 — sala 204",
    hours: "Seg a sáb, 9h às 20h",
  },
  {
    id: "campo-grande",
    name: "Campo Grande",
    city: "Rio de Janeiro",
    state: "RJ",
    address: "Estrada do Mendanha, 555 — loja 8",
    hours: "Seg a sáb, 9h às 19h",
  },
  {
    id: "barra",
    name: "Barra da Tijuca",
    city: "Rio de Janeiro",
    state: "RJ",
    address: "Av. das Américas, 4666 — bloco 2",
    hours: "Seg a sáb, 10h às 21h",
  },
  {
    id: "paulista",
    name: "Avenida Paulista",
    city: "São Paulo",
    state: "SP",
    address: "Av. Paulista, 2073 — conjunto 1402",
    hours: "Seg a sáb, 9h às 20h",
  },
];

export function getStoreUnitById(id: string) {
  return storeUnits.find((item) => item.id === id);
}

const CROSS_SELL: Record<string, string[]> = {
  "virilha-cera": ["meia-nadega-cera", "coxa-cera", "axila-cera"],
  "virilha-laser": ["virilha-comum-laser", "meia-nadega-cera", "coxa-cera"],
  "virilha-comum-laser": ["virilha-laser", "virilha-cavada-laser"],
  "peito-laser-masc": ["costas-laser-masc", "abdomen-laser-masc", "axilas-laser-masc"],
  "barba-laser-masc": ["nuca-laser-masc", "pescoco-laser-masc", "orelhas-laser-masc"],
  "peito-cera-masc": ["costas-cera-masc", "abdomen-cera-masc", "axila-cera-masc"],
  "virilha-cera-masc": ["meia-nadega-cera-masc", "coxa-cera-masc", "axila-cera-masc"],
};

export function relatedProducts(product: Product, limit = 4) {
  const mapped = (CROSS_SELL[product.id] ?? [])
    .map((id) => products.find((item) => item.id === id))
    .filter((item): item is Product => Boolean(item));
  const sameMethod = products.filter(
    (item) =>
      item.id !== product.id &&
      item.audience === product.audience &&
      item.method === product.method &&
      !mapped.some((related) => related.id === item.id),
  );
  const sameCategory = products.filter(
    (item) =>
      item.category === product.category &&
      item.audience === product.audience &&
      item.id !== product.id &&
      !mapped.some((related) => related.id === item.id) &&
      !sameMethod.some((related) => related.id === item.id),
  );
  return [...mapped, ...sameMethod, ...sameCategory].slice(0, limit);
}

const pernaCeraHero = formatHeroPrice(8700);
const axilasLaserHero = formatHeroPrice(89990);
const virilhaLaserHero = formatHeroPrice(209000);
const bracosLaserHero = formatHeroPrice(144000);
const peitoHero = formatHeroPrice(149500);
const costasHero = formatHeroPrice(149500);
const barbaHero = formatHeroPrice(99000);

export const heroSlides: HeroSlide[] = [
  {
    id: "verao",
    badge: "Cera 5% OFF",
    title: "Pernas prontas pra viver",
    ...pernaCeraHero,
    cta: "Ver cera",
    ctaHref: "/#cera",
    image: "/images/hero/hero-campaign-low.png",
    imageMobile: "/images/hero/hero-campaign-low-m.jpg",
    imagePosition: "50% 82%",
    imagePositionMobile: "50% 78%",
    imageAlt: "Mulher na campanha de pernas com cera Pello Menos",
    layout: "copy-top",
  },
  {
    id: "laser-10",
    badge: "5% OFF no e-commerce",
    title: "10 sessões de laser nas axilas",
    ...axilasLaserHero,
    cta: "Ver laser",
    ctaHref: "/#laser",
    image: "/images/hero/hero-campaign-center.png",
    imageMobile: "/images/hero/hero-campaign-center-m.jpg",
    imagePosition: "50% 40%",
    imagePositionMobile: "50% 38%",
    imageAlt: "Mulher no centro da campanha de laser nas axilas Pello Menos",
    layout: "split",
  },
  {
    id: "virilha",
    badge: "Mais vendido",
    title: "Virilha total a laser",
    ...virilhaLaserHero,
    cta: "Ver serviços",
    ctaHref: "/#produtos",
    image: "/images/hero/hero-campaign-left.png",
    imageMobile: "/images/hero/hero-campaign-left-m.jpg",
    imagePosition: "22% 40%",
    imagePositionMobile: "28% 38%",
    imageAlt: "Mulher à esquerda na campanha de virilha a laser Pello Menos",
    layout: "copy-right",
  },
  {
    id: "bracos",
    badge: "Novo no laser",
    title: "Braços inteiros a laser",
    ...bracosLaserHero,
    cta: "Ver braços",
    ctaHref: "/#laser",
    image: "/images/hero/hero-campaign-right.png",
    imageMobile: "/images/hero/hero-campaign-right-m.jpg",
    imagePosition: "78% 40%",
    imagePositionMobile: "72% 38%",
    imageAlt: "Mulher à direita na campanha de braços a laser Pello Menos",
    layout: "copy-left",
  },
];

export const heroSlidesMasculino: HeroSlide[] = [
  {
    id: "peito",
    badge: "Laser 5% OFF",
    title: "Peito liso, rotina leve",
    ...peitoHero,
    cta: "Ver laser",
    ctaHref: "/masculino#laser",
    image: M.heroPeito,
    imageMobile: M.heroPeitoM,
    imagePosition: "48% 28%",
    imagePositionMobile: "50% 26%",
    imageAlt: "Homem na campanha de laser no peito Pello Menos",
    layout: "copy-top",
  },
  {
    id: "costas",
    badge: "Masculino",
    title: "Costas a laser",
    ...costasHero,
    cta: "Ver costas",
    ctaHref: "/masculino#laser",
    image: M.heroCostas,
    imageMobile: M.heroCostasM,
    imagePosition: "50% 26%",
    imagePositionMobile: "50% 24%",
    imageAlt: "Homem na campanha de laser nas costas Pello Menos",
    layout: "split",
  },
  {
    id: "axilas-m",
    badge: "5% OFF no e-commerce",
    title: "10 sessões de laser nas axilas",
    ...axilasLaserHero,
    cta: "Ver axilas",
    ctaHref: "/masculino#produtos",
    image: M.heroAxilas,
    imageMobile: M.heroAxilasM,
    imagePosition: "42% 32%",
    imagePositionMobile: "50% 28%",
    imageAlt: "Homem na campanha de laser nas axilas Pello Menos",
    layout: "copy-right",
  },
  {
    id: "barba",
    badge: "Rosto",
    title: "Barba a laser",
    ...barbaHero,
    cta: "Ver barba",
    ctaHref: "/masculino#laser",
    image: M.heroBarba,
    imageMobile: M.heroBarbaM,
    imagePosition: "58% 28%",
    imagePositionMobile: "55% 22%",
    imageAlt: "Homem na campanha de laser na barba Pello Menos",
    layout: "copy-left",
  },
];

export const categories: Category[] = [
  { id: "cera", label: "Cera", image: "/images/categories/cat-pernas-v2.png", href: "#cera" },
  { id: "laser", label: "Laser", image: "/images/categories/cat-axilas-v2.png", href: "#laser" },
  { id: "linha", label: "Linha", image: "/images/categories/cat-rosto-v2.png", href: "#linha" },
  { id: "esfoliacao", label: "Esfoliação", image: "/images/categories/cat-pernas-v2.png", href: "#esfoliacao" },
  { id: "virilha", label: "Virilha", image: "/images/categories/cat-virilha-v2.png", href: "#produtos" },
];

export const categoriesMasculino: Category[] = [
  { id: "cera", label: "Cera", image: M.catCera, href: "#cera" },
  { id: "laser", label: "Laser", image: M.catLaser, href: "#laser" },
  { id: "esfoliacao", label: "Esfoliação", image: M.catEsfoliacao, href: "#esfoliacao" },
  { id: "axilas", label: "Axilas", image: M.catAxilas, href: "#produtos" },
  { id: "corpo", label: "Corpo", image: M.catCorpo, href: "#produtos" },
  { id: "rosto", label: "Rosto", image: M.catRosto, href: "#laser" },
  { id: "pernas", label: "Pernas", image: M.catPernas, href: "#produtos" },
];

const female = products.filter((item) => item.audience === "feminino");
const male = products.filter((item) => item.audience === "masculino");
const officialProducts = products.filter((item) => item.method === "produto");

export const productRails = {
  ceraOfertas: female.filter((item) => item.method === "cera"),
  ceraAreas: female.filter((item) =>
    [
      "virilha-cera",
      "axila-cera",
      "perna-cera",
      "buco-cera",
      "meia-nadega-cera",
      "design-sobrancelha",
      "meia-perna-cera",
      "coxa-cera",
      "bracos-cera",
      "virilha-comum-cera",
      "nadegas-cera",
      "queixo-cera",
      "costas-cera",
      "virilha-cavada-cera",
    ].includes(item.id),
  ),
  laserRosto: female.filter(
    (item) => item.method === "laser" && item.category === "rosto",
  ),
  laserCorpo: female.filter(
    (item) => item.method === "laser" && item.category !== "rosto",
  ),
  esfoliacao: female.filter((item) => item.method === "esfoliacao"),
  linha: female.filter((item) => item.method === "linha"),
  produtos: officialProducts,
  masculino: male,
  ceraOfertasMasc: male.filter((item) => item.method === "cera"),
  ceraAreasMasc: male.filter((item) =>
    [
      "virilha-cera-masc",
      "axila-cera-masc",
      "perna-cera-masc",
      "peito-cera-masc",
      "meia-nadega-cera-masc",
      "meia-perna-cera-masc",
      "coxa-cera-masc",
      "bracos-cera-masc",
      "virilha-comum-cera-masc",
      "nadegas-cera-masc",
      "queixo-cera-masc",
      "costas-cera-masc",
      "abdomen-cera-masc",
    ].includes(item.id),
  ),
  esfoliacaoMasc: male.filter((item) => item.method === "esfoliacao"),
  laserRostoMasc: male.filter(
    (item) => item.method === "laser" && item.category === "rosto",
  ),
  laserCorpoMasc: male.filter(
    (item) => item.method === "laser" && item.category !== "rosto",
  ),
};

export const rectangularBanners: PromoBannerData[] = [
  {
    id: "semana",
    badge: "Novidade",
    title: "Semana da Beleza",
    subtitle: "5% OFF em todos os serviços no e-commerce.",
    image: "/images/hero/promo-semana-v2.png",
    imageMobile: "/images/hero/promo-semana-v2-m.jpg",
    imagePosition: "50% 38%",
    imagePositionMobile: "50% 32%",
    imageAlt: "Mulher com axilas lisas na Semana da Beleza",
  },
  {
    id: "laser",
    badge: "Tecnologia",
    title: "Laser de última geração",
    subtitle: "Sessões mais rápidas e resultado duradouro.",
    image: "/images/hero/promo-laser-v3.png",
    imageMobile: "/images/hero/promo-laser-v3-m.jpg",
    imagePosition: "28% 40%",
    imagePositionMobile: "32% 32%",
    imageAlt: "Mulher em sessão de laser em clínica com luz natural",
    textSide: "right",
    overlay: "purple",
  },
  {
    id: "olhar",
    badge: "Olhar",
    title: "Design de sobrancelha",
    subtitle: "Cera, henna e realce para valorizar o olhar.",
    image: "/images/hero/promo-olhar-v2.png",
    imageMobile: "/images/hero/promo-olhar-v2-m.jpg",
    imagePosition: "50% 32%",
    imagePositionMobile: "50% 28%",
    imageAlt: "Mulher com design de sobrancelha em spa com luz e textura",
    overlay: "purple",
  },
];

export const rectangularBannersMasculino: PromoBannerData[] = [
  {
    id: "laser-m",
    badge: "Tecnologia",
    title: "Laser masculino",
    subtitle: "Peito, costas, barba e corpo com 5% OFF no site.",
    image: M.promoLaser,
    imageMobile: M.promoLaserM,
    imagePosition: "38% 40%",
    imagePositionMobile: "42% 32%",
    imageAlt: "Sessão de laser masculino na clínica Pello Menos",
    textSide: "right",
    overlay: "purple",
  },
  {
    id: "corpo-m",
    badge: "Corpo",
    title: "Costas e peito",
    subtitle: "As áreas mais pedidas do público masculino.",
    image: M.promoCorpo,
    imageMobile: M.promoCorpoM,
    imagePosition: "78% 40%",
    imagePositionMobile: "50% 28%",
    imageAlt: "Homem na campanha de costas e peito Pello Menos",
    overlay: "purple",
  },
];

export const squareBanners: SquareBannerData[] = [
  {
    id: "verao",
    title: "Combos Verão",
    subtitle: "5% OFF no site",
    image: "/images/hero/destaque-verao.png",
    imagePosition: "50% 30%",
    imageAlt: "Mulher alisando as pernas para o verão",
  },
  {
    id: "presente",
    title: "Cartão Presente",
    subtitle: "Surpreenda quem você ama",
    image: "/images/hero/destaque-presente.png",
    imagePosition: "50% 28%",
    imageAlt: "Mulher com cartão presente Pello Menos",
  },
  {
    id: "combo",
    title: "Combos de laser",
    subtitle: "Rosto, braços e corpo",
    badge: "Combos",
    image: "/images/hero/destaque-combo.png",
    imagePosition: "50% 28%",
    imageAlt: "Mulher cuidando da pele após sessão de laser",
  },
  {
    id: "olhar",
    title: "Sobrancelhas",
    subtitle: "Design e henna",
    image: "/images/hero/destaque-olhar.png",
    imagePosition: "50% 22%",
    imageAlt: "Mulher com design de sobrancelha",
  },
];

export const squareBannersMasculino: SquareBannerData[] = [
  {
    id: "peito",
    title: "Peito a laser",
    subtitle: "5% OFF no site",
    badge: "Destaque",
    image: M.destaquePeito,
    imagePosition: "50% 22%",
    imageAlt: "Destaque de laser no peito masculino",
  },
  {
    id: "verao-m",
    title: "Pernas e corpo",
    subtitle: "Combos verão",
    image: M.destaqueVerao,
    imagePosition: "50% 30%",
    imageAlt: "Destaque de pernas no catálogo masculino",
  },
  {
    id: "barba",
    title: "Barba a laser",
    subtitle: "Rosto definido",
    image: M.destaqueBarba,
    imagePosition: "50% 22%",
    imageAlt: "Destaque de barba a laser",
  },
];

export const googleReviews: Review[] = [
  {
    id: "r1",
    name: "Camila R.",
    rating: 5,
    text: "Fiz axilas a laser e o resultado veio rápido. Atendimento impecável.",
    time: "há 2 semanas",
  },
  {
    id: "r2",
    name: "Juliana M.",
    rating: 5,
    text: "Ambiente lindo e profissional. Volto sempre para as sessões.",
    time: "há 1 mês",
  },
  {
    id: "r3",
    name: "Patrícia S.",
    rating: 4,
    text: "Gostei muito da virilha a laser. Recomendo o pacote de 10 sessões.",
    time: "há 3 semanas",
  },
  {
    id: "r4",
    name: "Fernanda L.",
    rating: 5,
    text: "Buço a cera perfeito. Já indiquei para as amigas.",
    time: "há 5 dias",
  },
  {
    id: "r5",
    name: "Bianca T.",
    rating: 5,
    text: "Fiz meia perna e braços a laser. Sai lisa e o atendimento é rápido.",
    time: "há 4 dias",
  },
  {
    id: "r6",
    name: "Larissa P.",
    rating: 5,
    text: "Design de sobrancelha ficou impecável. Virou meu ritual.",
    time: "há 1 semana",
  },
];

export const googleReviewsMasculino: Review[] = [
  {
    id: "m1",
    name: "Rafael C.",
    rating: 5,
    text: "Fiz peito e costas a laser. Atendimento rápido e resultado nítido.",
    time: "há 2 semanas",
  },
  {
    id: "m2",
    name: "Bruno M.",
    rating: 5,
    text: "Barba a laser mudou a rotina. Ambiente discreto e profissional.",
    time: "há 1 mês",
  },
  {
    id: "m3",
    name: "Pedro S.",
    rating: 4,
    text: "Axilas a laser valeram o pacote. Comprei pelo site com 5% OFF.",
    time: "há 3 semanas",
  },
  {
    id: "m4",
    name: "Lucas T.",
    rating: 5,
    text: "Costas lisas depois de poucas sessões. Recomendo a unidade da Tijuca.",
    time: "há 5 dias",
  },
  {
    id: "m5",
    name: "Thiago P.",
    rating: 5,
    text: "Nuca e pescoço a laser. Saiu no mesmo fluxo, sem hora marcada.",
    time: "há 4 dias",
  },
  {
    id: "m6",
    name: "Marcelo L.",
    rating: 5,
    text: "Pernas a laser para o verão. Compra pelo e-commerce foi simples.",
    time: "há 1 semana",
  },
];

export const googleBusiness = {
  name: "Pello Menos",
  rating: 4.9,
  count: "2.148",
};

export const audienceLinks = [
  { href: "/", label: "Feminino", audience: "feminino" as const },
  { href: "/masculino", label: "Masculino", audience: "masculino" as const },
];

export const navLinks = [
  { href: "/#produtos", label: "Serviços" },
  { href: "/carrinho", label: "Carrinho" },
  { href: "/checkout", label: "Pagamento" },
];
