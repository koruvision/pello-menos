"use client";

import Image from "next/image";
import Link from "next/link";
import { Icon } from "@/components/Icon";

type Props = {
  id?: string;
  eyebrow: string;
  title: string;
  subtitle: string;
  image: string;
  imageAlt: string;
  ctaHref?: string;
  ctaLabel?: string;
  price?: string;
  oldPrice?: string;
  textSide?: "left" | "right";
};

export function SplitOffer({
  id,
  eyebrow,
  title,
  subtitle,
  image,
  imageAlt,
  ctaHref,
  ctaLabel,
  price,
  oldPrice,
  textSide = "left",
}: Props) {
  const textOnRight = textSide === "right";

  return (
    <section id={id} className="js-reveal mx-auto max-w-7xl scroll-mt-24 px-container-margin py-8">
      <div className="group relative overflow-hidden rounded-3xl bg-primary text-on-primary">
        <div className="relative min-h-[340px] md:min-h-[400px] lg:min-h-[440px]">
          <Image
            src={image}
            alt={imageAlt}
            fill
            className={`object-cover transition-transform duration-700 group-hover:scale-[1.03] ${
              textOnRight
                ? "object-left md:object-[24%_center]"
                : "object-[68%_center] md:object-[62%_center]"
            }`}
            sizes="(max-width: 768px) 100vw, 1280px"
          />
          {textOnRight ? (
            <div className="absolute inset-0 bg-[linear-gradient(to_right,transparent_0%,transparent_40%,rgb(112_0_83_/_0.5)_64%,var(--brand-primary)_100%)]" />
          ) : (
            <>
              <div className="absolute inset-0 bg-gradient-to-b from-primary via-primary/75 to-primary/20 md:hidden" />
              <div className="absolute inset-0 hidden bg-gradient-to-r from-primary from-0% via-primary/92 via-[36%] to-transparent to-[78%] md:block" />
              <div className="absolute inset-0 hidden bg-gradient-to-r from-primary/50 via-transparent to-transparent md:block" />
            </>
          )}
          <div
            className={`absolute inset-0 z-10 flex min-h-[340px] flex-col justify-center px-6 py-10 md:min-h-[400px] md:px-12 lg:min-h-[440px] lg:px-14 ${
              textOnRight ? "items-end text-right" : "items-start"
            }`}
          >
            <div className="max-w-xl">
              <p className="font-label-md text-label-md text-secondary-container uppercase">
                {eyebrow}
              </p>
              <h2 className="mt-2 font-[family-name:var(--font-display)] text-headline-md drop-shadow-[0_8px_24px_rgba(0,0,0,0.35)] md:text-headline-lg">
                {title}
              </h2>
              <p className="mt-2 max-w-md text-on-primary/85">{subtitle}</p>
              {price ? (
                <div className={`mt-4 flex flex-wrap items-baseline gap-2 ${textOnRight ? "justify-end" : ""}`}>
                  <span className="font-[family-name:var(--font-display)] text-3xl text-secondary-container">
                    {price}
                  </span>
                  {oldPrice ? (
                    <span className="text-sm text-on-primary/55 line-through">
                      {oldPrice}
                    </span>
                  ) : null}
                </div>
              ) : null}
              {ctaHref && ctaLabel ? (
                <Link
                  href={ctaHref}
                  className={`btn-lux btn-lux-gold mt-6 inline-flex w-fit items-center gap-2 rounded-full px-7 py-3 font-label-md text-label-md text-on-secondary-container uppercase ${
                    textOnRight ? "ml-auto" : ""
                  }`}
                >
                  {ctaLabel}
                  <Icon name="arrowRight" size={16} />
                </Link>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
