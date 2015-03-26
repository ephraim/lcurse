from PyQt5 import Qt
from bs4 import BeautifulSoup
from urllib.request import build_opener, HTTPCookieProcessor, HTTPError
from http import cookiejar
import zipfile
import defines
import os
import re
from _thread import start_new_thread

class CheckDlg(Qt.QDialog):
	checkFinished = Qt.pyqtSignal(Qt.QVariant, bool, Qt.QVariant)
	def __init__(self, parent, addons):
		super(CheckDlg, self).__init__(parent)
		settings = Qt.QSettings()
		layout = Qt.QVBoxLayout(self)
		if len(addons) == 1:
			layout.addWidget(Qt.QLabel(self.tr("Verifying if the addon needs an update...")))
		else:
			layout.addWidget(Qt.QLabel(self.tr("Verifying which addon needs an update...")))
		self.progress = Qt.QProgressBar(self)
		self.progress.setRange(0, len(addons))
		self.progress.setValue(0)
		self.progress.setFormat("%v / %m | %p%")
		layout.addWidget(self.progress)
		self.addons = addons
		self.maxThreads = int(settings.value(defines.LCURSE_MAXTHREADS_KEY, defines.LCURSE_MAXTHREADS_DEFAULT))
		self.sem = Qt.QSemaphore(self.maxThreads)

	def startWorkerThreads(self):
		self.threads = []
		for addon in self.addons:
			self.sem.acquire()
			thread = CheckWorker(addon)
			thread.checkFinished.connect(self.onCheckFinished)
			thread.start()
			self.threads.append(thread)	

	def exec_(self):
		start_new_thread(self.startWorkerThreads, ())
		super(CheckDlg, self).exec_()

	@Qt.pyqtSlot(int, Qt.QVariant)
	def onCheckFinished(self, addon, needsUpdate, updateData):
		self.sem.release()
		value = self.progress.value() + 1
		self.progress.setValue(value)
		self.checkFinished.emit(addon, needsUpdate, updateData)
		if value == self.progress.maximum():
			self.close()

class CheckWorker(Qt.QThread):
	checkFinished = Qt.pyqtSignal(Qt.QVariant, bool, Qt.QVariant)
	def __init__(self, addon):
		super(CheckWorker, self).__init__()
		self.addon = addon
		self.opener = build_opener(HTTPCookieProcessor(cookiejar.CookieJar()))
		# default User-Agent ('Python-urllib/2.6') will *not* work
		self.opener.addheaders = [('User-Agent', 'Mozilla/5.0'),]

	def needsUpdate(self):
		try:
			response = self.opener.open(str(self.addon[2]) + "/download")
			html = response.read()
			soup = BeautifulSoup(html)
			lis = soup.select('#breadcrumbs-wrapper ul li span')
			if len(lis) > 0:
				version = lis[len(lis) - 1].string
				if str(self.addon[3]) != version:
					downloadLink = soup.select(".download-link")[0].get('data-href')
					return (True, (version, downloadLink))
			return (False, ("", ""))
		except HTTPError as e:
			print(e)
		return (False, None)

	def run(self):
		result = self.needsUpdate()
		self.checkFinished.emit(self.addon, result[0], result[1]) 

class UpdateDlg(Qt.QDialog):
	updateFinished = Qt.pyqtSignal(Qt.QVariant, bool)
	def __init__(self, parent, addons):
		super(UpdateDlg, self).__init__(parent)
		settings = Qt.QSettings()
		layout = Qt.QVBoxLayout(self)
		if len(addons) == 1:
			layout.addWidget(Qt.QLabel(self.tr("Updating the addon...")))
		else:
			layout.addWidget(Qt.QLabel(self.tr("Updating the addons...")))
		self.progress = Qt.QProgressBar(self)
		self.progress.setRange(0, len(addons))
		self.progress.setValue(0)
		self.progress.setFormat("%v / %m | %p%")
		layout.addWidget(self.progress)
		self.addons = addons
		self.maxThreads = int(settings.value(defines.LCURSE_MAXTHREADS_KEY, defines.LCURSE_MAXTHREADS_DEFAULT))
		self.sem = Qt.QSemaphore(self.maxThreads)

	def startWorkerThreads(self):
		self.threads = []
		for addon in self.addons:
			self.sem.acquire()
			thread = UpdateWorker(addon)
			thread.updateFinished.connect(self.onUpdateFinished)
			thread.start()
			self.threads.append(thread)	

	def exec_(self):
		start_new_thread(self.startWorkerThreads, ())
		super(UpdateDlg, self).exec_()

	@Qt.pyqtSlot(int, Qt.QVariant)
	def onUpdateFinished(self, addon, result):
		value = self.progress.value() + 1
		self.progress.setValue(value)
		self.updateFinished.emit(addon, result)
		if value == self.progress.maximum():
			self.close()

class UpdateWorker(Qt.QThread):
	updateFinished = Qt.pyqtSignal(Qt.QVariant, bool)
	def __init__(self, addon):
		super(UpdateWorker, self).__init__()
		self.addon = addon
		self.opener = build_opener(HTTPCookieProcessor(cookiejar.CookieJar()))
		# default User-Agent ('Python-urllib/2.6') will *not* work
		self.opener.addheaders = [('User-Agent', 'Mozilla/5.0'),]

	def doUpdate(self):
		try:
			settings = Qt.QSettings()
			print("updating addon %s to version %s ..." % (self.addon[1], self.addon[4][0]))
			response = self.opener.open(self.addon[4][1])
			filename = "/tmp/%s" % (self.addon[4][1].split('/')[-1])
			dest = "%s/Interface/AddOns/" % (settings.value(defines.WOW_FOLDER_KEY, defines.WOW_FOLDER_DEFAULT))
			with open(filename, 'wb') as zipped:
				zipped.write(response.read())
			with zipfile.ZipFile(filename, "r") as z:
				z.extractall(dest)
			os.remove(filename)
			return True
		except Exception as e:
			print(e)
		return False

	def run(self):
		result = self.doUpdate()
		self.updateFinished.emit(self.addon, result) 


class UpdateCatalogDlg(Qt.QDialog):
	updateCatalogFinished = Qt.pyqtSignal(Qt.QVariant)
	def __init__(self, parent):
		super(UpdateCatalogDlg, self).__init__(parent)
		layout = Qt.QVBoxLayout(self)
		layout.addWidget(Qt.QLabel(self.tr("Updating list of available Addons...")))
		self.progress = Qt.QProgressBar(self)
		self.progress.setRange(0, 0)
		self.progress.setValue(0)
		layout.addWidget(self.progress)

	def exec_(self):
		self.thread = UpdateCatalogWorker()
		self.thread.updateCatalogFinished.connect(self.onUpdateCatalogFinished)
		self.thread.retrievedLastpage.connect(self.setMaxProgress)
		self.thread.progress.connect(self.onProgress)
		self.thread.start()
		super(UpdateCatalogDlg, self).exec_()

	@Qt.pyqtSlot(int)
	def setMaxProgress(self, maxval):
		self.progress.setRange(0, maxval)

	@Qt.pyqtSlot(int)
	def onProgress(self, foundAddons):
		value = self.progress.value() + 1
		self.progress.setValue(value)
		self.progress.setFormat(self.tr("%%p%% - found Addons: %d") % (foundAddons))

	@Qt.pyqtSlot(Qt.QVariant)
	def onUpdateCatalogFinished(self, addons):
		self.updateCatalogFinished.emit(addons)
		self.close()

class UpdateCatalogWorker(Qt.QThread):
	updateCatalogFinished = Qt.pyqtSignal(Qt.QVariant)
	retrievedLastpage = Qt.pyqtSignal(int)
	progress = Qt.pyqtSignal(int)
	def __init__(self):
		super(UpdateCatalogWorker, self).__init__()
		settings = Qt.QSettings()
		self.opener = build_opener(HTTPCookieProcessor(cookiejar.CookieJar()))
		# default User-Agent ('Python-urllib/2.6') will *not* work
		self.opener.addheaders = [('User-Agent', 'Mozilla/5.0'),]
		self.addons = []
		self.addonsMutex = Qt.QMutex()
		self.maxThreads = int(settings.value(defines.LCURSE_MAXTHREADS_KEY, defines.LCURSE_MAXTHREADS_DEFAULT))
		self.sem = Qt.QSemaphore(self.maxThreads)

	# pager => "Page 1 of 178"
	def parsePager(self, pager):
		m = re.search("(\d+) of (\d+)", pager)
		if m == None:
			raise Exception("pager is crap")
		return int(m.group(2))

	def retrievePartialListOfAddons(self, page):
		response = self.opener.open("http://www.curse.com/addons/wow?page=%d" % (page))
		soup = BeautifulSoup(response.read())

		pager = soup.select("span .pager-display")
		lastpage = self.parsePager(pager[0].string)

		links = soup.select("li .title h4 a") # li .title h4 a")
		self.addonsMutex.lock()
		for link in links:
			self.addons.append( [ link.string, "http://www.curse.com%s" % (link.get("href")) ])
		self.progress.emit(len(self.addons))
		self.addonsMutex.unlock()

		self.sem.release()

		return lastpage

	def retrieveListOfAddons(self):
		page = 1
		lastpage = 1
		self.sem.acquire()
		lastpage = self.retrievePartialListOfAddons(page)
		page += 1
		self.retrievedLastpage.emit(lastpage)

		while page <= lastpage:
			self.sem.acquire()
			start_new_thread(self.retrievePartialListOfAddons, (page,))
			page += 1

	def run(self):
		self.retrieveListOfAddons()

		# wait until all worker are done
		self.sem.acquire(self.maxThreads)

		self.updateCatalogFinished.emit(self.addons)
