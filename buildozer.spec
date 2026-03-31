[app]

# Название приложения (как будет отображаться)
title = GuitarFuns

# Внутреннее имя пакета (только латиница)
package.name = guitarfuns

# Домен + имя пакета (уникальный идентификатор)
package.domain = com.guitarfuns

# Путь к исходникам
source.dir = .

# Расширения файлов для включения
source.include_exts = py,png,jpg,kv,atlas,ttf,txt,json

# Требования (ДОБАВЛЯЕМ openssl и pyopenssl)
requirements = python3,kivy==2.3.0,kivymd==1.1.1,requests==2.31.0,pillow==10.1.0,plyer==2.1.1,urllib3==2.1.0,certifi,idna,chardet,openssl,pyopenssl

# Версия приложения
version = 1.0.0

# Ориентация
orientation = portrait

# Разрешения Android
android.permissions = INTERNET, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE

# Иконка (если есть)
# icon.filename = %(source.dir)s/icon.png

# Заставка (если есть)
# presplash.filename = %(source.dir)s/splash.png

# API уровни
android.api = 33
android.minapi = 21

# ВАЖНО: включаем AndroidX
android.enable_androidx = True

# ВАЖНО: разрешаем сетевые запросы
android.add_network_security_config = True

# ДОБАВЛЯЕМ: включаем поддержку HTTPS и SSL
android.gradle_dependencies = 'com.android.support:support-annotations:28.0.0'
android.ndk = 25b

# ДОБАВЛЯЕМ: дополнительные аргументы для сборки
android.archs = arm64-v8a, armeabi-v7a

# Автоматически принимать лицензии
android.accept_sdk_license = True

# Логгирование
log_level = 2

# Полноэкранный режим
fullscreen = 0