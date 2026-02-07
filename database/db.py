"""
SQLite подключение и миграции.
Создаёт таблицы при первом запуске.
"""

import sqlite3
import logging
from pathlib import Path

from config import DB_PATH

logger = logging.getLogger(__name__)

# Глобальное соединение (singleton)
_connection: sqlite3.Connection | None = None


def get_connection() -> sqlite3.Connection:
    """Возвращает соединение с БД (создаёт если нет)."""
    global _connection
    if _connection is None:
        # Создаём директорию data/ если нет
        db_dir = Path(DB_PATH).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        _connection = sqlite3.connect(DB_PATH)
        _connection.row_factory = sqlite3.Row
        _connection.execute("PRAGMA journal_mode=WAL")
        _connection.execute("PRAGMA foreign_keys=ON")
        logger.info(f"SQLite подключение: {DB_PATH}")
    return _connection


def init_db() -> None:
    """Создаёт таблицы если они не существуют."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            voice_type TEXT DEFAULT 'unknown',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(user_id),
            exercise_id TEXT,
            exercise_name TEXT,
            accuracy_percent REAL,
            duration_seconds REAL,
            pitch_data TEXT,
            ai_feedback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_sessions_user_id
            ON sessions(user_id);

        CREATE INDEX IF NOT EXISTS idx_sessions_created_at
            ON sessions(created_at);
    """)
    conn.commit()
    logger.info("Таблицы БД инициализированы")


def close_db() -> None:
    """Закрывает соединение с БД."""
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None
        logger.info("SQLite соединение закрыто")
