"""Inférence : même chemin que les notebooks du Projet 5.

Ordre obligatoire (sinon le pickle ne correspond plus) :

1. retirer id / constantes / cible
2. convertir ``augementation_salaire_precedente`` (``"11 %"`` → ``11.0``)
3. retirer les 3 colonnes trop corrélées
4. ``add_features``
5. Pipeline → proba → seuil (~0,484)
"""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd

from src.features import add_features

MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "attrition_model.pkl"

# Identifiant, constantes, cible : jamais vus par la Pipeline (notebook 03)
COLUMNS_UNUSED = [
    "id_employee",
    "eval_number",
    "code_sondage",
    "nombre_heures_travailless",
    "nombre_employee_sous_responsabilite",
    "ayant_enfants",
    "a_quitte_l_entreprise",
]

_artifact: dict | None = None


def load_artifact(model_path: Path | None = None) -> dict:
    """Charge le pickle une seule fois (dict : model, threshold, features_to_drop)."""
    global _artifact
    if _artifact is None:
        path = model_path or MODEL_PATH
        _artifact = joblib.load(path)
    return _artifact


def _parse_salary_increase(series: pd.Series) -> pd.Series:
    """Accepte ``11``, ``11.0`` ou ``"11 %"`` comme dans le CSV brut."""
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(float)
    return (
        series.astype(str)
        .str.replace("%", "", regex=False)
        .str.strip()
        .astype(float)
    )


def prepare_features(employee: dict) -> pd.DataFrame:
    """Transforme une ligne brute en DataFrame prêt pour ``predict_proba``."""
    artifact = load_artifact()
    X = pd.DataFrame([employee])

    X = X.drop(columns=COLUMNS_UNUSED, errors="ignore")

    if "augementation_salaire_precedente" in X.columns:
        X["augementation_salaire_precedente"] = _parse_salary_increase(
            X["augementation_salaire_precedente"]
        )

    X = X.drop(columns=artifact["features_to_drop"], errors="ignore")
    X = add_features(X)
    return X


def predict_attrition(employee: dict) -> dict:
    """Retourne la proba de départ, la classe 0/1 et le seuil utilisé."""
    artifact = load_artifact()
    model = artifact["model"]
    threshold = float(artifact["threshold"])

    X = prepare_features(employee)
    proba = float(model.predict_proba(X)[:, 1][0])
    pred = int(proba >= threshold)

    return {
        "prediction": pred,
        "label": "Oui" if pred == 1 else "Non",
        "proba_depart": proba,
        "seuil_utilise": threshold,
    }
