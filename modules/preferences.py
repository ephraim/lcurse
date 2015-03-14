from PyQt4 import Qt
import defines

class PreferencesDlg(Qt.QDialog):
	def __init__(self, parent):
		super(PreferencesDlg, self).__init__(parent)

		layout = Qt.QVBoxLayout(self)

		layout.addWidget(Qt.QLabel(self.tr("WoW Install Folder:"), self))
		folderlayout = Qt.QHBoxLayout()
		self.wowInstallFolder = Qt.QLineEdit(self.getWowFolder(), self)
		folderlayout.addWidget(self.wowInstallFolder)
		btn = Qt.QPushButton(self.tr("..."), self)
		btn.clicked.connect(self.browseForWoWFolder)
		folderlayout.addWidget(btn)
		layout.addLayout(folderlayout)

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
								self.tr("Select Wow Install Folder"), self.wowInstallFolder.text(),
								Qt.QFileDialog.ShowDirsOnly | Qt.QFileDialog.DontResolveSymlinks);

		if selectedDir != "":
			dir = Qt.QDir("%s/Interface/AddOns" % (selectedDir))
			if dir.exists():
				self.wowInstallFolder.setText(dir)
			else:
				Qt.QMessageBox.warning(self, self.tr("Not Wow-Folder"), self.tr("The selected folder wasn't an installation directory of wow.\nPlease select the wow folder"))

	def getWowFolder(self):
		settings = Qt.QSettings()
		return settings.value(defines.WOW_FOLDER_KEY, defines.WOW_FOLDER_DEFAULT).toString()

	def setWowFolder(self, newfolder):
		settings = Qt.QSettings()
		return settings.setValue(defines.WOW_FOLDER_KEY, newfolder)

	def accept(self):
		self.setWowFolder(self.wowInstallFolder.text())
		super(PreferencesDlg, self).accept()
