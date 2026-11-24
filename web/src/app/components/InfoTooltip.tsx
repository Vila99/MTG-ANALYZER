"use client";

import { useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";

/** Icono de información con tooltip al pasar el ratón / foco, para explicar
 * un parámetro sin saturar la etiqueta.
 *
 * El bocadillo se renderiza en un portal a `document.body` en vez de como
 * hijo absoluto del icono: si el icono vive dentro de un contenedor con
 * scroll (p. ej. un modal con `overflow-y-auto`), un bocadillo posicionado
 * dentro de ese contenedor queda recortado al salirse de sus límites,
 * aunque tenga un z-index alto — el recorte por overflow no respeta
 * z-index. El portal lo saca de ese contenedor por completo. */
export function InfoTooltip({ children }: { children: ReactNode }) {
  const [coords, setCoords] = useState<{ top: number; left: number } | null>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  function show() {
    const rect = triggerRef.current?.getBoundingClientRect();
    if (rect) setCoords({ top: rect.top, left: rect.left + rect.width / 2 });
  }

  function hide() {
    setCoords(null);
  }

  return (
    <span className="inline-flex">
      <button
        ref={triggerRef}
        type="button"
        aria-label="Más información"
        className="flex items-center"
        style={{ color: "var(--ink-muted)" }}
        onMouseEnter={show}
        onMouseLeave={hide}
        onFocus={show}
        onBlur={hide}
      >
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
          <rect x="11" y="10.5" width="2" height="7" rx="0.5" fill="currentColor" />
          <circle cx="12" cy="7.2" r="1.3" fill="currentColor" />
        </svg>
      </button>
      {coords &&
        typeof document !== "undefined" &&
        createPortal(
          <span
            role="tooltip"
            className="pointer-events-none fixed z-[200] w-64 -translate-x-1/2 -translate-y-full rounded-sm border p-3 text-xs leading-relaxed"
            style={{
              top: coords.top - 8,
              left: coords.left,
              borderColor: "var(--border)",
              background: "var(--surface)",
              color: "var(--foreground)",
              boxShadow: "0 8px 24px rgba(0,0,0,0.35)",
            }}
          >
            {children}
          </span>,
          document.body
        )}
    </span>
  );
}
