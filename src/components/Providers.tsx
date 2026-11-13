"use client";

import { StoreProvider } from "@/components/StoreProvider";
import { SiteShell } from "@/components/SiteShell";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <StoreProvider>
      <SiteShell>{children}</SiteShell>
    </StoreProvider>
  );
}
