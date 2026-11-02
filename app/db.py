"""SQLite local. Un fichier, aucune donnée ne quitte l'ordinateur."""

import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

from app.chart import ACCOUNTS

ROOT = Path(__file__).resolve().parent.parent

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name_fr TEXT NOT NULL,
    name_de TEXT NOT NULL DEFAULT '',
    name_ru TEXT NOT NULL DEFAULT '',
    statement TEXT NOT NULL CHECK (statement IN ('asset', 'liability', 'equity', 'pl', 'closing')),
    analytics_required INTEGER NOT NULL DEFAULT 0 CHECK (analytics_required IN (0, 1)),
    is_vat INTEGER NOT NULL DEFAULT 0 CHECK (is_vat IN (0, 1)),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
);

CREATE TABLE IF NOT EXISTS analytics (
    id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    name_fr TEXT NOT NULL,
    name_de TEXT NOT NULL DEFAULT '',
    name_ru TEXT NOT NULL DEFAULT '',
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    UNIQUE (account_id, code)
);

CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY,
    entry_date TEXT NOT NULL,
    piece TEXT NOT NULL DEFAULT '',
    label TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lines (
    id INTEGER PRIMARY KEY,
    entry_id INTEGER NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    analytic_id INTEGER REFERENCES analytics(id),
    side TEXT NOT NULL CHECK (side IN ('debit', 'credit')),
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0)
);

CREATE INDEX IF NOT EXISTS idx_lines_entry ON lines(entry_id);
CREATE INDEX IF NOT EXISTS idx_lines_account ON lines(account_id);
CREATE INDEX IF NOT EXISTS idx_entries_date ON entries(entry_date);
CREATE INDEX IF NOT EXISTS idx_analytics_account ON analytics(account_id);
"""


def db_path():
    override = os.environ.get("COMPTA_DB")
    if override:
        return Path(override)
    return ROOT / "data" / "compta.sqlite"


def now_stamp():
    return datetime.now().isoformat(timespec="seconds")


@contextmanager
def connect():
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _drop_entry_kind():
    """Ancienne case « à-nouveaux ». Les écritures antérieures à l'exercice restent le solde initial."""
    path = db_path()
    if not path.exists():
        return
    conn = sqlite3.connect(path)
    conn.isolation_level = None
    started = False
    try:
        conn.execute("PRAGMA foreign_keys = OFF")
        columns = [row[1] for row in conn.execute("PRAGMA table_info(entries)")]
        if "kind" not in columns:
            return
        conn.execute("BEGIN")
        started = True
        conn.execute(
            """
            CREATE TABLE entries_new (
                id INTEGER PRIMARY KEY,
                entry_date TEXT NOT NULL,
                piece TEXT NOT NULL DEFAULT '',
                label TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            INSERT INTO entries_new (id, entry_date, piece, label, created_at, updated_at)
            SELECT id, entry_date, piece, label, created_at, updated_at FROM entries
            """
        )
        conn.execute("DROP TABLE entries")
        conn.execute("ALTER TABLE entries_new RENAME TO entries")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_date ON entries(entry_date)")
        conn.execute("COMMIT")
    except Exception:
        if started:
            conn.execute("ROLLBACK")
        raise
    finally:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.close()


def init_db():
    _drop_entry_kind()
    with connect() as conn:
        for statement in SCHEMA.split(";"):
            sql = statement.strip()
            if sql:
                conn.execute(sql)
        count = conn.execute("SELECT COUNT(*) AS c FROM accounts").fetchone()["c"]
        if count == 0:
            conn.executemany(
                """
                INSERT INTO accounts
                    (code, name_fr, name_de, name_ru, statement, is_vat, active, analytics_required)
                VALUES (?, ?, ?, ?, ?, ?, 1, 0)
                """,
                ACCOUNTS,
            )
        if get_setting(conn, "secondary_lang") is None:
            set_setting(conn, "secondary_lang", "ru")
        if get_setting(conn, "company_name") is None:
            set_setting(conn, "company_name", "")
        set_setting(conn, "schema_version", "1")


def get_setting(conn, key, default=None):
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    if row is None:
        return default
    return row["value"]


def set_setting(conn, key, value):
    conn.execute(
        """
        INSERT INTO settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (key, value),
    )


def current_settings(conn):
    lang = get_setting(conn, "secondary_lang", "ru")
    if lang not in ("ru", "de", "off"):
        lang = "ru"
    return {
        "secondary_lang": lang,
        "company_name": get_setting(conn, "company_name", "") or "",
    }


def year_choices(conn, selected):
    row = conn.execute(
        "SELECT MIN(substr(entry_date, 1, 4)) AS a, MAX(substr(entry_date, 1, 4)) AS b FROM entries"
    ).fetchone()
    today = date.today().year
    start = min(today - 1, selected)
    end = max(today + 1, selected)
    if row["a"]:
        start = min(start, int(row["a"]))
    if row["b"]:
        end = max(end, int(row["b"]))
    return list(range(end, start - 1, -1))


def fetch_accounts(conn):
    rows = conn.execute("SELECT * FROM accounts ORDER BY CAST(code AS INTEGER), code").fetchall()
    return [dict(row) for row in rows]


def fetch_account(conn, account_id):
    row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    return dict(row) if row else None


def fetch_account_by_code(conn, code):
    row = conn.execute("SELECT * FROM accounts WHERE code = ?", (code,)).fetchone()
    return dict(row) if row else None


def account_has_lines(conn, account_id):
    row = conn.execute("SELECT 1 FROM lines WHERE account_id = ? LIMIT 1", (account_id,)).fetchone()
    return row is not None


def fetch_analytics(conn, account_id=None):
    if account_id is None:
        rows = conn.execute(
            "SELECT * FROM analytics ORDER BY account_id, code COLLATE NOCASE, id"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM analytics WHERE account_id = ? ORDER BY code COLLATE NOCASE, id",
            (account_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def analytic_has_lines(conn, analytic_id):
    row = conn.execute(
        "SELECT 1 FROM lines WHERE analytic_id = ? LIMIT 1", (analytic_id,)
    ).fetchone()
    return row is not None


def code_taken(conn, code, ignore_id=None):
    if ignore_id is None:
        row = conn.execute("SELECT id FROM accounts WHERE code = ?", (code,)).fetchone()
    else:
        row = conn.execute(
            "SELECT id FROM accounts WHERE code = ? AND id <> ?", (code, ignore_id)
        ).fetchone()
    return row is not None


def analytic_code_taken(conn, account_id, code, ignore_id=None):
    if ignore_id is None:
        row = conn.execute(
            "SELECT id FROM analytics WHERE account_id = ? AND lower(code) = lower(?)",
            (account_id, code),
        ).fetchone()
    else:
        row = conn.execute(
            """
            SELECT id FROM analytics
            WHERE account_id = ? AND lower(code) = lower(?) AND id <> ?
            """,
            (account_id, code, ignore_id),
        ).fetchone()
    return row is not None


def insert_account(conn, fields):
    cur = conn.execute(
        """
        INSERT INTO accounts
            (code, name_fr, name_de, name_ru, statement, analytics_required, is_vat, active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            fields["code"],
            fields["name_fr"],
            fields["name_de"],
            fields["name_ru"],
            fields["statement"],
            fields["analytics_required"],
            fields["is_vat"],
            fields["active"],
        ),
    )
    return cur.lastrowid


def update_account(conn, account_id, fields):
    conn.execute(
        """
        UPDATE accounts
        SET code = ?, name_fr = ?, name_de = ?, name_ru = ?, statement = ?,
            analytics_required = ?, is_vat = ?, active = ?
        WHERE id = ?
        """,
        (
            fields["code"],
            fields["name_fr"],
            fields["name_de"],
            fields["name_ru"],
            fields["statement"],
            fields["analytics_required"],
            fields["is_vat"],
            fields["active"],
            account_id,
        ),
    )


def delete_account(conn, account_id):
    conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))


def insert_analytic(conn, account_id, fields):
    cur = conn.execute(
        """
        INSERT INTO analytics (account_id, code, name_fr, name_de, name_ru, active)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            account_id,
            fields["code"],
            fields["name_fr"],
            fields["name_de"],
            fields["name_ru"],
            fields["active"],
        ),
    )
    return cur.lastrowid


def update_analytic(conn, analytic_id, fields):
    conn.execute(
        """
        UPDATE analytics
        SET code = ?, name_fr = ?, name_de = ?, name_ru = ?, active = ?
        WHERE id = ?
        """,
        (
            fields["code"],
            fields["name_fr"],
            fields["name_de"],
            fields["name_ru"],
            fields["active"],
            analytic_id,
        ),
    )


def delete_analytic(conn, analytic_id):
    conn.execute("DELETE FROM analytics WHERE id = ?", (analytic_id,))


def fetch_analytic(conn, analytic_id):
    row = conn.execute("SELECT * FROM analytics WHERE id = ?", (analytic_id,)).fetchone()
    return dict(row) if row else None


def replace_entry(conn, entry_id, entry_date, piece, label, lines):
    stamp = now_stamp()
    if entry_id is None:
        cur = conn.execute(
            """
            INSERT INTO entries (entry_date, piece, label, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (entry_date, piece, label, stamp, stamp),
        )
        entry_id = cur.lastrowid
    else:
        conn.execute(
            """
            UPDATE entries
            SET entry_date = ?, piece = ?, label = ?, updated_at = ?
            WHERE id = ?
            """,
            (entry_date, piece, label, stamp, entry_id),
        )
        conn.execute("DELETE FROM lines WHERE entry_id = ?", (entry_id,))
    for line in lines:
        conn.execute(
            """
            INSERT INTO lines (entry_id, account_id, analytic_id, side, amount_cents)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                entry_id,
                line["account_id"],
                line["analytic_id"],
                line["side"],
                line["amount_cents"],
            ),
        )
    return entry_id


def fetch_entry(conn, entry_id):
    row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
    if row is None:
        return None
    lines = conn.execute(
        "SELECT * FROM lines WHERE entry_id = ? ORDER BY id", (entry_id,)
    ).fetchall()
    return dict(row), [dict(line) for line in lines]


def delete_entry(conn, entry_id):
    cur = conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    return cur.rowcount > 0


def next_piece(conn, year):
    rows = conn.execute(
        "SELECT piece FROM entries WHERE entry_date BETWEEN ? AND ?",
        (f"{year:04d}-01-01", f"{year:04d}-12-31"),
    ).fetchall()
    nums = [int(row["piece"]) for row in rows if str(row["piece"]).isdigit()]
    if not nums:
        return "1"
    return str(max(nums) + 1)


def entry_count(conn, year):
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM entries WHERE entry_date BETWEEN ? AND ?",
        (f"{year:04d}-01-01", f"{year:04d}-12-31"),
    ).fetchone()
    return row["c"]
