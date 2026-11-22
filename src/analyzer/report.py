"""Formatea los resultados del análisis como texto para la terminal."""

from __future__ import annotations

from analyzer.cards import Card
from analyzer import metrics, scoring

_COLOR_NAMES = {"W": "Blanco", "U": "Azul", "B": "Negro", "R": "Rojo", "G": "Verde"}
_ROLE_NAMES = {
    "land": "Tierras",
    "ramp": "Ramp",
    "draw": "Robo de cartas",
    "removal": "Removal puntual",
    "wipe": "Wipes",
    "protection": "Protección",
    "tutor": "Tutores",
    "wincon": "Condiciones de victoria",
    "synergy": "Sinergia",
    "other": "Sin clasificar",
}
_RUBRIC_STATUS_LABEL = {"bajo": "bajo", "ok": "dentro de rango", "alto": "alto"}


def cards_by_role(card_roles: dict[str, list[str]]) -> dict[str, list[str]]:
    """Invierte nombre -> roles en rol -> nombres (sin duplicados, en orden
    de aparición), para poder enseñar qué cartas concretas cuenta cada
    barra de "cartas por rol"."""
    by_role: dict[str, list[str]] = {}
    for name, roles in card_roles.items():
        for role in roles:
            names = by_role.setdefault(role, [])
            if name not in names:
                names.append(name)
    return by_role


def build_summary(
    commanders: list[Card],
    deck_cards: list[Card],
    missing: list[str],
    role_counts: dict[str, int],
    rubric_status: dict[str, str],
    card_roles: dict[str, list[str]] | None = None,
    problemas: list[dict] | None = None,
) -> dict:
    """Resumen del análisis en forma de dict (para ``--json`` y la API web)."""
    summary = {
        "comandantes": [c.name for c in commanders],
        "tamano_deck": metrics.deck_size(deck_cards, commanders),
        "tierras": metrics.count_lands(deck_cards),
        "cmc_medio": round(metrics.average_cmc(deck_cards), 2),
        "curva_mana": metrics.mana_curve(deck_cards),
        "pips": metrics.color_pips(deck_cards),
        "fuentes_mana": metrics.mana_sources(deck_cards),
        "no_legales": [c.name for c in metrics.illegal_cards(deck_cards)],
        "no_encontradas": missing,
        "roles": role_counts,
        "rubric": rubric_status,
        "nota_deck": scoring.compute_deck_score(rubric_status, problemas),
    }
    if card_roles is not None:
        summary["cartas_por_rol"] = cards_by_role(card_roles)
    return summary


def render(
    commanders: list[Card],
    deck_cards: list[Card],
    missing: list[str],
    role_counts: dict[str, int] | None = None,
    rubric_status: dict[str, str] | None = None,
) -> str:
    lines: list[str] = []

    lines.append("=== Comandante(s) ===")
    if commanders:
        for card in commanders:
            identity = "".join(card.color_identity) or "Incoloro"
            lines.append(f"  - {card.name} ({identity})")
    else:
        lines.append("  (no se detectó comandante)")

    total = metrics.deck_size(deck_cards, commanders)
    lines.append("")
    lines.append(f"=== Tamaño del deck: {total} cartas ===")

    lands = metrics.count_lands(deck_cards)
    lines.append("")
    lines.append(f"Tierras: {lands}")

    curve = metrics.mana_curve(deck_cards)
    avg_cmc = metrics.average_cmc(deck_cards)
    lines.append("")
    lines.append(f"Curva de maná (sin tierras, CMC medio {avg_cmc:.2f}):")
    for cmc, count in curve.items():
        lines.append(f"  {cmc}: {'#' * count} ({count})")

    pips = metrics.color_pips(deck_cards)
    sources = metrics.mana_sources(deck_cards)
    lines.append("")
    lines.append("Pips vs. fuentes de maná por color:")
    for color in ("W", "U", "B", "R", "G"):
        lines.append(
            f"  {_COLOR_NAMES[color]}: {pips.get(color, 0)} pips / {sources.get(color, 0)} fuentes"
        )

    if role_counts is not None:
        lines.append("")
        lines.append("=== Roles (por reglas; 'sin clasificar' puede necesitar revisión con Haiku) ===")
        for role in ("ramp", "draw", "removal", "wipe", "tutor", "protection", "synergy", "wincon", "other"):
            count = role_counts.get(role, 0)
            if count:
                lines.append(f"  {_ROLE_NAMES[role]}: {count}")

    if rubric_status is not None:
        lines.append("")
        lines.append("=== Comparación con el rubric base ===")
        for role, status in rubric_status.items():
            count = role_counts.get(role, 0) if role_counts else 0
            lines.append(f"  {_ROLE_NAMES[role]}: {count} ({_RUBRIC_STATUS_LABEL[status]})")

    commander_identity = set()
    for card in commanders:
        commander_identity |= set(card.color_identity)
    if commander_identity:
        violations = metrics.color_identity_violations(deck_cards, commander_identity)
        if violations:
            lines.append("")
            lines.append("Fuera de la identidad de color del comandante:")
            for card in violations:
                lines.append(f"  - {card.name} ({''.join(card.color_identity)})")

    illegal = metrics.illegal_cards(deck_cards, "commander")
    if illegal:
        lines.append("")
        lines.append("No legales en Commander:")
        for card in illegal:
            lines.append(f"  - {card.name}")

    if missing:
        lines.append("")
        lines.append("No encontradas en la base de datos de cartas:")
        for name in missing:
            lines.append(f"  - {name}")

    return "\n".join(lines)


def render_analysis(analysis: dict) -> str:
    """Formatea el análisis de Claude (ya validado) para la terminal."""
    lines: list[str] = []

    lines.append("=== Análisis de Claude ===")
    lines.append(f"Estrategia detectada: {analysis.get('estrategia_detectada', '')}")
    lines.append(f"Arquetipo: {analysis.get('arquetipo', '')}")

    puntos_fuertes = analysis.get("puntos_fuertes") or []
    if puntos_fuertes:
        lines.append("")
        lines.append("Puntos fuertes:")
        for punto in puntos_fuertes:
            lines.append(f"  - {punto}")

    problemas = analysis.get("problemas") or []
    if problemas:
        lines.append("")
        lines.append("Problemas detectados:")
        for problema in problemas:
            lines.append(
                f"  [{problema['severidad']}] {problema['categoria']}: {problema['explicacion']}"
            )

    cortes = analysis.get("cortes_sugeridos") or []
    if cortes:
        lines.append("")
        lines.append("Cortes sugeridos:")
        for cut in cortes:
            lines.append(f"  - {cut['carta']}: {cut['motivo']}")

    añadidos = analysis.get("anadidos_sugeridos") or []
    if añadidos:
        lines.append("")
        lines.append("Añadidos sugeridos:")
        for addition in añadidos:
            reemplazo = f" (reemplaza a {addition['reemplaza_a']})" if addition.get("reemplaza_a") else ""
            lines.append(f"  - {addition['carta']} [{addition['rol']}]{reemplazo}: {addition['motivo']}")

    return "\n".join(lines)
