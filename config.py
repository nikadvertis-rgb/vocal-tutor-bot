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

# Z.AI (GLM-4.7 API, OpenAI-совместимый)
ZAI_API_KEY = os.getenv("ZAI_API_KEY")
if not ZAI_API_KEY:
    raise ValueError("ZAI_API_KEY не найден в переменных окружения!")
ZAI_BASE_URL = os.getenv("ZAI_BASE_URL", "https://api.z.ai/api/paas/v4/")

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
