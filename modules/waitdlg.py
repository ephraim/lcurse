from PyQt4 import Qt


class WaitDlg(Qt.QDialog):
	def __init__(self, parent, addonsCount, callback):
		super(WaitDlg, self).__init__(parent)
		layout = Qt.QVBoxLayout(self)
		self.progress = Qt.QProgressBar(self)
		self.progress.setRange(0, addonsCount - 1)
		layout.addWidget(self.progress)
		self.addonsCount = addonsCount
		self.callback = callback

	def exec_(self):
		self.threads = []
		for idx in xrange(self.addonsCount):
			self.threads.append(TaskThread(idx, self.callback))
			self.threads[idx].taskFinished.connect(self.onTaskFinished)
			self.threads[idx].start()
		super(WaitDlg, self).exec_()

	def onTaskFinished(self, idx):
		value = self.progress.value() + 1
		self.progress.setValue(value)
		if value == self.progress.maximum():
			self.close()


class TaskThread(Qt.QThread):
	taskFinished = Qt.pyqtSignal(int)
	def __init__(self, idx, callback):
		super(TaskThread, self).__init__()
		self.idx = idx
		self.callback = callback

	def run(self):
		self.callback(self.idx)
		self.taskFinished.emit(self.idx) 
		
