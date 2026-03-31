"""Database layer — SQLite schema and helpers for content tracking."""
import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path

import config


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Return a connection with row_factory set to sqlite3.Row."""
    path = db_path or config.DB_PATH
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn: sqlite3.Connection | None = None) -> None:
    """Create all tables if they don't exist."""
    own = conn is None
    if own:
        conn = get_connection()

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS content_pieces (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow         TEXT NOT NULL CHECK(workflow IN ('quick','video')),
            source_type      TEXT NOT NULL,
            source_text      TEXT NOT NULL,
            founder          TEXT,
            platform         TEXT NOT NULL,
            content_type     TEXT NOT NULL,
            title            TEXT,
            body             TEXT NOT NULL,
            status           TEXT NOT NULL DEFAULT 'draft',
            compliance_notes TEXT,
            scheduled_date   TEXT,
            published_date   TEXT,
            metadata_json    TEXT,
            created_at       TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at       TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS content_batches (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow         TEXT NOT NULL,
            founder          TEXT,
            source_summary   TEXT,
            piece_count      INTEGER NOT NULL DEFAULT 0,
            created_at       TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS calendar_entries (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id         INTEGER REFERENCES content_batches(id),
            piece_id         INTEGER REFERENCES content_pieces(id),
            platform         TEXT NOT NULL,
            scheduled_date   TEXT NOT NULL,
            scheduled_time   TEXT,
            content_preview  TEXT,
            status           TEXT NOT NULL DEFAULT 'scheduled',
            created_at       TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS compliance_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            piece_id         INTEGER NOT NULL REFERENCES content_pieces(id),
            action           TEXT NOT NULL,
            reviewer         TEXT,
            notes            TEXT,
            flags_json       TEXT,
            created_at       TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_pieces_status ON content_pieces(status);
        CREATE INDEX IF NOT EXISTS idx_pieces_platform ON content_pieces(platform);
        CREATE INDEX IF NOT EXISTS idx_pieces_workflow ON content_pieces(workflow);
        CREATE INDEX IF NOT EXISTS idx_calendar_date ON calendar_entries(scheduled_date);
    """)

    if own:
        conn.commit()
        conn.close()


# ── CRUD helpers ─────────────────────────────────────────────────────────────

def insert_batch(conn, workflow: str, founder: str | None, source_summary: str, piece_count: int) -> int:
    cur = conn.execute(
        "INSERT INTO content_batches (workflow, founder, source_summary, piece_count) VALUES (?,?,?,?)",
        (workflow, founder, source_summary[:500], piece_count),
    )
    conn.commit()
    return cur.lastrowid


def insert_piece(conn, *, workflow: str, source_type: str, source_text: str,
                 founder: str | None, platform: str, content_type: str,
                 title: str | None, body: str, status: str = "draft",
                 metadata: dict | None = None) -> int:
    cur = conn.execute(
        """INSERT INTO content_pieces
           (workflow, source_type, source_text, founder, platform, content_type,
            title, body, status, metadata_json)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (workflow, source_type, source_text[:2000], founder, platform,
         content_type, title, body, status,
         json.dumps(metadata) if metadata else None),
    )
    conn.commit()
    return cur.lastrowid


def update_piece_status(conn, piece_id: int, new_status: str,
                        compliance_notes: str | None = None) -> None:
    now = datetime.now(timezone.utc).isoformat()
    extra = ""
    params: list = [new_status, now]
    if compliance_notes is not None:
        extra = ", compliance_notes = ?"
        params.append(compliance_notes)
    if new_status == "published":
        extra += ", published_date = ?"
        params.append(now)
    params.append(piece_id)
    conn.execute(
        f"UPDATE content_pieces SET status = ?, updated_at = ?{extra} WHERE id = ?",
        params,
    )
    conn.commit()


def update_piece_body(conn, piece_id: int, body: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE content_pieces SET body = ?, updated_at = ? WHERE id = ?",
        (body, now, piece_id),
    )
    conn.commit()


def insert_calendar_entry(conn, *, batch_id: int | None, piece_id: int | None,
                          platform: str, scheduled_date: str,
                          scheduled_time: str | None = None,
                          content_preview: str | None = None,
                          status: str = "scheduled") -> int:
    cur = conn.execute(
        """INSERT INTO calendar_entries
           (batch_id, piece_id, platform, scheduled_date, scheduled_time, content_preview, status)
           VALUES (?,?,?,?,?,?,?)""",
        (batch_id, piece_id, platform, scheduled_date, scheduled_time,
         content_preview[:500] if content_preview else None, status),
    )
    conn.commit()
    return cur.lastrowid


def insert_compliance_log(conn, piece_id: int, action: str,
                          reviewer: str | None = None, notes: str | None = None,
                          flags: list | None = None) -> int:
    cur = conn.execute(
        "INSERT INTO compliance_log (piece_id, action, reviewer, notes, flags_json) VALUES (?,?,?,?,?)",
        (piece_id, action, reviewer, notes, json.dumps(flags) if flags else None),
    )
    conn.commit()
    return cur.lastrowid


def get_pieces_by_status(conn, status: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM content_pieces WHERE status = ? ORDER BY created_at DESC", (status,)
    ).fetchall()
    return [dict(r) for r in rows]


def get_pieces_by_batch(conn, batch_id: int) -> list[dict]:
    """Get pieces that were created near the same time as a batch (correlation by timing)."""
    batch = conn.execute("SELECT * FROM content_batches WHERE id = ?", (batch_id,)).fetchone()
    if not batch:
        return []
    rows = conn.execute(
        "SELECT * FROM content_pieces WHERE workflow = ? AND created_at >= ? ORDER BY id",
        (dict(batch)["workflow"], dict(batch)["created_at"]),
    ).fetchall()
    return [dict(r) for r in rows]


def get_all_pieces(conn, limit: int = 200) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM content_pieces ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    return [dict(r) for r in rows]


def get_piece(conn, piece_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM content_pieces WHERE id = ?", (piece_id,)).fetchone()
    return dict(row) if row else None


def get_calendar(conn, start_date: str | None = None, end_date: str | None = None) -> list[dict]:
    query = "SELECT * FROM calendar_entries WHERE 1=1"
    params = []
    if start_date:
        query += " AND scheduled_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND scheduled_date <= ?"
        params.append(end_date)
    query += " ORDER BY scheduled_date, scheduled_time"
    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def get_review_queue(conn) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM content_pieces WHERE status IN ('draft','review') ORDER BY created_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def get_compliance_logs(conn, piece_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM compliance_log WHERE piece_id = ? ORDER BY created_at", (piece_id,)
    ).fetchall()
    return [dict(r) for r in rows]


def get_dashboard_stats(conn) -> dict:
    stats = {}
    for status in config.VALID_STATUSES:
        row = conn.execute(
            "SELECT COUNT(*) as c FROM content_pieces WHERE status = ?", (status,)
        ).fetchone()
        stats[status] = dict(row)["c"]
    stats["total"] = sum(stats.values())
    # recent activity
    rows = conn.execute(
        "SELECT * FROM content_pieces ORDER BY updated_at DESC LIMIT 10"
    ).fetchall()
    stats["recent"] = [dict(r) for r in rows]
    return stats
