import type { Metadata } from "next";
import { CatalogPageView } from "@/components/CatalogPageView";
import { retailProducts } from "@/lib/data";

export const metadata: Metadata = {
  title: "Produtos | Pello Menos",
  description: "Body Splash e linha oficial Pello Menos para o cuidado em casa.",
};

export default function ProdutosPage() {
  return (
    <CatalogPageView
      audience="feminino"
      eyebrow="Loja"
      title="Produtos"
      subtitle="A linha oficial para usar em casa depois da sessão."
      items={retailProducts()}
    />
  );
}
