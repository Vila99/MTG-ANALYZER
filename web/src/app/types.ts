export type RubricStatus = "bajo" | "ok" | "alto";

export interface Problema {
  categoria: string;
  severidad: "alta" | "media" | "baja";
  explicacion: string;
}

export interface CorteSugerido {
  carta: string;
  motivo: string;
}

export interface AñadidoSugerido {
  carta: string;
  rol: string;
  reemplaza_a: string | null;
  categoria_problema: string | null;
  motivo: string;
  // Presentes solo si se dio `budget` en la petición (ver analyzer.budget).
  precio_eur?: number | null;
  incluido?: boolean;
}

export interface PresupuestoResumen {
  presupuesto: number;
  coste_estimado: number;
  supera_presupuesto: boolean;
  diferencia: number;
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
  cortes_sugeridos: CorteSugerido[];
  anadidos_sugeridos: AñadidoSugerido[];
  bracket: BracketAnalisis;
  presupuesto?: PresupuestoResumen | null;
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

export interface AnalyzeRequest {
  deck_text?: string;
  moxfield_url?: string;
  commander?: string;
  description?: string;
  budget?: number;
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
