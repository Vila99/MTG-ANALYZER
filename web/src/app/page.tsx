import type { ReactNode } from "react";
import Link from "next/link";
import { ManaIcon } from "./components/ManaIcon";

/** Landing pública. Siempre oscura: el atributo `data-page="landing"` hace
 * que globals.css fuerce la paleta oscura en todo el documento (Footer del
 * layout incluido) mientras esta página está montada. */

const ANALYZE_HREF = "/analizar";
const SAMPLE_HREF = "/analizar/ejemplo/tom-bombadil";
const REPO_HREF = "https://github.com/Vila99/MTG-ANALYZER";

/** Datos reales del análisis de ejemplo guardado en public/samples/tom-bombadil.json. */
const SAMPLE_PREVIEW = {
  commander: "Tom Bombadil",
  archetype: "Sagas / encantamientos de valor",
  cardImage: "https://cards.scryfall.io/normal/front/2/a/2ab04c49-76a1-4896-8dca-8cb4c615f489.jpg?1783916244",
  score: "6.0",
  stats: [
    { label: "Cartas", value: "100" },
    { label: "Tierras", value: "39" },
    { label: "CMC medio", value: "3.08" },
    { label: "Coste", value: "158 €" },
  ],
  // curva_mana del ejemplo (CMC 1-7), en % del valor máximo (23 cartas a CMC 2)
  curve: [6, 23, 14, 5, 7, 2, 1].map((count) => Math.round((count / 23) * 100)),
};

const PYTHON_ITEMS = [
  "Curva de maná, CMC medio y número de tierras",
  "Pips de cada color frente a fuentes de maná",
  "Legalidad e identidad de color",
  "Rol de cada carta: ramp, robo, removal, wipes…",
  "Suelo de bracket, Game Changers y combos reales",
  "Precio del deck y nota orientativa de 0 a 10",
];

const CLAUDE_ITEMS = [
  "Detecta la estrategia y el arquetipo del deck",
  "Valora las sinergias y los puntos fuertes",
  "Ordena los problemas por severidad",
  "Propone hasta 10 candidatas reales por problema",
  "Respeta tu estilo, tu presupuesto y lo que quieres evitar",
  "Tú eliges qué entra: Claude no decide los cortes",
];

const STEPS = [
  { title: "Parser", text: "Lee el texto o la URL de Moxfield y detecta el comandante." },
  { title: "Enriquecimiento", text: "Cruza cada carta con la base local de Scryfall." },
  { title: "Métricas", text: "Curva, tierras, pips frente a fuentes, legalidad y bracket." },
  { title: "Roles", text: "Reglas sobre el texto oracle, con Claude Haiku de respaldo." },
  { title: "Análisis Claude", text: "Estrategia, puntos fuertes y problemas, en JSON estructurado.", highlight: true },
  { title: "Validación", text: "Cada carta sugerida existe, es legal y encaja en tus colores." },
];

const ICON_PROPS = {
  width: 24,
  height: 24,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round",
  strokeLinejoin: "round",
  "aria-hidden": true,
} as const;

const FEATURES: { title: string; text: string; icon: ReactNode }[] = [
  {
    title: "Importa desde Moxfield",
    text: "Pega la URL de un deck público o una lista en texto con el comandante marcado.",
    icon: (
      <svg {...ICON_PROPS}>
        <path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1" />
        <path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1" />
      </svg>
    ),
  },
  {
    title: "Curva y maná",
    text: "Curva, CMC medio y pips de cada color frente a las fuentes que de verdad los producen.",
    icon: (
      <svg {...ICON_PROPS}>
        <path d="M4 20V10M10 20V4M16 20v-7M22 20H2" />
      </svg>
    ),
  },
  {
    title: "Roles y rubric",
    text: "Cuenta ramp, robo, removal y wipes y los compara con los rangos de referencia de tu arquetipo.",
    icon: (
      <svg {...ICON_PROPS}>
        <rect x="3" y="4" width="7" height="7" rx="1" />
        <rect x="14" y="4" width="7" height="7" rx="1" />
        <rect x="3" y="15" width="7" height="5" rx="1" />
        <rect x="14" y="15" width="7" height="5" rx="1" />
      </svg>
    ),
  },
  {
    title: "Bracket y combos",
    text: "Game Changers, turnos extra y combos reales detectados con Commander Spellbook.",
    icon: (
      <svg {...ICON_PROPS}>
        <path d="M12 3l8 4v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7z" />
        <path d="M9 12l2 2 4-4" />
      </svg>
    ),
  },
  {
    title: "Goldfish estadístico",
    text: "10.000 partidas simuladas: en qué turno lanzas el comandante y cuántas manos se atascan.",
    icon: (
      <svg {...ICON_PROPS}>
        <rect x="3" y="3" width="18" height="18" rx="2" />
        <circle cx="8" cy="8" r="1.2" />
        <circle cx="16" cy="16" r="1.2" />
        <circle cx="12" cy="12" r="1.2" />
      </svg>
    ),
  },
  {
    title: "Precios y presupuesto",
    text: "Coste aproximado con Cardmarket y TCGplayer, y un modo ajustado que prioriza lo barato.",
    icon: (
      <svg {...ICON_PROPS}>
        <path d="M17 6.5A6.5 6.5 0 1 0 17 17.5" />
        <path d="M4 10h9M4 14h9" />
      </svg>
    ),
  },
];

/** Fondo de los bloques que destacan lo que aporta Claude. */
const CLAUDE_BLOCK_STYLE = {
  background: "#0f2526",
  boxShadow: "inset 0 0 0 1px color-mix(in srgb, var(--accent) 28%, transparent)",
} as const;

function Eyebrow({ children }: { children: ReactNode }) {
  return (
    <p className="font-head text-xs font-bold uppercase tracking-[0.14em]" style={{ color: "var(--accent)" }}>
      {children}
    </p>
  );
}

function SectionTitle({ children }: { children: ReactNode }) {
  return (
    <h2
      className="font-head text-[clamp(2rem,3.6vw,3rem)] font-extrabold leading-[1.08] tracking-[-0.015em]"
      style={{ color: "var(--foreground)" }}
    >
      {children}
    </h2>
  );
}

export default function Landing() {
  return (
    <div data-page="landing" style={{ background: "var(--background)", color: "var(--foreground)" }}>
      {/* ============ HERO ============ */}
      <section className="relative overflow-hidden">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              "radial-gradient(60rem 30rem at 85% 10%, color-mix(in srgb, var(--accent) 16%, transparent), transparent 60%), radial-gradient(40rem 24rem at 0% 100%, rgba(240,168,59,0.08), transparent 60%)",
          }}
        />

        <header
          className="relative mx-auto flex max-w-[1200px] items-center justify-between gap-4 border-b px-6 py-4 sm:py-5"
          style={{ borderColor: "var(--border)" }}
        >
          <div className="flex min-w-0 items-center gap-3.5">
            <span className="font-head text-sm font-extrabold uppercase tracking-[0.08em]">MTG Deck Analyzer</span>
            <span className="hidden items-center gap-1.5 text-base sm:flex" aria-hidden="true">
              {["W", "U", "B", "R", "G"].map((color) => (
                <ManaIcon key={color} color={color} />
              ))}
            </span>
          </div>
          <nav
            aria-label="Principal"
            className="font-head flex flex-wrap items-center gap-x-6 gap-y-2 text-xs font-bold uppercase tracking-[0.06em]"
          >
            <a
              href="#como-funciona"
              className="hidden min-h-11 items-center hover:underline sm:inline-flex"
              style={{ color: "var(--ink-secondary)" }}
            >
              Cómo funciona
            </a>
            <a
              href={REPO_HREF}
              className="hidden min-h-11 items-center hover:underline sm:inline-flex"
              style={{ color: "var(--ink-secondary)" }}
            >
              GitHub
            </a>
            <Link href={ANALYZE_HREF} className="fx-btn fx-primary h-11 px-4 text-xs">
              <span className="sm:hidden">Analizar</span>
              <span className="hidden sm:inline">Analizar mi deck</span>
            </Link>
          </nav>
        </header>

        <div className="relative mx-auto flex max-w-[1200px] flex-wrap items-center gap-12 px-6 pt-12 pb-16 sm:gap-16 sm:pt-[88px] sm:pb-[104px]">
          <div className="flex min-w-0 flex-[1_1_460px] flex-col gap-7">
            <Eyebrow>Commander · EDH · Analizado con Claude</Eyebrow>
            <h1 className="font-head text-[clamp(2.5rem,5vw,4.25rem)] leading-[1.02] font-extrabold tracking-[-0.02em] text-white">
              Tu deck, leído carta a carta.
            </h1>
            <p className="max-w-[34rem] text-[19px] leading-[1.55]" style={{ color: "var(--ink-secondary)" }}>
              Pega una lista de Moxfield y obtén la curva, el maná, los roles y el bracket calculados al detalle.
              Después, Claude detecta la estrategia, señala los problemas y propone cartas reales para
              arreglarlos, todas validadas contra Scryfall.
            </p>
            <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
              <Link href={ANALYZE_HREF} className="fx-btn fx-primary h-[52px] px-[26px] text-sm">
                Analizar mi deck
              </Link>
              <Link href={SAMPLE_HREF} className="fx-btn fx-secondary h-[52px] px-[26px] text-sm">
                Ver un análisis real
              </Link>
            </div>
            <p className="text-[13px]" style={{ color: "var(--ink-muted)" }}>
              Gratis y de código abierto. Sin cuenta. Sin la API key solo te pierdes el análisis de Claude.
            </p>
          </div>

          {/* Vista previa del resultado (datos del ejemplo real) */}
          <div className="flex min-w-0 flex-[1_1_440px] justify-center">
            <div
              className="w-full max-w-[520px] overflow-hidden rounded sm:-rotate-[1.2deg]"
              style={{
                background: "#16181b",
                boxShadow:
                  "0 40px 80px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.14), 0 0 60px color-mix(in srgb, var(--accent) 12%, transparent)",
              }}
            >
              <div
                className="flex items-center justify-between gap-3 border-b px-4 py-2.5"
                style={{ background: "var(--surface)", borderColor: "var(--border)" }}
              >
                <span className="font-head text-[10px] font-extrabold uppercase tracking-[0.1em]">Análisis de ejemplo</span>
                <span className="text-[11px]" style={{ color: "var(--ink-muted)" }}>
                  Bracket 3 · Casual
                </span>
              </div>
              <div className="flex flex-col gap-4 p-5">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-head text-[22px] font-extrabold">{SAMPLE_PREVIEW.commander}</p>
                    <p
                      className="font-head mt-1 text-[10px] font-bold uppercase tracking-[0.06em]"
                      style={{ color: "var(--ink-muted)" }}
                    >
                      {SAMPLE_PREVIEW.archetype}
                    </p>
                  </div>
                  <p
                    className="flex h-14 w-14 flex-shrink-0 items-center justify-center rounded-full border-[3px] font-mono text-xl font-bold"
                    style={{ borderColor: "var(--status-warning)", color: "var(--status-warning)" }}
                    aria-label={`Nota ${SAMPLE_PREVIEW.score} sobre 10`}
                  >
                    {SAMPLE_PREVIEW.score}
                  </p>
                </div>
                <div className="flex items-start gap-4">
                  {/* eslint-disable-next-line @next/next/no-img-element -- imagen externa de Scryfall */}
                  <img
                    src={SAMPLE_PREVIEW.cardImage}
                    alt={`Carta ${SAMPLE_PREVIEW.commander}`}
                    className="mtg-card w-[38%] max-w-[150px] flex-shrink-0 object-cover"
                    style={{ aspectRatio: "5/7", boxShadow: "0 8px 20px rgba(0,0,0,0.5)" }}
                  />
                  <div className="grid min-w-0 flex-1 grid-cols-2 gap-2">
                    {SAMPLE_PREVIEW.stats.map((stat) => (
                      <div
                        key={stat.label}
                        className="rounded-sm border p-2.5"
                        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
                      >
                        <p
                          className="font-head text-[9px] font-bold uppercase tracking-[0.06em]"
                          style={{ color: "var(--ink-muted)" }}
                        >
                          {stat.label}
                        </p>
                        <p className="mt-1 font-mono text-xl font-bold">{stat.value}</p>
                      </div>
                    ))}
                    <div
                      className="col-span-2 rounded-sm border p-2.5"
                      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
                    >
                      <p
                        className="font-head text-[9px] font-bold uppercase tracking-[0.06em]"
                        style={{ color: "var(--ink-muted)" }}
                      >
                        Curva de maná
                      </p>
                      <div className="mt-2 flex h-[52px] items-end gap-1" aria-hidden="true">
                        {SAMPLE_PREVIEW.curve.map((height, index) => (
                          <div key={index} className="flex-1" style={{ height: `${height}%`, background: "var(--accent)" }} />
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
                <div className="flex items-start gap-2.5 border-t pt-3.5" style={{ borderColor: "var(--border)" }}>
                  <span
                    className="font-head mt-0.5 flex-shrink-0 rounded-sm px-2 py-0.5 text-[9px] font-extrabold uppercase tracking-[0.08em]"
                    style={{ background: "rgba(240,168,59,0.16)", color: "var(--status-warning)" }}
                  >
                    Media
                  </span>
                  <p className="text-[13px] leading-[1.45]" style={{ color: "var(--ink-secondary)" }}>
                    <strong style={{ color: "var(--foreground)" }}>Sin wipes ni respuesta masiva.</strong> Si un rival
                    crece en mesa, el deck tarda turnos en contestar. → 10 candidatas reales
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============ PRINCIPIO ============ */}
      <section className="border-t" style={{ borderColor: "var(--border)" }}>
        <div className="mx-auto flex max-w-[1200px] flex-col gap-12 px-6 py-16 sm:py-24">
          <div className="flex max-w-[44rem] flex-col gap-4">
            <Eyebrow>El principio</Eyebrow>
            <SectionTitle>El código calcula. Claude interpreta.</SectionTitle>
            <p className="text-lg leading-relaxed" style={{ color: "var(--ink-secondary)" }}>
              Nunca se le pide a una IA que cuente tierras ni que recuerde el texto de una carta. Lo objetivo se
              calcula de forma exacta, y Claude recibe esos datos ya listos para hacer lo que mejor se le da.
            </p>
          </div>
          <div
            className="grid grid-cols-[repeat(auto-fit,minmax(min(300px,100%),1fr))] gap-px border"
            style={{ background: "var(--border)", borderColor: "var(--border)" }}
          >
            <div className="flex flex-col gap-5 p-9" style={{ background: "var(--surface)" }}>
              <div className="flex items-center gap-3">
                <svg {...ICON_PROPS} width={28} height={28}>
                  <rect x="4" y="3" width="16" height="18" rx="1" />
                  <path d="M8 7h8M8 11h2M12 11h2M8 15h2M12 15h2M8 18h2M12 18h4" />
                </svg>
                <h3 className="font-head text-[13px] font-extrabold uppercase tracking-[0.08em]">Python calcula</h3>
              </div>
              <ul className="flex list-disc flex-col gap-2.5 pl-[18px] text-base leading-normal" style={{ color: "var(--ink-secondary)" }}>
                {PYTHON_ITEMS.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div className="flex flex-col gap-5 p-9" style={CLAUDE_BLOCK_STYLE}>
              <div className="flex items-center gap-3" style={{ color: "var(--accent)" }}>
                <svg {...ICON_PROPS} width={28} height={28}>
                  <path d="M12 3l1.8 4.6L18.5 9l-4.7 1.4L12 15l-1.8-4.6L5.5 9l4.7-1.4z" />
                  <path d="M18 15l.9 2.1L21 18l-2.1.9L18 21l-.9-2.1L15 18l2.1-.9z" />
                </svg>
                <h3
                  className="font-head text-[13px] font-extrabold uppercase tracking-[0.08em]"
                  style={{ color: "var(--foreground)" }}
                >
                  Claude interpreta
                </h3>
              </div>
              <ul className="flex list-disc flex-col gap-2.5 pl-[18px] text-base leading-normal" style={{ color: "var(--ink-secondary)" }}>
                {CLAUDE_ITEMS.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ============ CÓMO FUNCIONA ============ */}
      <section id="como-funciona" className="scroll-mt-4 border-t" style={{ borderColor: "var(--border)" }}>
        <div className="mx-auto flex max-w-[1200px] flex-col gap-12 px-6 py-16 sm:py-24">
          <div className="flex flex-wrap items-end justify-between gap-6">
            <div className="flex max-w-[40rem] flex-col gap-4">
              <Eyebrow>Cómo funciona</Eyebrow>
              <SectionTitle>De la lista al informe en seis pasos.</SectionTitle>
            </div>
            <p className="max-w-[26rem] text-base leading-[1.55]" style={{ color: "var(--ink-secondary)" }}>
              Cada sugerencia pasa un último filtro: si la carta no existe, no es legal, se sale de tu identidad de
              color o ya está en el deck, no se muestra.
            </p>
          </div>
          <ol
            className="grid grid-cols-[repeat(auto-fit,minmax(170px,1fr))] gap-px border"
            style={{ background: "var(--border)", borderColor: "var(--border)" }}
          >
            {STEPS.map((step, index) => (
              <li
                key={step.title}
                className="flex flex-col gap-3 p-6"
                style={step.highlight ? CLAUDE_BLOCK_STYLE : { background: "var(--surface)" }}
              >
                <span className="font-mono text-[13px] font-bold" style={{ color: "var(--accent)" }}>
                  {String(index + 1).padStart(2, "0")}
                </span>
                <span className="font-head text-[15px] font-extrabold">{step.title}</span>
                <span className="text-sm leading-normal" style={{ color: "var(--ink-secondary)" }}>
                  {step.text}
                </span>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* ============ FUNCIONALIDADES ============ */}
      <section className="border-t" style={{ borderColor: "var(--border)", background: "var(--surface-muted)" }}>
        <div className="mx-auto flex max-w-[1200px] flex-col gap-12 px-6 py-16 sm:py-24">
          <div className="flex max-w-[40rem] flex-col gap-4">
            <Eyebrow>Qué te da</Eyebrow>
            <SectionTitle>Todo lo que miras antes de una partida, en una pantalla.</SectionTitle>
          </div>
          <div className="grid grid-cols-[repeat(auto-fit,minmax(min(250px,100%),1fr))] gap-4">
            {FEATURES.map((feature) => (
              <div
                key={feature.title}
                className="flex flex-col gap-3 rounded-sm border p-7"
                style={{ background: "var(--surface)", borderColor: "var(--border)" }}
              >
                <span style={{ color: "var(--accent)" }}>{feature.icon}</span>
                <h3 className="font-head text-base font-extrabold">{feature.title}</h3>
                <p className="text-[15px] leading-[1.55]" style={{ color: "var(--ink-secondary)" }}>
                  {feature.text}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============ CTA FINAL ============ */}
      <section className="border-t" style={{ borderColor: "var(--border)" }}>
        <div className="mx-auto flex max-w-[1200px] flex-wrap items-center justify-between gap-10 px-6 py-16 sm:py-[104px]">
          <div className="flex min-w-0 flex-[1_1_520px] flex-col gap-[18px]">
            <h2 className="font-head text-[clamp(2rem,4vw,3.25rem)] leading-[1.05] font-extrabold tracking-[-0.015em] text-white">
              ¿Qué le falta a tu deck?
            </h2>
            <p className="max-w-[36rem] text-lg leading-[1.55]" style={{ color: "var(--ink-secondary)" }}>
              Pega la URL de Moxfield y en menos de dos minutos tienes las métricas, los problemas y las cartas que
              podrían arreglarlos.
            </p>
          </div>
          <div className="flex w-full flex-col gap-3 sm:w-auto sm:flex-row sm:flex-wrap">
            <Link href={ANALYZE_HREF} className="fx-btn fx-primary h-14 px-[30px] text-[15px]">
              Analizar mi deck
            </Link>
            <Link href={SAMPLE_HREF} className="fx-btn fx-secondary h-14 px-[30px] text-[15px]">
              Ver un análisis real
            </Link>
            <a href={REPO_HREF} className="fx-btn fx-secondary h-14 px-[30px] text-[15px]">
              Ver en GitHub
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}
