"""
Тесты для ai/coach.py — AI-коуч.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from ai.coach import get_ai_feedback, analyze_voice_type


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

        with patch("ai.coach._client") as mock_client:
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
        """При общей ошибке — запасное сообщение."""
        with patch("ai.coach._client") as mock_client:
            mock_client.chat.completions.create = AsyncMock(
                side_effect=RuntimeError("connection failed")
            )
            result = await get_ai_feedback({
                "exercise_name": "Гамма",
                "accuracy_percent": 50,
                "problem_notes": "Нет",
                "good_notes": "Нет",
            })
        assert "Не удалось" in result


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
