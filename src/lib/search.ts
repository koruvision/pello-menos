import { productCopy } from "@/lib/product-copy";
import {
  categoryLabels,
  type Product,
  type ProductAudience,
  type ProductCategory,
  type ProductMethod,
  unitsForProduct,
} from "@/lib/data";

export type SearchSort = "relevance" | "name" | "price-asc" | "price-desc";
export type SearchAudience = ProductAudience | "todos";
export type SessionBucket = "avulso" | "pacote" | "outro";
export type SearchSessions = "" | "avulso" | "pacote";

export type SearchFilters = {
  q: string;
  /** @deprecated prefer `categories`; kept synced for single-value callers */
  category: string;
  categories: string[];
  method: string;
  min: number | null;
  max: number | null;
  sort: SearchSort;
  audience: SearchAudience;
  sessions: SearchSessions;
  unit: string;
  promo: boolean;
};

function getParam(
  params: URLSearchParams | Record<string, string | string[] | undefined>,
  key: string,
) {
  if (params instanceof URLSearchParams) return params.get(key) || "";
  const raw = params[key];
  return Array.isArray(raw) ? raw[0] || "" : raw || "";
}

function parseCategories(raw: string): string[] {
  return raw
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
}

export function sessionBucket(product: Pick<Product, "duration">): SessionBucket {
  const duration = (product.duration || "").toLowerCase();
  if (/sess/.test(duration)) return "pacote";
  if (/avulso/.test(duration)) return "avulso";
  return "outro";
}

export function productHasPromo(
  product: Pick<Product, "badge" | "oldPriceCents" | "priceCents">,
): boolean {
  if (
    product.oldPriceCents != null &&
    product.oldPriceCents > product.priceCents
  ) {
    return true;
  }
  const badge = product.badge || "";
  return /\d+\s*%|%\s*off|\boff\b|esquenta|black/i.test(badge);
}

export function productAvailableAtUnit(
  product: Pick<Product, "id" | "method" | "audience">,
  unitId: string,
): boolean {
  if (!unitId) return true;
  return unitsForProduct(product).some((unit) => unit.id === unitId);
}

export function searchAreaOptions(
  audience: SearchAudience,
  catalog: Product[],
): { id: ProductCategory; label: string }[] {
  const set = new Set<ProductCategory>();
  for (const product of catalog) {
    if (audience !== "todos" && product.audience !== audience) continue;
    set.add(product.category);
  }
  return Array.from(set)
    .sort((a, b) =>
      categoryLabels[a].localeCompare(categoryLabels[b], "pt-BR"),
    )
    .map((id) => ({ id, label: categoryLabels[id] }));
}

export function countActiveSearchFilters(filters: SearchFilters): number {
  let n = 0;
  if (filters.audience === "feminino" || filters.audience === "masculino") n += 1;
  if (filters.categories.length) n += 1;
  if (filters.method) n += 1;
  if (filters.min != null || filters.max != null) n += 1;
  if (filters.sessions) n += 1;
  if (filters.unit) n += 1;
  if (filters.promo) n += 1;
  return n;
}

export function parseSearchFilters(
  params: URLSearchParams | Record<string, string | string[] | undefined>,
): SearchFilters {
  const minRaw = getParam(params, "min").replace(",", ".");
  const maxRaw = getParam(params, "max").replace(",", ".");
  const minNum = minRaw ? Number(minRaw) : NaN;
  const maxNum = maxRaw ? Number(maxRaw) : NaN;
  const sortRaw = getParam(params, "sort");
  const sort: SearchSort =
    sortRaw === "name" || sortRaw === "price-asc" || sortRaw === "price-desc"
      ? sortRaw
      : "relevance";
  const audienceRaw = getParam(params, "audience");
  const audience: SearchAudience =
    audienceRaw === "masculino"
      ? "masculino"
      : audienceRaw === "todos"
        ? "todos"
        : audienceRaw === "feminino"
          ? "feminino"
          : "todos";
  const categories = parseCategories(getParam(params, "category"));
  const sessionsRaw = getParam(params, "sessions");
  const sessions: SearchSessions =
    sessionsRaw === "avulso" || sessionsRaw === "pacote" ? sessionsRaw : "";
  const promoRaw = getParam(params, "promo");
  return {
    q: getParam(params, "q").trim(),
    category: categories[0] || "",
    categories,
    method: getParam(params, "method").trim(),
    min: Number.isFinite(minNum) ? Math.round(minNum * 100) : null,
    max: Number.isFinite(maxNum) ? Math.round(maxNum * 100) : null,
    sort,
    audience,
    sessions,
    unit: getParam(params, "unit").trim(),
    promo: promoRaw === "1" || promoRaw === "true",
  };
}

export function productSearchHaystack(product: Product) {
  return [
    product.name,
    product.duration,
    product.category,
    product.imageAlt,
    product.sku,
    product.code,
    product.description,
    productCopy(product.id).short,
    productCopy(product.id).long,
    product.badge || "",
    product.method,
  ]
    .join(" ")
    .toLowerCase();
}

export function matchesSearchQuery(product: Product, q: string) {
  const normalized = q.trim().toLowerCase();
  if (!normalized) return true;
  return productSearchHaystack(product).includes(normalized);
}

export function filterSearchProducts(
  catalog: Product[],
  filters: SearchFilters,
): Product[] {
  let list = catalog.slice();
  if (filters.audience !== "todos") {
    list = list.filter((product) => product.audience === filters.audience);
  }
  if (filters.q) {
    list = list.filter((product) => matchesSearchQuery(product, filters.q));
  }
  const cats =
    filters.categories.length > 0
      ? filters.categories
      : filters.category
        ? [filters.category]
        : [];
  if (cats.length) {
    const set = new Set(cats);
    list = list.filter((product) => set.has(product.category));
  }
  if (filters.method) {
    list = list.filter(
      (product) => product.method === (filters.method as ProductMethod),
    );
  }
  if (filters.min != null) {
    list = list.filter((product) => product.priceCents >= filters.min!);
  }
  if (filters.max != null) {
    list = list.filter((product) => product.priceCents <= filters.max!);
  }
  if (filters.sessions) {
    list = list.filter(
      (product) => sessionBucket(product) === filters.sessions,
    );
  }
  if (filters.unit) {
    list = list.filter((product) =>
      productAvailableAtUnit(product, filters.unit),
    );
  }
  if (filters.promo) {
    list = list.filter((product) => productHasPromo(product));
  }

  const sorted = [...list];
  if (filters.sort === "name") {
    sorted.sort((a, b) => a.name.localeCompare(b.name, "pt-BR"));
  } else if (filters.sort === "price-asc") {
    sorted.sort((a, b) => a.priceCents - b.priceCents);
  } else if (filters.sort === "price-desc") {
    sorted.sort((a, b) => b.priceCents - a.priceCents);
  } else if (filters.q) {
    const needle = filters.q.toLowerCase();
    sorted.sort((a, b) => {
      const aName = a.name.toLowerCase().startsWith(needle) ? 0 : 1;
      const bName = b.name.toLowerCase().startsWith(needle) ? 0 : 1;
      if (aName !== bName) return aName - bName;
      return a.name.localeCompare(b.name, "pt-BR");
    });
  } else {
    sorted.sort((a, b) => a.name.localeCompare(b.name, "pt-BR"));
  }
  return sorted;
}

export function emptySearchFilters(
  overrides: Partial<SearchFilters> = {},
): SearchFilters {
  return {
    q: "",
    category: "",
    categories: [],
    method: "",
    min: null,
    max: null,
    sort: "relevance",
    audience: "todos",
    sessions: "",
    unit: "",
    promo: false,
    ...overrides,
  };
}

export function buildSearchHref(
  filters: Partial<SearchFilters> & { q?: string },
) {
  const params = new URLSearchParams();
  if (filters.q?.trim()) params.set("q", filters.q.trim());
  if (filters.audience && filters.audience !== "todos") {
    params.set("audience", filters.audience);
  }
  const cats =
    filters.categories && filters.categories.length
      ? filters.categories
      : filters.category
        ? [filters.category]
        : [];
  if (cats.length) params.set("category", cats.join(","));
  if (filters.method) params.set("method", filters.method);
  if (filters.min != null) params.set("min", (filters.min / 100).toFixed(2));
  if (filters.max != null) params.set("max", (filters.max / 100).toFixed(2));
  if (filters.sort && filters.sort !== "relevance") {
    params.set("sort", filters.sort);
  }
  if (filters.sessions) params.set("sessions", filters.sessions);
  if (filters.unit) params.set("unit", filters.unit);
  if (filters.promo) params.set("promo", "1");
  const qs = params.toString();
  return qs ? `/busca?${qs}` : "/busca";
}
