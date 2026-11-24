"""Descarga el bulk data 'oracle_cards' de Scryfall y lo carga en data/cards.db.

Uso:
    python scripts/load_scryfall.py

La lógica vive en ``analyzer.scryfall_db`` (la reutilizan también el CLI y
la API para crear la base de datos automáticamente la primera vez).
"""

from analyzer.scryfall_db import main

if __name__ == "__main__":
    raise SystemExit(main())
