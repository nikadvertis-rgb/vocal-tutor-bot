"""
Обработчик команды /start.
Приветствует пользователя и предлагает выбрать тип голоса.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import VOICE_TYPES
from database.models import upsert_user, set_voice_type


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /start.
    Приветствует пользователя и показывает кнопки выбора типа голоса.
    """
    user = update.effective_user

    # Сохраняем пользователя в БД
    upsert_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
    )

    welcome_text = f"""
🎤 *Привет, {user.first_name}!*

Я — твой AI-тренер по вокалу.

*Что я умею:*
• Анализировать высоту твоего голоса
• Показывать точность попадания в ноты
• Давать персональные советы

*Для начала выбери свой тип голоса:*
"""

    # Создаём inline-клавиатуру с типами голосов
    keyboard = []
    for voice_id, voice_name in VOICE_TYPES.items():
        keyboard.append([
            InlineKeyboardButton(voice_name, callback_data=f"voice_{voice_id}")
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def voice_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик выбора типа голоса через inline-кнопку.
    """
    query = update.callback_query
    await query.answer()

    # Извлекаем тип голоса из callback_data
    voice_type = query.data.replace("voice_", "")
    voice_name = VOICE_TYPES.get(voice_type, "Неизвестный")

    # Сохраняем в контексте пользователя
    context.user_data["voice_type"] = voice_type

    # Сохраняем в БД
    user = query.from_user
    set_voice_type(user.id, voice_type)

    confirmation_text = f"""
✅ *Отлично!*

Твой тип голоса: *{voice_name}*

Теперь ты можешь:
• Отправить мне голосовое сообщение — я проанализирую
• Использовать /exercise — получить упражнение
• Использовать /progress — посмотреть свой прогресс

🎵 *Начнём?* Отправь голосовое или выбери /exercise
"""

    await query.edit_message_text(
        confirmation_text,
        parse_mode="Markdown"
    )
