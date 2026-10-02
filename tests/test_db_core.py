from app import db_core


def test_cloud_database_url_is_used(monkeypatch):
    connection = object()
    received = {}

    def fake_connect(database_url):
        received["database_url"] = database_url
        return connection

    monkeypatch.setattr(db_core, "DATABASE_URL", "postgres://user:pass@host/db")
    monkeypatch.setattr(db_core.psycopg2, "connect", fake_connect)

    result = db_core.DBCore.get_connection()

    assert result is connection
    assert received["database_url"] == "postgresql://user:pass@host/db"


def test_local_database_settings_are_used(monkeypatch):
    connection = object()
    received = {}

    def fake_connect(**database_settings):
        received.update(database_settings)
        return connection

    monkeypatch.setattr(db_core, "DATABASE_URL", None)
    monkeypatch.setattr(db_core, "DB_HOST", "localhost")
    monkeypatch.setattr(db_core, "DB_PORT", "5432")
    monkeypatch.setattr(db_core, "DB_NAME", "paperdesk")
    monkeypatch.setattr(db_core, "DB_USER", "paperdesk_user")
    monkeypatch.setattr(db_core, "DB_PASSWORD", "password")
    monkeypatch.setattr(db_core.psycopg2, "connect", fake_connect)

    result = db_core.DBCore.get_connection()

    assert result is connection
    assert received == {
        "host": "localhost",
        "port": "5432",
        "database": "paperdesk",
        "user": "paperdesk_user",
        "password": "password",
    }
