import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = "movimientos.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            date          TEXT NOT NULL,
            time          TEXT NOT NULL,
            moneda_from   TEXT NOT NULL,
            cantidad_from REAL NOT NULL,
            moneda_to     TEXT NOT NULL,
            cantidad_to   REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()


# ── Auth ──────────────────────────────────────────────────────────────────────

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


# ── Movements ─────────────────────────────────────────────────────────────────

def get_balance(currency, user_id):
    """Return the available balance of a given currency for a user."""
    conn = get_db()
    incoming = conn.execute(
        "SELECT COALESCE(SUM(cantidad_to), 0) FROM movimientos WHERE moneda_to = ? AND user_id = ?",
        (currency, user_id)
    ).fetchone()[0]
    outgoing = conn.execute(
        "SELECT COALESCE(SUM(cantidad_from), 0) FROM movimientos WHERE moneda_from = ? AND user_id = ?",
        (currency, user_id)
    ).fetchone()[0]
    conn.close()
    return incoming - outgoing


def get_all_movements(user_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM movimientos WHERE user_id = ? ORDER BY date DESC, time DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return rows


def insert_movement(user_id, date, time, from_currency, from_amount, to_currency, to_amount):
    conn = get_db()
    conn.execute(
        """INSERT INTO movimientos
           (user_id, date, time, moneda_from, cantidad_from, moneda_to, cantidad_to)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, date, time, from_currency, from_amount, to_currency, to_amount)
    )
    conn.commit()
    conn.close()


def get_status_data(user_id):
    """Return invested, recovered, and balances per crypto for a user."""
    conn = get_db()

    invested = conn.execute(
        "SELECT COALESCE(SUM(cantidad_from), 0) FROM movimientos WHERE moneda_from = 'EUR' AND user_id = ?",
        (user_id,)
    ).fetchone()[0]

    recovered = conn.execute(
        "SELECT COALESCE(SUM(cantidad_to), 0) FROM movimientos WHERE moneda_to = 'EUR' AND user_id = ?",
        (user_id,)
    ).fetchone()[0]

    cryptos_as_from = conn.execute(
        "SELECT DISTINCT moneda_from FROM movimientos WHERE moneda_from != 'EUR' AND user_id = ?",
        (user_id,)
    ).fetchall()
    cryptos_as_to = conn.execute(
        "SELECT DISTINCT moneda_to FROM movimientos WHERE moneda_to != 'EUR' AND user_id = ?",
        (user_id,)
    ).fetchall()
    conn.close()

    all_cryptos = set([r[0] for r in cryptos_as_from] + [r[0] for r in cryptos_as_to])
    balances = {c: get_balance(c, user_id) for c in all_cryptos}
    balances = {c: b for c, b in balances.items() if b > 0}

    return invested, recovered, balances
