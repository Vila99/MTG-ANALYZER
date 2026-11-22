import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "MTG Commander Deck Analyzer",
  description: "Analiza decks de Commander/EDH y propone mejoras con ayuda de Claude.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="es"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        {/* MANDATORY: avoid a flash of un-themed content before CSS loads */}
        <meta name="color-scheme" content="light dark" />
      </head>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
