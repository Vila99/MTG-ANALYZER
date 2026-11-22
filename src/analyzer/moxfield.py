"""Importa un deck directamente desde una URL de Moxfield, para no tener
que pegar la lista a mano.

Moxfield no publica una API oficial/documentada. El endpoint de abajo es
el que usa la propia web (confirmado en vivo) y el que usan varios
proyectos de la comunidad (p. ej. MarioMH8/moxfield-api, moxtrice) para
lo mismo: puede cambiar sin aviso, así que cualquier fallo de red o de
forma de la respuesta se traduce en un ``ValueError`` legible, nunca en
una excepción cruda.
"""

from __future__ import annotations

import re

import requests

from analyzer.parser import DeckEntry, ParsedDeck

MOXFIELD_API_URL = "https://api2.moxfield.com/v2/decks/all/{public_id}"
# Moxfield bloquea peticiones sin un User-Agent de navegador normal.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

_DECK_ID_IN_URL_RE = re.compile(r"moxfield\.com/decks/([A-Za-z0-9_-]+)", re.IGNORECASE)


def extract_deck_id(url_or_id: str) -> str:
    """Acepta una URL completa de Moxfield o ya el id del deck a secas."""
    match = _DECK_ID_IN_URL_RE.search(url_or_id)
    if match:
        return match.group(1)
    return url_or_id.strip().strip("/")


def fetch_moxfield_deck(url_or_id: str) -> ParsedDeck:
    """Descarga un deck público de Moxfield y lo devuelve como ``ParsedDeck``,
    igual que si se hubiera pegado la lista a mano con ``parse_decklist``."""
    deck_id = extract_deck_id(url_or_id)
    if not deck_id:
        raise ValueError("No se reconoce esa URL de Moxfield.")

    try:
        response = requests.get(
            MOXFIELD_API_URL.format(public_id=deck_id),
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )
    except requests.RequestException as exc:
        raise ValueError(f"No se pudo contactar con Moxfield: {exc}") from exc

    if response.status_code == 404:
        raise ValueError("No se encontró ese deck en Moxfield (¿es público?).")
    if not response.ok:
        raise ValueError(f"Moxfield respondió con un error ({response.status_code}).")

    try:
        data = response.json()
    except ValueError as exc:
        raise ValueError("Moxfield no devolvió un deck válido.") from exc

    commanders = list((data.get("commanders") or {}).keys())
    mainboard = data.get("mainboard") or {}
    cards = [
        DeckEntry(quantity=entry.get("quantity", 1), name=name)
        for name, entry in mainboard.items()
    ]

    if not commanders and not cards:
        raise ValueError("Ese deck de Moxfield no tiene cartas (¿la URL es correcta?).")

    return ParsedDeck(commanders=commanders, cards=cards)
