# Vocal Tutor Bot

🎤 Telegram-бот для тренировки вокала с AI-анализом.

## Возможности

- 🎵 Анализ высоты голоса (pitch detection)
- 📊 Сравнение с целевыми нотами
- 🤖 Персональные советы от AI (Claude)
- 📈 Отслеживание прогресса

## Быстрый старт

### 1. Установка зависимостей

```bash
# Клонируй репозиторий
cd vocal-tutor-bot

# Создай виртуальное окружение
python -m venv venv

# Активируй (Windows)
venv\Scripts\activate

# Активируй (Linux/Mac)
source venv/bin/activate

# Установи зависимости
pip install -r requirements.txt
```

### 2. FFmpeg (обязательно!)

FFmpeg нужен для конвертации аудио.

**Windows:**
```bash
# Через winget
winget install FFmpeg

# Или скачай с https://ffmpeg.org/download.html
```

**Linux:**
```bash
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

### 3. Настройка токенов

```bash
# Скопируй шаблон
cp .env.example .env

# Отредактируй .env и вставь свои токены
```

Нужно получить:
- `TELEGRAM_TOKEN` — от [@BotFather](https://t.me/BotFather)
- `ANTHROPIC_API_KEY` — от [console.anthropic.com](https://console.anthropic.com)

### 4. Запуск

```bash
python bot.py
```

## Структура проекта

```
vocal-tutor-bot/
├── bot.py              # Точка входа
├── config.py           # Конфигурация
├── requirements.txt    # Зависимости
├── .env.example        # Шаблон переменных
│
├── handlers/           # Обработчики команд
│   ├── start.py        # /start
│   ├── help.py         # /help
│   ├── voice.py        # Голосовые сообщения
│   ├── exercise.py     # /exercise
│   └── progress.py     # /progress
│
├── analysis/           # Анализ аудио
│   ├── pitch.py        # Pitch detection (librosa)
│   ├── notes.py        # Конвертация частот → ноты
│   └── report.py       # Формирование отчёта
│
├── ai/                 # AI-коучинг
│   └── coach.py        # Claude API
│
├── utils/              # Утилиты
│   └── audio.py        # Конвертация аудио
│
└── exercises/          # Упражнения
    └── exercises.json  # 10 базовых упражнений
```

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Начать, выбрать тип голоса |
| `/exercise` | Выбрать упражнение |
| `/progress` | Посмотреть статистику |
| `/help` | Справка |

## Технологии

- **Python 3.11+**
- **python-telegram-bot** — Telegram Bot API
- **librosa** — Pitch detection (PYIN алгоритм)
- **pydub** — Конвертация аудио
- **anthropic** — Claude API для AI-советов

## Лицензия

MIT
