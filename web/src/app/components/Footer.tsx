"use client";

import { useEffect, useState, type ReactElement } from "react";
import { ManaIcon } from "./ManaIcon";

const MANA_COLORS = ["W", "U", "B", "R", "G"];

function GithubIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="currentColor"
        d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.221-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0 1 12 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0 0 22 12.017C22 6.484 17.522 2 12 2Z"
      />
    </svg>
  );
}

function XIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="currentColor"
        d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"
      />
    </svg>
  );
}

function InstagramIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="3" y="3" width="18" height="18" rx="5" stroke="currentColor" strokeWidth="2" />
      <circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="2" />
      <circle cx="17.3" cy="6.7" r="1.3" fill="currentColor" />
    </svg>
  );
}

const SOCIAL_LINKS: { label: string; href: string; Icon: () => ReactElement }[] = [
  { label: "GitHub", href: "https://github.com/Vila99", Icon: GithubIcon },
  { label: "X (Twitter)", href: "https://x.com/gvila99", Icon: XIcon },
  { label: "Instagram", href: "https://www.instagram.com/gvila99/", Icon: InstagramIcon },
];

/** Pie de página: identidad legal a la izquierda, los cinco colores de maná
 * como separador central, y redes sociales a la derecha. */
export function Footer() {
  // new Date() es un valor "inestable" para el prerender estático de
  // Next.js (Cache Components): se calcula tras montar en el cliente en
  // vez de durante el build, con un valor de respaldo razonable mientras.
  const [year, setYear] = useState(2026);
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setYear(new Date().getFullYear());
  }, []);

  return (
    <footer className="border-t" style={{ borderColor: "var(--border)" }}>
      {/* Grid de 3 columnas iguales (33.3% cada una) en vez de un flex
       * justify-between: con columnas de ancho igual, la del medio queda
       * centrada de verdad sin importar que el bloque legal sea más largo
       * que el de redes sociales. En móvil es una sola columna centrada; el
       * margen lateral crece con la pantalla en vez de ser fijo (antes eran
       * 10rem a cada lado siempre, que en un móvil dejaban el texto en una
       * columna de pocas letras). */}
      <div className="grid grid-cols-1 items-center gap-5 px-5 py-6 text-center sm:grid-cols-3 sm:gap-4 sm:px-10 sm:py-5 sm:text-left lg:px-40">
        <div className="flex flex-col gap-1 text-xs leading-relaxed" style={{ color: "var(--ink-muted)" }}>
          <p className="font-head text-xs font-extrabold uppercase tracking-wide" style={{ color: "var(--foreground)" }}>
            MTG Deck Analyzer
          </p>
          <p>© {year} Vila. Todos los derechos reservados.</p>
          <p>Magic: The Gathering es marca de Wizards of the Coast. Fan-project no afiliado.</p>
          <p>Datos e imágenes de cartas vía Scryfall.</p>
        </div>

        <span className="flex items-center justify-center gap-2 text-xl" aria-hidden="true">
          {MANA_COLORS.map((color) => (
            <ManaIcon key={color} color={color} />
          ))}
        </span>

        <div className="flex items-center justify-center gap-1 sm:justify-end">
          {SOCIAL_LINKS.map(({ label, href, Icon }) => (
            <a
              key={label}
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={label}
              className="flex h-11 w-11 items-center justify-center transition-opacity hover:opacity-70"
              style={{ color: "var(--ink-muted)" }}
            >
              <Icon />
            </a>
          ))}
        </div>
      </div>
    </footer>
  );
}
