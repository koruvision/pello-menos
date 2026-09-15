"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import { Icon } from "@/components/Icon";
import { useStore } from "@/components/StoreProvider";
import { formatBRL } from "@/lib/data";

export function CartView() {
  const {
    cartItems,
    cartCount,
    subtotalCents,
    setQty,
    setAllQty,
    removeFromCart,
    clearCart,
  } = useStore();
  const [bulkQty, setBulkQty] = useState("1");
  const cartUnit = cartItems[0]?.unit;
  const mixedUnits = cartItems.some((item) => item.unit.id !== cartUnit?.id);
  const qtyInvalid = cartItems.some((item) => item.qty > 1);
  const canCheckout = !mixedUnits && !qtyInvalid;

  if (cartItems.length === 0) {
    return (
      <main className="mx-auto flex max-w-lg flex-col items-center px-container-margin py-20 text-center">
        <span className="flex h-20 w-20 items-center justify-center rounded-full bg-surface-container-low text-primary">
          <Icon name="shoppingCart" size={32} />
        </span>
        <h1 className="mt-6 font-[family-name:var(--font-display)] text-headline-md text-primary">
          Seu carrinho está vazio
        </h1>
        <p className="mt-2 text-on-surface-variant">
          Escolha um serviço na home para montar o pedido.
        </p>
        <Link
          href="/"
          className="btn-lux btn-lux-primary mt-8 inline-flex items-center gap-2 rounded-full px-8 py-3 font-label-md text-label-md text-on-primary uppercase"
        >
          Ver produtos
          <Icon name="arrowRight" size={16} />
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-6xl px-container-margin py-10">
      <p className="font-label-md text-label-md text-secondary uppercase">
        Pedido
      </p>
      <h1 className="mt-2 font-[family-name:var(--font-display)] text-headline-md text-primary md:text-headline-lg">
        Carrinho
      </h1>
      <p className="mt-1 text-on-surface-variant">
        {cartCount} {cartCount === 1 ? "item" : "itens"}
        {cartUnit ? ` · ${cartUnit.name}` : ""}
      </p>
      {mixedUnits ? (
        <p className="mt-4 rounded-2xl border border-primary/30 bg-surface-container-low px-4 py-3 text-sm text-primary">
          Há serviços de unidades diferentes. Esvazie o carrinho ou mantenha só
          uma loja para finalizar.
        </p>
      ) : null}
      {qtyInvalid ? (
        <div className="mt-4 rounded-2xl border border-primary/30 bg-surface-container-low px-4 py-4 text-sm text-primary">
          <p>
            Não dá para finalizar com mais de 1 unidade por serviço. Cada item
            precisa ficar com quantidade 1.
          </p>
          <label className="mt-3 block text-xs font-semibold uppercase tracking-wide text-on-surface">
            Alterar a quantidade de todos os itens
          </label>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <input
              type="number"
              min={1}
              step={1}
              value={bulkQty}
              onChange={(event) => setBulkQty(event.target.value)}
              className="w-24 rounded-xl border border-outline/50 bg-surface px-3 py-2 text-on-surface outline-none"
              aria-label="Quantidade para todos os itens"
            />
            <button
              type="button"
              onClick={() => {
                const next = Math.max(1, Number.parseInt(bulkQty, 10) || 1);
                setBulkQty(String(next));
                setAllQty(next);
              }}
              className="rounded-full bg-primary px-4 py-2 text-xs font-semibold text-on-primary uppercase"
            >
              Aplicar em todos
            </button>
          </div>
        </div>
      ) : null}
      <div className="mt-8 grid gap-8 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="space-y-4">
          {cartItems.map((item) => (
            <article
              key={item.lineId}
              className="flex gap-4 rounded-2xl bg-surface p-4 shadow-[0_18px_40px_rgba(58,10,60,0.08)]"
            >
              <Link
                href={`/produto/${item.product.id}`}
                className="relative h-28 w-24 shrink-0 overflow-hidden rounded-xl"
              >
                <Image
                  src={item.product.image}
                  alt={item.product.imageAlt}
                  fill
                  className="object-cover"
                  sizes="96px"
                />
              </Link>
              <div className="min-w-0 flex-1">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <Link href={`/produto/${item.product.id}`}>
                      <h2 className="font-[family-name:var(--font-display)] text-xl text-on-surface hover:text-primary">
                        {item.product.name}
                      </h2>
                    </Link>
                    <p className="mt-0.5 text-sm text-on-surface-variant">
                      {item.product.duration}
                    </p>
                    <p className="mt-1 text-xs text-on-surface-variant">
                      Unidade: {item.unit.name} · {item.unit.city}/{item.unit.state}
                    </p>
                    <p className="text-[11px] text-on-surface-variant">
                      SKU {item.product.sku}
                    </p>
                  </div>
                  <button
                    type="button"
                    className="rounded-full p-2 text-on-surface-variant hover:bg-surface-container-low hover:text-primary"
                    aria-label="Remover"
                    onClick={() => removeFromCart(item.lineId)}
                  >
                    <Icon name="trash" size={16} />
                  </button>
                </div>
                <p className="mt-2 font-semibold text-primary">
                  {formatBRL(item.product.priceCents)}
                </p>
                <div className="mt-3 inline-flex items-center rounded-full border border-outline/50">
                  <button
                    type="button"
                    className="flex h-9 w-9 items-center justify-center text-primary"
                    aria-label="Diminuir"
                    onClick={() => setQty(item.lineId, item.qty - 1)}
                  >
                    <Icon name="minus" size={14} />
                  </button>
                  <span className="min-w-6 text-center text-sm font-semibold">
                    {item.qty}
                  </span>
                  <button
                    type="button"
                    className="flex h-9 w-9 items-center justify-center text-primary"
                    aria-label="Aumentar"
                    onClick={() => setQty(item.lineId, item.qty + 1)}
                  >
                    <Icon name="plus" size={14} />
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
        <aside className="h-fit rounded-2xl bg-surface p-6 shadow-[0_18px_40px_rgba(58,10,60,0.08)] lg:sticky lg:top-40">
          <h2 className="font-[family-name:var(--font-display)] text-2xl text-primary">
            Resumo
          </h2>
          <div className="mt-5 space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-on-surface-variant">Subtotal</span>
              <span className="font-semibold">{formatBRL(subtotalCents)}</span>
            </div>
          </div>
          <div className="mt-5 flex justify-between border-t border-outline/40 pt-5">
            <span className="font-semibold">Total</span>
            <span className="font-[family-name:var(--font-display)] text-2xl text-primary">
              {formatBRL(subtotalCents)}
            </span>
          </div>
          {mixedUnits ? (
            <button
              type="button"
              onClick={clearCart}
              className="mt-3 w-full text-sm text-primary underline"
            >
              Esvaziar carrinho
            </button>
          ) : null}
          <Link
            href="/"
            className="mt-4 flex w-full items-center justify-center rounded-full border border-primary/30 py-3 text-sm font-semibold text-primary uppercase"
          >
            Continuar comprando
          </Link>
          {canCheckout ? (
            <Link
              href="/checkout"
              className="btn-lux btn-lux-gold mt-3 flex w-full items-center justify-center gap-2 rounded-full py-3.5 font-label-md text-label-md text-on-secondary-container uppercase"
            >
              Ir para o pagamento
              <Icon name="arrowRight" size={16} />
            </Link>
          ) : (
            <p className="mt-3 rounded-2xl bg-surface-container-low px-3 py-3 text-center text-xs text-primary">
              Ajuste a quantidade para 1 em todos os itens para ir ao pagamento.
            </p>
          )}
        </aside>
      </div>
    </main>
  );
}
