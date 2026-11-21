"""Parsea listas de deck en texto plano a nombres normalizados + comandante(s).

Formatos soportados (los habituales al exportar desde Moxfield, Archidekt,
EDHREC o escritos a mano):

    1 Sol Ring
    1x Atraxa, Praetors' Voice *CMDR*
    Commander:
    1 Atraxa, Praetors' Voice
    Deck:
    1 Sol Ring
    // comentario
    1 Arid Mesa (MH2) 123

No se consulta la base de datos de cartas aquí: solo se extraen cantidades,
nombres y qué entradas son el/los comandante(s).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_SECTION_HEADERS = {
    "commander": "commander",
    "commanders": "commander",
    "deck": "deck",
    "mainboard": "deck",
    "maybeboard": "ignore",
    "sideboard": "ignore",
    "considering": "ignore",
}

_QUANTITY_RE = re.compile(r"^(\d+)\s*x?\s+(.+)$", re.IGNORECASE)
_INLINE_COMMANDER_TAG_RE = re.compile(
    r"\s*(\*cmdr\*|\[commander\]|\(commander\))\s*$", re.IGNORECASE
)
_SET_COLLECTOR_SUFFIX_RE = re.compile(
    r"\s*\([A-Za-z0-9]{2,5}\)\s*(?:[A-Za-z0-9]+)?\s*$"
)
_FOIL_TAG_RE = re.compile(r"\s*\*[A-Za-z]\*\s*$")


@dataclass(frozen=True)
class DeckEntry:
    quantity: int
    name: str


@dataclass
class ParsedDeck:
    commanders: list[str] = field(default_factory=list)
    cards: list[DeckEntry] = field(default_factory=list)


def _clean_name(name: str) -> str:
    name = name.strip()
    name = _FOIL_TAG_RE.sub("", name)
    name = _SET_COLLECTOR_SUFFIX_RE.sub("", name)
    return name.strip()


def _section_for_header(line: str) -> str | None:
    header = line.strip().rstrip(":").strip().lower()
    return _SECTION_HEADERS.get(header)


def parse_decklist(text: str) -> ParsedDeck:
    """Convierte el texto de una lista de deck en un ``ParsedDeck``.

    Las líneas vacías y los comentarios (``#`` o ``//``) se ignoran. Las
    entradas en una sección "maybeboard"/"sideboard" se descartan.
    """
    deck = ParsedDeck()
    section = "deck"

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue

        new_section = _section_for_header(line)
        if new_section is not None:
            section = new_section
            continue

        if section == "ignore":
            continue

        is_commander = bool(_INLINE_COMMANDER_TAG_RE.search(line))
        line = _INLINE_COMMANDER_TAG_RE.sub("", line)

        match = _QUANTITY_RE.match(line)
        if match:
            quantity = int(match.group(1))
            name = _clean_name(match.group(2))
        else:
            quantity = 1
            name = _clean_name(line)

        if not name:
            continue

        if is_commander or section == "commander":
            if name not in deck.commanders:
                deck.commanders.append(name)
        else:
            deck.cards.append(DeckEntry(quantity=quantity, name=name))

    return deck
