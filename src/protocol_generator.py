"""
Модуль для генерации протоколов встреч на основе расшифровки голосовых сообщений.
Использует локальную модель LLM через Ollama API для структурирования текста
и WeasyPrint для создания PDF-документов.
"""

import os
import json
import requests
import logging
from pathlib import Path
from datetime import datetime
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

class ProtocolGenerator:
    """Класс для генерации протоколов встреч из расшифрованного текста."""
    
    def __init__(self, ollama_host="http://localhost:11434", model="llama3"):
        """
        Инициализация генератора протоколов.
        
        Args:
            ollama_host (str): URL-адрес Ollama API
            model (str): Название модели для использования (llama3, mistral, ...)
        """
        self.ollama_host = ollama_host
        self.model = model
        self.prompt_template = self._load_prompt_template()
        logger.info(f"Инициализирован генератор протоколов с моделью {model}")
        
    def _load_prompt_template(self):
        """Загрузка шаблона промпта для генерации протокола."""
        prompt_path = Path(__file__).parent / "prompts" / "protocol_prompt.md"
        
        # Если файл не существует, используем встроенный шаблон
        if not prompt_path.exists():
            return """
# Задача
Преобразуй расшифровку голосового сообщения в формализованный протокол встречи.

# Структура протокола
1. **Заголовок**: "Протокол встречи [ДАТА] ([ТЕМА])"
2. **Метаданные**:
   - Дата: [ДАТА]
   - Проект: [НАЗВАНИЕ ПРОЕКТА] | [ИДЕНТИФИКАТОР] | [ОТВЕТСТВЕННОЕ ЛИЦО]
3. **Повестка совещания**:
   - Подзаголовок: "Повестка совещания:"
   - Раздел "Вопросы:" с маркированным списком основных вопросов
4. **Решения и обсуждения**:
   - Подзаголовок: "Решили, обсудили:"
5. **Решения**:
   - Подзаголовок: "Решения:"
   - Пронумерованный список конкретных решений

# Расшифровка голосового сообщения:
{transcription}
"""
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def generate_protocol_text(self, transcription):
        """
        Генерация текста протокола на основе расшифровки голосового сообщения.
        
        Args:
            transcription (str): Расшифрованный текст голосового сообщения
            
        Returns:
            str: Структурированный текст протокола
        """
        try:
            # Подготовка промпта с расшифровкой
            prompt = self.prompt_template.replace("{transcription}", transcription)
            
            # Запрос к Ollama API
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Низкая температура для более детерминированных результатов
                        "top_p": 0.9
                    }
                },
                timeout=60
            )
            
            if response.status_code != 200:
                logger.error(f"Ошибка API Ollama: {response.status_code} - {response.text}")
                return f"Ошибка при генерации протокола: {response.status_code}"
            
            # Извлечение текста из ответа
            result = response.json()
            protocol_text = result.get("response", "")
            
            return protocol_text
            
        except Exception as e:
            logger.error(f"Ошибка при генерации протокола: {str(e)}")
            return f"Ошибка при генерации протокола: {str(e)}"
    
    def generate_protocol_pdf(self, protocol_text, output_path=None):
        """
        Создание PDF-документа из текста протокола.
        
        Args:
            protocol_text (str): Текст протокола в формате Markdown
            output_path (str, optional): Путь для сохранения PDF-файла
            
        Returns:
            str: Путь к созданному PDF-файлу
        """
        try:
            # Определение имени файла, если не указано
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"protocol_{timestamp}.pdf"
            
            # Преобразование Markdown в HTML
            html_content = self._markdown_to_html(protocol_text)
            
            # Настройка шрифтов
            font_config = FontConfiguration()
            css = CSS(string='''
                @page {
                    size: A4;
                    margin: 2cm;
                }
                body {
                    font-family: "Noto Sans", "Noto Sans CJK SC", sans-serif;
                    font-size: 12pt;
                    line-height: 1.5;
                }
                h1 {
                    font-size: 18pt;
                    font-weight: bold;
                    margin-bottom: 20pt;
                    text-align: center;
                }
                h2 {
                    font-size: 14pt;
                    font-weight: bold;
                    margin-top: 15pt;
                    margin-bottom: 10pt;
                }
                .metadata {
                    background-color: #f5f5f5;
                    padding: 10pt;
                    margin-bottom: 15pt;
                }
                .questions {
                    background-color: #f5f5f5;
                    padding: 10pt;
                    margin-bottom: 15pt;
                }
                .decisions {
                    background-color: #f5f5f5;
                    padding: 10pt;
                }
                ul {
                    margin-top: 5pt;
                    margin-bottom: 5pt;
                }
                ol {
                    margin-top: 5pt;
                    margin-bottom: 5pt;
                }
                li {
                    margin-bottom: 5pt;
                }
            ''', font_config=font_config)
            
            # Создание PDF
            HTML(string=html_content).write_pdf(
                output_path,
                stylesheets=[css],
                font_config=font_config
            )
            
            logger.info(f"PDF-протокол создан: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Ошибка при создании PDF: {str(e)}")
            return None
    
    def _markdown_to_html(self, markdown_text):
        """
        Преобразование текста Markdown в HTML.
        
        Args:
            markdown_text (str): Текст в формате Markdown
            
        Returns:
            str: HTML-представление текста
        """
        try:
            import markdown
            
            # Базовая структура HTML-документа
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Протокол встречи</title>
            </head>
            <body>
                {content}
            </body>
            </html>
            """
            
            # Преобразование Markdown в HTML
            html_content = markdown.markdown(
                markdown_text,
                extensions=['extra', 'smarty']
            )
            
            # Добавление классов для стилизации
            html_content = html_content.replace('<h1>', '<h1 class="title">')
            
            # Добавление классов для метаданных
            if '<p>Дата:' in html_content:
                start_idx = html_content.find('<p>Дата:')
                end_idx = html_content.find('<h2>', start_idx)
                if end_idx > start_idx:
                    metadata_html = html_content[start_idx:end_idx]
                    wrapped_metadata = f'<div class="metadata">{metadata_html}</div>'
                    html_content = html_content[:start_idx] + wrapped_metadata + html_content[end_idx:]
            
            # Добавление классов для вопросов
            if '<h2>Повестка совещания:</h2>' in html_content:
                start_idx = html_content.find('<h2>Повестка совещания:</h2>')
                next_h2_idx = html_content.find('<h2>', start_idx + 1)
                if next_h2_idx > start_idx:
                    questions_html = html_content[start_idx:next_h2_idx]
                    wrapped_questions = f'<div class="questions">{questions_html}</div>'
                    html_content = html_content[:start_idx] + wrapped_questions + html_content[next_h2_idx:]
            
            # Добавление классов для решений
            if '<h2>Решения:</h2>' in html_content:
                start_idx = html_content.find('<h2>Решения:</h2>')
                decisions_html = html_content[start_idx:]
                wrapped_decisions = f'<div class="decisions">{decisions_html}</div>'
                html_content = html_content[:start_idx] + wrapped_decisions
            
            return html_template.format(content=html_content)
            
        except Exception as e:
            logger.error(f"Ошибка при преобразовании Markdown в HTML: {str(e)}")
            # Возвращаем простой HTML при ошибке
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Протокол встречи</title>
            </head>
            <body>
                <pre>{markdown_text}</pre>
            </body>
            </html>
            """
    
    def process_voice_transcription(self, transcription, output_dir="protocols"):
        """
        Полный процесс обработки расшифровки голосового сообщения:
        1. Генерация структурированного текста протокола
        2. Создание PDF-документа
        
        Args:
            transcription (str): Расшифрованный текст голосового сообщения
            output_dir (str): Директория для сохранения результатов
            
        Returns:
            tuple: (путь к PDF-файлу, текст протокола)
        """
        try:
            # Создание директории, если не существует
            os.makedirs(output_dir, exist_ok=True)
            
            # Генерация текста протокола
            protocol_text = self.generate_protocol_text(transcription)
            
            # Определение имени файла на основе даты
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_path = os.path.join(output_dir, f"protocol_{timestamp}.pdf")
            
            # Создание PDF
            pdf_path = self.generate_protocol_pdf(protocol_text, pdf_path)
            
            return pdf_path, protocol_text
            
        except Exception as e:
            logger.error(f"Ошибка при обработке расшифровки: {str(e)}")
            return None, f"Ошибка при обработке расшифровки: {str(e)}"


# Пример использования
if __name__ == "__main__":
    # Пример расшифровки голосового сообщения
    sample_transcription = """
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
    """
    
    # Создание генератора протоколов
    generator = ProtocolGenerator()
    
    # Генерация протокола
    pdf_path, protocol_text = generator.process_voice_transcription(sample_transcription)
    
    print(f"Текст протокола:\n{protocol_text}")
    print(f"PDF-файл создан: {pdf_path}")
