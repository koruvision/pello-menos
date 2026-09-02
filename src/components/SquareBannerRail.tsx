"use client";

import Image from "next/image";
import { BadgeTag } from "@/components/BadgeTag";
import { CarouselArrows } from "@/components/CarouselArrows";
import { useCardCarousel } from "@/lib/carousel";
import type { SquareBannerData } from "@/lib/data";

type Props = {
  banners: SquareBannerData[];
  productsHref: string;
};

export function SquareBannerRail({ banners, productsHref }: Props) {
  const { scroller, scrollByCard } = useCardCarousel();

  return (
    <section className="js-reveal relative py-6">
      <div className="mx-auto mb-5 max-w-7xl px-container-margin">
        <h2 className="font-[family-name:var(--font-display)] text-headline-md text-primary">
          Em destaque
        </h2>
      </div>
      <div className="relative mx-auto max-w-7xl px-12 sm:px-14 md:px-16">
        <CarouselArrows
          prevLabel="Anterior"
          nextLabel="Próximo"
          onPrev={() => scrollByCard(-1)}
          onNext={() => scrollByCard(1)}
        />
        <div ref={scroller} className="carousel-track carousel-track--square hide-scrollbar pb-2">
          {banners.map((banner) => (
            <a
              key={banner.id}
              href={productsHref}
              data-carousel-card
              data-square-banner
              className="carousel-card group relative aspect-square overflow-hidden rounded-2xl"
            >
              <div data-carousel-media className="absolute inset-0">
                <Image
                  src={banner.image}
                  alt={banner.imageAlt}
                  fill
                  className="object-cover transition-transform duration-700 group-hover:scale-105"
                  style={{ objectPosition: banner.imagePosition ?? "50% 28%" }}
                  sizes="(max-width: 640px) 72vw, (max-width: 1024px) 50vw, 33vw"
                />
              </div>
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
              <div className="absolute inset-x-0 bottom-0 p-5 text-on-primary">
                {banner.badge ? (
                  <BadgeTag label={banner.badge} className="mb-2" />
                ) : null}
                <h3 className="font-[family-name:var(--font-display)] text-2xl">
                  {banner.title}
                </h3>
                <p className="mt-1 text-sm text-on-primary/80">{banner.subtitle}</p>
              </div>
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}
