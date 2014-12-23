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

import json
from threading import Thread
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

class TestJenkinsMonitor(unittest.TestCase):
    class FixedRequestHandler(BaseHTTPRequestHandler):
        jsonData = ""
        def do_GET(self):
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(TestJenkinsMonitor.FixedRequestHandler.jsonData)))
            self.end_headers()
            self.wfile.write(TestJenkinsMonitor.FixedRequestHandler.jsonData)

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
        self.assertEqual(list(monitor.allJobs()), [jobs[0], jobs[1]], "Only one job is monitored")
        self.assertEqual(list(monitor.monitoredJobs()), [jobs[0]], "two jobs alltogether")
        monitor.jobs.append(jobs[0])
        self.assertEqual(list(monitor.monitoredJobs()), [jobs[0], jobs[0]], "Two jobs are monitored")
        self.assertEqual(list(monitor.allJobs()), [jobs[0], jobs[1], jobs[0]], "three jobs alltogether")

    def testUpdatingFromData(self):
        monitor = JenkinsMonitor()
        jobs = [JenkinsJob("Name1", True, "Url1", JenkinsState.Successful), JenkinsJob("Name2", True, "Url2", JenkinsState.Failed)]
        monitor.jobs.append(jobs[0])
        monitor.jobs.append(jobs[1])
        self.assertEqual(list(monitor.monitoredJobs()), [jobs[0], jobs[1]], "Only one job is monitored")
        self.assertEqual(list(monitor.monitoredJobs()), [jobs[0], jobs[1]], "two jobs alltogether")

        monitor._refreshFromDict({"jobs": [{"name":"Name1", "url": "Url1", "color": "yellow"},
                                          {"name":"Name3", "url": "Url3", "color": "blue"}]})

        updatedJob1 = jobs[0]
        updatedJob1.state = JenkinsState.Unstable
        self.assertEqual(list(monitor.monitoredJobs()), [updatedJob1], "Only one job is monitored")
        self.assertEqual(list(monitor.allJobs()), [updatedJob1, JenkinsJob("Name3", False, "Url3", JenkinsState.Successful)], "two jobs alltogether")

    def testUpdatingFromServer(self):
        TestJenkinsMonitor.FixedRequestHandler.jsonData = json.dumps(
                    {"jobs":[{"name": "Name1", "color": "blue", "url": "Url1"},
                             {"name": "Name2", "color": "red", "url": "Url2"},
                             {"name": "Name3", "color": "yellow", "url": "Url3"},
                            ]
                    })
        server = HTTPServer(("localhost", 0), TestJenkinsMonitor.FixedRequestHandler)
        thread = Thread(target=server.serve_forever, name=str("localhost:%s" % server.server_address[1]),)
        thread.daemon = True
        thread.start()
        monitor = JenkinsMonitor("http://localhost:%s" % server.server_address[1])

        self.assertEqual(list(monitor.allJobs()), [], "No jobs registered initially")
        monitor.refreshFromServer()

        joblist1 = [JenkinsJob("Name1", False, "Url1", JenkinsState.Successful),
                    JenkinsJob("Name2", False, "Url2", JenkinsState.Failed),
                    JenkinsJob("Name3", False, "Url3", JenkinsState.Unstable),
                   ]
        self.assertEqual(list(monitor.allJobs()), joblist1, "3 jobs registered after refresh")
        self.assertEqual(list(monitor.monitoredJobs()), [], "No jobs monitored after refresh")

        TestJenkinsMonitor.FixedRequestHandler.jsonData = json.dumps(
                    {"jobs":[
                             {"name": "Name1", "color": "red", "url": "Url1"},
                             {"name": "Name3", "color": "blue", "url": "Url3"},
                             {"name": "Name4", "color": "blue", "url": "Url4"},
                            ]
                    })
        monitor.refreshFromServer()

        joblist2 = [JenkinsJob("Name1", False, "Url1", JenkinsState.Failed),
                    JenkinsJob("Name3", False, "Url3", JenkinsState.Successful),
                    JenkinsJob("Name4", False, "Url4", JenkinsState.Successful),
                   ]
        self.assertEqual(list(monitor.allJobs()), joblist2, "3 jobs registered after second refresh, but one removed")
        self.assertEqual(list(monitor.monitoredJobs()), [], "No jobs monitored after second refresh")

        server.shutdown()

        thread.join()

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
