"""
Тесты для database/models.py — CRUD операции.
"""

from database.models import (
    upsert_user,
    get_user,
    set_voice_type,
    save_session,
    get_user_stats,
    get_recent_sessions,
)


class TestUsers:
    """Тесты CRUD для users."""

    def test_create_user(self, in_memory_db):
        """Создание нового пользователя."""
        upsert_user(user_id=1, username="test_user", first_name="Test")
        user = get_user(1)
        assert user is not None
        assert user["username"] == "test_user"
        assert user["first_name"] == "Test"
        assert user["voice_type"] == "unknown"

    def test_upsert_updates_existing(self, in_memory_db):
        """Повторный upsert обновляет данные."""
        upsert_user(user_id=1, username="old_name")
        upsert_user(user_id=1, username="new_name")
        user = get_user(1)
        assert user["username"] == "new_name"

    def test_get_nonexistent_user(self, in_memory_db):
        """Несуществующий пользователь → None."""
        assert get_user(999) is None

    def test_set_voice_type(self, in_memory_db):
        """Установка типа голоса."""
        upsert_user(user_id=1, username="test")
        set_voice_type(1, "tenor")
        user = get_user(1)
        assert user["voice_type"] == "tenor"


class TestSessions:
    """Тесты CRUD для sessions."""

    def test_save_session(self, in_memory_db):
        """Сохранение сессии."""
        upsert_user(user_id=1, username="test")
        session_id = save_session(
            user_id=1,
            exercise_id="major-scale-c",
            exercise_name="Мажорная гамма До",
            accuracy_percent=75.0,
            duration_seconds=10.5,
        )
        assert session_id is not None
        assert session_id > 0

    def test_save_session_with_pitch_data(self, in_memory_db):
        """Сохранение сессии с pitch_data (JSON)."""
        upsert_user(user_id=1, username="test")
        pitch = {"duration": 5.0, "pitch_data": [{"frequency": 440.0}]}
        session_id = save_session(
            user_id=1,
            pitch_data=pitch,
        )
        assert session_id > 0


class TestStatistics:
    """Тесты статистики."""

    def test_empty_stats(self, in_memory_db):
        """Статистика без сессий."""
        upsert_user(user_id=1, username="test")
        stats = get_user_stats(1)
        assert stats["total_sessions"] == 0
        assert stats["total_minutes"] == 0.0
        assert stats["avg_accuracy"] is None

    def test_stats_after_sessions(self, in_memory_db):
        """Статистика после нескольких сессий."""
        upsert_user(user_id=1, username="test")
        save_session(user_id=1, accuracy_percent=70.0, duration_seconds=10.0)
        save_session(user_id=1, accuracy_percent=80.0, duration_seconds=20.0)

        stats = get_user_stats(1)
        assert stats["total_sessions"] == 2
        assert stats["total_minutes"] == 0.5  # 30 сек = 0.5 мин
        assert stats["avg_accuracy"] == 75.0

    def test_recent_sessions(self, in_memory_db):
        """Получение последних сессий."""
        upsert_user(user_id=1, username="test")
        save_session(user_id=1, exercise_name="Гамма 1", accuracy_percent=60.0, duration_seconds=5.0)
        save_session(user_id=1, exercise_name="Гамма 2", accuracy_percent=70.0, duration_seconds=5.0)

        recent = get_recent_sessions(1, limit=5)
        assert len(recent) == 2
        # Последняя сессия первая (ORDER BY created_at DESC)
        assert recent[0]["exercise_name"] == "Гамма 2"

    def test_recent_sessions_empty(self, in_memory_db):
        """Нет сессий → пустой список."""
        upsert_user(user_id=1, username="test")
        recent = get_recent_sessions(1)
        assert recent == []
