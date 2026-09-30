[app]
title = YT Downloader
package.name = ytdownloader
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1

# Python is pinned: plain "python3" pulls 3.14, which Kivy doesn't support yet
requirements = python3==3.11.5,hostpython3==3.11.5,kivy==2.3.1,yt-dlp,certifi,openssl,pyjnius,android

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True
android.allow_backup = True

[buildozer]
log_level = 1
warn_on_root = 1
