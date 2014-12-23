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

from jenkinsjob import JenkinsState, JenkinsJob, colorToJenkinsState

class JenkinsMonitor(object):
    def __init__(self):
        self.jobs = []

    def refreshFromDict(self, dictobj):
        knownjobnames = []
        for jobinfo in dictobj["jobs"]:
            job = self._findJobByName(jobinfo["name"])
            color = colorToJenkinsState(jobinfo["color"])
            if not job:
                self.jobs.append(JenkinsJob(jobinfo["name"], False, jobinfo["url"], color))
            else:
                job.state = color
            knownjobnames.append(jobinfo["name"])
        for job in list(self.jobs):
            if job.name not in knownjobnames:
                self.jobs.remove(job)

    def _findJobByName(self, name):
        candidates = filter(lambda job: job.name == name, self.jobs)
        assert(len(candidates) < 2)
        if len(candidates) > 0:
            return candidates[0]
        return None

    def allJobs(self):
        for job in self.jobs:
            yield job

    def __eq__(self, other):
        return self.jobs == other.jobs

    @classmethod
    def fromDict(cls, dictobj):
        monitor = JenkinsMonitor()
        for jobobj in dictobj["jobs"]:
            monitor.jobs.append(JenkinsJob.fromDict(jobobj))
        return monitor

    def toDict(self):
        return {"jobs": [job.toDict() for job in self.jobs]}

    def numFailedMonitoredJobs(self):
        count = 0
        for job in self.monitoredJobs():
            if job.state == JenkinsState.Failed:
                count += 1
        return count

    def monitoredJobs(self):
        for job in self.jobs:
            if job.monitored:
                yield job
