"""
Обработчик команды /progress.
Показывает статистику тренировок пользователя из БД.
"""

from telegram import Update
from telegram.ext import ContextTypes

from database.models import get_user_stats, get_recent_sessions


async def progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /progress.
    Показывает реальную статистику пользователя из SQLite.
    """
    user = update.effective_user
    stats = get_user_stats(user.id)

    # Форматируем среднюю точность
    avg_acc = f"{stats['avg_accuracy']}%" if stats["avg_accuracy"] is not None else "—"
    week_best = f"{stats['week_best']}%" if stats["week_best"] is not None else "—"

    text = f"""
📊 *Твой прогресс, {user.first_name}!*

*За всё время:*
• Сессий: {stats['total_sessions']}
• Общее время: {stats['total_minutes']} мин
• Средняя точность: {avg_acc}

*Последние 7 дней:*
• Сессий: {stats['week_sessions']}
• Лучший результат: {week_best}
"""

    # Добавляем последние сессии если есть
    recent = get_recent_sessions(user.id, limit=5)
    if recent:
        text += "\n*Последние тренировки:*\n"
        for s in recent:
            name = s["exercise_name"] or "Свободная запись"
            acc = f"{s['accuracy_percent']}%" if s["accuracy_percent"] is not None else "—"
            text += f"• {name} — {acc}\n"
    else:
        text += "\n---\n\n🎯 *Цель:* Выполни 5 упражнений на этой неделе!\n"

    text += "\n💡 Используй /exercise чтобы начать тренировку."

    await update.message.reply_text(text, parse_mode="Markdown")
