"""
Rate limiter для защиты от abuse.
Ограничивает количество голосовых сообщений на пользователя.
"""

import time
from collections import defaultdict

# Хранилище запросов в памяти: user_id → список timestamp'ов
_user_requests: dict[int, list[float]] = defaultdict(list)

# Лимиты
MAX_REQUESTS_PER_HOUR = 10
WINDOW_SECONDS = 3600  # 1 час


def check_rate_limit(user_id: int) -> bool:
    """
    Проверяет, не превысил ли пользователь лимит запросов.

    Returns:
        True — можно обрабатывать, False — лимит превышен.
    """
    now = time.time()

    # Очищаем устаревшие записи
    _user_requests[user_id] = [
        t for t in _user_requests[user_id]
        if now - t < WINDOW_SECONDS
    ]

    if len(_user_requests[user_id]) >= MAX_REQUESTS_PER_HOUR:
        return False

    _user_requests[user_id].append(now)
    return True


def get_remaining_requests(user_id: int) -> int:
    """Возвращает количество оставшихся запросов в окне."""
    now = time.time()
    active = [t for t in _user_requests.get(user_id, []) if now - t < WINDOW_SECONDS]
    return max(0, MAX_REQUESTS_PER_HOUR - len(active))
