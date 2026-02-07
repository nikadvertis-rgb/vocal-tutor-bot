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
    """Тесты analyze_voice_type()."""

    @pytest.mark.asyncio
    async def test_soprano(self):
        assert await analyze_voice_type((300, 1100)) == "soprano"

    @pytest.mark.asyncio
    async def test_bass(self):
        assert await analyze_voice_type((80, 300)) == "bass"

    @pytest.mark.asyncio
    async def test_tenor(self):
        assert await analyze_voice_type((200, 500)) == "tenor"

    @pytest.mark.asyncio
    async def test_baritone_low_min(self):
        assert await analyze_voice_type((100, 500)) == "baritone"
