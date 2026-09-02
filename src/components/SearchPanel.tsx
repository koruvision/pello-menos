"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { Icon } from "@/components/Icon";
import {
  audienceFromPath,
  categories,
  categoriesMasculino,
  formatBRL,
  productsForAudience,
  productsHref,
} from "@/lib/data";

type Props = {
  open: boolean;
  onClose: () => void;
};

export function SearchPanel({ open, onClose }: Props) {
  const pathname = usePathname();
  const audience = audienceFromPath(pathname);
  const catalog = useMemo(() => productsForAudience(audience), [audience]);
  const categoryList = audience === "masculino" ? categoriesMasculino : categories;
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [recent, setRecent] = useState<string[]>([]);

  useEffect(() => {
    if (!open) return;
    const saved = localStorage.getItem("pello-menos-recent-search");
    if (saved) {
      try {
        setRecent(JSON.parse(saved) as string[]);
      } catch {
        setRecent([]);
      }
    }
    const id = window.setTimeout(() => inputRef.current?.focus(), 40);
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => {
      window.clearTimeout(id);
      window.removeEventListener("keydown", onKey);
    };
  }, [open, onClose]);

  const normalized = query.trim().toLowerCase();

  const results = useMemo(() => {
    if (!normalized) return [];
    return catalog.filter((product) => {
      const haystack = [
        product.name,
        product.duration,
        product.category,
        product.imageAlt,
        product.sku,
        product.code,
        product.description,
        product.badge || "",
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(normalized);
    });
  }, [catalog, normalized]);

  const categoryHits = useMemo(() => {
    if (!normalized) return [];
    return categoryList.filter((category) =>
      category.label.toLowerCase().includes(normalized),
    );
  }, [categoryList, normalized]);

  function remember(term: string) {
    const clean = term.trim();
    if (!clean) return;
    const next = [clean, ...recent.filter((item) => item !== clean)].slice(0, 6);
    setRecent(next);
    localStorage.setItem("pello-menos-recent-search", JSON.stringify(next));
  }

  function goToProducts() {
    onClose();
    if (pathname === "/" || pathname === "/masculino") {
      document.getElementById("produtos")?.scrollIntoView({ behavior: "smooth" });
      return;
    }
    window.location.href = productsHref(audience);
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[70]">
      <button
        type="button"
        className="absolute inset-0 bg-black/55"
        aria-label="Fechar busca"
        onClick={onClose}
      />
      <div className="absolute inset-x-0 top-[168px] max-h-[min(calc(88vh-168px),720px)] overflow-y-auto rounded-b-3xl bg-white shadow-2xl md:top-[188px] md:max-h-[min(calc(88vh-188px),720px)]">
        <div className="mx-auto max-w-7xl px-container-margin py-6">
          <div className="flex items-center gap-3 rounded-full border border-primary/20 bg-surface-container-low px-4 py-3">
            <Icon name="search" size={20} className="text-primary" />
            <input
              ref={inputRef}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && query.trim()) remember(query);
              }}
              placeholder="Buscar axila, virilha, laser, cera..."
              className="w-full bg-transparent text-base text-on-surface outline-none placeholder:text-on-surface-variant"
            />
            {query ? (
              <button
                type="button"
                onClick={() => setQuery("")}
                className="text-on-surface-variant"
                aria-label="Limpar busca"
              >
                <Icon name="close" size={18} />
              </button>
            ) : null}
          </div>

          {!normalized ? (
            <div className="mt-6">
              <p className="font-label-md text-label-md text-primary uppercase">
                Sugestões
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {(audience === "masculino"
                  ? ["Axilas", "Peito", "Costas", "Barba", "Pernas", "Laser"]
                  : ["Axilas", "Virilha", "Pernas", "Braços", "Abdômen", "Sobrancelha", "Laser", "Cera"]
                ).map((term) => (
                  <button
                    key={term}
                    type="button"
                    onClick={() => setQuery(term)}
                    className="btn-lux btn-lux-ghost rounded-full border border-primary/20 px-4 py-2 text-sm text-primary"
                  >
                    {term}
                  </button>
                ))}
              </div>
              {recent.length > 0 ? (
                <div className="mt-6">
                  <p className="font-label-md text-label-md text-primary uppercase">
                    Recentes
                  </p>
                  <ul className="mt-2 space-y-1">
                    {recent.map((term) => (
                      <li key={term}>
                        <button
                          type="button"
                          onClick={() => setQuery(term)}
                          className="text-sm text-on-surface-variant hover:text-primary"
                        >
                          {term}
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          ) : results.length === 0 && categoryHits.length === 0 ? (
            <p className="mt-8 text-sm text-on-surface-variant">
              Nenhum serviço encontrado para “{query}”.
            </p>
          ) : (
            <div className="mt-6 space-y-6">
              {categoryHits.length > 0 ? (
                <div>
                  <p className="font-label-md text-label-md text-primary uppercase">
                    Categorias
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {categoryHits.map((category) => (
                      <button
                        key={category.id}
                        type="button"
                        onClick={goToProducts}
                        className="btn-lux btn-lux-primary rounded-full px-4 py-2 text-sm text-white"
                      >
                        {category.label}
                      </button>
                    ))}
                  </div>
                </div>
              ) : null}
              <div>
                <p className="font-label-md text-label-md text-primary uppercase">
                  {results.length} serviço{results.length === 1 ? "" : "s"}
                </p>
                <ul className="mt-3 divide-y divide-outline/40">
                  {results.map((product) => (
                    <li
                      key={product.id}
                      className="flex items-center gap-3 py-3"
                    >
                      <Link
                        href={`/produto/${product.id}`}
                        onClick={() => {
                          remember(query);
                          onClose();
                        }}
                        className="flex min-w-0 flex-1 items-center gap-3 text-left"
                      >
                        <span className="relative h-14 w-14 shrink-0 overflow-hidden rounded-xl bg-surface-container-high">
                          <Image
                            src={product.image}
                            alt=""
                            fill
                            className="object-cover"
                            sizes="56px"
                          />
                        </span>
                        <span className="min-w-0">
                          <span className="block truncate font-medium text-on-surface">
                            {product.name}
                          </span>
                          <span className="block text-sm text-primary">
                            {formatBRL(product.priceCents)}
                          </span>
                        </span>
                      </Link>
                      <Link
                        href={`/produto/${product.id}`}
                        onClick={() => {
                          remember(query);
                          onClose();
                        }}
                        className="btn-lux btn-lux-primary rounded-full px-3 py-2 text-[11px] font-semibold tracking-wide text-white uppercase"
                      >
                        Ver
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
