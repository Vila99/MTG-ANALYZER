"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import { InfoTooltip } from "./InfoTooltip";
import { ManaIcon } from "./ManaIcon";
import { ResultsView } from "./ResultsView";
import {
  formatRelativeTime,
  loadRecentAnalyses,
  removeRecentAnalysis,
  saveRecentAnalysis,
  type RecentEntry,
} from "../lib/recentAnalyses";
import {
  buildSampleExport,
  downloadSample,
  formatSampleDate,
  loadSample,
  loadSampleIndex,
  type SampleAnalysis,
  type SampleIndexEntry,
} from "../lib/sampleAnalyses";
import { AnalyzeRequest, AnalyzeResponse, SimulateRequest, SimulationResult } from "../types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const LOADING_MESSAGES = [
  "Resolviendo cartas contra la base de datos de Scryfall…",
  "Clasificando cada carta por su rol (reglas + Haiku)…",
  "Analizando la estrategia con Claude (Sonnet)…",
];

function fieldStyle() {
  return {
    borderColor: "var(--border)",
    background: "var(--surface)",
    color: "var(--foreground)",
  } as const;
}

function RecentAnalysesModal({
  recent,
  onSelect,
  onRemove,
  onClose,
}: {
  recent: RecentEntry[];
  onSelect: (entry: RecentEntry) => void;
  onRemove: (id: string) => void;
  onClose: () => void;
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
      className="fixed inset-0 z-[60] flex cursor-pointer items-start justify-center overflow-y-auto p-6 sm:items-center"
      style={{ background: "rgba(0,0,0,0.75)" }}
      onClick={onClose}
    >
      <div
        className="w-full max-w-xl rounded-sm border"
        style={{ borderColor: "var(--border)", background: "var(--background)" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b p-4" style={{ borderColor: "var(--border)" }}>
          <h2 className="font-head text-sm font-extrabold uppercase tracking-wide" style={{ color: "var(--foreground)" }}>
            Últimos decks analizados
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="font-head text-xs font-bold"
            style={{ color: "var(--ink-muted)" }}
          >
            Cerrar ✕
          </button>
        </div>

        {recent.length === 0 ? (
          <p className="p-4 text-sm" style={{ color: "var(--ink-muted)" }}>
            Todavía no has analizado ningún deck.
          </p>
        ) : (
          <div className="flex flex-col gap-px" style={{ background: "var(--border)" }}>
            {recent.map((entry) => (
              <div key={entry.id} className="flex items-center justify-between gap-3 p-3" style={{ background: "var(--surface)" }}>
                <button
                  type="button"
                  onClick={() => {
                    onSelect(entry);
                    onClose();
                  }}
                  className="flex min-w-0 flex-1 flex-wrap items-baseline gap-x-3 text-left"
                >
                  <span className="font-head truncate text-sm font-bold" style={{ color: "var(--foreground)" }}>
                    {entry.commander}
                  </span>
                  <span className="text-xs" style={{ color: "var(--ink-muted)" }}>
                    {entry.deckSize} cartas · {formatRelativeTime(entry.timestamp)}
                  </span>
                </button>
                <button
                  type="button"
                  onClick={() => onRemove(entry.id)}
                  aria-label={`Eliminar análisis de ${entry.commander} de la lista`}
                  className="font-head flex-shrink-0 text-xs font-bold"
                  style={{ color: "var(--ink-muted)" }}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function SampleAnalysesModal({
  onSelect,
  onClose,
}: {
  onSelect: (entry: SampleIndexEntry) => void;
  onClose: () => void;
}) {
  const [samples, setSamples] = useState<SampleIndexEntry[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    loadSampleIndex()
      .then((entries) => {
        if (!cancelled) setSamples(entries);
      })
      .catch((err) => {
        if (!cancelled) setLoadError(err instanceof Error ? err.message : "No se pudieron cargar los ejemplos.");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-[60] flex cursor-pointer items-start justify-center overflow-y-auto p-6 sm:items-center"
      style={{ background: "rgba(0,0,0,0.75)" }}
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Análisis de ejemplo"
        className="w-full max-w-xl cursor-default rounded-sm border"
        style={{ borderColor: "var(--border)", background: "var(--background)" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b p-4" style={{ borderColor: "var(--border)" }}>
          <h2 className="font-head text-sm font-extrabold uppercase tracking-wide" style={{ color: "var(--foreground)" }}>
            Análisis de ejemplo
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="font-head text-xs font-bold"
            style={{ color: "var(--ink-muted)" }}
          >
            Cerrar ✕
          </button>
        </div>

        {loadError ? (
          <p className="p-4 text-sm" style={{ color: "var(--status-critical)" }}>
            {loadError}
          </p>
        ) : samples === null ? (
          <p className="p-4 text-sm" style={{ color: "var(--ink-muted)" }}>
            Cargando ejemplos…
          </p>
        ) : samples.length === 0 ? (
          <p className="p-4 text-sm" style={{ color: "var(--ink-muted)" }}>
            Todavía no hay ningún análisis de ejemplo publicado.
          </p>
        ) : (
          <div className="flex flex-col gap-px" style={{ background: "var(--border)" }}>
            {samples.map((entry) => (
              <button
                key={entry.id}
                type="button"
                onClick={() => {
                  onSelect(entry);
                  onClose();
                }}
                className="flex flex-col gap-0.5 p-3 text-left"
                style={{ background: "var(--surface)" }}
              >
                <span className="flex flex-wrap items-baseline gap-x-3">
                  <span className="font-head text-sm font-bold" style={{ color: "var(--foreground)" }}>
                    {entry.title}
                  </span>
                  <span className="text-xs" style={{ color: "var(--ink-muted)" }}>
                    {entry.ai ? "Con análisis de Claude" : "Solo métricas"}
                  </span>
                </span>
                {entry.description && (
                  <span className="text-xs" style={{ color: "var(--ink-muted)" }}>
                    {entry.description}
                  </span>
                )}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/** El analizador completo (formulario, carga y resultados).
 *
 * `initialSampleId` (ruta `/analizar/ejemplo/[id]`) abre directamente ese
 * análisis de ejemplo: el componente arranca ya en estado "cargando ejemplo",
 * así que ni el HTML del servidor ni el primer pintado muestran el
 * formulario antes de que llegue el resultado.
 *
 * `sampleLoadingPlaceholder` pinta ese mismo estado "cargando ejemplo" sin
 * cargar nada: es el fallback de Suspense de esa ruta mientras se resuelve
 * el `id`, así el paso del fallback al componente real no se nota. */
export function AnalyzerApp({
  initialSampleId,
  sampleLoadingPlaceholder = false,
}: { initialSampleId?: string; sampleLoadingPlaceholder?: boolean } = {}) {
  const router = useRouter();
  const moxfieldUrlId = useId();
  const descriptionId = useId();
  const budgetId = useId();
  const styleId = useId();
  const avoidId = useId();
  const aiId = useId();

  const [moxfieldUrl, setMoxfieldUrl] = useState("");
  const [description, setDescription] = useState("");
  const [budgetMode, setBudgetMode] = useState<"ajustado" | "libre">("libre");
  const [style, setStyle] = useState<AnalyzeRequest["style"]>("casual");
  const [allowCombos, setAllowCombos] = useState(false);
  const [avoid, setAvoid] = useState("");
  const [ai, setAi] = useState(false);

  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [recent, setRecent] = useState<RecentEntry[]>([]);
  const [showRecentModal, setShowRecentModal] = useState(false);
  const [showSamplesModal, setShowSamplesModal] = useState(false);
  const [activeSample, setActiveSample] = useState<SampleAnalysis | null>(null);
  const [sampleLoading, setSampleLoading] = useState(Boolean(initialSampleId) || sampleLoadingPlaceholder);
  const [simulation, setSimulation] = useState<SimulationResult | null>(null);
  const [simulationLoading, setSimulationLoading] = useState(false);
  const [simulationError, setSimulationError] = useState<string | null>(null);

  const stepIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    // localStorage solo existe en el cliente: se lee tras el montaje para no
    // desincronizar el HTML del servidor con el del navegador.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setRecent(loadRecentAnalyses());
  }, []);

  useEffect(() => {
    if (!initialSampleId) return;
    let cancelled = false;
    loadSampleIndex()
      .then(async (entries) => {
        const entry = entries.find((item) => item.id === initialSampleId);
        if (!entry) throw new Error(`No existe el análisis de ejemplo «${initialSampleId}».`);
        const sample = await loadSample(entry);
        if (cancelled) return;
        setActiveSample(sample);
        setResult(sample.result);
        setMoxfieldUrl(sample.request.moxfieldUrl);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "No se pudo cargar el ejemplo.");
      })
      .finally(() => {
        if (!cancelled) setSampleLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [initialSampleId]);

  useEffect(() => {
    if (!loading) {
      return;
    }
    stepIntervalRef.current = setInterval(() => {
      setLoadingStep((step) => Math.min(step + 1, LOADING_MESSAGES.length - 1));
    }, 1600);
    return () => {
      if (stepIntervalRef.current) {
        clearInterval(stepIntervalRef.current);
        stepIntervalRef.current = null;
      }
    };
  }, [loading]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoadingStep(0);
    setLoading(true);
    setError(null);

    const body: AnalyzeRequest = {
      moxfield_url: moxfieldUrl.trim() || undefined,
      description: description.trim() || undefined,
      budget_mode: budgetMode,
      style,
      allow_combos: allowCombos,
      avoid: avoid
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
      ai,
    };

    try {
      const response = await fetch(`${API_URL}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail ?? `Error ${response.status} al analizar el deck.`);
      }

      const data: AnalyzeResponse = await response.json();
      setResult(data);
      setActiveSample(null);
      setRecent(saveRecentAnalysis(data, { moxfieldUrl: moxfieldUrl.trim() }));
      setSimulation(null);
      setSimulationError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido al analizar el deck.");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  async function handleRunSimulation() {
    if (activeSample?.simulation) {
      // Ejemplo: la simulación viene guardada; copia nueva para que
      // ResultsView vuelva a abrir el modal aunque ya se hubiera mostrado.
      setSimulation({ ...activeSample.simulation });
      return;
    }

    setSimulationLoading(true);
    setSimulationError(null);

    const body: SimulateRequest = {
      moxfield_url: moxfieldUrl.trim() || undefined,
      n_sims: 10000,
    };

    try {
      const response = await fetch(`${API_URL}/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail ?? `Error ${response.status} al simular el deck.`);
      }

      const data: SimulationResult = await response.json();
      setSimulation(data);
    } catch (err) {
      setSimulationError(err instanceof Error ? err.message : "Error desconocido al simular el deck.");
    } finally {
      setSimulationLoading(false);
    }
  }

  async function handleSelectSample(entry: SampleIndexEntry) {
    setError(null);
    try {
      const sample = await loadSample(entry);
      setActiveSample(sample);
      setResult(sample.result);
      setMoxfieldUrl(sample.request.moxfieldUrl);
      setSimulation(null);
      setSimulationError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cargar el ejemplo.");
    }
  }

  function handleExportSample() {
    if (!result) return;
    downloadSample(buildSampleExport(result, simulation, moxfieldUrl.trim()));
  }

  function handleReset() {
    if (initialSampleId) {
      // Desde /analizar/ejemplo/<id>, "Nuevo análisis" vuelve al analizador
      // normal en vez de dejar el formulario bajo la URL del ejemplo.
      router.push("/analizar");
      return;
    }
    setActiveSample(null);
    setResult(null);
    setError(null);
    setSimulation(null);
    setSimulationError(null);
  }

  return (
    <main className="mx-auto flex w-full max-w-[1400px] flex-col gap-7 px-5 py-8 sm:px-10">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b pb-5" style={{ borderColor: "var(--border)" }}>
        {result ? (
          <button
            type="button"
            onClick={handleReset}
            aria-label="Nuevo análisis"
            title="Nuevo análisis"
            className="flex items-center justify-center rounded-sm border p-2"
            style={{ borderColor: "var(--border)", color: "var(--foreground)" }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M19 12H5M11 18l-6-6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        ) : (
          <>
            <h1 className="font-head text-sm font-extrabold uppercase tracking-wide">
              <Link href="/" style={{ color: "var(--foreground)", textDecoration: "none" }}>
                MTG Deck Analyzer
              </Link>
            </h1>
            <span className="flex items-center gap-1.5 text-base" aria-hidden="true">
              {/* eslint-disable-next-line @next/next/no-img-element -- icono estatico en public/, sin optimizar */}
              <img src="/mana-colorless.svg" alt="" aria-hidden="true" className="h-5 w-5" />
              {["W", "U", "B", "R", "G"].map((color) => (
                <ManaIcon key={color} color={color} />
              ))}
            </span>
          </>
        )}
      </header>

      {sampleLoading && (
        <div className="mx-auto w-full max-w-xl py-16" role="status">
          <h2 className="font-head mb-6 text-xl font-extrabold" style={{ color: "var(--foreground)" }}>
            Cargando el análisis de ejemplo…
          </h2>
          <div className="relative h-[3px] overflow-hidden" style={{ background: "var(--border)" }}>
            <div
              className="absolute top-0 left-0 h-full w-[30%] animate-[sweep_1.1s_ease-in-out_infinite]"
              style={{ background: "var(--accent)" }}
            />
          </div>
        </div>
      )}

      {!result && !loading && !sampleLoading && (
        <>
        <form onSubmit={handleSubmit} aria-labelledby="analyze-form-heading" className="flex flex-wrap gap-6">
          <h2 id="analyze-form-heading" className="sr-only">
            Formulario de análisis de deck
          </h2>

          <div className="flex min-w-0 flex-[999_1_560px] flex-col gap-5">
            <div className="flex flex-col gap-1">
              <label htmlFor={moxfieldUrlId} className="font-head text-xs font-bold uppercase tracking-wide" style={{ color: "var(--foreground)" }}>
                URL de Moxfield
              </label>
              <input
                id={moxfieldUrlId}
                name="moxfield_url"
                type="text"
                required
                placeholder="https://www.moxfield.com/decks/..."
                value={moxfieldUrl}
                onChange={(e) => setMoxfieldUrl(e.target.value)}
                className="h-11 rounded-sm border px-3.5 text-[15px]"
                style={fieldStyle()}
              />
              <p className="text-xs" style={{ color: "var(--ink-muted)" }}>
                Pega la URL de un deck público de Moxfield.
              </p>
            </div>

            <div className="flex flex-col gap-1">
              <label htmlFor={descriptionId} className="font-head text-xs font-bold uppercase tracking-wide" style={{ color: "var(--foreground)" }}>
                Tu idea para el deck (opcional)
              </label>
              <textarea
                id={descriptionId}
                name="description"
                rows={3}
                placeholder="Ej.: quiero ir a lo ancho con tokens y encantamientos, sin depender del comandante en mesa."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="resize-y rounded-sm border p-3 text-sm"
                style={fieldStyle()}
              />
              <p className="text-xs" style={{ color: "var(--ink-muted)" }}>
                Cuéntale a Claude qué querías construir, en tus palabras — le da contexto antes de analizar las cartas.
              </p>
            </div>
          </div>

          <div className="flex h-fit min-w-[280px] max-w-[360px] flex-1 flex-col gap-3">
          <fieldset
            className="flex flex-col gap-4 rounded-sm border p-5"
            style={{ borderColor: "var(--border)", background: "var(--surface)" }}
          >
            <legend className="font-head border-b px-1 pb-3 text-xs font-extrabold uppercase tracking-wide" style={{ borderColor: "var(--border)", color: "var(--foreground)" }}>
              Parámetros
            </legend>

            <div className="grid grid-cols-1 gap-3">
              <div className="flex flex-col gap-1">
                <label htmlFor={budgetId} className="flex items-center gap-1.5 text-xs font-bold" style={{ color: "var(--foreground)" }}>
                  Presupuesto
                  <InfoTooltip>
                    <p>
                      <strong>Ajustado:</strong> entre varias cartas igual de válidas para un mismo problema,
                      prioriza las más baratas. No es un tope fijo en €.
                    </p>
                    <p className="mt-2">
                      <strong>Libre:</strong> sin esa preferencia — recomienda la que mejor encaje, sea barata
                      o cara.
                    </p>
                  </InfoTooltip>
                </label>
                <select
                  id={budgetId}
                  name="budget_mode"
                  value={budgetMode}
                  onChange={(e) => setBudgetMode(e.target.value as "ajustado" | "libre")}
                  className="h-9 rounded-sm border px-2.5"
                  style={fieldStyle()}
                >
                  <option value="libre">Libre</option>
                  <option value="ajustado">Ajustado</option>
                </select>
              </div>
            </div>

            <div className="flex flex-col gap-1">
              <label htmlFor={styleId} className="flex items-center gap-1.5 text-xs font-bold" style={{ color: "var(--foreground)" }}>
                Estilo
                <InfoTooltip>
                  <p>
                    <strong>Casual:</strong> prioriza la diversión de mesa, evita subir el bracket o sugerir
                    cartas opresivas.
                  </p>
                  <p className="mt-2">
                    <strong>Focused:</strong> optimiza dentro del bracket que ya tiene el deck (consistencia,
                    curva, sinergia).
                  </p>
                  <p className="mt-2">
                    <strong>cEDH:</strong> prioriza velocidad, interacción barata y el camino a la victoria
                    por encima de todo, aunque suba el bracket.
                  </p>
                </InfoTooltip>
              </label>
              <select
                id={styleId}
                name="style"
                value={style}
                onChange={(e) => setStyle(e.target.value as AnalyzeRequest["style"])}
                className="h-9 rounded-sm border px-2.5"
                style={fieldStyle()}
              >
                <option value="casual">Casual</option>
                <option value="focused">Focused</option>
                <option value="cedh">cEDH</option>
              </select>
            </div>

            <div className="flex flex-col gap-1">
              <label htmlFor={avoidId} className="text-xs font-bold" style={{ color: "var(--foreground)" }}>
                Evitar (cartas o mecánicas)
              </label>
              <input
                id={avoidId}
                name="avoid"
                type="text"
                value={avoid}
                onChange={(e) => setAvoid(e.target.value)}
                className="h-9 rounded-sm border px-2.5"
                style={fieldStyle()}
              />
            </div>

            <label className="flex items-start gap-2 text-sm">
              <input
                type="checkbox"
                className="mt-0.5"
                checked={allowCombos}
                onChange={(e) => setAllowCombos(e.target.checked)}
              />
              <span style={{ color: "var(--foreground)" }}>
                Permitir sugerir combos nuevos
                <span className="mt-0.5 block text-xs font-normal" style={{ color: "var(--ink-muted)" }}>
                  No afecta a los combos que ya tengas en la lista pegada — solo controla si Claude te propone alguno más.
                </span>
              </span>
            </label>

            <label className="flex items-center gap-2 text-sm font-bold">
              <input id={aiId} name="ai" type="checkbox" checked={ai} onChange={(e) => setAi(e.target.checked)} />
              <span style={{ color: "var(--foreground)" }}>Pedir análisis de Claude</span>
            </label>

            <button
              type="submit"
              className="font-head mt-auto h-11 text-sm font-extrabold uppercase tracking-wide"
              style={{ background: "var(--accent)", color: "var(--accent-ink)" }}
            >
              Analizar deck
            </button>
          </fieldset>

          <button
            type="button"
            onClick={() => setShowRecentModal(true)}
            className="font-head h-11 rounded-sm border text-[10px] font-bold uppercase"
            style={{ borderColor: "var(--border)", color: "var(--foreground)" }}
          >
            Últimos decks analizados
          </button>

          <button
            type="button"
            onClick={() => setShowSamplesModal(true)}
            className="font-head h-11 rounded-sm border text-[10px] font-bold uppercase"
            style={{ borderColor: "var(--border)", color: "var(--foreground)" }}
          >
            Ver análisis de ejemplo
          </button>
          </div>
        </form>

        {showRecentModal && (
          <RecentAnalysesModal
            recent={recent}
            onSelect={(entry) => {
              setActiveSample(null);
              setResult(entry.result);
              setMoxfieldUrl(entry.request?.moxfieldUrl ?? "");
              setSimulation(null);
              setSimulationError(null);
            }}
            onRemove={(id) => setRecent(removeRecentAnalysis(id))}
            onClose={() => setShowRecentModal(false)}
          />
        )}

        {showSamplesModal && (
          <SampleAnalysesModal
            onSelect={handleSelectSample}
            onClose={() => setShowSamplesModal(false)}
          />
        )}
        </>
      )}

      <div role="status" aria-live="polite">
        {error && (
          <p className="rounded-sm border p-3" style={{ borderColor: "var(--status-critical)", color: "var(--foreground)" }}>
            {error}
          </p>
        )}
      </div>

      {loading && (
        <div className="mx-auto w-full max-w-xl py-16">
          <p className="font-head mb-2 text-xs font-bold uppercase tracking-wide" style={{ color: "var(--ink-muted)" }}>
            Paso {loadingStep + 1} de {LOADING_MESSAGES.length}
          </p>
          <h2 className="font-head mb-6 text-xl font-extrabold" style={{ color: "var(--foreground)" }}>
            {LOADING_MESSAGES[loadingStep]}
          </h2>
          <div className="relative h-[3px] overflow-hidden" style={{ background: "var(--border)" }}>
            <div
              className="absolute top-0 left-0 h-full w-[30%] animate-[sweep_1.1s_ease-in-out_infinite]"
              style={{ background: "var(--accent)" }}
            />
          </div>
        </div>
      )}

      {result && (
        <div
          className="flex flex-wrap items-center justify-between gap-3 rounded-sm border px-4 py-2.5"
          style={{ borderColor: "var(--border)", background: "var(--surface)" }}
        >
          {activeSample ? (
            <p className="text-sm" style={{ color: "var(--foreground)" }}>
              <span className="font-head text-xs font-extrabold uppercase tracking-wide">Análisis de ejemplo</span>
              <span style={{ color: "var(--ink-muted)" }}>
                {" "}
                · resultado real guardado
                {formatSampleDate(activeSample.savedAt) && ` el ${formatSampleDate(activeSample.savedAt)}`}
              </span>
            </p>
          ) : (
            <>
              <p className="text-xs" style={{ color: "var(--ink-muted)" }}>
                Guarda este resultado como JSON para publicarlo como análisis de ejemplo.
              </p>
              <button
                type="button"
                onClick={handleExportSample}
                className="font-head h-9 rounded-sm border px-3 text-[10px] font-bold uppercase"
                style={{ borderColor: "var(--border)", color: "var(--foreground)" }}
              >
                Exportar como ejemplo
              </button>
            </>
          )}
        </div>
      )}

      {result && (
        <ResultsView
          result={result}
          simulation={simulation}
          simulationLoading={simulationLoading}
          simulationError={simulationError}
          onRunSimulation={
            activeSample && !activeSample.simulation && !moxfieldUrl.trim() ? undefined : handleRunSimulation
          }
        />
      )}
    </main>
  );
}
