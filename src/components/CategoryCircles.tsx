"use client";

import Image from "next/image";
import type { Category } from "@/lib/data";

type Props = {
  items: Category[];
};

export function CategoryCircles({ items }: Props) {
  return (
    <section className="mx-auto max-w-7xl overflow-x-auto px-container-margin py-10 hide-scrollbar">
      <div className="js-cats flex min-w-max justify-start gap-6 md:justify-center md:gap-10">
        {items.map((category) => (
          <a
            key={category.id}
            href={category.href}
            className="js-cat group flex w-[84px] flex-col items-center gap-3 md:w-[104px]"
          >
            <div className="relative h-[72px] w-[72px] overflow-hidden rounded-full border-2 border-secondary-container/70 shadow-[0_10px_30px_color-mix(in_srgb,var(--color-primary)_16%,transparent)] transition-transform group-hover:scale-105 md:h-20 md:w-20">
              <Image
                src={category.image}
                alt={category.label}
                fill
                className="object-cover object-[center_30%]"
                sizes="80px"
              />
            </div>
            <span className="text-center text-sm font-medium text-on-surface">
              {category.label}
            </span>
          </a>
        ))}
      </div>
    </section>
  );
}
