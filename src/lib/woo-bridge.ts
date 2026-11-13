import {
  resolveCatalogPrice,
  TEST_CHARGE_CENTS,
  type PriceRegion,
  type Product,
} from "@/lib/data";
import bridgeData from "@/lib/woo-bridge.json";

export type RegionQuote = {
  regularCents: number;
  saleCents: number;
};

export type WooUnitLink = {
  variationId: number;
  option: string;
};

export type WooBridge = {
  slug: string;
  productId: number;
  longText: string;
  rj?: RegionQuote;
  spdf?: RegionQuote;
  units: Record<string, WooUnitLink>;
};

const bridge = bridgeData as Record<string, WooBridge>;

export function productBridge(id: string) {
  if (bridge[id]) return bridge[id];
  // Chrome twins (`*-masc`) reuse the same Woo SKU as the feminine base id.
  if (id.endsWith("-masc")) {
    const base = id.slice(0, -5);
    return bridge[base];
  }
  return undefined;
}

/**
 * Tabela regional para a ficha. Preferimos o regular do bridge (RJ/SP-DF).
 * Se o bridge RJ divergir forte do originalCents do catálogo (SKU Woo
 * compartilhado / desatualizado), usamos o catálogo com o fator regional.
 */
function tableCentsFor(product: Product, region: PriceRegion): number {
  const row = productBridge(product.id);
  const side = region === "sp-df" ? row?.spdf ?? row?.rj : row?.rj;
  const rjSide = row?.rj;
  const catalog = Math.max(0, Math.round(Number(product.originalCents) || 0));

  if (side?.regularCents) {
    let table = Math.round(side.regularCents);
    if (
      catalog > 0 &&
      rjSide?.regularCents &&
      Math.abs(rjSide.regularCents - catalog) > Math.max(200, catalog * 0.12)
    ) {
      const factor =
        rjSide.regularCents > 0 ? side.regularCents / rjSide.regularCents : 1;
      table = Math.round(catalog * factor);
    }
    return table;
  }

  return (
    catalog ||
    Math.round(Number(product.oldPriceCents) || 0) ||
    Math.round(Number(product.priceCents) || 0)
  );
}

export function quoteFor(product: Product, region: PriceRegion): RegionQuote {
  const row = productBridge(product.id);
  const side = region === "sp-df" ? row?.spdf ?? row?.rj : row?.rj;
  const tableCents = tableCentsFor(product, region);

  if (!tableCents) {
    const fallback = side
      ? side
      : !product.oldPriceCents
        ? { regularCents: product.priceCents, saleCents: product.priceCents }
        : {
            regularCents: product.oldPriceCents ?? product.priceCents,
            saleCents: Math.floor(
              ((product.oldPriceCents ?? product.priceCents) * 9) / 10,
            ),
          };
    if (!TEST_CHARGE_CENTS) return fallback;
    return { regularCents: TEST_CHARGE_CENTS, saleCents: TEST_CHARGE_CENTS };
  }

  // Bridge regular já é tabela cheia — não reaplicar skipDiscount (÷0.95).
  const priced = resolveCatalogPrice({
    id: product.id,
    originalCents: tableCents,
    method: product.method,
    skipDiscount: side?.regularCents ? false : !!product.skipDiscount,
    audience: product.audience,
  });

  const quote: RegionQuote = {
    regularCents: priced.oldPriceCents ?? tableCents,
    saleCents: priced.priceCents,
  };
  if (!TEST_CHARGE_CENTS) return quote;
  return { regularCents: TEST_CHARGE_CENTS, saleCents: TEST_CHARGE_CENTS };
}

function composedLong(product: Product) {
  const area = product.name.replace(/\s+[–-]\s+.*/, "");
  const audience = product.audience === "masculino" ? "masculino" : "feminino";
  const technique: Record<Product["method"], string> = {
    cera: `A depilação a cera de ${area} retira o pelo pela raiz na região do serviço. A sessão é avulsa e o resultado aparece no mesmo dia.`,
    laser: `O laser de ${area} é feito em sessões, com intervalo entre uma aplicação e outra. O pacote reduz o pelo aos poucos e a manutenção fica com a profissional.`,
    linha: `A depilação com linha de ${area} faz o contorno fio a fio, na região marcada do serviço.`,
    esfoliacao: `A esfoliação de ${area} renova a pele da região antes ou junto da depilação, retirando as células da superfície.`,
    produto: `${product.name} é um item da loja para uso em casa, separado dos serviços de cabine.`,
    plano: `${product.name} reúne sessões ou benefícios do clube. O uso segue as regras do plano escolhido na unidade.`,
    presente: `${product.name} é um crédito para a pessoa presenteada usar nos serviços da loja.`,
  };
  const lead = product.description?.trim() || technique[product.method];
  return [
    `${product.name} no atendimento ${audience} da Pello Menos.`,
    lead,
    technique[product.method],
    "Antes da sessão, a região precisa estar limpa, sem creme e sem óleo. Depois, a profissional indica o cuidado do dia: evitar sol forte, piscina e academia até a pele assentar.",
    "A imagem do serviço é meramente ilustrativa. O valor muda conforme a unidade, porque São Paulo capital e DF têm outra tabela.",
  ].join("\n\n");
}

export function longCopy(short: string, longText: string, product?: Product) {
  const notice =
    "A imagem do serviço é meramente ilustrativa. O valor muda conforme a unidade, porque São Paulo capital e DF têm outra tabela.";
  const stored = longText || "";
  const rich = stored.trim().length > 500 ? stored : product ? composedLong(product) : stored;
  let source = rich || "";
  if (source && !/são paulo capital/i.test(source)) {
    source = `${source}\n\n${notice}`;
  }
  const parts = source
    .split(/\n\n+/)
    .map((part) => part.replace(/\s+/g, " ").trim())
    .filter(Boolean);
  if (!parts.length) return { lead: "", more: [] as string[] };

  const shortNorm = short.replace(/\s+/g, " ").trim();
  let [first, ...rest] = parts;
  if (first.toLowerCase() === shortNorm.toLowerCase()) {
    first = rest.shift() ?? "";
  } else if (first.toLowerCase().startsWith(shortNorm.toLowerCase())) {
    first = first.slice(shortNorm.length).replace(/^[\s.:;\-–—]+/, "").trim();
  }
  if (!first && rest.length) first = rest.shift() ?? "";
  return { lead: first, more: rest.filter(Boolean) };
}
