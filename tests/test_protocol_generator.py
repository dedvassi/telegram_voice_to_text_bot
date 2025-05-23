"""
Модуль для тестирования генерации протоколов встреч.
Позволяет проверить качество генерации протоколов на тестовых данных.
"""

import os
import sys
import logging
from pathlib import Path

# Добавляем родительскую директорию в путь для импорта модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.protocol_generator import ProtocolGenerator

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Тестовые расшифровки голосовых сообщений
TEST_TRANSCRIPTIONS = [
    """
    Сегодня встречались с Александром по проекту 25-24 ДП, обсуждали 3д визуализацию центральной зоны и черновой вариант. 
    Решили, что нужно проверить возможность диммирования светильников, чтобы не было слепящего эффекта. 
    Александр отправит план вентиляции. В прихожей оставляем зеленый потолок. 
    Диван нужно сделать менее угловатым, проверить пропорции. 
    Запросить данные по креслу за обеденным столом. 
    Добавить подсветку в нише для штор. 
    Александр пришлет ссылку на диагональ 77. 
    В санузле нужно место для полотенец и полотенцесушитель. 
    В прачечной забыли блок с гладильной доской. 
    Отпариватель будет в правом блоке. 
    Сушилку выдвижную убираем, оставляем только настенные сушилки.
    """,
    
    """
    Провели встречу с клиентом по проекту ремонта офиса. Обсудили планировку и материалы.
    Клиент хочет использовать экологичные материалы, предпочтительно дерево и стекло.
    Решили, что нужно заменить все окна на энергосберегающие. 
    Также договорились о замене напольного покрытия на паркет из дуба.
    Стены будут окрашены в светлые тона, предпочтительно белый и светло-серый.
    Клиент попросил предусмотреть больше мест для хранения документов.
    Нужно разработать дизайн-проект в течение двух недель и представить смету.
    Следующая встреча назначена на 15 мая.
    """
]

def test_protocol_generation():
    """
    Тестирование генерации протоколов на тестовых данных.
    Создает PDF-файлы и выводит текст протоколов.
    """
    # Создание директории для тестовых протоколов
    test_output_dir = "test_protocols"
    os.makedirs(test_output_dir, exist_ok=True)
    
    # Создание генератора протоколов
    generator = ProtocolGenerator()
    
    # Тестирование на каждой расшифровке
    for i, transcription in enumerate(TEST_TRANSCRIPTIONS):
        logger.info(f"Тестирование расшифровки #{i+1}")
        
        # Генерация протокола
        pdf_path, protocol_text = generator.process_voice_transcription(
            transcription, 
            output_dir=test_output_dir
        )
        
        # Вывод результатов
        logger.info(f"Текст протокола #{i+1}:\n{protocol_text}")
        logger.info(f"PDF-файл #{i+1} создан: {pdf_path}")
        
        # Проверка наличия файла
        if pdf_path and os.path.exists(pdf_path):
            logger.info(f"PDF-файл #{i+1} успешно создан и доступен")
        else:
            logger.error(f"Ошибка при создании PDF-файла #{i+1}")
    
    logger.info("Тестирование завершено")

if __name__ == "__main__":
    test_protocol_generation()
