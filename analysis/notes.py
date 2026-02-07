"""
Конвертация частот в музыкальные ноты.
"""

import math

# Названия нот (английская система)
NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Русские названия нот
NOTES_RU = {
    "C": "До",
    "C#": "До#",
    "D": "Ре",
    "D#": "Ре#",
    "E": "Ми",
    "F": "Фа",
    "F#": "Фа#",
    "G": "Соль",
    "G#": "Соль#",
    "A": "Ля",
    "A#": "Ля#",
    "B": "Си",
}


def frequency_to_note(freq: float) -> dict | None:
    """
    Конвертирует частоту (Hz) в музыкальную ноту.
    
    Базовая частота: A4 = 440 Hz
    Формула: semitones = 12 * log2(freq / 440)
    
    Args:
        freq: Частота в Hz
        
    Returns:
        dict с ключами:
        - note: Название ноты (C, D, E...)
        - octave: Номер октавы
        - name: Полное имя (C4, D#3...)
        - name_ru: Русское имя (До4, Ре#3...)
        - cents_off: Отклонение от идеальной ноты в центах (-50 до +50)
        - frequency: Частота идеальной ноты
    """
    if freq <= 0:
        return None
    
    # Вычисляем количество полутонов от A4 (440 Hz)
    semitones_from_a4 = 12 * math.log2(freq / 440.0)
    
    # MIDI номер ноты (A4 = 69)
    midi_number = round(semitones_from_a4) + 69
    
    # Индекс ноты (0-11)
    note_index = midi_number % 12
    
    # Номер октавы
    octave = (midi_number // 12) - 1
    
    # Вычисляем отклонение в центах
    exact_midi = semitones_from_a4 + 69
    cents_off = round((exact_midi - midi_number) * 100)
    
    # Частота идеальной ноты
    ideal_freq = 440.0 * (2 ** ((midi_number - 69) / 12))
    
    note = NOTES[note_index]
    
    return {
        "note": note,
        "octave": octave,
        "name": f"{note}{octave}",
        "name_ru": f"{NOTES_RU[note]}{octave}",
        "cents_off": cents_off,
        "frequency": round(ideal_freq, 2)
    }


def note_to_frequency(note_name: str) -> float:
    """
    Конвертирует название ноты в частоту.
    
    Args:
        note_name: Название ноты (например, "C4", "A#3")
        
    Returns:
        Частота в Hz
    """
    # Извлекаем ноту и октаву
    if "#" in note_name:
        note = note_name[:2]
        octave = int(note_name[2:])
    else:
        note = note_name[0]
        octave = int(note_name[1:])
    
    # Индекс ноты
    note_index = NOTES.index(note)
    
    # MIDI номер
    midi_number = (octave + 1) * 12 + note_index
    
    # Частота
    freq = 440.0 * (2 ** ((midi_number - 69) / 12))
    
    return round(freq, 2)


def format_pitch_report(pitch_data: dict) -> dict:
    """
    Форматирует результаты pitch detection в читаемый отчёт.
    
    Args:
        pitch_data: Результат analyze_pitch()
        
    Returns:
        dict с ключом 'text' — отформатированный текст отчёта
    """
    if not pitch_data["pitch_data"]:
        return {"text": "❌ Не удалось распознать ноты."}
    
    # Группируем частоты в ноты
    notes_detected = []
    for p in pitch_data["pitch_data"]:
        note_info = frequency_to_note(p["frequency"])
        if note_info:
            notes_detected.append(note_info)
    
    if not notes_detected:
        return {"text": "❌ Не удалось распознать ноты."}
    
    # Считаем уникальные ноты
    unique_notes = {}
    for note in notes_detected:
        name = note["name"]
        if name not in unique_notes:
            unique_notes[name] = {
                "count": 0,
                "total_cents": 0,
                "name_ru": note["name_ru"]
            }
        unique_notes[name]["count"] += 1
        unique_notes[name]["total_cents"] += note["cents_off"]
    
    # Форматируем вывод
    lines = [f"🎵 *Анализ записи ({pitch_data['duration']} сек)*\n"]
    lines.append("*Распознанные ноты:*\n")
    
    for name, data in sorted(unique_notes.items()):
        avg_cents = data["total_cents"] // data["count"]
        
        # Emoji в зависимости от точности
        if abs(avg_cents) < 20:
            emoji = "✅"
            status = "отлично"
        elif abs(avg_cents) < 50:
            emoji = "⚠️"
            status = "неплохо"
        else:
            emoji = "❌"
            status = "нужно поработать"
        
        cents_text = f"+{avg_cents}" if avg_cents > 0 else str(avg_cents)
        lines.append(f"{emoji} {data['name_ru']} ({cents_text}ц) — {status}")
    
    return {"text": "\n".join(lines)}
