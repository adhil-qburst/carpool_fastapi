import os

import pytest
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture(scope="session", autouse=True)
def set_test_database_url():
    os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL")
