from PyQt5 import Qt
from modules import defines


class PreferencesDlg(Qt.QDialog):
    def __init__(self, parent):
        super(PreferencesDlg, self).__init__(parent)
        self.settings = Qt.QSettings()

        print(defines)

        layout = Qt.QVBoxLayout(self)

        layout.addWidget(Qt.QLabel(self.tr("WoW Install Folder:"), self))
        folderlayout = Qt.QHBoxLayout()
        self.wowInstallFolder = Qt.QLineEdit(self.getWowFolder(), self)
        folderlayout.addWidget(self.wowInstallFolder)
        btn = Qt.QPushButton(self.tr("..."), self)
        btn.clicked.connect(self.browseForWoWFolder)
        folderlayout.addWidget(btn)
        layout.addLayout(folderlayout)

        layout.addWidget(Qt.QLabel(self.tr("Max. concurrent Threads:"), self))
        self.maxthreads = Qt.QSpinBox(self)
        self.maxthreads.setMinimum(1)
        self.maxthreads.setMaximum(1000)
        self.maxthreads.setValue(self.getMaxThreads())
        layout.addWidget(self.maxthreads)

        layout.addWidget(Qt.QLabel(self.tr("Current Toc Number:"), self))
        self.currenttoc = Qt.QLineEdit(str(self.getTocVersion()),self)
        layout.addWidget(self.currenttoc)

        bottom = Qt.QHBoxLayout()
        bottom.addSpacing(100)
        btn = Qt.QPushButton(self.tr("Save"), self)
        btn.clicked.connect(self.accept)
        btn.setDefault(True)
        bottom.addWidget(btn)
        btn = Qt.QPushButton(self.tr("Cancel"), self)
        btn.clicked.connect(self.reject)
        bottom.addWidget(btn)
        layout.addSpacing(100)
        layout.addLayout(bottom)
        self.setLayout(layout)

    def browseForWoWFolder(self):
        selectedDir = Qt.QFileDialog.getExistingDirectory(self,
                                                          self.tr("Select Wow Install Folder"),
                                                          self.wowInstallFolder.text(),
                                                          Qt.QFileDialog.ShowDirsOnly |
                                                          Qt.QFileDialog.DontResolveSymlinks)

        if selectedDir:
            directory = Qt.QDir("{}/Interface/AddOns".format(selectedDir))
            if directory.exists():
                self.wowInstallFolder.setText(selectedDir)
            else:
                Qt.QMessageBox.warning(self, self.tr("Not Wow-Folder"), self.tr(
                    "The selected folder wasn't an installation directory of wow.\nPlease select the wow folder"))

    def getMaxThreads(self):
        return int(self.settings.value(defines.LCURSE_MAXTHREADS_KEY, defines.LCURSE_MAXTHREADS_DEFAULT))

    def setMaxThreads(self, newMaxThreads):
        return self.settings.setValue(defines.LCURSE_MAXTHREADS_KEY, int(newMaxThreads))

    def getWowFolder(self):
        return self.settings.value(defines.WOW_FOLDER_KEY, defines.WOW_FOLDER_DEFAULT)

    def setWowFolder(self, newfolder):
        return self.settings.setValue(defines.WOW_FOLDER_KEY, newfolder)

    def getTocVersion(self):
        return self.settings.value(defines.WOW_TOC_KEY,70200)
    
    def setTocVersion(self,newtoc):
        return self.settings.setValue(defines.WOW_TOC_KEY,int(newtoc))
    
    def accept(self):
        self.setWowFolder(self.wowInstallFolder.text())
        self.setMaxThreads(self.maxthreads.value())
        self.setTocVersion(self.currenttoc.text())
        super(PreferencesDlg, self).accept()
