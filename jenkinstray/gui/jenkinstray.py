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
import traceback
from ..jenkinsmonitor import JenkinsMonitor
from ..jenkinsjob import JenkinsJob, JenkinsState

CONFIG_FILENAME = "jenkinstray.json"

def refreshMonitors(trayObject):
    errors = []
    for monitor in trayObject.monitors:
        try:
            monitor.refreshFromServer()
            if monitor in trayObject.monitorsWithConnectivityProblems:
                trayObject.monitorsWithConnectivityProblems.remove(monitor)
        except Exception, e:
            if monitor not in trayObject.monitorsWithConnectivityProblems:
                errors.append(str(e))
            trayObject.monitorsWithConnectivityProblems.append(monitor)
            print "Error refreshing jenkins server %s: %s" % (monitor.serverurl, traceback.format_exc())
    trayObject.serverInfoUpdated.emit(errors)

class JenkinsTray(QtCore.QObject):

    serverInfoUpdated = QtCore.pyqtSignal(list)

    def __init__(self, parent):
        QtCore.QObject.__init__(self, parent)
        self.monitors = []
        self.monitorsWithConnectivityProblems = []
        self.trayicon = QtGui.QSystemTrayIcon(self)
        self.menu = QtGui.QMenu()
        self.settingsAct = QtGui.QAction("Settings...", self.menu)
        self.settingsAct.activated.connect(self.openSettings)
        self.aboutQtAct = QtGui.QAction("About Qt", self.menu)
        self.aboutQtAct.activated.connect(self.aboutQt)
        self.aboutAct = QtGui.QAction("About %s" % QtGui.qApp.applicationName(), self.menu)
        self.aboutAct.activated.connect(self.aboutApp)
        self.quitAct = QtGui.QAction("Quit", self.menu)
        self.quitAct.activated.connect(QtGui.qApp.quit)
        self.menu.addAction(self.settingsAct)
        self.menu.addSeparator()
        self.menu.addAction(self.aboutAct)
        self.menu.addAction(self.aboutQtAct)
        self.menu.addSeparator()
        self.menu.addAction(self.quitAct)
        self.trayicon.setContextMenu(self.menu)
        self.image = QtGui.QImage(":///images/jenkinstray.png")
        assert(not self.image.isNull())
        self.trayicon.setIcon(QtGui.QIcon(QtGui.QPixmap.fromImage(self.image)))
        self.trayicon.setVisible(True)
        self.cfgDir = user_config_dir("jenkinstray", appauthor="jenkinstray", version="0.1")
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(lambda: threading.Thread(target=refreshMonitors(self)).start())
        self.serverInfoUpdated.connect(self.updateUiFromMonitors)
        self.updateFromSettings(self.readSettings())
        self.timer.start()

    def aboutApp(self):
        QtGui.QMessageBox.about(None,
                                "About %s" % QtGui.qApp.applicationName(),
                                "<b>About %s</b><br /><br />Version: %s<br /><br />Jenkins Tray is a system tray application that monitors one or more jobs running on one or more jenkins instances and shows the overal status of the jobs as well as allowing access to the job web pages." % (QtGui.qApp.applicationName(),
                                                    QtGui.qApp.applicationVersion()))

    def aboutQt(self):
        QtGui.QMessageBox.aboutQt(None, "About Qt")

    def updateFromSettings(self, settings):
        self.timer.setInterval(settings["refreshInterval"] * 1000)
        self.notificationTimeout = settings["notificationTimeout"] * 1000
        for server in settings["servers"]:
            match = filter(lambda monitor: monitor.serverurl == server["url"], self.monitors)
            monitor = None
            if match:
                monitor = match[0]
            else:
                monitor = JenkinsMonitor(server["url"])
                self.monitors.append(monitor)
            for job in server["jobs"]:
                monitorjobmatches = filter(lambda monitorjob: monitorjob.name == job["name"], monitor.allJobs())
                if monitorjobmatches:
                    monitorjob = monitorjobmatches[0]
                else:
                    monitorjob = JenkinsJob(job["name"], job["monitored"], "Unknown", JenkinsState.Unknown)
                    monitor.jobs.append(monitorjob)
                if job["monitored"]:
                    monitorjob.enableMonitoring()
                else:
                    monitorjob.disableMonitoring()
        for monitor in list(self.monitors):
            if len(filter(lambda server: monitor.serverurl == server["url"], settings["servers"])) == 0:
                self.monitors.remove(monitor)

    def addCountToImage(self, number):
        painter = QtGui.QPainter(self.image)
        font = painter.font()
        maxwidth = self.image.width() - round(self.image.width() * .3)
        maxheight = self.image.height() - round(self.image.height() * .3)
        metrics = QtGui.QFontMetrics(font)
        text = str(number)
        while metrics.width(text) < maxwidth and metrics.height() < maxheight:
            font.setPointSize(font.pointSize() + 1)
            metrics = QtGui.QFontMetrics(font)

        painter.setFont(font)
        painter.drawText(self.image.rect(), QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter, text)
        painter.end()

    def updateUiFromMonitors(self, errors):
        failCnt = 0
        unstableCnt = 0
        successfulCnt = 0
        failedjobs = []
        unstablejobs = []
        fixedjobs = []
        for monitor in self.monitors:
            failCnt += monitor.numFailedMonitoredJobs()
            unstableCnt += monitor.numUnstableMonitoredJobs()
            successfulCnt += monitor.numSuccessfulMonitoredJobs()
            for job in monitor.monitoredJobs():
                if job.lastState != job.state:
                    if job.state == JenkinsState.Failed and job.lastState in [JenkinsState.Unstable, JenkinsState.Successful]:
                        failedjobs.append(job.name)
                    elif job.state == JenkinsState.Unstable and job.lastState in [JenkinsState.Failed, JenkinsState.Successful]:
                        unstablejobs.append(job.name)
                    elif job.state == JenkinsState.Successful and job.lastState in [JenkinsState.Failed, JenkinsState.Unstable]:
                        fixedjobs.append(job.name)
        if failCnt > 0:
            self.image = QtGui.QImage(":///images/jenkinstray_failed.png")
        elif unstableCnt > 0:
            self.image = QtGui.QImage(":///images/jenkinstray_unstable.png")
        elif successfulCnt > 0:
            self.image = QtGui.QImage(":///images/jenkinstray_success.png")
        else:
            self.image = QtGui.QImage(":///images/jenkinstray.png")
        if len(errors) > 0:
            self.trayicon.showMessage("Connectivity Problems", "\n".join(errors), QtGui.QSystemTrayIcon.Critical, self.notificationTimeout)
        elif len(failedjobs) > 0:
            self.trayicon.showMessage("Failed Jobs", "\n".join(failedjobs), QtGui.QSystemTrayIcon.Critical, self.notificationTimeout)
        elif len(fixedjobs) > 0:
            self.trayicon.showMessage("Fixed Jobs", "\n".join(fixedjobs), QtGui.QSystemTrayIcon.Information, self.notificationTimeout)
        elif len(unstablejobs) > 0:
            self.trayicon.showMessage("Unstable Jobs", "\n".join(unstablejobs), QtGui.QSystemTrayIcon.Warning, self.notificationTimeout)
        if failCnt > 0 or unstableCnt > 0:
            self.addCountToImage(failCnt + unstableCnt)
        self.trayicon.setIcon(QtGui.QIcon(QtGui.QPixmap.fromImage(self.image)))
        self.trayicon.setToolTip("%s failed jobs\n%s unstable jobs\n%s successful jobs" % (failCnt, unstableCnt, successfulCnt))

    def readSettings(self):
        try:
            return json.load(open(os.path.join(self.cfgDir, CONFIG_FILENAME), "r"))
        except:
            return {"refreshInterval": 60, "servers": [], "notificationTimeout": 10}

    def openSettings(self):
        dialog = QtGui.QDialog()
        dialog.setWindowTitle("Jenkins Tray Settings")
        settingsdata = self.createSettingsFromMonitors()
        settingswidget = SettingsWidget(dialog, settingsdata)
        layout = QtGui.QVBoxLayout(dialog)
        layout.addWidget(settingswidget)
        buttonbox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.StandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel), QtCore.Qt.Horizontal, dialog)
        layout.addWidget(buttonbox)
        buttonbox.accepted.connect(dialog.accept)
        buttonbox.rejected.connect(dialog.reject)
        dialog.setModal(True)
        if dialog.exec_() == QtGui.QDialog.Accepted:
            self.writeSettings(settingsdata)
            self.updateFromSettings(settingsdata)

    def writeSettings(self, settings):
        if not os.path.exists(self.cfgDir):
            os.makedirs(self.cfgDir)
        json.dump(settings, open(os.path.join(self.cfgDir, CONFIG_FILENAME), "w"), indent=4, separators=(",", ": "))

    def createSettingsFromMonitors(self):
        return {
                "refreshInterval": int(self.timer.interval() / 1000),
                "notificationTimeout": int(self.notificationTimeout / 1000),
                "servers": map(lambda monitor: {
                                                "url": monitor.serverurl,
                                                "jobs": map(lambda job: {
                                                                         "name": job.name,
                                                                         "monitored": job.monitored
                                                                        },
                                                            monitor.allJobs())
                                               },
                               self.monitors)
               }
