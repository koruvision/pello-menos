import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { CatalogPageView } from "@/components/CatalogPageView";
import {
  productsByMethod,
  serviceMethodsFor,
  type ServiceMethod,
} from "@/lib/data";

const METHODS = serviceMethodsFor("masculino");

type Props = {
  params: Promise<{ method: string }>;
};

export function generateStaticParams() {
  return METHODS.map((item) => ({ method: item.id }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { method } = await params;
  const meta = METHODS.find((item) => item.id === method);
  if (!meta) return { title: "Serviço | Pello Menos" };
  return {
    title: `${meta.label} masculino | Pello Menos`,
    description: meta.subtitle,
  };
}

export default async function ServicoMethodMasculinoPage({ params }: Props) {
  const { method } = await params;
  const meta = METHODS.find((item) => item.id === method);
  if (!meta) notFound();
  return (
    <CatalogPageView
      audience="masculino"
      eyebrow="Serviços"
      title={meta.label}
      subtitle={meta.subtitle}
      items={productsByMethod("masculino", meta.id as ServiceMethod)}
    />
  );
}
