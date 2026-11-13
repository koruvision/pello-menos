import type { Metadata } from "next";
import { CatalogPageView } from "@/components/CatalogPageView";
import { giftCardProducts } from "@/lib/data";

export const metadata: Metadata = {
  title: "Cartão Presente | Pello Menos",
  description:
    "Gift card Pello Menos só para depilação a cera. Escolha o valor e a unidade onde o presente será usado.",
};

export default function GiftCardPage() {
  return (
    <CatalogPageView
      audience="feminino"
      eyebrow="Vale presente"
      title="Cartão Presente"
      subtitle="Vale só para depilação a cera — não serve para laser, linha, esfoliação nem planos. Escolha o valor e a unidade onde o presente será usado."
      items={giftCardProducts("feminino")}
    />
  );
}
