import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { CatalogPageView } from "@/components/CatalogPageView";
import {
  categoryLabels,
  maleAreaIds,
  productsByArea,
  type AreaCategory,
} from "@/lib/data";

type Props = {
  params: Promise<{ category: string }>;
};

export function generateStaticParams() {
  return maleAreaIds.map((category) => ({ category }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { category } = await params;
  const label = categoryLabels[category as AreaCategory];
  if (!label) return { title: "Área | Pello Menos" };
  return {
    title: `${label} masculino | Pello Menos`,
    description: `Serviços masculinos de ${label.toLowerCase()} na Pello Menos.`,
  };
}

export default async function AreaMasculinoPage({ params }: Props) {
  const { category } = await params;
  if (!maleAreaIds.includes(category as AreaCategory)) notFound();
  const id = category as AreaCategory;
  const title =
    id === "rosto"
      ? "Barba"
      : id === "axilas"
        ? "Axila"
        : id === "pernas"
          ? "Perna"
          : categoryLabels[id];
  return (
    <CatalogPageView
      audience="masculino"
      eyebrow="Áreas"
      title={title}
      subtitle={`Cera, laser e esfoliação em ${title.toLowerCase()}.`}
      items={productsByArea("masculino", id)}
    />
  );
}
