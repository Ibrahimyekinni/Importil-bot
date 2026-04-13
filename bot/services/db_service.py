import psycopg2
import psycopg2.extras
from config.settings import NEON_DATABASE_URL


def get_connection():
    """Creates and returns a new psycopg2 connection to the Neon PostgreSQL database."""
    return psycopg2.connect(NEON_DATABASE_URL)


def create_tables():
    """
    Creates the 'users' and 'queries' tables if they don't already exist.
    Safe to call on every startup — uses IF NOT EXISTS.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id               SERIAL PRIMARY KEY,
                    telegram_id      BIGINT UNIQUE NOT NULL,
                    telegram_username VARCHAR(255),
                    email            VARCHAR(255),
                    approved         BOOLEAN DEFAULT FALSE,
                    linked_at        TIMESTAMP DEFAULT NOW(),
                    approved_at      TIMESTAMP
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS queries (
                    id            SERIAL PRIMARY KEY,
                    telegram_id   BIGINT NOT NULL,
                    query_type    VARCHAR(10),
                    query_content TEXT,
                    verdict       VARCHAR(20),
                    full_response TEXT,
                    timestamp     TIMESTAMP DEFAULT NOW()
                );
            """)
        conn.commit()


def save_user(telegram_id, telegram_username, email):
    """
    Inserts a new user into the users table.
    If a user with the same telegram_id already exists, updates their
    username and email instead (upsert).
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (telegram_id, telegram_username, email)
                VALUES (%s, %s, %s)
                ON CONFLICT (telegram_id) DO UPDATE
                    SET telegram_username = EXCLUDED.telegram_username,
                        email             = EXCLUDED.email;
            """, (telegram_id, telegram_username, email))
        conn.commit()


def get_user(telegram_id):
    """
    Returns the full user record for the given telegram_id as a dict,
    or None if no matching user is found.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM users WHERE telegram_id = %s;",
                (telegram_id,)
            )
            return cur.fetchone()


def is_approved(telegram_id):
    """
    Returns True if the user exists and their approved flag is True,
    False in all other cases (user not found, or approved = false).
    """
    user = get_user(telegram_id)
    return bool(user and user["approved"])


def save_query(telegram_id, query_type, query_content, verdict, full_response):
    """
    Saves a compliance query result to the queries table.

    Parameters:
        telegram_id   – Telegram user ID who submitted the query
        query_type    – 'photo' or 'text'
        query_content – The raw text or image description sent by the user
        verdict       – 'allowed', 'rejected', or 'conditional'
        full_response – The full AI-generated compliance report
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO queries
                    (telegram_id, query_type, query_content, verdict, full_response)
                VALUES (%s, %s, %s, %s, %s);
            """, (telegram_id, query_type, query_content, verdict, full_response))
        conn.commit()


def get_all_users():
    """
    Returns all rows from the users table as a list of dicts.
    Used by the admin dashboard to display registered users.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM users ORDER BY linked_at DESC;")
            return cur.fetchall()


def get_all_queries():
    """
    Returns all rows from the queries table as a list of dicts,
    ordered newest first. Used by the admin dashboard history view.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM queries ORDER BY timestamp DESC;")
            return cur.fetchall()


def approve_user(telegram_id):
    """
    Marks a user as approved and records the approval timestamp.
    Called by the admin dashboard when granting bot access.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users
                SET approved    = TRUE,
                    approved_at = NOW()
                WHERE telegram_id = %s;
            """, (telegram_id,))
        conn.commit()


def revoke_user(telegram_id):
    """
    Revokes a user's access by setting approved=false.
    The approved_at timestamp is preserved for audit purposes.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users
                SET approved = FALSE
                WHERE telegram_id = %s;
            """, (telegram_id,))
        conn.commit()
