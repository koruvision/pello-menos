import type { Metadata } from "next";
import { CatalogPageView } from "@/components/CatalogPageView";
import { planProductsFor } from "@/lib/data";

export const metadata: Metadata = {
  title: "Planos de Assinatura | Pello Menos",
  description:
    "Silver Cera, Gold Cera, Clube de Laser e Pré-pago. Escolha o plano e compre em um clique.",
};

export default function PlanosPage() {
  return (
    <CatalogPageView
      audience="feminino"
      eyebrow="Assinatura"
      title="Planos de Assinatura"
      subtitle="Silver - Cera, Gold - Cera, Clube de Laser e Pré Pago. Planos no valor cheio, sem parcelamento."
      items={planProductsFor("feminino")}
    />
  );
}
