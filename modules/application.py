#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import os
import re
from shutil import rmtree
import urllib
from urllib.parse import urlparse
from urllib.request import build_opener, HTTPCookieProcessor, HTTPError
from http import cookiejar
from bs4 import BeautifulSoup

from PyQt5 import Qt

import preferences
import addaddondlg
import waitdlg
import defines

opener = build_opener(HTTPCookieProcessor(cookiejar.CookieJar()))
# default User-Agent ('Python-urllib/2.6') will *not* work
opener.addheaders = [('User-Agent', 'Mozilla/5.0'), ]


class MainWidget(Qt.QMainWindow):
    def __init__(self):
        super(MainWidget, self).__init__()
        self.ensureLCurseFolder()
        self.addonsFile = os.path.expanduser(defines.LCURSE_ADDONS)
        self.addWidgets()

        self.addons = []
        self.loadAddons()

        self.availableAddons = []
        self.loadAddonCatalog()

    def addWidgets(self):
        self.mainWidget = Qt.QWidget(self)
        box = Qt.QVBoxLayout(self.mainWidget)

        menubar = self.menuBar()

        actionLoad = Qt.QAction(self.tr("Load Addons"), self)
        actionLoad.setShortcut("Ctrl+L")
        actionLoad.setStatusTip(self.tr("Re/Load your addons configuration"))
        actionLoad.triggered.connect(self.loadAddons)

        actionSave = Qt.QAction(self.tr("Save Addons"), self)
        actionSave.setShortcut("Ctrl+S")
        actionSave.setStatusTip(self.tr("Save your addons configuration"))
        actionSave.triggered.connect(self.saveAddons)

        actionImport = Qt.QAction(self.tr("Import Addons"), self)
        actionImport.setStatusTip(self.tr("Import Addons from WoW installation"))
        actionImport.triggered.connect(self.importAddons)

        actionPrefs = Qt.QAction(self.tr("Preferences"), self)
        actionPrefs.setShortcut("Ctrl+P")
        actionPrefs.setStatusTip(self.tr("Change preferences like wow install folder"))
        actionPrefs.triggered.connect(self.openPreferences)

        actionExit = Qt.QAction(self.tr("Exit"), self)
        actionExit.setShortcuts(Qt.QKeySequence.Quit)
        actionExit.setStatusTip(self.tr("Exit application"))
        actionExit.triggered.connect(self.close)

        menuFile = menubar.addMenu(self.tr("General"))
        menuFile.addAction(actionLoad)
        menuFile.addAction(actionSave)
        menuFile.addAction(actionImport)
        menuFile.addSeparator()
        menuFile.addAction(actionPrefs)
        menuFile.addSeparator()
        menuFile.addAction(actionExit)
        self.addAction(actionLoad)
        self.addAction(actionSave)
        self.addAction(actionPrefs)
        self.addAction(actionExit)

        actionCheckAll = Qt.QAction(self.tr("Check all addons"), self)
        actionCheckAll.setShortcut('Ctrl+Shift+A')
        actionCheckAll.setStatusTip(self.tr("Check all addons for new version"))
        actionCheckAll.triggered.connect(self.checkAddonsForUpdate)

        actionCheck = Qt.QAction(self.tr("Check addon"), self)
        actionCheck.setShortcut('Ctrl+A')
        actionCheck.setStatusTip(self.tr("Check currently selected addon for new version"))
        actionCheck.triggered.connect(self.checkAddonForUpdate)

        actionUpdateAll = Qt.QAction(self.tr("Update all addons"), self)
        actionUpdateAll.setShortcut("Ctrl+Shift+U")
        actionUpdateAll.setStatusTip(self.tr("Update all addons which need an update"))
        actionUpdateAll.triggered.connect(self.updateAddons)

        actionUpdate = Qt.QAction(self.tr("Update addon"), self)
        actionUpdate.setShortcut("Ctrl+U")
        actionUpdate.setStatusTip(self.tr("Update currently selected addons if needed"))
        actionUpdate.triggered.connect(self.updateAddon)

        actionAdd = Qt.QAction(self.tr("Add addon"), self)
        actionAdd.setStatusTip(self.tr("Add a new addon"))
        actionAdd.triggered.connect(self.addAddon)

        actionRemove = Qt.QAction(self.tr("Remove addon"), self)
        actionRemove.setStatusTip(self.tr("Remove currently selected addon"))
        actionRemove.triggered.connect(self.removeAddon)

        actionForceUpdate = Qt.QAction(self.tr("Force update addon"), self)
        actionForceUpdate.setShortcut("Ctrl+F")
        actionForceUpdate.setStatusTip(self.tr("Force update of currently selected addon"))
        actionForceUpdate.triggered.connect(self.forceUpdateAddon)

        menuAddons = menubar.addMenu(self.tr("Addons"))
        menuAddons.addAction(actionCheckAll)
        menuAddons.addAction(actionCheck)
        menuAddons.addSeparator()
        menuAddons.addAction(actionUpdateAll)
        menuAddons.addAction(actionUpdate)
        menuAddons.addSeparator()
        menuAddons.addAction(actionAdd)
        menuAddons.addAction(actionRemove)
        menuAddons.addAction(actionForceUpdate)
        toolbar = self.addToolBar(self.tr("Addons"))
        toolbar.addAction(actionUpdateAll)
        toolbar.addAction(actionAdd)
        self.addAction(actionCheckAll)
        self.addAction(actionCheck)
        self.addAction(actionUpdateAll)
        self.addAction(actionUpdate)
        self.addAction(actionForceUpdate)

        actionCatalogUpdate = Qt.QAction(self.tr("Update Catalog"), self)
        actionCatalogUpdate.setStatusTip(self.tr("Retrieve a list of available addons"))
        actionCatalogUpdate.triggered.connect(self.updateCatalog)
        menuCatalog = menubar.addMenu(self.tr("Catalog"))
        menuCatalog.addAction(actionCatalogUpdate)
        toolbar = self.addToolBar(self.tr("Catalog"))
        toolbar.addAction(actionCatalogUpdate)

        self.addonList = Qt.QTableWidget(self.mainWidget)
        self.addonList.setColumnCount(4)
        self.addonList.setHorizontalHeaderLabels(["Name", "Url", "Version", "Allow Beta"])

        self.resize(1030, 815)
        screen = Qt.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2, (screen.height() - size.height()) / 4)
        self.setWindowTitle('WoW!Curse')

        box.addWidget(self.addonList)
        self.statusBar().showMessage(self.tr("Ready"))
        self.setCentralWidget(self.mainWidget)
        self.show()

    #	def resizeEvent(self, event):
    #		print(self.geometry())

    def ensureLCurseFolder(self):
        if not os.path.exists(defines.LCURSE_FOLDER):
            os.mkdir(defines.LCURSE_FOLDER)
        elif not os.path.isdir(defines.LCURSE_FOLDER):
            e = self.tr(
                "There is an entry \".lcurse\" in your home directory which is neither a folder nor a link to a folder."
                " Exiting!")
            Qt.QMessageBox.critical(None, self.tr("lcurse-folder not a folder"), e)
            print(e)
            raise

    def sizeHint(self):
        width = self.addonList.sizeHintForColumn(0) + self.addonList.sizeHintForColumn(
            1) + self.addonList.sizeHintForColumn(2) + self.addonList.sizeHintForColumn(3) + 120
        size = Qt.QSize(width, 815)
        return size

    def adjustSize(self):
        self.resize(self.sizeHint())

    def removeStupidStuff(self, s):
        s = re.sub(r"\|r", "", s)
        s = re.sub(r"\|c.{8}", "", s)
        s = re.sub(r"\[|\]", "", s)
        return s

    def extractAddonMetadataFromTOC(self, toc):
        (name, uri, version, curseId) = ("", "", "", "")
        title_re = re.compile(r"^## Title: (.*)$")
        curse_title_re = re.compile(r"^## X-Curse-Project-Name: (.*)$")
        curse_version_re = re.compile(r"^## X-Curse-Packaged-Version: (.*)$")
        version_re = re.compile(r"^## Version: (.*)$")
        curse_re = re.compile(r"^## X-Curse-Project-ID: (.*)$")
        with open(toc) as f:
            line = f.readline()
            while line != "":
                line = line.strip()
                m = curse_title_re.match(line)
                if m != None:
                    name = m.group(1)
                    line = f.readline()
                    continue
                if name == "":
                    m = title_re.match(line)
                    if m != None:
                        name = m.group(1)
                        line = f.readline()
                        continue
                m = curse_version_re.match(line)
                if m != None:
                    version = m.group(1)
                    line = f.readline()
                    continue
                if version == "":
                    m = version_re.match(line)
                    if m != None:
                        version = m.group(1)
                        line = f.readline()
                        continue
                m = curse_re.match(line)
                if m != None:
                    curseId = m.group(1)
                    line = f.readline()
                    continue
                line = f.readline()

        name = self.removeStupidStuff(name)
        curseId = self.removeStupidStuff(curseId)

        uri = "http://mods.curse.com/addons/wow/{}".format(name.lower().replace(" ", "-"))
        if curseId != "":
            uri = "http://mods.curse.com/addons/wow/{}".format(curseId)

        if name == "" or version == "":
            print("not enough informations found for addon in toc: {}".format(toc))
            return ["", "", ""]

        return [name, uri, version]

    def importAddons(self):
        settings = Qt.QSettings()
        parent = "{}/Interface/AddOns".format(str(settings.value(defines.WOW_FOLDER_KEY, defines.WOW_FOLDER_DEFAULT)))
        contents = os.listdir(parent)
        for item in contents:
            itemDir = "{}/{}".format(parent, item)
            if os.path.isdir(itemDir) and not item.lower().startswith("blizzard_"):
                for files in os.listdir(itemDir):
                    toc = "{}/{}.toc".format(itemDir, item)
                    if files.find(".toc") != -1:
                        toc = "{}/{}".format(itemDir, files)
                if os.path.exists(toc):
                    tmp = self.extractAddonMetadataFromTOC(toc)
                    if tmp[0] == "":
                        continue
                    (name, uri, version) = tmp
                    row = self.addonList.rowCount()
                    if len(self.addonList.findItems(name, Qt.Qt.MatchExactly)) == 0:
                        self.addonList.setRowCount(row + 1)
                        self.insertAddon(row, name, uri, version, False)
        self.addonList.resizeColumnsToContents()
        self.saveAddons()

    def openPreferences(self):
        pref = preferences.PreferencesDlg(self)
        pref.exec_()

    def insertAddon(self, row, name, uri, version, allowBeta):
        self.addonList.setItem(row, 0, Qt.QTableWidgetItem(name))
        self.addonList.setItem(row, 1, Qt.QTableWidgetItem(uri))
        self.addonList.setItem(row, 2, Qt.QTableWidgetItem(version))
        allowBetaItem = Qt.QTableWidgetItem()
        allowBetaItem.setCheckState(Qt.Qt.Checked if allowBeta else Qt.Qt.Unchecked)
        self.addonList.setItem(row, 3, allowBetaItem)

    def loadAddonCatalog(self):
        if os.path.exists(defines.LCURSE_ADDON_CATALOG):
            with open(defines.LCURSE_ADDON_CATALOG) as c:
                self.availableAddons = json.load(c)

    def loadAddons(self):
        self.addonList.clearContents()
        addons = None
        if os.path.exists(self.addonsFile):
            with open(self.addonsFile) as f:
                addons = json.load(f)
        if addons != None:
            self.addonList.setRowCount(len(addons))
            for (row, addon) in enumerate(addons):
                self.addonList.setItem(row, 0, Qt.QTableWidgetItem(addon["name"]))
                self.addonList.setItem(row, 1, Qt.QTableWidgetItem(addon["uri"]))
                self.addonList.setItem(row, 2, Qt.QTableWidgetItem(addon["version"]))
                allowBeta = False
                if "allowbeta" in addon:
                    allowBeta = addon["allowbeta"]
                allowBetaItem = Qt.QTableWidgetItem()
                allowBetaItem.setCheckState(Qt.Qt.Checked if allowBeta else Qt.Qt.Unchecked)
                self.addonList.setItem(row, 3, allowBetaItem)
            self.addonList.resizeColumnsToContents()
            self.adjustSize()

    def saveAddons(self):
        addons = []
        self.addonList.sortItems(0)
        for row in iter(range(self.addonList.rowCount())):
            addons.append(dict(
                name=str(self.addonList.item(row, 0).text()),
                uri=str(self.addonList.item(row, 1).text()),
                version=str(self.addonList.item(row, 2).text()),
                allowbeta=bool(self.addonList.item(row, 3).checkState() == Qt.Qt.Checked)
            ))

        with open(self.addonsFile, "w") as f:
            json.dump(addons, f)

    def addAddon(self):
        addAddonDlg = addaddondlg.AddAddonDlg(self, self.availableAddons)
        result = addAddonDlg.exec_()
        if result == Qt.QDialog.Accepted:
            name = ""
            nameOrUrl = addAddonDlg.getText()
            pieces = urlparse(nameOrUrl)
            if pieces.scheme != "" or pieces.netloc != "":
                url = str(nameOrUrl)
                if "curse.com" in url:
                    try:
                        print("retrieving addon informations")
                        response = opener.open(urlparse(quote(url, ':/')).geturl())
                        soup = BeautifulSoup(response.read())
                        captions = soup.select(".caption span span span")
                        name = captions[0].string
                    except HTTPError as e:
                        print(e)
                elif url.endswith(".git"):
                    name = os.path.basename(url)[:-4]
            else:
                name = nameOrUrl
                try:
                    for item in self.availableAddons:
                        if item[0] == name:
                            url = item[1]
                except IndexError:
                    print("can't handle: " + name)
                    name = ""

            if name != "":
                newrow = self.addonList.rowCount()
                self.addonList.insertRow(newrow)
                self.addonList.setItem(newrow, 0, Qt.QTableWidgetItem(name))
                self.addonList.setItem(newrow, 1, Qt.QTableWidgetItem(url))
                self.addonList.setItem(newrow, 2, Qt.QTableWidgetItem(""))
                allowBetaItem = Qt.QTableWidgetItem()
                allowBetaItem.setCheckState(Qt.Qt.Unchecked)
                self.addonList.setItem(newrow, 3, allowBetaItem)

    def removeAddon(self):
        row = self.addonList.currentRow()
        print("Current Row: {0:d}".format(row))
        answer = Qt.QMessageBox.question(self, self.tr("Remove selected addon"),
                                         str(self.tr("Do you really want to remove the following addon?\n{}")).format(
                                             str(self.addonList.item(row, 0).text())),
                                         Qt.QMessageBox.Yes, Qt.QMessageBox.No)
        if answer == Qt.QMessageBox.Yes:
            settings = Qt.QSettings()
            parent = "{}/Interface/AddOns".format(str(settings.value(defines.WOW_FOLDER_KEY, defines.WOW_FOLDER_DEFAULT)))
            contents = os.listdir(parent)
            addonName =  str(self.addonList.item(row, 0).text())
            deleted = False
            deleted_addons = []
            potential_deletions = []
            for item in contents:
                itemDir = "{}/{}".format(parent, item)
                if os.path.isdir(itemDir) and not item.lower().startswith("blizzard_"):
                    for files in os.listdir(itemDir):
                        toc = "{}/{}.toc".format(itemDir, item)
                        if files.find(".toc") != -1:
                            toc = "{}/{}".format(itemDir, files)
                        if os.path.exists(toc):
                            tmp = self.extractAddonMetadataFromTOC(toc)
                            if tmp[0] == addonName:
                                rmtree(itemDir)
                                deleted_addons.append(item)
                                deleted = True

            self.addonList.removeRow(row)

            if not deleted:
                Qt.QMessageBox.question(self, "No addons removed",
                                        str(self.tr("No addons matching \"{}\" found.\nThe addon might already be removed, or could be going under a different name.\nManual deletion may be required.")).format(addonName),
                                        Qt.QMessageBox.Ok)
            else:
                potential = False
                for item in contents:
                    itemDir = "{}/{}".format(parent, item)
                    if os.path.isdir(itemDir) and not item.lower().startswith("blizzard_"):
                        for files in os.listdir(itemDir):
                            toc = "{}/{}.toc".format(itemDir, item)
                            if files.find(".toc") != -1:
                                toc = "{}/{}".format(itemDir, files)
                        if os.path.exists(toc):
                            tmp = self.extractAddonMetadataFromTOC(toc)
                        for d in deleted_addons:
                            deletions = list(filter(None, re.split("[_, \-!?:]+", d)))
                            for word in deletions:
                                if re.search(word, tmp[0]) != None:
                                    potential_deletions.append(item)
                                    potential = True
                                    break
                            if potential:
                                break
                if potential:
                    to_delete = '\n'.join(potential_deletions)
                    removal = Qt.QMessageBox.question(self, "Potential deletion candidates found",
                                            str(self.tr("Remove the following addons as well?\n{}")).format(to_delete),
                                            Qt.QMessageBox.Yes, Qt.QMessageBox.No)    
                    if removal == Qt.QMessageBox.Yes:
                        for p in potential_deletions:
                            all_rows = self.addonList.rowCount()
                            for n in range(0, all_rows):
                                name = str(self.addonList.item(n, 0).text())
                                if p == name:
                                    self.addonList.removeRow(n)
                                    break
                            rmtree("{}/{}".format(parent, p))

            self.saveAddons()

    def setRowColor(self, row, color):
        self.addonList.item(row, 0).setBackground(color)
        self.addonList.item(row, 1).setBackground(color)
        self.addonList.item(row, 2).setBackground(color)

    def onCheckFinished(self, addon, result, data):
        if result:
            self.setRowColor(addon[0], Qt.Qt.yellow)
            self.addonList.item(addon[0], 0).setData(Qt.Qt.UserRole, data)
        elif data == None:
            self.setRowColor(addon[0], Qt.Qt.red)
        else:
            self.setRowColor(addon[0], Qt.Qt.white)

    def checkAddonForUpdate(self):
        row = self.addonList.currentRow()
        addons = []
        name = self.addonList.item(row, 0).text()
        uri = self.addonList.item(row, 1).text()
        version = self.addonList.item(row, 2).text()
        allowBeta = bool(self.addonList.item(row, 3).checkState() == Qt.Qt.Checked)
        addons.append((row, name, uri, version, allowBeta))

        checkDlg = waitdlg.CheckDlg(self, addons)
        checkDlg.checkFinished.connect(self.onCheckFinished)
        checkDlg.exec_()

    def checkAddonsForUpdate(self):
        addons = []
        for row in iter(range(self.addonList.rowCount())):
            name = self.addonList.item(row, 0).text()
            uri = self.addonList.item(row, 1).text()
            version = self.addonList.item(row, 2).text()
            allowBeta = bool(self.addonList.item(row, 3).checkState() == Qt.Qt.Checked)
            addons.append((row, name, uri, version, allowBeta))

        checkDlg = waitdlg.CheckDlg(self, addons)
        checkDlg.checkFinished.connect(self.onCheckFinished)
        checkDlg.exec_()

    def onUpdateFinished(self, addon, result):
        if result:
            data = self.addonList.item(addon[0], 0).data(Qt.Qt.UserRole)
            self.addonList.item(addon[0], 2).setText(data[0])
            self.addonList.item(addon[0], 0).setData(Qt.Qt.UserRole, None)
            self.setRowColor(addon[0], Qt.Qt.green)

    def forceUpdateAddon(self):
        row = self.addonList.currentRow()
        print("enforcing update of {:s}".format(self.addonList.item(row, 0).text()))
        self.addonList.item(row, 2).setText("")
        self.updateAddon()

    def updateAddon(self):
        row = self.addonList.currentRow()
        addons = []
        data = self.addonList.item(row, 0).data(Qt.Qt.UserRole)
        if data == None:
            self.checkAddonForUpdate()

        data = self.addonList.item(row, 0).data(Qt.Qt.UserRole)
        if data == None:
            return

        name = self.addonList.item(row, 0).text()
        uri = self.addonList.item(row, 1).text()
        version = self.addonList.item(row, 2).text()
        allowBeta = bool(self.addonList.item(row, 3).checkState() == Qt.Qt.Checked)
        addons.append((row, name, uri, version, allowBeta, data))

        if len(addons):
            updateDlg = waitdlg.UpdateDlg(self, addons)
            updateDlg.updateFinished.connect(self.onUpdateFinished)
            updateDlg.exec_()
            self.saveAddons()

    def updateAddons(self):
        self.checkAddonsForUpdate()
        addons = []
        for row in iter(range(self.addonList.rowCount())):
            data = self.addonList.item(row, 0).data(Qt.Qt.UserRole)
            if data:
                name = self.addonList.item(row, 0).text()
                uri = self.addonList.item(row, 1).text()
                version = self.addonList.item(row, 2).text()
                allowBeta = bool(self.addonList.item(row, 3).checkState() == Qt.Qt.Checked)
                addons.append((row, name, uri, version, allowBeta, data))

        if len(addons):
            updateDlg = waitdlg.UpdateDlg(self, addons)
            updateDlg.updateFinished.connect(self.onUpdateFinished)
            updateDlg.exec_()
            self.saveAddons()

    def onUpdateCatalogFinished(self, addons):
        print("retrieved list of addons: {}".format(len(addons)))
        self.availableAddons = addons
        with open(defines.LCURSE_ADDON_CATALOG, "w") as c:
            json.dump(self.availableAddons, c)

    def updateCatalog(self):
        updateCatalogDlg = waitdlg.UpdateCatalogDlg(self)
        updateCatalogDlg.updateCatalogFinished.connect(self.onUpdateCatalogFinished)
        updateCatalogDlg.exec_()

    def start(self):
        return self.exec_()


if __name__ == "__main__":
    sys.exit(42)
