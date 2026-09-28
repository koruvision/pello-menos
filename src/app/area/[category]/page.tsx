import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { CatalogPageView } from "@/components/CatalogPageView";
import {
  categoryLabels,
  femaleAreaIds,
  productsByArea,
  type AreaCategory,
} from "@/lib/data";

type Props = {
  params: Promise<{ category: string }>;
};

export function generateStaticParams() {
  return femaleAreaIds.map((category) => ({ category }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { category } = await params;
  const label = categoryLabels[category as AreaCategory];
  if (!label) return { title: "Área | Pello Menos" };
  return {
    title: `${label} | Pello Menos`,
    description: `Serviços de ${label.toLowerCase()} na Pello Menos.`,
  };
}

export default async function AreaPage({ params }: Props) {
  const { category } = await params;
  if (!femaleAreaIds.includes(category as AreaCategory)) notFound();
  const id = category as AreaCategory;
  return (
    <CatalogPageView
      audience="feminino"
      eyebrow="Áreas"
      title={categoryLabels[id]}
      subtitle={`Cera, laser e esfoliação em ${categoryLabels[id].toLowerCase()}.`}
      items={productsByArea("feminino", id)}
    />
  );
}
