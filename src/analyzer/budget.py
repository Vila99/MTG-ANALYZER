"""Selección de añadidos dentro de un presupuesto total (no por carta).

Claude ya propone los añadidos y, cuando hay varias alternativas para un
mismo corte, las ordena por preferencia; el código decide después, con
precios reales (``analyzer.prices``), cuáles entran de verdad si el
presupuesto no da para todos. Se prioriza resolver primero los problemas
de severidad ``alta``, luego ``media``, luego ``baja``; los añadidos sin
``categoria_problema`` (mejoras de sinergia, no ligadas a un problema
listado) van últimos.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from analyzer import prices as prices_module

_SEVERITY_RANK = {"alta": 0, "media": 1, "baja": 2}
_UNLINKED_RANK = 3
DEFAULT_OVERAGE = 7.5  # punto medio de "5-10€ mas, avisando"


@dataclass(frozen=True)
class BudgetSelection:
    additions: list[dict]  # cada anadido + "precio_eur" y "incluido"
    presupuesto: float
    coste_estimado: float
    supera_presupuesto: bool
    diferencia: float


def _severity_rank(categoria_problema: str | None, problem_severity: dict[str, str]) -> int:
    if categoria_problema is None:
        return _UNLINKED_RANK
    severidad = problem_severity.get(categoria_problema)
    return _SEVERITY_RANK.get(severidad, _UNLINKED_RANK)


def select_within_budget(
    additions: list[dict],
    prices: dict[str, float | None],
    problem_severity: dict[str, str],
    budget: float,
    overage: float = DEFAULT_OVERAGE,
) -> BudgetSelection:
    """Decide qué ``anadidos_sugeridos`` entran dentro de ``budget`` (+
    ``overage`` de margen, avisando si se usa). No reordena la lista de
    salida: solo añade ``precio_eur`` e ``incluido`` a cada uno."""
    order = sorted(
        range(len(additions)),
        key=lambda i: (
            _severity_rank(additions[i].get("categoria_problema"), problem_severity),
            prices.get(additions[i]["carta"]) if prices.get(additions[i]["carta"]) is not None else float("inf"),
        ),
    )

    running_total = 0.0
    included = [False] * len(additions)
    priced = [None] * len(additions)
    for i in order:
        price = prices.get(additions[i]["carta"])
        priced[i] = price
        if price is None:
            # Sin precio conocido: se muestra igualmente, no cuenta para el total.
            included[i] = True
            continue
        if running_total + price <= budget + overage:
            included[i] = True
            running_total += price

    enriched = [
        {**addition, "precio_eur": priced[i], "incluido": included[i]}
        for i, addition in enumerate(additions)
    ]
    return BudgetSelection(
        additions=enriched,
        presupuesto=budget,
        coste_estimado=round(running_total, 2),
        supera_presupuesto=running_total > budget,
        diferencia=round(running_total - budget, 2),
    )


def apply_budget_to_analysis(
    conn: sqlite3.Connection, analysis: dict, budget: float | None
) -> dict:
    """Consulta precios reales (``analyzer.prices``) para los añadidos ya
    validados y los adjunta como ``precio_eur``, se haya dado presupuesto o
    no (el precio es información útil por sí sola). Si además hay
    ``budget``, decide cuáles entran y añade el resumen ``presupuesto``."""
    additions = analysis.get("anadidos_sugeridos", [])
    if not additions:
        return analysis

    names = [addition["carta"] for addition in additions]
    prices = prices_module.fetch_prices(conn, names)

    if budget is None:
        enriched = [{**addition, "precio_eur": prices.get(addition["carta"])} for addition in additions]
        return {**analysis, "anadidos_sugeridos": enriched}

    problem_severity = {
        problema["categoria"]: problema["severidad"] for problema in analysis.get("problemas", [])
    }

    selection = select_within_budget(additions, prices, problem_severity, budget)
    return {
        **analysis,
        "anadidos_sugeridos": selection.additions,
        "presupuesto": {
            "presupuesto": selection.presupuesto,
            "coste_estimado": selection.coste_estimado,
            "supera_presupuesto": selection.supera_presupuesto,
            "diferencia": selection.diferencia,
        },
    }
