"""
Обработчик голосовых сообщений.
Скачивает аудио, анализирует pitch и отправляет результат.
"""

import os
import asyncio
import logging
import traceback
from telegram import Update
from telegram.ext import ContextTypes

from config import MAX_VOICE_DURATION, MIN_VOICE_DURATION
from utils.audio import download_and_convert_voice
from analysis.pitch import analyze_pitch, get_pitch_range
from analysis.notes import format_pitch_report
from analysis.report import compare_with_exercise
from ai.coach import get_ai_feedback, analyze_voice_type
from handlers.start import handle_voice_test_step
from config import VOICE_TYPES
from database.models import save_session, upsert_user, set_voice_type
from utils.rate_limit import check_rate_limit, get_remaining_requests

logger = logging.getLogger(__name__)


async def _safe_edit_text(message, text: str, parse_mode: str = None) -> None:
    """Отправляет сообщение, при ошибке Markdown — повторяет без форматирования."""
    if parse_mode:
        try:
            await message.edit_text(text, parse_mode=parse_mode)
            return
        except Exception:
            logger.warning("Markdown ошибка, отправляю без форматирования")
    # Убираем Markdown-символы для plain text
    plain = text.replace("*", "").replace("_", "")
    await message.edit_text(plain)


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
            f"Лимит: 10 анализов в час. Осталось: {remaining}.\n"
            f"Попробуй чуть позже."
        )
        return

    # Показываем статус
    status_message = await update.message.reply_text("⏳ Анализирую твою запись...")

    # Убеждаемся что пользователь в БД
    upsert_user(user_id=user.id, username=user.username, first_name=user.first_name)

    wav_path = None
    try:
        # Шаг 1: Скачиваем и конвертируем
        try:
            wav_path = await download_and_convert_voice(voice, context)
        except Exception as e:
            logger.error(f"Ошибка конвертации аудио от {user.id}: {traceback.format_exc()}")
            await status_message.edit_text(
                "❌ Ошибка конвертации аудио.\n"
                "Возможно, проблема с FFmpeg на сервере."
            )
            return

        # Шаг 2: Анализируем pitch
        try:
            pitch_data = await asyncio.to_thread(analyze_pitch, wav_path)
        except Exception as e:
            logger.error(f"Ошибка pitch-анализа от {user.id}: {traceback.format_exc()}")
            await status_message.edit_text(
                "❌ Ошибка анализа высоты звука.\n"
                "Попробуй записать ещё раз."
            )
            return

        if not pitch_data["pitch_data"]:
            await status_message.edit_text(
                "😕 Не удалось распознать голос.\n\n"
                "Попробуй:\n"
                "• Записать в более тихом месте\n"
                "• Петь громче и чётче\n"
                "• Держать телефон ближе"
            )
            return

        # Режим авто-определения типа голоса (пошаговый тест с гаммами)
        if context.user_data.get("detecting_voice_type"):
            await status_message.edit_text("✅ Голос записан, анализирую...")
            await handle_voice_test_step(update, context, pitch_data)
            return

        # Получаем текущее упражнение
        current_exercise = context.user_data.get("current_exercise")

        # Формируем отчёт
        if current_exercise:
            report = compare_with_exercise(pitch_data, current_exercise)
        else:
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
            # Убираем Markdown из AI-ответа чтобы не сломать форматирование
            safe_feedback = ai_feedback.replace("*", "").replace("_", "").replace("`", "")
            response += f"\n\n💬 *Совет от AI:*\n{safe_feedback}"

        await _safe_edit_text(status_message, response, parse_mode="Markdown")

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
        logger.error(f"Ошибка обработки голосового от {user.id}: {traceback.format_exc()}")
        try:
            await status_message.edit_text(
                "❌ Произошла ошибка при анализе.\n"
                "Попробуй записать ещё раз.\n\n"
                f"Детали: {type(e).__name__}: {e}"
            )
        except Exception:
            pass

    finally:
        # Удаляем временные файлы
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)
