/**
 * Campanha Black Novembro (e-commerce) — calendário + regras.
 * Espelho JSON: wordpress-loja/pm-home/black-nov-campaign.json
 * Espelho PHP: scripts/pm_black_nov_snippet.php
 *
 * Premissas: ≥3 IDs distintos por família; laser vs cera+esfoliação separados;
 * 5% de catálogo NÃO se aplica no período; % sobre preço de tabela (original).
 */

export type CampaignPhase = "off" | "esquenta" | "black_week";
export type CampaignFamily = "laser" | "cera_esf" | "excluded";
export type CeraTier = "P" | "M" | "G";

/** America/Sao_Paulo wall times as ISO offsets (-03:00). Ano = campanha vigente (nov/2026). */
export const BLACK_NOV = {
  year: 2026,
  timezone: "America/Sao_Paulo",
  esquentaStart: "2026-11-03T00:00:00-03:00",
  esquentaEnd: "2026-11-21T23:59:59-03:00",
  blackWeekStart: "2026-11-23T00:00:00-03:00",
  blackWeekEnd: "2026-11-30T23:59:59-03:00",
  laser: {
    esquenta: { any: 0.6, multi: 0.65 },
    black_week: { any: 0.7, multi: 0.75 },
  },
  ceraEsf: {
    esquenta: { any: 0.15, multi: 0.2 },
    black_week_esfoliacao: 0.15,
    black_week_cera: { P: 0.4, M: 0.3, G: 0.25 } as Record<CeraTier, number>,
  },
  multiThreshold: 3,
  excludeIdPrefixes: ["body-splash", "cartao-presente", "plano-"],
  excludeMethods: ["produto", "presente", "plano", "linha"] as const,
} as const;

/** Black Week cera — área P (40%). Inclui twins -masc quando existirem. */
export const CERA_TIER_P: string[] = [
  "axila-cera",
  "axila-cera-masc",
  "buco-cera",
  "queixo-cera",
  "queixo-cera-masc",
  "nariz-cera",
  "nariz-cera-masc",
  "seios-cera",
  "mamilos-cera-masc",
  "intergluteos-cera",
  "intergluteos-cera-masc",
];

/** Black Week cera — área M (30%). */
export const CERA_TIER_M: string[] = [
  "meia-perna-cera",
  "meia-perna-cera-masc",
  "coxa-cera",
  "coxa-cera-masc",
  "antebraco-cera",
  "antebraco-cera-masc",
  "faixa-cera",
  "faixa-cera-masc",
  "meia-nadega-cera",
  "meia-nadega-cera-masc",
  "sobrancelha-cera",
  "sobrancelha-cera-masc",
  "design-sobrancelha",
  "design-sobrancelha-masc",
  "sobrancelha-realce-cera",
  "design-sobrancelha-realce",
  "sobrancelha-henna-simples",
  "sobrancelha-henna",
  "labios-genitais-cera",
  "realce",
  "henna",
  "tintura-pelos-pubianos",
];

/** Black Week cera — área G (25%). */
export const CERA_TIER_G: string[] = [
  "abdomen-cera",
  "abdomen-cera-masc",
  "bracos-cera",
  "bracos-cera-masc",
  "costas-cera",
  "costas-cera-masc",
  "nadegas-cera",
  "nadegas-cera-masc",
  "perna-cera",
  "perna-cera-masc",
  "virilha-comum-cera",
  "virilha-comum-cera-masc",
  "virilha-comum-faixa-cera",
  "virilha-cavada-cera",
  "virilha-cavada-faixa-cera",
  "virilha-modelada-cera",
  "virilha-cera",
  "virilha-cera-masc",
  "peito-cera-masc",
  "torax-abdomen-cera-masc",
  "barba-cera-masc",
  "barba-modeladora-cera-masc",
  "bigode-cera-masc",
  "orelha-cera-masc",
  "pescoco-cera-masc",
  "saco-escrotal-cera-masc",
];

const tierP = new Set(CERA_TIER_P);
const tierM = new Set(CERA_TIER_M);
const tierG = new Set(CERA_TIER_G);

export function ceraTierForId(productId: string): CeraTier {
  const id = String(productId || "");
  if (tierP.has(id)) return "P";
  if (tierM.has(id)) return "M";
  if (tierG.has(id)) return "G";
  // Não mapeado: menor desconto (G) para não estourar margem.
  return "G";
}

function forcedPhase(): CampaignPhase | null {
  try {
    if (typeof process !== "undefined" && process.env?.PM_BLACK_NOV_FORCE) {
      const v = String(process.env.PM_BLACK_NOV_FORCE).toLowerCase();
      if (v === "esquenta" || v === "black_week" || v === "off") return v;
    }
  } catch {
    /* ignore */
  }
  try {
    if (typeof globalThis !== "undefined") {
      const w = globalThis as { __PM_BLACK_PHASE__?: string };
      const v = String(w.__PM_BLACK_PHASE__ || "").toLowerCase();
      if (v === "esquenta" || v === "black_week" || v === "off") return v;
    }
  } catch {
    /* ignore */
  }
  return null;
}

export function campaignPhaseAt(now: Date = new Date()): CampaignPhase {
  const forced = forcedPhase();
  if (forced) return forced;
  const t = now.getTime();
  const a = Date.parse(BLACK_NOV.esquentaStart);
  const b = Date.parse(BLACK_NOV.esquentaEnd);
  const c = Date.parse(BLACK_NOV.blackWeekStart);
  const d = Date.parse(BLACK_NOV.blackWeekEnd);
  if (t >= a && t <= b) return "esquenta";
  if (t >= c && t <= d) return "black_week";
  return "off";
}

export function isExcludedProduct(id: string, method?: string | null): boolean {
  const pid = String(id || "");
  if (!pid) return true;
  for (const prefix of BLACK_NOV.excludeIdPrefixes) {
    if (pid === prefix || pid.startsWith(prefix)) return true;
  }
  const m = String(method || "").toLowerCase();
  if (m && (BLACK_NOV.excludeMethods as readonly string[]).includes(m)) return true;
  return false;
}

export function familyForProduct(id: string, method?: string | null): CampaignFamily {
  if (isExcludedProduct(id, method)) return "excluded";
  const m = String(method || "").toLowerCase();
  const pid = String(id || "");
  if (m === "laser" || pid.includes("-laser") || pid.endsWith("laser")) return "laser";
  if (m === "cera" || m === "esfoliacao") return "cera_esf";
  if (pid.includes("-cera") || pid.includes("esfoliacao") || pid === "realce" || pid === "henna") {
    return "cera_esf";
  }
  if (pid.includes("tintura-pelos")) return "cera_esf";
  return "excluded";
}

export type CartLineLike = {
  id: string;
  method?: string | null;
  quantity?: number;
};

export function countDistinctAreas(lines: CartLineLike[], family: CampaignFamily): number {
  const ids = new Set<string>();
  for (const line of lines) {
    if (!line || !line.id) continue;
    if (familyForProduct(line.id, line.method) !== family) continue;
    ids.add(String(line.id));
  }
  return ids.size;
}

/**
 * Percentual OFF (0–1) para um item, dado o carrinho (contagem multi-área).
 * null = fora da campanha / excluído → usar preço normal (5% ou skipDiscount).
 */
export function discountRateForLine(
  productId: string,
  method: string | null | undefined,
  lines: CartLineLike[],
  now: Date = new Date(),
): number | null {
  const phase = campaignPhaseAt(now);
  if (phase === "off") return null;
  const family = familyForProduct(productId, method);
  if (family === "excluded") return null;

  if (family === "laser") {
    const n = countDistinctAreas(lines, "laser");
    const table = BLACK_NOV.laser[phase];
    return n >= BLACK_NOV.multiThreshold ? table.multi : table.any;
  }

  // cera + esfoliação
  const m = String(method || "").toLowerCase();
  const isEsf = m === "esfoliacao" || String(productId).startsWith("esfoliacao");

  if (phase === "esquenta") {
    const n = countDistinctAreas(lines, "cera_esf");
    const table = BLACK_NOV.ceraEsf.esquenta;
    return n >= BLACK_NOV.multiThreshold ? table.multi : table.any;
  }

  // black_week
  if (isEsf) return BLACK_NOV.ceraEsf.black_week_esfoliacao;
  const tier = ceraTierForId(productId);
  return BLACK_NOV.ceraEsf.black_week_cera[tier];
}

/**
 * Base de tabela para aplicar o %.
 * Itens masc cera/esfoliação com skipDiscount já estão no preço “e-commerce (−5%)”:
 * recuperamos a tabela cheia ÷0.95 antes do % da campanha.
 */
export function campaignBaseCents(
  originalCents: number,
  opts?: { skipDiscount?: boolean; method?: string | null; audience?: string | null },
): number {
  const base = Math.max(0, Math.round(Number(originalCents) || 0));
  if (!opts?.skipDiscount) return base;
  const m = String(opts.method || "").toLowerCase();
  if (m === "cera" || m === "esfoliacao") {
    return Math.round(base / (1 - 0.05));
  }
  return base;
}

export function applyCampaignCents(
  originalCents: number,
  rate: number,
  opts?: { skipDiscount?: boolean; method?: string | null; audience?: string | null },
): { oldPriceCents: number; priceCents: number; discountRate: number } {
  const oldPriceCents = campaignBaseCents(originalCents, opts);
  const priceCents = Math.round(oldPriceCents * (1 - rate));
  return { oldPriceCents, priceCents, discountRate: rate };
}

/** Nome do desconto na UI (resumo do carrinho / checkout). */
export function campaignDiscountLabel(now: Date = new Date()): string | null {
  const phase = campaignPhaseAt(now);
  if (phase === "esquenta") return "Desconto Esquenta Black";
  if (phase === "black_week") return "Desconto Black Week";
  return null;
}

export function multiAreaHint(
  lines: CartLineLike[],
  family: CampaignFamily,
  now: Date = new Date(),
): { need: number; nextRate: number; label: string } | null {
  const phase = campaignPhaseAt(now);
  if (phase === "off") return null;
  if (family === "laser") {
    const n = countDistinctAreas(lines, "laser");
    if (n >= BLACK_NOV.multiThreshold) return null;
    const next = BLACK_NOV.laser[phase].multi;
    return {
      need: BLACK_NOV.multiThreshold - n,
      nextRate: next,
      label: "laser",
    };
  }
  if (family === "cera_esf" && phase === "esquenta") {
    const n = countDistinctAreas(lines, "cera_esf");
    if (n >= BLACK_NOV.multiThreshold) return null;
    return {
      need: BLACK_NOV.multiThreshold - n,
      nextRate: BLACK_NOV.ceraEsf.esquenta.multi,
      label: "cera e esfoliação",
    };
  }
  return null;
}

/** Payload JSON consumido pelo cart.js / PHP. */
export function blackNovCampaignJson() {
  return {
    ...BLACK_NOV,
    ceraTierP: CERA_TIER_P,
    ceraTierM: CERA_TIER_M,
    ceraTierG: CERA_TIER_G,
  };
}
