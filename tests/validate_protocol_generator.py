"""
Тестовый скрипт для валидации качества генерации протоколов.
Запускает процесс генерации протоколов на тестовых данных и проверяет результаты.
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
    
    # Создание генератора протоколов с использованием заглушки вместо Ollama
    generator = MockProtocolGenerator()
    
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

class MockProtocolGenerator(ProtocolGenerator):
    """
    Мок-класс для генератора протоколов, который не требует запущенного Ollama.
    Используется для тестирования функциональности без зависимости от внешних сервисов.
    """
    
    def __init__(self):
        """Инициализация мок-генератора протоколов."""
        # Не вызываем родительский __init__, чтобы избежать подключения к Ollama
        self.prompt_template = self._load_prompt_template()
        logger.info("Инициализирован мок-генератор протоколов для тестирования")
    
    def generate_protocol_text(self, transcription):
        """
        Генерация текста протокола на основе расшифровки голосового сообщения.
        Возвращает предопределенный текст протокола вместо обращения к Ollama.
        
        Args:
            transcription (str): Расшифрованный текст голосового сообщения
            
        Returns:
            str: Структурированный текст протокола
        """
        # Извлекаем дату из текста или используем текущую
        import re
        from datetime import datetime
        
        date_match = re.search(r'\d{1,2}\s+\w+', transcription)
        if date_match:
            meeting_date = date_match.group(0)
        else:
            meeting_date = datetime.now().strftime("%d.%m.%Y")
        
        # Определяем тему встречи из текста
        if "3д визуализацию" in transcription:
            topic = "3D визуализация"
            project = "25-24 ДП"
            responsible = "Александр"
        elif "ремонта офиса" in transcription:
            topic = "Ремонт офиса"
            project = "Офис-2025"
            responsible = "Клиент"
        else:
            topic = "Обсуждение проекта"
            project = "Проект"
            responsible = "Заказчик"
        
        # Извлекаем вопросы из текста
        questions = []
        for line in transcription.split('\n'):
            line = line.strip()
            if line and len(line) > 10 and not line.startswith("Сегодня") and not line.startswith("Провели"):
                questions.append(f"- {line}")
        
        # Формируем решения
        decisions = []
        for i, q in enumerate(questions[:5], 1):
            decisions.append(f"{i}. {q[2:]}")
        
        # Формируем протокол
        protocol = f"""# Протокол встречи {meeting_date} ({topic})

Дата: {meeting_date}
Проект: {project} | Ответственное лицо: {responsible}

## Повестка совещания:

### Вопросы:
{chr(10).join(questions[:5])}

## Решили, обсудили:

{transcription}

## Решения:

{chr(10).join(decisions)}
"""
        return protocol

if __name__ == "__main__":
    test_protocol_generation()
