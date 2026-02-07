"""
Генерация аудиопримеров для упражнений.
Создаёт MP3 файлы с синтезированными нотами для каждого упражнения.
"""

import json
import os
import numpy as np
import soundfile as sf
from pathlib import Path


SAMPLE_RATE = 44100
NOTE_DURATION = 0.7      # секунды на ноту
PAUSE_DURATION = 0.15    # пауза между нотами
FADE_IN = 0.02           # плавное нарастание
FADE_OUT = 0.15          # плавное затухание


def generate_tone(frequency: float, duration: float, sr: int = SAMPLE_RATE) -> np.ndarray:
    """
    Генерирует тон с огибающей, имитирующей пианино.
    Основная частота + 2-я и 3-я гармоники для более натурального звука.
    """
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)

    # Основная частота + гармоники
    signal = (
        1.0 * np.sin(2 * np.pi * frequency * t) +
        0.3 * np.sin(2 * np.pi * frequency * 2 * t) +
        0.1 * np.sin(2 * np.pi * frequency * 3 * t)
    )

    # Нормализуем
    signal = signal / np.max(np.abs(signal))

    # Огибающая: быстрая атака, плавное затухание
    envelope = np.ones_like(t)

    # Fade in
    fade_in_samples = int(sr * FADE_IN)
    if fade_in_samples > 0:
        envelope[:fade_in_samples] = np.linspace(0, 1, fade_in_samples)

    # Экспоненциальное затухание (piano-like)
    decay = np.exp(-t * 2.0)
    envelope *= decay

    # Fade out
    fade_out_samples = int(sr * FADE_OUT)
    if fade_out_samples > 0:
        envelope[-fade_out_samples:] *= np.linspace(1, 0, fade_out_samples)

    signal *= envelope * 0.7  # общая громкость

    return signal


def generate_exercise_audio(exercise: dict, output_path: str):
    """Генерирует аудиофайл для упражнения."""
    target_notes = exercise.get("target_notes", [])
    if not target_notes:
        return

    audio_parts = []

    for note in target_notes:
        freq = note["frequency"]
        tone = generate_tone(freq, NOTE_DURATION)
        audio_parts.append(tone)

        # Пауза между нотами
        pause = np.zeros(int(SAMPLE_RATE * PAUSE_DURATION))
        audio_parts.append(pause)

    # Склеиваем
    full_audio = np.concatenate(audio_parts)

    # Записываем WAV
    wav_path = output_path.replace(".mp3", ".wav")
    sf.write(wav_path, full_audio, SAMPLE_RATE)

    print(f"  Created: {wav_path} ({len(full_audio) / SAMPLE_RATE:.1f}s)")
    return wav_path


def main():
    # Загружаем упражнения
    exercises_path = Path(__file__).parent.parent / "exercises" / "exercises.json"
    with open(exercises_path, "r", encoding="utf-8") as f:
        exercises = json.load(f)

    output_dir = Path(__file__).parent.parent / "exercises" / "audio" / "examples"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating audio examples for {len(exercises)} exercises...")
    print(f"Output: {output_dir}")
    print()

    for ex in exercises:
        print(f"[{ex['id']}] {ex['name']}")
        notes_str = " - ".join(n["name"] for n in ex.get("target_notes", []))
        print(f"  Notes: {notes_str}")

        output_path = str(output_dir / f"{ex['id']}.mp3")
        generate_exercise_audio(ex, output_path)
        print()

    print("Done!")


if __name__ == "__main__":
    main()
