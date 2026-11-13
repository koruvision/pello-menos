"use client";

import Image from "next/image";
import Link from "next/link";
import { useMemo, useState } from "react";
import { BadgeTag } from "@/components/BadgeTag";
import { ComingSoonOverlay } from "@/components/ComingSoonOverlay";
import { Icon } from "@/components/Icon";
import { useStore } from "@/components/StoreProvider";
import {
  BODY_SPLASH_LAUNCH_LABEL,
  isComingSoon,
  categoryLabels,
  formatBRL,
  getInstallment,
  homeHref,
  installmentHint,
  methodLabels,
  productsHref,
  relatedProducts,
  retailHref,
  planosHref,
  giftCardHref,
  isServiceMethod,
  unitsForProduct,
  type Product,
} from "@/lib/data";
import { productCopy } from "@/lib/product-copy";
import { productBridge, quoteFor } from "@/lib/woo-bridge";

type Props = {
  product: Product;
};

export function ProductPageView({ product }: Props) {
  const { addToCart } = useStore();
  const [unitId, setUnitId] = useState("");
  const [qty, setQty] = useState(1);
  const [unitError, setUnitError] = useState("");
  const [aboutOpen, setAboutOpen] = useState(false);
  const copy = productCopy(product.id);
  const aboutLong = copy.long.trim();
  const aboutClamped = aboutLong.length > 280 && !aboutOpen;

  const related = useMemo(() => relatedProducts(product), [product]);
  const bridge = productBridge(product.id);
  const availableUnits = useMemo(() => {
    const capacity = unitsForProduct(product);
    const map = bridge?.units;
    // Linha / esfoliação / presente / produto (Body Splash): capacidade já é todas as lojas.
    const allStoresMethod =
      product.method === "linha" ||
      product.method === "esfoliacao" ||
      product.method === "presente" ||
      product.method === "produto";
    if (allStoresMethod || !map || Object.keys(map).length === 0) return capacity;
    return capacity.filter((unit) => Boolean(map[unit.id]));
  }, [product, bridge]);
  const isTimedService = isServiceMethod(product.method);
  const comingSoon = isComingSoon(product.id);
  const unitsByState = useMemo(() => {
    const groups: Record<string, typeof availableUnits> = {};
    for (const unit of availableUnits) {
      (groups[unit.state] ??= []).push(unit);
    }
    return groups;
  }, [availableUnits]);
  const selectedUnit = availableUnits.find((unit) => unit.id === unitId);
  const quote = quoteFor(product, selectedUnit?.priceRegion ?? "rj-sp");
  const rjQuote = quoteFor(product, "rj-sp");
  const spQuote = quoteFor(product, "sp-df");
  const installment = getInstallment(quote.saleCents, product.method);
  const regionLabel = !selectedUnit
    ? "Tabela de Rio de Janeiro e interior de São Paulo. O valor muda ao escolher a unidade."
    : selectedUnit.priceRegion === "sp-df"
      ? "Tabela de São Paulo capital e DF"
      : "Tabela de Rio de Janeiro e interior de São Paulo";

  function handleAdd() {
    if (!selectedUnit) {
      setUnitError("Escolha a unidade para continuar.");
      return;
    }
    setUnitError("");
    addToCart(
      { ...product, priceCents: quote.saleCents },
      selectedUnit,
      qty,
    );
  }

  const discount =
    quote.regularCents > quote.saleCents
      ? Math.round((1 - quote.saleCents / quote.regularCents) * 100)
      : null;

  const catalogParent =
    product.method === "produto"
      ? { href: retailHref(product.audience), label: "Produtos" }
      : product.method === "plano"
        ? { href: planosHref(product.audience), label: "Planos de Assinatura" }
        : product.method === "presente"
          ? { href: giftCardHref(product.audience), label: "Cartão Presente" }
          : { href: productsHref(product.audience), label: "Serviços" };

  return (
    <main className="mx-auto w-full max-w-6xl px-container-margin py-8 md:py-12">
      <nav className="text-xs text-on-surface-variant">
        <Link href={homeHref(product.audience)} className="hover:text-primary">
          Início
        </Link>
        <span className="px-2">/</span>
        <Link href={catalogParent.href} className="hover:text-primary">
          {catalogParent.label}
        </Link>
        <span className="px-2">/</span>
        <span className="text-primary">{product.name}</span>
      </nav>

      <div className="mt-6 grid gap-8 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
        <div className="overflow-hidden rounded-3xl bg-surface shadow-[0_18px_40px_rgba(58,10,60,0.08)]">
          <div className="relative aspect-[4/5] bg-surface-container-high">
            <Image
              src={product.image}
              alt={product.imageAlt}
              fill
              priority
              data-pm-photo
              className={`${
                product.id === "plano-clube-laser"
                  ? "object-contain p-8"
                  : "object-cover"
              }${comingSoon ? " grayscale" : ""}`}
              sizes="(max-width: 1024px) 92vw, 560px"
            />
            {comingSoon ? <ComingSoonOverlay size="lg" /> : null}
            {product.badge ? (
              <div className="absolute top-4 left-4 z-20">
                <BadgeTag label={product.badge} />
              </div>
            ) : null}
          </div>
        </div>

        <div
          data-pm-buy
          data-product-id={bridge?.productId ?? ""}
          data-method={product.method}
          data-name={product.name}
          data-duration={product.duration}
          data-sku={product.sku}
          data-catalog-id={product.id}
          data-rj-sale={rjQuote.saleCents}
          data-rj-regular={rjQuote.regularCents}
          data-sp-sale={spQuote.saleCents}
          data-sp-regular={spQuote.regularCents}
        >
          <p className="font-label-md text-label-md text-secondary uppercase">
            {product.method === "cera" || product.method === "laser" || product.method === "linha" || product.method === "esfoliacao"
              ? `${methodLabels[product.method]} · ${categoryLabels[product.category]}`
              : methodLabels[product.method]}
          </p>
          <h1 className="mt-2 font-[family-name:var(--font-display)] text-headline-md text-primary md:text-headline-lg">
            {product.name}
          </h1>
          <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-on-surface-variant">
            <span className="inline-flex items-center gap-1.5">
              <Icon name="clock" size={15} />
              {product.duration}
              {isTimedService ? "*" : ""}
            </span>
            <span>SKU {product.sku}</span>
            <span>Cód. {product.code}</span>
          </div>

          <div className="mt-5 flex items-end gap-3">
            <p
              data-pm-sale
              className="font-[family-name:var(--font-display)] text-4xl text-primary"
            >
              {installment.times > 1
                ? `${installment.times}x de ${formatBRL(installment.installmentCents)}`
                : formatBRL(quote.saleCents)}
            </p>
            {installment.times > 1 ? (
              <p data-pm-total className="pb-1 text-sm text-on-surface-variant">
                Total {formatBRL(quote.saleCents)}
              </p>
            ) : (
              <p data-pm-total className="hidden pb-1 text-sm text-on-surface-variant" />
            )}
            {quote.regularCents > quote.saleCents ? (
              <p
                data-pm-regular
                className="pb-1 text-sm text-on-surface-variant line-through"
              >
                {formatBRL(quote.regularCents)}
              </p>
            ) : (
              <p data-pm-regular className="hidden pb-1 text-sm line-through" />
            )}
            {discount ? (
              <span
                data-pm-off
                className="mb-1 rounded-full bg-secondary-container px-2.5 py-1 text-[11px] font-semibold text-on-secondary-container"
              >
                -{discount}%
              </span>
            ) : (
              <span data-pm-off className="hidden" />
            )}
          </div>
          <p data-pm-region className="mt-1 text-xs text-on-surface-variant">
            {regionLabel}
          </p>
          {installment.times > 1 ||
          product.method === "plano" ||
          product.method === "presente" ? (
            <p className="mt-1 text-xs text-on-surface-variant">
              {installmentHint(product.method)}
            </p>
          ) : null}

          {copy.short ? (
            <p className="mt-5 text-body-md text-on-surface">{copy.short}</p>
          ) : null}
          {product.method === "produto" ? (
            <p
              data-pm-pickup-note
              className="mt-3 inline-flex items-start gap-2 rounded-xl bg-secondary-container/60 px-3 py-2 text-xs text-on-secondary-container"
            >
              <Icon name="mapPin" size={14} className="mt-0.5 shrink-0" />
              <span>
                <strong>Retirada na loja.</strong> Você compra aqui no site e retira na unidade
                Pello Menos escolhida — não enviamos pelos Correios.
              </span>
            </p>
          ) : null}
          {isTimedService ? (
            <p className="mt-3 text-xs text-on-surface-variant">
              * Tempo médio só da execução do serviço; não inclui anamnese.
            </p>
          ) : null}

          {comingSoon ? (
            <div
              data-pm-coming-soon-notice
              className="mt-6 rounded-2xl border border-outline/40 bg-surface-container-low p-5"
            >
              <p className="inline-flex items-center gap-2 text-sm font-semibold text-primary">
                <span
                  aria-hidden
                  className="block h-4 w-4 rounded-full border-2 border-primary/25 border-t-primary"
                  style={{ animation: "pm-coming-spin 0.9s linear infinite" }}
                />
                Em produção · lançamento {BODY_SPLASH_LAUNCH_LABEL}
              </p>
              <p className="mt-2 text-sm text-on-surface">
                O Body Splash ainda não está à venda. A partir de {BODY_SPLASH_LAUNCH_LABEL} você
                compra aqui no site e retira na unidade Pello Menos escolhida — não há envio pelos
                Correios.
              </p>
              <Link
                href={productsHref(product.audience)}
                className="btn-lux btn-lux-primary mt-4 inline-flex items-center justify-center gap-2 rounded-full px-6 py-3 text-xs font-semibold tracking-wide text-on-primary uppercase"
              >
                Ver serviços disponíveis
                <Icon name="arrowRight" size={14} />
              </Link>
            </div>
          ) : (
          <>
          <div className="mt-6">
            <label
              htmlFor="unit"
              className="block text-sm font-semibold text-on-surface"
            >
              Unidade <span className="text-primary">*</span>
            </label>
            <p className="mt-1 text-xs text-on-surface-variant">
              {product.method === "linha" ||
              product.method === "esfoliacao" ||
              product.method === "presente" ||
              product.method === "produto"
                ? "Campo obrigatório. Disponível em todas as unidades."
                : product.method === "laser"
                  ? "Campo obrigatório. Só unidades com laser neste público."
                  : product.method === "plano"
                    ? "Campo obrigatório. Unidades que oferecem este plano."
                    : "Campo obrigatório. Só unidades com este serviço neste público."}
            </p>
            <select
              id="unit"
              data-pm-unit
              required
              value={unitId}
              onChange={(event) => {
                setUnitId(event.target.value);
                if (event.target.value) setUnitError("");
              }}
              className={`mt-2 w-full rounded-xl border bg-surface-container-low px-4 py-3 text-on-surface outline-none ${
                unitError ? "border-primary" : "border-outline/50"
              }`}
            >
              <option value="">Selecione a unidade</option>
              {Object.entries(unitsByState).map(([state, units]) => (
                <optgroup key={state} label={state}>
                  {units.map((unit) => {
                    const link = bridge?.units?.[unit.id];
                    return (
                      <option
                        key={unit.id}
                        value={unit.id}
                        data-region={unit.priceRegion}
                        data-variation={link?.variationId ?? ""}
                        data-woo-option={link?.option ?? ""}
                        data-unit-name={unit.name}
                        data-city={unit.city}
                        data-state={unit.state}
                      >
                        {unit.name} — {unit.city}
                      </option>
                    );
                  })}
                </optgroup>
              ))}
            </select>
            {availableUnits.length === 0 ? (
              <p className="mt-2 text-sm text-primary">
                Este serviço ainda não está disponível para agendamento online.
              </p>
            ) : null}
            {selectedUnit ? (
              <p className="mt-2 inline-flex items-start gap-2 text-xs text-on-surface-variant">
                <Icon name="mapPin" size={14} className="mt-0.5 shrink-0 text-primary" />
                {selectedUnit.address} · {selectedUnit.hours}
              </p>
            ) : null}
            {unitError ? (
              <p data-pm-unit-error className="mt-2 text-sm text-primary">
                {unitError}
              </p>
            ) : (
              <p data-pm-unit-error className="mt-2 hidden text-sm text-primary">
                Escolha a unidade para continuar.
              </p>
            )}
            <p data-pm-added className="mt-3 hidden text-sm font-semibold text-primary" />
          </div>

          <div className="mt-5 flex flex-wrap items-center gap-3">
            <div className="inline-flex items-center rounded-full border border-outline/50">
              <button
                type="button"
                data-pm-dec
                className="flex h-11 w-11 items-center justify-center text-primary"
                aria-label="Diminuir quantidade"
                onClick={() => setQty((current) => Math.max(1, current - 1))}
              >
                <Icon name="minus" size={14} />
              </button>
              <span data-pm-qty className="min-w-7 text-center text-sm font-semibold">
                {qty}
              </span>
              <button
                type="button"
                data-pm-inc
                className="flex h-11 w-11 items-center justify-center text-primary"
                aria-label="Aumentar quantidade"
                onClick={() => setQty((current) => current + 1)}
              >
                <Icon name="plus" size={14} />
              </button>
            </div>
            <button
              type="button"
              data-pm-add
              onClick={handleAdd}
              className="btn-lux btn-lux-primary inline-flex min-w-[220px] flex-1 items-center justify-center gap-2 rounded-full py-3.5 text-sm font-semibold tracking-wide text-on-primary uppercase"
            >
              <Icon name="shoppingBag" size={16} />
              Adicionar ao carrinho
            </button>
          </div>
          </>
          )}
        </div>
      </div>

      {related.length > 0 ? (
        <section className="mt-14">
          <p className="font-label-md text-label-md text-primary uppercase">
            Você também pode gostar
          </p>
          <h2 className="mt-2 font-[family-name:var(--font-display)] text-headline-md text-primary">
            Outros serviços
          </h2>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {related.map((item) => (
              <Link
                key={item.id}
                href={`/produto/${item.id}`}
                className="group overflow-hidden rounded-2xl bg-surface shadow-[0_18px_40px_rgba(58,10,60,0.08)]"
              >
                <div className="relative aspect-[4/5] bg-surface-container-high">
                  <Image
                    src={item.image}
                    alt={item.imageAlt}
                    fill
                    className="object-cover transition-transform duration-700 group-hover:scale-105"
                    sizes="(max-width: 640px) 92vw, (max-width: 1024px) 45vw, 22vw"
                  />
                </div>
                <div className="p-4">
                  <h3 className="font-[family-name:var(--font-display)] text-lg text-on-surface">
                    {item.name}
                  </h3>
                  <p className="mt-1 text-sm font-semibold text-primary">
                    {(() => {
                      const parcel = getInstallment(item.priceCents, item.method);
                      return parcel.times > 1
                        ? `${parcel.times}x ${formatBRL(parcel.installmentCents)}`
                        : formatBRL(item.priceCents);
                    })()}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        </section>
      ) : null}

      {aboutLong ? (
        <section className="mt-14 max-w-3xl">
          <p className="font-label-md text-label-md text-primary uppercase">Descrição</p>
          <h2 className="mt-2 font-[family-name:var(--font-display)] text-headline-md text-primary">
            Sobre o serviço
          </h2>
          <p
            data-pm-long
            data-pm-chars={aboutLong.length}
            className={`mt-4 whitespace-pre-line text-body-md text-on-surface ${
              aboutClamped ? "pm-clamp" : ""
            }`}
          >
            {aboutLong.split(/(https?:\/\/[^\s]+|\/(?:images|docs)\/[^\s]+)/g).map((part, index) =>
              /^(https?:\/\/|\/(?:images|docs)\/)/.test(part) ? (
                <a
                  key={`doc-${index}`}
                  href={part}
                  target="_blank"
                  rel="noreferrer"
                  className="font-semibold text-primary underline underline-offset-2"
                >
                  {part}
                </a>
              ) : (
                <span key={`txt-${index}`}>{part}</span>
              ),
            )}
          </p>
          {aboutLong.length > 280 ? (
            <button
              type="button"
              data-pm-more-toggle
              className="mt-4 text-sm font-semibold text-primary"
              onClick={() => setAboutOpen((open) => !open)}
            >
              {aboutOpen ? "Ler menos" : "Ler mais"}
            </button>
          ) : null}
        </section>
      ) : null}
    </main>
  );
}
