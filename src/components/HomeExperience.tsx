"use client";

import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useMemo, useRef, useState } from "react";
import { CategoryCircles } from "@/components/CategoryCircles";
import { GoogleReviews } from "@/components/GoogleReviews";
import { HeroBanner } from "@/components/HeroBanner";
import { ProductGrid } from "@/components/ProductGrid";
import { PromoBanner } from "@/components/PromoBanner";
import { SplitOffer } from "@/components/SplitOffer";
import { SquareBannerRail } from "@/components/SquareBannerRail";
import {
  categories,
  categoriesMasculino,
  formatBRL,
  googleReviews,
  googleReviewsMasculino,
  heroSlides,
  heroSlidesMasculino,
  productRails,
  productsHref,
  rectangularBanners,
  rectangularBannersMasculino,
  squareBanners,
  squareBannersMasculino,
  type ProductAudience,
  type ProductMethod,
} from "@/lib/data";

gsap.registerPlugin(useGSAP, ScrollTrigger);

const femaleFilters: { id: "todos" | ProductMethod; label: string }[] = [
  { id: "todos", label: "Todos" },
  { id: "cera", label: "Cera" },
  { id: "laser", label: "Laser" },
  { id: "linha", label: "Linha" },
  { id: "esfoliacao", label: "Esfoliação" },
];

const maleFilters: { id: "todos" | ProductMethod; label: string }[] = [
  { id: "todos", label: "Todos" },
  { id: "cera", label: "Cera" },
  { id: "laser", label: "Laser" },
  { id: "esfoliacao", label: "Esfoliação" },
];

type Props = {
  audience?: ProductAudience;
};

export function HomeExperience({ audience = "feminino" }: Props) {
  const root = useRef<HTMLDivElement>(null);
  const isMale = audience === "masculino";
  const filters = isMale ? maleFilters : femaleFilters;
  const [filter, setFilter] = useState<(typeof filters)[number]["id"]>("todos");
  const catalogHref = productsHref(audience);

  const show = useMemo(
    () => ({
      cera: filter === "todos" || filter === "cera",
      laser: filter === "todos" || filter === "laser",
      linha: !isMale && (filter === "todos" || filter === "linha"),
      esfoliacao: filter === "todos" || filter === "esfoliacao",
      extra: filter === "todos",
    }),
    [filter, isMale],
  );

  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add("(prefers-reduced-motion: no-preference)", () => {
        gsap.utils.toArray<HTMLElement>(".js-reveal").forEach((section) => {
          gsap.from(section, {
            y: 36,
            opacity: 0,
            duration: 0.8,
            ease: "power3.out",
            scrollTrigger: {
              trigger: section,
              start: "top 88%",
            },
          });
        });
        gsap.from(".js-cat", {
          y: 18,
          opacity: 0,
          stagger: 0.07,
          duration: 0.55,
          ease: "power2.out",
          scrollTrigger: {
            trigger: ".js-cats",
            start: "top 90%",
          },
        });
      });
    },
    { scope: root },
  );

  return (
    <div ref={root}>
      <HeroBanner slides={isMale ? heroSlidesMasculino : heroSlides} />
      <CategoryCircles items={isMale ? categoriesMasculino : categories} />
      <div
        id="produtos"
        className="mx-auto flex max-w-7xl scroll-mt-28 flex-wrap gap-2 px-container-margin pb-2"
      >
        {filters.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => setFilter(item.id)}
            className={
              filter === item.id
                ? "rounded-full bg-primary px-4 py-2 text-sm font-semibold text-on-primary"
                : "rounded-full border border-primary/25 px-4 py-2 text-sm text-primary"
            }
          >
            {item.label}
          </button>
        ))}
      </div>
      {show.cera ? (
        <ProductGrid
          id="cera"
          eyebrow="Cera 5% OFF"
          title="Cera em destaque"
          subtitle="Preço da tabela com 5% de desconto no e-commerce"
          items={isMale ? productRails.ceraOfertasMasc : productRails.ceraOfertas}
          muted
        />
      ) : null}
      {show.cera ? (
        <ProductGrid
          eyebrow="Áreas mais pedidas"
          title="Cera por região"
          subtitle={
            isMale
              ? "Peito, costas, axila, pernas e virilha — todos os serviços da tabela"
              : "Virilha, axila, pernas, corpo e olhar — todos os serviços da tabela"
          }
          items={isMale ? productRails.ceraAreasMasc : productRails.ceraAreas}
        />
      ) : null}
      {show.extra ? (
        <SplitOffer
          eyebrow="Assinatura VIP Cera"
          title="Cera todo mês"
          subtitle={
            isMale
              ? "O cliente assina e faz a sessão de cera no mês, no horário dele — pele lisa o ano inteiro."
              : "A cliente assina e faz a sessão de cera no mês, no horário dela — pele lisa o ano inteiro."
          }
          image={isMale ? "/images/hero/male/assinatura-cera.jpg" : "/images/hero/assinatura-female.jpg"}
          imageAlt={
            isMale
              ? "Recepcionista atendendo um cliente na assinatura VIP Cera Pello Menos"
              : "Recepcionista atendendo uma cliente na assinatura VIP Cera Pello Menos"
          }
          ctaHref={isMale ? "/masculino#cera" : "/#cera"}
          ctaLabel="Quero assinar"
        />
      ) : null}
      {show.extra && !isMale ? (
        <SplitOffer
          eyebrow="Assinatura VIP Laser"
          title="Laser todo mês"
          subtitle="A cliente assina e faz a sessão a laser no mês, no horário dela — resultado contínuo, sem recomeçar."
          image="/images/hero/promo-laser-v3.png"
          imageAlt="Sessão de laser na assinatura VIP Laser Pello Menos"
          ctaHref="/#laser"
          ctaLabel="Quero assinar"
        />
      ) : null}
      {show.laser ? (
        <PromoBanner
          banner={
            isMale ? rectangularBannersMasculino[0]! : rectangularBanners[1]!
          }
        />
      ) : null}
      {show.laser ? (
        <ProductGrid
          id="laser"
          eyebrow="Laser"
          title={isMale ? "Laser no rosto" : "Laser no rosto"}
          subtitle={
            isMale
              ? "Barba, nuca, pescoço, orelhas e nariz"
              : "Pacotes nas áreas do rosto, depois da cera"
          }
          items={isMale ? productRails.laserRostoMasc : productRails.laserRosto}
        />
      ) : null}
      {show.laser ? (
        <ProductGrid
          eyebrow="Laser"
          title={isMale ? "Laser no corpo" : "Laser no corpo"}
          subtitle={
            isMale
              ? "Peito, costas, axilas, braços, pernas e virilha"
              : "Braços, pernas e corpo em carrossel próprio"
          }
          items={isMale ? productRails.laserCorpoMasc : productRails.laserCorpo}
          muted
        />
      ) : null}
      {show.extra ? (
        <SquareBannerRail
          banners={isMale ? squareBannersMasculino : squareBanners}
          productsHref={catalogHref}
        />
      ) : null}
      {show.esfoliacao ? (
        <ProductGrid
          id="esfoliacao"
          eyebrow="Esfoliação"
          title="Pele pronta para a cera"
          subtitle={
            isMale
              ? "Todas as áreas da tabela para potencializar a cera"
              : "Todas as áreas da tabela — pele pronta para a cera"
          }
          items={isMale ? productRails.esfoliacaoMasc : productRails.esfoliacao}
        />
      ) : null}
      {show.linha ? (
        <ProductGrid
          id="linha"
          eyebrow="Linha"
          title="Depilação com linha"
          subtitle="Buço, queixo e faixa — valores da tabela com 5% OFF"
          items={productRails.linha}
          muted
        />
      ) : null}
      {show.extra ? (
        <SplitOffer
          id="produtos-loja"
          eyebrow="Produto oficial"
          title="Body Splash Pello Menos"
          subtitle="Fragrância oficial para usar em casa depois da sessão."
          image="/images/hero/splash-banner.jpg"
          imageAlt="Body Splash oficial Pello Menos"
          ctaHref="/produto/body-splash"
          ctaLabel="Ver produto"
          price={
            productRails.produtos[0]
              ? formatBRL(productRails.produtos[0].priceCents)
              : undefined
          }
          oldPrice={
            productRails.produtos[0]?.oldPriceCents
              ? formatBRL(productRails.produtos[0].oldPriceCents)
              : undefined
          }
        />
      ) : null}
      <GoogleReviews reviews={isMale ? googleReviewsMasculino : googleReviews} />
    </div>
  );
}
