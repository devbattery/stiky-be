import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_PROJECT_NAME", "Stiky API")
os.environ.setdefault("APP_API_V1_PREFIX", "/api/v1")
os.environ.setdefault("APP_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/stiky")
os.environ.setdefault("APP_REDIS__URL", "redis://localhost:6379/0")
os.environ.setdefault("APP_REDIS__USE_SSL", "false")
os.environ.setdefault("APP_JWT__SECRET_KEY", "test-secret-key")
os.environ.setdefault("APP_JWT__ACCESS_TOKEN_TTL_MINUTES", "15")
os.environ.setdefault("APP_JWT__REFRESH_TOKEN_TTL_DAYS", "30")
os.environ.setdefault("APP_MAIL__API_KEY", "test-resend-key")
os.environ.setdefault("APP_MAIL__FROM_EMAIL", "no-reply@example.com")
os.environ.setdefault("APP_CLOUDINARY__CLOUD_NAME", "demo")
os.environ.setdefault("APP_CLOUDINARY__API_KEY", "demo-key")
os.environ.setdefault("APP_CLOUDINARY__API_SECRET", "demo-secret")
os.environ.setdefault("APP_CLOUDINARY__UPLOAD_FOLDER", "stiky/uploads")

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture(scope="session")
def client() -> TestClient:
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
