"""Toute prédiction passe par la BDD : on journalise l'input, puis l'output."""

from __future__ import annotations

from sqlalchemy.orm import Session

from src.db.models import Evaluation, PredictionInput, PredictionOutput, Sirh, Sondage
from src.db.session import get_session
from src.ml.predict import predict_attrition


def _row_to_dict(obj) -> dict:
    return {column.name: getattr(obj, column.name) for column in obj.__table__.columns}


def get_employee_payload(session: Session, id_employee: int) -> dict:
    """Reconstruit la ligne brute (comme le merge des 3 CSV)."""
    sirh = session.get(Sirh, id_employee)
    evaluation = session.get(Evaluation, id_employee)
    sondage = session.get(Sondage, id_employee)
    if sirh is None or evaluation is None or sondage is None:
        raise ValueError(f"Employé {id_employee} introuvable ou incomplet.")

    payload = {}
    payload.update(_row_to_dict(sirh))
    payload.update(_row_to_dict(evaluation))
    payload.update(_row_to_dict(sondage))
    return payload


def predict_and_trace(
    id_employee: int,
    session: Session | None = None,
) -> dict:
    """Lit l'employé en base, enregistre l'input, prédit, enregistre l'output."""
    own_session = session is None
    session = session or get_session()
    try:
        payload = get_employee_payload(session, id_employee)
        record_in = PredictionInput(id_employee=id_employee, payload=payload)
        session.add(record_in)
        session.flush()

        result = predict_attrition(payload)

        record_out = PredictionOutput(
            input_id=record_in.id,
            prediction=result["prediction"],
            label=result["label"],
            proba_depart=result["proba_depart"],
            seuil_utilise=result["seuil_utilise"],
        )
        session.add(record_out)
        session.commit()
        result["input_id"] = record_in.id
        result["id_employee"] = id_employee
        return result
    except Exception:
        session.rollback()
        raise
    finally:
        if own_session:
            session.close()


if __name__ == "__main__":
    print(predict_and_trace(1))
    print(predict_and_trace(2))
