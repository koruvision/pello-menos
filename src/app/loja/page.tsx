import type { Metadata } from "next";
import { CatalogPageView } from "@/components/CatalogPageView";
import { methodLabels, products, type ProductMethod } from "@/lib/data";

export const metadata: Metadata = {
  title: "Loja | Pello Menos",
  description:
    "Cera, laser, linha, esfoliação, planos, cartão presente e a linha oficial Pello Menos.",
};

const shopFilters: { id: "todos" | ProductMethod; label: string }[] = [
  { id: "todos", label: "Todos" },
  { id: "cera", label: methodLabels.cera },
  { id: "laser", label: methodLabels.laser },
  { id: "linha", label: methodLabels.linha },
  { id: "esfoliacao", label: methodLabels.esfoliacao },
  { id: "produto", label: methodLabels.produto },
  { id: "presente", label: methodLabels.presente },
  { id: "plano", label: methodLabels.plano },
];

const audienceFilters = [
  { id: "feminino", label: "Feminino" },
  { id: "masculino", label: "Masculino" },
];

export default function LojaPage() {
  return (
    <CatalogPageView
      audience="feminino"
      eyebrow="Loja"
      title="Loja"
      subtitle="Escolha o público e o tipo. O preço da tabela já entra com 5% de desconto no e-commerce. A unidade é escolhida na ficha."
      items={products}
      filters={shopFilters}
      audienceFilters={audienceFilters}
      defaultAudience="feminino"
    />
  );
}
