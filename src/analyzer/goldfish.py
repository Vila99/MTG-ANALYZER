"""Goldfish estadístico: Monte Carlo sin rivales bajo una política de juego
fija e ingenua (sin razonamiento real), para sacar estadísticas de
consistencia de maná/curva que las heurísticas estáticas de ``metrics.py``
no capturan (varianza real de la mano, no solo el ratio teórico de pips).

Simplificaciones explícitas (no son el comportamiento real de una partida):
- El maná genérico de una rampa no-tierra está disponible a partir del
  turno siguiente a cuando se lanza, no en el mismo turno.
- Una rampa no-tierra aporta +1 maná genérico de aproximación (no se
  parsea el texto oracle para la cantidad exacta).
- Disponibilidad de color: binaria (hay o no hay una fuente de ese color
  en juego, usando ``produced_mana``), no un recuento de pips.
- Como mucho una tierra y un hechizo por turno (sin encadenar varias
  rampas el mismo turno); se prioriza la rampa más barata que se pueda
  pagar antes que cualquier otro hechizo.
- El comandante no se "lanza" de verdad (no resta maná ni ocupa el turno
  de la política): se mide si *se podría* lanzar ese turno con el maná y
  los colores ya en juego, no una secuencia completa de turno.
- Mulligan simplificado: una mano de 7 con menos de 2 o más de 5 tierras
  se descarta y se roba otra de 7 (sin "poner N abajo"), hasta 2 veces.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from analyzer.cards import Card

DEFAULT_TURNS = 12
MIN_LAND_HAND = 2
MAX_LAND_HAND = 5
MAX_MULLIGANS = 2


@dataclass(frozen=True)
class SimCard:
    name: str
    cmc: float
    is_land: bool
    is_ramp: bool
    produced_mana: tuple[str, ...]


def build_sim_deck(deck_cards: list[Card], card_roles: dict[str, list[str]]) -> list[SimCard]:
    """Proyección ligera de las cartas del deck para simular, reutilizando
    el rol ``ramp`` ya clasificado por ``roles.classify_cards`` (sin Haiku:
    la caché ya está caliente porque este botón solo aparece tras un
    ``/analyze`` que ya clasificó esas mismas cartas)."""
    sim_cards = []
    for card in deck_cards:
        roles = card_roles.get(card.name, [])
        sim_cards.append(
            SimCard(
                name=card.name,
                cmc=card.cmc,
                is_land=card.is_land,
                is_ramp=(not card.is_land) and "ramp" in roles,
                produced_mana=tuple(card.produced_mana),
            )
        )
    return sim_cards


@dataclass(frozen=True)
class GameResult:
    comandante_turno: int | None
    primera_rampa_turno: int | None
    tierras_turno_3: int
    colores_en_juego_turno_4: frozenset[str]
    mana_por_turno: tuple[int, ...]
    mulligans: int


def _draw_opening_hand(
    deck: list[SimCard], rng: random.Random
) -> tuple[list[SimCard], list[SimCard], int]:
    """Baraja y aplica el mulligan simplificado. Devuelve (mano, biblioteca,
    número de mulligans hechos)."""
    mulligans = 0
    while True:
        shuffled = deck[:]
        rng.shuffle(shuffled)
        hand = shuffled[:7]
        library = shuffled[7:]
        land_count = sum(1 for c in hand if c.is_land)
        if MIN_LAND_HAND <= land_count <= MAX_LAND_HAND or mulligans >= MAX_MULLIGANS:
            return hand, library, mulligans
        mulligans += 1


def simulate_one_game(
    deck: list[SimCard],
    commander_identity: set[str],
    commander_cmc: float,
    rng: random.Random,
    turns: int = DEFAULT_TURNS,
) -> GameResult:
    hand, library, mulligans = _draw_opening_hand(deck, rng)

    lands_in_play = 0
    ramp_mana_online = 0
    pending_ramp_mana = 0
    colors_available: set[str] = set()

    comandante_turno: int | None = None
    primera_rampa_turno: int | None = None
    tierras_turno_3 = 0
    colores_en_juego_turno_4: frozenset[str] = frozenset()
    mana_por_turno: list[int] = []

    for turn in range(1, turns + 1):
        ramp_mana_online += pending_ramp_mana
        pending_ramp_mana = 0

        if turn > 1 and library:
            hand.append(library.pop())

        for i, card in enumerate(hand):
            if card.is_land:
                hand.pop(i)
                lands_in_play += 1
                colors_available |= set(card.produced_mana)
                break

        mana_total = lands_in_play + ramp_mana_online
        mana_por_turno.append(mana_total)
        if turn == 3:
            tierras_turno_3 = lands_in_play

        castable_ramp = sorted(
            (c for c in hand if c.is_ramp and c.cmc <= mana_total), key=lambda c: c.cmc
        )
        chosen = castable_ramp[0] if castable_ramp else None
        if chosen is None:
            castable_other = sorted(
                (c for c in hand if not c.is_land and not c.is_ramp and c.cmc <= mana_total),
                key=lambda c: c.cmc,
            )
            chosen = castable_other[0] if castable_other else None

        if chosen is not None:
            hand.remove(chosen)
            if chosen.is_ramp:
                pending_ramp_mana += 1
                colors_available |= set(chosen.produced_mana)
                if primera_rampa_turno is None:
                    primera_rampa_turno = turn

        if (
            comandante_turno is None
            and mana_total >= commander_cmc
            and commander_identity.issubset(colors_available)
        ):
            comandante_turno = turn

        if turn == 4:
            colores_en_juego_turno_4 = frozenset(colors_available & commander_identity)

    return GameResult(
        comandante_turno=comandante_turno,
        primera_rampa_turno=primera_rampa_turno,
        tierras_turno_3=tierras_turno_3,
        colores_en_juego_turno_4=colores_en_juego_turno_4,
        mana_por_turno=tuple(mana_por_turno),
        mulligans=mulligans,
    )


def run_monte_carlo(
    deck_cards: list[Card],
    card_roles: dict[str, list[str]],
    commanders: list[Card],
    n_sims: int = 10000,
    seed: int | None = None,
    turns: int = DEFAULT_TURNS,
) -> dict:
    """Corre ``n_sims`` partidas y agrega las estadísticas. Pasar ``seed``
    hace la corrida reproducible (los tests siempre lo hacen)."""
    if n_sims <= 0:
        raise ValueError("n_sims debe ser positivo")

    sim_deck = build_sim_deck(deck_cards, card_roles)
    commander_identity: set[str] = set()
    for commander in commanders:
        commander_identity |= set(commander.color_identity)
    commander_cmc = sum(commander.cmc for commander in commanders)

    rng = random.Random(seed)
    results = [
        simulate_one_game(sim_deck, commander_identity, commander_cmc, rng, turns)
        for _ in range(n_sims)
    ]

    turnos_comandante = [r.comandante_turno for r in results if r.comandante_turno is not None]
    turnos_rampa = [r.primera_rampa_turno for r in results if r.primera_rampa_turno is not None]

    por_turno_comandante = {
        str(t): round(
            sum(1 for turno in turnos_comandante if turno <= t) / n_sims, 4
        )
        for t in range(1, turns + 1)
    }
    por_turno_rampa = {
        str(t): round(sum(1 for turno in turnos_rampa if turno <= t) / n_sims, 4)
        for t in range(1, turns + 1)
    }
    curva_mana_media = {
        str(t): round(sum(r.mana_por_turno[t - 1] for r in results) / n_sims, 2)
        for t in range(1, turns + 1)
    }

    stats: dict = {
        "simulaciones": n_sims,
        "turno_comandante_lanzable": {
            "media": round(sum(turnos_comandante) / len(turnos_comandante), 2)
            if turnos_comandante
            else None,
            "por_turno": por_turno_comandante,
            "nunca_pct": round(1 - len(turnos_comandante) / n_sims, 4),
        },
        "prob_mana_screw_turno_3": round(
            sum(1 for r in results if r.tierras_turno_3 < MIN_LAND_HAND) / n_sims, 4
        ),
        "primera_rampa": {
            "media": round(sum(turnos_rampa) / len(turnos_rampa), 2) if turnos_rampa else None,
            "por_turno": por_turno_rampa,
        },
        "curva_mana_media": curva_mana_media,
        "prob_mulligan": round(sum(1 for r in results if r.mulligans > 0) / n_sims, 4),
    }
    if commander_identity:
        stats["colores_disponibles_turno_4"] = {
            color: round(
                sum(1 for r in results if color in r.colores_en_juego_turno_4) / n_sims, 4
            )
            for color in sorted(commander_identity)
        }
    return stats
