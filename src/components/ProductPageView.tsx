"use client";

import Image from "next/image";
import Link from "next/link";
import { useMemo, useState } from "react";
import { BadgeTag } from "@/components/BadgeTag";
import { Icon } from "@/components/Icon";
import { useStore } from "@/components/StoreProvider";
import {
  formatBRL,
  getInstallment,
  homeHref,
  installmentHint,
  productsHref,
  relatedProducts,
  storeUnits,
  type Product,
} from "@/lib/data";

type Props = {
  product: Product;
};

export function ProductPageView({ product }: Props) {
  const { addToCart } = useStore();
  const [unitId, setUnitId] = useState("");
  const [qty, setQty] = useState(1);
  const [unitError, setUnitError] = useState("");

  const related = useMemo(() => relatedProducts(product), [product]);
  const selectedUnit = storeUnits.find((unit) => unit.id === unitId);
  const installment = getInstallment(product.priceCents, product.method);

  function handleAdd() {
    if (!selectedUnit) {
      setUnitError("Escolha a unidade para continuar.");
      return;
    }
    setUnitError("");
    addToCart(product, selectedUnit, qty);
  }

  const discount =
    product.oldPriceCents && product.oldPriceCents > product.priceCents
      ? Math.round(
          (1 - product.priceCents / product.oldPriceCents) * 100,
        )
      : null;

  return (
    <main className="mx-auto max-w-6xl px-container-margin py-8 md:py-12">
      <nav className="text-xs text-on-surface-variant">
        <Link href={homeHref(product.audience)} className="hover:text-primary">
          Início
        </Link>
        <span className="px-2">/</span>
        <Link href={productsHref(product.audience)} className="hover:text-primary">
          Serviços
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
              className="object-cover"
              sizes="(max-width: 1024px) 92vw, 560px"
            />
            {product.badge ? (
              <div className="absolute top-4 left-4">
                <BadgeTag label={product.badge} />
              </div>
            ) : null}
          </div>
        </div>

        <div>
          <p className="font-label-md text-label-md text-secondary uppercase">
            {product.category}
          </p>
          <h1 className="mt-2 font-[family-name:var(--font-display)] text-headline-md text-primary md:text-headline-lg">
            {product.name}
          </h1>
          <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-on-surface-variant">
            <span className="inline-flex items-center gap-1.5">
              <Icon name="clock" size={15} />
              {product.duration}*
            </span>
            <span>SKU {product.sku}</span>
            <span>Cód. {product.code}</span>
          </div>

          <div className="mt-5 flex items-end gap-3">
            <p className="font-[family-name:var(--font-display)] text-4xl text-primary">
              {installment.times > 1
                ? `${installment.times}x de ${formatBRL(installment.installmentCents)}`
                : formatBRL(product.priceCents)}
            </p>
            {installment.times > 1 ? (
              <p className="pb-1 text-sm text-on-surface-variant">
                Total {formatBRL(product.priceCents)}
              </p>
            ) : null}
            {product.oldPriceCents ? (
              <p className="pb-1 text-sm text-on-surface-variant line-through">
                {formatBRL(product.oldPriceCents)}
              </p>
            ) : null}
            {discount ? (
              <span className="mb-1 rounded-full bg-secondary-container px-2.5 py-1 text-[11px] font-semibold text-on-secondary-container">
                -{discount}%
              </span>
            ) : null}
          </div>
          <p className="mt-1 text-xs text-on-surface-variant">
            {installmentHint(product.method)}
          </p>

          <p className="mt-5 text-body-md text-on-surface">{product.description}</p>
          <p className="mt-3 text-xs text-on-surface-variant">
            * Tempo médio só da execução do serviço; não inclui anamnese.
          </p>

          <div className="mt-6">
            <label
              htmlFor="unit"
              className="block text-sm font-semibold text-on-surface"
            >
              Unidade <span className="text-primary">*</span>
            </label>
            <p className="mt-1 text-xs text-on-surface-variant">
              Campo obrigatório. O serviço é atendido só na loja escolhida.
            </p>
            <select
              id="unit"
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
              {storeUnits.map((unit) => (
                <option key={unit.id} value={unit.id}>
                  {unit.name} — {unit.city}/{unit.state}
                </option>
              ))}
            </select>
            {selectedUnit ? (
              <p className="mt-2 inline-flex items-start gap-2 text-xs text-on-surface-variant">
                <Icon name="mapPin" size={14} className="mt-0.5 shrink-0 text-primary" />
                {selectedUnit.address} · {selectedUnit.hours}
              </p>
            ) : null}
            {unitError ? (
              <p className="mt-2 text-sm text-primary">{unitError}</p>
            ) : null}
          </div>

          <div className="mt-5 flex flex-wrap items-center gap-3">
            <div className="inline-flex items-center rounded-full border border-outline/50">
              <button
                type="button"
                className="flex h-11 w-11 items-center justify-center text-primary"
                aria-label="Diminuir quantidade"
                onClick={() => setQty((current) => Math.max(1, current - 1))}
              >
                <Icon name="minus" size={14} />
              </button>
              <span className="min-w-7 text-center text-sm font-semibold">
                {qty}
              </span>
              <button
                type="button"
                className="flex h-11 w-11 items-center justify-center text-primary"
                aria-label="Aumentar quantidade"
                onClick={() => setQty((current) => current + 1)}
              >
                <Icon name="plus" size={14} />
              </button>
            </div>
            <button
              type="button"
              onClick={handleAdd}
              className="btn-lux btn-lux-primary inline-flex min-w-[220px] flex-1 items-center justify-center gap-2 rounded-full py-3.5 text-sm font-semibold tracking-wide text-on-primary uppercase"
            >
              <Icon name="shoppingBag" size={16} />
              Adicionar ao carrinho
            </button>
          </div>
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
    </main>
  );
}
