from PyQt5 import Qt
from bs4 import BeautifulSoup
from urllib.request import build_opener, HTTPCookieProcessor, HTTPError
from http import cookiejar
import zipfile
import defines
import os
import re
from _thread import start_new_thread
from threading import Lock
from subprocess import check_output, check_call

class CheckDlg(Qt.QDialog):
	checkFinished = Qt.pyqtSignal(Qt.QVariant, bool, Qt.QVariant)
	closeSignal = Qt.pyqtSignal()
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
		cancelBox = Qt.QHBoxLayout()
		cancelBox.addStretch()
		self.cancelButton = Qt.QPushButton(self.tr("Cancel"), self)
		self.cancelButton.clicked.connect(self.onCancel)
		cancelBox.addWidget(self.cancelButton)
		cancelBox.addStretch()
		layout.addLayout(cancelBox)
		self.addons = addons
		self.maxThreads = int(settings.value(defines.LCURSE_MAXTHREADS_KEY, defines.LCURSE_MAXTHREADS_DEFAULT))
		self.sem = Qt.QSemaphore(self.maxThreads)

		# safe to use without a mutex because reading and writing are independent of each other, and GIL will make these atomic operations.
		self.cancelled = False

		# protected with self.progressMutex
		self.progressMutex = Lock()
		self.progressOrAborted = 0

		self.closeSignal.connect(self.close)

	def closeEvent(self, event):
		with self.progressMutex:
			if self.progressOrAborted < self.progress.maximum():
				# if we aren't ready to close, the user pressed the close button - set the cancel flag so we can stop
				self.cancelled = True
				event.ignore()

	def startWorkerThreads(self):
		self.threads = []
		for addon in self.addons:
			self.sem.acquire()
			if not self.cancelled:
				thread = CheckWorker(addon)
				thread.checkFinished.connect(self.onCheckFinished)
				thread.start()
				self.threads.append(thread)
			else:
				self.onCancelOrFinish(False)

	def exec_(self):
		start_new_thread(self.startWorkerThreads, ())
		super(CheckDlg, self).exec_()

	def onCancelOrFinish(self, updateProgress):
		self.sem.release()
		shouldClose = False
		if updateProgress:
			self.progress.setValue(self.progress.value() + 1)
		with self.progressMutex:
			self.progressOrAborted += 1
			if self.progressOrAborted == self.progress.maximum():
				shouldClose = True
		if shouldClose:
			# emit this as a signal so that it will be processed on the main thread.
			# Otherwise, this will try to do cleanup from a worker thread, which is a /bad/ idea.
			self.closeSignal.emit()

	@Qt.pyqtSlot(int, Qt.QVariant)
	def onCheckFinished(self, addon, needsUpdate, updateData):
		self.checkFinished.emit(addon, needsUpdate, updateData)
		self.onCancelOrFinish(True)

	def onCancel(self):
		self.cancelled = True

class CheckWorker(Qt.QThread):
	checkFinished = Qt.pyqtSignal(Qt.QVariant, bool, Qt.QVariant)
	def __init__(self, addon):
		super(CheckWorker, self).__init__()
		self.addon = addon
		self.opener = build_opener(HTTPCookieProcessor(cookiejar.CookieJar()))
		# default User-Agent ('Python-urllib/2.6') will *not* work
		self.opener.addheaders = [('User-Agent', 'Mozilla/5.0'),]

	def needsUpdateGit(self):
		try:
			settings = Qt.QSettings()
			dest = "%s/Interface/AddOns/%s" % (settings.value(defines.WOW_FOLDER_KEY, defines.WOW_FOLDER_DEFAULT), os.path.basename(str(self.addon[2])[:-4]))
			originCurrent = str(check_output(["git", "ls-remote", str(self.addon[2]), "HEAD"]), "utf-8").split()[0]
			localCurrent = self.addon[3]
			if localCurrent != originCurrent:
				return (True, (originCurrent, ""))
			return (False, ("", ""))
		except Exception as e:
			print(e)
		return (False, None)	

	def needsUpdateCurse(self):
		try:
			pattern = re.compile("-nolib$")
			response = self.opener.open(str(self.addon[2])) # + "/download")
			html = response.read()
			soup = BeautifulSoup(html)
			possibleValues = "1"
			if self.addon[4]:
				possibleValues = re.compile("^[12]$")
			lis = soup.findAll("td", attrs={"data-sort-value": possibleValues})
			if len(lis) > 0:
				versionIdx = 0
				version = lis[versionIdx].parent.contents[0].contents[0].string
				if len(lis) > 1 and pattern.search(version) != None and pattern.sub("", version) == lis[1].parent.contents[0].contents[0].string:
						versionIdx = 1
						version = lis[versionIdx].parent.contents[0].contents[0].string
				if str(self.addon[3]) != version:
					response = self.opener.open("http://www.curse.com" + lis[versionIdx].parent.contents[0].contents[0]['href'])
					html = response.read()
					soup = BeautifulSoup(html)
					downloadLink = soup.select(".download-link")[0].get('data-href')
					return (True, (version, downloadLink))
			return (False, ("", ""))
		except HTTPError as e:
			print(e)
		return (False, None)

	def run(self):
		if self.addon[2].startswith("http://www.curse.com"):
			result = self.needsUpdateCurse()
		elif self.addon[2].endswith(".git"):
			result = self.needsUpdateGit()
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
		self.sem.release()
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

	def doUpdateGit(self):
		try:
			settings = Qt.QSettings()
			dest = "%s/Interface/AddOns" % (settings.value(defines.WOW_FOLDER_KEY, defines.WOW_FOLDER_DEFAULT))
			destAddon = "%s/%s" % (dest, os.path.basename(str(self.addon[2]))[:-4])
			print(destAddon)
			if not os.path.exists(destAddon):
				os.chdir(dest)
				check_call(["git", "clone", self.addon[2]])
			else:
				os.chdir(destAddon)
				check_call(["git", "pull"])
			return True
		except Exception as e:
			print(e)
		return False

	def doUpdateCurse(self):
		try:
			settings = Qt.QSettings()
			print("updating addon %s to version %s ..." % (self.addon[1], self.addon[5][0]))
			print("getting new version from: %s" % (self.addon[5][1]))
			response = self.opener.open(self.addon[5][1])
			filename = "/tmp/%s" % (self.addon[5][1].split('/')[-1])
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
		if self.addon[2].startswith("http://www.curse.com"):
			result = self.doUpdateCurse()
		elif self.addon[2].endswith(".git"):
			result = self.doUpdateGit()
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
