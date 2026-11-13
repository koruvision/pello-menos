import Image from "next/image";
import Link from "next/link";
import { BadgeTag } from "@/components/BadgeTag";
import { ComingSoonOverlay } from "@/components/ComingSoonOverlay";
import { Icon } from "@/components/Icon";
import {
  BODY_SPLASH_LAUNCH_LABEL,
  formatBRL,
  getInstallment,
  homeHref,
  isComingSoon,
  type Product,
  type ProductAudience,
} from "@/lib/data";

type Filter = { id: string; label: string };

type Props = {
  audience: ProductAudience;
  eyebrow: string;
  title: string;
  subtitle: string;
  items: Product[];
  filters?: Filter[];
  audienceFilters?: Filter[];
  defaultAudience?: ProductAudience;
};

const activeFilter =
  "rounded-full bg-primary px-4 py-2 text-sm font-semibold text-on-primary";
const idleFilter =
  "rounded-full border border-primary/25 px-4 py-2 text-sm text-primary";

export function CatalogPageView({
  audience,
  eyebrow,
  title,
  subtitle,
  items,
  filters,
  audienceFilters,
  defaultAudience,
}: Props) {
  return (
    <main className="mx-auto w-full max-w-7xl px-container-margin py-8 md:py-12">
      <nav className="text-xs text-on-surface-variant">
        <Link href={homeHref(audience)} className="hover:text-primary">
          Início
        </Link>
        <span className="px-2">/</span>
        <span className="text-primary">{title}</span>
      </nav>
      <p className="mt-6 font-label-md text-label-md text-primary uppercase">
        {eyebrow}
      </p>
      <h1 className="mt-2 font-[family-name:var(--font-display)] text-headline-md text-primary md:text-headline-lg">
        {title}
      </h1>
      <p className="mt-2 max-w-2xl text-on-surface-variant">{subtitle}</p>

      {audienceFilters && audienceFilters.length > 0 ? (
        <div className="mt-6 flex flex-wrap gap-2">
          {audienceFilters.map((item) => {
            const on = (defaultAudience ?? audienceFilters[0]?.id) === item.id;
            return (
              <button
                key={item.id}
                type="button"
                data-audience-filter={item.id}
                aria-pressed={on}
                className={on ? activeFilter : idleFilter}
              >
                {item.label}
              </button>
            );
          })}
        </div>
      ) : null}

      {filters && filters.length > 0 ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {filters.map((item) => {
            const on = item.id === "todos";
            return (
              <button
                key={item.id}
                type="button"
                data-home-filter={item.id}
                className={on ? activeFilter : idleFilter}
              >
                {item.label}
              </button>
            );
          })}
        </div>
      ) : null}

      {items.length === 0 ? (
        <p className="mt-12 text-sm text-on-surface-variant">
          Nenhum item nesta categoria por enquanto.
        </p>
      ) : (
        <>
        <p data-catalog-empty className="mt-12 hidden text-sm text-on-surface-variant">
          Nenhum item neste filtro.
        </p>
        <div data-catalog-grid className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {items.map((product) => {
            const parcel = getInstallment(product.priceCents, product.method);
            const cardAudience = product.audience;
            const startHidden = Boolean(defaultAudience) && cardAudience !== defaultAudience;
            const comingSoon = isComingSoon(product.id);
            return (
              <article
                key={product.id}
                data-home-panel={product.method}
                data-audience={cardAudience}
                data-coming-soon={comingSoon ? "1" : undefined}
                className={`group overflow-hidden rounded-2xl bg-surface shadow-[0_18px_40px_rgba(58,10,60,0.08)]${startHidden ? " hidden" : ""}${comingSoon ? " opacity-90" : ""}`}
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
                    <h2 className="font-[family-name:var(--font-display)] text-lg leading-snug text-on-surface">
                      {product.name}
                    </h2>
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
                      className="btn-lux btn-lux-primary mt-2 inline-flex w-full items-center justify-center gap-2 rounded-full py-2.5 text-xs font-semibold tracking-wide text-on-primary uppercase"
                    >
                      <Icon name="shoppingBag" size={15} />
                      Ver produto
                    </Link>
                  )}
                </div>
              </article>
            );
          })}
        </div>
        </>
      )}
    </main>
  );
}
