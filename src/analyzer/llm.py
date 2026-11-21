"""Llamadas a la API de Claude.

Fase 2: respaldo de Haiku para clasificar cartas por rol cuando las reglas
de ``roles.py`` no deciden nada. Fase 3 añadirá el análisis completo del
deck con Sonnet (tool use + prompt caching, ver CLAUDE.md).

La API key solo se lee de la variable de entorno ``ANTHROPIC_API_KEY``.
Nunca se escribe en el código ni en los logs.
"""

from __future__ import annotations

import os

import anthropic

from analyzer.cards import Card
from analyzer.roles import ROLES

HAIKU_MODEL = "claude-haiku-5-5"

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
