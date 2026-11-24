"""API web (FastAPI) sobre el mismo pipeline que usa el CLI.

Lanzar en desarrollo:
    uvicorn analyzer.api:app --reload

El origen permitido para CORS se lee de ``FRONTEND_ORIGIN`` (por defecto,
el servidor de desarrollo de Next.js en ``http://localhost:3000``).

Si ``data/cards.db`` no existe al arrancar, se descarga de Scryfall en
segundo plano (desactivable con ``AUTO_DOWNLOAD_CARDS_DB=0``); mientras
tanto los endpoints de análisis responden 503 explicando que se está
creando.
"""

from __future__ import annotations

import logging
import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from analyzer import budget as budget_module
from analyzer import cards as cards_module
from analyzer import goldfish as goldfish_module
from analyzer import moxfield as moxfield_module
from analyzer import prices as prices_module
from analyzer import report
from analyzer import roles as roles_module
from analyzer import rubric
from analyzer import scryfall_db
from analyzer.cards import Card
from analyzer.parser import ParsedDeck, apply_commander_override, parse_decklist

FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")

logger = logging.getLogger(__name__)

# Estado de la descarga automática de cards.db: "idle", "downloading" o "error".
_db_download = {"status": "idle", "error": None}
_db_download_lock = threading.Lock()


def _download_cards_db() -> None:
    try:
        scryfall_db.build_database(cards_module.DEFAULT_DB_PATH, log=logger.info)
    except Exception as exc:
        logger.exception("No se pudo crear la base de datos de cartas")
        with _db_download_lock:
            _db_download.update(status="error", error=str(exc))
    else:
        with _db_download_lock:
            _db_download.update(status="idle", error=None)


def start_cards_db_download_if_missing() -> bool:
    """Lanza la descarga de cards.db en un hilo si falta. True si la lanza."""
    if cards_module.DEFAULT_DB_PATH.exists():
        return False
    if os.environ.get("AUTO_DOWNLOAD_CARDS_DB", "1").strip().lower() in ("0", "false", "no"):
        return False
    with _db_download_lock:
        if _db_download["status"] == "downloading":
            return False
        _db_download.update(status="downloading", error=None)
    logger.warning("No existe %s: descargándola de Scryfall en segundo plano...", cards_module.DEFAULT_DB_PATH)
    threading.Thread(target=_download_cards_db, name="cards-db-download", daemon=True).start()
    return True


def _cards_db_status() -> str:
    if cards_module.DEFAULT_DB_PATH.exists():
        return "ready"
    with _db_download_lock:
        return "missing" if _db_download["status"] == "idle" else _db_download["status"]


def _require_cards_db() -> None:
    status = _cards_db_status()
    if status == "ready":
        return
    if status == "downloading":
        detail = (
            "Se está descargando la base de datos de cartas de Scryfall (primer arranque). "
            "Vuelve a intentarlo en unos segundos."
        )
    elif status == "error":
        detail = (
            f"No se pudo descargar la base de datos de cartas ({_db_download['error']}). "
            "Ejecuta scripts/load_scryfall.py o reinicia el servidor."
        )
    else:
        detail = "No se encontró la base de datos de cartas. Ejecuta scripts/load_scryfall.py."
    raise HTTPException(status_code=503, detail=detail)


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    start_cards_db_download_if_missing()
    yield


app = FastAPI(title="MTG Commander Deck Analyzer", lifespan=_lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    deck_text: str | None = None
    moxfield_url: str | None = None
    commander: str | None = None
    description: str | None = None
    budget_mode: str | None = None
    style: str = "casual"
    allow_combos: bool = False
    avoid: list[str] = Field(default_factory=list)
    ai: bool = False


class SimulateRequest(BaseModel):
    deck_text: str | None = None
    moxfield_url: str | None = None
    commander: str | None = None
    n_sims: int = Field(default=10000, ge=100, le=20000)


@app.get("/health")
def health() -> dict:
    status = _cards_db_status()
    return {"status": "ok", "cards_db": status == "ready", "cards_db_status": status}


def _parse_deck_input(deck_text: str | None, moxfield_url: str | None) -> ParsedDeck:
    if moxfield_url:
        try:
            return moxfield_module.fetch_moxfield_deck(moxfield_url)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    if deck_text:
        return parse_decklist(deck_text)
    raise HTTPException(status_code=400, detail="Falta la lista del deck o una URL de Moxfield.")


def _resolve_commanders_and_cards(
    conn, parsed: ParsedDeck, commander_override: str | None
) -> tuple[list[Card], list[Card], list[str]]:
    if commander_override:
        # Campo escrito a mano: tolera nombres incompletos o con alguna
        # variación resolviéndolo contra la BD antes de añadirlo, para no
        # acabar con un comandante "no encontrado" por una tontería.
        commander_card = cards_module.find_card_by_name_fuzzy(conn, commander_override)
        apply_commander_override(parsed, commander_card.name if commander_card else commander_override)
    return cards_module.resolve_deck(conn, parsed)


def _collect_card_images(conn, commanders, deck_cards, analysis: dict | None) -> dict[str, str]:
    """Nombres de carta que pueden salir en la respuesta (deck + sugerencias
    de Claude) -> URL de imagen de Scryfall, para la vista previa al pasar
    el cursor en la web."""
    names: set[str] = {c.name for c in commanders} | {c.name for c in deck_cards}
    if analysis:
        for problema in analysis.get("problemas", []):
            for candidata in problema.get("candidatas_sugeridas", []):
                names.add(candidata["carta"])

    images: dict[str, str] = {}
    for name in names:
        card = cards_module.get_card_by_name(conn, name)
        if card is not None and card.image_uri:
            images[name] = card.image_uri
    return images


@app.post("/analyze")
def analyze(request: AnalyzeRequest) -> dict:
    _require_cards_db()

    client = None
    if request.ai:
        from analyzer import llm

        try:
            client = llm.get_client()
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    parsed = _parse_deck_input(request.deck_text, request.moxfield_url)

    conn = cards_module.connect(cards_module.DEFAULT_DB_PATH)
    try:
        commanders, deck_cards, missing = _resolve_commanders_and_cards(
            conn, parsed, request.commander
        )
        role_counts = roles_module.count_roles(conn, deck_cards)
        card_roles = roles_module.classify_cards(conn, deck_cards)

        analysis_run = None
        if request.ai:
            from analyzer import pipeline

            params = {
                "budget_mode": request.budget_mode,
                "style": request.style,
                "allow_combos": request.allow_combos,
                "avoid": request.avoid,
                "description": request.description,
            }
            analysis_run = pipeline.run_analysis(
                client, conn, commanders, deck_cards, card_roles, params
            )

        validated_analysis = analysis_run.validated_analysis if analysis_run else None
        if validated_analysis is not None:
            validated_analysis = budget_module.annotate_prices(
                conn, validated_analysis, request.budget_mode
            )
            combos_detectados = analysis_run.payload.get("bracket_suelo", {}).get("combos", [])
            validated_analysis = {**validated_analysis, "combos_detectados": combos_detectados}
        card_images = _collect_card_images(conn, commanders, deck_cards, validated_analysis)
        deck_cost = prices_module.compute_deck_cost(conn, deck_cards)
    finally:
        conn.close()

    rubric_status = rubric.evaluate_role_counts(role_counts)
    problemas = validated_analysis.get("problemas") if validated_analysis else None
    summary = report.build_summary(
        commanders, deck_cards, missing, role_counts, rubric_status, card_roles, problemas, deck_cost
    )
    if validated_analysis is not None:
        summary["analisis"] = validated_analysis
    summary["card_images"] = card_images
    return summary


@app.post("/simulate")
def simulate(request: SimulateRequest) -> dict:
    """Goldfish estadístico (Monte Carlo, sin rivales, política de juego
    fija) — ver ``analyzer.goldfish``. No hace ninguna llamada a la API de
    Claude: solo necesita el deck ya resuelto y los roles ya clasificados
    (su caché en SQLite ya está caliente si el deck se analizó antes)."""
    _require_cards_db()

    parsed = _parse_deck_input(request.deck_text, request.moxfield_url)

    conn = cards_module.connect(cards_module.DEFAULT_DB_PATH)
    try:
        commanders, deck_cards, missing = _resolve_commanders_and_cards(
            conn, parsed, request.commander
        )
        if not commanders:
            raise HTTPException(
                status_code=400, detail="No se detectó un comandante para simular."
            )
        card_roles = roles_module.classify_cards(conn, deck_cards)
        stats = goldfish_module.run_monte_carlo(
            deck_cards, card_roles, commanders, n_sims=request.n_sims
        )
    finally:
        conn.close()

    stats["no_encontradas"] = missing
    return stats
