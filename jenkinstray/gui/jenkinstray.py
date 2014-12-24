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

import sys

from PyQt4 import QtCore, QtGui

from settings import SettingsWidget

class JenkinsTray(QtCore.QObject):

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

    def openSettings(self):
        dialog = QtGui.QDialog()
        settings = SettingsWidget(dialog, {"servers": [{"name": "a", "jobs": [{"name":"job1", "monitored":True}, {"name":"job2", "monitored":False}]},
                                                       {"name": "b", "jobs": [{"name":"job3", "monitored":True}, {"name":"job5", "monitored":False}]},
                                                       {"name": "c", "jobs": [{"name":"job4", "monitored":True}, {"name":"job6", "monitored":False}]},
                                                      ], "refreshInterval": 60})
        layout = QtGui.QVBoxLayout(dialog)
        layout.addWidget(settings)
        layout.addWidget(QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.StandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel), QtCore.Qt.Horizontal, dialog))
        dialog.setModal(True)
        dialog.exec_()
