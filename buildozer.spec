[app]

# Название приложения
title = GuitarFuns

# Внутреннее имя пакета
package.name = guitarfuns

# Домен + имя пакета
package.domain = com.guitarfuns

# Путь к исходникам
source.dir = .

# Расширения файлов для включения
source.include_exts = py,png,jpg,kv,atlas,ttf,txt,json

# Требования
requirements = python3,kivy==2.3.0,kivymd==1.1.1,requests==2.31.0,pillow==10.1.0,plyer==2.1.0,urllib3==2.1.0,certifi,idna,chardet,openssl,pyopenssl

# Версия приложения
version = 1.0.0

# Ориентация
orientation = portrait

# Разрешения Android
android.permissions = INTERNET, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE

# API уровни
android.api = 33
android.minapi = 21

# Включаем AndroidX
android.enable_androidx = True

# Разрешаем сетевые запросы
android.add_network_security_config = True

# NDK версия
android.ndk = 25b

# Архитектуры
android.archs = arm64-v8a, armeabi-v7a

# Автоматически принимать лицензии
android.accept_sdk_license = True

# Логгирование
log_level = 2

# Полноэкранный режим
fullscreen = 0