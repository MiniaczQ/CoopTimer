import os
from threading import Thread
import time

from server.LineChecker import LineCheckBase


class LogsTracker:
    def __init__(self, path) -> None:
        self.lastLine = 0
        self.lastMTime = 0
        self.path = path
        self.running = False
        self.lineCheckers = set([])

    def addChecker(self, lineChecker: LineCheckBase) -> None:
        self.lineCheckers.add(lineChecker)

    def start(self) -> None:
        self.running = True
        Thread(target=self._listenThread).start()

    def stop(self) -> None:
        self.running = False

    def _listenThread(self) -> None:
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

    def _checkFile(self) -> None:
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