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
const CONFIANZA_LABEL: Record<string, string> = { alta: "Alta", media: "Media", baja: "Baja" };
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

function StatTile({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-sm border p-4" style={{ borderColor: "var(--border)", background: "var(--surface)" }}>
      <p className="font-head text-xs font-extrabold uppercase tracking-wide" style={{ color: "var(--ink-muted)" }}>
        {label}
      </p>
      <p className="text-2xl font-bold font-mono" style={{ color: "var(--foreground)" }}>
        {value}
      </p>
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

function SwapGroupCard({
  group,
  cardImages,
  onHover,
}: {
  group: SwapGroup;
  cardImages: Record<string, string>;
  onHover: HoverHandler;
}) {
  return (
    <div className="flex flex-col gap-3 p-4 sm:flex-row" style={{ background: "var(--surface)" }}>
      {group.cut && (
        <div
          className="underline-card flex-shrink-0 text-center sm:w-[130px]"
          onMouseEnter={(e) => onHover(group.cut!.carta, e.currentTarget)}
          onMouseLeave={() => onHover(null, null)}
        >
          <div className="font-head text-[10px] font-extrabold uppercase" style={{ color: "var(--status-critical)" }}>
            Corta
          </div>
          <div className="text-sm font-bold" style={{ color: "var(--foreground)" }}>
            {group.cut.carta}
          </div>
        </div>
      )}
      {group.cut && group.additions.length > 0 && (
        <span className="hidden self-center text-lg sm:block" style={{ color: "var(--ink-muted)" }}>
          →
        </span>
      )}
      <div className="flex flex-1 flex-col gap-3">
        {group.additions.length === 0 && group.cut && (
          <p className="text-sm leading-relaxed" style={{ color: "var(--foreground)" }}>
            <HighlightedText text={group.cut.motivo} cardImages={cardImages} onHover={onHover} />
          </p>
        )}
        {group.additions.map((addition, i) => (
          <div key={i} className="flex flex-wrap items-start gap-4">
            <div
              className="underline-card flex-shrink-0 text-center"
              onMouseEnter={(e) => onHover(addition.carta, e.currentTarget)}
              onMouseLeave={() => onHover(null, null)}
            >
              <div className="font-head text-[10px] font-extrabold uppercase" style={{ color: "var(--status-good)" }}>
                Añade{group.additions.length > 1 ? ` (opción ${i + 1})` : ""}
              </div>
              <div className="max-w-[140px] text-sm font-bold" style={{ color: "var(--foreground)" }}>
                {addition.carta}
              </div>
              <div className="text-[11px]" style={{ color: "var(--ink-muted)" }}>
                {addition.rol}
              </div>
            </div>
            <p className="min-w-[200px] flex-1 text-sm leading-relaxed" style={{ color: "var(--foreground)" }}>
              <HighlightedText text={addition.motivo} cardImages={cardImages} onHover={onHover} />
            </p>
          </div>
        ))}
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
      className="fixed inset-0 z-[60] flex items-center justify-center p-6"
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

export function ResultsView({ result }: { result: AnalyzeResponse }) {
  const [hoverTarget, setHoverTarget] = useState<HoverTarget | null>(null);
  const [expandedRole, setExpandedRole] = useState<string | null>(null);
  const [zoomedCard, setZoomedCard] = useState<string | null>(null);
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
      <FloatingCardPreview target={hoverTarget} cardImages={cardImages} />
      {zoomedCard && cardImages[zoomedCard] && (
        <CardZoomModal name={zoomedCard} imageUrl={cardImages[zoomedCard]} onClose={() => setZoomedCard(null)} />
      )}

      <section className="flex flex-col gap-5 border-b pb-6 lg:flex-row lg:items-start" style={{ borderColor: "var(--border)" }}>
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
          <div>
            <h2 className="font-head text-2xl font-extrabold" style={{ color: "var(--foreground)" }}>
              {result.comandantes.length > 0 ? result.comandantes.join(" + ") : "Sin comandante detectado"}
            </h2>
            {analisis?.bracket && (
              <p className="font-head mt-1 text-xs font-bold uppercase tracking-wide" style={{ color: "var(--ink-muted)" }}>
                Bracket deducido {analisis.bracket.deducido} · {analisis.arquetipo}
              </p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <StatTile label="Tamaño del deck" value={result.tamano_deck} />
            <StatTile label="Tierras" value={result.tierras} />
            <StatTile label="CMC medio" value={result.cmc_medio.toFixed(2)} />
            <StatTile label="Cartas no encontradas" value={result.no_encontradas.length} />
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

      {(result.no_encontradas.length > 0 || result.no_legales.length > 0) && (
        <section
          className="rounded-sm border p-4"
          style={{ borderColor: "var(--status-critical)", background: "var(--surface)" }}
        >
          {result.no_encontradas.length > 0 && (
            <p style={{ color: "var(--foreground)" }}>
              <strong>No encontradas:</strong> {result.no_encontradas.join(", ")}
            </p>
          )}
          {result.no_legales.length > 0 && (
            <p style={{ color: "var(--foreground)" }}>
              <strong>No legales en Commander:</strong> {result.no_legales.join(", ")}
            </p>
          )}
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
              <SectionLabel>Bracket deducido</SectionLabel>
              <div className="flex flex-wrap items-baseline gap-3">
                <span className="font-head text-3xl font-extrabold" style={{ color: "var(--foreground)" }}>
                  {analisis.bracket.deducido}
                </span>
                <span className="text-sm" style={{ color: "var(--ink-secondary)" }}>
                  confianza {CONFIANZA_LABEL[analisis.bracket.confianza] ?? analisis.bracket.confianza} · suelo{" "}
                  {analisis.bracket.suelo} · estimación de juego {analisis.bracket.estimacion_juego}
                </span>
              </div>
              {analisis.bracket.game_changers.length > 0 && (
                <p className="mt-2 text-sm" style={{ color: "var(--foreground)" }}>
                  <strong>Game Changers:</strong> {analisis.bracket.game_changers.join(", ")}
                </p>
              )}
              {analisis.bracket.razones.length > 0 && (
                <ul className="mt-2 list-inside list-disc text-sm leading-relaxed" style={{ color: "var(--foreground)" }}>
                  {analisis.bracket.razones.map((razon, i) => (
                    <li key={i}>{razon}</li>
                  ))}
                </ul>
              )}
              {(analisis.bracket.que_lo_moveria.subir.length > 0 ||
                analisis.bracket.que_lo_moveria.bajar.length > 0) && (
                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  {analisis.bracket.que_lo_moveria.bajar.length > 0 && (
                    <div>
                      <p className="text-xs font-bold uppercase" style={{ color: "var(--status-critical)" }}>
                        Lo bajaría
                      </p>
                      <ul className="list-inside list-disc text-sm leading-relaxed" style={{ color: "var(--foreground)" }}>
                        {analisis.bracket.que_lo_moveria.bajar.map((item, i) => (
                          <li key={i}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {analisis.bracket.que_lo_moveria.subir.length > 0 && (
                    <div>
                      <p className="text-xs font-bold uppercase" style={{ color: "var(--status-good)" }}>
                        Lo subiría
                      </p>
                      <ul className="list-inside list-disc text-sm leading-relaxed" style={{ color: "var(--foreground)" }}>
                        {analisis.bracket.que_lo_moveria.subir.map((item, i) => (
                          <li key={i}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
              {analisis.bracket.diferencia_con_objetivo && (
                <p className="mt-3 text-sm" style={{ color: "var(--foreground)" }}>
                  <strong>Frente a tu objetivo ({analisis.bracket.objetivo_usuario}):</strong>{" "}
                  {analisis.bracket.diferencia_con_objetivo}
                </p>
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
                <div className="flex flex-col gap-px overflow-hidden rounded-sm border" style={{ borderColor: "var(--border)", background: "var(--border)" }}>
                  {swaps.map((group, i) => (
                    <SwapGroupCard key={i} group={group} cardImages={cardImages} onHover={handleHover} />
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
