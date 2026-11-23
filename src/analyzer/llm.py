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
BRACKETS_KNOWLEDGE_PATH = Path(__file__).resolve().parents[2] / "prompts" / "knowledge" / "brackets.md"
INTERACTIONS_KNOWLEDGE_PATH = (
    Path(__file__).resolve().parents[2] / "prompts" / "knowledge" / "interactions.md"
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


_SYNERGY_KEYWORDS_TOOL = {
    "name": "extract_synergy_keywords",
    "description": (
        "Extrae palabras o frases cortas del texto oracle de un comandante que "
        "describan sus mecánicas principales, para buscar cartas que las "
        "compartan literalmente en su propio texto oracle."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "keywords": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "maxItems": 6,
                "description": (
                    "3-6 palabras o frases de 1-3 palabras (en inglés, tal cual "
                    "aparecerían en el texto oracle de otra carta: 'token', "
                    "'sacrifice', 'graveyard', 'enchantment', '+1/+1 counter'...). "
                    "Nunca nombres de carta ni frases largas."
                ),
            }
        },
        "required": ["keywords"],
    },
}


def extract_synergy_keywords_with_haiku(client: anthropic.Anthropic, commander: Card) -> list[str]:
    """Pide a Haiku 3-6 palabras clave mecánicas del texto oracle del
    comandante (p. ej. "token", "sacrifice", "graveyard"), para buscar
    después cartas que las compartan de verdad (ver ``analyzer.synergy``).

    Es una extracción interpretativa barata (Haiku), no una búsqueda: la
    búsqueda real sobre las cartas es SQL determinista, no de Claude.
    """
    message = client.messages.create(
        model=HAIKU_MODEL,
        max_tokens=256,
        tools=[_SYNERGY_KEYWORDS_TOOL],
        tool_choice={"type": "tool", "name": "extract_synergy_keywords"},
        messages=[
            {
                "role": "user",
                "content": (
                    f"Comandante: {commander.name}\n"
                    f"Texto oracle: {commander.oracle_text}\n\n"
                    "Extrae las palabras clave mecánicas de este comandante."
                ),
            }
        ],
    )
    for block in message.content:
        if block.type == "tool_use" and block.name == "extract_synergy_keywords":
            keywords = block.input.get("keywords", [])
            return [k for k in keywords if isinstance(k, str) and k.strip()]
    return []


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
                    "additionalProperties": False,
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
                    "additionalProperties": False,
                },
            },
            "anadidos_sugeridos": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "carta": {"type": "string"},
                        "rol": {"type": "string"},
                        "reemplaza_a": {
                            "anyOf": [{"type": "string"}, {"type": "null"}],
                            "description": (
                                "Nombre de la carta a la que reemplaza, o null si no "
                                "reemplaza ninguna en concreto."
                            ),
                        },
                        "categoria_problema": {
                            "anyOf": [{"type": "string"}, {"type": "null"}],
                            "description": (
                                "La `categoria` exacta (tal cual aparece en `problemas`) del "
                                "problema que este añadido soluciona, o null si no soluciona "
                                "ninguno en concreto (p. ej. es una mejora de sinergia)."
                            ),
                        },
                        "motivo": {"type": "string"},
                    },
                    "required": ["carta", "rol", "reemplaza_a", "categoria_problema", "motivo"],
                    "additionalProperties": False,
                },
            },
            "bracket": {
                "type": "object",
                "description": (
                    "Ver prompts/knowledge/brackets.md. 'suelo' y 'game_changers' "
                    "deben coincidir con los datos ya calculados que recibes en "
                    "'bracket_suelo'; no los recalcules de memoria."
                ),
                "properties": {
                    "deducido": {"type": "integer"},
                    "confianza": {"type": "string", "enum": ["alta", "media", "baja"]},
                    "suelo": {"type": "integer"},
                    "estimacion_juego": {"type": "integer"},
                    "game_changers": {"type": "array", "items": {"type": "string"}},
                    "senales_duras": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "tipo": {"type": "string"},
                                "detalle": {"type": "string"},
                            },
                            "required": ["tipo", "detalle"],
                            "additionalProperties": False,
                        },
                    },
                    "razones": {"type": "array", "items": {"type": "string"}},
                    "que_lo_moveria": {
                        "type": "object",
                        "properties": {
                            "bajar": {"type": "array", "items": {"type": "string"}},
                            "subir": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["bajar", "subir"],
                        "additionalProperties": False,
                    },
                },
                "required": [
                    "deducido",
                    "confianza",
                    "suelo",
                    "estimacion_juego",
                    "game_changers",
                    "senales_duras",
                    "razones",
                    "que_lo_moveria",
                ],
                "additionalProperties": False,
            },
        },
        "required": [
            "estrategia_detectada",
            "arquetipo",
            "puntos_fuertes",
            "problemas",
            "cortes_sugeridos",
            "anadidos_sugeridos",
            "bracket",
        ],
        "additionalProperties": False,
    },
    # Sonnet 5.5 ya no acepta tool_choice forzado ("tool"/"any"): se pide con
    # strict tool use + tool_choice "auto" en su lugar (ver analyze_deck).
    "strict": True,
}


def load_system_prompt() -> str:
    """Contrato de análisis (``system_analysis.md``) + el marco de criterios
    de construcción de decks (``prompts/knowledge/deckbuilding.md``), que
    sustituye al rubric fijo por uno condicional al plan del deck y al
    bracket, + las interacciones no obvias entre mecánicas
    (``prompts/knowledge/interactions.md``), para que Claude no tenga que
    reinventar cada vez implicaciones de reglas que no están escritas
    literalmente en el texto de las cartas. Se concatenan en un solo bloque
    de texto cacheado."""
    parts = [SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")]
    for path in (DECKBUILDING_KNOWLEDGE_PATH, BRACKETS_KNOWLEDGE_PATH, INTERACTIONS_KNOWLEDGE_PATH):
        if path.exists():
            parts.append(path.read_text(encoding="utf-8"))
    return "\n\n---\n\n".join(parts)


def build_analysis_payload(
    commanders: list[Card],
    deck_cards: list[Card],
    card_roles: dict[str, list[str]],
    params: dict,
    candidate_pool: list[Card] | None = None,
    bracket_floor: dict | None = None,
) -> dict:
    """Construye el JSON de entrada para ``analyze_deck``: comandante(s) con
    su texto oracle, métricas calculadas, cartas con su rol y texto, los
    parámetros del usuario (incluida ``description``, la idea del jugador
    para el deck, si la dio) y, opcionalmente, un pool de candidatas y el
    suelo de bracket ya calculado (ver ``analyzer.bracket.compute_floor``)."""
    from analyzer import metrics

    card_counts: dict[str, int] = {}
    unique_cards: dict[str, Card] = {}
    for card in deck_cards:
        card_counts[card.name] = card_counts.get(card.name, 0) + 1
        unique_cards.setdefault(card.name, card)

    payload = {
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
    if bracket_floor is not None:
        payload["bracket_suelo"] = bracket_floor
    return payload


def analyze_deck(client: anthropic.Anthropic, payload: dict) -> dict:
    """Pide a Sonnet el análisis completo del deck.

    El system prompt (con el rubric) va con ``cache_control`` para
    aprovechar el prompt caching entre análisis sucesivos.

    Sonnet 5.5 no acepta ``tool_choice`` forzado (``"tool"``/``"any"``): se
    usa ``strict`` tool use (ver ``_ANALYSIS_TOOL``) con ``tool_choice``
    ``"auto"``, pidiendo explícitamente en el mensaje que use la
    herramienta. ``max_tokens`` y el nivel de esfuerzo son generosos porque
    Sonnet 5.5 piensa (``thinking`` adaptativo) antes de responder, y ese
    razonamiento también consume el presupuesto de tokens de salida.
    """
    message = client.messages.create(
        model=SONNET_MODEL,
        max_tokens=16000,
        output_config={"effort": "high"},
        system=[
            {
                "type": "text",
                "text": load_system_prompt(),
                "cache_control": {"type": "ephemeral"},
            }
        ],
        tools=[_ANALYSIS_TOOL],
        tool_choice={"type": "auto"},
        messages=[
            {
                "role": "user",
                "content": (
                    json.dumps(payload, ensure_ascii=False)
                    + "\n\nUsa la herramienta analyze_deck para responder con el análisis."
                ),
            }
        ],
    )
    for block in message.content:
        if block.type == "tool_use" and block.name == "analyze_deck":
            return block.input
    raise RuntimeError("Claude no devolvió el análisis esperado vía tool use.")
