"""
Тесты для handlers/exercise.py — загрузка упражнений.
"""

from handlers.exercise import load_exercises


class TestLoadExercises:
    """Тесты load_exercises()."""

    def test_loads_exercises(self):
        """Упражнения загружаются из JSON."""
        exercises = load_exercises()
        assert len(exercises) == 10

    def test_exercise_has_required_fields(self):
        """Каждое упражнение имеет обязательные поля."""
        exercises = load_exercises()
        for ex in exercises:
            assert "id" in ex
            assert "name" in ex
            assert "target_notes" in ex
            assert "difficulty" in ex

    def test_target_notes_have_fields(self):
        """Целевые ноты имеют name и frequency."""
        exercises = load_exercises()
        for ex in exercises:
            for note in ex["target_notes"]:
                assert "name" in note
                assert "frequency" in note
                assert note["frequency"] > 0

    def test_difficulty_range(self):
        """Сложность от 1 до 3."""
        exercises = load_exercises()
        for ex in exercises:
            assert 1 <= ex["difficulty"] <= 3

    def test_first_exercise_is_c_major(self):
        """Первое упражнение — мажорная гамма До."""
        exercises = load_exercises()
        assert exercises[0]["id"] == "major-scale-c"
        assert exercises[0]["name"] == "Мажорная гамма До"
