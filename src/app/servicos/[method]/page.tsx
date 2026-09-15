import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { CatalogPageView } from "@/components/CatalogPageView";
import {
  productsByMethod,
  serviceMethods,
  type ServiceMethod,
} from "@/lib/data";

const METHODS = serviceMethods.map((item) => item.id);

type Props = {
  params: Promise<{ method: string }>;
};

export function generateStaticParams() {
  return METHODS.map((method) => ({ method }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { method } = await params;
  const meta = serviceMethods.find((item) => item.id === method);
  if (!meta) return { title: "Serviço | Pello Menos" };
  return {
    title: `${meta.label} | Pello Menos`,
    description: meta.subtitle,
  };
}

export default async function ServicoMethodPage({ params }: Props) {
  const { method } = await params;
  const meta = serviceMethods.find((item) => item.id === method);
  if (!meta) notFound();
  return (
    <CatalogPageView
      audience="feminino"
      eyebrow="Serviços"
      title={meta.label}
      subtitle={meta.subtitle}
      items={productsByMethod("feminino", meta.id as ServiceMethod)}
    />
  );
}
