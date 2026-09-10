"""Crée les tables PostgreSQL et y charge les 3 CSV du Projet 5."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.db.models import Base, Evaluation, Sirh, Sondage
from src.db.session import get_engine, get_session

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


def _native(row: dict) -> dict:
    """Convertit les types numpy (int64, etc.) en types Python pour psycopg2."""
    clean = {}
    for key, value in row.items():
        if hasattr(value, "item"):
            value = value.item()
        clean[key] = value
    return clean


def create_tables() -> None:
    engine = get_engine()
    Base.metadata.create_all(engine)
    print("Tables créées :", list(Base.metadata.tables))


def _load_frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    sirh = pd.read_csv(DATA_DIR / "extrait_sirh.csv")

    evaluations = pd.read_csv(DATA_DIR / "extrait_eval.csv")
    evaluations["id_employee"] = (
        evaluations["eval_number"].str.replace("E_", "", regex=False).astype(int)
    )
    evaluations = evaluations.drop(columns=["eval_number"])

    sondages = pd.read_csv(DATA_DIR / "extrait_sondage.csv")
    sondages["id_employee"] = sondages["code_sondage"].astype(int)
    sondages = sondages.drop(columns=["code_sondage"])

    return sirh, evaluations, sondages


def load_dataset() -> None:
    sirh, evaluations, sondages = _load_frames()
    session = get_session()
    try:
        if session.query(Sirh).count() > 0:
            print("Dataset déjà présent, chargement ignoré.")
            return

        session.add_all([Sirh(**_native(row)) for row in sirh.to_dict(orient="records")])
        session.flush()
        session.add_all(
            [Evaluation(**_native(row)) for row in evaluations.to_dict(orient="records")]
        )
        session.add_all(
            [Sondage(**_native(row)) for row in sondages.to_dict(orient="records")]
        )
        session.commit()
        print(f"Chargé : {len(sirh)} employés (SIRH + évaluations + sondages).")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    create_tables()
    load_dataset()
