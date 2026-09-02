import type { ReactNode } from "react";
import Link from "next/link";

type Props = {
  title: string;
  children: ReactNode;
};

export function LegalPage({ title, children }: Props) {
  return (
    <main className="mx-auto max-w-3xl px-container-margin py-12">
      <p className="font-label-md text-label-md text-primary uppercase">
        Pello Menos
      </p>
      <h1 className="mt-2 font-[family-name:var(--font-display)] text-headline-md text-primary md:text-headline-lg">
        {title}
      </h1>
      <div className="mt-8 space-y-4 text-sm leading-relaxed text-on-surface-variant">
        {children}
      </div>
      <Link
        href="/"
        className="btn-lux btn-lux-primary mt-10 inline-flex rounded-full px-6 py-3 text-sm font-semibold tracking-wide text-white uppercase"
      >
        Voltar à home
      </Link>
    </main>
  );
}
