import os
from threading import Thread
import time

from server.LineChecker import LineCheckBase


class LogsTracker:
    def __init__(self, path):
        self.lastLine = 0
        self.lastMTime = 0
        self.path = path
        self.running = False
        self.lineCheckers = set([])

    def addChecker(self, lineChecker: LineCheckBase):
        self.lineCheckers.add(lineChecker)

    def start(self):
        self.running = True
        Thread(target=self._listenThread).start()

    def stop(self):
        self.running = False

    def _listenThread(self):
        while self.running:
            try:
                time.sleep(0.05)
                if os.path.isfile(self.path):
                    mTime = os.path.getmtime(self.path)
                    if mTime != self.lastMTime:
                        self.lastMTime = mTime
                        self._checkFile()
            except:
                pass

    def _checkFile(self):
        with open(self.path, "r") as logsFile:
            content = logsFile.readlines()
            logsFile.close()

        if len(content) < self.lastLine:
            self.lastLine = 0

        for line in content[self.lastLine:]:
            print(line)
            for lineChecker in self.lineCheckers:
                lineChecker.check(line)
        self.lastLine = len(content)