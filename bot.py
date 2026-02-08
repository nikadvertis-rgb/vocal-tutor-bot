"""
Vocal Tutor Bot — Главная точка входа.

Telegram-бот для тренировки вокала.
Пользователь отправляет голосовое сообщение — бот анализирует
высоту звука, находит проблемные места, даёт персональный совет через AI.
"""

import logging
from telegram import BotCommand, Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import TELEGRAM_TOKEN
from database.db import init_db, close_db
from utils.audio import check_ffmpeg
from handlers.start import start_command, gender_callback, voice_type_callback
from handlers.voice import voice_handler
from handlers.exercise import exercise_command, exercise_callback
from handlers.progress import progress_command
from handlers.help import help_command
from handlers.settings import settings_command, settings_voice_callback, settings_gender_callback
from handlers.warmups import warmups_command, warmup_callback

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Запуск бота."""

    # Проверяем FFmpeg
    if not check_ffmpeg():
        logger.error("FFmpeg не найден! Установи: apt install ffmpeg (Linux) или brew install ffmpeg (macOS)")
        raise RuntimeError("FFmpeg не установлен — необходим для конвертации аудио")

    # Инициализируем базу данных
    init_db()

    # Создаём приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("exercise", exercise_command))
    application.add_handler(CommandHandler("progress", progress_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("warmups", warmups_command))

    # Обработчик callback-кнопок
    application.add_handler(CallbackQueryHandler(gender_callback, pattern="^gender_"))
    application.add_handler(CallbackQueryHandler(voice_type_callback, pattern="^voice_"))
    application.add_handler(CallbackQueryHandler(exercise_callback, pattern="^exercise_"))
    application.add_handler(CallbackQueryHandler(settings_gender_callback, pattern="^settings_gender_"))
    application.add_handler(CallbackQueryHandler(settings_voice_callback, pattern="^settings_voice_"))
    application.add_handler(CallbackQueryHandler(warmup_callback, pattern="^warmup_"))
    
    # Обработчик голосовых сообщений
    application.add_handler(MessageHandler(filters.VOICE, voice_handler))
    
    # Устанавливаем меню команд при старте
    async def post_init(app) -> None:
        await app.bot.set_my_commands([
            BotCommand("start", "Начать работу"),
            BotCommand("exercise", "Выбрать упражнение"),
            BotCommand("warmups", "Готовые распевки"),
            BotCommand("progress", "Мой прогресс"),
            BotCommand("settings", "Настройки"),
            BotCommand("help", "Справка"),
        ])
        logger.info("Меню команд установлено")

    application.post_init = post_init

    # Graceful shutdown — закрываем БД при остановке
    async def post_shutdown(app) -> None:
        close_db()
        logger.info("Бот остановлен, БД закрыта")

    application.post_shutdown = post_shutdown

    # Запускаем бота
    logger.info("🎤 Vocal Tutor Bot запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
