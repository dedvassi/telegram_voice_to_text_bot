"""
Модуль для генерации протоколов встреч на основе расшифровки голосовых сообщений.
Использует FPDF2 для создания PDF-документов с поддержкой кириллицы через LiberationSans.
"""

import os
import re
import json
import logging
import requests
import tempfile
from datetime import datetime
from pathlib import Path
from fpdf import FPDF

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProtocolGenerator:
    """
    Класс для генерации протоколов встреч на основе расшифровки голосовых сообщений.
    Использует локальную модель LLM через Ollama для структурирования текста
    и FPDF2 для создания PDF-документов с поддержкой кириллицы.
    """
    
    def __init__(self, model_name="llama3", ollama_url="http://localhost:11434"):
        """
        Инициализация генератора протоколов.
        
        Args:
            model_name (str): Название модели Ollama (llama3, mistral, etc.)
            ollama_url (str): URL для API Ollama
        """
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.prompt_template = self._load_prompt_template()
        
        # Проверка доступности Ollama
        try:
            self._check_ollama_availability()
            logger.info(f"Ollama доступен, используется модель {model_name}")
        except Exception as e:
            logger.warning(f"Ollama недоступен: {e}. Будет использоваться базовое форматирование.")
    
    def _load_prompt_template(self):
        """
        Загружает шаблон промпта для генерации протокола.
        
        Returns:
            str: Шаблон промпта
        """
        # Базовый шаблон промпта
        return """
        Ты профессиональный секретарь, который создает структурированные протоколы встреч.
        
        Преобразуй следующую расшифровку голосового сообщения в формальный протокол встречи.
        
        Структура протокола должна включать:
        1. Заголовок с датой и темой встречи
        2. Список участников (если упоминаются)
        3. Повестку встречи в виде списка вопросов
        4. Основное содержание обсуждения
        5. Принятые решения и ответственных лиц
        6. Сроки выполнения (если упоминаются)
        
        Расшифровка голосового сообщения:
        {transcription}
        
        Создай хорошо структурированный, профессиональный протокол на основе этой информации.
        """
    
    def _check_ollama_availability(self):
        """
        Проверяет доступность Ollama API.
        
        Raises:
            Exception: Если Ollama недоступен
        """
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            if response.status_code != 200:
                raise Exception(f"Ollama вернул код ошибки: {response.status_code}")
            
            # Проверка наличия нужной модели
            models = response.json().get("models", [])
            model_names = [model.get("name") for model in models]
            
            if not model_names:
                raise Exception("Нет доступных моделей")
            
            if self.model_name not in model_names:
                logger.warning(f"Модель {self.model_name} не найдена. Доступные модели: {', '.join(model_names)}")
                logger.warning(f"Будет использована первая доступная модель: {model_names[0]}")
                self.model_name = model_names[0]
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Не удалось подключиться к Ollama: {e}")
    
    def generate_protocol_text(self, transcription):
        """
        Генерация текста протокола на основе расшифровки голосового сообщения.
        
        Args:
            transcription (str): Расшифрованный текст голосового сообщения
            
        Returns:
            str: Структурированный текст протокола
        """
        try:
            # Попытка использовать Ollama для генерации протокола
            prompt = self.prompt_template.format(transcription=transcription)
            
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                logger.warning(f"Ошибка Ollama API: {response.status_code}. Использую базовое форматирование.")
                return self._basic_protocol_formatting(transcription)
                
        except Exception as e:
            logger.warning(f"Ошибка при генерации протокола через Ollama: {e}. Использую базовое форматирование.")
            return self._basic_protocol_formatting(transcription)
    
    def _basic_protocol_formatting(self, transcription):
        """
        Базовое форматирование протокола без использования LLM.
        
        Args:
            transcription (str): Расшифрованный текст голосового сообщения
            
        Returns:
            str: Базовый структурированный текст протокола
        """
        # Извлекаем дату из текста или используем текущую
        date_match = re.search(r'\d{1,2}\s+\w+|\d{1,2}\.\d{1,2}\.\d{2,4}', transcription)
        if date_match:
            meeting_date = date_match.group(0)
        else:
            meeting_date = datetime.now().strftime("%d.%m.%Y")
        
        # Определяем тему встречи из текста
        topic_match = re.search(r'(встреч[а-я]+|совещани[а-я]+|обсуждени[а-я]+)\s+(?:по|о|об|с)\s+([^\.]+)', transcription, re.IGNORECASE)
        if topic_match:
            topic = topic_match.group(2).strip()
        else:
            topic = "Обсуждение проекта"
        
        # Извлекаем вопросы из текста
        lines = [line.strip() for line in transcription.split('.') if len(line.strip()) > 10]
        questions = []
        for i, line in enumerate(lines[:5], 1):
            questions.append(f"{i}. {line}.")
        
        # Формируем протокол
        protocol = f"""# Протокол встречи от {meeting_date}

## Тема: {topic}

## Повестка совещания:

{chr(10).join(questions)}

## Содержание обсуждения:

{transcription}

## Решения и задачи:

1. Подготовить документацию по обсуждаемым вопросам
2. Согласовать сроки выполнения задач
3. Назначить ответственных за реализацию

Дата составления протокола: {datetime.now().strftime("%d.%m.%Y")}
"""
        return protocol
    
    def generate_pdf(self, protocol_text, output_path):
        """
        Создает PDF-документ на основе текста протокола с использованием FPDF2.
        Поддерживает кириллицу через шрифт LiberationSans.
        
        Args:
            protocol_text (str): Текст протокола в формате Markdown
            output_path (str): Путь для сохранения PDF-файла
            
        Returns:
            str: Путь к созданному PDF-файлу
        """
        try:
            # Пути к шрифтам LiberationSans
            fonts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fonts')
            regular_font_path = os.path.join(fonts_dir, 'LiberationSans-Regular.ttf')
            bold_font_path = os.path.join(fonts_dir, 'LiberationSans-Bold.ttf')
            
            # Проверяем наличие шрифтов
            if not os.path.exists(regular_font_path) or not os.path.exists(bold_font_path):
                logger.warning(f"Шрифты не найдены в директории проекта: {fonts_dir}")
                # Пытаемся найти шрифты в системе (для Linux)
                system_font_paths = {
                    "regular": [
                        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                        "/usr/share/fonts/TTF/LiberationSans-Regular.ttf"
                    ],
                    "bold": [
                        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                        "/usr/share/fonts/TTF/LiberationSans-Bold.ttf"
                    ]
                }
                
                for system_path in system_font_paths["regular"]:
                    if os.path.exists(system_path):
                        regular_font_path = system_path
                        logger.info(f"Используется системный шрифт Regular: {regular_font_path}")
                        break
                
                for system_path in system_font_paths["bold"]:
                    if os.path.exists(system_path):
                        bold_font_path = system_path
                        logger.info(f"Используется системный шрифт Bold: {bold_font_path}")
                        break
                
                if not os.path.exists(regular_font_path) or not os.path.exists(bold_font_path):
                    # Если шрифты не найдены, сохраняем только текстовый файл
                    logger.warning("Шрифты с поддержкой кириллицы не найдены. Сохраняем только текстовый файл.")
                    txt_path = output_path.replace('.pdf', '.txt')
                    with open(txt_path, 'w', encoding='utf-8') as f:
                        f.write(protocol_text)
                    return txt_path
            
            # Создаем PDF-документ с поддержкой кириллицы
            pdf = FPDF()
            pdf.add_page()
            
            # Регистрируем шрифты LiberationSans
            pdf.add_font("liberation", "", regular_font_path, uni=True)
            pdf.add_font("liberation", "B", bold_font_path, uni=True)
            
            # Устанавливаем шрифт по умолчанию
            pdf.set_font("liberation", size=12)
            
            # Парсинг Markdown и добавление в PDF
            lines = protocol_text.split('\n')
            for line in lines:
                # Обработка заголовков
                if line.startswith('# '):
                    pdf.set_font("liberation", 'B', size=16)
                    pdf.cell(0, 10, line[2:], ln=True)
                    pdf.ln(5)
                    pdf.set_font("liberation", size=12)
                elif line.startswith('## '):
                    pdf.set_font("liberation", 'B', size=14)
                    pdf.cell(0, 10, line[3:], ln=True)
                    pdf.ln(3)
                    pdf.set_font("liberation", size=12)
                elif line.startswith('### '):
                    pdf.set_font("liberation", 'B', size=13)
                    pdf.cell(0, 10, line[4:], ln=True)
                    pdf.set_font("liberation", size=12)
                # Обработка списков
                elif line.strip().startswith('- '):
                    pdf.cell(10, 10, "•", ln=0)
                    pdf.cell(0, 10, line.strip()[2:], ln=True)
                elif re.match(r'^\d+\.\s', line.strip()):
                    pdf.cell(0, 10, line.strip(), ln=True)
                # Обычный текст
                elif line.strip():
                    pdf.multi_cell(0, 10, line)
                # Пустая строка
                else:
                    pdf.ln(5)
            
            # Добавляем номер страницы в футер
            pdf.set_y(-15)
            pdf.set_font("liberation", size=8)
            pdf.cell(0, 10, f"Страница {pdf.page_no()}", 0, 0, "C")
            
            # Сохраняем PDF
            pdf.output(output_path)
            logger.info(f"PDF-протокол создан: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Ошибка при создании PDF: {e}")
            # Альтернативный вариант - сохранить как текстовый файл
            try:
                txt_path = output_path.replace('.pdf', '.txt')
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(protocol_text)
                logger.info(f"Текстовый протокол создан: {txt_path}")
                return txt_path
            except Exception as txt_error:
                logger.error(f"Ошибка при создании текстового файла: {txt_error}")
                return None
    
    def process_voice_transcription(self, transcription, output_dir="protocols"):
        """
        Обрабатывает расшифровку голосового сообщения и создает протокол.
        
        Args:
            transcription (str): Расшифрованный текст голосового сообщения
            output_dir (str): Директория для сохранения протоколов
            
        Returns:
            tuple: (путь_к_pdf, текст_протокола)
        """
        try:
            # Создаем директорию для протоколов, если она не существует
            os.makedirs(output_dir, exist_ok=True)
            
            # Генерация текста протокола
            protocol_text = self.generate_protocol_text(transcription)
            
            # Создание имени файла на основе текущей даты и времени
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_path = os.path.join(output_dir, f"protocol_{timestamp}.pdf")
            
            # Создание PDF-документа
            result_path = self.generate_pdf(protocol_text, pdf_path)
            
            return result_path, protocol_text
            
        except Exception as e:
            logger.error(f"Ошибка при обработке расшифровки: {e}")
            return None, protocol_text
