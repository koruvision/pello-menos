import type { Metadata } from "next";
import { Suspense } from "react";
import { SearchResultsView } from "@/components/SearchResultsView";

export const metadata: Metadata = {
  title: "Busca | Pello Menos",
  description:
    "Busque serviços de cera, laser, linha e esfoliação. Filtre por categoria, preço e ordem.",
};

export default function BuscaPage() {
  return (
    <Suspense
      fallback={
        <main className="mx-auto w-full max-w-7xl px-container-margin py-12">
          <p className="text-sm text-on-surface-variant">Carregando busca…</p>
        </main>
      }
    >
      <SearchResultsView />
    </Suspense>
  );
}
