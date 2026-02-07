"""
Тесты для analysis/report.py — сравнение с упражнением.
"""

from analysis.report import compare_with_exercise


class TestCompareWithExercise:
    """Тесты compare_with_exercise()."""

    def test_empty_pitch_data(self, sample_exercise):
        """Пустые данные → 0% точности."""
        pitch_data = {"duration": 5.0, "pitch_data": []}
        result = compare_with_exercise(pitch_data, sample_exercise)
        assert result["accuracy_percent"] == 0
        assert "Не удалось" in result["text"]

    def test_perfect_match(self, sample_exercise):
        """Идеальное попадание → 100% точности."""
        # Генерируем pitch_data с точными частотами целевых нот
        pitch_data = {
            "duration": 8.0,
            "pitch_data": [
                {"time": float(i), "frequency": n["frequency"], "confidence": 0.95}
                for i, n in enumerate(sample_exercise["target_notes"])
            ],
        }
        result = compare_with_exercise(pitch_data, sample_exercise)
        assert result["accuracy_percent"] == 100
        assert "Результат" in result["text"]

    def test_report_has_progress_bar(self, sample_pitch_data, sample_exercise):
        """Отчёт содержит progress bar."""
        result = compare_with_exercise(sample_pitch_data, sample_exercise)
        text = result["text"]
        assert "█" in text or "░" in text

    def test_report_has_accuracy(self, sample_pitch_data, sample_exercise):
        """Отчёт содержит процент точности."""
        result = compare_with_exercise(sample_pitch_data, sample_exercise)
        assert "%" in result["text"]
        assert isinstance(result["accuracy_percent"], (int, float))

    def test_problem_notes_string(self, sample_exercise):
        """Проблемные ноты записываются в строку."""
        # Частоты с большим отклонением (50 центов ~ 3% частоты)
        pitch_data = {
            "duration": 4.0,
            "pitch_data": [
                {"time": 0.0, "frequency": 130.81, "confidence": 0.95},  # C3 — точно
                {"time": 1.0, "frequency": 155.0, "confidence": 0.90},   # D3 — мимо
            ],
        }
        result = compare_with_exercise(pitch_data, sample_exercise)
        assert "good_notes" in result or "problem_notes" in result

    def test_no_target_notes(self, sample_pitch_data):
        """Упражнение без целевых нот."""
        exercise = {
            "id": "test",
            "name": "Тест",
            "target_notes": [],
            "tolerance_cents": 50,
        }
        result = compare_with_exercise(sample_pitch_data, exercise)
        assert result["accuracy_percent"] == 0
