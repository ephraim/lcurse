#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import os

from PyQt4 import Qt
from bs4 import BeautifulSoup
from zipfile import ZipFile

import cookielib, urllib2
import preferences
import waitdlg
import defines

opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
# default User-Agent ('Python-urllib/2.6') will *not* work
opener.addheaders = [('User-Agent', 'Mozilla/5.0'),]

class MainWidget(Qt.QWidget):
	def __init__(self):
		super(MainWidget, self).__init__()
		self.addonsFile = os.path.expanduser("~/.lcurse/addons.json")
		self.addWidgets()
		self.loadAddons()

	def addWidgets(self):
		box = Qt.QVBoxLayout(self)

		menubar = Qt.QMenuBar()
		menuFile = menubar.addMenu(self.tr("General"))
		action = Qt.QAction(self.tr("Load Addons"), self)
		action.setShortcut('Ctrl+L')
		action.setStatusTip(self.tr("Re/Load your addons configuration"))
		action.triggered.connect(self.loadAddons)
		menuFile.addAction(action)
		action = Qt.QAction(self.tr("Save Addons"), self)
		action.setShortcut('Ctrl+S')
		action.setStatusTip(self.tr("Save your addons configuration"))
		action.triggered.connect(self.saveAddons)
		menuFile.addAction(action)

		menuFile.addSeparator()

		action = Qt.QAction(self.tr("Preferences"), self)
		action.setShortcut('Ctrl+P')
		action.setStatusTip(self.tr("Change preferences like wow install folder"))
		action.triggered.connect(self.openPreferences)
		menuFile.addAction(action)

		menuFile.addSeparator()

		action = Qt.QAction(self.tr("Exit"), self)
		action.setShortcut('Ctrl+Q')
		action.setStatusTip(self.tr("Exit application"))
		self.connect(action, Qt.SIGNAL('triggered()'), Qt.SLOT('close()'))
		menuFile.addAction(action)

		menuAddons = menubar.addMenu(self.tr("Addons"))
		action = Qt.QAction(self.tr("Check all addons"), self)
		action.setShortcut('Ctrl+Shift+A')
		action.setStatusTip(self.tr("Check all addons for new version"))
		action.triggered.connect(self.checkAddonsForUpdate)
		menuAddons.addAction(action)
		action = Qt.QAction(self.tr("Check addon"), self)
		action.setShortcut('Ctrl+A')
		action.setStatusTip(self.tr("Check currently selected addon for new version"))
		action.triggered.connect(self.checkAddonForUpdate)
		menuAddons.addAction(action)
		menuAddons.addSeparator()

		action = Qt.QAction(self.tr("Update all addons"), self)
		action.setShortcut('Ctrl+Shift+U')
		action.setStatusTip(self.tr("Update all addons which need an update"))
		action.triggered.connect(self.updateAddons)
		menuAddons.addAction(action)
		action = Qt.QAction(self.tr("Update addon"), self)
		action.setShortcut('Ctrl+U')
		action.setStatusTip(self.tr("Update currently selected addons if needed"))
		action.triggered.connect(self.updateAddon)
		menuAddons.addAction(action)
		menuAddons.addSeparator()
		action = Qt.QAction(self.tr("Add addon"), self)
		action.setStatusTip(self.tr("Add a new addon"))
		action.triggered.connect(self.addAddon)
		menuAddons.addAction(action)
		action = Qt.QAction(self.tr("Remove addon"), self)
		action.setStatusTip(self.tr("Remove currently selected addon"))
		action.triggered.connect(self.removeAddon)
		menuAddons.addAction(action)
		menuAddons.addSeparator()

		self.addonList = Qt.QTableWidget()
		self.addonList.setColumnCount(3)
		self.addonList.setHorizontalHeaderLabels(["Name", "Url", "Version"])

		self.resize(800, 600)
		screen = Qt.QDesktopWidget().screenGeometry()
		size = self.geometry()
		self.move((screen.width()-size.width())/2, (screen.height()-size.height())/4)
		self.setWindowTitle('WoW!Curse')

		box.addWidget(menubar)
		box.addWidget(self.addonList)

	def openPreferences(self):
		pref = preferences.PreferencesDlg(self)
		pref.exec_()

	def loadAddons(self):
		self.addonList.clearContents()
		addons = None
		with file(self.addonsFile) as f:
			addons = json.load(f)
		if addons != None:
			self.addonList.setRowCount(len(addons))
			for (row, addon) in enumerate(addons):
				self.addonList.setItem(row, 0, Qt.QTableWidgetItem(addon["name"]))
				self.addonList.setItem(row, 1, Qt.QTableWidgetItem(addon["uri"]))
				self.addonList.setItem(row, 2, Qt.QTableWidgetItem(addon["version"]))
			self.addonList.resizeColumnsToContents()

	def saveAddons(self):
		addons = []
		for row in xrange(self.addonList.rowCount()):
			addons.append(dict(
					name=str(self.addonList.item(row, 0).text()),
					uri=str(self.addonList.item(row, 1).text()),
					version=str(self.addonList.item(row, 2).text())
				))
		with file(self.addonsFile, "w") as f:
			json.dump(addons, f)

	def addAddon(self):
		(url, ok) = Qt.QInputDialog.getText(self, self.tr("Add addon"), self.tr("Enter the curse URL to the addon:"), Qt.QLineEdit.Normal, "http://www.curse.com/addons/wow/atlas");
		if ok == True and url != "":
			name = ""
			try:
				print("retrieving addon informations")
				response = opener.open(str(url))
				soup = BeautifulSoup(response.read())
				captions = soup.select(".caption span span span")
				name = captions[0].string
			except urllib2.HTTPError as e:
				print e

			if name != "":
				newrow = self.addonList.rowCount()
				self.addonList.insertRow(newrow)
				self.addonList.setItem(newrow, 0, Qt.QTableWidgetItem(name))
				self.addonList.setItem(newrow, 1, Qt.QTableWidgetItem(url))
				self.addonList.setItem(newrow, 2, Qt.QTableWidgetItem(""))

	def removeAddon(self):
		row = self.addonList.currentRow()
		if row != 0:
			answer = Qt.QMessageBox.question(self, self.tr("Remove selected addon"), self.tr("Do you really want to remove the following addon?\n%s") % (str(self.addonList.item(row, 0).text())),
						Qt.QMessageBox.Yes, Qt.QMessageBox.No)
			if answer == Qt.QMessageBox.Yes:
				self.addonList.removeRow(row)

	def setRowColor(self, row, color):
		self.addonList.item(row, 0).setBackground(color)
		self.addonList.item(row, 1).setBackground(color)
		self.addonList.item(row, 2).setBackground(color)

	def _checkAddonForUpdate(self, row):
		try:
			self.setRowColor(row, Qt.Qt.white)
			response = opener.open(str(self.addonList.item(row, 1).text()) + "/download")
			html = response.read()
			with open("/tmp/response.txt", "w") as f:
				f.write(html)
			soup = BeautifulSoup(html)
			lis = soup.select('#breadcrumbs-wrapper ul li span')
			if len(lis) > 0:
				version = lis[len(lis) - 1].string
				if str(self.addonList.item(row, 2).text()) != version:
					downloadLink = soup.select(".download-link")[0].get('data-href')
					self.setRowColor(row, Qt.Qt.yellow)
					self.addonList.item(row, 0).setData(Qt.Qt.UserRole, (version, downloadLink))
		except urllib2.HTTPError as e:
			print e

	def checkAddonForUpdate(self):
		self._checkAddonForUpdate(self.addonList.currentRow())
		self.saveAddons()

	def checkAddonsForUpdate(self):
		waitDlg = waitdlg.WaitDlg(self, self.addonList.rowCount(), self._checkAddonForUpdate)
		waitDlg.exec_()
		self.saveAddons()

	def _updateAddon(self, row):
		data = self.addonList.item(row, 0).data(Qt.Qt.UserRole).toPyObject()
		if data == None:
			self._checkAddonForUpdate(row)
			data = self.addonList.item(row, 0).data(Qt.Qt.UserRole).toPyObject()
			if data == None:
				return
		try:
			settings = Qt.QSettings()
			print("updating addon %s to version %s ..." % (self.addonList.item(row, 0).text(), data[0]))
			response = opener.open(data[1])
			filename = data[1].split('/')[-1]
			with open('/tmp/{}'.format(filename), 'wb') as zipped:
				zipped.write(response.read())
			zipped = ZipFile('/tmp/{}'.format(filename))
			zipped.extractall(settings.value(defines.WOW_FOLDER_KEY, defines.WOW_FOLDER_DEFAULT))
			os.remove('/tmp/{}'.format(filename))
			self.addonList.setItem(row, 2, Qt.QTableWidgetItem(data[0]))
			self.setRowColor(row, Qt.Qt.green)
		except Exception as e:
			print(e)

	def updateAddon(self):
		row = self.addonList.currentRow()
		self._updateAddon(row)
		self.saveAddons()

	def updateAddons(self):
		waitDlg = waitdlg.WaitDlg(self, self.addonList.rowCount(), self._updateAddon)
		waitDlg.exec_()
		self.saveAddons()

	def start(self):
		return self.exec_()

if __name__ == "__main__":
	sys.exit(42)
