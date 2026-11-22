"""Nota simbólica (0-10) del deck en el momento del análisis.

Feedback rápido, no un juicio definitivo: combina el rubric (siempre
disponible, incluso sin pedir análisis a Claude) con la severidad de los
problemas detectados (si se pidió análisis). Código determinista, no
Claude — mismos datos de entrada, misma nota siempre.

Criterios:
- Cada rol del rubric (tierras, ramp, robo, removal, wipes) que esté
  "bajo" o "alto" resta 0.6 puntos (máximo 3.0 entre los 5).
- Cada problema que detectó Claude resta según su severidad: alta -1.2,
  media -0.6, baja -0.2 (sin tope: un deck con muchos problemas graves
  puede bajar más).
- Se parte de 10 y se recorta a [0, 10], redondeado al 0.5 más cercano.
"""

from __future__ import annotations

RUBRIC_ROLES = ("land", "ramp", "draw", "removal", "wipe")
_RUBRIC_PENALTY = 0.6
_SEVERITY_PENALTY = {"alta": 1.2, "media": 0.6, "baja": 0.2}


def compute_deck_score(
    rubric_status: dict[str, str],
    problemas: list[dict] | None = None,
) -> float:
    score = 10.0
    for role in RUBRIC_ROLES:
        if rubric_status.get(role) in ("bajo", "alto"):
            score -= _RUBRIC_PENALTY
    for problema in problemas or []:
        score -= _SEVERITY_PENALTY.get(problema.get("severidad"), 0.0)

    score = max(0.0, min(10.0, score))
    return round(score * 2) / 2
