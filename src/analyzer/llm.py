"""Llamadas a la API de Claude.

Fase 2: respaldo de Haiku para clasificar cartas por rol cuando las reglas
de ``roles.py`` no deciden nada. Fase 3: análisis completo del deck con
Sonnet (tool use + prompt caching del system prompt, ver CLAUDE.md).

La API key solo se lee de la variable de entorno ``ANTHROPIC_API_KEY``.
Nunca se escribe en el código ni en los logs.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from analyzer.cards import Card
from analyzer.roles import ROLES

HAIKU_MODEL = "claude-haiku-5-5"
SONNET_MODEL = "claude-sonnet-5-5"

SYSTEM_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "system_analysis.md"
DECKBUILDING_KNOWLEDGE_PATH = (
    Path(__file__).resolve().parents[2] / "prompts" / "knowledge" / "deckbuilding.md"
)

_CLASSIFY_TOOL = {
    "name": "classify_card",
    "description": (
        "Clasifica una carta de Magic: The Gathering por su rol funcional "
        "en un deck de Commander/EDH."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "roles": {
                "type": "array",
                "items": {"type": "string", "enum": list(ROLES)},
                "description": "Uno o varios roles que describen la función de la carta.",
            }
        },
        "required": ["roles"],
    },
}


def get_client() -> anthropic.Anthropic:
    load_dotenv()  # lee .env si existe; no sobrescribe variables ya puestas en el entorno
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Falta ANTHROPIC_API_KEY en el entorno (ver .env.example).")
    return anthropic.Anthropic(api_key=api_key)


def classify_card_with_haiku(client: anthropic.Anthropic, card: Card) -> list[str]:
    """Pide a Haiku que clasifique una carta por rol.

    Solo se debe llamar cuando ``roles.classify_by_rules`` no encontró nada
    (ver ``roles.classify_card``), para no gastar llamadas en cartas que las
    reglas ya resuelven.
    """
    message = client.messages.create(
        model=HAIKU_MODEL,
        max_tokens=256,
        tools=[_CLASSIFY_TOOL],
        tool_choice={"type": "tool", "name": "classify_card"},
        messages=[
            {
                "role": "user",
                "content": (
                    f"Carta: {card.name}\n"
                    f"Tipo: {card.type_line}\n"
                    f"Texto oracle: {card.oracle_text}\n\n"
                    "Clasifica esta carta por su rol funcional en un deck de Commander."
                ),
            }
        ],
    )
    for block in message.content:
        if block.type == "tool_use" and block.name == "classify_card":
            roles = block.input.get("roles", [])
            valid_roles = [r for r in roles if r in ROLES]
            return valid_roles or ["other"]
    return ["other"]


_ANALYSIS_TOOL = {
    "name": "analyze_deck",
    "description": "Registra el análisis estructurado de un deck de Commander/EDH.",
    "input_schema": {
        "type": "object",
        "properties": {
            "estrategia_detectada": {"type": "string"},
            "arquetipo": {"type": "string"},
            "puntos_fuertes": {"type": "array", "items": {"type": "string"}},
            "problemas": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "categoria": {"type": "string"},
                        "severidad": {"type": "string", "enum": ["alta", "media", "baja"]},
                        "explicacion": {"type": "string"},
                    },
                    "required": ["categoria", "severidad", "explicacion"],
                },
            },
            "cortes_sugeridos": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "carta": {"type": "string"},
                        "motivo": {"type": "string"},
                    },
                    "required": ["carta", "motivo"],
                },
            },
            "anadidos_sugeridos": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "carta": {"type": "string"},
                        "rol": {"type": "string"},
                        "reemplaza_a": {"type": ["string", "null"]},
                        "motivo": {"type": "string"},
                    },
                    "required": ["carta", "rol", "motivo"],
                },
            },
        },
        "required": [
            "estrategia_detectada",
            "arquetipo",
            "puntos_fuertes",
            "problemas",
            "cortes_sugeridos",
            "anadidos_sugeridos",
        ],
    },
}


def load_system_prompt() -> str:
    """Contrato de análisis (``system_analysis.md``) + el marco de criterios
    de construcción de decks (``prompts/knowledge/deckbuilding.md``), que
    sustituye al rubric fijo por uno condicional al plan del deck y al
    bracket. Se concatenan en un solo bloque de texto cacheado."""
    parts = [SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")]
    if DECKBUILDING_KNOWLEDGE_PATH.exists():
        parts.append(DECKBUILDING_KNOWLEDGE_PATH.read_text(encoding="utf-8"))
    return "\n\n---\n\n".join(parts)


def build_analysis_payload(
    commanders: list[Card],
    deck_cards: list[Card],
    card_roles: dict[str, list[str]],
    params: dict,
    candidate_pool: list[Card] | None = None,
) -> dict:
    """Construye el JSON de entrada para ``analyze_deck``: comandante(s) con
    su texto oracle, métricas calculadas, cartas con su rol y texto, los
    parámetros del usuario y, opcionalmente, un pool de candidatas."""
    from analyzer import metrics

    card_counts: dict[str, int] = {}
    unique_cards: dict[str, Card] = {}
    for card in deck_cards:
        card_counts[card.name] = card_counts.get(card.name, 0) + 1
        unique_cards.setdefault(card.name, card)

    return {
        "comandantes": [
            {
                "nombre": c.name,
                "identidad_color": c.color_identity,
                "texto_oracle": c.oracle_text,
            }
            for c in commanders
        ],
        "metricas": {
            "tamano_deck": metrics.deck_size(deck_cards, commanders),
            "tierras": metrics.count_lands(deck_cards),
            "cmc_medio": round(metrics.average_cmc(deck_cards), 2),
            "curva_mana": metrics.mana_curve(deck_cards),
            "pips": metrics.color_pips(deck_cards),
            "fuentes_mana": metrics.mana_sources(deck_cards),
        },
        "cartas": [
            {
                "nombre": name,
                "cantidad": count,
                "roles": card_roles.get(name, []),
                "texto_oracle": unique_cards[name].oracle_text,
            }
            for name, count in card_counts.items()
        ],
        "parametros_usuario": params,
        "pool_candidatas": [
            {"nombre": c.name, "texto_oracle": c.oracle_text} for c in (candidate_pool or [])
        ],
    }


def analyze_deck(client: anthropic.Anthropic, payload: dict) -> dict:
    """Pide a Sonnet el análisis completo del deck.

    El system prompt (con el rubric) va con ``cache_control`` para
    aprovechar el prompt caching entre análisis sucesivos.
    """
    message = client.messages.create(
        model=SONNET_MODEL,
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": load_system_prompt(),
                "cache_control": {"type": "ephemeral"},
            }
        ],
        tools=[_ANALYSIS_TOOL],
        tool_choice={"type": "tool", "name": "analyze_deck"},
        messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
    )
    for block in message.content:
        if block.type == "tool_use" and block.name == "analyze_deck":
            return block.input
    raise RuntimeError("Claude no devolvió el análisis esperado vía tool use.")
