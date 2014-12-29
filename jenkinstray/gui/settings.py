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

from PyQt4 import QtCore, QtGui, uic
from PyQt4.Qt import QProgressDialog
from threading import Thread
from ..jenkinsmonitor import JenkinsMonitor

class ServerListModel(QtGui.QStringListModel):
    pass

class JobListModel(QtGui.QStringListModel):
    def __init__(self, jobs, parent):
        QtGui.QStringListModel.__init__(self, map(lambda x: x["name"], jobs), parent)
        self.jobs = jobs

    def data(self, idx, role):
        """
        :type idx: QtCore.QModelIndex
        :type role: QtCore.Qt.ItemDataRole
        """
        if role == QtCore.Qt.CheckStateRole:
            return QtCore.Qt.Checked if self.jobs[idx.row()]["monitored"] else QtCore.Qt.Unchecked
        else:
            return QtGui.QStringListModel.data(self, idx, role)

    def setData(self, idx, data, role):
        """
        :type idx: QtCore.QModelIndex
        :type data: QtCore.QVariant
        :type role: QtCore.Qt.ItemDataRole
        """
        if role == QtCore.Qt.CheckStateRole:
            self.jobs[idx.row()]["monitored"] = True if data == QtCore.Qt.Checked else False
            return True
        else:
            return QtGui.QStringListModel.setData(self, idx, data, role)

    def flags(self, idx):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable

def loadJobs(settingsWidget, serverurl):
    try:
        monitor = JenkinsMonitor(serverurl)
        monitor.refreshFromServer()
        settingsWidget.jobsReceived.emit(serverurl, map(lambda job: {"name": job.name,
                                                                     "monitored": False}, monitor.jobs))
    except Exception, e:
        settingsWidget.jobLoadFailed.emit(serverurl, repr(e))

class SettingsWidget(QtGui.QWidget):

    jobsReceived = QtCore.pyqtSignal(str, list)
    jobLoadFailed = QtCore.pyqtSignal(str, str)

    def __init__(self, parent, settingsobj):
        QtGui.QWidget.__init__(self, parent)
        self.settings = settingsobj
        self.uiFile = QtCore.QFile(":///gui/settings.ui")
        self.uiFile.open(QtCore.QIODevice.ReadOnly)
        uic.loadUi(self.uiFile, self)
        self.refreshInterval.setValue(self.settings["refreshInterval"])
        self.refreshInterval.valueChanged.connect(self.updateRefreshInterval)
        self.refreshModel()
        self.removeServerBtn.setEnabled(False)
        self.addServerBtn.clicked.connect(self.addServer)
        self.removeServerBtn.clicked.connect(self.removeServer)

    def reportError(self, serverurl, error):
        QtGui.QMessageBox.critical(self, "Error loading job list", "Failed to fetch job list for %s: %s." % (serverurl, error))

    def addJobs(self, serverurl, joblist):
        server = filter(lambda server: server["url"] == serverurl, self.settings["servers"])[0]
        server["jobs"] = joblist

    def addServer(self):
        dlg = QtGui.QInputDialog(self)
        dlg.setLabelText("Provide the normal url the Jenkins server can be contacted at:")
        dlg.setWindowTitle("Add Jenkins Server")
        dlg.setInputMode(QtGui.QInputDialog.TextInput)
        dlg.setMinimumSize(120, 400)
        if dlg.exec_() == QtGui.QDialog.Accepted:
            self.settings["servers"].append({"url":dlg.textValue(), "jobs":[]})
            serverurl = dlg.textValue()
            self.fetchJobs(serverurl)
            self.refreshModel(serverurl)

    def fetchJobs(self, serverurl):
        dlg = QProgressDialog(self)
        self.jobsReceived.connect(self.addJobs)
        self.jobLoadFailed.connect(self.reportError)
        self.jobsReceived.connect(dlg.accept)
        self.jobLoadFailed.connect(dlg.accept)
        thread = Thread(target=lambda: loadJobs(self, serverurl))
        thread.start()
        dlg.exec_()
        self.jobLoadFailed.disconnect()
        self.jobsReceived.disconnect()
        if dlg.wasCanceled():
            server = filter(lambda server: server["url"] == serverurl, self.settings["servers"])[0]
            self.settings["servers"].remove(server)

    def removeServer(self):
        selection = self.serverList.selectionModel().selectedRows()
        for idx in selection:
            del self.settings["servers"][idx.row()]
            self.refreshModel()

    def refreshModel(self, selectServer=None):
        self.serverList.setModel(ServerListModel(map(lambda x: x["url"], self.settings["servers"]), self.serverList))
        self.serverList.selectionModel().selectionChanged.connect(self.serverSelected)
        if selectServer is not None:
            row = -1
            for i in range(len(self.settings["servers"])):
                if self.settings["servers"][i]["url"] == selectServer:
                    row = i
            if row != -1:
                model = self.serverList.model()
                self.serverList.selectionModel().select(model.index(row, 0, QtCore.QModelIndex()), QtGui.QItemSelectionModel.ClearAndSelect)
        else:
            self.jobList.setModel(None)

    def updateRefreshInterval(self, val):
        self.settings["refreshInterval"] = val

    def serverSelected(self, selected, deselected):
        """
        :type selected: QtGui.QItemSelection
        :type deselected: QtGui.QItemSelection
        """
        if len(selected.indexes()) > 0:
            idx = selected.indexes()[0]
            self.removeServerBtn.setEnabled(True)
            serverUrl = idx.data()
            server = filter(lambda x: x["url"] == serverUrl, self.settings["servers"])[0]
            self.jobList.setModel(JobListModel(server["jobs"], self.jobList))
        else:
            self.removeServerBtn.setEnabled(False)
            self.jobList.setModel(None)
