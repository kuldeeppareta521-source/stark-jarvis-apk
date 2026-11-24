[app]
title = J.A.R.V.I.S.
package.name = jarvisstark
package.domain = org.kuldeep.stark
source.dir = .
source.include_exts = py,png,jpg,kv,json
version = 1.0
requirements = python3,kivy==2.3.0,pyjnius
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,RECORD_AUDIO
android.api = 33
android.minapi = 21
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1