"use client";

import { Fragment, useEffect, useState, type ReactNode } from "react";
import { AnalyzeResponse, CandidataSugerida, COLOR_LABELS, ROLE_LABELS, SimulationResult } from "../types";
import { InfoTooltip } from "./InfoTooltip";
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
  tooltip,
}: {
  label: ReactNode;
  value: string | number;
  /** Aviso rojo bajo el valor; `detail` hace de tooltip nativo al pasar el ratón. */
  warning?: { label: string; detail: string };
  /** Icono de información junto a la etiqueta, con la explicación del parámetro al hover. */
  tooltip?: ReactNode;
}) {
  return (
    <div className="rounded-sm border p-4" style={{ borderColor: "var(--border)", background: "var(--surface)" }}>
      <p className="flex items-center gap-1.5 font-head text-xs font-extrabold uppercase tracking-wide" style={{ color: "var(--ink-muted)" }}>
        {label}
        {tooltip && <InfoTooltip>{tooltip}</InfoTooltip>}
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

/** Miniatura clicable (zoom) de una carta candidata dentro de un problema. */
/** Miniatura de una candidata dentro de la galería de "ver candidatas": el
 * doble de tamaño que las de "cartas por rol" (mitad de columnas en la
 * misma rejilla), ya que aquí solo se muestran unas pocas por problema en
 * vez de todo el mazo. Sin texto de motivo/rol/precio — eso vive en el
 * modal de detalle al hacer clic. */
function CandidateThumbnail({
  candidata,
  imageUrl,
  onClick,
}: {
  candidata: CandidataSugerida;
  imageUrl: string | undefined;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!imageUrl}
      className="flex flex-col gap-1 text-left transition-transform enabled:hover:scale-[1.04] disabled:cursor-default"
    >
      <div
        className="overflow-hidden rounded-sm border"
        style={{ aspectRatio: "5/7", borderColor: "var(--border)", background: "var(--surface-muted)" }}
      >
        {imageUrl ? (
          // eslint-disable-next-line @next/next/no-img-element -- imagen externa de Scryfall
          <img src={imageUrl} alt={candidata.carta} className="h-full w-full object-cover" />
        ) : null}
      </div>
      <p className="truncate text-center text-[11px]" style={{ color: "var(--ink-secondary)" }} title={candidata.carta}>
        {candidata.carta}
      </p>
    </button>
  );
}

/** Detalle de una candidata: mismo formato que el modal de combos (zoom de
 * la carta + explicación), pero en un solo clic desde la galería en vez de
 * un modal anidado. */
function CandidateDetailModal({
  candidata,
  imageUrl,
  cardImages,
  onClose,
  onHover,
}: {
  candidata: CandidataSugerida;
  imageUrl: string | undefined;
  cardImages: Record<string, string>;
  onClose: () => void;
  onHover: HoverHandler;
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
      className="fixed inset-0 z-[70] flex cursor-pointer items-center justify-center p-6"
      style={{ background: "rgba(0,0,0,0.75)", opacity: visible ? 1 : 0, transition: "opacity 150ms ease" }}
      onClick={onClose}
    >
      <div
        className="flex max-h-full w-full max-w-sm flex-col items-center gap-4 overflow-y-auto"
        style={{ transform: visible ? "scale(1)" : "scale(0.92)", transition: "transform 150ms ease" }}
      >
        {imageUrl && (
          // eslint-disable-next-line @next/next/no-img-element -- imagen externa de Scryfall
          <img
            src={imageUrl}
            alt={candidata.carta}
            onClick={(e) => e.stopPropagation()}
            className="cursor-default rounded-md"
            style={{ width: 300, aspectRatio: "5/7", objectFit: "cover", boxShadow: "0 24px 60px rgba(0,0,0,0.6)" }}
          />
        )}
        <div
          className="w-full cursor-default rounded-sm border p-4"
          style={{ borderColor: "var(--border)", background: "var(--background)" }}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="mb-1.5 flex flex-wrap items-baseline gap-2">
            <strong className="text-sm" style={{ color: "var(--foreground)" }}>
              {candidata.carta}
            </strong>
            <span className="text-[11px]" style={{ color: "var(--ink-muted)" }}>
              {candidata.rol}
            </span>
            {typeof candidata.precio_eur === "number" && (
              <span className="font-mono text-[11px] font-bold" style={{ color: "var(--ink-secondary)" }}>
                {candidata.precio_eur.toFixed(2)} €
              </span>
            )}
          </div>
          <p className="text-sm leading-relaxed" style={{ color: "var(--foreground)" }}>
            <HighlightedText text={candidata.motivo} cardImages={cardImages} onHover={onHover} />
          </p>
        </div>
      </div>
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

function recordToBarData(record: Record<string, number>, scale: number = 1): BarDatum[] {
  return Object.entries(record)
    .sort((a, b) => Number(a[0]) - Number(b[0]))
    .map(([turn, value]) => ({ label: `T${turn}`, value: Math.round(value * scale * 100) / 100 }));
}

/** Estadísticas del goldfish Monte Carlo (ver analyzer.goldfish): siempre
 * bajo una política de juego simple y fija, nunca una partida real — el
 * aviso de arriba del modal deja eso claro para no venderlo como un
 * playtest de verdad. */
function SimulationModal({ simulation, onClose }: { simulation: SimulationResult; onClose: () => void }) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const colores = simulation.colores_disponibles_turno_4
    ? Object.entries(simulation.colores_disponibles_turno_4)
    : [];

  return (
    <div
      className="fixed inset-0 z-[60] flex cursor-pointer items-center justify-center p-6"
      style={{ background: "rgba(0,0,0,0.75)" }}
      onClick={onClose}
    >
      <div
        className="w-full max-w-6xl overflow-y-auto overflow-x-hidden rounded-sm border"
        style={{ borderColor: "var(--border)", background: "var(--background)", maxHeight: "90vh" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b p-4" style={{ borderColor: "var(--border)" }}>
          <h2 className="font-head text-sm font-extrabold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
            Estadísticas de simulación
          </h2>
          <button type="button" onClick={onClose} className="font-head text-xs font-bold" style={{ color: "var(--ink-muted)" }}>
            Cerrar ✕
          </button>
        </div>

        <div className="flex flex-col gap-4 p-4">
          <p className="text-xs leading-relaxed" style={{ color: "var(--ink-muted)" }}>
            {simulation.simulaciones.toLocaleString("es-ES")} partidas bajo una política de juego simple y fija
            (sin rivales, sin estrategia real): juega tierra y la carta más barata que pueda pagar, priorizando
            rampa. No es un playtest de verdad, es una señal de consistencia de maná y curva.
          </p>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            <StatTile
              label="Turno medio: comandante"
              value={simulation.turno_comandante_lanzable.media ?? "—"}
              tooltip="Turno en el que, de media, tienes suficiente maná y los colores del comandante ya en juego para poder lanzarlo, bajo la política de simulación simple."
            />
            <StatTile
              label="Nunca lo lanzas"
              value={`${Math.round(simulation.turno_comandante_lanzable.nunca_pct * 100)}%`}
              tooltip="Porcentaje de partidas simuladas en las que nunca llegas a tener maná y colores suficientes para el comandante dentro de los turnos simulados."
            />
            <StatTile
              label="Mana screw (T3)"
              value={`${Math.round(simulation.prob_mana_screw_turno_3 * 100)}%`}
              tooltip="Porcentaje de partidas con menos de 2 tierras en juego para el turno 3."
            />
            <StatTile
              label="Turno medio: primera rampa"
              value={simulation.primera_rampa.media ?? "—"}
              tooltip="Turno medio en el que resuelves la primera carta de rampa (no tierra) de tu mazo."
            />
            <StatTile
              label="Manos con mulligan"
              value={`${Math.round(simulation.prob_mulligan * 100)}%`}
              tooltip="Porcentaje de partidas en las que la mano inicial de 7 cartas tenía menos de 2 o más de 5 tierras y tuvo que repetirse."
            />
            {colores.map(([color, prob]) => (
              <StatTile
                key={color}
                label={
                  <span className="flex items-center gap-1.5">
                    Mana
                    <span className="text-sm">
                      <ManaIcon color={color} />
                    </span>
                    en T4
                  </span>
                }
                value={`${Math.round(prob * 100)}%`}
                tooltip={`Porcentaje de partidas en las que tienes al menos una fuente de ${COLOR_LABELS[color] ?? color} en juego para el turno 4.`}
              />
            ))}
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <SingleSeriesBarChart
              title="% de partidas con comandante lanzable, por turno"
              data={recordToBarData(simulation.turno_comandante_lanzable.por_turno, 100)}
              colorVar="var(--chart-mana)"
              valueLabel="%"
            />

            <SingleSeriesBarChart
              title="Maná medio disponible por turno"
              data={recordToBarData(simulation.curva_mana_media)}
              colorVar="var(--chart-mana)"
              valueLabel="maná"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export function ResultsView({
  result,
  simulation,
  simulationLoading,
  simulationError,
  onRunSimulation,
}: {
  result: AnalyzeResponse;
  simulation?: SimulationResult | null;
  simulationLoading?: boolean;
  simulationError?: string | null;
  onRunSimulation?: () => void;
}) {
  const [hoverTarget, setHoverTarget] = useState<HoverTarget | null>(null);
  const [expandedRole, setExpandedRole] = useState<string | null>(null);
  const [zoomedCard, setZoomedCard] = useState<string | null>(null);
  const [openCombo, setOpenCombo] = useState<number | null>(null);
  const [expandedProblema, setExpandedProblema] = useState<number | null>(null);
  const [openCandidate, setOpenCandidate] = useState<CandidataSugerida | null>(null);
  const [showSimulationModal, setShowSimulationModal] = useState(false);

  useEffect(() => {
    // Abre el modal en cuanto llega una simulación nueva (tras pulsar el
    // botón); no hay forma de "sincronizar con un sistema externo" más
    // limpia aquí, el resultado solo existe como prop desde page.tsx.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (simulation) setShowSimulationModal(true);
  }, [simulation]);
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
      {openCandidate && (
        <CandidateDetailModal
          candidata={openCandidate}
          imageUrl={cardImages[openCandidate.carta]}
          cardImages={cardImages}
          onClose={() => setOpenCandidate(null)}
          onHover={handleHover}
        />
      )}
      {showSimulationModal && simulation && (
        <SimulationModal simulation={simulation} onClose={() => setShowSimulationModal(false)} />
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
            <div className="flex flex-shrink-0 flex-col gap-2 lg:w-[220px]">
              <div className="flex gap-2">
                {result.comandantes.map((name) => (
                  <div
                    key={name}
                    className="w-full overflow-hidden rounded-xl border"
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
              {onRunSimulation && (
                <button
                  type="button"
                  onClick={onRunSimulation}
                  disabled={simulationLoading}
                  className="font-head mt-4 h-11 text-sm font-extrabold uppercase tracking-wide disabled:opacity-60"
                  style={{ background: "var(--accent)", color: "var(--accent-ink)" }}
                >
                  {simulationLoading ? "Simulando…" : "Probar simulación"}
                </button>
              )}
              {simulationError && (
                <p className="text-xs" style={{ color: "var(--status-critical)" }}>
                  {simulationError}
                </p>
              )}
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
                  {sortedProblemas.map((problema, i) => {
                    const candidatas = problema.candidatas_sugeridas ?? [];
                    const expanded = expandedProblema === i;
                    return (
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
                        {candidatas.length > 0 && (
                          <div className="mt-2">
                            <button
                              type="button"
                              onClick={() => setExpandedProblema(expanded ? null : i)}
                              className="font-head text-[11px] font-bold uppercase underline-offset-2 hover:underline"
                              style={{ color: "var(--accent)" }}
                            >
                              {expanded ? "Ocultar candidatas" : `Ver candidatas (${candidatas.length})`}
                            </button>
                            {expanded && (
                              <div
                                className="mt-2 grid grid-cols-2 gap-3 rounded-sm border p-3 sm:grid-cols-3 md:grid-cols-3 lg:grid-cols-5"
                                style={{ borderColor: "var(--border)", background: "var(--surface)" }}
                              >
                                {candidatas.map((candidata, j) => (
                                  <CandidateThumbnail
                                    key={j}
                                    candidata={candidata}
                                    imageUrl={cardImages[candidata.carta]}
                                    onClick={() => setOpenCandidate(candidata)}
                                  />
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
