import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { ProductPageView } from "@/components/ProductPageView";
import { getProductById, products } from "@/lib/data";

type Props = {
  params: Promise<{ id: string }>;
};

export function generateStaticParams() {
  return products.map((product) => ({ id: product.id }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const product = getProductById(id);
  if (!product) {
    return { title: "Produto não encontrado" };
  }
  return {
    title: `${product.name} | Pello Menos`,
    description: product.description,
  };
}

export default async function ProductPage({ params }: Props) {
  const { id } = await params;
  const product = getProductById(id);
  if (!product) notFound();
  return <ProductPageView product={product} />;
}
