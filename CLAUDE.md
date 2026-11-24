# MTG Commander Deck Analyzer

Aplicación que analiza decks de Magic: The Gathering (formato Commander/EDH) y, con ayuda de la API de Claude, propone mejoras según criterios configurables.

## Principio de diseño

**El código calcula, Claude interpreta.**

- Todo lo que es objetivo (conteos, curva de maná, legalidad, identidad de color, fuentes de maná) se calcula de forma determinista en Python. Nunca se le pide a Claude que cuente ni que recuerde el texto de una carta.
- Claude recibe datos ya estructurados y se encarga de lo que hace bien: detectar la estrategia, valorar sinergias, explicar problemas y proponer cortes y añadidos.
- Toda carta que sugiera Claude se **valida** después contra la base de datos de Scryfall antes de mostrarla al usuario.

## Flujo del análisis

```
Lista del deck (texto / URL)
   │
   ▼
1. Parser ──────────────► nombres normalizados + comandante(s)
   │
   ▼
2. Enriquecimiento ─────► datos de cada carta desde la BD local (Scryfall bulk data)
   │
   ▼
3. Métricas ────────────► curva, CMC medio, tierras, pips vs fuentes, legalidad
   │
   ▼
4. Clasificación ───────► rol de cada carta (ramp, robo, removal…), con caché por carta
   │
   ▼
5. Análisis Claude ─────► JSON estructurado (estrategia, problemas, cortes, añadidos)
   │
   ▼
6. Validación ──────────► las sugerencias existen, son legales y encajan en la identidad de color
   │
   ▼
Informe final (CLI → más adelante web)
```

## Stack

- **Lenguaje:** Python 3.11+
- **API:** FastAPI (fase web)
- **BD:** SQLite (cartas de Scryfall + caché de clasificaciones)
- **IA:** SDK oficial `anthropic`
  - `claude-haiku-5-5` → clasificación masiva de cartas por rol (barato; resultado cacheado)
  - `claude-sonnet-5-5` → análisis final del deck
- **Frontend (fase posterior):** React / Next.js + Recharts
- **Tests:** pytest

## Estructura del proyecto

```
mtg-deck-analyzer/
├── CLAUDE.md
├── README.md
├── pyproject.toml
├── .env.example            # ANTHROPIC_API_KEY=
├── data/
│   ├── cards.db            # generado por scripts/load_scryfall.py (no se versiona)
│   └── sample_decks/       # decks de prueba en .txt
├── scripts/
│   └── load_scryfall.py    # descarga el bulk data "oracle_cards" y lo carga en SQLite
├── src/analyzer/
│   ├── parser.py           # texto → [(cantidad, nombre)], detecta comandante
│   ├── cards.py            # acceso a la BD de cartas
│   ├── metrics.py          # curva, tierras, pips, legalidad, identidad de color
│   ├── roles.py            # clasificación por rol (reglas + Claude Haiku + caché)
│   ├── rubric.py           # criterios configurables por arquetipo
│   ├── llm.py              # llamadas a la API de Claude (tool use, prompt caching)
│   ├── validate.py         # valida las sugerencias de Claude
│   ├── report.py           # salida en terminal / JSON
│   └── cli.py              # punto de entrada: `analyze deck.txt`
├── prompts/
│   └── system_analysis.md  # system prompt con el rubric (cacheable)
└── tests/
```

## Fuentes de datos

- **Scryfall** (fuente principal). Usar el *bulk data* `oracle_cards` y no hacer una petición por carta. Si se usa la API en vivo, respetar su límite de peticiones (~10/s, con pausas de 50–100 ms) y enviar un `User-Agent` propio.
- **Commander Spellbook** (opcional): detección de combos.
- **EDHREC** (opcional): no tiene API oficial; revisar sus condiciones de uso antes de usarlo.

## Rubric base (configurable)

Valores de referencia para un deck "estándar". `rubric.py` los ajusta según el arquetipo detectado.

| Rol                      | Rango   |
|--------------------------|---------|
| Tierras                  | 35–38   |
| Ramp                     | 10–12   |
| Robo / ventaja de cartas | 10+     |
| Removal puntual          | 8–10    |
| Wipes                    | 2–4     |
| CMC medio (sin tierras)  | ~3.0    |

Roles de carta: `land`, `ramp`, `draw`, `removal`, `wipe`, `protection`, `tutor`, `wincon`, `synergy`, `other`. Una carta puede tener varios roles.

Parámetros de usuario:
- `bracket` / nivel de poder (1–5)
- `budget_mode` (`ajustado` prioriza candidatas más baratas, `libre` no
  aplica esa preferencia; no es un importe fijo, solo un criterio de orden)
- `style` (casual, focused, cEDH)
- `allow_combos` (sí/no)
- `avoid` (cartas o mecánicas a evitar)

## Contrato con Claude

El análisis se pide con **tool use** para forzar este esquema de salida.
Los nombres de propiedad de un tool schema de la API solo admiten
`^[a-zA-Z0-9_.-]{1,64}$`: una `ñ` en el nombre de un campo (no en su
contenido) rompe la petición con un 400 (`BadRequestError`, descubierto
probando en real) — por eso campos como `candidatas_sugeridas` van sin
tilde. El texto de las sugerencias, en español, no tiene esa restricción.

```json
{
  "estrategia_detectada": "string",
  "arquetipo": "string",
  "puntos_fuertes": ["string"],
  "problemas": [
    {
      "categoria": "string",
      "severidad": "alta|media|baja",
      "explicacion": "string",
      "candidatas_sugeridas": [
        { "carta": "string", "rol": "string", "motivo": "string" }
      ]
    }
  ]
}
```

`candidatas_sugeridas` son hasta 10 cartas por problema que lo atacan;
Claude no decide qué cortar del mazo ni empareja una candidata 1:1 con una
carta a quitar, solo propone opciones y el jugador elige cuáles le
encajan con su plan (ver `prompts/system_analysis.md`).

Entrada que recibe Claude (JSON): comandante(s) con su texto oracle, métricas calculadas, lista de cartas con su rol y su texto, parámetros del usuario y, opcionalmente, un **pool de candidatas** (por ejemplo, de una búsqueda de Scryfall como `id<=bg otag:ramp`) para que elija entre cartas reales.

Reglas:
- El system prompt (con el rubric) va con `cache_control` para aprovechar el prompt caching.
- Las sugerencias que no pasen `validate.py` (no existe, no es legal, fuera de la identidad de color o ya está en el deck) se descartan o se vuelven a pedir.
- La API key solo se lee de la variable de entorno `ANTHROPIC_API_KEY`. Nunca se escribe en el código ni en los logs.

## Fases

- [ ] **Fase 1 – Base sin IA:** `load_scryfall.py`, parser, métricas y salida en la terminal.
- [ ] **Fase 2 – Clasificación por roles:** reglas sobre el texto oracle + Haiku como respaldo + caché en SQLite.
- [ ] **Fase 3 – Análisis con Claude:** `llm.py` con tool use y el JSON de arriba.
- [ ] **Fase 4 – Validación:** `validate.py` y pool de candidatas.
- [ ] **Fase 5 – Evaluación:** guardar los prompts y resultados de los `sample_decks/` para comparar versiones.
- [ ] **Fase 6 – Web:** FastAPI + frontend con gráficos de curva y roles.
- [ ] **Extras:** comparar dos versiones de un deck, filtro por presupuesto, combos y estimación de bracket.

## Comandos

```bash
# Entorno
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # y añadir ANTHROPIC_API_KEY

# Cargar la base de datos de cartas
python scripts/load_scryfall.py

# Analizar un deck
analyze data/sample_decks/ejemplo.txt
analyze data/sample_decks/ejemplo.txt --budget-mode ajustado --json

# Tests
pytest
```

## Convenciones

- Código y nombres en inglés; mensajes al usuario e informes en español.
- Type hints en todo y funciones puras en `metrics.py` (fáciles de testear).
- Cada métrica nueva va acompañada de su test.
- Nada de llamadas reales a la API en los tests: mockear `llm.py`.
- `data/cards.db` y `.env` van en `.gitignore`.
