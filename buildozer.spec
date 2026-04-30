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

# Требования - убираем прямую ссылку, используем kivymd из GitHub через pip
requirements = python3,kivy==2.3.1,kivymd==2.0.1.dev0,requests,pillow,plyer,openssl,pyopenssl

# Версия приложения
version = 1.0.0

# Ориентация
orientation = portrait

# Разрешения Android
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE

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

# Использовать свежую версию python-for-android
p4a.branch = master

# Добавляем pypi для поиска kivymd 2.0.1.dev0
p4a.allow_pypi_dependencies = True
