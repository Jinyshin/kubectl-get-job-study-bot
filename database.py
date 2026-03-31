import sqlite3
from contextlib import contextmanager

DB_PATH = "bot.db"

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_conn() as conn:
        c = conn.cursor()

        c.executescript("""
            CREATE TABLE IF NOT EXISTS weekly_participants (
                discord_id  TEXT,
                week_start  DATE,
                PRIMARY KEY (discord_id, week_start)
            );

            CREATE TABLE IF NOT EXISTS wake_logs (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id    TEXT,
                certified_at  DATETIME
            );

            CREATE TABLE IF NOT EXISTS ct_logs (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id    TEXT,
                certified_at  DATETIME
            );

            CREATE TABLE IF NOT EXISTS daily_logs (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id    TEXT,
                content       TEXT,
                certified_at  DATETIME
            );

            CREATE TABLE IF NOT EXISTS wake_recruit_messages (
                message_id   TEXT PRIMARY KEY,
                week_start   DATE
            );
        """)

        conn.commit()