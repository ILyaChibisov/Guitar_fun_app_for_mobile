# buildozer.spec

[app]

# --- ОСНОВНЫЕ НАСТРОЙКИ ---
title = GuitarFuns
package.name = guitarfuns
package.domain = com.guitarfuns
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,txt,json

# Включаем все файлы аккордов рекурсивно
source.include_patterns = chords/**, data/**, **/*.py

# Исключаем ненужные файлы
source.exclude_patterns = **/__pycache__, **/*.pyc, .venv, .git, test_*.py, check_*.py, create_icons.py, prepare_icons.py

version = 1.0.3
version.code = 2
orientation = portrait

# --- ИКОНКА ПРИЛОЖЕНИЯ ---
icon.filename = android_res/drawable/icon.png

# --- ЗАВИСИМОСТИ ---
requirements = python3,kivy==2.3.1,kivymd==1.2.0,requests,pillow,plyer,openssl,pyopenssl,asynckivy,asyncgui,certifi,urllib3

# --- ПРАВА ---
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,RECORD_AUDIO
android.api = 33
android.minapi = 24
android.enable_androidx = True
android.accept_sdk_license = True

# ВАЖНО: собираем только под одну архитектуру для ускорения.
# Когда сборка стабильно заработает — можно добавить armeabi-v7a.
android.archs = arm64-v8a

# --- ОТЛАДКА ---
fullscreen = 0
log_level = 1
# p4a.branch = develop  <-- убрано, используем стабильный master по умолчанию

# --- УВЕЛИЧИВАЕМ ВРЕМЯ СБОРКИ ---
android.gradle_repository_threads = 4

# --- ПОДПИСЬ (для релиза) ---
android.keystore = guitarfuns_keystore.jks
android.keystore_alias = guitarfuns
android.keystore_key_password = lexx311285

[buildozer]
log_level = 1
warn_on_root = 1