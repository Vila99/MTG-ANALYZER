"use client";

import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";

const BUBBLE_WIDTH = 256;
const VIEWPORT_MARGIN = 12;

type Placement = { top: number; left: number; below: boolean };

/** Botón "i" con un bocadillo de ayuda (toggletip), para explicar un
 * parámetro sin saturar la etiqueta.
 *
 * Se abre al pasar el ratón, al recibir el foco y también al tocarlo o
 * pulsarlo: en táctil no hay hover, y Safari en iOS no da el foco a un botón
 * al tocarlo, así que sin el clic el bocadillo era inalcanzable en móvil.
 * Se cierra con Escape, tocando fuera o al hacer scroll.
 *
 * El bocadillo se renderiza en un portal a `document.body` en vez de como
 * hijo absoluto del icono: si el icono vive dentro de un contenedor con
 * scroll (p. ej. un modal con `overflow-y-auto`), un bocadillo posicionado
 * dentro de ese contenedor queda recortado al salirse de sus límites,
 * aunque tenga un z-index alto — el recorte por overflow no respeta
 * z-index. El portal lo saca de ese contenedor por completo. Su posición se
 * ajusta para no salirse de la pantalla (en un móvil, un icono pegado al
 * borde dejaba medio bocadillo fuera). */
export function InfoTooltip({ children }: { children: ReactNode }) {
  const [placement, setPlacement] = useState<Placement | null>(null);
  const [pinned, setPinned] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const bubbleId = useId();

  function show() {
    const rect = triggerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const half = BUBBLE_WIDTH / 2;
    const minLeft = VIEWPORT_MARGIN + half;
    const maxLeft = window.innerWidth - VIEWPORT_MARGIN - half;
    const left = Math.min(Math.max(rect.left + rect.width / 2, minLeft), Math.max(minLeft, maxLeft));
    // Arriba del icono si cabe; si no (icono cerca del borde superior), debajo.
    const below = rect.top < 160;
    setPlacement({ top: below ? rect.bottom + 8 : rect.top - 8, left, below });
  }

  function hide() {
    setPlacement(null);
    setPinned(false);
  }

  useEffect(() => {
    if (!placement) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") hide();
    };
    const onPointerDown = (e: PointerEvent) => {
      if (!triggerRef.current?.contains(e.target as Node)) hide();
    };
    // El bocadillo es `fixed`: con scroll se quedaría separado del icono.
    const onScroll = () => hide();
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("scroll", onScroll, { capture: true, passive: true });
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("scroll", onScroll, { capture: true });
    };
  }, [placement]);

  return (
    <span className="inline-flex">
      <button
        ref={triggerRef}
        type="button"
        aria-label="Más información"
        aria-expanded={placement !== null}
        aria-controls={placement ? bubbleId : undefined}
        className="hit-area flex items-center"
        style={{ color: "var(--ink-muted)" }}
        onPointerEnter={(e) => {
          if (e.pointerType === "mouse") show();
        }}
        onPointerLeave={(e) => {
          if (e.pointerType === "mouse" && !pinned) setPlacement(null);
        }}
        onFocus={show}
        onBlur={hide}
        onClick={(e) => {
          // Evita que el clic active la <label> que envuelve al icono.
          e.preventDefault();
          if (pinned) {
            hide();
          } else {
            setPinned(true);
            show();
          }
        }}
      >
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
          <rect x="11" y="10.5" width="2" height="7" rx="0.5" fill="currentColor" />
          <circle cx="12" cy="7.2" r="1.3" fill="currentColor" />
        </svg>
      </button>
      {placement &&
        typeof document !== "undefined" &&
        createPortal(
          <span
            id={bubbleId}
            role="tooltip"
            className={`pointer-events-none fixed z-[200] -translate-x-1/2 rounded-sm border p-3 text-xs leading-relaxed ${
              placement.below ? "" : "-translate-y-full"
            }`}
            style={{
              top: placement.top,
              left: placement.left,
              width: `min(${BUBBLE_WIDTH}px, calc(100vw - ${VIEWPORT_MARGIN * 2}px))`,
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
