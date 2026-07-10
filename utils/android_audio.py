# utils/android_audio.py
"""
Захват звука на Android через JNI (AudioRecord)
С ПОЛНОЙ ОТЛАДКОЙ В ИНТЕРФЕЙСЕ
"""
import threading
import time
from kivy.utils import platform
from kivy.clock import Clock

# Глобальный callback для отображения в UI
_debug_callback = None


def set_debug_callback(callback):
    """Устанавливает callback для отладки"""
    global _debug_callback
    _debug_callback = callback


def debug_log(message, level="INFO"):
    """Логирует отладочное сообщение в UI и консоль"""
    global _debug_callback
    if _debug_callback:
        Clock.schedule_once(lambda dt: _debug_callback(message, level), 0)

    # Также пишем в консоль
    prefix = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "DEBUG": "🔍"
    }.get(level, "🔍")
    print(f"{prefix} {message}")


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
        self._frame_count = 0
        self._data_received = False
        self._start_time = 0
        self._last_log_time = 0

        # JNI классы
        self._AudioRecord = None
        self._AudioFormat = None
        self._MediaRecorder = None
        self._init_jni()

    def _init_jni(self):
        """Инициализирует JNI классы"""
        if platform != 'android':
            debug_log("⚠️ Не Android платформа, JNI не инициализируется", "WARNING")
            return

        try:
            from jnius import autoclass
            from android.permissions import request_permissions, Permission

            debug_log("📱 Запрос разрешения RECORD_AUDIO...", "DEBUG")
            request_permissions([Permission.RECORD_AUDIO])
            debug_log("✅ Разрешение RECORD_AUDIO запрошено", "SUCCESS")

            # Загружаем классы
            debug_log("📱 Загрузка JNI классов...", "DEBUG")
            self._AudioRecord = autoclass('android.media.AudioRecord')
            self._AudioFormat = autoclass('android.media.AudioFormat')
            self._MediaRecorder = autoclass('android.media.MediaRecorder')

            # Константы
            self._CHANNEL_CONFIG = self._AudioFormat.CHANNEL_IN_MONO
            self._ENCODING = self._AudioFormat.ENCODING_PCM_16BIT
            self._SOURCE = self._MediaRecorder.AudioSource.MIC

            debug_log("✅ JNI AudioRecord инициализирован", "SUCCESS")
            logger = get_logger()
            logger.info("✅ JNI AudioRecord инициализирован")

        except Exception as e:
            debug_log(f"❌ Ошибка JNI: {str(e)[:150]}", "ERROR")
            logger = get_logger()
            logger.error(f"❌ Ошибка инициализации JNI AudioRecord: {e}")
            raise

    def start_recording(self, callback, sample_rate=44100, chunk_size=1024):
        """Запускает запись с микрофона"""
        if self._running:
            debug_log("⚠️ Запись уже запущена", "WARNING")
            return

        if platform != 'android':
            debug_log("⚠️ AndroidAudioRecorder работает только на Android", "WARNING")
            return

        if not self._AudioRecord:
            debug_log("❌ JNI не инициализирован", "ERROR")
            raise Exception("JNI AudioRecord не инициализирован")

        self._callback = callback
        self._sample_rate = sample_rate
        self._chunk_size = chunk_size
        self._running = True
        self._frame_count = 0
        self._data_received = False
        self._start_time = time.time()
        self._last_log_time = 0

        debug_log(f"🎤 Запуск записи: {sample_rate}Hz, {chunk_size} samples", "INFO")

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

        elapsed = time.time() - self._start_time
        debug_log(f"⏹ Запись остановлена. Всего фреймов: {self._frame_count}, время: {elapsed:.1f}с", "INFO")

        logger = get_logger()
        logger.info(f"⏹ Запись остановлена, всего фреймов: {self._frame_count}")

    def _record_loop(self):
        """Цикл записи звука"""
        try:
            logger = get_logger()

            # Получаем минимальный размер буфера
            debug_log("📊 Получение минимального размера буфера...", "DEBUG")
            buffer_size = self._AudioRecord.getMinBufferSize(
                self._sample_rate,
                self._CHANNEL_CONFIG,
                self._ENCODING
            ) * 2

            debug_log(f"📊 Buffer size: {buffer_size}", "DEBUG")

            # Создаем AudioRecord
            debug_log("📱 Создание AudioRecord...", "DEBUG")
            audio_record = self._AudioRecord(
                self._SOURCE,
                self._sample_rate,
                self._CHANNEL_CONFIG,
                self._ENCODING,
                buffer_size
            )

            state = audio_record.getState()
            debug_log(f"📊 AudioRecord state: {state}", "DEBUG")

            if state != self._AudioRecord.STATE_INITIALIZED:
                debug_log(f"❌ AudioRecord НЕ инициализирован (state: {state})", "ERROR")
                logger.error(f"❌ AudioRecord не инициализирован (state: {state})")
                self._running = False
                return

            debug_log("✅ AudioRecord инициализирован, запуск записи...", "SUCCESS")
            audio_record.startRecording()

            # Проверяем что запись действительно началась
            recording_state = audio_record.getRecordingState()
            if recording_state != self._AudioRecord.RECORDSTATE_RECORDING:
                debug_log(f"❌ AudioRecord НЕ начал запись (state: {recording_state})", "ERROR")
                self._running = False
                return

            debug_log("✅ AudioRecord запущен, начата запись!", "SUCCESS")
            logger.info("✅ AudioRecord запущен, начата запись...")

            buffer = bytearray(self._chunk_size * 2)

            while self._running:
                bytes_read = audio_record.read(buffer, 0, len(buffer))

                if bytes_read > 0 and self._callback:
                    self._frame_count += 1

                    # Первый полученный фрейм
                    if not self._data_received:
                        self._data_received = True
                        debug_log(f"🎉 ПЕРВЫЕ ДАННЫЕ ПОЛУЧЕНЫ! {bytes_read} байт", "SUCCESS")

                    # Логируем каждые 100 фреймов
                    if self._frame_count % 100 == 0:
                        elapsed = time.time() - self._start_time
                        debug_log(f"📊 Фрейм {self._frame_count}, байт: {bytes_read}, время: {elapsed:.1f}с", "DEBUG")

                    data = bytes(buffer[:bytes_read])
                    self._callback(data)
                else:
                    # Если данные не приходят - логируем один раз в 3 секунды
                    if self._frame_count == 0:
                        current_time = time.time()
                        if current_time - self._last_log_time > 3.0:
                            debug_log(f"⚠️ Нет данных от AudioRecord... (bytes_read: {bytes_read})", "WARNING")
                            self._last_log_time = current_time

            audio_record.stop()
            audio_record.release()

            elapsed = time.time() - self._start_time
            debug_log(f"⏹ Запись остановлена, всего фреймов: {self._frame_count}, время: {elapsed:.1f}с", "INFO")
            logger.info(f"⏹ Запись остановлена, всего фреймов: {self._frame_count}")

        except Exception as e:
            debug_log(f"❌ ОШИБКА В ЦИКЛЕ: {str(e)[:200]}", "ERROR")
            logger = get_logger()
            logger.error(f"❌ Ошибка в цикле записи: {e}")
            import traceback
            traceback.print_exc()
            self._running = False
            raise


# Глобальный экземпляр
_audio_recorder = None


def get_audio_recorder():
    """Возвращает глобальный экземпляр AudioRecorder"""
    global _audio_recorder
    if _audio_recorder is None:
        _audio_recorder = AndroidAudioRecorder()
    return _audio_recorder