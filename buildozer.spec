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

# Требования (ОЧЕНЬ ВАЖНО!)
requirements = python3,kivy,kivymd,requests,pillow,plyer,urllib3

# Версия приложения
version = 1.0.0

# Ориентация
orientation = portrait

# Разрешения Android
android.permissions = INTERNET, ACCESS_NETWORK_STATE

# Иконка (если есть)
# icon.filename = %(source.dir)s/icon.png

# Заставка (если есть)
# presplash.filename = %(source.dir)s/splash.png

# API уровни
android.api = 33
android.minapi = 21
android.ndk = 23b
android.sdk = 33

# Автоматически принимать лицензии
android.accept_sdk_license = True

# Логгирование
log_level = 2

# Полноэкранный режим
fullscreen = 0