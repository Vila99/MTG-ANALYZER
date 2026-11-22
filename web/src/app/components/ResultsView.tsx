"use client";

import { Fragment, useState } from "react";
import {
  AñadidoSugerido,
  AnalyzeResponse,
  COLOR_LABELS,
  CorteSugerido,
  ROLE_LABELS,
} from "../types";
import { SingleSeriesBarChart } from "./SingleSeriesBarChart";

const RUBRIC_ORDER = ["land", "ramp", "draw", "removal", "wipe"];
const STATUS_LABEL: Record<string, string> = { bajo: "Bajo", ok: "Dentro de rango", alto: "Alto" };
const STATUS_COLOR_VAR: Record<string, string> = {
  bajo: "var(--status-warning)",
  ok: "var(--status-good)",
  alto: "var(--status-critical)",
};
const CONFIANZA_LABEL: Record<string, string> = { alta: "Alta", media: "Media", baja: "Baja" };

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
 * el cursor por encima, avisa a `onHover` para que el panel de vista previa
 * muestre la imagen real de Scryfall. */
function HighlightedText({
  text,
  cardImages,
  onHover,
}: {
  text: string;
  cardImages: Record<string, string>;
  onHover: (name: string | null) => void;
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
            onMouseEnter={() => onHover(part)}
            onMouseLeave={() => onHover(null)}
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

function CardPreviewPanel({
  hoveredCard,
  cardImages,
}: {
  hoveredCard: string | null;
  cardImages: Record<string, string>;
}) {
  const imageUrl = hoveredCard ? cardImages[hoveredCard] : undefined;
  return (
    <div
      className="sticky top-4 flex flex-col gap-2 rounded-sm border p-4"
      style={{ borderColor: "var(--border)", background: "var(--surface)", boxShadow: "0 8px 20px rgba(0,0,0,0.12)" }}
    >
      <SectionLabel color="var(--ink-muted)">Vista previa</SectionLabel>
      <div
        className="flex w-full items-center justify-center overflow-hidden rounded-sm border"
        style={{ aspectRatio: "5/7", borderColor: "var(--border)", background: "var(--surface-muted)" }}
      >
        {imageUrl ? (
          // eslint-disable-next-line @next/next/no-img-element -- imagen externa de Scryfall, sin dominio fijo
          <img src={imageUrl} alt={hoveredCard ?? ""} className="h-full w-full object-cover" />
        ) : (
          <span className="px-3 text-center text-xs" style={{ color: "var(--ink-muted)" }}>
            Pasa el cursor sobre una carta subrayada
          </span>
        )}
      </div>
      <p className="text-sm font-semibold" style={{ color: "var(--foreground)" }}>
        {hoveredCard ?? ""}
      </p>
    </div>
  );
}

interface SwapPair {
  cut?: CorteSugerido;
  addition?: AñadidoSugerido;
}

/** Empareja cada añadido con el corte al que sustituye (por `reemplaza_a`),
 * para mostrar "Corta X -> Añade Y" en vez de dos listas sueltas. Los
 * cortes y añadidos sin pareja se muestran solos. */
function pairCutsAndAdditions(cuts: CorteSugerido[], additions: AñadidoSugerido[]): SwapPair[] {
  const usedCutNames = new Set<string>();
  const pairs: SwapPair[] = [];

  for (const addition of additions) {
    const matchingCut = addition.reemplaza_a
      ? cuts.find((cut) => cut.carta === addition.reemplaza_a && !usedCutNames.has(cut.carta))
      : undefined;
    if (matchingCut) {
      usedCutNames.add(matchingCut.carta);
      pairs.push({ cut: matchingCut, addition });
    } else {
      pairs.push({ addition });
    }
  }
  for (const cut of cuts) {
    if (!usedCutNames.has(cut.carta)) {
      pairs.push({ cut });
    }
  }
  return pairs;
}

function SwapCard({
  pair,
  onHover,
}: {
  pair: SwapPair;
  onHover: (name: string | null) => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-4 p-4" style={{ background: "var(--surface)" }}>
      {pair.cut && (
        <div
          className="underline-card flex-shrink-0 text-center"
          onMouseEnter={() => onHover(pair.cut!.carta)}
          onMouseLeave={() => onHover(null)}
        >
          <div className="font-head text-[10px] font-extrabold uppercase" style={{ color: "var(--status-critical)" }}>
            Corta
          </div>
          <div className="max-w-[140px] text-sm font-bold" style={{ color: "var(--foreground)" }}>
            {pair.cut.carta}
          </div>
        </div>
      )}
      {pair.cut && pair.addition && (
        <span className="text-lg" style={{ color: "var(--ink-muted)" }}>
          →
        </span>
      )}
      {pair.addition && (
        <div
          className="underline-card flex-shrink-0 text-center"
          onMouseEnter={() => onHover(pair.addition!.carta)}
          onMouseLeave={() => onHover(null)}
        >
          <div className="font-head text-[10px] font-extrabold uppercase" style={{ color: "var(--status-good)" }}>
            Añade
          </div>
          <div className="max-w-[140px] text-sm font-bold" style={{ color: "var(--foreground)" }}>
            {pair.addition.carta}
          </div>
          <div className="text-[11px]" style={{ color: "var(--ink-muted)" }}>
            {pair.addition.rol}
          </div>
        </div>
      )}
      <p className="min-w-[220px] flex-1 text-sm" style={{ color: "var(--foreground)" }}>
        {pair.addition?.motivo ?? pair.cut?.motivo}
      </p>
    </div>
  );
}

export function ResultsView({ result }: { result: AnalyzeResponse }) {
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);
  const cardImages = result.card_images ?? {};

  const manaCurveData = Object.entries(result.curva_mana)
    .sort((a, b) => Number(a[0]) - Number(b[0]))
    .map(([cmc, count]) => ({ label: cmc, value: count }));

  const rolesData = Object.entries(result.roles)
    .filter(([role]) => role !== "other")
    .map(([role, count]) => ({ label: ROLE_LABELS[role] ?? role, value: count }));

  const analisis = result.analisis;
  const swaps = analisis ? pairCutsAndAdditions(analisis.cortes_sugeridos, analisis.anadidos_sugeridos) : [];

  return (
    <div className="flex flex-col gap-7">
      <section className="flex flex-wrap items-center gap-3 border-b pb-5" style={{ borderColor: "var(--border)" }}>
        <h2 className="font-head text-2xl font-extrabold" style={{ color: "var(--foreground)" }}>
          {result.comandantes.length > 0 ? result.comandantes.join(" + ") : "Sin comandante detectado"}
        </h2>
        {analisis?.bracket && (
          <span
            className="font-head text-xs font-bold uppercase tracking-wide"
            style={{ color: "var(--ink-muted)" }}
          >
            Bracket deducido {analisis.bracket.deducido} · {analisis.arquetipo}
          </span>
        )}
      </section>

      <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatTile label="Tamaño del deck" value={result.tamano_deck} />
        <StatTile label="Tierras" value={result.tierras} />
        <StatTile label="CMC medio" value={result.cmc_medio.toFixed(2)} />
        <StatTile label="Cartas no encontradas" value={result.no_encontradas.length} />
      </section>

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

      <section className="grid gap-4 sm:grid-cols-2">
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
        />
      </section>

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
                    {label}
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
                <span className="text-sm" style={{ color: "var(--ink-muted)" }}>
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
                <ul className="mt-2 list-inside list-disc text-sm" style={{ color: "var(--ink-secondary)" }}>
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
                      <ul className="list-inside list-disc text-sm" style={{ color: "var(--ink-secondary)" }}>
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
                      <ul className="list-inside list-disc text-sm" style={{ color: "var(--ink-secondary)" }}>
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

          <section className="grid gap-5 lg:grid-cols-[1fr_280px]">
            <div className="flex flex-col gap-5">
              <div>
                <SectionLabel>Estrategia</SectionLabel>
                <p className="text-[15px] leading-relaxed" style={{ color: "var(--foreground)" }}>
                  <HighlightedText text={analisis.estrategia_detectada} cardImages={cardImages} onHover={setHoveredCard} />
                </p>
              </div>

              {analisis.puntos_fuertes.length > 0 && (
                <div>
                  <SectionLabel color="var(--status-good)">Puntos fuertes</SectionLabel>
                  <ul className="list-inside list-disc text-sm" style={{ color: "var(--foreground)" }}>
                    {analisis.puntos_fuertes.map((punto, i) => (
                      <li key={i}>
                        <HighlightedText text={punto} cardImages={cardImages} onHover={setHoveredCard} />
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {analisis.problemas.length > 0 && (
                <div>
                  <SectionLabel color="var(--status-critical)">Problemas detectados</SectionLabel>
                  <div className="flex flex-col gap-2">
                    {analisis.problemas.map((problema, i) => (
                      <div key={i} className="flex items-baseline gap-2">
                        <span
                          className="font-head flex-shrink-0 border px-1.5 py-0.5 text-[11px] font-extrabold uppercase"
                          style={{
                            color:
                              problema.severidad === "alta"
                                ? "var(--status-critical)"
                                : problema.severidad === "media"
                                  ? "var(--status-warning)"
                                  : "var(--ink-muted)",
                            borderColor:
                              problema.severidad === "alta"
                                ? "var(--status-critical)"
                                : problema.severidad === "media"
                                  ? "var(--status-warning)"
                                  : "var(--border)",
                          }}
                        >
                          {problema.severidad}
                        </span>
                        <p className="text-sm" style={{ color: "var(--foreground)" }}>
                          <strong>{problema.categoria}:</strong>{" "}
                          <HighlightedText text={problema.explicacion} cardImages={cardImages} onHover={setHoveredCard} />
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
                    {swaps.map((pair, i) => (
                      <SwapCard key={i} pair={pair} onHover={setHoveredCard} />
                    ))}
                  </div>
                </div>
              )}
            </div>

            <CardPreviewPanel hoveredCard={hoveredCard} cardImages={cardImages} />
          </section>
        </>
      )}
    </div>
  );
}
