import type { Metadata } from "next";
import { CatalogHub } from "@/components/CatalogHub";
import { productsByMethod, serviceHref, serviceMethodsFor } from "@/lib/data";

export const metadata: Metadata = {
  title: "Serviços masculinos | Pello Menos",
  description: "Cera, laser e esfoliação masculina com 5% OFF no e-commerce.",
};

export default function ServicosMasculinoPage() {
  const audience = "masculino" as const;
  const cards = serviceMethodsFor(audience).map((method) => ({
    href: serviceHref(audience, method.id),
    label: method.label,
    subtitle: method.subtitle,
    image: productsByMethod(audience, method.id)[0]?.image ?? "/brand/logo-square.png",
  }));

  return (
    <CatalogHub
      audience={audience}
      eyebrow="Catálogo"
      title="Serviços"
      subtitle="Escolha o método: cera, laser ou esfoliação."
      cards={cards}
    />
  );
}
