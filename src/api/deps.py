"""Dépendances FastAPI : session BDD et clé d'API."""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from dotenv import dotenv_values, load_dotenv
from fastapi import Header, HTTPException, status

from src.db.session import get_session

_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_ENV_PATH)


def get_db():
    """Une session par requête, fermée ensuite."""
    session = get_session()
    try:
        yield session
    finally:
        session.close()


def verify_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    file_values = dotenv_values(_ENV_PATH)
    expected = (file_values.get("API_KEY") or os.getenv("API_KEY") or "").strip()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API_KEY manquante dans le .env",
        )
    if x_api_key is None or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide ou absente (header X-API-Key)",
        )
