# -*- coding: utf-8 -*-
# Copyright (c) 2014, Andreas Pakulat <apaku@gmx.de>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from PyQt4 import QtCore, QtGui

from settings import SettingsWidget
from appdirs import user_config_dir
import os
import json
import threading
from ..jenkinsmonitor import JenkinsMonitor

CONFIG_FILENAME = "jenkinstray.json"

def refreshMonitors(trayObject):
    for monitor in trayObject.monitors:
        monitor.refreshFromServer()
    trayObject.serverInfoUpdated.emit()

class JenkinsTray(QtCore.QObject):

    serverInfoUpdated = QtCore.pyqtSignal()

    def __init__(self, parent):
        QtCore.QObject.__init__(self, parent)
        self.trayicon = QtGui.QSystemTrayIcon(self)
        self.menu = QtGui.QMenu()
        self.settingsAct = QtGui.QAction("Settings...", self.menu)
        self.settingsAct.activated.connect(self.openSettings)
        self.quitAct = QtGui.QAction("Quit", self.menu)
        self.quitAct.activated.connect(QtGui.qApp.quit)
        self.menu.addAction(self.settingsAct)
        self.menu.addSeparator()
        self.menu.addAction(self.quitAct)
        self.trayicon.setContextMenu(self.menu)
        self.image = QtGui.QImage(":///images/jenkinstray.png")
        assert(not self.image.isNull())
        self.trayicon.setIcon(QtGui.QIcon(QtGui.QPixmap.fromImage(self.image)))
        self.trayicon.setVisible(True)
        self.cfgDir = user_config_dir("jenkinstray", appauthor="jenkinstray", version="0.1")
        self.settings = self.initializeSettings()
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(lambda: threading.Thread(target=refreshMonitors(self)).start())
        self.serverInfoUpdated.connect(self.updateUiFromMonitors)
        self.updateFromSettings()
        self.timer.start()

    def updateFromSettings(self):
        self.timer.setInterval(self.settings["refreshInterval"] * 1000)
        self.monitors = []
        for server in self.settings["servers"]:
            monitor = JenkinsMonitor(server["url"])
            monitor._refreshFromDict(server)
            for job in monitor.jobs:
                settingsjob = filter(lambda settingsjob: settingsjob["name"] == job.name, server["jobs"])[0]
                if settingsjob["monitored"]:
                    job.enableMonitoring()
            self.monitors.append(monitor)
        self.updateUiFromMonitors()

    def updateUiFromMonitors(self):
        failCnt = 0
        unstableCnt = 0
        for monitor in self.monitors:
            failCnt += monitor.numFailedMonitoredJobs()
            unstableCnt += monitor.numUnstableMonitoredJobs()
        if failCnt > 0:
            self.image = QtGui.QImage(":///images/jenkinstray_failed.png")
        elif unstableCnt > 0:
            self.image = QtGui.QImage(":///images/jenkinstray_unstable.png")
        else:
            self.image = QtGui.QImage(":///images/jenkinstray_success.png")
        self.trayicon.setIcon(QtGui.QIcon(QtGui.QPixmap.fromImage(self.image)))

    def initializeSettings(self):
        try:
            return json.load(open(os.path.join(self.cfgDir, CONFIG_FILENAME), "r"))
        except:
            return {"refreshInterval": 60, "servers": []}

    def openSettings(self):
        dialog = QtGui.QDialog()
        dialog.setWindowTitle("Jenkins Tray Settings")
        settings = dict(self.settings)
        settingswidget = SettingsWidget(dialog, settings)
        layout = QtGui.QVBoxLayout(dialog)
        layout.addWidget(settingswidget)
        buttonbox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.StandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel), QtCore.Qt.Horizontal, dialog)
        layout.addWidget(buttonbox)
        buttonbox.accepted.connect(dialog.accept)
        buttonbox.rejected.connect(dialog.reject)
        dialog.setModal(True)
        if dialog.exec_() == QtGui.QDialog.Accepted:
            self.settings = settings
            self.writeSettings()
            self.updateFromSettings()

    def writeSettings(self):
        if not os.path.exists(self.cfgDir):
            os.makedirs(self.cfgDir)
        json.dump(self.settings, open(os.path.join(self.cfgDir, CONFIG_FILENAME), "w"), indent=4, separators=(",", ": "))
