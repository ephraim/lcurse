#!/usr/bin/env python
# -*- coding: utf-8 -*-

# this script is based on the wowcurse.py from JörnS user from ubuntuusers.de
# I will try to improve it (Thilo Cestonaro)

# JörnS published it under the CC0
# http://creativecommons.org/publicdomain/zero/1.0/


import os, sys, urllib2, csv, pynotify

from urlparse import urlparse
from ConfigParser import RawConfigParser
from zipfile import ZipFile
from bs4 import BeautifulSoup
from PyQt4 import QtCore, QtGui, QtWebKit, QtNetwork

addons = []
updated = []

pynotify.init('Basics')

config = RawConfigParser()

try:
    config.read(os.path.expanduser('~/.wowcurse/settings.cfg'))
    prefix = config.get('Settings', 'Prefix')
    arch = config.getint('Settings', 'Arch')
    bumblebee = config.get('Settings', 'Bumblebee')
except:
    config.add_section('Settings')
    prefix = '.wine-wow'
    arch = 32
    bumblebee = 'none'
    config.set('Settings', 'Prefix', prefix)
    config.set('Settings', 'Arch', arch)
    config.set('Settings', 'Bumblebee', bumblebee)
    
    with open(os.path.expanduser('~/.wowcurse/settings.cfg'), 'wb') as configfile:
        config.write(configfile)

bitdict = {64: 'WoW-64.exe', 32: 'WoW.exe'}

bumbledict = {'primus': 'optirun -b primus wine', 'bumblebee': 'optirun wine', 'none': 'wine'}


def getFile(url):
    response = urllib2.urlopen(url)
    data = response.read()
    filename = url.split('/')[-1]
    with open('/tmp/{}'.format(filename), 'wb') as zipped:
        zipped.write(data)
    zipped = ZipFile('/tmp/{}'.format(filename))
    zipped.extractall(os.path.expanduser('~/{}/drive_c/Program Files (x86)/World of Warcraft/Interface/addons/'.format(prefix)))
    updated.append(filename)
    os.remove('/tmp/{}'.format(filename))
    return filename


class NetworkAccessManager(QtNetwork.QNetworkAccessManager):
    def __init__(self, old_manager):
        QtNetwork.QNetworkAccessManager.__init__(self)
        self.old_manager = old_manager
        self.setCache(old_manager.cache())
        self.setCookieJar(old_manager.cookieJar())
        self.setProxy(old_manager.proxy())
        self.setProxyFactory(old_manager.proxyFactory())

    
    def createRequest(self, operation, request, data):
        if request.url().scheme() != "curse":
            return QtNetwork.QNetworkAccessManager.createRequest(self, operation, request, data)
        else:
            #print(str(request.url()))
            o = urlparse(str(request.url().toString()))
            addons.append(['http://www.curse.com/addons/wow/{}'.format(o.path.split('/')[2]), ''])
            widget.table.setRowCount(len(addons))
            widget.updateCells()
            widget.table.resizeColumnsToContents()
            widget.html.hide()
            widget.table.show()
        if operation == self.GetOperation:
            # Handle download:// URLs separately by creating custom
            # QNetworkReply objects.
            #reply = QtNetwork.QNetworkReply(self, request.url(), self.GetOperation)
            #return reply

            return QtNetwork.QNetworkAccessManager.createRequest(self, operation, request, data)


class WoWCurseWindow(QtGui.QWidget):
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        
        self.resize(800, 600)
        self.setWindowTitle('WoW!Curse')
        #self.setWindowIcon(QtGui.QIcon('/usr/share/icons/Wow-icon-scalable.svg'))
        
        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width()-size.width())/2, (screen.height()-size.height())/2)
        
        settings = QtGui.QPushButton('Einstellungen')
        self.connect(settings, QtCore.SIGNAL('clicked()'), settings_widget.show)
        
        add = QtGui.QPushButton(u'Neues Addon hinzufügen')
        self.connect(add, QtCore.SIGNAL('clicked()'), self.getNewAddon)
        
        update = QtGui.QPushButton('Addons aktualisieren')
        self.connect(update, QtCore.SIGNAL('clicked()'), self.updateAddons)
        
        start = QtGui.QPushButton('Start')
        self.connect(start, QtCore.SIGNAL('clicked()'), self.startWoW)
        
        self.html = QtWebKit.QWebView()
        self.html.hide()
        self.table = QtGui.QTableWidget()
        self.table.setColumnCount(2)
        
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(settings)
        hbox.addStretch(1)
        hbox.addWidget(add)
        hbox.addWidget(update)
        hbox.addStretch(1)
        hbox.addWidget(start)
        
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.table)
        vbox.addWidget(self.html)
        vbox.addLayout(hbox)
        
        self.setLayout(vbox)
        
        self.loadCsv()

        
    def startWoW(self):
        os.system('env WINEDEBUG="-all" WINEPREFIX=$HOME/{} {} "C:\Program Files (x86)\World of Warcraft\{}" &'.format(prefix, bumbledict[bumblebee], bitdict[arch]))
        
        
    def loadCsv(self):
        try:
            with open(os.path.expanduser('~/.wowcurse/addons.csv'), 'rb') as csvfile:
                reader = csv.reader(csvfile, delimiter = ',')
                for row in reader:
                    addons.append(row)
        except:
            pass
        self.table.setRowCount(len(addons))
        self.updateCells()
        self.table.resizeColumnsToContents()
        
        
    def setCells(self, cells, row):
        cell_name = QtGui.QTableWidgetItem(cells[0])
        self.table.setItem(row, 0, cell_name)
        
        cell_ver = QtGui.QTableWidgetItem(cells[1])
        self.table.setItem(row, 1, cell_ver)
        
        
    def updateCells(self):
        for i in range(len(addons)):
            if len(addons[i]) == 2:
                self.setCells(addons[i], i)
            else:
                self.setCells([addons[i], ''], i)
            
            
    def updateAddons(self):
        for i in range(len(addons)):
            response = urllib2.urlopen(addons[i][0] + '/download')
            html = response.read()

            soup = BeautifulSoup(html)
            for link in soup.findAll('a'):
                zipfile = link.get('data-href')
                if zipfile != None:
                    if len(addons[i]) == 1:
                        version = getFile(zipfile)
                        if len(addons[i]) == 2:
                            addons[i][1] = version
                        else: addons[i].append(version)
                    elif zipfile.split('/')[-1] != addons[i][1]:
                        version = getFile(zipfile)
                        if len(addons[i]) == 2:
                            addons[i][1] = version
                        else: addons[i].append(version)
            self.setCells(addons[i], i)
            self.table.resizeColumnsToContents()
            

        with open(os.path.expanduser('~/.wowcurse/addons.csv'), 'wb') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=',')
            for i in range(len(addons)):
                csvwriter.writerow(addons[i])

        if len(updated) == 0:
            message = 'Alle Addons sind aktuell'
        else:
            message = 'Folgende Addons wurden aktualisiert:'
            for element in updated:
                message = message + '\n' + element
        n = pynotify.Notification('Curse Updater', message)
        n.show()
        
        
    def getNewAddon(self):
        self.table.hide()
        self.html.show()
        self.html.load(QtCore.QUrl('http://www.curse.com/addons/wow/'))


class SettingsWindow(QtGui.QWidget):
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        
        self.resize(400, 300)
        self.setWindowTitle('Einstellungen')
        #self.setWindowIcon(QtGui.QIcon('/usr/share/icons/Wow-icon-scalable.svg'))
        
        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width()-size.width())/2, (screen.height()-size.height())/2)
        
        bumblebox = QtGui.QComboBox()
        bumblebox.addItems(['Nein, kein Optimus', 'Ja, Primus-Backend', 'Ja, Bumblebee-Backend'])
        self.connect(bumblebox, QtCore.SIGNAL('activated(QString)'), self.bumble_chosen)
        dictionary = {'none': 0, 'primus': 1, 'bumblebee': 2}
        bumblebox.setCurrentIndex(dictionary[bumblebee])
        
        bitbox = QtGui.QComboBox()
        bitbox.addItems(['64 Bit', '32 Bit'])
        self.connect(bitbox, QtCore.SIGNAL('activated(QString)'), self.arch_chosen)
        dictionary = {64: 0, 32: 1}
        bitbox.setCurrentIndex(dictionary[arch])
        
        prefix_edit = QtGui.QLineEdit(prefix)
        prefix_edit.textChanged[str].connect(self.prefix_change)
        prefix_label = QtGui.QLabel('$HOME/')
        
        winecfg_prefix = QtGui.QPushButton(u'Winecfg für das Präfix aufrufen')
        self.connect(winecfg_prefix, QtCore.SIGNAL('clicked()'), self.winecfg)
        
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel('$HOME/'))
        hbox.addWidget(prefix_edit)
        
        vbox = QtGui.QVBoxLayout()
        
        vbox.addWidget(QtGui.QLabel(u'Präfix:'))
        vbox.addLayout(hbox)
        vbox.addWidget(winecfg_prefix)
        vbox.addWidget(QtGui.QLabel('Optimus:'))
        vbox.addWidget(bumblebox)
        vbox.addWidget(QtGui.QLabel('Architektur:'))
        vbox.addWidget(bitbox)
        
        self.setLayout(vbox)


    def bumble_chosen(self, value):
        dictionary = {'Nein, kein Optimus': 'none', 'Ja, Primus-Backend': 'primus', 'Ja, Bumblebee-Backend': 'bumblebee'}
        bumblebee = dictionary[str(value)]
        
        config.set('Settings', 'Bumblebee', bumblebee)
        with open(os.path.expanduser('~/.wowcurse/settings.cfg'), 'wb') as configfile:
            config.write(configfile)
            
            
    def arch_chosen(self, value):
        dictionary = {'64 Bit': 64, '32 Bit': 32}
        arch = dictionary[str(value)]
        
        config.set('Settings', 'Arch', arch)
        with open(os.path.expanduser('~/.wowcurse/settings.cfg'), 'wb') as configfile:
            config.write(configfile)
            
            
    def prefix_change(self, value):
        prefix = value
        
        config.set('Settings', 'Prefix', prefix)
        with open(os.path.expanduser('~/.wowcurse/settings.cfg'), 'wb') as configfile:
            config.write(configfile)
            
            
    def winecfg(self):
        os.system('env WINEPREFIX=$HOME/{} winecfg &'.format(prefix))
        

app = QtGui.QApplication(sys.argv)

settings_widget = SettingsWindow()
widget = WoWCurseWindow()
widget.show()

old_manager = widget.html.page().networkAccessManager()
new_manager = NetworkAccessManager(old_manager)
widget.html.page().setNetworkAccessManager(new_manager)

sys.exit(app.exec_())
