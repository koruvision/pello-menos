"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState, useTransition } from "react";
import { BadgeTag } from "@/components/BadgeTag";
import { ComingSoonOverlay } from "@/components/ComingSoonOverlay";
import { Icon } from "@/components/Icon";
import {
  BODY_SPLASH_LAUNCH_LABEL,
  formatBRL,
  getInstallment,
  homeHref,
  isComingSoon,
  methodLabels,
  products,
  storeUnits,
  unitsForProduct,
  type ProductAudience,
  type ProductMethod,
} from "@/lib/data";
import {
  buildSearchHref,
  countActiveSearchFilters,
  emptySearchFilters,
  filterSearchProducts,
  parseSearchFilters,
  productHasPromo,
  searchAreaOptions,
  sessionBucket,
  type SearchAudience,
  type SearchFilters,
  type SearchSessions,
  type SearchSort,
} from "@/lib/search";

const fieldClass =
  "mt-1.5 block w-full rounded-xl border border-primary/25 bg-white px-3 py-2.5 text-sm text-on-surface outline-none focus:border-primary";

const chipClass =
  "inline-flex shrink-0 items-center gap-1.5 rounded-full border px-3.5 py-2 text-sm transition";

const methodFilters: { id: "" | ProductMethod; label: string }[] = [
  { id: "", label: "Todos" },
  { id: "cera", label: methodLabels.cera },
  { id: "laser", label: methodLabels.laser },
  { id: "linha", label: methodLabels.linha },
  { id: "esfoliacao", label: methodLabels.esfoliacao },
  { id: "produto", label: methodLabels.produto },
  { id: "plano", label: methodLabels.plano },
  { id: "presente", label: methodLabels.presente },
];

function parseReais(raw: string): number | null {
  const trimmed = raw.trim();
  if (!trimmed) return null;
  const num = Math.round(Number(trimmed.replace(",", ".")) * 100);
  return Number.isFinite(num) ? num : null;
}

function homeAudience(audience: SearchAudience): ProductAudience {
  return audience === "masculino" ? "masculino" : "feminino";
}

type DraftState = {
  audience: SearchAudience;
  categories: string[];
  method: string;
  minReais: string;
  maxReais: string;
  sessions: SearchSessions;
  unit: string;
  promo: boolean;
};

function draftFromFilters(filters: SearchFilters): DraftState {
  return {
    audience: filters.audience,
    categories: [...filters.categories],
    method: filters.method,
    minReais: filters.min != null ? String(filters.min / 100) : "",
    maxReais: filters.max != null ? String(filters.max / 100) : "",
    sessions: filters.sessions,
    unit: filters.unit,
    promo: filters.promo,
  };
}

function FiltersForm({
  draft,
  setDraft,
  areaOptions,
  onApply,
  onClear,
  idPrefix,
}: {
  draft: DraftState;
  setDraft: (next: DraftState) => void;
  areaOptions: { id: string; label: string }[];
  onApply: () => void;
  onClear: () => void;
  idPrefix: string;
}) {
  function toggleCategory(id: string) {
    const has = draft.categories.includes(id);
    setDraft({
      ...draft,
      categories: has
        ? draft.categories.filter((item) => item !== id)
        : [...draft.categories, id],
    });
  }

  return (
    <div className="space-y-5" data-pm-search-filters-form={idPrefix}>
      <div>
        <p className="text-sm font-semibold text-on-surface">Público</p>
        <div className="mt-2 space-y-2" data-pm-search-audience-group>
          {(
            [
              ["todos", "Todos"],
              ["feminino", "Feminino"],
              ["masculino", "Masculino"],
            ] as const
          ).map(([value, label]) => (
            <label
              key={value}
              className="flex cursor-pointer items-center gap-2.5 text-sm text-on-surface"
            >
              <input
                type="radio"
                name={`${idPrefix}-audience`}
                value={value}
                checked={draft.audience === value}
                data-pm-search-audience={value}
                onChange={() =>
                  setDraft({ ...draft, audience: value, categories: [] })
                }
                className="accent-primary"
              />
              {label}
            </label>
          ))}
        </div>
      </div>

      <div>
        <p className="text-sm font-semibold text-on-surface">Áreas</p>
        <div className="mt-2 max-h-48 space-y-2 overflow-y-auto pr-1">
          {areaOptions.map((item) => (
            <label
              key={item.id}
              className="flex cursor-pointer items-center gap-2.5 text-sm text-on-surface"
            >
              <input
                type="checkbox"
                value={item.id}
                checked={draft.categories.includes(item.id)}
                data-pm-search-area={item.id}
                onChange={() => toggleCategory(item.id)}
                className="accent-primary"
              />
              {item.label}
            </label>
          ))}
        </div>
      </div>

      <label className="block text-sm text-on-surface-variant">
        Tipo de serviço
        <select
          className={fieldClass}
          value={draft.method}
          data-pm-search-method
          onChange={(event) =>
            setDraft({ ...draft, method: event.target.value })
          }
        >
          {methodFilters.map((item) => (
            <option key={item.id || "todos"} value={item.id}>
              {item.label}
            </option>
          ))}
        </select>
      </label>

      <div className="border-t border-outline/30 pt-5">
        <p className="text-sm font-semibold text-on-surface">Faixa de preço</p>
        <div className="mt-3 grid grid-cols-[1fr_auto_1fr] items-end gap-2">
          <label className="block text-xs text-on-surface-variant">
            Valor mínimo
            <input
              value={draft.minReais}
              onChange={(event) =>
                setDraft({ ...draft, minReais: event.target.value })
              }
              inputMode="decimal"
              placeholder="R$ 0,00"
              className={fieldClass}
              data-pm-search-min
            />
          </label>
          <span className="pb-3 text-xs text-on-surface-variant">até</span>
          <label className="block text-xs text-on-surface-variant">
            Valor máximo
            <input
              value={draft.maxReais}
              onChange={(event) =>
                setDraft({ ...draft, maxReais: event.target.value })
              }
              inputMode="decimal"
              placeholder="R$ 500,00"
              className={fieldClass}
              data-pm-search-max
            />
          </label>
        </div>
      </div>

      <div className="flex flex-col gap-2 pt-1">
        <button
          type="button"
          onClick={onApply}
          data-pm-search-apply
          className="btn-lux btn-lux-primary inline-flex w-full items-center justify-center gap-2 rounded-full py-3 text-sm font-semibold text-on-primary"
        >
          <Icon name="check" size={16} />
          Aplicar filtros
        </button>
        <button
          type="button"
          onClick={onClear}
          data-pm-search-clear
          className="inline-flex w-full items-center justify-center rounded-full border border-outline/50 bg-white py-3 text-sm font-semibold text-on-surface"
        >
          Limpar filtros
        </button>
      </div>
    </div>
  );
}

export function SearchResultsView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [, startTransition] = useTransition();
  const filters = useMemo(
    () => parseSearchFilters(searchParams),
    [searchParams],
  );
  const [draftQ, setDraftQ] = useState(filters.q);
  const [draft, setDraft] = useState(() => draftFromFilters(filters));
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    setDraftQ(filters.q);
    setDraft(draftFromFilters(filters));
  }, [filters]);

  useEffect(() => {
    if (!drawerOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setDrawerOpen(false);
    };
    document.addEventListener("keydown", onKey);
    document.documentElement.classList.add("overflow-hidden");
    return () => {
      document.removeEventListener("keydown", onKey);
      document.documentElement.classList.remove("overflow-hidden");
    };
  }, [drawerOpen]);

  const areaOptions = useMemo(
    () => searchAreaOptions(draft.audience, products),
    [draft.audience],
  );

  const results = useMemo(
    () => filterSearchProducts(products, filters),
    [filters],
  );
  const visible = useMemo(
    () => new Set(results.map((item) => item.id)),
    [results],
  );
  const activeCount = countActiveSearchFilters(filters);

  const sortedUnits = useMemo(
    () =>
      [...storeUnits].sort(
        (a, b) =>
          a.state.localeCompare(b.state) || a.name.localeCompare(b.name, "pt-BR"),
      ),
    [],
  );

  function push(next: Partial<SearchFilters> & { q?: string }) {
    const href = buildSearchHref({ ...filters, ...next });
    startTransition(() => {
      router.push(href);
    });
  }

  function applyDraft(closeDrawer = false) {
    push({
      audience: draft.audience,
      categories: draft.categories,
      category: draft.categories[0] || "",
      method: draft.method,
      min: parseReais(draft.minReais),
      max: parseReais(draft.maxReais),
      sessions: draft.sessions,
      unit: draft.unit,
      promo: draft.promo,
    });
    if (closeDrawer) setDrawerOpen(false);
  }

  function clearFilters() {
    const cleared = emptySearchFilters({ q: filters.q, sort: filters.sort });
    setDraft(draftFromFilters(cleared));
    push(cleared);
    setDrawerOpen(false);
  }

  function quickPatch(next: Partial<DraftState>) {
    const merged = { ...draft, ...next };
    setDraft(merged);
    push({
      audience: merged.audience,
      categories: merged.categories,
      category: merged.categories[0] || "",
      method: merged.method,
      min: parseReais(merged.minReais),
      max: parseReais(merged.maxReais),
      sessions: merged.sessions,
      unit: merged.unit,
      promo: merged.promo,
    });
  }

  return (
    <main
      className="mx-auto w-full max-w-7xl px-container-margin py-8 md:py-12"
      data-pm-search-page
    >
      <nav className="text-xs text-on-surface-variant">
        <Link
          href={homeHref(homeAudience(filters.audience))}
          className="hover:text-primary"
        >
          Início
        </Link>
        <span className="px-2">/</span>
        <span className="text-primary">Busca</span>
      </nav>

      <h1 className="mt-6 font-[family-name:var(--font-display)] text-headline-md text-primary md:text-headline-lg">
        Encontre o tratamento ideal
      </h1>
      {filters.q ? (
        <p className="mt-2 text-sm text-on-surface-variant" data-pm-search-query-label>
          Resultados para “{filters.q}”
        </p>
      ) : (
        <p className="mt-2 text-sm text-on-surface-variant">
          Filtre por região, sessões, unidade ou promoção.
        </p>
      )}

      <form
        className="sticky top-[154px] z-30 mt-6 flex flex-col gap-3 bg-background/95 py-3 backdrop-blur-md sm:flex-row sm:items-center md:top-[164px]"
        action="/busca"
        method="get"
        onSubmit={(event) => {
          event.preventDefault();
          push({ q: draftQ });
        }}
      >
        <div className="flex min-w-0 flex-1 items-center gap-3 rounded-full border border-primary/20 bg-surface-container-low px-4 py-3">
          <Icon name="search" size={20} className="shrink-0 text-primary" />
          <input
            name="q"
            value={draftQ}
            onChange={(event) => setDraftQ(event.target.value)}
            placeholder="Buscar axila, virilha, laser, cera..."
            className="w-full bg-transparent text-base text-on-surface outline-none placeholder:text-on-surface-variant"
            data-pm-search-input
          />
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            className="inline-flex flex-1 items-center justify-center gap-2 rounded-full border border-primary/30 bg-white px-4 py-3 text-sm font-semibold text-primary md:hidden"
            data-pm-search-open-drawer
            onClick={() => setDrawerOpen(true)}
          >
            <Icon name="sliders" size={16} />
            Filtros
            <span
              className={`rounded-full bg-primary px-2 py-0.5 text-[11px] text-on-primary${activeCount ? "" : " hidden"}`}
              data-pm-search-filter-count
            >
              {activeCount || 0}
            </span>
          </button>
          <button
            type="submit"
            className="btn-lux btn-lux-primary rounded-full px-6 py-3 text-sm font-semibold text-on-primary"
          >
            Buscar
          </button>
        </div>
      </form>

      <style>{`
        [data-pm-search-layout]{display:grid;gap:2rem;align-items:start}
        @media (min-width:768px){
          [data-pm-search-layout]{grid-template-columns:240px minmax(0,1fr)}
          [data-pm-search-sidebar]{display:block!important;position:sticky;top:180px}
          [data-pm-search-open-drawer]{display:none!important}
          [data-pm-search-drawer]{display:none!important}
        }
        @media (min-width:1024px){
          [data-pm-search-layout]{grid-template-columns:280px minmax(0,1fr)}
        }
      `}</style>
      <div
        className="mt-8 grid gap-8 md:grid-cols-[240px_minmax(0,1fr)] lg:grid-cols-[280px_minmax(0,1fr)]"
        data-pm-search-layout
      >
        <aside
          className="hidden rounded-2xl border border-outline/40 bg-white/95 p-5 md:sticky md:top-[180px] md:block md:self-start"
          data-pm-search-sidebar
        >
          <div className="mb-5 flex items-center justify-between">
            <p className="font-label-md text-label-md text-primary uppercase">
              Filtros
            </p>
            <Icon name="sliders" size={18} className="text-primary" />
          </div>
          <FiltersForm
            idPrefix="desk"
            draft={draft}
            setDraft={setDraft}
            areaOptions={areaOptions}
            onApply={() => applyDraft(false)}
            onClear={clearFilters}
          />
        </aside>

        <section className="min-w-0">
          <div className="text-left" data-pm-search-quick>
            <p className="font-label-md text-label-md text-primary uppercase">
              Filtros rápidos
            </p>
            <div className="mt-3 flex flex-wrap justify-start gap-2">
              <label className="relative shrink-0">
                <span className="sr-only">Região do corpo</span>
                <select
                  className={`${chipClass} appearance-none border-primary/25 bg-white pr-9 text-on-surface`}
                  value={filters.categories[0] || ""}
                  data-pm-search-quick-region
                  onChange={(event) => {
                    const value = event.target.value;
                    quickPatch({
                      categories: value ? [value] : [],
                    });
                  }}
                >
                  <option value="">Região do corpo</option>
                  {searchAreaOptions(filters.audience, products).map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.label}
                    </option>
                  ))}
                </select>
                <Icon
                  name="chevronDown"
                  size={14}
                  className="pointer-events-none absolute top-1/2 right-3 -translate-y-1/2 text-primary"
                />
              </label>

              <label className="relative shrink-0">
                <span className="sr-only">Quantidade de sessões</span>
                <select
                  className={`${chipClass} appearance-none border-primary/25 bg-white pr-9 text-on-surface`}
                  value={filters.sessions}
                  data-pm-search-quick-sessions
                  onChange={(event) =>
                    quickPatch({
                      sessions: event.target.value as SearchSessions,
                    })
                  }
                >
                  <option value="">Quantidade de sessões</option>
                  <option value="avulso">Avulso</option>
                  <option value="pacote">Pacote (sessões)</option>
                </select>
                <Icon
                  name="chevronDown"
                  size={14}
                  className="pointer-events-none absolute top-1/2 right-3 -translate-y-1/2 text-primary"
                />
              </label>

              <label className="relative shrink-0">
                <span className="sr-only">Unidade</span>
                <select
                  className={`${chipClass} max-w-[220px] appearance-none border-primary/25 bg-white pr-9 text-on-surface`}
                  value={filters.unit}
                  data-pm-search-quick-unit
                  onChange={(event) => quickPatch({ unit: event.target.value })}
                >
                  <option value="">Unidade</option>
                  {sortedUnits.map((unit) => (
                    <option key={unit.id} value={unit.id}>
                      {unit.name} ({unit.state})
                    </option>
                  ))}
                </select>
                <Icon
                  name="chevronDown"
                  size={14}
                  className="pointer-events-none absolute top-1/2 right-3 -translate-y-1/2 text-primary"
                />
              </label>

              <button
                type="button"
                data-pm-search-quick-promo
                onClick={() => quickPatch({ promo: !filters.promo })}
                className={`${chipClass} ${
                  filters.promo
                    ? "border-primary bg-primary text-on-primary"
                    : "border-primary/25 bg-white text-on-surface"
                }`}
              >
                <Icon name="badgePercent" size={15} />
                Promoções
              </button>
            </div>
          </div>

          <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <h2
              className="text-left font-[family-name:var(--font-display)] text-xl text-on-surface"
              data-pm-search-count
            >
              Tratamentos ({results.length})
            </h2>
            <label className="text-left text-sm text-on-surface-variant sm:min-w-[200px]">
              Ordenar
              <select
                className={fieldClass}
                value={filters.sort}
                data-pm-search-sort
                onChange={(event) =>
                  push({ sort: event.target.value as SearchSort })
                }
              >
                <option value="relevance">Relevância</option>
                <option value="name">Nome A–Z</option>
                <option value="price-asc">Menor preço</option>
                <option value="price-desc">Maior preço</option>
              </select>
            </label>
          </div>

          <p
            className={`mt-8 text-left text-sm text-on-surface-variant${results.length ? " hidden" : ""}`}
            data-pm-search-empty
          >
            Nenhum tratamento encontrado
            {filters.q ? ` para “${filters.q}”` : ""}. Tente outro termo ou limpe
            os filtros.
          </p>

          <div
            className={`mt-5 grid gap-5 sm:grid-cols-2 xl:grid-cols-3${results.length ? "" : " hidden"}`}
            data-pm-search-grid
          >
            {products.map((product) => {
              const parcel = getInstallment(product.priceCents, product.method);
              const comingSoon = isComingSoon(product.id);
              const show = visible.has(product.id);
              const promo = productHasPromo(product);
              const sessions = sessionBucket(product);
              const unitIds = unitsForProduct(product)
                .map((unit) => unit.id)
                .join(",");
              return (
                <article
                  key={product.id}
                  data-pm-search-card
                  data-audience={product.audience}
                  data-category={product.category}
                  data-method={product.method}
                  data-price-cents={product.priceCents}
                  data-sessions={sessions}
                  data-promo={promo ? "1" : "0"}
                  data-units={unitIds}
                  data-name={product.name.toLowerCase()}
                  data-haystack={[
                    product.name,
                    product.sku,
                    product.code,
                    product.category,
                    product.method,
                    product.description,
                    product.duration,
                    product.badge || "",
                  ]
                    .join(" ")
                    .toLowerCase()}
                  data-coming-soon={comingSoon ? "1" : undefined}
                  className={`group overflow-hidden rounded-2xl bg-surface shadow-[0_18px_40px_rgba(58,10,60,0.08)]${comingSoon ? " opacity-90" : ""}${show ? "" : " hidden"}`}
                >
                  <Link href={`/produto/${product.id}`} className="block">
                    <div className="relative aspect-[4/5] overflow-hidden bg-surface-container-high">
                      <Image
                        src={product.image}
                        alt={product.imageAlt}
                        fill
                        className={`object-cover object-center transition-transform duration-700 group-hover:scale-105${comingSoon ? " grayscale" : ""}`}
                        sizes="(max-width: 640px) 92vw, (max-width: 1024px) 45vw, 25vw"
                      />
                      {comingSoon ? <ComingSoonOverlay /> : null}
                      {product.badge ? (
                        <div className="absolute top-3 left-3 z-20">
                          <BadgeTag label={product.badge} />
                        </div>
                      ) : null}
                    </div>
                  </Link>
                  <div className="flex flex-col gap-2 p-4">
                    <Link href={`/produto/${product.id}`}>
                      <h3 className="font-[family-name:var(--font-display)] text-lg leading-snug text-on-surface">
                        {product.name}
                      </h3>
                    </Link>
                    <div className="flex items-center gap-1.5 text-xs text-on-surface-variant">
                      <Icon name="clock" size={14} />
                      {product.duration}
                    </div>
                    <div className="mt-1 flex flex-wrap items-baseline gap-2">
                      {parcel.times > 1 ? (
                        <>
                          <span className="text-lg font-semibold text-primary">
                            {parcel.times}x {formatBRL(parcel.installmentCents)}
                          </span>
                          <span className="text-xs text-on-surface-variant">
                            {formatBRL(product.priceCents)}
                          </span>
                        </>
                      ) : (
                        <span className="text-lg font-semibold text-primary">
                          {formatBRL(product.priceCents)}
                        </span>
                      )}
                      {product.oldPriceCents ? (
                        <span className="text-xs text-on-surface-variant line-through">
                          {formatBRL(product.oldPriceCents)}
                        </span>
                      ) : null}
                    </div>
                    {comingSoon ? (
                      <span className="mt-2 inline-flex w-full items-center justify-center gap-2 rounded-full border border-outline/40 bg-surface-container-low py-2.5 text-xs font-semibold tracking-wide text-on-surface-variant uppercase">
                        <Icon name="clock" size={15} />
                        Em breve · {BODY_SPLASH_LAUNCH_LABEL}
                      </span>
                    ) : (
                      <Link
                        href={`/produto/${product.id}`}
                        className="mt-2 inline-flex w-full items-center justify-center gap-2 py-2 text-sm font-semibold text-primary underline-offset-4 hover:underline"
                      >
                        Ver detalhes
                      </Link>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      </div>

      <div
        className={`fixed inset-0 z-[90] md:hidden${drawerOpen ? "" : " hidden"}`}
        data-pm-search-drawer
        role="dialog"
        aria-modal="true"
        aria-label="Filtros de busca"
      >
        <button
          type="button"
          className="absolute inset-0 bg-black/45"
          aria-label="Fechar filtros"
          onClick={() => setDrawerOpen(false)}
        />
        <div className="absolute inset-x-0 bottom-0 max-h-[92vh] overflow-y-auto rounded-t-3xl bg-white p-5 pb-8 shadow-2xl">
          <div className="mb-5 flex items-center justify-between">
            <p className="font-label-md text-label-md text-primary uppercase">
              Filtros
            </p>
            <button
              type="button"
              aria-label="Fechar"
              onClick={() => setDrawerOpen(false)}
              className="rounded-full border border-outline/40 p-2 text-on-surface"
            >
              <Icon name="close" size={18} />
            </button>
          </div>
          <FiltersForm
            idPrefix="mob"
            draft={draft}
            setDraft={setDraft}
            areaOptions={areaOptions}
            onApply={() => applyDraft(true)}
            onClear={clearFilters}
          />
        </div>
      </div>

      {/* Hidden category option banks kept for WP mirror compatibility */}
      <select
        className="hidden"
        data-pm-search-category-options
        data-audience="feminino"
        aria-hidden="true"
        tabIndex={-1}
      >
        <option value="">Todas as áreas</option>
        {searchAreaOptions("feminino", products).map((item) => (
          <option key={item.id} value={item.id}>
            {item.label}
          </option>
        ))}
      </select>
      <select
        className="hidden"
        data-pm-search-category-options
        data-audience="masculino"
        aria-hidden="true"
        tabIndex={-1}
      >
        <option value="">Todas as áreas</option>
        {searchAreaOptions("masculino", products).map((item) => (
          <option key={item.id} value={item.id}>
            {item.label}
          </option>
        ))}
      </select>
      <select
        className="hidden"
        data-pm-search-category-options
        data-audience="todos"
        aria-hidden="true"
        tabIndex={-1}
      >
        <option value="">Todas as áreas</option>
        {searchAreaOptions("todos", products).map((item) => (
          <option key={item.id} value={item.id}>
            {item.label}
          </option>
        ))}
      </select>
    </main>
  );
}
