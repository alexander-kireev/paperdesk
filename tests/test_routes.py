import importlib
import re
from pathlib import Path

import pytest

from app.stock.stock_model import Stock


app_module = importlib.import_module("app.app")


def test_protected_route_redirects_anonymous_user(client):
    response = client.get("/my_details")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/log_in")


def test_get_only_routes_reject_post(client, authenticated_client):
    assert authenticated_client.post("/market").status_code == 405
    assert client.post("/sample_market").status_code == 405


def test_sample_market_preserves_symbol_case_when_company_name_is_unavailable(
    client, monkeypatch
):
    monkeypatch.setattr(app_module, "ALL_SYMBOLS", {"AAPL"})
    monkeypatch.setattr(
        app_module,
        "create_stock",
        lambda symbol: Stock(symbol, symbol, "123.45"),
    )

    response = client.get("/sample_market?ticker=AAPL")

    assert response.status_code == 200
    assert response.data.count(b"<strong>AAPL</strong>") == 2


def test_logout_rejects_get(authenticated_client):
    assert authenticated_client.get("/log_out").status_code == 405


def test_post_without_csrf_token_is_rejected(flask_app, client):
    flask_app.config["WTF_CSRF_ENABLED"] = True

    response = client.post("/log_in", data={"email": "test@example.com", "password": "Password123"})

    assert response.status_code == 400


def test_invalid_login_displays_error_and_consumes_flash(client, monkeypatch):
    monkeypatch.setattr(
        app_module,
        "authenticate_user",
        lambda email, password: {
            "success": False,
            "message": "Invalid email address or password.",
        },
    )

    response = client.post(
        "/log_in",
        data={"email": "invalid@example.com", "password": "WrongPassword1"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert response.data.count(b"Invalid email address or password.") == 1

    next_response = client.get("/sample_market")
    assert b"Invalid email address or password." not in next_response.data


def test_all_post_forms_include_csrf_token():
    templates = Path("app/templates").glob("*.html")
    post_form = re.compile(r'<form[^>]*method=["\']POST["\'][^>]*>(.*?)</form>', re.IGNORECASE | re.DOTALL)

    for template in templates:
        contents = template.read_text(encoding="utf-8")
        for form in post_form.findall(contents):
            assert "csrf_token" in form, f"Missing CSRF token in {template}"


@pytest.mark.parametrize("action, service_name", [("BUY", "buy_stock"), ("SELL", "sell_stock")])
def test_place_order_fetches_quote_once_and_passes_stock_to_service(
    authenticated_client, monkeypatch, action, service_name
):
    stock = Stock("Apple", "AAPL", "200.00")
    calls = {"quotes": 0}

    def fake_create_stock(symbol):
        calls["quotes"] += 1
        assert symbol == "aapl"
        return stock

    def fake_trade(user_id, received_stock, number_of_shares):
        assert user_id == 1
        assert received_stock is stock
        assert number_of_shares == 2
        return {"success": True, "message": "Trade completed."}

    monkeypatch.setattr(app_module, "ALL_SYMBOLS", {"AAPL"})
    monkeypatch.setattr(app_module, "create_stock", fake_create_stock)
    monkeypatch.setattr(app_module, service_name, fake_trade)

    response = authenticated_client.post(
        "/place_order",
        data={"action": action, "display_stock_symbol": "AAPL", "order_amount": "2"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/market")
    assert calls["quotes"] == 1


def test_invalid_trade_date_range_does_not_query_service(authenticated_client, monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("Trade service should not be called for an invalid date range")

    monkeypatch.setattr(app_module, "get_user_trade_history", fail_if_called)

    response = authenticated_client.get("/trades?start_date=2026-02-01&end_date=2026-01-01")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/trades")


def test_incomplete_transaction_report_range_does_not_query_service(
    authenticated_client, monkeypatch
):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("Transaction service should not be called for an invalid date range")

    monkeypatch.setattr(app_module, "get_user_transaction_history", fail_if_called)

    response = authenticated_client.post(
        "/transaction_history",
        data={"history_type": "range", "start_date": "2026-01-01", "end_date": ""},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/account")
