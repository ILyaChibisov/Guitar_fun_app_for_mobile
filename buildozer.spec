[app]

# --- ОСНОВНЫЕ НАСТРОЙКИ ---
title = GuitarFuns
package.name = guitarfuns
package.domain = com.guitarfuns
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,txt,json,wav,mp3,ogg

# Включаем все файлы рекурсивно
source.include_patterns = chords/**, **/*.py, **/*.png, **/*.jpg, **/*.json

# Исключаем ненужные файлы
source.exclude_patterns = **/__pycache__, **/*.pyc, .venv, .git, test_*.py, check_*.py, **/.DS_Store, **/buildozer.spec

version = 1.0.2
version.code = 2
orientation = portrait

# --- ЗАВИСИМОСТИ (МИНИМАЛЬНЫЕ) ---
requirements = python3,kivy==2.3.1,kivymd==1.2.0,requests,pillow,plyer,pyjnius

# --- ПРАВА ---
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE
android.api = 33
android.minapi = 24
android.enable_androidx = True
android.add_network_security_config = True
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True

# --- НАСТРОЙКИ СБОРКИ ---
fullscreen = 0
log_level = 1
p4a.branch = develop
android.gradle_repository_threads = 4
android.ndk = 25b

# --- ОТКЛЮЧАЕМ НЕНУЖНЫЕ РЕЦЕПТЫ (libthorvg не нужен) ---
# p4a.local_recipes = ./recipes
# p4a.whitelist =

# --- ПОДПИСЬ (РАСКОММЕНТИРУЙ ЕСЛИ ЕСТЬ КЛЮЧ) ---
# android.keystore = guitarfuns_keystore.jks
# android.keystore_alias = guitarfuns
# android.keystore_key_password = lexx311285

[buildozer]
log_level = 1
warn_on_root = 1

[gradle]
user_repos = https://google.com/