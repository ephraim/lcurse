import os
import sys
import json
from PyQt5 import Qt

rootDir = os.path.dirname(os.path.realpath(__file__))
modulesDir = "{}/modules".format(rootDir)
appTranslationFile = "{}/translations/{}.qm".format(rootDir, Qt.QLocale.system().name())

sys.path.insert(0, modulesDir)

from modules import waitdlg, defines
from _thread import start_new_thread

def loadAddons(addonsFile):
    addons = None
    if os.path.exists(addonsFile):
        with open(addonsFile) as f:
            addons = json.load(f)
    return addons

def saveAddons(addonsFile, addons):
    with open(addonsFile, "w") as f:
        json.dump(addons, f)

class CheckConsole(Qt.QApplication):
    def __init__(self, argv, addons):
        super(Qt.QApplication, self).__init__(argv)
        settings = Qt.QSettings()
        self.maxThreads = int(settings.value(defines.LCURSE_MAXTHREADS_KEY, defines.LCURSE_MAXTHREADS_DEFAULT))
        self.sem = Qt.QSemaphore(self.maxThreads)
        self.addons = addons

    @Qt.pyqtSlot(Qt.QVariant, bool)
    def onUpdateFinished(self, addon, result):
        self.sem.release()
        self.threadsCount -= 1
        print("Addon '{}' updated: {}".format(addon[1], result and "successfully" or "failed"))
        if result:
            # addon[0] == idx, addon[5] == data from check, addon[5][0] new version
            self.addons[addon[0]]["version"] = addon[5][0] # replace old version with new version in addon
        if self.threadsCount <= 0:
            saveAddons(os.path.expanduser(defines.LCURSE_ADDONS), self.addons)
            self.quit()

    @Qt.pyqtSlot(Qt.QVariant, bool, Qt.QVariant)
    def onCheckFinished(self, addon, needsUpdate, updateData):
        self.sem.release()
        if not needsUpdate:
            print("Addon '{}' is up to date.".format(addon[1]))
            self.threadsCount -= 1
        else:
            self.sem.acquire()
            print("Addon '{}' needs update. New Version: {}".format(addon[1], updateData[0]))
            addon.append(updateData)
            thread = waitdlg.UpdateWorker(addon)
            thread.updateFinished.connect(self.onUpdateFinished)
            thread.start()
            self.threads.append(thread)

        if self.threadsCount <= 0:
            saveAddons(os.path.expanduser(defines.LCURSE_ADDONS), self.addons)
            self.quit()

    def startWorkerThreads(self):
        self.threads = []
        self.threadsCount = len(self.addons)
        i = 0
        for i in range(len(self.addons)):
            addon = self.addons[i]
            self.sem.acquire()
            thread = waitdlg.CheckWorker([i, addon["name"], addon["uri"], addon["version"], addon["allowbeta"]])
            thread.checkFinished.connect(self.onCheckFinished)
            thread.start()
            self.threads.append(thread)

    def exec_(self):
        print("checking all addons. please wait ...")
        start_new_thread(self.startWorkerThreads, ())
        return super(Qt.QApplication, self).exec_()

Qt.QCoreApplication.setApplicationName("lcurse")
Qt.QCoreApplication.setOrganizationName("None-Inc.")

check = CheckConsole(sys.argv, loadAddons(os.path.expanduser(defines.LCURSE_ADDONS)))
ret = check.exec_()
print("Done. Bye Bye!")
sys.exit(ret)
