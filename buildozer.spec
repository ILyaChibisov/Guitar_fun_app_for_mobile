[app]

# --- ОСНОВНЫЕ НАСТРОЙКИ ---
title = GuitarFuns
package.name = guitarfuns
package.domain = com.guitarfuns
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,txt,json,wav,mp3,ogg

# Включаем все файлы рекурсивно
source.include_patterns = chords/**, dicts/**, **/*.py, **/*.png, **/*.jpg, **/*.json

# Исключаем ненужные файлы
source.exclude_patterns = **/__pycache__, **/*.pyc, .venv, .git, test_*.py, check_*.py

# ПОВЫШАЕМ ВЕРСИЮ
version = 1.0.3
version.code = 3
orientation = portrait

# --- ЗАВИСИМОСТИ (ДОБАВЛЯЕМ ffpyplayer ДЛЯ ЗВУКА) ---
requirements = python3,\
    kivy==2.3.1,\
    kivymd==1.2.0,\
    requests,\
    pillow,\
    plyer,\
    openssl,\
    pyopenssl,\
    asynckivy,\
    asyncgui,\
    pyjnius,\
    ffpyplayer

# --- ПРАВА (ДОБАВЛЯЕМ ВСЕ НЕОБХОДИМЫЕ) ---
android.permissions = INTERNET,\
    ACCESS_NETWORK_STATE,\
    ACCESS_WIFI_STATE,\
    MODIFY_AUDIO_SETTINGS,\
    WRITE_EXTERNAL_STORAGE,\
    READ_EXTERNAL_STORAGE

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

# --- ОТКЛЮЧАЕМ libthorvg ---
p4a.recipes = sdl2,python3,kivy,kivymd,requests,pillow,plyer,pyjnius,ffpyplayer

# --- УВЕЛИЧИВАЕМ ВРЕМЯ СБОРКИ ---
android.gradle_repository_threads = 4
android.ndk = 25b

# --- ПОДПИСЬ ---
android.keystore = guitarfuns_keystore.jks
android.keystore_alias = guitarfuns
android.keystore_key_password = lexx311285

[buildozer]
log_level = 2
warn_on_root = 1

[gradle]
user_repos = https://google.com/