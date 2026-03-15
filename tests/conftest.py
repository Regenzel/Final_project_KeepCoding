import pytest
import models
from app import app as flask_app


@pytest.fixture
def test_db(tmp_path):
    """Redirect DB to a temporary file for each test."""
    original = models.DB_PATH
    models.DB_PATH = str(tmp_path / "test.db")
    models.init_db()
    yield
    models.DB_PATH = original


@pytest.fixture
def client(test_db):
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret-key"
    with flask_app.test_client() as c:
        yield c


@pytest.fixture
def logged_in_client(client):
    """Client with a registered and logged-in user."""
    client.post("/register", data={
        "username": "testuser",
        "password": "testpass123",
        "confirm": "testpass123",
    })
    client.post("/login", data={
        "username": "testuser",
        "password": "testpass123",
    })
    return client
