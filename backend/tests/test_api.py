import os
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_newtonite.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
from fastapi.testclient import TestClient
from app.main import app
from app.seed import seed
from app.db import Base, engine

Base.metadata.drop_all(bind=engine)
seed()
client = TestClient(app)
PASSWORD = "NewtoniteDemo!2026"

def token(email):
    response = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200
    return response.json()["access_token"]

def headers(email="admin@newtonite.local"):
    return {"Authorization": f"Bearer {token(email)}"}

def test_health():
    assert client.get("/health").json()["status"] == "ok"

def test_login():
    assert client.post("/auth/login", json={"email": "member@newtonite.local", "password": PASSWORD}).status_code == 200

def test_cross_team_access_denied():
    admin = headers()
    item = client.post("/work-items", headers=admin, json={"title":"Private team issue","description":"test","team_id":2,"priority":"High","item_type":"Task"})
    assert item.status_code == 201
    outsider = headers("outsider@newtonite.local")
    response = client.get(f"/work-items/{item.json()['id']}", headers=outsider)
    assert response.status_code == 403

def test_stale_update_rejected():
    h = headers()
    created = client.post("/work-items", headers=h, json={"title":"Version test item","team_id":1,"priority":"Medium","item_type":"Task"}).json()
    first = client.patch(f"/work-items/{created['id']}", headers=h, json={"version":created["version"],"priority":"High"})
    assert first.status_code == 200
    stale = client.patch(f"/work-items/{created['id']}", headers=h, json={"version":created["version"],"priority":"Low"})
    assert stale.status_code == 409

def test_claim_only_once():
    h = headers("member@newtonite.local")
    created = client.post("/work-items", headers=headers(), json={"title":"Claim race item","team_id":1,"priority":"Urgent","item_type":"Task"}).json()
    one = client.post(f"/work-items/{created['id']}/claim", headers=h, json={})
    two = client.post(f"/work-items/{created['id']}/claim", headers=h, json={})
    assert one.status_code == 200
    assert two.status_code == 409

def test_invalid_transition_rejected():
    h = headers()
    created = client.post("/work-items", headers=h, json={"title":"Workflow test item","team_id":1,"priority":"Low","item_type":"Task"}).json()
    result = client.post(f"/work-items/{created['id']}/transition", headers=h, json={"status":"Closed","version":created["version"]})
    assert result.status_code == 422
