"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Icon, type IconName } from "@/components/Icon";
import { useStore } from "@/components/StoreProvider";
import { audienceFromPath, homeHref } from "@/lib/data";

export function BottomNav() {
  const pathname = usePathname();
  const { cartCount } = useStore();
  const home = homeHref(audienceFromPath(pathname));

  const items: { href: string; icon: IconName; label: string }[] = [
    { href: home, icon: "house", label: "Início" },
    { href: "/carrinho", icon: "shoppingCart", label: "Carrinho" },
    { href: "/checkout", icon: "creditCard", label: "Pagamento" },
  ];

  return (
    <nav className="fixed bottom-0 left-0 z-50 flex w-full items-center justify-around border-t border-outline/40 bg-surface/95 px-2 py-2.5 backdrop-blur-md md:hidden">
      {items.map((item) => {
        const active = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={
              active
                ? "btn-lux btn-lux-primary relative flex min-w-[88px] flex-col items-center rounded-2xl px-4 py-2 text-on-primary"
                : "relative flex min-w-[88px] flex-col items-center rounded-2xl px-4 py-2 text-on-surface-variant"
            }
          >
            <Icon name={item.icon} size={20} filled={active} />
            {item.href === "/carrinho" && cartCount > 0 ? (
              <span className="absolute top-1 right-3 flex h-4 min-w-4 items-center justify-center rounded-full bg-secondary-container px-1 text-[10px] font-bold text-on-secondary-container">
                {cartCount}
              </span>
            ) : null}
            <span className="mt-1 font-label-sm text-label-sm uppercase">
              {item.label}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
