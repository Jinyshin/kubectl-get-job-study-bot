import sqlite3
from contextlib import contextmanager
from datetime import date, datetime

DB_PATH = "bot.db"

# Python 3.12+에서 기본 date/datetime adapter가 deprecated.
# 기존 기본 어댑터와 동일한 ISO 포맷으로 명시 등록 → 저장 포맷 변화 없이 경고만 제거.
sqlite3.register_adapter(date, date.isoformat)
sqlite3.register_adapter(datetime, lambda dt: dt.isoformat(sep=" "))

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

            CREATE TABLE IF NOT EXISTS ct_threads (
                date         DATE PRIMARY KEY,
                thread_id    TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS study_activity (
                message_id   TEXT PRIMARY KEY,
                discord_id   TEXT NOT NULL,
                channel_id   TEXT NOT NULL,
                created_at   DATETIME NOT NULL
            );
        """)

        conn.commit()