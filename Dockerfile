FROM python:3.12-slim

# Установка FFmpeg (обязателен для pydub)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Устанавливаем зависимости отдельным слоем (кеширование)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Создаём директорию для данных
RUN mkdir -p /app/data

CMD ["python", "bot.py"]
