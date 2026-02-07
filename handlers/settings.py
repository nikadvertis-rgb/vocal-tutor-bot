"""
Обработчик команды /settings.
Позволяет менять тип голоса и просматривать настройки.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import VOICE_TYPES
from database.models import get_user, set_voice_type, upsert_user


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /settings.
    Показывает текущие настройки и кнопку смены голоса.
    """
    user = update.effective_user
    upsert_user(user_id=user.id, username=user.username, first_name=user.first_name)

    db_user = get_user(user.id)
    voice_type = db_user["voice_type"] if db_user else "unknown"
    voice_name = VOICE_TYPES.get(voice_type, "Не выбран")

    text = f"""
*Настройки*

*Тип голоса:* {voice_name}

Нажми кнопку ниже, чтобы изменить тип голоса:
"""

    keyboard = []
    for voice_id, name in VOICE_TYPES.items():
        label = f"{'> ' if voice_id == voice_type else ''}{name}"
        keyboard.append([
            InlineKeyboardButton(label, callback_data=f"settings_voice_{voice_id}")
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def settings_voice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик смены типа голоса через /settings.
    """
    query = update.callback_query
    await query.answer()

    voice_type = query.data.replace("settings_voice_", "")
    voice_name = VOICE_TYPES.get(voice_type, "Неизвестный")

    user = query.from_user
    set_voice_type(user.id, voice_type)
    context.user_data["voice_type"] = voice_type

    await query.edit_message_text(
        f"*Тип голоса изменён на:* {voice_name}\n\n"
        f"Теперь упражнения будут подобраны под твой голос.",
        parse_mode="Markdown",
    )
