"""
Обработчик команды /start.
Приветствует пользователя и предлагает выбрать тип голоса.
Пошаговое автоопределение через гаммы.
"""

import logging
import traceback
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import VOICE_TYPES, VOICE_TYPES_BY_GENDER, GENDER_LABELS
from database.models import upsert_user, set_voice_type, set_gender

logger = logging.getLogger(__name__)

# Гаммы для тестирования (от низкой к высокой)
VOICE_TEST_DIR = Path(__file__).parent.parent / "exercises" / "audio" / "voice_test"

VOICE_TEST_STEPS = [
    {
        "scale_id": "scale_C3",
        "name": "До мажор (C3-C4)",
        "description": "Средний мужской диапазон",
        "file": "scale_C3.ogg",
    },
    {
        "scale_id": "scale_C4",
        "name": "До мажор (C4-C5)",
        "description": "На октаву выше",
        "file": "scale_C4.ogg",
    },
    {
        "scale_id": "scale_C5",
        "name": "До мажор (C5-C6)",
        "description": "Ещё на октаву выше",
        "file": "scale_C5.ogg",
    },
]


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /start.
    Приветствует пользователя и предлагает выбрать пол.
    """
    user = update.effective_user

    # Сохраняем пользователя в БД
    upsert_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
    )

    welcome_text = (
        f"🎤 *Привет, {user.first_name}!*\n\n"
        f"Я — твой AI-тренер по вокалу.\n\n"
        f"*Что я умею:*\n"
        f"• Анализировать высоту твоего голоса\n"
        f"• Показывать точность попадания в ноты\n"
        f"• Давать персональные советы\n\n"
        f"*Для начала — укажи свой пол:*\n"
        f"_(нужно для точного определения типа голоса)_"
    )

    keyboard = [
        [
            InlineKeyboardButton("👨 Мужской", callback_data="gender_male"),
            InlineKeyboardButton("👩 Женский", callback_data="gender_female"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def gender_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик выбора пола. Показывает типы голоса для этого пола."""
    query = update.callback_query
    await query.answer()

    gender = query.data.replace("gender_", "")  # "male" или "female"
    user = query.from_user

    # Сохраняем пол
    set_gender(user.id, gender)
    context.user_data["gender"] = gender

    gender_label = GENDER_LABELS.get(gender, gender)
    voice_types = VOICE_TYPES_BY_GENDER.get(gender, {})

    keyboard = [
        [InlineKeyboardButton(
            "🎙 Определить автоматически (эксперим.)",
            callback_data="voice_auto_detect"
        )]
    ]
    for voice_id, voice_name in voice_types.items():
        keyboard.append([
            InlineKeyboardButton(voice_name, callback_data=f"voice_{voice_id}")
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"Пол: *{gender_label}*\n\n"
        f"*Теперь выбери тип голоса:*\n"
        f"Можешь выбрать вручную или определить автоматически.",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def voice_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик выбора типа голоса через inline-кнопку.
    """
    query = update.callback_query
    await query.answer()

    # Авто-определение типа голоса — запускаем пошаговый тест
    if query.data == "voice_auto_detect":
        # Инициализируем состояние теста
        context.user_data["voice_test_step"] = 0
        context.user_data["voice_test_data"] = []
        context.user_data["detecting_voice_type"] = True

        await query.edit_message_text(
            "🎙 *Определяем тип голоса (эксперим.)*\n\n"
            "Я отправлю тебе гамму — послушай и спой в ответ.\n"
            "Потом отправлю на октаву выше, и так далее.\n\n"
            "Если будет слишком высоко — нажми кнопку.\n\n"
            "⚠️ _Автоопределение — экспериментальная функция. "
            "Результат может быть неточным._\n\n"
            "Поехали!",
            parse_mode="Markdown"
        )

        # Отправляем первую гамму
        await _send_test_scale(query.message, context, step=0)
        return

    # Кнопка "слишком высоко" — завершаем тест
    if query.data == "voice_too_high":
        await _finish_voice_test(query, context)
        return

    # Ручной выбор типа голоса
    voice_type = query.data.replace("voice_", "")
    voice_name = VOICE_TYPES.get(voice_type, "Неизвестный")

    # Сохраняем в контексте пользователя
    context.user_data["voice_type"] = voice_type

    # Сохраняем в БД
    user = query.from_user
    set_voice_type(user.id, voice_type)

    confirmation_text = (
        f"✅ *Отлично!*\n\n"
        f"Твой тип голоса: *{voice_name}*\n\n"
        f"Теперь ты можешь:\n"
        f"• Отправить мне голосовое сообщение — я проанализирую\n"
        f"• /exercise — получить упражнение\n"
        f"• /warmups — готовые распевки\n"
        f"• /progress — посмотреть свой прогресс\n\n"
        f"🎵 *Начнём?* Отправь голосовое или выбери /exercise"
    )

    await query.edit_message_text(
        confirmation_text,
        parse_mode="Markdown"
    )


async def _send_test_scale(message, context, step: int):
    """Отправляет тестовую гамму для текущего шага."""
    if step >= len(VOICE_TEST_STEPS):
        return

    scale = VOICE_TEST_STEPS[step]
    audio_path = VOICE_TEST_DIR / scale["file"]

    step_num = step + 1
    total = len(VOICE_TEST_STEPS)

    text = (
        f"🎹 *Шаг {step_num}/{total}: {scale['name']}*\n"
        f"_{scale['description']}_\n\n"
        f"Послушай гамму и спой её голосовым сообщением."
    )

    # Кнопка "слишком высоко" (не на первом шаге)
    keyboard = None
    if step > 0:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "⬆️ Слишком высоко для меня",
                callback_data="voice_too_high"
            )]
        ])

    await message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)

    if audio_path.exists():
        try:
            with open(audio_path, "rb") as audio_file:
                await message.reply_voice(
                    voice=audio_file,
                    caption=f"🎹 Спой эту гамму ({scale['name']})",
                )
        except Exception as e:
            logger.warning(f"Не удалось отправить гамму: {e}")
    else:
        logger.warning(f"Файл гаммы не найден: {audio_path}")


async def handle_voice_test_step(update, context, pitch_data: dict):
    """
    Обрабатывает голосовое сообщение в рамках теста голоса.
    Вызывается из voice_handler когда detecting_voice_type=True.

    Returns:
        True если тест продолжается, False если завершён
    """
    step = context.user_data.get("voice_test_step", 0)
    test_data = context.user_data.get("voice_test_data", [])

    # Сохраняем данные этого шага
    test_data.append({
        "step": step,
        "scale": VOICE_TEST_STEPS[step]["scale_id"] if step < len(VOICE_TEST_STEPS) else "unknown",
        "pitch_data": pitch_data["pitch_data"],
    })
    context.user_data["voice_test_data"] = test_data

    # Переходим к следующему шагу
    next_step = step + 1
    context.user_data["voice_test_step"] = next_step

    if next_step < len(VOICE_TEST_STEPS):
        # Есть ещё гаммы — отправляем следующую
        await update.message.reply_text(
            f"✅ Записал! Теперь попробуй на октаву выше."
        )
        await _send_test_scale(update.message, context, next_step)
        return True
    else:
        # Все гаммы спеты — определяем голос
        context.user_data["detecting_voice_type"] = False
        await _determine_voice_from_test(update, context)
        return False


async def _finish_voice_test(query, context):
    """Завершает тест досрочно (кнопка 'слишком высоко')."""
    context.user_data["detecting_voice_type"] = False
    test_data = context.user_data.get("voice_test_data", [])

    if not test_data:
        await query.edit_message_text(
            "Нет данных для анализа. Попробуй /start заново."
        )
        return

    # Используем данные, которые уже есть
    await _determine_voice_from_test_data(query.message, query.from_user, context, test_data)


async def _determine_voice_from_test(update, context):
    """Определяет тип голоса по всем записанным данным."""
    test_data = context.user_data.get("voice_test_data", [])
    user = update.effective_user

    if not test_data:
        await update.message.reply_text(
            "Нет данных для анализа. Попробуй /start заново."
        )
        return

    await _determine_voice_from_test_data(update.message, user, context, test_data)


async def _determine_voice_from_test_data(message, user, context, test_data):
    """Общая логика определения голоса по данным теста."""
    from analysis.pitch import get_pitch_range, get_pitch_median
    from ai.coach import (
        analyze_voice_type_from_test, analyze_voice_type_ai,
        get_voice_confidence, CONFIDENCE_TEXT,
    )

    # Объединяем все pitch data (для отчёта)
    all_pitch_data = []
    for step_data in test_data:
        all_pitch_data.extend(step_data["pitch_data"])

    if not all_pitch_data:
        await message.reply_text(
            "Не удалось распознать голос. Попробуй /start и пой громче."
        )
        return

    try:
        gender = context.user_data.get("gender")
        gender_label = GENDER_LABELS.get(gender, "не указан")

        pitch_range = get_pitch_range(all_pitch_data)
        median_freq = get_pitch_median(all_pitch_data)

        # Гибрид: алгоритм + AI
        algo_type = analyze_voice_type_from_test(test_data, gender=gender)
        ai_type = await analyze_voice_type_ai(test_data, gender=gender)

        # Итоговый результат: AI подтверждает или алгоритм как основа
        if ai_type and ai_type != algo_type:
            detected_type = ai_type  # AI корректирует
            method_note = f"Алгоритм: {VOICE_TYPES.get(algo_type, algo_type)} | AI: {VOICE_TYPES.get(ai_type, ai_type)}"
        elif ai_type:
            detected_type = algo_type  # Совпали
            method_note = f"Алгоритм и AI совпали"
        else:
            detected_type = algo_type  # AI недоступен
            method_note = f"Определено алгоритмом (AI недоступен)"

        voice_name = VOICE_TYPES.get(detected_type, detected_type)
        confidence = get_voice_confidence(all_pitch_data, detected_type)
        confidence_label = CONFIDENCE_TEXT.get(confidence, "")

        # Информация о пройденных шагах
        steps_done = len(test_data)
        last_scale = VOICE_TEST_STEPS[min(steps_done - 1, len(VOICE_TEST_STEPS) - 1)]["name"]

        # Сохраняем
        set_voice_type(user.id, detected_type)
        context.user_data["voice_type"] = detected_type
        context.user_data.pop("voice_test_step", None)
        context.user_data.pop("voice_test_data", None)

        result_text = (
            f"🎙 *Результат анализа голоса (эксперим.)*\n\n"
            f"Пол: {gender_label}\n"
            f"Пройдено шагов: {steps_done}\n"
            f"Максимальная гамма: {last_scale}\n"
            f"Диапазон: {pitch_range[0]:.0f} — {pitch_range[1]:.0f} Hz\n"
            f"Тесситура (медиана): {median_freq:.0f} Hz\n"
            f"Определён тип: *{voice_name}*\n"
            f"Уверенность: {confidence_label}\n"
            f"_{method_note}_\n\n"
            f"⚠️ _Автоопределение — экспериментальная функция. "
            f"Точный тип голоса определит вокальный педагог._\n\n"
            f"Если неточно — выбери вручную: /settings\n\n"
            f"Теперь ты можешь:\n"
            f"• /exercise — упражнения с аудиопримерами\n"
            f"• /warmups — готовые распевки\n"
            f"• /progress — твой прогресс"
        )

        try:
            await message.reply_text(result_text, parse_mode="Markdown")
        except Exception:
            # Markdown ошибка — отправляем без форматирования
            plain = result_text.replace("*", "").replace("_", "")
            await message.reply_text(plain)

    except Exception as e:
        logger.error(f"Ошибка определения типа голоса: {traceback.format_exc()}")
        # Сбрасываем состояние теста
        context.user_data.pop("detecting_voice_type", None)
        context.user_data.pop("voice_test_step", None)
        context.user_data.pop("voice_test_data", None)
        await message.reply_text(
            f"❌ Ошибка определения типа голоса.\n"
            f"Детали: {type(e).__name__}: {e}\n\n"
            f"Выбери тип вручную: /settings"
        )
