"""Feature engineering partagé entre les notebooks et l'API.

Important : cette fonction doit rester identique à celle utilisée
lors de l'entraînement (notebook 04), sinon l'inférence diverge.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_features(X: pd.DataFrame) -> pd.DataFrame:
    """Ajoute les variables métier dérivées avant le passage dans la Pipeline.

    Parameters
    ----------
    X :
        DataFrame des features (après suppression éventuelle des colonnes
        très corrélées), avec les colonnes brutes attendues par le modèle.

    Returns
    -------
    pd.DataFrame
        Copie de ``X`` enrichie des features dérivées.
    """
    X = X.copy()

    satisfaction_columns = [
        "satisfaction_employee_environnement",
        "satisfaction_employee_nature_travail",
        "satisfaction_employee_equipe",
        "satisfaction_employee_equilibre_pro_perso",
    ]

    # Satisfaction générale
    X["satisfaction_globale"] = X[satisfaction_columns].mean(axis=1)

    # Niveau de satisfaction le plus faible
    X["satisfaction_min"] = X[satisfaction_columns].min(axis=1)

    # Dispersion des différentes satisfactions
    X["dispersion_satisfaction"] = (
        X[satisfaction_columns].max(axis=1)
        - X[satisfaction_columns].min(axis=1)
    )

    # Part de l'ancienneté passée sous le responsable actuel
    anciennete = X["annees_dans_l_entreprise"].replace(0, np.nan)

    X["ratio_responsable_anciennete"] = (
        X["annes_sous_responsable_actuel"] / anciennete
    )

    # Temps sans promotion relativement à l'ancienneté
    X["ratio_sans_promotion"] = (
        X["annees_depuis_la_derniere_promotion"] / anciennete
    )

    # Promotion récente
    X["promotion_recente"] = (
        X["annees_depuis_la_derniere_promotion"] <= 2
    ).astype(int)

    # Faible ancienneté
    X["faible_anciennete"] = (
        X["annees_dans_l_entreprise"] <= 2
    ).astype(int)

    # Interaction : heures supplémentaires + faible satisfaction
    X["heures_sup_faible_satisfaction"] = (
        (X["heure_supplementaires"] == "Oui")
        & (X["satisfaction_globale"] < 2.5)
    ).astype(int)

    # Interaction : distance importante + heures supplémentaires
    X["distance_et_heures_sup"] = (
        (X["distance_domicile_travail"] >= 20)
        & (X["heure_supplementaires"] == "Oui")
    ).astype(int)

    # Nettoyage uniquement des ratios créés
    ratio_columns = [
        "ratio_responsable_anciennete",
        "ratio_sans_promotion",
    ]

    X[ratio_columns] = (
        X[ratio_columns]
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0)
    )

    return X
