"""
Тесты для ai/coach.py — AI-коуч.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from ai.coach import get_ai_feedback, analyze_voice_type, analyze_voice_type_from_test


class TestGetAiFeedback:
    """Тесты get_ai_feedback()."""

    @pytest.mark.asyncio
    async def test_returns_string(self):
        """Возвращает строку."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Отличная работа!"

        with patch("ai.coach._client") as mock_client:
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            result = await get_ai_feedback({
                "exercise_name": "Гамма",
                "accuracy_percent": 75,
                "problem_notes": "Фа3 (-35ц)",
                "good_notes": "До3, Ре3",
            })
        assert isinstance(result, str)
        assert "Отличная работа!" in result

    @pytest.mark.asyncio
    async def test_api_error_fallback(self):
        """При ошибке API — запасное сообщение."""
        from openai import APIError

        with patch("ai.coach._client") as mock_client, \
             patch("ai.coach._openrouter_client", None):
            mock_client.chat.completions.create = AsyncMock(
                side_effect=APIError(
                    message="test error",
                    request=MagicMock(),
                    body=None,
                )
            )
            result = await get_ai_feedback({
                "exercise_name": "Гамма",
                "accuracy_percent": 50,
                "problem_notes": "Нет",
                "good_notes": "Нет",
            })
        assert "недоступен" in result

    @pytest.mark.asyncio
    async def test_generic_error_fallback(self):
        """При общей ошибке (все провайдеры) — запасное сообщение."""
        with patch("ai.coach._client") as mock_client, \
             patch("ai.coach._openrouter_client", None):
            mock_client.chat.completions.create = AsyncMock(
                side_effect=RuntimeError("connection failed")
            )
            result = await get_ai_feedback({
                "exercise_name": "Гамма",
                "accuracy_percent": 50,
                "problem_notes": "Нет",
                "good_notes": "Нет",
            })
        assert "недоступен" in result


class TestAnalyzeVoiceType:
    """Тесты analyze_voice_type() — с медианой."""

    @pytest.mark.asyncio
    async def test_soprano_with_median(self):
        """Высокая медиана + высокий max → сопрано."""
        assert await analyze_voice_type((250, 1100), median_freq=400) == "soprano"

    @pytest.mark.asyncio
    async def test_mezzo_with_median(self):
        """Медиана ~280 + высокий max → меццо."""
        assert await analyze_voice_type((200, 800), median_freq=280) == "mezzo"

    @pytest.mark.asyncio
    async def test_tenor_with_median(self):
        """Медиана ~200 + max > 400 → тенор."""
        assert await analyze_voice_type((130, 450), median_freq=200) == "tenor"

    @pytest.mark.asyncio
    async def test_tenor_low_median(self):
        """Медиана ~160 но max > 400 → тенор (не баритон!)."""
        assert await analyze_voice_type((120, 420), median_freq=160) == "tenor"

    @pytest.mark.asyncio
    async def test_baritone_with_median(self):
        """Медиана ~155 + max < 400 → баритон."""
        assert await analyze_voice_type((100, 350), median_freq=155) == "baritone"

    @pytest.mark.asyncio
    async def test_bass_with_median(self):
        """Низкая медиана ~110 + низкий max → бас."""
        assert await analyze_voice_type((75, 250), median_freq=110) == "bass"

    @pytest.mark.asyncio
    async def test_fallback_soprano_no_median(self):
        """Без медианы: max > 1000 → сопрано."""
        assert await analyze_voice_type((300, 1100)) == "soprano"

    @pytest.mark.asyncio
    async def test_fallback_tenor_no_median(self):
        """Без медианы: max > 400 → тенор."""
        assert await analyze_voice_type((130, 450)) == "tenor"

    @pytest.mark.asyncio
    async def test_fallback_bass_no_median(self):
        """Без медианы: max <= 300 → бас."""
        assert await analyze_voice_type((80, 250)) == "bass"


class TestAnalyzeVoiceTypeFromTest:
    """Тесты analyze_voice_type_from_test() — пошаговый тест с гаммами."""

    def _make_pitch_data(self, freqs):
        """Генерирует pitch_data из списка частот."""
        return [{"frequency": f, "time": i * 0.1, "confidence": 0.9} for i, f in enumerate(freqs)]

    # ─── Тесты без gender (обратная совместимость) ─────────────────

    def test_male_wide_range_is_tenor(self):
        """Мужчина прошёл все 3 гаммы → тенор (НЕ сопрано!) — без gender."""
        test_data = [
            {"step": 0, "scale": "scale_C3", "pitch_data": self._make_pitch_data(
                [135, 150, 165, 175, 200, 220, 245, 260]
            )},
            {"step": 1, "scale": "scale_C4", "pitch_data": self._make_pitch_data(
                [265, 295, 330, 350, 395, 440, 495, 525]
            )},
            {"step": 2, "scale": "scale_C5", "pitch_data": self._make_pitch_data(
                [525, 590, 660, 700, 785, 880, 990, 1050]
            )},
        ]
        assert analyze_voice_type_from_test(test_data) == "tenor"

    def test_empty_data_fallback(self):
        """Пустые данные без gender → баритон (фолбэк)."""
        assert analyze_voice_type_from_test([]) == "baritone"

    def test_empty_data_fallback_female(self):
        """Пустые данные с gender=female → меццо."""
        assert analyze_voice_type_from_test([], gender="female") == "mezzo"

    # ─── Тесты с gender=male ──────────────────────────────────────

    def test_male_gender_wide_range_is_tenor(self):
        """Мужчина с gender=male прошёл все 3 гаммы → тенор."""
        test_data = [
            {"step": 0, "scale": "scale_C3", "pitch_data": self._make_pitch_data(
                [135, 150, 165, 175, 200, 220, 245, 260]
            )},
            {"step": 1, "scale": "scale_C4", "pitch_data": self._make_pitch_data(
                [265, 295, 330, 350, 395, 440, 495, 525]
            )},
            {"step": 2, "scale": "scale_C5", "pitch_data": self._make_pitch_data(
                [525, 590, 660, 700, 785, 880, 990, 1050]
            )},
        ]
        result = analyze_voice_type_from_test(test_data, gender="male")
        assert result == "tenor"

    def test_male_gender_never_soprano(self):
        """Мужчина НИКОГДА не получает soprano/mezzo/alto."""
        test_data = [
            {"step": 0, "scale": "scale_C3", "pitch_data": self._make_pitch_data(
                [135, 150, 165, 175, 200, 220, 245, 260]
            )},
            {"step": 1, "scale": "scale_C4", "pitch_data": self._make_pitch_data(
                [265, 295, 330, 350, 395, 440, 495, 525]
            )},
            {"step": 2, "scale": "scale_C5", "pitch_data": self._make_pitch_data(
                [525, 590, 660, 700, 785, 880, 990, 1050]
            )},
        ]
        result = analyze_voice_type_from_test(test_data, gender="male")
        assert result in ("bass", "baritone", "tenor")

    def test_male_one_step_low_median_bass(self):
        """Мужчина прошёл только 1 гамму с низкой медианой → бас."""
        test_data = [
            {"step": 0, "scale": "scale_C3", "pitch_data": self._make_pitch_data(
                [130, 135, 140, 145, 150, 155, 160, 165]
            )},
        ]
        assert analyze_voice_type_from_test(test_data, gender="male") == "bass"

    def test_male_one_step_baritone(self):
        """Мужчина прошёл 1 гамму с медианой ~190 → баритон."""
        test_data = [
            {"step": 0, "scale": "scale_C3", "pitch_data": self._make_pitch_data(
                [150, 170, 185, 195, 200, 210, 230, 250]
            )},
        ]
        assert analyze_voice_type_from_test(test_data, gender="male") == "baritone"

    def test_male_two_steps_tenor(self):
        """Мужчина прошёл 2 гаммы с медианой >= 155 → тенор."""
        test_data = [
            {"step": 0, "scale": "scale_C3", "pitch_data": self._make_pitch_data(
                [135, 150, 170, 180, 200, 220, 245, 260]
            )},
            {"step": 1, "scale": "scale_C4", "pitch_data": self._make_pitch_data(
                [265, 295, 330, 350, 395, 440, 495, 525]
            )},
        ]
        assert analyze_voice_type_from_test(test_data, gender="male") == "tenor"

    def test_male_two_steps_low_first_baritone(self):
        """Мужчина прошёл 2 гаммы но медиана первой < 155 → баритон."""
        test_data = [
            {"step": 0, "scale": "scale_C3", "pitch_data": self._make_pitch_data(
                [130, 135, 140, 145, 150, 155, 160, 165]
            )},
            {"step": 1, "scale": "scale_C4", "pitch_data": self._make_pitch_data(
                [265, 295, 330, 350, 395, 440, 495, 525]
            )},
        ]
        assert analyze_voice_type_from_test(test_data, gender="male") == "baritone"

    # ─── Тесты с gender=female ─────────────────────────────────────

    def test_female_gender_never_male_types(self):
        """Женщина НИКОГДА не получает bass/baritone/tenor."""
        test_data = [
            {"step": 0, "scale": "scale_C3", "pitch_data": self._make_pitch_data(
                [135, 150, 165, 175, 200, 220, 245, 260]
            )},
            {"step": 1, "scale": "scale_C4", "pitch_data": self._make_pitch_data(
                [265, 295, 330, 350, 395, 440, 495, 525]
            )},
        ]
        result = analyze_voice_type_from_test(test_data, gender="female")
        assert result in ("alto", "mezzo", "soprano")

    def test_female_one_step_low_alto(self):
        """Женщина с низкой медианой (<200) + 1 гамма → альт."""
        test_data = [
            {"step": 0, "scale": "scale_C3", "pitch_data": self._make_pitch_data(
                [135, 150, 165, 175, 190, 195, 200, 210]
            )},
        ]
        assert analyze_voice_type_from_test(test_data, gender="female") == "alto"

    def test_female_one_step_mezzo(self):
        """Женщина с медианой >= 200 + 1 гамма → меццо."""
        test_data = [
            {"step": 0, "scale": "scale_C3", "pitch_data": self._make_pitch_data(
                [200, 210, 230, 250, 260, 270, 280, 290]
            )},
        ]
        assert analyze_voice_type_from_test(test_data, gender="female") == "mezzo"

    def test_female_two_steps_soprano(self):
        """Женщина с высокой медианой (>280) + 2 гаммы → сопрано."""
        test_data = [
            {"step": 0, "scale": "scale_C4", "pitch_data": self._make_pitch_data(
                [290, 310, 330, 350, 395, 440, 495, 525]
            )},
            {"step": 1, "scale": "scale_C5", "pitch_data": self._make_pitch_data(
                [525, 590, 660, 700, 785, 880, 990, 1050]
            )},
        ]
        assert analyze_voice_type_from_test(test_data, gender="female") == "soprano"

    def test_female_three_steps_mezzo(self):
        """Женщина с медианой < 250 + 3 гаммы → меццо."""
        test_data = [
            {"step": 0, "scale": "scale_C3", "pitch_data": self._make_pitch_data(
                [180, 190, 200, 210, 220, 230, 240, 250]
            )},
            {"step": 1, "scale": "scale_C4", "pitch_data": self._make_pitch_data(
                [265, 295, 330, 350, 395, 440, 495, 525]
            )},
            {"step": 2, "scale": "scale_C5", "pitch_data": self._make_pitch_data(
                [525, 590, 660, 700, 785, 880, 990, 1050]
            )},
        ]
        assert analyze_voice_type_from_test(test_data, gender="female") == "mezzo"

    def test_female_three_steps_soprano(self):
        """Женщина с медианой >= 250 + 3 гаммы → сопрано."""
        test_data = [
            {"step": 0, "scale": "scale_C3", "pitch_data": self._make_pitch_data(
                [240, 250, 260, 270, 280, 290, 300, 310]
            )},
            {"step": 1, "scale": "scale_C4", "pitch_data": self._make_pitch_data(
                [265, 295, 330, 350, 395, 440, 495, 525]
            )},
            {"step": 2, "scale": "scale_C5", "pitch_data": self._make_pitch_data(
                [525, 590, 660, 700, 785, 880, 990, 1050]
            )},
        ]
        assert analyze_voice_type_from_test(test_data, gender="female") == "soprano"
