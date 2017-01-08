from PyQt5 import Qt


class AddAddonDlg(Qt.QDialog):
    def __init__(self, parent, availableAddons):
        super(AddAddonDlg, self).__init__(parent)
        box = Qt.QVBoxLayout(self)
        box.addWidget(Qt.QLabel(self.tr("Type name or url of the addon you want to add:"), self))
        self.input = Qt.QLineEdit(self)
        box.addWidget(self.input)
        btnBox = Qt.QDialogButtonBox(Qt.QDialogButtonBox.Ok | Qt.QDialogButtonBox.Cancel)
        btnBox.accepted.connect(self.accept)
        btnBox.rejected.connect(self.reject)
        box.addWidget(btnBox)
        self.show()
        if availableAddons:
            self.completer = Qt.QCompleter([addon[0] for addon in availableAddons], self)
            self.completer.setFilterMode(Qt.Qt.MatchContains)
            self.completer.setCaseSensitivity(Qt.Qt.CaseInsensitive)
            self.input.setCompleter(self.completer)
        else:
            Qt.QMessageBox.information(self, self.tr("No addon catalog data"), self.tr(
                "You haven't updated the available addons catalog, "
                "so you need to insert a URL for the addon you want to add."))

    def getText(self):
        return self.input.text()
