"""
Исправленный модуль для распознавания речи с использованием различных движков.
Поддерживает Whisper и Vosk.
"""

import os
import logging
from abc import ABC, abstractmethod

import whisper
from pydub import AudioSegment

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpeechRecognitionEngine(ABC):
    """Абстрактный класс для движков распознавания речи."""
    
    @abstractmethod
    def recognize_speech(self, audio_path):
        """
        Распознает речь из аудиофайла.
        
        Args:
            audio_path (str): Путь к аудиофайлу.
            
        Returns:
            str: Распознанный текст.
        """
        pass
    
    # Для обратной совместимости
    def recognize(self, audio_path):
        """Алиас для recognize_speech для обратной совместимости."""
        return self.recognize_speech(audio_path)


class WhisperEngine(SpeechRecognitionEngine):
    """Движок распознавания речи на основе OpenAI Whisper."""
    
    def __init__(self, model_name="tiny"):
        """
        Инициализирует движок Whisper.
        
        Args:
            model_name (str): Название модели Whisper (tiny, base, small, medium, large).
        """
        logger.info(f"Инициализация Whisper с моделью {model_name}")
        try:
            self.model = whisper.load_model(model_name)
            logger.info("Модель Whisper успешно загружена")
        except Exception as e:
            logger.error(f"Ошибка при загрузке модели Whisper: {e}")
            raise
    
    def recognize_speech(self, audio_path):
        """
        Распознает речь из аудиофайла с помощью Whisper.
        
        Args:
            audio_path (str): Путь к аудиофайлу.
            
        Returns:
            str: Распознанный текст.
        """
        try:
            # Конвертация аудио в формат WAV, если это не WAV
            if not audio_path.lower().endswith('.wav'):
                wav_path = audio_path.rsplit('.', 1)[0] + '.wav'
                audio = AudioSegment.from_file(audio_path)
                audio.export(wav_path, format="wav")
                audio_path = wav_path
            
            # Распознавание речи
            logger.info(f"Распознавание речи из файла {audio_path}")
            result = self.model.transcribe(audio_path)
            return result["text"].strip()
        except Exception as e:
            logger.error(f"Ошибка при распознавании речи с Whisper: {e}")
            return "Ошибка распознавания речи."


class VoskEngine(SpeechRecognitionEngine):
    """Движок распознавания речи на основе Vosk."""
    
    def __init__(self, model_path="model"):
        """
        Инициализирует движок Vosk.
        
        Args:
            model_path (str): Путь к модели Vosk.
        """
        try:
            from vosk import Model, KaldiRecognizer, SetLogLevel
            import wave
            
            self.KaldiRecognizer = KaldiRecognizer
            self.wave = wave
            
            # Отключение логов Vosk
            SetLogLevel(-1)
            
            logger.info(f"Инициализация Vosk с моделью из {model_path}")
            if not os.path.exists(model_path):
                logger.error(f"Модель Vosk не найдена по пути {model_path}")
                raise FileNotFoundError(f"Модель Vosk не найдена по пути {model_path}")
            
            self.model = Model(model_path)
            logger.info("Модель Vosk успешно загружена")
        except ImportError:
            logger.error("Библиотека Vosk не установлена")
            raise
        except Exception as e:
            logger.error(f"Ошибка при инициализации Vosk: {e}")
            raise
    
    def recognize_speech(self, audio_path):
        """
        Распознает речь из аудиофайла с помощью Vosk.
        
        Args:
            audio_path (str): Путь к аудиофайлу.
            
        Returns:
            str: Распознанный текст.
        """
        try:
            # Конвертация аудио в формат WAV, если это не WAV
            if not audio_path.lower().endswith('.wav'):
                wav_path = audio_path.rsplit('.', 1)[0] + '.wav'
                audio = AudioSegment.from_file(audio_path)
                audio = audio.set_channels(1)  # Vosk требует моно аудио
                audio = audio.set_frame_rate(16000)  # Рекомендуемая частота дискретизации для Vosk
                audio.export(wav_path, format="wav")
                audio_path = wav_path
            
            # Распознавание речи
            logger.info(f"Распознавание речи из файла {audio_path}")
            wf = self.wave.open(audio_path, "rb")
            
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                logger.warning("Аудио не соответствует требованиям Vosk (моно, 16 бит, PCM)")
            
            rec = self.KaldiRecognizer(self.model, wf.getframerate())
            rec.SetWords(True)
            
            result = ""
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    pass
            
            final_result = rec.FinalResult()
            import json
            result_dict = json.loads(final_result)
            return result_dict.get("text", "").strip()
        except Exception as e:
            logger.error(f"Ошибка при распознавании речи с Vosk: {e}")
            return "Ошибка распознавания речи."


def get_speech_recognition_engine(engine_type, **kwargs):
    """
    Фабричный метод для создания движка распознавания речи.
    
    Args:
        engine_type (str): Тип движка ("whisper" или "vosk").
        **kwargs: Дополнительные параметры для движка.
        
    Returns:
        SpeechRecognitionEngine: Экземпляр движка распознавания речи.
    """
    if engine_type.lower() == "whisper":
        model_name = kwargs.get("model_name", "tiny")
        return WhisperEngine(model_name)
    elif engine_type.lower() == "vosk":
        model_path = kwargs.get("model_path", "model")
        return VoskEngine(model_path)
    else:
        raise ValueError(f"Неизвестный тип движка: {engine_type}")
