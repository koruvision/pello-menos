"use client";

import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import Image from "next/image";
import { useCallback, useEffect, useRef, useState } from "react";
import { Icon } from "@/components/Icon";

gsap.registerPlugin(useGSAP);

const COUPON_CODE = "AGOSTO15";
const STORAGE_KEY = "pello-menos-cupom-agosto";

export function CouponPopup() {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const overlayRef = useRef<HTMLButtonElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);

  const rememberSeen = useCallback(() => {
    try {
      localStorage.setItem(STORAGE_KEY, "1");
    } catch {
      /* ignore */
    }
  }, []);

  const close = useCallback(() => {
    rememberSeen();
    const overlay = overlayRef.current;
    const card = cardRef.current;
    if (!overlay || !card) {
      setOpen(false);
      return;
    }
    const tl = gsap.timeline({ onComplete: () => setOpen(false) });
    tl.to(
      card,
      {
        opacity: 0,
        y: 48,
        rotateX: 14,
        rotateY: 10,
        scale: 0.88,
        filter: "blur(8px)",
        duration: 0.4,
        ease: "power3.in",
      },
      0,
    );
    tl.to(overlay, { opacity: 0, duration: 0.35, ease: "power2.in" }, 0);
  }, [rememberSeen]);

  useEffect(() => {
    try {
      if (localStorage.getItem(STORAGE_KEY)) return;
    } catch {
      /* ignore */
    }

    const delayId = window.setTimeout(() => {
      rememberSeen();
      setOpen(true);
    }, 5000);

    return () => window.clearTimeout(delayId);
  }, [rememberSeen]);

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
      gsap.fromTo(
        overlayRef.current,
        { opacity: 0 },
        { opacity: 1, duration: 0.4, ease: "power2.out" },
      );
      gsap.fromTo(
        cardRef.current,
        {
          opacity: 0,
          y: 56,
          rotateX: 18,
          rotateY: -12,
          scale: 0.84,
          filter: "blur(10px)",
        },
        {
          opacity: 1,
          y: 0,
          rotateX: 0,
          rotateY: 0,
          scale: 1,
          filter: "blur(0px)",
          duration: 0.85,
          ease: "power3.out",
        },
      );
    },
    { dependencies: [open] },
  );

  async function copyCode() {
    try {
      await navigator.clipboard.writeText(COUPON_CODE);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
      <button
        ref={overlayRef}
        type="button"
        className="absolute inset-0 bg-[#2a1a24]/70 backdrop-blur-[6px]"
        aria-label="Fechar cupom"
        onClick={close}
      />
      <div
        className="relative z-10 w-full max-w-[440px]"
        style={{ perspective: "1400px" }}
      >
        <div
          ref={cardRef}
          className="relative w-full overflow-hidden rounded-[28px] border border-[#e8b86d]/50 bg-[#1a0818] shadow-[0_40px_90px_rgba(58,10,60,0.55),0_0_0_1px_rgba(232,184,109,0.18)]"
          style={{ transformStyle: "preserve-3d" }}
          role="dialog"
          aria-labelledby="cupom-agosto-title"
        >
          <button
            type="button"
            onClick={close}
            className="absolute top-3 right-3 z-10 flex h-9 w-9 items-center justify-center rounded-full bg-black/35 text-white hover:bg-black/55"
            aria-label="Fechar"
          >
            <Icon name="close" size={18} />
          </button>

          <div className="coupon-3d relative aspect-[4/3] overflow-hidden">
            <Image
              src="/images/promo/cupom-agosto.png"
              alt="Cupom de agosto Pello Menos, 15% off"
              fill
              priority
              className="object-cover"
              sizes="440px"
            />
            <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-[#1a0818] via-transparent to-transparent" />
            <Image
              src="/images/promo/cupom-agosto-badge.png"
              alt=""
              width={96}
              height={96}
              className="absolute -bottom-6 left-5 h-20 w-20 rounded-full object-cover shadow-[0_12px_30px_rgba(232,184,109,0.45)] ring-2 ring-[#e8b86d]"
            />
          </div>

          <div className="px-6 pt-10 pb-7 text-center">
            <p className="font-label-md text-label-md tracking-[0.22em] text-[#e8b86d] uppercase">
              Só em agosto
            </p>
            <h2
              id="cupom-agosto-title"
              className="mt-2 font-[family-name:var(--font-display)] text-3xl text-white md:text-4xl"
            >
              Cupom do mês
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-white/75">
              15% de desconto no primeiro pedido da loja. Válido até 31 de
              agosto.
            </p>

            <button
              type="button"
              onClick={copyCode}
              className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-2xl border border-[#e8b86d]/40 bg-[#2a1028] px-4 py-3 font-mono text-lg tracking-[0.28em] text-[#e8b86d]"
            >
              {COUPON_CODE}
              <span className="text-[11px] tracking-wide text-white/60 uppercase">
                {copied ? "Copiado" : "Copiar"}
              </span>
            </button>

            <button
              type="button"
              onClick={close}
              className="btn-lux btn-lux-gold mt-4 w-full rounded-full py-3.5 text-sm font-semibold tracking-wide text-on-secondary-container uppercase"
            >
              Quero usar agora
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
