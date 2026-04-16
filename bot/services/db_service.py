import psycopg2
import psycopg2.extras
from config.settings import NEON_DATABASE_URL


def get_connection():
    """
    Creates and returns a new psycopg2 connection to the Neon PostgreSQL database.
    Returns None if the connection fails so callers can degrade gracefully
    instead of crashing the bot.
    """
    try:
        return psycopg2.connect(NEON_DATABASE_URL)
    except psycopg2.OperationalError as e:
        print(f"[db_service] Warning: could not connect to database: {e}")
        return None


def create_tables():
    """
    Creates the 'users' and 'queries' tables if they don't already exist.
    Safe to call on every startup — uses IF NOT EXISTS.
    Does nothing if the database is unreachable.
    """
    conn = get_connection()
    if conn is None:
        return

    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id               SERIAL PRIMARY KEY,
                    telegram_id      BIGINT UNIQUE NOT NULL,
                    telegram_username VARCHAR(255),
                    email            VARCHAR(255),
                    approved         BOOLEAN DEFAULT FALSE,
                    linked_at        TIMESTAMP DEFAULT NOW(),
                    approved_at      TIMESTAMP,
                    language         VARCHAR(5) DEFAULT 'en'
                );
            """)
            # Add language column to existing tables that pre-date this migration
            cur.execute("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS language VARCHAR(5) DEFAULT 'en';
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
            cur.execute("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS conv_state VARCHAR(50) DEFAULT NULL;
            """)
            cur.execute("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS conv_data TEXT DEFAULT NULL;
            """)
        conn.commit()


def save_user(telegram_id, telegram_username, email):
    """
    Inserts a new user into the users table.
    If a user with the same telegram_id already exists, updates their
    username and email instead (upsert).
    Does nothing if the database is unreachable.
    """
    conn = get_connection()
    if conn is None:
        return

    with conn:
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
    or None if no matching user is found or the database is unreachable.
    """
    conn = get_connection()
    if conn is None:
        return None

    with conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM users WHERE telegram_id = %s;",
                (telegram_id,)
            )
            return cur.fetchone()


def is_approved(telegram_id):
    """
    Returns True if the user exists and their approved flag is True,
    False in all other cases (user not found, approved = false, or DB unavailable).
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

    Does nothing if the database is unreachable.
    """
    conn = get_connection()
    if conn is None:
        return

    with conn:
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
    Returns an empty list if the database is unreachable.
    """
    conn = get_connection()
    if conn is None:
        return []

    with conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM users ORDER BY linked_at DESC;")
            return cur.fetchall()


def get_all_queries():
    """
    Returns all rows from the queries table as a list of dicts,
    ordered newest first. Used by the admin dashboard history view.
    Returns an empty list if the database is unreachable.
    """
    conn = get_connection()
    if conn is None:
        return []

    with conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM queries ORDER BY timestamp DESC;")
            return cur.fetchall()


def approve_user(telegram_id):
    """
    Marks a user as approved and records the approval timestamp.
    Called by the admin dashboard when granting bot access.
    Does nothing if the database is unreachable.
    """
    conn = get_connection()
    if conn is None:
        return

    with conn:
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
    Does nothing if the database is unreachable.
    """
    conn = get_connection()
    if conn is None:
        return

    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users
                SET approved = FALSE
                WHERE telegram_id = %s;
            """, (telegram_id,))
        conn.commit()


def update_user_language(telegram_id, language):
    """
    Sets the preferred language ('en' or 'he') for a user.
    Does nothing if the database is unreachable.
    """
    conn = get_connection()
    if conn is None:
        return

    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users
                SET language = %s
                WHERE telegram_id = %s;
            """, (language, telegram_id))
        conn.commit()


def get_user_language(telegram_id):
    """
    Returns the user's preferred language ('en' or 'he').
    Falls back to 'en' if the user is not found or the DB is unreachable.
    """
    user = get_user(telegram_id)
    if user and user.get("language"):
        return user["language"]
    return "en"


def set_user_state(telegram_id, state, data=None):
    """
    Upserts conv_state and conv_data for the given user.
    Pass state=None to clear the conversation state.
    Does nothing if the database is unreachable.
    """
    conn = get_connection()
    if conn is None:
        return

    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (telegram_id, conv_state, conv_data)
                VALUES (%s, %s, %s)
                ON CONFLICT (telegram_id) DO UPDATE
                    SET conv_state = EXCLUDED.conv_state,
                        conv_data  = EXCLUDED.conv_data;
            """, (telegram_id, state, data))
        conn.commit()


def get_user_state(telegram_id):
    """
    Returns (conv_state, conv_data) for the given user.
    Returns (None, None) if the user is not found or the DB is unreachable.
    """
    conn = get_connection()
    if conn is None:
        return (None, None)

    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT conv_state, conv_data FROM users WHERE telegram_id = %s;",
                (telegram_id,)
            )
            row = cur.fetchone()
            if row is None:
                return (None, None)
            return (row[0], row[1])
