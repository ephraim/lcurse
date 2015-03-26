from PyQt5 import Qt

WOW_FOLDER_KEY = "Preferences/wowfolder"
WOW_FOLDER_DEFAULT = "%s/.wine/drive_c/Program Files (x86)/World of Warcraft" % (Qt.QDir.homePath())

LCURSE_ADDONS = "%s/.lcurse/addons.json" % (Qt.QDir.homePath())
LCURSE_ADDON_CATALOG = "%s/.lcurse/addon-catalog.json" % (Qt.QDir.homePath())

LCURSE_MAXTHREADS_KEY = "Preferences/maxthreads"
LCURSE_MAXTHREADS_DEFAULT = 50
