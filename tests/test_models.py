import pytest
import models.user as user_model
import models.movement as movement_model


# ── User model ────────────────────────────────────────────────────────────────

class TestUserModel:

    def test_create_user_success(self, test_db):
        assert user_model.create_user("alice", "password123") is True

    def test_create_user_duplicate_username(self, test_db):
        user_model.create_user("alice", "password123")
        assert user_model.create_user("alice", "otherpass") is False

    def test_verify_password_correct(self, test_db):
        user_model.create_user("alice", "password123")
        user = user_model.verify_password("alice", "password123")
        assert user is not None
        assert user["username"] == "alice"

    def test_verify_password_wrong(self, test_db):
        user_model.create_user("alice", "password123")
        assert user_model.verify_password("alice", "wrongpass") is None

    def test_verify_password_unknown_user(self, test_db):
        assert user_model.verify_password("nobody", "password123") is None

    def test_get_user_by_username(self, test_db):
        user_model.create_user("alice", "password123")
        user = user_model.get_user_by_username("alice")
        assert user is not None
        assert user["username"] == "alice"

    def test_get_user_by_username_not_found(self, test_db):
        assert user_model.get_user_by_username("nobody") is None


# ── Movement model ────────────────────────────────────────────────────────────

class TestMovementModel:

    USER_ID = 1

    @pytest.fixture(autouse=True)
    def create_user(self, test_db):
        user_model.create_user("testuser", "testpass123")

    def test_get_balance_no_movements(self):
        assert movement_model.get_balance("BTC", self.USER_ID) == 0.0

    def test_get_balance_after_buy(self):
        movement_model.insert_movement(
            self.USER_ID, "2026-01-01", "10:00:00",
            "EUR", 1000.0, "BTC", 0.05
        )
        assert movement_model.get_balance("BTC", self.USER_ID) == pytest.approx(0.05)
        assert movement_model.get_balance("EUR", self.USER_ID) == pytest.approx(-1000.0)

    def test_get_balance_after_buy_and_sell(self):
        movement_model.insert_movement(
            self.USER_ID, "2026-01-01", "10:00:00",
            "EUR", 1000.0, "BTC", 0.05
        )
        movement_model.insert_movement(
            self.USER_ID, "2026-01-02", "10:00:00",
            "BTC", 0.02, "EUR", 500.0
        )
        assert movement_model.get_balance("BTC", self.USER_ID) == pytest.approx(0.03)

    def test_get_all_movements_empty(self):
        assert movement_model.get_all_movements(self.USER_ID) == []

    def test_get_all_movements_returns_inserted(self):
        movement_model.insert_movement(
            self.USER_ID, "2026-01-01", "10:00:00",
            "EUR", 1000.0, "BTC", 0.05
        )
        movements = movement_model.get_all_movements(self.USER_ID)
        assert len(movements) == 1
        assert movements[0]["moneda_from"] == "EUR"
        assert movements[0]["moneda_to"] == "BTC"

    def test_get_all_movements_isolates_by_user(self):
        user_model.create_user("otheruser", "pass123")
        movement_model.insert_movement(
            self.USER_ID, "2026-01-01", "10:00:00",
            "EUR", 1000.0, "BTC", 0.05
        )
        movement_model.insert_movement(
            2, "2026-01-01", "10:00:00",
            "EUR", 500.0, "ETH", 1.0
        )
        assert len(movement_model.get_all_movements(self.USER_ID)) == 1
        assert len(movement_model.get_all_movements(2)) == 1

    def test_get_status_data(self):
        movement_model.insert_movement(
            self.USER_ID, "2026-01-01", "10:00:00",
            "EUR", 1000.0, "BTC", 0.05
        )
        movement_model.insert_movement(
            self.USER_ID, "2026-01-02", "10:00:00",
            "BTC", 0.02, "EUR", 400.0
        )
        invested, recovered, balances = movement_model.get_status_data(self.USER_ID)
        assert invested == pytest.approx(1000.0)
        assert recovered == pytest.approx(400.0)
        assert "BTC" in balances
        assert balances["BTC"] == pytest.approx(0.03)

    def test_get_status_data_excludes_zero_balances(self):
        movement_model.insert_movement(
            self.USER_ID, "2026-01-01", "10:00:00",
            "EUR", 1000.0, "BTC", 0.05
        )
        movement_model.insert_movement(
            self.USER_ID, "2026-01-02", "10:00:00",
            "BTC", 0.05, "EUR", 1100.0
        )
        _, _, balances = movement_model.get_status_data(self.USER_ID)
        assert "BTC" not in balances
