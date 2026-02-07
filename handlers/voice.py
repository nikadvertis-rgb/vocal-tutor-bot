"""
Обработчик голосовых сообщений.
Скачивает аудио, анализирует pitch и отправляет результат.
"""

import os
import logging
from telegram import Update
from telegram.ext import ContextTypes

from config import MAX_VOICE_DURATION, MIN_VOICE_DURATION
from utils.audio import download_and_convert_voice
from analysis.pitch import analyze_pitch
from analysis.notes import format_pitch_report
from analysis.report import compare_with_exercise
from ai.coach import get_ai_feedback
from database.models import save_session, upsert_user
from utils.rate_limit import check_rate_limit, get_remaining_requests

logger = logging.getLogger(__name__)


async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик голосовых сообщений.

    1. Проверяет длительность
    2. Скачивает и конвертирует в WAV
    3. Анализирует pitch через librosa
    4. Сравнивает с упражнением (если выбрано)
    5. Получает AI-feedback
    6. Сохраняет сессию в БД
    7. Отправляет результат
    """
    voice = update.message.voice
    user = update.effective_user

    # Проверяем длительность
    duration = voice.duration
    if duration > MAX_VOICE_DURATION:
        await update.message.reply_text(
            f"⚠️ Запись слишком длинная ({duration} сек).\n"
            f"Максимум — {MAX_VOICE_DURATION} секунд."
        )
        return

    if duration < MIN_VOICE_DURATION:
        await update.message.reply_text(
            f"⚠️ Запись слишком короткая ({duration} сек).\n"
            f"Минимум — {MIN_VOICE_DURATION} секунды."
        )
        return

    # Проверяем rate limit
    if not check_rate_limit(user.id):
        remaining = get_remaining_requests(user.id)
        await update.message.reply_text(
            f"⚠️ Слишком много запросов!\n"
            f"Лимит: 10 анализов в час.\n"
            f"Попробуй чуть позже."
        )
        return

    # Показываем статус
    status_message = await update.message.reply_text("⏳ Анализирую твою запись...")

    # Убеждаемся что пользователь в БД
    upsert_user(user_id=user.id, username=user.username, first_name=user.first_name)

    wav_path = None
    try:
        # Скачиваем и конвертируем
        wav_path = await download_and_convert_voice(voice, context)

        # Анализируем pitch
        pitch_data = analyze_pitch(wav_path)

        if not pitch_data["pitch_data"]:
            await status_message.edit_text(
                "😕 Не удалось распознать голос.\n\n"
                "Попробуй:\n"
                "• Записать в более тихом месте\n"
                "• Петь громче и чётче\n"
                "• Держать телефон ближе"
            )
            return

        # Получаем текущее упражнение
        current_exercise = context.user_data.get("current_exercise")

        # Формируем отчёт
        if current_exercise:
            # Сравниваем с целевыми нотами упражнения
            report = compare_with_exercise(pitch_data, current_exercise)
        else:
            # Просто показываем распознанные ноты
            report = format_pitch_report(pitch_data)

        # Получаем AI-feedback (если есть анализ)
        ai_feedback = ""
        if current_exercise and "accuracy_percent" in report:
            session_data = {
                "exercise_name": current_exercise["name"],
                "accuracy_percent": report["accuracy_percent"],
                "problem_notes": report.get("problem_notes", "Нет"),
                "good_notes": report.get("good_notes", "Нет"),
            }
            ai_feedback = await get_ai_feedback(session_data)

        # Формируем финальный ответ
        response = report["text"]
        if ai_feedback:
            response += f"\n\n💬 *Совет от AI:*\n{ai_feedback}"

        await status_message.edit_text(response, parse_mode="Markdown")

        # Сохраняем сессию в БД
        save_session(
            user_id=user.id,
            exercise_id=current_exercise["id"] if current_exercise else None,
            exercise_name=current_exercise["name"] if current_exercise else None,
            accuracy_percent=report.get("accuracy_percent"),
            duration_seconds=float(duration),
            pitch_data=pitch_data,
            ai_feedback=ai_feedback or None,
        )

    except Exception as e:
        logger.error(f"Ошибка обработки голосового от {user.id}: {e}")
        await status_message.edit_text(
            "❌ Произошла ошибка при анализе.\n"
            "Попробуй записать ещё раз."
        )

    finally:
        # Удаляем временные файлы
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)
