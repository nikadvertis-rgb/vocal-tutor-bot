"""
Формирование отчёта по сессии.
Сравнивает исполнение с целевыми нотами упражнения.
"""

from analysis.notes import frequency_to_note


def compare_with_exercise(pitch_data: dict, exercise: dict) -> dict:
    """
    Сравнивает распознанные ноты с целевыми нотами упражнения.
    
    Args:
        pitch_data: Результат analyze_pitch()
        exercise: Объект упражнения с target_notes
        
    Returns:
        dict с ключами:
        - text: Отформатированный отчёт
        - accuracy_percent: Процент точности
        - problem_notes: Строка с проблемными нотами
        - good_notes: Строка с хорошими нотами
    """
    target_notes = exercise.get("target_notes", [])
    tolerance = exercise.get("tolerance_cents", 50)
    
    if not pitch_data["pitch_data"]:
        return {
            "text": "❌ Не удалось распознать голос. Попробуй записать ещё раз.",
            "accuracy_percent": 0
        }
    
    # Конвертируем распознанные частоты в ноты
    detected_notes = []
    for p in pitch_data["pitch_data"]:
        note_info = frequency_to_note(p["frequency"])
        if note_info:
            detected_notes.append({
                **note_info,
                "time": p["time"]
            })
    
    if not detected_notes:
        return {
            "text": "❌ Не удалось распознать ноты.",
            "accuracy_percent": 0
        }
    
    # Сравниваем с целевыми нотами
    results = []
    good_notes = []
    problem_notes = []
    in_tolerance_count = 0

    for target in target_notes:
        target_name = target["name"]
        target_freq = target["frequency"]

        # Ищем ближайшую распознанную ноту
        closest_match = None
        min_diff = float("inf")

        for detected in detected_notes:
            if detected["name"] == target_name:
                diff = abs(detected["cents_off"])
                if diff < min_diff:
                    min_diff = diff
                    closest_match = detected

        if closest_match:
            cents = closest_match["cents_off"]

            # Определяем статус
            if abs(cents) <= 20:
                emoji = "✅"
                status = "отлично!"
                good_notes.append(target_name)
                in_tolerance_count += 1
            elif abs(cents) <= tolerance:
                emoji = "⚠️"
                if cents > 0:
                    status = "высоковато"
                else:
                    status = "низковато"
                problem_notes.append(f"{target_name} ({cents:+d}ц)")
                in_tolerance_count += 1
            else:
                emoji = "❌"
                if cents > 0:
                    status = "слишком высоко"
                else:
                    status = "слишком низко"
                problem_notes.append(f"{target_name} ({cents:+d}ц)")

            cents_text = f"{cents:+d}ц"
            results.append(f"{emoji} {target_name} ({cents_text}) — {status}")
        else:
            results.append(f"❓ {target_name} — не услышал")

    # Считаем accuracy (ноты в допуске: отлично + приемлемо)
    total_notes = len(target_notes)
    accuracy = round((in_tolerance_count / total_notes) * 100) if total_notes > 0 else 0
    
    # Формируем progress bar
    filled = round(accuracy / 10)
    progress_bar = "█" * filled + "░" * (10 - filled)
    
    # Формируем текст отчёта
    lines = [
        f"📊 *Результат: {exercise['name']}*\n",
        f"Точность: {accuracy}% {progress_bar}\n",
        *results
    ]
    
    return {
        "text": "\n".join(lines),
        "accuracy_percent": accuracy,
        "problem_notes": ", ".join(problem_notes) if problem_notes else "Нет",
        "good_notes": ", ".join(good_notes) if good_notes else "Нет"
    }
