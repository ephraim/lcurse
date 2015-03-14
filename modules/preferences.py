from PyQt4 import Qt


class PreferencesDlg(Qt.QDialog):
	def __init__(self, parent):
		super(PreferencesDlg, self).__init__(parent)
		settings = Qt.QSettings()

		layout = Qt.QVBoxLayout(self)
		layout.addWidget(Qt.QLabel("WoW Install Folder:", self))

		self.wowInstallFolder = Qt.QLineEdit(settings.value("Preferences/wowfolder", "~/.wine/drive_c/Program Files (x86)/World of Warcraft").toString(), self)
		layout.addWidget(self.wowInstallFolder)
		bottom = Qt.QHBoxLayout()
		bottom.addSpacing(100)
		btn = Qt.QPushButton("Save", self)
		btn.clicked.connect(self.accept)
		btn.setDefault(True)
		bottom.addWidget(btn)
		btn = Qt.QPushButton("Cancel", self)
		btn.clicked.connect(self.reject)
		bottom.addWidget(btn)
		layout.addSpacing(100)
		layout.addLayout(bottom)
		self.setLayout(layout)
