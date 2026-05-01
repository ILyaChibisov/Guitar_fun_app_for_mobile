[app]
title = GuitarFuns
package.name = guitarfuns
package.domain = com.guitarfuns
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,txt,json
version = 1.0.0
orientation = portrait

requirements = python3,kivy==2.3.1,https://github.com/kivymd/KivyMD/archive/master.zip,requests,pillow,plyer,openssl,pyopenssl,cython==3.0.11

android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE
android.api = 33
android.minapi = 21
android.enable_androidx = True
android.add_network_security_config = True
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True

fullscreen = 0
log_level = 2

p4a.branch = develop