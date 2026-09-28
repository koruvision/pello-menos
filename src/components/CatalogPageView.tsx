import Image from "next/image";
import Link from "next/link";
import { BadgeTag } from "@/components/BadgeTag";
import { Icon } from "@/components/Icon";
import {
  formatBRL,
  getInstallment,
  homeHref,
  type Product,
  type ProductAudience,
} from "@/lib/data";

type Props = {
  audience: ProductAudience;
  eyebrow: string;
  title: string;
  subtitle: string;
  items: Product[];
};

export function CatalogPageView({
  audience,
  eyebrow,
  title,
  subtitle,
  items,
}: Props) {
  return (
    <main className="mx-auto max-w-7xl px-container-margin py-8 md:py-12">
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

      {items.length === 0 ? (
        <p className="mt-12 text-sm text-on-surface-variant">
          Nenhum item nesta categoria por enquanto.
        </p>
      ) : (
        <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {items.map((product) => {
            const parcel = getInstallment(product.priceCents, product.method);
            return (
              <article
                key={product.id}
                className="group overflow-hidden rounded-2xl bg-surface shadow-[0_18px_40px_rgba(58,10,60,0.08)]"
              >
                <Link href={`/produto/${product.id}`} className="block">
                  <div className="relative aspect-[4/5] overflow-hidden bg-surface-container-high">
                    <Image
                      src={product.image}
                      alt={product.imageAlt}
                      fill
                      className="object-cover object-center transition-transform duration-700 group-hover:scale-105"
                      sizes="(max-width: 640px) 92vw, (max-width: 1024px) 45vw, 25vw"
                    />
                    {product.badge ? (
                      <div className="absolute top-3 left-3">
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
                  <Link
                    href={`/produto/${product.id}`}
                    className="btn-lux btn-lux-primary mt-2 inline-flex w-full items-center justify-center gap-2 rounded-full py-2.5 text-xs font-semibold tracking-wide text-on-primary uppercase"
                  >
                    <Icon name="shoppingBag" size={15} />
                    Ver produto
                  </Link>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </main>
  );
}
