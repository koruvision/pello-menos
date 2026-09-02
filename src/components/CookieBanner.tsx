"use client";

import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import Link from "next/link";
import { useCallback, useLayoutEffect, useRef, useState } from "react";

gsap.registerPlugin(useGSAP);

const STORAGE_KEY = "pello-menos-cookies";

export function CookieBanner() {
  const [visible, setVisible] = useState(false);
  const barRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    try {
      if (localStorage.getItem(STORAGE_KEY)) return;
    } catch {
      /* ignore */
    }
    setVisible(true);
  }, []);

  useGSAP(
    () => {
      if (!visible || !barRef.current) return;
      gsap.fromTo(
        barRef.current,
        { yPercent: 100, opacity: 0 },
        { yPercent: 0, opacity: 1, duration: 0.45, ease: "power3.out" },
      );
    },
    { dependencies: [visible] },
  );

  const choose = useCallback((value: "accept" | "reject") => {
    const node = barRef.current;
    const finish = () => {
      try {
        localStorage.setItem(STORAGE_KEY, value);
      } catch {
        /* ignore */
      }
      setVisible(false);
    };
    if (!node) {
      finish();
      return;
    }
    gsap.to(node, {
      yPercent: 100,
      opacity: 0,
      duration: 0.35,
      ease: "power3.in",
      onComplete: finish,
    });
  }, []);

  if (!visible) return null;

  return (
    <div
      ref={barRef}
      role="dialog"
      aria-label="Aviso de cookies"
      className="fixed inset-x-0 bottom-0 z-[95] border-t border-[#e8b86d]/25 bg-[#1a0818]/95 text-white backdrop-blur-md"
    >
      <div className="mx-auto flex max-w-7xl items-center gap-3 px-3 py-1.5 md:px-6">
        <p className="min-w-0 flex-1 truncate text-[11px] leading-tight text-white/85 md:text-xs">
          Usamos cookies para lembrar preferências e melhorar a loja.{" "}
          <Link href="/privacidade" className="text-[#e8b86d] underline-offset-2 hover:underline">
            Privacidade
          </Link>
        </p>
        <div className="flex shrink-0 items-center gap-1.5">
          <button
            type="button"
            onClick={() => choose("reject")}
            className="rounded-full px-3 py-1 text-[10px] font-semibold tracking-wide text-white/70 uppercase hover:text-white"
          >
            Recusar
          </button>
          <button
            type="button"
            onClick={() => choose("accept")}
            className="btn-lux btn-lux-gold rounded-full px-3 py-1 text-[10px] font-semibold tracking-wide text-on-secondary-container uppercase"
          >
            Aceitar
          </button>
        </div>
      </div>
    </div>
  );
}
