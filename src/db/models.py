"""Schéma relationnel Futurisys (dataset RH + journal des prédictions)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Sirh(Base):
    """Données contrat / identité (extrait_sirh.csv)."""

    __tablename__ = "sirh"

    id_employee: Mapped[int] = mapped_column(Integer, primary_key=True)
    age: Mapped[int] = mapped_column(Integer)
    genre: Mapped[str] = mapped_column(String(8))
    revenu_mensuel: Mapped[int] = mapped_column(Integer)
    statut_marital: Mapped[str] = mapped_column(String(32))
    departement: Mapped[str] = mapped_column(String(64))
    poste: Mapped[str] = mapped_column(String(64))
    nombre_experiences_precedentes: Mapped[int] = mapped_column(Integer)
    nombre_heures_travailless: Mapped[int] = mapped_column(Integer)
    annee_experience_totale: Mapped[int] = mapped_column(Integer)
    annees_dans_l_entreprise: Mapped[int] = mapped_column(Integer)
    annees_dans_le_poste_actuel: Mapped[int] = mapped_column(Integer)

    evaluation: Mapped["Evaluation"] = relationship(back_populates="sirh")
    sondage: Mapped["Sondage"] = relationship(back_populates="sirh")


class Evaluation(Base):
    """Évaluations et heures sup (extrait_eval.csv)."""

    __tablename__ = "evaluations"

    id_employee: Mapped[int] = mapped_column(
        Integer, ForeignKey("sirh.id_employee"), primary_key=True
    )
    satisfaction_employee_environnement: Mapped[int] = mapped_column(Integer)
    note_evaluation_precedente: Mapped[int] = mapped_column(Integer)
    niveau_hierarchique_poste: Mapped[int] = mapped_column(Integer)
    satisfaction_employee_nature_travail: Mapped[int] = mapped_column(Integer)
    satisfaction_employee_equipe: Mapped[int] = mapped_column(Integer)
    satisfaction_employee_equilibre_pro_perso: Mapped[int] = mapped_column(Integer)
    note_evaluation_actuelle: Mapped[int] = mapped_column(Integer)
    heure_supplementaires: Mapped[str] = mapped_column(String(8))
    augementation_salaire_precedente: Mapped[str] = mapped_column(String(16))

    sirh: Mapped[Sirh] = relationship(back_populates="evaluation")


class Sondage(Base):
    """Sondage RH + cible historique (extrait_sondage.csv)."""

    __tablename__ = "sondages"

    id_employee: Mapped[int] = mapped_column(
        Integer, ForeignKey("sirh.id_employee"), primary_key=True
    )
    a_quitte_l_entreprise: Mapped[str] = mapped_column(String(8))
    nombre_participation_pee: Mapped[int] = mapped_column(Integer)
    nb_formations_suivies: Mapped[int] = mapped_column(Integer)
    nombre_employee_sous_responsabilite: Mapped[int] = mapped_column(Integer)
    distance_domicile_travail: Mapped[int] = mapped_column(Integer)
    niveau_education: Mapped[int] = mapped_column(Integer)
    domaine_etude: Mapped[str] = mapped_column(String(64))
    ayant_enfants: Mapped[str] = mapped_column(String(8))
    frequence_deplacement: Mapped[str] = mapped_column(String(32))
    annees_depuis_la_derniere_promotion: Mapped[int] = mapped_column(Integer)
    annes_sous_responsable_actuel: Mapped[int] = mapped_column(Integer)

    sirh: Mapped[Sirh] = relationship(back_populates="sondage")


class PredictionInput(Base):
    """Snapshot des features envoyées au modèle (une ligne = un appel)."""

    __tablename__ = "prediction_inputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_employee: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sirh.id_employee"), nullable=True
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    output: Mapped["PredictionOutput | None"] = relationship(
        back_populates="input", uselist=False
    )


class PredictionOutput(Base):
    """Résultat du modèle, lié à l'input correspondant."""

    __tablename__ = "prediction_outputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    input_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("prediction_inputs.id"), unique=True
    )
    prediction: Mapped[int] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(String(8))
    proba_depart: Mapped[float] = mapped_column(Float)
    seuil_utilise: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    input: Mapped[PredictionInput] = relationship(back_populates="output")
