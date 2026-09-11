"""Tests fonctionnels du modèle : même chemin que l'API, sans Postgres."""

from src.ml.predict import COLUMNS_UNUSED, predict_attrition, prepare_features
from tests.conftest import employee_dict


def test_employe_1_predit_depart(employees_df):
    result = predict_attrition(employee_dict(employees_df, 1))
    assert result["prediction"] == 1
    assert result["label"] == "Oui"
    assert result["proba_depart"] >= result["seuil_utilise"]
    assert 0.48 < result["seuil_utilise"] < 0.49


def test_employe_2_predit_reste(employees_df):
    result = predict_attrition(employee_dict(employees_df, 2))
    assert result["prediction"] == 0
    assert result["label"] == "Non"
    assert result["proba_depart"] < result["seuil_utilise"]


def test_pourcentage_salaire_est_numerique(employees_df):
    row = employee_dict(employees_df, 1)
    assert isinstance(row["augementation_salaire_precedente"], str)
    assert "%" in str(row["augementation_salaire_precedente"])
    prepared = prepare_features(row)
    assert prepared["augementation_salaire_precedente"].dtype.kind == "f"


def test_colonnes_inutiles_absentes_apres_prepare(employees_df):
    prepared = prepare_features(employee_dict(employees_df, 1))
    for col in COLUMNS_UNUSED:
        assert col not in prepared.columns
    for col in ["niveau_hierarchique_poste", "annee_experience_totale", "annees_dans_le_poste_actuel"]:
        assert col not in prepared.columns
