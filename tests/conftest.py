"""
Общие фикстуры для тестов.
"""

import os
import sys
import sqlite3
import pytest

# Добавляем корень проекта в sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Устанавливаем переменные окружения ДО импорта config
os.environ.setdefault("TELEGRAM_TOKEN", "test-token-123")
os.environ.setdefault("AI_API_KEY", "test-key-123")
os.environ.setdefault("DB_PATH", ":memory:")


@pytest.fixture
def in_memory_db():
    """Создаёт in-memory SQLite базу с таблицами."""
    import database.db as db_module

    # Подменяем глобальное соединение
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            voice_type TEXT DEFAULT 'unknown',
            gender TEXT DEFAULT NULL,
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
    """)
    conn.commit()

    old_conn = db_module._connection
    db_module._connection = conn

    yield conn

    db_module._connection = old_conn
    conn.close()


@pytest.fixture
def sample_pitch_data():
    """Пример данных pitch detection."""
    return {
        "duration": 5.0,
        "pitch_data": [
            {"time": 0.5, "frequency": 131.0, "confidence": 0.95},
            {"time": 1.0, "frequency": 147.0, "confidence": 0.92},
            {"time": 1.5, "frequency": 165.0, "confidence": 0.90},
            {"time": 2.0, "frequency": 175.0, "confidence": 0.88},
            {"time": 2.5, "frequency": 196.0, "confidence": 0.93},
            {"time": 3.0, "frequency": 220.0, "confidence": 0.91},
            {"time": 3.5, "frequency": 247.0, "confidence": 0.89},
            {"time": 4.0, "frequency": 262.0, "confidence": 0.94},
        ],
    }


@pytest.fixture
def sample_exercise():
    """Пример упражнения (мажорная гамма До)."""
    return {
        "id": "major-scale-c",
        "name": "Мажорная гамма До",
        "description": "Пропойте вверх: До Ре Ми Фа Соль Ля Си До",
        "difficulty": 1,
        "target_notes": [
            {"name": "C3", "frequency": 130.81},
            {"name": "D3", "frequency": 146.83},
            {"name": "E3", "frequency": 164.81},
            {"name": "F3", "frequency": 174.61},
            {"name": "G3", "frequency": 196.00},
            {"name": "A3", "frequency": 220.00},
            {"name": "B3", "frequency": 246.94},
            {"name": "C4", "frequency": 261.63},
        ],
        "tolerance_cents": 50,
    }
