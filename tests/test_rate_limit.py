"""
Тесты для utils/rate_limit.py — rate limiter.
"""

import time
from unittest.mock import patch

from utils.rate_limit import (
    check_rate_limit,
    get_remaining_requests,
    _user_requests,
    MAX_REQUESTS_PER_HOUR,
)


class TestCheckRateLimit:
    """Тесты check_rate_limit()."""

    def setup_method(self):
        """Очищаем state перед каждым тестом."""
        _user_requests.clear()

    def test_first_request_allowed(self):
        """Первый запрос всегда разрешён."""
        assert check_rate_limit(123) is True

    def test_under_limit(self):
        """9 запросов из 10 — разрешено."""
        for _ in range(9):
            check_rate_limit(123)
        assert check_rate_limit(123) is True

    def test_at_limit(self):
        """10 запросов — лимит достигнут, 11-й запрещён."""
        for _ in range(MAX_REQUESTS_PER_HOUR):
            check_rate_limit(123)
        assert check_rate_limit(123) is False

    def test_different_users_independent(self):
        """Лимиты разных пользователей независимы."""
        for _ in range(MAX_REQUESTS_PER_HOUR):
            check_rate_limit(111)
        # Пользователь 111 заблокирован
        assert check_rate_limit(111) is False
        # Пользователь 222 — нет
        assert check_rate_limit(222) is True

    def test_old_requests_expire(self):
        """Устаревшие запросы (>1 час) не считаются."""
        old_time = time.time() - 3700  # > 1 часа назад
        _user_requests[123] = [old_time] * MAX_REQUESTS_PER_HOUR
        # Должен пройти — старые записи очищены
        assert check_rate_limit(123) is True


class TestGetRemainingRequests:
    """Тесты get_remaining_requests()."""

    def setup_method(self):
        _user_requests.clear()

    def test_new_user_full_limit(self):
        """Новый пользователь — все запросы доступны."""
        assert get_remaining_requests(999) == MAX_REQUESTS_PER_HOUR

    def test_after_one_request(self):
        """После 1 запроса — на 1 меньше."""
        check_rate_limit(123)
        assert get_remaining_requests(123) == MAX_REQUESTS_PER_HOUR - 1

    def test_at_limit_zero_remaining(self):
        """При лимите — 0 оставшихся."""
        for _ in range(MAX_REQUESTS_PER_HOUR):
            check_rate_limit(123)
        assert get_remaining_requests(123) == 0
