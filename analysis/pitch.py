"""
Pitch detection через librosa.
Определяет высоту звука (частоту) в аудиозаписи.
"""

import librosa
import numpy as np
from config import SAMPLE_RATE


def analyze_pitch(wav_path: str) -> dict:
    """
    Анализирует pitch (высоту звука) в WAV файле.
    
    Использует librosa.pyin — лучший алгоритм для голоса.
    fmin=C2 (65 Hz), fmax=C6 (1047 Hz) — покрывает все типы голосов.
    
    Args:
        wav_path: Путь к WAV файлу
        
    Returns:
        dict с ключами:
        - duration: длительность записи в секундах
        - pitch_data: список распознанных нот с временными метками
    """
    # Загружаем аудио
    y, sr = librosa.load(wav_path, sr=SAMPLE_RATE)
    
    # Применяем pyin для определения pitch
    f0, voiced_flag, voiced_prob = librosa.pyin(
        y,
        fmin=65,      # C2 — самая низкая нота (бас)
        fmax=1047,    # C6 — самая высокая (сопрано)
        sr=sr
    )
    
    # Получаем временные метки для каждого фрейма
    times = librosa.times_like(f0, sr=sr)
    
    # Собираем результаты только для "вокализованных" участков
    results = []
    for t, freq, is_voiced, prob in zip(times, f0, voiced_flag, voiced_prob):
        # Фильтруем: только вокализованные участки с высокой уверенностью
        if is_voiced and prob > 0.8 and not np.isnan(freq):
            results.append({
                "time": round(float(t), 2),
                "frequency": round(float(freq), 2),
                "confidence": round(float(prob), 2)
            })
    
    return {
        "duration": round(float(len(y) / sr), 2),
        "pitch_data": results
    }


def get_average_pitch(pitch_data: list) -> float:
    """
    Вычисляет среднюю частоту по всем распознанным нотам.
    
    Args:
        pitch_data: Список словарей с frequency
        
    Returns:
        Средняя частота в Hz
    """
    if not pitch_data:
        return 0.0
    
    frequencies = [p["frequency"] for p in pitch_data]
    return round(np.mean(frequencies), 2)


def get_pitch_range(pitch_data: list) -> tuple:
    """
    Определяет диапазон голоса (min и max частоты).
    
    Args:
        pitch_data: Список словарей с frequency
        
    Returns:
        Tuple (min_freq, max_freq)
    """
    if not pitch_data:
        return (0.0, 0.0)
    
    frequencies = [p["frequency"] for p in pitch_data]
    return (round(min(frequencies), 2), round(max(frequencies), 2))
