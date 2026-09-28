"use client";

import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { useRef } from "react";
import { Icon } from "@/components/Icon";
import { useStore } from "@/components/StoreProvider";

gsap.registerPlugin(useGSAP);

export function Toast() {
  const { toast } = useStore();
  const ref = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      if (!toast || !ref.current) return;
      gsap.fromTo(
        ref.current,
        { y: -16, opacity: 0, scale: 0.94 },
        { y: 0, opacity: 1, scale: 1, duration: 0.35, ease: "power3.out" },
      );
    },
    { dependencies: [toast] },
  );

  if (!toast) return null;

  return (
    <div
      ref={ref}
      className="fixed top-40 left-1/2 z-[80] flex -translate-x-1/2 items-center gap-2 rounded-full bg-primary px-5 py-2.5 text-sm font-medium text-on-primary shadow-lg"
    >
      <Icon name="shoppingCart" size={16} />
      {toast.message}
    </div>
  );
}
