"use client";

import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { audienceFromPath } from "@/lib/data";

gsap.registerPlugin(useGSAP);

const femalePurchases = [
  {
    name: "Camila R.",
    city: "Copacabana, RJ",
    product: "Axilas Laser",
    href: "/produto/axilas-laser",
    image: "/images/social/cliente-1.png",
    when: "há 2 minutos",
  },
  {
    name: "Juliana M.",
    city: "Tijuca, RJ",
    product: "Virilha Total Laser",
    href: "/produto/virilha-laser",
    image: "/images/social/cliente-2.png",
    when: "há 6 minutos",
  },
  {
    name: "Fernanda L.",
    city: "Barra da Tijuca, RJ",
    product: "Perna Inteira – Cera",
    href: "/produto/perna-cera",
    image: "/images/social/cliente-3.png",
    when: "há 11 minutos",
  },
  {
    name: "Bianca T.",
    city: "Avenida Paulista, SP",
    product: "Design de Sobrancelha",
    href: "/produto/design-sobrancelha",
    image: "/images/social/cliente-4.png",
    when: "há 18 minutos",
  },
  {
    name: "Larissa P.",
    city: "Campo Grande, RJ",
    product: "Braços Inteiros Laser",
    href: "/produto/bracos-laser",
    image: "/images/social/cliente-5.png",
    when: "há 24 minutos",
  },
];

const malePurchases = [
  {
    name: "Rafael C.",
    city: "Copacabana, RJ",
    product: "Peito Laser",
    href: "/produto/peito-laser-masc",
    image: "/images/products/male/peito.jpg",
    when: "há 2 minutos",
  },
  {
    name: "Bruno M.",
    city: "Tijuca, RJ",
    product: "Costas Laser",
    href: "/produto/costas-laser-masc",
    image: "/images/products/male/costas.jpg",
    when: "há 6 minutos",
  },
  {
    name: "Pedro S.",
    city: "Barra da Tijuca, RJ",
    product: "Axilas Laser",
    href: "/produto/axilas-laser-masc",
    image: "/images/products/male/axilas.jpg",
    when: "há 11 minutos",
  },
  {
    name: "Lucas T.",
    city: "Avenida Paulista, SP",
    product: "Barba Laser",
    href: "/produto/barba-laser-masc",
    image: "/images/products/male/barba.jpg",
    when: "há 18 minutos",
  },
  {
    name: "Thiago P.",
    city: "Campo Grande, RJ",
    product: "Nuca Laser",
    href: "/produto/nuca-laser-masc",
    image: "/images/products/male/nuca.jpg",
    when: "há 24 minutos",
  },
];

const CYCLE_MS = 13000;
const VISIBLE_MS = 8000;

export function PurchasePopup() {
  const pathname = usePathname();
  const audience = audienceFromPath(pathname);
  const purchases = audience === "masculino" ? malePurchases : femalePurchases;
  const [index, setIndex] = useState(0);
  const [visible, setVisible] = useState(true);
  const cardRef = useRef<HTMLAnchorElement>(null);

  useEffect(() => {
    setIndex(0);
    setVisible(true);
  }, [audience]);

  useEffect(() => {
    const hide = window.setTimeout(() => setVisible(false), VISIBLE_MS);
    const next = window.setTimeout(() => {
      setIndex((current) => (current + 1) % purchases.length);
      setVisible(true);
    }, CYCLE_MS);

    return () => {
      window.clearTimeout(hide);
      window.clearTimeout(next);
    };
  }, [index, purchases.length]);

  useGSAP(
    () => {
      const node = cardRef.current;
      if (!node) return;
      if (visible) {
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
    <div className="fixed bottom-24 left-4 z-[60] w-[min(calc(100vw-2rem),320px)] md:bottom-8">
      <Link
        ref={cardRef}
        href={item.href}
        className="flex items-center gap-3 rounded-2xl border border-primary/15 bg-white p-2.5 shadow-[0_18px_40px_rgba(58,10,60,0.18)]"
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
          <span className="block truncate text-sm font-semibold text-on-surface">
            {item.name}
          </span>
          <span className="block truncate text-xs text-on-surface-variant">
            comprou {item.product}
          </span>
          <span className="mt-0.5 block truncate text-[11px] text-primary">
            {item.city} · {item.when}
          </span>
        </span>
      </Link>
    </div>
  );
}
