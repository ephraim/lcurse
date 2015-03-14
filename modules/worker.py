from PyQt4 import Qt


class UpdateAddon(QtCore.QThread):
    taskFinished = QtCore.pyqtSignal()
    def run(self):
        self.taskFinished.emit() 

class CheckAddon(QtCore.QThread):
    taskFinished = QtCore.pyqtSignal()
    def run(self):
        self.taskFinished.emit() 
