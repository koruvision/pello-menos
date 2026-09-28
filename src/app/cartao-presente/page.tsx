import type { Metadata } from "next";
import { CatalogPageView } from "@/components/CatalogPageView";
import { giftCardProducts } from "@/lib/data";

export const metadata: Metadata = {
  title: "Cartão Presente | Pello Menos",
  description:
    "Gift card Pello Menos. Escolha o valor do vale presente e a unidade onde será usado.",
};

export default function GiftCardPage() {
  return (
    <CatalogPageView
      audience="feminino"
      eyebrow="Vale presente"
      title="Cartão Presente"
      subtitle="Escolha o valor do gift card. Informe a unidade onde o presente será usado."
      items={giftCardProducts()}
    />
  );
}
