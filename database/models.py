"""
CRUD операции с таблицами users и sessions.
"""

import json
import logging
from datetime import datetime, timedelta

from database.db import get_connection

logger = logging.getLogger(__name__)


# ─── Users ────────────────────────────────────────────────────────────

def upsert_user(user_id: int, username: str = None, first_name: str = None) -> None:
    """Создаёт или обновляет пользователя."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO users (user_id, username, first_name)
           VALUES (?, ?, ?)
           ON CONFLICT(user_id) DO UPDATE SET
               username = COALESCE(excluded.username, users.username),
               first_name = COALESCE(excluded.first_name, users.first_name),
               updated_at = CURRENT_TIMESTAMP""",
        (user_id, username, first_name)
    )
    conn.commit()


def set_voice_type(user_id: int, voice_type: str) -> None:
    """Устанавливает тип голоса пользователя."""
    conn = get_connection()
    conn.execute(
        """UPDATE users SET voice_type = ?, updated_at = CURRENT_TIMESTAMP
           WHERE user_id = ?""",
        (voice_type, user_id)
    )
    conn.commit()


def set_gender(user_id: int, gender: str) -> None:
    """Устанавливает пол пользователя ('male' или 'female')."""
    conn = get_connection()
    conn.execute(
        """UPDATE users SET gender = ?, updated_at = CURRENT_TIMESTAMP
           WHERE user_id = ?""",
        (gender, user_id)
    )
    conn.commit()


def get_user(user_id: int) -> dict | None:
    """Возвращает данные пользователя или None."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    return dict(row) if row else None


# ─── Sessions ─────────────────────────────────────────────────────────

def save_session(
    user_id: int,
    exercise_id: str = None,
    exercise_name: str = None,
    accuracy_percent: float = None,
    duration_seconds: float = None,
    pitch_data: dict = None,
    ai_feedback: str = None,
) -> int:
    """
    Сохраняет сессию тренировки.

    Returns:
        ID созданной записи.
    """
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO sessions
           (user_id, exercise_id, exercise_name, accuracy_percent,
            duration_seconds, pitch_data, ai_feedback)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            exercise_id,
            exercise_name,
            accuracy_percent,
            duration_seconds,
            json.dumps(pitch_data) if pitch_data else None,
            ai_feedback,
        )
    )
    conn.commit()
    logger.info(f"Сессия сохранена: user={user_id}, exercise={exercise_id}")
    return cursor.lastrowid


# ─── Statistics ───────────────────────────────────────────────────────

def get_user_stats(user_id: int) -> dict:
    """
    Возвращает полную статистику пользователя.

    Returns:
        dict с ключами:
        - total_sessions: int
        - total_minutes: float
        - avg_accuracy: float | None
        - week_sessions: int
        - week_best: float | None
        - last_session_date: str | None
    """
    conn = get_connection()

    # Общая статистика
    row = conn.execute(
        """SELECT
               COUNT(*) as total_sessions,
               COALESCE(SUM(duration_seconds), 0) as total_seconds,
               AVG(accuracy_percent) as avg_accuracy,
               MAX(created_at) as last_session
           FROM sessions WHERE user_id = ?""",
        (user_id,)
    ).fetchone()

    total_sessions = row["total_sessions"]
    total_minutes = round(row["total_seconds"] / 60, 1)
    avg_accuracy = round(row["avg_accuracy"], 1) if row["avg_accuracy"] else None
    last_session = row["last_session"]

    # Статистика за 7 дней
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    week_row = conn.execute(
        """SELECT
               COUNT(*) as week_sessions,
               MAX(accuracy_percent) as week_best
           FROM sessions
           WHERE user_id = ? AND created_at >= ?""",
        (user_id, week_ago)
    ).fetchone()

    return {
        "total_sessions": total_sessions,
        "total_minutes": total_minutes,
        "avg_accuracy": avg_accuracy,
        "week_sessions": week_row["week_sessions"],
        "week_best": round(week_row["week_best"], 1) if week_row["week_best"] else None,
        "last_session_date": last_session,
    }


def get_recent_sessions(user_id: int, limit: int = 5) -> list[dict]:
    """Возвращает последние N сессий пользователя."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT exercise_name, accuracy_percent, duration_seconds, created_at
           FROM sessions
           WHERE user_id = ?
           ORDER BY id DESC
           LIMIT ?""",
        (user_id, limit)
    ).fetchall()
    return [dict(r) for r in rows]
