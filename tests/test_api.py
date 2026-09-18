"""Tests HTTP de l'API, sans Docker.

FastAPI `dependency_overrides` remplace get_db / verify_api_key.
`monkeypatch.setattr` remplace predict_and_trace : on teste le routage
(status 200/401/404), pas Postgres ni le pickle.
"""

from fastapi.testclient import TestClient

from src.api.deps import get_db, verify_api_key
from src.api.main import app


def _client(*, auth: bool) -> TestClient:
    """Client HTTP in-process. auth=True : on saute la vérif de clé."""
    app.dependency_overrides.clear()
    if auth:
        app.dependency_overrides[verify_api_key] = lambda: None

    def fake_db():
        yield None  # session fictive : predict_and_trace est mocké ailleurs

    app.dependency_overrides[get_db] = fake_db
    return TestClient(app)


def test_health_renvoie_200_et_le_modele():
    """/health est public : pas de X-API-Key."""
    with _client(auth=False) as client:
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "ok"
    assert body["status"] in {"ok", "degraded"}
    assert "database" in body


def test_predict_sans_cle_fait_401(monkeypatch):
    """Sans header : 401. On force une clé connue pour ne pas tomber en 500."""
    monkeypatch.setattr(
        "src.api.deps.dotenv_values",
        lambda *args, **kwargs: {"API_KEY": "test-secret"},
    )
    app.dependency_overrides.clear()
    with TestClient(app) as client:
        response = client.post("/predict/1")
    assert response.status_code == 401


def test_predict_mauvaise_cle_fait_401(monkeypatch):
    monkeypatch.setattr(
        "src.api.deps.dotenv_values",
        lambda *args, **kwargs: {"API_KEY": "test-secret"},
    )
    app.dependency_overrides.clear()
    with TestClient(app) as client:
        response = client.post(
            "/predict/1",
            headers={"X-API-Key": "wrong"},
        )
    assert response.status_code == 401


def test_predict_ok_quand_trace_reussit(monkeypatch):
    """Le métier est stubé : on vérifie que l'API relaie bien le JSON."""
    monkeypatch.setattr(
        "src.api.main.predict_and_trace",
        lambda id_employee, session=None: {
            "id_employee": id_employee,
            "input_id": 42,
            "prediction": 1,
            "label": "Oui",
            "proba_depart": 0.85,
            "seuil_utilise": 0.484,
        },
    )
    with _client(auth=True) as client:
        response = client.post("/predict/1")
    assert response.status_code == 200
    body = response.json()
    assert body["label"] == "Oui"
    assert body["input_id"] == 42
    assert body["id_employee"] == 1


def test_predict_employe_inconnu_fait_404(monkeypatch):
    """ValueError métier → HTTP 404."""
    def raise_missing(id_employee, session=None):
        raise ValueError(f"Employé {id_employee} introuvable ou incomplet.")

    monkeypatch.setattr("src.api.main.predict_and_trace", raise_missing)
    with _client(auth=True) as client:
        response = client.post("/predict/99999")
    assert response.status_code == 404
    assert "99999" in response.json()["detail"]
