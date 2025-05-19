"""
Интеграция генератора протоколов в Telegram-бота.
Расширяет функциональность бота для преобразования голосовых сообщений
в структурированные протоколы встреч в формате PDF.
"""

import os
import logging
from pathlib import Path
from telegram import Update
from telegram.ext import (
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes,
    ConversationHandler
)

from config import TEMP_DIR
from speech_recognition_engine import SpeechRecognitionEngine
from protocol_generator import ProtocolGenerator

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
WAITING_FOR_VOICE = 1

class ProtocolBot:
    """Расширение бота для генерации протоколов встреч."""
    
    def __init__(self, bot, speech_engine):
        """
        Инициализация расширения для генерации протоколов.
        
        Args:
            bot: Экземпляр Telegram-бота
            speech_engine: Экземпляр движка распознавания речи
        """
        self.bot = bot
        self.speech_engine = speech_engine
        self.protocol_generator = ProtocolGenerator()
        
        # Создание директорий для временных файлов и протоколов
        os.makedirs(TEMP_DIR, exist_ok=True)
        os.makedirs("protocols", exist_ok=True)
        
        # Регистрация обработчиков
        self._register_handlers()
        
        logger.info("Инициализировано расширение для генерации протоколов")
    
    def _register_handlers(self):
        """Регистрация обработчиков команд и сообщений."""
        # Обработчик команды /protocol
        self.bot.add_handler(CommandHandler("protocol", self.start_protocol_generation))
        
        # Обработчик для голосовых сообщений в режиме создания протокола
        protocol_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("protocol", self.start_protocol_generation)],
            states={
                WAITING_FOR_VOICE: [
                    MessageHandler(filters.VOICE, self.process_voice_for_protocol),
                    MessageHandler(filters.TEXT, self.cancel_protocol)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_protocol)],
        )
        
        self.bot.add_handler(protocol_conv_handler)
    
    async def start_protocol_generation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /protocol - начало процесса создания протокола.
        
        Args:
            update: Объект обновления Telegram
            context: Контекст бота
        """
        await update.message.reply_text(
            "Отправьте голосовое сообщение с резюме встречи, и я создам структурированный протокол в формате PDF.\n\n"
            "Для отмены отправьте /cancel."
        )
        return WAITING_FOR_VOICE
    
    async def process_voice_for_protocol(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработка голосового сообщения для создания протокола.
        
        Args:
            update: Объект обновления Telegram
            context: Контекст бота
        """
        try:
            # Отправка сообщения о начале обработки
            await update.message.reply_text("Получено голосовое сообщение. Начинаю обработку...")
            
            # Получение голосового сообщения
            voice = update.message.voice
            voice_file = await context.bot.get_file(voice.file_id)
            
            # Создание временного файла для голосового сообщения
            temp_dir = Path(TEMP_DIR)
            temp_dir.mkdir(exist_ok=True)
            
            voice_path = os.path.join(TEMP_DIR, f"{voice.file_id}.ogg")
            await voice_file.download_to_drive(voice_path)
            logger.info(f"Голосовое сообщение сохранено: {voice_path}")
            
            # Отправка сообщения о начале распознавания
            status_message = await update.message.reply_text("Распознаю речь...")
            
            # Распознавание речи
            transcription = self.speech_engine.recognize_speech(voice_path)
            
            # Обновление статуса
            await status_message.edit_text("Речь распознана. Генерирую протокол...")
            
            # Генерация протокола
            pdf_path, protocol_text = self.protocol_generator.process_voice_transcription(transcription)
            
            if pdf_path and os.path.exists(pdf_path):
                # Отправка PDF-файла
                await update.message.reply_document(
                    document=open(pdf_path, 'rb'),
                    filename=os.path.basename(pdf_path),
                    caption="Протокол встречи в формате PDF"
                )
                
                # Отправка текста протокола
                await update.message.reply_text(
                    f"Расшифровка голосового сообщения:\n\n{transcription}\n\n"
                    f"Структурированный протокол:\n\n{protocol_text[:3900]}..."
                    if len(protocol_text) > 4000 else
                    f"Расшифровка голосового сообщения:\n\n{transcription}\n\n"
                    f"Структурированный протокол:\n\n{protocol_text}"
                )
            else:
                await update.message.reply_text(
                    f"Произошла ошибка при создании протокола. "
                    f"Расшифровка голосового сообщения:\n\n{transcription}"
                )
            
            # Удаление временного файла
            if os.path.exists(voice_path):
                os.remove(voice_path)
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Ошибка при обработке голосового сообщения: {str(e)}")
            await update.message.reply_text(
                f"Произошла ошибка при обработке голосового сообщения: {str(e)}"
            )
            return ConversationHandler.END
    
    async def cancel_protocol(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Отмена процесса создания протокола.
        
        Args:
            update: Объект обновления Telegram
            context: Контекст бота
        """
        await update.message.reply_text("Создание протокола отменено.")
        return ConversationHandler.END


# Функция для интеграции с основным ботом
def integrate_protocol_bot(bot, speech_engine):
    """
    Интегрирует функциональность генерации протоколов в основного бота.
    
    Args:
        bot: Экземпляр Telegram-бота
        speech_engine: Экземпляр движка распознавания речи
        
    Returns:
        ProtocolBot: Экземпляр расширения для генерации протоколов
    """
    return ProtocolBot(bot, speech_engine)
