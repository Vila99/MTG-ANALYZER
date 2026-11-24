# MTG Commander Deck Analyzer

Analizador de decks de Magic: The Gathering en formato **Commander/EDH**. Calcula las métricas objetivas del deck (curva, tierras, fuentes de maná, roles, bracket…) y, con ayuda de la API de Claude, detecta su estrategia, señala sus problemas y propone cartas reales para corregirlos.

> **El código calcula, Claude interpreta.** Todo lo que es objetivo se calcula de forma determinista en Python; Claude solo recibe datos ya estructurados y se encarga de la estrategia, las sinergias y las sugerencias. Cada carta que propone se valida después contra la base de datos de Scryfall antes de mostrarla.

## Funcionalidades

- **Entrada flexible:** lista en texto plano (con el comandante marcado como `*CMDR*` o `Commander:`) o importación directa desde una URL pública de **Moxfield**.
- **Métricas deterministas:** curva de maná, CMC medio, número de tierras, pips de color frente a fuentes, legalidad e identidad de color.
- **Clasificación por rol:** `ramp`, `draw`, `removal`, `wipe`, `protection`, `tutor`, `wincon`… Usa reglas sobre el texto oracle y Claude Haiku como respaldo, con caché en SQLite.
- **Rubric configurable:** compara el deck con los rangos de referencia (35–38 tierras, 10–12 de ramp, 10+ de robo…), ajustados según el arquetipo.
- **Suelo de bracket:** detección de Game Changers, destrucción masiva de tierras, turnos extra y combos reales vía **Commander Spellbook**.
- **Goldfish estadístico:** simulación Monte Carlo sin rivales para medir la consistencia de maná y curva (en qué turno puedes lanzar el comandante, manos con problemas de color…).
- **Análisis con Claude (Sonnet):** estrategia detectada, puntos fuertes y problemas ordenados por severidad. Cada problema trae hasta 10 candidatas elegidas de un pool de cartas reales.
- **Validación de sugerencias:** se descartan las cartas que no existen, no son legales, quedan fuera de la identidad de color o ya están en el deck.
- **Precios:** coste aproximado del deck y modo de presupuesto `ajustado`, con precios de Cardmarket y TCGplayer vía Scryfall.
- **Nota orientativa de 0 a 10**, calculada de forma determinista a partir del rubric y de la severidad de los problemas.
- **Interfaz web:** app en Next.js con gráficos de curva y roles, imágenes de carta con zoom, detalle de combos e historial de análisis recientes.

## Stack

| Capa | Tecnología |
|---|---|
| Núcleo | Python 3.11+ |
| Datos | SQLite con el bulk data `oracle_cards` de Scryfall, más las cachés de roles, precios y combos |
| IA | SDK oficial `anthropic`: Claude Haiku para clasificar roles y Claude Sonnet para el análisis, con tool use y prompt caching |
| API | FastAPI + Uvicorn |
| Frontend | Next.js, React, Tailwind CSS y Recharts |
| Tests | pytest (sin llamadas reales a la API) |

## Instalación

Requisitos: Python 3.11 o superior y Node.js 20 o superior (este último solo para la web).

```bash
git clone https://github.com/Vila99/MTG-ANALYZER.git
cd MTG-ANALYZER

python -m venv .venv
source .venv/bin/activate      # en Windows: .venv\Scripts\activate
pip install -e ".[dev]"

cp .env.example .env           # añade tu ANTHROPIC_API_KEY

# Opcional: descarga el bulk data de Scryfall y genera data/cards.db
python scripts/load_scryfall.py
```

La base de datos de cartas (`data/cards.db`, unos 40 MB) no está en el repositorio. Se genera en tu equipo con las cartas actualizadas de Scryfall. Si no la creas a mano, se crea sola la primera vez:

- **`analyze`** te pregunta si quieres descargarla. Con `--download-db` la descarga sin preguntar, útil en scripts.
- **El backend** la descarga en segundo plano al arrancar. Mientras tanto, la web avisa de que se está preparando. Para desactivarlo, usa `AUTO_DOWNLOAD_CARDS_DB=0`.

Vuelve a ejecutar `python scripts/load_scryfall.py` cuando quieras actualizar las cartas, por ejemplo tras una colección nueva o cambios de baneos. Las cachés de roles, precios y combos se conservan.

La API key solo se lee de la variable de entorno `ANTHROPIC_API_KEY`. Sin ella funciona todo salvo el análisis con Claude (`--ai`) y el respaldo de Haiku para clasificar roles.

## Uso desde la terminal

```bash
# Métricas, roles y rubric, sin IA
analyze data/sample_decks/atraxa_sample.txt

# Importar desde Moxfield
analyze --moxfield-url https://www.moxfield.com/decks/<id>

# Análisis completo con Claude
analyze data/sample_decks/jasnah.txt --ai --style focused --budget-mode ajustado

# Salida en JSON
analyze data/sample_decks/jasnah.txt --ai --json
```

| Opción | Descripción |
|---|---|
| `--ai` | Pide a Claude el análisis completo del deck |
| `--style casual\|focused\|cedh` | Estilo o nivel de exigencia del deck |
| `--budget-mode ajustado\|libre` | `ajustado` prioriza candidatas más baratas; `libre` no aplica esa preferencia |
| `--allow-combos` | Permite que se sugieran combos |
| `--avoid <carta o mecánica>` | Algo que no quieres en las sugerencias (se puede repetir) |
| `--commander <nombre>` | Comandante, si no está marcado en la lista |
| `--description "<texto>"` | Tu idea del deck, en tus palabras, como contexto para Claude |
| `--json` | Salida en JSON en vez de texto |
| `--download-db` | Si falta `data/cards.db`, la descarga de Scryfall sin preguntar |

## Interfaz web

```bash
# Backend: desde la raíz del repo, con el venv activado
uvicorn analyzer.api:app --reload
# → http://localhost:8000  (documentación interactiva en /docs)

# Frontend: en otra terminal
cd web
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
# → http://localhost:3000
```

El backend solo acepta peticiones del origen indicado en `FRONTEND_ORIGIN` (por defecto `http://localhost:3000`).

Endpoints principales: `GET /health`, `POST /analyze` y `POST /simulate` (goldfish).

## Cómo funciona

```
Lista del deck (texto / Moxfield)
   │
   ▼
1. Parser ──────────► nombres normalizados + comandante(s)
2. Enriquecimiento ─► datos de cada carta desde la BD local de Scryfall
3. Métricas ────────► curva, CMC medio, tierras, pips vs fuentes, legalidad, bracket
4. Clasificación ───► rol de cada carta (reglas + Haiku, con caché)
5. Análisis Claude ─► JSON estructurado mediante tool use
6. Validación ──────► las sugerencias existen, son legales y encajan en la identidad de color
   │
   ▼
Informe (terminal, JSON o web)
```

Claude no decide qué cortar ni empareja cada candidata con una carta a quitar: propone opciones por problema y el jugador elige las que encajan con su plan. El contrato completo está en [CLAUDE.md](CLAUDE.md#contrato-con-claude) y el system prompt en [`prompts/system_analysis.md`](prompts/system_analysis.md).

## Estructura

```
├── src/analyzer/        # parser, cards, metrics, roles, rubric, bracket, combos,
│                        # goldfish, prices, scoring, llm, validate, pipeline, report, cli, api
├── prompts/             # system prompt del análisis (cacheable)
├── scripts/             # load_scryfall.py, run_eval.py, compare_eval.py
├── data/sample_decks/   # decks de prueba
├── tests/               # pytest
└── web/                 # frontend Next.js
```

## Tests y evaluación

```bash
pytest                                              # toda la suite; llm.py está mockeado

python scripts/run_eval.py                          # analiza los decks de data/sample_decks/ con Claude
python scripts/compare_eval.py <run1.json> <run2.json>   # compara dos ejecuciones guardadas
```

Las evaluaciones requieren `ANTHROPIC_API_KEY` y se guardan en `data/eval_runs/`, que no se versiona.

## Créditos

- Datos de cartas e imágenes: [Scryfall](https://scryfall.com).
- Detección de combos: [Commander Spellbook](https://commanderspellbook.com).
- Iconos de maná: [Mana](https://github.com/andrewgioia/mana), de Andrew Gioia.

*Proyecto de fans no oficial. Magic: The Gathering y todo lo relacionado es propiedad de Wizards of the Coast. Este proyecto no está producido, respaldado ni afiliado con Wizards of the Coast.*
