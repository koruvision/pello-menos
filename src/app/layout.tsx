import type { Metadata } from "next";
import { Cormorant_Garamond, Manrope } from "next/font/google";
import {
  GoogleTagManagerBody,
  GoogleTagManagerHead,
} from "@/components/GoogleTagManager";
import { Providers } from "@/components/Providers";
import "./globals.css";

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const display = Cormorant_Garamond({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Pello Menos - Depilação",
  description:
    "Depilação a laser e cera. Prontas pra viver. Pacotes e avulsos com desconto.",
  icons: {
    icon: [
      {
        url: "https://loja.pellomenos.com.br/wp-content/uploads/2021/04/cropped-favicon-50x50.png",
        sizes: "32x32",
        type: "image/png",
      },
      {
        url: "https://loja.pellomenos.com.br/wp-content/uploads/2021/04/cropped-favicon-300x300.png",
        sizes: "192x192",
        type: "image/png",
      },
    ],
    apple:
      "https://loja.pellomenos.com.br/wp-content/uploads/2021/04/cropped-favicon-300x300.png",
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="pt-BR"
      className={`${manrope.variable} ${display.variable} h-full antialiased`}
    >
      <head>
        <GoogleTagManagerHead />
      </head>
      <body
        className="min-h-full bg-background font-sans text-on-background"
        suppressHydrationWarning
      >
        <GoogleTagManagerBody />
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
