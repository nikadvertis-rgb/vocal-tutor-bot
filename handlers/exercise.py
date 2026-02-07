"""
Обработчик команды /exercise.
Показывает список упражнений и позволяет выбрать одно.
"""

import json
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Загружаем упражнения из JSON
EXERCISES_PATH = Path(__file__).parent.parent / "exercises" / "exercises.json"


def load_exercises() -> list:
    """Загружает упражнения из JSON файла."""
    if EXERCISES_PATH.exists():
        with open(EXERCISES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


async def exercise_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /exercise.
    Показывает список доступных упражнений.
    """
    exercises = load_exercises()
    
    if not exercises:
        await update.message.reply_text(
            "😕 Упражнения пока не загружены.\n"
            "Попробуй позже."
        )
        return
    
    text = """
🎵 *Выбери упражнение:*

Начни с простых (⭐) и постепенно переходи к сложным (⭐⭐⭐).
"""
    
    # Группируем по сложности
    keyboard = []
    for exercise in exercises:
        difficulty = "⭐" * exercise.get("difficulty", 1)
        button_text = f"{difficulty} {exercise['name']}"
        keyboard.append([
            InlineKeyboardButton(
                button_text, 
                callback_data=f"exercise_{exercise['id']}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def exercise_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик выбора упражнения через inline-кнопку.
    """
    query = update.callback_query
    await query.answer()
    
    exercise_id = query.data.replace("exercise_", "")
    exercises = load_exercises()
    
    # Находим выбранное упражнение
    exercise = next((e for e in exercises if e["id"] == exercise_id), None)
    
    if not exercise:
        await query.edit_message_text("❌ Упражнение не найдено.")
        return
    
    # Сохраняем в контексте
    context.user_data["current_exercise"] = exercise
    
    # Формируем описание целевых нот
    target_notes = exercise.get("target_notes", [])
    notes_text = " → ".join([n["name"] for n in target_notes])
    
    text = f"""
🎵 *{exercise['name']}*

{exercise.get('description', '')}

*Целевые ноты:*
{notes_text}

*Допустимое отклонение:* ±{exercise.get('tolerance_cents', 50)} центов

---

📱 *Теперь запиши голосовое сообщение с этим упражнением!*

Я проанализирую твоё исполнение и дам обратную связь.
"""
    
    await query.edit_message_text(text, parse_mode="Markdown")
