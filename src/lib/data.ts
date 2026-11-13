import {
  BLACK_NOV,
  applyCampaignCents,
  campaignPhaseAt,
  discountRateForLine,
  type CartLineLike,
} from "./black-nov-campaign";

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
  /** Preço de tabela (antes de 5% / campanha). */
  originalCents: number;
  priceCents: number;
  oldPriceCents?: number;
  skipDiscount?: boolean;
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
  /** Arte intermediária (md–lg), tipicamente 1536×960. */
  imageTablet?: string;
  imagePosition?: string;
  imagePositionMobile?: string;
  imageAlt: string;
  layout: HeroLayout;
  /** Texto/preço já estão na arte — não renderiza overlay HTML. */
  bakedText?: boolean;
  /** Só no mobile a arte traz texto — desktop continua com overlay HTML. */
  bakedTextMobile?: boolean;
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

/** Override global de cobrança (0 = preços reais de catálogo/bridge). */
export const TEST_CHARGE_CENTS = 0;

export function withEcommercePrice(originalCents: number) {
  return {
    oldPriceCents: originalCents,
    priceCents: Math.round(originalCents * (1 - ECOMMERCE_DISCOUNT)),
  };
}

export {
  BLACK_NOV,
  campaignPhaseAt,
  campaignDiscountLabel,
  discountRateForLine,
  applyCampaignCents,
  multiAreaHint,
  familyForProduct,
  type CampaignPhase,
  type CartLineLike,
} from "./black-nov-campaign";

/** Preço de vitrine: campanha Black (se ativa) ou 5% / skipDiscount. */
export function resolveCatalogPrice(
  args: {
    id: string;
    originalCents: number;
    method?: ProductMethod | null;
    skipDiscount?: boolean;
    audience?: ProductAudience | null;
  },
  cartLines?: CartLineLike[],
) {
  const lines =
    cartLines && cartLines.length
      ? cartLines
      : [{ id: args.id, method: args.method ?? null }];
  const rate = discountRateForLine(args.id, args.method, lines);
  if (rate != null) {
    return applyCampaignCents(args.originalCents, rate, {
      skipDiscount: args.skipDiscount,
      method: args.method,
      audience: args.audience,
    });
  }
  if (args.skipDiscount) {
    return {
      priceCents: args.originalCents,
      oldPriceCents: undefined as number | undefined,
      discountRate: null as number | null,
    };
  }
  return { ...withEcommercePrice(args.originalCents), discountRate: null as number | null };
}

export function chargeCents(cents: number) {
  return TEST_CHARGE_CENTS || cents;
}

export function formatBRL(cents: number) {
  return (cents / 100).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

/** Preço de banner na Esquenta (1 área): cera 15%, laser 60%. Fora da campanha, cai no 5%. */
export function formatHeroCampaignPrice(
  originalCents: number,
  method: "cera" | "laser" | "esfoliacao",
  opts?: { skipDiscount?: boolean; audience?: ProductAudience },
) {
  const phase = campaignPhaseAt();
  let rate: number | null = null;
  if (phase === "esquenta" || phase === "black_week") {
    if (method === "laser") {
      rate = BLACK_NOV.laser[phase].any;
    } else if (phase === "esquenta") {
      rate = BLACK_NOV.ceraEsf.esquenta.any;
    } else {
      rate = BLACK_NOV.ceraEsf.black_week_esfoliacao;
    }
  }
  const sale =
    rate != null
      ? chargeCents(
          applyCampaignCents(originalCents, rate, {
            skipDiscount: opts?.skipDiscount,
            method,
            audience: opts?.audience,
          }).priceCents,
        )
      : chargeCents(withEcommercePrice(originalCents).priceCents);
  const reais = Math.floor(sale / 100);
  const cc = sale % 100;
  return {
    priceReais: reais.toLocaleString("pt-BR"),
    priceCents: String(cc).padStart(2, "0"),
  };
}

/** @deprecated Use formatHeroCampaignPrice — mantido para scripts legados. */
export function formatHeroPrice(cents: number) {
  return formatHeroCampaignPrice(cents, "cera");
}

export function audienceFromPath(pathname: string): ProductAudience {
  if (pathname.startsWith("/masculino")) return "masculino";
  // Fichas usam /produto/:id (sem prefixo /masculino); ids masculinos terminam em -masc.
  const productMatch = pathname.match(/^\/produto\/([^/?#]+)/);
  if (productMatch) {
    const id = decodeURIComponent(productMatch[1]).replace(/\/$/, "");
    if (id.endsWith("-masc")) return "masculino";
  }
  return "feminino";
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

export function giftCardHref(audience: ProductAudience = "feminino") {
  return audience === "masculino" ? "/masculino/cartao-presente" : "/cartao-presente";
}

/** Shared SKUs that need a chrome twin (`*-masc`) so masculino keeps male header/footer. */
export const SHARED_CHROME_TWIN_IDS = [
  "body-splash-livre",
  "body-splash-marcante",
  "body-splash-autentica",
  "cartao-presente",
  "cartao-presente-160",
  "cartao-presente-215",
  "cartao-presente-290",
  "plano-silver",
  "plano-gold",
  "plano-prepago",
] as const;

/** Catalog bases for the three Body Splash fragrances (same photo, distinct SKUs). */
export const BODY_SPLASH_IDS = [
  "body-splash-livre",
  "body-splash-marcante",
  "body-splash-autentica",
] as const;

export function isBodySplashId(id: string) {
  const base = canonicalCatalogId(id);
  return (BODY_SPLASH_IDS as readonly string[]).includes(base);
}

/**
 * Body Splash: lançamento em 1º de dezembro (reunião 29/10). Até lá a vitrine
 * mostra o produto "em produção", sem botão de compra e fora do cross-sell.
 * Para liberar a venda: trocar para `true`, exportar e publicar.
 */
export const BODY_SPLASH_FOR_SALE = false;
export const BODY_SPLASH_LAUNCH_LABEL = "1º de dezembro";

/** Produto visível na vitrine mas ainda sem venda (hoje, só o Body Splash). */
export function isComingSoon(id: string) {
  return !BODY_SPLASH_FOR_SALE && isBodySplashId(id);
}

export type SharedChromeTwinId = (typeof SHARED_CHROME_TWIN_IDS)[number];

export function isSharedChromeTwinBase(id: string): id is SharedChromeTwinId {
  return (SHARED_CHROME_TWIN_IDS as readonly string[]).includes(id);
}

export function canonicalCatalogId(id: string) {
  return id.endsWith("-masc") ? id.slice(0, -5) : id;
}

export function productHref(audience: ProductAudience, id: string) {
  const base = canonicalCatalogId(id);
  if (audience === "masculino" && isSharedChromeTwinBase(base)) {
    return `/produto/${base}-masc`;
  }
  return `/produto/${base}`;
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
/** Total mínimo pós-desconto para liberar parcelamento (abaixo = só 1x, sem texto Nx). */
export const MIN_INSTALLMENT_ORDER_CENTS = 18000;
/** Teto do select CF7 `cerainstallments` na loja (cera / esfoliação / clareamento). */
export const CHECKOUT_CERA_MAX_TIMES = 3;
/** Teto do select CF7 `allinstallments` na loja (laser, linha, produto…). */
export const CHECKOUT_DEFAULT_MAX_TIMES = 10;

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

/**
 * Parcelas exibidas na ficha — alinhadas ao CF7 #1831 da loja.pellomenos.com.br:
 * total pós-desconto < R$ 180 → 1x (sem Nx); cera/esfoliação → até 3x; plano/presente → 1x;
 * demais → até 10x; piso R$ 50/parcela.
 */
export function getInstallment(
  priceCents: number,
  method: ProductMethod = "laser",
) {
  if (method === "plano" || method === "presente") {
    return { times: 1, installmentCents: priceCents };
  }
  if (priceCents < MIN_INSTALLMENT_ORDER_CENTS) {
    return { times: 1, installmentCents: priceCents };
  }
  const maxTimes =
    method === "cera" || method === "esfoliacao"
      ? CHECKOUT_CERA_MAX_TIMES
      : CHECKOUT_DEFAULT_MAX_TIMES;
  const byFloor = Math.max(1, Math.floor(priceCents / MIN_INSTALLMENT_CENTS));
  const times = Math.min(maxTimes, byFloor);
  const installmentCents = Math.ceil(priceCents / times);
  return { times, installmentCents };
}

export function installmentHint(method: ProductMethod) {
  if (method === "plano") {
    return "Planos são cobrados no valor cheio, sem parcelamento.";
  }
  if (method === "presente") {
    return "Vale só para cera. Valor cheio, sem parcelamento e sem o 5% OFF do e-commerce.";
  }
  if (method === "cera") {
    return "Em cera, parcele em até 3x. Parcela mínima de R$ 50.";
  }
  if (method === "esfoliacao") {
    return "Em esfoliação, parcele em até 3x. Parcela mínima de R$ 50.";
  }
  return "Parcele em até 10x, com parcela mínima de R$ 50.";
}

export function catalogImage(id: string, audience: ProductAudience = "feminino") {
  if (audience === "masculino") {
    return `/images/products/male/${id}.webp`;
  }
  return `/images/products/${id}.webp`;
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
  promoLaser: "/images/hero/male/promo-laser-v5.jpg",
  promoLaserM: "/images/hero/male/promo-laser-v5-m.jpg",
  promoCorpo: "/images/hero/male/promo-corpo.jpg",
  promoCorpoM: "/images/hero/male/promo-corpo-m.jpg",
  destaqueCera: "/images/hero/male/destaque-cera.jpg",
  destaqueLaser: "/images/hero/male/destaque-laser.jpg",
  destaqueEsfoliacao: "/images/hero/male/destaque-esfoliacao.jpg",
  destaqueSplash: "/images/hero/male/destaque-splash.jpg",
  // legados (outras telas podem referenciar)
  destaquePeito: "/images/hero/male/destaque-peito.jpg",
  destaqueVerao: "/images/hero/male/destaque-verao.jpg",
  destaqueBarba: "/images/hero/male/destaque-barba.jpg",
  catLaser: "/images/categories/male/cat-laser.jpg",
  catCera: "/images/categories/male/cat-cera.jpg",
  catEsfoliacao: "/images/categories/male/cat-esfoliacao.jpg",
  catAxilas: "/images/categories/male/cat-axilas.jpg",
  catCorpo: "/images/categories/male/cat-corpo.jpg",
  catRosto: "/images/categories/male/cat-rosto.jpg",
  catPernas: "/images/categories/male/cat-pernas.jpg",
  assinaturaCera: "/images/hero/male/assinatura-cera.jpg",
  peito: "/images/products/male/peito-cera-masc.webp",
  costas: "/images/products/male/costas-cera-masc.webp",
  barba: "/images/products/male/barba-laser-masc.webp",
  axilas: "/images/products/male/axila-cera-masc.webp",
  abdomen: "/images/products/male/abdomen-cera-masc.webp",
  bracos: "/images/products/male/bracos-cera-masc.webp",
  pernas: "/images/products/male/perna-cera-masc.webp",
  virilha: "/images/products/male/virilha-cera-masc.webp",
  pescoco: "/images/products/male/pescoco-laser-masc.webp",
  antebraco: "/images/products/male/antebraco-cera-masc.webp",
};

const catalogItems: ProductSeed[] = [
  // Cera / laser / linha feminino — nomes, preços Copacabana I e descrições do CSV da loja
  { id: "abdomen-cera", name: "Abdômen – Cera", duration: "15 min • Avulso", originalCents: 5800, category: "corpo", image: catalogImage("abdomen-cera"), imageAlt: "Abdômen feminino com a área central marcada", description: "A depilação a cera do abdômen feminino vai remover os pelos da parede abdominal abaixo dos seios até a linha do baixo ventre." },
  { id: "axila-cera", name: "Axila – Cera", duration: "15 min • Avulso", originalCents: 3300, category: "axilas", image: catalogImage("axila-cera"), imageAlt: "Axila feminina com a região axilar marcada", description: "Na depilação com cera nas axilas são eliminados os pelos de toda a região axilar.", badge: "Cera", highlight: true },
  { id: "antebraco-cera", name: "Antebraço – Cera", duration: "15 min • Avulso", originalCents: 4990, category: "bracos", image: catalogImage("antebraco-cera"), imageAlt: "Antebraços femininos com a região marcada", description: "A depilação a cera do antebraço feminino vai remover os pelos do antebraço, que pode ser tanto a parte superior ou inferior do membro." },
  { id: "bracos-cera", name: "Braços – Cera", duration: "20 min • Avulso", originalCents: 6990, category: "bracos", image: catalogImage("bracos-cera"), imageAlt: "Braços femininos com a região marcada", description: "Remova os pelos do braço e ao seu redor." },
  { id: "buco-cera", name: "Buço – Cera", duration: "10 min • Avulso", originalCents: 2690, category: "rosto", image: catalogImage("buco-cera"), imageAlt: "Buço feminino com a região marcada", description: "Retire os pelos da parte em cima da boca e da parte entre o queixo e a boca.", highlight: true },
  { id: "costas-cera", name: "Costas – Cera", duration: "25 min • Avulso", originalCents: 5500, category: "corpo", image: catalogImage("costas-cera"), imageAlt: "Costas femininas com a região marcada dos ombros à cintura", description: "A depilação com cera nas costas vai eliminar os pelos das imediações dos ombros até a linha da cintura." },
  { id: "coxa-cera", name: "Coxa – Cera", duration: "20 min • Avulso", originalCents: 4990, category: "pernas", image: catalogImage("coxa-cera"), imageAlt: "Coxas femininas com a região marcada", description: "A depilação com cera nas coxas vai remover os pelos da linha do joelho até as proximidades da dobra superior da perna." },
  { id: "faixa-cera", name: "Faixa – Cera", duration: "10 min • Avulso", originalCents: 2600, category: "corpo", image: catalogImage("faixa-cera"), imageAlt: "Faixa de cera no corpo", description: "É considerado faixa, pequenas regiões com pelos na extensão do corpo, como na região do umbigo, por exemplo." },
  { id: "intergluteos-cera", name: "Interglúteos – Cera", duration: "15 min • Avulso", originalCents: 3250, category: "corpo", image: catalogImage("intergluteos-cera"), imageAlt: "Região dos interglúteos marcada", description: "Remove os pelos da lateral anal e cóccix." },
  { id: "nariz-cera", name: "Nariz – Cera", duration: "10 min • Avulso", originalCents: 2890, category: "rosto", image: catalogImage("nariz-cera"), imageAlt: "Nariz feminino com a região marcada", description: "A depilação a cera no nariz feminino vai remover os pelos da entrada da cavidade nasal e uma faixa na parte de fora." },
  { id: "nadegas-cera", name: "Nádegas Completas – Cera", duration: "20 min • Avulso", originalCents: 4990, category: "corpo", image: catalogImage("nadegas-cera"), imageAlt: "Nádegas completas com a região marcada", description: "A depilação de nádegas completas com cera vai remover os pelos em toda a extensão das nádegas e da faixa acima do cóccix." },
  { id: "meia-nadega-cera", name: "Meia Nádega – Cera", duration: "15 min • Avulso", originalCents: 2499, category: "corpo", image: catalogImage("meia-nadega-cera"), imageAlt: "Meia nádega após cera", description: "Depilação a cera para meia nádega: resultado impecável e duradouro. Remova os pelos com conforto e facilidade. Agende sua sessão!", badge: "Cera" },
  { id: "perna-cera", name: "Perna Inteira – Cera", duration: "40 min • Avulso", originalCents: 8590, category: "pernas", image: catalogImage("perna-cera"), imageAlt: "Perna inteira feminina com a região marcada", description: "Remove os pelos da região, desde os pelos que ficam na área do calcanhar e pé (opcional) até a dobra superior da coxa.",     badge: "15% OFF", highlight: true },
  { id: "meia-perna-cera", name: "Meia Perna – Cera", duration: "20 min • Avulso", originalCents: 4990, category: "pernas", image: catalogImage("meia-perna-cera"), imageAlt: "Meia perna após cera", description: "A depilação com cera meia perna feminina vai remover os pelos da região do joelho até o calcanhar. A faixa do pé e os dedinhos do pé são cortesia: entram na mesma sessão, sem custo adicional." },
  { id: "queixo-cera", name: "Queixo – Cera", duration: "10 min • Avulso", originalCents: 2690, category: "rosto", image: catalogImage("queixo-cera"), imageAlt: "Queixo após cera", description: "A depilação a cera do queixo feminino vai remover os pelos do queixo e ao seu redor.", badge: "Cera" },
  { id: "seios-cera", name: "Seios – Cera", duration: "10 min • Avulso", originalCents: 2790, category: "corpo", image: catalogImage("seios-cera"), imageAlt: "Seios após cera", description: "Remove os pelos do centro e ao redor dos mamilos." },
  { id: "virilha-comum-cera", name: "Virilha Comum – Cera", duration: "15 min • Avulso", originalCents: 3850, category: "virilha", image: catalogImage("virilha-comum-cera"), imageAlt: "Virilha comum com o contorno marcado", description: "Remove os pelos no contorno da virilha, podendo se aproximar dos lábios, porém os lábios, ânus e cóccix não estão incluídos na depilação.", badge: "Cera" },
  { id: "virilha-comum-faixa-cera", name: "Virilha Comum + Faixa – Cera", duration: "20 min • Avulso", originalCents: 5150, category: "virilha", image: catalogImage("virilha-comum-faixa-cera"), imageAlt: "Virilha comum com faixa vertical marcada", description: "Remove os pelos no contorno da virilha, podendo se aproximar aos lábios. Essa depilação inclui faixa de contorno, porém os lábios, ânus e cóccix não estão inclusos." },
  { id: "virilha-cavada-cera", name: "Virilha Cavada – Cera", duration: "20 min • Avulso", originalCents: 7100, category: "virilha", image: catalogImage("virilha-cavada-cera"), imageAlt: "Virilha cavada após cera", description: "Remove os pelos da virilha, lábios internos e externos, porém deixa uma pequena faixa de pelo no púbis. Essa depilação inclui ânus e cóccix." },
  { id: "virilha-cavada-faixa-cera", name: "Virilha Cavada + Faixa – Cera", duration: "25 min • Avulso", originalCents: 8400, category: "virilha", image: catalogImage("virilha-cavada-faixa-cera"), imageAlt: "Virilha cavada com faixa após cera", description: "Remove os pelos da virilha, lábios internos e externos, porém deixa uma pequena faixa de pelo no púbis. Essa depilação inclui ânus, cóccix e a faixa de contorno." },
  { id: "virilha-modelada-cera", name: "Virilha Modelada – Cera", duration: "25 min • Avulso", originalCents: 8390, category: "virilha", image: catalogImage("virilha-modelada-cera"), imageAlt: "Virilha modelada após cera", description: "A depilação a cera da virilha feminina modelada vai remover os pelos dos lábios internos e externos e os pelos envoltos do molde escolhido pela cliente no púbis. Não inclui ânus e cóccix." },
  { id: "virilha-cera", name: "Virilha Total – Cera", duration: "25 min • Avulso", originalCents: 8500, category: "virilha", image: catalogImage("virilha-cera"), imageAlt: "Virilha total após cera", description: "Remove por completo todos os pelos da virilha, lábios externos e internos, incluindo ânus, cóccix e faixa do baixo ventre.", highlight: true },
  { id: "labios-genitais-cera", name: "Lábios Genitais – Cera", duration: "15 min • Avulso", originalCents: 3850, category: "virilha", image: catalogImage("labios-genitais-cera"), imageAlt: "Cera nos lábios genitais", description: "A depilação dos grandes lábios genitais a cera vai retirar os pelos dos lábios internos e externos." },
  { id: "sobrancelha-cera", name: "Sobrancelha – Cera", duration: "15 min • Avulso", originalCents: 4799, category: "sobrancelha", image: catalogImage("sobrancelha-cera"), imageAlt: "Sobrancelha com cera", description: "A depilação de sobrancelha com cera remove os pelos de acordo com o desenho já existente, fazendo apenas a limpeza da região. Acabamento final com lápis finalizador, explicando a cliente que ao lavar o rosto o mesmo sairá." },
  { id: "sobrancelha-realce-cera", name: "Sobrancelha + Realce – Cera", duration: "25 min • Avulso", originalCents: 7590, category: "sobrancelha", image: catalogImage("sobrancelha-realce-cera"), imageAlt: "Sobrancelha com realce", description: "Remove os pelos de acordo com o desenho já existente, fazendo apenas a limpeza com cera ou pinça. O Realce é uma coloração temporária feita na sobrancelha, de preferência nos pelos claros ou brancos, para valorizar o olhar." },
  { id: "sobrancelha-henna-simples", name: "Sobrancelha Simples + Henna", duration: "25 min • Avulso", originalCents: 8390, category: "sobrancelha", image: catalogImage("sobrancelha-henna-simples"), imageAlt: "Sobrancelha simples com henna", description: "Transforme suas sobrancelhas com a henna e cera da Pello Menos. Definição precisa e resultados duradouros para um olhar marcante." },
  { id: "design-sobrancelha", name: "Design de Sobrancelha – Cera", duration: "20 min • Avulso", originalCents: 5850, category: "sobrancelha", image: catalogImage("design-sobrancelha"), imageAlt: "Design de sobrancelha", description: "A técnica de design de sobrancelha com cera consiste em ressaltar a beleza dos olhos e do rosto, dando-lhes o equilíbrio e a simetria adequada. As sobrancelhas serão remodeladas de forma a valorizar o olhar e embelezar o rosto.", badge: "Olhar", highlight: true },
  { id: "design-sobrancelha-realce", name: "Design de Sobrancelha + Realce – Cera", duration: "30 min • Avulso", originalCents: 7850, category: "sobrancelha", image: catalogImage("design-sobrancelha-realce"), imageAlt: "Design de sobrancelha com realce", description: "O Design remodela as sobrancelhas com cera para valorizar o olhar. O Realce colore temporariamente os pelos brancos das sobrancelhas." },
  { id: "sobrancelha-henna", name: "Design de Sobrancelha + Henna Feminino", duration: "30 min • Avulso", originalCents: 8650, category: "sobrancelha", image: catalogImage("sobrancelha-henna"), imageAlt: "Design de sobrancelha com henna", description: "Realce suas sobrancelhas com henna e cera. Definição impecável, longa duração e visual natural. Agende sua sessão agora!", badge: "Combo" },
  { id: "realce", name: "Realce", duration: "15 min • Avulso", originalCents: 3200, category: "sobrancelha", image: catalogImage("realce"), imageAlt: "Realce de sobrancelha com tintura", description: "Aplicação de tintura específica para pelos da sobrancelha. O produto não entra em contato com a pele. Indicado para disfarçar fios brancos ou clarear tons apagados, sem alterar o desenho natural da sobrancelha.", method: "cera" },
  { id: "henna", name: "Henna", duration: "20 min • Avulso", originalCents: 4100, category: "sobrancelha", image: catalogImage("henna"), imageAlt: "Henna nas sobrancelhas", description: "Realce suas sobrancelhas com nossa henna especial. Definição perfeita, longa duração e resultados naturais. Adquira já e transforme seu olhar!", method: "cera" },
  // Preço provisório (= Realce R$ 32): produto sumiu do Woo; confirmar tabela com Pello antes do GO loja.
  { id: "tintura-pelos-pubianos", name: "Tintura de Pelos Pubianos", duration: "15 min • Avulso", originalCents: 3200, category: "virilha", image: catalogImage("labios-genitais-cera"), imageAlt: "Tintura de pelos pubianos", description: "Coloração temporária dos pelos pubianos. Sessão avulsa. Informe a unidade no pedido.", method: "cera", badge: "Cera" },

  // Linha feminino
  { id: "buco-linha", name: "Buço – Linha", duration: "10 min • Avulso", originalCents: 2092, category: "rosto", image: catalogImage("buco-linha"), imageAlt: "Buço após linha", description: "Elimine os pelos indesejados do buço com nossa depilação a linha. Resultados suaves e duradouros para uma pele impecável. Agende agora!", method: "linha", badge: "Linha" },
  { id: "queixo-linha", name: "Queixo – Linha", duration: "10 min • Avulso", originalCents: 2790, category: "rosto", image: catalogImage("queixo-linha"), imageAlt: "Queixo após linha", description: "Depilação a linha para o queixo: resultados suaves e duradouros. Remova os pelos com conforto e precisão. Agende sua sessão na Pello Menos!", method: "linha", badge: "Linha" },
  { id: "faixa-linha", name: "Faixa – Linha", duration: "10 min • Avulso", originalCents: 2550, category: "rosto", image: catalogImage("faixa-linha"), imageAlt: "Faixa após linha", description: "Depilação a linha para faixa: remoção precisa e eficaz dos pelos. Resultados suaves e duradouros para uma pele impecável. Agende sua sessão!", method: "linha", badge: "Linha" },

  // Esfoliação feminino — preço cartão da tabela oficial
  { id: "esfoliacao-faixa", name: "Esfoliação Faixa 01", duration: "10 min • Avulso", originalCents: 1300, category: "corpo", image: catalogImage("esfoliacao-faixa"), imageAlt: "Esfoliação de faixa", method: "esfoliacao" },
  { id: "esfoliacao-meio-braco", name: "Esfoliação de meio braço", duration: "15 min • Avulso", originalCents: 2495, category: "bracos", image: catalogImage("esfoliacao-meio-braco"), imageAlt: "Esfoliação de meio braço", method: "esfoliacao" },
  { id: "esfoliacao-braco", name: "Esfoliação de braço", duration: "20 min • Avulso", originalCents: 3495, category: "bracos", image: catalogImage("esfoliacao-braco"), imageAlt: "Esfoliação de braço", method: "esfoliacao" },
  { id: "esfoliacao-meia-perna", name: "Esfoliação de meia perna", duration: "20 min • Avulso", originalCents: 2495, category: "pernas", image: catalogImage("esfoliacao-meia-perna"), imageAlt: "Esfoliação de meia perna", method: "esfoliacao" },
  { id: "esfoliacao-abdomen", name: "Esfoliação de abdômen", duration: "15 min • Avulso", originalCents: 2900, category: "corpo", image: catalogImage("esfoliacao-abdomen"), imageAlt: "Esfoliação de abdômen", method: "esfoliacao" },
  { id: "esfoliacao-axilas", name: "Esfoliação de axilas", duration: "15 min • Avulso", originalCents: 1650, category: "axilas", image: catalogImage("esfoliacao-axilas"), imageAlt: "Esfoliação de axilas", method: "esfoliacao", badge: "Pele" },
  { id: "esfoliacao-nadegas", name: "Esfoliação de nádegas", duration: "15 min • Avulso", originalCents: 2495, category: "corpo", image: catalogImage("esfoliacao-nadegas"), imageAlt: "Esfoliação de nádegas", method: "esfoliacao" },
  { id: "esfoliacao-meia-nadega", name: "Esfoliação de meia nádega", duration: "10 min • Avulso", originalCents: 1250, category: "corpo", image: catalogImage("esfoliacao-meia-nadega"), imageAlt: "Esfoliação de meia nádega", method: "esfoliacao" },
  { id: "esfoliacao-coxa", name: "Esfoliação de coxa", duration: "20 min • Avulso", originalCents: 2495, category: "pernas", image: catalogImage("esfoliacao-coxa"), imageAlt: "Esfoliação de coxa", method: "esfoliacao" },
  { id: "esfoliacao-costas", name: "Esfoliação de costas", duration: "20 min • Avulso", originalCents: 2750, category: "corpo", image: catalogImage("esfoliacao-costas"), imageAlt: "Esfoliação de costas", method: "esfoliacao" },
  { id: "esfoliacao-perna", name: "Esfoliação de perna inteira", duration: "25 min • Avulso", originalCents: 4295, category: "pernas", image: catalogImage("esfoliacao-perna"), imageAlt: "Esfoliação de perna inteira", method: "esfoliacao", badge: "Pele", highlight: true },
  { id: "esfoliacao-virilha", name: "Esfoliação de virilha", duration: "15 min • Avulso", originalCents: 1925, category: "virilha", image: catalogImage("esfoliacao-virilha"), imageAlt: "Esfoliação de virilha", method: "esfoliacao" },
  { id: "esfoliacao-virilha-faixa", name: "Esfoliação de virilha + faixa", duration: "20 min • Avulso", originalCents: 2575, category: "virilha", image: catalogImage("esfoliacao-virilha-faixa"), imageAlt: "Esfoliação de virilha com faixa", method: "esfoliacao" },
  { id: "esfoliacao-seios", name: "Esfoliação de seios", duration: "10 min • Avulso", originalCents: 1395, category: "corpo", image: catalogImage("esfoliacao-seios"), imageAlt: "Esfoliação de seios", method: "esfoliacao" },

  // Laser feminino
  { id: "axilas-laser", name: "Axilas Laser", duration: "15 min • até 10 sessões", originalCents: 89990, category: "axilas", image: catalogImage("axilas-laser"), imageAlt: "Axilas após laser", description: "Descubra a revolucionária depilação a laser para axilas. Resultados eficazes e duradouros. Conquiste axilas suaves e sem pelos. Adquira agora!", badge: "60% OFF", highlight: true },
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

  // Produto oficial (3 fragrâncias), planos e presente — mesma foto do Body Splash
  // Artes oficiais do Drive (pasta BODY SPLASHS); mesma URL fem/masc (chrome twin reutiliza `image`).
  { id: "body-splash-livre", name: "Body Splash - Livre", duration: "Uso diário", originalCents: 8590, badge: "Oficial", category: "produtos", method: "produto", image: catalogImage("body-splash-livre"), imageAlt: "Body Splash - Livre Pello Menos" },
  { id: "body-splash-marcante", name: "Body Splash - Marcante", duration: "Uso diário", originalCents: 8590, badge: "Oficial", category: "produtos", method: "produto", image: catalogImage("body-splash-marcante"), imageAlt: "Body Splash - Marcante Pello Menos" },
  { id: "body-splash-autentica", name: "Body Splash - Autêntica", duration: "Uso diário", originalCents: 8590, badge: "Oficial", category: "produtos", method: "produto", image: catalogImage("body-splash-autentica"), imageAlt: "Body Splash - Autêntica Pello Menos" },
  {
    id: "cartao-presente",
    name: "Gift Card R$ 79,99",
    duration: "Vale presente",
    originalCents: 7999,
    skipDiscount: true,
    badge: "Presente",
    highlight: true,
    category: "produtos",
    method: "presente",
    image: catalogImage("cartao-presente"),
    imageAlt: "Cartão presente Pello Menos de R$ 79,99 sobre a mesa",
    description:
      "Gift Card R$ 79,99. Vale presente só para depilação a cera. Não vale para laser, linha, esfoliação nem planos. Informe a unidade onde o presente será usado.",
  },
  {
    id: "cartao-presente-160",
    name: "Gift Card R$ 160,00",
    duration: "Vale presente",
    originalCents: 16000,
    skipDiscount: true,
    badge: "Presente",
    highlight: true,
    category: "produtos",
    method: "presente",
    image: catalogImage("cartao-presente-160"),
    imageAlt: "Cartão presente Pello Menos de R$ 160 sobre a mesa",
    description:
      "Gift Card R$ 160,00. Vale presente só para depilação a cera. Não vale para laser, linha, esfoliação nem planos. Informe a unidade onde o presente será usado.",
  },
  {
    id: "cartao-presente-215",
    name: "Gift Card R$ 215,00",
    duration: "Vale presente",
    originalCents: 21500,
    skipDiscount: true,
    badge: "Presente",
    highlight: true,
    category: "produtos",
    method: "presente",
    image: catalogImage("cartao-presente-215"),
    imageAlt: "Cartão presente Pello Menos de R$ 215 sobre a mesa",
    description:
      "Gift Card R$ 215,00. Vale presente só para depilação a cera. Não vale para laser, linha, esfoliação nem planos. Informe a unidade onde o presente será usado.",
  },
  {
    id: "cartao-presente-290",
    name: "Gift Card R$ 290,00",
    duration: "Vale presente",
    originalCents: 29000,
    skipDiscount: true,
    badge: "Presente",
    highlight: true,
    category: "produtos",
    method: "presente",
    image: catalogImage("cartao-presente-290"),
    imageAlt: "Cartão presente Pello Menos de R$ 290 sobre a mesa",
    description:
      "Gift Card R$ 290,00. Vale presente só para depilação a cera. Não vale para laser, linha, esfoliação nem planos. Informe a unidade onde o presente será usado.",
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

  // Cera masculino — tabela Rafael e-commerce (já com desconto; skipDiscount)
  { id: "peito-cera-masc", name: "Peito – Cera", duration: "20 min • Avulso", originalCents: 4990, skipDiscount: true, category: "torax", image: catalogImage("peito-cera-masc", "masculino"), imageAlt: "Homem após cera no peito Pello Menos", method: "cera", audience: "masculino", badge: "Cera", highlight: true },
  { id: "abdomen-cera-masc", name: "Abdômen – Cera", duration: "15 min • Avulso", originalCents: 5790, skipDiscount: true, category: "torax", image: catalogImage("abdomen-cera-masc", "masculino"), imageAlt: "Homem após cera no abdômen Pello Menos", method: "cera", audience: "masculino" },
  { id: "axila-cera-masc", name: "Axila – Cera", duration: "15 min • Avulso", originalCents: 3890, skipDiscount: true, category: "axilas", image: catalogImage("axila-cera-masc", "masculino"), imageAlt: "Homem após cera nas axilas Pello Menos", method: "cera", audience: "masculino", badge: "Cera", highlight: true },
  { id: "antebraco-cera-masc", name: "Antebraço – Cera", duration: "15 min • Avulso", originalCents: 3850, skipDiscount: true, category: "bracos", image: catalogImage("antebraco-cera-masc", "masculino"), imageAlt: "Homem após cera no antebraço Pello Menos", method: "cera", audience: "masculino" },
  { id: "bracos-cera-masc", name: "Braços – Cera", duration: "20 min • Avulso", originalCents: 7400, skipDiscount: true, category: "bracos", image: catalogImage("bracos-cera-masc", "masculino"), imageAlt: "Homem após cera nos braços Pello Menos", method: "cera", audience: "masculino" },
  { id: "costas-cera-masc", name: "Costas – Cera", duration: "25 min • Avulso", originalCents: 5990, skipDiscount: true, category: "corpo", image: catalogImage("costas-cera-masc", "masculino"), imageAlt: "Homem após cera nas costas Pello Menos", method: "cera", audience: "masculino", highlight: true },
  { id: "coxa-cera-masc", name: "Coxa – Cera", duration: "20 min • Avulso", originalCents: 6190, skipDiscount: true, category: "pernas", image: catalogImage("coxa-cera-masc", "masculino"), imageAlt: "Homem após cera na coxa Pello Menos", method: "cera", audience: "masculino" },
  { id: "faixa-cera-masc", name: "Faixa – Cera", duration: "10 min • Avulso", originalCents: 3400, skipDiscount: true, category: "corpo", image: catalogImage("faixa-cera-masc", "masculino"), imageAlt: "Homem após cera na faixa Pello Menos", method: "cera", audience: "masculino" },
  { id: "intergluteos-cera-masc", name: "Interglúteos – Cera", duration: "15 min • Avulso", originalCents: 4850, skipDiscount: true, category: "corpo", image: catalogImage("intergluteos-cera-masc", "masculino"), imageAlt: "Homem após cera nos interglúteos Pello Menos", method: "cera", audience: "masculino" },
  { id: "nariz-cera-masc", name: "Nariz – Cera", duration: "10 min • Avulso", originalCents: 3290, skipDiscount: true, category: "rosto", image: catalogImage("nariz-cera-masc", "masculino"), imageAlt: "Homem após cera no nariz Pello Menos", method: "cera", audience: "masculino" },
  { id: "nadegas-cera-masc", name: "Nádegas – Cera", duration: "20 min • Avulso", originalCents: 5250, skipDiscount: true, category: "corpo", image: catalogImage("nadegas-cera-masc", "masculino"), imageAlt: "Homem após cera nas nádegas Pello Menos", method: "cera", audience: "masculino" },
  { id: "meia-nadega-cera-masc", name: "Meia nádega – Cera", duration: "15 min • Avulso", originalCents: 2795, skipDiscount: true, category: "corpo", image: catalogImage("meia-nadega-cera-masc", "masculino"), imageAlt: "Homem após cera na meia nádega Pello Menos", method: "cera", audience: "masculino", badge: "Cera" },
  { id: "perna-cera-masc", name: "Perna Inteira – Cera", duration: "40 min • Avulso", originalCents: 11500, skipDiscount: true, category: "pernas", image: catalogImage("perna-cera-masc", "masculino"), imageAlt: "Homem após cera na perna inteira Pello Menos", method: "cera", audience: "masculino", badge: "15% OFF", highlight: true },
  { id: "meia-perna-cera-masc", name: "Meia Perna – Cera", duration: "20 min • Avulso", originalCents: 6190, skipDiscount: true, category: "pernas", image: catalogImage("meia-perna-cera-masc", "masculino"), imageAlt: "Homem após cera na meia perna Pello Menos", method: "cera", audience: "masculino" },
  { id: "queixo-cera-masc", name: "Queixo – Cera", duration: "10 min • Avulso", originalCents: 3290, skipDiscount: true, category: "rosto", image: catalogImage("queixo-cera-masc", "masculino"), imageAlt: "Homem após cera no queixo Pello Menos", method: "cera", audience: "masculino", badge: "Cera" },
  { id: "virilha-comum-cera-masc", name: "Virilha comum – Cera", duration: "15 min • Avulso", originalCents: 5890, skipDiscount: true, category: "virilha", image: catalogImage("virilha-comum-cera-masc", "masculino"), imageAlt: "Homem após cera na virilha comum Pello Menos", method: "cera", audience: "masculino", badge: "Cera" },
  { id: "virilha-cera-masc", name: "Virilha Total – Cera", duration: "25 min • Avulso", originalCents: 8890, skipDiscount: true, category: "virilha", image: catalogImage("virilha-cera-masc", "masculino"), imageAlt: "Homem após cera na virilha total Pello Menos", method: "cera", audience: "masculino", highlight: true },


  // Cera masculino — áreas novas (tabela Rafael; skipDiscount; Woo próprio no oficialteste)
  { id: "barba-cera-masc", name: "Barba – Cera", duration: "20 min • Avulso", originalCents: 5690, skipDiscount: true, category: "rosto", image: catalogImage("barba-cera-masc", "masculino"), imageAlt: "Barba – Cera Pello Menos", description: "Depilação a cera da barba masculina: remove os pelos da região da barba pela raiz.", method: "cera", audience: "masculino", badge: "Cera", highlight: true },
  { id: "barba-modeladora-cera-masc", name: "Barba Modeladora – Cera", duration: "25 min • Avulso", originalCents: 7490, skipDiscount: true, category: "rosto", image: catalogImage("barba-modeladora-cera-masc", "masculino"), imageAlt: "Barba Modeladora – Cera Pello Menos", description: "Modelagem da barba com cera: desenho e limpeza das linhas para valorizar o contorno.", method: "cera", audience: "masculino" },
  { id: "bigode-cera-masc", name: "Bigode – Cera", duration: "10 min • Avulso", originalCents: 3850, skipDiscount: true, category: "rosto", image: catalogImage("bigode-cera-masc", "masculino"), imageAlt: "Bigode – Cera Pello Menos", description: "Depilação a cera do bigode masculino: remove os pelos da região do bigode.", method: "cera", audience: "masculino" },
  { id: "orelha-cera-masc", name: "Orelha – Cera", duration: "10 min • Avulso", originalCents: 3290, skipDiscount: true, category: "rosto", image: catalogImage("orelha-cera-masc", "masculino"), imageAlt: "Orelha – Cera Pello Menos", description: "Depilação a cera das orelhas masculinas: remove os pelos da orelha e entrada do canal.", method: "cera", audience: "masculino" },
  { id: "pescoco-cera-masc", name: "Pescoço – Cera", duration: "10 min • Avulso", originalCents: 3290, skipDiscount: true, category: "rosto", image: catalogImage("pescoco-cera-masc", "masculino"), imageAlt: "Pescoço – Cera Pello Menos", description: "Depilação a cera do pescoço masculino: remove os pelos da região do pescoço.", method: "cera", audience: "masculino" },
  { id: "mamilos-cera-masc", name: "Mamilos – Cera", duration: "10 min • Avulso", originalCents: 3290, skipDiscount: true, category: "torax", image: catalogImage("mamilos-cera-masc", "masculino"), imageAlt: "Mamilos – Cera Pello Menos", description: "Depilação a cera dos mamilos masculinos: remove os pelos ao redor dos mamilos.", method: "cera", audience: "masculino" },
  { id: "sobrancelha-cera-masc", name: "Sobrancelha – Cera", duration: "15 min • Avulso", originalCents: 5290, skipDiscount: true, category: "sobrancelha", image: catalogImage("sobrancelha-cera-masc", "masculino"), imageAlt: "Sobrancelha – Cera Pello Menos", description: "Depilação de sobrancelha masculina com cera: limpeza conforme o desenho já existente.", method: "cera", audience: "masculino", badge: "Cera" },
  { id: "design-sobrancelha-masc", name: "Design de Sobrancelha – Cera", duration: "20 min • Avulso", originalCents: 6990, skipDiscount: true, category: "sobrancelha", image: catalogImage("design-sobrancelha-masc", "masculino"), imageAlt: "Design de Sobrancelha – Cera Pello Menos", description: "Design de sobrancelha masculino com cera: remodela o desenho para valorizar o olhar.", method: "cera", audience: "masculino", badge: "Cera", highlight: true },
  { id: "torax-abdomen-cera-masc", name: "Tórax + Abdômen – Cera", duration: "35 min • Avulso", originalCents: 8990, skipDiscount: true, category: "torax", image: catalogImage("torax-abdomen-cera-masc", "masculino"), imageAlt: "Tórax + Abdômen – Cera Pello Menos", description: "Combo peito e abdômen a cera: remove os pelos do tórax e da parede abdominal.", method: "cera", audience: "masculino", badge: "Cera", highlight: true },
  { id: "saco-escrotal-cera-masc", name: "Saco Escrotal – Cera", duration: "15 min • Avulso", originalCents: 5890, skipDiscount: true, category: "virilha", image: catalogImage("saco-escrotal-cera-masc", "masculino"), imageAlt: "Saco Escrotal – Cera Pello Menos", description: "Depilação a cera do saco escrotal: remove os pelos da região do saco.", method: "cera", audience: "masculino", badge: "Cera" },
  // Esfoliação masculino — tabela Rafael e-commerce (já com desconto; skipDiscount)
  { id: "esfoliacao-faixa-masc", name: "Esfoliação Faixa 01", duration: "10 min • Avulso", originalCents: 1700, skipDiscount: true, category: "corpo", image: catalogImage("esfoliacao-faixa-masc", "masculino"), imageAlt: "Esfoliação de faixa masculina Pello Menos", method: "esfoliacao", audience: "masculino" },
  { id: "esfoliacao-braco-masc", name: "Esfoliação de braço", duration: "20 min • Avulso", originalCents: 3700, skipDiscount: true, category: "bracos", image: catalogImage("esfoliacao-braco-masc", "masculino"), imageAlt: "Esfoliação de braço masculina Pello Menos", method: "esfoliacao", audience: "masculino" },
  { id: "esfoliacao-meia-perna-masc", name: "Esfoliação de meia perna", duration: "20 min • Avulso", originalCents: 3095, skipDiscount: true, category: "pernas", image: catalogImage("esfoliacao-meia-perna-masc", "masculino"), imageAlt: "Esfoliação de meia perna masculina Pello Menos", method: "esfoliacao", audience: "masculino" },
  { id: "esfoliacao-abdomen-masc", name: "Esfoliação de abdômen", duration: "15 min • Avulso", originalCents: 2895, skipDiscount: true, category: "torax", image: catalogImage("esfoliacao-abdomen-masc", "masculino"), imageAlt: "Esfoliação de abdômen masculina Pello Menos", method: "esfoliacao", audience: "masculino" },
  { id: "esfoliacao-axilas-masc", name: "Esfoliação de axilas", duration: "15 min • Avulso", originalCents: 1945, skipDiscount: true, category: "axilas", image: catalogImage("esfoliacao-axilas-masc", "masculino"), imageAlt: "Esfoliação de axilas masculina Pello Menos", method: "esfoliacao", audience: "masculino", badge: "Pele" },
  { id: "esfoliacao-nadegas-masc", name: "Esfoliação de nádegas", duration: "15 min • Avulso", originalCents: 2625, skipDiscount: true, category: "corpo", image: catalogImage("esfoliacao-nadegas-masc", "masculino"), imageAlt: "Esfoliação de nádegas masculina Pello Menos", method: "esfoliacao", audience: "masculino" },
  { id: "esfoliacao-coxa-masc", name: "Esfoliação de coxa", duration: "20 min • Avulso", originalCents: 3095, skipDiscount: true, category: "pernas", image: catalogImage("esfoliacao-coxa-masc", "masculino"), imageAlt: "Esfoliação de coxa masculina Pello Menos", method: "esfoliacao", audience: "masculino" },
  { id: "esfoliacao-costas-masc", name: "Esfoliação de costas", duration: "20 min • Avulso", originalCents: 2995, skipDiscount: true, category: "corpo", image: catalogImage("esfoliacao-costas-masc", "masculino"), imageAlt: "Esfoliação de costas masculina Pello Menos", method: "esfoliacao", audience: "masculino" },
  { id: "esfoliacao-perna-masc", name: "Esfoliação de perna inteira", duration: "25 min • Avulso", originalCents: 5750, skipDiscount: true, category: "pernas", image: catalogImage("esfoliacao-perna-masc", "masculino"), imageAlt: "Esfoliação de perna inteira masculina Pello Menos", method: "esfoliacao", audience: "masculino", badge: "Pele", highlight: true },
  { id: "esfoliacao-virilha-masc", name: "Esfoliação de virilha", duration: "15 min • Avulso", originalCents: 2945, skipDiscount: true, category: "virilha", image: catalogImage("esfoliacao-virilha-masc", "masculino"), imageAlt: "Esfoliação de virilha masculina Pello Menos", method: "esfoliacao", audience: "masculino" },

  // Laser masculino — 10 sessões: originalCents = tabela cheia; Esquenta/Black aplica % sobre a tabela
  { id: "axilas-laser-masc", name: "Axila Laser", duration: "15 min • até 10 sessões", originalCents: 98000, category: "axilas", image: catalogImage("axilas-laser-masc", "masculino"), imageAlt: "Homem em campanha de laser nas axilas Pello Menos", method: "laser", audience: "masculino", badge: "60% OFF", highlight: true },
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
    return "Cartão Presente Pello Menos só para depilação a cera. Não vale para laser, linha, esfoliação nem planos. Informe a unidade onde o presente será usado.";
  }
  return "Body Splash oficial da linha Pello Menos para o cuidado em casa após a depilação.";
}

function catalogSku(index: number) {
  return `PM-${String(index + 1).padStart(4, "0")}`;
}

function catalogCode(id: string) {
  return `PEL-${id.replace(/-/g, "").toUpperCase()}`;
}


const SHARED_CHROME_TWIN_OVERRIDES: Partial<Record<string, Partial<ProductSeed>>> = {
  "plano-silver-masc": { originalCents: 12490, skipDiscount: true },
  "plano-gold-masc": { originalCents: 12990, skipDiscount: true },
};

function expandCatalogWithAudienceTwins(items: ProductSeed[]): ProductSeed[] {
  const out = items.slice();
  for (const baseId of SHARED_CHROME_TWIN_IDS) {
    const base = items.find((item) => item.id === baseId);
    if (!base) continue;
    if (out.some((item) => item.id === `${baseId}-masc`)) continue;
    const twinId = `${baseId}-masc`;
    out.push({
      ...base,
      id: twinId,
      audience: "masculino",
      ...(SHARED_CHROME_TWIN_OVERRIDES[twinId] ?? {}),
    });
  }
  return out;
}

export const products: Product[] = expandCatalogWithAudienceTwins(catalogItems).map(
  (item, index) => {
    const {
      originalCents,
      method: explicitMethod,
      audience: explicitAudience,
      skipDiscount,
      description,
      ...rest
    } = item;
    const method = inferMethod(canonicalCatalogId(item.id), explicitMethod);
    const audience = explicitAudience ?? "feminino";
    const pricing = resolveCatalogPrice({
      id: item.id,
      originalCents,
      method,
      skipDiscount,
      audience,
    });
    const charged = TEST_CHARGE_CENTS
      ? { priceCents: TEST_CHARGE_CENTS, oldPriceCents: pricing.oldPriceCents }
      : pricing;
    return {
      ...rest,
      originalCents,
      skipDiscount: !!skipDiscount,
      ...charged,
      duration: item.duration.replace(/^(\d+)/, "~$1"),
      method,
      audience,
      sku: catalogSku(index),
      code: catalogCode(item.id),
      description: description ?? defaultDescription(item, method, audience),
    };
  },
);

/** Recalcula preço de um produto já montado (ex.: carrinho com ≥3 áreas). */
export function priceProductInCart(product: Product, cartLines: CartLineLike[]) {
  return resolveCatalogPrice(
    {
      id: product.id,
      originalCents: product.originalCents,
      method: product.method,
      skipDiscount: product.skipDiscount,
      audience: product.audience,
    },
    cartLines,
  );
}

export function getProductById(id: string) {
  return products.find((item) => item.id === id);
}

export function productsForAudience(audience: ProductAudience) {
  // Twins carry explicit audience; shared fem SKUs stay feminino-only in listings.
  return products.filter((item) => item.audience === audience);
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

const SERVICE_CARD_PRODUCT: Record<ProductAudience, Partial<Record<ServiceMethod, string>>> = {
  feminino: {
    cera: "axila-cera",
    laser: "axilas-laser",
    linha: "buco-linha",
    esfoliacao: "esfoliacao-axilas",
  },
  masculino: {
    cera: "axila-cera-masc",
    laser: "axilas-laser-masc",
    esfoliacao: "esfoliacao-axilas-masc",
  },
};

export function serviceMethodCardImage(audience: ProductAudience, method: ServiceMethod) {
  const id = SERVICE_CARD_PRODUCT[audience][method];
  const product = id ? getProductById(id) : undefined;
  if (product?.image) return product.image;
  const fallback = productsByMethod(audience, method)[0];
  return fallback?.image ?? "/brand/logo-square.png";
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

export function retailProducts(audience: ProductAudience = "feminino") {
  return products.filter(
    (item) => item.method === "produto" && item.audience === audience,
  );
}

export function planProducts() {
  return products.filter((item) => item.method === "plano");
}

export function planProductsFor(audience: ProductAudience) {
  return planProducts().filter((item) => item.audience === audience);
}

export function giftCardProducts(audience: ProductAudience = "feminino") {
  return products
    .filter((item) => item.method === "presente" && item.audience === audience)
    .sort((a, b) => a.priceCents - b.priceCents);
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

function sortStoreUnits(units: StoreUnit[]) {
  return units.slice().sort(
    (a, b) =>
      a.state.localeCompare(b.state) || a.name.localeCompare(b.name, "pt-BR"),
  );
}

/** Which stores can sell this SKU (capacity flags). Bridge variation pruning is done by the caller. */
export function unitsForProduct(product: Pick<Product, "id" | "method" | "audience">) {
  const method = inferMethod(product.id, product.method);
  const audience = product.audience ?? "feminino";
  const baseId = canonicalCatalogId(product.id);

  // Linha / esfoliação / presente / produto: available in every unit.
  if (
    method === "linha" ||
    method === "esfoliacao" ||
    method === "presente" ||
    method === "produto" ||
    isBodySplashId(baseId)
  ) {
    return sortStoreUnits(storeUnits);
  }

  // Cera subscription plans follow cera capacity for the audience.
  if (method === "plano") {
    if (baseId === "plano-clube-laser") {
      if (audience === "masculino") return [];
      return sortStoreUnits(storeUnits.filter((unit) => unit.offersLaser));
    }
    // silver / gold / prepago = cera
    if (audience === "masculino") {
      return sortStoreUnits(storeUnits.filter((unit) => unit.offersCeraMasculino));
    }
    return sortStoreUnits(storeUnits.filter((unit) => unit.offersCera));
  }

  if (method === "cera") {
    if (audience === "masculino") {
      return sortStoreUnits(storeUnits.filter((unit) => unit.offersCeraMasculino));
    }
    return sortStoreUnits(storeUnits.filter((unit) => unit.offersCera));
  }

  if (method === "laser") {
    if (audience === "masculino") {
      return sortStoreUnits(storeUnits.filter((unit) => unit.offersLaserMasculino));
    }
    return sortStoreUnits(storeUnits.filter((unit) => unit.offersLaser));
  }

  return sortStoreUnits(storeUnits);
}

const CROSS_SELL: Record<string, string[]> = {
  "axila-cera": ["meia-perna-cera", "virilha-comum-cera", "buco-cera"],
  "abdomen-cera": ["virilha-comum-cera", "meia-perna-cera", "axila-cera"],
  "virilha-cera": ["meia-nadega-cera", "coxa-cera", "axila-cera"],
  "virilha-laser": ["virilha-comum-laser", "meia-nadega-cera", "coxa-cera"],
  "virilha-comum-laser": ["virilha-laser", "virilha-cavada-laser"],
  "axilas-laser": ["bracos-laser", "virilha-laser", "axila-cera"],
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
  return [...mapped, ...sameMethod, ...sameCategory]
    .filter((item) => !isComingSoon(item.id))
    .slice(0, limit);
}

/** Até `limit` sugestões a partir dos itens do carrinho (exclui o que já está no pedido). */
export function cartRecommendations(
  cartProductIds: string[],
  limit = 3,
): Product[] {
  const inCart = new Set(cartProductIds);
  const seen = new Set<string>();
  const out: Product[] = [];
  for (const id of cartProductIds) {
    const product = getProductById(id);
    if (!product) continue;
    for (const candidate of relatedProducts(product, 6)) {
      if (inCart.has(candidate.id) || seen.has(candidate.id)) continue;
      seen.add(candidate.id);
      out.push(candidate);
      if (out.length >= limit) return out;
    }
  }
  return out;
}

const pernaCeraHero = formatHeroCampaignPrice(8590, "cera");
const axilasLaserHero = formatHeroCampaignPrice(89990, "laser");
const axilasLaserMascHero = formatHeroCampaignPrice(98000, "laser");
const virilhaLaserHero = formatHeroCampaignPrice(209000, "laser");
const bracosLaserHero = formatHeroCampaignPrice(144000, "laser");
const peitoHero = formatHeroCampaignPrice(142000, "laser");
const costasHero = formatHeroCampaignPrice(158000, "laser");
const barbaHero = formatHeroCampaignPrice(107000, "laser");

export const heroSlides: HeroSlide[] = [
  {
    id: "verao",
    badge: "Cera 15% OFF",
    title: "Pernas prontas pra viver",
    ...pernaCeraHero,
    cta: "Ver cera",
    ctaHref: "/servicos/cera",
    image: "/images/hero/examples/banner-perna-desktop-fw.jpg",
    imageTablet: "/images/hero/examples/banner-exemplo-avatar-esquerda-tablet.jpg",
    imageMobile: "/images/hero/examples/banner-exemplo-avatar-esquerda.jpg",
    imagePosition: "50% 50%",
    imagePositionMobile: "50% 42%",
    imageAlt: "Mulher na campanha de pernas com cera Pello Menos",
    layout: "copy-top",
    bakedText: true,
  },
  {
    id: "laser-10",
    badge: "Laser 60% OFF",
    title: "10 sessões de laser nas axilas",
    ...axilasLaserHero,
    cta: "Ver laser",
    ctaHref: "/servicos/laser",
    image: "/images/hero/examples/banner-axilas-desktop-fw.jpg",
    imageTablet: "/images/hero/examples/banner-exemplo-avatar-direita-tablet.jpg",
    imageMobile: "/images/hero/examples/banner-exemplo-avatar-direita.jpg",
    imagePosition: "50% 50%",
    imagePositionMobile: "50% 42%",
    imageAlt: "Mulher no centro da campanha de laser nas axilas Pello Menos",
    layout: "split",
    bakedText: true,
  },
  {
    id: "virilha",
    badge: "Esquenta Black",
    title: "Virilha total a laser",
    ...virilhaLaserHero,
    cta: "Ver serviços",
    ctaHref: "/servicos",
    image: "/images/hero/examples/banner-virilha-desktop-fw.jpg",
    imageTablet: "/images/hero/examples/banner-virilha-tablet.jpg",
    imageMobile: "/images/hero/examples/banner-virilha-mobile.jpg",
    imagePosition: "50% 50%",
    imagePositionMobile: "50% 42%",
    imageAlt: "Mulher à esquerda na campanha de virilha a laser Pello Menos",
    layout: "copy-right",
    bakedText: true,
  },
  {
    id: "bracos",
    badge: "Laser 60% OFF",
    title: "Braços inteiros a laser",
    ...bracosLaserHero,
    cta: "Ver braços",
    ctaHref: "/servicos/laser",
    image: "/images/hero/examples/banner-bracos-desktop-fw.jpg",
    imageTablet: "/images/hero/examples/banner-bracos-tablet.jpg",
    imageMobile: "/images/hero/examples/banner-bracos-mobile.jpg",
    imagePosition: "50% 50%",
    imagePositionMobile: "50% 42%",
    imageAlt: "Mulher à direita na campanha de braços a laser Pello Menos",
    layout: "copy-left",
    bakedText: true,
  },
];

export const heroSlidesMasculino: HeroSlide[] = [
  {
    id: "peito",
    badge: "Laser 60% OFF",
    title: "Tórax liso, rotina leve",
    ...peitoHero,
    cta: "Ver laser",
    ctaHref: "/masculino/servicos/laser",
    image: M.heroPeito,
    imageMobile: M.heroPeito,
    imagePosition: "48% 28%",
    imagePositionMobile: "48% 28%",
    imageAlt: "Homem na campanha de laser no tórax Pello Menos",
    layout: "copy-right",
  },
  {
    id: "costas",
    badge: "Esquenta Black",
    title: "Costas a laser",
    ...costasHero,
    cta: "Ver costas",
    ctaHref: "/masculino/servicos/laser",
    image: M.heroCostas,
    imageMobile: M.heroCostas,
    imagePosition: "50% 26%",
    imagePositionMobile: "50% 26%",
    imageAlt: "Homem na campanha de laser nas costas Pello Menos",
    layout: "copy-left",
  },
  {
    id: "axilas-m",
    badge: "Laser 60% OFF",
    title: "10 sessões de laser nas axilas",
    ...axilasLaserMascHero,
    cta: "Ver axilas",
    ctaHref: "/masculino/servicos",
    image: M.heroAxilas,
    imageMobile: M.heroAxilas,
    imagePosition: "42% 32%",
    imagePositionMobile: "42% 32%",
    imageAlt: "Homem na campanha de laser nas axilas Pello Menos",
    layout: "copy-right",
  },
  {
    id: "barba",
    badge: "Esquenta Black",
    title: "Barba a laser",
    ...barbaHero,
    cta: "Ver barba",
    ctaHref: "/masculino/servicos/laser",
    image: M.heroBarba,
    imageMobile: M.heroBarba,
    imagePosition: "58% 28%",
    imagePositionMobile: "58% 28%",
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
const officialProducts = retailProducts("feminino");
const officialProductsMasc = retailProducts("masculino");

// Ranking real de itens vendidos, por unidades (pedidos de 01/08 a 13/11/2026).
// Itens fora da lista (sem venda no periodo) ficam no fim e mantem a ordem do
// catalogo, porque o sort e estavel. `filter` sozinho preserva a ordem
// alfabetica do catalogo — sem o sort a lista de ids nao tem efeito nenhum.
const salesSorter = (ranking: string[]) => (a: { id: string }, b: { id: string }) => {
  const rank = (id: string) => {
    const i = ranking.indexOf(id);
    return i < 0 ? ranking.length : i;
  };
  return rank(a.id) - rank(b.id);
};

const CERA_SALES = [
  "virilha-cera", // 174 un. — Virilha Total
  "perna-cera", // 54 — Perna Inteira
  "buco-cera", // 51 — Buço
  "axila-cera", // 51 — Axila
  "meia-nadega-cera", // 45 — Meia Nádega
  "virilha-cavada-cera", // 41
  "meia-perna-cera", // 35
  "virilha-cavada-faixa-cera", // 28
  "coxa-cera", // 24
  "sobrancelha-cera", // 20
  "virilha-comum-cera", // 19
  "faixa-cera", // 15
  "nariz-cera", // 13
  "virilha-comum-faixa-cera", // 12
];

const LASER_SALES = [
  "axilas-laser", // 38 un. no trimestre
  "virilha-comum-laser", // 8
  "buco-laser", // 3
  "rosto-inteiro-laser", // 2
  "virilha-laser", // 1
  "virilha-cavada-laser", // 1
  "pescoco-laser", // 1
  "perna-laser", // 1
  "orelhas-laser", // 1
  "intergluteos-laser", // 1
];

const ceraAreasIds = [
  "virilha-cavada-cera",
  "meia-perna-cera",
  "virilha-cavada-faixa-cera",
  "coxa-cera",
  "design-sobrancelha",
  "bracos-cera",
  "virilha-comum-cera",
  "nadegas-cera",
  "queixo-cera",
  "costas-cera",
];

export const productRails = {
  // "Cera em destaque": os 5 mais vendidos primeiro, na ordem do relatorio.
  ceraOfertas: female
    .filter((item) => item.method === "cera")
    .sort(salesSorter(CERA_SALES)),
  // "Cera por região": abre com os 4 seguintes mais vendidos (6o ao 9o).
  ceraAreas: female
    .filter((item) => ceraAreasIds.includes(item.id))
    .sort(salesSorter(CERA_SALES)),
  laserRosto: female
    .filter((item) => item.method === "laser" && item.category === "rosto")
    .sort(salesSorter(LASER_SALES)),
  laserCorpo: female
    .filter((item) => item.method === "laser" && item.category !== "rosto")
    .sort(salesSorter(LASER_SALES)),
  // Esfoliação: nenhuma venda registrada ate 13/11/2026 (produtos criados em
  // 12/11) — nao ha ranking real, mantem a ordem do catalogo.
  esfoliacao: female.filter((item) => item.method === "esfoliacao"),
  linha: female.filter((item) => item.method === "linha"),
  produtos: officialProducts,
  produtosMasc: officialProductsMasc,
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
      "barba-cera-masc",
      "bigode-cera-masc",
      "torax-abdomen-cera-masc",
      "saco-escrotal-cera-masc",
      "sobrancelha-cera-masc",
      "design-sobrancelha-masc",
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
    badge: "Esquenta Black",
    title: "Esquenta Black",
    subtitle: "Cera e esfoliação com 15% OFF. Laser com 60% OFF no site.",
    image: "/images/hero/promo-semana-v2.png",
    imageMobile: "/images/hero/promo-semana-v2-m.jpg",
    imagePosition: "50% 38%",
    imagePositionMobile: "28% 32%",
    imageAlt: "Mulher com axilas lisas na Esquenta Black",
  },
  {
    id: "olhar",
    badge: "Olhar",
    title: "Design de sobrancelha",
    subtitle: "Cera, henna e realce para valorizar o olhar.",
    image: "/images/hero/promo-olhar-v2.png",
    imageMobile: "/images/hero/promo-olhar-v2-m.jpg",
    imagePosition: "50% 32%",
    imagePositionMobile: "72% 28%",
    imageAlt: "Mulher com design de sobrancelha em spa com luz e textura",
    overlay: "purple",
  },
];

export const rectangularBannersMasculino: PromoBannerData[] = [
  {
    id: "laser-m",
    badge: "Esquenta Black",
    title: "Laser masculino",
    subtitle: "Peito, costas, barba e corpo com 60% OFF no site.",
    image: M.heroPeito,
    imageMobile: M.heroPeito,
    imagePosition: "48% 28%",
    imagePositionMobile: "48% 28%",
    imageAlt: "Homem na campanha de laser no tórax Pello Menos",
    textSide: "right",
    overlay: "purple",
  },
  {
    id: "corpo-m",
    badge: "Corpo",
    title: "Costas e peito",
    subtitle: "As áreas mais pedidas do público masculino na Esquenta Black.",
    image: M.promoCorpo,
    imageMobile: M.promoCorpoM,
    imagePosition: "62% 42%",
    imagePositionMobile: "72% 40%",
    imageAlt: "Homem na campanha de costas e peito Pello Menos",
    overlay: "purple",
  },
];

export const squareBanners: SquareBannerData[] = [
  {
    id: "cera",
    title: "Cera",
    subtitle: "Sessão avulsa, resultado no mesmo dia",
    image: catalogImage("axila-cera"),
    imagePosition: "62% 42%",
    imageAlt: "Depilação a cera na axila — área marcada",
    href: "/servicos/cera",
  },
  {
    id: "linha",
    title: "Linha",
    subtitle: "Precisão no contorno do rosto",
    image: catalogImage("buco-linha"),
    imagePosition: "50% 38%",
    imageAlt: "Depilação com linha no buço — área marcada",
    href: "/servicos/linha",
  },
  {
    id: "laser",
    title: "Laser",
    subtitle: "Pacotes de até 10 sessões",
    image: catalogImage("axilas-laser"),
    imagePosition: "62% 42%",
    imageAlt: "Depilação a laser na axila — área marcada",
    href: "/servicos/laser",
  },
  {
    id: "esfoliacao",
    title: "Esfoliação",
    subtitle: "Pele pronta para a cera",
    image: catalogImage("esfoliacao-axilas"),
    imagePosition: "62% 42%",
    imageAlt: "Esfoliação na axila — área marcada",
    href: "/servicos/esfoliacao",
  },
];

export const squareBannersMasculino: SquareBannerData[] = [
  {
    id: "cera-m",
    title: "Cera",
    subtitle: "Sessão avulsa, resultado no mesmo dia",
    image: catalogImage("peito-cera-masc", "masculino"),
    imagePosition: "50% 34%",
    imageAlt: "Depilação a cera no peito masculino — área marcada",
    href: "/masculino/servicos/cera",
  },
  {
    id: "laser-m",
    title: "Laser",
    subtitle: "Pacotes de até 10 sessões",
    image: catalogImage("barba-laser-masc", "masculino"),
    imagePosition: "50% 36%",
    imageAlt: "Depilação a laser na barba — área marcada",
    href: "/masculino/servicos/laser",
  },
  {
    id: "esfoliacao-m",
    title: "Esfoliação",
    subtitle: "Pele pronta para a cera",
    image: catalogImage("esfoliacao-axilas-masc", "masculino"),
    imagePosition: "58% 40%",
    imageAlt: "Esfoliação masculina na axila — área marcada",
    href: "/masculino/servicos/esfoliacao",
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
    { label: "Silver - Cera", href: productHref(audience, "plano-silver") },
    { label: "Gold - Cera", href: productHref(audience, "plano-gold") },
  ];
  if (audience === "feminino") {
    planChildren.push({ label: "Clube de Laser", href: productHref(audience, "plano-clube-laser") });
  }
  planChildren.push({ label: "Pré Pago", href: productHref(audience, "plano-prepago") });

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
    {
      label: "Cartão Presente",
      href: giftCardHref(audience),
      children: giftCardProducts(audience).map((item) => ({
        label: item.name,
        href: productHref(audience, item.id),
      })),
    },
    { label: "Produtos", href: retailHref(audience) },
  ];
}
