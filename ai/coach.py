"""
AI-коуч через Z.AI GLM-4.7 API (OpenAI-совместимый).
Генерирует персональные рекомендации на основе анализа.
"""

import logging
from openai import AsyncOpenAI, APIError
from config import ZAI_API_KEY, ZAI_BASE_URL, ZAI_MODEL

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
            model=ZAI_MODEL,
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


async def analyze_voice_type(pitch_range: tuple, median_freq: float = 0.0) -> str:
    """
    Определяет тип голоса по диапазону и медиане (тесситуре).

    Медиана — основной критерий: приближение к тесситуре (зоне комфорта).
    Диапазон (перцентили 5/95) — дополнительный сигнал.

    Типичные диапазоны (по данным вокальной педагогики):
      Бас:        E2–E4  (82–330 Hz),  медиана ~110–150
      Баритон:    A2–A4  (110–440 Hz), медиана ~130–185
      Тенор:      C3–C5  (131–523 Hz), медиана ~160–260
      Меццо:      A3–A5  (220–880 Hz), медиана ~220–340
      Сопрано:    C4–C6  (262–1047 Hz),медиана ~300–520

    Args:
        pitch_range: Tuple (min_freq, max_freq) в Hz (перцентили 5/95)
        median_freq: Медианная частота в Hz

    Returns:
        Рекомендуемый тип голоса
    """
    min_freq, max_freq = pitch_range

    # Если есть медиана — используем её как основной критерий
    if median_freq > 0:
        if median_freq >= 350:
            return "soprano"
        elif median_freq >= 250:
            if max_freq > 700:
                return "mezzo"
            else:
                return "tenor"
        elif median_freq >= 185:
            if max_freq > 500:
                return "tenor"
            elif max_freq > 400:
                return "tenor"
            else:
                return "baritone"
        elif median_freq >= 140:
            if max_freq > 400:
                return "tenor"
            else:
                return "baritone"
        else:
            if max_freq > 350:
                return "baritone"
            else:
                return "bass"

    # Фолбэк: только по диапазону (менее точно)
    if max_freq > 1000:
        return "soprano"
    elif max_freq > 700:
        return "mezzo"
    elif max_freq > 400:
        return "tenor"
    elif max_freq > 300:
        return "baritone"
    else:
        return "bass"


def get_voice_confidence(pitch_data: list, detected_type: str) -> str:
    """
    Оценивает уверенность определения типа голоса.

    Анализирует:
    - Количество данных (мало фреймов = низкая уверенность)
    - Разброс частот (большой разброс = низкая уверенность)

    Returns:
        "high", "medium" или "low"
    """
    if len(pitch_data) < 20:
        return "low"

    frequencies = [p["frequency"] for p in pitch_data]
    import numpy as np
    std = np.std(frequencies)
    mean = np.mean(frequencies)
    cv = std / mean if mean > 0 else 1.0  # коэффициент вариации

    if len(pitch_data) >= 50 and cv < 0.3:
        return "high"
    elif len(pitch_data) >= 30 and cv < 0.5:
        return "medium"
    else:
        return "low"


CONFIDENCE_TEXT = {
    "high": "Высокая уверенность",
    "medium": "Средняя уверенность",
    "low": "Низкая уверенность (запиши более длинный фрагмент)",
}
