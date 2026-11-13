"use client";

import { usePathname } from "next/navigation";
import { useState } from "react";
import { AuthModal } from "@/components/AuthModal";
import { BottomNav } from "@/components/BottomNav";
import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";
import { CookieBanner } from "@/components/CookieBanner";
import { CouponPopup } from "@/components/CouponPopup";
import { PurchasePopup } from "@/components/PurchasePopup";
import { Toast } from "@/components/Toast";
import { WhatsAppFloat } from "@/components/WhatsAppFloat";
import { isCheckoutFunnelPath } from "@/lib/checkoutPaths";
import { audienceFromPath } from "@/lib/data";

export function SiteShell({ children }: { children: React.ReactNode }) {
  const [authOpen, setAuthOpen] = useState(false);
  const pathname = usePathname();
  const audience = audienceFromPath(pathname);
  const funnel = isCheckoutFunnelPath(pathname);
  // Funnel hides the audience switch strip (~40px); keep feminine chrome.
  const pad = funnel
    ? "pt-[114px] md:pt-[124px]"
    : "pt-[154px] md:pt-[164px]";

  return (
    <div
      data-audience={audience}
      className={`flex min-h-screen flex-col overflow-x-hidden bg-background ${pad} pb-24 font-sans text-on-background md:pb-0`}
    >
      <Header onOpenAuth={() => setAuthOpen(true)} />
      <div className="w-full flex-1">{children}</div>
      <Footer onOpenAuth={() => setAuthOpen(true)} />
      <BottomNav />
      <PurchasePopup />
      <WhatsAppFloat />
      <CouponPopup />
      <CookieBanner />
      <Toast />
      <AuthModal open={authOpen} onClose={() => setAuthOpen(false)} />
    </div>
  );
}
