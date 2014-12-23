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

from enum import IntEnum

def colorToJenkinsState(colorstr):
    assert(colorstr in ["blue", "yellow", "red"])
    if colorstr == "blue":
        return JenkinsState.Successful
    elif colorstr == "yellow":
        return JenkinsState.Unstable
    else:
        return JenkinsState.Failed

class JenkinsState(IntEnum):
    Unstable = 0
    Failed = 1
    Successful = 2

class JenkinsJob(object):
    def __init__(self, name, monitored, url, state):
        assert name is not None
        self.name = name
        assert url is not None
        self.url = url
        assert state in JenkinsState
        self.state = state
        assert monitored is not None 
        self.monitored = monitored

    def __ne__(self, other):
        return self.name != other.name or self.url != other.url or self.monitored != other.monitored or self.state != other.state

    def __eq__(self, other):
        return self.name == other.name and self.url == other.url and self.monitored == other.monitored and self.state == other.state

    def enableMonitoring(self):
        self.monitored = True
        
    def disableMonitoring(self):
        self.monitored = False
        
    def toDict(self):
        return {"name": self.name, "state" : int(self.state), "url": self.url, "monitored": self.monitored}
    
    @classmethod
    def fromDict(clz, dictobj):
        return JenkinsJob(dictobj["name"], dictobj["monitored"], dictobj["url"], JenkinsState(dictobj["state"]))