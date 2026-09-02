"use client";

import Link from "next/link";
import { Icon } from "@/components/Icon";

export default function DesejosPage() {
  return (
    <main className="mx-auto flex max-w-lg flex-col items-center px-container-margin py-20 text-center">
      <span className="flex h-20 w-20 items-center justify-center rounded-full bg-surface-container-low text-primary">
        <Icon name="heart" size={32} />
      </span>
      <h1 className="mt-6 font-[family-name:var(--font-display)] text-headline-md text-primary">
        Lista de Desejos
      </h1>
      <p className="mt-2 text-on-surface-variant">
        Sua lista está vazia. Explore os serviços e guarde os favoritos.
      </p>
      <Link
        href="/#produtos"
        className="btn-lux btn-lux-primary mt-8 inline-flex items-center gap-2 rounded-full px-8 py-3 font-label-md text-label-md text-on-primary uppercase"
      >
        Ver serviços
        <Icon name="arrowRight" size={16} />
      </Link>
    </main>
  );
}
