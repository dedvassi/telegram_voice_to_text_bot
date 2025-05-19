"""
Конфигурационный файл для Telegram Voice-to-Text бота.
"""

import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Токен Telegram бота
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Настройки для распознавания речи
# Выбор движка: "whisper" или "vosk"
SPEECH_RECOGNITION_ENGINE = os.getenv("SPEECH_RECOGNITION_ENGINE", "whisper")

# Настройки для Whisper
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "tiny")  # tiny, base, small, medium, large

# Настройки для Vosk
VOSK_MODEL_PATH = os.getenv("VOSK_MODEL_PATH", "model")

# Пути для временных файлов
TEMP_DIR = os.getenv("TEMP_DIR", "temp")

# Настройки логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "bot.log")

# Создание временной директории, если она не существует
os.makedirs(TEMP_DIR, exist_ok=True)
