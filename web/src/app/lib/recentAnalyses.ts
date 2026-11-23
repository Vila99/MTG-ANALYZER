import { AnalyzeResponse } from "../types";

const STORAGE_KEY = "mtg-analyzer-recent";
const MAX_ENTRIES = 8;

export interface RecentEntry {
  id: string;
  timestamp: number;
  commander: string;
  deckSize: number;
  result: AnalyzeResponse;
}

/** Rellena con valores por defecto los campos que se fueron añadiendo a
 * AnalyzeResponse después de guardarse algunas entradas: localStorage
 * conserva el JSON tal cual se guardó, así que un análisis antiguo puede
 * no tener `identidad_color`, `nota_deck` o `coste_aproximado`. Sin esto,
 * cargar una entrada vieja rompe la vista de resultados. */
function normalizeStoredResult(result: Partial<AnalyzeResponse>): AnalyzeResponse {
  return {
    identidad_color: [],
    nota_deck: 0,
    coste_aproximado: { total_eur: 0, cartas_sin_precio: [] },
    ...result,
  } as AnalyzeResponse;
}

export function loadRecentAnalyses(): RecentEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.map((entry) => ({ ...entry, result: normalizeStoredResult(entry.result) }));
  } catch {
    return [];
  }
}

export function saveRecentAnalysis(result: AnalyzeResponse): RecentEntry[] {
  const entry: RecentEntry = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    timestamp: Date.now(),
    commander: result.comandantes.length > 0 ? result.comandantes.join(" + ") : "Sin comandante",
    deckSize: result.tamano_deck,
    result,
  };
  const next = [entry, ...loadRecentAnalyses()].slice(0, MAX_ENTRIES);
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  } catch {
    // almacenamiento no disponible (privado/bloqueado): seguimos sin persistir
  }
  return next;
}

export function removeRecentAnalysis(id: string): RecentEntry[] {
  const next = loadRecentAnalyses().filter((entry) => entry.id !== id);
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  } catch {
    // ignorado: ver saveRecentAnalysis
  }
  return next;
}

export function formatRelativeTime(timestamp: number): string {
  const minutes = Math.round((Date.now() - timestamp) / 60000);
  if (minutes < 1) return "ahora mismo";
  if (minutes < 60) return `hace ${minutes} min`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `hace ${hours} h`;
  const days = Math.round(hours / 24);
  return `hace ${days} d`;
}
