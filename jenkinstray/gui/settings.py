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

class ServerListModel(QtGui.QStringListModel):
    pass

class JobListModel(QtGui.QStringListModel):
    pass

class SettingsWidget(QtGui.QWidget):

    def __init__(self, parent, settingsobj):
        QtGui.QWidget.__init__(self, parent)
        self.settings = settingsobj
        self.uiFile = QtCore.QFile(":///gui/settings.ui")
        self.uiFile.open(QtCore.QIODevice.ReadOnly)
        uic.loadUi(self.uiFile, self)
        self.refreshInterval.setValue(self.settings["refreshInterval"])
        self.serverList.setModel(ServerListModel(map(lambda x: x["name"], self.settings["servers"])))
        self.serverList.clicked.connect(self.serverSelected)

    def serverSelected(self, idx):
        """:type idx: QtCore.QModelIndex"""
        serverName = idx.data().toString()
        server = filter(lambda x: x["name"] == serverName, self.settings["servers"])[0]
        self.jobList.setModel(JobListModel(map(lambda x: x["name"], server["jobs"])))
