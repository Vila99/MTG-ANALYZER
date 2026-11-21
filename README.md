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

## Estado

Fase 1 (parser, métricas y CLI sin IA) implementada. Ver la lista de fases en [CLAUDE.md](CLAUDE.md#fases).
