"""Tests unitaires du feature engineering (hors modèle, hors API)."""

import pandas as pd

from src.features import add_features
from tests.conftest import employee_dict


ENGINEERED = [
    "satisfaction_globale",
    "satisfaction_min",
    "dispersion_satisfaction",
    "ratio_responsable_anciennete",
    "ratio_sans_promotion",
    "promotion_recente",
    "faible_anciennete",
    "heures_sup_faible_satisfaction",
    "distance_et_heures_sup",
]


def test_add_features_ajoute_les_colonnes_metier(employees_df):
    raw = pd.DataFrame([employee_dict(employees_df, 1)])
    out = add_features(raw)
    for col in ENGINEERED:
        assert col in out.columns


def test_add_features_ne_modifie_pas_l_entree(employees_df):
    raw = pd.DataFrame([employee_dict(employees_df, 1)])
    before = list(raw.columns)
    add_features(raw)
    assert list(raw.columns) == before


def test_satisfaction_globale_est_la_moyenne():
    raw = pd.DataFrame(
        [
            {
                "satisfaction_employee_environnement": 1,
                "satisfaction_employee_nature_travail": 3,
                "satisfaction_employee_equipe": 2,
                "satisfaction_employee_equilibre_pro_perso": 2,
                "annees_dans_l_entreprise": 4,
                "annes_sous_responsable_actuel": 2,
                "annees_depuis_la_derniere_promotion": 1,
                "heure_supplementaires": "Non",
                "distance_domicile_travail": 5,
            }
        ]
    )
    out = add_features(raw)
    assert out["satisfaction_globale"].iloc[0] == 2.0
    assert out["satisfaction_min"].iloc[0] == 1
    assert out["dispersion_satisfaction"].iloc[0] == 2


def test_anciennete_zero_ne_produit_pas_d_inf():
    raw = pd.DataFrame(
        [
            {
                "satisfaction_employee_environnement": 3,
                "satisfaction_employee_nature_travail": 3,
                "satisfaction_employee_equipe": 3,
                "satisfaction_employee_equilibre_pro_perso": 3,
                "annees_dans_l_entreprise": 0,
                "annes_sous_responsable_actuel": 0,
                "annees_depuis_la_derniere_promotion": 0,
                "heure_supplementaires": "Non",
                "distance_domicile_travail": 1,
            }
        ]
    )
    out = add_features(raw)
    assert out["ratio_responsable_anciennete"].iloc[0] == 0
    assert out["ratio_sans_promotion"].iloc[0] == 0
