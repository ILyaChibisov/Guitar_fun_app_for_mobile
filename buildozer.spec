[app]
title = GuitarFuns
package.name = guitarfuns
package.domain = com.guitarfuns
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,txt,json
version = 1.0.0
orientation = portrait

# Все зависимости для стабильной работы
requirements = python3,kivy==2.3.1,kivymd==1.2.0,requests,pillow,plyer,openssl,pyopenssl,cython==3.0.11

# Разрешения для Android 13
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE
# Целевой API 33 (Android 13)
android.api = 33
# Минимальная версия Android 5 (Lollipop)
android.minapi = 21
android.enable_androidx = True
android.add_network_security_config = True

# КЛЮЧЕВОЙ ПАРАМЕТР: Сборка ТОЛЬКО под ARM!
android.archs = arm64-v8a, armeabi-v7a

android.accept_sdk_license = True

fullscreen = 0
log_level = 2

# КЛЮЧЕВОЙ ПАРАМЕТР: Используем develop-ветку python-for-android!
# Она исправляет критическую ошибку с архитектурами
p4a.branch = develop
