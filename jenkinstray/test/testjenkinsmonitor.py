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

import unittest
from jenkinstray.jenkinsmonitor import JenkinsMonitor
from jenkinstray.jenkinsjob import JenkinsJob, JenkinsState

class TestJenkinsMonitor(unittest.TestCase):


    def testDictConversion(self):
        monitor = JenkinsMonitor()
        jobs = [JenkinsJob("Name1", True, "Url1", JenkinsState.Successful), JenkinsJob("Name2", False, "Url2", JenkinsState.Failed)]
        monitor.jobs.append(jobs[0])
        monitor.jobs.append(jobs[1])
        dictobj = monitor.toDict()
        self.assertEqual(dictobj, {"jobs": [job.toDict() for job in jobs]}, "Dict conversion")
        self.assertEqual(monitor, JenkinsMonitor.fromDict(dictobj), "Restoring from dict works")


    def testFailedJobs(self):
        monitor = JenkinsMonitor()
        monitor.jobs.append(JenkinsJob("Name1", True, "Url1", JenkinsState.Successful))
        monitor.jobs.append(JenkinsJob("Name2", False, "Url2", JenkinsState.Failed))
        self.assertEqual(monitor.numFailedMonitoredJobs(), 0, "No monitored job failed")
        monitor.jobs.append(JenkinsJob("Name3", True, "Url3", JenkinsState.Failed))
        self.assertEqual(monitor.numFailedMonitoredJobs(), 1, "One monitored job failed")

    def testMonitoredJobs(self):
        monitor = JenkinsMonitor()
        jobs = [JenkinsJob("Name1", True, "Url1", JenkinsState.Successful), JenkinsJob("Name2", False, "Url2", JenkinsState.Failed)]
        monitor.jobs.append(jobs[0])
        monitor.jobs.append(jobs[1])
        self.assertEqual(list(monitor.monitoredJobs()), [jobs[0]], "Only one job is monitored")
        monitor.jobs.append(jobs[0])
        self.assertEqual(list(monitor.monitoredJobs()), [jobs[0], jobs[0]], "Two jobs are monitored")

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
