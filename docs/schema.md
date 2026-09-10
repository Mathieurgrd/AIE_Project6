# Schéma de la base Futurisys

Les tables `sirh`, `evaluations` et `sondages` reprennent les 3 CSV du Projet 5 (une ligne = un employé). Les tables `prediction_inputs` et `prediction_outputs` journalisent **chaque** appel au modèle : aucune prédiction sans passage en base.

```mermaid
erDiagram
    sirh ||--|| evaluations : "id_employee"
    sirh ||--|| sondages : "id_employee"
    sirh ||--o{ prediction_inputs : "id_employee"
    prediction_inputs ||--o| prediction_outputs : "input_id"

    sirh {
        int id_employee PK
        int age
        string genre
        int revenu_mensuel
        string poste
    }

    evaluations {
        int id_employee PK, FK
        int note_evaluation_actuelle
        string heure_supplementaires
        string augementation_salaire_precedente
    }

    sondages {
        int id_employee PK, FK
        string a_quitte_l_entreprise
        string domaine_etude
        int distance_domicile_travail
    }

    prediction_inputs {
        int id PK
        int id_employee FK
        jsonb payload
        datetime created_at
    }

    prediction_outputs {
        int id PK
        int input_id FK
        int prediction
        string label
        float proba_depart
        float seuil_utilise
        datetime created_at
    }
```

## Choix techniques

- **3 tables sources** plutôt qu’une seule table dénormalisée : on respecte l’origine des fichiers (SIRH / eval / sondage) et on évite de mélanger contrat, évaluation et cible.
- **`payload` JSONB** : on stocke exactement ce qui a été envoyé au modèle (reproductibilité), sans dupliquer 30 colonnes.
- **Input et output séparés** : la consigne demande des tables dédiées ; on peut auditer un appel même si la prédiction échoue après l’insert input (l’API gérera le rollback).

## Lancer en local

```powershell
copy .env.example .env
docker compose up -d
uv run python -m src.db.create_db
uv run python -m src.db.trace
```
