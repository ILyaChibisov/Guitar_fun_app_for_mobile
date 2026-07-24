# buildozer.spec

[app]

# --- ОСНОВНЫЕ НАСТРОЙКИ ---
title = GuitarFuns
package.name = guitarfuns
package.domain = com.guitarfuns
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,txt,json

# Включаем все файлы аккордов рекурсивно
source.include_patterns = chords/**, **/*.py

# Исключаем ненужные файлы
source.exclude_patterns = **/__pycache__, **/*.pyc, .venv, .git, test_*.py, check_*.py, create_icons.py, prepare_icons.py

version = 1.0.3
version.code = 2
orientation = portrait

# --- ИКОНКА ПРИЛОЖЕНИЯ ---
icon.filename = android_res/drawable/icon.png

# --- ЗАВИСИМОСТИ ---
# УБРАЛИ audiostream - используем JNI напрямую через jnius (уже есть в kivy)
requirements = python3,kivy==2.3.1,kivymd==1.2.0,requests,pillow,plyer,openssl,pyopenssl,asynckivy,asyncgui,certifi,urllib3


# --- ПРАВА ---
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,RECORD_AUDIO
android.api = 33
android.minapi = 24
android.enable_androidx = True
android.add_network_security_config = True
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True

# --- ОТЛАДКА ---
fullscreen = 0
log_level = 2
p4a.branch = develop

# --- УВЕЛИЧИВАЕМ ВРЕМЯ СБОРКИ ---
android.gradle_repository_threads = 4

# --- ПОДПИСЬ (для релиза) ---
android.keystore = guitarfuns_keystore.jks
android.keystore_alias = guitarfuns
android.keystore_key_password = lexx311285

[buildozer]
log_level = 2
warn_on_root = 1

[gradle]
user_repos = https://google.com/