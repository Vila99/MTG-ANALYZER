"""API web (FastAPI) sobre el mismo pipeline que usa el CLI.

Lanzar en desarrollo:
    uvicorn analyzer.api:app --reload

El origen permitido para CORS se lee de ``FRONTEND_ORIGIN`` (por defecto,
el servidor de desarrollo de Next.js en ``http://localhost:3000``).
"""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from analyzer import cards as cards_module
from analyzer import report
from analyzer import roles as roles_module
from analyzer import rubric
from analyzer.parser import apply_commander_override, parse_decklist

FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")

app = FastAPI(title="MTG Commander Deck Analyzer")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    deck_text: str
    commander: str | None = None
    description: str | None = None
    budget: float | None = None
    style: str = "casual"
    allow_combos: bool = False
    avoid: list[str] = Field(default_factory=list)
    ai: bool = False


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "cards_db": cards_module.DEFAULT_DB_PATH.exists()}


def _collect_card_images(conn, commanders, deck_cards, analysis: dict | None) -> dict[str, str]:
    """Nombres de carta que pueden salir en la respuesta (deck + sugerencias
    de Claude) -> URL de imagen de Scryfall, para la vista previa al pasar
    el cursor en la web."""
    names: set[str] = {c.name for c in commanders} | {c.name for c in deck_cards}
    if analysis:
        for cut in analysis.get("cortes_sugeridos", []):
            names.add(cut["carta"])
        for addition in analysis.get("anadidos_sugeridos", []):
            names.add(addition["carta"])
            if addition.get("reemplaza_a"):
                names.add(addition["reemplaza_a"])

    images: dict[str, str] = {}
    for name in names:
        card = cards_module.get_card_by_name(conn, name)
        if card is not None and card.image_uri:
            images[name] = card.image_uri
    return images


@app.post("/analyze")
def analyze(request: AnalyzeRequest) -> dict:
    if not cards_module.DEFAULT_DB_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail="No se encontró la base de datos de cartas. Ejecuta scripts/load_scryfall.py.",
        )

    client = None
    if request.ai:
        from analyzer import llm

        try:
            client = llm.get_client()
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    parsed = parse_decklist(request.deck_text)

    conn = cards_module.connect(cards_module.DEFAULT_DB_PATH)
    try:
        if request.commander:
            # Campo escrito a mano: tolera nombres incompletos o con alguna
            # variación resolviéndolo contra la BD antes de añadirlo, para
            # no acabar con un comandante "no encontrado" por una tontería.
            commander_card = cards_module.find_card_by_name_fuzzy(conn, request.commander)
            apply_commander_override(parsed, commander_card.name if commander_card else request.commander)

        commanders, deck_cards, missing = cards_module.resolve_deck(conn, parsed)
        role_counts = roles_module.count_roles(conn, deck_cards)
        card_roles = roles_module.classify_cards(conn, deck_cards)

        analysis_run = None
        if request.ai:
            from analyzer import pipeline

            params = {
                "budget": request.budget,
                "style": request.style,
                "allow_combos": request.allow_combos,
                "avoid": request.avoid,
                "description": request.description,
            }
            analysis_run = pipeline.run_analysis(
                client, conn, commanders, deck_cards, card_roles, params
            )

        validated_analysis = analysis_run.validated_analysis if analysis_run else None
        card_images = _collect_card_images(conn, commanders, deck_cards, validated_analysis)
    finally:
        conn.close()

    rubric_status = rubric.evaluate_role_counts(role_counts)
    summary = report.build_summary(
        commanders, deck_cards, missing, role_counts, rubric_status, card_roles
    )
    if validated_analysis is not None:
        summary["analisis"] = validated_analysis
    summary["card_images"] = card_images
    return summary
