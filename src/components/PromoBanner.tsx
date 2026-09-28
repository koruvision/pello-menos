"use client";

import { BadgeTag } from "@/components/BadgeTag";
import { BannerCover } from "@/components/BannerCover";
import type { PromoBannerData } from "@/lib/data";

export function PromoBanner({ banner }: { banner: PromoBannerData }) {
  const textOnRight = banner.textSide === "right";
  const purple = banner.overlay === "purple";

  const overlayClass = purple
    ? textOnRight
      ? "bg-gradient-to-r from-transparent via-primary/35 to-primary/80"
      : "bg-gradient-to-r from-primary/80 via-primary/35 to-transparent"
    : "bg-gradient-to-r from-black/55 via-black/15 to-transparent";

  const copy = (
    <>
      <BadgeTag label={banner.badge} size="md" className="mb-3" />
      <h3 className="font-[family-name:var(--font-display)] text-headline-md md:text-headline-lg">
        {banner.title}
      </h3>
      <p className="mt-2 max-w-lg text-sm text-on-primary/85 md:text-base">
        {banner.subtitle}
      </p>
    </>
  );

  return (
    <section className="js-reveal mx-auto max-w-7xl px-container-margin py-4">
      <div className="group relative aspect-[4/5] overflow-hidden rounded-3xl md:aspect-auto md:h-[360px] lg:h-[420px]">
        <BannerCover
          src={banner.image}
          srcMobile={banner.imageMobile}
          alt={banner.imageAlt}
          position={banner.imagePosition ?? (textOnRight ? "32% 40%" : "50% 38%")}
          positionMobile={banner.imagePositionMobile}
          className="transition-transform duration-700 group-hover:scale-105"
          sizes="(max-width: 768px) 100vw, 1280px"
        />
        <div className={`absolute inset-0 ${overlayClass}`} />
        <div
          className={`relative z-10 flex h-full flex-col justify-center px-6 text-on-primary md:px-12 ${
            textOnRight ? "items-end text-right" : ""
          }`}
        >
          <div className={textOnRight ? "max-w-lg" : ""}>{copy}</div>
        </div>
      </div>
    </section>
  );
}
