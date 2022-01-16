import os
import json
import signal
from threading import Thread
import asyncio
import time
import socket

from server.LineChecker import LineChecker
from server.LogsTracker import LogsTracker


class TimerClientInstance:
    def __init__(self, parent, c, addr):
        self.parent = parent
        self.clientSocket: socket.socket = c
        self.addr = addr
        self.running = True
        self.thread = Thread(target=self.loop)
        self.thread.start()

    def loop(self):
        try:
            while self.running:
                msg = self.clientSocket.recv(1024).decode()
                if msg == "quit":
                    self.running = False
                    self.send("end")
                elif self.parent.password is not None:
                    if msg == self.parent.password+"pause":
                        self.parent.togglePause()
                    elif msg == self.parent.password+"reset":
                        self.parent.resetTimer()
        except:
            pass
        self.detachFromClient()

    def detachFromClient(self):
        if self.parent is not None:
            self.parent.removeClient(self)
            self.parent = None

    def send(self, msg):
        self.clientSocket.send(msg.encode())

    def stop(self):
        self.running = False
        self.send("end")
        try:
            self.clientSocket.close()
        except:
            pass
        self.detachFromClient()


class TimerServer:
    def __init__(self, addr="127.0.0.1", port=25564, password=None):
        self.addr = addr
        self.port = port
        self.password = password

        self.socket = socket.socket()

        self.clients = []
        self.running = False
        self.startTime = time.time()
        self.pauseTime = 0
        self.timerStatus = "stopped"

    def start(self):
        if not self.running:
            self.running = True

            self.socket.bind((self.addr, self.port))
            self.socket.listen(50)

            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            self.acceptConnectionsThread = Thread(
                target=self.acceptConnectionsLoop)
            self.acceptConnectionsThread.start()

    def togglePause(self):
        if self.timerStatus == "running":
            self.pauseTimer()
        else:
            self.startTimer()

    def startTimer(self):
        if self.timerStatus != "running":
            self.startTime = time.time() - self.pauseTime
            self.timerStatus = "running"
        self.updateClients()

    def resetTimer(self):
        if self.timerStatus != "stopped":
            self.pauseTime = 0
            self.timerStatus = "stopped"
        self.updateClients()

    def pauseTimer(self):
        if self.timerStatus == "running":
            self.pauseTime = time.time()-self.startTime
            self.timerStatus = "paused"
        self.updateClients()

    def updateClient(self, client):
        if self.timerStatus == "stopped":
            client.send("stop")
        else:
            client.send(self.timerStatus+":"+str(self.getTime()))

    def updateClients(self):
        for client in self.clients:
            self.updateClient(client)

    def sendToAll(self, msg):
        for client in self.clients:
            client.send(msg)

    def acceptConnectionsLoop(self):
        while self.running:
            try:
                c, addr = self.socket.accept()
                client = TimerClientInstance(self, c, addr)
                if self.running:
                    self.clients.append(client)
                    print("[Timer Server] Client '"+str(addr)+"' connected.")
                    self.updateClient(client)
            except:
                pass

    def setTime(self, x):
        self.pauseTime = x
        self.startTime = time.time()-x

    def getTime(self):
        if self.timerStatus == "stopped":
            return 0.0
        elif self.timerStatus == "running":
            return time.time()-self.startTime
        elif self.timerStatus == "paused":
            return self.pauseTime

    def kill(self):
        for i in self.clients:
            i.stop()
        self.running = False
        self.socket.close()

    def removeClient(self, client):
        try:
            self.clients.remove(client)
            print("[Timer Server] Client '"+str(client.addr)+"' disconnected.")
        except:
            pass

async def main():
    jsonDict = {}
    if os.path.isfile("coop_timer_server.json"):
        with open("coop_timer_server.json", "r") as jsonFile:
            jsonDict = json.load(jsonFile)
            jsonFile.close()

    path = os.path.join(jsonDict.get("logs", "logs"), "latest.log")

    lt = LogsTracker(path)
    ts = TimerServer(jsonDict.get("address", "127.0.0.1"), jsonDict.get(
        "port", 25564), jsonDict.get("password", None))

    lt.addChecker(LineChecker(ts.startTimer, "Set the time to 0"))
    lt.addChecker(LineChecker(ts.resetTimer, "Stopping the server"))

    ts.start()
    lt.start()

    stop_event = asyncio.Event()

    def handle_interrupt(sig, frame):
        stop_event.set()

    signal.signal(signal.SIGTERM, handle_interrupt)
    signal.signal(signal.SIGINT, handle_interrupt)

    await stop_event.wait()

    lt.stop()
    ts.kill()

if __name__ == "__main__":
    asyncio.run(main())
