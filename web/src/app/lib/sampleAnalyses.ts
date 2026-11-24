import { AnalyzeResponse, SimulationResult } from "../types";
import { normalizeStoredResult } from "./recentAnalyses";

/** Análisis de ejemplo: un resultado real de /analyze (y, si se ejecutó, de
 * /simulate) congelado como JSON estático en `public/samples/`. Sirve para
 * enseñar cómo resuelve el analizador un deck con Claude sin backend, sin
 * API key y sin gastar tokens. Para publicar uno: «Exportar como ejemplo»
 * en la vista de resultados, copiar el archivo a `public/samples/` y
 * añadirlo a `public/samples/index.json`. */

const SAMPLES_BASE = "/samples";
const SAMPLE_FORMAT_VERSION = 1;

export interface SampleIndexEntry {
  id: string;
  title: string;
  commander: string;
  description?: string;
  /** Si el ejemplo incluye el análisis de Claude o solo las métricas. */
  ai: boolean;
  /** Nombre del archivo dentro de `public/samples/`. */
  file: string;
}

export interface SampleAnalysis {
  version: number;
  id: string;
  title: string;
  description: string;
  /** Fecha ISO en la que se hizo el análisis. */
  savedAt: string;
  request: { moxfieldUrl: string };
  result: AnalyzeResponse;
  simulation: SimulationResult | null;
}

export async function loadSampleIndex(): Promise<SampleIndexEntry[]> {
  const response = await fetch(`${SAMPLES_BASE}/index.json`, { cache: "no-store" });
  if (!response.ok) throw new Error(`No se pudo cargar la lista de ejemplos (${response.status}).`);
  const parsed = await response.json();
  return Array.isArray(parsed) ? parsed : [];
}

export async function loadSample(entry: SampleIndexEntry): Promise<SampleAnalysis> {
  const response = await fetch(`${SAMPLES_BASE}/${encodeURIComponent(entry.file)}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`No se pudo cargar el ejemplo «${entry.title}» (${response.status}).`);
  const sample = (await response.json()) as SampleAnalysis;
  return {
    ...sample,
    request: sample.request ?? { moxfieldUrl: "" },
    simulation: sample.simulation ?? null,
    result: normalizeStoredResult(sample.result),
  };
}

function slugify(text: string): string {
  return (
    text
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "") || "deck"
  );
}

export function buildSampleExport(
  result: AnalyzeResponse,
  simulation: SimulationResult | null,
  moxfieldUrl: string
): SampleAnalysis {
  const commander = result.comandantes.length > 0 ? result.comandantes.join(" + ") : "Sin comandante";
  return {
    version: SAMPLE_FORMAT_VERSION,
    id: slugify(commander),
    title: commander,
    description: result.analisis?.arquetipo ?? "",
    savedAt: new Date().toISOString(),
    request: { moxfieldUrl },
    result,
    simulation,
  };
}

/** Descarga el ejemplo como `<id>.json` para soltarlo en `public/samples/`. */
export function downloadSample(sample: SampleAnalysis): void {
  const blob = new Blob([JSON.stringify(sample, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${sample.id}.json`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export function formatSampleDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleDateString("es-ES", { day: "numeric", month: "long", year: "numeric" });
}
