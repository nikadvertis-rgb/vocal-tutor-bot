"""
Тесты для analysis/notes.py — конвертация частот в ноты.
"""

from analysis.notes import frequency_to_note, note_to_frequency, format_pitch_report


class TestFrequencyToNote:
    """Тесты frequency_to_note()."""

    def test_a4_440hz(self):
        """A4 = 440 Hz — эталонная нота."""
        result = frequency_to_note(440.0)
        assert result["note"] == "A"
        assert result["octave"] == 4
        assert result["name"] == "A4"
        assert result["cents_off"] == 0

    def test_c4_middle_c(self):
        """C4 (До средней октавы) ~ 261.63 Hz."""
        result = frequency_to_note(261.63)
        assert result["note"] == "C"
        assert result["octave"] == 4
        assert result["name"] == "C4"
        assert abs(result["cents_off"]) <= 1

    def test_c3_low(self):
        """C3 ~ 130.81 Hz."""
        result = frequency_to_note(130.81)
        assert result["note"] == "C"
        assert result["octave"] == 3

    def test_zero_frequency(self):
        """Нулевая частота → None."""
        assert frequency_to_note(0) is None

    def test_negative_frequency(self):
        """Отрицательная частота → None."""
        assert frequency_to_note(-100) is None

    def test_slightly_sharp(self):
        """Частота чуть выше A4 → положительные центы."""
        result = frequency_to_note(445.0)
        assert result["note"] == "A"
        assert result["cents_off"] > 0

    def test_slightly_flat(self):
        """Частота чуть ниже A4 → отрицательные центы."""
        result = frequency_to_note(435.0)
        assert result["note"] == "A"
        assert result["cents_off"] < 0

    def test_has_russian_name(self):
        """Возвращает русское название ноты."""
        result = frequency_to_note(261.63)
        assert result["name_ru"] == "До4"

    def test_sharp_note(self):
        """F#3 ~ 185 Hz."""
        result = frequency_to_note(185.0)
        assert result["note"] == "F#"
        assert result["octave"] == 3

    def test_ideal_frequency_returned(self):
        """Возвращает частоту идеальной ноты."""
        result = frequency_to_note(440.0)
        assert result["frequency"] == 440.0


class TestNoteToFrequency:
    """Тесты note_to_frequency()."""

    def test_a4(self):
        """A4 → 440 Hz."""
        assert note_to_frequency("A4") == 440.0

    def test_c4(self):
        """C4 → 261.63 Hz."""
        assert note_to_frequency("C4") == 261.63

    def test_c3(self):
        """C3 → 130.81 Hz."""
        assert note_to_frequency("C3") == 130.81

    def test_sharp_note(self):
        """F#3 — корректно парсится."""
        freq = note_to_frequency("F#3")
        assert 184 < freq < 186

    def test_roundtrip(self):
        """Частота → нота → частота (примерное совпадение)."""
        original = 440.0
        note = frequency_to_note(original)
        restored = note_to_frequency(note["name"])
        assert abs(restored - original) < 0.1


class TestFormatPitchReport:
    """Тесты format_pitch_report()."""

    def test_empty_pitch_data(self):
        """Пустые данные → сообщение об ошибке."""
        result = format_pitch_report({"duration": 5.0, "pitch_data": []})
        assert "Не удалось" in result["text"]

    def test_valid_data(self, sample_pitch_data):
        """Корректные данные → отчёт содержит длительность."""
        result = format_pitch_report(sample_pitch_data)
        assert "5.0 сек" in result["text"]
        assert "Распознанные ноты" in result["text"]

    def test_contains_note_names(self, sample_pitch_data):
        """Отчёт содержит русские названия нот."""
        result = format_pitch_report(sample_pitch_data)
        text = result["text"]
        # Должны быть какие-то ноты
        assert any(name in text for name in ["До", "Ре", "Ми", "Фа", "Соль", "Ля", "Си"])
