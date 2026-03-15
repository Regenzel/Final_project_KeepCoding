import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from models import get_db


def create_user(username, password):
    """Create a new user. Returns True on success, False if username is taken."""
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, generate_password_hash(password))
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_user_by_username(username):
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return user


def verify_password(username, password):
    """Return the user row if credentials are valid, None otherwise."""
    user = get_user_by_username(username)
    if user and check_password_hash(user["password_hash"], password):
        return user
    return None
