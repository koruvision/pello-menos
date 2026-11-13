"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Icon } from "@/components/Icon";
import { useStore } from "@/components/StoreProvider";
import {
  campaignDiscountLabel,
  cartRecommendations,
  formatBRL,
  getProductById,
  isComingSoon,
  multiAreaHint,
  priceProductInCart,
  type CartLineLike,
} from "@/lib/data";
import { couponErrorMessage } from "@/lib/coupons";
import { productBridge, quoteFor } from "@/lib/woo-bridge";

type PmWoo = {
  applyCoupon?: (code: string) => Promise<unknown>;
  removeCoupon?: (code: string) => Promise<unknown>;
  getCart?: () => Promise<{
    coupons?: Array<{ code?: string } | string>;
    totals?: Record<string, string | number>;
    items?: Array<{
      key?: string;
      id?: number | string;
      quantity?: number;
      totals?: { line_subtotal?: string; line_total?: string };
      prices?: { price?: string };
    }>;
  }>;
  totalsCents?: (data: unknown) => {
    subtotal: number;
    discount: number;
    total: number;
  };
  lineUnitCents?: (line: unknown) => number;
  couponCodesFromCart?: (data: unknown) => string[];
  couponRuleFromCart?: (data: unknown) => CouponRule | null;
  displayDiscountCents?: (rule: CouponRule | null, subtotalCents: number) => number;
  writeSavedCoupons?: (codes: string[]) => string[];
};

/** Regra do cupom devolvida por `pmWoo.couponRuleFromCart` (product.js). */
type CouponRule = {
  code: string;
  type: string;
  percent: number;
  fixedCents: number;
  targetCents?: number;
  catalogIds?: string[];
};

/** Desconto de vitrine: percentual sobre o subtotal exibido (recalcula a cada mudança). */
function displayDiscountFor(rule: CouponRule | null, subtotalCents: number): number {
  if (!rule) return 0;
  const subtotal = Math.max(0, Math.round(subtotalCents));
  if (rule.type === "target_total") {
    const target = Math.max(0, Math.round(rule.targetCents ?? 100));
    return Math.max(0, subtotal - target);
  }
  if (rule.type === "fixed_cart") return Math.min(subtotal, Math.max(0, rule.fixedCents));
  if (rule.percent > 0) return Math.min(subtotal, Math.round((subtotal * rule.percent) / 100));
  return Math.min(subtotal, Math.max(0, rule.fixedCents));
}

/** Cupom longo no resumo: corta e coloca "..." (ex.: PM1L47SQ9A…). */
function shortCouponCode(code: string, maxLen = 10): string {
  const s = String(code || "").toUpperCase();
  if (s.length <= maxLen) return s;
  return `${s.slice(0, maxLen)}...`;
}

declare global {
  interface Window {
    pmWoo?: PmWoo;
  }
}

const cartShellClass =
  "mx-auto flex min-h-[100dvh] w-full max-w-xl flex-col items-center justify-center px-container-margin py-10 text-center";

export function CartView() {
  const {
    cartItems,
    cartCount,
    subtotalCents,
    setQty,
    removeFromCart,
    clearCart,
    addToCart,
    patchCartPrices,
  } = useStore();
  const [ready, setReady] = useState(false);
  const [upsellBusy, setUpsellBusy] = useState(false);
  const [relatedBusyId, setRelatedBusyId] = useState<string | null>(null);
  const [couponCode, setCouponCode] = useState("");
  const [couponBusy, setCouponBusy] = useState(false);
  const [couponError, setCouponError] = useState("");
  const [appliedCoupons, setAppliedCoupons] = useState<string[]>([]);
  const [couponRule, setCouponRule] = useState<CouponRule | null>(null);
  const [wooTotal, setWooTotal] = useState<number | null>(null);

  useEffect(() => {
    setReady(true);
  }, []);
  const cartUnit = cartItems[0]?.unit;
  const mixedUnits = cartItems.some((item) => item.unit.id !== cartUnit?.id);
  const canCheckout = !mixedUnits;
  const splashAudience = cartItems[0]?.product.audience ?? "feminino";
  const splash =
    getProductById(
      splashAudience === "masculino" ? "body-splash-livre-masc" : "body-splash-livre",
    ) || getProductById("body-splash-livre");
  const splashBridge = productBridge("body-splash-livre");
  const splashInCart = cartItems.some((item) =>
    item.product.id.includes("body-splash"),
  );
  // Body Splash fora do cross-sell até o lançamento (01/12) — ver BODY_SPLASH_FOR_SALE.
  const showUpsell = Boolean(
    splash && splashBridge?.productId && cartUnit && !isComingSoon(splash.id),
  );
  /** Preço do Body Splash no carrinho (R$ 85,90 com 5% OFF = R$ 81,61). */
  const splashUpsellCents = splash?.priceCents ?? 8161;
  const related = cartRecommendations(
    cartItems.map((item) => item.product.id),
    3,
  );
  const linesCamp: CartLineLike[] = useMemo(
    () =>
      cartItems.map((item) => ({
        id: item.product.id,
        method: item.product.method,
      })),
    [cartItems],
  );
  const pricedLines = useMemo(
    () =>
      cartItems.map((item) => {
        if (item.product.id.includes("body-splash")) {
          return {
            lineId: item.lineId,
            saleCents: splashUpsellCents,
            listCents: 8590,
            qty: item.qty,
          };
        }
        const campaign = priceProductInCart(item.product, linesCamp);
        const sale = campaign.priceCents > 0 ? campaign.priceCents : item.product.priceCents;
        const list =
          campaign.oldPriceCents && campaign.oldPriceCents > 0
            ? campaign.oldPriceCents
            : item.product.originalCents || sale;
        return { lineId: item.lineId, saleCents: sale, listCents: list, qty: item.qty };
      }),
    [cartItems, linesCamp, splashUpsellCents],
  );
  const listSubtotal = pricedLines.reduce((sum, row) => sum + row.listCents * row.qty, 0);
  const saleSubtotal = pricedLines.reduce((sum, row) => sum + row.saleCents * row.qty, 0);
  const campaignSavings = Math.max(0, listSubtotal - saleSubtotal);
  const campaignLabel =
    campaignDiscountLabel() ||
    (campaignSavings > 0 ? "Desconto e-commerce (5%)" : null);
  const displaySubtotal = listSubtotal > 0 ? listSubtotal : saleSubtotal;
  const blackHints = useMemo(() => {
    const out: string[] = [];
    for (const fam of ["laser", "cera_esf"] as const) {
      const hint = multiAreaHint(linesCamp, fam);
      if (hint && hint.need > 0) {
        out.push(
          `Adicione mais ${hint.need} área${hint.need === 1 ? "" : "s"} diferente${hint.need === 1 ? "" : "s"} de ${hint.label} para liberar ${Math.round(hint.nextRate * 100)}% OFF.`,
        );
      }
    }
    return out;
  }, [linesCamp]);
  const couponBase = useMemo(() => {
    if (couponRule?.type !== "target_total" || !couponRule.catalogIds?.length) {
      return saleSubtotal;
    }
    const allowed = new Set(couponRule.catalogIds);
    return cartItems.reduce((sum, item, index) => {
      if (!allowed.has(item.product.id)) return sum;
      const row = pricedLines[index];
      return sum + (row?.saleCents || 0) * item.qty;
    }, 0);
  }, [cartItems, couponRule, pricedLines, saleSubtotal]);
  const wooDiscount = useMemo(
    () => displayDiscountFor(couponRule, couponBase),
    [couponRule, couponBase],
  );
  const couponLabel = couponRule
    ? couponRule.percent > 0
      ? `Desconto (${shortCouponCode(couponRule.code)} · ${String(couponRule.percent).replace(".", ",")}%)`
      : `Desconto (${shortCouponCode(couponRule.code)})`
    : "Desconto";
  const displayTotal = Math.max(0, saleSubtotal - wooDiscount);

  function syncFromWoo(data: unknown) {
    const pm = window.pmWoo;
    if (!pm) return;
    const codes = pm.couponCodesFromCart?.(data) || [];
    const totals = pm.totalsCents?.(data);
    setAppliedCoupons(codes);
    setCouponRule(pm.couponRuleFromCart?.(data) ?? null);
    setWooTotal(totals ? totals.total : null);
    pm.writeSavedCoupons?.(codes);

    // Woo no oficialteste cobra R$ 1,00 de teste. Vitrine = campanha Black ou catálogo.
    const lines: CartLineLike[] = cartItems.map((item) => ({
      id: item.product.id,
      method: item.product.method,
    }));
    const updates: Array<{ lineId: string; priceCents: number }> = [];
    for (const item of cartItems) {
      if (item.product.id.includes("body-splash")) {
        if (item.product.priceCents !== splashUpsellCents) {
          updates.push({ lineId: item.lineId, priceCents: splashUpsellCents });
        }
        continue;
      }
      const campaign = priceProductInCart(item.product, lines);
      let sale = campaign.priceCents;
      const bridgeSale = quoteFor(item.product, item.unit.priceRegion).saleCents;
      // Fora da campanha, bridge regional pode sobrescrever; na campanha o % Black manda.
      if (campaign.discountRate == null && bridgeSale > 100) {
        sale = bridgeSale;
      }
      if (sale > 0 && sale !== item.product.priceCents) {
        updates.push({ lineId: item.lineId, priceCents: sale });
      }
    }
    if (updates.length) patchCartPrices(updates);
  }

  useEffect(() => {
    const lines: CartLineLike[] = cartItems.map((item) => ({
      id: item.product.id,
      method: item.product.method,
    }));
    const updates: Array<{ lineId: string; priceCents: number }> = [];
    for (const item of cartItems) {
      if (item.product.id.includes("body-splash")) continue;
      const campaign = priceProductInCart(item.product, lines);
      if (campaign.priceCents > 0 && campaign.priceCents !== item.product.priceCents) {
        updates.push({ lineId: item.lineId, priceCents: campaign.priceCents });
      }
    }
    if (updates.length) patchCartPrices(updates);
  }, [cartItems, patchCartPrices]);

  useEffect(() => {
    const pm = window.pmWoo;
    if (!pm?.getCart) return;
    let cancelled = false;
    pm.getCart()
      .then((data) => {
        if (!cancelled) syncFromWoo(data);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [cartItems.length, subtotalCents]);

  if (!ready) {
    return (
      <main data-pm-cart-page data-pm-cart-state="loading" className={cartShellClass}>
        <span
          className="block h-11 w-11 rounded-full border-[3px] border-primary/20 border-t-primary"
          style={{ animation: "pm-cart-spin 0.75s linear infinite" }}
          aria-hidden
        />
        <p className="mt-5 text-sm text-on-surface-variant" role="status">
          Carregando carrinho…
        </p>
        <style>{`@keyframes pm-cart-spin{to{transform:rotate(360deg)}}`}</style>
      </main>
    );
  }

  if (cartItems.length === 0) {
    return (
      <main data-pm-cart-page data-pm-cart-state="empty" className={cartShellClass}>
        <span className="flex h-20 w-20 items-center justify-center rounded-full bg-surface-container-low text-primary md:h-24 md:w-24">
          <Icon name="shoppingCart" size={32} />
        </span>
        <h1 className="mt-6 w-full max-w-md px-2 font-[family-name:var(--font-display)] text-headline-md leading-snug text-primary md:text-headline-lg">
          Seu carrinho está vazio
        </h1>
        <p className="mt-3 max-w-sm text-body-md text-on-surface-variant md:max-w-md md:text-body-lg">
          Escolha um serviço na home para montar o pedido.
        </p>
        <Link
          href="/"
          className="btn-lux btn-lux-primary mt-8 inline-flex items-center gap-2 rounded-full px-8 py-3 font-label-md text-label-md text-on-primary uppercase md:mt-10 md:px-10 md:py-3.5"
        >
          Ver produtos
          <Icon name="arrowRight" size={16} />
        </Link>
      </main>
    );
  }

  return (
    <main data-pm-cart-page className="mx-auto max-w-6xl px-container-margin py-10">
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
      {blackHints.length > 0 ? (
        <p
          className="mt-3 rounded-xl bg-surface-container-low px-4 py-3 text-sm text-on-surface"
          data-pm-black-hint
        >
          {blackHints.map((line, i) => (
            <span key={line}>
              {i > 0 ? <br /> : null}
              {line}
            </span>
          ))}
        </p>
      ) : null}
      {mixedUnits ? (
        <p className="mt-4 rounded-2xl border border-primary/30 bg-surface-container-low px-4 py-3 text-sm text-primary">
          Há serviços de unidades diferentes. Esvazie o carrinho ou mantenha só
          uma loja para finalizar.
        </p>
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
                  {(() => {
                    const row = pricedLines.find((p) => p.lineId === item.lineId);
                    const sale = row?.saleCents ?? item.product.priceCents;
                    const list = row?.listCents ?? item.product.originalCents;
                    if (list > sale && sale > 0) {
                      return (
                        <>
                          <span className="text-sm font-normal text-on-surface-variant line-through">
                            {formatBRL(list)}
                          </span>{" "}
                          <span>{formatBRL(sale)}</span>
                        </>
                      );
                    }
                    return formatBRL(sale);
                  })()}
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
          {related.length > 0 && cartUnit ? (
            <section
              data-pm-cart-upsell
              className="mt-8 border-t border-outline/40 pt-8"
            >
              <p className="font-label-md text-label-md text-secondary uppercase">
                Os mais pedidos
              </p>
              <h2 className="mt-1 font-[family-name:var(--font-display)] text-2xl text-primary">
                Adicione também
              </h2>
              <p className="mt-1 text-sm text-on-surface-variant">
                Sugestões com base no seu carrinho · {cartUnit.name}
              </p>
              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                {related.map((product, index) => (
                  <article
                    key={product.id}
                    className={`flex flex-col overflow-hidden rounded-2xl bg-surface shadow-[0_12px_28px_rgba(58,10,60,0.08)]${index > 0 ? " hidden sm:flex" : ""}`}
                  >
                    <Link
                      href={`/produto/${product.id}`}
                      className="relative aspect-[4/5] overflow-hidden bg-surface-container-high"
                    >
                      <Image
                        src={product.image}
                        alt={product.imageAlt}
                        fill
                        className="object-cover"
                        sizes="(max-width: 640px) 100vw, 200px"
                      />
                    </Link>
                    <div className="flex flex-1 flex-col gap-2 p-3">
                      <Link href={`/produto/${product.id}`}>
                        <h3 className="font-[family-name:var(--font-display)] text-base leading-snug text-on-surface hover:text-primary">
                          {product.name}
                        </h3>
                      </Link>
                      <p className="text-xs text-on-surface-variant">
                        {product.duration}
                      </p>
                      <p className="mt-auto font-semibold text-primary">
                        {formatBRL(product.priceCents)}
                      </p>
                      <button
                        type="button"
                        disabled={relatedBusyId === product.id}
                        onClick={() => {
                          if (!cartUnit || relatedBusyId) return;
                          setRelatedBusyId(product.id);
                          addToCart(product, cartUnit, 1);
                          window.setTimeout(() => setRelatedBusyId(null), 400);
                        }}
                        className="btn-lux btn-lux-primary mt-1 inline-flex w-full items-center justify-center gap-2 rounded-full px-3 py-2 text-xs font-semibold text-on-primary uppercase disabled:opacity-60"
                      >
                        {relatedBusyId === product.id ? (
                          "carregando"
                        ) : (
                          <>
                            <Icon name="shoppingBag" size={15} />
                            Adicionar
                          </>
                        )}
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          ) : null}
        </div>
        <aside className="h-fit rounded-2xl bg-surface p-6 shadow-[0_18px_40px_rgba(58,10,60,0.08)] lg:sticky lg:top-40">
          <h2 className="font-[family-name:var(--font-display)] text-2xl text-primary">
            Resumo
          </h2>
          <div className="mt-5 space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-on-surface-variant">Subtotal</span>
              <span className="font-semibold">{formatBRL(displaySubtotal)}</span>
            </div>
            {campaignSavings > 0 && campaignLabel ? (
              <div className="flex justify-between text-primary">
                <span>{campaignLabel}</span>
                <span className="font-semibold">−{formatBRL(campaignSavings)}</span>
              </div>
            ) : null}
            {wooDiscount > 0 ? (
              <div className="flex justify-between gap-3 text-primary">
                <span className="min-w-0 truncate" title={couponRule?.code?.toUpperCase()}>
                  {couponLabel}
                </span>
                <span className="shrink-0 font-semibold">−{formatBRL(wooDiscount)}</span>
              </div>
            ) : null}
          </div>
          <div className="mt-5 flex justify-between border-t border-outline/40 pt-5">
            <span className="font-semibold">Total</span>
            <span className="font-[family-name:var(--font-display)] text-2xl text-primary">
              {formatBRL(displayTotal)}
            </span>
          </div>
          <div className="mt-5 border-t border-outline/40 pt-5">
            <p className="text-sm font-semibold text-on-surface">Cupom</p>
            <form
              className="mt-2 flex gap-2"
              onSubmit={(event) => {
                event.preventDefault();
                const pm = window.pmWoo;
                const code = couponCode.trim();
                if (!code) {
                  setCouponError("Digite o código do cupom.");
                  return;
                }
                if (!pm?.applyCoupon) {
                  setCouponError(
                    "Cupom Woo disponível na loja publicada. Cadastre cupons em Marketing → Cupons.",
                  );
                  return;
                }
                setCouponBusy(true);
                setCouponError("");
                pm
                  .applyCoupon(code)
                  .then((data) => {
                    syncFromWoo(data);
                    setCouponCode("");
                  })
                  .catch((error: unknown) => {
                    setCouponError(couponErrorMessage(error, code));
                  })
                  .finally(() => setCouponBusy(false));
              }}
            >
              <input
                type="text"
                value={couponCode}
                onChange={(event) => setCouponCode(event.target.value)}
                placeholder="Código do cupom"
                autoComplete="off"
                className="min-w-0 flex-1 rounded-full border border-primary/25 px-4 py-2.5 text-sm text-on-surface outline-none focus:border-primary"
              />
              <button
                type="submit"
                disabled={couponBusy}
                className="btn-lux btn-lux-primary shrink-0 rounded-full px-4 py-2.5 text-xs font-semibold text-on-primary uppercase disabled:opacity-60"
              >
                {couponBusy ? "…" : "Aplicar"}
              </button>
            </form>
            {couponError ? (
              <p className="mt-2 text-xs text-primary">{couponError}</p>
            ) : null}
            {appliedCoupons.length > 0 ? (
              <ul className="mt-1">
                {appliedCoupons.map((code) => (
                  <li
                    key={code}
                    className="mt-2 flex items-center justify-between gap-2 rounded-xl bg-surface-container-low px-3 py-2 text-xs"
                  >
                    <span
                      className="min-w-0 truncate font-semibold text-primary uppercase"
                      title={code.toUpperCase()}
                    >
                      {shortCouponCode(code, 16)}
                    </span>
                    <button
                      type="button"
                      className="shrink-0 text-on-surface-variant underline"
                      onClick={() => {
                        const pm = window.pmWoo;
                        if (!pm?.removeCoupon) return;
                        setCouponBusy(true);
                        pm
                          .removeCoupon(code)
                          .then((data) => syncFromWoo(data))
                          .catch(() => {
                            setCouponError("Não foi possível remover o cupom.");
                          })
                          .finally(() => setCouponBusy(false));
                      }}
                    >
                      Remover
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
          <button
            type="button"
            onClick={clearCart}
            className="mt-3 w-full text-sm text-primary underline"
          >
            Esvaziar carrinho
          </button>
          <Link
            href="/"
            className="mt-4 flex w-full items-center justify-center rounded-full border border-primary/30 py-3 text-sm font-semibold text-primary uppercase"
          >
            Continuar comprando
          </Link>
          {showUpsell && splash && cartUnit ? (
            <div className="mt-4 rounded-2xl border border-primary/20 bg-surface-container-low p-4">
              <p className="text-sm font-semibold text-primary">
                Complete sua compra com Body Splash!
              </p>
              <p className="mt-1 text-xs text-on-surface-variant">
                Adicione seu favorito ao pedido com apenas um clique.
              </p>
              <div className="mt-3 flex gap-3">
                <span className="relative h-16 w-14 shrink-0 overflow-hidden rounded-xl bg-white">
                  <Image
                    src={splash.image}
                    alt={splash.imageAlt}
                    fill
                    className="object-cover"
                    sizes="56px"
                  />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold text-on-surface">
                    {splash.name}
                  </p>
                  <p className="mt-0.5 font-semibold text-primary">
                    {formatBRL(splashUpsellCents)}
                  </p>
                  {splashInCart ? (
                    <p className="mt-2 text-xs font-semibold text-primary">
                      Já no carrinho
                    </p>
                  ) : (
                    <button
                      type="button"
                      disabled={upsellBusy}
                      onClick={() => {
                        if (upsellBusy) return;
                        setUpsellBusy(true);
                        addToCart(
                          { ...splash, priceCents: splashUpsellCents },
                          cartUnit,
                          1,
                        );
                        window.setTimeout(() => setUpsellBusy(false), 400);
                      }}
                      className="btn-lux btn-lux-primary mt-2 inline-flex w-full items-center justify-center gap-2 rounded-full px-3 py-2 text-xs font-semibold text-on-primary uppercase disabled:opacity-60"
                    >
                      {upsellBusy ? (
                        "carregando"
                      ) : (
                        <>
                          <Icon name="shoppingBag" size={15} />
                          Adicionar ao carrinho
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ) : null}
          {canCheckout ? (
            <Link
              href="/finalizar-pagamento"
              className="btn-lux btn-lux-gold mt-3 flex w-full items-center justify-center gap-2 rounded-full py-3.5 font-label-md text-label-md text-on-secondary-container uppercase"
            >
              <Icon name="shoppingCart" size={16} />
              Ir para o pagamento
            </Link>
          ) : (
            <p className="mt-3 rounded-2xl bg-surface-container-low px-3 py-3 text-center text-xs text-primary">
              Mantenha só uma unidade para ir ao pagamento.
            </p>
          )}
        </aside>
      </div>
    </main>
  );
}
