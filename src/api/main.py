"""API Futurisys : prédiction d'attrition (passe toujours par PostgreSQL)."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from src.api.deps import get_db, verify_api_key
from src.api.schemas import HealthResponse, PredictionResponse
from src.db.session import get_engine
from src.db.trace import predict_and_trace
from src.ml.predict import load_artifact


@asynccontextmanager
async def lifespan(_app: FastAPI):
    load_artifact()
    yield


app = FastAPI(
    title="Futurisys — API attrition",
    description=(
        "Expose le modèle XGBoost du Projet 5. "
        "Chaque prédiction est journalisée en PostgreSQL "
        "(prediction_inputs / prediction_outputs). "
        "Authentification : header `X-API-Key`."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse, tags=["infra"])
def health() -> HealthResponse:
    """Vérifie que l'API, la BDD et le pickle répondent (sans auth)."""
    db_status = "ok"
    model_status = "ok"
    try:
        with get_engine().connect() as conn:
            conn.exec_driver_sql("SELECT 1")
    except Exception:
        db_status = "down"
    try:
        load_artifact()
    except Exception:
        model_status = "down"
    overall = "ok" if db_status == "ok" and model_status == "ok" else "degraded"
    return HealthResponse(status=overall, database=db_status, model=model_status)


@app.post(
    "/predict/{id_employee}",
    response_model=PredictionResponse,
    tags=["prédiction"],
    dependencies=[Depends(verify_api_key)],
)
def predict_employee(
    id_employee: int,
    session: Session = Depends(get_db),
) -> PredictionResponse:
    """Charge l'employé en base, journalise l'appel, retourne Oui/Non + proba."""
    try:
        result = predict_and_trace(id_employee, session=session)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return PredictionResponse(**result)
