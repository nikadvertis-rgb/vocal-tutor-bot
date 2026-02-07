"""
AI-коуч через Z.AI GLM-4.7 API (OpenAI-совместимый).
Генерирует персональные рекомендации на основе анализа.
"""

import logging
from openai import AsyncOpenAI, APIError
from config import ZAI_API_KEY, ZAI_BASE_URL

logger = logging.getLogger(__name__)

# Клиент Z.AI (OpenAI-совместимый)
_client = AsyncOpenAI(api_key=ZAI_API_KEY, base_url=ZAI_BASE_URL)


async def get_ai_feedback(session_data: dict) -> str:
    """
    Генерирует персональный feedback от AI-коуча.

    Args:
        session_data: Данные сессии с ключами:
            - exercise_name: Название упражнения
            - accuracy_percent: Процент точности
            - problem_notes: Строка с проблемными нотами
            - good_notes: Строка с хорошими нотами

    Returns:
        Текст рекомендации от AI
    """
    prompt = f"""Ты — дружелюбный вокальный педагог в Telegram-боте.

Упражнение: {session_data['exercise_name']}
Средняя точность: {session_data['accuracy_percent']}%

Проблемные ноты (>30 центов отклонения):
{session_data['problem_notes']}

Хорошие ноты (<20 центов):
{session_data['good_notes']}

Ответь КРАТКО (3-4 предложения, без Markdown):
1. Похвали за то что получилось
2. Назови главную проблему
3. Дай ОДИН конкретный совет (техника, дыхание, положение гортани и т.д.)
4. Мотивируй продолжать

Стиль: тёплый, на «ты». Эмодзи: 1-2 штуки максимум."""

    try:
        response = await _client.chat.completions.create(
            model="glm-4.7",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    except APIError as e:
        logger.error(f"Z.AI API error: {e}")
        return "(AI временно недоступен)"
    except Exception as e:
        logger.error(f"AI feedback error: {e}")
        return "(Не удалось получить совет от AI)"


async def analyze_voice_type(pitch_range: tuple) -> str:
    """
    Определяет тип голоса по диапазону.

    Args:
        pitch_range: Tuple (min_freq, max_freq) в Hz

    Returns:
        Рекомендуемый тип голоса
    """
    min_freq, max_freq = pitch_range

    if max_freq > 1000:
        return "soprano"
    elif max_freq > 700:
        return "mezzo"
    elif max_freq >= 500:
        if min_freq < 130:
            return "baritone"
        else:
            return "tenor"
    elif max_freq > 350:
        if min_freq < 100:
            return "bass"
        else:
            return "baritone"
    else:
        return "bass"
