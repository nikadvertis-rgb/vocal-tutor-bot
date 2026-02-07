"""
Утилиты для работы с аудио.
Скачивание и конвертация голосовых сообщений.
"""

import os
import shutil
import logging
import tempfile
from telegram import Voice
from telegram.ext import ContextTypes
from pydub import AudioSegment

logger = logging.getLogger(__name__)


def check_ffmpeg() -> bool:
    """Проверяет, установлен ли FFmpeg."""
    return shutil.which("ffmpeg") is not None


async def download_and_convert_voice(voice: Voice, context: ContextTypes.DEFAULT_TYPE) -> str:
    """
    Скачивает голосовое сообщение из Telegram и конвертирует в WAV.
    
    Telegram отправляет голосовые в формате OGG (Opus codec).
    Librosa работает лучше с WAV, поэтому конвертируем через pydub.
    
    Args:
        voice: Объект Voice из telegram
        context: Контекст бота
        
    Returns:
        Путь к временному WAV файлу
        
    Note:
        Не забудь удалить файл после использования!
    """
    # Создаём временную директорию если нет
    temp_dir = tempfile.gettempdir()
    
    # Генерируем уникальные имена файлов
    ogg_path = os.path.join(temp_dir, f"voice_{voice.file_unique_id}.ogg")
    wav_path = os.path.join(temp_dir, f"voice_{voice.file_unique_id}.wav")
    
    try:
        # Скачиваем OGG файл
        voice_file = await context.bot.get_file(voice.file_id)
        await voice_file.download_to_drive(ogg_path)
        
        # Конвертируем OGG -> WAV через pydub (требует FFmpeg!)
        audio = AudioSegment.from_ogg(ogg_path)
        audio.export(wav_path, format="wav")
        
        return wav_path
        
    finally:
        # Удаляем OGG файл (WAV нужен для анализа)
        if os.path.exists(ogg_path):
            os.remove(ogg_path)


def get_audio_duration(file_path: str) -> float:
    """
    Получает длительность аудиофайла в секундах.
    
    Args:
        file_path: Путь к аудиофайлу
        
    Returns:
        Длительность в секундах
    """
    audio = AudioSegment.from_file(file_path)
    return len(audio) / 1000.0  # pydub работает в миллисекундах


def normalize_audio(file_path: str, target_db: float = -20.0) -> str:
    """
    Нормализует громкость аудио.
    
    Args:
        file_path: Путь к аудиофайлу
        target_db: Целевой уровень громкости в dB
        
    Returns:
        Путь к нормализованному файлу
    """
    audio = AudioSegment.from_file(file_path)
    
    # Вычисляем разницу с целевой громкостью
    change_in_db = target_db - audio.dBFS
    
    # Применяем усиление
    normalized = audio + change_in_db
    
    # Сохраняем
    output_path = file_path.replace(".wav", "_normalized.wav")
    normalized.export(output_path, format="wav")
    
    return output_path
