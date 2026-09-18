# Futurisys — API de prédiction d’attrition

POC pour **Futurisys** : exposer un modèle de machine learning (XGBoost, Projet 5) via une **API FastAPI**, avec **PostgreSQL** pour la traçabilité, **Pytest** et **GitHub Actions**.

Le modèle estime la probabilité qu’un collaborateur quitte l’entreprise. La décision Oui/Non utilise le **seuil max F1** du notebook d’optimisation (≈ 0,484), pas 0,5.

Le déploiement de l’API se présente **en local**.

---

## Architecture

```
Client HTTP
    → FastAPI (Pydantic + X-API-Key)
        → PostgreSQL  (lecture employé + INSERT input)
            → pickle (Pipeline sklearn + XGBoost)
        → PostgreSQL  (INSERT output)
    → JSON { prediction, label, proba_depart, seuil }
```

Toute prédiction **passe par la base** : tables `prediction_inputs` et `prediction_outputs`.

Schéma UML : [`docs/schema.md`](docs/schema.md)  
Couverture de tests : [`docs/coverage.txt`](docs/coverage.txt)

---

## Stack

| Couche | Outil |
|---|---|
| API | FastAPI, Uvicorn, Pydantic v2 |
| ML | scikit-learn 1.7.2, XGBoost 3.2.0, joblib |
| BDD | PostgreSQL 16 (Docker), SQLAlchemy, psycopg2 |
| Qualité | Pytest, pytest-cov |
| CI | GitHub Actions |
| Python | 3.10 (aligné sur l’entraînement) |

---

## Prérequis

- Python **3.10**
- [uv](https://docs.astral.sh/uv/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (moteur WSL2 / virtualisation activée)
- Git

---

## Installation

```powershell
git clone https://github.com/Mathieurgrd/AIE_Project6.git
cd AIE_Project6
uv venv --python 3.10.6
uv pip install -r requirements.txt
copy .env.example .env
```

Éditer `.env` : mettre une **vraie** `API_KEY`.

```env
DATABASE_URL=postgresql+psycopg2://futurisys:futurisys@localhost:5432/futurisys
API_KEY=clé-API
```

---

## Base de données

```powershell
docker compose up -d
uv run python -m src.db.create_db
```

Charge 1470 employés (SIRH + évaluations + sondages).  
Vérification SQL :

```powershell
docker exec -it -e PGPASSWORD=futurisys futurisys-postgres psql -U futurisys -d futurisys
```

```sql
\dt
SELECT COUNT(*) FROM sirh;
```

---

## Lancer l’API (dev / prod locale)

```powershell
uv run uvicorn src.api.main:app --reload
```

- Swagger : http://127.0.0.1:8000/docs  
- Santé : http://127.0.0.1:8000/health  

`uvicorn` n’est pas dans le PATH Windows : passe par `uv run` (ou `.venv\Scripts\uvicorn.exe`).

### Endpoints

| Méthode | Route | Auth | Rôle |
|---|---|---|---|
| `GET` | `/health` | non | API + BDD + pickle |
| `POST` | `/predict/{id_employee}` | header `X-API-Key` | Prédiction journalisée |

Exemple (employé 1) :

```powershell
curl -X POST http://127.0.0.1:8000/predict/1 -H "X-API-Key: ta-cle"
```

Réponse type : `prediction` 0/1, `label` Non/Oui, `proba_depart`, `seuil_utilise`, `input_id`.

Codes : **401** clé absente/fausse, **404** employé inconnu, **422** id invalide.

---

## Authentification et sécurité

- Header obligatoire : `X-API-Key` (comparaison `secrets.compare_digest`).
- `.env` est dans `.gitignore` ; seul `.env.example` (valeur `changeme`) est versionné.
- Pas de mot de passe Postgres dans le code : `DATABASE_URL` via l’environnement.
- Le pickle n’est chargé que depuis `models/attrition_model.pkl` du dépôt (ne pas charger un `.pkl` inconnu).
- En CI, GitHub Actions n’utilise **pas** les secrets locaux : variables factices, tests sans vraie BDD.

Pour la soutenance : Settings GitHub → **Secrets** (`API_KEY`, `DATABASE_URL`) si tu branches un déploiement plus tard.

---

## Tests

```powershell
uv run pytest
```

15 tests : feature engineering, pickle (employés 1 → Oui, 2 → Non), API (200 / 401 / 404).  
Couverture cible ≥ 70 % (seuil aussi en CI). Rapport : `docs/coverage.txt`.

---

## CI/CD et environnements

Fichier : [`.github/workflows/ci.yml`](.github/workflows/ci.yml)

| Environnement | Rôle |
|---|---|
| **dev** | Docker + uvicorn sur ta machine |
| **test** | GitHub Actions (`pytest` à chaque push / PR vers `master`) |
| **prod** | même code `master`, API locale pour la soutenance |

Validation avant fusion : onglet **Checks** de la PR (exiger le job `test` dans Settings → Branches si tu verrouilles `master`).

---

## Modèle (maintenance)

Artefact `models/attrition_model.pkl` (joblib) :

- `model` : Pipeline (preprocess + XGBoost) déjà *fit*
- `threshold` : seuil max F1 (notebook 05)
- `features_to_drop` : 3 colonnes corrélées

Le feature engineering `src/features.py` **n’est pas** dans le pickle : il doit rester identique aux notebooks 04/05.

**Protocole de mise à jour :** réentraîner dans le Projet 5 → exporter le dict artefact → remplacer le `.pkl` → figer les versions dans `requirements.txt` → relancer `uv run pytest` → tag de version.

Les versions sklearn / XGBoost / Python doivent matcher l’entraînement, sinon `joblib.load` peut échouer.

---

## Structure

```
src/api/          FastAPI
src/ml/           chargement pickle + prédiction
src/db/           SQLAlchemy, create_db, traçabilité
src/features.py   add_features (P5)
models/           attrition_model.pkl
data/raw/         CSV RH
tests/            Pytest
docs/             schéma BDD + couverture
.github/workflows CI
```

---

## Choix techniques

- **joblib** plutôt que pickle brut (objets numpy / sklearn).
- **3 tables sources** (fichiers RH) + 2 tables de journal, plutôt qu’une table unique.
- **Seuil métier** sérialisé avec le modèle (pas 0,5 par défaut).
- Tests API **mockés** sur la BDD pour que la CI reste rapide et sans Docker.

---

## Licence / auteur

Projet pédagogique OpenClassrooms — Mathieu, parcours Data science / AI Engineer.
