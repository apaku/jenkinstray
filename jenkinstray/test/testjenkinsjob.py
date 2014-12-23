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
from jenkinstray.jenkinsjob import JenkinsJob, JenkinsState

class TestJenkinsJob(unittest.TestCase):


    def testCreationInvalidArgs(self):
        self.assertRaises(AssertionError, lambda: JenkinsJob(None, None, None, None))
        self.assertRaises(AssertionError, lambda: JenkinsJob("test", None, None, None))
        self.assertRaises(AssertionError, lambda: JenkinsJob("test", True, None, None))
        self.assertRaises(AssertionError, lambda: JenkinsJob("test", True, "foo", None))
        self.assertRaises(AssertionError, lambda: JenkinsJob("test", True, "foo", 1))
        self.assertRaises(AssertionError, lambda: JenkinsJob("test", None, None, JenkinsState.Failed))

    def testJsonConversion(self):
        job = JenkinsJob("Name", True, "URL", JenkinsState.Failed)
        dictobj = job.toDict()
        self.assertEqual(dictobj, {"name": "Name", "monitored": True, "url": "URL", "state": int(JenkinsState.Failed)}, "Verify dict conversion")
        self.assertEqual(JenkinsJob.fromDict(dictobj), job, "Conversion roundtrip generates 'same' object")

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
