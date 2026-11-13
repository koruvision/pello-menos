"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import { isCheckoutFunnelPath } from "@/lib/checkoutPaths";
import { WHATSAPP_TEXT, whatsappHref } from "@/lib/contact";

// Reunião 29/10: a consultora do WhatsApp (Mariana) só atende laser; os demais serviços se compram no site.
// Texto enviado para aprovação da Adriana (P9 em historico/21).
const BUBBLE_TEXT = "Dúvidas sobre laser? Fale com a nossa consultora 💜";
const INTERVAL_MS = 30_000;
const VISIBLE_MS = 5_000;

export function WhatsAppFloat() {
  const pathname = usePathname();
  const blocked = isCheckoutFunnelPath(pathname);
  const [bubble, setBubble] = useState(false);
  const dismissed = useRef(false);

  useEffect(() => {
    dismissed.current = false;
    setBubble(false);
    if (blocked) return;

    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const timeouts: number[] = [];
    let intervalId = 0;

    const show = () => {
      if (document.hidden || dismissed.current) return;
      setBubble(true);
      timeouts.push(
        window.setTimeout(() => setBubble(false), reduce ? 1 : VISIBLE_MS),
      );
    };

    timeouts.push(window.setTimeout(show, INTERVAL_MS));
    intervalId = window.setInterval(show, INTERVAL_MS);

    return () => {
      timeouts.forEach((id) => window.clearTimeout(id));
      window.clearInterval(intervalId);
    };
  }, [blocked, pathname]);

  if (blocked) return null;

  const href = whatsappHref(WHATSAPP_TEXT);

  return (
    <div className="pointer-events-none fixed bottom-24 right-4 z-[70] flex flex-col items-end gap-2 md:bottom-8">
      {bubble ? (
        <div className="pointer-events-auto relative max-w-[min(calc(100vw-5rem),260px)]">
          <a
            href={href}
            target="_blank"
            rel="noreferrer"
            className="block rounded-[22px] rounded-br-md bg-[#25D366] px-4 py-3 text-[15px] leading-snug text-white shadow-[0_8px_24px_rgba(37,211,102,0.35)]"
          >
            {BUBBLE_TEXT}
          </a>
          <button
            type="button"
            aria-label="Fechar notificação"
            onClick={() => {
              dismissed.current = true;
              setBubble(false);
            }}
            className="absolute -top-2 -right-2 flex h-6 w-6 items-center justify-center rounded-full bg-white text-xs text-on-surface shadow"
          >
            ×
          </button>
        </div>
      ) : null}
      <a
        href={href}
        target="_blank"
        rel="noreferrer"
        aria-label="WhatsApp SAC Pello Menos"
        className="pm-wa-shine pointer-events-auto flex h-14 w-14 items-center justify-center rounded-full bg-[#25D366] text-white shadow-[0_10px_28px_rgba(37,211,102,0.45)] transition hover:scale-105"
      >
        <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <path d="M19.05 4.91A9.82 9.82 0 0 0 12.04 2C6.55 2 2.08 6.45 2.08 11.94c0 1.76.46 3.48 1.34 5L2 22l5.2-1.36a10 10 0 0 0 4.84 1.23h.01c5.49 0 9.96-4.45 9.96-9.94a9.87 9.87 0 0 0-2.96-7.02Zm-7.01 15.29h-.01a8.3 8.3 0 0 1-4.23-1.16l-.3-.18-3.08.81.82-3-.2-.31a8.23 8.23 0 0 1-1.27-4.41c0-4.54 3.72-8.24 8.29-8.24 2.21 0 4.29.86 5.85 2.41a8.18 8.18 0 0 1 2.43 5.83c0 4.55-3.73 8.25-8.3 8.25Zm4.55-6.17c-.25-.12-1.47-.72-1.7-.81-.23-.08-.4-.12-.56.13-.17.24-.64.8-.79.97-.14.16-.29.18-.54.06-.25-.13-1.05-.38-2-1.23-.74-.66-1.24-1.47-1.38-1.72-.15-.25-.02-.38.11-.5.11-.11.25-.29.37-.43.13-.15.17-.25.25-.41.08-.17.04-.31-.02-.43-.06-.12-.56-1.34-.76-1.84-.2-.48-.4-.41-.56-.42h-.48c-.17 0-.43.06-.66.31-.23.24-.87.85-.87 2.07 0 1.22.9 2.4 1.02 2.56.13.17 1.77 2.7 4.29 3.79.6.26 1.07.41 1.43.53.6.19 1.15.16 1.58.1.48-.07 1.47-.6 1.68-1.18.21-.58.21-1.07.14-1.18-.06-.10-.23-.17-.48-.29Z" />
        </svg>
      </a>
    </div>
  );
}
