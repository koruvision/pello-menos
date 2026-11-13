"use client";

import Image from "next/image";
import Link from "next/link";
import { useMemo, useState } from "react";
import { Icon } from "@/components/Icon";
import { useStore } from "@/components/StoreProvider";
import {
  campaignDiscountLabel,
  formatBRL,
  priceProductInCart,
  type CartLineLike,
} from "@/lib/data";

function Steps({ current }: { current: 1 | 2 | 3 }) {
  const steps = ["Carrinho", "Pagamento", "Confirmação"];
  return (
    <ol className="mb-8 flex items-center gap-2 text-xs tracking-wide uppercase">
      {steps.map((label, index) => {
        const step = (index + 1) as 1 | 2 | 3;
        const active = step <= current;
        return (
          <li key={label} className="flex items-center gap-2">
            {index > 0 ? (
              <span className="h-px w-6 bg-outline/60 md:w-10" />
            ) : null}
            <span
              className={
                active
                  ? "flex h-6 w-6 items-center justify-center rounded-full bg-primary text-[10px] text-on-primary"
                  : "flex h-6 w-6 items-center justify-center rounded-full border border-outline text-[10px] text-on-surface-variant"
              }
            >
              {step}
            </span>
            <span
              className={
                active
                  ? "hidden font-semibold text-primary sm:inline"
                  : "hidden text-on-surface-variant sm:inline"
              }
            >
              {label}
            </span>
          </li>
        );
      })}
    </ol>
  );
}

export function CheckoutView() {
  const { cartItems } = useStore();
  const [done, setDone] = useState(false);
  const unit = cartItems[0]?.unit;

  const linesCamp: CartLineLike[] = useMemo(
    () =>
      cartItems.map((item) => ({
        id: item.product.id,
        method: item.product.method,
      })),
    [cartItems],
  );
  const summary = useMemo(() => {
    let list = 0;
    let sale = 0;
    for (const item of cartItems) {
      if (item.product.id.includes("body-splash")) {
        list += 8590 * item.qty;
        sale += (item.product.priceCents || 8161) * item.qty;
        continue;
      }
      const campaign = priceProductInCart(item.product, linesCamp);
      const saleUnit = campaign.priceCents > 0 ? campaign.priceCents : item.product.priceCents;
      const listUnit =
        campaign.oldPriceCents && campaign.oldPriceCents > 0
          ? campaign.oldPriceCents
          : item.product.originalCents || saleUnit;
      list += listUnit * item.qty;
      sale += saleUnit * item.qty;
    }
    const campaignSavings = Math.max(0, list - sale);
    const campaignLabel =
      campaignDiscountLabel() ||
      (campaignSavings > 0 ? "Desconto e-commerce (5%)" : null);
    return {
      listSubtotal: list,
      saleSubtotal: sale,
      campaignSavings,
      campaignLabel,
    };
  }, [cartItems, linesCamp]);

  const hasPlan = cartItems.some((item) => item.product.method === "plano");
  const hasRetail = cartItems.some((item) => item.product.method === "produto");
  const paymentNote = hasPlan
    ? "Planos são cobrados no valor cheio, sem parcelamento."
    : "Parcela mínima de R$ 50. Em cera e esfoliação, até 3x; demais serviços, até 10x (igual à loja).";

  if (cartItems.length === 0 && !done) {
    return (
      <main className="mx-auto flex max-w-lg flex-col items-center px-container-margin py-20 text-center">
        <span className="flex h-20 w-20 items-center justify-center rounded-full bg-surface-container-low text-primary">
          <Icon name="creditCard" size={32} />
        </span>
        <h1 className="mt-6 font-[family-name:var(--font-display)] text-headline-md text-primary">
          Pagamento
        </h1>
        <p className="mt-2 text-on-surface-variant">
          Adicione produtos à sacola para ver o visual desta etapa.
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

  if (done) {
    return (
      <main className="mx-auto max-w-lg px-container-margin py-16 text-center">
        <Steps current={3} />
        <span className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container">
          <Icon name="check" size={36} />
        </span>
        <h1 className="mt-6 font-[family-name:var(--font-display)] text-headline-md text-primary">
          Pedido confirmado
        </h1>
        <p className="mt-2 text-on-surface-variant">
          Unidade: {unit?.name ?? "loja escolhida"}. Cartão final 4242.
        </p>
        <p className="mt-3 text-sm text-on-surface-variant">
          Compareça com documento. O tempo do serviço é só da execução — não
          inclui anamnese. Um e-mail de confirmação será enviado (simulação).
        </p>
        <Link
          href="/"
          className="btn-lux btn-lux-gold mt-8 inline-flex items-center gap-2 rounded-full px-8 py-3 font-label-md text-label-md text-on-secondary-container uppercase"
        >
          Voltar à home
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-6xl px-container-margin py-10">
      <Steps current={2} />
      <h1 className="font-[family-name:var(--font-display)] text-headline-md text-primary md:text-headline-lg">
        Pagamento
      </h1>
      <div className="mt-8 grid gap-8 lg:grid-cols-[minmax(0,1fr)_340px]">
        <form
          className="space-y-8 rounded-2xl bg-surface p-6 shadow-[0_18px_40px_rgba(58,10,60,0.08)] md:p-8"
          onSubmit={(event) => {
            event.preventDefault();
            setDone(true);
          }}
        >
          <section>
            <h2 className="mb-4 font-[family-name:var(--font-display)] text-2xl text-primary">
              Seus dados
            </h2>
            <div className="grid gap-4 md:grid-cols-2">
              <label className="block text-sm text-on-surface-variant">
                Nome
                <input
                  className="mt-1.5 w-full rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface"
                  defaultValue="Ana Souza"
                  readOnly
                />
              </label>
              <label className="block text-sm text-on-surface-variant">
                WhatsApp
                <input
                  className="mt-1.5 w-full rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface"
                  defaultValue="(11) 99999-0000"
                  readOnly
                />
              </label>
              <label className="block text-sm text-on-surface-variant">
                E-mail
                <input
                  className="mt-1.5 w-full rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface"
                  defaultValue="ana@email.com"
                  readOnly
                />
              </label>
              <label className="block text-sm text-on-surface-variant">
                CPF
                <input
                  className="mt-1.5 w-full rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface"
                  defaultValue="000.000.000-00"
                  readOnly
                />
              </label>
            </div>
          </section>
          <section>
            <h2 className="mb-4 font-[family-name:var(--font-display)] text-2xl text-primary">
              Pagamento
            </h2>
            <div className="flex items-center gap-3 rounded-2xl border border-primary bg-surface-container-low px-4 py-4">
              <Icon name="creditCard" size={22} />
              <span>
                <span className="block text-sm font-semibold">Cartão</span>
                <span className="text-xs text-on-surface-variant">
                  {paymentNote}
                </span>
              </span>
            </div>
          </section>
          <button
            type="submit"
            className="btn-lux btn-lux-gold w-full rounded-full py-3.5 font-label-md text-label-md text-on-secondary-container uppercase"
          >
            Finalizar compra
          </button>
        </form>
        <aside className="h-fit rounded-2xl bg-surface p-6 shadow-[0_18px_40px_rgba(58,10,60,0.08)] lg:sticky lg:top-40">
          <h2 className="font-[family-name:var(--font-display)] text-2xl text-primary">
            Pedido
          </h2>
          <ul className="mt-4 space-y-4">
            {cartItems.map((item) => (
              <li key={item.lineId} className="flex gap-3">
                <div className="relative h-16 w-14 overflow-hidden rounded-lg">
                  <Image
                    src={item.product.image}
                    alt={item.product.imageAlt}
                    fill
                    className="object-cover"
                    sizes="56px"
                  />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold">
                    {item.product.name}
                  </p>
                  <p className="text-xs text-on-surface-variant">
                    {item.unit.name}
                  </p>
                  <p className="text-xs text-on-surface-variant">
                    {item.qty}x {formatBRL(item.product.priceCents)}
                  </p>
                </div>
              </li>
            ))}
          </ul>
          {hasRetail ? (
            <p
              data-pm-pickup-note
              className="mt-4 inline-flex items-start gap-2 rounded-xl bg-secondary-container/60 px-3 py-2 text-xs text-on-secondary-container"
            >
              <Icon name="mapPin" size={14} className="mt-0.5 shrink-0" />
              <span>
                <strong>Body Splash: retirada na loja.</strong> Compra online com retirada na
                unidade {unit?.name ?? "escolhida"} — não enviamos pelos Correios.
              </span>
            </p>
          ) : null}
          <div className="mt-5 space-y-3 border-t border-outline/40 pt-4 text-sm">
            <div className="flex justify-between">
              <span className="text-on-surface-variant">Subtotal</span>
              <span className="font-semibold">{formatBRL(summary.listSubtotal)}</span>
            </div>
            {summary.campaignSavings > 0 && summary.campaignLabel ? (
              <div className="flex justify-between text-primary">
                <span>{summary.campaignLabel}</span>
                <span className="font-semibold">−{formatBRL(summary.campaignSavings)}</span>
              </div>
            ) : null}
            <div className="flex justify-between border-t border-outline/40 pt-4">
              <span className="font-semibold">Total</span>
              <span className="font-[family-name:var(--font-display)] text-2xl text-primary">
                {formatBRL(summary.saleSubtotal)}
              </span>
            </div>
          </div>
        </aside>
      </div>
    </main>
  );
}
