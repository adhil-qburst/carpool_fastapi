import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from app.main import app

load_dotenv()


@pytest.fixture(scope="session", autouse=True)
def set_test_database_url():
    os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL")


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
