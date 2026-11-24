export type RubricStatus = "bajo" | "ok" | "alto";

export interface CandidataSugerida {
  carta: string;
  rol: string;
  motivo: string;
  // Siempre presente tras pasar por analyzer.budget.annotate_prices.
  precio_eur?: number | null;
}

export interface Problema {
  categoria: string;
  severidad: "alta" | "media" | "baja";
  explicacion: string;
  candidatas_sugeridas: CandidataSugerida[];
}

export interface SenalDura {
  tipo: string;
  detalle: string;
}

export interface ComboDetectado {
  cartas: string[];
  produce: string[];
  descripcion: string;
  velocidad?: "temprano" | "tardío";
}

export interface BracketAnalisis {
  deducido: number;
  confianza: "alta" | "media" | "baja";
  suelo: number;
  estimacion_juego: number;
  game_changers: string[];
  senales_duras: SenalDura[];
  razones: string[];
  que_lo_moveria: { bajar: string[]; subir: string[] };
}

export interface Analisis {
  estrategia_detectada: string;
  arquetipo: string;
  puntos_fuertes: string[];
  problemas: Problema[];
  bracket: BracketAnalisis;
  combos_detectados?: ComboDetectado[];
}

export interface AnalyzeResponse {
  comandantes: string[];
  identidad_color: string[];
  tamano_deck: number;
  tierras: number;
  cmc_medio: number;
  curva_mana: Record<string, number>;
  pips: Record<string, number>;
  fuentes_mana: Record<string, number>;
  no_legales: string[];
  no_encontradas: string[];
  roles: Record<string, number>;
  rubric: Record<string, RubricStatus>;
  nota_deck: number;
  coste_aproximado: { total_eur: number; cartas_sin_precio: string[] };
  analisis?: Analisis;
  card_images: Record<string, string>;
  cartas_por_rol: Record<string, string[]>;
}

export interface SimulationResult {
  simulaciones: number;
  turno_comandante_lanzable: {
    media: number | null;
    por_turno: Record<string, number>;
    nunca_pct: number;
  };
  prob_mana_screw_turno_3: number;
  primera_rampa: {
    media: number | null;
    por_turno: Record<string, number>;
  };
  curva_mana_media: Record<string, number>;
  prob_mulligan: number;
  colores_disponibles_turno_4?: Record<string, number>;
  no_encontradas: string[];
}

export interface SimulateRequest {
  deck_text?: string;
  moxfield_url?: string;
  commander?: string;
  n_sims: number;
}

export interface AnalyzeRequest {
  deck_text?: string;
  moxfield_url?: string;
  commander?: string;
  description?: string;
  budget_mode?: "ajustado" | "libre";
  style: "casual" | "focused" | "cedh";
  allow_combos: boolean;
  avoid: string[];
  ai: boolean;
}

export const ROLE_LABELS: Record<string, string> = {
  land: "Tierras",
  ramp: "Ramp",
  draw: "Robo de cartas",
  removal: "Removal puntual",
  wipe: "Wipes",
  protection: "Protección",
  tutor: "Tutores",
  wincon: "Condiciones de victoria",
  synergy: "Sinergia",
  other: "Sin clasificar",
};

export const COLOR_LABELS: Record<string, string> = {
  W: "Blanco",
  U: "Azul",
  B: "Negro",
  R: "Rojo",
  G: "Verde",
};
