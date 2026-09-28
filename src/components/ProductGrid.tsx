"use client";

import Image from "next/image";
import Link from "next/link";
import { CarouselArrows } from "@/components/CarouselArrows";
import { Icon } from "@/components/Icon";
import { BadgeTag } from "@/components/BadgeTag";
import { useCardCarousel } from "@/lib/carousel";
import { formatBRL, getInstallment, type Product } from "@/lib/data";

type Props = {
  id?: string;
  eyebrow: string;
  title: string;
  subtitle: string;
  items: Product[];
  muted?: boolean;
};

export function ProductGrid({
  id,
  eyebrow,
  title,
  subtitle,
  items,
  muted = false,
}: Props) {
  const { scroller, scrollByCard } = useCardCarousel();

  return (
    <section
      id={id}
      className={`js-reveal relative scroll-mt-24 py-12 ${muted ? "bg-surface-container-low" : "bg-background"}`}
    >
      <div className="mx-auto mb-8 max-w-7xl px-container-margin">
        <p className="font-label-md text-label-md text-primary uppercase">
          {eyebrow}
        </p>
        <h2 className="mt-2 font-[family-name:var(--font-display)] text-headline-md text-primary md:text-headline-lg">
          {title}
        </h2>
        <p className="mt-1 text-on-surface-variant">{subtitle}</p>
      </div>

      <div className="relative mx-auto max-w-7xl px-12 sm:px-14 md:px-16">
        <CarouselArrows
          prevLabel="Produtos anteriores"
          nextLabel="Próximos produtos"
          onPrev={() => scrollByCard(-1)}
          onNext={() => scrollByCard(1)}
        />

        <div ref={scroller} className="carousel-track hide-scrollbar pb-4">
          {items.map((product) => (
            <article
              key={product.id}
              data-carousel-card
              data-product-card
              className="carousel-card group overflow-hidden rounded-2xl bg-surface shadow-[0_18px_40px_rgba(58,10,60,0.08)]"
            >
              <Link href={`/produto/${product.id}`} className="block">
                <div
                  data-carousel-media
                  className="relative aspect-[4/5] overflow-hidden bg-surface-container-high"
                >
                  <Image
                    src={product.image}
                    alt={product.imageAlt}
                    fill
                    className="object-cover object-center transition-transform duration-700 group-hover:scale-105"
                    sizes="(max-width: 640px) 78vw, (max-width: 768px) 50vw, (max-width: 1024px) 33vw, 25vw"
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
                  <h3 className="font-[family-name:var(--font-display)] text-lg leading-snug text-on-surface">
                    {product.name}
                  </h3>
                </Link>
                <div className="flex items-center gap-1.5 text-xs text-on-surface-variant">
                  <Icon name="clock" size={14} />
                  {product.duration}
                </div>
                <div className="mt-1 flex flex-wrap items-baseline gap-2">
                  {(() => {
                    const parcel = getInstallment(
                      product.priceCents,
                      product.method,
                    );
                    return parcel.times > 1 ? (
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
                    );
                  })()}
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
          ))}
        </div>
      </div>
    </section>
  );
}
