"""Fixtures partagées : une ligne employé issue des CSV (sans Postgres)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw"


@pytest.fixture(scope="session")
def employees_df() -> pd.DataFrame:
    sirh = pd.read_csv(DATA / "extrait_sirh.csv")
    evaluations = pd.read_csv(DATA / "extrait_eval.csv")
    sondages = pd.read_csv(DATA / "extrait_sondage.csv")
    evaluations["id_employee"] = (
        evaluations["eval_number"].str.replace("E_", "", regex=False).astype(int)
    )
    sondages["id_employee"] = sondages["code_sondage"].astype(int)
    return (
        sirh.merge(evaluations, on="id_employee")
        .merge(sondages, on="id_employee")
    )


def employee_dict(employees_df: pd.DataFrame, employee_id: int) -> dict:
    return employees_df.loc[employees_df["id_employee"] == employee_id].iloc[0].to_dict()
