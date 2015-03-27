from PyQt5 import Qt

WOW_FOLDER_KEY = "Preferences/wowfolder"
WOW_FOLDER_DEFAULT = "%s/.wine/drive_c/Program Files (x86)/World of Warcraft" % (Qt.QDir.homePath())

LCURSE_FOLDER = "%s/.lcurse" % (Qt.QDir.homePath())
LCURSE_ADDONS = LCURSE_FOLDER + "/addons.json"
LCURSE_ADDON_CATALOG = LCURSE_FOLDER + "/addon-catalog.json"

LCURSE_MAXTHREADS_KEY = "Preferences/maxthreads"
LCURSE_MAXTHREADS_DEFAULT = 50
