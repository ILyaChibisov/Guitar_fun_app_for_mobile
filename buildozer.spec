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
source.exclude_patterns = **/__pycache__, **/*.pyc, .venv, .git, test_*.py, check_*.py

version = 1.0.0
orientation = portrait

# --- ЗАВИСИМОСТИ ---
# Убрали cython==3.0.11 (он может вызывать проблемы)
requirements = python3,kivy==2.3.1,kivymd==1.2.0,requests,pillow,plyer,openssl,pyopenssl,asynckivy,asyncgui

# Для работы с base64 изображениями
requirements.android = python3,kivy==2.3.1,kivymd==1.2.0,requests,pillow,plyer,openssl,pyopenssl

# --- ПРАВА ---
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE
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

# --- УВЕЛИЧИВАЕМ ВРЕМЯ СБОРКИ ДЛЯ БОЛЬШОГО ПРОЕКТА ---
# (для GitHub Actions может потребоваться)
android.gradle_repository_threads = 4

# --- ДОПОЛНИТЕЛЬНЫЕ ФАЙЛЫ (если нужно) ---
# android.add_src =

# --- ПОДПИСЬ (для релиза) ---
# android.keystore =
# android.keystore_alias =
# android.keystore_password =

[buildozer]
log_level = 2
warn_on_root = 1

[app]

# --- GITHUB ACTIONS ---
# Для GitHub Actions нужно установить SDK
[gradle]
user_repos = https://google.com/