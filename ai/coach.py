"""
AI-коуч через Z.AI GLM-4.7 API (OpenAI-совместимый).
Фолбэк на OpenRouter (бесплатные модели) если Z.AI недоступен.
"""

import logging
from openai import AsyncOpenAI, APIError
from config import (
    ZAI_API_KEY, ZAI_BASE_URL, ZAI_MODEL,
    OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODELS,
)

logger = logging.getLogger(__name__)

# Клиент Z.AI (OpenAI-совместимый)
_client = AsyncOpenAI(api_key=ZAI_API_KEY, base_url=ZAI_BASE_URL)

# Клиент OpenRouter (фолбэк)
_openrouter_client = (
    AsyncOpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)
    if OPENROUTER_API_KEY else None
)


async def _ai_request(prompt: str, max_tokens: int = 300) -> str | None:
    """
    Отправляет запрос к AI с цепочкой фолбэков:
    Z.AI → OpenRouter (несколько моделей) → None.

    Returns:
        Текст ответа или None если все провайдеры недоступны.
    """
    # 1. Пробуем Z.AI
    try:
        response = await _client.chat.completions.create(
            model=ZAI_MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.warning(f"Z.AI недоступен: {type(e).__name__}: {e}")

    # 2. Пробуем OpenRouter модели по очереди
    if _openrouter_client:
        for model in OPENROUTER_MODELS:
            try:
                response = await _openrouter_client.chat.completions.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )
                logger.info(f"OpenRouter OK: {model}")
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"OpenRouter {model}: {type(e).__name__}: {e}")

    return None


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

    result = await _ai_request(prompt, max_tokens=300)
    if result:
        return result
    return "(AI временно недоступен)"


async def analyze_voice_type(pitch_range: tuple, median_freq: float = 0.0) -> str:
    """
    Определяет тип голоса по диапазону и медиане.
    Используется как фолбэк при обычной записи (не пошаговый тест).
    """
    min_freq, max_freq = pitch_range

    if median_freq > 0:
        if median_freq >= 350:
            return "soprano"
        elif median_freq >= 250:
            if max_freq > 700:
                return "mezzo"
            else:
                return "tenor"
        elif median_freq >= 185:
            return "tenor"
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


def analyze_voice_type_from_test(test_data: list, gender: str = None) -> str:
    """
    Определяет тип голоса по данным пошагового теста с гаммами.

    Принцип: НИЖНИЙ конец диапазона (первая гамма) определяет тип голоса.
    Количество пройденных шагов показывает ширину диапазона, но НЕ тип.

    С учётом пола:
    - male → только bass / baritone / tenor
    - female → только alto / mezzo / soprano
    - None → старая логика (без ограничений)

    Args:
        test_data: Список словарей с ключами step, scale, pitch_data
        gender: "male", "female" или None

    Returns:
        Тип голоса: bass, baritone, tenor, alto, mezzo, soprano
    """
    import numpy as np

    if not test_data:
        if gender == "female":
            return "mezzo"
        return "baritone"

    steps_completed = len(test_data)

    first_step_data = test_data[0]["pitch_data"]
    if not first_step_data:
        if gender == "female":
            return "mezzo"
        return "baritone"

    first_freqs = [p["frequency"] for p in first_step_data]
    low_end = float(np.percentile(first_freqs, 5))
    first_median = float(np.median(first_freqs))

    if gender == "male":
        # Мужской: только bass / baritone / tenor
        if steps_completed == 1:
            if first_median < 155:
                return "bass"
            else:
                return "baritone"
        elif steps_completed == 2:
            if first_median < 155:
                return "baritone"
            else:
                return "tenor"
        else:
            return "tenor"

    elif gender == "female":
        # Женский: только alto / mezzo / soprano
        if steps_completed == 1:
            if first_median < 200:
                return "alto"
            else:
                return "mezzo"
        elif steps_completed == 2:
            if first_median < 200:
                return "alto"
            elif first_median < 280:
                return "mezzo"
            else:
                return "soprano"
        else:
            if first_median < 250:
                return "mezzo"
            else:
                return "soprano"

    # Без пола — старая логика
    if low_end < 200:
        if steps_completed == 1:
            if first_median < 155:
                return "bass"
            else:
                return "baritone"
        elif steps_completed == 2:
            if first_median < 155:
                return "baritone"
            else:
                return "tenor"
        else:
            return "tenor"
    elif low_end < 280:
        if steps_completed >= 2:
            return "mezzo"
        else:
            return "tenor"
    else:
        if steps_completed >= 2:
            return "soprano"
        else:
            return "mezzo"


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


async def analyze_voice_type_ai(test_data: list, gender: str) -> str | None:
    """
    Определяет тип голоса через AI (Z.AI → OpenRouter фолбэк).
    Дополнительный метод — подтверждает/корректирует алгоритмический результат.

    Returns:
        Тип голоса или None если все провайдеры недоступны.
    """
    import numpy as np

    if not test_data or not gender:
        return None

    valid_types = {
        "male": ["bass", "baritone", "tenor"],
        "female": ["alto", "mezzo", "soprano"],
    }
    allowed = valid_types.get(gender, [])
    if not allowed:
        return None

    gender_ru = "мужской" if gender == "male" else "женский"

    # Формируем описание шагов теста
    steps_desc = []
    for step_info in test_data:
        pd = step_info["pitch_data"]
        if not pd:
            continue
        freqs = [p["frequency"] for p in pd]
        median = float(np.median(freqs))
        low = float(np.min(freqs))
        high = float(np.max(freqs))
        steps_desc.append(
            f"- Шаг {step_info['step'] + 1} ({step_info['scale']}): "
            f"медиана {median:.0f} Hz, диапазон {low:.0f}-{high:.0f} Hz, "
            f"{len(freqs)} фреймов"
        )

    if not steps_desc:
        return None

    prompt = (
        f"Ты — эксперт по вокальной педагогике. Определи тип голоса.\n"
        f"Пол: {gender_ru}\n"
        f"Тест гаммами (от низкой к высокой):\n"
        f"{chr(10).join(steps_desc)}\n"
        f"Ответь ОДНИМ словом из списка: {', '.join(allowed)}"
    )

    result = await _ai_request(prompt, max_tokens=10)
    if not result:
        return None

    result = result.strip().lower()
    # Проверяем что ответ — валидный тип
    if result in allowed:
        return result
    # Пытаемся найти валидный тип в ответе
    for t in allowed:
        if t in result:
            return t
    logger.warning(f"AI вернул невалидный тип: {result}")
    return None
