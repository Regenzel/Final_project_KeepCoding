from unittest.mock import patch
import models.movement as movement_model
import models.user as user_model


# ── Auth routes ───────────────────────────────────────────────────────────────

class TestAuthRoutes:

    def test_login_page_loads(self, client):
        response = client.get("/login")
        assert response.status_code == 200
        assert b"Sign in" in response.data

    def test_register_page_loads(self, client):
        response = client.get("/register")
        assert response.status_code == 200
        assert b"Create account" in response.data

    def test_register_success(self, client):
        response = client.post("/register", data={
            "username": "alice",
            "password": "testpass123",
            "confirm": "testpass123",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"Sign in" in response.data

    def test_register_password_too_short(self, client):
        response = client.post("/register", data={
            "username": "alice",
            "password": "123",
            "confirm": "123",
        }, follow_redirects=True)
        assert b"at least 6 characters" in response.data

    def test_register_password_mismatch(self, client):
        response = client.post("/register", data={
            "username": "alice",
            "password": "testpass123",
            "confirm": "different",
        }, follow_redirects=True)
        assert b"do not match" in response.data

    def test_register_duplicate_username(self, client):
        client.post("/register", data={
            "username": "alice",
            "password": "testpass123",
            "confirm": "testpass123",
        })
        response = client.post("/register", data={
            "username": "alice",
            "password": "otherpass",
            "confirm": "otherpass",
        }, follow_redirects=True)
        assert b"already taken" in response.data

    def test_login_success_redirects_to_index(self, client):
        client.post("/register", data={
            "username": "alice",
            "password": "testpass123",
            "confirm": "testpass123",
        })
        response = client.post("/login", data={
            "username": "alice",
            "password": "testpass123",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"Movements" in response.data

    def test_login_wrong_password(self, client):
        client.post("/register", data={
            "username": "alice",
            "password": "testpass123",
            "confirm": "testpass123",
        })
        response = client.post("/login", data={
            "username": "alice",
            "password": "wrongpass",
        }, follow_redirects=True)
        assert b"Invalid" in response.data

    def test_logout_redirects_to_login(self, logged_in_client):
        response = logged_in_client.get("/logout", follow_redirects=True)
        assert b"Sign in" in response.data


# ── Protected routes redirect when not logged in ──────────────────────────────

class TestProtectedRoutes:

    def test_index_redirects_if_not_logged_in(self, client):
        response = client.get("/", follow_redirects=True)
        assert b"Sign in" in response.data

    def test_purchase_redirects_if_not_logged_in(self, client):
        response = client.get("/purchase", follow_redirects=True)
        assert b"Sign in" in response.data

    def test_status_redirects_if_not_logged_in(self, client):
        response = client.get("/status", follow_redirects=True)
        assert b"Sign in" in response.data


# ── Main routes ───────────────────────────────────────────────────────────────

class TestMainRoutes:

    def test_index_loads_with_no_movements(self, logged_in_client):
        response = logged_in_client.get("/")
        assert response.status_code == 200
        assert b"No movements yet" in response.data

    def test_index_shows_movements_after_insert(self, logged_in_client):
        user = user_model.get_user_by_username("testuser")
        movement_model.insert_movement(
            user["id"], "2026-01-01", "10:00:00",
            "EUR", 1000.0, "BTC", 0.05
        )
        response = logged_in_client.get("/")
        assert b"BTC" in response.data
        assert b"BUY" in response.data

    def test_purchase_page_loads(self, logged_in_client):
        response = logged_in_client.get("/purchase")
        assert response.status_code == 200
        assert b"Buy / Sell / Trade" in response.data

    def test_purchase_calcular_calls_api(self, logged_in_client):
        with patch("services.crypto_api.convert_price", return_value=0.012345) as mock_api:
            response = logged_in_client.post("/purchase", data={
                "action": "calcular",
                "moneda_from": "EUR",
                "moneda_to": "BTC",
                "cantidad_from": "500",
            })
            assert response.status_code == 200
            mock_api.assert_called_once_with(500.0, "EUR", "BTC")
            assert b"0.012345" in response.data

    def test_purchase_aceptar_saves_movement(self, logged_in_client):
        with patch("services.crypto_api.convert_price", return_value=0.01):
            response = logged_in_client.post("/purchase", data={
                "action": "aceptar",
                "moneda_from": "EUR",
                "moneda_to": "BTC",
                "cantidad_from": "500",
                "cantidad_to": "0.01",
            }, follow_redirects=True)
            assert response.status_code == 200
            assert b"recorded successfully" in response.data

    def test_purchase_insufficient_balance(self, logged_in_client):
        response = logged_in_client.post("/purchase", data={
            "action": "calcular",
            "moneda_from": "BTC",
            "moneda_to": "ETH",
            "cantidad_from": "1.0",
        }, follow_redirects=True)
        assert b"Insufficient balance" in response.data

    def test_purchase_same_currency_rejected(self, logged_in_client):
        response = logged_in_client.post("/purchase", data={
            "action": "calcular",
            "moneda_from": "BTC",
            "moneda_to": "BTC",
            "cantidad_from": "1.0",
        }, follow_redirects=True)
        assert b"must be different" in response.data

    def test_purchase_invalid_amount(self, logged_in_client):
        response = logged_in_client.post("/purchase", data={
            "action": "calcular",
            "moneda_from": "EUR",
            "moneda_to": "BTC",
            "cantidad_from": "abc",
        }, follow_redirects=True)
        assert b"valid amount" in response.data

    def test_status_page_loads(self, logged_in_client):
        with patch("services.crypto_api.get_price_in_eur", return_value=0.0):
            response = logged_in_client.get("/status")
            assert response.status_code == 200
            assert b"Portfolio Status" in response.data

    def test_status_shows_correct_values(self, logged_in_client):
        user = user_model.get_user_by_username("testuser")
        movement_model.insert_movement(
            user["id"], "2026-01-01", "10:00:00",
            "EUR", 1000.0, "BTC", 0.05
        )
        with patch("services.crypto_api.get_price_in_eur", return_value=1200.0):
            response = logged_in_client.get("/status")
            assert b"1000" in response.data
            assert b"1200" in response.data
