"""
Конфигурация приложения.
Загружает переменные окружения из .env файла.
"""

import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не найден в переменных окружения!")

# AI Provider (любой OpenAI-совместимый API)
AI_API_KEY = os.getenv("AI_API_KEY", os.getenv("ZAI_API_KEY", ""))
if not AI_API_KEY:
    raise ValueError(
        "AI_API_KEY не найден в переменных окружения!\n"
        "Укажите ключ любого OpenAI-совместимого API в .env файле.\n"
        "Подробности: README.md → Настройка AI-провайдера"
    )
AI_BASE_URL = os.getenv("AI_BASE_URL", os.getenv("ZAI_BASE_URL", "https://api.openai.com/v1"))
AI_MODEL = os.getenv("AI_MODEL", os.getenv("ZAI_MODEL", "gpt-4o-mini"))

# SQLite
DB_PATH = os.getenv("DB_PATH", "data/vocal_tutor.db")

# Константы приложения
MAX_VOICE_DURATION = 30  # секунд
MIN_VOICE_DURATION = 2   # секунд
SAMPLE_RATE = 22050      # Hz для librosa

# Типы голосов
VOICE_TYPES = {
    "soprano": "Сопрано (женский высокий)",
    "mezzo": "Меццо-сопрано (женский средний)",
    "alto": "Альт (женский низкий)",
    "tenor": "Тенор (мужской высокий)",
    "baritone": "Баритон (мужской средний)",
    "bass": "Бас (мужской низкий)",
}

# Типы голосов, сгруппированные по полу
VOICE_TYPES_BY_GENDER = {
    "male": {
        "bass": "Бас (низкий)",
        "baritone": "Баритон (средний)",
        "tenor": "Тенор (высокий)",
    },
    "female": {
        "alto": "Альт (низкий)",
        "mezzo": "Меццо-сопрано (средний)",
        "soprano": "Сопрано (высокий)",
    },
}

GENDER_LABELS = {
    "male": "Мужской",
    "female": "Женский",
}
