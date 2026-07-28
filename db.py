"""Postgres-backed persistence (Supabase) for client records.

Active whenever DATABASE_URL is set (a Supabase connection string). When it is
NOT set, coachlib falls back to a local JSON file, so local development and the
current deploy keep working with zero changes.

Each client is stored as a single JSONB blob keyed by name — it mirrors the
in-app dict model exactly, so nothing above this layer had to change shape.
The `clients` table is created automatically on first connect (no manual SQL).
"""
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
_cache = {}


def enabled():
    return bool(DATABASE_URL)


def _conn():
    """Return a live autocommit connection, (re)connecting if needed."""
    import psycopg2
    c = _cache.get("conn")
    if c is not None and getattr(c, "closed", 1) == 0:
        try:
            with c.cursor() as cur:
                cur.execute("SELECT 1;")
            return c
        except Exception:
            try:
                c.close()
            except Exception:
                pass
            _cache.pop("conn", None)
    c = psycopg2.connect(DATABASE_URL, connect_timeout=10)
    c.autocommit = True
    with c.cursor() as cur:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS clients ("
            "  name text PRIMARY KEY,"
            "  data jsonb NOT NULL DEFAULT '{}'::jsonb,"
            "  updated_at timestamptz NOT NULL DEFAULT now()"
            ");")
        cur.execute(
            "CREATE TABLE IF NOT EXISTS applications ("
            "  id serial PRIMARY KEY,"
            "  data jsonb NOT NULL DEFAULT '{}'::jsonb,"
            "  status text NOT NULL DEFAULT 'new',"
            "  submitted_at timestamptz NOT NULL DEFAULT now()"
            ");")
    _cache["conn"] = c
    return c


def load_all():
    with _conn().cursor() as cur:
        cur.execute("SELECT name, data FROM clients ORDER BY name;")
        return {name: (data or {}) for name, data in cur.fetchall()}


def get_one(name):
    with _conn().cursor() as cur:
        cur.execute("SELECT data FROM clients WHERE name = %s;", (name,))
        row = cur.fetchone()
        return (row[0] or {}) if row else {}


def save_one(name, data):
    from psycopg2.extras import Json
    with _conn().cursor() as cur:
        cur.execute(
            "INSERT INTO clients (name, data, updated_at) "
            "VALUES (%s, %s, now()) "
            "ON CONFLICT (name) DO UPDATE "
            "SET data = EXCLUDED.data, updated_at = now();",
            (name, Json(data)))


def delete_one(name):
    with _conn().cursor() as cur:
        cur.execute("DELETE FROM clients WHERE name = %s;", (name,))


# ---------------- applications ----------------
def save_application(payload):
    from psycopg2.extras import Json
    with _conn().cursor() as cur:
        cur.execute(
            "INSERT INTO applications (data) VALUES (%s) RETURNING id;",
            (Json(payload),))
        return cur.fetchone()[0]


def load_applications():
    with _conn().cursor() as cur:
        cur.execute("SELECT id, data, status, submitted_at "
                    "FROM applications ORDER BY submitted_at DESC;")
        return [{"id": rid, "status": status,
                 "submitted_at": ts.isoformat() if ts else "",
                 **(data or {})}
                for rid, data, status, ts in cur.fetchall()]


def set_application_status(app_id, status):
    with _conn().cursor() as cur:
        cur.execute("UPDATE applications SET status = %s WHERE id = %s;",
                    (status, app_id))


def delete_application(app_id):
    with _conn().cursor() as cur:
        cur.execute("DELETE FROM applications WHERE id = %s;", (app_id,))
