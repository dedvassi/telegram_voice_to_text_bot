"""
Основной модуль Telegram бота для преобразования голосовых сообщений в текст.
"""

import os
import logging
import tempfile
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from config import (
    TELEGRAM_TOKEN,
    SPEECH_RECOGNITION_ENGINE,
    WHISPER_MODEL,
    VOSK_MODEL_PATH,
    TEMP_DIR,
    LOG_LEVEL,
    LOG_FILE
)
from speech_recognition_engine import get_speech_recognition_engine

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, LOG_LEVEL),
    filename=LOG_FILE if LOG_FILE else None
)
logger = logging.getLogger(__name__)

# Инициализация движка распознавания речи
try:
    if SPEECH_RECOGNITION_ENGINE.lower() == "whisper":
        speech_engine = get_speech_recognition_engine(
            "whisper", 
            model_name=WHISPER_MODEL
        )
    elif SPEECH_RECOGNITION_ENGINE.lower() == "vosk":
        speech_engine = get_speech_recognition_engine(
            "vosk", 
            model_path=VOSK_MODEL_PATH
        )
    else:
        logger.error(f"Неизвестный движок распознавания речи: {SPEECH_RECOGNITION_ENGINE}")
        raise ValueError(f"Неизвестный движок распознавания речи: {SPEECH_RECOGNITION_ENGINE}")
except Exception as e:
    logger.error(f"Ошибка при инициализации движка распознавания речи: {e}")
    raise


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! 👋\n\n"
        f"Я бот для преобразования голосовых сообщений в текст. "
        f"Просто отправь мне голосовое сообщение, и я верну его текстовую расшифровку."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help."""
    await update.message.reply_text(
        "🔍 *Как использовать этот бот:*\n\n"
        "1. Отправьте голосовое сообщение\n"
        "2. Дождитесь обработки (это может занять несколько секунд)\n"
        "3. Получите текстовую расшифровку\n\n"
        "📋 *Доступные команды:*\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n"
        "/about - Информация о боте\n\n"
        "⚙️ Бот использует технологию распознавания речи на основе "
        f"{SPEECH_RECOGNITION_ENGINE.capitalize()}.",
        parse_mode="Markdown"
    )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /about."""
    await update.message.reply_text(
        "🤖 *Voice-to-Text Bot*\n\n"
        "Этот бот преобразует голосовые сообщения в текст, используя "
        f"технологию распознавания речи {SPEECH_RECOGNITION_ENGINE.capitalize()}.\n\n"
        "🔧 *Технические детали:*\n"
        f"- Движок распознавания: {SPEECH_RECOGNITION_ENGINE.capitalize()}\n"
        f"- Модель: {WHISPER_MODEL if SPEECH_RECOGNITION_ENGINE.lower() == 'whisper' else 'Стандартная'}\n\n"
        "📦 *Исходный код:*\n"
        "https://github.com/dedvassi/telegram_voice_to_text_bot",
        parse_mode="Markdown"
    )


async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик голосовых сообщений."""
    try:
        # Отправка сообщения о начале обработки
        processing_message = await update.message.reply_text(
            "🔄 Обрабатываю голосовое сообщение...",
            reply_to_message_id=update.message.message_id
        )
        
        # Получение информации о голосовом сообщении
        voice = update.message.voice
        voice_file = await context.bot.get_file(voice.file_id)
        
        # Создание временного файла для сохранения голосового сообщения
        temp_dir = Path(TEMP_DIR)
        temp_dir.mkdir(exist_ok=True)
        
        voice_ogg_path = temp_dir / f"{voice.file_id}.ogg"
        
        # Скачивание голосового сообщения
        await voice_file.download_to_drive(voice_ogg_path)
        
        logger.info(f"Голосовое сообщение сохранено: {voice_ogg_path}")
        
        # Распознавание речи
        recognized_text = speech_engine.recognize(str(voice_ogg_path))
        
        # Отправка результата
        if recognized_text:
            await update.message.reply_text(
                f"🔊➡️📝 *Расшифровка:*\n\n{recognized_text}",
                reply_to_message_id=update.message.message_id,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "❌ Не удалось распознать речь в этом сообщении.",
                reply_to_message_id=update.message.message_id
            )
        
        # Удаление сообщения о обработке
        await processing_message.delete()
        
        # Удаление временного файла
        try:
            os.remove(voice_ogg_path)
        except Exception as e:
            logger.warning(f"Не удалось удалить временный файл {voice_ogg_path}: {e}")
            
    except Exception as e:
        logger.error(f"Ошибка при обработке голосового сообщения: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке голосового сообщения. Пожалуйста, попробуйте еще раз.",
            reply_to_message_id=update.message.message_id
        )


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений."""
    await update.message.reply_text(
        "Пожалуйста, отправьте голосовое сообщение для преобразования в текст.",
        reply_to_message_id=update.message.message_id
    )


def main() -> None:
    """Запуск бота."""
    # Проверка наличия токена
    if not TELEGRAM_TOKEN:
        logger.error("Токен Telegram не найден. Пожалуйста, укажите его в .env файле.")
        return
    
    # Создание и настройка приложения
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    
    # Регистрация обработчиков сообщений
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # Запуск бота
    logger.info("Бот запущен")
    application.run_polling()


if __name__ == "__main__":
    main()
