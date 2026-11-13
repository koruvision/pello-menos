"use client";

import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { audienceFromPath, catalogImage } from "@/lib/data";

gsap.registerPlugin(useGSAP);

const femalePurchases = [
  {
    name: "Camila R.",
    city: "Copacabana, RJ",
    product: "Axilas Laser",
    href: "/produto/axilas-laser",
    image: catalogImage("axilas-laser"),
    when: "há 2 minutos",
  },
  {
    name: "Juliana M.",
    city: "Tijuca, RJ",
    product: "Virilha Total Laser",
    href: "/produto/virilha-laser",
    image: catalogImage("virilha-laser"),
    when: "há 6 minutos",
  },
  {
    name: "Fernanda L.",
    city: "Barra da Tijuca, RJ",
    product: "Perna Inteira – Cera",
    href: "/produto/perna-cera",
    image: catalogImage("perna-cera"),
    when: "há 11 minutos",
  },
  {
    name: "Bianca T.",
    city: "Avenida Paulista, SP",
    product: "Design de Sobrancelha",
    href: "/produto/design-sobrancelha",
    image: catalogImage("design-sobrancelha"),
    when: "há 18 minutos",
  },
  {
    name: "Larissa P.",
    city: "Campo Grande, RJ",
    product: "Braços Inteiros Laser",
    href: "/produto/bracos-laser",
    image: catalogImage("bracos-laser"),
    when: "há 24 minutos",
  },
];

const malePurchases = [
  {
    name: "Rafael C.",
    city: "Copacabana, RJ",
    product: "Tórax Laser",
    href: "/produto/peito-laser-masc",
    image: "/images/products/male/peito-laser-masc.webp",
    when: "há 2 minutos",
  },
  {
    name: "Bruno M.",
    city: "Tijuca, RJ",
    product: "Costas Laser",
    href: "/produto/costas-laser-masc",
    image: "/images/products/male/costas-laser-masc.webp",
    when: "há 6 minutos",
  },
  {
    name: "Pedro S.",
    city: "Barra da Tijuca, RJ",
    product: "Axila Laser",
    href: "/produto/axilas-laser-masc",
    image: "/images/products/male/axilas-laser-masc.webp",
    when: "há 11 minutos",
  },
  {
    name: "Lucas T.",
    city: "Avenida Paulista, SP",
    product: "Barba Laser",
    href: "/produto/barba-laser-masc",
    image: "/images/products/male/barba-laser-masc.webp",
    when: "há 18 minutos",
  },
  {
    name: "Thiago P.",
    city: "Copacabana, RJ",
    product: "Queixo Laser",
    href: "/produto/queixo-laser-masc",
    image: "/images/products/male/queixo-laser-masc.webp",
    when: "há 24 minutos",
  },
];

const VISIBLE_MS = 6000;
const OUT_MS = 400;
const GAP_MIN_MS = 4000;
const GAP_MAX_MS = 7000;

function randomGapMs() {
  return GAP_MIN_MS + Math.floor(Math.random() * (GAP_MAX_MS - GAP_MIN_MS + 1));
}

export function PurchasePopup() {
  const pathname = usePathname();
  const audience = audienceFromPath(pathname);
  const purchases = audience === "masculino" ? malePurchases : femalePurchases;
  const [index, setIndex] = useState(0);
  const [visible, setVisible] = useState(true);
  const cardRef = useRef<HTMLAnchorElement>(null);
  const reduceMotion = useRef(false);

  useEffect(() => {
    reduceMotion.current = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
  }, []);

  useEffect(() => {
    setIndex(0);
    setVisible(true);
  }, [audience]);

  useEffect(() => {
    const timers: number[] = [];
    const outMs = reduceMotion.current ? 0 : OUT_MS;

    timers.push(
      window.setTimeout(() => setVisible(false), VISIBLE_MS),
    );
    timers.push(
      window.setTimeout(() => {
        setIndex((current) => (current + 1) % purchases.length);
        setVisible(true);
      }, VISIBLE_MS + outMs + randomGapMs()),
    );

    return () => {
      timers.forEach((id) => window.clearTimeout(id));
    };
  }, [index, purchases.length]);

  useGSAP(
    () => {
      const node = cardRef.current;
      if (!node) return;
      const reduce = reduceMotion.current;
      if (visible) {
        if (reduce) {
          gsap.set(node, { x: 0, y: 0, opacity: 1, scale: 1 });
          return;
        }
        gsap.fromTo(
          node,
          { x: -28, y: 12, opacity: 0, scale: 0.96 },
          {
            x: 0,
            y: 0,
            opacity: 1,
            scale: 1,
            duration: 0.5,
            ease: "power3.out",
          },
        );
      } else if (reduce) {
        gsap.set(node, { opacity: 0 });
      } else {
        gsap.to(node, {
          x: -20,
          y: 10,
          opacity: 0,
          scale: 0.96,
          duration: 0.4,
          ease: "power3.in",
        });
      }
    },
    { dependencies: [visible, index] },
  );

  const item = purchases[index];
  if (!item) return null;

  return (
    <div
      data-pm-purchase
      className={`fixed bottom-24 left-4 z-[60] hidden w-max max-w-[min(calc(100vw-2rem),22rem)] md:bottom-8 md:block ${
        visible ? "" : "pointer-events-none"
      }`}
      aria-hidden={!visible}
    >
      <Link
        ref={cardRef}
        href={item.href}
        tabIndex={visible ? 0 : -1}
        className="inline-flex items-center gap-3 rounded-2xl border border-primary/15 bg-white p-2.5 shadow-[0_18px_40px_rgba(58,10,60,0.18)]"
      >
        <span className="relative h-14 w-14 shrink-0 overflow-hidden rounded-xl bg-surface-container-high">
          <Image
            src={item.image}
            alt=""
            fill
            className="object-cover"
            sizes="56px"
          />
        </span>
        <span className="min-w-0">
          <span className="block text-sm font-semibold text-on-surface">
            {item.name}
          </span>
          <span className="block text-xs whitespace-normal text-on-surface-variant">
            comprou {item.product}
          </span>
          <span className="mt-0.5 block text-[11px] whitespace-normal text-primary">
            {item.city} · {item.when}
          </span>
        </span>
      </Link>
    </div>
  );
}
