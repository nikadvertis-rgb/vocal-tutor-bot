# Vocal Tutor Bot

Telegram-бот для тренировки вокала с AI-анализом голоса.

## Возможности

- **Pitch detection** — анализ высоты голоса через librosa (PYIN алгоритм)
- **Сравнение с целевыми нотами** — точность попадания в центах
- **AI-коучинг** — персональные советы от LLM (любой OpenAI-совместимый API)
- **Автоопределение типа голоса** — пошаговый тест гаммами + AI-подтверждение
- **Готовые упражнения** — гаммы, интервалы, арпеджио с аудиопримерами
- **Распевки** — 3 готовых аудио (7/10/20 мин)
- **Прогресс** — SQLite-хранилище тренировок, статистика

## Быстрый старт

### 1. Клонируйте и установите зависимости

```bash
git clone https://github.com/nikadvertis-rgb/vocal-tutor-bot.git
cd vocal-tutor-bot

python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

### 2. FFmpeg (обязательно)

```bash
# Linux
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
winget install FFmpeg
```

### 3. Настройка

```bash
cp .env.example .env
```

Отредактируйте `.env`:

| Переменная | Описание | Где получить |
|---|---|---|
| `TELEGRAM_TOKEN` | Токен Telegram-бота | [@BotFather](https://t.me/BotFather) |
| `AI_API_KEY` | Ключ OpenAI-совместимого API | См. ниже |
| `AI_BASE_URL` | Base URL провайдера | См. ниже |
| `AI_MODEL` | Название модели | См. ниже |

#### Поддерживаемые AI-провайдеры

Бот работает с любым OpenAI-совместимым API:

| Провайдер | `AI_BASE_URL` | `AI_MODEL` (пример) |
|---|---|---|
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| OpenRouter | `https://openrouter.ai/api/v1` | `google/gemini-2.5-flash` |
| Z.AI (GLM) | `https://open.bigmodel.cn/api/paas/v4` | `glm-4.7` |
| Ollama (локально) | `http://localhost:11434/v1` | `llama3.2` |

### 4. Запуск

```bash
python bot.py
```

### Docker

```bash
cp .env.example .env
# отредактируйте .env
docker compose up -d
```

## Структура проекта

```
vocal-tutor-bot/
├── bot.py              # Точка входа
├── config.py           # Конфигурация (env vars)
├── requirements.txt    # Зависимости
├── Dockerfile
├── docker-compose.yml
│
├── handlers/           # Обработчики Telegram-команд
│   ├── start.py        # /start — онбординг, выбор голоса
│   ├── voice.py        # Голосовые сообщения — анализ pitch
│   ├── exercise.py     # /exercise — упражнения
│   ├── warmups.py      # /warmups — готовые распевки
│   ├── progress.py     # /progress — статистика
│   ├── settings.py     # /settings — тип голоса, пол
│   └── help.py         # /help
│
├── analysis/           # Анализ аудио
│   ├── pitch.py        # Pitch detection (librosa PYIN)
│   ├── notes.py        # Частоты → ноты (A4=440Hz)
│   └── report.py       # Сравнение с упражнением
│
├── ai/                 # AI-коучинг
│   └── coach.py        # OpenAI-compatible client
│
├── database/           # Хранилище
│   ├── db.py           # SQLite (WAL mode)
│   └── models.py       # CRUD операции
│
├── utils/              # Утилиты
│   ├── audio.py        # Конвертация OGG→WAV
│   └── rate_limit.py   # Rate limiter (10 req/hour)
│
├── exercises/          # Упражнения + аудио
│   ├── exercises.json  # Описания упражнений
│   └── audio/          # OGG/MP3 файлы
│
└── tests/              # Тесты (pytest)
```

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Начать — выбор пола и типа голоса |
| `/exercise` | Выбрать упражнение с аудиопримером |
| `/warmups` | Готовые распевки (7/10/20 мин) |
| `/progress` | Статистика тренировок |
| `/settings` | Изменить тип голоса |
| `/help` | Справка |

## Как работает анализ

1. Пользователь отправляет голосовое сообщение
2. OGG → WAV конвертация (pydub + FFmpeg)
3. Pitch detection — librosa PYIN (65–1047 Hz)
4. Частоты → ноты (12-TET, A4=440Hz) с отклонением в центах
5. Сравнение с целевыми нотами упражнения
6. AI генерирует персональный совет
7. Результат сохраняется в SQLite

## Технологии

- **Python 3.11+**
- **python-telegram-bot 20.x** — Telegram Bot API
- **librosa** — Pitch detection (PYIN)
- **pydub** + FFmpeg — аудио конвертация
- **openai** — клиент для любого OpenAI-совместимого API
- **SQLite** (WAL mode) — хранилище данных

## Автор

Мельников Никита Сергеевич — [GitHub](https://github.com/nikadvertis-rgb) · [LinkedIn](https://www.linkedin.com/in/nikita-melnikoff)

## Лицензия и дисклеймер

MIT

This project is a **non-commercial educational prototype**. Vocal exercises and warmup audio materials inspired by Seth Riggs' "Speech Level Singing" methodology are included solely for testing and personal learning purposes. All rights to the original materials belong to their respective owners. This project is not affiliated with or endorsed by Seth Riggs or SLS International.
