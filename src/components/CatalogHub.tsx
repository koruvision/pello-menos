import Image from "next/image";
import Link from "next/link";
import { Icon } from "@/components/Icon";
import {
  homeHref,
  type ProductAudience,
} from "@/lib/data";

export type CatalogHubCard = {
  href: string;
  label: string;
  subtitle: string;
  image: string;
};

type Props = {
  audience: ProductAudience;
  eyebrow: string;
  title: string;
  subtitle: string;
  cards: CatalogHubCard[];
};

export function CatalogHub({ audience, eyebrow, title, subtitle, cards }: Props) {
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
      <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((card) => (
          <Link
            key={card.href}
            href={card.href}
            className="group overflow-hidden rounded-2xl bg-surface shadow-[0_18px_40px_rgba(58,10,60,0.08)]"
          >
            <div className="relative aspect-[4/5] bg-surface-container-high">
              <Image
                src={card.image}
                alt={card.label}
                fill
                className="object-cover transition-transform duration-700 group-hover:scale-105"
                sizes="(max-width: 640px) 92vw, (max-width: 1024px) 45vw, 25vw"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/10 to-transparent" />
              <div className="absolute inset-x-0 bottom-0 p-5 text-white">
                <h2 className="font-[family-name:var(--font-display)] text-2xl">
                  {card.label}
                </h2>
                <p className="mt-1 text-sm text-white/80">{card.subtitle}</p>
                <span className="mt-3 inline-flex items-center gap-1 text-xs font-semibold tracking-wide uppercase">
                  Ver
                  <Icon name="arrowRight" size={14} />
                </span>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </main>
  );
}
