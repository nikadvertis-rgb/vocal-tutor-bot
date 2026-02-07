"""
Обработчик команды /warmups.
Готовые распевки — полноценные аудио для разогрева голоса.
"""

import logging
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

WARMUPS_DIR = Path(__file__).parent.parent / "exercises" / "audio" / "warmups"

# Каталог готовых распевок
WARMUPS = [
    {
        "id": "warmup_20min",
        "name": "Полная распевка (20 мин)",
        "description": "Комплексный разогрев голоса на 20 минут. Подходит перед выступлением или серьёзной тренировкой.",
        "file": "warmup_20min.mp3",
    },
    {
        "id": "warmup_10min",
        "name": "Средняя распевка (10 мин)",
        "description": "Сбалансированная распевка на 10 минут. Хороша для ежедневных занятий.",
        "file": "warmup_10min.mp3",
    },
    {
        "id": "warmup_7min",
        "name": "Быстрая распевка (7 мин)",
        "description": "Короткий разогрев на 7 минут. Когда мало времени, но нужно размять голос.",
        "file": "warmup_7min.mp3",
    },
]


async def warmups_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /warmups.
    Показывает список готовых распевок.
    """
    text = (
        "🎙 *Готовые распевки*\n\n"
        "Профессиональные аудио-распевки для разогрева голоса.\n"
        "Выбери подходящую по времени:"
    )

    keyboard = []
    for warmup in WARMUPS:
        keyboard.append([
            InlineKeyboardButton(
                warmup["name"],
                callback_data=f"warmup_{warmup['id']}"
            )
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def warmup_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик выбора распевки через inline-кнопку.
    Отправляет MP3 файл.
    """
    query = update.callback_query
    await query.answer()

    warmup_id = query.data.replace("warmup_", "")

    warmup = next((w for w in WARMUPS if w["id"] == warmup_id), None)

    if not warmup:
        await query.edit_message_text("Распевка не найдена.")
        return

    audio_path = WARMUPS_DIR / warmup["file"]

    if not audio_path.exists():
        await query.edit_message_text(
            f"Файл {warmup['file']} не найден.\n"
            "Попробуй позже."
        )
        return

    await query.edit_message_text(
        f"🎙 *{warmup['name']}*\n\n"
        f"{warmup['description']}\n\n"
        f"Отправляю аудио...",
        parse_mode="Markdown"
    )

    try:
        with open(audio_path, "rb") as audio_file:
            await query.message.reply_audio(
                audio=audio_file,
                title=warmup["name"],
                caption=f"🎙 {warmup['name']}\n{warmup['description']}",
            )
    except Exception as e:
        logger.error(f"Ошибка отправки распевки {warmup_id}: {e}")
        await query.message.reply_text(
            "Не удалось отправить файл. Возможно, он слишком большой."
        )
