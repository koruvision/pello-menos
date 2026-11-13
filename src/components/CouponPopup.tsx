"use client";

import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { Icon } from "@/components/Icon";
import { FIRST_PURCHASE_COUPON, FIRST_PURCHASE_PERCENT } from "@/lib/coupons";

gsap.registerPlugin(useGSAP);

/**
 * Pop-up dividido (reunião 29/10): lado A cupom de primeira compra com botão
 * copiar; lado B preços de Black Friday. Decisão 30/10: só na home (feminina e
 * masculina), uma única vez por visita — abre aos 5 s e não volta enquanto a
 * aba estiver aberta (sessionStorage); fechou o site e voltou, aparece de novo.
 * Cliente logada que já comprou vê só o lado Black.
 *
 * A versão publicada no WordPress é `wordpress-loja/pm-home/promo-popup.js`
 * (mesmas classes e textos) — manter as duas em sincronia.
 */
const FIRST_DELAY_MS = 5_000;
const SESSION_KEY = "pello-menos-popup-v3";
const BLACK_HREF = "/servicos";

function isHomePath(pathname: string) {
  const path = pathname.replace(/\/+$/, "") || "/";
  return path === "/" || path === "/masculino";
}

declare global {
  interface Window {
    /** Definido pelo WordPress quando a cliente está logada e já tem pedido. */
    pmHasPurchased?: boolean;
  }
}

export function CouponPopup() {
  const pathname = usePathname();
  const blocked = !isHomePath(pathname ?? "/");
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const [onlyBlack, setOnlyBlack] = useState(false);
  const overlayRef = useRef<HTMLButtonElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);

  const close = useCallback(() => {
    const overlay = overlayRef.current;
    const card = cardRef.current;
    if (!overlay || !card) {
      setOpen(false);
      return;
    }
    const tl = gsap.timeline({ onComplete: () => setOpen(false) });
    tl.to(
      card,
      { opacity: 0, y: 40, scale: 0.92, filter: "blur(8px)", duration: 0.35, ease: "power3.in" },
      0,
    );
    tl.to(overlay, { opacity: 0, duration: 0.3, ease: "power2.in" }, 0);
  }, []);

  // Uma única abertura por visita, aos 5 s, só na home.
  useEffect(() => {
    if (blocked) return;
    try {
      if (sessionStorage.getItem(SESSION_KEY) === "done") return;
    } catch {
      /* ignore */
    }
    const firstId = window.setTimeout(() => {
      try {
        sessionStorage.setItem(SESSION_KEY, "done");
      } catch {
        /* ignore */
      }
      setOnlyBlack(Boolean(window.pmHasPurchased));
      setOpen(true);
    }, FIRST_DELAY_MS);

    return () => window.clearTimeout(firstId);
  }, [blocked]);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") close();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, close]);

  useGSAP(
    () => {
      if (!open || !cardRef.current || !overlayRef.current) return;
      gsap.fromTo(overlayRef.current, { opacity: 0 }, { opacity: 1, duration: 0.35, ease: "power2.out" });
      gsap.fromTo(
        cardRef.current,
        { opacity: 0, y: 48, scale: 0.9, filter: "blur(10px)" },
        { opacity: 1, y: 0, scale: 1, filter: "blur(0px)", duration: 0.7, ease: "power3.out" },
      );
    },
    { dependencies: [open] },
  );

  async function copyCode() {
    try {
      await navigator.clipboard.writeText(FIRST_PURCHASE_COUPON);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  }

  if (!open || blocked) return null;

  const blackHref = pathname?.startsWith("/masculino") ? `/masculino${BLACK_HREF}` : BLACK_HREF;

  return (
    <div data-pm-promo-popup className="fixed inset-0 z-[90] flex items-center justify-center p-4">
      <button
        ref={overlayRef}
        type="button"
        className="absolute inset-0 bg-[#2a1a24]/70 backdrop-blur-[6px]"
        aria-label="Fechar"
        onClick={close}
      />
      <div
        ref={cardRef}
        role="dialog"
        aria-labelledby="pm-promo-title"
        className={`relative z-10 grid w-full overflow-hidden rounded-[28px] border border-[#e8b86d]/40 shadow-[0_40px_90px_rgba(58,10,60,0.55)] ${
          onlyBlack ? "max-w-[440px]" : "max-w-[760px] md:grid-cols-2"
        }`}
      >
        <button
          type="button"
          onClick={close}
          className="absolute top-3 right-3 z-20 flex h-9 w-9 items-center justify-center rounded-full bg-black/35 text-white hover:bg-black/55"
          aria-label="Fechar"
        >
          <Icon name="close" size={18} />
        </button>

        {onlyBlack ? null : (
          <section className="pm-promo-side pm-promo-side--light flex flex-col justify-center px-7 py-10 text-center md:px-8 text-[#3a0a3c] md:min-h-[460px] md:py-14">
            <span className="pm-promo-seal pm-promo-seal--light" aria-hidden>
              <Icon name="gift" size={26} />
            </span>
            <p className="font-label-md text-label-md tracking-[0.22em] text-primary uppercase">
              Primeira compra
            </p>
            <h2
              id="pm-promo-title"
              className="mt-2 inline-flex items-center justify-center gap-2 font-[family-name:var(--font-display)] text-3xl text-primary md:text-4xl"
            >
              <Icon name="badgePercent" size={30} className="shrink-0" />
              {FIRST_PURCHASE_PERCENT}% de desconto
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-[#3a0a3c]/80">
              No total do seu primeiro pedido no site. Um uso por cliente; não acumula com outros cupons.
            </p>
            <button
              type="button"
              onClick={copyCode}
              data-pm-copy-coupon
              className="mt-6 inline-flex w-full items-center justify-between gap-3 rounded-2xl border border-primary/30 bg-white/90 px-4 py-3 text-primary shadow-[0_8px_20px_rgba(179,25,111,0.10)]"
            >
              <span className="inline-flex items-center gap-2 font-mono text-base tracking-[0.22em]">
                <Icon name="ticket" size={18} className="shrink-0 text-[#e8b86d]" />
                {FIRST_PURCHASE_COUPON}
              </span>
              <span className="inline-flex items-center gap-1 text-[11px] tracking-wide text-[#3a0a3c]/60 uppercase">
                <Icon name={copied ? "check" : "copy"} size={14} />
                {copied ? "Copiado" : "Copiar"}
              </span>
            </button>
            <p className="mt-3 text-[11px] text-[#3a0a3c]/60">Cole o código no carrinho.</p>
          </section>
        )}

        <section className="pm-promo-side pm-promo-side--dark flex flex-col justify-center px-7 py-10 text-center md:px-8 text-white md:min-h-[460px] md:py-14">
          <span className="pm-promo-seal pm-promo-seal--dark" aria-hidden>
            <Icon name="flame" size={26} />
          </span>
          <p className="font-label-md text-label-md tracking-[0.22em] text-[#e8b86d] uppercase">
            Black Friday
          </p>
          <h2
            id={onlyBlack ? "pm-promo-title" : undefined}
            className="mt-2 inline-flex items-center justify-center gap-2 font-[family-name:var(--font-display)] text-3xl text-white md:text-4xl"
          >
            <Icon name="tag" size={28} className="shrink-0 text-[#e8b86d]" />
            Preços de Black
          </h2>
          <p className="mt-3 text-sm leading-relaxed text-white/75">
            Cera, laser e esfoliação com preço especial de Black Friday aqui no site. Escolha a unidade e garanta o seu.
          </p>
          <Link
            href={blackHref}
            onClick={close}
            className="btn-lux btn-lux-gold mt-6 inline-flex w-full items-center justify-center gap-2 rounded-full py-3.5 text-sm font-semibold tracking-wide text-on-secondary-container uppercase"
          >
            <Icon name="sparkles" size={16} />
            Ver ofertas
            <Icon name="arrowRight" size={16} />
          </Link>
        </section>
      </div>
    </div>
  );
}
