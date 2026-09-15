"use client";

import { Icon } from "@/components/Icon";
import { googleBusiness, googleReviews as defaultReviews, type Review } from "@/lib/data";

type Props = {
  reviews?: Review[];
};

export function GoogleReviews({ reviews = defaultReviews }: Props) {
  return (
    <section className="js-reveal bg-surface py-14">
      <div className="mx-auto max-w-7xl px-container-margin">
        <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="font-label-md text-label-md text-secondary uppercase">
              Google Meu Negócio
            </p>
            <h2 className="mt-2 font-[family-name:var(--font-display)] text-headline-md text-primary md:text-headline-lg">
              O que dizem no Google
            </h2>
          </div>
          <div className="flex items-center gap-4 rounded-2xl border border-outline/50 bg-background px-5 py-4">
            <span className="flex h-11 w-11 items-center justify-center rounded-full bg-white text-lg font-bold text-[#4285F4] shadow-sm">
              G
            </span>
            <div>
              <p className="font-semibold text-on-surface">{googleBusiness.name}</p>
              <div className="mt-0.5 flex items-center gap-2 text-sm">
                <span className="font-bold text-primary">
                  {googleBusiness.rating}
                </span>
                <span className="flex text-[#FABB05]">
                  {Array.from({ length: 5 }).map((_, index) => (
                    <Icon key={index} name="star" size={14} filled />
                  ))}
                </span>
                <span className="text-on-surface-variant">
                  {googleBusiness.count} avaliações
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 flex snap-x snap-mandatory gap-4 overflow-x-auto overscroll-x-contain pb-2 hide-scrollbar">
          {reviews.map((review) => (
            <article
              key={review.id}
              className="w-[min(82vw,340px)] shrink-0 snap-start snap-always rounded-2xl border border-outline/40 bg-background p-5 shadow-[0_12px_30px_rgba(58,10,60,0.06)] sm:w-[calc((100%-16px)/2)] lg:w-[calc((100%-32px)/3)]"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-semibold text-on-surface">{review.name}</p>
                  <p className="text-xs text-on-surface-variant">{review.time}</p>
                </div>
                <span className="text-xs font-bold text-[#4285F4]">Google</span>
              </div>
              <div className="mt-3 flex text-[#FABB05]">
                {Array.from({ length: 5 }).map((_, index) => (
                  <Icon
                    key={index}
                    name="star"
                    size={14}
                    filled={index < review.rating}
                  />
                ))}
              </div>
              <p className="mt-3 text-sm leading-relaxed text-on-surface-variant">
                {review.text}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
