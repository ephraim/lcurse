#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import os
import re
from shutil import rmtree
import urllib
from urllib.parse import urlparse, quote as urlquote
from urllib.request import build_opener, HTTPCookieProcessor, HTTPError
from http import cookiejar
from bs4 import BeautifulSoup

from PyQt5 import Qt

from modules import preferences
from modules import addaddondlg
from modules import waitdlg
from modules import defines
#from PyQt4.uic.Compiler.qtproxies import QtGui
from PyQt5 import QtGui

opener = build_opener(HTTPCookieProcessor(cookiejar.CookieJar()))
# default User-Agent ('Python-urllib/2.6') will *not* work
opener.addheaders = [('User-Agent', 'Mozilla/5.0'), ]

class Grid(Qt.QTableWidget):
    def __init__(self, parent=None):
        self.parent = parent
        super().__init__(parent.mainWidget)
    
    def contextMenuEvent(self,event):
        self.menu = Qt.QMenu(self)
        row=self.currentRow()
        name=self.item(row,0).text()
        self.menu.addAction(self.tr("Context menu for {}").format(name))
        removefromlistAction = Qt.QAction(self.tr("Remove from list"),self)
        removefromlistAction.setStatusTip(self.tr("Leave all files unaltered, useful for subaddons"))
        removefromlistAction.triggered.connect(self.removeFromList)
        self.menu.addAction(removefromlistAction)
        actionUpdate = Qt.QAction(self.tr("Update addon"), self)
        actionUpdate.setStatusTip(self.tr("Update currently selected addons if needed"))
        actionUpdate.triggered.connect(self.parent.updateAddon)        
        self.menu.addAction(actionUpdate)
        actionForceUpdate = Qt.QAction(self.tr("Force Update addon"), self)
        actionForceUpdate.setStatusTip(self.tr("Unconditionally update currently selected addons"))
        actionForceUpdate.triggered.connect(self.parent.forceUpdateAddon)        
        self.menu.addAction(actionForceUpdate)
        self.menu.popup(Qt.QCursor.pos())

    def removeFromList(self):
        row = self.currentRow()
        self.removeRow(row)
        self.parent.saveAddons()
        
        

class MainWidget(Qt.QMainWindow):
    def __init__(self):
        super(MainWidget, self).__init__()
        self.ensureLCurseFolder()
        self.addonsFile = os.path.expanduser(defines.LCURSE_ADDONS)
        defines.TOC=self.getWowToc()
        self.addWidgets()

        self.addons = []
        self.loadAddons()

        self.availableAddons = []
        self.loadAddonCatalog()
            
    def getWowToc(self):
        settings = Qt.QSettings()
        try:
            buildinfo="{}/.build.info".format(settings.value(defines.WOW_FOLDER_KEY, defines.WOW_FOLDER_DEFAULT))
            print(buildinfo)
            with open(buildinfo, encoding="utf8", errors='replace') as f:
                line = f.readline()
                version=f.readline().split('|')[11]
                f.close()
            v=version.split('.')
            return str(int(v[0])*10000 + int(v[1])*100)
        except Exception as e:
            return settings.value(defines.WOW_TOC_KEY,defines.TOC)
            print("Error messages",e)
                
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

        self.addonList = Grid(self)

        self.addonList.setColumnCount(5)
        self.addonList.setHorizontalHeaderLabels(["Name", "Url", "Version", "Toc", "Allow Beta"])

        self.resize(1070, 815)
        screen = Qt.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2, (screen.height() - size.height()) / 5)
        self.setWindowTitle('WoW!Curse ' + '(TOC: ' + defines.TOC +')')

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
        (name, uri, version, curseId, tocversion) = ("", "", "", "", "")
        title_re = re.compile(r"^## *Title: *(.*)")
        title2_re = re.compile(r"^## *Title.....: *(.*)")
        curse_title_re = re.compile(r"^## *X-Curse-Project-Name: *(.*)")
        curse_version_re = re.compile(r"^## *X-Curse-Packaged-Version: *(.*)")
        version_re = re.compile(r"^## *Version: *(.*)$")
        curse_re = re.compile(r"^## °X-Curse-Project-ID: *(.*)")
        tocversion_re = re.compile(r"^## *Interface: *(\d*)")
        with open(toc, encoding="utf8", errors='replace') as f:
            line = f.readline()
            while line != "":
                line = line.strip()
                m = curse_title_re.match(line)
                if m:
                    name = m.group(1).strip()
                    line = f.readline()
                    continue
                if name == "":
                    m = title_re.match(line)
                    if m:
                        name = m.group(1).strip()
                        line = f.readline()
                        continue
                if name == "":
                    m = title2_re.match(line)
                    if m:
                        name = m.group(1).strip()
                        line = f.readline()
                        continue
                m = curse_version_re.match(line)
                if m:
                    version = m.group(1).strip()
                    line = f.readline()
                    continue
                if version == "":
                    m = version_re.match(line)
                    if m:
                        version = m.group(1).strip()
                        line = f.readline()
                        continue
                m = curse_re.match(line)
                if m:
                    curseId = m.group(1).strip()
                    line = f.readline()
                    continue
                m = tocversion_re.match(line)
                if m:
                    tocversion = m.group(1).strip()
                    line = f.readline()
                    continue
                line = f.readline()
            if not version:
                version="n/a"
            if not name:
                print("not enough informations found for addon  {}\n(version={},name={},toc={})\n".format(toc,version,name,tocversion))
        name = self.removeStupidStuff(name)
        curseId = self.removeStupidStuff(curseId)
        
        uri = "http://mods.curse.com/addons/wow/{}".format(name.lower().replace(" ", "-"))
        if curseId:
            uri = "http://mods.curse.com/addons/wow/{}".format(curseId)
        
            #return ["", "", "", ""]

        return [name, uri, version, tocversion]

    def importAddons(self):
        settings = Qt.QSettings()
        parent = "{}/Interface/AddOns".format(str(settings.value(defines.WOW_FOLDER_KEY, defines.WOW_FOLDER_DEFAULT)))
        contents = os.listdir(parent)
        for item in contents:
            itemDir = "{}/{}".format(parent, item)
            if os.path.isdir(itemDir) and not item.lower().startswith("blizzard_"):
                toc = "{}/{}.toc".format(itemDir, item)
                if os.path.exists(toc):
                    tmp = self.extractAddonMetadataFromTOC(toc)
                    if tmp[0] == "":
                        continue
                    (name, uri, version, tocVersion) = tmp
                    row = self.addonList.rowCount()
                    if not self.addonList.findItems(name, Qt.Qt.MatchExactly):
                        self.addonList.setRowCount(row + 1)
                        self.insertAddon(row, name, uri, version, tocVersion, False)
        self.addonList.resizeColumnsToContents()
        self.saveAddons()

    def openPreferences(self):
        pref = preferences.PreferencesDlg(self)
        pref.exec_()

    def insertAddon(self, row, name, uri, version, tocVersion, allowBeta):
        self.addonList.setItem(row, 0, Qt.QTableWidgetItem(name))
        self.addonList.setItem(row, 1, Qt.QTableWidgetItem(uri))
        self.addonList.setItem(row, 2, Qt.QTableWidgetItem(version))
        self.addonList.setItem(row, 3, Qt.QTableWidgetItem(tocVersion))
        allowBetaItem = Qt.QTableWidgetItem()
        allowBetaItem.setCheckState(Qt.Qt.Checked if allowBeta else Qt.Qt.Unchecked)
        self.addonList.setItem(row, 4, allowBetaItem)

    def loadAddonCatalog(self):
        if os.path.exists(defines.LCURSE_ADDON_CATALOG):
            with open(defines.LCURSE_ADDON_CATALOG) as c:
                self.availableAddons = json.load(c)

    def loadAddons(self):
        self.addonList.clearContents()
        addons = None
        if os.path.exists(self.addonsFile):
            with open(self.addonsFile) as f:
                data = json.load(f)
                try:
                    dbversion = data['dbversion']
                    addons = data['addons']
                except:
                    print("Warning, old database, will convert")
                    dbversion = 0
                    addons = data 
        if not addons:
            return
        self.addonList.setRowCount(len(addons))
        tocs=self.updateDatabaseFormat(dbversion-10)
        for (row, addon) in enumerate(addons):
            self.addonList.setItem(row, 0, Qt.QTableWidgetItem(addon["name"]))
            self.addonList.setItem(row, 1, Qt.QTableWidgetItem(addon["uri"]))
            self.addonList.setItem(row, 2, Qt.QTableWidgetItem(addon["version"]))
            try:
                if addon["toc"] == "":
                    addon["toc"] = "n/a"
                self.addonList.setItem(row, 3, Qt.QTableWidgetItem(addon["toc"]))
                
            except Exception as e:
                addon["toc"] = "n/a"
            if addon["toc"] == "n/a":
                try:
                    self.addonList.setItem(row, 3, Qt.QTableWidgetItem(tocs[addon["name"]]["toc"]))
                except Exception as e:
                    self.addonList.setItem(row, 3, Qt.QTableWidgetItem("n/a"))
            toc=self.addonList.item(row, 3).text()
            if (toc=="n/a"): 
                self.addonList.item(row, 3).setForeground(Qt.Qt.black)
            elif ( toc == defines.TOC):
                self.addonList.item(row, 3).setForeground(Qt.Qt.blue)
            else:
                self.addonList.item(row, 3).setForeground(Qt.Qt.red)                    
            allowBeta = addon.get("allowbeta", False)
            allowBetaItem = Qt.QTableWidgetItem()
            allowBetaItem.setCheckState(Qt.Qt.Checked if allowBeta else Qt.Qt.Unchecked)
            self.addonList.setItem(row, 4, allowBetaItem)
        self.addonList.resizeColumnsToContents()
        self.adjustSize()
        
    def saveAddons(self):
        print("Saving addons to ",self.addonsFile)
        addons = []
        self.addonList.sortItems(0)
        for row in iter(range(self.addonList.rowCount())):
            addons.append(dict(
                name=str(self.addonList.item(row, 0).text()),
                uri=str(self.addonList.item(row, 1).text()),
                version=str(self.addonList.item(row, 2).text()),
                toc=str(self.addonList.item(row,3).text()),
                allowbeta=bool(self.addonList.item(row, 4).checkState() == Qt.Qt.Checked)
            ))
        data={}
        data['addons'] = addons
        data['dbversion'] = defines.LCURSE_DBVERSION
        with open(self.addonsFile, "w") as f:
            json.dump(data, f,indent=1)

    def addAddon(self):
        url = None
        addAddonDlg = addaddondlg.AddAddonDlg(self, self.availableAddons)
        result = addAddonDlg.exec_()
        if result != Qt.QDialog.Accepted:
            return
        nameOrUrl = addAddonDlg.getText()
        name = nameOrUrl
        try:
            for item in self.availableAddons:
                if item[0] == name:
                    url = item[1]
        except IndexError:
            print("can't handle: " + name)
            name = ""
        
        if url == None:
            url = str(nameOrUrl)
            if "curse.com" in url:
                try:
                    print("retrieving addon informations")
                    response = opener.open(urlparse(urlquote(url, ':/')).geturl())
                    soup = BeautifulSoup(response.read(), "lxml")
                    try:
                        captions = soup.select("#project-overview header h2")
                        name = captions[0].string
                    except:
                        print("Curse.com layout has changed.")
                        pass
                except HTTPError as e:
                    print(e)
            elif url.endswith(".git"):
                name = os.path.basename(url)[:-4]

        if name:
            newrow = self.addonList.rowCount()
            self.addonList.insertRow(newrow)
            self.addonList.setItem(newrow, 0, Qt.QTableWidgetItem(name))
            self.addonList.setItem(newrow, 1, Qt.QTableWidgetItem(url))
            self.addonList.setItem(newrow, 2, Qt.QTableWidgetItem(""))
            self.addonList.setItem(newrow, 3, Qt.QTableWidgetItem(""))
            allowBetaItem = Qt.QTableWidgetItem()
            allowBetaItem.setCheckState(Qt.Qt.Unchecked)
            self.addonList.setItem(newrow, 4, allowBetaItem)

    def updateDatabaseFormat(self,oldVersion):
        print("Db version is ", oldVersion, " vs ", defines.LCURSE_DBVERSION)
        if oldVersion >= defines.LCURSE_DBVERSION:
            return {}
        print("Database update!")
        settings = Qt.QSettings()
        parent = "{}/Interface/AddOns".format(str(settings.value(defines.WOW_FOLDER_KEY, defines.WOW_FOLDER_DEFAULT)))
        contents = os.listdir(parent)
        contents.sort()
        tocversions={}
        for item in contents:
            itemDir = "{}/{}".format(parent, item)
            if os.path.isdir(itemDir) and not item.lower().startswith("blizzard_"):
                toc = "{}/{}.toc".format(itemDir, item)
                if os.path.exists(toc):
                    tmp = self.extractAddonMetadataFromTOC(toc)
                    name=self.removeStupidStuff(tmp[0])
                    tocversions[tmp[0]]={"folder":item,"toc":tmp[3]}
        with open(defines.LCURSE_ADDON_TOCS_CACHE, "w") as f:
            json.dump(tocversions, f,indent=1)
        return tocversions

    def removeAddon(self):
        row = self.addonList.currentRow()
        print("Current Row: {0:d}".format(row))
        answer = Qt.QMessageBox.question(self, self.tr("Remove selected addon"),
                                         str(self.tr("Do you really want to remove the following addon?\n{}")).format(
                                             str(self.addonList.item(row, 0).text())),
                                         Qt.QMessageBox.Yes, Qt.QMessageBox.No)
        if answer != Qt.QMessageBox.Yes:
            return
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
                toc = "{}/{}.toc".format(itemDir, item)
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
                    toc = "{}/{}.toc".format(itemDir, item)
                    if os.path.exists(toc):
                        tmp = self.extractAddonMetadataFromTOC(toc)
                    for d in deleted_addons:
                        deletions = list(filter(None, re.split("[_, \-!?:]+", d)))
                        for word in deletions:
                            if re.search(word, tmp[0]):
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
        elif data is None:
            self.setRowColor(addon[0], Qt.Qt.red)
        else:
            self.setRowColor(addon[0], Qt.Qt.white)

    def checkAddonForUpdate(self):
        row = self.addonList.currentRow()
        addons = []
        name = self.addonList.item(row, 0).text()
        uri = self.addonList.item(row, 1).text()
        version = self.addonList.item(row, 2).text()
        allowBeta = bool(self.addonList.item(row, 4).checkState() == Qt.Qt.Checked)
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
            allowBeta = bool(self.addonList.item(row, 4).checkState() == Qt.Qt.Checked)
            addons.append((row, name, uri, version, allowBeta))

        checkDlg = waitdlg.CheckDlg(self, addons)
        checkDlg.checkFinished.connect(self.onCheckFinished)
        checkDlg.exec_()

    def onUpdateFinished(self, addon, result):
        if result:
            toc=str(addon[6])
            if os.path.exists(toc):
                tmp = self.extractAddonMetadataFromTOC(toc)
            data = self.addonList.item(addon[0], 0).data(Qt.Qt.UserRole)
            self.addonList.item(addon[0], 2).setText(data[0])
            self.addonList.item(addon[0], 3).setText(tmp[3])
            if (tmp[3] < defines.TOC):
                self.addonList.item(addon[0], 3).setForeground(Qt.Qt.red)
            else:
                self.addonList.item(addon[0], 3).setForeground(Qt.Qt.blue)
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
        if not data:
            self.checkAddonForUpdate()

        data = self.addonList.item(row, 0).data(Qt.Qt.UserRole)
        if not data:
            return

        name = self.addonList.item(row, 0).text()
        uri = self.addonList.item(row, 1).text()
        version = self.addonList.item(row, 2).text()
        allowBeta = bool(self.addonList.item(row, 4).checkState() == Qt.Qt.Checked)
        addons.append((row, name, uri, version, allowBeta, data))

        if addons:
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
                allowBeta = bool(self.addonList.item(row, 4).checkState() == Qt.Qt.Checked)
                addons.append((row, name, uri, version, allowBeta, data))

        if addons:
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
