export type ProductCategory =
  | "axilas"
  | "virilha"
  | "pernas"
  | "rosto"
  | "sobrancelha"
  | "bracos"
  | "corpo"
  | "torax"
  | "produtos";

export type ProductMethod =
  | "cera"
  | "laser"
  | "linha"
  | "esfoliacao"
  | "produto"
  | "plano"
  | "presente";

export type ServiceMethod = "cera" | "laser" | "linha" | "esfoliacao";

export type AreaCategory =
  | "axilas"
  | "virilha"
  | "pernas"
  | "rosto"
  | "sobrancelha"
  | "bracos"
  | "corpo"
  | "torax";

export type ProductAudience = "feminino" | "masculino";

export type StoreState = "RJ" | "SP" | "DF";

export type PriceRegion = "rj-sp" | "sp-df";

export type StoreUnit = {
  id: string;
  code: string;
  name: string;
  city: string;
  state: StoreState;
  address: string;
  hours: string;
  offersCera: boolean;
  offersLaser: boolean;
  offersCeraMasculino: boolean;
  offersLaserMasculino: boolean;
  priceRegion: PriceRegion;
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
  skipDiscount?: boolean;
  description?: string;
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
  href?: string;
};

export type NavChild = {
  label: string;
  href: string;
};

export type NavItem = {
  label: string;
  href: string;
  children?: NavChild[];
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
  return audience === "masculino" ? "/masculino/servicos" : "/servicos";
}

export function serviceHref(audience: ProductAudience, method?: ServiceMethod) {
  const base = audience === "masculino" ? "/masculino/servicos" : "/servicos";
  return method ? `${base}/${method}` : base;
}

export function areaHref(audience: ProductAudience, category: AreaCategory) {
  const base = audience === "masculino" ? "/masculino/area" : "/area";
  return `${base}/${category}`;
}

export function planosHref(audience: ProductAudience) {
  return audience === "masculino" ? "/masculino/planos" : "/planos";
}

export function retailHref(audience: ProductAudience) {
  return audience === "masculino" ? "/masculino/produtos" : "/produtos";
}

export const SHARED_METHODS: ProductMethod[] = ["produto", "plano", "presente"];

export function isSharedProduct(product: Pick<Product, "method">) {
  return SHARED_METHODS.includes(product.method);
}

export const categoryLabels: Record<ProductCategory, string> = {
  axilas: "Axilas",
  virilha: "Virilha",
  pernas: "Pernas",
  rosto: "Rosto",
  sobrancelha: "Sobrancelha",
  bracos: "Braços",
  corpo: "Corpo",
  torax: "Tórax/abdômen",
  produtos: "Produtos",
};

export const methodLabels: Record<ProductMethod, string> = {
  cera: "Cera",
  laser: "Laser",
  linha: "Linha",
  esfoliacao: "Esfoliação",
  produto: "Produtos",
  plano: "Planos",
  presente: "Cartão Presente",
};

export const serviceMethods: { id: ServiceMethod; label: string; subtitle: string }[] = [
  { id: "cera", label: "Cera", subtitle: "Sessão avulsa, resultado no mesmo dia" },
  { id: "laser", label: "Laser", subtitle: "Pacotes de até 10 sessões" },
  { id: "linha", label: "Linha", subtitle: "Precisão no contorno do rosto" },
  { id: "esfoliacao", label: "Esfoliação", subtitle: "Pele pronta para a cera" },
];

export function serviceMethodsFor(audience: ProductAudience) {
  return serviceMethods.filter((item) => audience === "feminino" || item.id !== "linha");
}

export const MIN_INSTALLMENT_CENTS = 5000;
export const WAX_TEN_X_MIN_CENTS = 18000;

export function inferMethod(id: string, explicit?: ProductMethod): ProductMethod {
  if (explicit) return explicit;
  if (id.includes("linha")) return "linha";
  if (id.includes("esfolia")) return "esfoliacao";
  if (id.includes("plano")) return "plano";
  if (id.includes("presente") || id.includes("cartao")) return "presente";
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
  if (method === "plano") {
    return { times: 1, installmentCents: priceCents };
  }
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
  if (method === "plano") {
    return "Planos são cobrados no valor cheio, sem parcelamento.";
  }
  if (method === "cera") {
    return "Em cera, 10x só acima de R$ 180. Parcela mínima de R$ 50.";
  }
  return "Parcele em até 10x, com parcela mínima de R$ 50.";
}

export function catalogImage(id: string, audience: ProductAudience = "feminino") {
  if (audience === "masculino") {
    return `/images/products/male/${id}.png`;
  }
  return `/images/products/${id}.png`;
}

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
  peito: "/images/products/male/peito-cera-masc.png",
  costas: "/images/products/male/costas-cera-masc.png",
  barba: "/images/products/male/barba-laser-masc.png",
  axilas: "/images/products/male/axila-cera-masc.png",
  abdomen: "/images/products/male/abdomen-cera-masc.png",
  bracos: "/images/products/male/bracos-cera-masc.png",
  pernas: "/images/products/male/perna-cera-masc.png",
  virilha: "/images/products/male/virilha-cera-masc.png",
  pescoco: "/images/products/male/pescoco-laser-masc.png",
  antebraco: "/images/products/male/antebraco-cera-masc.png",
};

const catalogItems: ProductSeed[] = [
  // Cera / laser / linha feminino — nomes, preços Copacabana I e descrições do CSV da loja
  { id: "abdomen-cera", name: "Abdômen – Cera", duration: "15 min • Avulso", originalCents: 5801, category: "corpo", image: catalogImage("abdomen-cera"), imageAlt: "Abdômen após cera", description: "A depilação a cera do abdômen feminino vai remover os pelos da parede abdominal abaixo dos seios até a linha do baixo ventre." },
  { id: "axila-cera", name: "Axila – Cera", duration: "15 min • Avulso", originalCents: 3300, category: "axilas", image: catalogImage("axila-cera"), imageAlt: "Axila lisa após cera", description: "Garanta axilas suaves e livre de pelos com a depilação a cera. Resultados duradouros para sua maior confiança.", badge: "Cera", highlight: true },
  { id: "antebraco-cera", name: "Antebraço – Cera", duration: "15 min • Avulso", originalCents: 4990, category: "bracos", image: catalogImage("antebraco-cera"), imageAlt: "Antebraço após cera", description: "A depilação a cera do antebraço feminino vai remover os pelos do antebraço, que pode ser tanto a parte superior ou inferior do membro." },
  { id: "bracos-cera", name: "Braços – Cera", duration: "20 min • Avulso", originalCents: 6990, category: "bracos", image: catalogImage("bracos-cera"), imageAlt: "Braços lisos após cera", description: "Obtenha pele suave e livre de pelos com a depilação a cera para braços. Conforto, eficácia e resultados duradouros. Agende sua sessão hoje mesmo!" },
  { id: "buco-cera", name: "Buço – Cera", duration: "10 min • Avulso", originalCents: 2690, category: "rosto", image: catalogImage("buco-cera"), imageAlt: "Buço após cera", description: "A depilação do buço com cera remove os pelos da parte em cima da boca e da parte entre o queixo e a boca.", highlight: true },
  { id: "costas-cera", name: "Costas – Cera", duration: "25 min • Avulso", originalCents: 5501, category: "corpo", image: catalogImage("costas-cera"), imageAlt: "Costas após cera", description: "Desfrute de costas lisas e sem pelos com nossa depilação a cera. Resultados suaves e duradouros para uma pele sedosa. Agende já!" },
  { id: "coxa-cera", name: "Coxa – Cera", duration: "20 min • Avulso", originalCents: 4990, category: "pernas", image: catalogImage("coxa-cera"), imageAlt: "Coxa após cera", description: "Transforme suas coxas com nossa depilação a cera. Pele macia, livre de pelos e resultados prolongados. Agende sua sessão agora!" },
  { id: "faixa-cera", name: "Faixa – Cera", duration: "10 min • Avulso", originalCents: 2600, category: "corpo", image: catalogImage("faixa-cera"), imageAlt: "Faixa de cera no corpo", description: "Experimente nossa depilação a cera para faixa. Remova os pelos de forma eficaz e rápida, com resultados duradouros e conforto garantido." },
  { id: "intergluteos-cera", name: "Interglúteos – Cera", duration: "15 min • Avulso", originalCents: 3250, category: "corpo", image: catalogImage("intergluteos-cera"), imageAlt: "Cera na região dos interglúteos", description: "Depilação com cera para interglúteos: conforto e higiene garantidos. Serviço seguro e eficiente. Agende sua sessão agora mesmo!" },
  { id: "nariz-cera", name: "Nariz – Cera", duration: "10 min • Avulso", originalCents: 2890, category: "rosto", image: catalogImage("nariz-cera"), imageAlt: "Nariz após cera", description: "Depilação com cera para nariz: elimine pelos visíveis com praticidade e segurança. Rápido, eficiente e confortável. Agende já!" },
  { id: "nadegas-cera", name: "Nádegas Completas – Cera", duration: "20 min • Avulso", originalCents: 4990, category: "corpo", image: catalogImage("nadegas-cera"), imageAlt: "Nádegas após cera", description: "Depilação completa de nádegas com cera. Rápida, eficiente e ideal para quem busca conforto e bem-estar. Agende sua sessão!" },
  { id: "meia-nadega-cera", name: "Meia Nádega – Cera", duration: "15 min • Avulso", originalCents: 2499, category: "corpo", image: catalogImage("meia-nadega-cera"), imageAlt: "Meia nádega após cera", description: "Depilação a cera para meia nádega: resultado impecável e duradouro. Remova os pelos com conforto e facilidade. Agende sua sessão!", badge: "Cera" },
  { id: "perna-cera", name: "Perna Inteira – Cera", duration: "40 min • Avulso", originalCents: 8590, category: "pernas", image: catalogImage("perna-cera"), imageAlt: "Perna inteira após cera", description: "Desfrute de uma pele lisinha por mais tempo com nosso serviço de depilação a cera para perna inteira. Conforto e cuidado que sua pele merece.", badge: "5% OFF", highlight: true },
  { id: "meia-perna-cera", name: "Meia Perna – Cera", duration: "20 min • Avulso", originalCents: 4990, category: "pernas", image: catalogImage("meia-perna-cera"), imageAlt: "Meia perna após cera", description: "A depilação com cera meia perna feminino vai remover os pelos da região do joelho até o calcanhar sem qualquer custo adicional." },
  { id: "queixo-cera", name: "Queixo – Cera", duration: "10 min • Avulso", originalCents: 2690, category: "rosto", image: catalogImage("queixo-cera"), imageAlt: "Queixo após cera", description: "Elimine os pelos indesejados do queixo com nossa depilação a cera. Resultados eficazes e duradouros para uma pele suave e bem cuidada.", badge: "Cera" },
  { id: "seios-cera", name: "Seios – Cera", duration: "10 min • Avulso", originalCents: 2790, category: "corpo", image: catalogImage("seios-cera"), imageAlt: "Seios após cera", description: "Descubra a cera de depilação delicada para seios, ideal para peles sensíveis. Garanta resultados suaves e duradouros." },
  { id: "virilha-comum-cera", name: "Virilha Comum – Cera", duration: "15 min • Avulso", originalCents: 3850, category: "virilha", image: catalogImage("virilha-comum-cera"), imageAlt: "Virilha comum após cera", description: "Opte pela simplicidade com nossa depilação a cera para virilha comum. Suavidade e limpeza para sua pele.", badge: "Cera" },
  { id: "virilha-comum-faixa-cera", name: "Virilha Comum + Faixa – Cera", duration: "20 min • Avulso", originalCents: 5150, category: "virilha", image: catalogImage("virilha-comum-faixa-cera"), imageAlt: "Virilha comum com faixa após cera", description: "Depilação a cera eficaz para a virilha comum. Conforto e higiene em um serviço de qualidade." },
  { id: "virilha-cavada-cera", name: "Virilha Cavada – Cera", duration: "20 min • Avulso", originalCents: 7101, category: "virilha", image: catalogImage("virilha-cavada-cera"), imageAlt: "Virilha cavada após cera", description: "Depilação a Cera Virilha Cavada remove os pelos da virilha, lábios internos e externos, porém deixa uma pequena faixa de pelo no púbis. Essa depilação inclui ânus e cóccix." },
  { id: "virilha-cavada-faixa-cera", name: "Virilha Cavada + Faixa – Cera", duration: "25 min • Avulso", originalCents: 8401, category: "virilha", image: catalogImage("virilha-cavada-faixa-cera"), imageAlt: "Virilha cavada com faixa após cera", description: "Depilação a Cera Virilha Cavada + Faixa - Valor e Duração: Explore a depilação a cera para uma virilha cavada mais definida. Estética e conforto em harmonia." },
  { id: "virilha-modelada-cera", name: "Virilha Modelada – Cera", duration: "25 min • Avulso", originalCents: 8390, category: "virilha", image: catalogImage("virilha-modelada-cera"), imageAlt: "Virilha modelada após cera", description: "A depilação a cera da virilha feminina modelada vai remover os pelos dos lábios internos e externos e os pelos envoltos do molde escolhido pela cliente no púbis. Não inclui ânus e cóccix." },
  { id: "virilha-cera", name: "Virilha Total – Cera", duration: "25 min • Avulso", originalCents: 8501, category: "virilha", image: catalogImage("virilha-cera"), imageAlt: "Virilha total após cera", description: "Remove por completo todos os pelos da virilha, lábios externos e internos , incluindo anus , cóccix e faixa do baixo ventre.", highlight: true },
  { id: "labios-genitais-cera", name: "Lábios Genitais – Cera", duration: "15 min • Avulso", originalCents: 3850, category: "virilha", image: catalogImage("labios-genitais-cera"), imageAlt: "Cera nos lábios genitais", description: "Experimente a depilação a cera para lábios genitais com total conforto e segurança. Resultados suaves e duradouros para a sua confiança." },
  { id: "sobrancelha-cera", name: "Sobrancelha – Cera", duration: "15 min • Avulso", originalCents: 4799, category: "sobrancelha", image: catalogImage("sobrancelha-cera"), imageAlt: "Sobrancelha com cera", description: "Obtenha sobrancelhas perfeitas com nossa cera exclusiva para sobrancelhas. Perfeita para um olhar marcante!" },
  { id: "sobrancelha-realce-cera", name: "Sobrancelha + Realce – Cera", duration: "25 min • Avulso", originalCents: 7590, category: "sobrancelha", image: catalogImage("sobrancelha-realce-cera"), imageAlt: "Sobrancelha com realce", description: "Realce suas sobrancelhas com nossa cera especializada, projetada para definição e beleza duradouras. Adquira já!" },
  { id: "sobrancelha-henna-simples", name: "Sobrancelha Simples + Henna", duration: "25 min • Avulso", originalCents: 8390, category: "sobrancelha", image: catalogImage("sobrancelha-henna-simples"), imageAlt: "Sobrancelha simples com henna", description: "Transforme suas sobrancelhas com a henna e cera da Pello Menos. Definição precisa e resultados duradouros para um olhar marcante." },
  { id: "design-sobrancelha", name: "Design de Sobrancelha – Cera", duration: "20 min • Avulso", originalCents: 5850, category: "sobrancelha", image: catalogImage("design-sobrancelha"), imageAlt: "Design de sobrancelha", description: "A técnica de design de sobrancelha com cera consiste em ressaltar a beleza dos olhos e do rosto, dando-lhes o equilíbrio e a simetria adequada.", badge: "Olhar", highlight: true },
  { id: "design-sobrancelha-realce", name: "Design de Sobrancelha + Realce – Cera", duration: "30 min • Avulso", originalCents: 7850, category: "sobrancelha", image: catalogImage("design-sobrancelha-realce"), imageAlt: "Design de sobrancelha com realce", description: "Obtenha o design perfeito para suas sobrancelhas com nossa depilação a cera. Realce sua expressão de maneira natural e duradoura." },
  { id: "sobrancelha-henna", name: "Design de Sobrancelha + Henna Feminino", duration: "30 min • Avulso", originalCents: 8650, category: "sobrancelha", image: catalogImage("sobrancelha-henna"), imageAlt: "Design de sobrancelha com henna", description: "Realce suas sobrancelhas com henna e cera. Definição impecável, longa duração e visual natural. Agende sua sessão agora!", badge: "Combo" },
  { id: "realce", name: "Realce", duration: "15 min • Avulso", originalCents: 3200, category: "sobrancelha", image: catalogImage("realce"), imageAlt: "Realce de sobrancelha", description: "Realce sua beleza com nossos tratamentos exclusivos. Descubra como nossos serviços de depilação e design de sobrancelhas podem transformar seu visual.", method: "cera" },
  { id: "henna", name: "Henna", duration: "20 min • Avulso", originalCents: 4100, category: "sobrancelha", image: catalogImage("henna"), imageAlt: "Henna nas sobrancelhas", description: "Realce suas sobrancelhas com nossa henna especial. Definição perfeita, longa duração e resultados naturais. Adquira já e transforme seu olhar!", method: "cera" },

  // Linha feminino
  { id: "buco-linha", name: "Buço – Linha", duration: "10 min • Avulso", originalCents: 2092, category: "rosto", image: catalogImage("buco-linha"), imageAlt: "Buço após linha", description: "Elimine os pelos indesejados do buço com nossa depilação a linha. Resultados suaves e duradouros para uma pele impecável. Agende agora!", method: "linha", badge: "Linha" },
  { id: "queixo-linha", name: "Queixo – Linha", duration: "10 min • Avulso", originalCents: 2790, category: "rosto", image: catalogImage("queixo-linha"), imageAlt: "Queixo após linha", description: "Depilação a linha para o queixo: resultados suaves e duradouros. Remova os pelos com conforto e precisão. Agende sua sessão na Pello Menos!", method: "linha", badge: "Linha" },
  { id: "faixa-linha", name: "Faixa – Linha", duration: "10 min • Avulso", originalCents: 2550, category: "rosto", image: catalogImage("faixa-linha"), imageAlt: "Faixa após linha", description: "Depilação a linha para faixa: remoção precisa e eficaz dos pelos. Resultados suaves e duradouros para uma pele impecável. Agende sua sessão!", method: "linha", badge: "Linha" },

  // Esfoliação feminino — preço cartão da tabela oficial
  { id: "esfoliacao-faixa", name: "Esfoliação Faixa 01", duration: "10 min • Avulso", originalCents: 1200, category: "corpo", image: catalogImage("esfoliacao-faixa"), imageAlt: "Esfoliação de faixa", method: "esfoliacao" },
  { id: "esfoliacao-faixa-02", name: "Esfoliação Faixa 02", duration: "10 min • Avulso", originalCents: 2400, category: "corpo", image: catalogImage("esfoliacao-faixa-02"), imageAlt: "Esfoliação de faixa 02", method: "esfoliacao" },
  { id: "esfoliacao-meio-braco", name: "Esfoliação de meio braço", duration: "15 min • Avulso", originalCents: 2390, category: "bracos", image: catalogImage("esfoliacao-meio-braco"), imageAlt: "Esfoliação de meio braço", method: "esfoliacao" },
  { id: "esfoliacao-braco", name: "Esfoliação de braço", duration: "20 min • Avulso", originalCents: 3390, category: "bracos", image: catalogImage("esfoliacao-braco"), imageAlt: "Esfoliação de braço", method: "esfoliacao" },
  { id: "esfoliacao-meia-perna", name: "Esfoliação de meia perna", duration: "20 min • Avulso", originalCents: 2325, category: "pernas", image: catalogImage("esfoliacao-meia-perna"), imageAlt: "Esfoliação de meia perna", method: "esfoliacao" },
  { id: "esfoliacao-abdomen", name: "Esfoliação de abdômen", duration: "15 min • Avulso", originalCents: 2750, category: "corpo", image: catalogImage("esfoliacao-abdomen"), imageAlt: "Esfoliação de abdômen", method: "esfoliacao" },
  { id: "esfoliacao-axilas", name: "Esfoliação de axilas", duration: "15 min • Avulso", originalCents: 1590, category: "axilas", image: catalogImage("esfoliacao-axilas"), imageAlt: "Esfoliação de axilas", method: "esfoliacao", badge: "Pele" },
  { id: "esfoliacao-nadegas", name: "Esfoliação de nádegas", duration: "15 min • Avulso", originalCents: 2390, category: "corpo", image: catalogImage("esfoliacao-nadegas"), imageAlt: "Esfoliação de nádegas", method: "esfoliacao" },
  { id: "esfoliacao-meia-nadega", name: "Esfoliação de meia nádega", duration: "10 min • Avulso", originalCents: 1195, category: "corpo", image: catalogImage("esfoliacao-meia-nadega"), imageAlt: "Esfoliação de meia nádega", method: "esfoliacao" },
  { id: "esfoliacao-coxa", name: "Esfoliação de coxa", duration: "20 min • Avulso", originalCents: 2325, category: "pernas", image: catalogImage("esfoliacao-coxa"), imageAlt: "Esfoliação de coxa", method: "esfoliacao" },
  { id: "esfoliacao-costas", name: "Esfoliação de costas", duration: "20 min • Avulso", originalCents: 2600, category: "corpo", image: catalogImage("esfoliacao-costas"), imageAlt: "Esfoliação de costas", method: "esfoliacao" },
  { id: "esfoliacao-perna", name: "Esfoliação de perna inteira", duration: "25 min • Avulso", originalCents: 3995, category: "pernas", image: catalogImage("esfoliacao-perna"), imageAlt: "Esfoliação de perna inteira", method: "esfoliacao", badge: "Pele", highlight: true },
  { id: "esfoliacao-virilha", name: "Esfoliação de virilha", duration: "15 min • Avulso", originalCents: 1825, category: "virilha", image: catalogImage("esfoliacao-virilha"), imageAlt: "Esfoliação de virilha", method: "esfoliacao" },
  { id: "esfoliacao-virilha-faixa", name: "Esfoliação de virilha + faixa", duration: "20 min • Avulso", originalCents: 2425, category: "virilha", image: catalogImage("esfoliacao-virilha-faixa"), imageAlt: "Esfoliação de virilha com faixa", method: "esfoliacao" },
  { id: "esfoliacao-seios", name: "Esfoliação de seios", duration: "10 min • Avulso", originalCents: 1250, category: "corpo", image: catalogImage("esfoliacao-seios"), imageAlt: "Esfoliação de seios", method: "esfoliacao" },

  // Laser feminino
  { id: "axilas-laser", name: "Axilas Laser", duration: "15 min • até 10 sessões", originalCents: 89990, category: "axilas", image: catalogImage("axilas-laser"), imageAlt: "Axilas após laser", description: "Descubra a revolucionária depilação a laser para axilas. Resultados eficazes e duradouros. Conquiste axilas suaves e sem pelos. Adquira agora!", badge: "5% OFF", highlight: true },
  { id: "areola-laser", name: "Aréola Laser", duration: "10 min • até 10 sessões", originalCents: 38090, category: "corpo", image: catalogImage("areola-laser"), imageAlt: "Aréola após laser", description: "A depilação a laser da aréola feminina vai eliminar os pelos ao redor dos mamilos." },
  { id: "buco-laser", name: "Buço Laser", duration: "10 min • até 10 sessões", originalCents: 42590, category: "rosto", image: catalogImage("buco-laser"), imageAlt: "Buço após laser", description: "Na depilação a laser do buço são eliminados os pelos da parte em cima da boca e da parte entre o queixo e a boca." },
  { id: "virilha-laser", name: "Virilha Total Laser", duration: "20 min • até 10 sessões", originalCents: 209000, category: "virilha", image: catalogImage("virilha-laser"), imageAlt: "Virilha total após laser", description: "Na depilação a laser total na virilha são eliminados os pelos das seguintes regiões: virilha, lábios externos e internos, ânus, cóccix e faixa do baixo ventre.", badge: "Mais vendido", highlight: true },
  { id: "virilha-comum-laser", name: "Virilha Comum Laser", duration: "15 min • até 10 sessões", originalCents: 132000, category: "virilha", image: catalogImage("virilha-comum-laser"), imageAlt: "Virilha comum após laser", description: "Garanta sua sessão de depilação a laser para virilha no Pello Menos. Resultados incríveis com conforto e segurança garantidos." },
  { id: "virilha-cavada-laser", name: "Virilha Cavada Laser", duration: "20 min • até 10 sessões", originalCents: 179000, category: "virilha", image: catalogImage("virilha-cavada-laser"), imageAlt: "Virilha cavada após laser", description: "Experimente a depilação a laser para virilha cavada no Pello Menos. Tecnologia avançada para máxima eficiência e conforto." },
  { id: "virilha-cavada-faixa-laser", name: "Virilha Cavada c/ Faixa Laser", duration: "20 min • até 10 sessões", originalCents: 203500, category: "virilha", image: catalogImage("virilha-cavada-faixa-laser"), imageAlt: "Virilha cavada com faixa após laser", description: "Realize sua depilação a laser para virilha cavada com faixa no Pello Menos. Qualidade, segurança e resultados duradouros." },
  { id: "virilha-faixa-laser", name: "Virilha Comum + Faixa Laser", duration: "15 min • até 10 sessões", originalCents: 156000, category: "virilha", image: catalogImage("virilha-faixa-laser"), imageAlt: "Virilha comum com faixa após laser", description: "Transforme sua experiência de depilação com o laser para virilha comum + faixa no Pello Menos. Conforto e eficácia em cada sessão." },
  { id: "perna-laser", name: "Perna Inteira Laser", duration: "40 min • até 10 sessões", originalCents: 423500, category: "pernas", image: catalogImage("perna-laser"), imageAlt: "Perna inteira após laser", description: "Transforme suas pernas com a depilação a laser. Suavidade duradoura e eficácia comprovada. Conheça nosso tratamento para pernas inteiras. Compre já!", badge: "Verão" },
  { id: "meia-perna-laser", name: "Meia Perna Laser", duration: "20 min • até 10 sessões", originalCents: 203000, category: "pernas", image: catalogImage("meia-perna-laser"), imageAlt: "Meia perna após laser", description: "A depilação a laser meia perna feminino vai eliminar os pelos da região do joelho até o calcanhar, podendo fazer a faixa do pé e dos dedos sem qualquer custo adicional.", badge: "Verão", highlight: true },
  { id: "coxas-laser", name: "Coxas Inteiras Laser", duration: "25 min • até 10 sessões", originalCents: 219990, category: "pernas", image: catalogImage("coxas-laser"), imageAlt: "Coxas após laser", description: "Na depilação a laser da coxa feminino são eliminados os pelos da linha do joelho até as proximidades da dobra superior da perna." },
  { id: "bracos-laser", name: "Braços Inteiros Laser", duration: "20 min • até 10 sessões", originalCents: 144000, category: "bracos", image: catalogImage("bracos-laser"), imageAlt: "Braços após laser", description: "Garanta braços lisos e sem pelos com a depilação a laser Pello Menos. Resultados eficazes e duradouros para sua pele. Agende agora!", badge: "Novo", highlight: true },
  { id: "antebraco-laser", name: "Antebraço Laser", duration: "15 min • até 10 sessões", originalCents: 108000, category: "bracos", image: catalogImage("antebraco-laser"), imageAlt: "Antebraço após laser", description: "Depilação a laser para antebraços: pele macia e livre de pelos por mais tempo. Conforto e eficácia no cuidado com você." },
  { id: "abdomen-laser", name: "Abdômen Laser", duration: "20 min • até 10 sessões", originalCents: 102000, category: "corpo", image: catalogImage("abdomen-laser"), imageAlt: "Abdômen após laser", description: "Na depilação a laser do abdômen feminino são eliminados os pelos da parede abdominal abaixo dos seios até a linha do baixo ventre.", badge: "Corpo" },
  { id: "costas-laser", name: "Costas Laser", duration: "25 min • até 10 sessões", originalCents: 149500, category: "corpo", image: catalogImage("costas-laser"), imageAlt: "Costas após laser", description: "Depilação a laser para costas: resultados eficazes e duradouros. Livre-se dos pelos com conforto e segurança. Agende sua sessão hoje!" },
  { id: "queixo-laser", name: "Queixo Laser", duration: "10 min • até 10 sessões", originalCents: 73300, category: "rosto", image: catalogImage("queixo-laser"), imageAlt: "Queixo após laser", description: "Acabe com os pelos indesejados no queixo com nossa depilação a laser. Pele macia e resultados de longa duração. Experimente!" },
  { id: "pescoco-laser", name: "Pescoço Laser", duration: "10 min • até 10 sessões", originalCents: 70300, category: "rosto", image: catalogImage("pescoco-laser"), imageAlt: "Pescoço após laser", description: "Depilação a laser para pescoço: toque suave e duradouro. Elimine os pelos com conforto e segurança. Agende sua sessão já!" },
  { id: "nariz-laser", name: "Nariz Laser", duration: "10 min • até 10 sessões", originalCents: 34000, category: "rosto", image: catalogImage("nariz-laser"), imageAlt: "Nariz após laser", description: "Depilação a laser para nariz: toque suave e eficaz. Remova os pelos de forma segura e duradoura. Agende sua sessão agora!" },
  { id: "orelhas-laser", name: "Orelhas Laser", duration: "10 min • até 10 sessões", originalCents: 43990, category: "rosto", image: catalogImage("orelhas-laser"), imageAlt: "Orelhas após laser", description: "Transforme suas orelhas com o Laser Pello Menos! Resultados incríveis, sem dor e com tecnologia avançada. Veja depoimentos e decida agora mesmo!" },
  { id: "rosto-inteiro-laser", name: "Rosto Inteiro Laser (BU+QU+NZ+PSD P)", duration: "20 min • até 10 sessões", originalCents: 144500, category: "rosto", image: catalogImage("rosto-inteiro-laser"), imageAlt: "Rosto inteiro após laser", description: "Na depilação a laser no rosto inteiro são eliminados os pelos na região do buço, queixo, nariz e PSD P (parte do corpo sem definição).", badge: "Combo", highlight: true },
  { id: "intergluteos-laser", name: "Interglúteos Laser", duration: "15 min • até 10 sessões", originalCents: 47000, category: "corpo", image: catalogImage("intergluteos-laser"), imageAlt: "Interglúteos após laser", description: "Na depilação a laser de interglúteos feminino são eliminados os pelos da lateral anal e cóccix." },
  { id: "meia-nadega-laser", name: "Meia Nádega Laser", duration: "15 min • até 10 sessões", originalCents: 70300, category: "corpo", image: catalogImage("meia-nadega-laser"), imageAlt: "Meia nádega após laser", description: "Na depilação meia nádega a laser são eliminados os pelos de forma opcional de uma faixa no sentido horizontal ou vertical de acordo com os pelos da cliente." },
  { id: "nadegas-laser", name: "Nádegas Laser", duration: "20 min • até 10 sessões", originalCents: 123090, category: "corpo", image: catalogImage("nadegas-laser"), imageAlt: "Nádegas após laser", description: "A depilação das nádegas completas a laser vai eliminar os pelos em toda a extensão das nádegas e da faixa acima do cóccix." },
  { id: "psd-p-laser", name: "PSD P Laser (até 10 cm)", duration: "10 min • até 10 sessões", originalCents: 43000, category: "corpo", image: catalogImage("psd-p-laser"), imageAlt: "Área sem definição P após laser", description: "Área sem definição pequena (até 10 cm) na depilação a laser. Resultados eficazes e duradouros para uma pele impecável." },
  { id: "psd-m-laser", name: "PSD M Laser (até 20 cm)", duration: "15 min • até 10 sessões", originalCents: 49500, category: "corpo", image: catalogImage("psd-m-laser"), imageAlt: "Área sem definição M após laser", description: "Área sem definição média (até 20 cm) na depilação a laser. Resultados rápidos e eficazes." },
  { id: "psd-g-laser", name: "PSD G Laser (a partir de 21 cm)", duration: "20 min • até 10 sessões", originalCents: 76900, category: "corpo", image: catalogImage("psd-g-laser"), imageAlt: "Área sem definição G após laser", description: "Na depilação a laser PSD G considera-se todas as regiões do corpo (a partir de 21 cm) que não possuem definição clara." },

  // Produto oficial, planos e presente
  { id: "body-splash", name: "Body Splash Pello Menos", duration: "Uso diário", originalCents: 6900, badge: "Oficial", category: "produtos", method: "produto", image: catalogImage("body-splash"), imageAlt: "Body Splash oficial Pello Menos" },
  {
    id: "cartao-presente",
    name: "Cartão Presente",
    duration: "Vale presente",
    originalCents: 20000,
    skipDiscount: true,
    badge: "Presente",
    highlight: true,
    category: "produtos",
    method: "presente",
    image: catalogImage("cartao-presente"),
    imageAlt: "Cartão Presente Pello Menos",
    description:
      "Cartão Presente Pello Menos para presentear com serviços de depilação. Informe a unidade onde o presente será usado.",
  },
  {
    id: "plano-silver",
    name: "Plano de Assinatura VIP – Silver",
    duration: "1ª parcela • mensal",
    originalCents: 10990,
    skipDiscount: true,
    badge: "Silver",
    highlight: true,
    category: "produtos",
    method: "plano",
    image: catalogImage("plano-silver"),
    imageAlt: "Plano de assinatura VIP Silver Cera Pello Menos",
    description:
      "Como assinante Vip Silver você depila 3 áreas a cera (axila + 1/2 perna + qualquer virilha) por um valor fixo mensal, com 10% em serviços extras. A compra no e-commerce é a primeira parcela: depois cadastre a recorrência na loja escolhida.",
  },
  {
    id: "plano-gold",
    name: "Plano de Assinatura VIP – Gold",
    duration: "1ª parcela • mensal",
    originalCents: 11490,
    skipDiscount: true,
    badge: "Gold",
    highlight: true,
    category: "produtos",
    method: "plano",
    image: catalogImage("plano-gold"),
    imageAlt: "Plano de assinatura VIP Gold Cera Pello Menos",
    description:
      "No Vip Gold você escolhe os serviços de cera da sessão mensal. Exceto sobrancelha; perna inteira conta como 2 serviços. A compra no e-commerce é a primeira parcela: depois cadastre a recorrência na loja escolhida.",
  },
  {
    id: "plano-clube-laser",
    name: "Clube do Laser",
    duration: "1ª parcela • mensal",
    originalCents: 24990,
    skipDiscount: true,
    badge: "Laser",
    highlight: true,
    category: "produtos",
    method: "plano",
    image: catalogImage("plano-clube-laser"),
    imageAlt: "Clube de Laser Pello Menos",
    description:
      "Assinatura mensal de laser por R$ 249,90, com fidelidade mínima de 5 meses. Até 8 áreas no mês, sem hora marcada. A compra no e-commerce é a primeira parcela: depois cadastre a recorrência do clube na loja escolhida.",
  },
  {
    id: "plano-prepago",
    name: "Pré-pago Pello Menos",
    duration: "Compra única • 3 sessões",
    originalCents: 34470,
    skipDiscount: true,
    badge: "Pré-pago",
    highlight: true,
    category: "produtos",
    method: "plano",
    image: catalogImage("plano-prepago"),
    imageAlt: "Plano Pré-pago Pello Menos",
    description:
      "Pacote pré-pago de cera em compra única: 3 sessões, com até 3 serviços por visita. Perna inteira conta como 2 serviços; sobrancelha não entra. Informe a unidade no pedido e use na loja escolhida.",
  },

  // Cera masculino — áreas da tabela RJ-SP para homem; preço cartão + 5% OFF no site
  { id: "peito-cera-masc", name: "Peito – Cera", duration: "20 min • Avulso", originalCents: 5990, category: "torax", image: catalogImage("peito-cera-masc", "masculino"), imageAlt: "Homem após cera no peito Pello Menos", method: "cera", audience: "masculino", badge: "Cera", highlight: true },
  { id: "abdomen-cera-masc", name: "Abdômen – Cera", duration: "15 min • Avulso", originalCents: 5990, category: "torax", image: catalogImage("abdomen-cera-masc", "masculino"), imageAlt: "Homem após cera no abdômen Pello Menos", method: "cera", audience: "masculino" },
  { id: "axila-cera-masc", name: "Axila – Cera", duration: "15 min • Avulso", originalCents: 3500, category: "axilas", image: catalogImage("axila-cera-masc", "masculino"), imageAlt: "Homem após cera nas axilas Pello Menos", method: "cera", audience: "masculino", badge: "Cera", highlight: true },
  { id: "antebraco-cera-masc", name: "Antebraço – Cera", duration: "15 min • Avulso", originalCents: 5190, category: "bracos", image: catalogImage("antebraco-cera-masc", "masculino"), imageAlt: "Homem após cera no antebraço Pello Menos", method: "cera", audience: "masculino" },
  { id: "bracos-cera-masc", name: "Braços – Cera", duration: "20 min • Avulso", originalCents: 7190, category: "bracos", image: catalogImage("bracos-cera-masc", "masculino"), imageAlt: "Homem após cera nos braços Pello Menos", method: "cera", audience: "masculino" },
  { id: "costas-cera-masc", name: "Costas – Cera", duration: "25 min • Avulso", originalCents: 5800, category: "corpo", image: catalogImage("costas-cera-masc", "masculino"), imageAlt: "Homem após cera nas costas Pello Menos", method: "cera", audience: "masculino", highlight: true },
  { id: "coxa-cera-masc", name: "Coxa – Cera", duration: "20 min • Avulso", originalCents: 5190, category: "pernas", image: catalogImage("coxa-cera-masc", "masculino"), imageAlt: "Homem após cera na coxa Pello Menos", method: "cera", audience: "masculino" },
  { id: "faixa-cera-masc", name: "Faixa – Cera", duration: "10 min • Avulso", originalCents: 2800, category: "corpo", image: catalogImage("faixa-cera-masc", "masculino"), imageAlt: "Homem após cera na faixa Pello Menos", method: "cera", audience: "masculino" },
  { id: "intergluteos-cera-masc", name: "Interglúteos – Cera", duration: "15 min • Avulso", originalCents: 3390, category: "corpo", image: catalogImage("intergluteos-cera-masc", "masculino"), imageAlt: "Homem após cera nos interglúteos Pello Menos", method: "cera", audience: "masculino" },
  { id: "nariz-cera-masc", name: "Nariz – Cera", duration: "10 min • Avulso", originalCents: 3000, category: "rosto", image: catalogImage("nariz-cera-masc", "masculino"), imageAlt: "Homem após cera no nariz Pello Menos", method: "cera", audience: "masculino" },
  { id: "nadegas-cera-masc", name: "Nádegas – Cera", duration: "20 min • Avulso", originalCents: 5190, category: "corpo", image: catalogImage("nadegas-cera-masc", "masculino"), imageAlt: "Homem após cera nas nádegas Pello Menos", method: "cera", audience: "masculino" },
  { id: "meia-nadega-cera-masc", name: "Meia nádega – Cera", duration: "15 min • Avulso", originalCents: 2600, category: "corpo", image: catalogImage("meia-nadega-cera-masc", "masculino"), imageAlt: "Homem após cera na meia nádega Pello Menos", method: "cera", audience: "masculino", badge: "Cera" },
  { id: "perna-cera-masc", name: "Perna Inteira – Cera", duration: "40 min • Avulso", originalCents: 8700, category: "pernas", image: catalogImage("perna-cera-masc", "masculino"), imageAlt: "Homem após cera na perna inteira Pello Menos", method: "cera", audience: "masculino", badge: "5% OFF", highlight: true },
  { id: "meia-perna-cera-masc", name: "Meia Perna – Cera", duration: "20 min • Avulso", originalCents: 5190, category: "pernas", image: catalogImage("meia-perna-cera-masc", "masculino"), imageAlt: "Homem após cera na meia perna Pello Menos", method: "cera", audience: "masculino" },
  { id: "queixo-cera-masc", name: "Queixo – Cera", duration: "10 min • Avulso", originalCents: 2800, category: "rosto", image: catalogImage("queixo-cera-masc", "masculino"), imageAlt: "Homem após cera no queixo Pello Menos", method: "cera", audience: "masculino", badge: "Cera" },
  { id: "virilha-comum-cera-masc", name: "Virilha comum – Cera", duration: "15 min • Avulso", originalCents: 3999, category: "virilha", image: catalogImage("virilha-comum-cera-masc", "masculino"), imageAlt: "Homem após cera na virilha comum Pello Menos", method: "cera", audience: "masculino", badge: "Cera" },
  { id: "virilha-cera-masc", name: "Virilha Total – Cera", duration: "25 min • Avulso", originalCents: 8890, category: "virilha", image: catalogImage("virilha-cera-masc", "masculino"), imageAlt: "Homem após cera na virilha total Pello Menos", method: "cera", audience: "masculino", highlight: true },

  // Esfoliação masculino — preço cartão da tabela oficial (sem meio braço, meia nádega, virilha+faixa e seios)
  { id: "esfoliacao-faixa-masc", name: "Esfoliação Faixa 01", duration: "10 min • Avulso", originalCents: 1850, category: "corpo", image: catalogImage("esfoliacao-faixa-masc", "masculino"), imageAlt: "Esfoliação de faixa masculina Pello Menos", method: "esfoliacao", audience: "masculino" },
  { id: "esfoliacao-faixa-02-masc", name: "Esfoliação Faixa 02", duration: "10 min • Avulso", originalCents: 3700, category: "corpo", image: catalogImage("esfoliacao-faixa-02-masc", "masculino"), imageAlt: "Esfoliação de faixa 02 masculina Pello Menos", method: "esfoliacao", audience: "masculino" },
  { id: "esfoliacao-braco-masc", name: "Esfoliação de braço", duration: "20 min • Avulso", originalCents: 3850, category: "bracos", image: catalogImage("esfoliacao-braco-masc", "masculino"), imageAlt: "Esfoliação de braço masculina Pello Menos", method: "esfoliacao", audience: "masculino" },
  { id: "esfoliacao-meia-perna-masc", name: "Esfoliação de meia perna", duration: "20 min • Avulso", originalCents: 3295, category: "pernas", image: catalogImage("esfoliacao-meia-perna-masc", "masculino"), imageAlt: "Esfoliação de meia perna masculina Pello Menos", method: "esfoliacao", audience: "masculino" },
  { id: "esfoliacao-abdomen-masc", name: "Esfoliação de abdômen", duration: "15 min • Avulso", originalCents: 3095, category: "torax", image: catalogImage("esfoliacao-abdomen-masc", "masculino"), imageAlt: "Esfoliação de abdômen masculina Pello Menos", method: "esfoliacao", audience: "masculino" },
  { id: "esfoliacao-axilas-masc", name: "Esfoliação de axilas", duration: "15 min • Avulso", originalCents: 2095, category: "axilas", image: catalogImage("esfoliacao-axilas-masc", "masculino"), imageAlt: "Esfoliação de axilas masculina Pello Menos", method: "esfoliacao", audience: "masculino", badge: "Pele" },
  { id: "esfoliacao-nadegas-masc", name: "Esfoliação de nádegas", duration: "15 min • Avulso", originalCents: 2795, category: "corpo", image: catalogImage("esfoliacao-nadegas-masc", "masculino"), imageAlt: "Esfoliação de nádegas masculina Pello Menos", method: "esfoliacao", audience: "masculino" },
  { id: "esfoliacao-coxa-masc", name: "Esfoliação de coxa", duration: "20 min • Avulso", originalCents: 3245, category: "pernas", image: catalogImage("esfoliacao-coxa-masc", "masculino"), imageAlt: "Esfoliação de coxa masculina Pello Menos", method: "esfoliacao", audience: "masculino" },
  { id: "esfoliacao-costas-masc", name: "Esfoliação de costas", duration: "20 min • Avulso", originalCents: 3145, category: "corpo", image: catalogImage("esfoliacao-costas-masc", "masculino"), imageAlt: "Esfoliação de costas masculina Pello Menos", method: "esfoliacao", audience: "masculino" },
  { id: "esfoliacao-perna-masc", name: "Esfoliação de perna inteira", duration: "25 min • Avulso", originalCents: 5945, category: "pernas", image: catalogImage("esfoliacao-perna-masc", "masculino"), imageAlt: "Esfoliação de perna inteira masculina Pello Menos", method: "esfoliacao", audience: "masculino", badge: "Pele", highlight: true },
  { id: "esfoliacao-virilha-masc", name: "Esfoliação de virilha", duration: "15 min • Avulso", originalCents: 3095, category: "virilha", image: catalogImage("esfoliacao-virilha-masc", "masculino"), imageAlt: "Esfoliação de virilha masculina Pello Menos", method: "esfoliacao", audience: "masculino" },

  // Laser masculino — preço de 10 sessões da tabela oficial (sem 50% de loja; 5% OFF só no e-commerce)
  { id: "axilas-laser-masc", name: "Axila Laser", duration: "15 min • até 10 sessões", originalCents: 98000, category: "axilas", image: catalogImage("axilas-laser-masc", "masculino"), imageAlt: "Homem em campanha de laser nas axilas Pello Menos", method: "laser", audience: "masculino", badge: "5% OFF", highlight: true },
  { id: "peito-laser-masc", name: "Tórax Laser", duration: "25 min • até 10 sessões", originalCents: 142000, category: "torax", image: catalogImage("peito-laser-masc", "masculino"), imageAlt: "Homem em campanha de laser no tórax Pello Menos", method: "laser", audience: "masculino", badge: "Masculino", highlight: true },
  { id: "abdomen-laser-masc", name: "Abdômen Laser", duration: "20 min • até 10 sessões", originalCents: 109000, category: "torax", image: catalogImage("abdomen-laser-masc", "masculino"), imageAlt: "Homem em campanha de laser no abdômen Pello Menos", method: "laser", audience: "masculino" },
  { id: "torax-abdomen-laser-masc", name: "Tórax + Abdômen Laser", duration: "40 min • até 10 sessões", originalCents: 236500, category: "torax", image: catalogImage("torax-abdomen-laser-masc", "masculino"), imageAlt: "Homem em campanha de laser no tórax e abdômen Pello Menos", method: "laser", audience: "masculino", badge: "Combo", highlight: true },
  { id: "mamilo-laser-masc", name: "Mamilo Laser", duration: "10 min • até 10 sessões", originalCents: 46000, category: "torax", image: catalogImage("mamilo-laser-masc", "masculino"), imageAlt: "Homem em campanha de laser no mamilo Pello Menos", method: "laser", audience: "masculino" },
  { id: "costas-laser-masc", name: "Costas Laser", duration: "30 min • até 10 sessões", originalCents: 158000, category: "corpo", image: catalogImage("costas-laser-masc", "masculino"), imageAlt: "Homem em campanha de laser nas costas Pello Menos", method: "laser", audience: "masculino", badge: "Masculino", highlight: true },
  { id: "bracos-laser-masc", name: "Braço Laser", duration: "20 min • até 10 sessões", originalCents: 146000, category: "bracos", image: catalogImage("bracos-laser-masc", "masculino"), imageAlt: "Homem em campanha de laser nos braços Pello Menos", method: "laser", audience: "masculino" },
  { id: "antebraco-laser-masc", name: "Antebraço Laser", duration: "15 min • até 10 sessões", originalCents: 115500, category: "bracos", image: catalogImage("antebraco-laser-masc", "masculino"), imageAlt: "Homem em campanha de laser no antebraço Pello Menos", method: "laser", audience: "masculino" },
  { id: "coxa-laser-masc", name: "Coxa Laser", duration: "25 min • até 10 sessões", originalCents: 228000, category: "pernas", image: catalogImage("coxa-laser-masc", "masculino"), imageAlt: "Homem em campanha de laser na coxa Pello Menos", method: "laser", audience: "masculino" },
  { id: "nadegas-laser-masc", name: "Nádegas Laser", duration: "20 min • até 10 sessões", originalCents: 131000, category: "corpo", image: catalogImage("nadegas-laser-masc", "masculino"), imageAlt: "Homem em campanha de laser nas nádegas Pello Menos", method: "laser", audience: "masculino" },
  { id: "meia-nadega-laser-masc", name: "Meia Nádega Laser", duration: "15 min • até 10 sessões", originalCents: 78000, category: "corpo", image: catalogImage("meia-nadega-laser-masc", "masculino"), imageAlt: "Homem em campanha de laser na meia nádega Pello Menos", method: "laser", audience: "masculino" },
  { id: "meia-perna-laser-masc", name: "Meia Perna Laser", duration: "20 min • até 10 sessões", originalCents: 211500, category: "pernas", image: catalogImage("meia-perna-laser-masc", "masculino"), imageAlt: "Homem em campanha de laser na meia perna Pello Menos", method: "laser", audience: "masculino" },
  { id: "perna-laser-masc", name: "Perna Inteira Laser", duration: "40 min • até 10 sessões", originalCents: 432000, category: "pernas", image: catalogImage("perna-laser-masc", "masculino"), imageAlt: "Homem em campanha de laser nas pernas Pello Menos", method: "laser", audience: "masculino", badge: "Verão" },
  { id: "pescoco-laser-masc", name: "Pescoço Laser", duration: "10 min • até 10 sessões", originalCents: 78000, category: "rosto", image: catalogImage("pescoco-laser-masc", "masculino"), imageAlt: "Homem em campanha de laser no pescoço Pello Menos", method: "laser", audience: "masculino" },
  { id: "intergluteos-laser-masc", name: "Interglúteos Laser", duration: "15 min • até 10 sessões", originalCents: 55000, category: "corpo", image: catalogImage("intergluteos-laser-masc", "masculino"), imageAlt: "Homem em campanha de laser nos interglúteos Pello Menos", method: "laser", audience: "masculino" },
  { id: "virilha-laser-masc", name: "Virilha Laser", duration: "20 min • até 10 sessões", originalCents: 139900, category: "virilha", image: catalogImage("virilha-laser-masc", "masculino"), imageAlt: "Homem em campanha de laser na virilha Pello Menos", method: "laser", audience: "masculino" },
  { id: "virilha-total-laser-masc", name: "Virilha Total Laser", duration: "25 min • até 10 sessões", originalCents: 217000, category: "virilha", image: catalogImage("virilha-total-laser-masc", "masculino"), imageAlt: "Homem em campanha de laser na virilha total Pello Menos", method: "laser", audience: "masculino", highlight: true },
  { id: "barba-laser-masc", name: "Barba Laser", duration: "15 min • até 10 sessões", originalCents: 107000, category: "rosto", image: catalogImage("barba-laser-masc", "masculino"), imageAlt: "Homem em campanha de laser na barba Pello Menos", method: "laser", audience: "masculino", badge: "Rosto", highlight: true },
  { id: "bigode-laser-masc", name: "Bigode Laser", duration: "10 min • até 10 sessões", originalCents: 50500, category: "rosto", image: catalogImage("bigode-laser-masc", "masculino"), imageAlt: "Homem em campanha de laser no bigode Pello Menos", method: "laser", audience: "masculino" },
  { id: "nariz-laser-masc", name: "Nariz Laser", duration: "10 min • até 10 sessões", originalCents: 41500, category: "rosto", image: catalogImage("nariz-laser-masc", "masculino"), imageAlt: "Homem em campanha de laser no nariz Pello Menos", method: "laser", audience: "masculino" },
  { id: "orelhas-laser-masc", name: "Orelhas Laser", duration: "10 min • até 10 sessões", originalCents: 52000, category: "rosto", image: catalogImage("orelhas-laser-masc", "masculino"), imageAlt: "Homem em campanha de laser nas orelhas Pello Menos", method: "laser", audience: "masculino" },
  { id: "queixo-laser-masc", name: "Queixo Laser", duration: "10 min • até 10 sessões", originalCents: 81000, category: "rosto", image: catalogImage("queixo-laser-masc", "masculino"), imageAlt: "Homem em campanha de laser no queixo Pello Menos", method: "laser", audience: "masculino" },
  { id: "rosto-inteiro-laser-masc", name: "Rosto Inteiro Laser (Barba + NZ + PSD P)", duration: "20 min • até 10 sessões", originalCents: 159500, category: "rosto", image: catalogImage("rosto-inteiro-laser-masc", "masculino"), imageAlt: "Homem em campanha de laser no rosto inteiro Pello Menos", method: "laser", audience: "masculino", badge: "Combo", highlight: true },
  { id: "psd-p-laser-masc", name: "PSD P Laser (até 10 cm)", duration: "10 min • até 10 sessões", originalCents: 50500, category: "corpo", image: catalogImage("psd-p-laser-masc", "masculino"), imageAlt: "Área sem definição P masculina após laser Pello Menos", method: "laser", audience: "masculino" },
  { id: "psd-m-laser-masc", name: "PSD M Laser (até 20 cm)", duration: "15 min • até 10 sessões", originalCents: 58000, category: "corpo", image: catalogImage("psd-m-laser-masc", "masculino"), imageAlt: "Área sem definição M masculina após laser Pello Menos", method: "laser", audience: "masculino" },
  { id: "psd-g-laser-masc", name: "PSD G Laser (a partir de 21 cm)", duration: "20 min • até 10 sessões", originalCents: 85000, category: "corpo", image: catalogImage("psd-g-laser-masc", "masculino"), imageAlt: "Área sem definição G masculina após laser Pello Menos", method: "laser", audience: "masculino" },
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
  if (method === "plano") {
    return `${item.name}. A compra no e-commerce é a primeira parcela: depois cadastre a recorrência na loja escolhida.`;
  }
  if (method === "presente") {
    return "Cartão Presente Pello Menos para presentear com serviços de depilação. Informe a unidade onde o presente será usado.";
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
  const {
    originalCents,
    method: explicitMethod,
    audience: explicitAudience,
    skipDiscount,
    description,
    ...rest
  } = item;
  const method = inferMethod(item.id, explicitMethod);
  const audience = explicitAudience ?? "feminino";
  const pricing = skipDiscount
    ? { priceCents: originalCents }
    : withEcommercePrice(originalCents);
  return {
    ...rest,
    ...pricing,
    duration: item.duration.replace(/^(\d+)/, "~$1"),
    method,
    audience,
    sku: catalogSku(index),
    code: catalogCode(item.id),
    description: description ?? defaultDescription(item, method, audience),
  };
});

export function getProductById(id: string) {
  return products.find((item) => item.id === id);
}

export function productsForAudience(audience: ProductAudience) {
  return products.filter(
    (item) => item.audience === audience || isSharedProduct(item),
  );
}

export function isServiceMethod(method: ProductMethod): method is ServiceMethod {
  return (
    method === "cera" ||
    method === "laser" ||
    method === "linha" ||
    method === "esfoliacao"
  );
}

export function productsByMethod(audience: ProductAudience, method: ServiceMethod) {
  return productsForAudience(audience).filter((item) => item.method === method);
}

export function productsByArea(audience: ProductAudience, category: AreaCategory) {
  return productsForAudience(audience).filter((item) => {
    if (!isServiceMethod(item.method)) return false;
    if (audience === "masculino" && category === "corpo") {
      return item.category === "corpo" || item.category === "virilha" || item.category === "bracos";
    }
    return item.category === category;
  });
}

export function retailProducts() {
  return products.filter((item) => item.method === "produto");
}

export function planProducts() {
  return products.filter((item) => item.method === "plano");
}

export function planProductsFor(audience: ProductAudience) {
  const items = planProducts();
  if (audience === "masculino") {
    return items.filter((item) => item.id !== "plano-clube-laser");
  }
  return items;
}

export const femaleAreaIds: AreaCategory[] = [
  "virilha",
  "pernas",
  "axilas",
  "rosto",
  "sobrancelha",
  "bracos",
  "corpo",
];

export const maleAreaIds: AreaCategory[] = [
  "torax",
  "axilas",
  "pernas",
  "rosto",
  "corpo",
];

export function areaIdsFor(audience: ProductAudience) {
  return audience === "masculino" ? maleAreaIds : femaleAreaIds;
}

const HOURS = "Seg a sáb, 9h às 20h";

function unit(
  code: string,
  name: string,
  city: string,
  state: StoreState,
  address: string,
  offersCera: boolean,
  offersLaser: boolean,
  offersCeraMasculino: boolean,
  offersLaserMasculino: boolean,
  priceRegion: PriceRegion = state === "DF" || state === "SP" ? "sp-df" : "rj-sp",
): StoreUnit {
  return {
    id: code.toLowerCase().replace(/\s+/g, "-"),
    code,
    name,
    city,
    state,
    address,
    hours: HOURS,
    offersCera,
    offersLaser,
    offersCeraMasculino,
    offersLaserMasculino,
    priceRegion: state === "DF" ? "sp-df" : priceRegion,
  };
}

export const storeUnits: StoreUnit[] = [
  // Cera feminino
  unit("APE", "Tijuca — Afonso Pena", "Rio de Janeiro", "RJ", "Rua Afonso Pena, Tijuca", true, false, false, false),
  unit("BON", "Bonsucesso", "Rio de Janeiro", "RJ", "Bonsucesso", true, false, false, false),
  unit("CAX", "Duque de Caxias", "Duque de Caxias", "RJ", "Duque de Caxias", true, false, false, false),
  unit("CGR2", "Campo Grande", "Rio de Janeiro", "RJ", "Campo Grande", true, false, false, false),
  unit("DF-ASU", "Asa Sul", "Brasília", "DF", "Asa Sul", true, false, false, false, "sp-df"),
  unit("DF-ANO", "Asa Norte", "Brasília", "DF", "Asa Norte", true, false, false, false, "sp-df"),
  unit("LEB2", "Leblon", "Rio de Janeiro", "RJ", "Leblon", true, false, false, false),
  unit("MAD", "Madureira", "Rio de Janeiro", "RJ", "Madureira", true, false, false, false),
  unit("MEI", "Méier", "Rio de Janeiro", "RJ", "Méier", true, false, false, false),
  unit("SNP", "Tijuca — Saens Peña", "Rio de Janeiro", "RJ", "Praça Saens Peña, Tijuca", true, false, false, false),
  unit("SJM", "São João de Meriti", "São João de Meriti", "RJ", "São João de Meriti", true, false, false, false),
  unit("SJO", "Centro — Rua São José", "Rio de Janeiro", "RJ", "Rua São José, Centro", true, false, false, false),
  unit("TON", "Copacabana I — Barata Ribeiro", "Rio de Janeiro", "RJ", "Av. Barata Ribeiro, Copacabana", true, false, false, false),
  unit("IPA", "Ipanema", "Rio de Janeiro", "RJ", "Ipanema", true, false, false, false),
  unit("NIG", "Nova Iguaçu I", "Nova Iguaçu", "RJ", "Rua Otávio Tarquino, Nova Iguaçu", true, false, false, false),
  unit("13M", "Centro — Treze de Maio", "Rio de Janeiro", "RJ", "Rua Treze de Maio, Centro", true, false, false, false),
  // Cera feminino e masculino (REC também tem laser feminino, sem laser masculino)
  unit("REC", "Recreio dos Bandeirantes", "Rio de Janeiro", "RJ", "Recreio dos Bandeirantes", true, true, true, false),
  unit("SP-AUG", "Rua Augusta", "São Paulo", "SP", "Rua Augusta", true, false, true, false, "sp-df"),
  unit("SP-AVP", "Avenida Paulista", "São Paulo", "SP", "Av. Paulista", true, false, true, false, "sp-df"),
  // Cera e laser feminino
  unit("CEN", "Centro — Gonçalves Dias", "Rio de Janeiro", "RJ", "Rua Gonçalves Dias, Centro", true, true, false, false),
  unit("SGO", "São Gonçalo — Partage", "São Gonçalo", "RJ", "Shopping Partage, São Gonçalo", true, true, false, false),
  unit("NIL", "Nilópolis", "Nilópolis", "RJ", "Nilópolis", true, true, false, false),
  unit("LMA", "Largo do Machado", "Rio de Janeiro", "RJ", "Largo do Machado", true, true, false, false),
  unit("SP-SJC", "São José dos Campos", "São José dos Campos", "SP", "São José dos Campos", true, true, false, false, "rj-sp"),
  unit("PET", "Petrópolis", "Petrópolis", "RJ", "Petrópolis", true, true, false, false),
  unit("IG02", "Ilha do Governador II", "Rio de Janeiro", "RJ", "Estrada do Galeão, Ilha do Governador", true, true, false, false),
  unit("HUT", "Humaitá", "Rio de Janeiro", "RJ", "Humaitá", true, true, false, false),
  // Cera e laser feminino e masculino
  unit("URG", "Tijuca — Uruguai", "Rio de Janeiro", "RJ", "Rua Uruguai, Tijuca", true, true, true, true),
  unit("BAN", "Bangu", "Rio de Janeiro", "RJ", "Bangu", true, true, true, true),
  unit("BOT", "Botafogo", "Rio de Janeiro", "RJ", "Botafogo", true, true, true, true),
  unit("COPA-2", "Copacabana II", "Rio de Janeiro", "RJ", "Av. Nossa Senhora de Copacabana", true, true, true, true),
  unit("EBA", "Estrada dos Bandeirantes", "Rio de Janeiro", "RJ", "Crystal Mall, Estrada dos Bandeirantes", true, true, true, true),
  unit("FLA", "Flamengo", "Rio de Janeiro", "RJ", "Flamengo", true, true, true, true),
  unit("FRE", "Jacarepaguá — Freguesia", "Rio de Janeiro", "RJ", "Largo da Freguesia, Jacarepaguá", true, true, true, true),
  unit("ICA", "Icaraí", "Niterói", "RJ", "Icaraí", true, true, true, true),
  unit("LBI", "Largo do Bicão", "Rio de Janeiro", "RJ", "Largo do Bicão", true, true, true, true),
  unit("NIG2", "Nova Iguaçu II", "Nova Iguaçu", "RJ", "Ao lado do TOP Shopping Nova Iguaçu", true, true, true, true),
];

export function getStoreUnitById(id: string) {
  return storeUnits.find((item) => item.id === id);
}

export function unitsForProduct(product: Pick<Product, "id" | "method" | "audience">) {
  const needsLaser = product.method === "laser" || product.id === "plano-clube-laser";
  const needsCera =
    product.method === "cera" ||
    product.method === "esfoliacao" ||
    product.method === "linha" ||
    (product.method === "plano" && product.id !== "plano-clube-laser");

  return storeUnits
    .filter((store) => {
      if (product.audience === "masculino") {
        if (needsLaser) return store.offersLaserMasculino;
        if (needsCera) return store.offersCeraMasculino;
        return store.offersCeraMasculino || store.offersLaserMasculino;
      }
      if (needsLaser) return store.offersLaser;
      if (needsCera) return store.offersCera;
      return true;
    })
    .sort(
      (a, b) =>
        a.state.localeCompare(b.state) ||
        a.name.localeCompare(b.name, "pt-BR"),
    );
}

const CROSS_SELL: Record<string, string[]> = {
  "virilha-cera": ["meia-nadega-cera", "coxa-cera", "axila-cera"],
  "virilha-laser": ["virilha-comum-laser", "meia-nadega-cera", "coxa-cera"],
  "virilha-comum-laser": ["virilha-laser", "virilha-cavada-laser"],
  "peito-laser-masc": ["abdomen-laser-masc", "torax-abdomen-laser-masc", "axilas-laser-masc"],
  "barba-laser-masc": ["bigode-laser-masc", "queixo-laser-masc", "rosto-inteiro-laser-masc"],
  "virilha-laser-masc": ["virilha-total-laser-masc", "intergluteos-laser-masc", "nadegas-laser-masc"],
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

const pernaCeraHero = formatHeroPrice(8590);
const axilasLaserHero = formatHeroPrice(89990);
const axilasLaserMascHero = formatHeroPrice(98000);
const virilhaLaserHero = formatHeroPrice(209000);
const bracosLaserHero = formatHeroPrice(144000);
const peitoHero = formatHeroPrice(142000);
const costasHero = formatHeroPrice(158000);
const barbaHero = formatHeroPrice(107000);

export const heroSlides: HeroSlide[] = [
  {
    id: "verao",
    badge: "Cera 5% OFF",
    title: "Pernas prontas pra viver",
    ...pernaCeraHero,
    cta: "Ver cera",
    ctaHref: "/servicos/cera",
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
    ctaHref: "/servicos/laser",
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
    ctaHref: "/servicos",
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
    ctaHref: "/servicos/laser",
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
    title: "Tórax liso, rotina leve",
    ...peitoHero,
    cta: "Ver laser",
    ctaHref: "/masculino/servicos/laser",
    image: M.heroPeito,
    imageMobile: M.heroPeitoM,
    imagePosition: "48% 28%",
    imagePositionMobile: "50% 26%",
    imageAlt: "Homem na campanha de laser no tórax Pello Menos",
    layout: "copy-top",
  },
  {
    id: "costas",
    badge: "Masculino",
    title: "Costas a laser",
    ...costasHero,
    cta: "Ver costas",
    ctaHref: "/masculino/servicos/laser",
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
    ...axilasLaserMascHero,
    cta: "Ver axilas",
    ctaHref: "/masculino/servicos",
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
    ctaHref: "/masculino/servicos/laser",
    image: M.heroBarba,
    imageMobile: M.heroBarbaM,
    imagePosition: "58% 28%",
    imagePositionMobile: "55% 22%",
    imageAlt: "Homem na campanha de laser na barba Pello Menos",
    layout: "copy-left",
  },
];

export const categories: Category[] = [
  { id: "virilha", label: "Virilha", image: catalogImage("virilha-cera"), href: areaHref("feminino", "virilha") },
  { id: "pernas", label: "Pernas", image: catalogImage("perna-cera"), href: areaHref("feminino", "pernas") },
  { id: "axilas", label: "Axilas", image: catalogImage("axila-cera"), href: areaHref("feminino", "axilas") },
  { id: "rosto", label: "Rosto", image: catalogImage("rosto-inteiro-laser"), href: areaHref("feminino", "rosto") },
  { id: "corpo", label: "Corpo", image: catalogImage("abdomen-cera"), href: areaHref("feminino", "corpo") },
];

export const categoriesMasculino: Category[] = [
  { id: "torax", label: "Tórax/abdômen", image: M.peito, href: areaHref("masculino", "torax") },
  { id: "axilas", label: "Axila", image: M.catAxilas, href: areaHref("masculino", "axilas") },
  { id: "pernas", label: "Perna", image: M.catPernas, href: areaHref("masculino", "pernas") },
  { id: "rosto", label: "Barba", image: M.barba, href: areaHref("masculino", "rosto") },
  { id: "corpo", label: "Corpo", image: M.catCorpo, href: areaHref("masculino", "corpo") },
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
    href: "/produto/cartao-presente",
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

export function navItems(audience: ProductAudience): NavItem[] {
  const planChildren: NavChild[] = [
    { label: "Silver - Cera", href: "/produto/plano-silver" },
    { label: "Gold - Cera", href: "/produto/plano-gold" },
  ];
  if (audience === "feminino") {
    planChildren.push({ label: "Clube de Laser", href: "/produto/plano-clube-laser" });
  }
  planChildren.push({ label: "Pré Pago", href: "/produto/plano-prepago" });

  return [
    {
      label: "Serviços",
      href: serviceHref(audience),
      children: serviceMethodsFor(audience).map((item) => ({
        label: item.label,
        href: serviceHref(audience, item.id),
      })),
    },
    {
      label: "Planos de Assinatura",
      href: planosHref(audience),
      children: planChildren,
    },
    { label: "Cartão Presente", href: "/produto/cartao-presente" },
    { label: "Produtos", href: retailHref(audience) },
  ];
}
