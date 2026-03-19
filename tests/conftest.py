import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.config import get_settings

settings = get_settings()

# -----------------------------
# Test DB — separate from dev DB
# -----------------------------
TEST_DATABASE_URL = settings.DATABASE_URL.replace(
    "/ai_support_db", "/ai_support_test_db"
)

engine = create_engine(TEST_DATABASE_URL, future=True)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# -----------------------------
# Create/drop all tables once per session
# -----------------------------
@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# -----------------------------
# Each test gets a clean DB via rollback
# -----------------------------
@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# -----------------------------
# Override get_db with test session
# -----------------------------
@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# -----------------------------
# Helper: register + login, return headers
# -----------------------------
@pytest.fixture
def auth_headers(client):
    client.post("/auth/register", json={
        "email": "testuser@example.com",
        "password": "Test@1234"
    })
    response = client.post("/auth/login", json={
        "email": "testuser@example.com",
        "password": "Test@1234"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# -----------------------------
# Helper: agent user headers
# -----------------------------
@pytest.fixture
def agent_headers(client, db):
    from app.auth.models import User, UserRole
    from app.auth.security import hash_password

    agent = User(
        email="agent@example.com",
        hashed_password=hash_password("Agent@1234"),
        role=UserRole.SUPPORT_AGENT,
    )
    db.add(agent)
    db.commit()

    response = client.post("/auth/login", json={
        "email": "agent@example.com",
        "password": "Agent@1234"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# -----------------------------
# Helper: admin user headers
# -----------------------------
@pytest.fixture
def admin_headers(client, db):
    from app.auth.models import User, UserRole
    from app.auth.security import hash_password

    admin = User(
        email="admin@example.com",
        hashed_password=hash_password("Admin@1234"),
        role=UserRole.ADMIN,
    )
    db.add(admin)
    db.commit()

    response = client.post("/auth/login", json={
        "email": "admin@example.com",
        "password": "Admin@1234"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# -----------------------------
# Helper: create a ticket (AI auto-classify mocked)
# -----------------------------
@pytest.fixture
def sample_ticket(client, auth_headers):
    from unittest.mock import patch
    mock_result = {
        "category": "technical",
        "priority": "low",
        "summary": "Test ticket summary.",
        "confidence": 0.9
    }
    with patch("app.ai.services.classify_ticket", return_value=mock_result):
        response = client.post("/tickets/", json={
            "title": "Sample test ticket",
            "description": "This is a test ticket description for testing.",
            "priority": "medium",
            "category": "technical"
        }, headers=auth_headers)
    return response.json()