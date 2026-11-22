"""Orquesta el análisis con Claude: payload -> Sonnet -> validación.

Lo reutilizan ``cli.py`` (flag ``--ai``) y ``scripts/run_eval.py`` (Fase 5),
para no duplicar la secuencia payload/llamada/validación en los dos sitios.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

import anthropic

from analyzer import bracket, llm, synergy, validate
from analyzer.cards import Card


@dataclass(frozen=True)
class AnalysisRun:
    payload: dict
    raw_analysis: dict
    validated_analysis: dict


def run_analysis(
    client: anthropic.Anthropic,
    conn: sqlite3.Connection,
    commanders: list[Card],
    deck_cards: list[Card],
    card_roles: dict[str, list[str]],
    params: dict,
    candidate_pool: list[Card] | None = None,
) -> AnalysisRun:
    """Construye el payload, pide el análisis a Sonnet y lo valida.

    Se devuelven las tres etapas (payload, análisis crudo, análisis
    validado) porque ``scripts/run_eval.py`` las guarda todas para poder
    comparar versiones del prompt/rubric más adelante.
    """
    bracket_floor = bracket.compute_floor(commanders, deck_cards)
    if candidate_pool is None:
        candidate_pool = synergy.build_candidate_pool(
            conn,
            commanders,
            deck_cards,
            llm_extract=lambda commander: llm.extract_synergy_keywords_with_haiku(client, commander),
        )
    payload = llm.build_analysis_payload(
        commanders, deck_cards, card_roles, params, candidate_pool, bracket_floor
    )
    raw_analysis = llm.analyze_deck(client, payload)
    validated_analysis = validate.validate_analysis(conn, raw_analysis, commanders, deck_cards)
    return AnalysisRun(payload=payload, raw_analysis=raw_analysis, validated_analysis=validated_analysis)
