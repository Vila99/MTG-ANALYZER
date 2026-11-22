import type { Metadata } from "next";
import { Montserrat, Roboto } from "next/font/google";
import "./globals.css";

const montserrat = Montserrat({
  variable: "--font-montserrat",
  subsets: ["latin"],
  weight: ["600", "700", "800"],
});

const roboto = Roboto({
  variable: "--font-roboto",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
});

export const metadata: Metadata = {
  title: "MTG Commander Deck Analyzer",
  description: "Analiza decks de Commander/EDH y propone mejoras con ayuda de Claude.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="es"
      className={`${montserrat.variable} ${roboto.variable} h-full antialiased`}
    >
      <head>
        {/* MANDATORY: avoid a flash of un-themed content before CSS loads */}
        <meta name="color-scheme" content="light dark" />
        {/* eslint-disable-next-line @next/next/no-css-tags -- hoja de estilos de un paquete de iconos vendorizado en public/, no un modulo importable */}
        <link rel="stylesheet" href="/mana-master/css/mana.css" />
      </head>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
