"""Schémas Pydantic : contrat JSON de l'API (validation + doc Swagger)."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    database: str
    model: str


class PredictionResponse(BaseModel):
    id_employee: int
    input_id: int = Field(description="Ligne prediction_inputs créée pour cet appel")
    prediction: int = Field(description="1 = risque de départ, 0 = reste")
    label: str
    proba_depart: float
    seuil_utilise: float
