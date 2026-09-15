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
import { audienceFromPath } from "@/lib/data";

export function SiteShell({ children }: { children: React.ReactNode }) {
  const [authOpen, setAuthOpen] = useState(false);
  const audience = audienceFromPath(usePathname());

  return (
    <div
      data-audience={audience}
      className="flex min-h-screen flex-col overflow-x-hidden bg-background pt-[154px] pb-24 font-sans text-on-background md:pt-[164px] md:pb-0"
    >
      <Header onOpenAuth={() => setAuthOpen(true)} />
      <div className="flex-1">{children}</div>
      <Footer onOpenAuth={() => setAuthOpen(true)} />
      <BottomNav />
      <PurchasePopup />
      <CouponPopup />
      <CookieBanner />
      <Toast />
      <AuthModal open={authOpen} onClose={() => setAuthOpen(false)} />
    </div>
  );
}
