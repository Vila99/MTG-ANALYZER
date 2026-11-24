"""Anota el precio real de las candidatas sugeridas por Claude.

``budget_mode`` ya no es un importe fijo: es solo una preferencia
(``"ajustado"`` o ``"libre"``). El código no recorta nada por precio, solo
consulta el precio real (``analyzer.prices``) para mostrarlo y, si el modo
es ``"ajustado"``, reordena las candidatas de cada problema de más barata a
más cara (Claude no calcula precios exactos, ver ``prompts/system_analysis.md``).
"""

from __future__ import annotations

import sqlite3

from analyzer import prices as prices_module


def annotate_prices(
    conn: sqlite3.Connection, analysis: dict, budget_mode: str | None
) -> dict:
    """Añade ``precio_eur`` a cada candidata de ``problemas[*].candidatas_sugeridas``.

    Si ``budget_mode == "ajustado"``, además reordena las candidatas de cada
    problema de más barata a más cara (las sin precio conocido van al
    final, en el orden en que las propuso Claude)."""
    problemas = analysis.get("problemas", [])
    if not problemas:
        return analysis

    names = [
        candidata["carta"]
        for problema in problemas
        for candidata in problema.get("candidatas_sugeridas", [])
    ]
    prices = prices_module.fetch_prices(conn, names) if names else {}

    def _sort_key(candidata: dict) -> float:
        price = prices.get(candidata["carta"])
        return price if price is not None else float("inf")

    annotated_problemas = []
    for problema in problemas:
        candidatas = [
            {**candidata, "precio_eur": prices.get(candidata["carta"])}
            for candidata in problema.get("candidatas_sugeridas", [])
        ]
        if budget_mode == "ajustado":
            candidatas = sorted(candidatas, key=_sort_key)
        annotated_problemas.append({**problema, "candidatas_sugeridas": candidatas})

    return {**analysis, "problemas": annotated_problemas}
