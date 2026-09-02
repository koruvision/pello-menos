"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Icon, type IconName } from "@/components/Icon";
import { audienceFromPath, homeHref } from "@/lib/data";

const trust: { icon: IconName; label: string }[] = [
  { icon: "truck", label: "Unidades no RJ e SP" },
  { icon: "badgePercent", label: "Até 10x no cartão" },
  { icon: "shieldCheck", label: "Compra segura" },
];

const WHATSAPP_SAC =
  "https://wa.me/?text=" +
  encodeURIComponent("Olá! Gostaria de falar com o SAC Pello Menos.");

const socials = [
  {
    href: WHATSAPP_SAC,
    label: "WhatsApp",
    icon: "whatsapp" as const,
  },
  {
    href: "https://www.instagram.com/pellomenos/",
    label: "Instagram",
    icon: "instagram" as const,
  },
  {
    href: "https://www.facebook.com/pellomenosfranquia",
    label: "Facebook",
    icon: "facebook" as const,
  },
  {
    href: "https://www.linkedin.com/company/pellomenos",
    label: "LinkedIn",
    icon: "linkedin" as const,
  },
];

function SocialGlyph({
  name,
  size = 18,
}: {
  name: "whatsapp" | "instagram" | "facebook" | "linkedin";
  size?: number;
}) {
  const props = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "currentColor",
    "aria-hidden": true,
  } as const;

  if (name === "whatsapp") {
    return (
      <svg {...props}>
        <path d="M19.05 4.91A9.82 9.82 0 0 0 12.04 2C6.55 2 2.08 6.45 2.08 11.94c0 1.76.46 3.48 1.34 5L2 22l5.2-1.36a10 10 0 0 0 4.84 1.23h.01c5.49 0 9.96-4.45 9.96-9.94a9.87 9.87 0 0 0-2.96-7.02Zm-7.01 15.29h-.01a8.3 8.3 0 0 1-4.23-1.16l-.3-.18-3.08.81.82-3-.2-.31a8.23 8.23 0 0 1-1.27-4.41c0-4.54 3.72-8.24 8.29-8.24 2.21 0 4.29.86 5.85 2.41a8.18 8.18 0 0 1 2.43 5.83c0 4.55-3.73 8.25-8.3 8.25Zm4.55-6.17c-.25-.12-1.47-.72-1.7-.81-.23-.08-.4-.12-.56.13-.17.24-.64.8-.79.97-.14.16-.29.18-.54.06-.25-.13-1.05-.38-2-1.23-.74-.66-1.24-1.47-1.38-1.72-.15-.25-.02-.38.11-.5.11-.11.25-.29.37-.43.13-.15.17-.25.25-.41.08-.17.04-.31-.02-.43-.06-.12-.56-1.34-.76-1.84-.2-.48-.4-.41-.56-.42h-.48c-.17 0-.43.06-.66.31-.23.24-.87.85-.87 2.07 0 1.22.9 2.4 1.02 2.56.13.17 1.77 2.7 4.29 3.79.6.26 1.07.41 1.43.53.6.19 1.15.16 1.58.1.48-.07 1.47-.6 1.68-1.18.21-.58.21-1.07.14-1.18-.06-.10-.23-.17-.48-.29Z" />
      </svg>
    );
  }

  if (name === "instagram") {
    return (
      <svg {...props}>
        <path d="M7.8 2h8.4C19.4 2 22 4.6 22 7.8v8.4a5.8 5.8 0 0 1-5.8 5.8H7.8C4.6 22 2 19.4 2 16.2V7.8A5.8 5.8 0 0 1 7.8 2Zm-.2 2A3.6 3.6 0 0 0 4 7.6v8.8C4 18.39 5.61 20 7.6 20h8.8a3.6 3.6 0 0 0 3.6-3.6V7.6C20 5.61 18.39 4 16.4 4H7.6Zm9.65 1.5a1.25 1.25 0 1 1 0 2.5 1.25 1.25 0 0 1 0-2.5ZM12 7a5 5 0 1 1 0 10 5 5 0 0 1 0-10Zm0 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z" />
      </svg>
    );
  }

  if (name === "facebook") {
    return (
      <svg {...props}>
        <path d="M13.5 22v-8.2h2.76l.41-3.2H13.5V8.56c0-.93.26-1.56 1.59-1.56H16.8V4.14A21.3 21.3 0 0 0 14.36 4C11.9 4 10.2 5.5 10.2 8.24v2.36H7.5v3.2h2.7V22h3.3Z" />
      </svg>
    );
  }

  return (
    <svg {...props}>
      <path d="M20.45 20.45h-3.55v-5.57c0-1.33-.02-3.04-1.85-3.04-1.86 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.47-.9 1.63-1.85 3.36-1.85 3.6 0 4.27 2.37 4.27 5.45v6.29ZM5.34 7.43a2.06 2.06 0 1 1 0-4.12 2.06 2.06 0 0 1 0 4.12ZM7.12 20.45H3.56V9h3.56v11.45ZM22 0H2C.9 0 0 .9 0 2v20c0 1.1.9 2 2 2h20c1.1 0 2-.9 2-2V2c0-1.1-.9-2-2-2Z" />
    </svg>
  );
}

type Props = {
  onOpenAuth: () => void;
};

export function Footer({ onOpenAuth }: Props) {
  const audience = audienceFromPath(usePathname());
  const isMale = audience === "masculino";

  return (
    <footer className="site-footer mt-8 pb-28 text-white md:pb-0">
      <div className="mx-auto max-w-7xl px-container-margin py-12">
        <div className="grid gap-10 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.9fr)_minmax(0,1fr)]">
          <div>
            <Link href={homeHref(audience)} className="inline-block">
              <Image
                src={isMale ? "/brand/logo-male-footer.png" : "/brand/logo-footer.png"}
                alt="pello menos"
                width={1024}
                height={576}
                className="h-16 w-auto object-contain md:h-24"
              />
            </Link>
            {isMale ? null : (
              <p className="mt-1 text-xs tracking-[0.2em] text-secondary-container uppercase">
                depilação avançada
              </p>
            )}
            <p className="mt-4 max-w-sm text-sm leading-relaxed text-white/70">
              Compras realizadas na loja on-line, são pessoais e
              intransferíveis. Utilização somente após 24h, a contar da
              confirmação do pagamento.
            </p>
            <div className="mt-5 flex items-center gap-3">
              {socials.map((item) => (
                <a
                  key={item.label}
                  href={item.href}
                  target="_blank"
                  rel="noreferrer"
                  aria-label={item.label}
                  className="btn-lux btn-lux-ghost flex h-10 w-10 items-center justify-center rounded-full border border-white/20 text-secondary-container hover:text-white"
                >
                  <SocialGlyph name={item.icon} size={18} />
                </a>
              ))}
            </div>
          </div>

          <div>
            <h2 className="font-[family-name:var(--font-display)] text-2xl text-secondary-container">
              Pello Menos
            </h2>
            <nav className="mt-4 flex flex-col gap-2.5 text-sm text-white/75">
              <Link href="/termos" className="hover:text-secondary-container">
                Termos e Condições de uso
              </Link>
              <Link href="/privacidade" className="hover:text-secondary-container">
                Política de Privacidade
              </Link>
              <button
                type="button"
                onClick={onOpenAuth}
                className="text-left hover:text-secondary-container"
              >
                Minha Conta/Cadastre-se
              </button>
              <Link href="/desejos" className="hover:text-secondary-container">
                Lista de Desejos
              </Link>
            </nav>
          </div>

          <div>
            <h2 className="font-[family-name:var(--font-display)] text-2xl text-secondary-container">
              Informações para contato
            </h2>
            <ul className="mt-4 space-y-3 text-sm text-white/75">
              <li>
                <a
                  href="mailto:pellomenos@pellomenos.com.br"
                  className="inline-flex items-center gap-2 hover:text-secondary-container"
                >
                  <Icon name="mail" size={16} />
                  pellomenos@pellomenos.com.br
                </a>
              </li>
              <li>
                <a
                  href="tel:08002821233"
                  className="inline-flex items-center gap-2 hover:text-secondary-container"
                >
                  <Icon name="phone" size={16} />
                  SAC 0800 282 1233
                </a>
              </li>
              <li>
                <a
                  href={WHATSAPP_SAC}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 hover:text-secondary-container"
                >
                  <SocialGlyph name="whatsapp" size={16} />
                  Whatsapp Sac Pello Menos
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-10 grid gap-4 border-t border-white/15 pt-8 sm:grid-cols-3">
          {trust.map((item) => (
            <div
              key={item.label}
              className="flex items-center gap-3 text-secondary-container"
            >
              <Icon name={item.icon} size={18} />
              <span className="text-sm text-white/85">{item.label}</span>
            </div>
          ))}
        </div>
      </div>
    </footer>
  );
}
