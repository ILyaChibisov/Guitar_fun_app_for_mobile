# buildozer.spec

[app]

# --- ОСНОВНЫЕ НАСТРОЙКИ ---
title = GuitarFuns
package.name = guitarfuns
package.domain = com.guitarfuns
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,otf,txt,json,xml
source.include_patterns = chords/**, data/**, android_res/**, fonts/**, **/*.py
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

# --- СТАБИЛЬНЫЕ ВЕРСИИ GRADLE И AGP ---
# Фиксируем, чтобы GitHub Actions не тянул нестабильные зависимости
android.gradle_plugin_version = 8.2.2
android.gradle_version = 8.2.2
android.gradle_repository_threads = 4

# --- NETWORK SECURITY CONFIG ---
# Манифест мы правим скриптом в build.yml, тут ничего не указываем

# --- АРХИТЕКТУРА ---
android.archs = arm64-v8a

# --- ОТЛАДКА ---
fullscreen = 0
log_level = 2

# --- ПОДПИСЬ ---
android.keystore = guitarfuns_keystore.jks
android.keystore_alias = guitarfuns
android.keystore_key_password = lexx311285
# Пароль самого хранилища (добавлено, чтобы не было рассинхрона)
android.keystore_store_password = lexx311285

[buildozer]
log_level = 2
warn_on_root = 1