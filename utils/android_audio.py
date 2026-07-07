# utils/android_audio.py
"""
Захват звука на Android через JNI (AudioRecord)
Работает в реальном времени без audiostream
"""
import threading
import struct
from kivy.utils import platform

logger = None


def get_logger():
    global logger
    if logger is None:
        from config.logger_config import get_logger
        logger = get_logger('AndroidAudio')
    return logger


class AndroidAudioRecorder:
    """Захват звука на Android через JNI"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._running = False
        self._thread = None
        self._callback = None
        self._sample_rate = 44100
        self._chunk_size = 1024

        # JNI классы
        self._AudioRecord = None
        self._AudioFormat = None
        self._MediaRecorder = None
        self._init_jni()

    def _init_jni(self):
        """Инициализирует JNI классы"""
        if platform != 'android':
            return

        try:
            from jnius import autoclass
            from android.permissions import request_permissions, Permission

            # Запрашиваем разрешение
            request_permissions([Permission.RECORD_AUDIO])

            # Загружаем классы
            self._AudioRecord = autoclass('android.media.AudioRecord')
            self._AudioFormat = autoclass('android.media.AudioFormat')
            self._MediaRecorder = autoclass('android.media.MediaRecorder')

            # Константы
            self._CHANNEL_CONFIG = self._AudioFormat.CHANNEL_IN_MONO
            self._ENCODING = self._AudioFormat.ENCODING_PCM_16BIT
            self._SOURCE = self._MediaRecorder.AudioSource.MIC

            logger = get_logger()
            logger.info("✅ JNI AudioRecord инициализирован")

        except Exception as e:
            logger = get_logger()
            logger.error(f"❌ Ошибка инициализации JNI AudioRecord: {e}")

    def start_recording(self, callback, sample_rate=44100, chunk_size=1024):
        """Запускает запись с микрофона"""
        if self._running:
            return

        if platform != 'android':
            logger = get_logger()
            logger.warning("⚠️ AndroidAudioRecorder работает только на Android")
            return

        if not self._AudioRecord:
            logger = get_logger()
            logger.error("❌ JNI не инициализирован")
            return

        self._callback = callback
        self._sample_rate = sample_rate
        self._chunk_size = chunk_size
        self._running = True

        self._thread = threading.Thread(target=self._record_loop)
        self._thread.daemon = True
        self._thread.start()

        logger = get_logger()
        logger.info(f"🎤 Запись запущена: {sample_rate}Hz, {chunk_size} samples")

    def stop_recording(self):
        """Останавливает запись"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
            self._thread = None

        logger = get_logger()
        logger.info("⏹ Запись остановлена")

    def _record_loop(self):
        """Цикл записи звука"""
        try:
            # Создаем AudioRecord
            buffer_size = self._AudioRecord.getMinBufferSize(
                self._sample_rate,
                self._CHANNEL_CONFIG,
                self._ENCODING
            ) * 2

            audio_record = self._AudioRecord(
                self._SOURCE,
                self._sample_rate,
                self._CHANNEL_CONFIG,
                self._ENCODING,
                buffer_size
            )

            if audio_record.getState() != self._AudioRecord.STATE_INITIALIZED:
                logger = get_logger()
                logger.error("❌ AudioRecord не инициализирован")
                return

            audio_record.startRecording()

            logger = get_logger()
            logger.info("✅ AudioRecord запущен")

            # Буфер для данных
            buffer = bytearray(self._chunk_size * 2)

            while self._running:
                bytes_read = audio_record.read(buffer, 0, len(buffer))

                if bytes_read > 0 and self._callback:
                    data = bytes(buffer[:bytes_read])
                    self._callback(data)

            audio_record.stop()
            audio_record.release()

        except Exception as e:
            logger = get_logger()
            logger.error(f"❌ Ошибка в цикле записи: {e}")
            self._running = False

    def is_recording(self):
        return self._running


# Глобальный экземпляр
_audio_recorder = None


def get_audio_recorder():
    """Возвращает глобальный экземпляр AudioRecorder"""
    global _audio_recorder
    if _audio_recorder is None:
        _audio_recorder = AndroidAudioRecorder()
    return _audio_recorder