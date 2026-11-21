"""Rubric base (configurable): rangos de referencia para un deck "estándar".

Ver la tabla en CLAUDE.md. Pensado para que ``rubric.py`` pueda ajustar
estos rangos según el arquetipo detectado en fases futuras; por ahora
expone el rubric base sin ajustar.
"""

from __future__ import annotations

from dataclasses import dataclass

AVG_CMC_TARGET = 3.0


@dataclass(frozen=True)
class RoleRange:
    minimum: int | None
    maximum: int | None

    def status(self, count: int) -> str:
        if self.minimum is not None and count < self.minimum:
            return "bajo"
        if self.maximum is not None and count > self.maximum:
            return "alto"
        return "ok"


BASE_RUBRIC: dict[str, RoleRange] = {
    "land": RoleRange(35, 38),
    "ramp": RoleRange(10, 12),
    "draw": RoleRange(10, None),
    "removal": RoleRange(8, 10),
    "wipe": RoleRange(2, 4),
}


def evaluate_role_counts(role_counts: dict[str, int]) -> dict[str, str]:
    """Compara los conteos de roles contra el rubric base.

    Devuelve, por cada rol del rubric, "bajo"/"ok"/"alto".
    """
    return {role: rng.status(role_counts.get(role, 0)) for role, rng in BASE_RUBRIC.items()}
