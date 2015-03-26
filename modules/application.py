#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import os
import re
from urllib.parse import urlparse
import urllib
from urllib.request import build_opener, HTTPCookieProcessor
from http import cookiejar
from bs4 import BeautifulSoup

from PyQt5 import Qt

import preferences
import addaddondlg
import waitdlg
import defines

opener = build_opener(HTTPCookieProcessor(cookiejar.CookieJar()))
# default User-Agent ('Python-urllib/2.6') will *not* work
opener.addheaders = [('User-Agent', 'Mozilla/5.0'),]

class MainWidget(Qt.QMainWindow):
	def __init__(self):
		super(MainWidget, self).__init__()
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

		menuAddons = menubar.addMenu(self.tr("Addons"))
		menuAddons.addAction(actionCheckAll)
		menuAddons.addAction(actionCheck)
		menuAddons.addSeparator()
		menuAddons.addAction(actionUpdateAll)
		menuAddons.addAction(actionUpdate)
		menuAddons.addSeparator()
		menuAddons.addAction(actionAdd)
		menuAddons.addAction(actionRemove)
		toolbar = self.addToolBar(self.tr("Addons"))
		toolbar.addAction(actionUpdateAll)
		toolbar.addAction(actionAdd)
		self.addAction(actionCheckAll)
		self.addAction(actionCheck)
		self.addAction(actionUpdateAll)
		self.addAction(actionUpdate)

		actionCatalogUpdate = Qt.QAction(self.tr("Update Catalog"), self)
		actionCatalogUpdate.setStatusTip(self.tr("Retrieve a list of available addons"))
		actionCatalogUpdate.triggered.connect(self.updateCatalog)
		menuCatalog = menubar.addMenu(self.tr("Catalog"))
		menuCatalog.addAction(actionCatalogUpdate)
		toolbar = self.addToolBar(self.tr("Catalog"))
		toolbar.addAction(actionCatalogUpdate)

		self.addonList = Qt.QTableWidget(self.mainWidget)
		self.addonList.setColumnCount(3)
		self.addonList.setHorizontalHeaderLabels(["Name", "Url", "Version"])

		self.resize(830, 805)
		screen = Qt.QDesktopWidget().screenGeometry()
		size = self.geometry()
		self.move((screen.width()-size.width())/2, (screen.height()-size.height())/4)
		self.setWindowTitle('WoW!Curse')

		box.addWidget(self.addonList)
		self.statusBar().showMessage(self.tr("Ready"))
		self.setCentralWidget(self.mainWidget)
		self.show()

	def sizeHint(self):
		width = self.addonList.sizeHintForColumn(0) + self.addonList.sizeHintForColumn(1) + self.addonList.sizeHintForColumn(2) + 63
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

		uri = "http://www.curse.com/addons/wow/%s" % (name.lower().replace(" ", "-"))
		if curseId != "":
			uri = "http://www.curse.com/addons/wow/%s" % (curseId)

		if name == "" or version == "":
			print("not enough informations found for addon in toc: %s" % (toc))
			return ["","",""]

		return [name, uri, version]

	def importAddons(self):
		settings = Qt.QSettings()
		parent = "%s/Interface/AddOns" % (str(settings.value(defines.WOW_FOLDER_KEY, defines.WOW_FOLDER_DEFAULT)))
		contents = os.listdir(parent)
		for item in contents:
			itemDir = "%s/%s" % (parent, item)
			if os.path.isdir(itemDir) and not item.lower().startswith("blizzard_"):
				toc = "%s/%s.toc" % (itemDir, item)
				if os.path.exists(toc):
					tmp = self.extractAddonMetadataFromTOC(toc)
					if tmp[0] == "":
						continue
					(name, uri, version) = tmp
					row = self.addonList.rowCount()
					if len(self.addonList.findItems(name, Qt.Qt.MatchExactly)) == 0:
						self.addonList.setRowCount(row + 1)
						self.insertAddon(row, name, uri, version)
		self.addonList.resizeColumnsToContents()
		self.addonList.sortItems(0)
		self.saveAddons()

	def openPreferences(self):
		pref = preferences.PreferencesDlg(self)
		pref.exec_()

	def insertAddon(self, row, name, uri, version):
		self.addonList.setItem(row, 0, Qt.QTableWidgetItem(name))
		self.addonList.setItem(row, 1, Qt.QTableWidgetItem(uri))
		self.addonList.setItem(row, 2, Qt.QTableWidgetItem(version))

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
			self.addonList.resizeColumnsToContents()
			self.adjustSize()

	def saveAddons(self):
		addons = []
		for row in iter(range(self.addonList.rowCount())):
			addons.append(dict(
					name=str(self.addonList.item(row, 0).text()),
					uri=str(self.addonList.item(row, 1).text()),
					version=str(self.addonList.item(row, 2).text())
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
				try:
					print("retrieving addon informations")
					response = opener.open(url)
					soup = BeautifulSoup(response.read())
					captions = soup.select(".caption span span span")
					name = captions[0].string
				except urllib2.HTTPError as e:
					print(e)
			else:
				name = nameOrUrl
				url  = [ item[1] for item in self.availableAddons if item[0] == name ][0]

			if name != "":
				newrow = self.addonList.rowCount()
				self.addonList.insertRow(newrow)
				self.addonList.setItem(newrow, 0, Qt.QTableWidgetItem(name))
				self.addonList.setItem(newrow, 1, Qt.QTableWidgetItem(url))
				self.addonList.setItem(newrow, 2, Qt.QTableWidgetItem(""))

	def removeAddon(self):
		row = self.addonList.currentRow()
		if row != 0:
			answer = Qt.QMessageBox.question(self, self.tr("Remove selected addon"), str(self.tr("Do you really want to remove the following addon?\n%s")) % (str(self.addonList.item(row, 0).text())),
						Qt.QMessageBox.Yes, Qt.QMessageBox.No)
			if answer == Qt.QMessageBox.Yes:
				self.addonList.removeRow(row)

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
		addons.append((row, name, uri, version))

		checkDlg = waitdlg.CheckDlg(self, addons)
		checkDlg.checkFinished.connect(self.onCheckFinished)
		checkDlg.exec_()

	def checkAddonsForUpdate(self):
		addons = []
		for row in iter(range(self.addonList.rowCount())):
			name = self.addonList.item(row, 0).text()
			uri = self.addonList.item(row, 1).text()
			version = self.addonList.item(row, 2).text()
			addons.append((row, name, uri, version))

		checkDlg = waitdlg.CheckDlg(self, addons)
		checkDlg.checkFinished.connect(self.onCheckFinished)
		checkDlg.exec_()

	def onUpdateFinished(self, addon, result):
		if result:
			data = self.addonList.item(addon[0], 0).data(Qt.Qt.UserRole)
			self.addonList.item(addon[0], 2).setText(data[0])
			self.addonList.item(addon[0], 0).setData(Qt.Qt.UserRole, None)
			self.setRowColor(addon[0], Qt.Qt.green)

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
		addons.append((row, name, uri, version, data))

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
				addons.append((row, name, uri, version, data))

		if len(addons):
			updateDlg = waitdlg.UpdateDlg(self, addons)
			updateDlg.updateFinished.connect(self.onUpdateFinished)
			updateDlg.exec_()
			self.saveAddons()

	def onUpdateCatalogFinished(self, addons):
		print("retrieved list of addons: %d" % (len(addons)))
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
