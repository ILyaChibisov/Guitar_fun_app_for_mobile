[app]
title = GuitarFuns
package.name = guitarfuns
package.domain = com.guitarfuns
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,txt,json

# ✅ Добавлено: явно включаем все файлы в папке chords
source.include_patterns = chords/**

version = 1.0.0
orientation = portrait

requirements = python3,kivy==2.3.1,kivymd==1.2.0,cython==0.29.33,requests,pillow,plyer,openssl,pyopenssl,asynckivy,asyncgui

android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE
android.api = 33
android.minapi = 24
android.enable_androidx = True
android.add_network_security_config = True
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True

fullscreen = 0
log_level = 2
p4a.branch = develop