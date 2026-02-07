"""
Генерация тестовых гамм для определения типа голоса.
Создаёт гаммы на разных октавах.
"""

import numpy as np
import soundfile as sf
from pathlib import Path

SAMPLE_RATE = 44100
NOTE_DURATION = 0.8
PAUSE_DURATION = 0.2
FADE_IN = 0.02
FADE_OUT = 0.15

# Частоты нот для мажорной гаммы До на разных октавах
SCALES = {
    "scale_C2": {
        "name": "C2-C3",
        "notes": [
            ("C2", 65.41), ("D2", 73.42), ("E2", 82.41), ("F2", 87.31),
            ("G2", 98.00), ("A2", 110.00), ("B2", 123.47), ("C3", 130.81),
        ]
    },
    "scale_C3": {
        "name": "C3-C4",
        "notes": [
            ("C3", 130.81), ("D3", 146.83), ("E3", 164.81), ("F3", 174.61),
            ("G3", 196.00), ("A3", 220.00), ("B3", 246.94), ("C4", 261.63),
        ]
    },
    "scale_C4": {
        "name": "C4-C5",
        "notes": [
            ("C4", 261.63), ("D4", 293.66), ("E4", 329.63), ("F4", 349.23),
            ("G4", 392.00), ("A4", 440.00), ("B4", 493.88), ("C5", 523.25),
        ]
    },
    "scale_C5": {
        "name": "C5-C6",
        "notes": [
            ("C5", 523.25), ("D5", 587.33), ("E5", 659.25), ("F5", 698.46),
            ("G5", 783.99), ("A5", 880.00), ("B5", 987.77), ("C6", 1046.50),
        ]
    },
}


def generate_tone(frequency, duration, sr=SAMPLE_RATE):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    signal = (
        1.0 * np.sin(2 * np.pi * frequency * t) +
        0.3 * np.sin(2 * np.pi * frequency * 2 * t) +
        0.1 * np.sin(2 * np.pi * frequency * 3 * t)
    )
    signal = signal / np.max(np.abs(signal))

    envelope = np.ones_like(t)
    fade_in_samples = int(sr * FADE_IN)
    if fade_in_samples > 0:
        envelope[:fade_in_samples] = np.linspace(0, 1, fade_in_samples)
    decay = np.exp(-t * 1.5)
    envelope *= decay
    fade_out_samples = int(sr * FADE_OUT)
    if fade_out_samples > 0:
        envelope[-fade_out_samples:] *= np.linspace(1, 0, fade_out_samples)

    signal *= envelope * 0.7
    return signal


def main():
    output_dir = Path(__file__).parent.parent / "exercises" / "audio" / "voice_test"
    output_dir.mkdir(parents=True, exist_ok=True)

    for scale_id, scale_info in SCALES.items():
        audio_parts = []
        for note_name, freq in scale_info["notes"]:
            tone = generate_tone(freq, NOTE_DURATION)
            audio_parts.append(tone)
            pause = np.zeros(int(SAMPLE_RATE * PAUSE_DURATION))
            audio_parts.append(pause)

        full_audio = np.concatenate(audio_parts)
        wav_path = output_dir / f"{scale_id}.wav"
        sf.write(str(wav_path), full_audio, SAMPLE_RATE)
        dur = len(full_audio) / SAMPLE_RATE
        print(f"Created {scale_id}.wav ({scale_info['name']}, {dur:.1f}s)")

    print("Done!")


if __name__ == "__main__":
    main()
