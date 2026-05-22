[app]
# (str) Title of your application
title = Zombie Survival

# (str) Package name
package.name = zombie_survival

# (str) Package domain (needed for android/ios packaging)
package.domain = org.example

# (str) Source code where the main.py live
source.dir = .
source.include_exts = py,kv,wav,mp3

# (str) Application versioning
version = 1.0

# (list) Application requirements
requirements = python3,kivy

# (str) Supported orientation
orientation = landscape

# (bool) If True, the application will be fullscreen
fullscreen = 1

# (str) Android entry point, default is ok for Kivy
# android.entrypoint = org.kivy.android.PythonActivity

# (list) Permissions
android.permissions = INTERNET

[buildozer]
log_level = 2
warn_on_root = 1
