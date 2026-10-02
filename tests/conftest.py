import os

import pytest


os.environ.setdefault("SECRET_KEY", "test-secret-key")


@pytest.fixture
def flask_app():
    from app.app import app

    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    yield app


@pytest.fixture
def client(flask_app):
    return flask_app.test_client()


@pytest.fixture
def authenticated_client(client):
    with client.session_transaction() as session:
        session["user_id"] = 1

    return client
