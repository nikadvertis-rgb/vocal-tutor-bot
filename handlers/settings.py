"""
Обработчик команды /settings.
Позволяет менять тип голоса, пол и просматривать настройки.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import VOICE_TYPES, VOICE_TYPES_BY_GENDER, GENDER_LABELS
from database.models import get_user, set_voice_type, set_gender, upsert_user


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /settings.
    Показывает текущие настройки и кнопки смены голоса/пола.
    """
    user = update.effective_user
    upsert_user(user_id=user.id, username=user.username, first_name=user.first_name)

    db_user = get_user(user.id)
    voice_type = db_user["voice_type"] if db_user else "unknown"
    gender = db_user["gender"] if db_user else None
    voice_name = VOICE_TYPES.get(voice_type, "Не выбран")
    gender_label = GENDER_LABELS.get(gender, "Не указан")

    # Типы голоса для текущего пола (или все, если пол не указан)
    if gender and gender in VOICE_TYPES_BY_GENDER:
        available_types = VOICE_TYPES_BY_GENDER[gender]
    else:
        available_types = VOICE_TYPES

    text = (
        f"*Настройки*\n\n"
        f"*Пол:* {gender_label}\n"
        f"*Тип голоса:* {voice_name}\n\n"
        f"Нажми кнопку ниже, чтобы изменить:"
    )

    keyboard = []

    # Кнопки смены пола
    keyboard.append([
        InlineKeyboardButton(
            f"{'> ' if gender == 'male' else ''}👨 Мужской",
            callback_data="settings_gender_male"
        ),
        InlineKeyboardButton(
            f"{'> ' if gender == 'female' else ''}👩 Женский",
            callback_data="settings_gender_female"
        ),
    ])

    # Кнопки типов голоса
    for voice_id, name in available_types.items():
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
    """Обработчик смены типа голоса через /settings."""
    query = update.callback_query
    await query.answer()

    voice_type = query.data.replace("settings_voice_", "")
    voice_name = VOICE_TYPES.get(voice_type, "Неизвестный")

    user = query.from_user
    set_voice_type(user.id, voice_type)
    context.user_data["voice_type"] = voice_type

    await query.edit_message_text(
        f"✅ *Тип голоса обновлён:* {voice_name}",
        parse_mode="Markdown",
    )


async def settings_gender_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик смены пола через /settings."""
    query = update.callback_query
    await query.answer()

    gender = query.data.replace("settings_gender_", "")
    gender_label = GENDER_LABELS.get(gender, gender)

    user = query.from_user
    set_gender(user.id, gender)
    context.user_data["gender"] = gender

    # Показываем типы голоса для нового пола
    voice_types = VOICE_TYPES_BY_GENDER.get(gender, VOICE_TYPES)

    keyboard = []
    for voice_id, name in voice_types.items():
        keyboard.append([
            InlineKeyboardButton(name, callback_data=f"settings_voice_{voice_id}")
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"✅ *Пол обновлён:* {gender_label}\n\n"
        f"Выбери тип голоса:",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )
