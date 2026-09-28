"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Icon } from "@/components/Icon";
import { SearchPanel } from "@/components/SearchPanel";
import { useStore } from "@/components/StoreProvider";
import { TrustBar } from "@/components/TrustBar";
import {
  audienceFromPath,
  audienceLinks,
  navItems,
  type NavItem,
} from "@/lib/data";

const iconBtn =
  "btn-lux btn-lux-ghost relative flex h-11 w-11 items-center justify-center rounded-full border border-primary/20 text-primary hover:text-secondary";

type Props = {
  onOpenAuth: () => void;
};

function normalizePath(pathname: string) {
  if (pathname.length > 1 && pathname.endsWith("/")) {
    return pathname.slice(0, -1);
  }
  return pathname;
}

function linkActive(pathname: string, item: NavItem) {
  const path = normalizePath(pathname);
  if (item.label === "Serviços") {
    return path === "/servicos" || path.endsWith("/servicos") || path.includes("/servicos/");
  }
  if (item.label === "Planos de Assinatura") {
    return (
      path.includes("/planos") ||
      path.includes("plano-silver") ||
      path.includes("plano-gold") ||
      path.includes("plano-clube-laser") ||
      path.includes("plano-prepago")
    );
  }
  if (item.label === "Cartão Presente") {
    return path.includes("cartao-presente");
  }
  if (item.label === "Produtos") {
    return path === "/produtos" || path === "/masculino/produtos";
  }
  return path === item.href;
}

function NavMenu({
  items,
  pathname,
  onNavigate,
  mobile = false,
}: {
  items: NavItem[];
  pathname: string;
  onNavigate?: () => void;
  mobile?: boolean;
}) {
  const [openLabel, setOpenLabel] = useState<string | null>(null);

  if (mobile) {
    return (
      <div className="flex flex-col gap-1 py-2">
        {items.map((item) => {
          const active = linkActive(pathname, item);
          const expanded = openLabel === item.label;
          if (!item.children?.length) {
            return (
              <Link
                key={item.label}
                href={item.href}
                onClick={onNavigate}
                className={
                  active
                    ? "rounded-xl bg-primary px-4 py-3 text-sm font-semibold text-on-primary"
                    : "rounded-xl px-4 py-3 text-sm font-semibold text-on-surface hover:bg-primary/8"
                }
              >
                {item.label}
              </Link>
            );
          }
          return (
            <div key={item.label}>
              <button
                type="button"
                className={
                  active
                    ? "flex w-full items-center justify-between rounded-xl bg-primary px-4 py-3 text-sm font-semibold text-on-primary"
                    : "flex w-full items-center justify-between rounded-xl px-4 py-3 text-sm font-semibold text-on-surface hover:bg-primary/8"
                }
                aria-expanded={expanded}
                onClick={() => setOpenLabel(expanded ? null : item.label)}
              >
                {item.label}
                <Icon name="chevronDown" size={16} className={expanded ? "rotate-180" : ""} />
              </button>
              {expanded ? (
                <div className="ml-3 flex flex-col gap-1 border-l border-outline/40 py-1 pl-3">
                  {item.children.map((child) => (
                    <Link
                      key={child.href}
                      href={child.href}
                      onClick={onNavigate}
                      className="rounded-lg px-3 py-2 text-sm text-on-surface-variant hover:bg-primary/8 hover:text-primary"
                    >
                      {child.label}
                    </Link>
                  ))}
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <>
      {items.map((item) => {
        const active = linkActive(pathname, item);
        const className = active
          ? "font-label-md text-label-md text-primary"
          : "font-label-md text-label-md text-on-surface-variant transition-colors hover:text-primary";

        if (!item.children?.length) {
          return (
            <Link key={item.label} href={item.href} className={`whitespace-nowrap ${className}`}>
              {item.label}
            </Link>
          );
        }

        return (
          <div key={item.label} className="group relative">
            <Link
              href={item.href}
              className={`inline-flex items-center gap-1 whitespace-nowrap ${className}`}
            >
              {item.label}
              <Icon name="chevronDown" size={14} className="opacity-70" />
            </Link>
            <div className="invisible absolute top-full left-1/2 z-50 pt-3 opacity-0 transition group-hover:visible group-hover:opacity-100 group-focus-within:visible group-focus-within:opacity-100 -translate-x-1/2">
              <div className="min-w-[210px] rounded-2xl border border-outline/40 bg-white py-2 shadow-[0_18px_40px_rgba(58,10,60,0.12)]">
                {item.children.map((child) => (
                  <Link
                    key={child.href}
                    href={child.href}
                    className="block px-4 py-2 text-sm text-on-surface hover:bg-primary/8 hover:text-primary"
                  >
                    {child.label}
                  </Link>
                ))}
              </div>
            </div>
          </div>
        );
      })}
    </>
  );
}

export function Header({ onOpenAuth }: Props) {
  const pathname = usePathname();
  const audience = audienceFromPath(pathname);
  const { cartCount, user } = useStore();
  const [searchOpen, setSearchOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const items = navItems(audience);

  useEffect(() => {
    setMenuOpen(false);
  }, [pathname]);

  return (
    <>
      <header className="fixed top-0 z-[80] w-full border-b border-outline/40 bg-white/95 backdrop-blur-md">
        <TrustBar audience={audience} />
        <div className="border-b border-outline/30 bg-white">
          <div
            className="mx-auto flex max-w-7xl items-center justify-center gap-1 px-container-margin py-1.5"
            role="navigation"
            aria-label="Público"
          >
            {audienceLinks.map((link) => {
              const active = audience === link.audience;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={
                    active
                      ? "rounded-full bg-primary px-5 py-1.5 text-xs font-semibold tracking-wide text-on-primary uppercase"
                      : "rounded-full px-5 py-1.5 text-xs font-semibold tracking-wide text-primary uppercase hover:bg-primary/10"
                  }
                >
                  {link.label}
                </Link>
              );
            })}
          </div>
        </div>
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-container-margin py-2.5">
          <Link href={audience === "masculino" ? "/masculino" : "/"} className="flex flex-col items-start leading-none">
            <Image
              src={audience === "masculino" ? "/brand/logo-male.png" : "/brand/logo-female.png"}
              alt="pello menos"
              width={498}
              height={190}
              priority
              className="h-12 w-auto object-contain md:h-14"
            />
          </Link>
          <nav className="hidden items-center gap-6 lg:flex" aria-label="Principal">
            <NavMenu items={items} pathname={pathname} />
          </nav>
          <div className="flex items-center gap-2">
            <button
              type="button"
              className={`${iconBtn} lg:hidden`}
              aria-label={menuOpen ? "Fechar menu" : "Abrir menu"}
              aria-expanded={menuOpen}
              onClick={() => {
                setSearchOpen(false);
                setMenuOpen((open) => !open);
              }}
            >
              <Icon name={menuOpen ? "close" : "menu"} size={20} />
            </button>
            <button
              type="button"
              className={iconBtn}
              aria-label="Buscar serviços"
              onClick={() => {
                setMenuOpen(false);
                setSearchOpen((open) => !open);
              }}
            >
              <Icon name="search" size={20} />
            </button>
            <button
              type="button"
              className={iconBtn}
              aria-label={user ? "Minha conta" : "Entrar ou criar conta"}
              onClick={() => {
                setSearchOpen(false);
                setMenuOpen(false);
                onOpenAuth();
              }}
            >
              <Icon name="user" size={20} />
            </button>
            <Link
              href="/carrinho"
              className={iconBtn}
              aria-label={`Carrinho com ${cartCount} itens`}
            >
              <Icon name="shoppingCart" size={20} />
              {cartCount > 0 ? (
                <span className="absolute -top-1 -right-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-bold text-white">
                  {cartCount}
                </span>
              ) : null}
            </Link>
          </div>
        </div>
        {menuOpen ? (
          <div className="border-t border-outline/30 bg-white lg:hidden">
            <nav className="mx-auto max-w-7xl px-container-margin py-2" aria-label="Principal mobile">
              <NavMenu
                items={items}
                pathname={pathname}
                mobile
                onNavigate={() => setMenuOpen(false)}
              />
            </nav>
          </div>
        ) : null}
      </header>
      <SearchPanel open={searchOpen} onClose={() => setSearchOpen(false)} />
    </>
  );
}
