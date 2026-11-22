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
  motivo: string;
}

export interface Analisis {
  estrategia_detectada: string;
  arquetipo: string;
  puntos_fuertes: string[];
  problemas: Problema[];
  cortes_sugeridos: CorteSugerido[];
  anadidos_sugeridos: AñadidoSugerido[];
}

export interface AnalyzeResponse {
  comandantes: string[];
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
  analisis?: Analisis;
}

export interface AnalyzeRequest {
  deck_text: string;
  bracket?: number;
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
