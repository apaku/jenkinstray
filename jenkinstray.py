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

import json

from PyQt4.QtCore import QTimer, QUrl, QObject, QSettings, QPoint, QRect, Qt, QSignalMapper
from PyQt4.QtGui import QApplication, QSystemTrayIcon, QIcon, QPixmap, QImage, QPainter, \
                        QMenu, QAction, QDesktopServices, QColor
from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest

POLL_INTERVAL = 2000
JENKINS_SERVER = "http://jenkins.froglogic.com"

class Job(object):
    def __init__(self, name, url=None, color=None):
        self.name = name
        self.url = url
        self.color = color

class JenkinsTray(QObject):
    def __init__(self, app):
        QObject.__init__(self)
        self.nam = QNetworkAccessManager(self)
        self.icon = QSystemTrayIcon(self)
        self.updateTimer = QTimer(self)
        self.image = QImage("./jenkinstray.png")
        self.icon.setIcon(QIcon(QPixmap.fromImage(self.image)))
        self.icon.setVisible(True)
        self.updateTimer.setInterval(POLL_INTERVAL)
        self.updateTimer.start()
        self.updateTimer.timeout.connect(self.queryJenkins)
        (self.jobs, self.ignoredJobs) = self.readConfiguration()
        self.menu = QMenu()
        self.openUrlMapper = QSignalMapper(self)
        self.openUrlMapper.mapped[str].connect(self.openJobUrl)
        self.watchJobMapper = QSignalMapper(self)
        self.watchJobMapper.mapped[str].connect(self.watchJob)
        self.updateContextMenuJobList()
        self.jobSeparator = self.menu.addSeparator()
        self.newSubMenu = self.menu.addMenu("Watch New Jobs")
        self.menu.addSeparator()
        self.menu.addAction("Exit").triggered.connect(app.exit)
        self.newSubMenu.addAction("Watch all").triggered.connect(self.watchAll)
        self.newSubMenu.addAction("Watch none").triggered.connect(self.watchNone)
        self.newSubMenu.addSeparator()
        self.icon.setContextMenu(self.menu)
        self.status = ""

    def updateContextMenuJobList(self):
        actiontexts = [action.text() for action in self.menu.actions()]
        for job in self.jobs:
            if job.name not in actiontexts:
                act = QAction(job.name, self.menu)
                self.menu.insertAction(self.jobSeparator, act)
                self.openUrlMapper.setMapping(act, job.name)
                act.triggered.connect(self.openUrlMapper.map)
                self.updateActionIcon(act, job.color)

    def watchNone(self):
        self.ignoredJobs += self.newjobs
        self.newjobs = []
        self.updateNewSubmenu()
        self.saveConfiguration()

    def watchAll(self):
        self.jobs += self.newjobs
        self.newjobs = []
        self.updateNewSubmenu()
        self.saveConfiguration()

    def watchJob(self, jobname):
        for job in filter(lambda x: x.name == jobname, self.newjobs):
            self.jobs.append(job)
            self.newjobs.remove(job)
        self.updateContextMenuJobList()
        self.updateNewSubmenu()
        self.saveConfiguration()

    def updateNewSubmenu(self):
        for action in self.newSubMenu.actions():
            if action.text() != "Watch all" and action.text() != "Watch none":
                self.newSubMenu.removeAction(action)
        for job in self.newjobs:
            act = self.newSubMenu.addAction(job.name)
            self.watchJobMapper.setMapping(act, job.name)
            act.triggered.connect(self.watchJobMapper.map)
            self.updateActionIcon(act, job.color)

    def openJobUrl(self, jobname):
        for job in filter(lambda x: x.name == jobname, self.jobs):
            QDesktopServices.openUrl(QUrl(job.url))

    def readConfiguration(self):
        settings = QSettings("JenkinsTray", "JenkinsTray")
        return (self.readJobList(settings, "Jobs"), self.readJobList(settings, "IgnoredJobs", False))

    def readJobList(self, settings, groupName, urlAndColor=True):
        settings.beginGroup(groupName)
        jobs = []
        for jobGroup in settings.childGroups():
            settings.beginGroup(jobGroup)
            url = None
            color = None
            if urlAndColor:
                url = settings.value("Url")
            if urlAndColor:
                color = settings.value("Color")
            jobs.append(Job(settings.value("Name"), url, color))
            settings.endGroup()
        settings.endGroup()
        return jobs

    def saveConfiguration(self):
        settings = QSettings("JenkinsTray", "JenkinsTray")
        self.storeJobList(settings, "Jobs", self.jobs)
        self.storeJobList(settings, "Ignored Jobs", self.ignoredJobs, False)

    def storeJobList(self, settings, groupName, jobList, urlAndColor=True):
        settings.beginGroup(groupName)
        settings.remove("")
        cnt = 0
        for job in jobList:
            settings.beginGroup("Job_%d" % cnt)
            settings.setValue("Name", job.name)
            if urlAndColor:
                settings.setValue("Url", job.url)
            if urlAndColor:
                settings.setValue("Color", job.color)
            settings.endGroup()
            cnt += 1
        settings.endGroup()

    def queryJenkins(self):
        self.startJobListingQuery()

    def startJobListingQuery(self):
        request = QNetworkRequest(QUrl(JENKINS_SERVER+"/api/json"))
        self.jobListingReply = self.nam.get(request)
        self.jobListingReply.finished.connect(self.jobListingDone)

    def jobListingDone(self):
        jsondata = json.loads(self.jobListingReply.readAll().data())
        jobdata = [Job(j["name"], j["url"], j["color"]) for j in jsondata["jobs"]]
        trackedjobnames = [j.name for j in self.jobs]
        ignoredjobnames = [j.name for j in self.ignoredJobs]
        self.newjobs = filter(lambda j: j.name not in trackedjobnames and j.name not in ignoredjobnames, jobdata)
        if len(self.newjobs):
            #self.icon.showMessage("New Jobs", "Found %d new jobs" % len(self.newjobs))
            self.updateNewSubmenu()
        updatedjobdata = dict([(job.name,job.color) for job in filter(lambda j: j.name in trackedjobnames, jobdata)])
        for job in self.jobs:
            if job.color != updatedjobdata[job.name]:
                job.color = updatedjobdata[job.name]
                self.updateAction(job.name, job.color)
        status = ""
        problemcnt = 0
        for job in self.jobs:
            if job.color == "yellow":
                if status == "blue" or status == "disabled":
                    status = job.color
                problemcnt += 1
            elif job.color == "red":
                status = job.color
                problemcnt += 1
            elif job.color == "blue" and status =="disabled":
                status = job.color
            else:
                status = job.color
        if status != self.status:
            self.status = status
            print "Updating icon", status, problemcnt
            self.updateIcon(status, problemcnt)

    def updateIcon(self, status, cnt):
        image = QImage(self.image)
        painter = QPainter(image)
        width = image.width()
        height = image.height()
        brush = painter.brush()
        self.updateBrushForStatus(brush, status)
        painter.setBrush(brush)
        painter.drawEllipse(QPoint(width/2, height/2), 12, 12)
        font = painter.font()
        font.setPixelSize(12)
        painter.setFont(font)
        brush.setColor(QColor(0, 0, 0))
        painter.setBrush(brush)
        painter.drawText(QRect(0, 0, 24, 24), Qt.AlignVCenter | Qt.AlignHCenter, "%d" % cnt)
        painter.end()
        print "Updated icon to", status, cnt
        self.icon.setIcon(QIcon(QPixmap.fromImage(image)))

    def updateBrushForStatus(self, brush, status):
        if status == "disabled":
            brush.setColor(QColor(128,128,128))
        elif status == "blue":
            brush.setColor(QColor(0,0,255))
        elif status == "yellow":
            brush.setColor(QColor(255,255,0))
        elif status == "red":
            brush.setColor(QColor(255,0,0))
        brush.setStyle(Qt.SolidPattern)

    def updateAction(self, jobname, jobstatus):
        for action in self.menu.actions():
            if action.text() == jobname:
                self.updateActionIcon(action, jobstatus)

    def updateActionIcon(self, action, status):
        image = QImage(16, 16, QImage.Format_ARGB32)
        painter = QPainter(image)
        brush = painter.brush()
        self.updateBrushForStatus(brush, status)
        painter.setBrush(brush)
        painter.drawEllipse(QPoint(image.width()/2, image.height()/2), 4, 4)
        painter.end()
        action.setIcon(QIcon(QPixmap.fromImage(image)))

def main(args):
    global app
    app = QApplication(args)
    tray = JenkinsTray(app)
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main(sys.argv))
