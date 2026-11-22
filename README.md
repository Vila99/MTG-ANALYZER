# MTG Commander Deck Analyzer

Analiza decks de Magic: The Gathering (Commander/EDH) y, con ayuda de Claude, propone mejoras según criterios configurables.

Ver [CLAUDE.md](CLAUDE.md) para la arquitectura, el flujo del análisis y las fases del proyecto.

## Uso rápido

```bash
python -m venv .venv
source .venv/bin/activate   # en Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env        # y añade tu ANTHROPIC_API_KEY

python scripts/load_scryfall.py          # descarga y carga data/cards.db
analyze data/sample_decks/atraxa_sample.txt

pytest
```

## Web (API + frontend)

```bash
# Backend (FastAPI) — desde la raíz del repo, con el venv activado
uvicorn analyzer.api:app --reload
# API en http://localhost:8000 (docs interactivas en /docs)

# Frontend (Next.js) — en otra terminal
cd web
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
# App en http://localhost:3000
```

El backend solo acepta peticiones del origen en `FRONTEND_ORIGIN` (por defecto `http://localhost:3000`); cambia la variable de entorno si sirves el frontend desde otro origen.

## Evaluación (Fase 5)

```bash
python scripts/run_eval.py                 # analiza todos los decks de data/sample_decks/ con Claude
python scripts/compare_eval.py <run1.json> <run2.json>   # compara dos corridas guardadas
```

Requiere `ANTHROPIC_API_KEY`. Los resultados se guardan en `data/eval_runs/<deck>/<timestamp>.json` (no se versionan).

## Estado

Fases 1-6 del roadmap implementadas (ver [CLAUDE.md](CLAUDE.md#fases)): parser, métricas y CLI; clasificación por rol; análisis con Claude (Sonnet, tool use); validación de sugerencias; script de evaluación; API FastAPI + frontend Next.js/Recharts. Ninguna llamada real a `ANTHROPIC_API_KEY` se ha hecho todavía — se deja para cuando se configure la key.
