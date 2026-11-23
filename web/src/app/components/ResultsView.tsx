"use client";

import { Fragment, useEffect, useState } from "react";
import {
  AñadidoSugerido,
  AnalyzeResponse,
  COLOR_LABELS,
  CorteSugerido,
  ROLE_LABELS,
} from "../types";
import { ManaIcon } from "./ManaIcon";
import { BarDatum, SingleSeriesBarChart } from "./SingleSeriesBarChart";

const RUBRIC_ORDER = ["land", "ramp", "draw", "removal", "wipe"];
const STATUS_LABEL: Record<string, string> = { bajo: "Bajo", ok: "Dentro de rango", alto: "Alto" };
const STATUS_COLOR_VAR: Record<string, string> = {
  bajo: "var(--status-warning)",
  ok: "var(--status-good)",
  alto: "var(--status-critical)",
};
const SEVERITY_ORDER: Record<string, number> = { alta: 0, media: 1, baja: 2 };
const SEVERITY_COLOR_VAR: Record<string, string> = {
  alta: "var(--status-critical)",
  media: "var(--status-warning)",
  baja: "var(--ink-muted)",
};

interface HoverTarget {
  name: string;
  rect: DOMRect;
}

type HoverHandler = (name: string | null, el: HTMLElement | null) => void;

/** Nota simbólica 0-10 (ver analyzer.scoring): combina el rubric con la
 * severidad de los problemas detectados, para dar feedback rápido de cómo
 * ha salido el análisis de un vistazo. */
function scoreColorVar(score: number): string {
  if (score >= 8) return "var(--status-good)";
  if (score >= 5) return "var(--status-warning)";
  return "var(--status-critical)";
}

function scoreLabel(score: number): string {
  if (score >= 8) return "Sólido";
  if (score >= 5) return "Mejorable";
  return "Necesita trabajo";
}

function DeckScoreBadge({ score }: { score: number }) {
  const color = scoreColorVar(score);
  return (
    <div className="flex flex-shrink-0 items-center gap-2.5 text-right">
      <div>
        <p className="font-head text-xs font-extrabold uppercase tracking-wide" style={{ color: "var(--ink-muted)" }}>
          Nota del análisis
        </p>
        <p className="font-head text-xs font-bold" style={{ color }}>
          {scoreLabel(score)}
        </p>
      </div>
      <div
        className="font-head flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full border-2 text-xl font-extrabold"
        style={{ borderColor: color, color }}
      >
        {score.toFixed(1)}
      </div>
    </div>
  );
}

const COLOR_GLOW: Record<string, string> = {
  W: "#e8dfb8",
  U: "#2f6fd1",
  B: "#7c5ba6",
  R: "#e0552f",
  G: "#2f9e58",
};

/** Fondo decorativo: manchas difuminadas con los colores de la identidad del
 * comandante, fijas detrás del contenido, para dar un toque temático sin
 * estorbar la lectura. */
function ColorThemeBackground({ colors }: { colors: string[] | undefined }) {
  // defensivo: un analisis guardado en localStorage (ver lib/recentAnalyses)
  // antes de que existiera este campo no lo tendria.
  if (!colors || colors.length === 0) return null;
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden" aria-hidden="true">
      {colors.map((color, i) => (
        <div
          key={color}
          style={{
            position: "absolute",
            top: "-15%",
            left: `${(i / Math.max(colors.length - 1, 1)) * 70}%`,
            width: "45vw",
            height: "45vw",
            maxWidth: 560,
            maxHeight: 560,
            borderRadius: "50%",
            background: COLOR_GLOW[color],
            filter: "blur(110px)",
            opacity: 0.22,
          }}
        />
      ))}
    </div>
  );
}

function StatTile({
  label,
  value,
  warning,
}: {
  label: string;
  value: string | number;
  /** Aviso rojo bajo el valor; `detail` hace de tooltip nativo al pasar el ratón. */
  warning?: { label: string; detail: string };
}) {
  return (
    <div className="rounded-sm border p-4" style={{ borderColor: "var(--border)", background: "var(--surface)" }}>
      <p className="font-head text-xs font-extrabold uppercase tracking-wide" style={{ color: "var(--ink-muted)" }}>
        {label}
      </p>
      <p className="text-2xl font-bold font-mono" style={{ color: "var(--foreground)" }}>
        {value}
      </p>
      {warning && (
        <p
          className="mt-1 cursor-help truncate text-[11px] font-bold"
          style={{ color: "var(--status-critical)" }}
          title={warning.detail}
        >
          ⚠ {warning.label}
        </p>
      )}
    </div>
  );
}

function SectionLabel({ children, color }: { children: React.ReactNode; color?: string }) {
  return (
    <p
      className="font-head text-xs font-extrabold uppercase tracking-wide mb-2"
      style={{ color: color ?? "var(--accent)" }}
    >
      {children}
    </p>
  );
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** Subraya los nombres de carta conocidos dentro de un texto libre; al pasar
 * el cursor por encima, avisa con el elemento para que una vista previa
 * flotante se posicione justo ahí (como un tooltip, no un panel aparte). */
function HighlightedText({
  text,
  cardImages,
  onHover,
}: {
  text: string;
  cardImages: Record<string, string>;
  onHover: HoverHandler;
}) {
  const names = Object.keys(cardImages).sort((a, b) => b.length - a.length);
  if (names.length === 0) {
    return <>{text}</>;
  }
  const pattern = new RegExp(`(${names.map(escapeRegExp).join("|")})`, "g");
  const parts = text.split(pattern);
  return (
    <>
      {parts.map((part, i) =>
        cardImages[part] ? (
          <span
            key={i}
            className="underline-card"
            onMouseEnter={(e) => onHover(part, e.currentTarget)}
            onMouseLeave={() => onHover(null, null)}
          >
            {part}
          </span>
        ) : (
          <Fragment key={i}>{part}</Fragment>
        ),
      )}
    </>
  );
}

/** Tooltip flotante que sigue a la carta subrayada que se está mirando, en
 * vez de vivir fijo en una columna aparte. */
function FloatingCardPreview({
  target,
  cardImages,
}: {
  target: HoverTarget | null;
  cardImages: Record<string, string>;
}) {
  if (!target) return null;
  const imageUrl = cardImages[target.name];
  if (!imageUrl) return null;

  const width = 220;
  const height = Math.round((width * 7) / 5);
  const margin = 12;
  let left = target.rect.left;
  let top = target.rect.bottom + 8;
  if (typeof window !== "undefined") {
    if (left + width > window.innerWidth - margin) left = window.innerWidth - width - margin;
    if (left < margin) left = margin;
    if (top + height > window.innerHeight - margin) top = target.rect.top - height - 8;
  }

  return (
    <div
      className="pointer-events-none fixed z-50 overflow-hidden rounded-sm border"
      style={{ left, top, width, borderColor: "var(--border)", boxShadow: "0 14px 32px rgba(0,0,0,0.4)" }}
    >
      {/* eslint-disable-next-line @next/next/no-img-element -- imagen externa de Scryfall */}
      <img src={imageUrl} alt={target.name} className="h-full w-full object-cover" style={{ aspectRatio: "5/7" }} />
    </div>
  );
}

interface SwapGroup {
  cut?: CorteSugerido;
  additions: AñadidoSugerido[];
}

/** Agrupa todas las alternativas de añadido que sustituyen a un mismo corte
 * (por `reemplaza_a`), para mostrar "Corta X -> Añade Y / Z / W" en vez de
 * forzar una única alternativa por corte. */
function pairCutsAndAdditions(cuts: CorteSugerido[], additions: AñadidoSugerido[]): SwapGroup[] {
  const byReemplazaA = new Map<string, AñadidoSugerido[]>();
  const standalone: AñadidoSugerido[] = [];

  for (const addition of additions) {
    if (addition.reemplaza_a && cuts.some((cut) => cut.carta === addition.reemplaza_a)) {
      const list = byReemplazaA.get(addition.reemplaza_a) ?? [];
      list.push(addition);
      byReemplazaA.set(addition.reemplaza_a, list);
    } else {
      standalone.push(addition);
    }
  }

  const groups: SwapGroup[] = cuts.map((cut) => ({
    cut,
    additions: byReemplazaA.get(cut.carta) ?? [],
  }));
  for (const addition of standalone) {
    groups.push({ additions: [addition] });
  }
  return groups;
}

/** Miniatura clicable (zoom) de una carta dentro de un cambio sugerido, con
 * su etiqueta (Corta/Añade) encima para identificarla de un vistazo sin
 * tener que pasar el ratón por el nombre. */
function SwapThumbnail({
  name,
  label,
  labelColor,
  imageUrl,
  onZoom,
  dimmed,
}: {
  name: string;
  label: string;
  labelColor: string;
  imageUrl: string | undefined;
  onZoom: (name: string) => void;
  dimmed?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={() => imageUrl && onZoom(name)}
      disabled={!imageUrl}
      className="flex w-[84px] flex-shrink-0 flex-col items-center gap-1 text-center transition-transform enabled:hover:scale-[1.05] disabled:cursor-default"
      style={{ opacity: dimmed ? 0.5 : 1 }}
    >
      <div className="font-head text-[10px] font-extrabold uppercase" style={{ color: labelColor }}>
        {label}
      </div>
      <div
        className="w-full overflow-hidden rounded-sm border"
        style={{ aspectRatio: "5/7", borderColor: "var(--border)", background: "var(--surface-muted)" }}
      >
        {imageUrl ? (
          // eslint-disable-next-line @next/next/no-img-element -- imagen externa de Scryfall
          <img src={imageUrl} alt={name} className="h-full w-full object-cover" />
        ) : null}
      </div>
      <p className="w-full truncate text-[11px]" style={{ color: "var(--foreground)" }} title={name}>
        {name}
      </p>
    </button>
  );
}

function SwapGroupCard({
  group,
  cardImages,
  onHover,
  onZoom,
}: {
  group: SwapGroup;
  cardImages: Record<string, string>;
  onHover: HoverHandler;
  onZoom: (name: string) => void;
}) {
  const [optionIndex, setOptionIndex] = useState(0);
  const selected = group.additions[optionIndex];

  return (
    <div className="flex flex-wrap items-center gap-3 p-4" style={{ background: "var(--surface)" }}>
      {group.cut && (
        <SwapThumbnail
          name={group.cut.carta}
          label="Corta"
          labelColor="var(--status-critical)"
          imageUrl={cardImages[group.cut.carta]}
          onZoom={onZoom}
        />
      )}
      {group.cut && selected && (
        <span className="hidden self-center text-lg sm:block" style={{ color: "var(--ink-muted)" }}>
          →
        </span>
      )}

      {selected && (
        <SwapThumbnail
          name={selected.carta}
          label="Añade"
          labelColor="var(--status-good)"
          imageUrl={cardImages[selected.carta]}
          onZoom={onZoom}
          dimmed={selected.incluido === false}
        />
      )}

      {selected && (
        <div className="flex min-w-[220px] flex-1 flex-col gap-1">
          <div className="flex flex-wrap items-baseline gap-2">
            <span className="text-[11px]" style={{ color: "var(--ink-muted)" }}>
              {selected.rol}
            </span>
            {typeof selected.precio_eur === "number" && (
              <span className="font-mono text-[11px] font-bold" style={{ color: "var(--ink-secondary)" }}>
                {selected.precio_eur.toFixed(2)} €
              </span>
            )}
            {selected.incluido === false && (
              <span className="font-head text-[10px] font-bold uppercase" style={{ color: "var(--status-warning)" }}>
                Fuera de presupuesto
              </span>
            )}
          </div>
          <p className="text-sm leading-relaxed" style={{ color: "var(--foreground)" }}>
            <HighlightedText text={selected.motivo} cardImages={cardImages} onHover={onHover} />
          </p>
          {group.additions.length > 1 && (
            <div className="mt-1 flex items-center gap-1.5">
              <span className="text-[10px]" style={{ color: "var(--ink-muted)" }}>
                opción:
              </span>
              {group.additions.map((_, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => setOptionIndex(i)}
                  className="font-head flex h-6 w-6 items-center justify-center rounded-full text-[11px] font-bold"
                  style={{
                    background: i === optionIndex ? "var(--accent)" : "var(--surface-muted)",
                    color: i === optionIndex ? "var(--accent-ink)" : "var(--ink-muted)",
                  }}
                >
                  {i + 1}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {!selected && group.cut && (
        <p className="min-w-[220px] flex-1 text-sm leading-relaxed" style={{ color: "var(--foreground)" }}>
          <HighlightedText text={group.cut.motivo} cardImages={cardImages} onHover={onHover} />
        </p>
      )}
    </div>
  );
}

function RoleCardGallery({
  roleLabel,
  cardNames,
  cardImages,
  onClose,
  onCardClick,
}: {
  roleLabel: string;
  cardNames: string[];
  cardImages: Record<string, string>;
  onClose: () => void;
  onCardClick: (name: string) => void;
}) {
  return (
    <div className="rounded-sm border p-4" style={{ borderColor: "var(--border)", background: "var(--surface)" }}>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-head text-xs font-extrabold uppercase tracking-wide" style={{ color: "var(--ink-muted)" }}>
          Cartas en &quot;{roleLabel}&quot; ({cardNames.length})
        </h3>
        <button
          type="button"
          onClick={onClose}
          className="font-head text-xs font-bold"
          style={{ color: "var(--ink-muted)" }}
        >
          Cerrar ✕
        </button>
      </div>
      <div className="grid grid-cols-3 gap-3 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-10">
        {cardNames.map((name) => (
          <button
            type="button"
            key={name}
            onClick={() => onCardClick(name)}
            disabled={!cardImages[name]}
            className="flex flex-col gap-1 text-left transition-transform hover:scale-[1.04] disabled:cursor-default disabled:hover:scale-100"
          >
            <div
              className="overflow-hidden rounded-sm border"
              style={{ aspectRatio: "5/7", borderColor: "var(--border)", background: "var(--surface-muted)" }}
            >
              {cardImages[name] ? (
                // eslint-disable-next-line @next/next/no-img-element -- imagen externa de Scryfall
                <img src={cardImages[name]} alt={name} className="h-full w-full object-cover" />
              ) : null}
            </div>
            <p className="truncate text-center text-[11px]" style={{ color: "var(--ink-secondary)" }} title={name}>
              {name}
            </p>
          </button>
        ))}
      </div>
    </div>
  );
}

/** Vista ampliada de una carta al hacer clic en su miniatura, con una
 * pequeña animación de entrada en vez de aparecer de golpe. */
function CardZoomModal({
  name,
  imageUrl,
  onClose,
}: {
  name: string;
  imageUrl: string;
  onClose: () => void;
}) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const raf = requestAnimationFrame(() => setVisible(true));
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-[80] flex cursor-pointer items-center justify-center p-6"
      style={{ background: "rgba(0,0,0,0.75)", opacity: visible ? 1 : 0, transition: "opacity 150ms ease" }}
      onClick={onClose}
    >
      {/* eslint-disable-next-line @next/next/no-img-element -- imagen externa de Scryfall */}
      <img
        src={imageUrl}
        alt={name}
        onClick={(e) => e.stopPropagation()}
        className="max-h-full rounded-md"
        style={{
          width: 360,
          aspectRatio: "5/7",
          objectFit: "cover",
          boxShadow: "0 24px 60px rgba(0,0,0,0.6)",
          transform: visible ? "scale(1)" : "scale(0.85)",
          transition: "transform 150ms ease",
        }}
      />
    </div>
  );
}

/** Detalle de un combo detectado: imágenes de las cartas que lo forman y su
 * explicación completa, en un modal en vez de saturar la sección de
 * bracket con el texto de cada combo. */
function ComboDetailModal({
  combo,
  cardImages,
  onClose,
  onZoomCard,
}: {
  combo: { cartas: string[]; produce: string[]; descripcion: string; velocidad?: string };
  cardImages: Record<string, string>;
  onClose: () => void;
  onZoomCard: (name: string) => void;
}) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-[60] flex cursor-pointer items-center justify-center p-6"
      style={{ background: "rgba(0,0,0,0.75)" }}
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg rounded-sm border"
        style={{ borderColor: "var(--border)", background: "var(--background)" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b p-4" style={{ borderColor: "var(--border)" }}>
          <h2 className="font-head text-sm font-extrabold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
            Combo detectado
          </h2>
          <button type="button" onClick={onClose} className="font-head text-xs font-bold" style={{ color: "var(--ink-muted)" }}>
            Cerrar ✕
          </button>
        </div>

        <div className="flex flex-wrap gap-3 p-4">
          {combo.cartas.map((name) => (
            <button
              type="button"
              key={name}
              onClick={() => onZoomCard(name)}
              disabled={!cardImages[name]}
              className="flex w-[110px] flex-col gap-1 text-left transition-transform enabled:hover:scale-[1.04] disabled:cursor-default"
            >
              <div
                className="overflow-hidden rounded-sm border"
                style={{ aspectRatio: "5/7", borderColor: "var(--border)", background: "var(--surface-muted)" }}
              >
                {cardImages[name] ? (
                  // eslint-disable-next-line @next/next/no-img-element -- imagen externa de Scryfall
                  <img src={cardImages[name]} alt={name} className="h-full w-full object-cover" />
                ) : null}
              </div>
              <p className="truncate text-center text-[11px]" style={{ color: "var(--ink-secondary)" }} title={name}>
                {name}
              </p>
            </button>
          ))}
        </div>

        <div className="border-t p-4" style={{ borderColor: "var(--border)" }}>
          {combo.velocidad && (
            <span
              className="font-head text-[10px] font-bold uppercase"
              style={{ color: combo.velocidad === "temprano" ? "var(--status-critical)" : "var(--status-warning)" }}
            >
              {combo.velocidad}
            </span>
          )}
          {combo.produce.length > 0 && (
            <p className="mt-1 text-sm" style={{ color: "var(--foreground)" }}>
              <strong>Produce:</strong> {combo.produce.join(", ")}
            </p>
          )}
          {combo.descripcion && (
            <p className="mt-2 text-sm leading-relaxed" style={{ color: "var(--foreground)" }}>
              {combo.descripcion}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export function ResultsView({ result }: { result: AnalyzeResponse }) {
  const [hoverTarget, setHoverTarget] = useState<HoverTarget | null>(null);
  const [expandedRole, setExpandedRole] = useState<string | null>(null);
  const [zoomedCard, setZoomedCard] = useState<string | null>(null);
  const [openCombo, setOpenCombo] = useState<number | null>(null);
  const cardImages = result.card_images ?? {};
  const cartasPorRol = result.cartas_por_rol ?? {};

  const handleHover: HoverHandler = (name, el) => {
    setHoverTarget(name && el ? { name, rect: el.getBoundingClientRect() } : null);
  };

  const manaCurveData: BarDatum[] = Object.entries(result.curva_mana)
    .sort((a, b) => Number(a[0]) - Number(b[0]))
    .map(([cmc, count]) => ({ label: cmc, value: count }));

  const rolesData: BarDatum[] = Object.entries(result.roles)
    .filter(([role]) => role !== "other")
    .map(([role, count]) => ({ label: ROLE_LABELS[role] ?? role, value: count, key: role }));

  function handleRoleBarClick(item: BarDatum) {
    const role = item.key;
    if (!role) return;
    setExpandedRole((current) => (current === role ? null : role));
  }

  const analisis = result.analisis;
  const swaps = analisis ? pairCutsAndAdditions(analisis.cortes_sugeridos, analisis.anadidos_sugeridos) : [];
  const sortedProblemas = analisis
    ? [...analisis.problemas].sort((a, b) => (SEVERITY_ORDER[a.severidad] ?? 9) - (SEVERITY_ORDER[b.severidad] ?? 9))
    : [];

  return (
    <div className="flex flex-col gap-7" onMouseLeave={() => setHoverTarget(null)}>
      <ColorThemeBackground colors={result.identidad_color} />
      <FloatingCardPreview target={hoverTarget} cardImages={cardImages} />
      {zoomedCard && cardImages[zoomedCard] && (
        <CardZoomModal name={zoomedCard} imageUrl={cardImages[zoomedCard]} onClose={() => setZoomedCard(null)} />
      )}
      {openCombo !== null && analisis?.combos_detectados?.[openCombo] && (
        <ComboDetailModal
          combo={analisis.combos_detectados[openCombo]}
          cardImages={cardImages}
          onClose={() => setOpenCombo(null)}
          onZoomCard={(name) => setZoomedCard(name)}
        />
      )}

      <section className="flex flex-col gap-5 border-b pb-6" style={{ borderColor: "var(--border)" }}>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2.5">
              <h2 className="font-head text-2xl font-extrabold" style={{ color: "var(--foreground)" }}>
                {result.comandantes.length > 0 ? result.comandantes.join(" + ") : "Sin comandante detectado"}
              </h2>
              {result.identidad_color && result.identidad_color.length > 0 && (
                <span className="flex items-center gap-1 text-xl" aria-hidden="true">
                  {result.identidad_color.map((color) => (
                    <ManaIcon key={color} color={color} />
                  ))}
                </span>
              )}
            </div>
            {analisis?.bracket && (
              <p className="font-head mt-1 text-xs font-bold uppercase tracking-wide" style={{ color: "var(--ink-muted)" }}>
                Bracket deducido {analisis.bracket.deducido} · {analisis.arquetipo}
              </p>
            )}
          </div>
          <DeckScoreBadge score={result.nota_deck} />
        </div>

        <div className="flex flex-col gap-5 lg:flex-row lg:items-start">
          {result.comandantes.length > 0 && (
            <div className="flex flex-shrink-0 gap-2 lg:w-[220px]">
              {result.comandantes.map((name) => (
                <div
                  key={name}
                  className="w-full overflow-hidden rounded-sm border"
                  style={{ borderColor: "var(--border)" }}
                >
                  {cardImages[name] ? (
                    // eslint-disable-next-line @next/next/no-img-element -- imagen externa de Scryfall
                    <img
                      src={cardImages[name]}
                      alt={name}
                      className="block w-full"
                      style={{ aspectRatio: "5/7", objectFit: "cover" }}
                    />
                  ) : (
                    <div
                      className="flex items-center justify-center p-3 text-center text-xs"
                      style={{ aspectRatio: "5/7", background: "var(--surface-muted)", color: "var(--ink-muted)" }}
                    >
                      Sin imagen
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          <div className="flex min-w-0 flex-1 flex-col gap-4">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <StatTile
                label="Tamaño del deck"
                value={result.tamano_deck}
                warning={
                  result.no_encontradas.length > 0
                    ? {
                        label: `no encontrada${result.no_encontradas.length > 1 ? "s" : ""}`,
                        detail: result.no_encontradas.join(", "),
                      }
                    : undefined
                }
              />
              <StatTile label="Tierras" value={result.tierras} />
              <StatTile label="CMC medio" value={result.cmc_medio.toFixed(2)} />
              <StatTile
                label="Coste aproximado"
                value={`${result.coste_aproximado.total_eur.toFixed(2)} €`}
                warning={
                  result.coste_aproximado.cartas_sin_precio.length > 0
                    ? {
                        label: "sin precio para algunas cartas",
                        detail: result.coste_aproximado.cartas_sin_precio.join(", "),
                      }
                    : undefined
                }
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <SingleSeriesBarChart
                title="Curva de maná (sin tierras)"
                data={manaCurveData}
                colorVar="var(--chart-mana)"
                valueLabel="cartas"
              />
              <SingleSeriesBarChart
                title="Cartas por rol"
                data={rolesData}
                colorVar="var(--chart-roles)"
                valueLabel="cartas"
                onBarClick={handleRoleBarClick}
              />
            </div>
          </div>
        </div>
      </section>

      {expandedRole && cartasPorRol[expandedRole] && (
        <RoleCardGallery
          roleLabel={ROLE_LABELS[expandedRole] ?? expandedRole}
          cardNames={cartasPorRol[expandedRole]}
          cardImages={cardImages}
          onClose={() => setExpandedRole(null)}
          onCardClick={(name) => setZoomedCard(name)}
        />
      )}

      {result.no_legales.length > 0 && (
        <section
          className="rounded-sm border p-4"
          style={{ borderColor: "var(--status-critical)", background: "var(--surface)" }}
        >
          <p style={{ color: "var(--foreground)" }}>
            <strong>No legales en Commander:</strong> {result.no_legales.join(", ")}
          </p>
        </section>
      )}

      <section className="grid gap-4 lg:grid-cols-[1.3fr_1fr]">
        <div
          tabIndex={0}
          role="region"
          aria-labelledby="rubric-table-caption"
          className="overflow-auto rounded-sm border"
          style={{ borderColor: "var(--border)" }}
        >
          <table className="w-full text-sm">
            <caption
              id="rubric-table-caption"
              className="font-head border-b p-3 text-left text-xs font-extrabold uppercase tracking-wide"
              style={{ borderColor: "var(--border)", color: "var(--ink-muted)" }}
            >
              Comparación con el rubric base
            </caption>
            <thead>
              <tr style={{ background: "var(--surface-muted)" }}>
                <th className="p-2 text-left" style={{ color: "var(--ink-secondary)" }}>
                  Rol
                </th>
                <th className="p-2 text-left" style={{ color: "var(--ink-secondary)" }}>
                  Cantidad
                </th>
                <th className="p-2 text-left" style={{ color: "var(--ink-secondary)" }}>
                  Estado
                </th>
              </tr>
            </thead>
            <tbody>
              {RUBRIC_ORDER.map((role) => {
                const status = result.rubric[role];
                return (
                  <tr key={role} style={{ borderTop: "1px solid var(--border)" }}>
                    <th scope="row" className="p-2 text-left font-normal" style={{ color: "var(--foreground)" }}>
                      {ROLE_LABELS[role] ?? role}
                    </th>
                    <td className="p-2 font-mono" style={{ color: "var(--foreground)" }}>
                      {result.roles[role] ?? 0}
                    </td>
                    <td className="p-2">
                      <span className="inline-flex items-center gap-1.5" style={{ color: "var(--foreground)" }}>
                        <span
                          aria-hidden="true"
                          className="inline-block h-2.5 w-2.5 rounded-full"
                          style={{ background: STATUS_COLOR_VAR[status] }}
                        />
                        {STATUS_LABEL[status] ?? status}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div
          tabIndex={0}
          role="region"
          aria-labelledby="pips-table-caption"
          className="overflow-auto rounded-sm border"
          style={{ borderColor: "var(--border)" }}
        >
          <table className="w-full text-sm">
            <caption
              id="pips-table-caption"
              className="font-head border-b p-3 text-left text-xs font-extrabold uppercase tracking-wide"
              style={{ borderColor: "var(--border)", color: "var(--ink-muted)" }}
            >
              Pips vs. fuentes de maná
            </caption>
            <thead>
              <tr style={{ background: "var(--surface-muted)" }}>
                <th className="p-2 text-left" style={{ color: "var(--ink-secondary)" }}>
                  Color
                </th>
                <th className="p-2 text-left" style={{ color: "var(--ink-secondary)" }}>
                  Pips
                </th>
                <th className="p-2 text-left" style={{ color: "var(--ink-secondary)" }}>
                  Fuentes
                </th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(COLOR_LABELS).map(([code, label]) => (
                <tr key={code} style={{ borderTop: "1px solid var(--border)" }}>
                  <th scope="row" className="p-2 text-left font-normal" style={{ color: "var(--foreground)" }}>
                    <span className="inline-flex items-center gap-2">
                      <ManaIcon color={code} />
                      {label}
                    </span>
                  </th>
                  <td className="p-2 font-mono" style={{ color: "var(--foreground)" }}>
                    {result.pips[code] ?? 0}
                  </td>
                  <td className="p-2 font-mono" style={{ color: "var(--foreground)" }}>
                    {result.fuentes_mana[code] ?? 0}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {analisis && (
        <>
          {analisis.bracket && (
            <section className="rounded-sm border p-5" style={{ borderColor: "var(--border)", background: "var(--surface)" }}>
              <p className="font-head text-2xl font-extrabold" style={{ color: "var(--accent)" }}>
                BRACKET {analisis.bracket.deducido}
              </p>
              {analisis.bracket.game_changers.length > 0 && (
                <p className="mt-2 text-sm" style={{ color: "var(--foreground)" }}>
                  <strong>Game Changers:</strong> {analisis.bracket.game_changers.join(", ")}
                </p>
              )}
              {analisis.combos_detectados && analisis.combos_detectados.length > 0 && (
                <div className="mt-3">
                  <p className="font-head text-xs font-extrabold uppercase" style={{ color: "var(--foreground)" }}>
                    Combos detectados (verificado contra Commander Spellbook)
                  </p>
                  <ul className="mt-1.5 flex flex-col gap-1.5">
                    {analisis.combos_detectados.map((combo, i) => (
                      <li key={i} className="text-sm" style={{ color: "var(--foreground)" }}>
                        <button
                          type="button"
                          onClick={() => setOpenCombo(i)}
                          className="font-bold underline-offset-2 hover:underline"
                          style={{ color: "var(--accent)" }}
                        >
                          {combo.cartas.join(" + ")}
                        </button>
                        {combo.velocidad && (
                          <span
                            className="font-head ml-2 text-[10px] font-bold uppercase"
                            style={{ color: combo.velocidad === "temprano" ? "var(--status-critical)" : "var(--status-warning)" }}
                          >
                            {combo.velocidad}
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {analisis.bracket.razones.length > 0 && (
                <ul className="mt-2 list-inside list-disc text-sm leading-relaxed" style={{ color: "var(--foreground)" }}>
                  {analisis.bracket.razones.map((razon, i) => (
                    <li key={i}>{razon}</li>
                  ))}
                </ul>
              )}
            </section>
          )}

          <section className="flex flex-col gap-6">
            <div>
              <SectionLabel>Estrategia</SectionLabel>
              <p className="text-[15px] leading-7" style={{ color: "var(--foreground)" }}>
                <HighlightedText text={analisis.estrategia_detectada} cardImages={cardImages} onHover={handleHover} />
              </p>
            </div>

            {analisis.puntos_fuertes.length > 0 && (
              <div>
                <SectionLabel color="var(--status-good)">Puntos fuertes</SectionLabel>
                <ul className="list-inside list-disc space-y-1.5 text-[15px] leading-7" style={{ color: "var(--foreground)" }}>
                  {analisis.puntos_fuertes.map((punto, i) => (
                    <li key={i}>
                      <HighlightedText text={punto} cardImages={cardImages} onHover={handleHover} />
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {sortedProblemas.length > 0 && (
              <div>
                <SectionLabel color="var(--status-critical)">Problemas detectados</SectionLabel>
                <div className="flex flex-col gap-px overflow-hidden rounded-sm border" style={{ borderColor: "var(--border)", background: "var(--border)" }}>
                  {sortedProblemas.map((problema, i) => (
                    <div key={i} className="p-4" style={{ background: "var(--surface)" }}>
                      <div className="mb-1.5 flex items-center gap-2">
                        <span
                          className="font-head flex-shrink-0 border px-1.5 py-0.5 text-[11px] font-extrabold uppercase"
                          style={{ color: SEVERITY_COLOR_VAR[problema.severidad], borderColor: SEVERITY_COLOR_VAR[problema.severidad] }}
                        >
                          {problema.severidad}
                        </span>
                        <strong className="text-sm" style={{ color: "var(--foreground)" }}>
                          {problema.categoria}
                        </strong>
                      </div>
                      <p className="text-[15px] leading-7" style={{ color: "var(--foreground)" }}>
                        <HighlightedText text={problema.explicacion} cardImages={cardImages} onHover={handleHover} />
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {swaps.length > 0 && (
              <div>
                <SectionLabel>Cambios sugeridos</SectionLabel>
                {analisis.presupuesto && (
                  <p
                    className="mb-3 text-sm"
                    style={{ color: analisis.presupuesto.supera_presupuesto ? "var(--status-warning)" : "var(--ink-secondary)" }}
                  >
                    Coste estimado de lo incluido:{" "}
                    <strong>{analisis.presupuesto.coste_estimado.toFixed(2)} €</strong> de{" "}
                    {analisis.presupuesto.presupuesto.toFixed(2)} € de presupuesto
                    {analisis.presupuesto.supera_presupuesto &&
                      ` — se pasa por ${analisis.presupuesto.diferencia.toFixed(2)} € para no dejar sin resolver los problemas más graves`}
                    .
                  </p>
                )}
                <div className="flex flex-col gap-px overflow-hidden rounded-sm border" style={{ borderColor: "var(--border)", background: "var(--border)" }}>
                  {swaps.map((group, i) => (
                    <SwapGroupCard
                      key={i}
                      group={group}
                      cardImages={cardImages}
                      onHover={handleHover}
                      onZoom={(name) => setZoomedCard(name)}
                    />
                  ))}
                </div>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
